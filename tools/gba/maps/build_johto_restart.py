#!/usr/bin/env python3
"""Fresh custom Johto exterior on immutable Emerald terrain. No v4 inputs.
Uses the earlier exact compositor, with original generated art and a new layout.
"""
import hashlib,itertools,json,struct,subprocess,sys,shutil
from pathlib import Path
from PIL import Image,ImageDraw
from tiles import Tileset,palette
ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'gba/art/johto-restart';OUT=ART/'native';EV=ART/'evidence';G=ROOT/'tools/vendor/gba/johto-restart-game';BASE=ROOT/'tools/vendor/gba/johto-art-v3-baseline'
assert subprocess.check_output(['git','-C',str(BASE),'status','--porcelain'],text=True)==''
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='f09ec1de2e6754e9f9a8e02281d3d773efcfa65e'
ts=Tileset(BASE,'cherrygrove','cherrygrove');W,H=64,36
# Recolor the editable native Emerald palette; retain proven terrain tiles/animation.
def rgb5(c):return tuple((n<<3)|(n>>2) for n in [round(v*31/255) for v in c])
changes={(111,173,174):(144,184,128),(67,159,143):(112,160,112),(162,202,175):(176,208,152),
 (216,195,118):(224,208,152),(231,218,147):(240,224,176),(208,172,97):(208,184,128),(200,150,76):(176,160,112),
 (231,202,182):(232,200,152),(216,172,147):(208,168,120),(185,143,125):(176,136,104),
 (154,112,104):(152,112,88),(131,89,83):(128,96,80),(100,66,76):(88,72,64),(72,53,62):(56,56,48),
 (66,106,179):(56,128,176),(83,127,179):(72,144,192),(54,92,161):(48,112,160),(48,85,137):(40,104,144),(37,70,124):(32,88,128)}
for side in range(2):
 for b,p in enumerate(ts.pals[side]):ts.pals[side][b]=[rgb5(changes.get(c,c)) for c in p]
pals={b:list(ts.pals[b>=6][b]) for b in range(13)};grass=sorted(c for _,c in ts.render(1).getcolors())
for b in [8,10]:pals[b]=palette(ROOT/f'gba/art/johto-v2/native/{b:02}.pal')
def quant(cs,n):
 a=Image.new('RGB',(len(cs),1));a.putdata(cs);q=a.quantize(colors=n,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);pp=q.getpalette();result=[]
 for i in sorted(set(q.getdata())):
  c=rgb5(tuple(pp[i*3:i*3+3]))
  if c not in result:result.append(c)
 return result
