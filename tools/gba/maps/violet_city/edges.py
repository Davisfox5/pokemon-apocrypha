"""Violet-only native pixel edge finishing; no resampling or geometry changes."""
import numpy as np
from claude_cherrygrove.pixel import Canvas


def soften_building(c):
    """Ease high-contrast outer ink into the facade's existing palette.

    Keep lower contact shadows, small spires, windows and internal outlines.
    Clip one pixel from supported convex corners instead of blurring the asset.
    """
    old=c.px.copy(); opaque=old>0
    pad=np.pad(opaque,1)
    neighbors=[pad[:-2,1:-1],pad[2:,1:-1],pad[1:-1,:-2],pad[1:-1,2:]]
    edge=opaque & ~np.logical_and.reduce(neighbors)
    colors=np.array(c.pal.gba(),int)
    for y,x in zip(*np.where(edge)):
        inward=[]
        for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]:
            xx,yy=x+dx,y+dy
            if 0<=xx<c.w and 0<=yy<c.h and old[yy,xx] and not edge[yy,xx]:inward.append(colors[old[yy,xx]])
        if not inward or y==c.h-1:continue
        # South-facing contact shadow remains grounded against the lawn.
        if y+1<c.h and not opaque[y+1,x]:continue
        color=colors[old[y,x]];inner=np.mean(inward,axis=0)
        if inner.mean()>color.mean()+18:
            target=color*.45+inner*.55
            c.px[y,x]=1+((colors[1:]-target)**2).sum(1).argmin()
    for y,x in zip(*np.where(edge)):
        runs=[]
        for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]:
            runs.append(all(0<=x+dx*k<c.w and 0<=y+dy*k<c.h and opaque[y+dy*k,x+dx*k] for k in range(1,4)))
        n,s,w,e=[bool(a[y,x]) for a in neighbors]
        if n+s+w+e==2 and (runs[0] or runs[1]) and (runs[2] or runs[3]):c.px[y,x]=0


def rounded_distance(missing, radius, ripple=False):
    y,x=np.indices((16,16));edges=[y,15-y,x,15-x]
    d=np.full((16,16),99.,float)
    wave=np.array([0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0])
    for i,absent in enumerate(missing):
        if absent:d=np.minimum(d,edges[i]-(wave[x] if i<2 else wave[y]) if ripple else edges[i])
    for a,b in [(0,2),(0,3),(1,2),(1,3)]:
        if missing[a] and missing[b]:
            d=np.minimum(d,radius-np.hypot(np.maximum(radius-edges[a],0),np.maximum(radius-edges[b],0)))
    return d


def shoreline(interior,bits):
    """Repeated six-pixel grass/bank/shallow-water transition, 12px corners."""
    c=Canvas(16,16,interior.pal);c.px=interior.px.copy()
    missing=[not(bits & 1<<i) for i in range(4)]
    if not any(missing):return c
    d=rounded_distance(missing,12,True)
    pal=np.array(c.pal.gba(),int)
    def near(rgb):return 1+((pal[1:]-rgb)**2).sum(1).argmin()
    c.px[d<1]=0
    for low,high,rgb in [(1,2,(104,200,152)),(2,3,(88,176,136)),(3,4,(160,144,104)),(4,5,(72,200,224)),(5,6,(64,184,224))]:
        c.px[(d>=low)&(d<high)]=near(rgb)
    return c
