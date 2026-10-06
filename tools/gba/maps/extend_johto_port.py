#!/usr/bin/env python3
"""Narrow, reproducible port extension over the preserved owner-authored snapshot.
Never imports or reruns the destructive fresh-layout builder.
"""
from pathlib import Path
import argparse,json,struct,itertools,shutil,hashlib
from PIL import Image,ImageDraw
from tiles import Tileset
R=Path(__file__).resolve().parents[3];A=R/'gba/art/johto-restart';S=A/'owner-20260921';G=R/'tools/vendor/gba/johto-boundary-review-game';EV=A/'evidence'
current=G/'data/layouts/CherrygroveCity/map.bin';guard=EV/'port-authored-state.json'
allowed={hashlib.sha256((S/'data/layouts/CherrygroveCity/map.bin').read_bytes()).hexdigest()}
if guard.exists():allowed.add(json.loads(guard.read_text())['map_sha256'])
assert hashlib.sha256(current.read_bytes()).hexdigest() in allowed, 'New owner map edits detected: preserve and incorporate them before regeneration.'
p=argparse.ArgumentParser();p.add_argument('--undo-shift',action='store_true');args=p.parse_args()
t=Tileset(S,'cherrygrove','cherrygrove');W,H=64,36
raw=list(struct.unpack('<2304H',(S/'data/layouts/CherrygroveCity/map.bin').read_bytes()))
shift=0 if args.undo_shift else -5
original=[raw[((y-5)%H)*W+x] for y in range(H) for x in range(W)] if args.undo_shift else raw.copy()
original += [0x3c01]*(64*6)
H=42
original=[v for y in range(H) for v in original[y*64:(y+1)*64]+[0x3c01]*8]
W=72
final=original.copy();changed=set();images={};attrs={};boats=[]
def ents(mid):return t.blocks[mid>=512][mid-512 if mid>=512 else mid]
def attr(mid):return t.attrs[mid>=512][mid-512 if mid>=512 else mid]
def px(x,y):
 i=y*W+x
 return images.get(i,t.render(final[i]&1023)).copy()
def setcell(x,y,im,solid=False,behavior=0x1000):
 if 0<=x<W and 0<=y<H:
  i=y*W+x;images[i]=im.convert('RGB');attrs[i]=behavior;final[i]=(0x3c00 if solid else 0x3000)|(final[i]&1023);changed.add(i)
def put(x,y,mid,solid=False):setcell(x,y,t.render(mid),solid,attr(mid)|0x1000)
def rect(x,y,w,h,mid=1,solid=False):
 for yy in range(y,y+h):
  for xx in range(x,x+w):put(xx,yy,mid,solid)
