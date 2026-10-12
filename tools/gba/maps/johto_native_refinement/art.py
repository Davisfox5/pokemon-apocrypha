"""Johto extension using the approved Cherrygrove architecture and foliage."""
from pathlib import Path
import numpy as np
from claude_cherrygrove.pixel import Canvas, Palette

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'gba/art/johto-native-refinement'
FOREST_AUDITS=[]
def pad(a,w,h,x=0,y=0):
    out=np.zeros((h,w,4),np.uint8);out[y:y+a.shape[0],x:x+a.shape[1]]=a;return out

def architecture(base):
    """Reuse the approved indexed Cherrygrove shells at native pixel size."""
    house=base['house'].to_rgba();gable=base['gable'].to_rgba()
    from PIL import Image
    # Original institutional building; palette conversion occurs in its own bank.
    im=Image.open(OUT/'generated/institute.png').convert('RGBA')
    im.putalpha(im.getchannel('A').point(lambda v:255 if v>=192 else 0))
    im=im.crop(im.getbbox()).resize((176,96),Image.Resampling.NEAREST)
    lab=np.zeros((112,176,4),np.uint8);lab[16:]=np.asarray(im)
    return dict(institute=lab,annex=gable,
                west_house=house,east_house=house,staff_a=house,staff_b=gable,
                gate29=pad(gable,144,144,32,64),
                mr_pokemon=pad(gable,112,112,16,20),
                berry_house=pad(house,96,80),gate31=pad(gable,128,96,32,16))

def tall_slices():
    # Six colors matched to the decoded HGSS egrass ladder, but blades authored
    # at native scale rather than copying DS material noise into the GBA sheet.
    pal=Palette(6,[(32,112,80),(32,120,88),(40,136,80),(56,152,88),(64,168,112),(80,192,120)],
                ['deep','shade','base','leaf','light','tip'])
    c=Canvas(16,16,pal);c.rect(0,0,16,16,'base')
    for x,y in [(3,8),(12,6),(8,15)]:
        c.hline(x-2,y,5,'deep');c.hline(x-1,y-1,3,'shade')
        for dx,dy in [(-2,-3),(-1,-2),(-1,-4),(0,-2),(0,-3),(0,-5),(1,-3),(2,-4)]:
            c.put(x+dx,y+dy,'leaf')
        c.put(x-1,y-5,'light');c.put(x,y-6,'tip');c.put(x+2,y-5,'light')
        c.put(x+1,y-1,'base');c.put(x-2,y+1,'shade')
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
    from PIL import Image,ImageDraw
    p=Palette(9,[(56,64,64),(96,112,104),(152,168,152),(208,216,192),(240,240,224)],
              ['dark','shadow','steel','light','white'])
    c=Canvas(32,64,p)
    c.rect(14,18,4,42,'shadow');c.rect(15,19,2,40,'light')
    c.rect(10,59,13,3,'shadow');c.hline(10,59,13,'steel')
    im=Image.fromarray(c.px.astype('uint8'));d=ImageDraw.Draw(im)
    for poly in [[(15,17),(15,1),(18,1),(18,12)],
                 [(14,18),(2,23),(3,26),(13,22)],
                 [(17,20),(27,31),(30,29),(21,20)]]:
        d.polygon(poly,fill=p.index['white'],outline=p.index['steel'])
    c.px=np.asarray(im).copy();c.ellipse(16,19,3,3,'shadow');c.ellipse(16,18,2,2,'light')
    return dict(wind=c.to_rgba(),labwind=c.to_rgba(),
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
    from PIL import Image,ImageDraw
    cave=np.asarray(Image.open(ROOT/'gba/art/hgss-connections/references/route31-hgss.png').convert('RGBA').crop((824,176,872,224))).copy()
    cm=Image.new('L',(48,48));ImageDraw.Draw(cm).polygon(
        [(0,0),(47,0),(47,43),(39,47),(33,45),(30,40),
         (17,40),(13,46),(5,47),(0,44)],fill=255)
    cave[...,3]=np.asarray(cm)
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
                cliff_corner=rock,cave_mouth=cave,bridge=bridge.to_rgba())

