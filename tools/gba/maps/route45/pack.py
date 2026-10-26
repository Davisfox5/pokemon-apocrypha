"""Route 45 traversal and layer helpers for pack_fixed.py (Route 43's pack.py, trimmed to
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
import elements as E                                          # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-45'
SRC = ART / 'source'
W, H = 32, 160
CLEAR = -1                                                    # transparent pixel marker in keys
FLAT = ('flat_',)                                             # ground details, never above the player: tall grass, flowers, the diagonal stairs
EVENTS = json.loads((SRC / 'hgss-events.json').read_text())
SIGNS = {tuple(e['cell']) for e in EVENTS['signs'] if e['bg_type'] == 1}

def key5(px, mask=None):
    k = B.rgb5(px).astype(np.int16)
    if mask is not None:
        k[~mask] = CLEAR
    return k.tobytes()

# Solid cells with art Gen 3 cannot use: the Dark Cave mouth (HGSS warp 0x6E into Dark Cave's
# Route 45 side, which is not built).
SOLID = {'D': "HGSS warps into Dark Cave's Route 45 side here; that map is not built, so the mouth is solid"}

def river_route(cells):
    """The Surf route back up to Blackthorn (owner review, 2026-10-26): the river runs on under
    every bridge. Returns (deck cells over the river, the bridges' other deck cells, the road
    cells either side of each bridge, the cascade cells). Walkers cross a bridge at elevation
    4 (Gen 3 offers Surf only from elevation 3, so no one surfs off a bridge), stepping on and
    off through the road cell either side at elevation 0 (a transition: none touches water);
    the deck over the river is elevation 15, which walkers at 4 and surfers at 1 both pass,
    and MB_BRIDGE_OVER_OCEAN, as Emerald's Routes 110 and 119."""
    deck = {(x, y) for y in range(H) for x in range(W) if cells[y][x]['lab'] == 'b'}
    over_river, rest, ends = set(), set(), set()
    for x, y in deck:
        top = min(yy for xx, yy in deck if xx == x and abs(yy - y) <= 2)
        bottom = max(yy for xx, yy in deck if xx == x and abs(yy - y) <= 2)
        wet = [cells[yy][x] for yy in (top - 1, bottom + 1) if 0 <= yy < H]
        (over_river if any(E.is_river(c) for c in wet) else rest).add((x, y))
        for dx in (-1, 1):
            if (x + dx, y) not in deck and 0 <= x + dx < W:
                ends.add((x + dx, y))
    for x, y in ends:
        assert not any(E.is_river(cells[y + dy][x + dx]) for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))
                       if 0 <= x + dx < W and 0 <= y + dy < H), ('a bridge transition cell touches water', (x, y))
    falls = {(x, y) for y in E.CASCADE_ROWS for x in range(W) if E.is_river(cells[y][x])}
    return over_river, rest, ends, falls

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
    over_river, deck_rest, deck_ends, falls = river_route(cells)
    out = []
    for y in range(H):
        for x in range(W):
            t, k = int(types[y, x]), int(coll[y, x])
            lab = cells[y][x]['lab']
            c = dict(x=x, y=y, hgss_type=t, hgss_collision=k, element=lab + cells[y][x]['floor'][0])
            if lab in SOLID:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation=SOLID[lab])
            elif t == 0x3B:
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif t == 0x39:
                c.update(foot='ledge_west', behavior='MB_JUMP_WEST', collision=1, elevation=0)
            elif t == 0x10:
                c.update(foot='surf', behavior='MB_POND_WATER', collision=0, elevation=1)
            elif t == 0x15:                                     # HGSS sea water: the river, Blackthorn's lake behaviour
                c.update(foot='surf', behavior='MB_OCEAN_WATER', collision=0, elevation=1)
            elif lab == 'F' and (x, y) not in rooted:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS's offset tree crowns overhang this woods cell; no non-overlapping Gen 3 tree root fits it")
            elif t == 0x02 and not k & 0x80:
                c.update(foot='open', behavior='MB_TALL_GRASS', collision=0, elevation=3, grass=True)
            elif k & 0x80:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            # Owner review (2026-10-26): ground in place of cliff, and the river's Surf route.
            if (x, y) in E.OWNER_GROUND or (x, y) in E.RIVER_LANDING or (x, y) in E.RIVER_SHORE:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation={**{p: 'the rock top beside the row 47 ledge\'s east end is road, so the ledge meets a wall'
                                        for p in E.LEDGE_END_GROUND},
                                     **{p: 'stairs down the shore at the river\'s foot, where the Surf route back up starts'
                                        for p in E.RIVER_SHORE},
                                     **{p: 'stairs down the bank to the river below Blackthorn, where the Surf route back up lands'
                                        for p in E.RIVER_LANDING}}[(x, y)])
            elif (x, y) in falls:
                c.update(foot='surf', behavior='MB_WATERFALL', collision=0, elevation=1,
                         adaptation='HGSS\'s cascade, a Gen 3 waterfall: Surf slides down it, Waterfall climbs it')
            elif lab == 'X' and E.is_river(cells[y][x]):
                c.update(foot='surf', behavior='MB_OCEAN_WATER', collision=0, elevation=1,
                         adaptation='HGSS blocks the river beside a bridge; it runs on here, for the Surf route back up')
            elif (x, y) in over_river:
                c.update(foot='open', behavior='MB_BRIDGE_OVER_OCEAN', collision=0, elevation=15, bridge=True,
                         adaptation='bridge deck over the river: walkers cross it, surfers pass under')
            elif (x, y) in deck_rest:
                c.update(elevation=4, adaptation='bridge deck: walkers cross at elevation 4, so no one surfs off a bridge')
            elif (x, y) in deck_ends:
                c.update(elevation=0, adaptation='road at a bridge end: the step between elevation 3 and the deck\'s 4')
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
    under the player wherever they are. A bridge deck over the river (owner bridge_deck) is
    above: a surfer passes under it, and a walker on it, at elevation 4, is drawn over it."""
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
            out[y, x] = ('' in names and (top[sl][..., 3] > 0).any()) or 'bridge_deck' in names or \
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
