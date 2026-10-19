"""Read-only native tree, gate-seal and preservation evidence."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=E/'tree-closure';D.mkdir(exist_ok=True);B=S/'tree-closure/baseline';r=json.loads((E/'assembly.json').read_text());old=json.loads((B/'assembly.json').read_text());edit=json.loads((S/'tree-closure/edit-report.json').read_text());names={'tree-hgss','maple-hgss','maple-amber','maple-autumn'}
assert [p for p in r['placements'] if p['name'] not in names]==[p for p in old['placements'] if p['name'] not in names]
for n,sha in edit['shared_master_hashes'].items():assert hashlib.sha256((S/'masters'/(n+'.png')).read_bytes()).hexdigest()==sha
blocked=np.zeros((52,72),bool);layers=[]
for n,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 t=Tileset(G,bank,bank);g=np.fromfile(G/'data/layouts'/n/'map.bin','<u2').reshape(h,72);blocked[y0:y0+h]=(g&0xc00)!=0;layers.append(np.array(t.map_image(g.ravel().tolist(),72)))
now=np.concatenate(layers);before=np.array(Image.open(B/'native-map.png').convert('RGB'));mask=np.zeros(now.shape[:2],bool)
for x0,y0,x1,y1 in edit['changed_regions_native_pixels']:mask[y0:y1,x0:x1]=True
changed=np.any(before!=now,2);assert not (changed&~mask).any()
assert blocked[:,6].all() and blocked[:,66].all(),'An exterior side gate can be bypassed.'
assert np.where(~blocked[45])[0].tolist()==[40,41,42],'Southern torii must be the sole passage across its forest belt.'
def flood(block):
 todo=[(41,35)];seen=set(todo)
 for x,y in todo:
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   nx,ny=x+dx,y+dy
   if 0<=nx<72 and 0<=ny<52 and not block[ny,nx] and (nx,ny) not in seen:seen.add((nx,ny));todo.append((nx,ny))
 return seen
seen=flood(blocked);assert (41,49) in seen and (7,25) in seen and (65,33) in seen
closed=blocked.copy();closed[45:47,40:43]=True;assert (41,49) not in flood(closed),'Alternate path around the torii exists.'
# Independent native foreground/priority decode at every blocked edge above
# accessible player space. Covered BG2/BG3 stay below elevation-3 actors;
# normal BG1 foreground must retain its exact transparent mask and RGB.
protect=np.load(S/'tree-closure/exposed-mask.npy');expected=np.array(Image.open(S/'tree-closure/exposed-foreground.png'));above=np.load(S/'tree-closure/above.npy');checked=0
for n,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 t=Tileset(G,bank,bank);g=np.fromfile(G/'data/layouts'/n/'map.bin','<u2').reshape(h,72)
 for y,x in np.ndindex(h,72):
  mid=int(g[y,x]&1023);assert (g[y,x]>>12)==3;assert ((t.attrs[mid>=512][mid%512]&0x3000)==0)==above[y+y0,x]
  if not protect[y+y0,x]:continue
  rgba=np.zeros((16,16,4),np.uint8)
  for q,e in enumerate(t.blocks[mid>=512][mid%512][4:]):
   tid=e&1023;tile=t.tiles[tid>=512][tid%512];pal=t.pals[0][e>>12]
   for yy,xx in np.ndindex(8,8):
    value=tile[(7-yy if e&2048 else yy)*8+(7-xx if e&1024 else xx)]%16
    if value:rgba[q//2*8+yy,q%2*8+xx]=list(pal[value])+[255]
  want=expected[(y+y0)*16:(y+y0+1)*16,x*16:(x+1)*16];m=want[...,3]>0;assert np.array_equal(rgba[...,3],want[...,3]) and np.array_equal(rgba[m,:3],want[m,:3]);checked+=1
(D/'layer-priority.json').write_text(json.dumps(dict(exposed_normal_cells_checked=checked,native_foreground_mask_errors=0,native_foreground_RGB_errors=0,layer_attribute_errors=0,all_native_cell_elevations=3,packing_rule='Preserve exposed normal BG1 masks. Flexible blocked covered BG2/BG3 remain below elevation-3 actors; normal joins are repacked only when the next player cell south is blocked.'),indent=2)+'\n')
oldsolid=np.load(B/'solid.npy');diff=[dict(x=int(x),y=int(y),before=bool(oldsolid[y,x]),after=bool(blocked[y,x])) for y,x in np.argwhere(oldsolid!=blocked)]
ref=Image.open(S/'hgss-reference.png').convert('RGB');registered=Image.new('RGB',(1152,832),'#223039');registered.paste(ref,(64,16))
for n,box in [('burned-grove',(272,48,544,320)),('bell-grove',(504,128,800,320)),('west-gate',(0,304,176,560)),('east-gate',(976,400,1152,688)),('southern-torii',(560,656,880,832))]:
 w,h=box[2]-box[0],box[3]-box[1];im=Image.new('RGB',(w*6+32,h*2+48),'#223039');d=ImageDraw.Draw(im)
 for i,(label,a) in enumerate([('HGSS geography',registered),('Approved c8a826',Image.fromarray(before)),('Closer woodland / closed bypasses',Image.fromarray(now))]):
  x=8+i*(w*2+8);d.text((x,5),label,fill='white');d.text((x,21),'Native cells '+str([v//16 for v in box]),fill='white');im.paste(a.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x,40))
 im.save(D/(n+'.png'))
sh=Image.new('RGB',(2320,872),'#223039');d=ImageDraw.Draw(sh);d.text((8,8),'Approved c8a826',fill='white');d.text((1168,8),'Tree closure',fill='white');sh.paste(Image.fromarray(before),(8,32));sh.paste(Image.fromarray(now),(1168,32));sh.save(D/'whole-map.png')
report=dict(baseline_source='c8a8267606411bd62a6274ed0e5f430b1b2f7e80',tree_count=len(r['trees']),added=len(edit['added']),moved=len(edit['moved']),master_art_unchanged=True,building_placements_unchanged=True,visible_RGB_changes_outside_tree_neighborhoods=0,gate_checks={'west_closed_forest_wall_column':6,'east_closed_forest_wall_column':66,'side_gate_city_approaches_reachable':True,'torii_cross_section_row':45,'torii_only_open_columns':[40,41,42],'torii_central_path_reachable':True,'torii_path_unreachable_when_center_blocked':True},collision_changes=diff,owner_direction='Bring complete trees closer to both towers; fill gate/forest gaps and prevent walking around gates.',limits=['Existing side gates/interiors/routes remain unwired and closed. Southern torii passage remains open.','Tree placements are owner-requested refinements to the HGSS interpretation, not new extracted DS data.'])
(D/'review.json').write_text(json.dumps(report,indent=2)+'\n');print('Tree closure:',len(r['trees']),'full trees; side gate seals and torii-only path pass; artwork unchanged.')