def source_tree():
    """Literal indexed Cherrygrove source, never regenerated from the screenshot."""
    from PIL import Image
    from tiles import palette
    source=ROOT/'gba/art/claude-cherrygrove/source'
    colors=palette(source/'palettes/bank03-tree.pal')[1:]
    pal=Palette(12,colors,[f'c{i}' for i in range(15)])
    im=np.asarray(Image.open(source/'tree.idx.png'))
    c=Canvas(im.shape[1],im.shape[0],pal);c.px=im.copy();c.pool='secondary'
    assert np.array_equal(c.to_rgba(),np.asarray(Image.open(source/'tree.png').convert('RGBA')))
    return c


def ledges(base):
    """Complete rocky lip and face, using the town's cliff material."""
    rock=base['cliff'].to_rgba()
    # Compress only the height of the rock face for a low jump ledge. The
    # upper turf rim and bottom shadow give it depth without fence-like teeth.
    from PIL import Image
    src=np.asarray(Image.fromarray(rock[16:40]).resize((32,10),Image.Resampling.NEAREST)).copy()
    whole=np.zeros((16,32,4),np.uint8);whole[4:14]=src
    whole[2:4]=[80,144,96,255];whole[3]=[128,168,104,255]
    whole[14]=[80,64,48,255];whole[15]=[96,152,104,255]
    a=whole[:,:16].copy();b=whole[:,16:].copy()
    left=a.copy();right=b.copy()
    left[:3,:3,3]=0;left[12:,:2,3]=0
    right[:3,-3:,3]=0;right[12:,-2:,3]=0
    return dict(ledge_l=left,ledge_a=a,ledge_b=b,ledge_r=right,
                wall_top=np.rot90(left),wall=np.rot90(a),
                corner_se=b,corner_sw=a,corner_ne=np.rot90(b))

def cliff_pieces(base):
    """Continuous cliff modules, free of donor grass and tree fragments."""
    rock=base['cliff'].to_rgba()
    top=rock[8:24];foot=rock[24:40]
    side=foot[:,:16].copy()
    return dict(top0=top[:,:16],top1=foot[:,:16],
                east0=side,east1=side[:,::-1],
                corner00=top[:,:16],corner01=top[:,16:],
                corner10=foot[:,:16],corner11=foot[:,16:],
                cross=foot[:,:16],west=side)

def forest(p,tree):
    """Full crowns, fixed 48px rows, no tightly interleaved filler instances."""
    h,w=p.shape;items=[];covered=np.zeros(p.shape,bool)
    def fits(x,y):
        # Each instance fits completely on the map and inside forest cells.
        if x<0 or y<0 or x+2>w or y+3>h:return [],[],False
        rows=list(range(max(0,y),min(h,y+3)))
        cols=list(range(max(0,x),min(w,x+2)))
        return rows,cols,bool(rows and cols and (p[np.ix_(rows,cols)]=='T').all())
    # Each complete tree occupies exactly 2x3 cells. Instances never overlap
    # each other or occupy a path/building cell.
    for y in range(-3,h,3):
        for x in range(-2,w,2):
            rows,cols,ok=fits(x,y)
            if ok:
                items.append((x*16,y*16,tree));covered[np.ix_(rows,cols)]=True
    # Shift entire edge trees into remaining full 3x3 pockets, with no overlap
    # against another crown. Never fill a narrow strip with half a tree.
    for y,x in zip(*np.nonzero((p=='T')&~covered)):
        if covered[y,x]:continue
        for yy,xx in ((y,x),(y-1,x),(y-2,x)):
            if yy<0 or xx<0:continue
            rows,cols,ok=fits(xx,yy)
            if ok and not covered[np.ix_(rows,cols)].any():
                items.append((xx*16,yy*16,tree));covered[np.ix_(rows,cols)]=True;break
    occupied=np.zeros((h*16,w*16),bool)
    allowed=np.repeat(np.repeat(p=='T',16,axis=0),16,axis=1)
    for x,y,c in items:
        m=c.px>0;region=occupied[y:y+c.h,x:x+c.w]
        assert not (region&m).any(),'overlapping tree silhouettes'
        assert allowed[y:y+c.h,x:x+c.w][m].all(),'tree spills onto a path or building'
        region|=m
    FOREST_AUDITS.append(dict(width=w,height=h,instances=len(items),overlap_pixels=0,non_forest_pixels=0,clipped_instances=0))
    return sorted(items,key=lambda v:(v[1],v[0]))
