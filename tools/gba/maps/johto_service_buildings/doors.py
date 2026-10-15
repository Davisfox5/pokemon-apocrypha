"""Exact-color service-door frames plus lossless remaps of existing house doors."""
from pathlib import Path
import sys,re,json,subprocess
import numpy as np
from PIL import Image
from build import ROOT,OUT,E,BASE
sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
QUADS=[(x+dx,y+dy) for x,y in [(0,0),(0,16),(16,0),(16,16)] for dx,dy in [(0,0),(8,0),(0,8),(8,8)]]
def main(game):
 t=Tileset(game,'johto_cherrygrove','johto_cherrygrove');pals=[list(t.pals[b>=6][b]) for b in range(13)];grid=np.fromfile(game/'data/layouts/CherrygroveCity/map.bin','<u2');scene=np.array(t.map_image(grid.tolist(),80));luts={int(k):np.array(v,np.uint8) for k,v in json.loads((OUT/'CherrygroveCity-palette-remap.json').read_text()).items()}
 source=(game/'src/field_door.c').read_text();original=subprocess.check_output(['git','show',BASE+':src/field_door.c'],cwd=game,text=True)
 used={b:set() for b in range(13)}
 for v in grid:
  mid=int(v&1023)
  for en in t.blocks[mid>=512][mid%512]:
   tid=en&1023;used[en>>12]|=set(t.tiles[tid>=512][tid%512])-{0}
 folder=game/'graphics/door_anims/johto_shared';folder.mkdir(exist_ok=True,parents=True);decl=[];framespecs={}
 for name,x,y,rect,dark in [('PokemonCenter',61,9,(0,16,16,28),(41,41,49)),('Mart',51,9,(3,5,17,25),(24,40,64))]:
  closed=scene[(y-1)*16:(y+1)*16,x*16:(x+2)*16];l,top,r,bot=rect;frames=[];leaf=closed[top:bot,l:r];width=r-l;half=width//2
  for amount in (max(1,half//3),max(2,half*2//3),half):
   f=closed.copy();f[top:bot,l:r]=dark
   if amount<half:
    f[top:bot,l:l+half-amount]=leaf[:,amount:half]
    f[top:bot,l+half+amount:r]=leaf[:,half:width-amount]
   frames.append(f)
  framespecs[name]=(closed,frames)
 # Allocate only unused colors in the private palette set. Never touch sea
 # palette slots; later water frames use colors absent in the static frame.
 requirements=[]
 for name,(closed,frames) in framespecs.items():
  for q,(x,y) in enumerate(QUADS):requirements.append((name,q,set(tuple(map(int,c)) for f in frames for c in f[y:y+8,x:x+8].reshape(-1,3))))
 # Account for colors used only by legacy house animation frames too.
 for name in ['PlayerHouse','GoldHouse','NeighborHouse','HarborHouse','GardenHouse']:
  banks=list(map(int,re.search(r'sRestartDoorPal_'+name+r'\[20\] = \{([^}]+)\}',original).group(1).split(',')))[:16]
  old=subprocess.check_output(['git','show',BASE+f':graphics/door_anims/johto_restart/{name}.4bpp'],cwd=game)
  for f in range(3):
   for q,b in enumerate(banks):
    ar=np.frombuffer(old[(f*16+q)*32:(f*16+q+1)*32],np.uint8);ix=set(ar&15)|set(ar>>4);used[b]|={int(luts.get(b,np.arange(16))[i]) for i in ix}-{0}
 free={b:sorted(set(range(1,16))-used[b]) if b!=1 else [] for b in range(13)}
 def solve(pal,slots,pending,assigned):
  if not pending:return pal,assigned
  options=[]
  for name,q,colors in pending:
   choices=[]
   for b in range(13):
    missing=colors-set(pal[b][1:])
    if len(missing)<=len(slots[b]):choices.append((len(missing),b,missing))
   if not choices:return None
   options.append((len(choices),-len(colors),name,q,colors,choices))
  _,_,name,q,colors,choices=min(options,key=lambda v:v[:4]);remaining=[r for r in pending if r[:2]!=(name,q)]
  for _,b,missing in sorted(choices,key=lambda v:(v[0],len(slots[v[1]]),v[1])):
   pp=[p.copy() for p in pal];ss={b:v.copy() for b,v in slots.items()}
   for c in sorted(missing):pp[b][ss[b].pop(0)]=c
   found=solve(pp,ss,remaining,{**assigned,(name,q):b})
   if found:return found
  return None
 result=solve(pals,free,requirements,{})
 assert result,'Exact door palette allocation failed'
 pals,assignments=result
 for name in ['PlayerHouse','GoldHouse','NeighborHouse','Mart','PokemonCenter','HarborHouse','GardenHouse']:
  if name in framespecs:
   closed,frames=framespecs[name];banks=[assignments[name,q] for q in range(16)];raw=bytearray()
   for f in frames:
    for (x,y),bank in zip(QUADS,banks):
     pm={c:i for i,c in enumerate(pals[bank]) if i};ix=np.array([pm[tuple(map(int,c))] for c in f[y:y+8,x:x+8].reshape(-1,3)],np.uint8)
     raw.extend((ix[::2]|ix[1::2]<<4).tobytes())
   Image.fromarray(np.concatenate([closed]+frames,axis=1)).resize((512,128),Image.Resampling.NEAREST).save(E/f'door-{name}.png')
  else:
   banks=list(map(int,re.search(r'sRestartDoorPal_'+name+r'\[20\] = \{([^}]+)\}',original).group(1).split(',')))[:16]
   old=subprocess.check_output(['git','show',BASE+f':graphics/door_anims/johto_restart/{name}.4bpp'],cwd=game);raw=bytearray()
   for f in range(3):
    for q,bank in enumerate(banks):
     data=np.frombuffer(old[(f*16+q)*32:(f*16+q+1)*32],np.uint8);ix=np.empty(64,np.uint8);ix[::2]=data&15;ix[1::2]=data>>4;ix=luts.get(bank,np.arange(16,dtype=np.uint8))[ix];raw.extend((ix[::2]|ix[1::2]<<4).tobytes())
  (folder/f'{name}.4bpp').write_bytes(raw)
  decl.append(f'static const u8 sSharedDoor_{name}[] = INCBIN_U8("graphics/door_anims/johto_shared/{name}.4bpp");\nstatic const u8 sSharedDoorPal_{name}[20] = {{'+','.join(map(str,banks+[0]*4))+'};')
 for b in range(13):
  for part in ('primary','secondary'):
   (game/f'data/tilesets/{part}/johto_cherrygrove/palettes/{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
 marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] ='
 source=re.sub(r'^static const u8 sSharedDoor[^\n]*\n','',source,flags=re.M)
 source=source.replace(marker,'\n'.join(decl)+'\n'+marker);(game/'src/field_door.c').write_text(source)
 assert np.array_equal(np.array(Tileset(game,'johto_cherrygrove','johto_cherrygrove').map_image(grid.tolist(),80)),scene)
 (E/'door-validation.json').write_text(json.dumps({'new_door_frames':'exact RGB palette encoding; no nearest-color conversion','existing_house_frames':'palette labels remapped losslessly','exterior_unchanged':True,'target_banks':{n:[assignments[n,q] for q in range(16)] for n in framespecs}},indent=2)+'\n')
 print('Seven private door animations written; service frames retain exact colors.')
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
