"""Johto standard pond borders (owner-approved 2026-11-21).

Water texture stays the map's own. The border is Emerald's general-tileset pond set:
b0 b1 b2 (top-left, top, top-right), b8 ba (left, right), c0 c2 (inner corners), a1
(interior), with Emerald's light water replaced by the map's water and Emerald's shadow
band replaced by that water at 72% brightness. The bottom rim is the top two rows of
Emerald metatile 0x2, drawn only over ground-coloured pixels of the land cell below.

Only the bottom layer changes. Each cell's top layer (tree canopies hanging over the
water, props) is drawn back on top, and bottom-layer pixels that are not old water or
shore are kept. See AGENTS.md "Never draw over what is already there".

restyle(engine, map) returns (old, new, water_cells). EMERALD_ENGINE must point at a
checkout with vanilla data/tilesets/primary/general.
"""
import sys, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parents[3] / 'tools/hoennconv')]
import map_gate as G, numpy as np
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw
from layers import render_layer
b=Path(os.environ.get('EMERALD_ENGINE','game'))/'data/tilesets'
EM=G._load_tileset(b/'primary/general',b/'secondary/petalburg')
def em(i): return np.asarray(EM.render(i).convert('RGB')).astype(int)
H=np.array((115,189,246)); Gs=np.array((74,115,172))
PIECES={k:em(v) for k,v in dict(a1=0xa1,b0=0xb0,b1=0xb1,b2=0xb2,b8=0xb8,ba=0xba,c0=0xc0,c2=0xc2).items()}
LIP=em(0x2)[:2]
WATER={'MB_POND_WATER','MB_DEEP_WATER','MB_OCEAN_WATER','MB_SHALLOW_WATER'}
def mbnames(p):
    import re
    names,n={},0
    for line in (Path(p)/'include/constants/metatile_behaviors.h').read_text().split('enum',1)[1].split('}',1)[0].splitlines():
        m=re.match(r'\s*(MB_\w+)\s*(?:=\s*(\w+))?\s*,',line)
        if m:
            if m.group(2): n=int(m.group(2),0)
            names[n]=m.group(1); n+=1
    return names
def compose(piece,water,shade=0.72):
    out=piece.copy()
    mh=(piece==H).all(-1); mg=(piece==Gs).all(-1)
    out[mh]=water[mh]; out[mg]=(water[mg]*shade).astype(int)
    return out
def ponds(w, max_cells=400):
    """Water components that count as ponds: not touching the map edge and at most max_cells.
    The sea, rivers that run off the map and big lakes are left alone; decide those case by case."""
    H, W = w.shape; lab = np.zeros(w.shape, int); keep = np.zeros(w.shape, bool); n = 0
    for y0, x0 in zip(*np.where(w)):
        if lab[y0, x0]: continue
        n += 1; st = [(y0, x0)]; lab[y0, x0] = n; cells = []
        while st:
            y, x = st.pop(); cells.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and w[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n; st.append((yy, xx))
        c = np.array(cells)
        edge = c[:, 0].min() == 0 or c[:, 1].min() == 0 or c[:, 0].max() == H - 1 or c[:, 1].max() == W - 1
        if not edge and len(c) <= max_cells:
            keep[c[:, 0], c[:, 1]] = True
    return keep

def restyle(engine,mapname,box_cells=None,rim_map=None,max_cells=400):
    e=G.Engine(Path(engine)); m=e.by_name[mapname]; lay=e.layouts[m['layout']]; g=e.grid(lay)&1023; ts=e.tileset(lay); mb=mbnames(engine)
    w=np.vectorize(lambda v:mb.get(G.behavior(ts,int(v)) or 0,'') in WATER)(g)
    w=ponds(w,max_cells)
    img=np.asarray(G.native_image(e,m).convert('RGB')).astype(int); out=img.copy()
    Hh,Ww=g.shape
    # interior water texture: most common metatile among water cells fully surrounded
    def wt_at(y0,x0):
        # interior water metatile nearest this cell
        best=None
        for y in range(1,Hh-1):
            for x in range(1,Ww-1):
                if w[y-1:y+2,x-1:x+2].all():
                    d=abs(y-y0)+abs(x-x0)
                    if best is None or d<best[0]: best=(d,int(g[y,x]))
        return np.asarray(ts.render(best[1]).convert('RGB')).astype(int)
    cache={}
    # old shore colours: colours in edge water cells' bottom layers that are not in the water tile
    edge=[int(g[y,x]) for y in range(Hh) for x in range(Ww) if w[y,x] and not w[max(0,y-1):y+2,max(0,x-1):x+2].all()]
    SHORE=np.unique(np.concatenate([render_layer(ts,v,0)[0].reshape(-1,3) for v in set(edge)]),axis=0) if edge else np.zeros((0,3),int)
    col=(e.grid(lay)>>10)&3
    plain=[int(g[y,x]) for y in range(Hh) for x in range(Ww) if not w[y,x] and col[y,x]==0]
    cnt=Counter(map(tuple,np.concatenate([render_layer(ts,v,0)[0].reshape(-1,3) for v,_ in Counter(plain).most_common(4)])))
    GROUND=np.array([c for c,_ in cnt.most_common(3)])
    W_=lambda y,x: (not (0<=y<Hh and 0<=x<Ww)) or w[y,x]
    # ground colours: most common colours of plain walkable non-water cells
    def is_water_px(px,ref):  # pixel belongs to old water/shore: close to any colour in the water tile or shore palette
        return (np.abs(ref[None,None,:,:]-px[:,:,None,:]).sum(-1).min(-1)<24)
    for y in range(Hh):
        for x in range(Ww):
            mid=int(g[y,x])
            if w[y,x]:
                n,s,wst,est=W_(y-1,x),W_(y+1,x),W_(y,x-1),W_(y,x+1)
                if not n: k='b0' if not wst else 'b2' if not est else 'b1'
                elif not wst: k='b8'
                elif not est: k='ba'
                elif not W_(y-1,x-1): k='c0'
                elif not W_(y-1,x+1): k='c2'
                else: k='a1'
                wt=wt_at(y,x)
                bot,_=render_layer(ts,mid,0); top,tm=render_layer(ts,mid,1,bg=False)
                new=compose(PIECES[k],wt)
                # keep bottom-layer pixels that are not old water/shore (e.g. trunks baked into the bottom layer)
                ref=np.unique(np.concatenate([wt.reshape(-1,3),SHORE]),axis=0)
                keep=~is_water_px(bot,ref)
                cell=np.where(keep[...,None],bot,new)
                cell=np.where(tm[...,None],top,cell)
                out[y*16:y*16+16,x*16:x*16+16]=cell
            elif y>0 and w[y-1,x]:
                bot,_=render_layer(ts,mid,0); top,tm=render_layer(ts,mid,1,bg=False)
                cell=bot.copy()
                grd=is_water_px(cell[:2],GROUND)
                cell[:2]=np.where(grd[...,None],LIP,cell[:2])
                cell=np.where(tm[...,None],top,cell)
                out[y*16:y*16+16,x*16:x*16+16]=cell
    return img.astype(np.uint8),out.astype(np.uint8),w
