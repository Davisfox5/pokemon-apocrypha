"""Audit the installed Route 45, and Blackthorn City beside it, from their native files.

    python3 tools/gba/maps/route45/check3.py ENGINE_CHECKOUT PHG_CHECKOUT

Decodes data/layouts/Route45 and data/layouts/BlackthornCity with their installed tileset pairs
exactly as the game composes them (a bottom-layer index 0 shows the backdrop) and checks: Route
45's decode equals the packer's and its assembled art on every pixel; Blackthorn's decode, with
the metatiles appended to its tables, equals its decode as committed on BASE (no Blackthorn
pixel changed); every Route 45 pixel Blackthorn's tilesets ever draw (assemble.views), decoded
with Blackthorn's installed pair the way the engine draws a connection, equals Route 45's; every
Blackthorn pixel Route 45's tilesets ever draw equals Blackthorn's; the connection both ways and
matching collision and elevation across the seam; behaviour, collision, elevation and layer
type per cell against the traversal ledger; movement as Gen 3 moves (gen3_reach: elevation,
ledges, Surf on and off, waterfalls): on foot HGSS's own reach plus the owner review's ground,
every ledge one way, the river entered and left only at its shore at the foot and the landing
below Blackthorn, and the Surf route from the one up the cascades and under the bridges to the
other; walk-behind layering; budgets; shared masters byte-identical; only Route 45 files,
Blackthorn's connection and its appended metatiles, and the shared registration files changed.

Material audit (docs/GBA_MAP_RECONSTRUCTION.md section 4): every decoded Route 45 pixel is
classified by colour against vocabularies built from the source masters, never from the
layout's labels, and each cell compared with what HGSS's flat decode shows there. Writes
evidence/pack3/{native-audit.json, material-audit.json, native-grid.png}.
"""
from __future__ import annotations
import hashlib, io, json, subprocess, sys, tempfile
from collections import Counter, deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import build as B                                   # noqa: E402
import pack as P                                    # noqa: E402
import elements as E                                # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-45'
SRC, EV = ART / 'source', ART / 'evidence'
OUT = EV / 'pack3'
W, H = 32, 160
NW, NH, NDY = 64, 64, 64                            # Blackthorn City; its y = Route 45's y + 64
BASE = 'origin/claude/blackthorn-city'
NB_SEC = 'data/tilesets/secondary/blackthorn_city'
LAYOUTS = {'route45': ('Route45', 'cherrygrove', 'route_45', W, H), 'blackthorn': ('BlackthornCity', 'cherrygrove', 'blackthorn_city', NW, NH)}

def rgba(p): return np.array(Image.open(p).convert('RGBA'))
def c5set(a, m=None):
    a = np.asarray(a)
    px = a[..., :3][a[..., 3] > 0] if a.shape[-1] == 4 and m is None else (a[m] if m is not None else a.reshape(-1, 3))
    return {tuple(c) for c in (px.astype(int) >> 3).tolist()}

# --------------------------------------------------------------------------- native decode
def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def decode(g, layout, pfolder, sfolder, w, h, grid=None):
    """Decode a layout's map.bin (or the given grid of metatile ids) with the tileset pair
    (pfolder, sfolder). Ids past the pair's tables draw nothing."""
    prim, sec = g / f'data/tilesets/primary/{pfolder}', g / f'data/tilesets/secondary/{sfolder}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [np.array(B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal')) for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    pad = 512 - len(pm[:512])
    metas = list(pm[:512]) + [np.zeros(8, np.uint16)] * pad + list(sm)
    attrs = list(pa[:512]) + [0] * pad + list(sa)
    if grid is None:
        grid = np.frombuffer((g / f'data/layouts/{layout}/map.bin').read_bytes(), '<u2').reshape(h, w)
    hh, ww = grid.shape
    img = np.zeros((hh * 16, ww * 16, 3), np.uint8)
    beh, layer, coll, elev = (np.zeros((hh, ww), np.int32) for _ in range(4))
    for y, x in np.ndindex(hh, ww):
        v = int(grid[y, x]); m = v & 1023
        coll[y, x], elev[y, x] = (v >> 10) & 3, v >> 12
        if m >= len(metas):
            continue
        beh[y, x], layer[y, x] = int(attrs[m]) & 0xFF, (int(attrs[m]) >> 12) & 3
        for i, e in enumerate(metas[m]):
            e = int(e); t = tiles[e & 1023] if (e & 1023) < len(tiles) else np.zeros((8, 8), np.uint8)
            if e & 1024: t = t[:, ::-1]
            if e & 2048: t = t[::-1]
            q = i % 4; oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
            sub = img[oy:oy + 8, ox:ox + 8]
            if i >= 4:
                sub[t > 0] = pals[e >> 12][t[t > 0]]
            else:
                sub[:] = np.where(t[..., None] > 0, pals[e >> 12][t], pals[0][0])
    return img, beh, layer, coll, elev, len(st), len(sm), len(pm), grid

