"""Guarded, additive native edit of df08620e: inner joins and extra coastal tier.
Preserve every existing metatile/glyph and all pixels outside the recorded cells.
Never replay on a later owner-edited map. Palette files and renderer are untouched.
"""
from pathlib import Path
import sys,json,subprocess,struct,csv
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/olivine-city/source';A=S/'base-terrain';E=S.parent/'evidence';O=E/'corner-revision';O.mkdir(exist_ok=True)
BASE='df08620e053e1a437557370399cac39667bbd2a4'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True)
sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
from elevation import build,cliffs
sections=json.loads((E/'sections.json').read_text());ts=Tileset(G,'olivinecity01','olivinecity01');donor=Tileset(G)
before=np.array(Image.open(S/'native-ground.png'));ids=np.load(A/'metatile-map.npy');oldids=ids.copy();physical=np.load(A/'material.npy');oldphysical=physical.copy();solid=np.load(S/'solid.npy');oldsolid=solid.copy();oldheight=np.load(A/'height.npy');mat,height=build();wall,ledger=cliffs(mat,height);oldgeo=json.loads((A/'geometry.json').read_text());oldwall={(v['x'],v['y']):v for v in oldgeo['cliffs']}
coast=(oldheight==0)&(np.indices(oldheight.shape)[1]>=39)&np.isin(physical,['grass','cliff']);assert int(coast.sum())==69
assert np.array_equal(height[~coast],oldheight[~coast]);assert np.all(height[coast]==-1)
# Immutable existing atlas entries, including deliberate flip sharing.
usedglyphs=max(e&1023 for m in set(map(int,ids.ravel())) for e in ts.blocks[0][m])+1
glyphs=[np.array(ts.tiles[0][i],np.uint8).reshape(8,8) for i in range(usedglyphs)];lookup={}
for tid,a in enumerate(glyphs):
 for h in range(2):
  for v in range(2):lookup.setdefault(a[::-1 if v else 1,::-1 if h else 1].tobytes(),tid|h<<10|v<<11)
blocks=[list(b) for b in ts.blocks[0][:int(ids.max())+1]];block_lookup={tuple(b):i for i,b in enumerate(blocks)}
def entry(a,bank):
 key=a.tobytes()
 if key not in lookup:
  tid=len(glyphs);glyphs.append(a)
  for h in range(2):
   for v in range(2):lookup.setdefault(a[::-1 if v else 1,::-1 if h else 1].tobytes(),tid|h<<10|v<<11)
 return lookup[key]|bank<<12

def block(es):
 key=tuple(es)
 if key not in block_lookup:block_lookup[key]=len(blocks);blocks.append(es)
 return block_lookup[key]
water={}
for y,x in np.argwhere(physical=='water'):water.setdefault((int(x%4),int(y%4)),int(ids[y,x]))
remap={(131,131,139):(104,72,56),(98,65,82):(104,72,56),(131,90,90):(128,88,64),(156,115,115):(160,112,80),(189,148,139):(192,144,96),(222,180,164):(216,176,120),(238,213,205):(216,176,120)}
rockpal=ts.pals[0][5];donors={};changes=[]
def rock(mid):
 if mid not in donors:
  ar=np.array(donor.render(mid));pix=np.zeros((16,16),np.uint8)
  for rgb,c in remap.items():pix[np.all(ar==rgb,2)]=rockpal.index(c)
  assert np.any(pix);donors[mid]=pix
 return donors[mid]
for y,x in np.argwhere(coast):
 ids[y,x]=water[x%4,y%4];physical[y,x]='water';solid[y,x]=True;changes.append(dict(x=int(x),y=int(y),reason='remove extra lowest coastal grass/rock course'))
