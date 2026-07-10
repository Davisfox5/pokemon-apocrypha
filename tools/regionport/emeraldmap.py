#!/usr/bin/env python3
"""emeraldmap.py - parse pokeemerald map data into images + walkability grids.

Formats per pret pokeemerald (include/global.fieldmap.h, include/fieldmap.h):
  map.bin   : width*height u16 LE, row-major. bits 0-9 metatile id, 10-11 collision,
              12-15 elevation.
  metatiles.bin          : 8 u16 per metatile (bottom layer 4 subtiles, top layer 4),
              subtile u16 = bits 0-9 tile id, 10 hflip, 11 vflip, 12-15 palette.
  metatile_attributes.bin: u16 per metatile, bits 0-7 behavior (MB_*).
  tiles.png : 4bpp indexed strip of 8x8 tiles, 16 tiles per row.
  palettes/NN.pal        : JASC-PAL text, 16 colors.
Primary tileset owns metatiles/tiles 0..511 and palettes 0..5; secondary owns
512..1023 and palettes 6..12.

Usage:
  emeraldmap.py render  <MAP_ID>            -> PNG + grid json in --out dir
  emeraldmap.py stitch  <MAP_ID> [...]      -> stitched world PNG + grid via connections
"""
import json
import os
import struct
import sys
from functools import lru_cache

from PIL import Image

EMERALD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "..", "disasm", "pokeemerald")
EMERALD = os.path.normpath(EMERALD)

NUM_TILES_PRIMARY = 512
NUM_METATILES_PRIMARY = 512
NUM_PALS_PRIMARY = 6
NUM_PALS_TOTAL = 13

WATER_BEHAVIORS = set(range(0x10, 0x1B)) | {0x13, 0x50, 0x51, 0x52, 0x53}
GRASS_BEHAVIORS = {0x02, 0x03, 0x09, 0x24}
IMPASSABLE_BEHAVIORS = set(range(0x30, 0x38)) | {0x01}
LEDGE_BEHAVIORS = set(range(0x38, 0x40))


def tileset_dir(label):
    # gTileset_General -> general; gTileset_PetalburgGym -> petalburg_gym
    name = label[len("gTileset_"):]
    snake = "".join(("_" + c.lower()) if c.isupper() else c for c in name).lstrip("_")
    for kind in ("primary", "secondary"):
        d = os.path.join(EMERALD, "data/tilesets", kind, snake)
        if os.path.isdir(d):
            return kind, d
    raise FileNotFoundError(f"tileset dir for {label} ({snake})")


@lru_cache(maxsize=None)
def load_layouts():
    with open(os.path.join(EMERALD, "data/layouts/layouts.json")) as f:
        data = json.load(f)
    return {l["id"]: l for l in data["layouts"] if l}


@lru_cache(maxsize=None)
def map_json_index():
    idx = {}
    maps_dir = os.path.join(EMERALD, "data/maps")
    for name in os.listdir(maps_dir):
        p = os.path.join(maps_dir, name, "map.json")
        if os.path.isfile(p):
            with open(p) as f:
                j = json.load(f)
            idx[j["id"]] = j
    return idx


