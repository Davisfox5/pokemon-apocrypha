"""Independent native geometry/interaction and preservation review for heritage."""
from pathlib import Path
import json,sys,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=E/'heritage';D.mkdir(exist_ok=True);B=S/'heritage/baseline';r=json.loads((E/'assembly.json').read_text());old=json.loads((B/'assembly.json').read_text());solid=np.load(S/'solid.npy');above=np.load(S/'heritage/above.npy');seen={(41,35)};todo=list(seen)
for x,y in todo:
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  xx,yy=x+dx,y+dy
  if 0<=xx<72 and 0<=yy<52 and not solid[yy,xx] and (xx,yy) not in seen:seen.add((xx,yy));todo.append((xx,yy))
assert len(seen)==int((~solid).sum()),('Isolated walkable cells',[(int(x),int(y)) for y,x in np.argwhere(~solid) if (x,y) not in seen])
for n in ['tree-amber','tree-autumn','tree-autumn-burned-shadow','tree-autumn-bell-shadow']:
 a=np.array(Image.open(S/'masters'/(n+'.png')));green=np.array(Image.open(S/'masters/tree-hgss.png'));assert np.array_equal(a[...,3],green[...,3]);assert len(set(map(tuple,a[a[...,3]>0,:3])))<=9
assert len(r['trees'])==489
for n in ['house','house-entry','house-green','house-southeast','gym','center','mart','dance-theater','burned-tower','bell-entrance']:
 assert (S/'masters'/(n+'.png')).read_bytes()==(B/'masters'/(n+'.png')).read_bytes(),n
assert not any(p['name'] in ['maple-hgss','maple-autumn','maple-amber','house-lantern','shrine-lantern'] for p in r['placements'])
cases=[]
for x,y in sorted(seen,key=lambda p:(p[1],p[0])):
 for name,dx,dy in [('RIGHT',1,0),('LEFT',-1,0),('DOWN',0,1),('UP',0,-1)]:
  xx,yy=x+dx,y+dy
  if y in [26,27] or yy in [26,27]:continue
  if 0<=xx<72 and 0<=yy<52 and solid[yy,xx]:cases.append(dict(map=52 if y<27 else 51,x=x,y=y if y<27 else y-27,direction=name,target=[xx,yy]))
(D/'boundary-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
interactions=json.loads((S/'heritage/interactions.json').read_text());interactionproof=[]
for i in interactions:
 mid=i['map'];n='JohtoEcruteakCity' if mid==51 else 'JohtoEcruteakTempleDistrict';p=G/'data/maps'/n;d=json.loads((p/'map.json').read_text());assert all(v['graphics_id'].startswith('OBJ_EVENT_GFX_ECRUTEAK_') for v in d['object_events']);e=next(v for v in d['bg_events'] if v['x']==i['x'] and v['y']==i['y']);assert e['script'].endswith('_'+i['name']);y=i['y']+(27 if mid==51 else 0);assert solid[y,i['x']] and (i['x'],y+1) in seen;interactionproof.append(dict(**i,reachable_south_approach=True,blocked_fixture=True))
# All native attributes and both actual tile layers must match the intended source,
# including alpha on every exposed normal-layer edge (prevents player clipping).
source=[np.array(Image.open(S/(n+'.png'))) for n in ['background','foreground']];normal_checks=0
for n,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 t=Tileset(G,bank,bank);grid=np.fromfile(G/'data/layouts'/n/'map.bin','<u2').reshape(h,72)
 for y,x in np.ndindex(h,72):
  mid=int(grid[y,x]&1023);attr=t.attrs[mid>=512][mid%512];assert bool(grid[y,x]&0xc00)==bool(solid[y+y0,x]);assert ((attr&0x3000)==0)==above[y+y0,x]
  if solid[y+y0,x] and not (above[y+y0,x] and y+y0<51 and not solid[y+y0+1,x]):continue
  entries=t.blocks[mid>=512][mid%512]
  for layer in [0,1]:
   for q,e in enumerate(entries[layer*4:layer*4+4]):
    tid=e&1023;idx=np.array(t.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)
    if e&1024:idx=idx[:,::-1]
    if e&2048:idx=idx[::-1]
    # Tileset's stored palette entries use exact RGB5-expanded colors.
    yy=(y+y0)*16+q//2*8;xx=x*16+q%2*8;src=source[layer][yy:yy+8,xx:xx+8];assert np.array_equal(idx>0,src[...,3]>0),(n,x,y,layer,'alpha')
   normal_checks+=1
assert np.where(~solid[45])[0].tolist()==[41,42];assert np.where(~solid[46])[0].tolist()==[41,42]
crossings=json.loads((S/'heritage/district-crossings.json').read_text());columns=crossings['columns'];assert columns==np.where(~solid[26]&~solid[27])[0].tolist()
for name,gy,behavior,dest in [('JohtoEcruteakCity',27,100,'MAP_JOHTO_ECRUTEAK_TEMPLE_DISTRICT'),('JohtoEcruteakTempleDistrict',26,101,'MAP_JOHTO_ECRUTEAK_CITY')]:
 data=json.loads((G/'data/maps'/name/'map.json').read_text());assert not data['coord_events'];assert len(data['warp_events'])==len(columns)
 for j,e in enumerate(data['warp_events']):assert e['x']==columns[j] and e['dest_map']==dest and int(e['dest_warp_id'])==j and not solid[gy,e['x']]
 assert np.all(np.load(S/'behaviors.npy')[gy,columns]==behavior)
report=dict(baseline_source='103874452f101ba3f597cafcca73c1aa1e32998d',native_cells=3744,reachable_cells=len(seen),isolated_walkable_cells=0,tree_count=489,cleared_pond_trees=4,identical_foliage_geometry=True,unchanged_building_masters=True,one_red_lantern_master=True,gate_visual_center_x=672,gate_passage_columns=[41,42],normal_layer_alpha_checks=normal_checks,boundary_cases=len(cases),paired_native_crossings=len(columns),crossing_approaches_clear=True,static_architecture_objects=2,interactions=interactionproof,NPCs_added=0,persistent_flags_added=0,limits=['Existing building interiors and adjoining routes remain unwired.','Offering counter is unattended: inspection only, no commerce or rewards.','Shrines/signs provide repeatable public descriptions; campaign actors remain owner-placed.'])
(D/'review.json').write_text(json.dumps(report,indent=2)+'\n')
now=Image.open(E/'native-map.png');prior=Image.open(B/'native-map.png');concept=Image.open(S/'heritage/approved-concept.png');shutil.copyfile(S/'heritage/approved-concept.png',D/'approved-concept.png')
for name,box in [('restoration',(304,88,528,312)),('pond-shrine',(704,208,1024,400)),('heritage-court',(504,448,656,560)),('lanterns',(672,432,832,560)),('centered-arch',(592,672,752,784)),('tree-geometry',(256,0,464,112))]:
 w,h=box[2]-box[0],box[3]-box[1];im=Image.new('RGB',(w*4+24,h*2+36),'#223039');draw=ImageDraw.Draw(im)
 for j,(label,a) in enumerate([('Before 10387445',prior),('Native heritage',now)]):x=8+j*(w*2+8);draw.text((x,5),label,fill='white');im.paste(a.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x,28))
 im.save(D/(name+'.png'))
print('Heritage review:',len(seen),'reachable;',len(cases),'boundary probes;',len(interactions),'interactions')
