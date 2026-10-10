"""Native 16px Johto modules. No screenshot crops in buildings or grass.

HGSS provides layout/reference; Cherrygrove provides the warm timber/coral
palette. Roof rows, wall courses, windows and blade clusters are pixel authored.
"""
from pathlib import Path
import numpy as np
from claude_cherrygrove.pixel import Canvas, Palette

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'gba/art/johto-native-refinement'
P=Palette(6,[(56,48,48),(96,64,56),(152,80,72),(184,104,88),
             (216,136,112),(240,168,136),(112,104,88),(152,144,120),
             (192,184,152),(224,216,184),(48,80,88),(80,136,152),
             (136,192,208),(240,240,216),(104,208,152)],
          ['ink','wood','roof_dark','roof','roof_light','ridge','stone_dark',
           'stone','wall','wall_light','glass_dark','glass','glass_light','white','lawn'])

def window(c,x,y,w=16,h=16):
    c.rect(x,y,w,h,'ink');c.rect(x+1,y+1,w-2,h-2,'wall_light')
    c.rect(x+3,y+3,w-6,h-6,'glass_dark')
    c.rect(x+4,y+4,w-8,h-8,'glass');c.hline(x+4,y+4,w-8,'glass_light')
    c.vline(x+w//2,y+3,h-6,'white');c.hline(x+3,y+h//2,w-6,'white')
    c.hline(x-1,y+h,w+2,'stone_dark');c.hline(x-1,y+h+1,w+2,'wall_light')

def roof(c,x,y,w,h):
    # A symmetric hipped roof; every roof course uses the same tile rhythm.
    for yy in range(h):
        inset=max(0,(h-yy)//4)
        c.hline(x+inset,y+yy,w-2*inset,'roof')
        c.put(x+inset,y+yy,'ink');c.put(x+w-inset-1,y+yy,'ink')
        if yy%8==1:c.hline(x+inset+1,y+yy,w-2*inset-2,'roof_light')
        if yy%8==7:c.hline(x+inset+1,y+yy,w-2*inset-2,'roof_dark')
        for xx in range(8+(4 if yy//8%2 else 0),w-4,8):
            if inset<xx<w-inset-1 and yy%8 not in (0,1):c.put(x+xx,y+yy,'roof_dark')
    c.hline(x+h//4,y,w-h//2,'ridge')
    c.rect(x,y+h,w,2,'ink');c.rect(x+1,y+h+2,w-2,2,'wood')
    c.hline(x+2,y+h+4,w-4,'ridge')

def building(w=80,h=80,door=1,lab=False):
    c=Canvas(w,h,P);walltop=48
    c.rect(7,walltop,w-14,h-walltop-2,'ink')
    c.rect(9,walltop,w-18,h-walltop-5,'wall')
    c.rect(9,walltop,w-18,3,'wood')
    for yy in range(walltop+5,h-7,8):
        c.hline(9,yy,w-18,'stone');c.hline(9,yy+1,w-18,'wall_light')
    c.vline(9,walltop+3,h-walltop-9,'wall_light');c.vline(w-10,walltop+3,h-walltop-9,'stone_dark')
    c.hline(8,h-6,w-16,'stone_dark');c.hline(8,h-5,w-16,'stone')
    roof(c,3,8,w-6,35)
    dx=door*16
    for wx in range(16,w-20,32):
        if abs(wx-dx)>=20:window(c,wx,55)
    c.rect(dx,54,16,h-54,'ink');c.rect(dx+2,56,12,h-58,'wood')
    c.rect(dx+3,57,10,8,'glass_dark');c.rect(dx+4,58,8,6,'glass')
    c.hline(dx+4,58,8,'glass_light');c.put(dx+11,70,'white')
    c.rect(dx,h-4,16,4,'stone');c.hline(dx,h-4,16,'wall_light')
    if lab:
        # Raised central monitor, glazed entrance and academic emblem.
        roof(c,80,0,48,31);c.rect(85,36,38,13,'wall_light')
        for wx in (86,98,110):window(c,wx,36,10,10)
        c.rect(dx-2,51,20,3,'white');c.rect(dx+2,55,12,18,'glass_dark')
        c.rect(dx+3,56,10,15,'glass');c.vline(dx+7,56,15,'white')
        c.hline(dx+3,57,10,'glass_light');c.hline(dx-3,73,22,'stone_dark')
        c.rect(53,56,18,15,'stone_dark');c.rect(54,57,16,13,'wall_light')
        c.ellipse(62,63,4,4,'glass_dark');c.hline(58,63,9,'white');c.put(62,63,'roof')
    return c.to_rgba()

def pad(a,w,h,x=0,y=0):
    out=np.zeros((h,w,4),np.uint8);out[y:y+a.shape[0],x:x+a.shape[1]]=a;return out

def architecture(base=None):
    house=building();gable=building(80,80,2)
    return dict(institute=building(208,80,6,True),annex=gable,
                west_house=house,east_house=house,staff_a=house,staff_b=gable,
                gate29=pad(gable,144,144,32,64),
                mr_pokemon=pad(gable,112,96,16,16),
                berry_house=pad(house,96,80),gate31=pad(building(80,80,4),96,96,0,16))

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

def props():
    c=Canvas(32,64,P);c.rect(14,22,4,38,'stone_dark');c.rect(15,23,2,36,'wall_light')
    c.rect(9,59,14,4,'stone');c.hline(9,59,14,'wall_light')
    for dx,dy in [(-1,-1),(1,1)]:
        for i in range(3,15):
            c.rect(16+dx*i-1,18+dy*i-1,3,3,'ink');c.rect(16+dx*i,18+dy*i,2,2,'white')
    for dx,dy in [(-1,1),(1,-1)]:
        for i in range(3,15):
            c.rect(16+dx*i-1,18+dy*i-1,3,3,'ink');c.rect(16+dx*i,18+dy*i,2,2,'white')
    c.ellipse(16,18,3,3,'wood');c.ellipse(16,18,2,2,'white')
    m=Canvas(16,32,P);m.rect(7,14,2,15,'wood');m.rect(3,7,10,10,'ink');m.rect(4,8,8,8,'roof');m.hline(5,10,6,'ridge');m.hline(5,13,6,'ink')
    return dict(wind=c.to_rgba(),labwind=c.to_rgba(),red_mailbox=m.to_rgba(),blue_mailbox=m.to_rgba(),lab_fence=np.zeros((16,16,4),np.uint8))

def cliff_modules():
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
    cliff.px[~keep]=0
    boundary=keep&~np.roll(keep,1,1);cliff.px[boundary]=p.index['deep']
    rim=keep&~np.roll(keep,1,0);cliff.px[rim]=p.index['top']
    return dict(cliff=cliff.to_rgba(),plateau=top.to_rgba(),face=face.to_rgba(),west_face=face.to_rgba()[:,:16],
                cliff_corner=face.to_rgba(),cave_mouth=cave.to_rgba(),bridge=bridge.to_rgba())

def forest(p,tree):
    """Full canopies on safe 32px footprints; small edge foliage fills odd strips.

    Canopies extend four pixels beyond trunks, just as Cherrygrove's accepted
    tree does. No clipping inside a tree and no random lawn holes in the forest.
    """
    h,w=p.shape;items=[];covered=np.zeros(p.shape,bool)
    for y in range(-2,h,2):
        for x in range(-2,w,2):
            lo,hi=max(y,0),min(y+2,h);lx,hx=max(x,0),min(x+2,w)
            if hi>lo and hx>lx and (p[lo:hi,lx:hx]=='T').all():
                items.append((x*16-4,y*16-16,tree));covered[lo:hi,lx:hx]=True
    # Edge foliage has the same bank as the accepted tree, with compact native
    # silhouettes. This covers single-cell forest strips without cutting trees.
    rgb=np.asarray(tree.pal.gba());valid=np.flatnonzero(rgb.sum(1)>0)
    green=valid[(rgb[valid,1]>rgb[valid,0])&(rgb[valid,0]>60)]
    order=green[np.argsort(rgb[green].sum(1))]
    shrub=Canvas(16,16,tree.pal)
    if len(order):
        yy,xx=np.indices((16,16));mask=((xx-7.5)/8)**2+((yy-8)/9)**2<=1
        shrub.px[mask]=order[len(order)//2]
        edge=mask&~(np.roll(mask,1,0)&np.roll(mask,-1,0)&np.roll(mask,1,1)&np.roll(mask,-1,1))
        shrub.px[edge]=order[0]
        for x,y in [(3,5),(8,3),(12,6),(6,9)]:shrub.px[y:y+2,x:x+2]=order[-1]
    for y,x in zip(*np.nonzero((p=='T')&~covered)):items.append((x*16,y*16,shrub))
    return sorted(items,key=lambda v:(v[1]+v[2].h,v[0]))

def native_tree(pal):
    """Complete rounded crown, branch groups, trunk and local ground shadow.
    Uses Cherrygrove's exact existing tree palette so connections remain valid.
    """
    c=Canvas(40,48,pal);rgb=np.asarray(pal.gba());valid=np.flatnonzero(rgb.sum(1)>0)
    leaves=valid[(rgb[valid,1]>rgb[valid,0])&(rgb[valid,0]>60)]
    leaves=leaves[np.argsort(rgb[leaves].sum(1))]
    dark,base,light,tip=[int(leaves[min(i,len(leaves)-1)]) for i in (0,len(leaves)//3,2*len(leaves)//3,len(leaves)-1)]
    def ellipse(cx,cy,rx,ry,index):
        yy,xx=np.indices(c.px.shape);c.px[((xx-cx)/rx)**2+((yy-cy)/ry)**2<=1]=index
    brown=int(valid[np.argmin(rgb[valid].sum(1))])
    ellipse(20,44,11,3,dark);c.px[31:45,17:23]=brown;c.px[32:44,18:21]=base
    ellipse(19.5,23,19,18,dark)
    # Broad overlapping branches create a continuous woodland canopy. Small
    # stepped highlight clusters read as leaves rather than blurred spheres.
    for cx,cy,rx,ry in [(9,26,9,10),(30,26,9,10),(20,32,11,8),
                        (7,17,7,8),(32,17,7,8),(20,10,11,9),(19,22,14,12)]:
        ellipse(cx,cy,rx,ry,base)
        ellipse(cx-1,cy-2,max(rx-2,2),max(ry-3,2),light)
    for x,y in [(15,5),(22,7),(9,13),(17,12),(26,12),(31,18),
                (7,22),(13,23),(21,20),(25,26),(14,31),(21,33)]:
        c.px[y:y+2,x:x+4]=tip;c.px[y+2,x+1:x+3]=light
        c.px[y+4,x+2:x+5]=base
    for x,y in [(6,29),(12,18),(26,17),(32,29),(17,27),(23,36)]:
        c.px[y:y+2,x:x+4]=dark;c.px[y-1,x+1:x+3]=base
    return c
