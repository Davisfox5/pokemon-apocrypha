"""Johto extension using the approved Cherrygrove architecture and foliage."""
from pathlib import Path
import numpy as np
from claude_cherrygrove.pixel import Canvas, Palette

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'gba/art/johto-native-refinement'
def pad(a,w,h,x=0,y=0):
    out=np.zeros((h,w,4),np.uint8);out[y:y+a.shape[0],x:x+a.shape[1]]=a;return out

def architecture(base):
    """Reuse the approved indexed Cherrygrove shells at native pixel size."""
    house=base['house'].to_rgba();gable=base['gable'].to_rgba()
    lab=np.zeros((80,208,4),np.uint8)
    wing=house.copy()
    # Convert the wing entrance to the existing glazed wall module; the central
    # gable supplies the institute's only entrance. Roofs retain source pixels.
    wing[56:80,16:32]=house[56:80,48:64]
    for x,a in [(0,wing),(128,wing),(64,gable)]:
        target=lab[:,x:x+a.shape[1]];m=a[...,3]>0;target[m]=a[m]
    return dict(institute=lab,annex=gable,
                west_house=house,east_house=house,staff_a=house,staff_b=gable,
                gate29=pad(gable,144,144,32,64),
                mr_pokemon=pad(gable,112,96,16,16),
                berry_house=pad(house,96,80),gate31=pad(gable,128,96,32,16))

def tall_slices():
    # Six colors matched to the decoded HGSS egrass ladder, but blades authored
    # at native scale rather than copying DS material noise into the GBA sheet.
    pal=Palette(6,[(32,112,80),(32,120,88),(40,136,80),(56,152,88),(64,168,112),(80,192,120)],
                ['deep','shade','base','leaf','light','tip'])
    c=Canvas(16,16,pal);c.rect(0,0,16,16,'base')
    for x,y in [(2,7),(10,7),(6,15),(14,15)]:
        c.hline(x-2,y,5,'deep');c.hline(x-1,y-1,3,'shade')
        for dx,dy in [(-2,-2),(-1,-3),(0,-4),(0,-5),(1,-2),(2,-3)]:c.put(x+dx,y+dy,'leaf')
        c.put(x-1,y-4,'light');c.put(x,y-6,'tip');c.put(x+2,y-4,'light')
    return c.to_rgba()

def tall_cell(src,n,s,w,e):
    a=src.copy()
    # The edge follows blade tips. Adjacent encounter cells tile uninterrupted.
    if not n:
        for x in range(16):a[:[3,2,1,0,3,2,1,2][x%8],x,3]=0
    if not s:a[15,:,3]=0
    if not w:a[:,0,3]=0
    if not e:a[:,15,3]=0
    return a

def orange_flowers():
    pal=Palette(12,[(32,112,80),(64,168,112),(184,104,88),(240,168,136),(240,240,216)],
                ['stem','leaf','shadow','petal','center'])
    c=Canvas(16,16,pal)
    for x,y in [(4,6),(11,11)]:
        c.vline(x,y+1,5,'stem');c.hline(x-2,y+4,3,'leaf')
        for dx,dy in [(-1,-2),(1,-1),(0,2),(-2,0)]:c.rect(x+dx,y+dy,2,2,'petal')
        c.put(x,y+1,'shadow');c.put(x,y,'center')
    return c.to_rgba()

def props(base):
    from johto_polish.art import new_bark
    source=new_bark()
    return dict(wind=source['wind'],labwind=source['labwind'],
                red_mailbox=base['mailbox'].to_rgba(),
                blue_mailbox=base['mailbox'].to_rgba(),
                lab_fence=np.zeros((16,16,4),np.uint8))

