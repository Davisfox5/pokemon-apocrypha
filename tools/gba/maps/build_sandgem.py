#!/usr/bin/env python3
"""Custom Sandgem exterior; writes only new Sandgem assets, never Cherrygrove art."""
from pathlib import Path
import json,struct,shutil,itertools
from PIL import Image
from tiles import Tileset
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';BASE=R/'tools/vendor/gba/johto-art-v3-baseline';A=R/'gba/art/sandgem-v1';EV=A/'evidence';OUT=A/'native';OUT.mkdir(exist_ok=True)
ts=Tileset(BASE,'cherrygrove','cherrygrove');W,H=48,40
# Owner reference: saturated mint grass, warm pale paths, blue/teal buildings.
def rgb5(c):return tuple((n<<3)|(n>>2) for n in [round(v*31/255) for v in c])
changes={(111,173,174):(80,216,136),(67,159,143):(56,184,104),(162,202,175):(136,240,160),(216,195,118):(240,224,152),(231,218,147):(255,240,176),(208,172,97):(224,208,128),(200,150,76):(200,184,112)}
for side in range(2):
 for b,p in enumerate(ts.pals[side]):ts.pals[side][b]=[rgb5(changes.get(c,c)) for c in p]
pals={b:list(ts.pals[b>=6][b]) for b in range(13)}
sources={}
for name,size,bank in [('tree',(32,40),6),('house',(64,80),7),('lab',(112,80),8),('center',(64,64),9),('mart',(64,48),10)]:
 im=Image.open(A/f'generated/{name}-reference.png').convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:255 if a>=224 else 0));im=im.crop(im.getbbox());im=im.resize(size,Image.Resampling.NEAREST)
 cs=[p[:3] for p in im.getdata() if p[3]];strip=Image.new('RGB',(len(cs),1));strip.putdata(cs);q=strip.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);pal=q.getpalette();colors=list(dict.fromkeys(rgb5(tuple(pal[i*3:i*3+3])) for i in sorted(set(q.getdata()))));pals[bank]=[(0,0,0)]+colors;pals[bank]+=[(0,0,0)]*(16-len(pals[bank]));px=[None if not p[3] else min(colors,key=lambda c:sum((p[j]-c[j])**2 for j in range(3))) for p in im.getdata()];sources[name]=(*size,px);im.putdata([(0,0,0,0) if c is None else (*c,255) for c in px]);im.save(OUT/f'{name}.png')
# Smaller western house shares the authored house palette and silhouette.
w,h,px=sources['house'];im=Image.new('RGBA',(w,h));im.putdata([(0,0,0,0) if c is None else (*c,255) for c in px]);im=im.resize((48,64),Image.Resampling.NEAREST);sources['smallhouse']=(48,64,[p[:3] if p[3] else None for p in im.getdata()]);im.save(OUT/'smallhouse.png')
def entries(mid):return ts.blocks[mid>=512][mid%512]
def attr(mid):return ts.attrs[mid>=512][mid%512]
def entry_pixels(e):
 tid=e&1023;t=ts.tiles[tid>=512][tid%512];colors=ts.pals[(e>>12)>=6][e>>12]
 return [None if not(v:=t[(7-y if e&2048 else y)*8+(7-x if e&1024 else x)]) else colors[v] for y in range(8) for x in range(8)]
