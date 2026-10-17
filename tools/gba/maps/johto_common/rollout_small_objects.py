"""Replace old apricorn conversions and New Bark mailboxes at retained anchors."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.rollout import P,save,dump,split,encode
from johto_common.rollout_scenery import setup,reserve,CAT
from johto_common.trees import rgba
from johto_service_buildings.build import decode
from route36.gate_surround.build import over
from tiles import Tileset
from claude_cherrygrove import ground
SPECS={
 'CherrygroveRoute29Approach':[('T03',(320,176,48,48),(330,200),'grass')],
 'JohtoRoute31':[('T03',(320,192,48,48),(330,216),'path')],
 'CherrygroveRoute30Approach':[('T04',(336,64,16,32),(327,64),'grass'),('T03',(192,816,16,32),(183,820),'grass')],
 'NewBarkTown':[('P10',(144,80,16,32),(144,80),'grass'),('P10',(336,256,16,32),(336,256),'grass')]
}
def main(game):
 reports=[]
 for config in json.loads((P/'source/initial-inventory.json').read_text()):
  name=config['map']
  if name not in SPECS:continue
  t=Tileset(game,config['secondary'],config['primary']);l=config['layout'];grid=np.fromfile(game/l['blockdata_filepath'],'<u2').reshape(l['height'],l['width']);layers,banks,es,attrs=decode(t,grid);setup(t,grid,es,np.fromfile(game/l['border_filepath'],'<u2')&1023)
  before=layers[0].copy();over(before,layers[1]);target=before.copy();fore=np.zeros_like(before);pal=np.array(t.pals[0][0][1:],int);ys,xs=np.indices(before.shape[:2]);background={}
  for mat,key in [(ground.GRASS,'grass'),(ground.PATH,'path')]:
   raw=ground.textures()[mat];tex=pal[np.square(raw[:,:,None,:].astype(int)-pal).sum(3).argmin(2)];background[key]=np.dstack([tex[ys%tex.shape[0],xs%tex.shape[1]],np.full(before.shape[:2],255,np.uint8)])
  t.background=background['grass'];records=[];treecolors=set()
  for id in ['T01','T02']:
   a=rgba(ROOT/f'gba/art/johto-common/trees/source/{id}.png');treecolors.update(map(tuple,a[a[:,:,3]>0,:3]))
  for id,(x,y,w,h),(ax,ay),material in SPECS[name]:
   art=rgba(ROOT/f'gba/art/johto-common/trees/source/{id}.png') if id.startswith('T') else rgba(CAT/'source'/f'{id}.idx.png');reserve(t,art)
   sl=np.s_[y:y+h,x:x+w];a=before[sl];terrain=np.any([np.all(a[:,:,:3]==c,2) for c in t.pals[0][0][1:] if c!=(64,136,104)],axis=0)
   preserve=np.any([np.all(a[:,:,:3]==c,2) for c in treecolors],axis=0) if id.startswith('P') else np.zeros((h,w),bool)
   remove=~terrain&~preserve;target[sl][remove]=background[material][sl][remove]
   over(target,art,ax,ay);over(fore,art,ax,ay);records.append(dict(master=id,old_bounds=[x,y,w,h],origin=[ax,ay],background=material))
  changed=np.any(target!=before,2);split(target,layers,changed,t,fore[:,:,3]>0);info=encode(game,config,t,grid,attrs,layers,target,changed);info.update(map=name,objects=records)
  save(P/'review'/f'{name}-objects-before.png',before);save(P/'review'/f'{name}.png',target)
  sheet=Image.new('RGB',(512,len(records)*192),'#25323b')
  for i,r in enumerate(records):
   x,y,w,h=r['old_bounds'];box=(max(0,x-16),max(0,y-16),min(before.shape[1],x+w+16),min(before.shape[0],y+h+16))
   for j,a in enumerate((before,target)):sheet.paste(Image.fromarray(a).crop(box).resize(((box[2]-box[0])*2,(box[3]-box[1])*2),Image.Resampling.NEAREST),(j*256,i*192))
  sheet.save(P/'review'/f'{name}-objects.png');reports.append(info);print(info,flush=True)
 dump(P/'evidence/small-objects.json',reports)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);a=p.parse_args();main(a.engine)
