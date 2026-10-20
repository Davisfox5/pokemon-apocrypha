"""Read-only Azalea native/Porymap, shared-art and traversal review."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G,P=map(Path,sys.argv[1:3]);S=ROOT/'gba/art/azalea-town/source';E=S.parent/'evidence';t=Tileset(G,'azalea','azalea');g=np.fromfile(G/'data/layouts/JohtoAzaleaTown/map.bin','<u2').reshape(33,64);now=np.array(t.map_image(g.ravel().tolist(),64));bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));expected=bg.copy();m=fg[...,3]>0;expected[m]=fg[m];assert np.array_equal(now,expected[...,:3]);assert np.array_equal(now,np.array(Image.open(P/'JohtoAzaleaTown.png').convert('RGB')))
solid=np.load(S/'solid.npy');beh=np.load(S/'behaviors.npy');assert np.array_equal((g&0xc00)!=0,solid)
for y,x in np.ndindex(33,64):
 mid=int(g[y,x]&1023);a=t.attrs[int(mid>=512)][mid%512];assert a&255==beh[y,x]
assert all(not any(tile) for tile in t.tiles[1][496:512]), 'Door reserve not empty'
assert all((int(e)&1023)<1008 for part in t.blocks for block in part for e in block), 'Door tile reserve used by static art'
r=json.loads((E/'assembly.json').read_text());roots=np.zeros((33,64),np.uint8)
for x,y in r['trees']:roots[y+1:y+3,x:x+2]+=1
assert roots.max()==1 and np.all(solid[roots>0]);assert all(0<=x*16 and x*16+32<=1024 and y*16+48<=528 for x,y in r['trees'])
# Reconstruct foreground ownership to compare only actually visible master pixels.
owner=np.zeros((528,1024),np.uint16);images={}
for i,p in enumerate(r['placements'],1):
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));a[...,:3]&=248;images[i]=a;h,w=a.shape[:2];mask=a[...,3]>0;owner[p['y']:p['y']+h,p['x']:p['x']+w][mask]=i
asset_checks=[]
for i,p in enumerate(r['placements'],1):
 if p['name'] not in ['well','gym','small-boulder','well-S01','well-S03','well-S04','gate-P04','kurt-kiln','kurt-firewood','kurt','house','tree','center','mart','gate','P09-native','P12','P13','P15','F01','L11','L12','L13','boulder']:continue
 a=images[i];h,w=a.shape[:2];visible=owner[p['y']:p['y']+h,p['x']:p['x']+w]==i;assert np.array_equal(now[p['y']:p['y']+h,p['x']:p['x']+w][visible],a[visible,:3]);asset_checks.append(dict(name=p['name'],x=p['x'],y=p['y'],visible_pixels=int(visible.sum()),RGB_errors=0))
final_rocks={(p['x'],p['y']):p for p in r['rock_placements']}
for p in final_rocks.values():
 a=np.array(Image.open(S/'masters'/(p['tile']+'.png')).convert('RGBA'));a=a[:,::-1] if p['mirror'] else a;x,y=p['x']*16,p['y']*16;mask=a[...,3]>0
 if p['tile'].startswith('well-'):
  # Authoring modules remain complete. Native encoding may reuse occluded BG
  # pixels, while foreground objects and every visible terrain pixel stay exact.
  authored=np.array(Image.open(S/'well-elevation-rebuild/target-background.png').convert('RGBA'));assert np.array_equal(authored[y:y+16,x:x+16][mask],a[mask]);visible=mask&(fg[y:y+16,x:x+16,3]==0);assert np.array_equal(now[y:y+16,x:x+16][visible],a[visible,:3])
 else:
  visible=mask&(fg[y:y+16,x:x+16,3]==0);assert np.array_equal(now[y:y+16,x:x+16][visible],a[visible,:3])
# Static reachability from central street, including directional ledges. This is
# authored topology interpreted from the overview, not extracted DS collision.
seen={(20,18)};todo=list(seen)
for x,y in todo:
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  nx,ny=x+dx,y+dy
  if not(0<=nx<64 and 0<=ny<33):continue
  if solid[ny,nx]:
   if dy==1 and beh[ny,nx]==59:ny+=1
   else:continue
  if ny<33 and not solid[ny,nx] and (nx,ny) not in seen:seen.add((nx,ny));todo.append((nx,ny))
points={'Kurt':(14,12),'Center':(25,16),'Mart':(34,14),'Gym':(20,25),'house':(34,22),'well':(48,16),'Ilex gate':(8,18),'east road':(61,24),'well outer corridor':(52,12),'Kurt side yard':(20,9),'Kurt addition front':(18,12),'well stair west':(43,10),'well stair east':(45,10),'well south stair head':(49,16),'well south stair foot':(49,17)}
assert all(p in seen for p in points.values()),{k:p for k,p in points.items() if p not in seen}
assert not any(x<8 for x,y in seen),'Gate bypass remains reachable'
mat=np.load(S/'material-grid.npy');ledger=[]
for y,x in np.ndindex(33,64):ledger.append(dict(x=x,y=y,reference_pixel_box=[x*16-64,y*16-16,x*16-48,y*16],material=mat[y,x],native_metatile=int(g[y,x]&1023),collision=int(g[y,x]>>10&3),behavior=int(beh[y,x]),reference_limits='Overview registration; foreground/roof/forest occlusion and approved footprint adaptations recorded separately.'))
(E/'cell-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');(E/'shared-art-review.json').write_text(json.dumps(asset_checks,indent=2)+'\n')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);native=Image.fromarray(now);native.save(E/'native-map.png');native.resize((2048,1056),Image.Resampling.NEAREST).save(E/'native-map-2x.png');ref=Image.open(S/'hgss-reference.png').convert('RGB');registered=Image.new('RGB',(1024,528),'#223039');registered.paste(ref,(64,16));sheet=Image.new('RGB',(2080,590),'#223039');d=ImageDraw.Draw(sheet)
for x,title,im in [(8,'HGSS registered at +64,+16; dark border is extension',registered),(1048,'Native Azalea exterior / complete shared trees and service buildings',native)]:d.text((x,8),title,font=font,fill='white');sheet.paste(im,(x,40))
sheet.save(E/'reference-comparison.png')
for title,im in [('reference',registered),('native',native)]:
 sh=Image.new('RGB',(1072,576),'#223039');sh.paste(im,(32,32));d=ImageDraw.Draw(sh)
 for x in range(65):d.line((32+x*16,32,32+x*16,560),fill='#586974');d.text((32+x*16,12),str(x),fill='white')
 for y in range(34):d.line((32,32+y*16,1056,32+y*16),fill='#586974');d.text((4,32+y*16),str(y),fill='white')
 sh.save(E/(title+'-grid.png'))
for name,box in [('Kurt',(144,80,336,240)),('service-buildings',(352,112,640,288)),('Gym-loop',(192,288,480,464)),('well',(672,96,880,288)),('house-forest',(480,256,752,432)),('gate',(0,192,192,336))]:
 w,h=box[2]-box[0],box[3]-box[1];sh=Image.new('RGB',(w*4+32,h*2+44),'#223039');d=ImageDraw.Draw(sh)
 for i,(label,im) in enumerate([('HGSS',registered),('Native',native)]):x=8+i*(w*2+16);d.text((x,6),label,font=font,fill='white');sh.paste(im.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x,36))
 sh.save(E/(name+'-comparison.png'))
owned=[p for p in G.glob('data/tilesets/*/azalea/**/*') if p.is_file()]+list((G/'data/layouts/JohtoAzaleaTown').glob('*'))+list((G/'data/maps/JohtoAzaleaTown').glob('*'))
(S/'native-edit-lock.json').write_text(json.dumps({'authority':'Native source is now the editor; do not replay first-authoring build over committed layouts.','files':{str(p.relative_to(G)):hashlib.sha256(p.read_bytes()).hexdigest() for p in owned}},indent=2)+'\n')
report=dict(native_cells=2112,Porymap_RGB_errors=0,decoded_physics_errors=0,tree_count=r['tree_count'],partial_tree_sprites=0,overlapping_root_cells=0,visible_shared_pixels_checked=sum(v['visible_pixels'] for v in asset_checks),shared_RGB_errors=0,complete_rock_cells=len(final_rocks),reachable_ground_cells=len(seen),reachable_approaches={k:list(v) for k,v in points.items()},glyphs=r['glyphs'],palettes=r['palettes'],metatiles=r['metatiles'],owner_visual_acceptance='pending',scope='Exterior design only; doors, well descent and adjacent-map connections remain closed pending their separate area implementation.')
(E/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
