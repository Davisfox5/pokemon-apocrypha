#!/usr/bin/env python3
"""Custom Floccesy exterior; writes only new Floccesy assets, never Cherrygrove art."""
from pathlib import Path
import json,struct,shutil,itertools
from PIL import Image
from tiles import Tileset
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';BASE=R/'tools/vendor/gba/johto-art-v3-baseline';A=R/'gba/art/floccesy-v1';EV=A/'evidence';OUT=A/'native';OUT.mkdir(parents=True,exist_ok=True)
ts=Tileset(BASE,'cherrygrove','cherrygrove');W,H=56,78
# Owner reference: saturated mint grass, warm pale paths, blue/teal buildings.
def rgb5(c):return tuple((n<<3)|(n>>2) for n in [round(v*31/255) for v in c])
changes={(111,173,174):(136,192,88),(67,159,143):(104,168,72),(162,202,175):(192,224,120),(216,195,118):(240,224,152),(231,218,147):(255,240,176),(208,172,97):(224,208,128),(200,150,76):(200,184,112)}
for side in range(2):
 for b,p in enumerate(ts.pals[side]):ts.pals[side][b]=[rgb5(changes.get(c,c)) for c in p]
pals={b:list(ts.pals[b>=6][b]) for b in range(13)}
sources={}
for name,size,bank in [('tree',(32,40),6),('house',(64,80),7),('alder',(64,64),8),('center',(80,80),9),('tower',(48,80),10),('shed',(64,64),11)]:
 im=Image.open(A/f'generated/{name}-reference.png').convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:255 if a>=224 else 0));im=im.crop(im.getbbox());im=im.resize(size,Image.Resampling.NEAREST)
 cs=[p[:3] for p in im.getdata() if p[3]];strip=Image.new('RGB',(len(cs),1));strip.putdata(cs);q=strip.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);pal=q.getpalette();colors=list(dict.fromkeys(rgb5(tuple(pal[i*3:i*3+3])) for i in sorted(set(q.getdata()))));pals[bank]=[(0,0,0)]+colors;pals[bank]+=[(0,0,0)]*(16-len(pals[bank]));px=[None if not p[3] else min(colors,key=lambda c:sum((p[j]-c[j])**2 for j in range(3))) for p in im.getdata()];sources[name]=(*size,px);im.putdata([(0,0,0,0) if c is None else (*c,255) for c in px]);im.save(OUT/f'{name}.png')
pals[12]=list(map(rgb5,[(0,0,0),(120,120,112),(128,128,120),(144,144,128),(192,184,144),(208,192,144),(176,128,72),(200,152,88),(216,168,104),(104,96,72),(224,208,144),(208,184,112),(240,224,160),(80,128,48),(144,192,72),(176,216,96)]))

