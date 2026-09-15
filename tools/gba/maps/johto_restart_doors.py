#!/usr/bin/env python3
"""Make facade-specific native doors above the clean Emerald door implementation."""
from pathlib import Path
import json,struct,numpy as np
from PIL import Image
from tiles import Tileset
R=Path(__file__).resolve().parents[3];A=R/'gba/art/johto-restart';G=R/'tools/vendor/gba/johto-restart-game';B=R/'tools/vendor/gba/johto-art-v3-baseline'
t=Tileset(G,'cherrygrove','cherrygrove');rgb=np.array(Image.open(A/'evidence/town-overview.png')).astype(int);spec=json.loads((A/'layout.json').read_text());grid=struct.unpack('<'+'H'*(spec['width']*spec['height']),(G/'data/layouts/CherrygroveCity/map.bin').read_bytes())
folder=G/'graphics/door_anims/johto_restart';folder.mkdir(parents=True,exist_ok=True)
quads=[(x+dx,y+dy) for x,y in [(0,0),(0,16),(16,0),(16,16)] for dx,dy in [(0,0),(8,0),(0,8),(8,8)]]
source=(B/'src/field_door.c').read_text();declarations=['extern const struct Tileset gTileset_Cherrygrove;'];table=[];report=[]
for b in spec['buildings']:
 name=b['name'];x,y=b['door'];closed=rgb[(y-1)*16:(y+1)*16,x*16:(x+2)*16].copy();l,top,r,bot=(2,17,15,30) if b['style']=='house' else (0,16,21,31) if b['style']=='center' else (1,17,16,31)
 frames=[]
 for amount in [3,8,r-l]:
  f=closed.copy();f[top:bot,l:r]=(24,32,40)
  keep=max(0,r-l-amount)
  for col in range(keep):f[top:bot,l+col]=closed[top:bot,l+int(col*(r-l)/max(1,keep))]
  frames.append(f)
 banks=[];tiledata=bytearray();views=[]
 for qx,qy in quads:
  colors=np.concatenate([f[qy:qy+8,qx:qx+8].reshape(-1,3) for f in frames]);best=None
  for bank in range(13):
   pal=np.array(t.pals[bank>=6][bank][1:]);dist=((colors[:,None,:]-pal[None,:,:])**2).sum(axis=2);cost=dist.min(axis=1).sum()
   if best is None or cost<best[0]:best=(cost,bank)
  banks.append(best[1])
 for frame in frames:
  preview=np.zeros((32,32,3),dtype=np.uint8)
  for (qx,qy),bank in zip(quads,banks):
   pal=np.array(t.pals[bank>=6][bank][1:]);colors=frame[qy:qy+8,qx:qx+8].reshape(-1,3);ix=((colors[:,None,:]-pal[None,:,:])**2).sum(axis=2).argmin(axis=1);preview[qy:qy+8,qx:qx+8]=pal[ix].reshape(8,8,3);ix=ix+1
   tiledata.extend(int(ix[k])|(int(ix[k+1])<<4) for k in range(0,64,2))
  views.append(preview)
 (folder/(name+'.4bpp')).write_bytes(tiledata)
 Image.fromarray(np.concatenate([closed.astype(np.uint8)]+views,axis=1)).resize((512,128),Image.Resampling.NEAREST).save(A/f'evidence/door-{name}.png')
 declarations.append(f'static const u8 sRestartDoor_{name}[] = INCBIN_U8("graphics/door_anims/johto_restart/{name}.4bpp");\nstatic const u8 sRestartDoorPal_{name}[20] = {{'+','.join(map(str,banks+[0]*4))+'};')
 mid=grid[y*spec['width']+x]&1023
 table.append(f'    {{.metatileNum={mid}, .tileset=&gTileset_Cherrygrove, .sound='+('DOOR_SOUND_NORMAL' if b['style']=='house' else 'DOOR_SOUND_SLIDING')+f', .size=DOOR_SIZE_2x2_LEFT, .tiles=sRestartDoor_{name}, .palettes=sRestartDoorPal_{name}}},')
 report.append(dict(name=name,metatile=mid,frames=3,tile_bytes=len(tiledata),palette_bytes=20))
marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{';assert marker in source
source=source.replace(marker,'// Fresh custom Johto facade animations.\n'+'\n'.join(declarations)+'\n'+marker+'\n'+'\n'.join(table));(G/'src/field_door.c').write_text(source)
(A/'evidence/doors.json').write_text(json.dumps(report,indent=2)+'\n');print('Five native animated doors compiled.')
