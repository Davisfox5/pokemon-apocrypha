#!/usr/bin/env python3
"""Littleroot Town 3-D pilot.

Produces converted/hoenn/pilot_littleroot/:
  models/hoenn_house.nsbmd   wk_hhouse (bm_field 20) with palettes remapped
                             to Littleroot's tan roof / blue-grey walls
  models/hoenn_lab.nsbmd     wk_labo (bm_field 21) remapped to the lab's
                             olive roof / grey walls
  preview/models_before_after.png   donor vs retextured texture sheets
  preview/ground_c*.png      ground textures for Littleroot's two chunks
                             with building footprints filled with terrain
  placements.json            the three 48-byte building entries (and their
                             decoded fields) for the two chunks
  land_data/                 the two Littleroot chunk .bin files with the
                             building entries patched in (models 340/341)

Palette remap: luminance-quantile mapping onto a hand-picked Littleroot
color ramp per palette. Keeps every texel and all shading structure; only
the palette colors move. Window/shadow textures (h_mado/h_kage) untouched.

Building entry layout (48 bytes, verified against vanilla chunk dumps and
DSPRE): u32 modelId, fx32 x, fx32 y, fx32 z (relative to the chunk center,
1.0 = one tile), then rotation/scale words vanilla leaves mostly zero — we
copy them from a vanilla placement of the same donor model.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mapeditor"))

import gba
import narc
import stitch
from hgss_map import MapChunk
from nsbtx import Tex0

ROOT = Path(__file__).resolve().parents[2]
HG = ROOT / "disasm" / "pokeheartgold"
OUT = ROOT / "converted" / "hoenn" / "pilot_littleroot"
CHUNKS = ROOT / "converted" / "hoenn" / "land_data"

HOUSE_DONOR, LAB_DONOR = 20, 21           # wk_hhouse, wk_labo
HOUSE_ID, LAB_ID = 340, 341               # appended after vanilla 0..339

# Littleroot color ramps (dark -> light), sampled from the extracted cutouts.
# Donor atlases mix roof/walls/door in one palette, so colors are remapped
# by hue class: browns -> roof ramp, neutrals -> wall ramp, teal -> door.
HOUSE_CLASSES = {
    # orange shingles
    "roof": [(140, 70, 40), (190, 105, 45), (225, 145, 65), (240, 185, 110)],
    # cream stone walls, dark blue-grey timber/eaves at the dark end
    "wall": [(48, 56, 88), (120, 110, 90), (190, 180, 140), (225, 218, 182)],
    # brown door
    "door": [(90, 60, 40), (139, 90, 55), (180, 130, 90)],
}
LAB_CLASSES = {
    # olive-green tiled roof
    "roof": [(105, 110, 70), (140, 148, 95), (170, 178, 115), (195, 195, 135)],
    # cream speckled walls
    "wall": [(60, 66, 95), (150, 145, 105), (200, 195, 150), (228, 222, 180)],
    # green door + window frames
    "door": [(50, 100, 55), (85, 150, 75), (130, 195, 105)],
}


def _classify(c) -> str:
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*[x / 255 for x in c])
    deg = h * 360
    if s < 0.16:
        return "wall"
    if 10 <= deg <= 62:
        return "roof"
    if 140 <= deg <= 215:
        return "door"
    return "wall"


def _ramp_at(ramp, t: float):
    t = min(max(t, 0.0), 1.0) * (len(ramp) - 1)
    a, b = ramp[int(t)], ramp[min(int(t) + 1, len(ramp) - 1)]
    f = t - int(t)
    return tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))


def remap_palette(tex: Tex0, name: str, classes: dict) -> None:
    import colorsys
    pal = next(p for p in tex.palettes if p.name == name)
    colors = tex.palette_colors(pal, pal.pal_ncolors)
    out = []
    for c in colors:
        v = colorsys.rgb_to_hsv(*[x / 255 for x in c])[2]
        out.append(_ramp_at(classes[_classify(c)], v))
    tex.set_palette_colors(pal, out)


def texture_sheet(tex: Tex0, label: str):
    from PIL import Image, ImageDraw
    imgs = [(e.name, tex.render(e)) for e in tex.textures]
    w = sum(i.width for _, i in imgs) + 6 * len(imgs)
    h = max(i.height for _, i in imgs) + 14
    sheet = Image.new("RGBA", (w + 70, h), (40, 40, 50, 255))
    d = ImageDraw.Draw(sheet)
    d.text((2, h // 2 - 4), label, fill=(255, 255, 120, 255))
    x = 70
    for name, i in imgs:
        sheet.paste(i, (x, 14))
        d.text((x, 1), name, fill=(200, 200, 200, 255))
        x += i.width + 6
    return sheet


def build_models() -> None:
    from PIL import Image
    models = narc.load(HG / "files/fielddata/build_model/bm_field.narc")
    (OUT / "models").mkdir(parents=True, exist_ok=True)
    (OUT / "preview").mkdir(exist_ok=True)
    sheets = []
    for donor, out_name, pals, classes in (
            (HOUSE_DONOR, "hoenn_house", ("wk_hh_a_pl", "wk_hh_b_pl"),
             HOUSE_CLASSES),
            (LAB_DONOR, "hoenn_lab", ("wk_labo_a_pl", "wk_labo_b_pl"),
             LAB_CLASSES)):
        tex = Tex0(models[donor])
        sheets.append(texture_sheet(tex, f"{out_name}\n(before)"))
        for p in pals:
            remap_palette(tex, p, classes)
        (OUT / "models" / f"{out_name}.nsbmd").write_bytes(tex.bytes())
        sheets.append(texture_sheet(tex, f"{out_name}\n(after)"))
    W = max(s.width for s in sheets)
    H = sum(s.height for s in sheets) + 6 * len(sheets)
    out = Image.new("RGBA", (W, H), (40, 40, 50, 255))
    y = 0
    for s in sheets:
        out.paste(s, (0, y))
        y += s.height + 6
    out = out.resize((W * 2, H * 2), Image.NEAREST)
    out.save(OUT / "preview" / "models_before_after.png")
    print("models + before/after sheet written")


# --------------------------------------------------------------------------- #
#  placements + chunk patching
# --------------------------------------------------------------------------- #
def vanilla_entry_for(model_id: int) -> bytes:
    """First vanilla 48-byte building entry that places model_id (used as a
    template for rotation/scale words)."""
    for member in narc.load(HG / "files/a/0/6/5"):
        perm, bldg, _, _ = struct.unpack_from("<4I", member, 0)
        _, bgs = struct.unpack_from("<HH", member, 16)
        off = 20 + bgs + perm
        for i in range(bldg // 48):
            e = member[off + i * 48: off + (i + 1) * 48]
            if struct.unpack_from("<I", e, 0)[0] == model_id:
                return bytes(e)
    raise LookupError(model_id)


def fx32(v: float) -> int:
    return int(round(v * 65536)) & 0xFFFFFFFF


def make_entry(template: bytes, model_id: int,
               tx: float, ty: float, tz: float) -> bytes:
    e = bytearray(template)
    struct.pack_into("<I", e, 0, model_id)
    struct.pack_into("<III", e, 4, fx32(tx), fx32(ty), fx32(tz))
    return bytes(e)


def place_buildings() -> list[dict]:
    placed = stitch.stitch()
    placed, _, _ = stitch.normalize(placed)
    catalog = json.loads((ROOT / "converted/hoenn/buildings/buildings.json")
                         .read_text())
    lits = [c for c in catalog if c["map"] == "MAP_LITTLEROOT_TOWN"]
    tmpl_house = vanilla_entry_for(HOUSE_DONOR)
    tmpl_lab = vanilla_entry_for(LAB_DONOR)

    (OUT / "land_data").mkdir(exist_ok=True)
    by_chunk: dict[tuple[int, int], list[bytes]] = {}
    records = []
    for c in lits:
        gx, gy, w, h = c["global"]
        cx_f, cy_f = gx + w / 2, gy + h / 2       # building center, global tiles
        cell = (int(cx_f) // 32, int(cy_f) // 32)
        # chunk-center-relative, 1.0 == one tile
        tx, tz = cx_f - (cell[0] * 32 + 16), cy_f - (cell[1] * 32 + 16)
        model = LAB_ID if w >= 6 else HOUSE_ID
        tmpl = tmpl_lab if model == LAB_ID else tmpl_house
        ty = struct.unpack_from("<i", tmpl, 8)[0] / 65536   # keep donor height
        entry = make_entry(tmpl, model, tx, ty, tz)
        by_chunk.setdefault(cell, []).append(entry)
        records.append({"building": c["files"], "model": model,
                        "chunk_cell": list(cell),
                        "pos_tiles_rel_center": [round(tx, 2), round(ty, 2),
                                                 round(tz, 2)]})

    manifest = json.loads((ROOT / "converted/hoenn/manifest.json").read_text())
    mw = manifest["matrix"]["width"]
    cell_to_chunk = {tuple(e["cell"]): e["chunk"] for e in manifest["chunks"]}
    for cell, entries in by_chunk.items():
        cid = cell_to_chunk[cell]
        f = CHUNKS / f"chunk_{cid:04}.bin"
        ch = MapChunk.load(f)
        ch.buildings = b"".join(entries)
        patched = ch.serialize()
        f.write_bytes(patched)
        (OUT / "land_data" / f.name).write_bytes(patched)
    (OUT / "placements.json").write_text(json.dumps(records, indent=2) + "\n")
    print(f"{len(records)} placements across {len(by_chunk)} chunks")
    return records


# --------------------------------------------------------------------------- #
#  ground textures with footprints filled
# --------------------------------------------------------------------------- #
def ground_textures() -> None:
    from PIL import Image
    placed = stitch.stitch()
    placed, _, _ = stitch.normalize(placed)
    p = placed["MAP_LITTLEROOT_TOWN"]
    layout = gba.load_layout(p.layout_id)
    pair = gba.TilesetPair(layout.primary_tileset, layout.secondary_tileset)
    catalog = json.loads((ROOT / "converted/hoenn/buildings/buildings.json")
                         .read_text())
    boxes = [c["local"] for c in catalog if c["map"] == "MAP_LITTLEROOT_TOWN"]

    def in_box(x, y):
        return any(bx <= x < bx + bw and by <= y < by + bh
                   for bx, by, bw, bh in boxes)

    def filler(bx, by, bw, bh) -> int:
        """most common metatile in the 1-tile ring around a footprint"""
        from collections import Counter
        ring = Counter()
        for x in range(bx - 1, bx + bw + 1):
            for y in range(by - 1, by + bh + 1):
                if (bx <= x < bx + bw and by <= y < by + bh):
                    continue
                if 0 <= x < layout.width and 0 <= y < layout.height:
                    ring[layout.metatile(x, y)] += 1
        return ring.most_common(1)[0][0]

    fills = {tuple(b): filler(*b) for b in boxes}
    cells = sorted({((p.x + x) // 32, (p.y + y) // 32)
                    for x in range(layout.width) for y in range(layout.height)})
    for cx, cy in cells:
        img = Image.new("RGBA", (512, 512), (0, 0, 0, 255))
        for ty in range(32):
            for tx in range(32):
                gx, gy = cx * 32 + tx, cy * 32 + ty
                lx, ly = gx - p.x, gy - p.y
                if not (0 <= lx < layout.width and 0 <= ly < layout.height):
                    continue
                mt = layout.metatile(lx, ly)
                for (bx, by, bw, bh), fill in fills.items():
                    if bx <= lx < bx + bw and by <= ly < by + bh:
                        mt = fill
                        break
                img.paste(pair.render_metatile(mt), (tx * 16, ty * 16))
        img.save(OUT / "preview" / f"ground_c{cx}_{cy}.png")
    print(f"ground textures for cells {cells}")


if __name__ == "__main__":
    build_models()
    place_buildings()
    ground_textures()
