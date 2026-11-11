"""Celadon's per-cell element ledger, read from HGSS's own map data.

    python3 tools/gba/maps/celadon_elements/ledger.py PATH/TO/pokeheartgold

Each cell of the 60x50 cut gets the HGSS element it holds, from the flat top-down render
of the land chunks (the material under each pixel), the permissions (collision, behaviour)
and the building footprints:

    floor  grass (grass01gs, grass01_a, flowers, under trees), pave (tama_yuka, the
           hexagon paving), brick (tama_yuka2, the terraces the north row and the Gym stand
           on), kerb (tama_br on a terrace's edge), bridge (tama_br over the canal), water
           (pond_un, pond_line). tama_fuch is HGSS's lawn edge polygon: its cell takes
           whichever ground most of its pixels show.
    lab    T tree (HGSS's 2x2 tree block: crown row, trunk row), f fence post (tama_f),
           L jump ledge (allpeak), X building or prop, B other blocked ground, . open
    deco   flower01-03 beds and grass01_a tufts, at their own cells

Writes source/elements/ledger.json and ledger.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C                                  # noqa: E402

W, H, HW, HH, SRC = C.W, C.H, C.HW, C.HH, C.SRC
FLOOR = dict(grass01gs='grass', grass01_a='grass', flower01='grass', flower02='grass', flower03='grass',
             tree01_re='grass', tree01_un='grass', tree01gs='grass', tama_yuka='pave', tama_yuka2='brick',
             tama_br='kerb', tama_f='fence', pond_un='water', pond_line='water', allpeak_pgs='grass', allpeakgs='grass')
GRASS_RGB = [(115, 222, 173), (115, 214, 173), (99, 189, 156), (107, 206, 165)]
PAVE_RGB = [(198, 198, 173), (214, 214, 189), (189, 189, 165), (156, 165, 132)]
BRICK_RGB = [(140, 123, 115), (156, 148, 132), (99, 87, 81), (70, 61, 57), (78, 74, 66)]
CANAL = (25, 30)                    # the canal's fence columns; the water and bridge run between them

def topdown(phg):
    r = C.R()
    land, tex0, _, chunks, _ = C.load(str(phg))
    cv = r.Canvas(HW * 16, HH * 16)
    for c in chunks:
        ch = r.hgss_map.MapChunk.parse(land[c['land']])
        ox, oz = c['cx'] * 32, c['cz'] * 32
        r.draw_model(cv, r.mdlview.Model(ch.model), tex0, lambda x, y, z, ox=ox, oz=oz: (x + 16 + ox, y, z + 16 + oz), -1, None, flat=True)
    return cv.mat, list(r.MATERIAL_NAMES), cv.rgb.astype(np.uint8)

def trees(mat, names, rgb):
    """HGSS's trees, one per trunk (the brown core of tree01_un): (x0, y0) of each 2x2
    block, crown row y0, trunk row y0 + 1."""
    from scipy import ndimage
    un = names.index('tree01_un')
    trunk = (mat == un) & (np.abs(rgb.astype(int) - np.array([148, 115, 74])).sum(-1) < 8)
    lab, n = ndimage.label(trunk)
    out = set()
    for cy, cx in ndimage.center_of_mass(trunk, lab, range(1, n + 1)):
        out.add((int(round(cx / 16)) - 1, int(cy // 16) - 1))
    return sorted(out, key=lambda t: (t[1], t[0]))

def near(px, cols):
    return (np.abs(px[:, None, :].astype(int) - np.array(cols)[None]).sum(-1) <= 12).any(-1).sum()

def ledger(phg):
    mat, names, rgb = topdown(phg)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    nm = np.array(names + ['none'])
    m = np.where(mat >= 0, mat, len(names)).reshape(HH, 16, HW, 16).transpose(0, 2, 1, 3).reshape(HH, HW, 256)
    px = rgb.reshape(HH, 16, HW, 16, 3).transpose(0, 2, 1, 3, 4).reshape(HH, HW, 256, 3)
    blds = json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']
    owner = np.full((HH, HW), -1, int)
    for i, b in enumerate(blds):
        x0, z0, x1, z1 = b['footprint']
        owner[int(np.floor(z0)):int(np.ceil(z1)), int(np.floor(x0)):int(np.ceil(x1))] = i
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            u, cnt = np.unique(nm[m[y, x]], return_counts=True)
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            dom = str(u[np.argmax(cnt)])
            floor = FLOOR.get(dom)
            if dom == 'tama_fuch' or floor is None or floor == 'fence':
                score = dict(grass=near(px[y, x], GRASS_RGB), pave=near(px[y, x], PAVE_RGB), brick=near(px[y, x], BRICK_RGB))
                floor = max(score, key=score.get)
            t, k = int(types[y, x]), int(coll[y, x])
            water_col = [yy for yy in range(HH) if types[yy, x] == 0x10]
            if CANAL[0] < x < CANAL[1] and water_col and min(water_col) < y < max(water_col) and t != 0x10:
                floor = 'bridge'                              # the footbridge's deck, between the canal's two reaches
            blocked = bool(k & 0x80)
            deco = next((d for d in ('flower01', 'flower02', 'flower03') if frac.get(d, 0) >= 96), None)
            if deco is None and frac.get('grass01_a', 0) >= 24:
                deco = 'grass01_a'
            if t == 0x10:
                floor = 'water'
            if t == 0x06:
                lab = 'T'
            elif t == 0x3B:
                lab = 'L'
            elif blocked and frac.get('tama_f', 0) >= 24:
                lab = 'f'
            elif blocked and floor == 'water':
                lab = '~'
            elif blocked and owner[y, x] >= 0:
                lab = 'X'
            elif blocked:
                lab = 'B'
            else:
                lab = '.'
            row.append(dict(lab=lab, floor=floor, type=t, blocked=blocked, owner=int(owner[y, x]), material=dom, deco=deco))
        cells.append(row)
    for x0, y0 in trees(mat, names, rgb):
        for yy in (y0, y0 + 1):
            for xx in (x0, x0 + 1):
                if 0 <= xx < W and 0 <= yy < H:
                    cells[yy][xx].update(tree=[x0, y0], lab='T', floor='grass')
    return cells

def save(cells):
    out = SRC / 'elements'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'ledger.json').write_text(json.dumps(dict(
        note='Per-cell element ledger from HGSS land_data (header 55, zone T07), the 60x50 cut. lab: T tree (tree: its '
             '2x2 block), f fence post, L jump ledge, X building or prop, B blocked ground, ~ blocked water, . open. '
             'floor: grass, pave, brick, kerb, bridge, water. deco: flower bed or grass tuft.',
        cells=[[c['lab'] + c['floor'][0] for c in row] for row in cells], detail=cells)) + '\n')
    img = Image.new('RGB', (W * 12, H * 12), (20, 20, 24)); d = ImageDraw.Draw(img)
    fl = dict(grass=(110, 210, 160), pave=(214, 214, 189), brick=(140, 123, 115), kerb=(230, 230, 220), bridge=(170, 170, 170),
              water=(60, 180, 250))
    col = dict(T=(70, 110, 40), f=(120, 120, 120), L=(150, 100, 70), X=(90, 90, 110), B=(60, 60, 70))
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d.rectangle((x * 12, y * 12, x * 12 + 11, y * 12 + 11), fill=col.get(c['lab']) or fl[c['floor']])
            if c['deco']:
                d.text((x * 12 + 3, y * 12), c['deco'][-1], fill='black')
    img.save(out / 'ledger.png')

def main(phg):
    C.textures(phg)
    cells = ledger(phg)
    save(cells)
    labs = {}
    for row in cells:
        for c in row:
            labs[c['lab'] + c['floor']] = labs.get(c['lab'] + c['floor'], 0) + 1
    print(json.dumps(dict(sorted(labs.items()))))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
