"""Reuse approved front/side gate masters, keeping the existing destinations."""
from pathlib import Path
import argparse,json,sys,subprocess
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.rollout import P,save,dump,split,encode
from johto_common.rollout_scenery import setup,reserve
from johto_common.trees import rgba
from johto_service_buildings.build import decode
from route36.gate_surround.build import over
from tiles import Tileset
from claude_cherrygrove import ground
SPECS={
 'CherrygroveRoute29Approach':[('G01a',(49,4),(50,7,5,5),None,False)],
 'JohtoRoute31':[('G01a',(1,8),(2,11,6,5),(4,15),False)],
}
def main(game,maps=None):
 reports=[]
 for config in json.loads((P/'source/initial-inventory.json').read_text()):
  name=config['map']
  if name not in SPECS or (maps and name not in maps):continue
  t=Tileset(game,config['secondary'],config['primary']);l=config['layout'];grid=np.fromfile(game/l['blockdata_filepath'],'<u2').reshape(l['height'],l['width']);oldgrid=grid.copy();layers,banks,es,attrs=decode(t,grid);oldattrs=attrs.copy();setup(t,grid,es,np.fromfile(game/l['border_filepath'],'<u2')&1023);t.allow_primary_palettes=name=='VioletCity';t.sort_complexity=True
  before=layers[0].copy();over(before,layers[1]);target=before.copy();fore=np.zeros_like(before);pal=np.array(t.pals[0][0][1:],int);raw=ground.textures()[ground.GRASS];tex=pal[np.square(raw[:,:,None,:].astype(int)-pal).sum(3).argmin(2)];ys,xs=np.indices(before.shape[:2]);bg=np.dstack([tex[ys%tex.shape[0],xs%tex.shape[1]],np.full(before.shape[:2],255,np.uint8)]);t.background=bg
  trees=json.loads((P/'source'/f'{name}-trees.json').read_text());trees_img=np.zeros_like(before)
  for r in sorted(trees,key=lambda a:(a['y'],a['x'])):over(trees_img,rgba(ROOT/f'gba/art/johto-common/trees/source/{r["asset"]}.png'),r['x'],r['y'])
  # Approved Route 36 gate cells carry the canonical roof/body/step layering.
  rt=Tileset(game,'johto_route36','johto_route36');rg=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);_,_,_,ra=decode(rt,rg)
  region=np.zeros(grid.shape,bool);records=[]
  for id,(ax,ay),(ox,oy,ow,oh),door,flip in SPECS[name]:
   art=rgba(ROOT/f'gba/art/johto-common-review/gates/refinement-4/{id}.png');art=art[:,::-1].copy() if flip else art
   if id=='G01a':reserve(t,art)
   ah,aw=art.shape[:2];left,top=min(ax,ox),min(ay,oy);right,bottom=max(ax+aw//16,ox+ow),max(ay+ah//16,oy+oh);sl=np.s_[top*16:bottom*16,left*16:right*16];region[top:bottom,left:right]=True
   target[sl]=bg[sl];over(target[sl],trees_img[sl]);over(target,art,ax*16,ay*16);over(fore,art,ax*16,ay*16)
   # Remove the old facade's invisible footprint, retaining real tree barriers.
   grid[oy:oy+oh,ox:ox+ow]=(grid[oy:oy+oh,ox:ox+ow]&1023)|0x3000;attrs[oy:oy+oh,ox:ox+ow]=0x1000
   sy,sx=(24,55) if id=='G01a' else (9,0)
   flags=rg[sy:sy+ah//16,sx:sx+aw//16]&0xfc00;at=ra[sy:sy+ah//16,sx:sx+aw//16]
   if flip:flags=flags[:,::-1];at=at[:,::-1]
   grid[ay:ay+ah//16,ax:ax+aw//16]=(grid[ay:ay+ah//16,ax:ax+aw//16]&1023)|flags;attrs[ay:ay+ah//16,ax:ax+aw//16]=at
   if door:
    dx,dy=door;grid[dy,dx]&=1023;attrs[dy,dx]=0x1060
   # Southern crowns remain in front; northern crowns remain behind the gate.
   for r in trees:
    tx,ty=r['x']//16,r['y']//16
    if ty>=ay+5 and ty<bottom and tx<right and tx+2>left:
     tree=rgba(ROOT/f'gba/art/johto-common/trees/source/{r["asset"]}.png');over(target,tree,r['x'],r['y']);over(fore,tree,r['x'],r['y'])
   records.append(dict(master=id,origin=[ax,ay],old_box=[ox,oy,ow,oh],door=door,mirrored=flip))
  for r in trees:
   tx,ty=r['x']//16,r['y']//16
   for y in range(max(0,ty+1),min(grid.shape[0],ty+3)):
    for x in range(max(0,tx),min(grid.shape[1],tx+2)):
     if region[y,x] and not any(v['origin'][0]<=x<v['origin'][0]+7 and v['origin'][1]<=y<v['origin'][1]+7 for v in records):grid[y,x]|=0xc00
  changed=np.any(target!=before,2);changed|=region.repeat(16,0).repeat(16,1)&((grid!=oldgrid)|(attrs!=oldattrs)).repeat(16,0).repeat(16,1)
  split(target,layers,changed,t,fore[:,:,3]>0);info=encode(game,config,t,grid,attrs,layers,target,changed)
  save(P/'review'/f'{name}-gates-before.png',before);save(P/'review'/f'{name}.png',target);info.update(map=name,gates=records,collision_changes=int((((oldgrid^grid)&0xfc00)>0).sum()),attribute_changed_cells=int((attrs!=oldattrs).sum()));reports.append(info);print(info,flush=True)
 old=json.loads((P/'evidence/gates.json').read_text()) if (P/'evidence/gates.json').exists() else []
 dump(P/'evidence/gates.json',[v for v in old if v['map'] not in {r['map'] for r in reports}]+reports)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--maps',nargs='+');a=p.parse_args();main(a.engine,a.maps)
