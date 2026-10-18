"""Fit native collision/behavior to the rebuilt rock outline, with a cell ledger."""
from pathlib import Path
import json,struct,sys
import numpy as np
from PIL import Image
from rock_structures import CONFIGS,P
from johto_common.regional_rocks import load
for c in CONFIGS:
 n=c['map'];game=Path(c['engine']);t,g,l,b,e,a,im=load(c,game);_,bg,_,_,_,ba,_=load(c,Path(c['baseline']));h,w=g.shape
 roles=np.load(P/'source'/f'{n}-roles.npy');fg=np.load(P/'source'/f'{n}-foreground.npy');removed=np.load(P/'source'/f'{n}-removed.npy');solid=(roles>0)&~fg
 def counts(mask):return mask.reshape(h,16,w,16).sum((1,3))
 cover=counts(solid);removedcount=counts(removed);treecount=counts(fg)
 protected=set((v['x'],v['y']) for v in json.loads((game/'data/maps'/n/'map.json').read_text())['warp_events'])
 if n=='JohtoRoute31':protected|={(x,y) for x in [33,34] for y in [16,17]}|{(x,y) for x in [37,38,39] for y in [28,29]}
 else:protected|={(x,y) for x in range(8,11) for y in range(59,62)}|{(x,y) for x in range(6,9) for y in range(87,90)}
 edits=[];blocks=list(t.blocks[1]);ats=list(t.attrs[1]);used=set(g.ravel()&1023)|set(np.fromfile(game/c['layout']['border_filepath'],'<u2')&1023);free=[i for i in range(512,1024) if i not in used];clones={}
 for y in range(1,h-1):
  for x in range(1,w-1):
   if (x,y) in protected:continue
   oldcol=int(bg[y,x]>>10&3);behavior=int(a[y,x]);high=int(g[y,x]&0xfc00);reason=None
   if cover[y,x]>=160 and oldcol==0:
    high=0x3c00;behavior=(behavior&~255);reason='new coherent rock outline'
   elif removedcount[y,x]>=160 and cover[y,x]<16 and treecount[y,x]<16 and oldcol==3:
    tile=im[y*16:y*16+16,x*16:x*16+16].astype(int);water=np.mean(tile[:,:,2]>tile[:,:,0]+40)>.8
    high=0x1000 if water else 0x3000;behavior=(behavior&~255)|(0x15 if water else 0);reason='removed superseded rock; restore '+('water' if water else 'ground')
   if reason is None:continue
   mid=int(g[y,x]&1023)
   if behavior!=int(a[y,x]):
    key=(mid,behavior)
    if key not in clones:
     assert free,'attribute metatile capacity';dest=free.pop(0)
     while len(blocks)<=dest-512:blocks.append([0]*8);ats.append(0)
     blocks[dest-512]=list(t.blocks[mid>=512][mid%512]);ats[dest-512]=behavior;clones[key]=dest
    mid=clones[key]
   before=int(g[y,x]);g[y,x]=high|mid;edits.append(dict(x=x,y=y,from_collision=oldcol,to_collision=int(g[y,x]>>10&3),from_behavior=int(a[y,x]),to_behavior=behavior,reason=reason))
 folder=game/'data/tilesets/secondary'/c['secondary'];(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in blocks));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(ats),*ats));g.astype('<u2').tofile(game/c['layout']['blockdata_filepath'])
 *_,actual=load(c,game);assert np.array_equal(actual,im)
 (P/'evidence'/f'{n}-collision.json').write_text(json.dumps(edits,indent=2)+'\n');print(n,len(edits),'collision/behavior cells aligned')
