#!/usr/bin/env python3
"""pokeemerald (Gen-3 GBA) map/tileset readers for the Hoenn -> HGSS port.

Everything is read from the decomp working tree, with formats taken from the
decomp's own headers:
  include/global.fieldmap.h : MAPGRID_* masks (map.bin cell packing) and
                              METATILE_ATTR_* masks (metatile_attributes.bin)
  include/fieldmap.h        : NUM_TILES_IN_PRIMARY=512, NUM_METATILES_IN_PRIMARY=512,
                              NUM_PALS_IN_PRIMARY=6
  include/constants/metatile_behaviors.h : MB_* enum (implicit values, in order)

A map.bin cell is u16 LE: bits 0-9 metatile id, 10-11 collision, 12-15 elevation.
A metatile is 8 u16s (bottom layer 4 tiles then top layer 4 tiles); each tile
ref is u16: bits 0-9 tile index, 10 xflip, 11 yflip, 12-15 palette.
"""

from __future__ import annotations

import json
import re
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

EMERALD = Path(__file__).resolve().parents[2] / "disasm" / "pokeemerald"

NUM_TILES_IN_PRIMARY = 512
NUM_METATILES_IN_PRIMARY = 512
NUM_PALS_IN_PRIMARY = 6

MAPGRID_METATILE_MASK = 0x03FF
MAPGRID_COLLISION_SHIFT = 10
MAPGRID_COLLISION_MASK = 0x3
MAPGRID_ELEVATION_SHIFT = 12


# --------------------------------------------------------------------------- #
#  metatile behaviors (MB_* enum -> value, value -> name)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def behaviors() -> dict[int, str]:
    text = (EMERALD / "include/constants/metatile_behaviors.h").read_text()
    body = text[text.index("enum"):]
    out: dict[int, str] = {}
    val = 0
    for m in re.finditer(r"^\s*(MB_\w+)(?:\s*=\s*(\d+))?\s*,", body, re.M):
        if m.group(2):
            val = int(m.group(2))
        out[val] = m.group(1)
        val += 1
    return out


# --------------------------------------------------------------------------- #
#  layouts
# --------------------------------------------------------------------------- #
@dataclass
class Layout:
    id: str
    width: int          # in metatiles
    height: int
    primary_tileset: str
    secondary_tileset: str
    blockdata: list[int]    # u16 per cell, row-major

    def metatile(self, x: int, y: int) -> int:
        return self.blockdata[y * self.width + x] & MAPGRID_METATILE_MASK

    def collision(self, x: int, y: int) -> int:
        return (self.blockdata[y * self.width + x] >> MAPGRID_COLLISION_SHIFT) & MAPGRID_COLLISION_MASK

    def elevation(self, x: int, y: int) -> int:
        return self.blockdata[y * self.width + x] >> MAPGRID_ELEVATION_SHIFT


@lru_cache(maxsize=1)
def layouts() -> dict[str, dict]:
    j = json.loads((EMERALD / "data/layouts/layouts.json").read_text())
    return {l["id"]: l for l in j["layouts"] if l and "id" in l}


def load_layout(layout_id: str) -> Layout:
    l = layouts()[layout_id]
    raw = (EMERALD / l["blockdata_filepath"]).read_bytes()
    n = l["width"] * l["height"]
    blockdata = list(struct.unpack(f"<{n}H", raw[:n * 2]))
    return Layout(layout_id, l["width"], l["height"],
                  l["primary_tileset"], l["secondary_tileset"], blockdata)


# --------------------------------------------------------------------------- #
#  maps (headers + events + connections)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def maps() -> dict[str, dict]:
    """MAP_* id -> map.json contents for every map in the tree."""
    out = {}
    for p in (EMERALD / "data/maps").iterdir():
        f = p / "map.json"
        if f.exists():
            j = json.loads(f.read_text())
            out[j["id"]] = j
    return out


# --------------------------------------------------------------------------- #
#  tilesets -> RGBA metatile images
# --------------------------------------------------------------------------- #
def _tileset_dir(label: str) -> Path:
    # gTileset_General -> general; gTileset_BattleFrontierOutsideWest ->
    # battle_frontier_outside_west (snake_case, matching the repo layout)
    name = label.removeprefix("gTileset_")
    snake = re.sub(r"(?<!^)(?=[A-Z0-9])", "_", name).lower().replace("__", "_")
    for kind in ("primary", "secondary"):
        d = EMERALD / "data/tilesets" / kind / snake
        if d.exists():
            return d
    raise FileNotFoundError(f"tileset dir for {label} ({snake})")


