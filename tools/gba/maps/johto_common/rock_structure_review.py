"""Registered source/native grid review of the complete structure rebuild."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from rock_structures import CONFIGS,P,ROOT
from johto_common.regional_rocks import load
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13);reports=[]
for c in CONFIGS:
 n=c['map'];t,g,l,b,e,a,actual=load(c,Path(c['engine']));_,bg,_,_,_,ba,before=load(c,Path(c['baseline']));target=np.array(Image.open(P/'review'/f'{n}-target.png').convert('RGBA'))
 assert np.array_equal(actual,target),(n,'native target');group='faces' if n=='JohtoRoute31' else 'r32';pm=np.array(Image.open('/tmp/rock-rebuild-'+group+'-porymap/'+n+'.png').convert('RGB'));assert np.array_equal(pm,actual[:,:,:3]),'Porymap mismatch'
 expected=json.loads((P/'evidence'/f'{n}-collision.json').read_text());allowed={(r['x'],r['y']) for r in expected};changed_attr=(a!=ba)|((g&0xfc00)!=(bg&0xfc00));assert set((int(x),int(y)) for y,x in np.argwhere(changed_attr))==allowed
 assert (Path(c['baseline'])/'data/maps'/n/'map.json').read_bytes()==(Path(c['engine'])/'data/maps'/n/'map.json').read_bytes()
 Image.fromarray(actual).save(P/'review'/f'{n}-native.png');ref=Image.new('RGB',(g.shape[1]*16,g.shape[0]*16),'#354148')
 if n=='JohtoRoute31':rp=ROOT/'gba/art/hgss-connections/references/route31-hgss.png';ref.paste(Image.open(rp),(0,0))
 else:rp=ROOT/'gba/art/johto-common/rocks/hgss-placement-audit/source/route32-hgss-blocks/hgss-reference.png';ref.paste(Image.open(rp).crop((0,0,480,2000)),(16,16))
 delta=np.any(actual!=before,2).reshape(g.shape[0],16,g.shape[1],16).any((1,3));pages=[]
 for y in range(0,g.shape[0],16):
  for x in range(0,g.shape[1],32):
   if not delta[y:y+16,x:x+32].any():continue
   w=min(32,g.shape[1]-x)*16;h=min(16,g.shape[0]-y)*16;board=Image.new('RGB',(2*(w+20),h+44),'#172329');d=ImageDraw.Draw(board)
   for i,(im,label) in enumerate([(ref,'HGSS'),(Image.fromarray(actual),'Rebuilt native')]):
    ox=i*(w+20)+10;d.text((ox,5),f'{label} | x{x}-{x+w//16-1}, y{y}-{y+h//16-1}',fill='white',font=font);board.paste(im.crop((x*16,y*16,x*16+w,y*16+h)),(ox,28))
    for q in range(0,w+1,16):d.line((ox+q,28,ox+q,28+h),fill='#466769')
    for q in range(0,h+1,16):d.line((ox,28+q,ox+w,28+q),fill='#466769')
   name=f'{n}-grid-x{x}-y{y}.png';board.save(P/'review'/name);pages.append(name)
 with (P/'evidence'/f'{n}-cells.csv').open('w') as f:
  writer=csv.writer(f);writer.writerow(['x','y','old_collision_elevation','new_collision_elevation','old_behavior','new_behavior'])
  for y,x in np.argwhere(delta|changed_attr):writer.writerow([x,y,int(bg[y,x]>>10),int(g[y,x]>>10),int(ba[y,x]),int(a[y,x])])
 reports.append(dict(map=n,changed_art_cells=int(delta.sum()),collision_behavior_changes=len(expected),native_target_errors=0,porymap_errors=0,event_changes=0,reference=str(rp.relative_to(ROOT)),reference_sha256=hashlib.sha256(rp.read_bytes()).hexdigest(),grid_pages=pages))
(P/'evidence/review.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))
