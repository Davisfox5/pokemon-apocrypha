"""Read-only native/Porymap, complete-footprint and cell/traversal audit."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G,P=map(Path,sys.argv[1:3]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';r=json.loads((E/'assembly.json').read_text());W,H=r['size'];solid=np.load(S/'solid.npy');beh=np.load(S/'behaviors.npy');mat=np.load(S/'material-grid.npy');ground=np.load(S/'ground-material-grid.npy');ims=[];ledger=[];usage=[]
for district in r['districts']:
 name,bank,h,y0=district['map'],district['tileset'],district['height'],district['global_y'];t=Tileset(G,bank,bank);g=np.fromfile(G/'data/layouts'/name/'map.bin','<u2').reshape(h,W);im=np.array(t.map_image(g.ravel().tolist(),W));assert np.array_equal(im,np.array(Image.open(P/(name+'.png')).convert('RGB')))
 ids=set();pals=set()
 for y,x in np.ndindex(h,W):
  mid=int(g[y,x]&1023);a=t.attrs[mid>=512][mid%512];assert a&255==beh[y+y0,x];assert bool(g[y,x]&0xc00)==solid[y+y0,x]
  for e in t.blocks[mid>=512][mid%512]:ids.add(e&1023);pals.add(e>>12)
  sx,sy=x*16-64,(y+y0)*16-16
  ledger.append(dict(map=name,x=x,y=y,global_y=y+y0,reference_pixel_box=[sx,sy,sx+16,sy+16],background_material=str(ground[y+y0,x]),foreground_material=str(mat[y+y0,x]),native_metatile=mid,foot_blocked=bool(solid[y+y0,x]),behavior=a&255,source_status='padding / completed perimeter proposal' if sx<0 or sy<0 or sx+16>1032 or sy+16>785 else 'overview interpretation; foreground-occluded original ground/traversal unverified'))
 assert max(ids)<1008 and max(pals)<13
 usage.append(dict(map=name,unique_glyph_IDs=len(ids),highest_glyph_ID=max(ids),palette_banks=sorted(pals),metatiles=district['metatiles'],Porymap_pixel_errors=0))
 ims.append((y0,im))
now=np.concatenate([v for _,v in sorted(ims)]);bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));expected=bg.copy();m=fg[...,3]>0;expected[m]=fg[m];assert np.array_equal(now,expected[...,:3])
# Inanimate architecture uses native OBJ graphics; Porymap background comparison
# above remains exact. Decode the committed indexed assets for the full overview.
Image.fromarray(now).save(E/'native-background.png')
for p in r.get('object_placements',[]):
 a=np.array(Image.open(G/p['graphics_path']).convert('RGBA'));px,py=p['native_padding'];master=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=master.shape[:2];a=a[py:py+h,px:px+w];assert np.array_equal(a,master),p['name'];m=a[...,3]>0;now[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m,:3]
roots=np.zeros((H,W),np.uint8)
for p in r['trees']:
 x,y=p['x'],p['y'];roots[y+1:y+3,x:x+2]+=1;assert 0<=x*16 and x*16+32<=W*16 and 0<=y*16 and y*16+48<=H*16
assert roots.max()==1 and np.all(solid[roots>0])
# Shared canonical pixels are tested only where visible after later placements.
owner=np.zeros((H*16,W*16),np.uint16);masters={}
for i,p in enumerate(r['placements'],1):
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));a[...,:3]&=248;masters[i]=a;h,w=a.shape[:2];m=a[...,3]>0;owner[p['y']:p['y']+h,p['x']:p['x']+w][m]=i
shared={v['name'] for v in json.loads((S/'shared-provenance.json').read_text())};checks=[]
for i,p in enumerate(r['placements'],1):
 a=masters[i];h,w=a.shape[:2];visible=owner[p['y']:p['y']+h,p['x']:p['x']+w]==i
 assert np.array_equal(now[p['y']:p['y']+h,p['x']:p['x']+w][visible],a[visible,:3]),p;checks.append(dict(name=p['name'],kind='shared' if p['name'] in shared else 'local',x=p['x'],y=p['y'],visible_pixels=int(visible.sum()),RGB_errors=0))
# Material and traversal are deliberately separate. The overview does not prove
# hidden original collision; this BFS qualifies the authored exterior only.
seen={(41,35)};todo=list(seen)
for x,y in todo:
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  nx,ny=x+dx,y+dy
  if 0<=nx<W and 0<=ny<H and not solid[ny,nx] and (nx,ny) not in seen:seen.add((nx,ny));todo.append((nx,ny))
points={'Burned Tower stair foot':(25,18),'Burned Tower door':(25,14),'Bell Tower entrance':(41,18),'northwest house':(25,26),'northeast house':(35,26),'west house':(25,34),'Dance Theater':(47,34),'Gym':(26,41),'Center':(47,41),'Mart':(56,34),'south torii':(41,46)}
assert all(p in seen for p in points.values()),{k:p for k,p in points.items() if p not in seen}
(E/'cell-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');(E/'shared-art-review.json').write_text(json.dumps(checks,indent=2)+'\n')
native=Image.fromarray(now);native.save(E/'native-map.png');native.resize((W*32,H*32),Image.Resampling.NEAREST).save(E/'native-map-2x.png');ref=Image.open(S/'hgss-reference.png').convert('RGB');registered=Image.new('RGB',(W*16,H*16),'#223039');registered.paste(ref,(64,16))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
sheet=Image.new('RGB',(W*32+32,H*16+64),'#223039');d=ImageDraw.Draw(sheet)
for x,label,im in [(8,'HGSS original, registered +64,+16; dark border is native extension',registered),(W*16+24,'Decoded Gen 3 exterior; shared Center/Mart, complete native trees',native)]:d.text((x,8),label,font=font,fill='white');sheet.paste(im,(x,40))
sheet.save(E/'reference-comparison.png')
for name,im in [('reference',registered),('native',native)]:
 sh=Image.new('RGB',(W*16+48,H*16+48),'#223039');sh.paste(im,(32,32));d=ImageDraw.Draw(sh)
 for x in range(W+1):d.line((32+x*16,32,32+x*16,H*16+32),fill='#697279');d.text((32+x*16,12),str(x),fill='white')
 for y in range(H+1):d.line((32,32+y*16,W*16+32,32+y*16),fill='#697279');d.text((4,32+y*16),str(y),fill='white')
 sh.save(E/(name+'-grid.png'))
for name,box in [('Burned-Tower',(304,96,512,304)),('temple-pond',(536,176,912,400)),('residential-courts',(336,336,672,576)),('civic-buildings',(664,432,1000,688)),('Gym-torii',(336,544,768,784)),('grove-outcrop',(176,224,304,336))]:
 w,h=box[2]-box[0],box[3]-box[1];sh=Image.new('RGB',(w*4+32,h*2+40),'#223039');d=ImageDraw.Draw(sh)
 for i,(label,im) in enumerate([('HGSS',registered),('Native',native)]):x=8+i*(w*2+16);d.text((x,6),label,font=font,fill='white');sh.paste(im.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x,32))
 sh.save(E/(name+'-comparison.png'))
report=dict(native_cells=W*H,source_grid='16px at source(+64,+16), no geometric scaling',Porymap_RGB_errors=0,decoded_material_pixels_vs_authoring_errors=0,decoded_collision_behavior_errors=0,tree_count=len(r['trees']),partial_trees=0,overlapping_root_cells=0,visible_master_pixels_checked=sum(v['visible_pixels'] for v in checks),visible_shared_pixels_checked=sum(v['visible_pixels'] for v in checks if v['kind']=='shared'),reachable_cells=len(seen),reachable_approaches={k:list(v) for k,v in points.items()},district_usage=usage,owner_visual_acceptance='pending',limits=['Overview-derived geography, not extracted DS collision or hidden ground.','Native building footprints, complete tree alignment and gate padding are adaptations.','Two rendering districts use short ordinary fades on the avenue; adjacent routes and interiors remain closed.'])
(E/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