def cliff_modules(base):
    p=Palette(9,[(72,64,48),(112,88,64),(152,112,72),(184,144,96),(208,176,120),(224,200,152),(104,208,152)],
              ['ink','deep','shade','rock','light','top','lawn'])
    def piece(w,h):return Canvas(w,h,p)
    top=piece(32,32);top.rect(0,0,32,32,'light')
    for y in range(0,32,8):
        for x in range(0,32,8):top.hline(x+2,y+2,3,'top');top.put(x+6,y+6,'rock')
    face=piece(32,32);face.rect(0,0,32,32,'rock');face.rect(0,0,32,3,'top');face.hline(0,3,32,'deep')
    for y in (9,18,27):
        offset=4 if y==18 else 0
        for x in range(-offset,32,12):
            face.rect(x,y-3,10,3,'shade');face.hline(x+1,y-4,8,'light')
            face.hline(x,y,10,'deep');face.vline(x+10,y-3,4,'deep')
            face.hline(x+2,y+2,5,'light')
    face.hline(0,31,32,'ink')
    cave=piece(48,48);cave.rect(0,0,48,48,'rock')
    cave.ellipse(24,27,20,22,'shade');cave.ellipse(24,30,14,20,'deep');cave.ellipse(24,32,11,19,'ink')
    cave.rect(13,28,23,20,'ink');cave.rect(16,40,16,8,'deep');cave.hline(16,47,16,'shade')
    for x,y in [(6,18),(10,9),(20,5),(32,7),(39,17)]:cave.rect(x,y,5,3,'light')
    bridge=piece(48,48);bridge.rect(0,0,48,48,'deep')
    for y in range(1,48,8):bridge.rect(0,y,48,6,'rock');bridge.hline(0,y,48,'top')
    bridge.rect(0,0,3,48,'ink');bridge.rect(45,0,3,48,'ink')
    # Measured HGSS landform outline, filled using native rock modules.
    # The silhouette is geometry only; no pixels from the DS render enter it.
    from PIL import Image,ImageDraw
    cliff=piece(288,224)
    mask=Image.new('L',(288,224));ImageDraw.Draw(mask).polygon(
        [(168,0),(287,0),(287,191),(161,191),(161,214),
         (39,214),(39,97),(24,97),(24,46),(32,25),(103,25),(103,13),(168,13)],fill=255)
    keep=np.asarray(mask)>0
    for y in range(0,224,32):
        for x in range(0,288,32):cliff.px[y:y+32,x:x+32]=top.px
    # Continuous exposed faces at the two foreground terraces.
    for y,x0,x1 in [(176,40,160),(160,160,288)]:
        for x in range(x0,x1,8):cliff.px[y:y+32,x:x+8]=face.px[:,:8]
    # Preserve the landform outline but use Cherrygrove's exact exposed rock
    # and grassy cliff-top pixels. These are texture modules, not a new palette.
    from claude_cherrygrove import ground
    soil,_=ground.paint(np.full((2,2),ground.GRASS,np.int8))
    rock=base['cliff'].to_rgba()[24:56]
    result=cliff.to_rgba()
    for y in range(0,224,32):
        for x in range(0,288,32):result[y:y+32,x:x+32]=soil
    for y,x0,x1 in [(176,40,160),(160,160,288)]:
        for x in range(x0,x1,8):result[y:y+32,x:x+8]=rock[:,:8]
    result[~keep]=0
    cliff.px[~keep]=0
    boundary=keep&~np.roll(keep,1,1);cliff.px[boundary]=p.index['deep']
    rim=keep&~np.roll(keep,1,0);cliff.px[rim]=p.index['top']
    return dict(cliff=result,plateau=soil,face=rock,west_face=rock[:,:16],
                cliff_corner=rock,cave_mouth=cave.to_rgba(),bridge=bridge.to_rgba())

def forest(p,tree):
    """Place the exact Cherrygrove crowns on its established 32x24 lattice."""
    h,w=p.shape;items=[];covered=np.zeros(p.shape,bool)
    def fits(x,yp):
        rows=list(range(max(0,yp//16),min(h,(yp+31)//16+1)))
        cols=[v for v in (x,x+1) if 0<=v<w]
        return rows,cols,bool(rows and cols and (p[np.ix_(rows,cols)]=='T').all())
    def add(x,yp,rows,cols):
        items.append((x*16,yp,tree));covered[np.ix_(rows,cols)]=True
    for yp in range(-48,h*16,24):
        for x in range(-2,w,2):
            rows,cols,ok=fits(x,yp)
            if ok:add(x,yp,rows,cols)
    for y,x in zip(*np.nonzero((p=='T')&~covered)):
        if covered[y,x]:continue
        placed=False
        for x0 in (x-1,x):
            for yp in range(-48,h*16,24):
                if not yp//16<=y<=(yp+31)//16:continue
                rows,cols,ok=fits(x0,yp)
                if ok:add(x0,yp,rows,cols);placed=True;break
            if placed:break
    return sorted(items,key=lambda v:(v[1],v[0]))
