"""Bounded R02 rock-family installation on reconciled native layouts.
Never reruns map generators. Source images/placement ledgers remain editable.
"""
from pathlib import Path
import sys,json,hashlib,shutil,struct,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
from johto_service_buildings.build import decode
from route36.gate_surround.build import over
from johto_common.rollout import encode,split
P=ROOT/'gba/art/johto-common/rocks/regional-rollout'
R={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (ROOT/'gba/art/johto-common/rocks/r02-complete-tiles/source/tiles').glob('*.png')}
FRONT=np.concatenate([R['R02'],R['R04']],axis=1);WEST=np.concatenate([R['R12'],R['R11']],axis=0)
STONE=sorted(set(map(tuple,FRONT[:,:,:3].reshape(-1,3))),key=lambda c:sum(map(int,c)))
def save(name,a):Image.fromarray(a).save(P/'review'/name)
def load(c,game):
 l=c['layout'];t=Tileset(game,c['secondary'],c['primary']);g=np.fromfile(game/l['blockdata_filepath'],'<u2').reshape(l['height'],l['width']);layers,banks,es,attrs=decode(t,g);im=layers[0].copy();over(im,layers[1]);return t,g,layers,banks,es,attrs,im

def target(c):
 name=c['map'];t,g,layers,banks,es,attrs,old=load(c,Path(c['baseline']));new=old.copy();h,w=old.shape[:2];yy,xx=np.indices((h,w));ledger=[];protected=np.zeros((h,w),bool)
 def stamp(x,y,n,mirror=False,keep=None):
  a=R[n][:,::-1] if mirror else R[n];sl=np.s_[y:y+16,x:x+16];mask=np.ones((16,16),bool) if keep is None else ~keep
  new[sl][mask]=a[mask];ledger.append(dict(x=x,y=y,tile=n,mirror=mirror,kind='complete native tile',preserved_pixels=int((~mask).sum())))
 def recolor(mask):
  src=sorted(set(map(tuple,old[mask,:3])),key=lambda c:sum(map(int,c)))
  for i,col in enumerate(src):new[mask&np.all(old[:,:,:3]==col,2),:3]=STONE[round(i*(len(STONE)-1)/max(1,len(src)-1))]
 def front_rect(x0,y0,x1,y1,mask):
  region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&mask
  # Fixed 16px native body at its existing baseline; no vertical scaling.
  new[region]=FRONT[(yy[region]-y0)%16,(xx[region]-x0)%32];ledger.append(dict(box=[x0,y0,x1,y1],kind='front',master=['R02','R04']))
 def side_rect(x0,y0,x1,y1,mask,mirror=False):
  region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&mask;a=WEST[:,::-1] if mirror else WEST
  new[region]=a[(yy[region]-y0)%32,(xx[region]-x0)%16];ledger.append(dict(box=[x0,y0,x1,y1],kind='side',master=['R12','R11'],mirror=mirror))
 if name in ['CherrygroveCity','CherrygroveRoute29Approach']:
  row,start,end=(8,0,38) if name=='CherrygroveCity' else (31,10,98)
  # Coast has a 16px main front, existing 8px upper bevel and existing foot.
  # Retain water/sand/overlook silhouettes; no grass is placed on the shore.
  rock=(banks==2)&(old[:,:,0].astype(int)>old[:,:,1]+12)&(old[:,:,1].astype(int)>old[:,:,2]+10)
  scope=(yy>=(row-1)*16)&(yy<(row+2)*16)&(xx>=start*16)&(xx<end*16)
  recolor(rock&scope)
  for x in range(start,end):
   sl=np.s_[row*16:(row+1)*16,x*16:(x+1)*16]
   if rock[sl].sum()>120:stamp(x*16,row*16,'R02' if x%2==0 else 'R04',keep=~rock[sl])
  # Lower exposed course shares the face; retain the bottom shore/foot silhouette.
  for x in range(start,end):
   sl=np.s_[(row+1)*16:(row+2)*16,x*16:(x+1)*16];m=rock[sl].copy();m[8:]=False
   if m.any():stamp(x*16,(row+1)*16,'R02' if x%2==0 else 'R04',keep=~m)
  # One shared jagged grass-to-stone cap profile, authored into the full tile.
  for x in range(start,end):
   sl=np.s_[(row-1)*16:row*16,x*16:(x+1)*16];patch=old[sl];m=rock[sl]
   if m.sum()<20:continue
   a=new[sl];top=min(np.where(m)[0]);profile=R['R01' if x%2==0 else 'R03']
   for iy in range(min(8,16-top)):
    eligible=m[top+iy]|((banks[sl][top+iy]==0)&(patch[top+iy,:,1]>patch[top+iy,:,0]))
    a[top+iy,eligible]=profile[iy,eligible]
   ledger.append(dict(x=x,y=row-1,kind='existing coast bevel with shared 1-3px cap',profile='R01/R03',existing_top=top))
  if name=='CherrygroveRoute29Approach':
   # Four inland side runs were omitted by the coast-only rollout.
   shape=json.loads((ROOT/'gba/art/johto-common/rocks/hgss-placement-audit/source/route29-hgss-blocks/structures.json').read_text())
   for (cx,cy,cw,ch),mirror in zip(shape['walls'],[True,False,False,True]):
    for iy in range(cy,cy+ch):
     sl=np.s_[iy*16:iy*16+16,cx*16:cx*16+16];m=(banks[sl]==8)&(old[sl][:,:,0]>old[sl][:,:,1])
     stamp(cx*16,iy*16,'R06' if iy%2==0 else 'R07',mirror,keep=~m)
   # Low hop ledges keep their original transparent silhouette and behavior.
   low=np.repeat(np.repeat((attrs&255)==0x3b,16,0),16,1)&(banks==8)
   recolor(low)
 elif name=='CherrygroveRoute30Approach':
  # Emerald terrain is bank8; gray stairs and one-way ledges are excluded.
  rock=(banks==8)&(old[:,:,0]>old[:,:,1])
  wallcells=rock.reshape(h//16,16,w//16,16).sum((1,3))>12;wallcells&=~np.isin(attrs&255,[0x3b,0x38,0x39,0x3a,0x49,0x4a,0x4b,0x4c,0x4d,0x4e]);
  # Keep stair treads, but replace the colored rock shoulders in the same cell.
  plan=np.load(ROOT/'gba/art/route30-hgss-blocks/source/plan.npy')
  remnants=np.repeat(np.repeat(plan=='R',16,0),16,1)&rock
  # These cells were explicitly generated as forest fillers, not HGSS cliffs.
  clean=(banks==0).reshape(h//16,16,w//16,16).all((1,3))
  candidates=[]
  for gy,gx in np.argwhere(clean):
   a=old[gy*16:gy*16+16,gx*16:gx*16+16]
   if np.all(a[:,:,1]>a[:,:,0]):candidates.append(a)
  from collections import Counter
  key=Counter(a.tobytes() for a in candidates).most_common(1)[0][0];grass=np.frombuffer(key,np.uint8).reshape(16,16,4)
  new[remnants]=grass[yy[remnants]%16,xx[remnants]%16];wallcells[plan=='R']=False
  ledger.append(dict(kind='remove non-HGSS forest rock fillers',cells=np.argwhere(plan=='R')[:,::-1].tolist(),pixels=int(remnants.sum()),collision='existing forest footprint preserved'))
  low=np.repeat(np.repeat((attrs&255)==0x3b,16,0),16,1)&(banks==8);recolor(low)
  for cy,cx in np.argwhere(wallcells):
   sl=np.s_[cy*16:cy*16+16,cx*16:cx*16+16];keep=~(rock[sl]|((banks[sl]==0)&(old[sl][:,:,1]>old[sl][:,:,0])))
   if cx==15 and 6<=cy<28:n='R06' if cy%2==0 else 'R07';mirror=False
   elif cx in (3,4,5) and cy>=36:n=('R06' if cy%2==0 else 'R07') if cx in (3,4) else ('R12' if cy%2==0 else 'R11');mirror=True
   elif cx in (33,34) and cy<46:n='R06' if cy%2==0 else 'R07';mirror=False
   else:n=('R02' if cx%2==0 else 'R04') if cy>0 and wallcells[cy-1,cx] else ('R01' if cx%2==0 else 'R03');mirror=False
   stamp(cx*16,cy*16,n,mirror,keep)
  # Coherent outside turn from lower separator to southern terrace.
  for cx,cy,mir in [(4,63,True),(34,0,False)]:
   if wallcells[cy,cx]:
    sl=np.s_[cy*16:cy*16+16,cx*16:cx*16+16];stamp(cx*16,cy*16,'R16',mir,keep=~(rock[sl]|(banks[sl]==0)))
 elif name=='JohtoRoute31':
  rock=(banks==8)&(old[:,:,0]>old[:,:,1]);wc=rock.reshape(h//16,16,w//16,16).sum((1,3))>12;wc&=~np.isin(attrs&255,[0x3b,0x49,0x4a,0x4b,0x4c,0x4d,0x4e])
  low=np.repeat(np.repeat((attrs&255)==0x3b,16,0),16,1)&(banks==8);recolor(low)
  for cy,cx in np.argwhere(wc):
   sl=np.s_[cy*16:cy*16+16,cx*16:cx*16+16];keep=~(rock[sl]|((banks[sl]==0)&(old[sl][:,:,1]>old[sl][:,:,0])))
   if cx in (33,34) and cy<28:n=('R06' if cy%2==0 else 'R07') if cx==34 else ('R12' if cy%2==0 else 'R11')
   else:n=('R01' if cx%2==0 else 'R03') if cy==28 else ('R02' if cx%2==0 else 'R04')
   stamp(cx*16,cy*16,n,keep=keep)
  mountain=(banks==12)&(old[:,:,0].astype(int)>old[:,:,1]+12)&(old[:,:,1].astype(int)>old[:,:,2]+10)&(xx>=712)&(yy<216)
  # Receiving profiles are measured on the retained HGSS-derived mountain.
  # Never change the black arch, threshold, sign, plateau or tree silhouettes.
  profiles=[(736,64,784,80),(896,128,1008,144),(848,152,1008,168),(752,176,1008,192),(752,200,1008,216)]
  for x0,y0,x1,y1 in profiles:front_rect(x0,y0,x1,y1,mountain)
  for box in [(736,24,752,64),(752,80,776,176),(816,16,840,120),(880,0,896,72),(896,96,912,128)]:side_rect(*box,mountain)
  # Preserve the existing stone plateau/bevel, as on Route32.
  # Recoloring those top-plane pixels created an artificial horizontal band.
 elif name=='JohtoRoute32':
  p=np.load(P/'source/route32/refined-plan.npy');mask=np.repeat(np.repeat(p=='R',16,0),16,1)
  stone=(banks==2)&mask
  # Explicit continuous source planes replace the incomplete mask-only pass.
  planes=json.loads((ROOT/'gba/art/johto-common/rocks/hgss-placement-audit/source/route32-planes.json').read_text())
  front=np.zeros((h,w),bool);left=front.copy();right=front.copy()
  for role in ['sides','fronts']:
   for plane in planes[role]:
    x0,y0,x1,y1=[v+16 for v in plane['box']];region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&stone
    if role=='fronts':
     iy=(yy[region]-y0)%16;new[region]=FRONT[iy,xx[region]%32];front|=region
    else:
     ix=(xx[region]-x0)%16;module=WEST[:,::-1] if plane['mirror'] else WEST;new[region]=module[yy[region]%32,ix];(right if plane['mirror'] else left)[region]=True
    ledger.append(dict(kind='registered HGSS plane',role=role,**plane,native_offset=[16,16],pixels=int(region.sum())))
  # Reuse one existing 32px plateau core on unexposed stone tops.
  # This reserves native graphics for complete faces and corners.
  topmask=stone&~(front|left|right);core=old[304:336,16:48];assert (banks[304:336,16:48]==2).all()
  new[topmask]=core[yy[topmask]%32,xx[topmask]%32]
  # Inferred front/side overlaps are receiving turns, preserve native silhouettes.
  # Only exposed native rock changes; the independent foreground masks stay exact.
  ledger.append(dict(kind='registered native face/side masks',source='explicit registered HGSS continuous planes',front_pixels=int(front.sum()),west_pixels=int(left.sum()),east_pixels=int(right.sum()),master=['R02','R04','R11','R12'],plateau_treatment='existing 32px core reused within original rock-top silhouette'))
  np.save(P/'source/route32/applied-face-mask.npy',front|left|right)
 else:raise ValueError(name)
 change=np.any(new!=old,2);save(name+'-target.png',new);save(name+'-change-mask.png',(change*255).astype(np.uint8));(P/'source'/(name+'-placements.json')).write_text(json.dumps(ledger,indent=2,default=int)+'\n');print(name,'changed',change.sum(),'cells',change.reshape(h//16,16,w//16,16).any((1,3)).sum(),flush=True)
 return new

def install(c,game):
 t,g,layers,banks,es,attrs,old=load(c,game)
 bt,bg,bl,bb,be,ba,baseline=load(c,Path(c['baseline']))
 assert np.array_equal(g,bg) and np.array_equal(old,baseline),('source changed',c['map'])
 new=np.array(Image.open(P/'review'/(c['map']+'-target.png')).convert('RGBA'));changed=np.any(new!=old,2)
 # Only entries not used by any existing map/border pixel may gain colors.
 used_indices={i:{0} for i in range(13)};border=np.fromfile(game/c['layout']['border_filepath'],'<u2')&1023
 for mid in set((g&1023).ravel())|set(border):
  for en in t.blocks[int(mid>=512)][int(mid)%512]:
   tid=en&1023;used_indices[en>>12].update(t.tiles[int(tid>=512)][tid%512])
 t.allow_primary_palettes=c['primary'] in ['johto_cherrygrove','route32','route32_primary']
 t.free_slots={i:[j for j in range(1,16) if j not in used_indices[i]] if i>=6 or t.allow_primary_palettes else [] for i in range(13)}
 t.free_banks=[i for i in range(6,13) if len(t.free_slots[i])==15];t.new_banks=set();t.background=old.copy();t.sort_complexity=True
 if c['primary'] in ['johto_cherrygrove','route32']:
  master=set(STONE)|{(104,200,152),(96,192,144)};missing=master-set(t.pals[0][5][1:]);assert len(missing)<=len(t.free_slots[5])
  for col in sorted(missing):t.pals[0][5][t.free_slots[5].pop(0)]=col
  t.new_banks.add(5)
 # Split may reuse an existing color in a formerly unused slot. Keep one
 # copy available throughout allocation (notably opaque black at cave mouths).
 target_colors=set(map(tuple,new[:,:,:3].reshape(-1,3)))
 for bank in range(13):
  pal=t.pals[bank>=6][bank]
  for col in target_colors:
   ids=[i for i in range(1,16) if tuple(pal[i])==col]
   if ids and all(i in t.free_slots[bank] for i in ids):t.free_slots[bank].remove(ids[0])
 fg=(banks==3)|((layers[1][:,:,3]>0)&~changed)
 split(new,layers,changed,t,fg)
 assert np.array_equal(new,np.array(Image.open(P/'review'/(c['map']+'-target.png')).convert('RGBA'))), 'No palette approximation permitted'
 if c['primary'] in ['johto_cherrygrove','route32']:
  from johto_common.rock_private_pack import pack
  report=pack(game,c,t,g,attrs,layers,new,changed)
 else:report=encode(game,c,t,g,attrs,layers,new,changed)
 report.update(source_commit=c['commit'],layout_sha256=hashlib.sha256((Path(c['baseline'])/c['layout']['blockdata_filepath']).read_bytes()).hexdigest(),changed_pixels=int(changed.sum()),new_palette_banks=sorted(t.new_banks),scope='native cliff art only; collision/elevation/behavior unchanged')
 out=P/'evidence';out.mkdir(exist_ok=True);(out/(c['map']+'-native.json')).write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',type=Path);p.add_argument('--map');a=p.parse_args()
 for c in json.loads((P/'source/inputs.json').read_text()):
  if a.map and a.map!=c['map']:continue
  if a.engine:install(c,a.engine)
  else:target(c)
