"""The underwater path under the Route 45 side's lake (owner direction, November 2026: Dive down to an
underwater path and a new section of the cave).

Laid out in the Route 45 side's own coordinates, since Gen 3 dives and emerges at the same cell:
under the lake's Dive spot (decade.DIVE, 37-39 x 31-33) a pool of open water, then a trench south,
west and north to a water door at (28, 33) that leads to the grotto (grotto.py). Everything else is
the seabed's rock plateau.

Drawn with Emerald's own underwater pieces (gTileset_Underwater, as Underwater_Route105 uses them),
by rule, not by pattern matching (a learned 5x5 model left stray slope pieces):

    plateau 531        floor 681 (Emerald's no-surfacing floor)     seaweed 641
    open to the west 654, east 653, north 547, south 644
    open north+west 637, north+east 638, south+west 645, south+east 646
    open only diagonally: south-west 519, south-east 518, north-east 547, north-west 546
    the water door: Underwater_Route128's six pieces round its door (613-615 over 621-623)

The art is then recoloured from Emerald's violet to the cave's water (each colour takes the hue of
HGSS's driver texture, its lightness dimmed alike for the dark under a cave lake) and graded like
the cave (decade.grade). It packs with the other Dark Cave maps (pack.py); emerging is allowed only
under the Dive spot (MB_NORMAL there, MB_NO_SURFACING and MB_SEAWEED_NO_SURFACING elsewhere, as
Emerald's underwater routes do), and the door is MB_WATER_DOOR.
"""
from __future__ import annotations
import colorsys, json
import numpy as np
from PIL import Image

W = H = 64
TRENCH = [(36, 30, 40, 34), (37, 35, 39, 43), (29, 41, 39, 43), (27, 35, 30, 43), (27, 34, 29, 34)]   # x0, y0, x1, y1
DOOR = (28, 33)
EMERGE = [(x, y) for y in range(31, 34) for x in range(37, 40)]           # under decade.DIVE
WEED = [(38, 40), (39, 41), (31, 42), (32, 43), (28, 38), (29, 39), (40, 31)]
DOOR_STAMP = [[613, 614, 615], [621, 622, 623]]
PLATEAU, FLOOR, SEAWEED = 531, 681, 641

def layout():
    op = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in TRENCH:
        op[y0:y1 + 1, x0:x1 + 1] = True
    o = lambda x, y: bool(op[y, x]) if 0 <= x < W and 0 <= y < H else False
    g = np.full((H, W), PLATEAU, int)
    for y in range(H):
        for x in range(W):
            if op[y, x]:
                g[y, x] = FLOOR
                continue
            n, s, w, e = o(x, y - 1), o(x, y + 1), o(x - 1, y), o(x + 1, y)
            nw, ne, sw, se = o(x - 1, y - 1), o(x + 1, y - 1), o(x - 1, y + 1), o(x + 1, y + 1)
            assert not (n and s) and not (w and e), ('rock one cell thick', x, y)
            g[y, x] = (637 if n and w else 638 if n and e else 645 if s and w else 646 if s and e else
                       654 if w else 653 if e else 547 if n else 644 if s else
                       519 if sw else 518 if se else 547 if ne else 546 if nw else PLATEAU)
    for x, y in WEED:
        assert op[y, x] and (x, y) not in EMERGE, (x, y)
        g[y, x] = SEAWEED
    dx, dy = DOOR
    for j, row in enumerate(DOOR_STAMP):
        for i, m in enumerate(row):
            g[dy - 1 + j, dx - 1 + i] = m
    assert op[dy + 1, dx] and not op[dy, dx]
    return g, op

LIGHT = 0.62                       # under a cave lake: Emerald's open-sea light, dimmed

def recolour(img, water):
    """Emerald's violet to the cave water's hue, every colour dimmed alike (LIGHT), so the seabed's
    own shading is kept; then the cave's grade."""
    import decade as D
    base = np.mean(np.array(water, float), 0) / 255
    hue, _, sat = colorsys.rgb_to_hls(*base)
    out = img.copy()
    for c in {tuple(int(v) for v in p) for p in img.reshape(-1, 3)}:
        h, l, s = colorsys.rgb_to_hls(*(np.array(c) / 255))
        r = colorsys.hls_to_rgb(hue, l * LIGHT, min(1.0, s * 0.85))
        out[np.all(img == c, -1)] = [int(round(v * 255)) for v in r]
    return D.grade(out)

def build(engine, src, ev, water):
    """Writes source/assemble/underwater{.png,-class.npy,-ledger.json} and its evidence image."""
    import decade as D
    g, op = layout()
    img = np.zeros((H * 16, W * 16, 3), np.uint8)
    cache = {}
    for y in range(H):
        for x in range(W):
            m = int(g[y, x])
            if m not in cache:
                b, t = D.metatile_layers(engine, 'general', 'underwater', m)
                cell = b[..., :3].copy(); a = t[..., 3] > 0
                cell[a] = t[a, :3]
                cache[m] = cell
            img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16] = cache[m]
    img = recolour(img, water)
    cls = np.where(np.kron(op, np.ones((16, 16), bool)), 7, 2).astype(np.int8)        # water, wall
    cells = []
    for y in range(H):
        for x in range(W):
            kind = ('door' if (x, y) == DOOR else 'emerge' if (x, y) in EMERGE else 'seaweed' if (x, y) in WEED
                    else 'floor' if op[y, x] else 'rock')
            cells.append(dict(x=x, y=y, kind=kind, metatile=int(g[y, x])))
    (src / 'assemble').mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(src / 'assemble/underwater.png')
    np.save(src / 'assemble/underwater-class.npy', cls)
    (src / 'assemble/underwater-ledger.json').write_text(json.dumps(dict(
        source='Emerald gTileset_Underwater pieces by rule (underwater.py), recoloured to the cave water',
        trench=TRENCH, door=list(DOOR), emerge=EMERGE, cells=cells)) + '\n')
    (ev / 'assemble').mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(ev / 'assemble/underwater.png')
    return dict(open=int(op.sum()), emerge=len(EMERGE), seaweed=len(WEED), door=list(DOOR),
                emerald_metatiles=sorted({int(v) for v in g.ravel()}))
