"""Native + actual Porymap equality and cell-by-cell receiving review sheets."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.regional_rocks import P,load
inputs=json.loads((P/'source/inputs.json').read_text());reports=[];pages=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
paths={'CherrygroveCity':'faces','JohtoRoute31':'faces','CherrygroveRoute29Approach':'r29','CherrygroveRoute30Approach':'r30','JohtoRoute32':'r32'}
for c in inputs:
 n=c['map'];group=paths[n];game=Path('/tmp/apocrypha-rock-'+group);t,g,l,b,e,a,actual=load(c,game);bt,bg,bl,bb,be,ba,old=load(c,Path(c['baseline']));target=np.array(Image.open(P/'review'/(n+'-target.png')).convert('RGBA'));pm=np.array(Image.open('/tmp/rock-'+group+'-porymap/'+n+'.png').convert('RGB'))
 assert np.array_equal(actual,target);assert np.array_equal(actual[:,:,:3],pm),(n,'Porymap mismatch');assert np.array_equal(g&0xfc00,bg&0xfc00);assert np.array_equal(a,ba)
 oldevents=json.loads((Path(c['baseline'])/'data/maps'/n/'map.json').read_text());events=json.loads((game/'data/maps'/n/'map.json').read_text());assert events==oldevents
 changed=np.any(actual!=old,2);cells=changed.reshape(g.shape[0],16,g.shape[1],16).any((1,3));coords=np.argwhere(cells);unique={}
 for y,x in coords:
  sl=np.s_[y*16:y*16+16,x*16:x*16+16];key=old[sl].tobytes()+actual[sl].tobytes();unique.setdefault(key,[]).append([int(x),int(y)])
 vals=list(unique.values());cellpages=[]
 for offset in range(0,len(vals),48):
  sheet=Image.new('RGB',(1152,720),'#172329');d=ImageDraw.Draw(sheet);d.text((8,4),n+' | before / native | changed unique cells '+str(offset+1)+'-'+str(min(len(vals),offset+48)),fill='white',font=font)
  for j,positions in enumerate(vals[offset:offset+48]):
   x,y=positions[0];dx=j%8*144+4;dy=j//8*114+24;d.text((dx,dy),f'({x},{y}) x{len(positions)}',font=font,fill='white');sl=np.s_[y*16:y*16+16,x*16:x*16+16]
   sheet.paste(Image.fromarray(old[sl]).resize((64,64),Image.Resampling.NEAREST),(dx,dy+20));sheet.paste(Image.fromarray(actual[sl]).resize((64,64),Image.Resampling.NEAREST),(dx+68,dy+20))
  p=P/'review'/f'{n}-cells-{offset//48+1:02}.png';sheet.save(p);cellpages.append(str(p.relative_to(ROOT)));pages.append(str(p))
 Image.fromarray(actual).save(P/'review'/(n+'-native.png'))
 # Context sheets cover every changed cell in 8x8-tile neighborhoods.
 boxes=sorted({(int(x)//8*8,int(y)//8*8) for y,x in coords},key=lambda q:(q[1],q[0]));contexts=[]
 for offset in range(0,len(boxes),8):
  sheet=Image.new('RGB',(1088,4*300),'#172329');d=ImageDraw.Draw(sheet)
  for j,(x,y) in enumerate(boxes[offset:offset+8]):
   dx=j%2*544;dy=j//2*300;d.text((dx+8,dy+5),f'{n} ({x},{y}) before / native',fill='white',font=font)
   for k,arr in enumerate([old,actual]):sheet.paste(Image.fromarray(arr[y*16:(y+8)*16,x*16:(x+8)*16]).resize((min(128,arr.shape[1]-x*16)*2,min(128,arr.shape[0]-y*16)*2),Image.Resampling.NEAREST),(dx+k*272+4,dy+28))
  pp=P/'review'/f'{n}-context-{offset//8+1:02}.png';sheet.save(pp);contexts.append(str(pp.relative_to(ROOT)))
 reports.append(dict(map=n,changed_cells=int(cells.sum()),changed_pixels=int(changed.sum()),native_porymap_errors=0,collision_elevation_errors=0,behavior_errors=0,event_changes=0,unique_cell_pairs=len(vals),cell_pages=cellpages,context_pages=contexts,positions=coords[:,::-1].tolist(),visual_review='see separate visual-review.json receipt'))
(P/'evidence/native-review.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['map','changed_cells','unique_cell_pairs','context_pages']} for r in reports],indent=2))
