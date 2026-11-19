"""The apartment block built from its floor plans (apartments_floorplans.py) in HGSS's model
styling (owner, 2026-11-03).

    python3 tools/gba/maps/celadon_elements/apartments_build.py assets PATH/TO/pokeheartgold
    python3 tools/gba/maps/celadon_elements/apartments_build.py compose

The city's method indoors: the floors are HGSS's own room floors at 1:1, seen from above (cut
from HGSS's top-down renders of its Celadon Condominiums); everything standing (walls, doors,
stairs, furniture) is HGSS's own model at the city's 45 degrees with the Gen 3 finish
(gen3_art.convert): the walls cut from HGSS's room shells rendered at 45 degrees, the furniture
HGSS's room models (a/1/4/8). The one piece from FireRed is its sofa (HGSS has none; owner).

    assets   renders and cuts every piece into gba/art/celadon-elements/source/apartments/
    compose  draws each floor from its plan: evidence/apartments/built-*.png, and per floor the
             picture, its two layers and its traversal (source/apartments/<floor>.npz)

Walls by the game's rule: a wall cell with floor south of it shows the lower half of its face,
the cell above that the upper half (so an east-west wall and the end of a north-south wall show
a two-cell face), any other wall cell its top, seen from above. A piece stands with its bottom
on its footprint's last row; what it draws above a walkable cell goes on the top layer, so the
player walks behind it.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C                                  # noqa: E402
import apartments_floorplans as FP                  # noqa: E402

ROOT = C.ROOT
ASSETS = ROOT / 'gba/art/celadon-elements/source/apartments'
EV = ROOT / 'gba/art/celadon-elements/evidence/apartments'
ROOMS = ROOT / 'gba/art/celadon-elements/source/hgss-rooms'

# --------------------------------------------------------------------------- assets
SHELLS = dict(c1f='MAP_CELADON_CONDOMINIUMS_1F', c2f='MAP_CELADON_CONDOMINIUMS_2F', room='MAP_CELADON_CONDOMINIUMS_ROOF_ROOM')

def render_shell(phg, name):
    """An HGSS room's own model (its land chunk, with its area's textures) at 45 degrees."""
    import gen3_art as G3
    import hgss_rooms as HRm
    r = C.R()
    a = phg / 'files/a'
    h = HRm.header(phg, name)
    d = (phg / 'files/fielddata/mapmatrix/map_matrix' / (h['matrix'].replace('NARC_map_matrix_', '').replace('_bin', '') + '.bin')).read_bytes()
    w, hh, hd, al, nl = d[:5]
    lid = struct.unpack_from('<H', d, 5 + nl + (2 * w * hh if hd else 0) + (w * hh if al else 0))[0]
    ch = r.hgss_map.MapChunk.parse(r.narc.load(a / '0/6/5')[lid])
    bld, ms = struct.unpack_from('<HH', r.narc.load(a / '0/4/2')[h['area']], 0)
    tex0 = r.Tex0(r.narc.load(a / '0/4/4')[ms])
    Orig = r.mdlview.Model
    class M(Orig):
        def __init__(s, b):
            super().__init__(b)
            if b is ch.model:
                s.tex = tex0
    r.mdlview.Model = M
    try:
        img, _ = G3.convert([ch.model], [(0, (0, 0, 0))], scale=16.0, pitch=45.0, n=12, light=True, finish=True)
    finally:
        r.mdlview.Model = Orig
    return img

# HGSS room models used (a/1/4/8): name -> model id
MODELS = dict(bed=17, tv=19, stove=20, fridge=21, plant=23, pc=24, books=39, shelf=48, wardrobe=64, table=94, dining=98,
              coffee=90, stool=89, round=111, planter=114, tree=123, painting=139, counter=45, cabinet=37, mail=49, clock=16,
              lamp=157, stairs_up=11, elevator=63)

def assets(phg):
    import gen3_art as G3
    sys.path.insert(0, str(HERE.parent / 'olivine_elements'))
    import hgss_render as HR
    ASSETS.mkdir(parents=True, exist_ok=True)
    mods = HR.narc.load(phg / 'files/a/1/4/8')
    for name, mid in MODELS.items():
        img, _ = G3.convert(mods, [(mid, (0, 0, 0))], scale=16.0, pitch=45.0, n=10, finish=True)
        Image.fromarray(img).save(ASSETS / f'm_{name}.png')
    import apartments_plan as AP                      # FireRed's sofa, end-on, its own pixels
    m = AP.piece_mask('sofa_side'); px = AP.piece_pixels('sofa_side')
    img = np.zeros(px.shape[:2] + (4,), np.uint8); img[..., :3] = np.clip(px, 0, 255); img[..., 3] = m * 255
    Image.fromarray(img).save(ASSETS / 'm_sofa.png')
    for k, name in SHELLS.items():
        Image.fromarray(render_shell(phg, name)).save(ASSETS / f'shell_{k}.png')
    print('assets', sorted(p.name for p in ASSETS.glob('*.png')))

def load(name):
    return np.array(Image.open(ASSETS / f'{name}.png').convert('RGBA'))

def floors():
    """HGSS's floors at 1:1 from its top-down renders: one period of each."""
    top = lambda room: np.array(Image.open(ROOMS / f'condominiums_{room}/hgss-render.png').convert('RGB'))
    cut = lambda img, x, y, w, h: img[y * 16:(y + h) * 16, x * 16:(x + w) * 16]
    return dict(marble=cut(top('3f'), 8, 4, 2, 2), tile=cut(top('1f'), 3, 5, 2, 2), carpet=cut(top('roof_room'), 5, 3, 2, 2),
                blue=cut(top('3f'), 6, 9, 2, 2),
                paving=cut(np.array(Image.open(ROOMS / 'condominiums_roof/hgss-ground.png').convert('RGB')), 10, 2, 2, 2))

