#!/usr/bin/env python3
"""Insert a PNG frame strip into an HGSS overworld BTX0 mmodel member.

The strip must match the target model's unique-frame layout: same frame
size, one frame per unique texture data block, in ascending data-offset
order — exactly what extract_ow.py produces. Indexed PNGs keep their
palette (first 16 colors, index 0 transparent); RGBA input is accepted if
it uses <= 15 opaque colors.

Usage:
  insert_ow.py MMODEL_DIR strip.png --model N (-o OUT.bin | --in-place)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nitro

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: python3 -m pip install Pillow (or make setup)")


def strip_to_indexed(img):
    """-> (flat indices, palette[(r,g,b)]) with index 0 transparent."""
    if img.mode == "P":
        tr = img.info.get("transparency", 0)
        if tr != 0:
            sys.exit("indexed input must use palette index 0 as transparent")
        pal = img.getpalette()
        used = {i for i in img.getdata()}
        if max(used) > 15:
            sys.exit(f"strip uses palette index {max(used)}; only 0-15 fit 4bpp")
        colors = [tuple(pal[i * 3:i * 3 + 3]) for i in range(16)]
        return list(img.getdata()), colors
    rgba = img.convert("RGBA")
    opaque = sorted({p[:3] for p in rgba.getdata() if p[3] >= 128})
    if len(opaque) > 15:
        sys.exit(f"RGBA input has {len(opaque)} opaque colors; max 15 "
                 "(+ transparent). Quantize first (scripts/quantize.py).")
    colors = [(255, 0, 255)] + opaque + [(0, 0, 0)] * (15 - len(opaque))
    lut = {c: i + 1 for i, c in enumerate(opaque)}
    return [0 if p[3] < 128 else lut[p[:3]] for p in rgba.getdata()], colors


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mmodel_dir", help="files/data/mmodel/mmodel directory")
    ap.add_argument("png", help="frame strip (from extract_ow.py layout)")
    ap.add_argument("--model", type=int, required=True, help="target mmodel index")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-o", "--out", help="write the patched member here")
    g.add_argument("--in-place", action="store_true", help="overwrite the member")
    args = ap.parse_args()

    member = os.path.join(args.mmodel_dir, f"mmodel_{args.model:08d}.bin")
    for path in (member, args.png):
        if not os.path.isfile(path):
            sys.exit(f"missing input: {path}")
    with open(member, "rb") as f:
        blob = f.read()
    if blob[:4] != b"BTX0":
        sys.exit(f"mmodel {args.model} is not a BTX0 texture member")

    frames, texdata = nitro.btx_frames(blob)
    uniq = sorted({f[1]: f for f in frames}.values(), key=lambda f: f[1])
    fw, fh = uniq[0][2], uniq[0][3]

    img = Image.open(args.png)
    if img.size != (fw * len(uniq), fh):
        sys.exit(f"strip is {img.size[0]}x{img.size[1]}; model {args.model} "
                 f"needs {fw * len(uniq)}x{fh} ({len(uniq)} frames of {fw}x{fh})")
    indices, colors = strip_to_indexed(img)

    stride = fw * len(uniq)
    frame_pixels = {}
    for i, fr in enumerate(uniq):
        px = []
        for y in range(fh):
            row = indices[y * stride + i * fw: y * stride + i * fw + fw]
            px.extend(row)
        frame_pixels[fr[1]] = px
    patched = nitro.btx_replace(blob, frame_pixels, colors)

    # self-check: re-extract and compare
    rframes, rtex = nitro.btx_frames(patched)
    for fr in uniq:
        got = nitro.btx_pixels(patched, fr, rtex)
        if got != frame_pixels[fr[1]]:
            sys.exit("self-check failed: re-extracted pixels differ")

    out = member if args.in_place else args.out
    with open(out, "wb") as f:
        f.write(patched)
    print(f"wrote {out} ({len(uniq)} frames, {fw}x{fh})")


if __name__ == "__main__":
    main()
