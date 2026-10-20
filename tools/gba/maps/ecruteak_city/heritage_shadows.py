"""Keep complete tree geometry; shade only tree feet tucked beneath landmark roofs.
The eight-pixel occlusion band uses the receiving roof's existing dark material
ramp, retaining every alpha pixel and shade ordering instead of dropping detail.
"""
from pathlib import Path
import json,numpy as np
from PIL import Image
S=Path(__file__).resolve().parents[4]/'gba/art/ecruteak-city/source';E=S.parent/'evidence';M=S/'masters';r=json.loads((E/'assembly.json').read_text());fg=np.array(Image.open(S/'foreground.png'));bg=np.array(Image.open(S/'background.png'));art={p.stem:np.array(Image.open(p)) for p in M.glob('*.png')};a=art['tree-autumn'];changes=[]
for n,ramp in [('tree-autumn-burned-shadow',[(24,32,32),(40,40,56),(64,64,88)]),('tree-autumn-bell-shadow',[(32,32,32),(64,16,0),(88,64,48)])]:
 v=a.copy();q=v[40:];m=q[...,3]>0;colors=sorted(set(map(tuple,q[m,:3])),key=lambda c:sum(map(int,c)))
 for i,c in enumerate(colors):q[np.all(q[...,:3]==c,2)&m,:3]=ramp[min(2,int(i*3/len(colors)))]
 assert np.array_equal(v[...,3],a[...,3]);art[n]=v;Image.fromarray(v).save(M/(n+'.png'))
for p in r['placements']:
 if p['name']=='tree-autumn' and (p['y']==64 and 352<=p['x']<=480):p['name']='tree-autumn-burned-shadow';changes.append([p['x'],p['y'],p['name']])
 if p['name']=='tree-autumn' and (p['y']==160 and 544<=p['x']<=704):p['name']='tree-autumn-bell-shadow';changes.append([p['x'],p['y'],p['name']])
for t in r['trees']:
 if t['name']=='tree-autumn' and t['y']==4 and 22<=t['x']<=30:t['name']='tree-autumn-burned-shadow'
 if t['name']=='tree-autumn' and t['y']==10 and 34<=t['x']<=44:t['name']='tree-autumn-bell-shadow'
owner=np.zeros(fg.shape[:2],np.int32)
for i,p in enumerate(r['placements']):
 a=art[p['name']];h,w=a.shape[:2];owner[p['y']:p['y']+h,p['x']:p['x']+w][a[...,3]>0]=i+1
for i,p in enumerate(r['placements']):
 if 'shadow' not in p['name']:continue
 a=art[p['name']];h,w=a.shape[:2];m=owner[p['y']:p['y']+h,p['x']:p['x']+w]==i+1;fg[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m]
Image.fromarray(fg).save(S/'foreground.png');(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');(S/'heritage/roof-shadow-adaptation.json').write_text(json.dumps(dict(affected_trees=changes,foot_band=[40,48],geometry_unchanged=True,texture_shade_order_preserved=True,reason='Complete tree feet sit under Burned/Bell roof shadow; reuse the receiving dark roof ramp at this occlusion band. Upper foliage remains identical to normal autumn master.'),indent=2)+'\n')
