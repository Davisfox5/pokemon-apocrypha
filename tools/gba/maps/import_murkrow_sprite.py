#!/usr/bin/env python3
"""Adapt HGSS Murkrow follower art for Silver's Chapter 1 departure."""
from pathlib import Path
import hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "artwork-library/heartgold-johto/overworld-sprites/0498_follower_mon_murkrow.png"
GAME = ROOT / "tools/vendor/gba/opening-house-work"
ART = ROOT / "gba/art/chapter1-murkrow"
ORDER = (0, 2, 3, 2, 4, 5, 4, 1, 0, 6, 7, 6)

def main():
    source = Image.open(SOURCE).convert("RGBA")
    assert source.size == (32, 256)
    sheet = Image.new("RGBA", (32, 384))
    for i, frame in enumerate(ORDER):
        sheet.paste(source.crop((0, frame * 32, 32, (frame + 1) * 32)), (0, i * 32))
    colors = sorted({px[:3] for px in sheet.getdata() if px[3]})
    assert len(colors) <= 15
    palette = [(0, 0, 0)] + colors + [(0, 0, 0)] * (15 - len(colors))
    index = {color: i + 1 for i, color in enumerate(colors)}
    native = Image.new("P", sheet.size)
    native.putpalette([value for color in palette for value in color] + [0] * (768 - 48))
    native.putdata([index[px[:3]] if px[3] else 0 for px in sheet.getdata()])
    dest = GAME / "graphics/object_events/pics/people/johto/murkrow.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    native.save(dest, bits=4)
    (GAME / "graphics/object_events/palettes/johto_murkrow.pal").write_text(
        "JASC-PAL\n0100\n16\n" + "\n".join(" ".join(map(str, c)) for c in palette) + "\n"
    )
    ART.mkdir(parents=True, exist_ok=True)
    native.save(ART / "murkrow-native-12-frames.png", bits=4)
    (ART / "provenance.txt").write_text(
        f"HGSS source: {SOURCE.relative_to(ROOT)}\n"
        f"SHA-256: {hashlib.sha256(SOURCE.read_bytes()).hexdigest()}\n"
        f"Eight source frames repeated in order {ORDER} for the GBA 12-frame table.\n"
    )
    print("Imported Murkrow flight scene sprite")

if __name__ == "__main__":
    main()
