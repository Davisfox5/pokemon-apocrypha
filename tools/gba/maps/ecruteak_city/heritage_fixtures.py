"""Finish fixture footings and wire the approved public-facing interactions."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'heritage';r=json.loads((E/'assembly.json').read_text());bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));mat=np.load(S/'material-grid.npy');solid=np.load(S/'solid.npy');above=np.load(S/'tree-closure/above.npy');art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (S/'masters').glob('*.png')}
# Retire old sign hitboxes, including the old extra blocked row below their feet.
oldsign=mat=='S';solid[oldsign]=False;mat[oldsign]=np.load(S/'ground-material-grid.npy')[oldsign];above[oldsign]=False
# Align two boards on the half-grid to a complete native cell. Repaint their
# local lawn/court backings and overlapping art in accepted order.
for p in r['placements']:
 if p['name']=='P12' and p['x'] in [600,696]:
  x,y=p['x'],p['y'];newx=x+8
  bg[y:y+32,x:newx+32]=art['court' if x==600 else 'grass'][(np.indices((32,40))[0]+y-16)%16,(np.indices((32,40))[1]+x-64)%16];fg[y:y+32,x:newx+32]=0;p['x']=newx
  for q in r['placements']:
   a=art[q['name']];h,w=a.shape[:2];l=max(x,q['x']);t=max(y,q['y']);rr=min(newx+32,q['x']+w);bb=min(y+32,q['y']+h)
   if l>=rr or t>=bb:continue
   v=a[t-q['y']:bb-q['y'],l-q['x']:rr-q['x']];m=v[...,3]>0;fg[t:bb,l:rr][m]=v[m]
for p in r['placements']:
 if p['name'] in ['P12','P13']:
  a=art[p['name']];ys,xs=np.where(a[...,3]>0);y=(p['y']+int(ys.max()))//16
  for x in range((p['x']+int(xs.min()))//16,(p['x']+int(xs.max()))//16+1):solid[y,x]=True;mat[y,x]='S';above[y,x]=False
for x in [21,30]:solid[7:14,x]=True;mat[7:14,x]='B'
# Extend the shrine's stone approach toward the public south-bank walk without
# changing any pond water/shore pixels or expanding the cleared woodland.
a=art['paving'];yy,xx=np.indices((32,32));bg[352:384,944:976]=a[(yy+352-16)%len(a),(xx+944-64)%a.shape[1]]
np.save(S/'solid.npy',solid);np.save(S/'material-grid.npy',mat);np.save(S/'tree-closure/above.npy',above);np.save(D/'above.npy',above)
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
# Read-only interactions. No NPC placements, campaign flags, invented rewards,
# unlocks, trading or persistent state. Shrine visitors/merchant are owner-placed later.
entries=[
 ('Restoration',52,27,17,'BURNED TOWER RESTORATION\\nThe city and the tower sages are\\lrepairing the old timberwork.\\pThe surviving beams are being\\nreinforced before rebuilding.\\lPlease keep clear of the scaffold.'),
 ('BellRecords',52,44,17,'BELL TOWER APPROACH\\nThe sages preserve the city\'s\\lrecords and sacred traditions.\\pVisitors seeking historical texts\\nshould ask at the archive.'),
 ('Archive',52,35,25,'ECRUTEAK HISTORICAL ARCHIVE\\nRecords of the towers and the\\lcity\'s traditions are kept here.\\pVisits to the reading room are\\narranged with the tower sages.'),
 ('WaysideShrine',51,35,4,'A small shrine tended by the city.\\nIts wooden panel depicts the\\ltwo towers above ECRUTEAK.\\pA place to pause and remember\\nthose who cared for them.'),
 ('OfferingCounter',51,32,6,'Neatly wrapped shrine offerings\\nrest on the wooden counter.\\pThe stall is unattended.\\nPlease leave the parcels here.'),
 ('HeritageBoard',51,38,6,'ECRUTEAK HERITAGE COURT\\nThe shrine and offering stall\\lkeep local traditions close\\lto everyday city life.'),
 ('PondShrine',52,59,18,'A quiet shrine beside the spring.\\nWater glimmers beneath its\\lweathered offering shelf.\\pThe path and lanterns have been\\nrenewed by the city\'s caretakers.'),
 ('PondBoard',52,61,22,'SPRING SHRINE\\nA quiet place for reflection.\\pPlease stay on the stone approach\\nand keep the spring clear.'),
 ('Gym',51,27,14,'ECRUTEAK CITY GYM\\nLEADER: WILL\\lA student of Psychic discipline\\land spiritual meditation.'),
 ('Theater',51,45,6,'ECRUTEAK DANCE THEATER\\nTraditional dance and music\\lcontinue here, passed from\\lone generation to the next.')]
for mid,name in [(51,'JohtoEcruteakCity'),(52,'JohtoEcruteakTempleDistrict')]:
 path=G/'data/maps'/name/'map.json';d=json.loads(path.read_text());assert not d['bg_events'];d['bg_events']=[dict(type='sign',x=x,y=y,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script=f'{name}_Heritage_{key}') for key,m,x,y,text in entries if m==mid];path.write_text(json.dumps(d,indent=2)+'\n');script=G/'data/maps'/name/'scripts.inc';s=script.read_text();assert '_Heritage_' not in s
 for key,m,x,y,text in entries:
  if m!=mid:continue
  label=f'{name}_Heritage_{key}';s+=f'\n{label}::\n    lockall\n    msgbox {label}_Text, MSGBOX_DEFAULT\n    releaseall\n    end\n\n{label}_Text:\n    .string "{text}$"\n'
 script.write_text(s)
(D/'interactions.json').write_text(json.dumps([dict(name=k,map=m,x=x,y=y,text=t) for k,m,x,y,t in entries],indent=2)+'\n')
# Check all new readings can be reached from the public city, not from a warp.
seen={(41,35)};todo=list(seen)
for x,y in todo:
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  xx,yy=x+dx,y+dy
  if 0<=xx<72 and 0<=yy<52 and not solid[yy,xx] and (xx,yy) not in seen:seen.add((xx,yy));todo.append((xx,yy))
for k,m,x,y,t in entries:
 gy=y+(27 if m==51 else 0);assert solid[gy,x],(k,'fixture body must block feet');assert (x,gy+1) in seen,(k,'front approach must be reachable')
print('Wired',len(entries),'read-only interactions;',len(seen),'reachable cells')
