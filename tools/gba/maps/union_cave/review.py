"""Review actual decoded Union Cave materials, native geometry and preservation."""
from pathlib import Path
import sys,json,csv,subprocess
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/union-cave-1f/source';E=S.parent/'evidence';t=Tileset(G,'union_cave','union_cave');grid=np.fromfile(G/'data/layouts/UnionCaveRoute32Entrance/map.bin','<u2').reshape(60,34);plan=np.array([list(r) for r in (S/'hgss-material-grid.txt').read_text().splitlines()]);native=t.map_image(list(map(int,grid.ravel())),34);native.save(E/'native-map.png');ref=Image.open(S/'hgss-reference.png').convert('RGB');old=Image.open('/workspace/scratch/route32-material-porymap/UnionCaveRoute32Entrance.png').convert('RGB') if Path('/workspace/scratch/route32-material-porymap/UnionCaveRoute32Entrance.png').exists() else None
errors=[];ledger=[];visible=np.array(native);r,g,b=visible.transpose(2,0,1).astype(int);decoded=np.full((60,34),'R',dtype='<U1');partial=[]
from scipy.ndimage import binary_dilation,label as components
seed=(g-r>=24)&(g-b>=8)&(r<80)&(g<=112);cc,n=components(seed);sizes=np.bincount(cc.ravel());keep=sizes>=20;keep[0]=False;seed=keep[cc];candidate=(g-r>=24)&(g<=112)&(b<=g+8);cc,n=components(candidate);ids=np.unique(cc[seed]);ids=ids[ids>0];actual_props=np.isin(cc,ids)
for y in range(60):
 for x in range(34):
  v=int(grid[y,x]);mid=v&1023;behavior=t.attrs[int(mid>=512)][mid-512 if mid>=512 else mid]&255;blocked=bool(v&0xc00);expected=str(plan[y,x]);want=bool(np.load(S/'hgss-foot-blocked.npy')[y,x])
  if blocked!=want or (expected=='W' and behavior!=16):errors.append([x,y,expected,blocked,behavior])
  sl=np.s_[y*16:y*16+16,x*16:x*16+16];co={'O':int(actual_props[sl].sum()),'W':int(((b[sl]-g[sl]>=24)&(g[sl]-r[sl]>=32)).sum()),'X':int((visible[sl].max(2)<32).sum()),'.':int(((g[sl]>=r[sl]+4)&(abs(g[sl]-b[sl])<=4)).sum())}
  got='O' if co['O']>=48 else ('.' if co['.']>=112 else ('W' if co['W']>=112 else ('X' if co['X']>=180 else 'R')));decoded[y,x]=got
  if got!=expected:partial.append({'cell':[x,y],'traced_material':expected,'decoded_RGB_majority':got,'scope':'mixed edge/foreground or explicit staircase/exit; inspect source/native panel'})
  ledger.append([x,y,expected,got,mid,behavior,blocked,v>>12])
with (S/'cell-ledger.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['x','y','HGSS_material','native_RGB_majority','metatile','behavior','blocked_on_foot','elevation']);w.writerows(ledger)
assert not errors,errors
pm=Image.open('/workspace/scratch/union-cave-final-porymap/UnionCaveRoute32Entrance.png').convert('RGB');pd=int(np.any(np.array(pm)!=visible,2).sum());assert pd==0
# Existing named locations retain IDs; the end sentinel is generated, not a campaign location.
base='7049fd5d8b95b3f357056ff53b8b2b3a3e848d74';protected=['data/layouts/JohtoRoute32','data/maps/JohtoRoute32','data/tilesets/primary/route32','data/tilesets/secondary/route32','data/tilesets/primary/cherrygrove','data/tilesets/secondary/cherrygrove','src/field_door.c']
for p in protected:assert not subprocess.check_output(['git','-C',str(G),'diff',base,'--',p]),p
oldj=json.loads(subprocess.check_output(['git','-C',str(G),'show',base+':src/data/region_map/region_map_sections.json'],text=True));newj=json.loads((G/'src/data/region_map/region_map_sections.json').read_text());assert newj['map_sections'][:-1]==oldj['map_sections']
report={'trace_basis':'original HGSS screenshot registered 1:1 to 34x60 native squares; visual interpretation, not DS collision','cells':2040,'material_collision_behavior_errors':errors,'native_RGB_majority_disagreements':partial,'RGB_majority_caveat':'RGB heuristics cannot fully distinguish shadowed walls/stalagmites/floor; all disagreements shown for review, never counted as confirmed matches','porymap_pixel_differences':pd,'protected_paths_unchanged':protected,'existing_named_map_section_ids_preserved':True,'features_not_wired':['Route33 exit exterior','B1F access at both staircase locations'],'water':'Surf behavior; water artwork static; Surf campaign access not tested'};(E/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
colors={'.':'#607c78','R':'#887d68','W':'#186890','X':'#000000','O':'#285850'}
def diagram(a):
 im=Image.new('RGB',(544,960));d=ImageDraw.Draw(im)
 for y,row in enumerate(a):
  for x,c in enumerate(row):d.rectangle((x*16,y*16,x*16+15,y*16+15),fill=colors[c])
 return im
out=Image.new('RGB',(1120,1010),'#1a2125');out.paste(ref,(10,32));out.paste(native,(570,32));d=ImageDraw.Draw(out);d.text((10,10),'HGSS Union Cave 1F',fill='white');d.text((570,10),'Native Gen 3 reconstruction',fill='white');out.save(E/'comparison.png')
for part in range(3):
 out=Image.new('RGB',(2240,390),'#1a2125');d=ImageDraw.Draw(out)
 for j,(im,title) in enumerate([(ref,'Original HGSS'),(native,'Native reconstruction'),(diagram(plan),'Traced material grid'),(diagram(decoded),'Decoded RGB majority')]):
  x=10+j*560;out.paste(im.crop((0,part*320,544,(part+1)*320)),(x,30));d.text((x,9),title,fill='white')
 d.text((10,365),'Rows %d-%d | gray-green: floor; brown: rock; blue: water; black: void. RGB classification differences are listed in audit.json.'%(part*20,part*20+19),fill='white');out.save(E/f'material-comparison-{part+1}.png')
if old:old.save(E/'previous-entrance-test-room.png')
print('2040 material/collision cells; errors',len(errors),'RGB mixed-cell review',len(partial),'Porymap pixel differences',pd)
