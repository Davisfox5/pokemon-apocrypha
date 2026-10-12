#!/usr/bin/env python3
"""September 22 narrow edits over the exact saved owner map, never a reconstruction."""
from pathlib import Path
import json,struct,hashlib,shutil
from PIL import Image
from tiles import Tileset
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';S=R/'tools/vendor/gba/johto-owner-direct-20260922';A=R/'gba/art/johto-restart';EV=A/'evidence'
t=Tileset(S,'cherrygrove','cherrygrove');raw=list(struct.unpack('<2688H',(S/'data/layouts/CherrygroveCity/map.bin').read_bytes()))
current=G/'data/layouts/CherrygroveCity/map.bin';guard=EV/'direct-edit-state.json';expected=hashlib.sha256((S/'data/layouts/CherrygroveCity/map.bin').read_bytes()).hexdigest()
allowed={expected}
if guard.exists():allowed.add(json.loads(guard.read_text())['map_sha256'])
assert hashlib.sha256(current.read_bytes()).hexdigest() in allowed,'New owner edits detected; stop and preserve them.'
# Eight tiles of camera scenery to either side; six below. Existing coordinates
# translate east by eight; all existing pixels outside explicit edits stay exact.
W,H=80,48;DX=8;original=[0x3e71]*(W*H)
for y in range(42):original[y*W+8:y*W+72]=raw[y*64:(y+1)*64]
final=original.copy();images={};attrs={};changed=set();boats=[];trees=[];newbuildings=[];shift=0
ents=lambda mid:t.blocks[mid>=512][mid%512]
def px(x,y):return images.get(y*W+x,t.render(final[y*W+x]&1023)).copy()
def cell(x,y,im,solid=True,behavior=0x1000):
 if 0<=x<W and 0<=y<H:
  i=y*W+x;images[i]=im.convert('RGB');attrs[i]=behavior;final[i]=(0x3c00 if solid else 0x3000)|(final[i]&1023);changed.add(i)
def put(x,y,value):
 i=y*W+x;final[i]=value;images.pop(i,None);attrs.pop(i,None);changed.add(i)
