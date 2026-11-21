"""Johto standard tall grass (owner-approved 2026-11-21).

The tile is a hand-drawn 16x16 (G3) in four greens. It is laid over each tall grass cell as a
full tile with no background, on top of the terrain that would be there without grass, so
path edges, their shadows and lining are never painted over. See restyle() and AGENTS.md
"Never draw over what is already there".
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[3] / 'tools/hoennconv')]
import map_gate as G
import numpy as np
from collections import Counter
from PIL import Image
from layers import render_layer

P = {'.': (32, 112, 80), 'd': (40, 136, 80), 'm': (72, 180, 116), 'L': (104, 208, 152)}
TILE = """
..L.....L....L..
.Lm..L..mL..Lm..
.mm.Lm.LmmL.mm.L
Lmd.mm.mmdm.md.m
mmd.md.mddm.mdLm
mmdLmdLmd.mLmddm
mdLmmd.mdLmmd.dm
mdmmdd.mmmmdd.dm
ddmmd.Lmdmmdd.dd
dmmddLmddmddd.dd
dmmd.mmd.dddd.Ld
ddmd.mdd.dd.dLmd
dddd.dd...d.dmdd
.d.d..d.....d.d.
................
................
"""

def parse(g):
    rows = g.strip('\n').split('\n')
    assert len(rows) == 16 and all(len(r) == 16 for r in rows)
    return np.array([[P[c] for c in r] for r in rows], np.uint8)

G3 = TILE
DARK=np.array(P['.']); 
def disk(r): return [(dy,dx) for dy in range(-r,r+1) for dx in range(-r,r+1) if dy*dy+dx*dx<=r*r+r*0.5]
def morph(m,r,op):
    out=m.copy() if op=='erode' else m.copy()
    for dy,dx in disk(r):
        sh=np.roll(np.roll(m,dy,0),dx,1)
        out = (out & sh) if op=='erode' else (out | sh)
    return out
def restyle(engine, name, tile=None):
    """Overlay the standard grass on every tall grass cell (owner 2026-11-21).

    1. Put the terrain back: the old grass clump lives in each grass metatile's top layer,
       and the bottom layer holds what is under it (plain ground, or a dirt path edge with
       its shadow and grey lining). Where the clump drew, the bottom layer is shown again.
    2. Lay the full 16x16 grass tile on top with no background: every blade pixel is drawn.
       The tile's dark shade fills in only where the old clump was or where the patch carries
       on into the neighbouring cell, and only over plain ground, so path edges, their shadow
       and lining show between the blades. No half tiles: every tall grass cell gets the
       whole tile.
    3. Anything in the cell's top layer that is not old grass (tree canopies, props) is drawn
       back on top.
    """
    e = G.Engine(Path(engine)); m = e.by_name[name]; lay = e.layouts[m['layout']]
    raw = e.grid(lay); g = raw & 1023; ts = e.tileset(lay)
    tg = np.vectorize(lambda v: G.behavior(ts, int(v)) == 2)(g)
    img = np.asarray(G.native_image(e, m).convert('RGB')).astype(int); out = img.copy()
    Hh, Ww = g.shape
    T = parse(G3 if tile is None else tile).astype(int)
    blade = ~(T == DARK).all(-1)
    near = lambda px, ref: np.abs(px[:, :, None, :] - ref[None, None]).sum(-1).min(-1) <= 12
    # old clump colours: the top layer of the commonest tall grass metatiles
    olds = [v for v, _ in Counter(int(v) for v in g[tg]).most_common(4)]
    OLD = np.unique(np.concatenate([t[mk] for t, mk in (render_layer(ts, v, 1, bg=False) for v in olds)]), axis=0)
    col = (raw >> 10) & 3
    def greenish(v):
        a = np.asarray(ts.render(int(v)).convert('RGB')).reshape(-1, 3).mean(0)
        return a[1] > a[0] * 1.15 and a[1] > a[2]
    gm = next(v for v, _ in Counter(int(v) for v, c, t in zip(g.flat, col.flat, tg.flat) if c == 0 and not t).most_common() if greenish(v))
    gcols = np.unique(np.asarray(ts.render(gm).convert('RGB')).reshape(-1, 3), axis=0).astype(int)
    for y in range(Hh):
        for x in range(Ww):
            if not tg[y, x]: continue
            sl = (slice(y * 16, y * 16 + 16), slice(x * 16, x * 16 + 16))
            v = int(g[y, x])
            bot, _ = render_layer(ts, v, 0)
            topl, tm = render_layer(ts, v, 1, bg=False)
            clump = tm & near(topl, OLD)
            base = np.where(clump[..., None], bot, img[sl])
            plain = near(base, gcols)
            fill = clump.copy()
            if y > 0 and tg[y - 1, x]: fill[:4] = True
            if y < Hh - 1 and tg[y + 1, x]: fill[12:] = True
            if x > 0 and tg[y, x - 1]: fill[:, :3] = True
            if x < Ww - 1 and tg[y, x + 1]: fill[:, 13:] = True
            cell = base.copy()
            cell[~blade & fill & plain] = DARK
            cell[blade] = T[blade]
            foreign = tm & ~clump
            cell = np.where(foreign[..., None], topl, cell)
            out[sl] = cell
    return img.astype(np.uint8), out.astype(np.uint8), tg

if __name__ == '__main__':
    out = HERE.parents[3] / 'gba/art/johto-common/standards/tall_grass_tile.png'
    Image.fromarray(parse(TILE)).save(out)
    print('wrote', out)
