"""Local native repair: restore Route 38's original rock01 prop without repacking committed banks."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'tools/gba/maps'),str(ROOT/'tools/gba/maps/route31_catalog')]
from tiles import Tileset
from rock import ROCK_RAMP
G=Path('/workspace/routes3839-complete');S=ROOT/'gba/art/routes3839-complete/source/route38';E=S.parents[1]/'evidence';BANK='routes3839_complete'
t=Tileset(G,BANK,BANK);mats=np.load(S/'materials.npz');mask=mats['material']==list(mats['names']).index('rock01');z=dict(np.load(S/'layers.npz'));original=np.array(Image.open(S/'ground.png').convert('RGB'))
ramp=np.array(ROCK_RAMP,int)&248;src=original[mask].astype(int);chosen=((src[:,None]-ramp[None])**2*np.array([3,4,2])).sum(-1).argmin(-1)
art=np.zeros(mask.shape+(4,),np.uint8);art[mask,:3]=ramp[chosen];art[mask,3]=255
visible=mask&(z['top'][...,3]==0)
words=np.fromfile(G/'data/layouts/JohtoRoute38/map.bin','<u2').reshape(32,64);assert all((int(words[y,x])&1023)==mid for x,y,mid in [(58,0,10),(59,0,3),(58,1,28),(59,1,29)]), 'Boulder repair already applied or native cells changed.'
before=np.array(t.map_image(words.ravel().tolist(),64));blocks=[tuple(a) for a in t.blocks[0]+t.blocks[1]];attrs=t.attrs[0]+t.attrs[1]
pals=[list(t.pals[b>=6][b]) for b in range(13)];used=[set() for _ in range(13)];tiles=t.tiles[0]+t.tiles[1]
for row in blocks:
 for e in row:used[e>>12]|={i&15 for i in tiles[e&1023] if i&15}
old_used=[s.copy() for s in used];maxid=max(e&1023 for row in blocks for e in row);newtiles=[];changed=[]
def tile_rgba(e):
 ix=np.array(tiles[e&1023],np.uint8).reshape(8,8)&15
 if e&1024:ix=ix[:,::-1]
 if e&2048:ix=ix[::-1]
 p=np.array(pals[e>>12],np.uint8);out=np.zeros((8,8,4),np.uint8);out[...,:3]=p[ix];out[...,3]=np.where(ix>0,255,0);return out
for y,x in sorted(set(zip(*(v//16 for v in np.nonzero(visible))))):
 old=int(words[y,x])&1023;entries=list(blocks[old])
 for q in range(4):
  sy=y*16+q//2*8;sx=x*16+q%2*8;sl=np.s_[sy:sy+8,sx:sx+8];m=visible[sl]
  if not m.any():continue
  px=tile_rgba(entries[4+q]);px[m]=art[sl][m];colors=set(map(tuple,px[px[...,3]>0,:3].tolist()));options=[]
  for b in range(13):
   have={pals[b][i] for i in used[b]};missing=colors-have;free=[i for i in range(1,16) if i not in used[b]]
   if len(missing)<=len(free):options.append((len(missing),b,missing,free))
  assert options,('no compatible palette',x,y,q,len(colors))
  _,b,missing,free=min(options,key=lambda o:(o[0],o[1]))
  for c,i in zip(sorted(missing),free):pals[b][i]=c;used[b].add(i)
  ix=np.zeros((8,8),np.uint8)
  for yy,xx in zip(*np.nonzero(px[...,3])):ix[yy,xx]=next(i for i in used[b] if pals[b][i]==tuple(px[yy,xx,:3]))
  tid=maxid+1+len(newtiles);assert tid<1008;newtiles.append((tid,ix));entries[4+q]=tid|(b<<12)
 mid=len(blocks);assert mid<1024;blocks.append(tuple(entries));attrs.append(attrs[old]);words[y,x]=(int(words[y,x])&~1023)|mid;changed.append([int(x),int(y),old,mid])
# Only new glyph slots, appended metatiles and unused palette slots are touched.
for side in [0,1]:
 d=G/f'data/tilesets/{"secondary" if side else "primary"}/{BANK}';im=Image.open(d/'tiles.png');a=np.array(im)
 for tid,ix in newtiles:
  if (tid>=512)!=bool(side):continue
  i=tid%512;a[i//16*8:i//16*8+8,i%16*8:i%16*8+8]=ix
 out=Image.fromarray(a,'P');out.putpalette(im.getpalette());out.save(d/'tiles.png',bits=4)
 for b in range(13):
  if (b>=6)!=bool(side):continue
  if pals[b]!=list(t.pals[side][b]):(d/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
 if side:
  (d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*r) for r in blocks[512:]));(d/'metatile_attributes.bin').write_bytes(struct.pack('<%dH'%len(attrs[512:]),*attrs[512:]))
words.astype('<u2').tofile(G/'data/layouts/JohtoRoute38/map.bin')
z['flat'][mask]=art[mask];np.savez_compressed(S/'layers.npz',**z);Image.fromarray(art).save(S/'local-art/original-boulder.png')
t2=Tileset(G,BANK,BANK);after=np.array(t2.map_image(words.ravel().tolist(),64));want=before.copy();want[visible]=art[visible,:3]
assert np.array_equal(after,want)
Image.fromarray(after).save(E/'route38/native.png');Image.fromarray(after).save(E/'route38/composed.png')
report=dict(original_material='rock01',source_pixels=int(mask.sum()),visible_pixels_restored=int(visible.sum()),cells=changed,new_glyphs=len(newtiles),last_used_glyph=maxid+len(newtiles),metatiles=len(blocks),untouched_pixels_exact=True,existing_palette_slots_preserved=all(all(pals[b][i]==tuple(t.pals[b>=6][b][i]) for i in old_used[b]) for b in range(13)))
(E/'boulder-repair.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