# Reuse approved custom Cherrygrove bench artwork, quantized into terrain bank.
im=Image.open(R/'gba/art/johto-restart/native/park-bench.png').convert('RGBA').resize((32,16),Image.Resampling.NEAREST)
colors=pals[12][1:];sources['bench']=(32,16,[None if p[3]<128 else min(colors,key=lambda c:sum((p[j]-c[j])**2 for j in range(3))) for p in im.getdata()])

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
   gx=x*16+xx-(8 if name in ('alder','shed') else 0);gy=y*16+yy
   if not(0<=gx<W*16 and 0<=gy<H*16):continue
   c=src[yy*w+xx]
   if c is None:continue
   i=(gy//16)*W+gx//16;j=gy%16*16+gx%16;pixels[i][j]=c;flags[i]=0x3c00;attributes[i]=0
 objects.append(dict(name=name,x=x,y=y,width=w,height=h))
# Original B2W2 spring map: lower paved village, tower lawn, northern lodge/court.
path=set()
def lane(x,y,w,h):path.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
lane(9,66,38,3);lane(29,39,3,29);lane(13,54,34,3)
# Paved streets with a narrow warm stone curb, no center stripe.
def custom(x,y,fn,solid=False):
 i=y*W+x;pixels[i]=[fn(xx,yy) for yy in range(16) for xx in range(16)];flags[i]=0x3c00 if solid else 0x3000;attributes[i]=0
C=pals[12]
for x,y in path:
 def road(xx,yy):
  edge=((x-1,y) not in path and xx<2) or ((x+1,y) not in path and xx>13) or ((x,y-1) not in path and yy<2) or ((x,y+1) not in path and yy>13)
  return C[4] if edge else C[2] if (xx*7+yy*11)%43==0 else C[1]
 custom(x,y,road)
def paving(x,y,w,h):
 for yy in range(y,y+h):
  for xx in range(x,x+w):custom(xx,yy,lambda a,b:C[6] if b%8==0 or (a+(8 if b//8%2 else 0))%16==0 else C[8] if b%8==1 else C[7])
paving(14,42,14,12);paving(14,57,14,9);paving(34,57,13,9)
# Clock green enclosed by a low dark hedge, with a southern opening.
rect(16,42,10,10,1)
for x in range(16,26):
 put(x,42,4,True)
 if x not in (20,21):put(x,51,4,True)
for y in range(43,51):put(16,y,4,True);put(25,y,4,True)
for x,y in [(18,44),(23,45),(18,48),(23,49)]:put(x,y,4)
obj('tower',20,44)
# Small eastern lawn, bench and flowers beside the high street.
for x,y in [(43,46),(44,47),(42,49),(35,50)]:put(x,y,4)
obj('bench',40,44)
# Northern dirt route and the training court beside Alder's lodge.
dirt=set()
def dirtlane(x,y,w,h):dirt.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
dirtlane(29,27,3,13);dirtlane(30,28,17,3);dirtlane(17,29,8,9)
dirtlane(18,25,2,5)
for yy,xx in [(46,40),(47,39),(48,38),(49,38),(50,37),(51,36)]:dirtlane(xx,yy,3,2)
for x,y in dirt:
 n=(x,y-1) in dirt;ss=(x,y+1) in dirt;w=(x-1,y) in dirt;e=(x+1,y) in dirt;mid=0x121
 if not n:mid=0x119
 if not ss:mid=0x129
 if not w:mid=0x120 if n and ss else (0x118 if not n else 0x128)
 if not e:mid=0x122 if n and ss else (0x11a if not n else 0x12a)
 put(x,y,mid)
# Court boundary and a circular training marking, rendered with native terrain colors.
for y in range(31,37):
 for x in range(18,24):
  def court(a,b):
   xx=(x-18)*16+a;yy=(y-31)*16+b;r=(xx-47.5)**2+(yy-47.5)**2
   line=xx in (1,2,93,94,47,48) or yy in (1,2,93,94) or 20**2<=r<=22**2
   return C[11] if line else C[10] if (xx*7+yy*11)%47==0 else C[12]
  custom(x,y,court)
for x in range(16,26):put(x,28,0x149,True)
for y in range(29,38):
 put(16,y,0x141,True);put(25,y,0x142,True)
# Broad shallow steps link paved village and dirt upper terrace.
for y in range(39,41):
 for x in range(29,32):custom(x,y,lambda a,b:C[9] if b%5==0 else C[4] if b%5==1 else C[5])
buildings=[dict(name='PokemonCenter',style='center',x=16,y=58,door=[18,62],interior='FloccesyPokemonCenter'),dict(name='HouseWest',style='house',x=35,y=58,door=[36,62],interior='FloccesyHouseWest'),dict(name='HouseEast',style='house',x=41,y=58,door=[42,62],interior='FloccesyHouseEast'),dict(name='Lodge',style='alder',x=18,y=22,door=[19,25],interior='FloccesyLodge'),dict(name='ShedWest',style='shed',x=30,y=23,door=[31,26],interior='FloccesyShedWest'),dict(name='ShedEast',style='shed',x=36,y=23,door=[37,26],interior='FloccesyShedEast')]
# Shed door approaches join main east path.
for x in (31,37):put(x,27,0x121)
for b in buildings:
 obj(b['style'],b['x'],b['y']);x,y=b['door'];flags[y*W+x]=0;attributes[y*W+x]=0x69
# Forest frame and upper woodland clearing preserve the reference silhouette.
trees=[]
for y in range(-1,H,2):
 for x in range(0,W,2):
  west=x<12 and not(y in (65,67) and x>=8)
  east=x>=48
  bottom=y>=69
  top=y<21
  # Woodland opening above the lodge and sheds.
  if top and 26<=x<38 and 9<=y<17:top=False
  if top and x in (26,28) and 15<=y<21:top=False
  strip=y in (41,) and x<29 and x>=12
  northeast=33<=x<48 and 33<=y<41
  if west or east or bottom or top or strip or northeast:trees.append((x,y))
for y in range(0,64):
 put(6,y,0x116,True);put(7,y,0x117,True)
for x,y in sorted(set(trees),key=lambda t:(t[1],t[0])):obj('tree',x,y)
# Accessible woodland pocket is connected by its narrow forest path.
# Fenced east continuation awaits a future map. West is the Cherrygrove connection.
for y in range(28,31):put(46,y,0x141,True)
for y in range(66,69):attributes[y*W+9]=0x63;flags[y*W+9]=0x3000
spec=dict(name='FloccesyTown',width=W,height=H,spawn=[30,62],buildings=buildings,trees=trees,objects=objects,west_warp_x=9,west_warp_y=[66,67,68])
(A/'layout.json').write_text(json.dumps(spec,indent=2)+'\n')

for side in ["primary","secondary"]:
 dest=G/f"data/tilesets/{side}/floccesy"
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
    key=(ent,attributes[idx]|0x1000)
    if key not in block_lookup:block_lookup[key]=512+len(blocks);blocks.append(ent);attrs.append(attributes[idx]|0x1000)
    final.append(flags[idx]|block_lookup[key])
assert len(newtiles)<=len(allocation),('tile capacity',len(newtiles))
assert len(blocks)<=512,('metatile capacity',len(blocks))
folder=G/'data/tilesets/secondary/floccesy'
secondary_tiles=[t for i,t in zip(newids,newtiles) if i>=512];sheet=Image.new('P',(128,256));sheet.putpalette(Image.open(ts.dirs[1]/'tiles.png').getpalette())
for i,t in enumerate(secondary_tiles):
    part=Image.new('P',(8,8));part.putdata(t);sheet.paste(part,(i%16*8,i//16*8))
sheet.save(folder/'tiles.png')
primary_sheet=Image.new('P',(128,256));primary_sheet.putpalette(Image.open(ts.dirs[0]/'tiles.png').getpalette())
for i,t in enumerate(primary_output):
 part=Image.new('P',(8,8));part.putdata(t);primary_sheet.paste(part,(i%16*8,i//16*8))
primary_sheet.save(G/'data/tilesets/primary/floccesy/tiles.png')
for b in range(6,13):
    text='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n'
    (folder/f'palettes/{b:02}.pal').write_text(text)
    (OUT/f'{b:02}.pal').write_text(text)
(folder/'metatiles.bin').write_bytes(struct.pack('<'+'H'*(len(blocks)*8),*[e for b in blocks for e in b]))
(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
for b in range(6):
 (G/f'data/tilesets/primary/floccesy/palettes/{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')

folder=G/'data/layouts/FloccesyTown';folder.mkdir(exist_ok=True)
(folder/'map.bin').write_bytes(struct.pack('<'+'H'*len(final),*final))
(folder/'border.bin').write_bytes(struct.pack('<4H',*[final[y*W+x] for y in [1,2] for x in [2,3]]))
installed=Tileset(G,'floccesy','floccesy');im=installed.map_image(final,W);im.save(EV/'town-overview.png')
for i,p in enumerate(pixels):assert list(installed.render(final[i]&1023).getdata())==p,('roundtrip',i%W,i//W)
(EV/'integration.json').write_text(json.dumps(dict(new_art_tiles=len(newtiles),secondary_metatiles=len(blocks),metatile_capacity=512,exact_scene_roundtrip=True,static_tiles_exclude_animation=True),indent=2)+'\n')
print('Floccesy:',len(newtiles),'tiles',len(blocks),'metatiles')
