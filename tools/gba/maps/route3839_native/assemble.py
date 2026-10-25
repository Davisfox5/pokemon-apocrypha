"""First authoring of two terrain-only native maps from independent original layers.
Uses shared FRLG terraces and Cherrygrove materials; committed maps are authoritative.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_fill_holes
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from claude_cherrygrove import ground as G
from tiles import Tileset
spec=importlib.util.spec_from_file_location('shared_terraces',HERE.parent/'route31_catalog/rock.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
ENGINE=Path(sys.argv[1]);S=ROOT/'gba/art/route38-39-native/source';E=S.parent/'evidence';E.mkdir(exist_ok=True)
assert not subprocess.check_output(['git','-C',str(ENGINE),'ls-files','data/tilesets/primary/route3839_native'],text=True).strip(),'Committed native map exists; edit it directly.'
t=Tileset(ENGINE,'cherrygrove','cherrygrove');b=np.fromfile(ENGINE/'data/layouts/CherrygroveCity/map.bin','<u2');town=np.array(t.map_image(b.tolist(),80));tex=G.textures();grass=tex[G.GRASS];road=tex[G.PATH]
# Use the actual accepted town road's phase, not a new road texture.
from collections import Counter
c=Counter();core=np.isin(town[...,0],[216,224])&np.isin(town[...,1],[184,200])&(town[...,2]==128)
for y in range(0,town.shape[0]-31,32):
 for x in range(0,town.shape[1]-31,32):
  if core[y:y+32,x:x+32].all():c[town[y:y+32,x:x+32].tobytes()]+=1
assert c;road=np.frombuffer(c.most_common(1)[0][0],np.uint8).reshape(32,32,3);tex[G.PATH]=road
Image.fromarray(grass).save(S/'shared-lawn.png');Image.fromarray(road).save(S/'shared-road.png');pieces=R.frlg_pieces(ENGINE)
# Retain complete native reusable pieces as editable source art.
for family,entries in pieces.items():
 for name,a in entries.items():
  rgba=np.zeros((16,16,4),np.uint8)
  for i,col in enumerate(R.ROCK_RAMP):rgba[a==i]=tuple(v&248 for v in col)+(255,)
  rgba[a==R.SHADOW]=R.BORDER_GRAY+(255,)
  p=S/'shared-rock'/family;p.mkdir(parents=True,exist_ok=True);Image.fromarray(rgba).save(p/(('-'.join(name) if isinstance(name,tuple) else name)+'.png'))
alltiles=[];ids={};maps={};adapt=[];reports=[]
for route,W,H in [(38,64,32),(39,32,64)]:
 z=np.load(S/f'route{route}-original.npz');o=np.load(S/f'route{route}-hgss/decoded.npz');typ=z['types'];col=z['collision'];height=z['height'].copy();known=z['height_known'].copy();top=z['wall_top'];wall=z['wall_coverage']>.12;ramp=z['incline'].copy();ramp&=~((typ==0x4c)&((col&0x80)!=0));wall[ramp]=False
 # Every face comes from original terrain, not jump permissions or foreground boulders.
 closed=binary_fill_holes(wall)&~wall
 if route==38:closed&=np.indices((H,W))[1]>=60
 else:closed[:]=False
 wall|=closed
 for y,x in np.argwhere(closed):height[y,x]=4;known[y,x]=False
 # Per-8px road material from original bound triangles, free of canopy occlusion.
 roadpx=Image.new('1',(W*16,H*16));dr=ImageDraw.Draw(roadpx)
 for a in json.loads((S/f'route{route}-terrain-mesh.json').read_text()):
  if a['material'].startswith('road01'):dr.polygon([(v[0]*16,v[2]*16) for v in a['xyz']],fill=1)
 rm=np.array(roadpx);q=rm.reshape(H*2,8,W*2,8).mean((1,3))>=.5
 # A bound road material includes grass in its texture border. Resolve the
 # visible surface from the foreground-free original texture, not its mesh bounds.
 clear=np.load(S/f'route{route}-hgss/cleared.npz');rgb=clear['rgb'].astype(int);cm=clear['material'];cn=list(clear['names']);roadids=[i for i,n in enumerate(cn) if n.startswith('road01')];sand=np.isin(cm,roadids)&(rgb[...,0]>=rgb[...,1])&(rgb[...,0]>180)&(rgb[...,2]<175)
 q=sand.reshape(H*2,8,W*2,8).mean((1,3))>=.5
 # Original visible road pixels are independently checked at all unobscured quadrants.
 names=list(o['names']);nm=np.array(names+['none']);mi=np.where(o['material']>=0,o['material'],len(names));visible=np.isin(nm[mi],[n for n in names if n.startswith('road01')]);visibleq=visible.reshape(H*2,8,W*2,8).mean((1,3))>=.5
 # Foreground removal leaves the decoded ground beneath intact, including mixed ledge/path cells.
 matpx=np.repeat(np.repeat(q,8,0),8,1).astype(np.int8);yy,xx=np.indices(matpx.shape);base=grass[yy%32,xx%32].copy();base[matpx==1]=road[yy[matpx==1]%32,xx[matpx==1]%32]
 # Native-aligned straight runs; small local corner rims, no wavy sampling.
 for a,b in [(G.GRASS,G.PATH)]:
  da=G._chamfer(matpx==a);db=G._chamfer(matpx==b);pa,pb=G.PROFILES[(a,b)]
  for k,c1 in enumerate(pa):base[(matpx==a)&(db==k+1)]=c1
  for k,c1 in enumerate(pb):base[(matpx==b)&(da==k+1)]=c1
 cells=[];level=np.rint(height).astype(int)
 # Wall material elevation is its real model peak. Exclude ground height under a wall.
 for y,x in np.argwhere(wall):level[y,x]=max(1,round(float(top[y,x]))) if top[y,x]>=0 else max(1,round(float(height[y,x])))
 # In a two-course face the lower course remains its own original height.
 for y in range(H):
  row=[]
  for x in range(W):row.append(dict(lab='R' if wall[y,x] else '.',floor='sand' if q[y*2:y*2+2,x*2:x*2+2].mean()>=.5 else 'grass',ground=float(height[y,x]),peak=float(level[y,x])))
  cells.append(row)
 base,over,choices=R.rock_frlg(cells,level,wall,base,pieces,dict(grass=grass,sand=road));mask=over[...,3]>0;base[mask]=over[mask,:3]
 # The whole stair opening, tread phase and native shoulder join are authored together.
 stair=np.array(Image.open(ROOT/'gba/art/route38-39-terrain/source/masters/0xcf.png').convert('RGBA'));stair[...,:3]&=248;stair[...,3]=255  # Restore white tread noses keyed out by the historical donor mask.
 for y,x in np.argwhere(ramp):
  sl=np.s_[y*16:(y+1)*16,x*16:(x+1)*16]
  if z['grass_ramp'][y,x]:
   a=grass[yy[sl]%32,xx[sl]%32].copy();a[13:15]=[88,176,136];base[sl]=a
  else:
   a=base[sl].copy();flight=stair if route==39 else np.rot90(stair,1);m=flight[...,3]>0;a[m]=flight[m,:3];base[sl]=a
  # The junction's original slope material is a real east-facing stair flight.
 elevation=np.clip(np.rint(height)*2-1,1,13).astype(np.uint8);elevation[ramp]=0;solid=wall.copy();solid[0]=solid[-1]=True;solid[:,0]=solid[:,-1]=True
 if route==38:solid[11:14,0]=False
 else:solid[11:14,-1]=False
 labels=np.where(wall,'R',np.where(q.reshape(H,2,W,2).mean((1,3))>=.5,'P','L'));labels[ramp]='A';labels[ramp&~z['grass_ramp']]='S'
 grid=np.zeros((H,W),'<u2');ledger=[];bad=[]
 base&=248
 for y,x in np.ndindex(H,W):
  a=base[y*16:(y+1)*16,x*16:(x+1)*16];key=a.tobytes()
  if key not in ids:ids[key]=len(alltiles);alltiles.append(np.dstack([a,np.full((16,16),255,np.uint8)]))
  grid[y,x]=ids[key]|(int(elevation[y,x])<<12)|(0xc00 if solid[y,x] else 0)
  record=dict(x=x,y=y,original_type=int(typ[y,x]),original_collision=int(col[y,x]),material=str(labels[y,x]),ground_height=round(float(height[y,x]),4),height_known=bool(known[y,x]),terrain_peak=int(level[y,x]),native_blocked=bool(solid[y,x]),native_elevation=int(elevation[y,x]),rock_join=str(choices[y,x]))
  ledger.append(record)
  if bool(col[y,x]&0x80)!=bool(solid[y,x]):adapt.append(dict(route=route,**record,reason='preview perimeter' if x in [0,W-1] or y in [0,H-1] else 'original rock native footprint' if wall[y,x] else 'owner-cleared foreground, building, tall grass, fence or jump ledge'))
  for dx,dy in [(1,0),(0,1)]:
   nx,ny=x+dx,y+dy
   if nx<W and ny<H and not solid[y,x] and not solid[ny,nx] and elevation[y,x] and elevation[ny,nx] and elevation[y,x]!=elevation[ny,nx]:bad.append([x,y,nx,ny])
 Image.fromarray(base).save(S/f'route{route}-assembled.png');np.savez_compressed(S/f'route{route}-layers.npz',material=labels,solid=solid,elevation=elevation,source_height=height,source_height_known=known,terrace=level,quadrants=q,rock_piece=choices.astype(str))
 (S/f'route{route}-ledger.json').write_text('[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in ledger)+'\n]\n');(S/f'route{route}-materials.txt').write_text('\n'.join(''.join(r) for r in labels)+'\n');maps[f'route{route}']=grid
 reports.append(dict(route=route,wall_cells=int(wall.sum()),open_height_seams=bad,original_road_quadrants=int(visibleq.sum()),native_road_quadrants=int(q.sum())))
np.savez_compressed(S/'native-input.npz',pairs=np.array(alltiles),**maps);(S/'adaptations.json').write_text('[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in adapt)+'\n]\n');(E/'authoring.json').write_text(json.dumps(dict(routes=reports,metatiles=len(alltiles)),indent=2)+'\n')
(S/'art-provenance.json').write_text(json.dumps(dict(rock_source='native general_frlg primary tileset, complete mountain nine-slice, over-rock and concave corners',rock_method='shared route31_catalog/rock.py, same method as accepted Mahogany/Route43',rock_ramp=R.ROCK_RAMP,ground='accepted Cherrygrove lawn and actual native 32px road core',stairs='existing Emerald gray Mossdeep donor 0xcf',path_adaptation='8px original material registration; native straight edge with Cherrygrove profiles, wave disabled per owner'),indent=2)+'\n')
print(reports,'unique native tiles',len(alltiles))
