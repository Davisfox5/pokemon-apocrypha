#!/usr/bin/env python3
"""Connect the isolated artwork study through native directional route warps."""
from pathlib import Path
import json,struct,shutil
from tiles import Tileset
R=Path(__file__).resolve().parents[3];B=R/'tools/vendor/gba/johto-restart-game';G=R/'tools/vendor/gba/cherrygrove-art-study-work'
for file in ['metatiles.bin','metatile_attributes.bin']:
 shutil.copy2(B/'data/tilesets/secondary/cherrygrove'/file,G/'data/tilesets/secondary/cherrygrove'/file)
for name,x,y,beh,dest in [('CherrygroveRoute30Approach',44,17,0x65,8),('CherrygroveRoute29Approach',0,18,0x63,9)]:
 p=G/'data/maps'/name/'map.json';data=json.loads((B/'data/maps'/name/'map.json').read_text());data['connections']=[]
 data['warp_events'].append(dict(x=x,y=y,elevation=0,dest_map='MAP_CHERRYGROVE_CITY',dest_warp_id=str(dest)));p.write_text(json.dumps(data,indent=2)+'\n')
 t=Tileset(G,'cherrygrove','cherrygrove');lp=G/'data/layouts'/name/'map.bin';raw=(B/'data/layouts'/name/'map.bin').read_bytes();grid=list(struct.unpack('<'+'H'*(len(raw)//2),raw));layouts=json.loads((G/'data/layouts/layouts.json').read_text());w=next(r['width'] for r in layouts['layouts'] if r['name']==name+'_Layout');mid=grid[y*w+x]&1023;f=G/'data/tilesets/secondary/cherrygrove';new=512+len(t.blocks[1])
 with (f/'metatiles.bin').open('ab') as h:h.write(struct.pack('<8H',*t.blocks[mid>=512][mid%512]))
 with (f/'metatile_attributes.bin').open('ab') as h:h.write(struct.pack('<H',0x1000|beh))
 grid[y*w+x]=new|0x3000;lp.write_bytes(struct.pack('<'+'H'*len(grid),*grid))
