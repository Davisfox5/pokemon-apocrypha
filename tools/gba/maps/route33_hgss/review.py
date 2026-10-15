"""Read-only current native art/physics review; exports whole-map and detail evidence."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);P=Path(sys.argv[2]);S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';t=Tileset(G,'route33','route33');grid=np.fromfile(G/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);now=t.map_image(grid.ravel().tolist(),34);now.save(E/'native-map.png');ref=Image.open(S/'hgss-reference.png').convert('RGB');pory=Image.open(P/'JohtoRoute33.png').convert('RGB');assert np.array_equal(np.array(now),np.array(pory))
errors=[];solid=np.load(S/'solid.npy');beh=np.load(S/'behaviors.npy')
for y in range(29):
 for x in range(34):
  m=int(grid[y,x]&1023);a=t.attrs[int(m>=512)][m-512 if m>=512 else m]
  if bool(grid[y,x]&0xc00)!=bool(solid[y,x]) or a&255!=int(beh[y,x]):errors.append([x,y])
assert not errors
sheet=Image.new('RGB',(1120,520),(25,29,34));d=ImageDraw.Draw(sheet)
for title,im,x in [('Original HGSS reference',ref,8),('Current native Route 33',now,568)]:d.text((x,10),title,fill='white');sheet.paste(im,(x,35))
sheet.save(E/'comparison.png')
regions=[('Cave arch, threshold and ledge head',(192,128,352,224)),('Cliff shoulders and lower concave corner',(336,176,512,352)),('Tall-grass/dirt/canopy junction',(0,256,192,400)),('Ledge return and clearing',(192,224,400,352)),('Western boulder and forest feet',(16,160,176,288))]
canvas=Image.new('RGB',(1100,2900),(25,29,34));d=ImageDraw.Draw(canvas)
for i,(title,box) in enumerate(regions):
 y=i*580;d.text((10,y+5),title+' — HGSS / native (nearest-neighbor)',fill='white')
 for x,im in [(10,ref),(555,now)]:
  crop=im.crop(box);crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST);canvas.paste(crop,(x,y+25))
canvas.save(E/'detail-review.png')
for name,im in [('reference',ref),('native',now)]:
 canvas=Image.new('RGB',(580,510),(25,29,34));canvas.paste(im,(32,32));d=ImageDraw.Draw(canvas)
 for x in range(35):d.line((32+x*16,32,32+x*16,496),fill=(60,65,70));d.text((32+x*16,15),str(x),fill='white')
 for y in range(30):d.line((32,32+y*16,576,32+y*16),fill=(60,65,70));d.text((3,32+y*16),str(y),fill='white')
 canvas.save(E/f'{name}-grid.png')
(E/'review.json').write_text(json.dumps({'native_cells':986,'Porymap_RGB_errors':0,'behavior_collision_errors':errors,'regions':regions,'pixel_review':'Whole map, cliff caps/faces/corners, embedded arch, ledge head/return, tall grass borders, full tree crowns/roots, boulders, sign, apricorn silhouettes','original_collision':'Interpreted from reference topology, not decoded DS collision; inspect actual runtime separately','owner_visual_acceptance':'pending'},indent=2)+'\n')
owned=[p for p in G.glob('data/tilesets/*/route33/**/*') if p.is_file()]+list((G/'data/layouts/JohtoRoute33').glob('*'))+list((G/'data/maps/JohtoRoute33').glob('*'))
(S/'native-edit-lock.json').write_text(json.dumps({'authority':'Native sources; never replay authoring over committed owner layouts','files':{str(p.relative_to(G)):hashlib.sha256(p.read_bytes()).hexdigest() for p in owned}},indent=2)+'\n')
print('986 native cells and Porymap agree; detailed review exports written')
