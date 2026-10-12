#!/usr/bin/env python3
"""Add one native Route 29 tall-grass metatile without altering existing IDs."""
from pathlib import Path
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
REF = ROOT / "gba/art/chapter1-route/reference"
OUT = ROOT / "tools/vendor/gba/opening-house-work/data/tilesets/secondary/cherrygrove"

def main():
    original = REF / "cherrygrove-secondary-metatiles.bin"
    attrs = REF / "cherrygrove-secondary-attributes.bin"
    assert len(original.read_bytes()) // 16 == 374
    assert len(attrs.read_bytes()) // 2 == 374
    src = Image.open(ROOT / "tools/vendor/gba/opening-house-work/data/tilesets/primary/cherrygrove/tiles.png")
    sheet = Image.open(REF / "cherrygrove-secondary-tiles.png").copy()
    for i in range(4):
        base_id = 2 if i in (0, 3) else 3
        tile = src.crop((base_id * 8, 0, base_id * 8 + 8, 8)).copy()
        pix = tile.load()
        for offset in (1, 5):
            x = (offset + i) % 7
            y = 2 + (i + offset) % 3
            pix[x, y] = 3
            pix[x, y + 1] = 2
            pix[x + 1, y + 1] = 2
            pix[x + 1, y + 2] = 12
        tile_id = 1008 + i
        sheet.paste(tile, (((tile_id - 512) % 16) * 8, ((tile_id - 512) // 16) * 8))
    sheet.save(OUT / "tiles.png")
    entries = [0x2000 | (1008 + i) for i in range(4)] + [0, 0, 0, 0]
    (OUT / "metatiles.bin").write_bytes(original.read_bytes() + struct.pack("<8H", *entries))
    # MB_TALL_GRASS=1 with the same normal metatile layer as native grass.
    (OUT / "metatile_attributes.bin").write_bytes(attrs.read_bytes() + struct.pack("<H", 0x1001))
    print("Added Route 29 native tall grass at metatile 0x376")

if __name__ == "__main__":
    main()
