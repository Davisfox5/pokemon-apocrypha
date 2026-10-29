"""Route 46: one lossless pack beside Route 45's tilesets, so the two can be joined by a
map connection with Route 45 drawn exactly as its own pack draws it.

    python3 tools/gba/maps/route46/pack_fixed.py ENGINE_CHECKOUT PHG_CHECKOUT

HGSS joins Route 46's east edge to Route 45's west edge (Route 46 (x, y) = Route 45 (x - 32,
y + 128)). A Gen 3 connection draws the neighbouring map's metatiles with the current map's
tilesets, and crossing it reloads only the secondary tileset (the tiles already on screen
stay). So:

- Route 46's primary tileset is Route 45's (gTileset_CherrygrovePrimary: tiles 0-511, palettes
  0-5, metatiles 0-511). Route 46 reuses any of its tiles that draw a Route 46 tile exactly,
  the animated sea among them.
- Route 46's secondary tileset carries exact copies of everything the Route 45 cells Route
  46's tilesets ever draw (assemble.views: Route 45's west columns by its foot) use from
  Route 45's secondary: those metatiles at Route 45's ids, their tiles at
  Route 45's tile indices, and the palette slots they use. Everything else is Route 46's own
  (free tile indices, the other slots of those banks and the free banks, free metatile ids).
- The part of Route 46 Route 45's tilesets ever draw (assemble.views: Route 46's east columns) is
  drawn with Route 45's metatiles: a cell whose art equals one of Route 45's metatiles uses
  that metatile (and its attributes). A cell only partly in view uses a Route 45 secondary
  metatile id whose visible quadrants draw the same in both maps (Route 46 defines the rest
  of it). A cell no Route 45 metatile draws is a new metatile appended to Route 45's
  tables, built from quadrants of Route 45's own metatiles or from new tiles after
  Route 45's own; no Route 45 cell uses it.

Lossless as before: every visible native pixel keeps its assembled colour in RGB555, palette
banks are exact colour sets, tiles dedupe only under a flip, and the only compaction is a
bottom tile hidden under fully opaque top-layer art. The script fails if the art does not fit,
and proves: Route 46 decoded with its pair equals its assembled art; every Route 46 pixel
Route 45 can show, decoded with Route 45's pair (with the appended metatiles), equals it
too; every Route 45 pixel Route 46 can show, decoded with Route 46's pair, equals Route 45's
own decode; Route 45 decoded with the appended tables is unchanged.

Reads gba/art/route-46/source/assemble/layers.npz and Route 45's tilesets and map as committed
on BASE; writes gba/art/route-46/source/pack3/{pack.npz, traversal.json} and evidence/pack3/
{pack.json, native.png, seam-*.png}.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import build as B                                   # noqa: E402
import pack as P                                    # noqa: E402
import pack_lossless as PL                          # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-46'
SRC, EV = ART / 'source', ART / 'evidence'
OUT_SRC, OUT_EV = SRC / 'pack3', EV / 'pack3'
W, H = 32, 70
MW, MH = 32, 160                                     # Route 45, the neighbour (owner-accepted, locked)
PRIMARY_BANKS, BANKS = 6, 13
PRIMARY_TILES, TILES, METAS = 512, 1008, 512
MAH_PRIMARY, MAH_SECONDARY = 'data/tilesets/primary/cherrygrove', 'data/tilesets/secondary/route_45'
NB_LAYOUT = 'data/layouts/Route45'

# --------------------------------------------------------------------------- Route 45's tilesets
class Pair:
    """A tileset pair as the engine sees it: tile index patterns (0-1023), 13 palette banks in
    RGB555, metatile entries and attributes by id."""
    def __init__(self):
        self.tiles, self.pals, self.metas, self.attrs = {}, {}, {}, {}

    def decode(self, mid, layers=(0, 1)):
        """16x16 RGB555 of metatile mid (bottom layer, then top over it) and its opaque mask."""
        img = np.zeros((16, 16, 3), np.int32)
        ents = self.metas[mid]
        for li in range(8):
            if li // 4 not in layers:
                continue
            e = ents[li]
            ix = self.tiles.get(e & 1023, np.zeros((8, 8), np.uint8))
            if e & 0x400: ix = ix[:, ::-1]
            if e & 0x800: ix = ix[::-1]
            q = li % 4
            sub = img[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            if li >= 4:
                m = ix > 0
                sub[m] = self.pals[e >> 12][ix[m]]
            else:                                         # bottom index 0 shows the backdrop (bank 0 colour 0)
                sub[:] = np.where(ix[..., None] > 0, self.pals[e >> 12][ix], self.pals[0][0])
        return img

BASE = 'origin/claude/route-45'                      # Route 45 as its own branch has it (engine PR #43)

def accepted(engine, rel):
    """A Route 45 file as committed at BASE (an earlier Route 46 install appends to it)."""
    import subprocess
    return subprocess.run(['git', '-C', str(engine), 'show', f'{BASE}:{rel}'], capture_output=True, check=True).stdout

def load_tileset(engine, rel, base, pair, banks):
    import io
    d = engine / rel
    a = np.array(Image.open(io.BytesIO(accepted(engine, f'{rel}/tiles.png'))))
    if a.ndim == 3:
        raise SystemExit(f'{rel}/tiles.png is not indexed')
    a = a & 15
    n = 0
    for ty in range(a.shape[0] // 8):
        for tx in range(a.shape[1] // 8):
            pair.tiles[base + n] = a[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].astype(np.uint8)
            n += 1
    for b in banks:
        cols = [tuple(map(int, l.split())) for l in accepted(engine, f'{rel}/palettes/{b:02}.pal').decode().replace('\r', '').splitlines()[3:19]]
        pair.pals[b] = np.array(cols, np.int32) >> 3
    mt = np.frombuffer(accepted(engine, f'{rel}/metatiles.bin'), '<u2').reshape(-1, 8)
    at = np.frombuffer(accepted(engine, f'{rel}/metatile_attributes.bin'), '<u2')
    mbase = 0 if base == 0 else 512
    for i in range(len(mt)):
        pair.metas[mbase + i] = tuple(int(v) for v in mt[i])
        pair.attrs[mbase + i] = int(at[i])
    return n, len(mt)

def neighbour(engine):
    pair = Pair()
    np_, nmp = load_tileset(engine, MAH_PRIMARY, 0, pair, range(PRIMARY_BANKS))
    ns, nms = load_tileset(engine, MAH_SECONDARY, PRIMARY_TILES, pair, range(PRIMARY_BANKS, BANKS))
    grid = np.frombuffer(accepted(engine, f'{NB_LAYOUT}/map.bin'), '<u2').reshape(MH, MW)
    for rel in (MAH_PRIMARY, MAH_SECONDARY):              # palettes are never touched by the install
        for f in [f'palettes/{b:02}.pal' for b in range(16)]:
            crlf = lambda v: v.replace(b'\r', b'')                # the checkout may carry CRLF line ends
            assert crlf((engine / rel / f).read_bytes()) == crlf(accepted(engine, f'{rel}/{f}')), (rel, f, 'differs from BASE')
    return pair, grid, dict(primary_tiles=np_, primary_metatiles=nmp, secondary_tiles=ns, secondary_metatiles=nms)

def draw(pair, ids, h, w):
    img = np.zeros((h * 16, w * 16, 3), np.int32)
    cache = {}
    for y in range(h):
        for x in range(w):
            m = int(ids[y, x]) & 1023
            if m not in pair.metas:
                continue
            if m not in cache:
                cache[m] = pair.decode(m)
            img[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = cache[m]
    return img

# --------------------------------------------------------------------------- Route 46's layers
def route46_traversal(engine, phg, z):
    trav, shared = PL.traversal(engine, phg, z['objects'], z['owner'].astype(object))
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door') for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, z['objects'], shared, z['owner'].astype(object))
    for c in trav:
        c['layer'] = 'normal' if above[c['y'], c['x']] else 'covered'
    return trav

def plan_layers(z, layer_of):
    """pack_lossless's per-8x8 layer plan: objects on the top layer over the terrain, part-rock
    tiles split onto the top layer where the cell draws under the player, overlapping objects
    split back and front, hidden bottom pixels compacted (Lake of Rage's pack_pair.plan_layers)."""
    ground, rock, top, owner, trees, gate = z['ground'], z['rock'], z['objects'].copy(), z['owner'].astype(object), z['trees'], z['gate']
    terrain = ground.copy()
    rk_all = rock[..., 3] > 0
    terrain[rk_all] = rock[rk_all, :3]
    above = np.array([[layer_of[(x, y)] == 'normal' for x in range(W)] for y in range(H)])
    # Flat ground details (pack.FLAT) ride the top layer only where the cell draws it under the
    # player; where it draws above (a crown the player walks behind) they join the bottom.
    flat = np.char.startswith(owner.astype(str), P.FLAT[0]) & (top[..., 3] > 0)
    up = np.repeat(np.repeat(above, 16, 0), 16, 1) & flat
    terrain[up] = top[up, :3]
    ground = ground.copy(); ground[up] = top[up, :3]
    rock = rock.copy(); rock[up, 3] = 0
    rk_all = rock[..., 3] > 0
    want_top = top.copy()
    top[up, 3] = 0
    common = Counter(ground[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(H * 2) for tx in range(W * 2)).most_common(1)[0][0]
    filler = np.frombuffer(common, np.uint8).reshape(8, 8, 3)
    fam = np.vectorize(PL.family)(owner)
    lay = {}
    base = np.zeros(owner.shape, np.int32)
    for name in set(owner.ravel().tolist()) - {''}:
        mm = owner == name
        base[mm] = int(np.nonzero(mm.any(1))[0].max())
    from claude_cherrygrove import ground as G
    tex = G.textures()
    yy, xx = np.mgrid[0:H * 16, 0:W * 16]
    grass_plain = tex[G.GRASS][yy % tex[G.GRASS].shape[0], xx % tex[G.GRASS].shape[1]].astype(np.uint8)
    path_plain = tex[G.PATH][yy % tex[G.PATH].shape[0], xx % tex[G.PATH].shape[1]].astype(np.uint8)

    def backing(b, vis, sl):
        for plain in (grass_plain, path_plain):
            if (plain[sl][vis] == b[vis]).all():
                return plain[sl].copy()
        if (ground[sl][vis] == b[vis]).all():
            return ground[sl].copy()
        if rk_all[sl].all() and (rock[sl][..., :3][vis] == b[vis]).all():
            return rock[sl][..., :3].copy()
        v = b[vis].reshape(-1, 3)
        cols, cnt = np.unique(v, axis=0, return_counts=True)
        b[~vis] = cols[cnt.argmax()]
        return b

    full = np.ones((8, 8), bool)
    def want_top_rgb(sl):
        w = terrain[sl].copy()
        a = top[sl][..., 3] > 0
        w[a] = top[sl][a, :3]
        return w
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            ob = top[sl][..., 3] > 0
            rk = rk_all[sl]
            fs = set(fam[sl][ob].ravel().tolist())
            merge = False
            if len(fs) > 1 and not above[ty // 2, tx // 2]:
                front = fam[sl][ob].ravel()[np.argmax(base[sl][ob].ravel())]
                # Crowns over the gate's foundation: where the crown and the foundation it leaves
                # in view fit the tree palette with the foundation's two darkest teals, both take
                # the top layer over plain lawn.
                merge = fs == {'tree', 'gate'} and front == 'tree' and colour_set(top[sl][..., :3], ob) <= MERGE_SET
                if fs == {'tree', 'gate'}:
                    front = 'gate'                         # otherwise the gate takes the top layer
            if merge:
                lay[(tx, ty, 0)] = dict(px=backing(terrain[sl].copy(), ~ob, sl), mask=full)
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=ob)
            elif len(fs) > 1 and not above[ty // 2, tx // 2]:
                gate_tree = fs == {'tree', 'gate'}
                fm = ob & (fam[sl] == front)
                bm = ob & ~fm
                b = terrain[sl].copy(); b[bm] = top[sl][bm, :3]
                if gate_tree:
                    # Round the gate (the Route 36 surround) the picture is already composed and
                    # the cell is solid, so either part may take the top layer: the gate does, and
                    # the trees lie whole below it with the lawn, in the palette trees and lawn
                    # already share, so these tiles repeat from tree to tree.
                    whole = trees
                    wa = whole[sl][..., 3] > 0
                    b[wa] = whole[sl][wa, :3]
                    assert (b[~fm] == want_top_rgb(sl)[~fm]).all()
                hide = bool(fm.all())
                lay[(tx, ty, 0)] = dict(px=filler if hide else b if gate_tree else backing(b, ~fm, sl), mask=full)
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=fm)
            elif ob.any():
                hide = bool(ob.all())
                lay[(tx, ty, 0)] = dict(px=filler if hide else backing(terrain[sl].copy(), ~ob, sl), mask=full)
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=ob)
            elif rk.all():
                lay[(tx, ty, 0)] = dict(px=rock[sl][..., :3], mask=full)
            elif rk.any() and not above[ty // 2, tx // 2]:
                lay[(tx, ty, 0)] = dict(px=backing(ground[sl].copy(), ~rk, sl), mask=full)
                lay[(tx, ty, 1)] = dict(px=rock[sl][..., :3], mask=rk)
            else:
                lay[(tx, ty, 0)] = dict(px=terrain[sl], mask=full)
    want = terrain.copy()
    a = want_top[..., 3] > 0
    want[a] = want_top[a, :3]
    a = top[..., 3] > 0
    want[a] = top[a, :3]
    return lay, want

# T01's colours and the gate foundation's two darkest teals (RGB555)
MERGE_SET = frozenset(tuple(v // 8 for v in c) for c in (
    (64, 56, 40), (64, 64, 40), (72, 72, 48), (80, 88, 40), (88, 104, 32), (88, 112, 32), (96, 120, 32),
    (112, 144, 32), (120, 152, 32), (136, 104, 64), (136, 168, 40), (24, 80, 64), (32, 144, 136)))

def colour_set(px, mask):
    return frozenset(map(tuple, B.rgb5(px)[mask].reshape(-1, 3).tolist()))

# --------------------------------------------------------------------------- the seam
def reserved_from_view(mgrid, mview):
    """Route 45's metatiles in the cells Route 46's tilesets draw, with the 8x8 quadrants of
    each that are ever in view: {id: {quadrant}}. (A primary metatile may draw secondary tiles
    or banks too.)"""
    out = {}
    for y in range(MH):
        for x in range(MW):
            m = int(mgrid[y, x]) & 1023
            for q in range(4):
                if mview[y * 16 + (q // 2) * 8:y * 16 + (q // 2) * 8 + 8, x * 16 + (q % 2) * 8:x * 16 + (q % 2) * 8 + 8].any():
                    out.setdefault(m, set()).add(q)
    return out

def closure(mah, metas, quads=None):
    """Secondary tiles and secondary banks the given Route 45 metatiles (or only the given
    quadrants of them: {mid: [quadrant indices 0-3]}) reference."""
    tiles, banks = set(), set()
    for m in metas:
        qs = range(4) if quads is None or m not in quads else quads[m]
        for li in range(8):
            if li % 4 not in qs:
                continue
            e = mah.metas[m][li]
            if (e & 1023) >= PRIMARY_TILES:
                tiles.add(e & 1023)
            if (e >> 12) >= PRIMARY_BANKS:
                banks.add(e >> 12)
    return tiles, banks

def seam_cells(mah, want, view, reserved):
    """Decide every Route 46 cell Route 45 can show (any pixel in view). reserved: Route 45
    secondary metatiles Route 46 copies unchanged (no hybrid may use their ids)."""
    full = {}
    for mid in mah.metas:
        full.setdefault(mah.decode(mid).tobytes(), []).append(mid)
    quad = {}
    for mid in sorted(mah.metas):
        d = mah.decode(mid)
        for q in range(4):
            k = d[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8].tobytes()
            quad.setdefault(k, []).append((mid, q))
    w5 = B.rgb5(want)
    out = {}
    for y in range(H):
        for x in range(W):
            v = view[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            if not v.any():
                continue
            cell = w5[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            hit = full.get(cell.tobytes())
            if hit:
                # prefer a primary metatile, then the lowest id
                out[(x, y)] = dict(kind='neighbour', id=min(hit, key=lambda m: (m >= 512, m)))
                continue
            vq = [q for q in range(4) if v[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8].any()]
            sub = lambda img, q: img[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            if len(vq) < 4:
                # a Route 45 secondary id whose visible quadrants draw this cell's
                used = {o['id'] for o in out.values() if o['kind'] == 'hybrid'}
                cands = [m for m in sorted(mah.metas) if m >= 512 and m not in reserved and m not in used and all((sub(mah.decode(m), q) == sub(cell, q)).all() for q in vq)]
                if cands:
                    out[(x, y)] = dict(kind='hybrid', id=cands[0], quads=vq)
                    continue
            src = []
            for q in range(4):
                if q not in vq:
                    src.append(None)
                    continue
                c = quad.get(sub(cell, q).tobytes())
                if not c:
                    src.append(('new', q))                  # new_quadrants() draws it with new Route 45 tiles
                    continue
                src.append(min(c, key=lambda mq: (any((mah.metas[mq[0]][li] & 1023) >= PRIMARY_TILES or (mah.metas[mq[0]][li] >> 12) >= PRIMARY_BANKS
                                                       for li in (mq[1], mq[1] + 4)), mq)))
            out[(x, y)] = dict(kind='append', quads=vq, src=src)
    return out

MAH_NEW_TILES = None                                 # set by main: after Route 45's own secondary tiles

def new_quadrants(mah, seam, lay):
    """Quadrants Route 46 shows to Route 45's camera that no Route 45 metatile draws: each layer
    of each is a Route 45 tile as it is (any tile, flip and bank of Route 45's), or else a new
    tile added to Route 45's secondary tile sheet after its own (no Route 45 cell uses it), drawn
    with one of Route 45's palette banks exactly as installed. Fills s['new'][q] = (bottom entry,
    top entry); returns the new tiles' index patterns."""
    look = {}
    for t, pat in sorted(mah.tiles.items()):
        for f, v in enumerate(B.flips(pat)):
            nz = v > 0
            for b in range(BANKS):
                img = mah.pals[b][v]
                look.setdefault((np.where(nz[..., None], img, mah.pals[0][0]).tobytes(), True), (t, f, b))
                if nz.any():
                    look.setdefault((np.where(nz[..., None], img, -1).tobytes(), False), (t, f, b))
    sets = {b: [tuple(c) for c in mah.pals[b][1:16].tolist()] for b in range(BANKS)}
    new, missing = {}, []
    for (x, y), sd in sorted(seam.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if sd['kind'] != 'append':
            continue
        for q, src in enumerate(sd['src']):
            if not (src and src[0] == 'new'):
                continue
            ents = []
            for l in (0, 1):
                L = lay.get((2 * x + q % 2, 2 * y + q // 2, l))
                if L is None:
                    ents.append(0)
                    continue
                px = B.rgb5(L['px'])
                key = (px.tobytes(), True) if l == 0 else (np.where(L['mask'][..., None], px, -1).tobytes(), False)
                hit = look.get(key)
                if hit is None:
                    cs = set(map(tuple, px[L['mask']].reshape(-1, 3).tolist()))
                    b = next((b for b in range(BANKS) if cs <= set(sets[b])), None)
                    if b is None:
                        missing.append(((x, y), q, l, sorted(cs - set().union(*map(set, sets.values())))))
                        ents.append(0)
                        continue
                    # clear top-layer pixels index 0, whatever colour the layer plan left under them
                    ix = np.array([[sets[b].index(tuple(c)) + 1 if (l == 0 or L['mask'][i, j]) else 0
                                    for j, c in enumerate(row)] for i, row in enumerate(px.tolist())], np.uint8)
                    vs = B.flips(ix)
                    o = min(range(4), key=lambda i: vs[i].tobytes())
                    k = vs[o].tobytes()
                    if k not in new:
                        new[k] = MAH_NEW_TILES + len(new)
                        mah.tiles[new[k]] = vs[o]
                    hit = (new[k], o, b)
                    look[key] = hit
                t, f, b = hit
                ents.append(t | ((f & 1) << 10) | ((f >> 1) << 11) | (b << 12))
            sd.setdefault('new', {})[q] = tuple(ents)
    assert not missing, ('no Route 45 bank holds these quadrants\' colours', missing)
    assert MAH_NEW_TILES + len(new) <= 1008, ('Route 45\'s secondary tile sheet is full', len(new))
    return [np.frombuffer(k, np.uint8).reshape(8, 8) for k, _ in sorted(new.items(), key=lambda kv: kv[1])]

def pack_partial(sets, init, caps, tries=200, seed=0, time_limit=600):
    """Exact colour banks when some banks already hold fixed colours: every set must lie inside
    one bank, and a bank may take at most caps[k] colours beyond its fixed ones (init[k]).
    Greedy with randomised restarts (pack_lossless.pack_sets), then an integer program."""
    distinct = set(sets)
    maximal = [c for c in distinct if not any(c < d for d in distinct)]
    rng = np.random.default_rng(seed)
    fits = lambda b, k, c: len((b | c) - init[k]) <= caps[k]
    for t in range(tries):
        banks = [set(b) for b in init]
        todo = sorted(maximal, key=lambda c: -len(c) - (rng.random() * 3 if t else 0))
        while todo:
            c = todo.pop(0)
            opts = [(len(c - b), -len(c & b), k) for k, b in enumerate(banks) if fits(b, k, c)]
            if not opts:
                break
            banks[min(opts)[2]] |= c
        else:
            return banks
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import lil_matrix
    cols = sorted(set().union(*maximal)); ci = {c: i for i, c in enumerate(cols)}
    S, C, Bn = len(maximal), len(cols), len(init)
    X = lambda s, b: s * Bn + b
    Y = lambda c, b: S * Bn + c * Bn + b
    nv = S * Bn + C * Bn
    rows = S + sum(len(x) for x in maximal) * Bn + Bn
    A = lil_matrix((rows, nv)); lo = np.zeros(rows); hi = np.zeros(rows); r = 0
    for si in range(S):
        for b in range(Bn): A[r, X(si, b)] = 1
        lo[r] = hi[r] = 1; r += 1
    for si, st in enumerate(maximal):
        for c in st:
            for b in range(Bn):
                A[r, X(si, b)] = 1; A[r, Y(ci[c], b)] = -1; lo[r] = -np.inf; hi[r] = 0; r += 1
    for b in range(Bn):
        for c in cols:
            if c not in init[b]:
                A[r, Y(ci[c], b)] = 1
        lo[r] = 0; hi[r] = caps[b]; r += 1
    res = milp(c=np.zeros(nv), constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=np.ones(nv),
               bounds=Bounds(np.zeros(nv), np.ones(nv)), options=dict(time_limit=time_limit, disp=False))
    print('milp', res.status, res.message)
    if res.x is None or res.status != 0:
        return None
    banks = [set(b) for b in init]
    for si, st in enumerate(maximal):
        banks[int(np.argmax([res.x[X(si, b)] for b in range(Bn)]))] |= st
    return banks

# --------------------------------------------------------------------------- main
def main(engine, phg):
    OUT_SRC.mkdir(parents=True, exist_ok=True); OUT_EV.mkdir(parents=True, exist_ok=True)
    MB = B.behaviors(engine)
    mah, mgrid, mcount = neighbour(engine)
    global MAH_NEW_TILES
    MAH_NEW_TILES = PRIMARY_TILES + mcount['secondary_tiles']
    mah_native = draw(mah, mgrid, MH, MW)
    z = np.load(SRC / 'assemble/layers.npz')
    view = z['route45_view']
    trav = route46_traversal(engine, phg, z)
    tcell = {(c['x'], c['y']): c for c in trav}
    lay, want = plan_layers(z, {k: c['layer'] for k, c in tcell.items()})
    w5 = B.rgb5(want)

    # ---- the seam: reserved Route 45 metatiles, Route 46's visible cells
    assert not mah.tiles[0].any(), 'Route 45 primary tile 0 is not blank'
    mview = z['route_view_of_route45']
    seen_quads = reserved_from_view(mgrid, mview)
    res_quads = {m: q for m, q in seen_quads.items() if m >= 512}
    seam = seam_cells(mah, want, view, set(res_quads))
    mah_new = new_quadrants(mah, seam, lay)
    whole = set()                                         # Route 45 metatiles Route 46's own cells use
    for (x, y), s in seam.items():
        if s['kind'] == 'neighbour':
            whole.add(s['id'])
            if s['id'] >= 512:
                res_quads[s['id']] = {0, 1, 2, 3}         # Route 46 draws it whole
    res_metas = set(res_quads)
    hybrids = {s['id'] for s in seam.values() if s['kind'] == 'hybrid'}
    assert not hybrids & res_metas, ('a hybrid id is one Route 46 must copy', hybrids & res_metas)
    res_tiles, res_banks = closure(mah, sorted(set(seen_quads) | res_metas), {m: sorted(q) for m, q in {**seen_quads, **res_quads}.items()})
    wt, wb = closure(mah, sorted(whole))                  # a primary id may draw secondary tiles or banks
    res_tiles |= wt; res_banks |= wb
    ht, hb = closure(mah, sorted(hybrids), {s['id']: s['quads'] for s in seam.values() if s['kind'] == 'hybrid'})
    res_tiles |= ht; res_banks |= hb
    appends = [(xy, s) for xy, s in sorted(seam.items(), key=lambda kv: (kv[0][1], kv[0][0])) if s['kind'] == 'append']
    for _, s in appends:
        for src in filter(None, s['src']):
            if src[0] == 'new':
                ents = s['new'][src[1]]
                res_tiles |= {e & 1023 for e in ents if (e & 1023) >= PRIMARY_TILES}
                res_banks |= {e >> 12 for e in ents if (e >> 12) >= PRIMARY_BANKS}
                continue
            at, ab = closure(mah, [src[0]], {src[0]: [src[1]]})
            res_tiles |= at; res_banks |= ab
    # Route 45's (tile, bank) pairs Route 46 must draw exactly as Route 45 does, and the palette
    # slots they use: in banks 6-12 only those slots are fixed, Route 46 fills the others.
    pairs = set()
    def take(m, qs=range(4)):
        for q in qs:
            for li in (q, q + 4):
                e = mah.metas[m][li]
                pairs.add((e & 1023, e >> 12))
    for m in res_metas: take(m, sorted(res_quads[m]))
    for m, q in seen_quads.items(): take(m, sorted(q))
    for m in whole: take(m)
    for sd in seam.values():
        if sd['kind'] == 'hybrid': take(sd['id'], sd['quads'])
        if sd['kind'] == 'append':
            for src in filter(None, sd['src']):
                if src[0] == 'new':
                    pairs.update((e & 1023, e >> 12) for e in sd['new'][src[1]])
                else:
                    take(src[0], [src[1]])
    slots = {b: set() for b in range(PRIMARY_BANKS, BANKS)}
    for t, bk in pairs:
        if bk >= PRIMARY_BANKS:
            slots[bk] |= set(np.unique(mah.tiles[t]).tolist()) - {0}
    free_slots = {b: [i for i in range(1, 16) if i not in slots[b]] for b in slots}

    # ---- tile lookup: every existing (pattern, flip, bank) Route 46 may reuse as it is
    lookup = {}
    def add(t, b):
        for f, v in enumerate(B.flips(mah.tiles[t])):
            nz = v > 0
            img = mah.pals[b][v]
            lookup.setdefault((np.where(nz[..., None], img, mah.pals[0][0]).tobytes(), True), (t, f, b))
            if nz.any():
                lookup.setdefault((np.where(nz[..., None], img, -1).tobytes(), False), (t, f, b))
    for t in range(PRIMARY_TILES):
        for b in range(PRIMARY_BANKS):
            add(t, b)
    for t, b in sorted(pairs):
        if t >= PRIMARY_TILES or b >= PRIMARY_BANKS:
            add(t, b)

    def entry(t, f, b):
        return t | ((f & 1) << 10) | ((f >> 1) << 11) | (b << 12)

    # ---- encode every layer tile: an existing tile, or a new pattern
    new_jobs = []
    for pos, L in lay.items():
        px = B.rgb5(L['px'])
        if pos[2] == 0:
            k = (px.tobytes(), True)
        else:
            k = (np.where(L['mask'][..., None], px, -1).tobytes(), False)
        hit = lookup.get(k)
        if hit:
            L['entry'] = entry(*hit)
        else:
            new_jobs.append(pos)
    prim_sets = {b: set(map(tuple, mah.pals[b][1:16].tolist())) for b in range(PRIMARY_BANKS)}
    own_sets = []
    for pos in new_jobs:
        L = lay[pos]
        c = colour_set(L['px'], L['mask'])
        L['cset'] = c
        if not any(c <= st for st in prim_sets.values()):
            own_sets.append(c)
    over15 = [pos for pos in new_jobs if len(lay[pos]['cset']) > 15]
    assert not over15, ('tiles with more than 15 colours', [(p[0] // 2, p[1] // 2, p[2]) for p in over15[:20]], len(over15))
    sec = list(range(PRIMARY_BANKS, BANKS))
    init = [set(tuple(mah.pals[b][i].tolist()) for i in slots[b]) for b in sec]
    caps = [len(free_slots[b]) for b in sec]
    banks = pack_partial(own_sets, init, caps)
    assert banks is not None, ('Route 46\'s own colours do not fit banks 6-12', caps, len(set(own_sets)))
    final = {b: mah.pals[b].copy() for b in range(PRIMARY_BANKS)}
    for b, st, ini in zip(sec, banks, init):
        pal = np.zeros((16, 3), np.int32)
        for i in slots[b]:
            pal[i] = mah.pals[b][i]
        extra = sorted(st - ini)
        fs = free_slots[b]
        assert len(extra) <= len(fs)
        for i, c in zip(fs, extra):
            pal[i] = c
        fill = extra[-1] if extra else (tuple(pal[min(slots[b])].tolist()) if slots[b] else (0, 0, 0))
        for i in fs[len(extra):]:
            pal[i] = fill
        final[b] = pal
    bank_sets = {b: set(map(tuple, final[b][1:16].tolist())) for b in final}
    patterns = {}                                             # canonical index pattern -> new tile id
    for pos in new_jobs:
        L = lay[pos]
        c = L['cset']
        b = next(b for b in range(BANKS) if c <= bank_sets[b])
        pal = final[b][1:16].astype(int)
        px = B.rgb5(L['px']).reshape(64, 3).astype(int)
        d = np.abs(px[:, None, :] - pal[None]).sum(-1)
        ix = (d.argmin(-1) + 1).astype(np.uint8)
        assert (d.min(-1)[L['mask'].ravel()] == 0).all()
        if pos[2] == 1:
            ix = np.where(L['mask'].ravel(), ix, 0).astype(np.uint8)
        vs = B.flips(ix.reshape(8, 8))
        o = min(range(4), key=lambda i: vs[i].tobytes())
        kk = vs[o].tobytes()
        patterns.setdefault(kk, len(patterns))
        L.update(bank=b, pattern=patterns[kk], flip=o)
    free_tiles = [t for t in range(PRIMARY_TILES, TILES) if t not in res_tiles]
    if len(patterns) > len(free_tiles):
        own_names = z['owner']
        by = {}
        for pos in new_jobs:
            tx, ty, l = pos
            o = own_names[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            names = sorted({n.split('_')[0] if not n.startswith('flat_') else n for n in o.ravel().tolist()} - {''}) or ['terrain']
            by.setdefault('+'.join(names) + f'/L{l}', set()).add(lay[pos]['pattern'])
        print('new tiles by owner', sorted(((k, len(v)) for k, v in by.items()), key=lambda kv: -kv[1]))
    assert len(patterns) <= len(free_tiles), ('secondary tiles over budget', len(patterns), len(free_tiles))
    tile_of = {}
    for kk, i in patterns.items():
        tile_of[i] = free_tiles[i]
    for pos in new_jobs:
        L = lay[pos]
        L['entry'] = entry(tile_of[L['pattern']], L['flip'], L['bank'])

    # ---- metatiles
    def own_entries(x, y):
        q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
        return [lay[(a, b, 0)]['entry'] for a, b in q] + [lay[(a, b, 1)]['entry'] if (a, b, 1) in lay else 0 for a, b in q]
    def own_attr(x, y):
        c = tcell[(x, y)]
        return c['behavior_id'] | ((0 if c['layer'] == 'normal' else 1) << 12)
    rt = {}                                                  # Route 46's metatile table: id -> (entries, attr)
    for m in sorted(res_metas):
        # the quadrants ever in view are Route 45's; the rest draw nothing (never on screen)
        rt[m] = (tuple(e if (i % 4) in res_quads[m] else 0 for i, e in enumerate(mah.metas[m])), mah.attrs[m])
    grid = np.zeros((H, W), np.uint16)
    p_append, s_append = [], []                               # appended to Route 45: (entries, attr)
    mah_next_p = 1 + max(m for m in mah.metas if m < 512)
    mah_next_s = 1 + max(m for m in mah.metas if m >= 512)
    seam_report = []
    for (x, y), s in sorted(seam.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        c = tcell[(x, y)]
        if s['kind'] == 'neighbour':
            grid[y, x] = s['id']
            attr = mah.attrs[s['id']]
            # the cell takes the Route 45 metatile's behaviour and layer type
            beh = {v: k for k, v in MB.items()}[attr & 0xFF]
            if c['behavior'] != beh or ((attr >> 12) == 0) != (c['layer'] == 'normal'):
                c['seam_attr_from'] = dict(behavior=c['behavior'], layer=c['layer'])
            c['behavior'], c['behavior_id'] = beh, attr & 0xFF
            c['layer'] = 'normal' if (attr >> 12) == 0 else 'covered'
            seam_report.append(dict(cell=[x, y], kind='route45 metatile', id=s['id']))
        elif s['kind'] == 'hybrid':
            ents = own_entries(x, y)
            for q in s['quads']:
                ents[q] = mah.metas[s['id']][q]; ents[q + 4] = mah.metas[s['id']][q + 4]
            rt[s['id']] = (tuple(ents), own_attr(x, y))
            grid[y, x] = s['id']
            seam_report.append(dict(cell=[x, y], kind='Route 45 secondary id, visible quadrants shared', id=s['id'], quads=s['quads']))
        else:
            ents_vis = [None] * 8
            for q, src in enumerate(s['src']):
                if src and src[0] == 'new':
                    ents_vis[q], ents_vis[q + 4] = s['new'][q]
                elif src:
                    m, sq = src
                    ents_vis[q], ents_vis[q + 4] = mah.metas[m][sq], mah.metas[m][sq + 4]
            primary_ok = all(e is not None and (e & 1023) < PRIMARY_TILES and (e >> 12) < PRIMARY_BANKS for e in ents_vis)
            attr = own_attr(x, y)
            if primary_ok:
                mid = mah_next_p + len(p_append)
                p_append.append((tuple(ents_vis), attr))
                rt[mid] = (tuple(ents_vis), attr)
                kind = 'appended to Route 45\'s primary'
            else:
                mid = mah_next_s + len(s_append)
                own_e = own_entries(x, y)
                mine = [ents_vis[i] if ents_vis[i] is not None else own_e[i] for i in range(8)]
                # Route 45's copy draws the visible quadrants; its hidden ones repeat a visible one
                v0 = next(q for q in range(4) if ents_vis[q] is not None)
                theirs = [ents_vis[i] if ents_vis[i] is not None else ents_vis[v0 + 4 * (i // 4)] for i in range(8)]
                s_append.append((tuple(theirs), attr))
                rt[mid] = (tuple(mine), attr)
                kind = 'appended to Route 45\'s secondary, visible quadrants shared'
            grid[y, x] = mid
            seam_report.append(dict(cell=[x, y], kind=kind, id=mid, quads=s['quads'],
                                    sources=[(['new Route 45 tiles'] + [int(e) for e in s['new'][v[1]]]) if v and v[0] == 'new'
                                             else (list(v) if v else None) for v in s['src']]))
    taken = set(rt)
    prim_by_key = {(mah.metas[m], mah.attrs[m]): m for m in sorted(mah.metas) if m < 512}
    for i, (e, a) in enumerate(p_append):
        prim_by_key.setdefault((e, a), mah_next_p + i)
    own_ids = (m for m in range(512, 512 + METAS) if m not in taken and not (mah_next_s <= m < mah_next_s + len(s_append)))
    by_key = {}
    for y in range(H):
        for x in range(W):
            if (x, y) in seam:
                continue
            k = (tuple(own_entries(x, y)), own_attr(x, y))
            if k in prim_by_key:
                grid[y, x] = prim_by_key[k]
                continue
            if k not in by_key:
                mid = next(own_ids, None)
                if mid is None:
                    keys = {(tuple(own_entries(xx, yy)), own_attr(xx, yy)) for yy in range(H) for xx in range(W) if (xx, yy) not in seam}
                    print('metatiles wanted', len(keys - set(prim_by_key)), 'taken', len(taken), 'appended', len(s_append))
                assert mid is not None, 'secondary metatiles over budget'
                by_key[k] = mid
                rt[mid] = k
            grid[y, x] = by_key[k]

    # ---- the pairs as the engine sees them
    rp = Pair()
    for t in range(PRIMARY_TILES):
        if t in mah.tiles: rp.tiles[t] = mah.tiles[t]
    for t in res_tiles:
        rp.tiles[t] = mah.tiles[t]
    pat_arr = {i: np.frombuffer(kk, np.uint8).reshape(8, 8) for kk, i in patterns.items()}
    for i, t in tile_of.items():
        rp.tiles[t] = pat_arr[i]
    for b in range(BANKS):
        rp.pals[b] = final[b]
    for m in range(PRIMARY_TILES):
        if m in mah.metas: rp.metas[m] = mah.metas[m]; rp.attrs[m] = mah.attrs[m]
    for i, (e, a) in enumerate(p_append):
        rp.metas[mah_next_p + i] = e; rp.attrs[mah_next_p + i] = a
    for m, (e, a) in rt.items():
        if m >= 512:
            rp.metas[m] = e; rp.attrs[m] = a
    mahx = Pair()                                             # Route 45 with the appended metatiles
    mahx.tiles, mahx.pals = mah.tiles, mah.pals
    mahx.metas, mahx.attrs = dict(mah.metas), dict(mah.attrs)
    for i, (e, a) in enumerate(p_append):
        mahx.metas[mah_next_p + i] = e; mahx.attrs[mah_next_p + i] = a
    for i, (e, a) in enumerate(s_append):
        mahx.metas[mah_next_s + i] = e; mahx.attrs[mah_next_s + i] = a

    # ---- proofs
    report = dict(method='lossless pack on Route 45 City\'s tilesets: Route 45\'s primary (tiles 0-511, palettes 0-5, '
                         'metatiles 0-511); a secondary carrying exact copies of what Route 45\'s visible edge uses, then '
                         'Route 46\'s own art')
    native = draw(rp, grid, H, W)
    d = (native != w5).any(-1)
    if d.any():
        ys, xs = np.nonzero(d)
        bad = sorted({(int(x) // 16, int(y) // 16) for y, x in zip(ys, xs)})
        print('differing cells', bad[:40], [int(grid[y, x]) for x, y in bad[:40]])
        for x, y in bad[:4]:
            m = int(grid[y, x])
            dd = (native[y*16:y*16+16, x*16:x*16+16] != w5[y*16:y*16+16, x*16:x*16+16]).any(-1)
            print((x, y), m, 'quads', [q for q in range(4) if dd[(q//2)*8:(q//2)*8+8, (q%2)*8:(q%2)*8+8].any()],
                  'entries', [(e & 1023, e >> 12) for e in rp.metas[m]], 'own', [(e & 1023, e >> 12) for e in own_entries(x, y)],
                  'in seam', (x, y) in seam, 'res', m in res_metas, 'hyb', m in hybrids)
            t, b = rp.metas[m][0] & 1023, rp.metas[m][0] >> 12
            print(' tile', t, 'reserved', t in res_tiles, 'own', t in tile_of.values(), 'pair', (t, b) in pairs,
                  'idx', sorted(set(np.unique(mah.tiles[t]).tolist())), 'slots', sorted(slots[b]),
                  'same tile', (rp.tiles[t] == mah.tiles[t]).all(), 'pal eq', [bool((final[b][i] == mah.pals[b][i]).all()) for i in range(16)])
    assert not d.any(), ('Route 46 pixels differ from the assembled art', int(d.sum()))
    Image.fromarray(((native << 3) | (native >> 2)).astype(np.uint8)).save(OUT_EV / 'native.png')
    report['native_pixels_exact'] = int(d.size)
    seen = draw(mahx, grid, H, W)                              # Route 46 as Route 45's tilesets draw it
    vv = view
    d = (seen != w5).any(-1) & vv
    assert not d.any(), ('Route 46 pixels Route 45 can show differ under Route 45\'s tilesets', int(d.sum()))
    report['route46_pixels_in_route45_view'] = int(vv.sum())
    report['route46_pixels_in_route45_view_exact'] = True
    shown = np.where(vv[..., None], seen, 0)
    Image.fromarray(((shown << 3) | (shown >> 2)).astype(np.uint8)).save(OUT_EV / 'seam-route46-with-route45-tilesets.png')
    strip = draw(rp, mgrid, MH, MW)
    d = (strip != mah_native).any(-1) & mview
    assert not d.any(), ('Route 45 pixels Route 46 can show differ under Route 46\'s tilesets', int(d.sum()))
    shown = np.where(mview[..., None], strip, 0)
    Image.fromarray(((shown << 3) | (shown >> 2)).astype(np.uint8)).save(OUT_EV / 'seam-route45-with-route46-tilesets.png')
    report['route45_pixels_in_route46_view'] = int(mview.sum())
    report['route45_pixels_in_route46_view_exact'] = True
    again = draw(mahx, mgrid, MH, MW)
    assert (again == mah_native).all(), 'Route 45 draws differently with the appended metatiles'
    report['route45_unchanged_with_appended_metatiles'] = True
    # the border block: Route 45's, shared-primary metatile 0
    report.update(
        reserved_metatiles={m: sorted(res_quads[m]) for m in sorted(res_metas)}, reserved_tiles=sorted(res_tiles),
        reserved_palette_slots={b: sorted(v) for b, v in slots.items() if v}, banks=[len(set(map(tuple, rp.pals[b][1:].tolist()))) for b in range(BANKS)],
        primary_tiles_reused=len({e & 1023 for k in rt.values() for e in k[0] if (e & 1023) < PRIMARY_TILES} |
                                 {e & 1023 for m in set(grid.ravel().tolist()) if m < 512 for e in rp.metas[m]}),
        new_secondary_tiles=len(patterns), secondary_tile_slots=len(free_tiles),
        secondary_metatiles=len([m for m in rt if m >= 512]), primary_metatiles_used=len({int(m) for m in grid.ravel() if m < 512}),
        route45_new_tiles=dict(first=MAH_NEW_TILES, count=len(mah_new)),
        route45_appended=dict(primary=[mah_next_p + i for i in range(len(p_append))], secondary=[mah_next_s + i for i in range(len(s_append))]),
        seam=seam_report, route45_counts=mcount)
    # ---- save
    sec_tiles = np.zeros((max(rp.tiles) + 1 - PRIMARY_TILES, 8, 8), np.uint8)
    for t, p in rp.tiles.items():
        if t >= PRIMARY_TILES: sec_tiles[t - PRIMARY_TILES] = p
    top_id = max(m for m in rp.metas if m >= 512)
    sec_metas = np.zeros((top_id + 1 - 512, 9), np.uint16)
    for m in range(512, top_id + 1):
        if m in rp.metas:
            sec_metas[m - 512, :8] = rp.metas[m]; sec_metas[m - 512, 8] = rp.attrs[m]
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b in range(BANKS):
        pal_rgb[b] = ((rp.pals[b] << 3) | (rp.pals[b] >> 2)).astype(np.uint8)
    np.savez_compressed(
        OUT_SRC / 'pack.npz', grid=grid, secondary_tiles=sec_tiles, palettes=pal_rgb, secondary_metatiles=sec_metas,
        route45_primary_append=np.array([list(e) + [a] for e, a in p_append], np.uint16).reshape(-1, 9),
        route45_secondary_append=np.array([list(e) + [a] for e, a in s_append], np.uint16).reshape(-1, 9),
        route45_new_tiles=np.array(mah_new, np.uint8).reshape(-1, 8, 8),
        collision=np.array([[tcell[(x, y)]['collision'] for x in range(W)] for y in range(H)], np.uint8),
        elevation=np.array([[tcell[(x, y)]['elevation'] for x in range(W)] for y in range(H)], np.uint8))
    (OUT_SRC / 'traversal.json').write_text(json.dumps(trav) + '\n')
    (OUT_EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('seam', 'reserved_tiles')}))
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
