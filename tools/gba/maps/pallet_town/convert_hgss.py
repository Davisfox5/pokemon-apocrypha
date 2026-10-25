#!/usr/bin/env python3
"""HGSS models/textures -> native source art, fitted to the FRLG material/warp reference.
Model projection uses the qualified renderer; reduction is per compatible asset family,
never nearest-tile replacement. Editable layers remain separate from collision.
"""
from pathlib import Path
import json,sys,struct,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
from native import words,numbered
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent/'route29_catalog'));import hgss_render as R
E=Path(sys.argv[1]);P=Path(sys.argv[2]);RAW=Path(sys.argv[3]);ART=ROOT/'gba/art/pallet-town';SRC=ART/'source/hgss';SRC.mkdir(parents=True,exist_ok=True)
models=R.narc.load(P/'files/a/0/4/0');roommodels=R.narc.load(P/'files/fielddata/build_model/bm_room.narc');tex=R.Tex0(R.narc.load(P/'files/a/0/4/4')[18]);roomtex=R.Tex0(R.narc.load(P/'files/a/0/4/4')[43]);provenance=[]
def q(im,n=15):
 a=np.array(im.convert('RGBA'));mask=a[:,:,3]>0
 if not mask.any():return Image.new('RGBA',im.size)
 # Transparency never spends a foreground color. Shared source ramps remain identical across props.
 opaque=Image.fromarray(a[:,:,:3][mask].reshape(-1,1,3));template=opaque.quantize(n,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 rgb=Image.fromarray(a[:,:,:3]).quantize(palette=template,dither=Image.Dither.NONE).convert('RGB');b=np.array(rgb)&248
 return Image.fromarray(np.dstack([b,np.where(mask,255,0).astype(np.uint8)]),'RGBA')

def texture(t,name):
 e=next(e for e in t.textures if e.name==name);pal=t.pal_for(e).name
 # Prefer exact name pairing (most palettes use _pl); pal_for supplies the archive's binding fallback.
 p=next((p.name for p in t.palettes if p.name in (name+'_pl',name)),pal)
 if name=='sea_on':p='sea_f02_pl'
 return Image.fromarray(R.decode(t,e,p),'RGBA')
def opaque_model(ids,room=None):
 p=RAW/(room or '');im=Image.open(p/'hgss-foreground.png').convert('RGBA');own=np.load(p/'hgss-foreground-owner.npz')['owner'];a=np.array(im);a[:,:,3]=np.where(np.isin(own,ids),255,0);im=Image.fromarray(a);return im.crop(im.getbbox())
def fit_asset(im,size,label):
 src=im.copy();src.save(SRC/(label+'-projected.png'))
 if label in ('house','lab'):
  # Preserve complete HGSS geometry while fitting its door to the reference's native 16px entrance.
  a,b=(20,40) if label=='house' else (44,64);left,right=(16,32) if label=='house' else (48,64);fitted=Image.new('RGBA',size)
  for x0,x1,u0,u1 in [(0,a,0,left),(a,b,left,right),(b,im.width,right,size[0])]:fitted.paste(im.crop((x0,0,x1,im.height)).resize((u1-u0,size[1]),Image.Resampling.NEAREST),(u0,0))
 else:fitted=im.resize(size,Image.Resampling.NEAREST)
 out=q(fitted);out.save(SRC/(label+'.png'));provenance.append(dict(asset=label,source_projected_size=list(src.size),target_size=list(size),reduction='per-family 15 colors, RGB555, nearest resampling; no dither'));return out
house=fit_asset(opaque_model([3,4]),(80,80),'house');lab=fit_asset(opaque_model([5,6]),(112,80),'lab')
sign=fit_asset(opaque_model([0]),(16,32),'house-sign');townsign=fit_asset(opaque_model([2]),(16,16),'memorial-sign');labsign=fit_asset(opaque_model([7]),(16,32),'lab-sign')
# Complete source models remain editable and credited; no source/archive mutations.
for mid in (313,314,310,311,30,29,31):(SRC/f'field-model-{mid}.nsbmd').write_bytes(models[mid])
for mid in (1,4,17,18,19,20,21,22,114,24,27,29,30,31,53,54,66,67,70,91,94,95,210):(SRC/f'room-model-{mid}.nsbmd').write_bytes(roommodels[mid])
# Render standalone HGSS plant, rather than borrowing opaque floor from a screenshot donor.
m=R.mdlview.Model(roommodels[114]);cv=R.Canvas(256,256);R.draw_model(cv,m,m.tex,lambda x,y,z:(x+8,y,z+10),0,0);a=np.dstack([cv.rgb.astype(np.uint8),np.where(cv.depth>-1e8,255,0).astype(np.uint8)]);plant=Image.fromarray(a);plant=fit_asset(plant.crop(plant.getbbox()),(16,32),'plant')
# Accepted shared tree and lawn: copied from current catalog evidence, not repainted.
tree=Image.open(ROOT/'gba/art/route31-catalog/source/shared-art/T01.png').convert('RGBA');tree.save(SRC/'shared-tree.png')
sys.path.insert(0,str(HERE.parent));from claude_cherrygrove import hgss as CG
lawn=Image.fromarray(CG.grass_texture()).convert('RGBA');lawn.save(SRC/'shared-lawn.png')
light=texture(tex,'grass02');light=q(light);water=texture(tex,'sea_un');water.putalpha(255);water.alpha_composite(texture(tex,'sea_on'));water=q(water);flowers=texture(tex,'flower01');a=np.array(flowers);plain=np.unique(np.array(texture(tex,'grass01gs'))[:,:,:3].reshape(-1,3),axis=0);a[:,:,3]=np.where((a[:,:,:3,None]==plain.T[None,None,:,:]).all(2).any(2),0,a[:,:,3]);flowers=q(Image.fromarray(a));fence=q(texture(tex,'fence_a'))
for name,im in [('hgss-lawn-detail',light),('hgss-water',water),('hgss-flowers',flowers),('hgss-fence',fence)]:im.save(SRC/(name+'.png'))
# FRLG registrations remain exactly 24x20 and 0,0. Foreground fits receiving baselines.
W,H=24,20;ground=Image.new('RGBA',(W*16,H*16));fg=Image.new('RGBA',ground.size)
for y in range(0,H*16,lawn.height):
 for x in range(0,W*16,lawn.width):ground.paste(lawn,(x,y))
# The light lawn is lawn, not a dirt road. Preserve FRLG's lighter lawn footprint cell by cell.
from native import Bank
ref=Bank(E,'primary/general_frlg','secondary/pallet_town_frlg');grid=words(E/'data/layouts/PalletTown_Frlg/map.bin');refim=ref.map(grid,W)
# Classify ground via ORIGINAL materials, never by collision. No original dark patch becomes a path.
lightids={0x009,0x285,0x286,0x28c,0x296,0x297,0x2be}
for y in range(H):
 for x in range(W):
  mid=grid[y*W+x]&1023
  if False:ground.alpha_composite(light,(x*16,y*16))
# Shadow masks are the original FRLG receiving ground planes, recolored into the shared lawn ramp.
arr=np.array(refim);ga=np.array(ground)
# Original light-lawn palette is an explicit material mask, including its original mixed-square rim.
# Keep the accepted lawn grain; lift the ramp coherently instead of pasting square lawn-detail decals.
full=(arr==np.array([189,238,213])).all(2)|(arr==np.array([238,255,255])).all(2)
rim=(arr==np.array([156,230,197])).all(2)|(arr==np.array([139,213,189])).all(2)
ga[:,:,:3]=np.minimum(248,ga[:,:,:3].astype(np.int16)+np.where(full,16,np.where(rim,8,0))[:,:,None]).astype(np.uint8)
ground=Image.fromarray(ga)
# Local silhouettes, full canopies and 2x2 non-overlapping tree roots. Canopy overlap is supported art.
roots=[]
for y in range(0,H,2):roots.extend([(0,y),(22,y)])
for x in range(2,22,2):
 if x not in (12,):roots.append((x,0))
 if x in (2,4,18,20):roots.append((x,20))
for x,y in roots:fg.alpha_composite(tree,(x*16,(y-1)*16))
# Art placements only; original blocked/open cells are retained independently by pack_hgss.py.
for image,pos in [(house,(80,48)),(house,(224,48)),(lab,(208,144)),(sign,(64,96)),(sign,(208,96)),(townsign,(144,176)),(townsign,(80,224)),(labsign,(256,240))]:fg.alpha_composite(image,pos)
# Flowers and fences use HGSS terrain textures on original FRLG cell footprints.
for y in (12,13):
 for x in range(5,9):fg.alpha_composite(flowers,(x*16,y*16))
# Fence module's centre horizontal rail from HGSS texture; no synthetic stone or substituted vegetation.
fence_strip=fence.crop((0,8,32,24)).resize((32,16),Image.Resampling.NEAREST)
for y,x0,x1 in [(11,5,9),(16,13,18)]:
 for x in range(x0,x1+1):
  if (x,y) not in ((9,11),(16,16)):fg.alpha_composite(fence_strip.crop((0,0,16,16)),(x*16,y*16))
# HGSS water and its rock/shore lip, at the original FRLG shore cells.
waterids={0x123,0x12a,0x12b,0x12c,0x2d1,0x2d2};shore=texture(tex,'sea_rock')
for y in range(H):
 for x in range(W):
  if grid[y*W+x]&1023 in waterids:
   # Retain original receiving shore mask; texture is HGSS, never source character pixels.
   patch=water.crop(((x%2)*16,(y%2)*16,(x%2+1)*16,(y%2+1)*16));ground.paste(patch,(x*16,y*16))
# The receiving shoreline lip follows the original mask at the native pixel level, using HGSS rock shades.
a=np.array(refim);ga=np.array(ground);shorecolors=np.array(q(shore).convert('RGB')).reshape(-1,3);rock=shorecolors[np.argsort(shorecolors.sum(1))][len(shorecolors)//3:]
for y in range(17*16,H*16):
 for x in range(7*16,11*16):
  if grid[(y//16)*W+x//16]&1023 not in waterids:continue
  r,g,b=map(int,a[y,x]);
  if r>b*.8 and r>g*1.1:
   val=(r+g+b)//3;ga[y,x,:3]=(104,88,72) if val<100 else (160,144,112) if val<150 else (200,184,152)
ground=Image.fromarray(ga);out=ground.copy();out.alpha_composite(fg)
for label,im in [('ground',ground),('foreground',fg),('assembled',out)]:im.save(SRC/f'town-{label}.png')
# Interior materials and each furniture model are adapted into FRLG's authored footprints.
rooms={}
for name,source,w,h in [('ApocPalletRedHouse1F','Red1F',13,10),('ApocPalletRedHouse2F','Red2F',12,9),('ApocPalletOakHouse','OakHouse',13,10),('ApocPalletLab','Lab',13,14)]:
 floor=texture(roomtex,'o_kido_yuka1' if source=='Lab' else 'red_h_yuka1');floor.putalpha(255);floor=q(floor);wall=texture(roomtex,'o_kido_kaeb1' if source=='Lab' else 'red_h_kabe1');wall.putalpha(255);wall=q(wall);g=Image.new('RGBA',(w*16,h*16));f=Image.new('RGBA',g.size)
 for y in range(h):
  for x in range(w):g.paste(floor,(x*16,y*16))
 for x in range(w):f.paste(wall.crop((0,0,16,32)),(x*16,0))
 if source in ('Red1F','OakHouse'):
  # Table, all four chairs and carpet: clean original model assembly, no actors or removals.
  raw=Image.open(RAW/source/'hgss-render.png').convert('RGBA');box=(32,80,128,144) if source=='Red1F' else (80,80,176,144)
  mats=np.load(RAW/source/'hgss-ground-materials.npz');mn=list(mats['names']);carpet=np.isin(mats['material'],[i for i,n in enumerate(mn) if n.startswith('red_h_mat1')]);owners=np.load(RAW/source/'hgss-foreground-owner.npz')['owner'];mask=carpet|np.isin(owners,[6,7,8,9,10]);aa=np.array(raw);aa[:,:,3]=np.where(mask,255,0);table=q(Image.fromarray(aa).crop(box).resize((96,64),Image.Resampling.NEAREST));f.alpha_composite(table,(64,48))
  props=[([5],(16 if source=='Red1F' else 0,16),(48,32)),([4],(64 if source=='Red1F' else 48,16),(16,32)),([3],(96 if source=='Red1F' else 80,16),(16,32))]
  for ids,(x,y),size in props:f.alpha_composite(fit_asset(opaque_model(ids,source),size,source+'-prop-'+str(ids[0])),(x,y))
  for x,y in ([(16,96),(192,96)] if source=='Red1F' else [(0,112),(192,112)]):f.alpha_composite(plant,(x,y))
  f.alpha_composite(q(texture(roomtex,'red_h_mado')),(128 if source=='Red1F' else 112,16))
  if source=='OakHouse':f.alpha_composite(fit_asset(opaque_model([0],source),(32,32),'oak-bookshelf'),(176,16))
 elif source=='Red2F':
  props=[([0],(32,64),(32,48)),([2],(16,16),(32,32)),([3],(48,16),(16,32)),([5,6],(64,16),(32,32)),([7],(96,64),(16,32))]
  for ids,(x,y),size in props:f.alpha_composite(fit_asset(opaque_model(ids,source),size,source+'-prop-'+str(ids[0])),(x,y))
 elif source=='Lab':
  props=[([12,13,5],(0,16),(64,32)),([15],(16,48),(32,48)),([8,9],(144,16),(64,32)),([7],(128,64),(48,32)),([0,1],(128,112),(80,48)),([2,3],(0,112),(80,48)),([14],(0,48),(16,32)),([6],(64,16),(32,32))]
  for ids,(x,y),size in props:f.alpha_composite(fit_asset(opaque_model(ids,source),size,source+'-prop-'+str(ids[0])),(x,y))
  for x in (0,192):f.alpha_composite(plant,(x,176))
 # Native visible stair assembly, from HGSS terrain, retained on original stairs' receiving squares.
 if source in ('Red1F','Red2F'):
  terrain=Image.open(RAW/source/'hgss-terrain.png').convert('RGBA');stair=q(terrain.crop((160,16,208,64)));f.alpha_composite(stair,((160 if source=='Red1F' else 128),16))
 # Preserve original voids, carpet/warp squares, and original solid/open domains independently.
 old=json.loads((ART/f'source/{name}-reference.json').read_text())['layout'];orig=words(E/old['blockdata_filepath']);refbank=Bank(E,'primary/building_frlg','secondary/'+{'Red1F':'generic_building_1_frlg','Red2F':'generic_building_1_frlg','OakHouse':'generic_building_2_frlg','Lab':'lab_frlg'}[source]);voids={mid for mid in {v&1023 for v in orig} if not np.array(refbank.render(mid)).any()}
 for y in range(h):
  for x in range(w):
   if (orig[y*w+x]&1023) in voids:g.paste((0,0,0,255),(x*16,y*16,x*16+16,y*16+16));f.paste((0,0,0,0),(x*16,y*16,x*16+16,y*16+16))
 # HGSS entry mat fits each original carpet; native warp registration is unaltered.
 mat=fit_asset(opaque_model([4] if source=='Lab' else [2] if source in ('Red1F','OakHouse') else [7],source),(48 if source!='Red2F' else 16,16),source+'-mat')
 if source!='Red2F':f.alpha_composite(mat,((80 if source=='Lab' else 48),(192 if source=='Lab' else 128)))
 n=SRC/name;n.mkdir(exist_ok=True);g.save(n/'ground.png');f.save(n/'foreground.png');a=g.copy();a.alpha_composite(f);a.save(n/'assembled.png');rooms[name]=dict(width=w,height=h,source_matrix=source)
(SRC/'conversion.json').write_text(json.dumps(dict(reference='FRLG 24x20 origin (0,0), no expansion',models=provenance,tree_roots=roots,rooms=rooms,hgss_source_revision=__import__('subprocess').check_output(['git','-C',str(P),'rev-parse','HEAD'],text=True).strip()),indent=2)+'\n')
print('HGSS models and texture layers assembled.')
