"""Rebuild complete outdoor rock structures from explicit HGSS contours.
Contours, foreground and gameplay remain separate. No old rock face survives.
"""
from pathlib import Path
import json,sys,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import regional_rocks as rr
P=ROOT/'gba/art/johto-common/rocks/structure-rebuild'
CONFIGS=json.loads((P/'source/inputs.json').read_text())
SHAPES=json.loads((P/'source/structures.json').read_text())

def poly(points,shape):
 im=Image.new('1',(shape[1],shape[0]));ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=1);return np.array(im,bool)

def build(c):
 n=c['map'];t,g,l,b,e,attrs,old=rr.load(c,Path(c['baseline']));h,w=old.shape[:2];yy,xx=np.indices((h,w));cfg=SHAPES[n];ox,oy=cfg['offset'];rock=np.zeros_like(old);roles=np.zeros((h,w),np.uint8)
 # Clean 32px source top; native color ramp, not a sampled old wall mask.
 src=np.array(Image.open(ROOT/'gba/art/hgss-connections/references/route31-hgss.png').convert('RGB'))[32:64,944:976]
 bank=12 if n=='JohtoRoute31' else 2
 colors=np.array([col for col in t.pals[bank>=6][bank][1:] if col[0]>col[1]>col[2]],int)
 dist=((src[:,:,None,:].astype(int)-colors)**2).sum(3);core=np.concatenate([colors[dist.argmin(2)].astype(np.uint8),np.full((32,32,1),255,np.uint8)],2)
 Image.fromarray(core).save(P/'source'/f'{n}-top.png')
 def front(x0,y0,x1,y1):
  m=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1);height=y1-y0
  # One continuous drop: resample the complete 16px face to its measured height.
  rel=yy[m]-y0;iy=(rel*16//height).clip(0,15)
  rock[m]=(rr.R['R02'][iy,xx[m]%16] if n=='JohtoRoute32' else rr.FRONT[iy,xx[m]%32]);roles[m]=2
 def side(x0,y0,x1,y1,mirror):
  m=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1);width=x1-x0;rel=xx[m]-x0
  ix=(rel*16//width).clip(0,15)
  module=rr.R['R12'] if n=='JohtoRoute32' else rr.WEST;module=module[:,::-1] if mirror else module;rock[m]=module[yy[m]%len(module),ix];roles[m]=3 if mirror else 4
 for label,points in cfg['solids']:
  pts=[(x+ox,y+oy) for x,y in points];top=poly(pts,(h,w))
  period=16 if n=='JohtoRoute32' else 32
  rock[top]=core[yy[top]%period,xx[top]%period];roles[top]=1
  for (x0,y0),(x1,y1) in zip(pts,pts[1:]+pts[:1]):
   if y0==y1 and x1<x0:front(x1,y0,x0,y0+24)
   elif x0==x1 and y1>y0 and x0<w:side(x0-16,y0,x0,y1,True)
   elif x0==x1 and y1<y0 and x0>0:side(x0,y1,x0+16,y0,False)
 for label,kind,x0,y0,x1,y1,mirror in cfg['walls']:
  x0+=ox;x1+=ox;y0+=oy;y1+=oy
  if kind=='front':
   front(x0,y0,x1,y1)
   # Shared grass rim appears once at the raised ground, not between courses.
   if label not in ['stairs lower','west shoreline foot']:
    for x in range(max(0,x0),min(w,x1)):
     for dy in range(3):
      if y0+dy>=h:continue
      cap=rr.R['R01' if (x//16)%2==0 else 'R03'][dy,x%16]
      if cap[1]>cap[0]:rock[y0+dy,x]=cap
  else:
   side(x0,y0,x1,y1,mirror)
   for y in range(max(0,y0),min(h,y1)):
    for dx in range(3):
     cap=rr.R['R06' if (y//16)%2==0 else 'R07'][y%16,15-dx]
     x=x0+dx if mirror else x1-1-dx
     if 0<=x<w and cap[1]>cap[0]:rock[y,x]=cap
 if n=='JohtoRoute32':
  # Continue source-edge massifs through the native one-cell border.
  rock[:2016,:16]=rock[:2016,16:32];roles[:2016,:16]=roles[:2016,16:32]
  rock[:2016,496:]=rock[:2016,480:496];roles[:2016,496:]=roles[:2016,480:496]
  rock[2016:]=0;roles[2016:]=0
 # Determine removal from immutable pre-rollout terrain roles, never use that
 # mask to clip new geometry. The new outline comes exclusively from contours.
 orig=next(x for x in json.loads((rr.P/'source/inputs.json').read_text()) if x['map']==n)
 _,_,ol,ob,_,oa,original=rr.load(orig,Path(orig['baseline']))
 if n=='JohtoRoute31':
  removed=((ob==12)&(xx>=712)&(yy<216))|((ob==8)&(xx>=528)&((yy>=448)|((xx<560)&(yy>=48)))&(original[:,:,0]>original[:,:,1]))
  foreground=(ob==3)
  cave=(xx>=824)&(xx<864)&(yy>=184)&(yy<224)&(original[:,:,0]<50)&(original[:,:,1]<50)
 else:
  plan=np.load(rr.P/'source/route32/refined-plan.npy');scope=np.repeat(np.repeat(plan=='R',16,0),16,1);removed=(ob==2)&scope&(yy<2016)
  foreground=(ob==3)|((yy>=1056)&(yy<1120)) # complete trees and railway overpass
  cave=(xx>=216)&(xx<264)&(yy>=1856)&(yy<1904)&(original[:,:,0]<50)&(original[:,:,1]<50)
 # Treads and non-rock entrances are explicit independent pieces.
 stairs=(ob==8)&(original[:,:,0]==original[:,:,1])&(original[:,:,1]==original[:,:,2])
 if n=='JohtoRoute32':
  for x0,y0,x1,y1 in [(96,1392,144,1440),(128,952,176,992)]:
   stairs|=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&~removed
 foreground|=stairs|cave
 new=old.copy();clean=(ob==0).reshape(h//16,16,w//16,16).all((1,3));gy,gx=next((int(y),int(x)) for y,x in np.argwhere(clean) if np.all(original[y*16:y*16+16,x*16:x*16+16,1]>original[y*16:y*16+16,x*16:x*16+16,0]))
 grass=original[gy*16:gy*16+16,gx*16:gx*16+16];new[removed]=grass[yy[removed]%16,xx[removed]%16]
 if n=='JohtoRoute32':
  water=original[976:992,336:352];assert np.mean(water[:,:,2])>np.mean(water[:,:,0])+40
  sea=removed&(((yy>=960)&(yy<1248)&(xx>=184))|((yy>=1248)&(yy<1440)&(xx>=240)))
  new[sea]=water[yy[sea]%16,xx[sea]%16]
 visible=(rock[:,:,3]>0)&~foreground;new[visible]=rock[visible];new[foreground]=old[foreground]
 # Preserve live threshold and entrance pixels independently of rebuilt facade.
 if n=='JohtoRoute31':new[208:224,832:848]=old[208:224,832:848]
 else:new[1888:1904,224:256]=old[1888:1904,224:256]
 Image.fromarray(rock).save(P/'source'/f'{n}-structures.png');Image.fromarray(new).save(P/'review'/f'{n}-target.png');Image.fromarray(old).save(P/'review'/f'{n}-before.png');np.save(P/'source'/f'{n}-roles.npy',roles)
 np.save(P/'source'/f'{n}-removed.npy',removed)
 np.save(P/'source'/f'{n}-foreground.npy',foreground)
 changed=np.any(new!=old,2);cells=changed.reshape(h//16,16,w//16,16).any((1,3));print(n,'changed cells',cells.sum(),'exposed rock over open cells',int(((roles>0)&~foreground&np.repeat(np.repeat((g>>10&3)==0,16,0),16,1)).sum()),flush=True)
 return new

def install(c):
 # Reuse the verified lossless native compiler with a new immutable baseline.
 oldp=rr.P;rr.P=P
 try:rr.install(c,Path(c['engine']))
 finally:rr.P=oldp

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--map');ap.add_argument('--install',action='store_true');a=ap.parse_args()
 for c in CONFIGS:
  if a.map and c['map']!=a.map:continue
  build(c)
  if a.install:install(c)
