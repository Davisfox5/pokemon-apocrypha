"""Read-only native audit of the final fence and entrance-mask correction."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=E/'landmark-finish';D.mkdir(exist_ok=True);B=S/'landmark-finish/baseline';edit=json.loads((S/'landmark-finish/edit-report.json').read_text());r=json.loads((E/'assembly.json').read_text());old=json.loads((B/'assembly.json').read_text());before=np.array(Image.open(B/'native-map.png').convert('RGB'));now=np.array(Image.open(E/'native-map.png').convert('RGB'));solid=np.load(S/'solid.npy');above=np.load(S/'landmark-finish/above.npy');bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));names={'tree-hgss','maple-hgss','maple-amber','maple-autumn'}
assert r['trees']==[t for t in old['trees'] if t!=edit['removed_tree']];assert len(r['trees'])==493
assert [p for p in r['placements'] if p['name'] not in names]==[p for p in old['placements'] if p['name'] not in names]
assert np.array_equal(solid,np.load(B/'solid.npy'));mask=np.zeros(now.shape[:2],bool)
for x,y,xx,yy in edit['areas']:mask[y:yy,x:xx]=True
assert not (np.any(before!=now,2)&~mask).any()
a=np.array(Image.open(S/'masters/bell-entrance.png'));b=np.array(Image.open(B/'bell-entrance.png'));allowed=np.zeros(a.shape[:2],bool);allowed[2:4,69:180]=True;allowed[18:23,59:74]=True;assert not (np.any(a!=b,2)&~allowed).any();assert not a[2:4,69:180,3].any()
# Decode both hardware layers, including transparency and flip bits. Check
# affected cells plus all exposed normal edges, not merely the final RGB merge.
check=np.zeros((52,72),bool)
for x,y,xx,yy in edit['areas']:check[y//16:(yy+15)//16,x//16:(xx+15)//16]=True
exposed=above&solid;exposed[-1]=False;exposed[:-1]&=~solid[1:];check|=exposed;checked=0
for n,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 t=Tileset(G,bank,bank);grid=np.fromfile(G/'data/layouts'/n/'map.bin','<u2').reshape(h,72)
 for y,x in np.ndindex(h,72):
  mid=int(grid[y,x]&1023);assert bool(grid[y,x]&0xc00)==solid[y+y0,x];assert ((t.attrs[mid>=512][mid%512]&0x3000)==0)==above[y+y0,x]
  if not check[y+y0,x]:continue
  for layer,want in enumerate([bg,fg]):
   out=np.zeros((16,16,4),np.uint8)
   for q,e in enumerate(t.blocks[mid>=512][mid%512][layer*4:layer*4+4]):
    tid=e&1023;tile=t.tiles[tid>=512][tid%512];pal=t.pals[0][e>>12]
    for yy,xx in np.ndindex(8,8):
     v=tile[(7-yy if e&2048 else yy)*8+(7-xx if e&1024 else xx)]%16
     if v:out[q//2*8+yy,q%2*8+xx]=list(pal[v])+[255]
   expected=want[(y+y0)*16:(y+y0+1)*16,x*16:(x+1)*16];m=expected[...,3]>0;assert np.array_equal(out[...,3],expected[...,3]) and np.array_equal(out[m,:3],expected[m,:3])
  checked+=1
ref=Image.open(S/'hgss-reference.png').convert('RGB');registered=Image.new('RGB',(1152,832),'#223039');registered.paste(ref,(64,16))
for n,box in [('fence',(472,232,568,320)),('entrance',(536,184,752,304))]:
 w,h=box[2]-box[0],box[3]-box[1];sheet=Image.new('RGB',(w*9+32,h*3+48),'#223039');draw=ImageDraw.Draw(sheet)
 for i,(label,im) in enumerate([('HGSS',registered),('Approved d5405cdc',Image.fromarray(before)),('Final masks / restored fence',Image.fromarray(now))]):
  x=8+i*(w*3+8);draw.text((x,5),label,fill='white');draw.text((x,21),'Native cells '+str([v//16 for v in box]),fill='white');sheet.paste(im.crop(box).resize((w*3,h*3),Image.Resampling.NEAREST),(x,40))
 sheet.save(D/(n+'.png'))
report=dict(baseline_source=edit['baseline_source'],removed_tree=edit['removed_tree'],tree_count=493,all_other_tree_positions_unchanged=True,building_placements_unchanged=True,collision_unchanged=True,visible_changes_outside_three_local_rectangles=0,decoded_native_layer_cells_checked=checked,layer_RGB_and_transparency_errors=0,exposed_normal_edges_checked=int(exposed.sum()),Bell_mask_correction='Remove two source-foliage rows above the original dark ridge outline; recover the small leaf-occluded timber edge from its unchanged vertical grain eight pixels below. Preserve the ridge and annex gold rail.',limits=['Exterior only; gates, interiors and adjoining routes remain unwired as before.','The roof repair uses an unobscured nearby timber donor for hidden source pixels.'])
(D/'review.json').write_text(json.dumps(report,indent=2)+'\n');print('Landmark audit: one tree removed, all collision unchanged, exact native layers and local art scope pass.')
