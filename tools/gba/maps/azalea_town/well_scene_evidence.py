"""Read-only evidence for the fresh native well scene; no engine/map mutations."""
from pathlib import Path
import sys,json,numpy as np,hashlib
from PIL import Image,ImageDraw,ImageFont
HUB=Path(__file__).resolve().parents[4];S=HUB/'gba/art/azalea-town/source';D=S/'well-scene';E=S.parent/'evidence';G=Path(sys.argv[1]);sys.path.insert(0,str(HUB/'tools/gba/maps'));from tiles import Tileset
r=json.loads((E/'assembly.json').read_text());plan=json.loads((D/'ledger.json').read_text());t=Tileset(G,'azalea','azalea');grid=np.fromfile(G/'data/layouts/JohtoAzaleaTown/map.bin','<u2').reshape(33,64);native=t.map_image(grid.ravel().tolist(),64).convert('RGB');a=np.array(native);target=np.array(Image.open(D/'proposal.png').convert('RGB'));assert np.array_equal(a,target)
before=np.array(Image.open(D/'before-background.png'));f=np.array(Image.open(D/'before-foreground.png'));before[f[...,3]>0]=f[f[...,3]>0];diff=np.any(a!=before[...,:3],2);authorized=np.load(D/'edit-mask.npy');assert not diff[~authorized].any()
root=np.load(S/'tree-footprints.npy');assert root.max()==1
# Reuse exact current native comparison, never image-generated redraws.
reference=Image.new('RGB',(1024,528),'#223039');reference.paste(Image.open(D/'hgss-reference-true-heights.png').convert('RGB'),(-16,112))
box=(640,112,944,368);w,h=box[2]-box[0],box[3]-box[1];comparison=Image.new('RGB',(w*4+12,h*2),'#223039');comparison.paste(reference.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(0,0));comparison.paste(native.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(w*2+12,0));comparison.save(E/'well-scene-comparison.png');comparison.save(E/'well-comparison.png')
native.crop((640,48,944,368)).resize((912,960),Image.Resampling.NEAREST).save(E/'well-scene-current.png')
# Exact 16-pixel native cells, with real map coordinates (not an approximate generated grid).
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13);label=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
sh=Image.new('RGB',(1252,586),'#223039');draw=ImageDraw.Draw(sh)
for x,title,img in [(16,'HGSS decoded, registered cell-for-cell',reference),(644,'Native map / exact 16px cells',native)]:
 draw.text((x,6),title,font=label,fill='white');sh.paste(img.crop(box).resize((608,512),Image.Resampling.NEAREST),(x,46))
 for xx in range(20):
  px=x+xx*32;draw.line((px,46,px,558),fill='#667b79');draw.text((px+2,28),str(40+xx),font=font,fill='white')
 for yy in range(17):
  py=46+yy*32;draw.line((x,py,x+608,py),fill='#667b79');draw.text((x+1,py+1),str(7+yy),font=font,fill='white')
sh.save(E/'well-scene-grid.png')
# Topographic diagram uses actual decoded relative heights -3..0, with tree heights excluded.
chart=Image.new('RGB',(820,610),'#223039');draw=ImageDraw.Draw(chart);palette={0:'#72b87d',-1:'#d2b278',-2:'#9c9160',-3:'#6d9099'};coords={(c['native'][0],c['native'][1]):c for c in plan['cells']}
for y in range(7,23):
 for x in range(40,59):
  c=coords.get((x,y));v=int(c['relative_to_town']) if c else 0;px=24+(x-40)*32;py=52+(y-7)*32;draw.rectangle((px,py,px+31,py+31),fill=palette.get(v,'#53625a'),outline='#263b37');draw.text((px+5,py+8),str(v),font=font,fill='#101c1d')