def _load_pal(path: Path) -> list[tuple[int, int, int]]:
    lines = path.read_text().splitlines()
    assert lines[0].strip() == "JASC-PAL"
    n = int(lines[2])
    return [tuple(int(c) for c in ln.split()) for ln in lines[3:3 + n]]


class TilesetPair:
    """Composed primary+secondary tileset: renders any metatile to RGBA."""

    def __init__(self, primary_label: str, secondary_label: str):
        from PIL import Image

        self.labels = (primary_label, secondary_label)
        pdir, sdir = _tileset_dir(primary_label), _tileset_dir(secondary_label)

        def tile_pixels(d: Path) -> list[bytes]:
            im = Image.open(d / "tiles.png").convert("P")
            w, h = im.size
            raw = im.tobytes()  # 1 byte per pixel (palette index)
            tiles = []
            for ty in range(h // 8):
                for tx in range(w // 8):
                    t = bytearray()
                    for r in range(8):
                        o = (ty * 8 + r) * w + tx * 8
                        t += raw[o:o + 8]
                    tiles.append(bytes(t))
            return tiles

        ptiles, stiles = tile_pixels(pdir), tile_pixels(sdir)
        self.tiles: list[bytes] = (ptiles + [bytes(64)] * NUM_TILES_IN_PRIMARY)[:NUM_TILES_IN_PRIMARY]
        self.tiles += stiles

        def pals(d: Path) -> list[list[tuple[int, int, int]]]:
            return [_load_pal(d / "palettes" / f"{i:02}.pal") for i in range(16)]

        ppals, spals = pals(pdir), pals(sdir)
        self.palettes = ppals[:NUM_PALS_IN_PRIMARY] + spals[NUM_PALS_IN_PRIMARY:]

        def metas(d: Path) -> list[tuple[int, ...]]:
            raw = (d / "metatiles.bin").read_bytes()
            return [struct.unpack_from("<8H", raw, i) for i in range(0, len(raw), 16)]

        self.metatiles = metas(pdir)
        self.metatiles_secondary = metas(sdir)

        def attrs(d: Path) -> list[int]:
            raw = (d / "metatile_attributes.bin").read_bytes()
            return list(struct.unpack(f"<{len(raw)//2}H", raw))

        self.attrs = attrs(pdir)
        self.attrs_secondary = attrs(sdir)

    # -- lookups ------------------------------------------------------- #
    def metatile_def(self, mt: int) -> tuple[int, ...]:
        if mt < NUM_METATILES_IN_PRIMARY:
            return self.metatiles[mt] if mt < len(self.metatiles) else (0,) * 8
        i = mt - NUM_METATILES_IN_PRIMARY
        return self.metatiles_secondary[i] if i < len(self.metatiles_secondary) else (0,) * 8

    def behavior(self, mt: int) -> int:
        if mt < NUM_METATILES_IN_PRIMARY:
            a = self.attrs[mt] if mt < len(self.attrs) else 0
        else:
            i = mt - NUM_METATILES_IN_PRIMARY
            a = self.attrs_secondary[i] if i < len(self.attrs_secondary) else 0
        return a & 0x00FF

    # -- rendering ------------------------------------------------------ #
    def render_metatile(self, mt: int, layers: tuple[int, ...] = (0, 1)):
        """16x16 RGBA PIL image of a metatile.

        layers selects which of the two 4-tile planes to draw: (0, 1) is the
        full composite, (1,) is layer B alone (roof/wall art with transparent
        background — see buildings.py), (0,) is layer A alone. Palette index
        0 is transparent on every layer except a solo layer 0 full render's
        base, so cutouts stay clean.
        """
        from PIL import Image

        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        px = img.load()
        tdef = self.metatile_def(mt)
        for layer in layers:
            for q in range(4):
                ref = tdef[layer * 4 + q]
                tile = ref & 0x03FF
                xf, yf = ref & 0x0400, ref & 0x0800
                pal = self.palettes[(ref >> 12) & 0xF]
                data = self.tiles[tile] if tile < len(self.tiles) else bytes(64)
                ox, oy = (q & 1) * 8, (q >> 1) * 8
                for r in range(8):
                    for c in range(8):
                        idx = data[(7 - r if yf else r) * 8 + (7 - c if xf else c)]
                        if idx == 0 and layer == 1:
                            continue          # top layer: index 0 transparent
                        if idx >= len(pal):
                            continue
                        col = pal[idx]
                        px[ox + c, oy + r] = (col[0], col[1], col[2], 255)
        return img
