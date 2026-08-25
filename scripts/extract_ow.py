#!/usr/bin/env python3
"""Extract HGSS overworld NPC sprites (BTX0 mmodel members) to PNG strips.

Each overworld model is one BTX0 file in files/data/mmodel/mmodel/
(mmodel_%08d.bin). NPC walkers carry 16 texture slots sharing 12 unique
32x32 4bpp frames and one 16-color palette. The strip written here holds
the UNIQUE frames in ascending data-offset order — the same order
insert_ow.py expects back. Index 0 is transparent.

Usage:
  extract_ow.py MMODEL_DIR --model N -o OUT_DIR [--names mmodel.h]
  extract_ow.py MMODEL_DIR --all     -o OUT_DIR [--names mmodel.h]
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nitro

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: python3 -m pip install Pillow (or make setup)")


def load_names(path):
    """MMODEL_* constants -> {index: lowercase name} from constants/mmodel.h."""
    names = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"#define\s+MMODEL_(\w+)\s+(\d+)", line)
                if m:
                    names[int(m.group(2))] = m.group(1).lower()
    except OSError as e:
        print(f"warning: cannot read names file: {e}", file=sys.stderr)
    return names


def extract_model(mmodel_dir, idx, out_dir, names):
    path = os.path.join(mmodel_dir, f"mmodel_{idx:08d}.bin")
    if not os.path.isfile(path):
        return f"mmodel {idx}: no such member ({path})"
    with open(path, "rb") as f:
        blob = f.read()
    if blob[:4] != b"BTX0":
        return f"mmodel {idx}: not a BTX0 (probably an NSBMD prop model) — skipped"
    try:
        frames, texdata = nitro.btx_frames(blob)
        pal = nitro.btx_palette(blob)
    except ValueError as e:
        return f"mmodel {idx}: {e}"
    if not frames:
        return f"mmodel {idx}: no 4bpp textures — skipped"
    uniq = sorted({f[1]: f for f in frames}.values(), key=lambda f: f[1])
    w, h = uniq[0][2], uniq[0][3]
    strip = Image.new("P", (w * len(uniq), h))
    strip.putpalette(sum(([r, g, b] for r, g, b in pal), []) + [0, 0, 0] * (256 - len(pal)) * 1)
    for i, fr in enumerate(uniq):
        px = nitro.btx_pixels(blob, fr, texdata)
        tile = Image.new("P", (fr[2], fr[3]))
        tile.putdata(px)
        strip.paste(tile, (i * w, 0))
    suffix = f"_{names[idx]}" if idx in names else ""
    out = os.path.join(out_dir, f"mmodel_{idx:03d}{suffix}.png")
    strip.save(out, transparency=0)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mmodel_dir", help="files/data/mmodel/mmodel directory")
    ap.add_argument("-o", "--out", required=True, help="output directory")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--model", type=int, help="mmodel index to extract")
    g.add_argument("--all", action="store_true", help="extract every BTX0 member")
    ap.add_argument("--names", help="path to constants/mmodel.h for named files")
    args = ap.parse_args()

    if not os.path.isdir(args.mmodel_dir):
        sys.exit(f"missing input: {args.mmodel_dir} is not a directory")
    os.makedirs(args.out, exist_ok=True)
    names = load_names(args.names) if args.names else {}

    if args.model is not None:
        indices = [args.model]
    else:
        indices = sorted(int(m.group(1)) for f in os.listdir(args.mmodel_dir)
                         if (m := re.match(r"mmodel_(\d{8})\.bin$", f)))
    done = 0
    for idx in indices:
        err = extract_model(args.mmodel_dir, idx, args.out, names)
        if err:
            print(err, file=sys.stderr)
        else:
            done += 1
    print(f"extracted {done}/{len(indices)} model(s) -> {args.out}")
    if done == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
