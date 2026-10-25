#!/usr/bin/env python3
"""Native 1x2 door animation from the receiving HGSS pixels; original facade remains unchanged."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
from native import Bank,words
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];E=Path(sys.argv[1]);ART=ROOT/'gba/art/pallet-town-rebuild';OUT=ART/'source/doors';OUT.mkdir(parents=True,exist_ok=True);D=E/'graphics/door_anims/pallet_hgss';D.mkdir(exist_ok=True)
b=Bank(E,'primary/palletoutdoor','secondary/pallettown',False);used={e>>12 for part in b.blocks for m in part for e in m};free=[i for i in range(13) if i not in used and i];banks=[set(b.pals[i>=6][i][1:]) for i in range(13)];new={}
plans=[]
for idx,(x,y,left,top,right,bottom) in enumerate([(6,8,0,0,16,25),(15,8,0,0,16,25),(16,14,0,11,16,31)]):
 grid=words(E/'data/layouts/ApocPalletTown/map.bin');im=Image.new('RGB',(16,32));im.paste(b.render(grid[(y-1)*24+x]&1023),(0,0));im.paste(b.render(grid[y*24+x]&1023),(0,16));a=np.array(im);dark=min(set(map(tuple,a[top:bottom,left:right].reshape(-1,3))),key=lambda c:sum(map(int,c)));frames=[]
 for shrink in [5,10,16]:
  frame=a.copy();frame[top:bottom,left:right]=dark
  w=right-left-shrink
  if w>0:frame[top:bottom,left:left+w]=np.array(Image.fromarray(a[top:bottom,left:right]).resize((w,bottom-top),Image.Resampling.NEAREST))
  frames.append(frame)
 # One palette per native 8x8 tile, valid for every frame, with no changes to already used banks.
 pals=[]
 for ty in range(4):
  for tx in range(2):
   st=set(map(tuple,np.concatenate([f[ty*8:ty*8+8,tx*8:tx*8+8].reshape(-1,3) for f in [a]+frames])))
   fits=[i for i in range(13) if st<=banks[i]]
   if not fits:
    merge=[i for i in free if len(new.get(i,set())|st)<=15];assert merge,(idx,ty,tx,len(st))
    i=min(merge,key=lambda k:len(new.get(k,set())|st));new.setdefault(i,set()).update(st);banks[i]=new[i];fits=[i]
   pals.append(fits[0])
 plans.append(dict(index=idx,x=x,y=y,closed=a,frames=frames,palettes=pals,dark=dark))
# Store spare-bank palettes without moving/recoloring a single compiled scenery pixel.
for i,colors in new.items():
 pal=[(0,0,0)]+sorted(colors);pal += [(0,0,0)]*(16-len(pal));b.pals[i>=6][i]=pal
 p=E/('data/tilesets/primary/palletoutdoor' if i<6 else 'data/tilesets/secondary/pallettown')/'palettes'/f'{i:02}.pal';p.write_text('JASC-PAL\n0100\n16\n'+''.join('%d %d %d\n'%c for c in pal))
extra='\n// HGSS Pallet doors: fitted to the receiving facade, including its actual ground.\nextern const struct Tileset gTileset_ApocPallet;\n';entries=[];report=[]
for p in plans:
 idx=p['index'];raw=bytearray();preview=Image.new('RGB',(16*4,32));preview.paste(Image.fromarray(p['closed']),(0,0))
 for frameindex,frame in enumerate(p['frames']):
  preview.paste(Image.fromarray(frame),(16*(frameindex+1),0))
  for ty in range(4):
   for tx in range(2):
    bank=p['palettes'][ty*2+tx];pal=b.pals[bank>=6][bank];vals=[pal.index(tuple(v),1) for v in frame[ty*8:ty*8+8,tx*8:tx*8+8].reshape(-1,3)]
    raw.extend(vals[j]|vals[j+1]<<4 for j in range(0,64,2))
 (D/f'{idx}.4bpp').write_bytes(raw);preview.resize((512,256),Image.Resampling.NEAREST).save(OUT/f'door-{idx}-frames.png')
 extra+=f'static const u8 sPalletHgssDoor{idx}[] = INCBIN_U8("graphics/door_anims/pallet_hgss/{idx}.4bpp");\nstatic const u8 sPalletHgssDoorPal{idx}[] = {{'+','.join(map(str,p['palettes']))+'};\n'
 mid=grid[p['y']*24+p['x']]&1023;entries.append(f'    {{.metatileNum={mid}, .tileset=&gTileset_ApocPallet, .sound=DOOR_SOUND_NORMAL, .size=DOOR_SIZE_1x2, .tiles=sPalletHgssDoor{idx}, .palettes=sPalletHgssDoorPal{idx}}},')
 report.append(dict(x=p['x'],y=p['y'],metatile=mid,frames=3,bytes=len(raw),palette_banks=p['palettes'],closed_pixels_unchanged=True))
f=E/'src/field_door.c';s=f.read_text();marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] ='
if '// HGSS Pallet doors:' in s:
 a=s.index('// HGSS Pallet doors:');z=s.index(marker,a);s=s[:a]+s[z:];s='\n'.join(l for l in s.split('\n') if '.tiles=sPalletHgssDoor' not in l)
s=s.replace(marker,extra+marker).replace(marker+'\n{',marker+'\n{\n'+'\n'.join(entries));f.write_text(s)
(OUT/'doors.json').write_text(json.dumps(report,indent=2)+'\n');print('Three HGSS native doors, exact closed pixels, spare palette banks',list(new))
