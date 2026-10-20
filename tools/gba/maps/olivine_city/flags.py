"""Guarded native edit: lift existing flag silhouettes above the player.
Preserve all displayed city pixels, source collision/elevation and section IDs.
"""
from pathlib import Path
import sys,json,subprocess,struct
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/olivine-city/source';E=S.parent/'evidence';O=E/'flag-underpasses';O.mkdir(exist_ok=True)
BASE='86b1e47e0305596bb76fd1a1ff94f3b47947e47d'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True)
sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
bg=np.array(Image.open(S/'native-ground.png'));fg=np.array(Image.open(S/'shared-foreground.png'));before=bg.copy();m=fg[...,3]>0;before[m]=fg[m,:3];above=np.load(S/'above.npy').copy()
# Trace complete cloth silhouettes and the connecting rope. Keep poles/bases
# in their existing physical layer; no rectangular pavement foreground.
polys=[[(115,279),(139,282),(164,283),(190,283),(214,282),(239,279),(239,282),(214,285),(190,286),(164,286),(139,285),(115,282)],[(120,282),(124,282),(124,284),(137,282),(137,289),(134,294),(129,296),(122,296),(117,294),(119,288)],[(139,284),(157,284),(157,288),(152,292),(148,296),(144,292),(140,288)],[(156,284),(172,284),(172,297),(156,297)],[(172,284),(189,284),(189,288),(185,292),(181,297),(176,293),(173,289)],[(188,284),(205,284),(205,297),(188,297)],[(204,284),(221,282),(221,286),(217,291),(213,296),(208,292),(205,288)],[(220,282),(237,280),(239,294),(224,295),(221,289)]]
maskim=Image.new('L',(1040,864));d=ImageDraw.Draw(maskim)
for dx,dy in [(0,0),(224,112)]:
 for p in polys:d.polygon([(x+dx,y+dy) for x,y in p],fill=255)
mask=np.array(maskim)>0;maskim.save(S/'flag-foreground-mask.png');maskim.save(O/'mask.png');assert not np.any(fg[...,3][mask])
# Preserve native background pixels. Duplicate only exact cloth/rope pixels to
# a transparent foreground mask; the underlying copy remains fully covered.
fg[mask,:3]=bg[mask];fg[mask,3]=255
sections=json.loads((E/'sections.json').read_text());plans=[];records=[]
for sec in sections:
 n=sec['name'];x0,y0,x1,y1=sec['box']
 if not mask[y0*16:y1*16,x0*16:x1*16].any():continue
 ts=Tileset(G,n.lower(),n.lower());grid=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y0,x1-x0);newgrid=grid.copy();glyphs=[np.zeros((8,8),np.uint8)];lookup={glyphs[0].tobytes():0};blocks={};attrs={};assigned={}
 def entry(a,bank):
  key=a.tobytes()
  if key not in lookup:
   tid=len(glyphs);glyphs.append(a)
   for h in range(2):
    for v in range(2):lookup.setdefault(a[::-1 if v else 1,::-1 if h else 1].tobytes(),tid|h<<10|v<<11)
  return lookup[key]|bank<<12
 for cy,cx in np.ndindex(grid.shape):
  y,x=(cy+y0)*16,(cx+x0)*16;mid=int(grid[cy,cx]&1023);es=ts.blocks[mid>=512][mid%512];aa=ts.attrs[mid>=512][mid%512];out=[];affected=mask[y:y+16,x:x+16].any()
  for layer in range(2):
   for q in range(4):
    e=es[layer*4+q];tid=e&1023;bank=e>>12;a=np.array(ts.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)[::-1 if e&2048 else 1,::-1 if e&1024 else 1].copy();yy=y+q//2*8;xx=x+q%2*8;mm=mask[yy:yy+8,xx:xx+8]
    if mm.any():
     bottom=es[q];bb=bottom>>12;bt=bottom&1023;ba=np.array(ts.tiles[bt>=512][bt%512],np.uint8).reshape(8,8)[::-1 if bottom&2048 else 1,::-1 if bottom&1024 else 1];pal=np.array(ts.pals[bb>=6][bb],np.uint8)
     if layer==1:
      assert not a.any();a[mm]=ba[mm];bank=bb
     # Keep the original background glyph below the exact foreground mask.
     # Its flag pixels are fully covered by that mask, preserving both scenery
     # and the tight hardware budget without putting pavement over the player.

    out.append(entry(a,bank))
  if affected:aa&=~0x3000;above[cy+y0,cx+x0]=True
  key=tuple(out)+(aa,)
  if key not in assigned:
   preferred=mid if mid not in blocks else next(i for i in range(1024) if i not in blocks);assigned[key]=preferred;blocks[preferred]=out;attrs[preferred]=aa
  newgrid[cy,cx]=(int(grid[cy,cx])&~1023)|assigned[key]
 assert np.array_equal(grid&0xfc00,newgrid&0xfc00)
 assert len(glyphs)<=1008,(n,len(glyphs));plans.append((n,glyphs,blocks,attrs,newgrid));records.append(dict(map=n,glyphs=len(glyphs),foreground_cells=int(sum(mask[y:y+16,x:x+16].any() for y in range(y0*16,y1*16,16) for x in range(x0*16,x1*16,16)))))
for n,glyphs,blocks,attrs,grid in plans:
 for part in range(2):
  p=G/f'data/tilesets/{"secondary" if part else "primary"}/{n.lower()}';start=part*512;count=512 if part==0 else max(1,len(glyphs)-512);im=Image.new('P',(128,((count+15)//16)*8));im.putpalette([c for i in range(256) for c in (i*17%256,)*3])
  for i in range(count):
   if start+i<len(glyphs):im.paste(Image.fromarray(glyphs[start+i]).convert('P'),(i%16*8,i//16*8))
  im.save(p/'tiles.png',bits=4);(p/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*blocks.get(i,[0]*8)) for i in range(start,start+512)));(p/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*[attrs.get(i,0x1000) for i in range(start,start+512)]))
 grid.tofile(G/f'data/layouts/{n}/map.bin');np.full((2,2),int(grid[0,0])|0xc00,'<u2').tofile(G/f'data/layouts/{n}/border.bin')
comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m,:3];assert np.array_equal(comp,before),'Preserve every displayed scenery pixel'
Image.fromarray(bg).save(S/'native-ground.png');Image.fromarray(fg).save(S/'shared-foreground.png');np.save(S/'above.npy',above);Image.fromarray(fg).save(O/'foreground.png');Image.fromarray(comp).save(O/'native-map.png');(O/'native-edit.json').write_text(json.dumps(dict(baseline=BASE,sections=records,mask_pixels=int(mask.sum()),city_composite_RGB_errors=0,collision_elevation_changes=0,method='Exact native cloth/rope cutouts on split foreground layer; Transparent foreground mask over existing native background; support posts untouched'),indent=2)+'\n');print(records)
