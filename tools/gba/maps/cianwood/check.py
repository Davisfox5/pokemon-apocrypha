"""Audit decoded native Cianwood art, cell behavior, reachability and preservation."""
from pathlib import Path
from collections import deque
import json,sys,struct,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=ROOT/'gba/art/cianwood-city'
sys.path.insert(0,str(HERE.parent))
from tiles import Tileset

def main(g):
    t=Tileset(g,'cianwood','cianwood');grid=np.frombuffer((g/'data/layouts/CianwoodCity/map.bin').read_bytes(),'<u2').reshape(42,35)
    image=t.map_image(grid.ravel().tolist(),35);image.save(OUT/'evidence/native.png')
    ledger=json.loads((OUT/'evidence/material-traversal-ledger.json').read_text())['cells'];assert len(ledger)==1470
    patterns=set();banks=set()
    for c in ledger:
        x,y=c['x'],c['y'];v=int(grid[y,x]);mid=v&1023
        assert mid==c['metatile']
        attr=t.attrs[mid>=512][mid%512];assert attr&255==c['behavior']
        actual='blocked' if v&0xc00 else 'water' if attr&255==16 else 'open'
        assert actual==c['foot'],(x,y,actual,c)
        for e in t.blocks[mid>=512][mid%512]:
            patterns.add(e&1023);banks.add(e>>12);assert e&1023<1008 and e>>12<12
    # Read the real stored upper-layer pixels, not a pre-conversion mockup.
    ci=np.asarray(Image.open(ROOT/'gba/art/cherrygrove-synthesis/refined/center.png'))
    center_pixels=0
    for y,x in zip(*np.nonzero(ci)):
        gx,gy=352+int(x),496+int(y);mid=int(grid[gy//16,gx//16]&1023)
        q=(gy%16//8)*2+gx%16//8;e=t.blocks[mid>=512][mid%512][4+q];assert e>>12==8
        tid=e&1023;xx,yy=gx%8,gy%8
        if e&1024:xx=7-xx
        if e&2048:yy=7-yy
        assert t.tiles[tid>=512][tid%512][yy*8+xx]==ci[y,x],(x,y)
        center_pixels+=1
    assert (g/'data/tilesets/secondary/cianwood/palettes/08.pal').read_text().splitlines()==(g/'data/tilesets/secondary/cherrygrove/palettes/08.pal').read_text().splitlines()
    def open_cell(x,y):return 0<=x<35 and 0<=y<42 and not grid[y,x]&0xc00 and grid[y,x]>>12!=1
    reached={(15,20)};q=deque(reached)
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            p=x+dx,y+dy
            if p not in reached and open_cell(*p):reached.add(p);q.append(p)
    approaches=[(7,10),(10,27),(20,25),(21,31),(10,35),(17,37),(25,37),(9,18)]
    for p in approaches:assert p in reached,('unreachable approach',p)
    assert not open_cell(8,18) and not open_cell(30,32)
    # Stable old IDs and old source paths, including accepted shared art.
    before=json.loads(subprocess.check_output(['git','-C',str(g),'show','HEAD:data/maps/map_groups.json']))
    groups=json.loads((g/'data/maps/map_groups.json').read_text())
    for key,values in before.items():
        if isinstance(values,list):assert groups[key][:len(values)]==values
    allowed={'data/event_scripts.s','data/layouts/layouts.json','data/maps/map_groups.json','include/regions.h','src/apocrypha_map_proof.c','src/data/region_map/region_map_sections.json','src/data/tilesets/graphics.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'}
    changed=subprocess.check_output(['git','-C',str(g),'diff','--name-only'],text=True).splitlines()
    prefixes=('data/layouts/CianwoodCity/','data/maps/CianwoodCity/','data/maps/CianwoodPokemonCenter/','data/maps/CianwoodCenterUpstairs/','data/tilesets/primary/cianwood/','data/tilesets/secondary/cianwood/')
    unexpected=[p for p in changed if p not in allowed and not p.startswith(prefixes)]
    assert not unexpected,unexpected
    compare=Image.new('RGB',(1120,720),(28,35,43));d=ImageDraw.Draw(compare)
    d.text((12,10),'HGSS ORIGINAL — 550 x 671, no rescaling',fill='white');d.text((572,10),'DECODED GEN 3 SOURCE — 35 x 42 cells',fill='white')
    compare.paste(Image.open(OUT/'references/cianwood-hgss.png'),(0,40));compare.paste(image,(560,40));compare.save(OUT/'evidence/original-native.png')
    gridview=image.resize((1120,1344),Image.Resampling.NEAREST);d=ImageDraw.Draw(gridview)
    for x in range(35):d.line((x*32,0,x*32,1344),fill=(75,80,90));d.text((x*32+2,2),str(x),fill='white',stroke_fill='black',stroke_width=1)
    for y in range(42):d.line((0,y*32,1120,y*32),fill=(75,80,90));d.text((1,y*32+3),str(y),fill='white',stroke_fill='black',stroke_width=1)
    gridview.save(OUT/'evidence/native-grid.png')
    result=dict(cells_audited=1470,graphics_patterns=len(patterns),highest_tile=max(patterns),palette_banks=sorted(banks),reachable_foot_cells=len(reached),reachable_approaches=approaches,approved_center_pixels_exact=center_pixels,existing_ids_preserved=True,existing_map_and_art_sources_unchanged=True)
    (OUT/'evidence/native-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
