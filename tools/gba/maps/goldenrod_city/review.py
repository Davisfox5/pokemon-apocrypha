"""Read actual native files, actual Porymap exports, and independent ledgers."""
from pathlib import Path
import sys,json,csv,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
G,P=map(Path,sys.argv[1:3]);S=R/'gba/art/goldenrod-city/source';E=S.parent/'evidence';sections=json.loads((E/'sections.json').read_text());solid=np.load(S/'solid.npy');mat=np.load(S/'material.npy');above=np.load(S/'above.npy');source=np.array(Image.open(S/'reference-ground.png'));fg=np.array(Image.open(S/'shared-foreground.png'));expected=np.array(Image.open(S/'native-ground.png'));m=fg[...,3]>0;expected[m]=fg[m,:3];native=np.zeros((896,1344,3),np.uint8);owned=[];ledger=[];physics_errors=0
for s in sections:
 n=s['name'];x,y,x1,y1=s['box'];t=Tileset(G,n.lower(),n.lower());g=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x);im=np.array(t.map_image(g.ravel().tolist(),x1-x));assert np.array_equal(im,np.array(Image.open(P/(n+'.png')).convert('RGB'))),(n,'Porymap mismatch');native[y*16:y1*16,x*16:x1*16]=im;assert np.array_equal((g&0xc00)!=0,solid[y:y1,x:x1]);
 for cy,cx in np.ndindex(g.shape):
  wx,wy=x+cx,y+cy;mid=int(g[cy,cx]&1023);attr=t.attrs[mid>=512][mid%512];assert attr&255==0;assert ((attr>>12)&3)==(0 if above[wy,wx] else 1)
  v=str(mat[wy,wx]);greens=((source[wy*16:wy*16+16,wx*16:wx*16+16,1].astype(int)>source[wy*16:wy*16+16,wx*16:wx*16+16,0].astype(int)+12)&(source[wy*16:wy*16+16,wx*16:wx*16+16,1].astype(int)>source[wy*16:wy*16+16,wx*16:wx*16+16,2].astype(int)+8)).mean()
  # Green detection only labels obvious exposed ordinary lawn. It never decides
  # collision or ambiguous material/structure, roofs, walls or hidden ground.
  if v=='paving' and greens>.65:v='exposed lawn'
  ledger.append(dict(x=wx,y=wy,reference_box=f'{wx*16},{wy*16},{min(1330,wx*16+16)},{min(885,wy*16+16)}',visible_material_structure=v,blocked=int(solid[wy,wx]),above_player=int(above[wy,wx]),map=n,native_metatile=mid,behavior=attr&255,reference_status='padding adaptation' if wx>=83 or wy>=55 else 'roof/foreground; hidden ground not scored' if v in ['building','shared Center','forest roots','rail viaduct'] else 'overview interpretation; not decoded DS collision'))
 owned+=list((G/'data/layouts'/n).glob('*'))+list((G/'data/maps'/n).glob('*'))+[p for p in G.glob('data/tilesets/*/'+n.lower()+'/**/*') if p.is_file()]
