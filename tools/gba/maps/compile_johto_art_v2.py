#!/usr/bin/env python3
"""Import the owner's selected generated buildings without aspect distortion.

Two shared, tile-selected RGB555 palettes preserve roof and facade colors within
existing banks 8/10. This is deterministic format conversion, not new artwork.
"""
import hashlib,json,struct,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'gba/art/johto-v1';ART=ROOT/'gba/art/johto-v2';OUT=ART/'native'
OUT.mkdir(parents=True,exist_ok=True)
tiles=[];assets=[]
for name,file in [('house','house-final.png'),('center','center.png')]:
 src=OLD/'generated'/file;im=Image.open(src).convert('RGBA')
 mask=im.getchannel('A').point(lambda a:255 if a>=224 else 0);bounds=mask.getbbox()
 im.putalpha(mask);im=im.crop(bounds)
 scale=min(80/im.width,80/im.height);size=tuple(round(v*scale) for v in im.size)
 im=im.resize(size,Image.Resampling.NEAREST)
 canvas=Image.new('RGBA',(80,80));canvas.paste(im,((80-im.width)//2,80-im.height))
 start=len(tiles)
 for y in range(0,80,8):
  for x in range(0,80,8):
   px=np.array(canvas.crop((x,y,x+8,y+8))).reshape(64,4)
   tiles.append(dict(rgb=px[:,:3].astype(np.int32),mask=px[:,3]>0,bank=int(y>=40),x=x,y=y))
 assets.append(dict(name=name,source=str(src.relative_to(ROOT)),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),source_bounds=bounds,width=80,height=80,content_size=size,tile_start=start,tile_count=100))
def palette(which):
 pix=np.concatenate([t['rgb'][t['mask']] for t in tiles if t['bank']==which])
 strip=Image.fromarray(pix.astype(np.uint8).reshape(1,-1,3))
 q=strip.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 colors=np.array(q.getpalette(),dtype=np.int32).reshape(-1,3)[:15]
 return np.rint(colors*31/255).astype(np.int32)*255//31
def match(t,p):
 d=((t['rgb'][:,None,:]-p[None,:,:])**2).sum(axis=2)
 ids=d.argmin(axis=1);error=d[np.arange(64),ids][t['mask']].sum()
 return ids,error
for iteration in range(16):
 pals=[palette(i) for i in range(2)];changed=0
 for t in tiles:
  choices=[match(t,p)[1] for p in pals];bank=int(np.argmin(choices))
  changed+=bank!=t['bank'];t['bank']=bank
 if not changed:break
pals=[palette(i) for i in range(2)]
for i,p in enumerate(pals):
 bank=[8,10][i];colors=[(0,0,0)]+[tuple(map(int,c)) for c in p]
 (OUT/f'{bank:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
 (OUT/f'{bank:02}.gbapal').write_bytes(struct.pack('<16H',*[sum(round(c[j]*31/255)<<(j*5) for j in range(3)) for c in colors]))
for a in assets:
 local=tiles[a.pop('tile_start'):][:100];preview=Image.new('RGBA',(80,80));packed=bytearray();banks=[]
 for t in local:
  ids=match(t,pals[t['bank']])[0]+1;ids[~t['mask']]=0
  packed.extend(int(ids[i])|int(ids[i+1])<<4 for i in range(0,64,2))
  colors=np.vstack([np.zeros((1,3),dtype=np.int32),pals[t['bank']]])
  rgba=np.column_stack([colors[ids],np.where(ids,255,0)]).astype(np.uint8).reshape(8,8,4)
  preview.paste(Image.fromarray(rgba),(t['x'],t['y']));banks.append([8,10][t['bank']])
 preview.save(OUT/(a['name']+'.png'))
 (OUT/(a['name']+'.4bpp')).write_bytes(packed)
 a.update(tile_palette_banks=banks,packed_bytes=len(packed),unique_tiles=len({bytes(packed[i:i+32]) for i in range(0,len(packed),32)}))
tree=json.loads((OLD/'native/manifest.json').read_text())['assets'][2]
for ext in ['png','pal','gbapal','4bpp']:shutil.copy2(OLD/'native'/('tree.'+ext),OUT/('tree.'+ext))
tree['tile_palette_banks']=[6]*tree['tile_count'];assets.append(tree)
manifest=dict(format='8x8 4bpp tile data; per-tile RGB555 palette selection',alpha_threshold=224,resampling='nearest; aspect preserved, centered and bottom aligned',palette_banks=[6,8,10],assets=assets)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
board=Image.new('RGB',(800,430),'#15262b');d=ImageDraw.Draw(board)
d.text((20,15),'SAME GENERATED SOURCES / revised GBA import',fill='white')
for row,name in enumerate(['house','center']):
 y=50+row*185
 for col,ver in enumerate([OLD,ART]):
  im=Image.open(ver/'native'/(name+'.png')).convert('RGBA');im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
  board.paste(im,(20+col*230,y),im)
 d.text((490,y+20),name.upper()+' / before -> after',fill='white')
 d.text((490,y+45),'80 x 80; original proportions',fill='white')
 d.text((490,y+65),'Two shared tile-selected palettes',fill='white')
 im=Image.open(OUT/(name+'.png'));board.paste(im,(490,y+90),im)
board.save(ART/'comparison.png');print(json.dumps({a['name']:a.get('unique_tiles') for a in assets}))
