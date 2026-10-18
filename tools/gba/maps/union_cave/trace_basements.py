"""Trace the visible original HGSS basement sections, without using native drafts."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.ndimage import label as components,find_objects
from PIL import Image,ImageDraw
from config import FLOORS
ROOT=Path(__file__).resolve().parents[4]
for key in ['b1f','b2f']:
 c=FLOORS[key];W,H=c['size'];S=ROOT/f'gba/art/union-cave-{key}/source';E=S.parent/'evidence';original=Image.open(S/'hgss-reference.png').convert('RGB');canvas=Image.new('RGB',(W*16,H*16));canvas.paste(original,(0,0));a=np.array(canvas);r,g,b=a.transpose(2,0,1).astype(int)
 label=np.full(a.shape[:2],'R',dtype='<U1');floor=(g>=48)&(g>=r+4)&(abs(g-b)<=4)&(g-r<=32);water=(b>=96)&(b-g>=24)&(g-r>=32);label[floor]='.';label[water]='W';label[a.max(2)<32]='X'
 seed=(r<=32)&(g>=32)&(g<=112)&(g-r>=24)&(b<=g+8);candidate=(g-r>=24)&(g<=112)&(b<=g+8);cc,n=components(candidate);ids=np.unique(cc[seed]);props=np.isin(cc,ids[ids>0]);label[props]='O'
 clean=a.copy();floor_template=np.array(Image.open(ROOT/'gba/art/union-cave-1f/source/hgss-reference.png').convert('RGB'))[288:304,96:112]
 def fill(box,kind='.'):
  x0,y0,x1,y1=box
  for y in range(y0,y1):
   for x in range(x0,x1):
    clean[y,x]=floor_template[y%16,x%16] if kind=='.' else a[464+y%16,240+x%16];label[y,x]=kind
 if key=='b1f':
  removed=[(236,76,260,110),(364,260,388,296),(140,748,164,788),(444,744,468,780),(464,408,480,424),(208,556,224,572)]
  for box in removed:fill(box)
  # Hiker head was in front of the plateau; restore the actual warm front face.
  clean[256:280,368:384]=a[256:280,352:368];label[256:280,368:384]='R';fill((364,280,388,296))
  # Western lower-chamber trainer overlaps the pool's bank above his feet.
  clean[748:768,140:160]=a[748:768,116:136];label[748:768,140:160]='W'
 else:
  removed=[(124,292,148,326),(412,488,436,526),(92,560,112,598),(432,80,448,96),(304,440,320,456)]
  for box in removed:fill(box)
  # Lapras is campaign content, not a baked terrain sprite.
  removed.append((328,624,360,656));clean[624:656,328:360]=np.tile(a[624:640,304:320],(2,2,1));label[624:656,328:360]='W'
 # Reuse the same native-ready cave floor texture while retaining every outline.
 yy,xx=np.indices(label.shape);mask=label=='.';clean[mask]=floor_template[yy[mask]%16,xx[mask]%16]
 plan=np.full((H,W),'R',dtype='<U1')
 for y in range(H):
  for x in range(W):
   q=label[y*16:y*16+16,x*16:x*16+16];co={v:int((q==v).sum()) for v in '.WROX'}
   plan[y,x]='O' if co['O']>=48 else ('.' if co['.']>=112 else ('W' if co['W']>=112 else ('X' if co['X']>=180 else 'R')))
 blocked=np.isin(plan,['R','W','X']);heads=np.zeros(label.shape,bool);formations=[];cc,n=components(label=='O')
 for i,box in enumerate(find_objects(cc),1):
  if box is None:continue
  sy,sx=box;mask=cc[box]==i
  if mask.sum()<12:continue
  root_y=(sy.stop-1)//16;roots=[[x,root_y] for x in range(sx.start//16,(sx.stop-1)//16+1)]
  for x,y in roots:blocked[y,x]=True
  heads[box][mask & (np.arange(sy.start,sy.stop)[:,None]//16<root_y)]=True
  formations.append({'source_pixel_box':[sx.start,sy.start,sx.stop,sy.stop],'root_cells':roots})
 for y,x in zip(*np.where(plan=='O')):
  if any([int(x),int(y)] in q['root_cells'] for q in formations):continue
  p=label[y*16:y*16+16,x*16:x*16+16];blocked[y,x]=(p=='R').sum()>=80 or (p=='X').sum()>=32
 # These are low shoreline lips, not raised rock walls. The original
 # top-left and top-right B2F banks must touch Surf water directly.
 bank_cells=[]
 if key=='b2f':
  bank_cells=[(x,8) for x in [4,5,6,9,10,11,12,13,14]]+[(x,12) for x in range(25,29)]
  for x,y in bank_cells:plan[y,x]='B';blocked[y,x]=False
 (S/'reviewed-low-shores.json').write_text(json.dumps({'kind':'walkable low bank lip, original shore trim retained','cells':bank_cells,'purpose':'preserve Surf embark/disembark at the original north lake banks; raised rock masses remain blocked'},indent=2)+'\n')
 for x,y in c['ladders']:plan[y,x]='S';blocked[y,x]=False
 # One fixed Strength boulder exists in the original upper B1F corridor.
 if key=='b1f':blocked[12,8]=True;blocked[13,8]=True;plan[12,8]='K'
 (S/'hgss-material-grid.txt').write_text('\n'.join(''.join(row) for row in plan)+'\n');np.save(S/'hgss-pixel-materials.npy',label);np.save(S/'hgss-foot-blocked.npy',blocked);np.save(S/'hgss-overhead-rock-heads.npy',heads);Image.fromarray(clean).save(S/'clean-terrain.png');(S/'stalagmite-footprints.json').write_text(json.dumps(formations,indent=2)+'\n')
 origin=json.loads((S/'reference-origin.json').read_text());origin.update(native_grid=[W,H],original_dimensions=list(original.size),origin=[0,0],scale=1,padding='B2F bottom eight pixels padded with void' if key=='b2f' else None,basis='original visible-material trace; original DS warp graph separately registered to pictured branch ends',removed_sprite_boxes=removed,scope='pictured HGSS sections; off-image upper Alph transit chambers excluded',sha256=hashlib.sha256((S/'hgss-reference.png').read_bytes()).hexdigest());(S/'reference.json').write_text(json.dumps(origin,indent=2)+'\n')
 out=Image.new('RGB',(W*16+64,H*16+60),'white');out.paste(canvas,(44,30));d=ImageDraw.Draw(out)
 for x in range(W+1):d.line((44+x*16,30,44+x*16,30+H*16),fill='#777777');d.text((44+x*16,8),str(x),fill='black')
 for y in range(H+1):d.line((44,30+y*16,44+W*16,30+y*16),fill='#777777');d.text((4,30+y*16),str(y),fill='black')
 out.save(E/'numbered-hgss.png');print(key,'traced',W,H,'foreground formations',len(formations))
