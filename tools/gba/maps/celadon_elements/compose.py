"""Compose Celadon City: HGSS's ground, then everything that stands, in two Gen 3 layers.

    python3 tools/gba/maps/celadon_elements/compose.py

Inputs: ledger.py's ledger, the cached HGSS textures, buildings.py's sprites, the
owner-locked C06 Center. The ground (ground.py) is the bottom layer. Everything that stands
(trees, fence posts, buildings, signs, the fountain, the market stalls, lamps) is drawn in
painter's order by the row its foot stands on, by its own opaque pixels only, so whatever
stands behind it shows round it. Where two palette families meet in one 8x8 tile, one takes
the top layer and the bottom layer there is the picture with that family left out (Olivine's
split), so no pixel of either is lost.

Story changes on HGSS's plan (DESIGN.md Chapter 6, evidence/plan.png):
    1  market stalls round the fountain lawn under rainbow parasols; lamps where HGSS has
       its two lawn lights; the city sign a cell east, clear of the north-east stall
    2  the Dept Store is the market's services building (its sign)
    3  the Gym is the Botanical Gardens (buildings.py: glass roof, leaf crest); its two
       flanking houses' lots are flower beds on a lawn
    4  the Condominiums are the Pokemon Hotel (its sign)
    5  the restaurant is the cafe
    6  the Game Corner and its prize corner stay
    7  the bike lane (ground.py)
    8  the canal and its footbridge stay as HGSS has them

Writes source/elements/compose.npz, evidence/terrain.png and evidence/compare.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

import common as C
import ground as G
import props as P
import buildings as Bd

W, H, SRC, EV = C.W, C.H, C.SRC, C.EV
SHARED = SRC / 'shared-art'
CENTER_ORIGIN = (45, 9)                 # C06, 5x5, door tile (2, 4) on HGSS's Center door (47, 13)
CENTER_DOOR = (2, 4)

# name, sprite, HGSS model x (cells), base row (the row the sprite's bottom stands on).
PLACES = [
    ('house_0', 'house', 12.0, 13), ('services', 'services', 17.5, 13), ('house_1', 'house', 23.5, 13),
    ('tower', 'tower', 27.5, 13), ('hotel', 'hotel', 33.0, 13), ('house_2', 'house', 39.0, 13),
    ('house_3', 'house', 43.0, 13),
    ('flat', 'flat', 28.0, 25), ('gamecorner', 'gamecorner', 34.5, 25), ('prize', 'prize', 40.0, 25),
    ('house_4', 'house', 46.0, 25), ('house_5', 'house', 50.0, 25),
    ('house_6', 'house', 38.0, 37), ('cafe', 'cafe', 42.0, 37), ('house_7', 'house', 46.0, 37),
    ('house_8', 'house', 50.0, 37),
    ('gardens', 'gardens', 17.5, 42),
    ('fountain', 'fountain', 17.5, 26),
    ('stall_0', 'stall', 14.5, 23), ('stall_1', 'stall', 20.5, 23),
    ('stall_2', 'stall', 14.5, 28), ('stall_3', 'stall', 20.5, 28),
    ('lamp_0', 'lamp', 13.5, 25), ('lamp_1', 'lamp', 21.5, 25),
    ('citysign', 'citysign', 22.5, 21), ('board_0', 'board', 19.5, 14), ('board_1', 'board', 36.5, 13),
    ('board_2', 'board', 35.5, 28), ('board_3', 'board', 45.5, 28), ('board_4', 'board', 20.5, 44),
    ('board_5', 'board', 44.5, 38),
]
# HGSS's two houses beside the Gym give their lots to the Gardens' flower beds (change 3).
BED_LOTS = [(10, 38, 14, 43), (21, 38, 25, 43)]         # x0, y0, x1, y1 (exclusive)
BEDS = ('flower01', 'flower02', 'flower03')

def gardens_beds(cells):
    """The flanking lots as lawn planted with HGSS's flower beds, a row of each kind, a
    grass margin round them."""
    for x0, y0, x1, y1 in BED_LOTS:
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = cells[y][x]
                bed = BEDS[(y - y0) % 3] if y0 < y < y1 - 1 or x0 < x < x1 - 1 else None
                c.update(floor='grass', lab='.', deco=bed if x0 < x < x1 - 1 and y < y1 - 1 else None, owner=-1, story='gardens bed')
    return cells

def objects(cells, t):
    tree, post = P.tree(t), P.post(t)
    items = []
    seen = sorted({tuple(c['tree']) for row in cells for c in row if 'tree' in c}, key=lambda b: (b[1], b[0]))
    for x0, y0 in seen:
        items.append(dict(name=f'tree_{x0}_{y0}', fam='tree', img=tree, X=x0 * 16, Y=(y0 + 2) * 16 - tree.shape[0]))
    for y, row in enumerate(cells):
        for x, c in enumerate(row):
            if c['lab'] == 'f':
                items.append(dict(name=f'post_{x}_{y}', fam='ground', img=post, X=x * 16 + 4, Y=y * 16))
    origin = Bd.origins()
    for name, sprite, mx, row in PLACES:
        img = Bd.load(sprite)
        X = int(round((mx * 16 - origin[sprite][0]) / 8)) * 8
        Y = (row + 1) * 16 - img.shape[0]
        items.append(dict(name=name, fam=FAMILY.get(sprite, sprite), img=img, X=X, Y=Y, sprite=sprite))
    c06 = np.array(Image.open(SHARED / 'pokemon-center.png').convert('RGBA'))
    items.append(dict(name='pokemon_center', fam='center', img=c06, X=CENTER_ORIGIN[0] * 16, Y=CENTER_ORIGIN[1] * 16))
    return items

# Palette family per sprite: buildings.py's palette groups.
FAMILY = {n: g[0][0] for g in Bd.GROUPS for n in g[0]}
FLAT = ('post_',)

def stack(bottom, items, leave_out=None):
    """The picture: the ground, then everything standing in painter's order (by the row its
    foot stands on, north first; in one row, trees and posts before buildings), each by its
    own opaque pixels. Returns the picture and, per pixel, the family and owner shown."""
    want = bottom.copy()
    fam = np.full(bottom.shape[:2], '', '<U12')
    own = np.full(bottom.shape[:2], '', '<U16')
    foot = lambda it: it['Y'] + int(np.nonzero(it['img'][..., 3].any(1))[0].max())
    order = lambda it: (foot(it) // 16, it['fam'] not in ('tree', 'ground'), foot(it), it['X'])
    for it in sorted((it for it in items if it['fam'] != leave_out), key=order):
        img, X, Y = it['img'], it['X'], it['Y']
        y0, x0 = max(Y, 0), max(X, 0)
        y1, x1 = min(Y + img.shape[0], H * 16), min(X + img.shape[1], W * 16)
        if y1 <= y0 or x1 <= x0:
            continue
        part = img[y0 - Y:y1 - Y, x0 - X:x1 - X]
        m = part[..., 3] > 0
        sl = np.s_[y0:y1, x0:x1]
        want[sl][m] = part[..., :3][m]
        fam[sl][m] = it['fam']
        own[sl][m] = it['name']
    return want, fam, own

# Where two families show in one 8x8 tile the first here takes the top layer; the bottom
# layer is the picture with it left out.
TOP_FIRST = ('center', 'services', 'tower', 'gamecorner', 'house', 'cafe', 'gardens', 'stall', 'tree', 'ground')

def split(bottom, want, fam, behind):
    out = bottom.copy()
    top = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    shared = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    mixed = {}
    for ty in range(H * 2):
        for tx in range(W * 2):
            ts = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            f = fam[ts]
            kinds = set(np.unique(f).tolist()) - {''}
            if not kinds:
                continue
            first = min(kinds, key=TOP_FIRST.index)
            m = f == first
            dst = shared if first == 'center' else top
            dst[ts][m] = np.concatenate([want[ts][m], np.full((int(m.sum()), 1), 255, np.uint8)], 1)
            if ((f != '') & ~m).any():
                pic, _ = behind(first)
                out[ts] = pic[ts]
                mixed[(tx, ty)] = [first] + sorted(kinds - {first})
    return out, top, shared, mixed

def compose():
    cells = json.loads((SRC / 'elements/ledger.json').read_text())['detail']
    cells = gardens_beds(cells)
    t = C.textures()
    bottom = G.ground(cells, t)
    items = objects(cells, t)
    want, fam, owner = stack(bottom, items)
    cache = {}
    def behind(f):
        if f not in cache:
            cache[f] = stack(bottom, items, leave_out=f)[:2]
        return cache[f]
    bottom2, top, shared, mixed = split(bottom, want, fam, behind)
    return cells, bottom2, top, shared, owner, fam, mixed, want

def preview(bottom, top, shared):
    out = bottom.copy()
    for layer in (top, shared):
        a = layer[..., 3] > 0
        out[a] = layer[..., :3][a]
    return out

def main():
    cells, bottom, top, shared, owner, fam, mixed, want = compose()
    (SRC / 'elements').mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SRC / 'elements/compose.npz', bottom=bottom, top=top, shared=shared, owner=owner, family=fam)
    (SRC / 'elements/cells.json').write_text(json.dumps(cells) + '\n')
    v = preview(bottom, top, shared)
    assert (v == want).all(), 'the two layers do not rebuild the picture'
    EV.mkdir(parents=True, exist_ok=True)
    Image.fromarray(v).save(EV / 'terrain.png')
    ref = np.array(Image.open(SRC / 'hgss/hgss-render.png').convert('RGB'))[:H * 16, :W * 16]
    sheet = Image.new('RGB', (W * 16 * 2 + 12, H * 16 + 24), (28, 32, 38)); d = ImageDraw.Draw(sheet)
    for i, (img, txt) in enumerate(((ref, 'HGSS Celadon (pokeheartgold T07)'), (v, 'Gen 3 elements'))):
        sheet.paste(Image.fromarray(img), (i * (W * 16 + 12), 24)); d.text((i * (W * 16 + 12) + 4, 6), txt, fill='white')
    sheet.save(EV / 'compare.png')
    pairs = {}
    for k in mixed.values():
        pairs['/'.join(k)] = pairs.get('/'.join(k), 0) + 1
    print('composed;', len(mixed), 'tiles with art on both layers:', dict(sorted(pairs.items(), key=lambda kv: -kv[1])[:12]))

if __name__ == '__main__':
    main()