@lru_cache(maxsize=None)
def load_tileset(label):
    """Return (metatiles: list[8 u16], attrs: list[u16], tiles_img, palettes)."""
    kind, d = tileset_dir(label)
    with open(os.path.join(d, "metatiles.bin"), "rb") as f:
        mt_raw = f.read()
    metatiles = [struct.unpack_from("<8H", mt_raw, i * 16) for i in range(len(mt_raw) // 16)]
    with open(os.path.join(d, "metatile_attributes.bin"), "rb") as f:
        at_raw = f.read()
    attrs = list(struct.unpack(f"<{len(at_raw)//2}H", at_raw))
    tiles = Image.open(os.path.join(d, "tiles.png")).convert("P")
    pals = []
    for i in range(16):
        p = os.path.join(d, "palettes", f"{i:02}.pal")
        pals.append(load_jasc_pal(p) if os.path.isfile(p) else [(0, 0, 0)] * 16)
    return metatiles, attrs, tiles, pals


def load_jasc_pal(path):
    with open(path) as f:
        lines = [l.strip() for l in f if l.strip()]
    assert lines[0] == "JASC-PAL"
    n = int(lines[2])
    return [tuple(int(v) for v in lines[3 + i].split()) for i in range(n)]


@lru_cache(maxsize=None)
def tile_pixels(label, local_tile_id):
    """8x8 palette-index rows for a tile out of tiles.png (16 tiles per row)."""
    _, _, tiles, _ = load_tileset(label)
    tx, ty = (local_tile_id % 16) * 8, (local_tile_id // 16) * 8
    if ty + 8 > tiles.height:
        return [[0] * 8 for _ in range(8)]
    region = tiles.crop((tx, ty, tx + 8, ty + 8))
    data = list(region.getdata())
    return [data[r * 8:(r + 1) * 8] for r in range(8)]


class MapData:
    def __init__(self, map_id):
        self.map_id = map_id
        self.json = map_json_index()[map_id]
        self.layout = load_layouts()[self.json["layout"]]
        self.w, self.h = self.layout["width"], self.layout["height"]
        blockdata = os.path.join(EMERALD, self.layout["blockdata_filepath"])
        with open(blockdata, "rb") as f:
            raw = f.read()
        self.blocks = struct.unpack(f"<{self.w*self.h}H", raw[: self.w * self.h * 2])
        self.primary = self.layout["primary_tileset"]
        self.secondary = self.layout["secondary_tileset"]

    def metatile_def(self, mt_id):
        if mt_id < NUM_METATILES_PRIMARY:
            label, idx = self.primary, mt_id
        else:
            label, idx = self.secondary, mt_id - NUM_METATILES_PRIMARY
        metatiles, attrs, _, _ = load_tileset(label)
        if idx >= len(metatiles):
            return None, 0
        return metatiles[idx], (attrs[idx] & 0xFF) if idx < len(attrs) else 0

    def metatile_info(self, mt_id):
        """(mdef, behavior, layer_type, owner_tileset_short) — the full
        attribute word (behavior lo byte, layer bits 12-15) plus which
        tileset owns the metatile ('general', 'slateport', ...)."""
        if mt_id < NUM_METATILES_PRIMARY:
            label, idx = self.primary, mt_id
        else:
            label, idx = self.secondary, mt_id - NUM_METATILES_PRIMARY
        metatiles, attrs, _, _ = load_tileset(label)
        name = label[len("gTileset_"):]
        short = "".join(("_" + c.lower()) if c.isupper() else c
                        for c in name).lstrip("_")
        if idx >= len(metatiles):
            return None, 0, 0, short
        a = attrs[idx] if idx < len(attrs) else 0
        return metatiles[idx], a & 0xFF, (a >> 12) & 0xF, short

    def palettes(self):
        """Combined 13-slot palette bank: primary 0-5, secondary 6-12."""
        _, _, _, ppals = load_tileset(self.primary)
        _, _, _, spals = load_tileset(self.secondary)
        return ppals[:NUM_PALS_PRIMARY] + spals[NUM_PALS_PRIMARY:NUM_PALS_TOTAL]

    def subtile_pixels(self, tile_id):
        if tile_id < NUM_TILES_PRIMARY:
            return tile_pixels(self.primary, tile_id)
        return tile_pixels(self.secondary, tile_id - NUM_TILES_PRIMARY)

    def render(self):
        img = Image.new("RGB", (self.w * 16, self.h * 16), (0, 0, 0))
        px = img.load()
        pals = self.palettes()
        for ty in range(self.h):
            for tx in range(self.w):
                mt_id = self.blocks[ty * self.w + tx] & 0x3FF
                mdef, _ = self.metatile_def(mt_id)
                if mdef is None:
                    continue
                for layer in range(2):
                    for sub in range(4):
                        v = mdef[layer * 4 + sub]
                        tid, hf, vf, pal = v & 0x3FF, v & 0x400, v & 0x800, (v >> 12) & 0xF
                        rows = self.subtile_pixels(tid)
                        colors = pals[pal] if pal < len(pals) else [(0, 0, 0)] * 16
                        ox = tx * 16 + (sub % 2) * 8
                        oy = ty * 16 + (sub // 2) * 8
                        for ry in range(8):
                            srow = rows[7 - ry] if vf else rows[ry]
                            for rx in range(8):
                                ci = srow[7 - rx] if hf else srow[rx]
                                if layer == 1 and ci == 0:
                                    continue
                                c = colors[ci] if ci < len(colors) else (0, 0, 0)
                                px[ox + rx, oy + ry] = c
        return img

    def classify(self):
        """Per tile: '#'=blocked, '.'=walk, '~'=water, ','=grass, 'v'=ledge, 'D'=door."""
        grid = []
        for ty in range(self.h):
            row = []
            for tx in range(self.w):
                v = self.blocks[ty * self.w + tx]
                mt_id, coll = v & 0x3FF, (v >> 10) & 3
                _, beh = self.metatile_def(mt_id)
                if 0x60 <= beh <= 0x73:
                    ch = "D"
                elif beh in WATER_BEHAVIORS:
                    ch = "~"
                elif coll != 0 or beh in IMPASSABLE_BEHAVIORS:
                    ch = "#"
                elif beh in LEDGE_BEHAVIORS:
                    ch = "v"
                elif beh in GRASS_BEHAVIORS:
                    ch = ","
                else:
                    ch = "."
                row.append(ch)
            grid.append("".join(row))
        return grid


def stitch(map_ids):
    """Place maps on a shared tile grid using connection offsets (BFS from first)."""
    follow_all = map_ids[1:] == ["ALL"]
    placed = {map_ids[0]: (0, 0)}
    queue = [map_ids[0]]
    want = set(map_ids)
    maps = {}
    while queue:
        mid = queue.pop(0)
        m = maps.setdefault(mid, MapData(mid))
        ox, oy = placed[mid]
        for c in m.json.get("connections") or []:
            nid, off, d = c["map"], c["offset"], c["direction"]
            if d == "dive" or d == "emerge":
                continue
            if (not follow_all and nid not in want) or nid in placed:
                continue
            n = maps.setdefault(nid, MapData(nid))
            if d == "up":
                placed[nid] = (ox + off, oy - n.h)
            elif d == "down":
                placed[nid] = (ox + off, oy + m.h)
            elif d == "left":
                placed[nid] = (ox - n.w, oy + off)
            elif d == "right":
                placed[nid] = (ox + m.w, oy + off)
            else:
                continue
            queue.append(nid)
    missing = set() if follow_all else want - set(placed)
    if missing:
        raise SystemExit(f"not connected to {map_ids[0]}: {sorted(missing)}")
    minx = min(x for x, _ in placed.values())
    miny = min(y for _, y in placed.values())
    maxx = max(placed[m][0] + maps[m].w for m in placed)
    maxy = max(placed[m][1] + maps[m].h for m in placed)
    W, H = maxx - minx, maxy - miny
    img = Image.new("RGB", (W * 16, H * 16), (0, 0, 0))
    grid = [["#"] * W for _ in range(H)]
    origins = {}
    for mid, (x, y) in placed.items():
        m = maps[mid]
        gx, gy = x - minx, y - miny
        origins[mid] = [gx, gy, m.w, m.h]
        img.paste(m.render(), (gx * 16, gy * 16))
        for r, rowstr in enumerate(m.classify()):
            for cidx, ch in enumerate(rowstr):
                grid[gy + r][gx + cidx] = ch
    return img, ["".join(r) for r in grid], origins


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, ids = sys.argv[1], sys.argv[2:]
    out_dir = os.environ.get("OUT", ".")
    os.makedirs(out_dir, exist_ok=True)
    if cmd == "render":
        m = MapData(ids[0])
        m.render().save(os.path.join(out_dir, f"{ids[0]}.png"))
        meta = {"id": ids[0], "w": m.w, "h": m.h, "grid": m.classify(),
                "warps": m.json.get("warp_events", []),
                "connections": m.json.get("connections") or []}
        with open(os.path.join(out_dir, f"{ids[0]}.json"), "w") as f:
            json.dump(meta, f, indent=1)
        print(f"{ids[0]}: {m.w}x{m.h} -> {out_dir}")
    elif cmd == "stitch":
        img, grid, origins = stitch(ids)
        img.save(os.path.join(out_dir, "hoenn_stitch.png"))
        with open(os.path.join(out_dir, "hoenn_stitch.json"), "w") as f:
            json.dump({"grid": grid, "origins": origins}, f, indent=1)
        print(f"stitched {len(origins)} maps: {len(grid[0])}x{len(grid)} tiles -> {out_dir}")
    else:
        sys.exit(f"unknown cmd {cmd}")


if __name__ == "__main__":
    main()
