"""Olivine City as Gen 3 elements: ledger and terrain composer (the Blackthorn method).

    python3 tools/gba/maps/olivine_elements/elements.py ENGINE_CHECKOUT PHG_CHECKOUT

Builds Olivine from reusable elements instead of a 1:1 HGSS render. Every cell gets a
material and structure label from HGSS geometry (top-down height map, permissions, map
header 77, zone T26). Terrace levels are HGSS heights above the town floor; under a tree
the level is the ground the tree stands on (HGSS models its crowns as terrain, a level
above their trunks). Each element takes the Gen 3 piece that does its job, restyled with
HGSS's own colours:

    rock          FRLG's General mountain set in the HGSS rock ramp (Blackthorn's and
                  Cianwood's), per 8x8 quadrant, a top-layer overlay
    grass, sea    Cherrygrove's (CherrygrovePrimary, the sea animated)
    road          Cherrygrove's path sand
    plaza         Slateport's paving nine-slice (its scalloped edge onto grass is HGSS's
                  kerb round the lawns) in HGSS's blue-grey cobble ramp (as_fe01)
    deck          FRLG Vermilion's pier planks, turned to run north-south as HGSS's do,
                  in HGSS's grey deck ramp (as_fe02), with its dark edge over the sea
    fences        FRLG's metal fence in HGSS's chain-fence greys (fence_a)
    steps, ramp   FRLG's stone stairs; the wooden ramp up to the Lighthouse its turned
                  treads in HGSS's slope colours
    trees         HGSS's own Olivine tree (32 px, its trunk and shadow) in Cherrygrove's
                  tree greens, one per HGSS tree on the 2x2 grid HGSS plants them on
    sea rocks     HGSS's sea_rock texture resampled (Cianwood's), the rock climb wall
                  HGSS's r_climb texture

Buildings and props are HGSS's own models and textures rendered at C06's angle
(sprites.py, hgss_camera.view); the Center is the owner-locked C06, the Mart the shared
Johto Mart. Canon has no Olivine Gym (DESIGN.md): its building stays as a civic hall with
the emblem and the Gym sign left out.

    source/elements/ledger.json, ledger.png, compose-C.npz
    evidence/elements/terrain-C.png, compare.png
"""
from __future__ import annotations
import hashlib, json, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/olivine-elements'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 64, 64
ROCK = set('TESWNC')
FLOOR_HEIGHT = 1                     # HGSS height of the town floor (plaza and deck)
DIRS = dict(n=(0, -1), ne=(1, -1), e=(1, 0), se=(1, 1), s=(0, 1), sw=(-1, 1), w=(-1, 0), nw=(-1, -1))
ROCK_MATERIALS = ('cliff01gs', 'wall01_d', 'wall01_g', 'wall01_h', 'r_climb')
TREE_MATERIALS = ('tree01_re', 'tree01_un', 'tree01gs')
FLOORS = dict(as_fe01='cobble', as_fe01_r='kerb', as_fe03_r='grass', grass01gs='grass', grass01_a='grass',
              as_fe02='deck', as_fe02_r='deck', road01='sand', beach01='sand', slope='ramp', fence_a='cobble',
              as_hato01='deck', as_hato03='deck', c2_rale_a='deck', c2_rale_b='deck')
EVENTS = json.loads((SRC / 'hgss-events.json').read_text())

# --------------------------------------------------------------------------- ledger
def topdown(phg):
    """Flat top-down HGSS terrain: per-pixel height, material and colour."""
    sys.path.insert(0, str(HERE))
    import hgss_render as R
    land, tex0, models, chunks, meta = R.load(phg)
    cv = R.Canvas(W * 16, H * 16)
    for c in chunks:
        ch = R.hgss_map.MapChunk.parse(land[c['land']])
        ox, oz = c['cx'] * 32, c['cz'] * 32
        R.draw_model(cv, R.mdlview.Model(ch.model), tex0, lambda x, y, z, ox=ox, oz=oz: (x + 16 + ox, y, z + 16 + oz), -1, None, flat=True)
    h = np.nan_to_num(cv.height, nan=float(np.nanmin(cv.height)))
    return h, cv.mat, list(R.MATERIAL_NAMES), cv.rgb.astype(np.uint8)