def native_pixels(mid):
 p=[None]*256
 for layer in range(2):
  for q in range(4):
   for i,c in enumerate(entry_pixels(entries(mid)[layer*4+q])):
    if c is not None:p[((q//2)*8+i//8)*16+(q%2)*8+i%8]=c
 return p
# All terrain begins traversable. Visible forest/props establish the boundary.
grid=[1]*(W*H);flags=[0x3000]*(W*H);attributes=[0]*(W*H);pixels=[native_pixels(1) for _ in grid];objects=[]
def put(x,y,mid,solid=False):
 if 0<=x<W and 0<=y<H:
  i=y*W+x;grid[i]=mid;pixels[i]=[a if b is None else b for a,b in zip(pixels[i],native_pixels(mid))];flags[i]=0x3c00 if solid else 0x3000;attributes[i]=0

def rect(x,y,w,h,mid,solid=False):
 for yy in range(y,y+h):
  for xx in range(x,x+w):put(xx,yy,mid,solid)
def obj(name,x,y):
 w,h,src=sources[name]
 for yy in range(h):
  for xx in range(w):
   gx=x*16+xx;gy=y*16+yy
   if not(0<=gx<W*16 and 0<=gy<H*16):continue
   c=src[yy*w+xx]
   if c is None:continue
   i=(gy//16)*W+gx//16;j=gy%16*16+gx%16;pixels[i][j]=c;flags[i]=0x3c00;attributes[i]=0
 objects.append(dict(name=name,x=x,y=y,width=w,height=h))
# Layout follows the owner's original-game reference, with exterior scenery buffers.
path=set()
def lane(x,y,w,h):path.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
lane(8,16,28,2);lane(29,7,2,11);lane(18,17,2,10);lane(13,25,16,2);lane(28,25,3,10)
lane(15,13,2,5);lane(23,13,2,5);lane(33,13,2,5);lane(14,22,2,5);lane(23,22,2,5)
for x,y in sorted(path):
 n=(x,y-1) in path;s=(x,y+1) in path;w=(x-1,y) in path;e=(x+1,y) in path;mid=0x121
 if not n:mid=0x119
 if not s:mid=0x129
 if not w:mid=0x120 if n and s else (0x118 if not n else 0x128)
 if not e:mid=0x122 if n and s else (0x11a if not n else 0x12a)
 put(x,y,mid)
# Broad southeast dry sand patch. There is no water on this map.
for y in range(20,34):
 left=30 if y<22 else 29 if y<26 else 28
 for x in range(left,36):put(x,y,0x121)
for x,y in [(20,14),(26,14),(31,14),(28,23)]:put(x,y,3,True)
# Reference fence beside lab and flowers along forest edge.
for x in range(8,13):put(x,15,0x149,True)
for x in range(29,31):put(x,6,0x149,True)
for y in range(16,19):put(8,y,0x149,True)
buildings=[dict(name='Lab',style='lab',x=13,y=9,door=[15,13],interior='SandgemLab'),dict(name='PokemonCenter',style='center',x=22,y=10,door=[23,13],interior='SandgemPokemonCenter'),dict(name='Mart',style='mart',x=32,y=11,door=[33,13],interior='SandgemMart'),dict(name='HouseWest',style='smallhouse',x=13,y=19,door=[14,22],interior='SandgemHouseWest'),dict(name='HouseSouth',style='house',x=22,y=18,door=[23,22],interior='SandgemHouseSouth')]
for b in buildings:
 obj(b['style'],b['x'],b['y']);x,y=b['door'];flags[y*W+x]=0;attributes[y*W+x]=0x69
# Dense single-crown forest framing matches the reference, not sparse pine rows.
trees=[]
for y in range(-1,H,2):
 for x in range(0,W,2):
  top=y<7 and not(28<=x<32 and y>=5)
  west=x<8 or (x<12 and y>=19)
  east=x>=36
  bottom=y>=33 or (y>=27 and x<28)
  if top or west or east or bottom:trees.append((x,y))
for x,y in [(10,7),(20,7),(22,7),(24,7),(26,7),(32,8),(34,8)]:trees.append((x,y))
for x,y in sorted(set(trees),key=lambda t:(t[1],t[0])):obj('tree',x,y)
# Four rows of scenery remain beyond the actual directional exit.
for x in range(28,31):attributes[32*W+x]=0x65;flags[32*W+x]=0x3000
spec=dict(name='SandgemTown',width=W,height=H,spawn=[29,29],buildings=buildings,trees=trees,objects=objects,south_warp_y=32,south_warp_x=[28,29,30])
(A/'layout.json').write_text(json.dumps(spec,indent=2)+'\n')

for side in ["primary","secondary"]:
 dest=G/f"data/tilesets/{side}/sandgem"
 if not dest.exists():shutil.copytree(BASE/f"data/tilesets/{side}/cherrygrove",dest)
palette_maps={b:{c:i for i,c in reversed(list(enumerate(p))) if i} for b,p in pals.items()}
palette_sets={b:set(m) for b,m in palette_maps.items()}
# General's animation callback writes these VRAM slots after load. Matching a
# static tile's current pixels is not sufficient to make an animated slot reusable.
animated=set(range(432,462))|set(range(464,474))|set(range(480,490))|set(range(496,502))|set(range(508,512))
protected={e&1023 for mid in set(grid) for e in entries(mid) if (e&1023)<512}|animated|{0}
allocation=list(range(512,1008))+[i for i in range(511,0,-1) if i not in protected]
primary_output=list(ts.tiles[0]);newids=[]
tile_lookup={}
def aliases(raw,tid):
 for h,v,bits in [(False,False,0),(True,False,1024),(False,True,2048),(True,True,3072)]:
  flipped=bytes(raw[(7-y if v else y)*8+(7-x if h else x)] for y in range(8) for x in range(8))
  tile_lookup.setdefault(flipped,tid|bits)
for i,t in enumerate(ts.tiles[0]):
 if i in protected and i not in animated:aliases(bytes(t),i)
newtiles=[]
def tile_entry(data,bank,hidden=False):
    raw=bytes(data)
    if hidden and raw not in tile_lookup and 0 in raw:
        opaque=[(i,v) for i,v in enumerate(raw) if v]
        for tid,t in itertools.chain(((i,t) for i,t in enumerate(ts.tiles[0]) if i in protected and i not in animated),zip(newids,newtiles)):
            if all(t[i]==v for i,v in opaque):
                return tid|bank<<12
    if raw not in tile_lookup:
        assert len(newtiles)<len(allocation), 'Combined tileset capacity exceeded'
        tid=allocation[len(newtiles)];aliases(raw,tid);newtiles.append(raw);newids.append(tid)
        if tid<512:primary_output[tid]=list(raw)
    return tile_lookup[raw]|bank<<12
def encode_quad(colors):
    used=set(colors)
    choices=[(a,) for a in range(13) if used<=palette_sets[a]]
    if not choices:choices=[(a,b) for a,b in itertools.combinations(range(13),2) if used<=palette_sets[a]|palette_sets[b]]
    assert choices, ('More than two palette banks required',idx%W,idx//W,used)
    def cost(choice):
        a=choice[0];b=choice[-1]
        low=bytes(palette_maps[a].get(c,0) for c in colors)
        high=bytes(0 if c in palette_sets[a] else palette_maps[b][c] for c in colors)
        return (int(low not in tile_lookup)+int(high not in tile_lookup),len(choice),choice)
    choice=min(choices,key=cost);a=choice[0];b=choice[-1]
    return (tile_entry([palette_maps[a].get(c,0) for c in colors],a,hidden=True),
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
assert len(newtiles)<=len(allocation),('tile capacity',len(newtiles))
assert len(blocks)<=512,('metatile capacity',len(blocks))
folder=G/'data/tilesets/secondary/sandgem'
secondary_tiles=[t for i,t in zip(newids,newtiles) if i>=512];sheet=Image.new('P',(128,256));sheet.putpalette(Image.open(ts.dirs[1]/'tiles.png').getpalette())
for i,t in enumerate(secondary_tiles):
    part=Image.new('P',(8,8));part.putdata(t);sheet.paste(part,(i%16*8,i//16*8))
sheet.save(folder/'tiles.png')
primary_sheet=Image.new('P',(128,256));primary_sheet.putpalette(Image.open(ts.dirs[0]/'tiles.png').getpalette())
for i,t in enumerate(primary_output):
 part=Image.new('P',(8,8));part.putdata(t);primary_sheet.paste(part,(i%16*8,i//16*8))
primary_sheet.save(G/'data/tilesets/primary/sandgem/tiles.png')
for b in range(6,13):
    text='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n'
    (folder/f'palettes/{b:02}.pal').write_text(text)
    (OUT/f'{b:02}.pal').write_text(text)
(folder/'metatiles.bin').write_bytes(struct.pack('<'+'H'*(len(blocks)*8),*[e for b in blocks for e in b]))
(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
for b in range(6):
 (G/f'data/tilesets/primary/sandgem/palettes/{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')

folder=G/'data/layouts/SandgemTown';folder.mkdir(exist_ok=True)
(folder/'map.bin').write_bytes(struct.pack('<'+'H'*len(final),*final))
(folder/'border.bin').write_bytes(struct.pack('<4H',*[final[y*W+x] for y in [1,2] for x in [2,3]]))
installed=Tileset(G,'sandgem','sandgem');im=installed.map_image(final,W);im.save(EV/'town-overview.png')
for i,p in enumerate(pixels):assert list(installed.render(final[i]&1023).getdata())==p,('roundtrip',i%W,i//W)
(EV/'integration.json').write_text(json.dumps(dict(new_art_tiles=len(newtiles),secondary_metatiles=len(blocks),metatile_capacity=512,exact_scene_roundtrip=True,static_tiles_exclude_animation=True),indent=2)+'\n')
print('Sandgem:',len(newtiles),'tiles',len(blocks),'metatiles')
