#!/usr/bin/env python3
"""Compile revision 3 in the isolated town baseline, with context-aware scenery.

The artwork is generated/source artwork, not drawn here. This compiler samples
the new tree, preserves v2 buildings, composes existing native scenery, and packs
the actual visible pixels into two legal 4bpp layers without losing backgrounds.
"""
import hashlib, itertools, json, shutil, struct, subprocess, sys
from pathlib import Path
from PIL import Image
from tiles import Tileset, palette

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'gba/art/johto-v3'
OUT = ART / 'native'
EVIDENCE = ART / 'evidence'
SPEC = ROOT / 'gba/maps/cherrygrove/town-v3.json'
game = Path(sys.argv[1]).resolve()
assert game == ROOT / 'tools/vendor/gba/johto-art-v3-game', 'Use the dedicated revision 3 checkout.'
assert subprocess.check_output(['git','-C',str(game),'rev-parse','HEAD'], text=True).strip() == 'f09ec1de2e6754e9f9a8e02281d3d773efcfa65e'
# Repeatable against immutable town source; never consume a previous generated tileset.
base = ROOT / 'tools/vendor/gba/johto-art-v3-baseline'
assert (base / '.git').exists(), 'Create a clean shared town-baseline clone first.'
assert not subprocess.check_output(['git','-C',str(base),'status','--porcelain'],text=True).strip()
ts = Tileset(base, 'cherrygrove', 'cherrygrove')
spec = json.loads(SPEC.read_text())
W, H = spec['width'], spec['height']
pals = {b: ts.pals[b>=6][b] for b in range(13)}
grass = sorted(c for _, c in ts.render(1).getcolors())
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)