clip_min_x=0
def stamp(im,x,y):
 for dy in range(im.height//16):
  for dx in range(im.width//16):
   xx,yy=x+dx,y+dy
   if not(clip_min_x<=xx<W and 0<=yy<H):continue
   part=im.crop((dx*16,dy*16,dx*16+16,dy*16+16))
   if part.getchannel('A').getbbox():
    out=px(xx,yy).convert('RGBA');out.alpha_composite(part);cell(xx,yy,out)
native=lambda n:Image.open(A/f'native/{n}.png').convert('RGBA')
grass=raw[20*64+54];water=raw[11*64];rock=raw[12*64+6]|0xc00
# Move the exact authored house tile block, including the door behavior.
house=[raw[y*64+54:y*64+59] for y in range(21,26)]
for y in range(20,26):
 for x in range(54,59):put(x+DX,y,grass)
for dy,row in enumerate(house):
 for dx,v in enumerate(row):put(54+DX+dx,20+dy,v)
# A matching approach fills the single vacated door row, preserving flowers.
for x in [56,57]:put(x+DX,25,raw[26*64+x])
# Replace only the old bench footprint and add its north-facing version.
for x in [58,59]:put(x+DX,9,grass)
stamp(native('bench-north'),58+DX,8)
# Barge east one metatile, preserving actual animated water under the silhouette.
for y in range(14,21):
 for x in range(13,17):put(x+DX,y,water)
stamp(native('cargo-north'),14+DX,14)
# Match northern and southern forest phases, without repainting owner's trees.
for y in range(H):
 for x in range(W):
  if x<8:
   put(x,y,raw[y*64] if y<10 else water)
  elif x>=72:put(x,y,grass|0xc00)
  elif y>=42:put(x,y,water if x<39 else grass|0xc00)
# West land padding continues the full tree silhouette, not repeated fragments.
for y in range(7):
 for x in range(8):put(x,y,grass|0xc00)
for y in [0,3]:
 for x in range(-1,8,2):stamp(native('tree'),x,y)
# Repair only the actual outer two forest columns and continue their whole crowns.
for y in range(H):
 for x in range(70,W):put(x,y,grass|0xc00)
for y in [-1,2,5,8,11,14,20,23,26,29]:
 for x in range(70,80,2):stamp(native('tree'),x,y)
# Below the residential lane, use the existing forest's odd-column, three-row phase.
clip_min_x=70
for y in [33,36,39,42,45]:
 for x in range(69,80,2):stamp(native('tree'),x,y)
clip_min_x=0
for y in [42,45]:
 for x in range(39,70,2):stamp(native('tree'),x,y)
# Extend the road with straight edge/body metatiles rather than repeating its cap.
for y in [17,18,19]:
 for x in range(70,80):put(x,y,raw[y*64+61])
# Western surf barrier only where the original edge was water, never land/cliff.
reef=[]
for y in range(42):
 mid=raw[y*64]&1023
 if (t.attrs[mid>=512][mid%512]&255)==0x15:
  put(DX,y,rock);reef.append([DX,y])
# Close the water to the south too, preventing a bypass around the west reef.
for x in range(1,30):put(x+DX,41,rock);reef.append([x+DX,41])
# Preserve expected images before tile allocation, including exact copied cells.
for i in changed:
 if i not in images:images[i]=t.render(final[i]&1023);attrs[i]=t.attrs[(final[i]&1023)>=512][(final[i]&1023)%512]

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
# Water uses the native surf elevation with no hard wall collision. Rocks retain
# impassable flags and a non-water behavior; walking land stays at elevation 3.
water_collision_changes=[]
for i,v in enumerate(final):
 mid=v&1023;behavior=(at[mid-512] if mid>=512 else t.attrs[0][mid])&255
 if behavior in (0x10,0x15):
  final[i]=(v&1023)|0x1000;water_collision_changes.append(i)
(G/'data/layouts/CherrygroveCity/map.bin').write_bytes(struct.pack('<'+'H'*len(final),*final))
installed=Tileset(G,'cherrygrove','cherrygrove');render=installed.map_image(final,W);render.save(EV/'port-overview.png')
for i in range(W*H):
 expected=images.get(i,t.render(original[i]&1023));assert installed.render(final[i]&1023).tobytes()==expected.tobytes(),('pixel mismatch',i%W,i//W)
(EV/'port-integration.json').write_text(json.dumps(dict(allocated_tiles=len(allocated),remaining_tiles=len(free),metatiles=len(blocks),changed_cells=len(changed),unchanged_cells_preserved=W*H-len(changed),exact_pixel_roundtrip=True,boats=boats,trees=trees,newbuildings=newbuildings,shift=shift),indent=2)+'\n')
print(json.dumps(dict(allocated_tiles=len(allocated),remaining_tiles=len(free),metatiles=len(blocks),shift=shift)))

# Translate every authored event and return warp exactly once from the snapshot.
for folder in (S/'data/maps').glob('Cherrygrove*'):
 p=folder/'map.json'
 if not p.exists():continue
 m=json.loads(p.read_text());name=folder.name
 if name=='CherrygroveCity':
  for kind in ['object_events','warp_events','coord_events','bg_events']:
   for e in m.get(kind,[]):e['x']+=DX
  m['warp_events'][2]['y']-=1
  for e in m['object_events']:
   if e['local_id']=='LOCALID_JOHTO_GIRL':e.update(x=53+DX,y=20)
 elif name=='CherrygroveRoute30Approach':
  for kind in ['object_events','warp_events','coord_events','bg_events']:
   for e in m.get(kind,[]):e['x']+=DX
 (G/'data/maps'/name/'map.json').write_text(json.dumps(m,indent=2)+'\n')
spec=json.loads((S/'art/layout.json').read_text());spec.update(width=W,height=H,spawn=[48,20])
for b in spec['buildings']:
 b['x']+=DX;b['door'][0]+=DX
 if b['name']=='NeighborHouse':b['y']-=1;b['door'][1]-=1
for b in spec.get('port',[]):b['x']+=DX+(1 if b['name']=='cargo-north' else 0)
(A/'layout.json').write_text(json.dumps(spec,indent=2)+'\n')
res=json.loads((S/'art/residents.json').read_text())
for r in res:
 r['start'][0]+=DX
 for xy in r['positions']:xy[0]+=DX
 if r['name']=='JOHTO_GIRL':r.update(start=[61,20],positions=[[60,20],[61,20]])
(A/'residents.json').write_text(json.dumps(res,indent=2)+'\n')
# Full tree repeat in the two approach buffers; path edges remain straight.
pattern=[final[(27+dy)*W+41+dx] for dy in range(3) for dx in range(2)]
layouts=json.loads((S/'data/layouts/layouts.json').read_text())
for name,w,h in [('CherrygroveCity',W,H),('CherrygroveRoute30Approach',W,18),('CherrygroveRoute29Approach',24,H)]:
 for l in layouts['layouts']:
  if l['blockdata_filepath']==f'data/layouts/{name}/map.bin':l.update(width=w,height=h)
 if name=='CherrygroveCity':continue
 phase=1 if name.endswith('29Approach') else 0
 cells=[pattern[((y+phase)%3)*2+x%2] for y in range(h) for x in range(w)]
 for y in range(h):
  for x in range(w):
   if name.endswith('30Approach') and y>=12 and 43<=x<=45:cells[y*w+x]=final[x] if y>12 else original[x]
   if name.endswith('29Approach') and x<12 and 17<=y<=19:cells[y*w+x]=final[y*W+78]
 (G/f'data/layouts/{name}/map.bin').write_bytes(struct.pack('<'+'H'*len(cells),*cells))
(G/'data/layouts/layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
render.save(EV/'town-overview.png')
(A/'native/collision.json').write_text(json.dumps(dict(width=W,height=H,blocked=[[bool(final[y*W+x]&0xc00) for x in range(W)] for y in range(H)]))+'\n')
# Exact owner preservation check, excluding only explicit edits in original bounds.
untouched=0;edits=[]
for y in range(42):
 for x in range(64):
  i=y*W+x+DX
  if i not in changed:
   assert final[i]==raw[y*64+x] or i in water_collision_changes
   assert installed.render(final[i]&1023).tobytes()==t.render(raw[y*64+x]&1023).tobytes()
   untouched+=1
  else:edits.append([x,y])
report=dict(source_snapshot=str(S.relative_to(R)),translated_x=DX,surf_water_collision_cells=len(water_collision_changes),unchanged_owner_cells=untouched,explicitly_edited_owner_cells=edits,reef_cells=reef,map_sha256=hashlib.sha256(current.read_bytes()).hexdigest())
(EV/'direct-edit-state.json').write_text(json.dumps(report,indent=2)+'\n')
print('Exact owner cells preserved:',untouched)
