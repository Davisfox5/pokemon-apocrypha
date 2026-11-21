"""Johto standard tall grass (owner-approved 2026-11-21).

The tile is a hand-drawn 16x16 (G3) in four greens. Patches get rounded convex corners
(radius 7 px opening) and a wavy 1-2 px dark edge on the sides and bottom; the top row
shows blade tips over the ground. Carved-out pixels always show the map's plain grass ground,
never path, sand or other neighbouring colours (owner, 2026-11-21).

restyle(engine, map) returns (old, new, tall_grass_cells). Only pixels inside tall grass
cells change; anything in a cell's top layer that is not old grass (tree canopies, props)
is kept. See AGENTS.md "Never draw over what is already there".
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
def restyle(engine,name,tile=None,R=7):
    e=G.Engine(Path(engine)); m=e.by_name[name]; lay=e.layouts[m['layout']]; raw=e.grid(lay); g=raw&1023; ts=e.tileset(lay)
    tg=np.vectorize(lambda v:G.behavior(ts,int(v))==2)(g)
    img=np.asarray(G.native_image(e,m).convert('RGB')).astype(int); out=img.copy()
    Hh,Ww=g.shape
    tile=parse(G3).astype(int) if tile is None else tile
    # old grass colours (to tell grass from overlapping canopies in the top layer)
    olds=Counter(int(v) for v in g[tg]).most_common(6)
    OLD=np.unique(np.concatenate([np.asarray(ts.render(v).convert('RGB')).reshape(-1,3) for v,_ in olds]),axis=0).astype(int)
    # ground texture: most common walkable non-grass metatile
    col=(raw>>10)&3
    def greenish(v):
        a = np.asarray(ts.render(int(v)).convert('RGB')).reshape(-1, 3).mean(0)
        return a[1] > a[0] * 1.15 and a[1] > a[2]
    gm=next(v for v,_ in Counter(int(v) for v,c,t in zip(g.flat,col.flat,tg.flat) if c==0 and not t).most_common() if greenish(v))
    ground=np.asarray(ts.render(gm).convert('RGB')).astype(int)
    M=np.kron(tg,np.ones((16,16),bool))
    pad=8; Mp=np.pad(M,pad)
    Mr=morph(morph(Mp,R,'erode'),R,'dilate')[pad:-pad,pad:-pad]   # opening: rounds convex corners
    H,W=M.shape; yy,xx=np.mgrid[0:H,0:W]
    # wavy side/bottom edges: erode by 1 or 2 px following a tuft rhythm
    wave=((xx//4+yy//4)%2).astype(bool)
    inner1=morph(np.pad(Mr,pad),1,'erode')[pad:-pad,pad:-pad]
    inner2=morph(np.pad(Mr,pad),2,'erode')[pad:-pad,pad:-pad]
    keep=np.where(wave,inner1,Mr)
    above=np.zeros_like(M); above[1:]=M[:-1]
    # distance (px) from the top of the patch, per column
    top=np.zeros((H,W),int); run=np.zeros(W,int)
    for y in range(H):
        run=np.where(M[y],run+1,0); top[y]=run
    tex=np.tile(tile,(H//16,W//16,1))
    outline=keep & ~inner1
    for y in range(Hh):
        for x in range(Ww):
            if not tg[y,x]: continue
            sl=(slice(y*16,y*16+16),slice(x*16,x*16+16))
            mid=int(g[y,x]); topl,tm=render_layer(ts,mid,1,bg=False)
            # carved pixels show plain grass ground only (owner 2026-11-21: never path or sand colours)
            gnd=ground
            ground_=gnd
            cell=np.where(keep[sl][...,None],tex[sl],ground_)
            # top edge: only blade tips over ground in the first rows of the patch
            t=top[sl]; tips=(t<=4)&((tex[sl]==DARK).all(-1))
            cell[tips]=ground_[tips]
            ol=outline[sl]&~(t<=4)&~(tex[sl]==np.array(P['L'])).all(-1)
            cell[ol]=DARK
            # keep anything in the original top layer that isn't old grass (tree canopies etc.)
            foreign=tm & (np.abs(topl[:,:,None,:]-OLD[None,None]).sum(-1).min(-1)>12)
            cell=np.where(foreign[...,None],topl,cell)
            out[sl]=cell
    return img.astype(np.uint8),out.astype(np.uint8),tg


if __name__ == '__main__':
    out = HERE.parents[3] / 'gba/art/johto-common/standards/tall_grass_tile.png'
    Image.fromarray(parse(TILE)).save(out)
    print('wrote', out)
