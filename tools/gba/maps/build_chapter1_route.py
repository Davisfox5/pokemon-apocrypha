#!/usr/bin/env python3
"""Build the isolated Chapter 1 Route 29 / New Bark field-map draft.

The established Cherrygrove metatiles are reused; the owner's active Porymap
project and production game/ checkout are never touched by this builder.
"""
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GAME = ROOT / "tools/vendor/gba/opening-house-work"
LAYOUTS = GAME / "data/layouts"
MAPS = GAME / "data/maps"
REFERENCE = ROOT / "gba/art/chapter1-route/reference"


def read_grid(path, width):
    data = path.read_bytes()
    grid = list(struct.unpack("<" + "H" * (len(data) // 2), data))
    assert len(grid) % width == 0
    return grid, len(grid) // width


def save_grid(name, grid):
    folder = LAYOUTS / name
    folder.mkdir(exist_ok=True)
    (folder / "map.bin").write_bytes(struct.pack("<" + "H" * len(grid), *grid))
    (folder / "border.bin").write_bytes((LAYOUTS / "CherrygroveRoute29Approach" / "border.bin").read_bytes())


def put(grid, width, x, y, value):
    grid[y * width + x] = value


def main():
    old, height = read_grid(REFERENCE / "route29-approach.bin", 24)
    assert height == 48
    width = 72
    route = [old[y * 24 + (x if x < 24 else 12 + (x - 24) % 12)] for y in range(height) for x in range(width)]
    grass = 0x3000 | 0x202
    # Clear whole tree cells for a generous grass verge, avoiding clipped
    # crowns/trunks when the path crosses the existing forest pattern.
    for y in range(6, 33):
        for x in range(12, width):
            put(route, width, x, y, grass)
    for x0, x1, y0, y1 in ((28, 42, 9, 27), (48, 66, 9, 27)):
        for y in range(y0, y1):
            for x in range(x0, x1):
                put(route, width, x, y, grass)
    # The original approach joins Cherrygrove at y=17..19. Extend a three-row
    # walkable native path east, with clearings above and below it.
    for x in range(12, width):
        for y, source_y in ((17, 17), (18, 18), (19, 19)):
            put(route, width, x, y, old[source_y * 24 + 2])
    for x0, x1, y0, y1 in ((30, 38, 12, 16), (51, 62, 21, 25)):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if (x * 7 + y * 11) % 5 != 0:
                    put(route, width, x, y, 0x3000 | 0x376)
    for dst_x, dst_y in ((31, 23), (55, 11)):
        for dy in range(3):
            for dx in range(4):
                put(route, width, dst_x + dx, dst_y + dy, old[dy * 24 + dx])
    # Preserve the first 12 columns byte-for-byte where the town connection
    # and camera transition have already been qualified.
    assert all(route[y * width + x] == old[y * 24 + x] for y in range(height) for x in range(12))
    save_grid("CherrygroveRoute29Approach", route)

    town, town_h = read_grid(REFERENCE / "cherrygrove-town.bin", 80)
    assert town_h == 48
    nw, nh = 48, 36
    # Forest border uses the actual Johto tree sequence; the central campus is
    # native grass, paths and building metatiles from the same art family.
    new = [old[(y % 48) * 24 + (x % 24)] for y in range(nh) for x in range(nw)]
    for y in range(5, 31):
        for x in range(5, 43):
            put(new, nw, x, y, grass)
    # Native paths are directional metatiles: the top/bottom edges run along
    # rows, while a vertical branch uses separate left/right edge blocks.
    for x in range(0, 42):
        for y, tile in ((17, 0x31E), (18, 0x27C), (19, 0x325)):
            put(new, nw, x, y, 0x3000 | tile)
    for y in range(11, 18):
        for x, tile in ((26, 0x20B), (27, 0x20C), (28, 0x20C), (29, 0x20D)):
            put(new, nw, x, y, 0x3000 | tile)
    for y in range(17, 20):
        for x in range(26, 30):
            put(new, nw, x, y, 0x3000 | 0x20C)
    # Reception wing: an existing Johto blue-roof building. It is deliberately
    # modest in this first pass; later art can grow the institute footprint.
    for dy in range(5):
        for dx in range(7):
            put(new, nw, 25 + dx, 7 + dy, town[(5 + dy) * 80 + 49 + dx])
    # Research housing and a support office give the town a lived-in footprint.
    for dst_x, dst_y, src_x, src_y in ((10, 11, 41, 13), (35, 12, 52, 15)):
        for dy in range(6):
            for dx in range(7):
                put(new, nw, dst_x + dx, dst_y + dy, town[(src_y + dy) * 80 + src_x + dx])
    # Copy the town's native pond and a small planted court into the campus.
    for dy in range(5):
        for dx in range(5):
            put(new, nw, 6 + dx, 6 + dy, town[(5 + dy) * 80 + 64 + dx])
    for dy in range(4):
        for dx in range(6):
            put(new, nw, 34 + dx, 23 + dy, town[(12 + dy) * 80 + 62 + dx])
    for y in range(20, 24):
        for x, tile in ((35, 0x20B), (36, 0x20C), (37, 0x20D)):
            put(new, nw, x, y, 0x3000 | tile)
    # Two small shade groves frame the campus without touching roof planes.
    for dst_x, dst_y, src_x in ((13, 25, 72), (40, 27, 74)):
        for dy in range(3):
            for dx in range(4):
                put(new, nw, dst_x + dx, dst_y + dy, town[dy * 80 + src_x + dx])
    save_grid("NewBarkTown", new)

    layouts = LAYOUTS / "layouts.json"
    data = json.loads(layouts.read_text())
    assert isinstance(data, dict) and "layouts" in data
    if not any(x["id"] == "LAYOUT_NEW_BARK_TOWN" for x in data["layouts"]):
        data["layouts"].append({
            "id": "LAYOUT_NEW_BARK_TOWN", "name": "NewBarkTown_Layout",
            "width": nw, "height": nh,
            "primary_tileset": "gTileset_CherrygrovePrimary",
            "secondary_tileset": "gTileset_Cherrygrove",
            "border_filepath": "data/layouts/NewBarkTown/border.bin",
            "blockdata_filepath": "data/layouts/NewBarkTown/map.bin",
            "build_target": "emerald", "layout_version": "emerald",
        })
        layouts.write_text(json.dumps(data, indent=2) + "\n")
    print("Built isolated Route 29 and New Bark field layouts")


if __name__ == "__main__":
    main()
