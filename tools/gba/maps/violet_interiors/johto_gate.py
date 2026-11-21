"""Johto's east-west gatehouse interior (owner review of #39, second pass: "the outside gate is fine, but the inside
... is a Hoenn interior ... those aren't even the directions you enter at. Mimic the HeartGold SoulSilver interior and
redesign it to match the Gen 3 aesthetic").

    python3 tools/gba/maps/violet_interiors/johto_gate.py ENGINE [--preview]

HGSS's plan (R31R0101, Route 31's gate to Violet; pokeheartgold zone event 094 and its permission grid): windows along
the north wall, a potted plant in each corner, the officer's counter across the north half with the officer behind it,
a second counter across the south half, a mat between them, and the way through running east-west between the
counters with one exit in each side wall (arrow warps, HGSS's (1, 7) west and (10, 7) east). The old interior was
Emerald's Route 110 cycling-road gate, entered from the bottom wall.

Gen 3 pieces: FireRed's east-west gate (SaffronCity_EastWestEntrance: Route 7's and Route 8's gates) is that same plan
in Gen 3's own cells, so the room is its cells whole, with their collision and behaviour (its exits are the west and
east arrow warps at (1, 5) and (11, 5)). Colours: each material takes HGSS's room's (sampled from the render of
R31R0101): the beige wall and its brown baseboard, the grey floor, the light-blue counters, the orange mat, so the
Johto gate is not Kanto's kit (owner: each region has its own gatehouse set). Plants, windows, exit mats, outlines and
white keep Gen 3's own colours.

Both Violet gates use this layout: VioletEastGate (west exit to Violet, east exit to Route 31) and VioletWestGate
(west exit to Route 36, east exit to Violet), each with HGSS's officer behind the north counter.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / 'route30_catalog'), str(HERE.parent / 'violet_city')]
import native as N                       # noqa: E402
import shops_native as SN                # noqa: E402

SRC = 'SaffronCity_EastWestEntrance'
NAME, W, H = 'JohtoGate', 13, 9
PRIMARY = SECONDARY = 'johto_gate'
PSYM, SSYM = 'JohtoGatePrimary', 'JohtoGate'
FOLDER = 'JohtoGate'
WEST_EXIT, EAST_EXIT = (1, 5), (11, 5)
OFFICER = (6, 2)
ART = ROOT / 'gba/art/johto-gate'

# Gen 3 colour -> HGSS colour, per material (HGSS R31R0101's render: wall, baseboard, floor, counter, mat).
WALL = {(213, 222, 197): (231, 206, 173), (238, 255, 213): (239, 231, 206), (180, 197, 164): (206, 181, 156),
        (148, 172, 139): (173, 140, 115), (115, 156, 180): (156, 123, 99)}
FLOOR = {(222, 197, 106): (181, 181, 173), (189, 164, 82): (165, 165, 156), (230, 222, 156): (189, 189, 181),
         (246, 238, 189): (206, 206, 198), (115, 156, 180): (140, 140, 132)}
COUNTER = {(246, 238, 189): (148, 214, 255), (213, 205, 156): (123, 189, 239), (180, 180, 164): (107, 156, 206),
           (131, 131, 131): (74, 99, 140)}
MAT = {(115, 156, 180): (206, 115, 74), (246, 238, 189): (239, 173, 33), (230, 222, 156): (214, 140, 41),
       (213, 205, 156): (214, 140, 41), (180, 180, 164): (181, 115, 33)}

def regions():
    """Material of each cell: walls (rows 0-1, the side walls), counters (rows 3 and 7, columns 2-10), the mat
    (rows 4-6, columns 3-9), floor elsewhere. The side walls' exit mats keep Gen 3's red."""
    out = {}
    for y in range(H):
        for x in range(W):
            if y <= 1 or x in (0, W - 1):
                out[(x, y)] = WALL
            elif y in (3, 7) and 2 <= x <= 10:
                out[(x, y)] = COUNTER
            elif 4 <= y <= 6 and 3 <= x <= 9:
                out[(x, y)] = MAT
            else:
                out[(x, y)] = FLOOR
    return out

def compose():
    r = SN.NRoom(NAME, W, H)
    for y in range(H):
        for x in range(W):
            r.cell(SRC, x, y, x, y, label='gate')
    for (x, y), table in regions().items():
        sl = r.sl(x, y)
        for arr in (r.lower[sl], r.upper[sl]):
            rgb = arr[..., :3]
            op = arr[..., 3] > 0 if arr.shape[-1] == 4 else np.ones(rgb.shape[:2], bool)
            src = rgb.copy()
            for a, b in table.items():
                rgb[op & (src == a).all(-1)] = b
    r.notes.append('FireRed east-west gate cells on HGSS R31R0101 plan, HGSS colours by material')
    return r

def warp(xy, dest, wid):
    return dict(x=xy[0], y=xy[1], elevation=0, dest_map=dest, dest_warp_id=str(wid))

def officer(script):
    return {'local_id': 'LOCALID_GATE_OFFICER', 'graphics_id': 'OBJ_EVENT_GFX_POLICEMAN', 'x': OFFICER[0], 'y': OFFICER[1],
            'elevation': 3, 'movement_type': 'MOVEMENT_TYPE_FACE_DOWN', 'movement_range_x': 0, 'movement_range_y': 0,
            'trainer_type': 'TRAINER_TYPE_NONE', 'trainer_sight_or_berry_tree_id': '0', 'script': script, 'flag': '0'}

# map: (layout id, west exit's destination and warp id, east exit's, the officer's line)
GATES = {
    'VioletEastGate': ('LAYOUT_VIOLET_EAST_GATE', ('MAP_VIOLET_CITY', 0), ('MAP_JOHTO_ROUTE31', 0),
                       'West is VIOLET CITY.\\nEast is ROUTE 31.'),
    'VioletWestGate': ('LAYOUT_VIOLET_WEST_GATE', ('MAP_JOHTO_ROUTE36', 0), ('MAP_VIOLET_CITY', 1),
                       'West is ROUTE 36.\\nEast is VIOLET CITY.'),
}

def install_maps(engine):
    for name, (lid, west, east, line) in GATES.items():
        p = engine / 'data/maps' / name / 'map.json'
        mj = json.loads(p.read_text())
        mj['layout'] = lid
        # warp 0: the west exit, warp 1: the same cell (the outdoor gates' two stair cells both land here), warp 2:
        # the east exit. The outdoor maps' warp ids into these gates stay as they are (0 from the west, 2 from the east).
        mj['warp_events'] = [warp(WEST_EXIT, *west), warp(WEST_EXIT, *west), warp(EAST_EXIT, *east)]
        mj['object_events'] = [officer(f'{name}_EventScript_Officer')]
        mj['bg_events'] = []; mj['coord_events'] = []
        p.write_text(json.dumps(mj, indent=2) + '\n')
        (p.parent / 'scripts.inc').write_text(
            f'{name}_MapScripts::\n    .byte 0\n\n{name}_EventScript_Officer::\n    msgbox {name}_Text_Officer, MSGBOX_NPC\n    end\n\n'
            f'{name}_Text_Officer:\n    .string "{line}$"\n')

def build(engine, preview=False):
    import build as BD
    import ipack as IP
    from tiles import Tileset
    r = compose()
    ART.mkdir(parents=True, exist_ok=True)
    img = r.image()
    Image.fromarray(img).save(ART / 'composed.png')
    Image.fromarray(N.Source(SRC).image()).save(ART / 'gen3-source.png')
    if preview:
        return
    log = []
    pk = IP.pack({NAME: (W, H, BD.cells(r))}, log)
    IP.write(engine, PRIMARY, SECONDARY, pk)
    BD.register(engine, PRIMARY, SECONDARY, PSYM, SSYM)
    black = next((x, y) for y in range(H) for x in range(W) if not img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16].any())
    for name, (lid, _, _, _) in GATES.items():
        BD.layout(engine, lid, FOLDER, W, H, pk['words'][NAME], PSYM, SSYM, int(pk['words'][NAME][black[1], black[0]]),
                  name=f'{name}_Layout')
    install_maps(engine)
    t = Tileset(engine, SECONDARY, PRIMARY)
    got = np.array(t.map_image([int(w) & 1023 for w in pk['words'][NAME].ravel()], W).convert('RGB'))
    Image.fromarray(got).save(ART / 'installed.png')
    rep = dict(tiles=len(pk['tiles']), metatiles=len(pk['metas']), px_changed_by_palette=int(((got >> 3) != (img >> 3)).any(-1).sum()), log=log)
    (ART / 'build.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k != 'log'}))

if __name__ == '__main__':
    eng = Path(sys.argv[1]).resolve()
    N.ENG = eng
    build(eng, '--preview' in sys.argv)