def base_checkout(g, tmp):
    """Blackthorn's map and tileset pair as committed on BASE, written under tmp for decode()."""
    for rel in ('data/layouts/BlackthornCity/map.bin', f'{NB_SEC}/tiles.png', f'{NB_SEC}/metatiles.bin',
                f'{NB_SEC}/metatile_attributes.bin', 'data/tilesets/primary/cherrygrove/tiles.png',
                'data/tilesets/primary/cherrygrove/metatiles.bin', 'data/tilesets/primary/cherrygrove/metatile_attributes.bin',
                *[f'{d}/palettes/{b:02}.pal' for d in ('data/tilesets/primary/cherrygrove', NB_SEC) for b in range(16)]):
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:{rel}']))
    return tmp

def reach(foot, starts, surf):
    """Cells reachable from the seam, on foot (ledges one way) or with Surf as well."""
    seen = set(starts); q = deque(starts)
    passable = ('open', 'door', 'surf') if surf else ('open', 'door')
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if foot.get(n) in passable:
                if n not in seen:
                    seen.add(n); q.append(n)
            else:
                land = (x + 2 * dx, y + 2 * dy)
                if (foot.get(n), dx, dy) in (('ledge_south', 0, 1), ('ledge_west', -1, 0)) and foot.get(land) in passable and land not in seen:
                    seen.add(land); q.append(land)
    return seen

# --------------------------------------------------------------------------- material audit
def vocab():
    from claude_cherrygrove import ground as G
    import assemble as A
    sh, la = SRC / 'shared-art', SRC / 'local-art'
    pieces = E.frlg_pieces(ENGINE)
    ramp = {i for group in ('nine', 'rock', 'inner', 'ledge') for p in pieces[group].values() for i in p.ravel().tolist() if i >= 0}
    tex = E.cherry_textures()
    grass = c5set(tex['grass'])
    ground = np.array(Image.open(EV / 'assemble/ground.png').convert('RGB'))
    return dict(
        lawn=grass | {tuple(np.array(c) >> 3) for c in G.PROFILES[(G.GRASS, G.PATH)][0]} | c5set(rgba(la / 'flowers.png')),
        road=c5set(tex['sand']) | {tuple(np.array(c) >> 3) for c in G.PROFILES[(G.GRASS, G.PATH)][1]},
        rock={tuple(np.array(E.ROCK_RAMP[i]) >> 3) for i in ramp} | c5set(rgba(la / 'boulders.png')),
        water=c5set(tex['water']) | c5set(rgba(la / 'cascades.png')), bank=c5set(rgba(la / 'water-banks.png')) - grass,
        tall=c5set(rgba(sh / 'G15.png')), stairs=set().union(*(c5set(rgba(sh / f'S0{i}.png')) for i in range(1, 6))),
        cave={tuple(np.array(A.CAVE_DARK) >> 3), tuple(np.array(E.ROCK_RAMP[0]) >> 3)}, dirt=c5set(ground[148 * 16:152 * 16, :32]) - grass,
        bridge={tuple(np.array(c) >> 3) for c in A.WOOD},
        tree=c5set(rgba(sh / 'T01.png')), sign=c5set(rgba(sh / 'P13.png')) | c5set(rgba(sh / 'P14.png')))

