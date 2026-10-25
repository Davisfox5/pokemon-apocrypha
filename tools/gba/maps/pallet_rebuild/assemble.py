"""Fresh HGSS asset conversions against the FRLG receiving-material reference.

Run only for this explicitly authorized rebuild. It writes new editable art, never
the engine maps. Rejected assembled images, palettes and tiles are not inputs.
"""
from pathlib import Path
import hashlib, json, shutil, sys
import numpy as np
from PIL import Image, ImageDraw
from native import numbered

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/gba/maps/route29_catalog'))
import hgss_render as R
sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from claude_cherrygrove import hgss as CG
ART=ROOT/'gba/art/pallet-town-rebuild'; S=ART/'source'; EV=ART/'evidence'
AS=S/'assets'; AS.mkdir(parents=True,exist_ok=True)
RAW=Path(sys.argv[2]); PHG=Path(sys.argv[1])
maps=R.narc.load(PHG/'files/a/0/4/4');field=R.Tex0(maps[18]);room=R.Tex0(maps[43])
assets=[]; placements=[]; semantics={}; current_map='ApocPalletTown'

def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def reduce(im):
    a=np.array(im.convert('RGBA')); mask=a[...,3]>0
    if not mask.any():return im
    pixels=Image.fromarray(a[...,:3][mask].reshape(-1,1,3))
    palette=pixels.quantize(15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    rgb=np.array(Image.fromarray(a[...,:3]).quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB'))&248
    return Image.fromarray(np.dstack([rgb,np.where(mask,255,0).astype(np.uint8)]))
def texture(bank,name):
    e=next(e for e in bank.textures if e.name==name)
    p=next((p.name for p in bank.palettes if p.name in (name+'_pl',name)),bank.pal_for(e).name)
    if name=='sea_on':p='sea_f02_pl'
    return Image.fromarray(R.decode(bank,e,p),'RGBA')
def model(ids,where=''):
    a=np.array(Image.open(RAW/where/'hgss-foreground.png').convert('RGBA'))
    owners=np.load(RAW/where/'hgss-foreground-owner.npz')['owner']
    a[...,3]=np.where(np.isin(owners,ids),255,0)
    im=Image.fromarray(a);return im.crop(im.getbbox())
def fit(im,size,name,knots=None,xknots=None):
    save(im,AS/(name+'-original.png'))
    # Piecewise geometry preserves a full 32px facade instead of crushing the
    # high HGSS roof and facade together. No resampling between material planes.
    if knots:
        xknots=xknots or [(0,0),(im.width,size[0])]
        out=Image.new('RGBA',size)
        for (ya,y0),(yb,y1) in zip(knots,knots[1:]):
            for (xa,x0),(xb,x1) in zip(xknots,xknots[1:]):
                out.paste(im.crop((xa,ya,xb,yb)).resize((x1-x0,y1-y0),Image.Resampling.NEAREST),(x0,y0))
    else:out=im.resize(size,Image.Resampling.NEAREST)
    out=reduce(out);save(out,AS/(name+'.png'))
    assets.append(dict(name=name,source_size=im.size,native_size=size,y_planes=knots,x_planes=xknots,
                       colors='15 opaque colors, no dithering, RGB5; transparency excluded',sha256=hashlib.sha256((AS/(name+'.png')).read_bytes()).hexdigest()))
    return out
def place(f,im,x,y,name):
    f.alpha_composite(im,(x,y));placements.append(dict(map=current_map,asset=name,x=x,y=y,width=im.width,height=im.height))
    mask=np.array(im.convert('RGBA'))[...,3]>0
    for cy in range(y//16,(y+im.height+15)//16):
        for cx in range(x//16,(x+im.width+15)//16):
            x0,y0=max(0,cx*16-x),max(0,cy*16-y);x1,y1=min(im.width,(cx+1)*16-x),min(im.height,(cy+1)*16-y)
            if mask[y0:y1,x0:x1].any():semantics.setdefault(current_map,{}).setdefault(f'{cx},{cy}',[]).append(name)
def repeat(im,size):
    out=Image.new('RGBA',size)
    for y in range(0,size[1],im.height):
        for x in range(0,size[0],im.width):out.paste(im,(x,y))
    return out

# Keep every chosen original model and archive identity, not only final cutouts.
for archive,ids,label in [('files/a/0/4/0',[29,30,31,310,311,313,314],'field'),
                         ('files/fielddata/build_model/bm_room.narc',[1,4,17,18,19,20,21,24,27,29,30,31,53,54,66,67,70,91,94,95,114,210],'room')]:
    bank=R.narc.load(PHG/archive)
    for i in ids:(AS/f'{label}-{i}.nsbmd').write_bytes(bank[i])

house=fit(model([3,4]),(80,96),'pallet-house',[(0,0),(70,32),(122,64),(155,96)],[(0,0),(20,16),(40,32),(92,80)])
lab=fit(model([5,6]),(112,80),'pallet-lab',[(0,0),(66,40),(117,80)],[(0,0),(44,48),(64,64),(108,112)])
# Signs retain a complete face and post; the texture is not a chopped rail.
mail=fit(model([0]),(16,32),'mailbox')
sign=fit(model([2]),(16,24),'town-sign')
labsign=fit(model([7]),(16,32),'lab-sign')

tree=Image.open(ROOT/'gba/art/route31-catalog/source/local-art/cherrygrove-tree-with-shadow.png').convert('RGBA')
save(tree,AS/'shared-tree.png')
lawn=Image.fromarray(CG.grass_texture()).convert('RGBA'); save(lawn,AS/'shared-lawn.png')
ground=repeat(lawn,(384,368)); fg=Image.new('RGBA',ground.size)
ref=np.array(Image.open(S/'ApocPalletTown/frlg.png').convert('RGB'))
ga=np.array(ground)
# Receiving materials are explicit original palette masks. There is no colour
# classification deciding whether an unknown square is lawn, rock or a building.
light=np.isin(np.zeros(ref.shape[:2],np.uint8),[1])
for c in [(189,238,213),(238,255,255)]:light|=(ref==c).all(-1)
rim1=(ref==(156,230,197)).all(-1);rim2=(ref==(139,213,189)).all(-1)
core=ga[16:336,:,:3].astype(np.int16)
# A distinct light LAWN family retains the FRLG clearing's outline. It is not sand.
delta=np.array([56,24,24]);core[light]=np.minimum(248,core[light]+delta)
core[rim1]=np.minimum(248,core[rim1]+delta*2//3)
core[rim2]=np.minimum(248,core[rim2]+delta//3)
ga[16:336,:,:3]=core.astype(np.uint8)
# Extend the northern light-lawn socket through the single canopy-apron row.
upper=ga[:16,:,:3].astype(np.int16)
upper[light[:16]]=np.minimum(248,upper[light[:16]]+delta)
upper[rim1[:16]]=np.minimum(248,upper[rim1[:16]]+delta*2//3)
upper[rim2[:16]]=np.minimum(248,upper[rim2[:16]]+delta//3)
ga[:16,:,:3]=upper.astype(np.uint8)
ground=Image.fromarray(ga)

# Whole, uncut silhouettes, distinct 2x2 root beds, north-to-south layering.
# The 3 added rows contain the otherwise clipped crown/roots only.
roots=[(x,y) for y in range(1,23,2) for x in (0,22)]
roots += [(x,1) for x in range(2,22,2) if x!=12]
roots += [(x,21) for x in (2,4,18,20)]
occupied=set()
for x,y in roots:
    cells={(x+dx,y+dy) for dx in range(2) for dy in range(2)}
    assert not cells&occupied;occupied|=cells
for x,y in sorted(roots,key=lambda p:(p[1],p[0])):place(fg,tree,x*16,(y-1)*16,'shared-tree')
for im,x,y,name in [(house,80,48,'red-house'),(house,224,48,'oak-home'),(lab,208,160,'laboratory'),
                     (mail,64,112,'red-mailbox'),(mail,208,112,'oak-mailbox'),
                     (sign,144,184,'town-sign'),(sign,80,232,'red-memorial'),(labsign,256,256,'lab-sign')]:place(fg,im,x,y,name)

# Render the complete HGSS fence texture's first rail row. The rejected draft
# took its middle half, which removed the post heads and introduced a second rail.
fence=reduce(texture(field,'fence_a').crop((0,0,32,16)));save(fence,AS/'picket-fence.png')
for y,x0,x1,skip in [(12,5,9,9),(17,13,18,16)]:
    for x in range(x0,x1+1):
        if x!=skip:place(fg,fence.crop(((x%2)*16,0,(x%2+1)*16,16)),x*16,y*16,'picket-fence')
flower=texture(field,'flower01');a=np.array(flower)
plain=np.unique(np.array(texture(field,'grass01gs'))[...,:3].reshape(-1,3),axis=0)
remove=(a[...,:3,None]==plain.T[None,None,:,:]).all(2).any(2);a[...,3]=np.where(remove,0,a[...,3])
flower=reduce(Image.fromarray(a));save(flower,AS/'hgss-flowers.png')
for y in (13,14):
    for x in range(5,9):place(fg,flower,x*16,y*16,'flowers')

water=texture(field,'sea_un');water.putalpha(255);water.alpha_composite(texture(field,'sea_on'));water=reduce(water);save(water,AS/'hgss-water.png')
decoded=np.load(S/'ApocPalletTown/decoded.npz');mids=decoded['entries'].reshape(20,24)&1023
waterids={0x123,0x12a,0x12b,0x12c,0x2d1,0x2d2}
# Copy original shore silhouette (including concave corners); shade it with the
# actual HGSS rock material. The narrow lip does not become a whole cliff square.
rock=reduce(texture(field,'sea_rock')).convert('RGB');rc=np.array(rock)
colors=sorted({tuple(map(int,c)) for c in rc.reshape(-1,3) if abs(int(c[0])-int(c[1]))<32 and int(c[2])-int(c[0])<48},key=sum)
for y in range(17,22):
    oy=min(y,19)
    for x in range(24):
        if int(mids[oy,x]) not in waterids:continue
        patch=water.crop(((x%2)*16,(y%2)*16,(x%2+1)*16,(y%2+1)*16));ground.paste(patch,(x*16,(y+1)*16))
ga=np.array(ground)
for y in range(17*16,22*16):
    for x in range(7*16,11*16):
        oy=y if y<320 else 304+y%16
        if int(mids[oy//16,x//16]) not in waterids:continue
        r,g,b=map(int,ref[oy,x])
        if r>b*.8 and r>g*1.1:ga[y+16,x,:3]=colors[min(len(colors)-1,max(0,int((r+g+b)/3/256*len(colors))))]
ground=Image.fromarray(ga)
for name,im in [('ground',ground),('foreground',fg)]:save(im,S/'ApocPalletTown'/(name+'.png'))
composed=ground.copy();composed.alpha_composite(fg);save(composed,EV/'assembly-town.png');numbered(composed).save(EV/'assembly-town-grid.png')

# Every floor is freshly assembled from original HGSS room materials/props.
# Floor/rug surfaces are behind actors; furniture silhouettes remain complete.
roommodels=R.narc.load(PHG/'files/fielddata/build_model/bm_room.narc')
m=R.mdlview.Model(roommodels[114]);cv=R.Canvas(256,256)
R.draw_model(cv,m,m.tex,lambda x,y,z:(x+8,y,z+10),0,0)
plant=Image.fromarray(np.dstack([cv.rgb.astype(np.uint8),np.where(cv.depth>-1e8,255,0).astype(np.uint8)]))
plant=fit(plant.crop(plant.getbbox()),(16,32),'complete-potted-plant')

for name,where,w,h in [('ApocPalletRedHouse1F','Red1F',13,10),('ApocPalletRedHouse2F','Red2F',12,9),
                        ('ApocPalletOakHouse','OakHouse',13,10),('ApocPalletLab','Lab',13,14)]:
    current_map=name
    g=repeat(reduce(texture(room,'o_kido_yuka1' if where=='Lab' else 'red_h_yuka1')),(w*16,h*16))
    g.putalpha(255);f=Image.new('RGBA',g.size)
    wall=texture(room,'o_kido_kaeb1' if where=='Lab' else 'red_h_kabe1');wall.putalpha(255)
    wall=repeat(reduce(wall),(w*16,32))
    # Preserve continuous source texture phase across cells, including pilasters.
    f.paste(wall,(0,0))
    if where in ('Red1F','OakHouse'):
        raw=np.array(Image.open(RAW/where/'hgss-render.png').convert('RGBA'))
        mats=np.load(RAW/where/'hgss-ground-materials.npz');names=list(mats['names'])
        mask=np.isin(mats['material'],[i for i,n in enumerate(names) if n.startswith('red_h_mat1')])
        own=np.load(RAW/where/'hgss-foreground-owner.npz')['owner'];mask|=np.isin(own,[6,7,8,9,10]);raw[...,3]=np.where(mask,255,0)
        box=(32,80,128,144) if where=='Red1F' else (80,80,176,144)
        place(f,fit(Image.fromarray(raw).crop(box),(96,64),where+'-table-and-rug'),64,48,'table-and-four-chairs')
        props=[([5],(16 if where=='Red1F' else 0,16),(48,32),'kitchen'),([4],(64 if where=='Red1F' else 48,16),(16,32),'telephone'),([3],(96 if where=='Red1F' else 80,16),(16,32),'television')]
        for ids,(x,y),size,label in props:place(f,fit(model(ids,where),size,where+'-'+label),x,y,label)
        for x,y in ([(16,96),(192,96)] if where=='Red1F' else [(0,112),(192,112)]):place(f,plant,x,y,'potted-plant')
        window=reduce(texture(room,'red_h_mado'));place(f,window,128 if where=='Red1F' else 112,16,'window')
        if where=='OakHouse':place(f,fit(model([0],where),(32,32),'oak-bookshelf'),176,16,'bookshelf')
    elif where=='Red2F':
        # The original bedroom's rug was missing from the rejected conversion.
        rg=texture(room,'red_h_mat1_3');place(f,fit(rg,(80,64),'bedroom-rug'),64,64,'bedroom-rug')
        props=[([0],(32,64),(32,48),'bed'),([2],(16,16),(32,32),'pc'),([3],(48,16),(16,32),'chair'),
               ([5,6],(64,16),(32,32),'shelves'),([7],(96,64),(16,32),'game-console')]
        for ids,(x,y),size,label in props:place(f,fit(model(ids,where),size,'bedroom-'+label),x,y,label)
        place(f,fit(model([4],where),(16,16),'bedroom-notice'),176,16,'wall-notice')
    else:
        props=[([12,13,5],(0,16),(64,32),'research-machines'),([15],(16,48),(32,48),'lab-equipment'),
               ([8,9],(144,16),(64,32),'rear-cabinets'),([7],(128,64),(48,32),'research-table'),
               ([0,1],(128,112),(80,48),'right-cabinets'),([2,3],(0,112),(80,48),'left-cabinets'),
               ([14],(0,48),(16,32),'books'),([6],(64,16),(32,32),'rear-desk')]
        for ids,(x,y),size,label in props:place(f,fit(model(ids,where),size,'lab-'+label),x,y,label)
        for x in (0,192):place(f,plant,x,176,'potted-plant')
    if where in ('Red1F','Red2F'):
        stair=reduce(Image.open(RAW/where/'hgss-terrain.png').convert('RGBA').crop((160,16,208,64)))
        place(f,stair,160 if where=='Red1F' else 128,16,'original-HGSS-stairs')
    original=np.load(S/name/'decoded.npz');originalpixels=original['pixels'];entries=original['entries']
    for i,v in enumerate(entries):
        x,y=i%w,i//w
        if not originalpixels[y*16:y*16+16,x*16:x*16+16].any():
            g.paste((0,0,0,255),(x*16,y*16,x*16+16,y*16+16));f.paste((0,0,0,0),(x*16,y*16,x*16+16,y*16+16))
    if where!='Red2F':
        mat=fit(model([4] if where=='Lab' else [2],where),(48,16),where+'-exit-mat')
        place(f,mat,80 if where=='Lab' else 48,192 if where=='Lab' else 128,'exit-mat')
    save(g,S/name/'ground.png');save(f,S/name/'foreground.png');out=g.copy();out.alpha_composite(f)
    save(out,EV/(name+'-assembly.png'));numbered(out).save(EV/(name+'-assembly-grid.png'))

(S/'assets.json').write_text(json.dumps(assets,indent=2)+'\n')
(S/'placements.json').write_text(json.dumps(dict(tree_roots=roots,root_beds_disjoint=True,placements=placements),indent=2)+'\n')
(S/'foreground-material-grid.json').write_text(json.dumps(semantics,indent=2)+'\n')
print('Fresh receiving layers and complete HGSS assets assembled; native conversion still pending.')
