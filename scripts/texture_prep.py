#!/usr/bin/env python3
"""texture_prep.py — make map textures power-of-two and palettized.

Map geometry (houses, trees) is 3D (.nsbmd) with .nsbtx textures. Those
textures must have power-of-two dimensions — typically 32x32 or 64x64 —
and be palettized. This script takes an arbitrary source PNG and:

  1. brings each dimension to a power of two, either by
       pad    (default) pad right/bottom with transparency, or
       scale  nearest-neighbor resize to the nearest power of two
     (or to an explicit --size), then
  2. quantizes to an indexed palette with index 0 reserved for transparency.

The output PNG still needs conversion to .nsbtx by a Nitro tool (Pokémon DS
Map Studio does this on import); this script only guarantees the pixel
budget is legal before that step.

Examples:
    python3 scripts/texture_prep.py roof.png -o out/roof.png
    python3 scripts/texture_prep.py bark.png -o out/bark.png --mode scale --size 32x32
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("error: Pillow is not installed. Run `make setup` (or: .venv/bin/pip install Pillow)")

RESAMPLE_NEAREST = getattr(getattr(Image, "Resampling", Image), "NEAREST")
QUANTIZE_MEDIANCUT = getattr(getattr(Image, "Quantize", Image), "MEDIANCUT")
TRANSPARENT_MARKER = (255, 0, 255)


def parse_size(text):
    try:
        w, h = text.lower().split("x")
        w, h = int(w), int(h)
        if w <= 0 or h <= 0:
            raise ValueError
        return w, h
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid size {text!r}, expected WxH e.g. 64x64")


def next_pow2(n):
    p = 1
    while p < n:
        p *= 2
    return p


def build_palette(opaque_pixels, n_colors):
    pool = Image.new("RGB", (len(opaque_pixels), 1))
    pool.putdata(opaque_pixels)
    q = pool.quantize(colors=n_colors, method=QUANTIZE_MEDIANCUT)
    raw = q.getpalette()[: 3 * n_colors]
    entries = [tuple(raw[i : i + 3]) for i in range(0, len(raw), 3)]
    seen, unique = set(), []
    for e in entries:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    return unique


def nearest_index(color, palette, cache):
    hit = cache.get(color)
    if hit is not None:
        return hit
    r, g, b = color
    best, best_d = 0, 1 << 30
    for i, (pr, pg, pb) in enumerate(palette):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_d:
            best, best_d = i, d
    cache[color] = best
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="source texture PNG")
    ap.add_argument("-o", "--output", type=Path, required=True, help="output indexed PNG")
    ap.add_argument("--mode", choices=("pad", "scale"), default="pad",
                    help="pad with transparency (default) or nearest-neighbor scale")
    ap.add_argument("--size", type=parse_size, default=None, metavar="WxH",
                    help="explicit power-of-two target (e.g. 64x64); default: next power of two per dimension")
    ap.add_argument("--colors", type=int, default=16,
                    help="total palette size including transparent index 0 (default 16, max 256)")
    ap.add_argument("--alpha-threshold", type=int, default=128,
                    help="alpha below this counts as transparent (default 128)")
    args = ap.parse_args()

    if not args.input.is_file():
        sys.exit(f"error: input file not found: {args.input}")
    if not 2 <= args.colors <= 256:
        sys.exit("error: --colors must be between 2 and 256")

    try:
        img = Image.open(args.input).convert("RGBA")
    except OSError as e:
        sys.exit(f"error: could not read {args.input}: {e}")

    w, h = img.size
    if args.size:
        tw, th = args.size
        if (tw & (tw - 1)) or (th & (th - 1)):
            sys.exit(f"error: --size {tw}x{th} is not power-of-two")
    else:
        tw, th = next_pow2(w), next_pow2(h)

    if (w, h) != (tw, th):
        if args.mode == "scale":
            img = img.resize((tw, th), RESAMPLE_NEAREST)
        else:
            if w > tw or h > th:
                sys.exit(f"error: source {w}x{h} exceeds target {tw}x{th}; use --mode scale or a larger --size")
            canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            canvas.paste(img, (0, 0))
            img = canvas

    opaque = [(r, g, b) for r, g, b, a in img.getdata() if a >= args.alpha_threshold]
    palette = build_palette(opaque, args.colors - 1) if opaque else []

    cache = {}
    indices = []
    for r, g, b, a in img.getdata():
        if a < args.alpha_threshold:
            indices.append(0)
        else:
            indices.append(1 + nearest_index((r, g, b), palette, cache))
    out = Image.new("P", (tw, th))
    flat = list(TRANSPARENT_MARKER)
    for e in palette:
        flat.extend(e)
    flat.extend([0, 0, 0] * (256 - 1 - len(palette)))
    out.putpalette(flat)
    out.putdata(indices)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output, transparency=0)

    note = ""
    if max(tw, th) > 64:
        note = "  (warning: >64px is large for a map texture; 32x32 or 64x64 is typical)"
    print(f"{args.input} {w}x{h} -> {args.output} {tw}x{th} ({args.mode}), "
          f"{1 + len(palette)}/{args.colors} palette slots{note}")


if __name__ == "__main__":
    main()