def tree_grid(mat, names, rgb):
    """HGSS's trees: one per trunk (the brown core of tree01_un), centred on a cell
    boundary. Returns (x0, y0) of each tree's 2x2 block: crown row y0, trunk row y0 + 1."""
    from scipy import ndimage
    un = names.index('tree01_un')
    trunk = (mat == un) & (np.abs(rgb.astype(int) - np.array([148, 115, 74])).sum(-1) < 8)
    lab, n = ndimage.label(trunk)
    out = set()
    for cy, cx in ndimage.center_of_mass(trunk, lab, range(1, n + 1)):
        out.add((int(round(cx / 16)) - 1, int(cy // 16) - 1))
    return sorted(out, key=lambda t: (t[1], t[0]))

def ledger(phg):
    h, mat, names, rgb = topdown(phg)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    nm = np.array(names + ['none'])
    m = np.where(mat >= 0, mat, len(names)).reshape(H, 16, W, 16).transpose(0, 2, 1, 3).reshape(H, W, 256)
    hc = h.reshape(H, 16, W, 16).transpose(0, 2, 1, 3).reshape(H, W, 256)
    level = np.median(hc, axis=2)
    rockpx = np.isin(nm[m], ROCK_MATERIALS)
    rock_peak = np.where(rockpx.any(-1), np.where(rockpx, hc, -9).max(-1), -9)
    blds = json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']
    owner = np.full((H, W), -1, int)
    for i, b in enumerate(blds):
        x0, z0, x1, z1 = b['footprint']
        owner[int(np.floor(z0)):int(np.ceil(z1)), int(np.floor(x0)):int(np.ceil(x1))] = i
    trees = tree_grid(mat, names, rgb)
    # Fences stand up from the floor: count their faces in the lifted render, where they show.
    lift = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    fence = (lift['material'] == list(lift['names']).index('fence_a')).reshape(H, 16, W, 16).sum(axis=(1, 3))
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            u, cnt = np.unique(nm[m[y, x]], return_counts=True)
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            dominant = str(u[np.argmax(cnt)])
            blocked = bool(coll[y, x] & 0x80)
            t = int(types[y, x])
            treepx = sum(frac.get(k, 0) for k in TREE_MATERIALS)
            seapx = frac.get('sea_rock', 0) + frac.get('sea_rock_m', 0)
            floor = FLOORS.get(dominant, 'grass')
            if t == 0x15:
                lab, floor = ('R', 'water') if blocked else ('~', 'water')
            elif t == 0x17:
                lab, floor = '.', 'shallow'
            elif t == 0x21:
                lab, floor = '.', 'beach'
            elif t == 0x4C:
                lab = 'C'                                     # HGSS's rock climb wall (east-west)
            elif blocked and seapx >= 48:
                lab, floor = 'R', 'water'
            elif t == 0x06 or (blocked and treepx >= 128):
                lab, floor = 'F', 'grass'
            elif blocked and frac.get('rock01', 0) >= 32:
                lab = 'O'
            elif blocked and rockpx[y, x].sum() >= 64:
                lab = 'T'                                     # faces are read from terrace levels below
            elif blocked and fence[y, x] > 40:
                lab = 'f'                                     # a chain fence on the floor
            elif blocked and owner[y, x] >= 0:
                lab = 'X'
            elif blocked and fence[y, x] > 0 and floor == 'deck':
                lab = 'q'                                     # the quay's low rail along the deck's edge
            elif blocked:
                lab = 'B'                                     # blocked open ground (HGSS's unreachable strips)
            else:
                lab = '.'
            if floor == 'cobble' and frac.get('grass01gs', 0) > 160:
                floor = 'grass'
            if dominant in ('sea_un', 'sea_on', 'as_yachtwave') and floor == 'grass':
                floor = 'water'                               # a yacht's cells, the bollards off the pier's end
            if dominant == 'beach01':
                floor = 'beach'
            row.append(dict(lab=lab, floor=floor, level=round(float(level[y, x]), 2), rock_peak=round(float(rock_peak[y, x]), 2),
                            type=t, blocked=blocked, owner=int(owner[y, x]), material=dominant, frac=frac))
        cells.append(row)
    # Trees: each HGSS trunk plants a 2x2 tree; its cells stand on the trunk row's ground.
    tree_at = {}
    for x0, y0 in trees:
        for yy in (y0, y0 + 1):
            for xx in (x0, x0 + 1):
                if 0 <= xx < W and 0 <= yy < H:
                    tree_at[(xx, yy)] = (x0, y0)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if (x, y) in tree_at:
                x0, y0 = tree_at[(x, y)]
                c['tree'] = [x0, y0]
                if c['lab'] in ('F', '.', 'f'):
                    c['lab'] = 'F'
                c['ground'] = round(float(np.median(hc[min(y0 + 1, H - 1), x])), 2)
            elif c['lab'] == 'F':
                c['ground'] = c['level'] - 1 if c['material'] == 'tree01_re' else c['level']
    # Rock: terrace level from the rock pixels' own top; everything else from its ground.
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if c['lab'] in ROCK:
                c['terrace'] = max(1, int(round(c['rock_peak'])) - FLOOR_HEIGHT)
            elif c['floor'] in ('water', 'shallow'):
                c['terrace'] = -1
            else:
                c['terrace'] = int(round(c.get('ground', c['level']))) - FLOOR_HEIGHT
    # Steps and the Lighthouse ramp cut through cliff bands: each takes its column's rock
    # level, so no face turns toward them.
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if c['floor'] == 'ramp' and c['lab'] == '.':
                col = [cells[yy][x]['terrace'] for yy in range(max(0, y - 3), min(H, y + 4)) if cells[yy][x]['lab'] in ROCK]
                c['terrace'] = max(col) if col else c['terrace']
            if c['lab'] == 'B' and c['material'] == 'fence_a' and c['floor'] == 'cobble':
                c['floor'] = 'deck'                           # the quay rail's end posts on the deck's edge
    # A boulder is a 2x2 prop (rock01); its cells take the terrace round it.
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if c['lab'] == 'O' and 'boulder' not in c:
                x0 = x if x + 1 < W and cells[y][x + 1]['lab'] == 'O' else x - 1
                y0 = y if y + 1 < H and cells[y + 1][x]['lab'] == 'O' else y - 1
                for yy in (y0, y0 + 1):
                    for xx in (x0, x0 + 1):
                        if 0 <= xx < W and 0 <= yy < H:
                            cells[yy][xx].update(lab='O', boulder=[x0, y0])
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if c['lab'] == 'O':
                ring = [cells[yy][xx]['terrace'] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                        if 0 <= yy < H and 0 <= xx < W and cells[yy][xx]['lab'] != 'O']
                c['terrace'] = max(set(ring), key=lambda v: (ring.count(v), v)) if ring else 0
                c['floor'] = 'grass'
    return cells

def save_ledger(cells):
    out = SRC / 'elements'
    out.mkdir(parents=True, exist_ok=True)
    slim = [[{k: v for k, v in c.items() if k != 'frac'} for c in row] for row in cells]
    (out / 'ledger.json').write_text(json.dumps(dict(
        note='Per-cell element ledger derived from HGSS land_data. lab: T rock (faces from terrace levels), C rock climb, '
             'F tree (tree: its 2x2 block), O boulder, R sea rock, X building or prop, f fence, q quay rail, B blocked '
             'plain ground, ~ water, . open. '
             'floor: ground under the cell. terrace: level above the town floor (under trees, the ground they stand on).',
        cells=[[c['lab'] + c['floor'][0] for c in row] for row in cells],
        detail=slim)) + '\n')
    img = Image.new('RGB', (W * 12, H * 12), (20, 20, 24)); d = ImageDraw.Draw(img)
    col = dict(T=(150, 110, 80), C=(200, 120, 60), F=(40, 110, 50), X=(90, 90, 90), O=(120, 80, 60), R=(150, 150, 160),
               f=(200, 200, 210), q=(240, 240, 250), B=(60, 60, 70))
    fl = dict(water=(60, 120, 230), grass=(110, 210, 160), sand=(240, 220, 160), shallow=(170, 220, 230), cobble=(160, 175, 190),
              kerb=(200, 180, 130), deck=(215, 215, 215), ramp=(170, 120, 90), beach=(245, 240, 210))
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d.rectangle((x * 12, y * 12, x * 12 + 11, y * 12 + 11), fill=col.get(c['lab']) or fl[c['floor']])
            if c['lab'] in 'TCFXfqB' or c['terrace'] > 0:
                d.text((x * 12 + 3, y * 12), str(c['terrace']) if c['terrace'] >= 0 else '', fill='black')
    img.save(out / 'ledger.png')

# --------------------------------------------------------------------------- source art
def hgss_texture(phg, name, pal):
    sys.path.insert(0, str(HERE))
    import hgss_render as R
    _, tex0, _, _, _ = R.load(phg)
    e = next(t for t in tex0.textures if t.name == name)
    return R.decode(tex0, e, pal)

# HGSS rock ramp (wall01 and cliff01gs carry Blackthorn's colours): outline, then light to dark.
BLACKTHORN_RAMP = [(82, 58, 52), (239, 189, 140), (222, 173, 123), (198, 148, 115), (165, 115, 99), (132, 90, 74), (99, 70, 66)]

def _read_pal(p):
    v = list(map(int, p.read_text().split()[3:51]))
    return [tuple(c & 0xF8 for c in v[i * 3:i * 3 + 3]) for i in range(16)]

def _tiles(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    return [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]

def gen3_meta(engine, primary, secondary, mid):
    """A Gen 3 metatile (both layers) as (rgb, key): key = bank * 16 + colour index."""
    frlg = primary.endswith('_frlg')
    nt, nb = (640, 7) if frlg else (512, 6)
    pd = engine / 'data/tilesets/primary' / primary
    sd = engine / 'data/tilesets/secondary' / secondary if secondary else None
    pt, st = _tiles(pd), _tiles(sd) if sd else []
    pals = {b: _read_pal(pd / f'palettes/{b:02}.pal') for b in range(nb)}
    if sd:
        pals.update({b: _read_pal(sd / f'palettes/{b:02}.pal') for b in range(nb, 13)})
    pm = np.frombuffer((pd / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    sm = np.frombuffer((sd / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8) if sd else None
    row = pm[mid] if mid < nt else sm[mid - nt]
    rgb, key = np.zeros((16, 16, 3), np.uint8), np.zeros((16, 16), int)
    for layer in (0, 1):
        for q in range(4):
            e = int(row[layer * 4 + q]); i = e & 1023
            t = pt[i] if i < nt else st[i - nt]
            if e & 0x400: t = t[:, ::-1]
            if e & 0x800: t = t[::-1]
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            m = np.ones((8, 8), bool) if layer == 0 else t != 0
            rgb[sl][m] = np.array(pals[e >> 12], np.uint8)[t][m]
            key[sl][m] = (e >> 12) * 16 + t[m]
    return rgb, key

# Cherrygrove ground (accepted Johto vocabulary), learned from its decoded native map.
CHERRY = dict(grass=[(104, 208, 152), (88, 176, 136), (128, 136, 120), (104, 200, 152), (96, 192, 144)],
              water=[(24, 96, 216), (32, 120, 224), (40, 136, 224), (24, 104, 224), (56, 176, 224), (64, 192, 224)])
PATH = [(224, 200, 128), (216, 184, 128), (184, 168, 128)]         # Cherrygrove's path sand (CherrygrovePrimary bank 0)
BORDER_GRAY = (128, 136, 120)

def cherry_textures():
    """Cherrygrove's canonical 32x32 grass and water blocks (its 32 px grid) and its path."""
    img = np.array(Image.open(SRC / 'elements/cherrygrove-native.png').convert('RGB'))
    a = img.reshape(img.shape[0] // 8, 8, img.shape[1] // 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(img.shape[0] // 8, img.shape[1] // 8, 64, 3)
    out = {}
    for name, cols in CHERRY.items():
        hit = sum((a == np.array(c)).all(-1).sum(-1) for c in cols) >= (64 if name == 'water' else 40)
        blocks = {}
        for y in range(0, img.shape[0] - 31, 32):
            for x in range(0, img.shape[1] - 31, 32):
                ky, kx = y // 8, x // 8
                if hit[max(0, ky - 1):ky + 5, max(0, kx - 1):kx + 5].all():
                    b = img[y:y + 32, x:x + 32].tobytes(); blocks[b] = blocks.get(b, 0) + 1
        out[name] = np.frombuffer(max(sorted(blocks), key=blocks.get), np.uint8).reshape(32, 32, 3)
    out['path'] = img[288:320, 1120:1152].copy()                    # the plain path east of the town
    out['beach'] = img[384:400, 368:384].copy()                     # the sandbar's plain cream cell
    return out

PLAIN = dict(grass=(16, 0), water=(16, 0), path=(8, 8))             # flattest 8x8 block of each Cherrygrove texture

def plain(tex, k):
    oy, ox = PLAIN[k]
    return np.tile(tex[k][oy:oy + 8, ox:ox + 8], (2, 2, 1))

# --------------------------------------------------------------------------- harbour greys
# One ramp holds every neutral harbour surface (deck, quay, fences, cobbles, sea rocks),
# so they share one bank: HGSS's deck, quay and fence greys, its cobble blues, the lawn
# beside the paving, the foam and the sea rocks' slate.
HARBOUR = [(239, 247, 255), (222, 222, 222), (206, 206, 206), (189, 189, 189), (173, 189, 198), (156, 156, 156),
           (140, 156, 165), (132, 132, 132), (107, 107, 107), (90, 90, 90), (49, 49, 57), (56, 72, 96), (200, 232, 224)]

def harbour(c):
    """The harbour ramp's nearest colour (by 5-bit distance)."""
    P = np.array(HARBOUR, int)
    return tuple(int(v) for v in P[((P - np.array(c)) ** 2).sum(-1).argmin()])

# --------------------------------------------------------------------------- plaza
# Slateport's paving (Emerald, the Gen 3 port city's cobbles): a two-tone 16 px pattern and
# a nine-slice whose edge cells carry a scalloped rim onto the lawn. Recoloured to HGSS's
# blue-grey cobbles (as_fe01): stones in its light stone colour, joints in its mortar.
SLATE_NINE = {('N', 'W'): 0x208, ('N', 'M'): 0x209, ('N', 'E'): 0x20A, ('M', 'W'): 0x210, ('M', 'M'): 0x211,
              ('M', 'E'): 0x212, ('S', 'W'): 0x218, ('S', 'M'): 0x219, ('S', 'E'): 0x21A}
COBBLE = {6 * 16 + 2: (173, 189, 198), 6 * 16 + 3: (140, 156, 165)}   # Slateport bank 6: stone, joint
LAWN = 6 * 16 + 15                                                   # Slateport's grass beyond the rim

def paving(engine):
    out = {}
    for k, mid in SLATE_NINE.items():
        rgb, key = gen3_meta(engine, 'general', 'slateport', mid)
        out[k] = key
    return out

# --------------------------------------------------------------------------- deck
# FRLG Vermilion's pier planks (General FRLG 0x1C6: four plank shades in 4 px boards),
# turned a quarter so the boards run north-south as HGSS's do, in HGSS's deck greys (as_fe02).
DECK = {5 * 16 + 6: (222, 222, 222), 5 * 16 + 7: (206, 206, 206), 5 * 16 + 8: (189, 189, 189), 5 * 16 + 9: (156, 156, 156)}
DECK_EDGE = [(132, 132, 132), (90, 90, 90)]                          # HGSS as_fe02_r: the deck's side, its shadow
QUAY = [(222, 222, 222), (189, 189, 189), (132, 132, 132), (90, 90, 90), (49, 49, 57)]    # all harbour greys

# Two 8 px boards per cell, the way Vermilion's pier draws its planks (a seam, a lit edge,
# the board, a shaded edge, a few grain pixels), joints staggered half a cell, so the deck
# repeats every cell. HGSS's boards are about this wide; at 4 px they read as corrugation.
BOARD = ["sLbbbbbm", "sLbbbbbm", "sLbbbbbm", "sLbbbbbm", "sLbbgbbm", "sLbbbbbm", "sLbbbbbm", "sLbbbbbm",
         "ssssssss", "LLLLLLLm", "sLbbbbbm", "sLbgbbbm", "sLbbbbbm", "sLbbbbbm", "sLbbbbgm", "sLbbbbbm"]
BOARD_PAL = dict(s=(156, 156, 156), L=(222, 222, 222), b=(206, 206, 206), m=(189, 189, 189), g=(189, 189, 189))

def planks(engine):
    a = np.array([[BOARD_PAL[ch] for ch in r] for r in BOARD], np.uint8)
    b = np.roll(a, 8, axis=0)[:, ::-1]                              # the second board, its joint half a cell on
    b = np.concatenate([b[:, -1:], b[:, :-1]], 1)                   # its seam on its own left edge
    return np.concatenate([a, b], 1)

# --------------------------------------------------------------------------- ground
def ground(cells, tex, engine):
    """Bottom layer: every cell's own ground. Lawns are Cherrygrove's grass, the road its
    path, the sea its sea in phase; the plaza Slateport's paving per 8x8 quadrant, each
    quadrant facing a lawn taking the nine-slice piece its two edges call for (the rim
    onto the lawn is on the paving side, the lawn beyond it the plainest grass block, so
    edge tiles do not multiply by the grass's phase); the deck Vermilion's planks."""
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    out = tex['grass'][ys % 32, xs % 32].copy()
    floor = np.array([[c['floor'] for c in row] for row in cells])
    lab = np.array([[c['lab'] for c in row] for row in cells])
    pave = paving(engine)
    board = planks(engine)
    green = plain(tex, 'grass')
    is_cobble = lambda x, y: not (0 <= x < W and 0 <= y < H) or floor[y, x] in ('cobble', 'kerb', 'deck', 'sand', 'ramp', 'beach')
    for y in range(H):
        for x in range(W):
            f = floor[y, x]
            cell = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            if f == 'water' or f == 'shallow':
                out[cell] = tex['water'][ys[cell] % 32, xs[cell] % 32]
            elif f in ('sand', 'kerb'):
                out[cell] = tex['path'][ys[cell] % 32, xs[cell] % 32]
            elif f == 'beach':
                out[cell] = tex['beach'][ys[cell] % 16, xs[cell] % 16]
            elif f == 'deck':
                out[cell] = board
            elif f == 'cobble':
                lo = {k: not is_cobble(x + dx, y + dy) for k, (dx, dy) in DIRS.items()}
                blk = np.zeros((16, 16, 3), np.uint8)
                for qy in (0, 1):
                    v = ('N', 'S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M'
                    for qx in (0, 1):
                        h = ('W', 'E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M'
                        sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
                        key = pave[(v, h)][sl]
                        q = np.where((key == LAWN)[..., None], green[sl], np.array([COBBLE.get(int(k), (0, 0, 0)) for k in key.ravel()],
                                                                                     np.uint8).reshape(8, 8, 3))
                        blk[sl] = q
                out[cell] = blk
    return out

def deck_edges(out, top, cells):
    """The deck's rims: a dark side where it meets the sea, the quay's low rail on its
    south edge (posts every 8 px and a bar, on the top layer) above the deck's front face,
    and a step line where it meets the plaza."""
    floor = lambda x, y: cells[y][x]['floor'] if 0 <= x < W and 0 <= y < H else 'water'
    lab = lambda x, y: cells[y][x]['lab'] if 0 <= x < W and 0 <= y < H else '~'
    for y in range(H):
        for x in range(W):
            if floor(x, y) != 'deck':
                continue
            X0, Y0 = x * 16, y * 16
            if lab(x, y) in 'qB' and floor(x, y + 1) == 'water':
                # HGSS's quay edge: a row of low posts, the stone lip, the deck's dark front.
                out[Y0 + 9:Y0 + 10, X0:X0 + 16] = QUAY[0]
                out[Y0 + 10:Y0 + 12, X0:X0 + 16] = QUAY[1]
                out[Y0 + 12:Y0 + 14, X0:X0 + 16] = QUAY[2]
                out[Y0 + 14:Y0 + 16, X0:X0 + 16] = QUAY[3]
                for px in (X0 + 2, X0 + 10):
                    out[Y0 + 4:Y0 + 9, px:px + 4] = QUAY[1]
                    out[Y0 + 4:Y0 + 6, px:px + 4] = QUAY[0]
                    out[Y0 + 4:Y0 + 9, px + 3] = QUAY[2]
                    out[Y0 + 9, px:px + 4] = QUAY[2]
                continue
            for side, (dx, dy) in dict(w=(-1, 0), e=(1, 0), s=(0, 1)).items():
                if floor(x + dx, y + dy) == 'water' and lab(x + dx, y + dy) not in 'X':
                    if side == 'w':
                        out[Y0:Y0 + 16, X0] = DECK_EDGE[1]; out[Y0:Y0 + 16, X0 + 1] = DECK_EDGE[0]
                    elif side == 'e':
                        out[Y0:Y0 + 16, X0 + 15] = DECK_EDGE[1]; out[Y0:Y0 + 16, X0 + 14] = DECK_EDGE[0]
                    else:
                        out[Y0 + 14:Y0 + 16, X0:X0 + 16] = (DECK_EDGE[0], DECK_EDGE[1])[1]
                        out[Y0 + 14, X0:X0 + 16] = DECK_EDGE[0]
            if floor(x, y - 1) == 'cobble':
                out[Y0, X0:X0 + 16] = DECK_EDGE[0]

# HGSS's kerb (as_fe01_r) between the road and the plaza: a band of 8 px bricks, each a
# dark frame round a panel, laid on the plaza side of the road; in Cherrygrove's path
# colours (CherrygrovePrimary bank 0), so it needs no secondary colours.
KERB = dict(f=(152, 144, 112), p=(216, 184, 128), i=(184, 168, 128))
BRICK = ["ffffffffffffffff", "fppppppppppppppf", "fpiiiiiiiiiiiipf", "fpippppppppppipf", "fpippppppppppipf",
         "fpiiiiiiiiiiiipf", "fppppppppppppppf", "ffffffffffffffff"]

def kerbs(out, cells):
    br = np.array([[KERB[ch] for ch in r] for r in BRICK], np.uint8)            # 16 x 8, along a run
    fl = lambda x, y: cells[y][x]['floor'] if 0 <= x < W and 0 <= y < H else ''
    for y in range(H):
        for x in range(W):
            if fl(x, y) != 'kerb':
                continue
            X0, Y0 = x * 16, y * 16
            pave = {k: fl(x + dx, y + dy) in ('cobble',) for k, (dx, dy) in DIRS.items()}
            if pave['s'] or (fl(x, y + 1) == 'kerb' and not pave['e'] and not pave['w']):
                out[Y0 + 8:Y0 + 16, X0:X0 + 16] = br
            if pave['e'] or pave['se'] and not pave['s']:
                out[Y0:Y0 + 16, X0 + 8:X0 + 16] = br.transpose(1, 0, 2)
            if pave['w'] or pave['sw'] and not pave['s']:
                out[Y0:Y0 + 16, X0:X0 + 8] = br.transpose(1, 0, 2)
            if pave['n']:
                out[Y0:Y0 + 8, X0:X0 + 16] = br

# --------------------------------------------------------------------------- rock
def layers(cells):
    """Integer terrace level per cell and the set of rock cells facing a lower one."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    rock = np.isin(lab, list(ROCK))
    d = np.array([[c['terrace'] for c in row] for row in cells], int)
    pad = np.pad(d, 1, mode='edge')
    lower = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lower |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] < d
    return d, rock & lower, rock

# FRLG mountain set: bank 1 ramp 9-14 light to dark; 4 is the cast shadow.
FRLG_RAMP = {9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6}
FRLG_NINE = {('N', 'W'): 0x68, ('N', 'M'): 0x69, ('N', 'E'): 0x6A, ('M', 'W'): 0x70, ('M', 'M'): 0x71,
             ('M', 'E'): 0x72, ('S', 'W'): 0x78, ('S', 'M'): 0x79, ('S', 'E'): 0x7A}
FRLG_NINE_OVER_ROCK = {('N', 'W'): 0x6B, ('N', 'M'): 0x6C, ('N', 'E'): 0x6D, ('M', 'W'): 0x73, ('M', 'M'): 0x71,
                       ('M', 'E'): 0x75, ('S', 'W'): 0x7B, ('S', 'M'): 0x7C, ('S', 'E'): 0x7D}   # an edge onto lower rock
FRLG_INNER = dict(se=0xB2, sw=0xB3, ne=0xBA, nw=0xBB)          # whole-cell inner corners
CLEAR, SHADOW = -1, -2

def frlg_pieces(engine):
    """FRLG General's mountain pieces as index maps into the HGSS rock ramp (bank 1 only)."""
    d = engine / 'data/tilesets/primary/general_frlg'
    tiles = _tiles(d)
    blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    def piece(m):
        out = np.full((16, 16), CLEAR, int)
        for li in range(8):
            e = int(blocks[m][li])
            if e >> 12 != 1:
                continue
            t = tiles[e & 1023]
            if e & 0x400: t = t[:, ::-1]
            if e & 0x800: t = t[::-1]
            q = li % 4
            sub = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            for (yy, xx), v in np.ndenumerate(t):
                if v:
                    sub[yy, xx] = FRLG_RAMP.get(int(v), SHADOW)
        return out
    return dict(nine={k: piece(v) for k, v in FRLG_NINE.items()}, rock={k: piece(v) for k, v in FRLG_NINE_OVER_ROCK.items()},
                inner={k: piece(v) for k, v in FRLG_INNER.items()})

def rock_frlg(cells, base, pieces, tex):
    """Blob autotiling from FRLG's set (Blackthorn's and Cianwood's composer). A cell whose
    only lower neighbours are diagonal takes FRLG's whole inner-corner piece; every other
    cell is composed per 8x8 quadrant from the nine-slice piece its two edges call for,
    the over-rock pieces where the quadrant faces a lower rock terrace. The rock is a
    top-layer overlay; its clear pixels show what lies beyond that edge (the plainest
    8x8 block of that ground, or the rock top), its cast shadow Cherrygrove's border grey.
    Under a fully opaque quadrant the bottom is the rock top, so solid rock is one metatile."""
    d, face, isrock = layers(cells)
    out = base.copy()
    over = np.zeros(base.shape[:2] + (4,), np.uint8)
    nine, nine_rock, inner = pieces['nine'], pieces['rock'], pieces['inner']
    clamp = lambda x, y: (min(max(x, 0), W - 1), min(max(y, 0), H - 1))
    lvl = lambda x, y: d[clamp(x, y)[1], clamp(x, y)[0]]
    fill = np.array([BLACKTHORN_RAMP[i] for i in nine[('M', 'M')].ravel()], np.uint8).reshape(16, 16, 3)
    flat = {k: plain(tex, k) for k in PLAIN}
    def beyond(x, y):
        cx, cy = clamp(x, y)
        if isrock[cy, cx]:
            return fill, 'rock'
        f = cells[cy][cx]['floor']
        if f in ('water', 'shallow'):
            return flat['water'], 'water'
        if f == 'sand':
            return flat['path'], 'sand'
        if f in ('grass',):
            return flat['grass'], 'grass'
        return base[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16], 'other'
    cast = dict(grass=BORDER_GRAY, sand=BORDER_GRAY, rock=None, water=None, other=BORDER_GRAY)
    piece = np.full((H, W), '', object)
    for y in range(H):
        for x in range(W):
            if not isrock[y, x]:
                continue
            me = d[y, x]
            lo = {k: lvl(x + dx, y + dy) < me for k, (dx, dy) in DIRS.items()}
            X0, Y0 = x * 16, y * 16
            cell, ov = out[Y0:Y0 + 16, X0:X0 + 16], over[Y0:Y0 + 16, X0:X0 + 16]
            diag = [k for k in ('ne', 'se', 'sw', 'nw') if lo[k]]
            whole = None
            if not any(lo[k] for k in 'nesw') and diag:
                if len(diag) == 1:
                    whole = inner[diag[0]]
                elif sorted(diag) in (['se', 'sw'], ['ne', 'nw']):
                    r, l = ('se', 'sw') if 'se' in diag else ('ne', 'nw')
                    whole = np.concatenate([inner[l][:, :8], inner[r][:, 8:]], 1)
            for qy in (0, 1):
                v = ('N', 'S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M'
                for qx in (0, 1):
                    h = ('W', 'E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M'
                    sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
                    vk, hk = 'ns'[qy], 'we'[qx]
                    toward = next((DIRS[k] for k in (vk, hk, vk + hk) if lo[k]), None)
                    bg, kind = beyond(x + toward[0], y + toward[1]) if toward else (fill, 'rock')
                    if whole is not None:
                        ix = whole[sl]
                    elif lo[vk + hk] and not lo[vk] and not lo[hk]:
                        ix = inner[vk + hk][sl]
                    else:
                        ix = (nine_rock if kind == 'rock' else nine)[(v, h)][sl]
                    cell[sl] = bg[sl]
                    q = ov[sl]
                    for (yy, xx), k in np.ndenumerate(ix):
                        if k >= 0:
                            q[yy, xx] = BLACKTHORN_RAMP[k] + (255,)
                        elif k == SHADOW and cast[kind]:
                            q[yy, xx] = cast[kind] + (255,)
                    if (q[..., 3] > 0).all():
                        cell[sl] = fill[sl]
            piece[y, x] = ''.join(k for k in DIRS if lo[k])
    return out, over, d, piece

# --------------------------------------------------------------------------- trees
# HGSS's Olivine tree (tree01_re crown over tree01_un trunk and shadow, as its top-down
# terrain draws it), cut out at one tree and mapped onto Cherrygrove's tree greens
# (CherrygrovePrimary bank 3, the accepted Johto trees' own ramp) by nearest colour, so
# every tree tile needs no secondary colours. Its shadow is Cherrygrove's tree shadow.
TREE_RAMP = [(64, 56, 40), (64, 64, 40), (72, 72, 48), (80, 88, 40), (88, 104, 32), (88, 112, 32), (96, 120, 32),
             (112, 144, 32), (120, 152, 32), (136, 168, 40), (136, 104, 64)]
TREE_SHADOW = (64, 136, 104)

def tree_sprite(phg_topdown):
    """32 x 32 RGBA: one HGSS tree from the forest's top row (trunk row 7, cells 36-37),
    crown and trunk kept, grass cleared, shadow pixels in the tree shadow."""
    h, mat, names, rgb = phg_topdown
    X0, Y0 = 36 * 16, 6 * 16 - 6
    win = rgb[Y0:Y0 + 32, X0:X0 + 32].astype(int)
    m = mat[Y0:Y0 + 32, X0:X0 + 32]
    crown = np.isin(m, [names.index('tree01_re'), names.index('tree01gs')])
    under = m == names.index('tree01_un')
    green = (win[..., 1] > win[..., 0] + 50) & (win[..., 2] > 90)            # the grass and its shadow tones
    shadow = under & green & (win.sum(-1) < 330)
    body = crown | (under & ~green)
    img = np.zeros((32, 32, 4), np.uint8)
    P = np.array(TREE_RAMP, int)
    near = ((win[..., None, :] - P[None, None]) ** 2).sum(-1).argmin(-1)
    img[body, :3] = P[near][body]; img[body, 3] = 255
    img[shadow & ~body] = TREE_SHADOW + (255,)
    return img

def trees(top, cells, sprite):
    """One tree per HGSS tree, north rows first so a tree in front overlaps the one behind."""
    seen = sorted({tuple(c['tree']) for row in cells for c in row if 'tree' in c}, key=lambda t: (t[1], t[0]))
    for x0, y0 in seen:
        X0, Y0 = x0 * 16, y0 * 16
        for yy in range(32):
            for xx in range(32):
                if sprite[yy, xx, 3] and 0 <= Y0 + yy < H * 16 and 0 <= X0 + xx < W * 16:
                    top[Y0 + yy, X0 + xx] = sprite[yy, xx]
    return seen

# --------------------------------------------------------------------------- fences
# HGSS's chain fence (fence_a) the Gen 3 way: posts every 8 px, a white cap, an outline,
# a chain between them; vertical runs show the posts end on. In fence_a's greys as the
# harbour ramp holds them.
FENCE = dict(o=(49, 49, 57), d=(107, 107, 107), m=(132, 132, 132), l=(156, 156, 156), c=(206, 206, 206), w=(239, 247, 255))
FENCE_H = ["........", "..oooo..", ".occwco.", ".ollllo.", ".ommmmo.", "oommmmoo", "ddommodd", "ooommooo", ".ommmmo.", ".oddddo.", "..oooo.."]
FENCE_V = ["...oo...", "..occo..", "..olwo..", "..olmo..", "..ommo..", "..odmo..", "..oddo..", "...oo..."]

def fences(top, cells):
    f = lambda x, y: 0 <= x < W and 0 <= y < H and cells[y][x]['lab'] == 'f'
    hpost = np.array([[FENCE.get(ch, (0, 0, 0)) + ((255,) if ch in FENCE else (0,)) for ch in r] for r in FENCE_H], np.uint8)
    vpost = np.array([[FENCE.get(ch, (0, 0, 0)) + ((255,) if ch in FENCE else (0,)) for ch in r] for r in FENCE_V], np.uint8)
    def put(img, X, Y):
        a = img[..., 3] > 0
        top[Y:Y + img.shape[0], X:X + img.shape[1]][a] = img[a]
    for y in range(H):
        for x in range(W):
            if not f(x, y):
                continue
            X0, Y0 = x * 16, y * 16
            horiz = f(x - 1, y) or f(x + 1, y)
            vert = f(x, y - 1) or f(x, y + 1)
            if vert:
                # posts end on, two per cell, joined by a rail
                for py in (Y0, Y0 + 8):
                    put(vpost, X0 + 4, py)
                rail = top[Y0:Y0 + 16, X0 + 7:X0 + 9]
                rail[rail[..., 3] == 0] = FENCE['d'] + (255,)
            if horiz or not vert:
                for px in (X0, X0 + 8):
                    put(hpost, px, Y0 + 3)
                if f(x + 1, y):
                    pass

# --------------------------------------------------------------------------- props
# HGSS's sea rocks (sea_rock blobs, 32 x 22 each; a wider blob is touching rocks, 481 px
# apiece), small rocks (sea_rock_m), boulders (rock01) and stones (etc_a): top-left
# corners in cells, from the decoded top-down map.
def prop_blobs(td, name, unit=None):
    from scipy import ndimage
    h, mat, names, rgb = td
    m = mat == names.index(name)
    lab, n = ndimage.label(m)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        k = int((lab[sl] == i + 1).sum())
        if k < 8:
            continue
        x0, y0 = sl[1].start / 16, sl[0].start / 16
        for j in range(max(1, round(k / unit)) if unit else 1):
            out.append((x0 + 2 * j, y0))
    return out

def snap(v):
    return int(round(v * 16 / 8)) * 8

def sea_props(top, td, phg):
    sys.path.insert(0, str(HERE))
    import sprites as S
    tex = hgss_texture(phg, 'sea_rock', 'sea_rock')
    rock, peb = S.sea_rock(tex), S.sea_rock(tex, 16, 13)
    for img in (rock, peb):                                       # the rocks' greys as the harbour ramp holds them
        a = img[..., 3] > 0
        img[a, :3] = np.array([harbour(tuple(c)) for c in img[a, :3].tolist()], np.uint8)
    placed = []
    for img, pos in ((rock, prop_blobs(td, 'sea_rock', 481)), (peb, prop_blobs(td, 'sea_rock_m'))):
        for x0, y0 in pos:
            X, Y = snap(x0), snap(y0)
            sl = top[Y:Y + img.shape[0], X:X + img.shape[1]]
            a = img[:sl.shape[0], :sl.shape[1], 3] > 0
            sl[a] = img[:sl.shape[0], :sl.shape[1]][a]
            placed.append(('sea_rock' if img is rock else 'pebble', X, Y))
    return placed

def boulders(top, td, phg):
    """HGSS's boulder (rock01, clean pixel art) snapped onto the rock ramp by brightness
    (its own shades are that ramp's), and the small stones (Cianwood's)."""
    sys.path.insert(0, str(HERE))
    import sprites as S
    r = hgss_texture(phg, 'rock01', 'rock01').copy()
    a = r[..., 3] > 0
    light = sorted(BLACKTHORN_RAMP, key=sum)
    lum = r[..., :3].astype(int).sum(-1)
    levels = np.quantile(lum[a], np.linspace(0, 1, len(light) + 1)[1:-1])
    r[..., :3] = np.array(light, np.uint8)[np.searchsorted(levels, lum)]
    placed = []
    for x0, y0 in prop_blobs(td, 'rock01'):
        X, Y = int(round(x0)) * 16, int(round(y0)) * 16
        sl = top[Y:Y + 32, X:X + 32]
        sl[a[:sl.shape[0], :sl.shape[1]]] = r[:sl.shape[0], :sl.shape[1]][a[:sl.shape[0], :sl.shape[1]]]
        placed.append(('boulder', X, Y))
    st = S.stone(hgss_texture(phg, 'etc_a', 'etc_a'))
    for x0, y0 in prop_blobs(td, 'etc_a'):
        X, Y = snap(x0), int(y0) * 16 + 8
        sl = top[Y:Y + 8, X:X + 16]
        m = st[..., 3] > 0
        sl[m] = st[m]
        placed.append(('stone', X, Y))
    return placed

# HGSS's steps (slope, the stone stair at the top of the stair lane) and the Lighthouse
# ramp, in the slope texture's own colours: treads light, risers dark. The stair climbs
# north (treads across); the ramp climbs east (treads up and down).
STEP = [(224, 224, 184), (184, 168, 128), (152, 144, 112), (128, 136, 120)]   # slope's tans in CherrygrovePrimary bank 0

def steps(out, cells):
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if c['floor'] != 'ramp' or c['lab'] != '.':
                continue
            X0, Y0 = x * 16, y * 16
            ramp = cells[y][x - 1]['floor'] == 'deck' or cells[y][x - 1]['floor'] == 'ramp' or cells[y][x + 1]['floor'] == 'ramp'
            blk = np.zeros((16, 16, 3), np.uint8)
            for r in range(16):
                blk[r if not ramp else slice(None), r if ramp else slice(None)] = STEP[(0, 0, 1, 3)[r % 4]]
            if not ramp:
                if cells[y][x - 1]['floor'] != 'ramp':
                    blk[:, 0] = STEP[3]; blk[:, 1] = STEP[2]
                if cells[y][x + 1]['floor'] != 'ramp':
                    blk[:, 15] = STEP[3]; blk[:, 14] = STEP[2]
            else:
                if cells[y - 1][x]['floor'] != 'ramp':
                    blk[0] = STEP[3]; blk[1] = STEP[2]
                if cells[y + 1][x]['floor'] != 'ramp':
                    blk[15] = STEP[3]; blk[14] = STEP[2]
            out[Y0:Y0 + 16, X0:X0 + 16] = blk

def rock_climb(top, cells, phg):
    """HGSS's rock climb holds (r_climb: four rounded stepping holds, 16 px, clean pixel
    art) at their own size over the rock's face, in the rock ramp."""
    sys.path.insert(0, str(HERE))
    import sprites as S
    t = S.to_ramp(hgss_texture(phg, 'r_climb', 'r_climb'), BLACKTHORN_RAMP)
    a = t[..., 3] > 0
    for y in range(H):
        for x in range(W):
            if cells[y][x]['lab'] == 'C':
                top[y * 16:y * 16 + 16, x * 16:x * 16 + 16][a] = t[a]

# --------------------------------------------------------------------------- shore
# The east cove's beach (beach01) and its surf strip as Cherrygrove's sandbar (Cianwood's
# shore): each shallow cell beside land on one side is the sandbar's edge cell for that
# side, its sea pixels the sea at the map's phase, its sand the sandbar's plain cream.
SHORE_EDGE = dict(w=(432, 384), e=(352, 384), n=(384, 400), s=(368, 341))

def shore(out, cells, tex):
    img = np.array(Image.open(SRC / 'elements/cherrygrove-native.png').convert('RGB'))
    ys, xs = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    sea_src = (img == tex['water'][ys % 32, xs % 32]).all(-1)
    gy, gx = np.mgrid[0:H * 16, 0:W * 16]
    sea = tex['water'][gy % 32, gx % 32]
    land = lambda x, y: 0 <= x < W and 0 <= y < H and cells[y][x]['floor'] not in ('water', 'shallow')
    for y in range(H):
        for x in range(W):
            if cells[y][x]['floor'] != 'shallow':
                continue
            sides = [k for k, (dx, dy) in dict(w=(-1, 0), e=(1, 0), n=(0, -1), s=(0, 1)).items()
                     if land(x + dx, y + dy) and cells[y + dy][x + dx]['floor'] == 'beach']
            if len(sides) != 1:
                continue
            sx, sy = SHORE_EDGE[sides[0]]
            cell = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            piece, wet = img[sy:sy + 16, sx:sx + 16], sea_src[sy:sy + 16, sx:sx + 16]
            out[cell] = np.where(wet[..., None], sea[cell], piece)

# --------------------------------------------------------------------------- objects
# Buildings and props: each sprite's model origin on HGSS's placement across (snapped to
# the 8 px grid, so mirrored halves meet on a tile edge), its bottom on the bottom of its
# base row (the door's row, the bench's blocked row, a pole's foot). The Center (C06) and
# the shared Mart stand with their doors on HGSS's Center and Mart doors.
SHARED = SRC / 'shared-art'
# HGSS's city sign (board_ab) and its pier and Lighthouse notice boards (board_cd), as
# sprites; the Gym sign stays out (no Gym).
CENTER_ORIGIN = (14, 29)                # C06: 5x5, door tile (2,4) on HGSS's Center door (16,33)
MART_ORIGIN = (27, 28)                  # shared Mart: 7x6, door tile (2,5) on HGSS's Mart door (29,33)
# name, sprite, HGSS model x (cells), base row; bottom px overrides the base row
PLACES = [('gym', 'gym', 13.5, 14), ('cafe', 'cafe', 10.0, 33), ('house_0', 'house', 18.0, 23),
          ('house_1', 'house', 32.0, 17), ('house_2', 'house', 37.0, 17), ('lighthouse', 'lighthouse', 45.5, 39),
          ('terminal', 'terminal', 23.5, 60), ('bench_0', 'bench', 9.0, 42), ('bench_1', 'bench', 16.0, 42),
          ('bench_2', 'bench', 31.0, 42), ('yacht_0', 'yacht', 16.559, 48.5), ('yacht_1', 'yacht', 30.559, 48.5),
          ('bunting_0', 'bunting', 23.5, 0), ('bunting_1', 'bunting', 9.75, 21), ('bunting_2', 'bunting', 23.0, 30),
          ('citysign', 'citysign', 23.5, 23), ('board_0', 'board', 24.5, 42), ('board_1', 'board', 46.5, 40)]
# The flag line between the Center and the Mart stands 0.75 cells west of HGSS's, so its
# east pole clears the shared Mart (two cells wider than HGSS's).

def objects():
    sys.path.insert(0, str(HERE))
    import sprites as S
    origin = json.loads((SRC / 'elements/sprites/origins.json').read_text())
    out = []
    for name, sprite, mx, row in PLACES:
        img = S.load(sprite)
        X = int(round((mx * 16 - origin[sprite][0]) / 8)) * 8
        Y = int(round((row + 1) * 16)) - img.shape[0]
        out.append((name, img, X, Y))
    return out

TERRAIN_PROPS = ('tree', 'fence', 'rock', 'boulder', 'stone')

def place(bottom, top, owner, cells):
    """Objects in painter's order, north base rows first, so one standing further south
    draws over one behind it. An 8x8 tile that would mix a building's colours with a
    tree's, a fence's or a rock's keeps the building and loses the other's pixels there
    (no bank holds both; the building stands in front); the shared Center and Mart go on a
    layer of their own with their exact palettes, and nothing else keeps pixels in their tiles."""
    shared = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    shared_src = np.zeros(bottom.shape[:2], np.uint8)            # 1 Mart, 2 Center
    for src, f, (ox, oy) in ((1, 'poke-mart.png', MART_ORIGIN), (2, 'pokemon-center.png', CENTER_ORIGIN)):
        img = np.array(Image.open(SHARED / f).convert('RGBA'))
        sl = np.s_[oy * 16:oy * 16 + img.shape[0], ox * 16:ox * 16 + img.shape[1]]
        a = img[..., 3] > 0
        shared[sl][a] = img[a]; shared_src[sl][a] = src
        owner[sl][a] = 'poke_mart' if src == 1 else 'pokemon_center'
    lost = 0
    blocked = np.array([[c['blocked'] or c['lab'] in ROCK for c in row] for row in cells])
    for name, img, X, Y in sorted(objects(), key=lambda o: (o[3] + o[1].shape[0], o[2])):
        h, w = img.shape[:2]
        y0, x0 = max(Y, 0), max(X, 0)
        y1, x1 = min(Y + h, H * 16), min(X + w, W * 16)
        part = img[y0 - Y:y1 - Y, x0 - X:x1 - X]
        a = part[..., 3] > 0
        sl = np.s_[y0:y1, x0:x1]
        for ty in range(y0 // 8, (y1 + 7) // 8):
            for tx in range(x0 // 8, (x1 + 7) // 8):
                ts = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                hit = np.zeros((H * 16, W * 16), bool)[ts]
                mine = np.zeros((8, 8), bool)
                yy, xx = np.mgrid[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                inside = (yy >= y0) & (yy < y1) & (xx >= x0) & (xx < x1)
                mine[inside] = a[(yy - y0)[inside], (xx - x0)[inside]]
                if not mine.any():
                    continue
                o = owner[ts].astype(str)
                prop = np.zeros((8, 8), bool)
                for k in TERRAIN_PROPS:
                    prop |= np.char.startswith(o, k)
                prop &= (top[ts][..., 3] > 0) & ~mine
                if prop.any():
                    top[ts][prop] = 0; owner[ts][prop] = ''; lost += int(prop.sum())
                # Under an object in a blocked cell (drawn below the player either way) the
                # rock's top-layer overlay drops to the bottom layer, so the object's tiles
                # do not mix with the rock's.
                rock = (owner[ts] == '') & (top[ts][..., 3] > 0) & ~mine
                if rock.any() and blocked[ty // 2, tx // 2]:
                    bottom[ts][rock] = top[ts][..., :3][rock]
                    top[ts][rock] = 0
        top[sl][a] = part[a]
        owner[sl][a] = name
    # nothing else keeps pixels in a tile the shared buildings touch
    for ty in range(H * 2):
        for tx in range(W * 2):
            ts = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if (shared[ts][..., 3] > 0).any():
                top[ts] = 0
    place.tree_pixels_lost = lost
    return shared, shared_src

# --------------------------------------------------------------------------- compose
def compose(engine, phg, cells, td):
    tex = cherry_textures()
    bottom = ground(cells, tex, engine)
    top0 = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    deck_edges(bottom, top0, cells)
    kerbs(bottom, cells)
    steps(bottom, cells)
    shore(bottom, cells, tex)
    bottom, top, level, piece = rock_frlg(cells, bottom, frlg_pieces(engine), tex)
    owner = np.full(bottom.shape[:2], '', dtype='<U16')
    a = top0[..., 3] > 0
    top[a] = top0[a]
    rock_climb(top, cells, phg)
    before = top[..., 3] > 0
    for x0, y0 in trees(top, cells, tree_sprite(td)):
        sl = np.s_[y0 * 16:y0 * 16 + 32, x0 * 16:x0 * 16 + 32]
        owner[sl][(top[sl][..., 3] > 0) & ~before[sl]] = f'tree_{x0}_{y0}'
    before = top[..., 3] > 0
    fences(top, cells)
    owner[(top[..., 3] > 0) & ~before] = 'fence'
    for kind, X, Y in sea_props(top, td, phg) + boulders(top, td, phg):
        sl = np.s_[Y:Y + 32, X:X + 32]
        owner[sl][(top[sl][..., 3] > 0) & (owner[sl] == '')] = {'sea_rock': 'rock', 'pebble': 'rock', 'boulder': 'boulder',
                                                                 'stone': 'stone'}[kind] + f'_{X}_{Y}'
    shared, shared_src = place(bottom, top, owner, cells)
    return bottom, top, level, piece, owner, shared, shared_src

def preview(bottom, top, shared=None):
    out = bottom.copy()
    a = top[..., 3] > 0
    out[a] = top[..., :3][a]
    if shared is not None:
        a = shared[..., 3] > 0
        out[a] = shared[..., :3][a]
    return out

def main(engine, phg):
    td = topdown(phg)
    cells = ledger(phg)
    save_ledger(cells)
    (EV / 'elements').mkdir(parents=True, exist_ok=True)
    bottom, top, level, piece, owner, shared, shared_src = compose(engine, phg, cells, td)
    np.savez_compressed(SRC / 'elements' / 'compose-C.npz', bottom=bottom, top=top, shared=shared, shared_src=shared_src,
                        owner=owner, level=level, piece=piece.astype(str))
    v = preview(bottom, top, shared)
    Image.fromarray(v).save(EV / 'elements' / 'terrain-C.png')
    ref = np.array(Image.open(SRC / 'hgss/hgss-render.png').convert('RGB'))
    sheet = Image.new('RGB', (W * 16 * 2 + 12, H * 16 + 24), (28, 32, 38)); d = ImageDraw.Draw(sheet)
    for i, (img, t) in enumerate(((ref, 'HGSS reference (decoded map data)'), (v, 'Gen 3 elements'))):
        sheet.paste(Image.fromarray(img), (i * (W * 16 + 12), 24)); d.text((i * (W * 16 + 12) + 4, 6), t, fill='white')
    sheet.save(EV / 'elements' / 'compare.png')
    print('wrote terrain-C.png and compare.png; tree, fence and rock pixels given up to buildings:', place.tree_pixels_lost)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
