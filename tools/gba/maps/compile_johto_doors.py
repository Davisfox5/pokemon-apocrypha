#!/usr/bin/env python3
"""Build native sliding/swing-retraction door frames from the installed facade pixels.
All exterior pixels are preserved except the explicit aperture; 16 hardware tiles
are reserved by the scene compiler. No donor or production asset is changed.
"""
from pathlib import Path
import numpy as np,json,struct,re
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];A=ROOT/'gba/art/johto-v4';G=ROOT/'tools/vendor/gba/johto-v4-game'
scene=np.load(A/'native/scene.npz');palette=scene['palette'];original=np.array(Image.open(A/'evidence/town-overview.png')).astype(int)
grid=np.frombuffer((G/'data/layouts/CherrygroveCity/map.bin').read_bytes(),dtype='<u2').reshape(32,64)
layout=json.loads((A/'layout.json').read_text());folder=G/'graphics/door_anims/johto_v4';folder.mkdir(exist_ok=True)
assets=A/'native/doors';assets.mkdir(exist_ok=True)
# Bounds measured on the native facade, relative to the engine's 32x32 door patch.
apertures={'PlayerHouse':(4,10,23,25),'GoldHouse':(1,4,20,17),'NeighborHouse':(4,10,23,25),'Mart':(2,10,24,22),'PokemonCenter':(2,16,22,26)}
quads=[(mx+dx,my+dy) for mx,my in [(0,0),(0,16),(16,0),(16,16)] for dx,dy in [(0,0),(8,0),(0,8),(8,8)]]
decls=[];entries=[];report=[]
for b in layout['buildings']:
 name=b['name'];x,y=b['door'];base=original[(y-1)*16:(y+1)*16,x*16:(x+2)*16].copy();left,top,right,bottom=apertures[name];width=right-left;mid=(left+right)//2
 frames=[]
 for opening in [3,8,12]:
  frame=base.copy();frame[top:bottom,left:right]=(33,41,41)
  # Sliding shops retract both panels. Wooden doors retract toward their hinge.
  if name in ['Mart','PokemonCenter']:
   for xx in range(left,mid):
    if xx-opening>=left:frame[top:bottom,xx-opening]=base[top:bottom,xx]
   for xx in range(mid,right):
    if xx+opening<right:frame[top:bottom,xx+opening]=base[top:bottom,xx]
  else:
   remaining=max(0,width-opening*2)
   if remaining:
    for xx in range(remaining):frame[top:bottom,left+xx]=base[top:bottom,left+int(xx*width/remaining)]
  frames.append(frame)
 banks=[]
 for qx,qy in quads:
  cs=np.concatenate([f[qy:qy+8,qx:qx+8].reshape(-1,3) for f in frames]);best=None
  for bank in [0,3,6,7,8,9,10]:
   pp=palette[bank*16+1:bank*16+16];pp=pp[np.any(pp!=0,axis=1)];cost=np.min(np.sum((cs[:,None,:]-pp[None,:,:])**2,axis=2),axis=1).sum()
   if best is None or cost<best[0]:best=(cost,bank)
  banks.append(best[1])
 data=bytearray();display=[]
 for frame in frames:
  native=np.zeros((32,32,3),dtype=np.uint8)
  for (qx,qy),bank in zip(quads,banks):
   pp=palette[bank*16+1:bank*16+16];pp=pp[np.any(pp!=0,axis=1)];cs=frame[qy:qy+8,qx:qx+8].reshape(-1,3);ix=np.argmin(np.sum((cs[:,None,:]-pp[None,:,:])**2,axis=2),axis=1)+1
   data.extend(int(ix[i])|int(ix[i+1])<<4 for i in range(0,64,2));native[qy:qy+8,qx:qx+8]=palette[bank*16+ix].reshape(8,8,3)
  display.append(native)
 (folder/f'{name}.4bpp').write_bytes(data);(assets/f'{name}.4bpp').write_bytes(data)
 Image.fromarray(np.concatenate([base.astype(np.uint8)]+display,axis=1)).resize((512,128),Image.Resampling.NEAREST).save(A/f'evidence/door-{name}.png')
 decls.append(f'static const u8 sDoorTiles_JohtoV4_{name}[] = INCBIN_U8("graphics/door_anims/johto_v4/{name}.4bpp");\nstatic const u8 sDoorPal_JohtoV4_{name}[20] = {{'+', '.join(map(str,banks+[0]*4))+'};')
 mid=int(grid[y,x])&1023
 entries.append(f'    {{.metatileNum = {mid}, .tileset = &gTileset_CherrygrovePrimary, .sound = '+('DOOR_SOUND_SLIDING' if name in ['Mart','PokemonCenter'] else 'DOOR_SOUND_NORMAL')+f', .size = DOOR_SIZE_2x2_LEFT, .tiles = sDoorTiles_JohtoV4_{name}, .palettes = sDoorPal_JohtoV4_{name}}},')
 report.append(dict(name=name,metatile=mid,aperture=apertures[name],bytes=len(data),palette_bytes=20))
p=G/'src/field_door.c';s=p.read_text();s=re.sub(r'// BEGIN JOHTO V4 DOOR DECLS.*?// END JOHTO V4 DOOR DECLS\n','',s,flags=re.S);s=re.sub(r'// BEGIN JOHTO V4 DOOR ENTRIES.*?// END JOHTO V4 DOOR ENTRIES\n','',s,flags=re.S)
marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{';s=re.sub(re.escape(marker)+r'\n*',lambda _:marker+'\n',s);s=s.replace(marker,'// BEGIN JOHTO V4 DOOR DECLS\n'+'\n'.join(decls)+'\n// END JOHTO V4 DOOR DECLS\n'+marker+'\n// BEGIN JOHTO V4 DOOR ENTRIES\n'+'\n'.join(entries)+'\n// END JOHTO V4 DOOR ENTRIES\n');p.write_text(s)
(A/'evidence/doors.json').write_text(json.dumps(report,indent=2)+'\n');print('Compiled five three-frame native door animations.')