def stamp(im,x,y,name,solid=True):
 for dy in range(im.height//16):
  for dx in range(im.width//16):
   xx,yy=x+dx,y+dy
   if not(0<=xx<W and 0<=yy<H):continue
   part=im.crop((dx*16,dy*16,dx*16+16,dy*16+16))
   if not part.getchannel('A').getbbox():continue
   out=px(xx,yy).convert('RGBA');out.alpha_composite(part);setcell(xx,yy,out,solid,0x1000)
def native(name):return Image.open(A/f'native/{name}.png').convert('RGBA')
def prepare(name,size):
 im=Image.open(A/f'generated/{name}.png').convert('RGBA');im.putalpha(im.getchannel('A').point(lambda v:255 if v>=224 else 0));im=im.crop(im.getbbox());im.thumbnail(size,Image.Resampling.NEAREST)
 out=Image.new('RGBA',size);out.paste(im,((size[0]-im.width)//2,size[1]-im.height))
 colors=t.pals[1][10][1:];out.putdata([(*min(colors,key=lambda c:sum((c[j]-v[j])**2 for j in range(3))),255) if v[3] else (0,0,0,0) for v in out.getdata()]);out.save(A/f'native/{name}.png');return out
# The extension is positioned relative to the retained town, not a new coastline.
# Southern forest replacement is wholly east of the authored coast.
base=27+shift
rect(31,base,10,H-base)
rect(40,31+shift,20,H-(31+shift))
# Remove the old outer tree strip only where the residential clearing needs it.
rect(60,27+shift,4,H-(27+shift))
# Remove orphaned tree fragments left on the southwest bank by manual painting.
# Retain the subsequently recovered owner shoreline edits.
put(30,28,0x19d,True)
for yy in range(35,H):
 for xx in range(30):put(xx,yy,0x170,True);original[yy*W+xx]=0x3d70
 put(30,yy,0x19d,True)
# Two houses occupy the former southern forest, with a shared connected lane.
rect(54,20,8,7,1)
rect(62,20,2,7,1,True)
for yy in [20,23,26]:stamp(native('tree'),62,yy,'tree')
house_y=27+shift
rect(41,house_y,19,7)
path={(x,y) for y in range(29+shift,33+shift) for x in range(39,61)}
path|={(x,y) for y in range(24+shift,32+shift) for x in range(50,54)}
path|={(x,y) for x in range(30,41) for y in range(18+shift,20+shift)}
path|={(x,y) for x in range(52,58) for y in [25,26]}
for x,y in sorted(path):
 if not (0<=y<H):continue
 n=(x,y-1) in path;s=(x,y+1) in path;w=(x-1,y) in path;e=(x+1,y) in path
 mid=0x121 if n and s else 0x119 if not n else 0x129
 if not w:mid=0x120 if n and s else 0x118 if not n else 0x128
 if not e:mid=0x122 if n and s else 0x11a if not n else 0x12a
 put(x,y,mid)
newbuildings=[]
for name,x,warp in [('HarborHouse',42,6),('GardenHouse',55,7)]:
 stamp(native('house'),x,house_y,name);door=[x+2,house_y+4];i=door[1]*W+door[0];final[i]&=1023;attrs[i]=0x1069
 newbuildings.append(dict(name=name,x=x,y=house_y,style='house',door=door,warp=warp))
stamp(native('house'),54,20,'NeighborHouse')
final[24*W+56]&=1023;attrs[24*W+56]=0x1069
put(31,27,0x2d4,True);put(32,27,0x2d5,True)
# Full crowns, consistently spaced; trunks never form the old half-tree fringe.
trees=[]
for y in range(base,H,3):
 for x in [31,33,35,37]:trees.append((x,y))
for y in range(33+shift,H,3):
 for x in range(39,64,2):trees.append((x,y))
for y in range(27+shift,33+shift,3):trees.append((62,y))
for x,y in sorted(trees,key=lambda p:(p[1],p[0])):stamp(native('tree'),x,y,'tree')
# A continuous southern hedge/forest collision prevents any apparent exit.
for x in range(31,64):
 i=(H-1)*W+x;final[i]|=0xc00
# Harbor: narrow approach crosses the beach, keeping every shoreline cell's
# underlying pixels intact. Open pier terminates in pilings, not a false exit.
wood=t.pals[1][7];dark=min(wood[1:],key=sum);light=max(wood[1:],key=sum)
mid=sorted(set(wood[1:]),key=sum)[len(set(wood[1:]))//2]
deck={(x,y) for x in range(17,30) for y in range(18+shift,20+shift)}
deck|={(x,y) for x in range(17,19) for y in range(15+shift,23+shift)}
for x,y in sorted(deck):
 im=px(x,y);d=ImageDraw.Draw(im);d.rectangle((0,0,15,15),fill=mid)
 for py in [0,5,10,14]:d.line((0,py,15,py),fill=dark);d.line((0,py+1,15,py+1),fill=light)
 d.point((2,3),fill=dark);d.point((13,12),fill=dark)
 setcell(x,y,im)
 # Piling caps on outer corners remain visual and blocked at the pier ends.
 if y==15+shift and x in [17,18]:
  d.rectangle((1,1,5,5),fill=dark);d.rectangle((2,2,4,3),fill=light);setcell(x,y,im,True)
for yy in [23,24]:
 for xx in range(15,19):final[yy*W+xx]=(final[yy*W+xx]&1023)|0x3000
put(22,23,0x170,True);original[23*W+22]=0x3d70
for name,size,x,y in [('cargo-north',(48,112),15,14+shift),('fishing-north',(32,64),19,14+shift),('fishing-boat',(64,32),20,23+shift)]:
 im=prepare(name,size);stamp(im,x,y,name);boats.append(dict(name=name,x=x,y=y,width=size[0],height=size[1]))
# Whole northern crowns, a clear Route 30 corridor, and a sheltered pond.
rect(0,0,35,7,1,True)
for yy in [0,3]:
 for xx in range(-1,34,2):stamp(native('tree'),xx,yy,'tree')
for yy in range(3):
 for xx,mid0 in [(35,0x120),(36,0x121),(37,0x122)]:put(xx,yy,mid0)
rect(38,0,18,5,1,True)
for xx in range(38,56,2):stamp(native('tree'),xx,0,'tree')
rect(56,0,8,12,1)
for xx in range(56,64,2):stamp(native('tree'),xx,0,'tree')
# Rounded lake lies beneath the northern trees, with a full bank on each side.
water=t.render(0x170);grass=t.render(1)
for yy in range(3,9):
 for xx in range(56,64):
  im=grass.copy();wet=False
  for py in range(16):
   for px0 in range(16):
    gx=xx*16+px0;gy=yy*16+py
    dx=max(58*16-gx,0,gx-61*16);dy=max(5*16-gy,0,gy-6*16)
    d2=dx*dx+dy*dy
    if d2<23*23:im.putpixel((px0,py),water.getpixel((px0,py)));wet=True
    elif d2<26*26:im.putpixel((px0,py),min(grass.getdata(),key=sum))
  setcell(xx,yy,im,wet)
  if wet:original[yy*W+xx]=0x3d70
# Clear a small approach beside the existing garden, keeping a forest at the east.
rect(59,9,3,9,1)
rect(62,8,2,9,1,True)
for yy in [8,11,14]:stamp(native('tree'),62,yy,'tree')
for yy in range(10,18):
 for xx in [59,60]:put(xx,yy,0x121)
stamp(prepare('bench-north',(32,16)),58,8,'bench')
# Remove the complete old tree footprint beside the garden, including its last column.
rect(58,12,1,5,1)
for yy in [12,13,14]:setcell(58,yy,px(57,yy),True)
for xx in range(W):
 if xx not in [35,36,37]:final[xx]|=0xc00

# Retain the owner's hand-painted path joins.
path_atlas=Image.open(S/'path-edits.png')
for n,c in enumerate(json.loads((S/'path-edits.json').read_text())):
 setcell(c['x'],c['y'],path_atlas.crop((0,n*16,16,n*16+16)))
# Eight columns of forest keep every eastern camera view inside authored scenery.
rect(64,0,8,H,1,True)
for yy in list(range(-1,17,3))+list(range(20,H,3)):
 for xx in range(64,72,2):stamp(native('tree'),xx,yy,'tree')
for yy in range(17,20):
 for xx in range(64,W):put(xx,yy,0x119 if yy==17 else 0x129 if yy==19 else 0x121)

# Keep all unchanged metatile references and water-animation slots verbatim.
animated=set(range(432,462))|set(range(464,474))|set(range(480,490))|set(range(496,502))|set(range(508,512))
used={0}|animated|set(range(1008,1024))
for f in (S/'data/layouts').glob('Cherrygrove*/map.bin'):
 if f.parent.name not in ['CherrygroveCity','CherrygroveRoute29Approach','CherrygroveRoute30Approach']:continue
 vals=final if f.parent.name=='CherrygroveCity' else struct.unpack('<'+'H'*(f.stat().st_size//2),f.read_bytes())
 for v in vals:
  used.update(e&1023 for e in ents(v&1023))
free=[i for i in range(1,1008) if i not in used];allocated=[];lookup={}
output=t.tiles[0]+t.tiles[1]
for tid,rawtile in enumerate(output):
 if tid not in used or tid in animated or tid>=1008:continue
 for hf,vf,bits in [(0,0,0),(1,0,1024),(0,1,2048),(1,1,3072)]:
  key=bytes(rawtile[(7-y if vf else y)*8+(7-x if hf else x)] for y in range(8) for x in range(8));lookup.setdefault(key,tid|bits)
def tile(data,bank):
 key=bytes(data)
 if key not in lookup:
  assert free,('tile capacity',len(allocated));tid=free.pop(0);output[tid]=list(data);allocated.append(tid);lookup[key]=tid
 return lookup[key]|bank<<12
pm={b:{c:i for i,c in reversed(list(enumerate(t.pals[b>=6][b]))) if i} for b in range(13)}
sets={b:set(v) for b,v in pm.items()};blocks=list(t.blocks[1]);at=[(v&0xfff)|0x1000 for v in t.attrs[1]];bl={(tuple(e),a):512+i for i,(e,a) in enumerate(zip(blocks,at))}
for i,im in sorted(images.items()):
 pairs=[];old=ents(original[i]&1023)
 for q,(dx,dy) in enumerate([(0,0),(8,0),(0,8),(8,8)]):
  cs=list(im.crop((dx,dy,dx+8,dy+8)).getdata());palette_choices=[(a,b) for a in range(13) for b in range(a,13) if set(cs)<=sets[a]|sets[b]]
  assert palette_choices,('palette',i%W,i//W,q)
  def cost(ab):
   a,b=ab;lo=bytes(pm[a].get(c,0) for c in cs);hi=bytes(0 if c in sets[a] else pm[b][c] for c in cs);return (int(lo not in lookup)+int(hi not in lookup),a!=b)
  a,b=min(palette_choices,key=cost);lo=[pm[a].get(c,0) for c in cs];hi=[0 if c in sets[a] else pm[b][c] for c in cs]
  # Preserve live water under transparently composited boat/dock edges.
  oe=old[q];tid=oe&1023
  if tid in animated:
   rawtile=t.tiles[tid>=512][tid%512];bank=oe>>12;low=[t.pals[bank>=6][bank][rawtile[(7-y if oe&2048 else y)*8+(7-x if oe&1024 else x)]] for y in range(8) for x in range(8)]
   delta=[None if c==v else c for c,v in zip(cs,low)];bs=[b for b in range(13) if (set(delta)-{None})<=sets[b]]
   if bs:pairs.append((oe,tile([0 if c is None else pm[bs[0]][c] for c in delta],bs[0])));continue
  pairs.append((tile(lo,a),tile(hi,b)))
 ent=tuple(a for a,b in pairs)+tuple(b for a,b in pairs);key=(ent,attrs[i])
 if key not in bl:bl[key]=512+len(blocks);blocks.append(ent);at.append(attrs[i])
 final[i]=(final[i]&~1023)|bl[key]
assert len(blocks)<=512,('metatile capacity',len(blocks))
for side in range(2):
 folder=G/f'data/tilesets/{"secondary" if side else "primary"}/cherrygrove';sheet=Image.new('P',(128,256));sheet.putpalette(Image.open(t.dirs[side]/'tiles.png').getpalette())
 for j,values in enumerate(output[side*512:(side+1)*512]):
  im=Image.new('P',(8,8));im.putdata(values);sheet.paste(im,(j%16*8,j//16*8))
 sheet.save(folder/'tiles.png')
f=G/'data/tilesets/secondary/cherrygrove';(f/'metatiles.bin').write_bytes(struct.pack('<'+'H'*(len(blocks)*8),*[v for b in blocks for v in b]));(f/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(at),*at))
(G/'data/layouts/CherrygroveCity/map.bin').write_bytes(struct.pack('<'+'H'*len(final),*final))
installed=Tileset(G,'cherrygrove','cherrygrove');render=installed.map_image(final,W);render.save(EV/'port-overview.png')
for i in range(W*H):
 expected=images.get(i,t.render(original[i]&1023));assert installed.render(final[i]&1023).tobytes()==expected.tobytes(),('pixel mismatch',i%W,i//W)
(EV/'port-integration.json').write_text(json.dumps(dict(allocated_tiles=len(allocated),remaining_tiles=len(free),metatiles=len(blocks),changed_cells=len(changed),unchanged_cells_preserved=W*H-len(changed),exact_pixel_roundtrip=True,boats=boats,trees=trees,newbuildings=newbuildings,shift=shift),indent=2)+'\n')
print(json.dumps(dict(allocated_tiles=len(allocated),remaining_tiles=len(free),metatiles=len(blocks),shift=shift)))
# New homes use separate quiet preview interiors; existing IDs stay untouched.
town=json.loads((S/'data/maps/CherrygroveCity/map.json').read_text());spec=json.loads((S/'layout.json').read_text())
for b in spec['buildings']:
 if b['name']=='NeighborHouse':b['y']-=1;b['door'][1]-=1
 b['y']+=shift;b['door'][1]+=shift;town['warp_events'][b['warp']].update(x=b['door'][0],y=b['door'][1])
for b in newbuildings:
 name='Cherrygrove'+b['name'];mid='MAP_CHERRYGROVE_'+('HARBOR_HOUSE' if b['name']=='HarborHouse' else 'GARDEN_HOUSE')
 house=json.loads((G/'data/maps/CherrygroveNeighborHouse/map.json').read_text());house.update(id=mid,name=name,object_events=[])
 for w in house['warp_events']:w['dest_warp_id']=str(b['warp'])
 folder=G/'data/maps'/name;folder.mkdir(exist_ok=True);(folder/'map.json').write_text(json.dumps(house,indent=2)+'\n');(folder/'scripts.inc').write_text(name+'_MapScripts::\n\t.byte 0\n')
 groups=json.loads((G/'data/maps/map_groups.json').read_text())
 if name not in groups['gMapGroup_Cherrygrove']:groups['gMapGroup_Cherrygrove'].append(name)
 (G/'data/maps/map_groups.json').write_text(json.dumps(groups,indent=2)+'\n')
 town['warp_events'].append(dict(x=b['door'][0],y=b['door'][1],elevation=0,dest_map=mid,dest_warp_id='0'))
for o in town['object_events']:
 o['y']+=shift
 if o['local_id']=='LOCALID_JOHTO_GIRL':o.update(x=60,y=21+shift)
for o in town['bg_events']:o['y']+=shift
(G/'data/maps/CherrygroveCity/map.json').write_text(json.dumps(town,indent=2)+'\n')
spec['width']=W;spec['height']=H;spec['east_exit']=[W-1,17,3];spec['buildings']+=newbuildings;spec['trees']=trees;spec['port']=boats;spec['spawn']=[40,20+shift]
(A/'layout.json').write_text(json.dumps(spec,indent=2)+'\n')
res=json.loads((S/'residents.json').read_text())
for o in res:
 o['start'][1]+=shift
 for pos in o['positions']:pos[1]+=shift
 if o['name']=='JOHTO_GIRL':o.update(start=[60,21+shift],positions=[[59,21+shift],[60,21+shift]])
(A/'residents.json').write_text(json.dumps(res,indent=2)+'\n')
render.save(EV/'town-overview.png')
(A/'native/collision.json').write_text(json.dumps(dict(width=W,height=H,blocked=[[bool(final[y*W+x]&0xc00) for x in range(W)] for y in range(H)]))+'\n')
p=G/'data/event_scripts.s';s=p.read_text()
for name in ['CherrygroveHarborHouse','CherrygroveGardenHouse']:
 line=f'.include "data/maps/{name}/scripts.inc"'
 if line not in s:s+='\n'+line+'\n'
p.write_text(s)

(EV/'port-authored-state.json').write_text(json.dumps(dict(map_sha256=hashlib.sha256(current.read_bytes()).hexdigest()),indent=2)+'\n')
p=G/'src/apocrypha_map_proof.c';s=p.read_text().replace('MAP_CHERRYGROVE_ROUTE30_APPROACH};','MAP_CHERRYGROVE_ROUTE30_APPROACH, MAP_CHERRYGROVE_HARBOR_HOUSE, MAP_CHERRYGROVE_GARDEN_HOUSE};').replace('(region & 255) % 11','(region & 255) % ARRAY_COUNT(sMapProofMaps)');p.write_text(s)

layouts=json.loads((G/'data/layouts/layouts.json').read_text())
for row in layouts['layouts']:
 if row['id'] in ['LAYOUT_CHERRYGROVE_CITY','LAYOUT_CHERRYGROVE_ROUTE29_APPROACH']:row['height']=H
 if row['id'] in ['LAYOUT_CHERRYGROVE_CITY','LAYOUT_CHERRYGROVE_ROUTE30_APPROACH']:row['width']=W
 if row['id']=='LAYOUT_CHERRYGROVE_ROUTE29_APPROACH':row['width']=24
 if row['id']=='LAYOUT_CHERRYGROVE_ROUTE30_APPROACH':row['height']=18
(G/'data/layouts/layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
pattern=[final[(27+dy)*W+33+dx] for dy in range(3) for dx in range(2)]
for name,w,h in [('CherrygroveRoute30Approach',W,18),('CherrygroveRoute29Approach',24,H)]:
 phase=1 if name.endswith('29Approach') else 0
 cells=[pattern[((y+phase)%3)*2+x%2] for y in range(h) for x in range(w)]
 for y in range(h):
  for x in range(w):
   if name.endswith('30Approach') and y>=12 and 35<=x<=37:cells[y*w+x]=original[x] if y==12 else final[x]
   if name.endswith('29Approach') and x<12 and 17<=y<=19:cells[y*w+x]=final[y*W+63]
 (G/f'data/layouts/{name}/map.bin').write_bytes(struct.pack('<'+'H'*len(cells),*cells))
 # The unreachable far boundary uses foliage only; accessible views are padded.
 (G/f'data/layouts/{name}/border.bin').write_bytes(struct.pack('<4H',*pattern[:4]))
(G/'data/layouts/CherrygroveCity/border.bin').write_bytes(struct.pack('<4H',*pattern[:4]))
