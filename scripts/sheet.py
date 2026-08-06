#!/usr/bin/env python3
"""sheet.py — slice and assemble overworld sprite sheets by frame grid.

Overworld sprites are 32x32 per frame, laid out as sheets of directional
walk-cycle frames. This tool goes both ways:

  slice     cut a sheet into numbered frame PNGs (row-major order)
  assemble  paste numbered frame PNGs into a sheet on a fixed grid

Frames keep the sheet's palette when the sheet is indexed; when assembling,
all frames must share one mode/palette (run quantize.py or shared_palette.py
on the frames first if they do not).

Examples:
    python3 scripts/sheet.py slice sheet.png -o frames/ --frame 32x32
    python3 scripts/sheet.py assemble frames/*.png -o sheet.png --cols 4
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("error: Pillow is not installed. Run `make setup` (or: .venv/bin/pip install Pillow)")


def parse_size(text):
    try:
        w, h = text.lower().split("x")
        w, h = int(w), int(h)
        if w <= 0 or h <= 0:
            raise ValueError
        return w, h
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid size {text!r}, expected WxH e.g. 32x32")


def cmd_slice(args):
    if not args.input.is_file():
        sys.exit(f"error: input file not found: {args.input}")
    img = Image.open(args.input)
    fw, fh = args.frame
    w, h = img.size
    if w % fw or h % fh:
        sys.exit(f"error: sheet {w}x{h} is not an exact grid of {fw}x{fh} frames")

    cols, rows = w // fw, h // fh
    args.outdir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem
    n = 0
    for row in range(rows):
        for col in range(cols):
            frame = img.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))
            dest = args.outdir / f"{stem}_{n:03d}.png"
            save_kwargs = {}
            if img.mode == "P" and "transparency" in img.info:
                save_kwargs["transparency"] = img.info["transparency"]
            frame.save(dest, **save_kwargs)
            n += 1
    print(f"{args.input} ({cols}x{rows} grid) -> {n} frames in {args.outdir}/ ({stem}_000.png ...)")


def cmd_assemble(args):
    missing = [p for p in args.frames if not p.is_file()]
    if missing:
        sys.exit("error: frame file(s) not found: " + ", ".join(str(p) for p in missing))
    if not args.frames:
        sys.exit("error: no frames given")

    frames = [Image.open(p) for p in args.frames]
    fw, fh = frames[0].size
    mode = frames[0].mode
    palette = frames[0].getpalette() if mode == "P" else None
    for p, f in zip(args.frames, frames):
        if f.size != (fw, fh):
            sys.exit(f"error: {p} is {f.size[0]}x{f.size[1]}, expected {fw}x{fh} (all frames must match)")
        if f.mode != mode or (mode == "P" and f.getpalette() != palette):
            sys.exit(f"error: {p} has a different mode/palette than the first frame; "
                     "index all frames against one palette first (shared_palette.py)")

    cols = args.cols
    rows = -(-len(frames) // cols)  # ceil
    sheet = Image.new(mode, (cols * fw, rows * fh))
    if palette:
        sheet.putpalette(palette)
        # unused trailing cells stay index 0 (the transparent slot)
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % cols) * fw, (i // cols) * fh))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs = {}
    if mode == "P" and "transparency" in frames[0].info:
        save_kwargs["transparency"] = frames[0].info["transparency"]
    sheet.save(args.output, **save_kwargs)
    print(f"{len(frames)} frames -> {args.output}  {sheet.size[0]}x{sheet.size[1]} ({cols} cols x {rows} rows)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sl = sub.add_parser("slice", help="cut a sheet into numbered frames (row-major)")
    sl.add_argument("input", type=Path, help="sheet PNG")
    sl.add_argument("-o", "--outdir", type=Path, required=True, help="directory for frame PNGs")
    sl.add_argument("--frame", type=parse_size, default=(32, 32), metavar="WxH",
                    help="frame size (default 32x32)")
    sl.set_defaults(func=cmd_slice)

    asm = sub.add_parser("assemble", help="paste frames into a sheet on a grid")
    asm.add_argument("frames", type=Path, nargs="*", help="frame PNGs, in row-major order")
    asm.add_argument("-o", "--output", type=Path, required=True, help="output sheet PNG")
    asm.add_argument("--cols", type=int, required=True, help="number of columns in the grid")
    asm.set_defaults(func=cmd_assemble)

    args = ap.parse_args()
    if getattr(args, "cols", 1) is not None and getattr(args, "cols", 1) <= 0:
        sys.exit("error: --cols must be positive")
    args.func(args)


if __name__ == "__main__":
    main()
