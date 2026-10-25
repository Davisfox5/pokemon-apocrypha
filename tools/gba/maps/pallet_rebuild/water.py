"""Native UV scrolling of the converted HGSS water; shoreline art stays fixed.

Only native tiles containing the exact complete HGSS water patches are animated.
All other uses of each tile must have the same palette interpretation. The eight
phases scroll the source texture by four pixels, at eight frames per phase.
"""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from native import Bank
ROOT=Path(__file__).resolve().parents[4];A=ROOT/'gba/art/pallet-town-rebuild';E=Path(sys.argv[1])
b=Bank(E,'primary/palletoutdoor','secondary/pallettown',False)
water=np.array(Image.open(A/'source/assets/hgss-water.png').convert('RGB'))
uses={}
for blocks in b.blocks:
    for m in blocks:
        for e in m:uses.setdefault(e&1023,set()).add(e>>12)
plans=[]
for tid,banks in sorted(uses.items()):
    tile=np.array(b.tile(tid));bank=sorted(banks)[0];pal=b.pals[bank>=6][bank]
    rgb=np.array(pal,dtype=np.uint8)[tile]
    found=None
    for y in range(0,32,8):
        for x in range(0,32,8):
            for flip in range(4):
                patch=water[y:y+8,x:x+8];patch=patch[:,::-1] if flip&1 else patch;patch=patch[::-1] if flip&2 else patch
                if np.array_equal(rgb,patch):found=x,y,flip
    if found is None:continue
    assert all(np.array_equal(np.array(b.pals[p>=6][p],np.uint8)[tile],rgb) for p in banks),(tid,'shared differently colored tile')
    x,y,flip=found;frames=[]
    for frame in range(8):
        patch=np.roll(water,-frame*4,axis=1)[y:y+8,x:x+8]
        patch=patch[:,::-1] if flip&1 else patch;patch=patch[::-1] if flip&2 else patch
        indices=[pal.index(tuple(c),1) for c in patch.reshape(-1,3)]
        frames.append(bytes(indices[i]|indices[i+1]<<4 for i in range(0,64,2)))
    plans.append(dict(tile=tid,frames=frames))
assert 0<len(plans)<=20,len(plans)
data='// Pallet water: eight phases of the original converted HGSS texture.\n'
for p in plans:
    data+=f'static const u16 sPalletWater{p["tile"]}[8][16] = {{\n'
    for frame in p['frames']:
        data+='    {'+','.join(f'0x{int.from_bytes(frame[i:i+2],"little"):04x}' for i in range(0,32,2))+'},\n'
    data+='};\n'
(E/'data/tilesets/primary/palletoutdoor/water_animation.inc').write_text(data)
code='\n// BEGIN PALLET WATER\n#include "../data/tilesets/primary/palletoutdoor/water_animation.inc"\nstatic void TilesetAnim_PalletOutdoor(u16 timer)\n{\n    u16 frame = (timer / 8) % 8;\n    if (timer % 8 != 0) return;\n'
for p in plans:code+=f'    AppendTilesetAnimToBuffer(sPalletWater{p["tile"]}[frame], (u16 *)(BG_VRAM + TILE_OFFSET_4BPP({p["tile"]})), TILE_SIZE_4BPP);\n'
code+='}\nvoid InitTilesetAnim_PalletOutdoor(void)\n{\n    sPrimaryTilesetAnimCounter = 0;\n    sPrimaryTilesetAnimCounterMax = 64;\n    sPrimaryTilesetAnimCallback = TilesetAnim_PalletOutdoor;\n}\n// END PALLET WATER\n'
p=E/'src/tileset_anims.c';s=p.read_text()
if '// BEGIN PALLET WATER' in s:s=s[:s.index('// BEGIN PALLET WATER')].rstrip()+'\n'
p.write_text(s+code)
p=E/'src/data/tilesets/headers.h';s=p.read_text();start=s.index('const struct Tileset gTileset_PalletOutdoor =');end=s.index('};',start)
block=s[start:end].replace('.callback = NULL','.callback = InitTilesetAnim_PalletOutdoor')
s=s[:start]+block+s[end:]
if 'void InitTilesetAnim_PalletOutdoor(void);' not in s:s=s[:start]+'void InitTilesetAnim_PalletOutdoor(void);\n'+s[start:]
p.write_text(s)
(A/'source/water-animation.json').write_text(json.dumps(dict(tiles=[p['tile'] for p in plans],tile_frames={str(p['tile']):[f.hex() for f in p['frames']] for p in plans},frames=8,frames_per_phase=8,
    derivation='UV scroll of converted original HGSS water texture; timing is a native adaptation',shore_fixed=True),indent=2)+'\n')
print('Animated HGSS water tiles',len(plans))
