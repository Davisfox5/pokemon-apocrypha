"""Install approved grass adjacency family and cleaned scenery at existing anchors."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.rollout import P,save,dump,split,encode
from johto_common.trees import rgba
from johto_service_buildings.build import decode
from route36.gate_surround.build import over
from tiles import Tileset
from claude_cherrygrove import ground
CAT=ROOT/'gba/art/johto-common/scenery'
def reserve(t,art):
 colors=set(map(tuple,art[art[:,:,3]>0,:3]));assert len(colors)<=15
 if any(colors<=set(map(tuple,t.pals[b>=6][b][1:])) for b in range(13)):return
 assert t.free_banks,('no free palette for approved master',colors)
 b=t.free_banks.pop(0);t.pals[1][b]=[(0,0,0)]+sorted(colors)+[(0,0,0)]*(15-len(colors));t.new_banks.add(b);t.free_slots[b]=list(range(len(colors)+1,16))
def setup(t,grid,es,border):
 used={i:{0} for i in range(13)};banks=set()
 for mid in set((grid&1023).ravel())|set(border):
  for e in t.blocks[int(mid>=512)][mid%512]:
   tid=e&1023;used[e>>12].update(t.tiles[int(tid>=512)][tid%512]);banks.add(e>>12)
 t.free_banks=[b for b in range(6,13) if b not in banks];t.new_banks=set();t.free_slots={b:[i for i in range(1,16) if i not in used[b]] for b in range(13)}
def main(game,maps=None):
 configs=json.loads((P/'source/initial-inventory.json').read_text());catalog={a['id']:a for a in json.loads((CAT/'catalog.json').read_text())['assets']};placements=json.loads((P/'source/prop-placements.json').read_text());reports=[]
 for config in configs:
  name=config['map']
  if maps and name not in maps:continue
  t=Tileset(game,config['secondary'],config['primary']);l=config['layout'];grid=np.fromfile(game/l['blockdata_filepath'],'<u2').reshape(l['height'],l['width']);layers,banks,es,attrs=decode(t,grid);setup(t,grid,es,np.fromfile(game/l['border_filepath'],'<u2')&1023)
  before=layers[0].copy();over(before,layers[1]);target=before.copy();fore=np.zeros_like(before);h,w=grid.shape
  raw=ground.textures()[ground.GRASS];pal=np.array(t.pals[1][6][1:] if name=='JohtoRoute36' else t.pals[0][0][1:],int);tex=pal[np.square(raw[:,:,None,:].astype(int)-pal).sum(3).argmin(2)];ys,xs=np.indices(before.shape[:2]);bg=np.dstack([tex[ys%tex.shape[0],xs%tex.shape[1]],np.full(before.shape[:2],255,np.uint8)]);t.background=bg
  records=[]
  tall=(attrs&255)==2
  if tall.any():
   grass={i:rgba(CAT/'source'/f'G{i:02}.png') for i in range(16)};reserve(t,grass[15])
   for y,x in np.argwhere(tall):
    bits=''.join(str(int(0<=yy<h and 0<=xx<w and tall[yy,xx])) for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]);idx=int(bits,2);sl=np.s_[y*16:y*16+16,x*16:x*16+16];target[sl]=bg[sl];over(target,grass[idx],x*16,y*16);over(fore,grass[idx],x*16,y*16);records.append(dict(asset=f'G{idx:02}',x=int(x*16),y=int(y*16),neighbors=bits))
  # Low Emerald ledges retain their native silhouette and jump behavior.
  for id in ['L11','L12','L13']:
   inp=rgba(CAT/'inputs'/f'{id}.png');art=rgba(CAT/'source'/f'{id}.png');mask=inp[:,:,3]>0;removed=mask&(art[:,:,3]==0)
   if not removed.any():continue
   for y,x in np.ndindex(h,w):
    sl=np.s_[y*16:y*16+16,x*16:x*16+16];a=before[sl]
    if np.all(a[:,:,:3]==inp[:,:,:3],2)[mask].mean()<.99:continue
    target[sl][removed]=bg[sl][removed];over(fore,art,x*16,y*16);records.append(dict(asset=id,x=x*16,y=y*16))
  for id,positions in placements[name].items():
   inp=rgba(CAT/catalog[id]['input']);art=rgba(CAT/catalog[id]['master']);ah,aw=art.shape[:2];removed=(inp[:,:,3]>0)&(art[:,:,3]==0)
   for x,y in positions:
    sl=np.s_[y:y+ah,x:x+aw];a=target[sl];b=before[sl]
    # Background removal only changes obsolete non-terrain pixels. Existing
    # destination grass, paving and animated water stay exactly as installed.
    if id=='P06':a[removed&np.all(b[:,:,:3]==(132,132,132),2)]=bg[sl][removed&np.all(b[:,:,:3]==(132,132,132),2)]
    if id in ['P03','P04']:
     # These rails are surrounded by the existing bridge stone; use adjacent
     # pixels at the same height, rather than importing cyan donor water.
     m=removed&np.all(b[:,:,:3]==(56,184,232),2)
     for yy,xx in np.argwhere(m):
      candidates=[b[yy,k] for k in range(aw) if b[yy,k,3] and tuple(b[yy,k,:3])!=(56,184,232)]
      if candidates:a[yy,xx]=candidates[0]
    over(target,art,x,y);over(fore,art,x,y);records.append(dict(asset=id,x=x,y=y))
  # Restore any tree crown crossing a grass boundary; the object layer takes
  # precedence over new low foliage without changing its existing footprint.
  treecolors=set()
  for id in ['T01','T02']:
   a=rgba(ROOT/f'gba/art/johto-common/trees/source/{id}.png');treecolors.update(map(tuple,a[a[:,:,3]>0,:3]))
  crowns=np.any([np.all(before[:,:,:3]==c,2) for c in treecolors],axis=0);target[crowns]=before[crowns];fore[crowns]=before[crowns]
  changed=np.any(target!=before,2);split(target,layers,changed,t,fore[:,:,3]>0);info=encode(game,config,t,grid,attrs,layers,target,changed) if changed.any() else dict(changed_cells=0,native_pixel_errors=0,behavior_errors=0,collision_elevation_errors=0)
  save(P/'review'/f'{name}-scenery-before.png',before);save(P/'review'/f'{name}.png',target);dump(P/'source'/f'{name}-scenery.json',records);info.update(map=name,tall_grass_cells=int(tall.sum()),recorded_placements=len(records),changed_pixels=int(changed.sum()));reports.append(info);print(info,flush=True)
 old=json.loads((P/'evidence/scenery.json').read_text()) if maps and (P/'evidence/scenery.json').exists() else []
 dump(P/'evidence/scenery.json',[v for v in old if v['map'] not in {r['map'] for r in reports}]+reports)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--maps',nargs='+');a=p.parse_args();main(a.engine,a.maps)