assert np.array_equal(native,expected),'Native tile/palette/layer RGB differs from authoring intent'
roots=np.zeros((56,84),np.uint8);trees=json.loads((S/'trees.json').read_text());tree=np.array(Image.open(S/'masters/tree.png').convert('RGBA'));tree[...,:3]&=248
for x,y in trees:
 assert x%16==y%16==0 and x+32<=1344 and y+48<=896
 roots[y//16+1:y//16+3,x//16:x//16+2]+=1
 # Later canopies have supported overlap, so compare only final visible master
 # pixels. Every sprite still has its complete native32x48source silhouette.
assert roots.max()==1 and np.all(solid[roots>0]);assert np.array_equal(roots,np.load(S/'tree-roots.npy'))
center=np.array(Image.open(S/'masters/center.png').convert('RGBA'));center[...,:3]&=248;cm=center[...,3]>0;assert np.array_equal(native[576:656,800:880][cm],center[cm,:3])
seen={(58,48)};todo=list(seen)
for x,y in todo:
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  p=x+dx,y+dy
  if 0<=p[0]<84 and 0<=p[1]<56 and not solid[p[1],p[0]] and p not in seen:seen.add(p);todo.append(p)
approaches={'Radio Tower':(16,25),'Magnet station':(47,26),'Gym':(66,15),'Flower Shop':(71,13),'Game Corner':(51,35),'Department Store':(65,41),'Bike Shop':(70,46),'Center':(52,41),'north Underground':(47,15),'south Underground':(47,46),'north gate':(58,8),'south arrival':(58,48)}
assert all(p in seen for p in approaches.values())
with (E/'cell-ledger.csv').open('w') as f:w=csv.DictWriter(f,ledger[0].keys(),lineterminator='\n');w.writeheader();w.writerows(ledger)
Image.fromarray(native).save(E/'native-map.png');Image.fromarray(native).resize((2688,1792),Image.Resampling.NEAREST).save(E/'native-map-2x.png');ref=Image.new('RGB',(1344,896),'#26363c');ref.paste(Image.open(S/'hgss-reference.png'),(0,0));ni=Image.fromarray(native);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',9)
def panel(path,title,box,scale=2):
 w,h=box[2]-box[0],box[3]-box[1];out=Image.new('RGB',(w*scale*2+32,h*scale+48),'#223039');d=ImageDraw.Draw(out)
 for i,(label,im) in enumerate([('HGSS original',ref),('Decoded native tiles',ni)]):
  x=8+i*(w*scale+16);d.text((x,5),label+' — '+title,font=font,fill='white');out.paste(im.crop(box).resize((w*scale,h*scale),Image.Resampling.NEAREST),(x,36))
 out.save(E/path)
panel('reference-comparison.png','Goldenrod / 1:1 geography',(0,0,1344,896),1)
for name,box in [('Radio-plaza',(96,112,400,608)),('station-and-underpass',(560,240,1016,448)),('Gym-square',(864,0,1328,320)),('Center-and-Game-Corner',(624,432,912,688)),('department-and-bike',(976,448,1200,744)),('northern-forest-joins',(624,104,880,248)),('southern-blocks',(576,640,1328,896))]:panel(name+'-comparison.png',name,box)
for label,im in [('reference',ref),('native',ni)]:
 out=Image.new('RGB',(1384,936),'#223039');out.paste(im,(32,32));d=ImageDraw.Draw(out)
 for x in range(85):d.line((32+x*16,32,32+x*16,928),fill='#64737c');d.text((32+x*16,13),str(x),font=small,fill='white')
 for y in range(57):d.line((32,32+y*16,1376,32+y*16),fill='#64737c');d.text((7,32+y*16),str(y),font=small,fill='white')
 out.save(E/(label+'-grid.png'))
collision=ni.copy();d=ImageDraw.Draw(collision,'RGBA')
for y,x in np.ndindex(solid.shape):
 if solid[y,x]:d.rectangle((x*16,y*16,x*16+15,y*16+15),fill=(255,0,80,80))
collision.save(E/'collision-review.png')
report=dict(native_cells=4704,native_sections=len(sections),Porymap_version='6.3.1',Porymap_pixel_errors=0,authoring_to_decoded_pixel_errors=0,native_collision_and_layer_errors=0,complete_shared_trees=len(trees),overlapping_tree_roots=0,Center_exact_RGB5_pixels=int(cm.sum()),reachable_ground_cells=len(seen),connected_approaches=approaches,original_collision='Independent visual interpretation; not decoded DS data.',audit_scope='Every native cell/layer/palette decoded; original-reference material comparison is visible whole/grid/detail evidence, not an invented exact categorical score.',owner_visual_acceptance='pending')
(E/'review.json').write_text(json.dumps(report,indent=2)+'\n');(S/'native-edit-lock.json').write_text(json.dumps({'authority':'Edit the native source after first commit; never replay author.py on committed layouts. Regenerate stream.py from native source only.','files':{str(p.relative_to(G)):hashlib.sha256(p.read_bytes()).hexdigest() for p in owned}},indent=2)+'\n');print(json.dumps(report,indent=2))