# Import one crown, at a compact native scale, preserving its aspect ratio.
src = ART / 'generated/tree.png'
im = Image.open(src).convert('RGBA')
alpha = im.getchannel('A').point(lambda a: 255 if a >= 224 else 0)
bounds = alpha.getbbox()
im.putalpha(alpha)
im = im.crop(bounds)
scale = min(32/im.width, 40/im.height)
im = im.resize(tuple(round(v*scale) for v in im.size), Image.Resampling.NEAREST)
canvas = Image.new('RGBA', (32,48))
canvas.paste(im, ((32-im.width)//2,48-im.height))
visible = [p[:3] for p in canvas.getdata() if p[3]]
strip = Image.new('RGB', (len(visible),1)); strip.putdata(visible)
quant = strip.quantize(colors=12, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
qp = quant.getpalette()
tree_colors = []
for i in sorted(set(quant.getdata())):
    c = tuple(round(qp[i*3+j]*31/255)*255//31 for j in range(3))
    if c not in tree_colors: tree_colors.append(c)
# Grass colors remain exact so a tree and its grass can share a background layer
# behind a building. No new palette bank or lossy building conversion is needed.
pals[6] = [(0,0,0)] + tree_colors + grass
pals[6] += [(0,0,0)] * (16-len(pals[6]))
data = [0 if not p[3] else 1+min(range(len(tree_colors)), key=lambda i:sum((p[j]-tree_colors[i][j])**2 for j in range(3))) for p in canvas.getdata()]
tree = Image.new('P',(32,48));tree.putpalette([v for c in pals[6] for v in c]+[0]*720);tree.putdata(data)
tree.save(OUT/'tree.png',transparency=0)
packed = bytes(t[i]|t[i+1]<<4 for y in range(0,48,8) for x in range(0,32,8)
               for t in [list(tree.crop((x,y,x+8,y+8)).getdata())] for i in range(0,64,2))
(OUT/'tree.4bpp').write_bytes(packed)
for b in [8,10]: pals[b] = palette(ROOT/f'gba/art/johto-v2/native/{b:02}.pal')

def entries(mid): return ts.blocks[mid>=512][mid-512 if mid>=512 else mid]
def attr(mid): return ts.attrs[mid>=512][mid-512 if mid>=512 else mid]
def entry_pixels(e):
    tid=e&1023;t=ts.tiles[tid>=512][tid-512 if tid>=512 else tid]
    colors=ts.pals[(e>>12)>=6][e>>12]
    return [None if not (v:=t[(7-y if e&2048 else y)*8+(7-x if e&1024 else x)]) else colors[v]
            for y in range(8) for x in range(8)]

def native_pixels(mid, foreground=False, erase=()):
    pixels = [None]*256
    for layer in range(2):
        for q in range(4):
            for i,c in enumerate(entry_pixels(entries(mid)[layer*4+q])):
                if c is not None:
                    pixels[((q//2)*8+i//8)*16+(q%2)*8+i%8]=c
    if foreground: pixels=[None if c in erase else c for c in pixels]
    return pixels

grid=[1]*(W*H);flags=[0x3000]*(W*H);attributes=[0]*(W*H)
pixels=[native_pixels(1) for _ in grid]
overlaps=[];objects=[]
def put(x,y,mid,solid=False):
    if 0<=x<W and 0<=y<H:
        i=y*W+x;grid[i]=mid
        pixels[i]=[a if b is None else b for a,b in zip(pixels[i],native_pixels(mid))]
        flags[i]=0x3c00 if solid else 0x3000;attributes[i]=attr(mid)
def rect(x,y,w,h,mid,solid=False):
    for yy in range(y,y+h):
        for xx in range(x,x+w):put(xx,yy,mid,solid)
def overlay(x,y,w,h,source,name,solid=True):
    assert len(source)==w*h
    preserved=0;covered=0;non_grass_preserved=0
    for yy in range(h):
        for xx in range(w):
            gx=x*16+xx;gy=y*16+yy
            if not (0<=gx<W*16 and 0<=gy<H*16): continue
            i=(gy//16)*W+gx//16;j=(gy%16)*16+gx%16;c=source[yy*w+xx]
            if c is None:
                preserved+=1
                non_grass_preserved+=pixels[i][j] not in grass
                continue
            pixels[i][j]=c;covered+=1
            if solid:flags[i]=0x3c00;attributes[i]=0
    overlaps.append(dict(name=name,transparent_pixels_preserved=preserved,
                         non_grass_background_pixels_preserved=non_grass_preserved,opaque_pixels=covered))
    objects.append(dict(name=name,x=x,y=y,width=w,height=h))
def native_object(x,y,rows,name,erase=grass,solid=True):
    w=len(rows[0])*16;h=len(rows)*16;source=[None]*(w*h)
    for dy,row in enumerate(rows):
        for dx,mid in enumerate(row):
            block=native_pixels(mid,True,erase)
            for yy in range(16):source[(dy*16+yy)*w+dx*16:(dy*16+yy)*w+dx*16+16]=block[yy*16:yy*16+16]
    overlay(x,y,w,h,source,name,solid)

# HGSS geography: ocean occupies the west, not a thin moat around the town.
rect(0,0,W,H,0x170,True)
rect(0,0,38,6,1,True)
# North cliff and a narrow strip of beach at its foot.
rect(0,6,31,1,0x157,True)
for x in range(31):
    put(x,7,0x1f8 if x%2==0 else 0x1f9,True)
    put(x,8,0x189,True)
rect(0,9,31,1,0x170,True)
# Curved east bank. Staggered west-facing beach edge converges on a southern lip.
coast = [31]*10+[30]*3+[29]*3+[28]*3+[27]*3+[26]*4+[27]*3+[28]*2+[29]*3+[38]*6
for y,left in enumerate(coast):
    rect(left,y,W-left,1,1)
    if 10<=y<34:
        rect(left,y,3,1,0x121)
        put(left-1,y,0x123,True)
        put(left+2,y,0x122)
    if 34<=y: rect(38,y,W-38,1,1,True)
# Beach curves east at the south end; the waterfront fits inside this bay.
rect(29,31,10,3,0x121)
for x in range(29,38):put(x,34,0x12c,True)
# Offshore rocky island and a separate small sandbar, as in the reference.
rect(7,17,5,2,0x10c,True)
for x in range(7,12):put(x,19,0x157,True);put(x,20,0x1f8 if x%2==0 else 0x1f9,True);put(x,21,0x189,True)
for y in range(17,21):put(6,y,0x187,True);put(12,y,0x16f,True)
put(6,21,0x188,True);put(12,21,0x18a,True)
rect(17,28,4,2,0x121,True)
for x in range(17,21):put(x,27,0x11c,True);put(x,30,0x12c,True)
for y in range(28,30):put(16,y,0x123,True);put(21,y,0x125,True)
for x,y in [(4,15),(14,15),(8,24),(23,31),(25,29),(13,35)]:put(x,y,0x18c,True)

# Native paths, all placed before objects so they remain behind transparency.
path=set()
def lane(x,y,w,h):path.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
lane(38,0,4,32);lane(36,10,23,3);lane(38,21,26,4)
lane(35,17,5,3);lane(45,8,3,4);lane(55,9,3,14)
lane(35,29,5,3);lane(48,21,3,8);lane(57,29,3,4)
lane(39,30,20,3);lane(29,31,11,3)
for x,y in path:
    n=(x,y-1) in path;s=(x,y+1) in path;w=(x-1,y) in path;e=(x+1,y) in path
    mid=0x121
    if not n:mid=0x119
    if not s:mid=0x129
    if not w:mid=0x120 if n and s else (0x118 if not n else 0x128)
    if not e:mid=0x122 if n and s else (0x11a if not n else 0x12a)
    put(x,y,mid)
rect(46,23,7,3,0x10c)

# Compose individual trees in depth order. No metatile-id substitution, duplicated
# crowns, or grass-filled rectangular stamps. Foliage can overlap other foliage.
tree_pixels=[None if not i else pals[6][i] for i in data]
positions=set()
for y in [0,2]:
    positions.update((x,y) for x in range(0,38,2))
    positions.update((x,y) for x in range(42,64,2))
positions.update((x,3) for x in [42,48,50,52,58,60,62])
positions.update((62,y) for y in range(5,38,3) if not 20<=y<=25)
positions.update((x,y) for y in [34,36] for x in range(38,64,2))
for x,y in sorted(positions,key=lambda p:(p[1],p[0])):overlay(x,y,32,48,tree_pixels,'tree')

# Existing pink trees are single crowns; extract only their artwork, preserving
# the surrounding path/ground and previously placed trees around the silhouette.
blossoms=json.loads((ROOT/'gba/evidence/cherrygrove/layout-manifest.json').read_text())['blossom_metatiles']
pinkrows=[[blossoms[str(m)] for m in row] for row in [[0x1d4,0x1d5],[0x1e4,0x1e5],[0x1f4,0x1f5]]]
for x,y in [(42,26),(45,27),(42,30),(47,30),(30,17),(51,13),(59,10)]:native_object(x,y,pinkrows,'blossom-tree')

# Preserve the exact v2 building pixels and their two palettes.
building_pixels={}
for name in ['house','center']:
    a=Image.open(ROOT/f'gba/art/johto-v2/native/{name}.png').convert('RGBA')
    building_pixels[name]=[None if not p[3] else p[:3] for p in a.getdata()]
    shutil.copy2(ROOT/f'gba/art/johto-v2/native/{name}.png',OUT/f'{name}.png')
mart=[[0x30,0x31,0x32,0x33],[0x38,0x39,0x3a,0x3b],[0x60,0x41,0x42,0x43]]
building_checks=[]
for b in spec['buildings']:
    if b['style']=='mart':native_object(b['x'],b['y'],mart,'Mart')
    else:
        source=building_pixels[b['style']]
        before=[list(p) for p in pixels]
        overlay(b['x'],b['y'],80,80,source,b['name'])
        # Check both invariants at every source pixel, including transparent edges.
        for yy in range(80):
            for xx in range(80):
                gx=b['x']*16+xx;gy=b['y']*16+yy;i=(gy//16)*W+gx//16;j=(gy%16)*16+gx%16
                c=source[yy*80+xx]
                assert pixels[i][j] == (before[i][j] if c is None else c)
        building_checks.append(b['name'])
    x,y=b['door'];i=y*W+x
    flags[i]=0;attributes[i]=attr(0x21 if b['style']=='house' else 0x61 if b['style']=='center' else 0x41)

# Native waterfront props. Their transparent portions inherit sand/water/deck.
oldgrid=struct.unpack('<1760H',(base/'data/layouts/CherrygroveCity/map.bin').read_bytes())
def old(x,y):return oldgrid[y*44+x]&1023
deck=old(21,33);rail=old(21,38)
rect(29,32,3,6,deck)
rect(29,38,3,1,rail,True)
rect(25,23,3,4,deck)
rect(25,26,3,1,rail,True)
water_colors=sorted(c for _,c in ts.render(0x170).getcolors())
boatrows=[[old(x,y) for x in range(17,20)] for y in range(35,37)]
native_object(25,35,boatrows,'west-boat',erase=water_colors)
native_object(33,35,boatrows,'east-boat',erase=water_colors)
native_object(35,32,[[old(27,31),old(28,31)]],'drying-nets',erase=sorted(c for _,c in ts.render(0x121).getcolors()))
chairrows=[[old(x,y) for x in range(10,12)] for y in range(9,11)]
native_object(44,30,chairrows,'park-seating')
for x,y in [(37,19),(42,2),(61,20),(53,26),(32,31)]:native_object(x,y,[[3]],'sign')
for x,y in [(33,18),(37,18),(46,22),(50,22),(56,30),(60,30),(44,29),(46,31)]:native_object(x,y,[[4]],'flowers',solid=False)

# Encode the final visible pixels exactly, selecting at most two existing palette
# banks per 8x8 quadrant. The bottom bank is also opaque under the foreground;
# every transparent source pixel keeps the already composed scenery behind it.
palette_maps={b:{c:i for i,c in reversed(list(enumerate(p))) if i} for b,p in pals.items()}
palette_sets={b:set(m) for b,m in palette_maps.items()}
# General's animation callback writes these VRAM slots after load. Matching a
# static tile's current pixels is not sufficient to make an animated slot reusable.
animated=set(range(432,462))|set(range(464,474))|set(range(480,490))|set(range(496,502))|set(range(508,512))
tile_lookup={}
for i,t in enumerate(ts.tiles[0]):
    if i not in animated:tile_lookup.setdefault(bytes(t),i)
newtiles=[]
def tile_entry(data,bank):
    raw=bytes(data)
    if raw not in tile_lookup:tile_lookup[raw]=512+len(newtiles);newtiles.append(raw)
    return tile_lookup[raw]|bank<<12
def encode_quad(colors):
    used=set(colors)
    choices=[(a,) for a in range(13) if used<=palette_sets[a]]
    if not choices:choices=[(a,b) for a,b in itertools.combinations(range(13),2) if used<=palette_sets[a]|palette_sets[b]]
    assert choices, ('More than two palette banks required',used)
    def cost(choice):
        a=choice[0];b=choice[-1]
        low=bytes(palette_maps[a].get(c,0) for c in colors)
        high=bytes(0 if c in palette_sets[a] else palette_maps[b][c] for c in colors)
        return (int(low not in tile_lookup)+int(high not in tile_lookup),len(choice),choice)
    choice=min(choices,key=cost);a=choice[0];b=choice[-1]
    return (tile_entry([palette_maps[a].get(c,0) for c in colors],a),
            tile_entry([0 if c in palette_sets[a] else palette_maps[b][c] for c in colors],b))
blocks=[];attrs=[];block_lookup={};final=[];animated_underlays=0
for idx,p in enumerate(pixels):
    original=entries(grid[idx])
    if p==native_pixels(grid[idx]) and all((e&1023)<512 and (e>>12) not in (6,8,10) for e in original):
        # Retain original terrain references, including intentional water animation.
        ent=tuple(original)
    else:
        parts=[]
        for q,(dx,dy) in enumerate([(0,0),(8,0),(0,8),(8,8)]):
            colors=[p[(dy+y)*16+dx+x] for y in range(8) for x in range(8)]
            low=entry_pixels(original[q]);upper=entry_pixels(original[4+q])
            delta=[None if a==b else a for a,b in zip(colors,low)]
            required=set(delta)-{None}
            banks=[b for b in range(13) if required<=palette_sets[b]]
            if (original[q]&1023)<512 and (original[q]>>12) not in (6,8,10) and None not in low and not any(upper) and banks:
                bank=banks[0]
                parts.append((original[q],tile_entry([0 if c is None else palette_maps[bank][c] for c in delta],bank)))
                animated_underlays+=(original[q]&1023) in animated
            else:parts.append(encode_quad(colors))
        ent=tuple(v[0] for v in parts)+tuple(v[1] for v in parts)
        assert all((e&1023) not in animated for e in ent[4:]), 'Static foreground aliases animated VRAM'
        assert all((e&1023) not in animated or e==original[q] for q,e in enumerate(ent[:4])), 'Only the original terrain may use animated VRAM'
    key=(ent,attributes[idx])
    if key not in block_lookup:block_lookup[key]=512+len(blocks);blocks.append(ent);attrs.append(attributes[idx])
    final.append(flags[idx]|block_lookup[key])
assert len(newtiles)<=512,('tile capacity',len(newtiles))
assert len(blocks)<=512,('metatile capacity',len(blocks))
folder=game/'data/tilesets/secondary/cherrygrove'
sheet=Image.new('P',(128,((len(newtiles)+15)//16)*8));sheet.putpalette(Image.open(ts.dirs[1]/'tiles.png').getpalette())
for i,t in enumerate(newtiles):
    part=Image.new('P',(8,8));part.putdata(t);sheet.paste(part,(i%16*8,i//16*8))
sheet.save(folder/'tiles.png')
for b in range(6,13):
    text='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n'
    (folder/f'palettes/{b:02}.pal').write_text(text)
    (OUT/f'{b:02}.pal').write_text(text)
(folder/'metatiles.bin').write_bytes(struct.pack('<'+'H'*(len(blocks)*8),*[e for b in blocks for e in b]))
(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
mapfile=game/'data/layouts/CherrygroveCity/map.bin'
mapfile.write_bytes(struct.pack('<'+'H'*len(final),*final))
layouts=json.loads((base/'data/layouts/layouts.json').read_text())
for l in layouts['layouts']:
    if l['id']=='LAYOUT_CHERRYGROVE_CITY':l['width']=W;l['height']=H
    if l['id']=='LAYOUT_CHERRYGROVE_ROUTE30_APPROACH':l['width']=W
(game/'data/layouts/layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')

# Stable map IDs, scripts and reciprocal warp indices; only coordinates move.
town=json.loads((base/'data/maps/CherrygroveCity/map.json').read_text())
for b,event in zip(spec['buildings'],town['warp_events']):event['x'],event['y']=b['door']
for event in town['object_events']:
    event['x'],event['y']=(33,32) if 'Waterfront' in event['script'] else (52,21)
sign_positions=[(37,19),(42,2),(61,20),(53,26),(32,31)]
for event,pos in zip(town['bg_events'],sign_positions):event['x'],event['y']=pos
(game/'data/maps/CherrygroveCity/map.json').write_text(json.dumps(town,indent=2)+'\n')
for name,w,h,side in [('CherrygroveRoute29Approach',16,H,'east'),('CherrygroveRoute30Approach',W,12,'north')]:
    g=[0x3c0e]*(w*h)
    for y in range(h):
        for x in range(w):
            if (side=='east' and 22<=y<26 and x<12) or (side=='north' and 38<=x<42 and y>=4):g[y*w+x]=0x3121
    (game/f'data/layouts/{name}/map.bin').write_bytes(struct.pack('<'+'H'*len(g),*g))
for name in ['src/new_game.c','src/apocrypha_map_proof.c']:
    text=(base/name).read_text().replace('WARP_ID_NONE, 9, 17','WARP_ID_NONE, 36, 19')
    (game/name).write_text(text)

installed=Tileset(game,'cherrygrove','cherrygrove')
render=installed.map_image(final,W)
for idx,p in enumerate(pixels):
    assert list(installed.render(final[idx]&1023).getdata())==p,('tile round trip',idx%W,idx//W)
render.save(EVIDENCE/'town-overview.png')
manifest=dict(baseline_commit='f09ec1de2e6754e9f9a8e02281d3d773efcfa65e',spec=str(SPEC.relative_to(ROOT)),
    secondary_tiles=len(newtiles),secondary_metatiles=len(blocks),tile_capacity=512,metatile_capacity=512,
    exact_scene_roundtrip=True,static_tiles_exclude_animated_vram=True,
    original_animated_underlays_preserved=animated_underlays,
    building_pixels_and_transparency_verified=building_checks,scenery=overlaps,
    tree=dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),width=32,height=48,content_size=im.size,
              colors=len(tree_colors),grass_colors_shared=len(grass)),objects=objects)
(EVIDENCE/'integration.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k not in ('objects','scenery')},indent=2))
