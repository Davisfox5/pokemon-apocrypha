"""Narrow follow-up to reviewed d7a478: southeast rim, Theater sign and ridge trim."""
from pathlib import Path
import sys,json,subprocess
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,distance_transform_edt
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';M=S/'masters';D=S/'court-refinement';W,H=72,52
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='d7a4789d2b9772665a78dfab8b52bdd38e169350'
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True).strip(),'Preserve uncommitted native edits.'
bg=np.array(Image.open(S/'background.png').convert('RGBA'));fg=np.array(Image.open(S/'foreground.png').convert('RGBA'));solid=np.load(S/'solid.npy');mat=np.load(S/'material-grid.npy');ground=np.load(S/'ground-material-grid.npy');beh=np.load(S/'behaviors.npy');r=json.loads((E/'assembly.json').read_text());ref=np.array(Image.open(S/'hgss-reference.png'));art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')};above=np.zeros((H,W),bool);Y,X=np.indices(bg.shape[:2]);oldart={n:art[n].copy() for n in ['dance-theater','bell-entrance']};prior_bg=bg.copy()
for n,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 t=Tileset(G,bank,bank);g=np.fromfile(G/'data/layouts'/n/'map.bin','<u2').reshape(h,W)
 for y,x in np.ndindex(h,W):mid=int(g[y,x]&1023);above[y+y0,x]=(t.attrs[mid>=512][mid%512]&0x3000)==0

def rect(x,y,w,h):
 a=np.zeros(bg.shape[:2],bool);a[y+16:y+16+h,x+64:x+64+w]=True;return a

def texture(m,n):
 a=art[n];bg[m]=a[(Y[m]-16)%len(a),(X[m]-64)%a.shape[1]]

def court(x,y,w,h,door):
 texture(rect(x-8,y-8,w+16,h+16),'paving');m=rect(x,y,w,h)
 if door is not None:m &=~rect(door-16,y+h-16,32,24)
 d=distance_transform_edt(m);out=binary_dilation(m,iterations=2)&~m;bg[out,:3]=[128,136,120];texture(m,'court');bg[m&(d<=3),:3]=[120,120,112];band=m&(d>3)&(d<=8);bg[band,:3]=[152,160,128];bg[band&(((X-64)%16>=12)|((Y-16)%16>=12)),:3]=[136,144,128]
 for yy,xx in np.ndindex(H,W):
  if m[yy*16:yy*16+16,xx*16:xx*16+16].mean()>.3:
   ground[yy,xx]='C'
   if mat[yy,xx] in ['C','P']:mat[yy,xx]='C'
court(784,560,128,104,None);court(624,440,128,96,688)
for c in r['courts']:
 if c['court']=='southeast':c['recess_center']=None;c['recess_depth']=0;c['finding']='HGSS plain-front house has a straight southern rim; remove inherited false recess.'
a=art['dance-theater'].copy()
for y in range(72,104):
 for x in range(18,40):
  if y>=96:a[y,x]=0
  else:a[y,x]=a[y,127-x]
art['dance-theater']=a
# Gold roof ridges are material-specific. Preserve their original bar and grain
# coordinates rather than letting the large blue/red roofs erase their hue.
gold=np.array([(104,88,32),(144,128,56),(184,168,80)],np.uint8)
for n,box,bounds in [('dance-theater',(624,424,752,536),(34,4,98,17)),('bell-entrance',(480,184,672,280),(8,18,64,30))]:
 a=art[n].copy();raw=ref[box[1]:box[3],box[0]:box[2]];x0,y0,x1,y1=bounds
 for y in range(y0,y1):
  for x in range(x0,x1):
   rr,gg,bb=map(int,raw[y,x])
   if a[y,x,3] and rr>gg*.95 and gg>bb*1.8 and gg>55:a[y,x,:3]=gold[np.argmin(np.sum((gold.astype(int)-raw[y,x].astype(int))**2,1))]
 if n=='dance-theater':
  for old,new in [([32,72,152],[32,72,136]),([48,80,144],[48,96,152]),([88,112,144],[88,104,112])]:a[(a[...,3]>0)&np.all(a[...,:3]==old,2),:3]=new
 art[n]=a;Image.fromarray(a).save(M/(n+'.png'))
# Repair only these two foreground rectangles, then repaint later overlapping
# objects in their existing order. Other facade layer splits are untouched.
for n in ['dance-theater','bell-entrance']:
 p=next(p for p in r['placements'] if p['name']==n);x,y=p['x'],p['y'];h,w=oldart[n].shape[:2];fg[y:y+h,x:x+w]=0
 # Ground under removed board fragments was compacted while fully hidden.
 if n=='dance-theater':texture(rect(642,520,22,8),'court')
 for q in r['placements']:
  a=art[q['name']];hh,ww=a.shape[:2];l=max(x,q['x']);t=max(y,q['y']);rr=min(x+w,q['x']+ww);bb=min(y+h,q['y']+hh)
  if l>=rr or t>=bb:continue
  v=a[t-q['y']:bb-q['y'],l-q['x']:rr-q['x']];m=v[...,3]>0;fg[t:bb,l:rr][m]=v[m]
# The receiving court must not erase architectural pixels encoded on the
# background under an overlapping canopy. Preserve the original opaque join.
p=next(p for p in r['placements'] if p['name']=='house-southeast');a=art[p['name']]
for y in range(p['y']//8*8,(p['y']+len(a)+7)//8*8,8):
 for x in range(p['x']//8*8,(p['x']+a.shape[1]+7)//8*8,8):
  m=np.zeros((8,8),bool);l=max(x,p['x']);t=max(y,p['y']);rr=min(x+8,p['x']+a.shape[1]);bb=min(y+8,p['y']+len(a))
  if l>=rr or t>=bb:continue
  m[t-y:bb-y,l-x:rr-x]=a[t-p['y']:bb-p['y'],l-p['x']:rr-p['x'],3]>0;f=fg[y:y+8,x:x+8,3]>0
  if (m&~f).any() and np.all(m|f):bg[y:y+8,x:x+8]=prior_bg[y:y+8,x:x+8]
# Compact only invisible backings, preserving all visible source pixels.
for yy,xx in np.ndindex(H*2,W*2):
 sl=np.s_[yy*8:yy*8+8,xx*8:xx*8+8]
 if np.all(fg[sl][...,3]==255):bg[sl]=art['grass'][Y[sl]%16,X[sl]%16]
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
for n,a in [('ground-material-grid',ground),('material-grid',mat)]:np.save(S/(n+'.npy'),a)
comp=bg.copy();mask=fg[...,3]>0;comp[mask]=fg[mask];Image.fromarray(comp).save(D/'preview.png')
(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');(D/'finish-report.json').write_text(json.dumps(dict(baseline_source='d7a4789d2b9772665a78dfab8b52bdd38e169350',fixes=['Southeast house rim is straight as in HGSS, without an invented approach recess.','Theater embedded board fragment removed and occluded wall recovered by symmetry; one freestanding sign remains.','Theater and annex gold ridge accents restored at original source coordinates.'],collision_changes=0,tree_changes=0),indent=2)+'\n')
from compile_refinement import compile_native
compile_native(G,Path(sys.argv[2]),S,E,bg,fg,solid,beh,above,r)
