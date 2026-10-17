"""Lossless repack for a private, nonanimated map. RGB and behavior are invariant."""
import json,struct
import numpy as np
from PIL import Image
from violet_city.packing import Probe,optimize
from johto_service_buildings.build import decode
from route36.gate_surround.build import over
from tiles import Tileset

def encode_private(game,c,t,grid,attrs,layers,target,changed):
 assert c['primary']==c['secondary']=='violet_city'
 headers=(game/'src/data/tilesets/headers.h').read_text()
 for symbol in ['gTileset_VioletCityPrimary','gTileset_VioletCity']:
  assert '.callback = NULL' in headers.split('const struct Tileset '+symbol+' =')[1].split(';')[0]
 layout=c['layout'];border=np.fromfile(game/layout['border_filepath'],'<u2');bl,_,_,ba=decode(t,border.reshape(2,2));beforeborder=bl[0].copy();over(beforeborder,bl[1])
 pals=[list(t.pals[b>=6][b]) for b in range(13)];cs=[set(p[1:]) for p in pals];probe=Probe();allcells=[]
 def encode_layers(lays,ats,grid_for):
  result=[]
  for cy,cx in np.ndindex(ats.shape):
   entries=[]
   for layeridx,layer in enumerate(lays):
    for q in range(4):
     y,x=cy*16+q//2*8,cx*16+q%2*8;a=layer[y:y+8,x:x+8];m=a[:,:,3]>0;colors=set(map(tuple,a[m,:3]));mid=int(grid_for[cy,cx]&1023);preferred=t.blocks[int(mid>=512)][mid%512][layeridx*4+q]>>12;bank=next(b for b in [preferred]+list(range(13)) if colors<=cs[b]);ids={}
     for i,col in enumerate(pals[bank]):
      if i:ids.setdefault(col,i)
     ix=np.zeros((8,8),np.uint8)
     for col in colors:ix[m&np.all(a[:,:,:3]==col,2)]=ids[col]
     probe.tile(bank,ix);entries.append((bank,ix))
   result.append((entries,int(ats[cy,cx])))
  return result
 main=encode_layers(layers,attrs,grid);borders=encode_layers(bl,ba,border.reshape(2,2));print("bank counts",{k:len(v) for k,v in probe.raw.items()},flush=True);lut,stats=optimize(probe,fixed=(8,9));print(stats,flush=True)
 for b,p in enumerate(pals):
  if b in lut:
   new=list(p)
   for i in range(16):new[int(lut[b][i])]=p[i]
   pals[b]=new
 raw=[np.zeros((8,8),np.uint8)];cache={raw[0].tobytes():0};blocks=[];ats=[];bc={}
 def cell(rec):
  entries,attr=rec;es=[]
  for b,a in entries:
   a=lut[b][a];value=None
   for ar,bits in [(a,0),(a[:,::-1],1024),(a[::-1],2048),(a[::-1,::-1],3072)]:
    if ar.tobytes() in cache:value=cache[ar.tobytes()]|bits;break
   if value is None:value=len(raw);cache[a.tobytes()]=value;raw.append(a)
   es.append(value|b<<12)
  key=tuple(es),attr
  if key not in bc:bc[key]=len(blocks);blocks.append(es);ats.append(attr)
  return bc[key]
 mids=np.array([cell(v) for v in main],np.uint16).reshape(grid.shape);bm=np.array([cell(v) for v in borders],np.uint16)
 assert len(raw)<=1008,('graphic capacity',len(raw));assert len(blocks)<=1024,('metatile capacity',len(blocks))
 # No write occurs before both capacity gates pass.
 raw += [np.zeros((8,8),np.uint8)]*(1008-len(raw));blocks += [(0,)*8]*(1024-len(blocks));ats += [0]*(1024-len(ats))
 for sec in [False,True]:
  folder=game/'data/tilesets'/('secondary' if sec else 'primary')/'violet_city';im=Image.new('P',(128,248 if sec else 256));im.putpalette(Image.open(folder/'tiles.png').getpalette())
  for i,a in enumerate(raw[512:1008] if sec else raw[:512]):im.paste(Image.fromarray(a),(i%16*8,i//16*8))
  im.save(folder/'tiles.png',bits=4);start=512 if sec else 0;end=1024 if sec else 512
  (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in blocks[start:end]));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*ats[start:end]))
  for b in (range(6,13) if sec else range(6)):(folder/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,col)) for col in pals[b])+'\n')
 ng=(grid&0xfc00)|mids;ng.astype('<u2').tofile(game/layout['blockdata_filepath']);((border&0xfc00)|bm).astype('<u2').tofile(game/layout['border_filepath'])
 nt=Tileset(game,'violet_city','violet_city');ll,_,_,aa=decode(nt,ng);a=ll[0].copy();over(a,ll[1]);assert np.array_equal(a,target);assert np.array_equal(aa,attrs)
 ll,_,_,_=decode(nt,bm.reshape(2,2));a=ll[0].copy();over(a,ll[1]);assert np.array_equal(a,beforeborder)
 return dict(repack=stats,live_graphics=len(cache),live_metatiles=len(bc),native_exact=True,border_exact=True)
