#!/usr/bin/env python3
"""insert_trainer.py — insert a custom trainer battle sprite into an HGSS NARC.

The native-macOS replacement for the DSPRE sprite-insertion step. Takes an
indexed PNG frame strip (as produced by the pipeline, or by
extract_trainer.py) and splices it into a trainer graphics NARC:

  - tile data is re-encoded into the class's NCGR through its NCER cell
    layout (per-frame char partitions),
  - the NCLR's first 16 colors are replaced with the PNG's palette,
  - the NCER / NANR members are left untouched, so frame count and timing
    must match the vanilla class being replaced.

Input requirements (validate.py budgets):
  - P-mode (indexed) PNG, index 0 = transparent, <= 16 colors used
  - horizontal strip of 80x80 frames; frame count must equal the target
    class's cell-bank count (fronts usually 1; backs 5 or 8 — check with
    extract_trainer.py first)
  - optional --aux strip: the 2 extra VRAM-streamed animation frames
    (vanilla aux frames are kept when omitted)

Safety: never modifies the input NARC in place unless --in-place is given;
writes to --output otherwise. Round-trip guarantee: inserting frames
extracted by extract_trainer.py reproduces the source NARC byte-for-byte.

Example:
    python3 scripts/insert_trainer.py disasm/pokeheartgold/files/a/0/5/8 \\
        --cls 12 assets/out/trainers/front/kestra.png -o /tmp/a0508.new
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


def load_strip(path, expected_frames, what):
    """PNG strip -> (list of per-frame index lists, palette[(r,g,b)*16])."""
    img = Image.open(path)
    if img.mode != "P":
        sys.exit(f"error: {path}: not an indexed PNG (mode {img.mode}); run it through quantize.py")
    w, h = img.size
    if h == 80 and w % 80 == 0:
        pass
    elif w == 80 and h % 80 == 0:  # vertical strip: rotate into horizontal handling
        frames_v = h // 80
        strip = Image.new("P", (80 * frames_v, 80))
        strip.putpalette(img.getpalette())
        for i in range(frames_v):
            strip.paste(img.crop((0, i * 80, 80, (i + 1) * 80)), (i * 80, 0))
        img = strip
        w, h = img.size
    else:
        sys.exit(f"error: {path}: size {w}x{h} is not a strip of 80x80 frames")
    frames = w // 80
    if frames != expected_frames:
        sys.exit(f"error: {path}: has {frames} frame(s) but the target {what} needs exactly "
                 f"{expected_frames} (cell/animation data is reused, not rebuilt)")

    used = {idx for _n, idx in (img.getcolors(65536) or [])}
    over = {i for i in used if i > 15}
    if over:
        sys.exit(f"error: {path}: uses palette indices above 15 ({sorted(over)}); "
                 "16-color budget including transparent index 0")

    raw = img.getpalette()
    pal = [tuple(raw[i * 3:i * 3 + 3]) for i in range(16)]
    data = list(img.getdata())
    per_frame = []
    for f in range(frames):
        px = [0] * (80 * 80)
        for y in range(80):
            row = y * w + f * 80
            px[y * 80:(y + 1) * 80] = data[row:row + 80]
        per_frame.append(px)
    return per_frame, pal


def encode_frames(per_frame, banks, shift, parts, tiles_len, keep_tiles):
    """-> new tile blob: each frame decomposed into its char partition."""
    out = bytearray(keep_tiles)
    for pixels, bank, (poff, psz) in zip(per_frame, banks, parts):
        psz = psz if psz is not None else tiles_len
        out[poff:poff + psz] = nitro.decompose_frame(
            pixels, bank, shift, psz, base=keep_tiles[poff:poff + psz])
    return bytes(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("narc", type=Path, help="trainer sprite NARC to modify")
    ap.add_argument("png", type=Path, help="indexed PNG frame strip (80x80 per frame)")
    ap.add_argument("--cls", type=int, required=True, help="target trainer class index")
    ap.add_argument("--aux", type=Path, default=None,
                    help="optional strip for the auxiliary animation NCGR (2 frames)")
    dest = ap.add_mutually_exclusive_group(required=True)
    dest.add_argument("-o", "--output", type=Path, help="write modified NARC here")
    dest.add_argument("--in-place", action="store_true", help="overwrite the input NARC")
    args = ap.parse_args()

    if not args.narc.is_file():
        sys.exit(f"error: NARC not found: {args.narc}")
    if not args.png.is_file():
        sys.exit(f"error: PNG not found: {args.png}")
    if args.aux and not args.aux.is_file():
        sys.exit(f"error: aux PNG not found: {args.aux}")

    original = args.narc.read_bytes()
    try:
        members = narc.parse(original)
        g1, palm, cellm, animm, g2 = nitro.class_members(members, args.cls)
        banks, shift, parts = nitro.ncer_banks(cellm)
    except ValueError as e:
        sys.exit(f"error: {e}")

    tiles = nitro.ncgr_tiles(g1)
    per_frame, pal = load_strip(args.png, len(banks), f"class {args.cls}")
    new_g1 = nitro.ncgr_replace(g1, encode_frames(per_frame, banks, shift, parts, len(tiles), tiles))
    new_pal = nitro.nclr_replace(palm, pal)

    new_g2 = g2
    if args.aux:
        aux_tiles = nitro.ncgr_tiles(g2)
        n_aux = len(aux_tiles) // nitro.FRAME_BYTES
        aux_frames, _aux_pal = load_strip(args.aux, n_aux, "aux NCGR")
        aux_parts = [(i * nitro.FRAME_BYTES, nitro.FRAME_BYTES) for i in range(n_aux)]
        new_g2 = nitro.ncgr_replace(
            g2, encode_frames(aux_frames, [banks[0]] * n_aux, shift, aux_parts, len(aux_tiles), aux_tiles))
    else:
        print("note: aux animation NCGR kept from vanilla (pass --aux to replace its 2 frames)")

    base = args.cls * nitro.MEMBERS_PER_CLASS
    members[base + 0] = new_g1
    members[base + 1] = new_pal
    members[base + 4] = new_g2

    rebuilt = narc.build(members)
    # sanity: untouched classes must survive a parse round-trip
    check = narc.parse(rebuilt)
    if len(check) != len(members) or any(check[i] != members[i] for i in range(len(members))):
        sys.exit("error: NARC rebuild self-check failed; refusing to write")

    out = args.narc if args.in_place else args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(rebuilt)
    changed = "g1+pal+aux" if args.aux else "g1+pal"
    print(f"class {args.cls}: {len(banks)} frame(s) inserted ({changed}) -> {out} "
          f"({len(rebuilt)} bytes; was {len(original)})")


if __name__ == "__main__":
    main()
