"""Independent before/native audit and coordinate review for seven-map rollout."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.rollout import P,dump,save
from tiles import Tileset
from johto_service_buildings.build import decode
from route36.gate_surround.build import over

def scene(g,c):
 l=c['layout'];t=Tileset(g,c['secondary'],c['primary']);grid=np.fromfile(g/l['blockdata_filepath'],'<u2').reshape(l['height'],l['width']);layers,_,_,attrs=decode(t,grid);a=layers[0].copy();over(a,layers[1]);return a,grid,attrs,t

def main(base,game):
 configs=json.loads((P/'source/initial-inventory.json').read_text());reports=[];unique={};font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
 for c in configs:
  name=c['map'];old,og,oa,ot=scene(base,c);new,ng,na,nt=scene(game,c);save(P/'review'/f'{name}.png',new);save(P/'review'/f'{name}-baseline.png',old)
  pixels=np.any(old!=new,2);cells=pixels.reshape(ng.shape[0],16,ng.shape[1],16).any((1,3));flags=np.argwhere((og&0xfc00)!=(ng&0xfc00));attrs=np.argwhere(oa!=na)
  if name not in ['CherrygroveRoute29Approach','JohtoRoute31','VioletCity']:assert not len(flags) and not len(attrs),name
  for y,x in np.argwhere(cells):
   sl=np.s_[y*16:y*16+16,x*16:x*16+16];a,b=old[sl],new[sl];key=hashlib.sha256(a.tobytes()+b.tobytes()).hexdigest();v=unique.setdefault(key,dict(before=a,after=b,positions=[]));v['positions'].append([name,int(x),int(y)])
  oldevent=json.loads((base/'data/maps'/name/'map.json').read_text());event=json.loads((game/'data/maps'/name/'map.json').read_text());event_changes=[]
  for k in oldevent:
   if event[k]!=oldevent[k]:event_changes.append(k)
  assert not event_changes or (name=='VioletCity' and event_changes==['warp_events']),(name,event_changes)
  used=set((ng&1023).ravel())|set(np.fromfile(game/c['layout']['border_filepath'],'<u2')&1023);graphics=set(e&1023 for mid in used for e in nt.blocks[int(mid>=512)][mid%512]);assert max(graphics)<1008 and max(used)<1024
  reports.append(dict(map=name,changed_pixels=int(pixels.sum()),changed_cells=int(cells.sum()),collision_elevation_changes=[dict(x=int(x),y=int(y),before=int(og[y,x]&0xfc00),after=int(ng[y,x]&0xfc00)) for y,x in flags],behavior_changes=[dict(x=int(x),y=int(y),before=int(oa[y,x]),after=int(na[y,x])) for y,x in attrs],event_fields_changed=event_changes,live_graphics=len(graphics),live_metatiles=len(used)))
 vals=list(unique.values());ledger=[];per=48
 for page in range(math.ceil(len(vals)/per)):
  sheet=Image.new('RGB',(1200,850),'#202d37');d=ImageDraw.Draw(sheet);d.text((12,8),f'Johto rollout / native before | after / unique pairs {page*per+1}–{min(len(vals),(page+1)*per)}',fill='white',font=font)
  for j,v in enumerate(vals[page*per:(page+1)*per]):
   x=j%8*150+8;y=j//8*133+34;n,cx,cy=v['positions'][0];short={'NewBarkTown':'NB','CherrygroveRoute29Approach':'R29','CherrygroveCity':'CG','CherrygroveRoute30Approach':'R30','JohtoRoute31':'R31','VioletCity':'Violet','JohtoRoute36':'R36'}[n];label=f'{page*per+j+1}: {short} ({cx},{cy})';d.text((x,y),label[:23],fill='white',font=font)
   for k,im in enumerate([v['before'],v['after']]):sheet.paste(Image.fromarray(im).convert('RGB').resize((64,64),Image.Resampling.NEAREST),(x+k*67,y+23))
   d.text((x,y+91),f'{len(v["positions"])} map cells',fill='#b9c9d8',font=font);ledger.append(dict(pair=page*per+j+1,positions=v['positions']))
  sheet.save(P/'review'/f'cells-{page+1:02}.png')
 dump(P/'evidence/native-audit.json',dict(maps=reports,unique_pairs=len(vals)));dump(P/'evidence/cell-review.json',ledger)
 print([(r['map'],r['changed_cells'],len(r['collision_elevation_changes'])) for r in reports]);print('pairs',len(vals))
 # Whole maps at readable overview scale, with separate full-resolution exports.
 cards=[]
 for c in configs:
  im=Image.open(P/'review'/f'{c["map"]}.png').convert('RGB');im.thumbnail((650,680),Image.Resampling.NEAREST);card=Image.new('RGB',(674,im.height+40),'#202d37');ImageDraw.Draw(card).text((12,8),c['map'],font=font,fill='white');card.paste(im,(12,30));cards.append(card)
 for i in range(0,len(cards),2):
  cs=cards[i:i+2];out=Image.new('RGB',(1348,max(c.height for c in cs)),'#202d37')
  for j,c in enumerate(cs):out.paste(c,(j*674,0))
  out.save(P/'review'/f'overview-{i//2+1}.png')
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
