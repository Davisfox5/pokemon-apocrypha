#!/usr/bin/env python3
"""quantize.py — downscale + palette-quantize a source PNG for Gen 4 use.

Takes a full-resolution source PNG, optional target dimensions, and a color
count. Downscales with nearest-neighbor (pixel art — no smoothing), quantizes
to an indexed palette with index 0 reserved for transparency, and writes an
indexed PNG with index 0 marked transparent.

Palette index 0 is stored as magenta (255,0,255) purely as a visual marker;
the PNG tRNS chunk marks it fully transparent and DS insertion tools treat
index 0 as the transparent slot.

Examples:
    # Trainer battle front sprite: 80x80, 16 colors (15 opaque + transparent)
    python3 scripts/quantize.py art.png -o out.png --size 80x80 --colors 16

    # Quantize colors only, keep dimensions (e.g. an already-sized sheet)
    python3 scripts/quantize.py sheet.png -o out.png --colors 16
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("error: Pillow is not installed. Run `make setup` (or: .venv/bin/pip install Pillow)")

# Pillow >=9.1 moved these under enums; older names still work on most
# versions, but resolve defensively so the script runs on either.
RESAMPLE_NEAREST = getattr(getattr(Image, "Resampling", Image), "NEAREST")
QUANTIZE_MEDIANCUT = getattr(getattr(Image, "Quantize", Image), "MEDIANCUT")

TRANSPARENT_MARKER = (255, 0, 255)  # palette slot 0 fill color (marker only)


def parse_size(text):
    try:
        w, h = text.lower().split("x")
        w, h = int(w), int(h)
        if w <= 0 or h <= 0:
            raise ValueError
        return w, h
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid size {text!r}, expected WxH e.g. 80x80")


def build_palette(opaque_pixels, n_colors):
    """Median-cut a pool of opaque RGB pixels down to n_colors entries.

    Returns a list of (r,g,b) tuples, length <= n_colors.
    """
    pool = Image.new("RGB", (len(opaque_pixels), 1))
    pool.putdata(opaque_pixels)
    q = pool.quantize(colors=n_colors, method=QUANTIZE_MEDIANCUT)
    raw = q.getpalette()[: 3 * n_colors]
    entries = [tuple(raw[i : i + 3]) for i in range(0, len(raw), 3)]
    # Median-cut can return duplicate trailing entries; keep unique, in order.
    seen, unique = set(), []
    for e in entries:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    return unique


def nearest_index(color, palette, cache):
    """Index (0-based within `palette`) of the nearest palette entry."""
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


def index_against_palette(img_rgba, opaque_palette, alpha_threshold):
    """Map an RGBA image onto [transparent] + opaque_palette.

    Returns a P-mode image whose index 0 is transparent and whose indices
    1..len(opaque_palette) are the given opaque colors.
    """
    w, h = img_rgba.size
    cache = {}
    indices = []
    for r, g, b, a in img_rgba.getdata():
        if a < alpha_threshold:
            indices.append(0)
        else:
            indices.append(1 + nearest_index((r, g, b), opaque_palette, cache))
    out = Image.new("P", (w, h))
    flat = list(TRANSPARENT_MARKER)
    for e in opaque_palette:
        flat.extend(e)
    flat.extend([0, 0, 0] * (256 - 1 - len(opaque_palette)))
    out.putpalette(flat)
    out.putdata(indices)
    return out


def quantize_file(src, dest, size, colors, alpha_threshold):
    img = Image.open(src).convert("RGBA")
    if size is not None:
        img = img.resize(size, RESAMPLE_NEAREST)

    opaque = [(r, g, b) for r, g, b, a in img.getdata() if a >= alpha_threshold]
    if not opaque:
        print(f"warning: {src} is fully transparent; writing all-index-0 output", file=sys.stderr)
        palette = []
    else:
        palette = build_palette(opaque, colors - 1)  # slot 0 is transparency

    out = index_against_palette(img, palette, alpha_threshold)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, transparency=0, optimize=False)
    used = 1 + len(palette)
    print(f"{src} -> {dest}  {out.size[0]}x{out.size[1]}, {used}/{colors} palette slots (index 0 = transparent)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="source PNG")
    ap.add_argument("-o", "--output", type=Path, required=True, help="output indexed PNG")
    ap.add_argument("--size", type=parse_size, default=None, metavar="WxH",
                    help="target dimensions, nearest-neighbor (e.g. 80x80); omit to keep source size")
    ap.add_argument("--colors", type=int, default=16,
                    help="total palette size including transparent index 0 (default 16)")
    ap.add_argument("--alpha-threshold", type=int, default=128,
                    help="alpha below this counts as transparent (default 128)")
    args = ap.parse_args()

    if not args.input.is_file():
        sys.exit(f"error: input file not found: {args.input}")
    if not 2 <= args.colors <= 256:
        sys.exit("error: --colors must be between 2 and 256")
    if args.size and (args.size[0] % 8 or args.size[1] % 8):
        print(f"warning: --size {args.size[0]}x{args.size[1]} is not a multiple of 8; "
              "Gen 4 graphics dimensions must be", file=sys.stderr)

    try:
        quantize_file(args.input, args.output, args.size, args.colors, args.alpha_threshold)
    except OSError as e:
        sys.exit(f"error: could not process {args.input}: {e}")


if __name__ == "__main__":
    main()
