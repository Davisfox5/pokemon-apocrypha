"""Independent gate geometry, native collision and whole-exterior boundary audit."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=E/'gate-alignment';D.mkdir(exist_ok=True);B=S/'gate-alignment/baseline';r=json.loads((E/'assembly.json').read_text());old=json.loads((B/'assembly.json').read_text());edit=json.loads((S/'gate-alignment/edit-report.json').read_text());blocked=np.zeros((52,72),bool);elev=np.zeros((52,72),np.uint8);attr=np.zeros((52,72),np.uint16)
for n,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 t=Tileset(G,bank,bank);g=np.fromfile(G/'data/layouts'/n/'map.bin','<u2').reshape(h,72);blocked[y0:y0+h]=(g&0xc00)!=0;elev[y0:y0+h]=g>>12
 for y,x in np.ndindex(h,72):mid=int(g[y,x]&1023);attr[y+y0,x]=t.attrs[mid>=512][mid%512]
assert np.array_equal(blocked,np.load(S/'solid.npy'));assert (elev==3).all();assert np.array_equal(attr&255,np.load(S/'behaviors.npy'));assert np.array_equal((attr&0x3000)==0,np.load(S/'gate-alignment/above.npy'))
assert r['trees']==old['trees'];assert len(r['trees'])==493
assert [p for p in r['placements'] if p['name']!='south-gate']==[p for p in old['placements'] if p['name']!='south-gate']
for n,sha in edit['master_hashes'].items():assert hashlib.sha256((S/'masters'/(n+'.png')).read_bytes()).hexdigest()==sha
p=next(p for p in r['placements'] if p['name']=='south-gate');assert [p['x'],p['y']]==[640,688];a=np.array(Image.open(S/'masters/south-gate.png'));posts=set(((640+int(x))//16,(688+int(y))//16) for y,x in np.argwhere(a[...,3]>0) if y>=39);assert posts=={(40,45),(40,46),(43,45),(43,46),(44,45),(44,46)}
assert all(blocked[y,x] for x,y in posts);assert np.where(~blocked[45])[0].tolist()==[41,42];assert np.where(~blocked[46])[0].tolist()==[41,42]
roots=np.load(S/'tree-footprints.npy');assert roots.max()==1 and blocked[roots>0].all();mat=np.load(S/'material-grid.npy');ground=np.load(S/'ground-material-grid.npy');assert blocked[ground=='F'].all() and blocked[ground=='W'].all();ghost=(mat=='.')&blocked&(roots==0);ghost[0]=False;ghost[-1]=False;ghost[:,0]=False;ghost[:,-1]=False;assert not ghost.any()
def flood(block):
 seen={(41,35)};todo=list(seen)
 for x,y in todo:
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   xx,yy=x+dx,y+dy
   if 0<=xx<72 and 0<=yy<52 and not block[yy,xx] and (xx,yy) not in seen:seen.add((xx,yy));todo.append((xx,yy))
 return seen
seen=flood(blocked);assert len(seen)==int((~blocked).sum());assert (42,49) in seen;closed=blocked.copy();closed[45:47,41:43]=True;assert (42,49) not in flood(closed);assert blocked[:,6].all() and blocked[:,66].all()
prior=np.load(B/'solid.npy');changes=[dict(x=int(x),y=int(y),before=bool(prior[y,x]),after=bool(blocked[y,x])) for y,x in np.argwhere(prior!=blocked)];assert {(v['x'],v['y'],v['after']) for v in changes}=={(39,44,False),(40,45,True),(40,46,True)}
before=np.array(Image.open(B/'native-map.png').convert('RGB'));now=np.array(Image.open(E/'native-map.png').convert('RGB'));mask=np.zeros(now.shape[:2],bool);mask[688:752,624:720]=True;assert not (np.any(before!=now,2)&~mask).any()
# Every reachable open->blocked cardinal interface is exercised by the separate
# headless script. District trigger rows are covered by ordinary transition tests.
cases=[]
for x,y in sorted(seen,key=lambda p:(p[1],p[0])):
 for name,dx,dy in [('RIGHT',1,0),('LEFT',-1,0),('DOWN',0,1),('UP',0,-1)]:
  xx,yy=x+dx,y+dy
  if y in [26,27] or yy in [26,27]:continue
  if 0<=xx<72 and 0<=yy<52 and blocked[yy,xx]:cases.append(dict(map=52 if y<27 else 51,x=x,y=y if y<27 else y-27,global_y=y,direction=name,target=[xx,yy]))
(D/'boundary-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
ref=Image.open(S/'hgss-reference.png').convert('RGB');registered=Image.new('RGB',(1152,832),'#223039');registered.paste(ref,(64,16));box=(592,656,784,800);w,h=192,144;sheet=Image.new('RGB',(w*9+32,h*3+48),'#223039');d=ImageDraw.Draw(sheet)
for i,(label,im) in enumerate([('HGSS',registered),('Approved b89ae5d5',Image.fromarray(before)),('Gate +1 cell east',Image.fromarray(now))]):
 x=8+i*(w*3+8);d.text((x,5),label,fill='white');d.text((x,21),'Native cells [37,41,49,50]',fill='white');sheet.paste(im.crop(box).resize((w*3,h*3),Image.Resampling.NEAREST),(x,40))
sheet.save(D/'gate-comparison.png');report=dict(baseline_source=edit['baseline_source'],gate_offset=[1,0],gate_native_pixel_position=[640,688],passage_columns=[41,42],post_cells=sorted(posts),collision_changes=changes,native_cells_checked=3744,reachable_open_cells=len(seen),unreachable_open_cells=0,tree_count=493,all_tree_roots_blocked=True,all_fence_and_water_ground_blocked=True,unexplained_interior_blocked_lawn=0,gate_side_bypasses=False,side_gateway_forest_barriers_unchanged=True,visible_changes_outside_gate_rectangle=0,masters_and_other_placements_unchanged=True,boundary_engine_cases=len(cases),limits=['Interior doors and adjoining routes remain unwired and closed in this exterior preview.','HGSS geometry plus owner-requested gate adaptation; original hidden collision was not extracted.'])
(D/'review.json').write_text(json.dumps(report,indent=2)+'\n');print('Collision audit:',len(seen),'reachable cells;',len(cases),'native boundary probes queued; only three intended collision changes.')
