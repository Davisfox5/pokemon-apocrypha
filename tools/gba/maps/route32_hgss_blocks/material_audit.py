"""Check actual native terrain families, not just solidity or authoring labels."""
from pathlib import Path
import sys,json,csv
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);OUT=HERE.parents[3]/'gba/art/route32-hgss-blocks';S=OUT/'source';E=OUT/'evidence'
t=Tileset(G,'route32','route32');grid=np.fromfile(G/'data/layouts/JohtoRoute32/map.bin','<u2').reshape(128,32)
source=np.array([list(row) for row in (S/'hgss-material-grid.txt').read_text().splitlines()]);RGB=np.array(Image.open(E/'native-map.png').convert('RGB'));bank=np.full(RGB.shape[:2],-1,np.int8);bh=np.zeros(grid.shape,int)
for y in range(128):
 for x in range(32):
  mid=int(grid[y,x]&1023);part=int(mid>=512);ix=mid-512 if part else mid;bh[y,x]=t.attrs[part][ix]&255
  for layer in range(2):
   for q in range(4):
    en=t.blocks[part][ix][layer*4+q];tid=en&1023;p=np.array(t.tiles[int(tid>=512)][tid-512 if tid>=512 else tid],np.uint8).reshape(8,8)
    if en&1024:p=p[:,::-1]
    if en&2048:p=p[::-1]
    dst=bank[y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8];dst[p>0]=en>>12
# Visible material categories from the decoded hardware palettes and behavior.
pixel=np.full(bank.shape,'?',dtype='<U1');r,g,b=RGB.transpose(2,0,1).astype(int)
for bb,ch in [(1,'W'),(2,'R'),(3,'T'),(4,'X'),(5,'X'),(6,'B'),(8,'B'),(9,'D'),(10,'H'),(12,'G')]:pixel[bank==bb]=ch
for bb in [0,7]:
 selected=bank==bb;pixel[selected]='.';pixel[selected&(r>g)&(g>b)&(r>=128)]='P'
pixel[bank==11]='W'
actual=np.full((125,30),'?',dtype='<U1');rows=[];mismatches=[];counts={};foot=json.loads((S/'hgss-tree-footprints.json').read_text());prop_cells={tuple(q['source_cell']) for q in foot['props']+foot['signs']}
for sy in range(125):
 for sx in range(30):
  x,y=sx+1,sy+1;expected=source[sy,sx];p=pixel[y*16:y*16+16,x*16:x*16+16].copy();feature=int(np.isin(p,['T','X','B','H']).sum());status='checked'
  # Geometry is explicit, but the actual neutral stair pixels must be present.
  in_stairs=(9<=x<11 and 59<=y<62) or (6<=x<9 and 87<=y<89)
  if in_stairs:p[p=='H']='S';feature=int(np.isin(p,['T','X','B','H']).sum())
  if (sx,sy) in prop_cells or feature>=64:status='foreground feature/occlusion';got='X'
  elif bh[y,x]==2:got='G'
  elif bh[y,x]==59:got='_'
  else:
   valid=p[~np.isin(p,['T','X','B','H','?'])];u,n=np.unique(valid,return_counts=True);got=str(u[n.argmax()]) if len(u) else '?'
  actual[sy,sx]=got;counts[status]=counts.get(status,0)+1
  if status=='checked' and got!=expected:mismatches.append({'source':[sx,sy],'native':[x,y],'expected':expected,'decoded_visible':got})
  rows.append([sx,sy,x,y,expected,got,hex(int(grid[y,x]&1023)),hex(int(bh[y,x])),status])
# Verify explicitly traced rock planes against the actual native glyph pixels.
roles=np.load(S/'hgss-rock-quadrants.npy');family={}
for role,name in [('f','emerald-0x7c'),('t','rock-top')]:
 im=np.array(Image.open(S/'refined-materials'/f'{name}.png').convert('RGB'));family[role]=[im[y:y+8,x:x+8] for y in range(0,im.shape[0],8) for x in range(0,im.shape[1],8)]
planes_checked=0;planes_occluded=0;plane_errors=[]
for sy,sx in zip(*np.where(np.isin(roles,['f','t']))):
 if source[sy//2,sx//2]!='R':continue
 x,y=(sx+2)*8,(sy+2)*8;piece=RGB[y:y+8,x:x+8]
 if not np.all(bank[y:y+8,x:x+8]==2):planes_occluded+=1;continue
 planes_checked+=1
 if not any(np.array_equal(piece,p) for p in family[roles[sy,sx]]):plane_errors.append([int(sx),int(sy),str(roles[sy,sx])])
with (S/'source-native-materials.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['source_x','source_y','native_x','native_y','HGSS_material','decoded_native_material','metatile','behavior','scope']);w.writerows(rows)
report={'basis':'original HGSS visible terrain plus reviewed source continuity under occluders; not DS collision','checked_cell_count':counts.get('checked',0),'feature_or_occlusion_cells':counts.get('foreground feature/occlusion',0),'material_mismatches':mismatches,'explicit_cliff_quadrants_checked':planes_checked,'cliff_quadrants_partial_or_occluded':planes_occluded,'cliff_plane_errors':plane_errors,'comparison_method':'actual map.bin/metatile entries/tile graphics/palettes plus behavior; dirt/lawn by rendered ground color; cliff planes by actual native glyph RGB'}
(E/'material-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('Terrain checks',report['checked_cell_count'],'material mismatches',len(mismatches),'cliff quads',planes_checked,'cliff errors',len(plane_errors));print(mismatches[:30]);print(plane_errors[:10])

np.save(S/'native-visible-materials.npy',actual)
assert not mismatches and not plane_errors, 'Native terrain material mismatch'
