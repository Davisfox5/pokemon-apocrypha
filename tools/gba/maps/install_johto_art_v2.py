#!/usr/bin/env python3
"""Install the revised generated-source buildings and the existing tree into an isolated town checkout."""
import json, struct, sys, shutil, subprocess
from pathlib import Path
from PIL import Image
from tiles import Tileset

ROOT=Path(__file__).resolve().parents[3]
game=Path(sys.argv[1]).resolve()
assert game != ROOT/'game' and game != ROOT/'tools/vendor/gba/cherrygrove-game'
assert (game/'.git').is_dir()
assert not subprocess.check_output(['git','-C',str(game),'status','--porcelain'],text=True).strip(), 'Use a clean town baseline; preserve edits first.'
ART=ROOT/'gba/art/johto-v2'; native=ART/'native'
ts=Tileset(game,'cherrygrove','cherrygrove');folder=ts.dirs[1]
tiles=[bytes(t) for t in ts.tiles[1]];lookup={t:512+i for i,t in enumerate(tiles)}
blocks=list(ts.blocks[1]);attrs=list(ts.attrs[1]);assets={}
def tile(data,bank):
    data=bytes(data)
    if data not in lookup:lookup[data]=512+len(tiles);tiles.append(data)
    return lookup[data] | bank<<12
def block(im,x,y,banks,attr=0):
    entries=list(ts.blocks[0][1][:4])
    entries += [tile(im.crop((x+dx,y+dy,x+dx+8,y+dy+8)).getdata(),banks[((y+dy)//8)*(im.width//8)+(x+dx)//8])
                for dx,dy in [(0,0),(8,0),(0,8),(8,8)]]
    mid=512+len(blocks);blocks.append(entries);attrs.append(attr);return mid
for a in json.loads((native/'manifest.json').read_text())['assets']:
    n=a['name'];w=a['width'];h=a['height'];banks=a['tile_palette_banks']
    packed=(native/(n+'.4bpp')).read_bytes()
    assert len(packed)==w*h//2
    im=Image.new('P',(w,h))
    for i in range(len(packed)//32):
        data=[v for byte in packed[i*32:(i+1)*32] for v in (byte&15,byte>>4)]
        part=Image.new('P',(8,8));part.putdata(data)
        im.paste(part,((i%(w//8))*8,(i//(w//8))*8))
    rows=[[block(im,x,y,banks) for x in range(0,w,16)] for y in range(0,h,16)]
    assets[n]=rows
for bank in [8,10]:shutil.copy2(native/f'{bank:02}.pal',folder/'palettes'/f'{bank:02}.pal')
shutil.copy2(native/'tree.pal',folder/'palettes/06.pal')
mapfile=game/'data/layouts/CherrygroveCity/map.bin'
grid=list(struct.unpack('<1760H',mapfile.read_bytes()));before=list(grid);W=44
def stamp(x,y,rows,door=None,old_door=None):
    for dy,row in enumerate(rows):
        for dx,mid in enumerate(row):
            grid[(y+dy)*W+x+dx]=0x3c00|mid
    if door:
        x,y=door;index=y*W+x;mid=grid[index]&1023
        # Shared object metatile retains the engine's animated-door behavior.
        attrs[mid-512]=ts.attrs[old_door>=512][old_door-512 if old_door>=512 else old_door]
        grid[index]=mid  # same elevation/collision bits as the town's old door
spec=json.loads((ROOT/'gba/maps/cherrygrove/town.json').read_text())
for b in spec['buildings']:
    if b['style']=='house':stamp(b['x'],b['y']-1,assets['house'],b['door'],0x21)
    if b['style']=='center':stamp(b['x']-1,b['y']-1,assets['center'],b['door'],0x61)
tree_old=[0x1d4,0x1d5,0x1e4,0x1e5,0x1f4,0x1f5]
tree_new=sum(assets['tree'],[]);replacement=dict(zip(tree_old,tree_new))
for i,m in enumerate(grid):
    if m&1023 in replacement:grid[i]=(m&~1023)|replacement[m&1023]
assert len(tiles)<=512 and len(blocks)<=512
sheet=Image.new('P',(128,((len(tiles)+15)//16)*8));sheet.putpalette(Image.open(folder/'tiles.png').getpalette())
for i,t in enumerate(tiles):
    part=Image.new('P',(8,8));part.putdata(t);sheet.paste(part,((i%16)*8,(i//16)*8))
sheet.save(folder/'tiles.png')
(folder/'metatiles.bin').write_bytes(struct.pack('<'+'H'*(len(blocks)*8),*[e for b in blocks for e in b]))
(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
mapfile.write_bytes(struct.pack('<1760H',*grid))
evidence=ART/'evidence';evidence.mkdir(exist_ok=True)
Tileset(game,'cherrygrove','cherrygrove').map_image(grid,W).save(evidence/'town-overview.png')
manifest=dict(baseline_commit=subprocess.check_output(['git','-C',str(game),'rev-parse','HEAD'],text=True).strip(),
    secondary_tiles=len(tiles),secondary_tile_capacity=512,secondary_metatiles=len(blocks),secondary_metatile_capacity=512,
    changed_map_cells=sum(a!=b for a,b in zip(before,grid)),asset_metatiles=assets,
    note='Original generated house/Center proportions preserved at 80x80. Roofs extend one metatile north; Center extends one west, with existing door coordinates preserved. Building tiles choose banks 8/10; tree remains bank 6.')
(evidence/'integration.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
