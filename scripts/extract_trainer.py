#!/usr/bin/env python3
"""extract_trainer.py — decode HGSS trainer battle sprites from a NARC to PNG.

Works on the trainer graphics NARCs of the local decomp tree:
    front sprites: disasm/pokeheartgold/files/a/0/5/8   (129 classes)
    backsprites:   disasm/pokeheartgold/files/a/0/0/6   (17 classes)

Each class decodes to an indexed PNG strip, one 80x80 frame per cell bank,
laid out horizontally (fronts are usually 1 frame; backs are 5 or 8).
With --aux, the auxiliary NCGR (2 extra VRAM-streamed animation frames)
is written alongside as <name>_aux.png.

The output round-trips: feeding these PNGs back through insert_trainer.py
reproduces the original NARC byte-for-byte.

Examples:
    python3 scripts/extract_trainer.py disasm/pokeheartgold/files/a/0/0/6 -o ref/backs --all
    python3 scripts/extract_trainer.py disasm/pokeheartgold/files/a/0/5/8 -o ref --cls 0 --aux
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "hoennconv"))

try:
    from PIL import Image
except ImportError:
    sys.exit("error: Pillow is not installed. Run `make setup` (or: .venv/bin/pip install Pillow)")

import nitro

try:
    import narc
except ImportError:
    sys.exit("error: tools/hoennconv/narc.py not found (expected in this repo)")


def pal_flat(pal):
    flat = []
    for r, g, b in pal[:16]:
        flat += [r, g, b]
    return flat + [0, 0, 0] * (256 - 16)


def frames_to_strip(frames, pal):
    strip = Image.new("P", (80 * len(frames), 80))
    strip.putpalette(pal_flat(pal))
    for i, pixels in enumerate(frames):
        f = Image.new("P", (80, 80))
        f.putpalette(pal_flat(pal))
        f.putdata(pixels)
        strip.paste(f, (i * 80, 0))
    return strip


def load_class_names(header):
    """Parse TRAINERCLASS_* defines from the decomp constants header."""
    import re
    names = {}
    for m in re.finditer(r"#define\s+TRAINERCLASS_(\w+)\s+(\d+)", header.read_text()):
        n = int(m.group(2))
        if n not in names:
            names[n] = m.group(1).lower()
    return names


def extract_class(members, cls, outdir, stem, want_aux, names=None):
    g1, palm, cellm, _anim, g2 = nitro.class_members(members, cls)
    pal = nitro.nclr_palette(palm)
    banks, shift, parts = nitro.ncer_banks(cellm)
    tiles = nitro.ncgr_tiles(g1)

    frames = [nitro.compose_frame(bank, tiles, shift, poff)
              for bank, (poff, _sz) in zip(banks, parts)]
    suffix = f"_{names[cls]}" if names and cls in names else ""
    dest = outdir / f"{stem}_c{cls:03d}{suffix}.png"
    frames_to_strip(frames, pal).save(dest, transparency=0)
    report = f"class {cls:3d}: {len(frames)} frame(s) -> {dest}"

    if want_aux:
        aux_tiles = nitro.ncgr_tiles(g2)
        n_aux = len(aux_tiles) // nitro.FRAME_BYTES
        # aux frames are VRAM-streamed over bank 0's cell layout
        aux = [nitro.compose_frame(banks[0], aux_tiles, shift, i * nitro.FRAME_BYTES)
               for i in range(n_aux)]
        aux_dest = outdir / f"{stem}_c{cls:03d}{suffix}_aux.png"
        frames_to_strip(aux, pal).save(aux_dest, transparency=0)
        report += f" (+{n_aux} aux frames -> {aux_dest})"
    print(report)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("narc", type=Path, help="trainer sprite NARC (e.g. disasm/pokeheartgold/files/a/0/5/8)")
    ap.add_argument("-o", "--outdir", type=Path, required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--cls", type=int, help="single class index to extract")
    group.add_argument("--all", action="store_true", help="extract every class")
    ap.add_argument("--aux", action="store_true", help="also write the 2 auxiliary animation frames")
    ap.add_argument("--names", type=Path, default=None,
                    help="decomp trainer_class.h to append class names to filenames")
    args = ap.parse_args()

    if not args.narc.is_file():
        sys.exit(f"error: NARC not found: {args.narc}")
    try:
        members = narc.parse(args.narc.read_bytes())
    except ValueError as e:
        sys.exit(f"error: {args.narc}: {e}")
    if len(members) % nitro.MEMBERS_PER_CLASS:
        sys.exit(f"error: {args.narc}: member count {len(members)} is not a multiple of "
                 f"{nitro.MEMBERS_PER_CLASS} — not a trainer sprite NARC?")

    args.outdir.mkdir(parents=True, exist_ok=True)
    # stem like "a0508" from .../a/0/5/8, else the file name
    tail = [p for p in args.narc.parts[-4:] if len(p) <= 2]
    stem = "".join(tail) if len(tail) >= 3 else args.narc.stem

    names = None
    if args.names:
        if not args.names.is_file():
            sys.exit(f"error: names header not found: {args.names}")
        names = load_class_names(args.names)

    classes = range(len(members) // nitro.MEMBERS_PER_CLASS) if args.all else [args.cls]
    for cls in classes:
        try:
            extract_class(members, cls, args.outdir, stem, args.aux, names)
        except ValueError as e:
            sys.exit(f"error: class {cls}: {e}")


if __name__ == "__main__":
    main()