def cap(pillar):
    """A wall's top seen from above, one square: the tan of HGSS's wall top (its pillar's cap, as
    rendered), its two lit and shaded edges."""
    px = pillar[..., :3].reshape(-1, 3)
    a = pillar[..., 3].reshape(-1) > 0
    from collections import Counter
    tan = [c for c, _ in Counter(tuple(int(v) for v in c) for c in px[a]).most_common()
           if c[0] > c[2] + 25 and c[0] > 160 and abs(c[0] - c[1]) < 30][:3]          # the cap's three tans
    light, mid, dark = sorted(tan, key=lambda c: -sum(c))
    out = np.zeros((16, 16, 4), np.uint8); out[..., 3] = 255
    out[..., :3] = mid
    out[:, 0:2, :3] = light; out[:, 14:16, :3] = dark
    return out

def walls():
    """HGSS's walls at 45 degrees, two cells tall (cap line, face, baseboard), cut from its
    rendered room shells: each style's plain run (two cells, its period) and its window."""
    c1, room, c2 = load('shell_c1f'), load('shell_room'), load('shell_c2f')
    cut = lambda img, x, y, w, h: img[y * 16:(y + h) * 16, x * 16:(x + w) * 16]
    return dict(orange=dict(plain=cut(c1, 13, 6, 2, 2), window=cut(c1, 19, 6, 2, 2)),
                cream=dict(plain=cut(room, 13, 6, 2, 2), window=cut(room, 10, 6, 3, 2)),
                cap=cap(cut(c1, 16, 6, 1, 1)), stairs_down=cut(c2, 21, 12, 2, 2), elevator=cut(c1, 9, 6, 3, 3))

# --------------------------------------------------------------------------- compose
FLOOR_OF = dict(lobby='marble', core='marble', living='tile', kitchen='tile', bed='carpet', closet='carpet', study='blue',
                terrace='paving')
WALL_OF = dict(lobby='orange', core='orange', living='cream', kitchen='cream', bed='cream', closet='cream', study='cream',
               terrace='cream')

