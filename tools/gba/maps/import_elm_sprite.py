#!/usr/bin/env python3
"""Import HGSS Elm's twelve native walking frames into the isolated GBA build."""
from pathlib import Path
import hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "artwork-library/heartgold-johto/overworld-sprites/0054_doctor.png"
GAME = ROOT / "tools/vendor/gba/opening-house-work"
ART = ROOT / "gba/art/chapter1-elm"

def main():
    src = Image.open(SOURCE).convert("RGBA")
    assert src.size == (32, 384)
    colors = sorted({px[:3] for px in src.getdata() if px[3]})
    assert len(colors) <= 15
    assert {px[3] for px in src.getdata()} <= {0, 255}
    palette = [(0, 0, 0)] + colors + [(0, 0, 0)] * (15 - len(colors))
    lookup = {color: i + 1 for i, color in enumerate(colors)}
    native = Image.new("P", src.size)
    native.putpalette([channel for color in palette for channel in color] + [0] * (768 - 48))
    native.putdata([lookup[px[:3]] if px[3] else 0 for px in src.getdata()])
    dest = GAME / "graphics/object_events/pics/people/johto/elm.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    native.save(dest, bits=4)
    pal = GAME / "graphics/object_events/palettes/johto_elm.pal"
    pal.write_text("JASC-PAL\n0100\n16\n" + "\n".join(" ".join(map(str, c)) for c in palette) + "\n")
    ART.mkdir(parents=True, exist_ok=True)
    native.save(ART / "elm-native-12-frames.png", bits=4)
    (ART / "provenance.txt").write_text(
        f"HGSS source: {SOURCE.relative_to(ROOT)}\n"
        f"SHA-256: {hashlib.sha256(SOURCE.read_bytes()).hexdigest()}\n"
        "Native frame size: 32x32; 12 vertical frames; 4bpp indexed.\n"
        "No generated redesign or frame omission.\n"
    )
    print("Imported Elm from the HGSS native walking strip")

if __name__ == "__main__":
    main()