for row in ledger:
 x,y=row['x'],row['y'];mid=int(row['donor_metatile'],16);old=oldwall[x,y];inside='concave' in row['orientation'];sea=row['under']=='water' and old['under']!='water'
 if not inside and not sea:continue
 a=rock(mid);es=[]
 for q in range(4):es.append(entry(a[q//2*8:q//2*8+8,q%2*8:q%2*8+8],5))
 # Native two-layer metatile: exact existing ocean below transparent rock.
 # Both layers retain COVERED behavior (behind the player); walls are solid.
 if sea:es=blocks[water[x%4,y%4]][:4]+es
 else:
  assert np.all(a),'Inside corner must be a full native rock join'
  es=es+[0]*4
 ids[y,x]=block(es);changes.append(dict(x=x,y=y,reason='native inward corner' if inside else 'sea directly meets retained cliff',old_donor=old['donor_metatile'],new_donor=hex(mid)))
assert len(blocks)<=512 and len(glyphs)<=1008
# Decode the exact new entries, not an artist preview.
def render(es):
 out=np.zeros((16,16,3),np.uint8)
 for layer in range(2):
  for q,e in enumerate(es[layer*4:layer*4+4]):
   tid=e&1023;bank=e>>12;pix=glyphs[tid][::-1 if e&2048 else 1,::-1 if e&1024 else 1];pal=np.array(ts.pals[bank>=6][bank],np.uint8);view=out[q//2*8:q//2*8+8,q%2*8:q%2*8+8];m=pix!=0;view[m]=pal[pix[m]]
 return out
native=before.copy();allowed=np.zeros(ids.shape,bool)
for c in changes:
 x,y=c['x'],c['y'];allowed[y,x]=True;native[y*16:y*16+16,x*16:x*16+16]=render(blocks[int(ids[y,x])])
assert np.array_equal(ids[~allowed],oldids[~allowed]);pixelmask=np.repeat(np.repeat(allowed,16,0),16,1);assert np.array_equal(native[~pixelmask],before[~pixelmask])
# All retained straight/exterior rock pixels remain exact, including at water.
for row in ledger:
 if 'concave' in row['orientation']:continue
 x,y=row['x'],row['y'];alpha=rock(int(row['donor_metatile'],16))!=0
 # The prior packer omitted the donor's brightest rock color. Preserve all
 # previously present rock pixels; restore those missing light pixels at the
 # revised shore so they cannot become blue pinholes through the rock cap.
 alpha[np.all(np.array(donor.render(int(row['donor_metatile'],16)))==(238,213,205),2)]=False
 assert np.array_equal(native[y*16:y*16+16,x*16:x*16+16][alpha],before[y*16:y*16+16,x*16:x*16+16][alpha]),(x,y)
for sec in sections:
 n=sec['name'];x,y,x1,y1=sec['box'];grid=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x);grid=(grid&0xfc00)|ids[y:y1,x:x1];removed=coast[y:y1,x:x1];grid[removed]=0x1c00|ids[y:y1,x:x1][removed];grid.tofile(G/f'data/layouts/{n}/map.bin')
 for part in range(2):
  folder=G/f'data/tilesets/{"secondary" if part else "primary"}/{n.lower()}';start=part*512
  # Add glyphs in the existing bank's unused tail; existing entries never move.
  count=512 if part==0 else max(1,len(glyphs)-512);im=Image.open(folder/'tiles.png');out=Image.new('P',(128,((count+15)//16)*8));out.putpalette(im.getpalette())
  for i in range(count):
   if start+i<len(glyphs):out.paste(Image.fromarray(glyphs[start+i]).convert('P'),(i%16*8,i//16*8))
  out.save(folder/'tiles.png',bits=4)
  if part==0:
   oldbytes=(folder/'metatiles.bin').read_bytes();newbytes=b''.join(struct.pack('<8H',*b) for b in blocks);(folder/'metatiles.bin').write_bytes(newbytes+oldbytes[len(newbytes):])
# Current editable ledgers and exact source-ground render; no prop overlay added.
for p in [S/'native-ground.png',E/'native-map.png',A/'assembled-preview.png',O/'native-map.png']:Image.fromarray(native).save(p)
Image.fromarray(before).save(O/'before.png');Image.fromarray((pixelmask*255).astype(np.uint8)).save(O/'changed-cells.png')
for p,a in [(A/'metatile-map.npy',ids),(A/'height.npy',height),(A/'cliff-level.npy',height),(A/'solid.npy',solid),(S/'solid.npy',solid),(A/'material.npy',physical),(S/'material.npy',physical)]:np.save(p,a)
oldgeo['cliffs']=ledger;oldgeo['owner_revision']='Remove extra lowest coastal course; use native mountain inward joints 89/74/BF/BE.';(A/'geometry.json').write_text(json.dumps(oldgeo,indent=2)+'\n')
report=dict(baseline=BASE,coastal_cells_removed=int(coast.sum()),open_coastal_cells_removed=int((coast&~oldsolid).sum()),inside_corners_replaced=sum('concave' in r['orientation'] for r in ledger),affected_cells=int(allowed.sum()),outside_edit_RGB_errors=0,retained_straight_and_convex_rock_RGB_errors=0,palette_files_unchanged=True,metatiles_before=int(oldids.max())+1,metatiles_after=len(blocks),glyphs_before=usedglyphs,glyphs_after=len(glyphs),changes=changes)
(O/'native-edit.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='changes'})
