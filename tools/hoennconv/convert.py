#!/usr/bin/env python3
"""Hoenn overworld -> HGSS map data. Main driver.

Reads the pokeemerald tree (Gen 3), writes DS-format artifacts to
converted/hoenn/ in the repo root:

  matrix/hoenn_overworld.bin   HGSS MapMatrix (models+headers+altitudes),
                               same binary format the engine loads for the
                               vanilla 47x17 EVERYWHERE matrix
  land_data/chunk_NNNN.bin     HGSS land-data members: converted movement
                               permissions, empty buildings/BGS, donor flat
                               model+BDHC (real Hoenn models are the next
                               pipeline stage)
  land_data.narc               all chunks packed as a NARC for direct
                               inspection in DSPRE/Tinke
  zone_event/NNN_<MAP>.json    events in HGSS zone_event schema,
                               matrix-global coordinates
  tilesets/<pair>.png          composed 16px metatile atlases (texture
                               source material for the model stage)
  preview/overworld.png        stitched canvas render (4 px / metatile)
  preview/permissions.png      converted collision/type overlay
  manifest.json                placements, chunk<->cell table, header-slot
                               assignments, warp graph, conversion notes

Usage: python3 tools/hoennconv/convert.py [--no-preview]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mapeditor"))

import behavior_map
import events as ev
import gba
import narc
import stitch
from hgss_map import CHUNK_W, CHUNK_H, MapChunk, donor_flat_parts
from mapdata import MapMatrix

ROOT = Path(__file__).resolve().parents[2]
HG = ROOT / "disasm" / "pokeheartgold"
OUT = ROOT / "converted" / "hoenn"


def main(preview: bool = True) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for sub in ("matrix", "land_data", "zone_event", "tilesets", "preview"):
        (OUT / sub).mkdir(exist_ok=True)

    notes: list[str] = []

    # ---- stitch ---------------------------------------------------------- #
    placed = stitch.stitch()
    placed, W, H = stitch.normalize(placed)
    order = sorted(placed)                       # stable map order
    ovl = stitch.overlaps(placed)
    for a, b in ovl:
        notes.append(f"seam inconsistency: {a} overlaps {b} (first-placed wins)")
    mw = (W + CHUNK_W - 1) // CHUNK_W
    mh = (H + CHUNK_H - 1) // CHUNK_H
    print(f"stitched {len(placed)} maps -> {W}x{H} metatiles -> {mw}x{mh} matrix")

    # owner index per global cell (-1 = void). First-placed map wins overlaps.
    owner = [[-1] * W for _ in range(H)]
    for idx, mid in enumerate(order):
        p = placed[mid]
        for y in range(p.y, p.y + p.height):
            row = owner[y]
            for x in range(p.x, p.x + p.width):
                if row[x] < 0:
                    row[x] = idx

    # ---- per-map data ---------------------------------------------------- #
    layouts = {mid: gba.load_layout(placed[mid].layout_id) for mid in order}
    pairs: dict[tuple[str, str], gba.TilesetPair] = {}
    for mid in order:
        l = layouts[mid]
        pairs.setdefault((l.primary_tileset, l.secondary_tileset), None)
    for key in pairs:
        pairs[key] = gba.TilesetPair(*key)
    print(f"{len(pairs)} tileset pairs loaded")
    behaviors = gba.behaviors()

    def cell_g4(gx: int, gy: int) -> tuple[int, int]:
        oi = owner[gy][gx] if 0 <= gx < W and 0 <= gy < H else -1
        if oi < 0:
            return behavior_map.T_PLAIN, behavior_map.BLOCKED
        mid = order[oi]
        p, l = placed[mid], layouts[mid]
        lx, ly = gx - p.x, gy - p.y
        mt = l.metatile(lx, ly)
        pair = pairs[(l.primary_tileset, l.secondary_tileset)]
        mb = behaviors.get(pair.behavior(mt), "MB_NORMAL")
        return behavior_map.convert(mb, l.collision(lx, ly))

    # ---- chunks + matrix -------------------------------------------------- #
    vanilla_members = narc.load(HG / "files" / "a" / "0" / "6" / "5")
    donor_model, donor_bdhc = donor_flat_parts(vanilla_members)

    blocked = MapChunk([0] * 1024, [0x80] * 1024,
                       model=donor_model, bdhc=donor_bdhc)
    chunks: list[bytes] = [blocked.serialize()]     # id 0 = shared void chunk
    models: list[int] = []
    headers: list[int] = []
    chunk_table = []
    for cy in range(mh):
        for cx in range(mw):
            types, colls, owners = [], [], Counter()
            for y in range(CHUNK_H):
                for x in range(CHUNK_W):
                    gx, gy = cx * CHUNK_W + x, cy * CHUNK_H + y
                    t, c = cell_g4(gx, gy)
                    types.append(t)
                    colls.append(c)
                    if 0 <= gx < W and 0 <= gy < H and owner[gy][gx] >= 0:
                        owners[owner[gy][gx]] += 1
            if not owners:
                models.append(0)
                headers.append(0xFFFF)
                continue
            ch = MapChunk(types, colls, model=donor_model, bdhc=donor_bdhc)
            cid = len(chunks)
            chunks.append(ch.serialize())
            models.append(cid)
            headers.append(owners.most_common(1)[0][0])   # header slot = map index
            chunk_table.append({"chunk": cid, "cell": [cx, cy],
                                "owner": order[owners.most_common(1)[0][0]]})

    for i, ch in enumerate(chunks):
        (OUT / "land_data" / f"chunk_{i:04}.bin").write_bytes(ch)
    (OUT / "land_data.narc").write_bytes(narc.build(chunks))

    matrix = MapMatrix(mw, mh, "hoenn", models,
                       headers=headers, altitudes=[0] * (mw * mh))
    (OUT / "matrix" / "hoenn_overworld.bin").write_bytes(matrix.serialize())
    print(f"{len(chunks)} chunks ({len(chunks)-1} real + void), matrix {mw}x{mh}")

    # ---- events ----------------------------------------------------------- #
    emaps = gba.maps()
    warp_targets = set()
    for i, mid in enumerate(order):
        p = placed[mid]
        m = emaps[mid]
        tag = mid.removeprefix("MAP_").replace("_", "").lower()
        data = {
            "header": f"fielddata/script/scr_seq/event_HOENN_{mid.removeprefix('MAP_')}.h",
            "bgs": ev.convert_bgs(m.get("bg_events") or [], p.x, p.y),
            "objects": ev.convert_objects(tag, m.get("object_events") or [],
                                          p.x, p.y, notes),
            "warps": ev.convert_warps(m.get("warp_events") or [], p.x, p.y),
            "coords": ev.convert_coords(m.get("coord_events") or [], p.x, p.y),
        }
        warp_targets.update(w["header"] for w in data["warps"])
        f = OUT / "zone_event" / f"{i:03}_{mid.removeprefix('MAP_')}.json"
        f.write_text(json.dumps(data, indent=2) + "\n")
    interiors = sorted(warp_targets - set(order))
    print(f"zone events for {len(order)} maps; {len(interiors)} interior warp targets pending")

    # ---- tileset atlases --------------------------------------------------- #
    from PIL import Image
    for (prim, sec), pair in pairs.items():
        n = gba.NUM_METATILES_IN_PRIMARY + len(pair.metatiles_secondary)
        cols = 32
        rows = (n + cols - 1) // cols
        atlas = Image.new("RGBA", (cols * 16, rows * 16), (0, 0, 0, 0))
        for mt in range(n):
            atlas.paste(pair.render_metatile(mt), ((mt % cols) * 16, (mt // cols) * 16))
        name = f"{prim.removeprefix('gTileset_')}_{sec.removeprefix('gTileset_')}.png"
        atlas.save(OUT / "tilesets" / name)
    print(f"{len(pairs)} metatile atlases written")

    # ---- previews ----------------------------------------------------------- #
    if preview:
        SC = 4
        canvas = Image.new("RGBA", (W * SC, H * SC), (16, 16, 24, 255))
        thumbs: dict[tuple, object] = {}
        for mid in order:
            p, l = placed[mid], layouts[mid]
            key0 = (l.primary_tileset, l.secondary_tileset)
            pair = pairs[key0]
            for y in range(l.height):
                for x in range(l.width):
                    mt = l.metatile(x, y)
                    th = thumbs.get((key0, mt))
                    if th is None:
                        th = pair.render_metatile(mt).resize((SC, SC))
                        thumbs[(key0, mt)] = th
                    canvas.paste(th, ((p.x + x) * SC, (p.y + y) * SC))
        canvas.save(OUT / "preview" / "overworld.png")

        pal = {behavior_map.T_GRASS: (40, 180, 60), behavior_map.T_LONG_GRASS: (20, 140, 40),
               behavior_map.T_SEA: (40, 90, 220), behavior_map.T_POND: (90, 150, 240),
               behavior_map.T_SAND: (230, 210, 120), behavior_map.T_ICE: (170, 230, 250)}
        perm = Image.new("RGB", (W, H))
        px = perm.load()
        for gy in range(H):
            for gx in range(W):
                t, c = cell_g4(gx, gy)
                col = pal.get(t)
                if col is None:
                    col = (60, 60, 70) if c else (200, 200, 205)
                elif c and t not in (behavior_map.T_SEA, behavior_map.T_POND):
                    col = tuple(v // 2 for v in col)
                px[gx, gy] = col
        perm.resize((W * 2, H * 2), 0).save(OUT / "preview" / "permissions.png")
        print("previews written")

    # ---- manifest ------------------------------------------------------------ #
    manifest = {
        "source": "pokeemerald @ " + _rev(ROOT / "disasm" / "pokeemerald"),
        "target_format": "pokeheartgold @ " + _rev(HG),
        "canvas_metatiles": [W, H],
        "matrix": {"width": mw, "height": mh,
                   "file": "matrix/hoenn_overworld.bin",
                   "header_slot_semantics":
                       "headers[] stores an index into maps[] below; real "
                       "MAP_HOENN_* engine header ids get assigned at "
                       "integration time"},
        "maps": [{
            "index": i,
            "gen3_id": mid,
            "proposed_header": "MAP_HOENN_" + mid.removeprefix("MAP_"),
            "at": [placed[mid].x, placed[mid].y],
            "size": [placed[mid].width, placed[mid].height],
            "layout": placed[mid].layout_id,
            "zone_event": f"zone_event/{i:03}_{mid.removeprefix('MAP_')}.json",
        } for i, mid in enumerate(order)],
        "chunks": chunk_table,
        "interior_warp_targets_pending": interiors,
        "notes": notes,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"manifest written; {len(notes)} notes")


def _rev(repo: Path) -> str:
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            text=True).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    main(preview="--no-preview" not in sys.argv)