OBJECTS = ('tree', 'sign')
TERRAIN = ('lawn', 'road', 'rock', 'water', 'bank', 'tall', 'stairs', 'cave', 'dirt', 'bridge')
WATER_MATERIALS = ('river', 'river_r', 'pond_un', 'none')         # 'none': HGSS's cascades, a model over the river
RIM_MATERIALS = ('pond_line',)                                    # HGSS's pond rim: drawn as the natural bank
MODEL_CLASS = {31: 'sign', 32: 'sign'}

def hgss_classes(phg):
    """Per pixel, what HGSS shows, decoded flat: water, its rim (the bank class: the native
    draws it as the owner-approved natural bank), tall grass, stairs, the Dark Cave mouth,
    bridges, cliffs and boulders, trees, Route 46's dirt, lawn or road by its own colours,
    then its sign models."""
    h, mat, names, rgb = E.topdown(phg)
    nm = np.array(names + ['none'])
    m = nm[np.where(mat >= 0, mat, len(names))]
    rgb = rgb.astype(int)
    cls = np.full((H * 16, W * 16), '', object)
    cls[(rgb[..., 1] > rgb[..., 0] + 20)] = 'lawn'
    cls[(rgb[..., 0] >= rgb[..., 1]) & (rgb[..., 0] > 180) & (rgb[..., 2] < 175)] = 'road'
    cls[np.isin(m, E.ROCK_MATERIALS) | (m == 'rock01')] = 'rock'
    cls[np.isin(m, WATER_MATERIALS)] = 'water'
    cls[np.isin(m, RIM_MATERIALS)] = 'bank'
    cls[np.isin(m, ('road05', 'road05_sub'))] = 'dirt'
    cls[np.char.startswith(m.astype(str), 'egrass')] = 'tall'
    cls[m == 'slope'] = 'stairs'
    cls[m == 'cavehole'] = 'cave'
    cls[m == 'bridge_a'] = 'bridge'
    cls[np.isin(m, E.TREE_MATERIALS)] = 'tree'
    own = np.load(SRC / 'hgss/hgss-foreground-owner.npz')['owner']
    models = [b['model'] for b in json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']]
    for i, mm in enumerate(models):
        if mm in MODEL_CLASS:
            cls[own == i] = MODEL_CLASS[mm]
    return cls

def material_audit(img, phg):
    """Square by square: native classes from decoded colours (each colour votes for every
    vocabulary that holds it), HGSS classes from the flat decode. A terrain cell matches when
    the native's leading terrain material is one HGSS shows there (at least 24 px); an object
    cell when the same kind of object leads in both. Cells where an object leads in one but
    terrain in the other are foreground differences, not counted as matches."""
    v = vocab()
    owner = {}
    for k, s_ in v.items():
        for c in s_:
            owner.setdefault(c, set()).add(k)
    hc = hgss_classes(phg)
    c5 = img.astype(int) >> 3
    rows, mism, fg_diff, unknown = [], [], [], Counter()
    for y in range(H):
        for x in range(W):
            px = c5[y * 16:y * 16 + 16, x * 16:x * 16 + 16].reshape(-1, 3)
            votes = Counter()
            for c in map(tuple, px.tolist()):
                o = owner.get(c)
                if o is None:
                    unknown[c] += 1
                for k in o or ():
                    votes[k] += 1
            hv = Counter(hc[y * 16:y * 16 + 16, x * 16:x * 16 + 16].ravel().tolist())
            hv.pop('', None)
            native_obj = max((votes[k] for k in OBJECTS), default=0) >= 128
            hgss_obj = max((hv[k] for k in OBJECTS), default=0) >= 128
            nat_lead = max(OBJECTS if native_obj else TERRAIN, key=lambda k: votes[k])
            h_lead = max(OBJECTS if hgss_obj else TERRAIN, key=lambda k: hv[k])
            if native_obj != hgss_obj:
                status = 'foreground differs'
            elif native_obj:
                status = 'match' if votes[h_lead] >= 64 else 'mismatch'
            else:
                status = 'match' if hv[nat_lead] >= 24 or votes[h_lead] >= 24 else 'mismatch'
            row = dict(cell=[x, y], status=status, native_lead=nat_lead, hgss_lead=h_lead,
                       native=dict(votes.most_common(4)), hgss=dict(hv.most_common(4)))
            rows.append(row)
            if status == 'mismatch':
                mism.append(row)
            elif status == 'foreground differs':
                fg_diff.append(row)
    return rows, mism, fg_diff, unknown

def hgss_reach():
    """The cells HGSS's own permissions reach from Blackthorn's edge, on foot and with Surf
    (ledges one way): the native must reach exactly these."""
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    foot = {}
    for y, x in np.ndindex(H, W):
        t = int(types[y, x])
        foot[(x, y)] = ('ledge_south' if t == 0x3B else 'ledge_west' if t == 0x39 else 'surf' if t in (0x10, 0x15)
                        else 'blocked' if coll[y, x] & 0x80 else 'open')
    return reach(foot, [(x, 0) for x in range(W) if foot[(x, 0)] in ('open', 'surf')], True)

def gen3_reach(beh, coll, elev, walk_starts, surf=True):
    """Where a player gets on the installed Route 45, moving as Gen 3 moves: a step needs
    collision 0 and no elevation mismatch (the player's elevation and the cell's differ, neither
    0 nor 15 for the cell, the player's not 0); entering a cell takes its elevation unless it or
    the cell left is 15; a ledge jumps one way when the cell beyond is a step; Surf starts from
    elevation 3 onto surfable water across a mismatch, and stops onto an elevation-3 cell; a
    waterfall is climbed north and slid down south (HM Waterfall). Off the map is blocked.
    Returns (walked cells, surfed cells, surf entries as (land, water), dismounts as
    (water, land))."""
    names = {v: k for k, v in B.behaviors(ENGINE).items()}
    b = lambda x, y: names[int(beh[y, x])]
    inside = lambda x, y: 0 <= x < W and 0 <= y < H
    mismatch = lambda e, x, y: e != 0 and elev[y, x] not in (0, 15) and elev[y, x] != e
    surfable = lambda x, y: b(x, y) in ('MB_OCEAN_WATER', 'MB_POND_WATER', 'MB_WATERFALL')
    jumps = {(0, 1): 'MB_JUMP_SOUTH', (-1, 0): 'MB_JUMP_WEST', (1, 0): 'MB_JUMP_EAST', (0, -1): 'MB_JUMP_NORTH'}
    start = [(x, y, 'walk', int(elev[y, x])) for x, y in walk_starts]
    seen = set(start); q = deque(start)
    walked, surfed, entries, dismounts = set(), set(), set(), set()
    while q:
        x, y, mode, e = q.popleft()
        (walked if mode == 'walk' else surfed).add((x, y))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not inside(nx, ny):
                continue
            nxt = None
            if mode == 'walk':
                if b(nx, ny) == jumps[(dx, dy)]:
                    lx, ly = nx + dx, ny + dy
                    if inside(lx, ly) and not coll[ly, lx] and not mismatch(e, lx, ly) and not surfable(lx, ly):
                        nxt = (lx, ly, 'walk', e if elev[ly, lx] == 15 else int(elev[ly, lx]))
                elif not coll[ny, nx] and not mismatch(e, nx, ny) and not surfable(nx, ny):
                    keep = elev[ny, nx] == 15 or elev[y, x] == 15
                    nxt = (nx, ny, 'walk', e if keep else int(elev[ny, nx]))
                elif surf and e == 3 and not coll[ny, nx] and mismatch(e, nx, ny) and surfable(nx, ny):
                    nxt = (nx, ny, 'surf', 1); entries.add(((x, y), (nx, ny)))
            else:
                if not coll[ny, nx] and not mismatch(1, nx, ny):
                    nxt = (nx, ny, 'surf', 1)
                elif not coll[ny, nx] and elev[ny, nx] == 3:
                    nxt = (nx, ny, 'walk', 3); dismounts.add(((x, y), (nx, ny)))
            if nxt and nxt not in seen:
                seen.add(nxt); q.append(nxt)
    return walked, surfed, entries, dismounts

def hgss_foot_reach():
    """The cells HGSS's own permissions reach from Blackthorn's edge on foot (ledges one way)."""
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    foot = {}
    for y, x in np.ndindex(H, W):
        t = int(types[y, x])
        foot[(x, y)] = ('ledge_south' if t == 0x3B else 'ledge_west' if t == 0x39 else 'surf' if t in (0x10, 0x15)
                        else 'blocked' if coll[y, x] & 0x80 else 'open')
    return reach(foot, [(x, 0) for x in range(W) if foot[(x, 0)] == 'open'], False)

ENGINE = None

# Places along HGSS's road, from Blackthorn down to the river's mouth, the player reaches on foot
# from the seam (ledges one way, as in HGSS).
APPROACHES = dict(seam_road=(23, 1), route_sign=(23, 8), dark_cave_front=(10, 7), first_bridge=(18, 8), second_bridge=(10, 17),
                  west_tall_grass=(5, 25), east_tall_grass=(20, 21), north_stairs_foot=(26, 24), west_stairs_foot=(6, 38),
                  third_bridge=(11, 42), mid_tall_grass=(18, 57), diagonal_stairs=(19, 58), fourth_bridge=(13, 62),
                  fifth_bridge=(13, 85), lower_stairs=(16, 97), island_road=(9, 110), sixth_bridge=(14, 118),
                  south_lawn=(7, 133), pond_lawn=(26, 137), last_bridge=(14, 147), west_stairs=(0, 139))
# HGSS's Route 46 dirt at the west edge (0-1, 148-151, with a hidden item at (0, 149)) is reached
# from Route 46 alone, which is not built: it is listed among the unreachable open cells.

def main(g, phg):
    global ENGINE
    ENGINE = g
    MB = B.behaviors(g)
    r45 = decode(g, *LAYOUTS['route45'])
    nb = decode(g, *LAYOUTS['blackthorn'])
    img = r45[0]
    # Route 45: installed decode = packer decode = assembled art.
    assert (B.rgb5(img) == B.rgb5(np.array(Image.open(OUT / 'native.png').convert('RGB')))).all(), 'differs from the pack decode'
    z = np.load(SRC / 'assemble/layers.npz')
    want = z['ground'].copy()
    for layer_ in (z['rock'], z['objects']):
        a = layer_[..., 3] > 0
        want[a] = layer_[a, :3]
    assert (B.rgb5(img) == B.rgb5(want)).all(), 'differs from the assembled art'
    # Blackthorn: every pixel as committed on BASE.
    with tempfile.TemporaryDirectory() as tmp:
        accepted = decode(base_checkout(g, Path(tmp)), *LAYOUTS['blackthorn'])[0]
    assert (B.rgb5(nb[0]) == B.rgb5(accepted)).all(), 'Blackthorn pixels changed'
    # The seam, from the installed files: each map's grid drawn with the other's tileset pair.
    view, nview = z['blackthorn_view'], z['route_view_of_blackthorn']
    seen_r = decode(g, 'Route45', 'cherrygrove', 'blackthorn_city', W, H, grid=r45[8])[0]
    d = (B.rgb5(seen_r) != B.rgb5(img)).any(-1) & view
    assert not d.any(), ('Route 45 pixels Blackthorn shows differ under Blackthorn\'s tilesets', int(d.sum()))
    seen_n = decode(g, 'BlackthornCity', 'cherrygrove', 'route_45', NW, NH, grid=nb[8])[0]
    d = (B.rgb5(seen_n) != B.rgb5(nb[0])).any(-1) & nview
    assert not d.any(), ('Blackthorn pixels Route 45 shows differ under Route 45\'s tilesets', int(d.sum()))
    r45_map = json.loads((g / 'data/maps/Route45/map.json').read_text())
    nb_map = json.loads((g / 'data/maps/BlackthornCity/map.json').read_text())
    assert r45_map['connections'] == [dict(map='MAP_BLACKTHORN_CITY', offset=0, direction='up')]
    assert nb_map['connections'] == [dict(map='MAP_ROUTE45', offset=0, direction='down')]
    border_r = (g / 'data/layouts/Route45/border.bin').read_bytes()
    assert border_r == (g / 'data/layouts/BlackthornCity/border.bin').read_bytes(), 'border blocks differ'
    # Ledger.
    trav = json.loads((SRC / 'pack3/traversal.json').read_text())
    _, beh, layer, coll, elev = r45[:5]
    for c in trav:
        x, y = c['x'], c['y']
        assert beh[y, x] == MB[c['behavior']], (x, y, c['behavior'])
        assert coll[y, x] == c['collision'] and elev[y, x] == c['elevation'], (x, y)
        assert layer[y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    foot = {(c['x'], c['y']): c['foot'] for c in trav}
    # The seam: Route 45's top row and Blackthorn's bottom row agree on collision and elevation.
    nbc, nbe = nb[3], nb[4]
    seam_diff = [x for x in range(W) if (coll[0, x], elev[0, x]) != (nbc[NH - 1, x], nbe[NH - 1, x])]
    assert not seam_diff, ('collision or elevation differs across the seam', seam_diff)
    walk = lambda f: f in ('open', 'door')
    crossing = [x for x in range(W) if foot[(x, 0)] in ('open', 'surf') and not nbc[NH - 1, x]]
    # Reachability from the seam, moving as Gen 3 moves (gen3_reach).
    road = [(x, 0) for x in crossing if walk(foot[(x, 0)])]
    seen = gen3_reach(beh, coll, elev, road, surf=False)[0]
    walked, surfed, entries, dismounts = gen3_reach(beh, coll, elev, road)
    open_cells = {k for k, v in foot.items() if walk(v)}
    water = {k for k, v in foot.items() if v == 'surf'}
    # On foot, HGSS's own reach, less the Dark Cave warp (solid here, pack.SOLID), plus the
    # cells the owner review made ground (elements.OWNER_GROUND) that the road reaches.
    warps = {tuple(c['cell']) for c in json.loads((SRC / 'hgss-events.json').read_text())['warps']}
    hgss_foot = hgss_foot_reach() - warps
    assert hgss_foot <= seen and seen - hgss_foot <= set(E.OWNER_GROUND) | E.RIVER_LANDING, \
        ('reach on foot differs from HGSS\'s beyond the owner review\'s ground', sorted(hgss_foot ^ seen)[:20])
    # The ledges are one way on foot: from below a ledge, nothing above it is reached.
    for c in trav:
        if c['behavior'] in ('MB_JUMP_SOUTH', 'MB_JUMP_WEST'):
            x, y = c['x'], c['y']
            up, down = ((x, y - 1), (x, y + 1)) if c['behavior'] == 'MB_JUMP_SOUTH' else ((x + 1, y), (x - 1, y))
            if walk(foot.get(up)) and walk(foot.get(down)):
                assert up not in gen3_reach(beh, coll, elev, [down], surf=False)[0], ('a ledge can be walked round', (x, y))
    # The river (owner review): Surf gets on and off it only at its shore at the foot and at the
    # landing below Blackthorn (the pond is HGSS's own, apart from it); no one surfs off a bridge.
    river_ends = set(E.RIVER_SHORE) | set(E.RIVER_LANDING)
    names = {v: k for k, v in MB.items()}
    on_river = lambda w: names[int(beh[w[1], w[0]])] != 'MB_POND_WATER'
    bad_in = sorted(l for l, w in entries if on_river(w) and l not in river_ends)
    bad_out = sorted(l for w, l in dismounts if on_river(w) and l not in river_ends)
    assert not bad_in and not bad_out, ('the river is entered or left elsewhere', bad_in, bad_out)
    # The return route: from the shore at the foot, Surf, Waterfall up the three cascades and
    # under the seven bridges, land below Blackthorn and walk on into it; on foot alone the
    # ledges keep the shore from Blackthorn.
    shore = sorted(E.RIVER_SHORE)[0]
    up_walk, up_surf, _, up_out = gen3_reach(beh, coll, elev, [shore])
    falls = {(c['x'], c['y']) for c in trav if c['behavior'] == 'MB_WATERFALL'}
    decks = {(c['x'], c['y']) for c in trav if c['behavior'] == 'MB_BRIDGE_OVER_OCEAN'}
    assert falls <= up_surf and decks <= up_surf, ('the Surf route misses a cascade or a bridge', sorted(falls - up_surf), sorted(decks - up_surf))
    assert set(E.RIVER_LANDING) & {l for _, l in up_out} and set(road) <= up_walk, 'the Surf route does not reach Blackthorn'
    assert not set(road) & gen3_reach(beh, coll, elev, [shore], surf=False)[0], 'the shore reaches Blackthorn on foot'
    surf_route = dict(start=list(shore), landing=sorted(l for _, l in up_out if l in E.RIVER_LANDING), waterfalls=len(falls),
                      bridge_deck_cells_passed_under=len(decks), river_entries=sorted({l for l, w in entries if on_river(w)}),
                      river_exits=sorted({l for w, l in dismounts if on_river(w)}))
    missing = {k: p for k, p in APPROACHES.items() if p not in seen}
    assert not missing, ('unreachable approach', missing)
    # Walk-behind layering.
    top, owner = z['objects'], z['owner']
    walkable = np.array([[walk(foot[(x, y)]) for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, top, np.zeros_like(top), owner)
    seam_cells = {tuple(s['cell']) for s in json.loads((OUT / 'pack.json').read_text())['seam']}
    walk_behind = Counter()
    for y, x in np.ndindex(H, W):
        if (x, y) in seam_cells:
            continue                                       # these take Blackthorn's metatiles and their attributes
        assert layer[y, x] == (0 if above[y, x] else 1), ('layer type', x, y)
        if above[y, x]:
            cell = top[y * 16:y * 16 + 16, x * 16:x * 16 + 16][..., 3] > 0
            for o in set(owner[y * 16:y * 16 + 16, x * 16:x * 16 + 16][cell].ravel()) - {''}:
                if not o.startswith(P.FLAT[0]):
                    walk_behind[o.split('_')[0]] += 1
    seam_layers = Counter((bool(walkable[y, x]), int(layer[y, x])) for x, y in seam_cells)
    # Shared masters, budgets, scope.
    prov = json.loads((SRC / 'shared-art/provenance.json').read_text())
    shared_ok = {n: hashlib.sha256((SRC / 'shared-art' / n).read_bytes()).hexdigest() == r['sha256']
                 for n, r in prov.items() if isinstance(r, dict) and 'sha256' in r}
    assert all(shared_ok.values()), shared_ok
    budgets = dict(secondary_tiles=r45[5], secondary_metatiles=r45[6], primary_metatiles=r45[7],
                   blackthorn_secondary_metatiles=nb[6], blackthorn_secondary_tiles=nb[5])
    assert budgets['secondary_tiles'] <= 496 and budgets['secondary_metatiles'] <= 512 and budgets['primary_metatiles'] <= 512, budgets
    assert budgets['blackthorn_secondary_tiles'] <= 496 and budgets['blackthorn_secondary_metatiles'] <= 512, budgets
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        if isinstance(values, list):
            assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
               'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
               'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h', 'data/maps/BlackthornCity/map.json',
               f'{NB_SEC}/metatiles.bin', f'{NB_SEC}/metatile_attributes.bin', f'{NB_SEC}/tiles.png'}
    prefixes = ('data/layouts/Route45/', 'data/maps/Route45/', 'data/tilesets/secondary/route_45/')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    mt_before = subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:{NB_SEC}/metatiles.bin'])
    mt_now = (g / NB_SEC / 'metatiles.bin').read_bytes()
    assert mt_now[:len(mt_before)] == mt_before, 'Blackthorn\'s own metatiles changed'
    nb_diff = subprocess.check_output(['git', '-C', str(g), 'diff', BASE, '--', 'data/maps/BlackthornCity/map.json'], text=True)
    assert all(l.strip(' -+,{}[]"') in ('', 'connections": null', 'connections":', 'map": "MAP_ROUTE45', 'offset": 0', 'direction": "down')
               for l in nb_diff.splitlines() if l[:1] in '+-' and not l.startswith(('+++', '---'))), nb_diff
    old_tiles = np.array(Image.open(io.BytesIO(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:{NB_SEC}/tiles.png']))))
    assert (np.array(Image.open(g / NB_SEC / 'tiles.png'))[:old_tiles.shape[0]] == old_tiles).all(), 'Blackthorn tiles changed'
    # Material audit.
    rows, mism, fg_diff, unknown = material_audit(img, phg)
    (OUT / 'material-audit.json').write_text(json.dumps(dict(
        method=material_audit.__doc__.strip(), cells=len(rows), matches=sum(r['status'] == 'match' for r in rows),
        mismatches=mism, foreground_differs=fg_diff, unclassified_colours={str(k): n for k, n in unknown.most_common(20)},
        per_cell=rows), indent=1) + '\n')
    big = Image.fromarray(img).resize((W * 24, H * 24), Image.Resampling.NEAREST); d = ImageDraw.Draw(big)
    for i in range(W):
        d.line((i * 24, 0, i * 24, H * 24), fill=(60, 60, 70)); d.text((i * 24 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        d.line((0, i * 24, W * 24, i * 24), fill=(60, 60, 70)); d.text((2, i * 24 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for m_ in mism:
        x, y = m_['cell']
        d.rectangle((x * 24, y * 24, x * 24 + 23, y * 24 + 23), outline=(255, 0, 255), width=2)
    for m_ in fg_diff:
        x, y = m_['cell']
        d.rectangle((x * 24 + 2, y * 24 + 2, x * 24 + 21, y * 24 + 21), outline=(0, 220, 255), width=1)
    big.save(OUT / 'native-grid.png')
    result = dict(route45_matches_pack_decode_and_assembled_art=True, blackthorn_pixels_unchanged=True,
                  route45_pixels_blackthorn_shows_exact=int(view.sum()), blackthorn_pixels_route45_shows_exact=int(nview.sum()),
                  connections=dict(route45=r45_map['connections'], blackthorn=nb_map['connections']), border_shared=True,
                  ledger_behaviour_collision_elevation_layer=True, seam_crossing_columns=crossing, seam_collision_elevation_match=True,
                  reachable_foot_cells=len(seen), open_cells=len(open_cells), unreachable_open_cells=sorted(open_cells - seen),
                  surf_reachable_cells=len(surfed), water_cells=len(water), unreached_water_cells=sorted(water - surfed),
                  reach_on_foot_is_hgss_plus_owner_ground=True, ledges_one_way=True, surf_route=surf_route,
                  approaches=APPROACHES, walk_behind_cells=dict(walk_behind),
                  seam_cells_walkable_layer=[[k[0], k[1], n] for k, n in sorted(seam_layers.items())],
                  shared_masters_byte_identical=shared_ok, budgets=budgets,
                  existing_map_ids_preserved=True, changed_files_within_scope=True, blackthorn_metatiles_unchanged=True,
                  blackthorn_map_json_only_connection=True, material_cells=len(rows),
                  material_matches=sum(r['status'] == 'match' for r in rows),
                  material_mismatches=[m_['cell'] for m_ in mism], foreground_differs=[m_['cell'] for m_ in fg_diff])
    (OUT / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('approaches', 'shared_masters_byte_identical', 'foreground_differs',
                                                                    'unreachable_open_cells', 'unreached_water_cells', 'material_mismatches')}))
    print('unreachable open cells', sorted(open_cells - seen)[:40], len(open_cells - seen))
    print('unreached water', len(water - surfed), 'mismatches', [m_['cell'] for m_ in mism][:40], len(mism), 'foreground differs', len(fg_diff))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
