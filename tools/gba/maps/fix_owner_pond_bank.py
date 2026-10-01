#!/usr/bin/env python3
"""Repair ten pond-edge cells in the latest owner map; preserve all other cells."""
from pathlib import Path
import struct,json,hashlib
from tiles import Tileset
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';S=R/'tools/vendor/gba/johto-owner-pond-20260922';A=R/'gba/art/johto-restart/evidence'
p=G/'data/layouts/CherrygroveCity/map.bin';before=(S/'data/layouts/CherrygroveCity/map.bin').read_bytes();assert p.read_bytes()==before,'Owner map changed again; preserve latest edits first.'
t=Tileset(G,'cherrygrove','cherrygrove');v=list(struct.unpack('<3840H',before));old=v.copy();blocks=list(t.blocks[1]);attrs=list(t.attrs[1]);lookup={(b,a):512+i for i,(b,a) in enumerate(zip(blocks,attrs))};changed=[]
for y in range(3,8):
 for src,dest in [(64,69),(65,68)]:
  value=old[y*80+src];mid=value&1023;ent=t.blocks[mid>=512][mid%512];at=t.attrs[mid>=512][mid%512]
  flipped=tuple(ent[layer*4+(q^1)]^0x400 for layer in range(2) for q in range(4));key=(flipped,at)
  if key not in lookup:lookup[key]=512+len(blocks);blocks.append(flipped);attrs.append(at)
  v[y*80+dest]=(value&~1023)|lookup[key];changed.append([dest,y])
assert len(blocks)<=512
D=G/'data/tilesets/secondary/cherrygrove';(D/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks));(D/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs));p.write_bytes(struct.pack('<3840H',*v))
installed=Tileset(G,'cherrygrove','cherrygrove');allowed={y*80+x for x,y in changed}
for i in range(len(v)):
 if i not in allowed:assert v[i]==old[i] and installed.render(v[i]&1023).tobytes()==t.render(old[i]&1023).tobytes()
im=installed.map_image(v,80);im.save(A/'port-overview.png');im.save(A/'town-overview.png');im.crop((62*16,2*16,72*16,10*16)).resize((640,512)).save(A/'pond-bank-fixed.png')
(A/'pond-fix.json').write_text(json.dumps(dict(owner_snapshot=str(S.relative_to(R)),changed_cells=changed,unchanged_cells=3830,all_other_pixels_preserved=True,map_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2)+'\n')
