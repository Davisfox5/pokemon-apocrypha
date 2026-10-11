"""Native Emerald blade/ledge silhouettes, adapted to the accepted Johto colors.

Source: unmodified primary/general in the pinned pokeemerald-expansion base.
Nintendo / Game Freak / Creatures artwork; no scaled render or generated bitmap.
"""
import numpy as np
from claude_cherrygrove.pixel import Canvas, Palette
from tiles import Tileset


def emerald(source):
    t = Tileset(source)
    # Four blade values, a ground-contact shadow, and six warm stone values.
    colors = [(40,112,72),(56,160,88),(88,184,104),(120,208,136),
              (72,152,112),(104,72,56),(128,88,64),(160,112,80),
              (192,144,96),(216,176,120)]
    p = Palette(11, colors, [f'c{i}' for i in range(len(colors))])
    rgb = np.asarray(t.render(0x00d))
    grass = Canvas(16,16,p)
    dark = np.all(rgb == (57,82,0), axis=2)
    blade = np.all(rgb == (24,164,106), axis=2)
    grass.px[dark] = 1
    grass.px[blade] = 2
    # Light the existing native blades: broad faces, then their exposed tips.
    # Transparency replaces Emerald's lawn pixels, including lawn speckles.
    left = np.pad(blade,((0,0),(1,0)))[:,:16]
    above = np.pad(blade|dark,((1,0),(0,0)))[:16]
    grass.px[blade & ~left] = 3
    grass.px[blade & ~above] = 4
    grass.pool = 'secondary'
    out = {f'tall{n}{s}{w}{e}': grass for n in (0,1) for s in (0,1)
           for w in (0,1) for e in (0,1)}
    # Decode only Emerald's foreground layer: the unchanged local lawn/path
    # remains below it. Rounded ends and corner joins are real donor pixels.
    mids = dict(ledge_l=0xd5,ledge_a=0x87,ledge_b=0x87,ledge_r=0xd6,
                wall=0x85,wall_top=0x85,corner_se=0x8d,
                corner_sw=0x8e,corner_ne=0x86)
    remap = {(131,131,139):5,(98,65,82):6,(131,90,90):7,
             (156,115,115):8,(189,148,139):9,(222,180,164):10}
    for name,mid in mids.items():
        c = Canvas(16,16,p); c.pool = 'secondary'
        for q,e in enumerate(t.blocks[0][mid][4:]):
            tid=e&1023; bank=e>>12
            ar=np.array(t.tiles[tid>=512][tid%512]).reshape(8,8)
            if e&1024: ar=ar[:,::-1]
            if e&2048: ar=ar[::-1]
            for y,x in zip(*np.nonzero(ar)):
                color=t.pals[bank>=6][bank][int(ar[y,x])]
                assert color in remap,(name,color)
                c.px[q//2*8+y,q%2*8+x]=remap[color]
        out[name]=c
    return out,p


def clean_rock_edge(rgba, protect=None):
    """Remove exterior donor lawn/tree residue, preserving enclosed rock shade.

    Only edge-connected non-rock colors are cleared. This avoids both the
    square crop boundary and holes punched through the rock's own texture.
    """
    from collections import deque
    a=rgba.copy();rgb=a[...,:3].astype(int)
    candidate=(rgb[...,0]-rgb[...,1]<16)
    if protect is not None: candidate[protect]=False
    candidate |= a[...,3]==0
    h,w=candidate.shape;seen=np.zeros((h,w),bool);todo=deque()
    for y,x in zip(*np.nonzero(candidate)):
        if y in (0,h-1) or x in (0,w-1) or a[y,x,3]==0:
            todo.append((y,x));seen[y,x]=True
    while todo:
        y,x=todo.popleft()
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            yy,xx=y+dy,x+dx
            if 0<=yy<h and 0<=xx<w and candidate[yy,xx] and not seen[yy,xx]:
                seen[yy,xx]=True;todo.append((yy,xx))
    a[seen,3]=0
    return a
