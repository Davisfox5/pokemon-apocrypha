#!/usr/bin/env python3
"""shared_palette.py — derive ONE palette for two or more images, re-index all.

The Platinum case this exists for: VS mugshots pull their palette from the
front-sprite NARC (/poketool/trgra/trfgra), NOT from field_encountereffect.
So a trainer's front sprite and mugshot must be indexed against the exact
same 16-color palette or one of them renders with the wrong colors in-game.

The palette is derived from the combined opaque pixels of all inputs
(median cut), with index 0 reserved for transparency. Each input is then
re-indexed against that shared palette and written as an indexed PNG.
Inputs are NOT resized — size them first (see quantize.py --size).

Example:
    python3 scripts/shared_palette.py front.png mugshot.png -o assets/out/trainers/front/
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("error: Pillow is not installed. Run `make setup` (or: .venv/bin/pip install Pillow)")

QUANTIZE_MEDIANCUT = getattr(getattr(Image, "Quantize", Image), "MEDIANCUT")
TRANSPARENT_MARKER = (255, 0, 255)


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


def reindex(img_rgba, palette, alpha_threshold, cache):
    indices = []
    for r, g, b, a in img_rgba.getdata():
        if a < alpha_threshold:
            indices.append(0)
        else:
            indices.append(1 + nearest_index((r, g, b), palette, cache))
    out = Image.new("P", img_rgba.size)
    flat = list(TRANSPARENT_MARKER)
    for e in palette:
        flat.extend(e)
    flat.extend([0, 0, 0] * (256 - 1 - len(palette)))
    out.putpalette(flat)
    out.putdata(indices)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", type=Path, nargs="+", help="two or more source PNGs")
    ap.add_argument("-o", "--outdir", type=Path, required=True,
                    help="output directory (files keep their basenames)")
    ap.add_argument("--colors", type=int, default=16,
                    help="total shared palette size including transparent index 0 (default 16)")
    ap.add_argument("--alpha-threshold", type=int, default=128,
                    help="alpha below this counts as transparent (default 128)")
    args = ap.parse_args()

    if len(args.inputs) < 2:
        sys.exit("error: need at least two images to share a palette (for one image use quantize.py)")
    missing = [p for p in args.inputs if not p.is_file()]
    if missing:
        sys.exit("error: input file(s) not found: " + ", ".join(str(p) for p in missing))
    if not 2 <= args.colors <= 256:
        sys.exit("error: --colors must be between 2 and 256")

    images = []
    pool = []
    for p in args.inputs:
        try:
            img = Image.open(p).convert("RGBA")
        except OSError as e:
            sys.exit(f"error: could not read {p}: {e}")
        images.append((p, img))
        pool.extend((r, g, b) for r, g, b, a in img.getdata() if a >= args.alpha_threshold)

    if not pool:
        sys.exit("error: all inputs are fully transparent; nothing to build a palette from")

    palette = build_palette(pool, args.colors - 1)
    print(f"shared palette: {1 + len(palette)}/{args.colors} slots "
          f"(index 0 = transparent, {len(palette)} opaque colors)")
    for i, (r, g, b) in enumerate(palette, start=1):
        print(f"  [{i:2d}] #{r:02x}{g:02x}{b:02x}")

    args.outdir.mkdir(parents=True, exist_ok=True)
    cache = {}
    for p, img in images:
        dest = args.outdir / p.name
        if dest.resolve() == p.resolve():
            sys.exit(f"error: output would overwrite input: {p} (choose a different --outdir)")
        reindex(img, palette, args.alpha_threshold, cache).save(dest, transparency=0)
        print(f"{p} -> {dest}")


if __name__ == "__main__":
    main()
