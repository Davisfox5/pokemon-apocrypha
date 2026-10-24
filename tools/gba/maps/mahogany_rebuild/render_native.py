"""Render one actual Emerald or FRLG native layout, including its palette split."""
from pathlib import Path
import json,re
import numpy as np
from PIL import Image

def render(g,name):
    m=json.loads((g/'data/maps'/name/'map.json').read_text())
    l=next(v for v in json.loads((g/'data/layouts/layouts.json').read_text())['layouts'] if v['id']==m['layout'])
    headers=(g/'src/data/tilesets/graphics.h').read_text()
    definitions=(g/'src/data/tilesets/headers.h').read_text()
    ds=[]
    for sym in (l['primary_tileset'],l['secondary_tileset']):
        definition=re.search(r'\b'+sym+r'\s*=\s*\{([^}]+)\}',definitions).group(1)
        sym=re.search(r'\.tiles\s*=\s*(\w+)',definition).group(1)
        match=re.search(r'\b'+sym+r'\[\].*?"(data/tilesets/[^\"]+)/tiles.png"',headers)
        ds.append(g/match.group(1))
    frlg=l.get('layout_version')=='frlg';split=640 if frlg else 512;pal_split=7 if frlg else 6
    tiles=[];metas=[];pals=[]
    for d in ds:
        a=np.array(Image.open(d/'tiles.png'))&15
        tiles.append([a[y:y+8,x:x+8] for y in range(0,a.shape[0],8) for x in range(0,a.shape[1],8)])
        metas.append(np.frombuffer((d/'metatiles.bin').read_bytes(),'<u2').reshape(-1,8))
        pals.append([np.array([list(map(int,s.split())) for s in (d/'palettes'/f'{b:02}.pal').read_text().splitlines()[3:19]],np.uint8) for b in range(16)])
    grid=np.frombuffer((g/l['blockdata_filepath']).read_bytes(),'<u2').reshape(l['height'],l['width'])
    out=np.zeros((l['height']*16,l['width']*16,3),np.uint8)
    for y,x in np.ndindex(grid.shape):
        mid=int(grid[y,x]&1023);entries=metas[mid>=split][mid%split if mid<split else mid-split]
        for i,e in enumerate(entries):
            e=int(e);tid=e&1023;bank=e>>12;ix=tiles[tid>=split][tid if tid<split else tid-split]
            if e&1024:ix=ix[:,::-1]
            if e&2048:ix=ix[::-1]
            py=y*16+(i%4//2)*8;px=x*16+(i%2)*8;mask=ix>0 if i>=4 else np.ones((8,8),bool)
            out[py:py+8,px:px+8][mask]=pals[bank>=pal_split][bank][ix[mask]]
    return Image.fromarray(out)
