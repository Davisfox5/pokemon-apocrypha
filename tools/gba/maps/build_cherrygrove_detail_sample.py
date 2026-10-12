#!/usr/bin/env python3
"""Small isolated native-art experiment; never writes a reviewed town source."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.cluster.vq import kmeans2
from tiles import Tileset
R=Path(__file__).resolve().parents[3]; G=R/'tools/vendor/gba/cherrygrove-detail-sample-work'; A=R/'gba/art/cherrygrove-detail-sample-v1'; E=A/'evidence'; E.mkdir(parents=True,exist_ok=True)
ref=Image.open(R/'gba/art/cherrygrove-art-study-v1/reference.png').convert('RGB')
box=(768,448,1280,832); im=ref.crop(box).resize((256,192),Image.Resampling.BOX); im.save(A/'reference-at-native-scale.png')
ar=np.array(im).astype(int); ar=((ar*31+127)//255); ar=((ar<<3)|(ar>>2)).astype('uint8')
patches=np.array([ar[y:y+8,x:x+8].reshape(64,3) for y in range(0,192,8) for x in range(0,256,8)])
# Group native blocks by their actual color distributions, not broad terrain labels.
features=[]
for p in patches:
 hist=np.zeros(64)
 bins=(p[:,0]//64)*16+(p[:,1]//64)*4+p[:,2]//64
 np.add.at(hist,bins,1)
 features.append(np.r_[hist/64,p.mean(0)/255,p.std(0)/255])
_,labels=kmeans2(np.array(features),13,minit='++',seed=7,iter=30)
def palette(ps):
 strip=Image.fromarray(ps.reshape(1,-1,3)); q=strip.quantize(colors=15,method=Image.Quantize.MEDIANCUT).convert('RGB')
 cs=np.unique(np.array(q).reshape(-1,3),axis=0).astype(int); cs=(cs*31+127)//255; cs=((cs<<3)|(cs>>2)).astype('uint8')
 cs=np.unique(cs,axis=0);return np.concatenate([cs,np.repeat(cs[-1:],15-len(cs),axis=0)])
pals=np.array([palette(patches[labels==b]) for b in range(13)])
# Two refinement passes select the bank that minimizes color error for each block.
for _ in range(2):
 errors=np.array([((patches[:,:,None,:].astype(int)-pal[None,None,:,:].astype(int))**2*np.array([2,3,1])).sum(3).min(2).mean(1) for pal in pals]); labels=errors.argmin(0)
 pals=np.array([palette(patches[labels==b]) if (labels==b).any() else pals[b] for b in range(13)])
errors=np.array([((patches[:,:,None,:].astype(int)-pal[None,None,:,:].astype(int))**2*np.array([2,3,1])).sum(3).min(2).mean(1) for pal in pals]); labels=errors.argmin(0)
tiles=[bytes(64)]; lookup={bytes(64):0}; entries=[]; decoded=np.zeros_like(ar)
for i,p in enumerate(patches):
 b=int(labels[i]); ix=((p[:,None,:].astype(int)-pals[b][None,:,:].astype(int))**2*np.array([2,3,1])).sum(2).argmin(1)+1; raw=bytes(ix.tolist())
 if raw not in lookup:lookup[raw]=len(tiles);tiles.append(raw)
 entries.append(lookup[raw]|b<<12); y=i//32*8;x=i%32*8;decoded[y:y+8,x:x+8]=pals[b][ix-1].reshape(8,8,3)
# A single surface uses one bank per block; no merged backplates or bank reduction.
blocks=[];attrs=[]; grid=[0x3400]*(32*24); blank=entries[2*32+28];blocks.append((blank,blank,blank,blank,0,0,0,0));attrs.append(0x1000)
walk=[]
for y in range(12):
 for x in range(16):
  i=y*2*32+x*2; block=(entries[i],entries[i+1],entries[i+32],entries[i+33],0,0,0,0);blocks.append(block);attrs.append(0x1000)
  region=ar[y*16:y*16+16,x*16:x*16+16].astype(int); r,g,b=region[:,:,0],region[:,:,1],region[:,:,2]
  grass=(g>r*1.12)&(g>b*1.1)&(g>155);sand=(r>180)&(g>155)&(r>b*1.22)
  # House silhouette and forest remain blocked; open paths and bright turf walk.
  blocked=(grass|sand).mean()<.65 or (7<=x<=11 and 2<=y<=6)
  grid[(y+6)*32+x+8]=(len(blocks)-1)|(0x3400 if blocked else 0x3000)
  if not blocked:walk.append([x+8,y+6])
assert len(tiles)<=1008
for side,start in [('primary',0),('secondary',512)]:
 d=G/f'data/tilesets/{side}/cherry_study'; sheet=Image.new('P',(128,256));sheet.putpalette([v for c in [(0,0,0)]+pals[0].tolist() for v in c]+[0]*720)
 for i in range(512):
  t=Image.new('P',(8,8));t.putdata(tiles[start+i] if start+i<len(tiles) else bytes(64));sheet.paste(t,(i%16*8,i//16*8))
 sheet.save(d/'tiles.png');bs=blocks[start:start+512];ats=attrs[start:start+512]
 if side=='primary':bs += [(0,)*8]*(512-len(bs));ats += [0x1000]*(512-len(ats))
 if not bs:bs=[(0,)*8];ats=[0x1000]
 (d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bs));(d/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(ats),*ats))
 for bank in range(16):
  cs=[(0,0,0)]+(pals[bank].tolist() if bank<13 else [(0,0,0)]*15);(d/f'palettes/{bank:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in cs)+'\n')
layout=G/'data/layouts/CherrygroveCity';(layout/'map.bin').write_bytes(struct.pack('<'+'H'*len(grid),*grid));(layout/'border.bin').write_bytes(struct.pack('<4H',0x3400,0x3400,0x3400,0x3400))
p=G/'data/layouts/layouts.json';j=json.loads(p.read_text());next(v for v in j['layouts'] if v['id']=='LAYOUT_CHERRYGROVE_CITY').update(width=32,height=24);p.write_text(json.dumps(j,indent=2)+'\n')
p=G/'data/maps/CherrygroveCity/map.json';j=json.loads(p.read_text());j.update(object_events=[],warp_events=[],coord_events=[],bg_events=[],connections=[]);p.write_text(json.dumps(j,indent=2)+'\n')
Image.fromarray(decoded).save(E/'native-sample.png');Image.fromarray(decoded).resize((768,576),Image.Resampling.NEAREST).save(E/'native-sample-3x.png')
ts=Tileset(G,secondary='cherry_study',primary='cherry_study');render=ts.map_image(grid,32);render.save(E/'decoded-map.png');assert np.array_equal(np.array(render.crop((128,96,384,288))),decoded)
old=Image.open(R/'gba/art/cherrygrove-art-study-v1/evidence/artwork-area.png'); old=old.crop((round(box[0]*800/1619),round(box[1]*480/972),round(box[2]*800/1619),round(box[3]*480/972))).resize((256,192),Image.Resampling.NEAREST)
board=Image.new('RGB',(1536,424),(30,35,40));d=ImageDraw.Draw(board)
for i,(label,img) in enumerate([('REFERENCE AT NATIVE SCALE',im),('FIRST CONVERSION',old),('REVISED NATIVE TILE SAMPLE',Image.fromarray(decoded))]):
 d.text((i*512+12,8),label,fill='white');board.paste(img.resize((512,384),Image.Resampling.NEAREST),(i*512,32))
board.save(E/'comparison.png')
(E/'conversion.json').write_text(json.dumps(dict(reference_box=list(box),native_size=[256,192],tiles=len(tiles),metatiles=len(blocks),palettes=13,opaque_colors_per_bank=15,roundtrip=True,walk_cells=walk,whole_town=False),indent=2)+'\n')
print('native patterns',len(tiles),'palettes',13,'walk',walk)
