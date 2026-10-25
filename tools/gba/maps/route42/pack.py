"""Route 42 traversal and layer helpers for pack_fixed.py (Route 43's pack.py, trimmed to
what the lossless packer uses): the Gen 3 behaviour, collision and elevation of every cell
from the decoded HGSS permissions, the walk-behind rule, and the per-cell object art grid.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B                                             # noqa: E402
from elements import GATE_COLS, GATE_ROWS                     # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-42'
SRC = ART / 'source'
W, H = 96, 32
CLEAR = -1                                                    # transparent pixel marker in keys
FLAT = ('flat_',)                                             # ground details, never above the player: tall grass, flowers, the Mt. Mortar mouths
EVENTS = json.loads((SRC / 'hgss-events.json').read_text())
SIGN_MOVED = {(86, 12): (88, 12)}                            # assemble.SIGNS: new cell -> HGSS cell
SIGNS = {SIGN_MOVED.get(c, c) for c in (tuple(e['cell']) for e in EVENTS['signs'] if e['bg_type'] == 1)}

def key5(px, mask=None):
    k = B.rgb5(px).astype(np.int16)
    if mask is not None:
        k[~mask] = CLEAR
    return k.tobytes()

GATE_DOORS, ARROW_WARPS = {}, {}                              # Route 42 has no gatehouse
# Solid cells with art Gen 3 cannot use: the Mt. Mortar mouths (HGSS warps 0x6E; Mt. Mortar
# is not built), the Ecruteak gate's doorway (0x6D; the gate interior is not built) and the
# Rock Climb wall (0x4C; Gen 3 has no Rock Climb).
SOLID = {'D': 'HGSS warps into Mt. Mortar here; Mt. Mortar is not built, so the mouth is solid',
         'd': "the Ecruteak gate's doorway, G02's stairs one row south of HGSS's (elements.GATE_DOOR); "
              'its interior is not built, so the doorway is solid',
         'K': 'HGSS has a Rock Climb wall here; Gen 3 has no Rock Climb, so it is solid rock'}

def traversal(engine, cells, art, edge):
    """Gen 3 behaviour, collision and elevation per cell from the HGSS permissions. art is
    the per-cell 'has object art' grid (top layer, plus the sign cells); edge marks cells
    where only a building's top edge reaches, in the cell's lower half."""
    MB = B.behaviors(engine)
    trees = json.loads((SRC / 'trace/trees.json').read_text())['trees']
    rooted = {(x + dx, y + dy) for x, y in trees for dx in (0, 1) for dy in (0, 1)}
    rooted |= {(x + dx, y - 1) for x, y in trees for dx in (0, 1)}   # a T01 crown fills the row above its root
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    # HGSS blocks the cells its taller models rise over: a building's footprint and up to two
    # rows north of it. Elsewhere a blocked cell stays blocked.
    near_model = lambda x, y: any(0 <= y + k < H and cells[y + k][x]['owner'] >= 0 for k in (0, 1, 2))
    out = []
    for y in range(H):
        for x in range(W):
            t, k = int(types[y, x]), int(coll[y, x])
            lab = cells[y][x]['lab']
            c = dict(x=x, y=y, hgss_type=t, hgss_collision=k, element=lab + cells[y][x]['floor'][0])
            if lab in SOLID:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation=SOLID[lab])
            elif (x, y) in GATE_DOORS:
                c.update(foot='door', behavior='MB_NON_ANIMATED_DOOR', collision=0, elevation=3, door=GATE_DOORS[(x, y)])
            elif (x, y) in ARROW_WARPS:
                hx, dest = ARROW_WARPS[(x, y)]
                c.update(foot='door', behavior='MB_SOUTH_ARROW_WARP', collision=0, elevation=3, door=dest,
                         adaptation=f"HGSS's gate warp {hx} stands one row north, in front of its taller model; "
                                    "the arrow warp sits against the Gen 3 roof")
            elif t == 0x6F:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation='HGSS gate warp row; the arrow warp is the cell south of it')
            elif t == 0x3B:
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif t == 0x39:
                c.update(foot='ledge_west', behavior='MB_JUMP_WEST', collision=1, elevation=0)
            elif t == 0x10:
                c.update(foot='surf', behavior='MB_POND_WATER', collision=0, elevation=1)
            elif lab == 'F' and (x, y) not in rooted:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS's offset tree crowns overhang this woods cell; no non-overlapping Gen 3 tree root fits it")
            elif t == 0x02 and cells[y][x].get('trimmed'):
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS tall grass in the column that scrolls out under Mahogany's tilesets when crossing east; "
                                    "Mahogany has no tall grass colours, so it is lawn")
            elif t == 0x02 and not k & 0x80:
                c.update(foot='open', behavior='MB_TALL_GRASS', collision=0, elevation=3, grass=True)
            elif k & 0x80 and lab == 'X' and near_model(x, y) and not art[y, x]:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS's taller building model blocks it; the Gen 3 sprite does not reach this cell")
            elif k & 0x80 and lab == 'X' and near_model(x, y) and edge[y, x]:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS's taller building model blocks it; only the Gen 3 roof's top edge reaches this cell, and the player walks behind it")
            elif k & 0x80:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            if lab == 'X' and GATE_COLS[0] <= x <= GATE_COLS[1] and GATE_ROWS[0] <= y <= GATE_ROWS[1]:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3,
                         adaptation="the Ecruteak gate's G02 footprint is solid throughout, so no one walks round the gate "
                                    "between it and the woods (owner review, Route 42)")
            if (x, y) in SIGN_MOVED:                      # the east route sign's new cell (assemble.SIGNS)
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3,
                         adaptation=f"the route sign stands here, moved from HGSS's {SIGN_MOVED[(x, y)]} out of the columns Mahogany's tilesets draw")
            elif (x, y) in SIGN_MOVED.values():
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation='HGSS\'s route sign stood here; it moved two cells west, out of the columns Mahogany\'s tilesets draw')
            c['behavior_id'] = MB[c['behavior']]
            out.append(c)
    return out

def above_player(walkable, top, shared, owner):
    """Cells whose art draws above the player (layer type normal). A Gen 3 player is two
    cells tall: feet in its own cell, head in the cell north of it. Object art in a walkable
    cell draws above the player only when the object's base (the lowest row holding its
    pixels) lies further south, so the object stands in front: a roof or crown the player
    walks behind. A door, or any cell on an object's base row, is behind a player standing
    on it or south of it and stays below the player (covered), like every blocked cell.
    Top-layer art that belongs to no object keeps the plain rule (walkable means above).
    Flat ground details (HGSS draws its stones and sand tufts into the terrain mesh) lie
    under the player wherever they are."""
    art = (top[..., 3] > 0) | (shared[..., 3] > 0)
    base = {}
    for name in set(owner[art].ravel().tolist()) - {''}:
        base[name] = int(np.nonzero((owner == name).any(1))[0].max()) // 16
    out = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            a = art[sl]
            if not (walkable[y, x] and a.any()):
                continue
            names = set(owner[sl][a].ravel().tolist())
            out[y, x] = ('' in names and (top[sl][..., 3] > 0).any()) or \
                any(base[n] > y for n in names - {''} if not n.startswith(FLAT))
    return out

def object_art(top, shared, owner):
    px = (top[..., 3] > 0) | (shared[..., 3] > 0)
    art = px.reshape(H, 16, W, 16).any(axis=(1, 3))
    for x, y in SIGNS:
        art[y, x] = True
    upper = px.reshape(H, 16, W, 16)[:, :8].any(axis=(1, 3))
    flat = np.char.startswith(owner.astype(str), FLAT[0])
    edge = px.reshape(H, 16, W, 16).any(axis=(1, 3)) & ~upper & ~(flat & px).reshape(H, 16, W, 16).any(axis=(1, 3))
    return art, edge
