"""Two real hardware layers, with explicit foreground and ground shadows."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from claude_cherrygrove import ground,banks
from claude_cherrygrove.pixel import Canvas

def pack(comp,packer,pals,grid,source_dir):
 mc=comp['canvas'];fb,fi=mc.fore_bank,mc.fore_idx;bb,bi=mc.background_bank,mc.background_idx
 gimg,mat=ground.paint(comp['cells']);pal0=np.asarray(pals[0].gba(),int);rgb=gimg[...,:3].astype(int)
 gi=((rgb[...,None,:]-pal0[None,None])**2).sum(3).argmin(2).astype(np.uint8)
 h,w=gi.shape;cases={};mixed=[]
 for y in range(0,h,8):
  for x in range(0,w,8):
   fore=fb[y:y+8,x:x+8];background=bb[y:y+8,x:x+8];background_index=bi[y:y+8,x:x+8]
   keys=set(int(v) for v in np.unique(background) if v>=0)
   if (background<0).any():keys.add(0)
   # A fully opaque foreground quarter already covers every BG3 pixel.
   # Its invisible backing need not create another tile/metatile variant.
   if (fore>=0).all() and (fi[y:y+8,x:x+8]>0).all():continue
   # With no foreground, base and scenery can use their two usual layers.
   if len(keys)>1 and ((fore>=0).any() or mc.above[y//16,x//16]) and keys!={0,12}:
    q=gimg[y:y+8,x:x+8].copy()
    for bank in keys:
     mask=background==bank;q[mask,:3]=np.asarray(pals[bank].gba(),np.uint8)[background_index[mask]]
    name=f'background-{x//8:02}-{y//8:03}';cases[(x,y)]=name;mixed.append((name,q))
 if mixed:
  bank=banks.Bank(7,'NATIVE_TERRAIN_UNDER_OVERHANG','secondary').keep((104,208,152),(104,200,152),(88,176,136),(96,192,144),(64,136,104))
  for name,q in mixed:bank.add(name,q)
  converted=bank.build();pals[7]=bank.palette
 else:converted={}
 material=source_dir/'overhang-backgrounds';material.mkdir(exist_ok=True)
 current_names={name+'.png' for name,q in mixed}
 for stale in material.glob('background-*.png'):
  if stale.name not in current_names:stale.unlink()
 errors=[];foreground_errors=0
 for name,q in mixed:
  c=converted[name];Image.fromarray(c.to_rgba()).save(material/(name+'.png'))
  delta=np.abs(c.to_rgba()[...,:3].astype(int)-q[...,:3].astype(int));errors.append({'asset':name,'changed_pixels':int(np.any(delta,2).sum()),'max_channel_delta':int(delta.max())})
 def entry(bank,pixels):return packer.tile(bank,pixels)|(bank<<12) if pixels.any() else 0
 for y in range(comp['H']):
  for x in range(comp['W']):
   bottom=[];top=[]
   for q in range(4):
    xx,yy=x*16+q%2*8,y*16+q//2*8
    f=fb[yy:yy+8,xx:xx+8];fx=fi[yy:yy+8,xx:xx+8];b=bb[yy:yy+8,xx:xx+8];ix=bi[yy:yy+8,xx:xx+8]
    fs=[int(v) for v in np.unique(f) if v>=0];assert len(fs)<=1,('Overlapping foreground asset palettes',x,y,q,fs)
    bs=set(int(v) for v in np.unique(b) if v>=0)
    if (b<0).any():bs.add(0)
    base=gi[yy:yy+8,xx:xx+8]
    if fs and (f>=0).all() and (fx>0).all():
     bottom.append(0);top.append(entry(fs[0],fx.astype(np.uint8)));continue
    if not fs and (xx,yy) in cases:
     c=converted[cases[(xx,yy)]];bottom.append(entry(7,c.px.astype(np.uint8)));top.append(0);continue
    if not fs:
     if bs=={0,12}:
      colors=np.asarray(pals[12].gba(),int);src=gimg[yy:yy+8,xx:xx+8,:3].astype(int)
      ids=((src[...,None,:]-colors[None,None])**2).sum(3).argmin(2).astype(np.uint8)
      bottom.append(entry(12,np.where(b==12,ix,ids).astype(np.uint8)));top.append(0);continue
     if len(bs)==1:
      bank=next(iter(bs));pixels=np.where(b==bank,ix,base) if bank==0 else ix
      bottom.append(entry(bank,pixels));top.append(0)
     else:
      assert len(bs)==2 and 0 in bs,('Terrain needs more than two layers',x,y,q,bs)
      bank=next(v for v in bs if v!=0);bottom.append(entry(0,base));top.append(entry(bank,np.where(b==bank,ix,0).astype(np.uint8)))
     continue
    if (xx,yy) in cases:
     c=converted[cases[(xx,yy)]];bottom.append(entry(7,c.px.astype(np.uint8)))
    elif bs=={0,12}:
     colors=np.asarray(pals[12].gba(),int);src=gimg[yy:yy+8,xx:xx+8,:3].astype(int)
     ids=((src[...,None,:]-colors[None,None])**2).sum(3).argmin(2).astype(np.uint8)
     pixels=np.where(b==12,ix,ids).astype(np.uint8);bottom.append(entry(12,pixels))
    else:
     assert len(bs)==1,(x,y,q,bs)
     bank=next(iter(bs));pixels=np.where(b==bank,ix,base) if bank==0 else ix
     bottom.append(entry(bank,pixels))
    top.append(entry(fs[0],np.where(f==fs[0],fx,0).astype(np.uint8)))
   attr=int(comp['behavior'][y,x])|(0 if mc.above[y,x] else 0x1000)
   grid[y,x]=packer.metatile(bottom+top,attr)|0x3000|(0xc00 if comp['solid'][y,x] else 0)
 return {'composited_terrain_palette':7 if mixed else None,'background_assets':len(mixed),'background_colour_cleanup':errors,'ground_colours_pinned':True,'foreground_layers_explicit':True}
