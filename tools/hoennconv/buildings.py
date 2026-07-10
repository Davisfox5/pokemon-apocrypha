#!/usr/bin/env python3
"""Extract Hoenn buildings from the Gen-3 maps as standalone, background-free
art + footprint metadata — the feedstock for DS building models.

Why: HGSS never bakes buildings into the ground. Each chunk's ground model is
flat terrain; buildings are separate NSBMDs (files/fielddata/build_model/
bm_field.narc, 340 models) placed by 48-byte entries in the chunk. The
"ground rises with the roof" problem only exists if building pixels stay in
the ground texture. So: cut every building out of the 2-D map, hand back
(a) clean building sprites for texturing a model, and (b) the footprint so
the ground chunk can be patched with plain terrain underneath.

Background-free trick: Gen-3 metatiles are two layers of 4 tiles. Roof-edge
tiles that "bleed grass" keep the grass in layer A (bottom) and the roof
pixels in layer B (top, palette-0-transparent) — the layer split IS the
building/background separation (include/global.fieldmap.h layer types).
We emit three renders per building:
    *_full.png    both layers (what the GBA shows)
    *_struct.png  layer B only  -> roof/wall pixels, background-free edges
    *_base.png    layer A only  -> what's underneath (for ground patching)

Footprint detection: flood 4-connected from each door warp across blocked
metatiles (common buildings like Centers/Marts live in the *primary*
tileset, so tileset membership can't be the filter). Regions that grow past
MAX_BUILDING are dropped — that's the flood escaping into a tree line or
cliff, which door-seeding otherwise never reaches. Results are drawn on per-town review
overlays for eyeball correction; overrides.json (same directory) can add or
replace rectangles per map:  {"MAP_X": {"add": [[x,y,w,h],...], "drop": [i,...]}}

Usage: python3 tools/hoennconv/buildings.py       (writes converted/hoenn/buildings/)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gba
import stitch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "converted" / "hoenn" / "buildings"

DOOR_BEHAVIORS = {"MB_ANIMATED_DOOR", "MB_NON_ANIMATED_DOOR", "MB_WATER_DOOR",
                  "MB_LADDER", "MB_DEEP_SOUTH_WARP"}
WINDOW = 12            # flood window radius around each door, metatiles
MIN_CELLS = 3              # ignore specks


def detect(map_id: str, layout: gba.Layout, pair: gba.TilesetPair,
           warps: list[dict], behaviors: dict[int, str]) -> list[tuple[int, int, int, int]]:
    """Building bounding boxes [(x, y, w, h)] in map-local metatile coords."""
    W, H = layout.width, layout.height

    def is_door(x, y):
        return behaviors.get(pair.behavior(layout.metatile(x, y)), "") in DOOR_BEHAVIORS

    # No structural tile property separates buildings from trees (Petalburg's
    # Pokemon Center walls are primary-tileset layer-0, exactly like trees),
    # so the flood refuses green-dominant metatiles: tree/hedge masses are
    # overwhelmingly green, building shells are not. Fortree and cliff-hugging
    # buildings are the expected override cases.
    _green: dict[int, bool] = {}

    def is_greenish(mt: int) -> bool:
        hit = _green.get(mt)
        if hit is None:
            img = pair.render_metatile(mt)
            g = tot = 0
            for r, gr, b, a in img.getdata():
                if a:
                    tot += 1
                    if gr > r * 1.15 and gr > b * 1.15:
                        g += 1
            hit = tot > 0 and g / tot > 0.5
            _green[mt] = hit
        return hit

    def is_solid(x, y):
        return layout.collision(x, y) != 0 and not is_greenish(layout.metatile(x, y))

    # Roof top rows are walk-behind in Gen 3 (passable, art in layer B), so
    # the solid flood stops one row short of the roof line. A metatile whose
    # layer B carries real pixels is draw-over content — extend upward while
    # most of the row above has it (and isn't just tree canopy).
    _top: dict[int, bool] = {}

    def has_top_content(mt: int) -> bool:
        hit = _top.get(mt)
        if hit is None:
            img = pair.render_metatile(mt, layers=(1,))
            n = sum(1 for *_, a in img.getdata() if a)
            hit = n > 8 and not is_greenish(mt)
            _top[mt] = hit
        return hit

    seeds = {(int(w["x"]), int(w["y"])) for w in warps
             if 0 <= int(w["x"]) < W and 0 <= int(w["y"]) < H
             and is_door(int(w["x"]), int(w["y"]))}

    # Flood within a window around each door so fences/cliffs that link the
    # whole town together can't swallow every building into one region; then
    # trim sparse border rows/cols (fence spurs) off the bounding box.
    claimed: set[tuple[int, int]] = set()
    boxes = []
    for seed in sorted(seeds):
        if seed in claimed:
            continue
        sx, sy = seed
        region = {seed}
        frontier = [seed]
        seen = {seed}
        while frontier:
            x, y = frontier.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if ((nx, ny) in seen or not (0 <= nx < W and 0 <= ny < H)
                        or abs(nx - sx) > WINDOW or abs(ny - sy) > WINDOW):
                    continue
                seen.add((nx, ny))
                if is_solid(nx, ny) or is_door(nx, ny):
                    region.add((nx, ny))
                    frontier.append((nx, ny))
        if len(region) < MIN_CELLS:
            continue
        x0, x1 = min(c[0] for c in region), max(c[0] for c in region)
        y0, y1 = min(c[1] for c in region), max(c[1] for c in region)
        # trim: peel outer rows/cols holding too few region cells
        def count_col(cx):
            return sum(1 for c in region if c[0] == cx and y0 <= c[1] <= y1)
        def count_row(cy):
            return sum(1 for c in region if c[1] == cy and x0 <= c[0] <= x1)
        changed = True
        while changed and x1 > x0 and y1 > y0:
            changed = False
            if count_col(x0) < max(2, (y1 - y0 + 1) * 3 // 10):
                x0 += 1; changed = True
            if count_col(x1) < max(2, (y1 - y0 + 1) * 3 // 10):
                x1 -= 1; changed = True
            if count_row(y0) < max(2, (x1 - x0 + 1) * 3 // 10):
                y0 += 1; changed = True
            if count_row(y1) < max(2, (x1 - x0 + 1) * 3 // 10):
                y1 -= 1; changed = True
        claimed |= region
        # extend upward over walk-behind roof rows
        while y0 > 0:
            hits = sum(1 for x in range(x0, x1 + 1)
                       if has_top_content(layout.metatile(x, y0 - 1)))
            if hits * 2 < (x1 - x0 + 1):
                break
            y0 -= 1
            claimed |= {(x, y0) for x in range(x0, x1 + 1)}
        boxes.append((x0, y0, x1 - x0 + 1, y1 - y0 + 1))

    # merge overlapping boxes (two doors on one building, etc.)
    merged: list[list[int]] = []
    for b in sorted(boxes):
        for m in merged:
            if (b[0] <= m[0] + m[2] and m[0] <= b[0] + b[2] and
                    b[1] <= m[1] + m[3] and m[1] <= b[1] + b[3]):
                x2 = max(m[0] + m[2], b[0] + b[2])
                y2 = max(m[1] + m[3], b[1] + b[3])
                m[0], m[1] = min(m[0], b[0]), min(m[1], b[1])
                m[2], m[3] = x2 - m[0], y2 - m[1]
                break
        else:
            merged.append(list(b))
    return [tuple(m) for m in merged]


def render_box(layout: gba.Layout, pair: gba.TilesetPair, box, layers):
    from PIL import Image
    x0, y0, w, h = box
    img = Image.new("RGBA", (w * 16, h * 16), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            mt = layout.metatile(x0 + x, y0 + y)
            img.paste(pair.render_metatile(mt, layers=layers), (x * 16, y * 16))
    return img


def render_clean(layout: gba.Layout, pair: gba.TilesetPair, box):
    """Background-free full-building art: where layer B has pixels they win
    (roof over grass); everywhere else the composite is used with the
    surrounding ground's exact colors keyed out. This is the strategy-A
    texture source: the building as drawn, grass gone."""
    from PIL import Image
    x0, y0, w, h = box
    ring = set()
    for x in range(x0 - 1, x0 + w + 1):
        for y in (y0 - 1, y0 + h):
            if 0 <= x < layout.width and 0 <= y < layout.height:
                ring.add(layout.metatile(x, y))
    for y in range(y0, y0 + h):
        for x in (x0 - 1, x0 + w):
            if 0 <= x < layout.width and 0 <= y < layout.height:
                ring.add(layout.metatile(x, y))
    ground_colors = set()
    for mt in ring:
        ground_colors.update(
            p[:3] for p in pair.render_metatile(mt).getdata() if p[3])

    full = render_box(layout, pair, box, layers=(0, 1))
    top = render_box(layout, pair, box, layers=(1,))
    out = Image.new("RGBA", full.size, (0, 0, 0, 0))
    fp, tp, op = full.load(), top.load(), out.load()
    for y in range(full.height):
        for x in range(full.width):
            t = tp[x, y]
            if t[3]:
                op[x, y] = t
            else:
                f = fp[x, y]
                if f[3] and f[:3] not in ground_colors:
                    op[x, y] = f
    return out


def main() -> None:
    from PIL import Image, ImageDraw

    OUT.mkdir(parents=True, exist_ok=True)
    behaviors = gba.behaviors()
    placed = stitch.stitch()
    placed, _, _ = stitch.normalize(placed)
    emaps = gba.maps()
    overrides = {}
    ov_file = OUT / "overrides.json"
    if ov_file.exists():
        overrides = json.loads(ov_file.read_text())

    pairs: dict[tuple, gba.TilesetPair] = {}
    catalog = []
    total = 0
    for mid in sorted(placed):
        p = placed[mid]
        layout = gba.load_layout(p.layout_id)
        key = (layout.primary_tileset, layout.secondary_tileset)
        pair = pairs.setdefault(key, gba.TilesetPair(*key))
        boxes = detect(mid, layout, pair, emaps[mid].get("warp_events") or [],
                       behaviors)
        ov = overrides.get(mid, {})
        boxes = [b for i, b in enumerate(boxes) if i not in set(ov.get("drop", []))]
        boxes += [tuple(b) for b in ov.get("add", [])]
        if not boxes:
            continue
        d = OUT / mid.removeprefix("MAP_")
        d.mkdir(exist_ok=True)
        review = render_box(layout, pair, (0, 0, layout.width, layout.height),
                            layers=(0, 1))
        draw = ImageDraw.Draw(review)
        for i, b in enumerate(sorted(boxes)):
            x0, y0, w, h = b
            for name, layers in (("full", (0, 1)), ("struct", (1,)), ("base", (0,))):
                render_box(layout, pair, b, layers).save(d / f"bldg_{i:02}_{name}.png")
            render_clean(layout, pair, b).save(d / f"bldg_{i:02}_clean.png")
            draw.rectangle([x0 * 16, y0 * 16, (x0 + w) * 16 - 1, (y0 + h) * 16 - 1],
                           outline=(255, 0, 0, 255), width=2)
            draw.text((x0 * 16 + 3, y0 * 16 + 2), str(i), fill=(255, 0, 0, 255))
            catalog.append({
                "map": mid, "index": i,
                "local": [x0, y0, w, h],
                "global": [p.x + x0, p.y + y0, w, h],
                "files": f"{d.name}/bldg_{i:02}_*.png",
            })
            total += 1
        review.save(d / "review.png")
    (OUT / "buildings.json").write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"{total} buildings across {len({c['map'] for c in catalog})} maps")


if __name__ == "__main__":
    main()
