"""Keep Pallet's inlet as water beyond the camera edge without changing other maps."""
from pathlib import Path
import sys,struct,json
ROOT=Path(__file__).resolve().parents[4];E=Path(sys.argv[1]);S=ROOT/'gba/art/pallet-native/source'
sys.path.insert(0,str(ROOT/'tools/gba/maps/pallet_rebuild'))
from native import words
w=h=36;grid=words(E/'data/layouts/ApocPalletTown/map.bin');out=[]
for by in range(64):
 y=by if by<43 else by-64
 for bx in range(64):
  x=bx if bx<44 else bx-64
  if y>=36:
   sx=max(0,min(35,x));sy=34+(y%2)
  elif y<0:
   sx=max(0,min(35,x));sy=2+(y%2)
  else:
   sx=(x%2) if x<0 else 34+(x%2) if x>=36 else x;sy=y
  out.append(grid[sy*w+sx]&1023)
(E/'data/layouts/ApocPalletTown/camera_border.bin').write_bytes(struct.pack('<4096H',*out))
p=E/'src/fieldmap.c';s=p.read_text();needle='static inline u16 GetBorderBlockAt(int x, int y)'
if 'sPalletCameraBorder' not in s:
 s=s.replace(needle,'// Pallet has a southern inlet; its camera border preserves the coastline.\nstatic const u16 sPalletCameraBorder[] = INCBIN_U16("data/layouts/ApocPalletTown/camera_border.bin");\n\n'+needle)
 needle2='    if (mapLayout->isFrlg)'
 s=s.replace(needle2,'    if (gMapHeader.mapLayoutId == LAYOUT_APOC_PALLET_TOWN)\n    {\n        u32 bx = (x - MAP_OFFSET + 64) % 64;\n        u32 by = (y - MAP_OFFSET + 64) % 64;\n        return sPalletCameraBorder[by * 64 + bx] | MAPGRID_IMPASSABLE;\n    }\n\n'+needle2,1)
 p.write_text(s)
(S/'camera-border.json').write_text(json.dumps(dict(width=64,height=64,coordinate_origin=[0,0],wrap=64,scope='LAYOUT_APOC_PALLET_TOWN only',off_map_collision='impassable',southern_coastline='continues last two native rows'),indent=2)+'\n')