sources={}
def generated(name,size,bank,extra=()):
 im=Image.open(ART/f'generated/{name}.png').convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:255 if a>=224 else 0))
 if name=='cliff':im=im.resize(size,Image.Resampling.NEAREST)
 else:
  im=im.crop(im.getbbox());scale=min(size[0]/im.width,(size[1]-8)/im.height);im=im.resize(tuple(round(v*scale) for v in im.size),Image.Resampling.NEAREST);q=Image.new('RGBA',size);q.paste(im,((size[0]-im.width)//2,size[1]-im.height));im=q
 cs=quant([p[:3] for p in im.getdata() if p[3]],15-len(extra));pals[bank]=[(0,0,0)]+cs+list(extra);pals[bank]+=[(0,0,0)]*(16-len(pals[bank]))
 pix=[None if not p[3] else min(cs,key=lambda c:sum((p[j]-c[j])**2 for j in range(3))) for p in im.getdata()];sources[name]=(size[0],size[1],pix)
 rgba=Image.new('RGBA',size);rgba.putdata([(0,0,0,0) if p is None else (*p,255) for p in pix]);rgba.save(OUT/f'{name}.png')
generated('tree',(32,48),6,grass);generated('cliff',(128,48),7,grass);generated('island',(96,64),11)
# Mart is independently authored, with the same native color budget as the approved buildings.
a=Image.open(ART/'generated/mart.png').convert('RGBA');a.putalpha(a.getchannel('A').point(lambda a:255 if a>=224 else 0));im=Image.new('RGBA',(96,80));body=a.crop((126,186,1110,1062)).resize((80,80),Image.Resampling.NEAREST);im.paste(body,(0,0));sign=a.crop((1100,713,1228,909)).resize((12,18),Image.Resampling.NEAREST);im.paste(sign,(80,49))
cs=[p[:3] for p in im.getdata() if p[3]];blue=[c for c in cs if c[2]>c[0]*1.1];warm=[c for c in cs if c not in blue]
pals[9]=[(0,0,0)]+quant(blue,15);pals[12]=[(0,0,0)]+quant(warm,9)+grass+sorted(c for _,c in ts.render(0x121).getcolors())
for b in [9,12]:pals[b]+=[(0,0,0)]*(16-len(pals[b]))
allc=pals[9][1:]+pals[12][1:];mp=[None if not p[3] else min(allc,key=lambda c:sum((p[j]-c[j])**2 for j in range(3))) for p in im.getdata()];sources['mart']=(96,80,mp)
im.putdata([(0,0,0,0) if p is None else (*p,255) for p in mp]);im.save(OUT/'mart.png')
for name in ['house','center']:
 a=Image.open(ROOT/f'gba/art/johto-v2/native/{name}.png').convert('RGBA');sources[name]=(80,80,[None if not p[3] else p[:3] for p in a.getdata()]);shutil.copyfile(ROOT/f'gba/art/johto-v2/native/{name}.png',OUT/f'{name}.png')

def entries(mid):return ts.blocks[mid>=512][mid-512 if mid>=512 else mid]
def attr(mid):return ts.attrs[mid>=512][mid-512 if mid>=512 else mid]
def entry_pixels(e):
 tid=e&1023;t=ts.tiles[tid>=512][tid-512 if tid>=512 else tid];colors=ts.pals[(e>>12)>=6][e>>12]
 return [None if not (v:=t[(7-y if e&2048 else y)*8+(7-x if e&1024 else x)]) else colors[v] for y in range(8) for x in range(8)]
def native_pixels(mid,erase=()):
 p=[None]*256
 for layer in range(2):
  for q in range(4):
   for i,c in enumerate(entry_pixels(entries(mid)[layer*4+q])):
    if c is not None:p[((q//2)*8+i//8)*16+(q%2)*8+i%8]=c
 return [None if c in erase else c for c in p]
grid=[1]*(W*H);flags=[0x3000]*(W*H);attributes=[0x1000]*(W*H);pixels=[native_pixels(1) for _ in grid];objects=[];overlaps=[]
def put(x,y,mid,solid=False):
 if 0<=x<W and 0<=y<H:
  i=y*W+x;grid[i]=mid;pixels[i]=[a if b is None else b for a,b in zip(pixels[i],native_pixels(mid))];flags[i]=0x3c00 if solid else 0x3000;attributes[i]=attr(mid)|0x1000

def rect(x,y,w,h,mid,solid=False):
 for yy in range(y,y+h):
  for xx in range(x,x+w):put(xx,yy,mid,solid)
def overlay(x,y,w,h,source,name,solid=True):
 covered=preserved=0
 for yy in range(h):
  for xx in range(w):
   gx=x*16+xx;gy=y*16+yy
   if not (0<=gx<W*16 and 0<=gy<H*16):continue
   i=(gy//16)*W+gx//16;j=(gy%16)*16+gx%16;c=source[yy*w+xx]
   if c is None:preserved+=1;continue
   pixels[i][j]=c;covered+=1
   if solid:flags[i]=0x3c00
   # Entire trees are blocked; no partial trunk collision with ambiguous depth.
   attributes[i]=0 if name=='tree' else 0x1000
 objects.append(dict(name=name,x=x,y=y,width=w,height=h));overlaps.append(dict(name=name,transparent_pixels_preserved=preserved,opaque_pixels=covered))
def obj(name,x,y,solid=True):overlay(x,y,*sources[name],name,solid)
def native_object(x,y,rows,name,erase=grass,solid=True):
 w=len(rows[0])*16;h=len(rows)*16;p=[None]*(w*h)
 for dy,row in enumerate(rows):
  for dx,mid in enumerate(row):
   block=native_pixels(mid,erase)
   for yy in range(16):p[(dy*16+yy)*w+dx*16:(dy*16+yy)*w+dx*16+16]=block[yy*16:yy*16+16]
 overlay(x,y,w,h,p,name,solid)
# Fresh land/sea geometry. Settlement east, bay west, Route 30 north, Route 29 east.
rect(0,0,W,H,0x170,True)
rect(0,0,33,7,1,True)
coast=[30]*11+[27,26,25,25,24,24,24,24,24,25,25,26,26,27,28,29,30]+[31]*8
for y,left in enumerate(coast):
 rect(left,y,W-left,1,1)
 if 11<=y<=27:rect(left,y,3,1,0x121);put(left-1,y,0x123,True);put(left+2,y,0x122)
# Rounded beach top/bottom returns join actual Emerald animated shore tiles.
for x in range(26,33):put(x,10,0x11c,True)
for x in range(29,33):put(x,28,0x12c,True)
# Smooth pixel contours compose Emerald sand/foam over its live water underlay.
# Geometry is authored here; all surface pixels still come from native terrain.
waterpx=native_pixels(0x170);sandpx=native_pixels(0x121);grasspx=native_pixels(1);foam=pals[5][1]
for my in range(10,29):
 for mx in range(21,35):
  i=my*W+mx;grid[i]=0x170
  for py in range(16):
   fy=my+py/16;yy=min(int(fy),H-2);t=fy-yy;left=((1-t)*coast[yy]+t*coast[yy+1]-.5)*16
   for px in range(16):
    gx=mx*16+px;j=py*16+px
    pixels[i][j]=waterpx[j] if gx<left else foam if gx<left+2 else sandpx[j] if gx<left+48 else grasspx[j]
  centerleft=((coast[my]+coast[min(H-1,my+1)])/2-.5)*16
  flags[i]=0x3c00 if mx*16+8<centerleft+2 else 0x3000;attributes[i]=0x1000
# Custom continuous coastal wall; broad slabs instead of a row of unrelated rocks.
for x in range(0,32,8):obj('cliff',x,7)
# Existing native Emerald side/return pieces use the same warm rock palette family.
for y in range(7):put(32,y,0x16f,True)
for y in range(28,H):put(30,y,0x187,True)
# HGSS offshore landmarks: an irregular island, southern outcrop and sandbar.
obj('island',2,13);obj('island',-3,22)
rect(15,23,4,2,0x121,True)
for x in range(15,19):put(x,22,0x11c,True);put(x,25,0x12c,True)
for y in [23,24]:put(14,y,0x123,True);put(19,y,0x125,True)
for x,y in [(6,12),(12,14),(4,20),(8,26),(12,28),(22,23),(25,27),(28,27)]:put(x,y,0x18c,True)
# Modest northeastern pond enclosed by forest.
rect(55,0,7,7,0x170,True)
# Streets are drawn before objects, using the reliable Emerald corner/edge tiles.
path=set()
def lane(x,y,w,h):path.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
lane(35,0,3,16);lane(35,11,19,3);lane(39,12,3,13);lane(35,18,7,3);lane(40,22,14,3);lane(51,11,3,19);lane(52,17,12,3);lane(52,28,8,3);lane(35,17,2,3);lane(46,19,2,5);lane(56,25,2,5);lane(43,9,2,4);lane(53,9,2,4)
for x,y in sorted(path):
 n=(x,y-1) in path;s=(x,y+1) in path;w=(x-1,y) in path;e=(x+1,y) in path;mid=0x121
 if not n:mid=0x119
 if not s:mid=0x129
 if not w:mid=0x120 if n and s else (0x118 if not n else 0x128)
 if not e:mid=0x122 if n and s else (0x11a if not n else 0x12a)
 put(x,y,mid)
# Dense forests of single tree instances, with a staggered outer edge.
trees=set()
for y in [-2,0,2,4]:
 trees.update((x,y) for x in range(0,32,2));trees.update((x,y) for x in range(39,55,2) if y<4)
for y in [4,7,10,13]:trees.update((x,y) for x in [60,62])
for y in range(20,36,2):trees.update((x,y) for x in [60,62])
for y in range(27,36,2):trees.update((x,y) for x in [32,34,36,38])
for y in range(31,36,2):trees.update((x,y) for x in range(40,60,2))
for x,y in [(55,6),(57,7),(58,10),(58,14),(58,26)]:trees.add((x,y))
shadow=min(pals[6][1:-3],key=lambda c:sum((a-b)**2 for a,b in zip(c,(72,120,88))))
for x,y in sorted(trees):
 if (x+2,y) in trees and (x,y+2) in trees:
  overlay(x,y+1,32,32,[shadow]*1024,'forest-floor')
for x,y in sorted(trees,key=lambda p:(p[1],p[0])):obj('tree',x,y)
# Authored flower gardens are built from the baseline's native flower and fence objects.
for x,y,w in [(55,12,4),(43,27,6),(58,22,2)]:
 for xx in range(x,x+w):native_object(xx,y,[[4]],'flowers',solid=True);native_object(xx,y+1,[[4]],'flowers',solid=True)
 for xx in range(x,x+w):native_object(xx,y+2,[[0x149]],'fence')
# The original accepted house and Center remain byte-identical native assets.
buildings=[dict(name='PlayerHouse',x=33,y=13,style='house',door=[35,17],warp=0),dict(name='GoldHouse',x=44,y=15,style='house',door=[46,19],warp=1),dict(name='NeighborHouse',x=54,y=21,style='house',door=[56,25],warp=2),dict(name='Mart',x=41,y=5,style='mart',door=[43,9],warp=4),dict(name='PokemonCenter',x=51,y=5,style='center',door=[53,9],warp=5)]
for b in buildings:
 obj(b['style'],b['x'],b['y']);x,y=b['door'];i=y*W+x;flags[i]=0;attributes[i]=0x1069
for x,y in [(37,18),(45,20),(48,20),(54,26),(58,26)]:native_object(x,y,[[4]],'flowers',solid=False)
native_object(42,15,[[3]],'town-sign')
spawn=[40,20]
spec=dict(name='CherrygroveCity',width=W,height=H,spawn=spawn,north_exit=[35,0,3],east_exit=[63,17,3],buildings=buildings,trees=sorted(trees),objects=objects,dormant_warp=3)
(ART/'layout.json').write_text(json.dumps(spec,indent=2)+'\n')

# Encode the final visible pixels exactly, selecting at most two existing palette
# banks per 8x8 quadrant. The bottom bank is also opaque under the foreground;
# every transparent source pixel keeps the already composed scenery behind it.
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
folder=G/'data/tilesets/secondary/cherrygrove'
secondary_tiles=[t for i,t in zip(newids,newtiles) if i>=512];sheet=Image.new('P',(128,256));sheet.putpalette(Image.open(ts.dirs[1]/'tiles.png').getpalette())
for i,t in enumerate(secondary_tiles):
    part=Image.new('P',(8,8));part.putdata(t);sheet.paste(part,(i%16*8,i//16*8))
sheet.save(folder/'tiles.png')
primary_sheet=Image.new('P',(128,256));primary_sheet.putpalette(Image.open(ts.dirs[0]/'tiles.png').getpalette())
for i,t in enumerate(primary_output):
 part=Image.new('P',(8,8));part.putdata(t);primary_sheet.paste(part,(i%16*8,i//16*8))
primary_sheet.save(G/'data/tilesets/primary/cherrygrove/tiles.png')
for b in range(6,13):
    text='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n'
    (folder/f'palettes/{b:02}.pal').write_text(text)
    (OUT/f'{b:02}.pal').write_text(text)
(folder/'metatiles.bin').write_bytes(struct.pack('<'+'H'*(len(blocks)*8),*[e for b in blocks for e in b]))
(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
for b in range(6):
 (G/f'data/tilesets/primary/cherrygrove/palettes/{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
(G/'data/layouts/CherrygroveCity/map.bin').write_bytes(struct.pack('<'+'H'*len(final),*final))
layouts=json.loads((BASE/'data/layouts/layouts.json').read_text())
for row in layouts['layouts']:
 if row['id']=='LAYOUT_CHERRYGROVE_CITY':row.update(width=W,height=H)
 if row['id']=='LAYOUT_CHERRYGROVE_ROUTE29_APPROACH':row.update(height=H)
 if row['id']=='LAYOUT_CHERRYGROVE_ROUTE30_APPROACH':row.update(width=W)
(G/'data/layouts/layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
town=json.loads((BASE/'data/maps/CherrygroveCity/map.json').read_text())
for b in buildings:town['warp_events'][b['warp']].update(x=b['door'][0],y=b['door'][1])
town['warp_events'][3].update(x=34,y=32)
old_cast=ROOT/'tools/vendor/gba/regional-scale-v1-game/data/maps/CherrygroveCity'
town['object_events']=json.loads((old_cast/'map.json').read_text())['object_events']
residents=[('WATERFRONT',29,20,'UD',1),('COMMUTER',36,8,'LR',1),('JOHTO_BOY',42,24,'LR',1),('JOHTO_GIRL',58,20,'LR',1),('CAST_GOLD',40,18,'SQ',1),('CAST_SILVER',49,24,'SQ',1),('CAST_KESTRA',37,22,'LR',2),('COMPARE_HOENN',48,12,'LR',1),('COMPARE_KANTO',58,18,'SQ',1),('COMPARE_JOHTO',39,12,'SQ',1),('COMPARE_SINNOH',30,22,'SQ',1),('COMPARE_UNOVA',54,29,'LR',1)]
manifest=[]
for key,x,y,mode,n in residents:
 o=next(o for o in town['object_events'] if o['local_id']=='LOCALID_'+key);o.update(x=x,y=y,movement_type='MOVEMENT_TYPE_'+{'UD':'WALK_UP_AND_DOWN','LR':'WALK_LEFT_AND_RIGHT','SQ':'WALK_SEQUENCE_UP_RIGHT_DOWN_LEFT'}[mode],movement_range_x=n if mode!='UD' else 0,movement_range_y=n if mode!='LR' else 0)
 pos=[(x,y),(x,y-1),(x+1,y-1),(x+1,y)] if mode=='SQ' else [(xx,y) for xx in range(x-n,x+1)] if mode=='LR' else [(x,yy) for yy in range(y-n,y+1)]
 for xx,yy in pos:assert flags[yy*W+xx]&0xc00==0,('blocked resident',key,xx,yy)
 manifest.append(dict(name=key,graphics=o['graphics_id'],start=[x,y],mode=mode,positions=pos))
town['bg_events']=[dict(type='sign',x=42,y=15,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script='CherrygroveCity_TownSign')]
(G/'data/maps/CherrygroveCity/map.json').write_text(json.dumps(town,indent=2)+'\n');(ART/'residents.json').write_text(json.dumps(manifest,indent=2)+'\n')
s=(old_cast/'scripts.inc').read_text().replace('These boats do not go far anymore.\\nNow they mostly just... sit.','I come down here to watch the waves.\\nThere is always something to see.')
for name,text in {'HOENN':'The sea breeze reminds me of HOENN.','KANTO':'I traveled here from KANTO.\\nIt is a lovely place to take a break.','JOHTO':'The flowers look beautiful today!','SINNOH':'It is much warmer here than SINNOH.','UNOVA':'I came all the way from UNOVA.\\nThe quiet here is wonderful.'}.items():s=s.replace('"'+name+'$"','"'+text+'$"')
(G/'data/maps/CherrygroveCity/scripts.inc').write_text(s)
forest=[final[y*W+x] for y in [33,34] for x in [42,43]]
north_forest=[final[y*W+x] for y in [0,1] for x in [0,1]]
for name,w,h,side in [('CherrygroveRoute29Approach',16,H,'east'),('CherrygroveRoute30Approach',W,12,'north')]:
 g=[(north_forest if side=='north' else forest)[(y%2)*2+x%2] for y in range(h) for x in range(w)]
 for y in range(h):
  for x in range(w):
   if side=='east' and x<12:g[y*w+x]=final[y*W+62+x%2]
   elif side=='north' and y>=4:g[y*w+x]=final[(y%2)*W+x]
 (G/f'data/layouts/{name}/map.bin').write_bytes(struct.pack('<'+'H'*len(g),*g))
for name in ['CherrygroveCity','CherrygroveRoute29Approach','CherrygroveRoute30Approach']:(G/f'data/layouts/{name}/border.bin').write_bytes(struct.pack('<4H',*forest))
s=(BASE/'src/new_game.c').read_text().replace('WARP_ID_NONE, 9, 17','WARP_ID_NONE, 40, 20');(G/'src/new_game.c').write_text(s)
installed=Tileset(G,'cherrygrove','cherrygrove');render=installed.map_image(final,W);render.save(EV/'town-overview.png')
for i,p in enumerate(pixels):assert list(installed.render(final[i]&1023).getdata())==p,('scene roundtrip',i%W,i//W)
for name in ['house','center']:assert (OUT/f'{name}.png').read_bytes()==(ROOT/f'gba/art/johto-v2/native/{name}.png').read_bytes()
report=dict(fresh_emerald_foundation=True,rejected_v4_inputs=False,new_art_tiles=len(newtiles),secondary_tiles=len(secondary_tiles),secondary_tile_capacity=496,reclaimed_primary_tiles=sum(i<512 for i in newids),available_art_slots=len(allocation),door_tiles_reserved=16,secondary_metatiles=len(blocks),metatile_capacity=512,exact_scene_roundtrip=True,approved_buildings_byte_identical=True,static_tiles_exclude_animation=True,animated_underlays=animated_underlays,objects=objects)
(EV/'integration.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'collision.json').write_text(json.dumps(dict(width=W,height=H,blocked=[[bool(flags[y*W+x]&0xc00) for x in range(W)] for y in range(H)]))+'\n');print(json.dumps({k:v for k,v in report.items() if k!='objects'},indent=2))