def compose(plan, name):
    W, H = FP.W, FP.H
    fl, wl = floors(), walls()
    img = np.zeros((H * 16, W * 16, 3), np.int16)
    top = np.zeros((H * 16, W * 16, 4), np.uint8)
    kind = np.full((H, W), 'void', '<U8')
    style = np.full((H, W), 'core', '<U8')
    for (x0, y0, x1, y1), k, _ in plan['rooms']:
        kind[y0:y1 + 1, x0:x1 + 1] = 'floor'
        style[y0:y1 + 1, x0:x1 + 1] = k
    wall = np.zeros((H, W), bool)
    wall[0:2, :] = True
    for (x0, y0, x1, y1) in plan['walls']:
        wall[y0:y1 + 1, x0:x1 + 1] = True
    for x, y in plan['doors']:
        wall[y, x] = False
        kind[y, x] = 'floor'
        yy = y
        while yy < H - 1 and (yy, x) in {(dy, dx) for dx, dy in plan['doors']}:
            yy += 1
        style[y, x] = style[yy, x] if kind[yy, x] == 'floor' else style[max(0, y - 1), x]
    wall[H - 1, :] = False
    kind[wall] = 'wall'
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    # floors, in the world's phase
    for y in range(H):
        for x in range(W):
            if kind[y, x] != 'floor':
                continue
            f = FLOOR_OF.get(style[y, x])
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            if f is None:
                img[sl] = (150, 186, 120)
            else:
                t = fl[f]
                img[sl] = t[ys[sl] % t.shape[0], xs[sl] % t.shape[1]]
    # walls: faces where floor lies south, tops elsewhere
    below = lambda x, y, n: y + n < H and kind[y + n, x] != 'wall'
    for y in range(H):
        for x in range(W):
            if not wall[y, x]:
                continue
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            south = style[min(H - 1, y + 1), x] if below(x, y, 1) else style[min(H - 1, y + 2), x]
            ws = wl[WALL_OF.get(south, 'cream')]['plain']
            ph = (x % 2) * 16
            if below(x, y, 1):
                cell = ws[16:32, ph:ph + 16]
            elif below(x, y, 2):
                cell = ws[0:16, ph:ph + 16]
            else:
                cell = wl['cap']
            a = cell[..., 3] > 0
            img[sl][a] = cell[..., :3][a]
            img[sl][~a] = (60, 50, 40)
    pic = img.copy()
    objs = []
    def put(sprite, x, y, w, h, layer_split=True, name='', rows_solid=None):
        """A piece with its bottom on footprint row y + h - 1, centred over x .. x + w - 1."""
        sh, sw = sprite.shape[:2]
        X = x * 16 + (w * 16 - sw) // 2
        Y = (y + h) * 16 - sh
        objs.append(dict(img=sprite, X=X, Y=Y, x=x, y=y, w=w, h=h, name=name))
    # windows on the north wall where nothing stands against it
    against = {(fx, ) for n, fx, fy in plan['furniture'] if fy <= 1 for fx in range(fx, fx + FP.F[n][2])}
    fixed = set()
    for (x0, y0, x1, y1), label in plan['fixtures']:
        if y0 == 0:
            fixed |= {(x, ) for x in range(x0 - 1, x1 + 2)}
    for x in range(1, W - 2, 4):
        s = style[2, x]
        if s == 'terrace' or {(x, ), (x + 1, )} & (against | fixed) or wall[2, x] or wall[2, x + 1]:
            continue
        win = wl[WALL_OF.get(s, 'cream')]['window'][:, :32]
        a = win[..., 3] > 0
        img[0:32, x * 16:x * 16 + 32][a] = win[..., :3][a]
    # fixtures: the elevator in the north wall, the stairs
    for (x0, y0, x1, y1), label in plan['fixtures']:
        if label == 'elevator':
            e = wl['elevator']
            a = e[..., 3] > 0
            X = x0 * 16 - 8
            reg = img[0:48, X:X + 48]
            reg[a] = e[..., :3][a]
            hole = ~a[:32]; hole[:4] = False
            reg[:32][hole & (np.arange(48)[None, :] > 8) & (np.arange(48)[None, :] < 40)] = (40, 40, 56)
        elif label.startswith('stairs up'):
            put(load('m_stairs_up'), x0, 1, 2, 3, name='stairs_up')
        elif label.startswith('stairs down'):
            s = wl['stairs_down']; a = s[..., 3] > 0
            img[2 * 16:4 * 16, x0 * 16:x0 * 16 + 32][a] = s[..., :3][a]
    for n, x, y in plan['furniture']:
        label, mid, w, h = FP.F[n]
        if y <= 1:
            y = 2 - (h - 1) if h > 1 else 2                   # standing against the wall, on the first floor row
        put(load(f'm_{n}'), x, y, w, h, name=n)
    # painter's order: by the bottom of each piece
    objs.sort(key=lambda o: (o['Y'] + o['img'].shape[0], o['X']))
    solid = np.zeros((H, W), bool)
    solid[wall] = True
    for o in objs:
        s = o['img']; a = s[..., 3] > 0
        X, Y = o['X'], o['Y']
        y0, x0 = max(0, -Y), max(0, -X)
        reg = img[Y + y0:Y + s.shape[0], X + x0:X + s.shape[1]]
        aa = a[y0:y0 + reg.shape[0], x0:x0 + reg.shape[1]]
        reg[aa] = s[y0:y0 + reg.shape[0], x0:x0 + reg.shape[1], :3][aa]
        for yy in range(o['y'], o['y'] + o['h']):
            for xx in range(o['x'], o['x'] + o['w']):
                if 0 <= yy < H and 0 <= xx < W:
                    solid[yy, xx] = True
    out = np.clip(img, 0, 255).astype(np.uint8)
    for x, y in plan['doors']:
        solid[y, x] = False
    return dict(picture=out, solid=solid, kind=kind, objs=objs)

def main_compose():
    EV.mkdir(parents=True, exist_ok=True)
    plans = dict(lobby=FP.lobby(), typical=FP.typical(), penthouse=FP.penthouse(), roof=FP.roof())
    for k, p in plans.items():
        r = compose(p, k)
        Image.fromarray(r['picture']).save(EV / f'built-{k}.png')
        np.savez_compressed(ASSETS / f'{k}.npz', picture=r['picture'], solid=r['solid'], kind=r['kind'])
        print(k, r['picture'].shape)

if __name__ == '__main__':
    if sys.argv[1] == 'assets':
        assets(Path(sys.argv[2]).resolve())
    else:
        main_compose()