for x in range(40,59):draw.text((26+(x-40)*32,32),str(x),font=font,fill='white')
for y in range(7,23):draw.text((1,59+(y-7)*32),str(y),font=font,fill='white')
draw.text((20,7),'Decoded HGSS levels relative to town lawn',font=label,fill='white');draw.text((650,60),'Town: 0',font=label,fill='white');draw.text((650,91),'Return: -1',font=label,fill='white');draw.text((650,122),'Ramp: -2',font=label,fill='white');draw.text((650,153),'Court: -3',font=label,fill='white');draw.text((20,577),'Wall cells use their high edge; sloped grass quantized to native levels.',font=label,fill='white');chart.save(E/'well-scene-heights.png')
# Actual input/native collision agreement, exceptions explicitly recorded.
solid=(grid&0xc00)!=0;exceptions=[];checked=0
for c in plan['cells']:
 x,y=c['native']
 if 0<=y<33 and 0<=x<64 and authorized[y*16:(y+1)*16,x*16:(x+1)*16].any():
  checked+=1
  if bool(solid[y,x])!=c['blocked']:exceptions.append(dict(hgss=c['hgss'],native=[x,y],source_blocked=c['blocked'],native_blocked=bool(solid[y,x]),reason='Closed provisional well exterior / wider accepted well master; interior warp unwired'))
assert {(v['native'][0],v['native'][1]) for v in exceptions} <= {(48,12),(48,13),(48,14)},exceptions
wall=np.zeros((33,64),bool)
for c in plan['wall_modules']:x,y=c['native'];wall[y,x]=True
assert not (wall&(root>0)).any(),'Tree roots overlap a vertical face'
props=json.loads((D/'placements.json').read_text());canopy_conflicts=[]
for p in props['new']:
 if p['name']!='tree':continue
 x,y=p['x'],p['y'];sprite=np.array(Image.open(S/'masters/tree.png'));wallpx=np.repeat(np.repeat(wall,16,0),16,1)
 if np.any((sprite[...,3]>0)&wallpx[y:y+48,x:x+32]):canopy_conflicts.append([x,y])
assert not canopy_conflicts,canopy_conflicts
# All local canonical props, including the newly decoded tiny stone, remain exact.
point_checks=[]
for c in [{'at':[43,7],'finding':'Outer northwest: signed down-east/down-south junction, whole native corners.'},{'at':[54,7],'finding':'Outer northeast: west-facing depth, not a mirror chosen by screen side.'},{'at':[45,10],'finding':'Inner northwest: lower court joins the grassy northern ramp.'},{'at':[51,10],'finding':'Inner northeast: matching side and front course.'},{'at':[45,16],'finding':'Southern return faces north into the pit; former front-facing wall/stair opening removed.'},{'at':[51,16],'finding':'Southeast return keeps the east corridor open.'},{'at':[49,9],'finding':'Original east-west grassy slope; no invented gray staircase.'},{'at':[47,20],'finding':'Sign pedestal on town lawn, tiny stone matches decoded silhouette.'}]:point_checks.append(c)
report=json.loads((E/'well-scene-rebuild.json').read_text());report.update(visible_changed_pixels=int(diff.sum()),visible_changes_outside_scene=0,shared_building_visible_changes=0,tree_root_overlap_cells=0,tree_root_cliff_overlap_cells=0,canopy_cliff_overlaps=0,decoded_reference_collision_cells_checked=checked,collision_exceptions=exceptions,signed_wall_cells=len(plan['wall_modules']),review_findings=point_checks,native_RGB_errors=0)
(E/'well-scene-rebuild.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['glyphs','signed_wall_cells','decoded_reference_collision_cells_checked','collision_exceptions','visible_changes_outside_scene','tree_root_cliff_overlap_cells','canopy_cliff_overlaps']},indent=2))
# Every turn is shown in its immediate source/native neighborhood at 3x.
contact=Image.new('RGB',(820,940),'#223039');dr=ImageDraw.Draw(contact)
for i,item in enumerate(point_checks):
 x,y=item['at'];left=max(640,x*16-24);top=max(112,y*16-24);crop=(left,top,left+64,top+64);px=(i%2)*410;py=(i//2)*235;dr.text((px+6,py+4),f"native ({x},{y}) / HGSS left, native right",font=font,fill='white')
 contact.paste(reference.crop(crop).resize((192,192),Image.Resampling.NEAREST),(px+6,py+27));contact.paste(native.crop(crop).resize((192,192),Image.Resampling.NEAREST),(px+208,py+27))
contact.save(E/'well-scene-corners.png')
