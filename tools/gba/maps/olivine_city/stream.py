"""Read actual Porymap source into a Olivine-only viewport atlas.
Safe after ordinary native map edits: this never writes a layout or tileset.
"""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);E=R/'gba/art/olivine-city/evidence';sections=json.loads((E/'sections.json').read_text());W,H=65,54;atlas=[bytes(32)];lookup={bytes(32):0};entries=np.zeros((H,W,8),'<u4');layers=np.zeros((H,W),np.uint8)
for s in sections:
 n=s['name'];t=Tileset(G,n.lower(),n.lower());
 if s is sections[0]:global_palettes=t.pals
 else:assert t.pals==global_palettes,'Olivine uses one coherent global palette; propagate intentional bank edits across its sections.'
 x,y,x1,y1=s['box'];g=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x)
 for cy,cx in np.ndindex(g.shape):
  mid=int(g[cy,cx]&1023);es=t.blocks[mid>=512][mid%512];layers[y+cy,x+cx]=t.attrs[mid>=512][mid%512]>>12&3
  for i,e in enumerate(es):
   tid=e&1023;pixels=np.array(t.tiles[tid>=512][tid%512],np.uint8).reshape(-1)
   # An entirely opaque foreground quadrant hides every background pixel.
   # Omit its unused background glyph from the runtime cache, while keeping
   # ordinary native/Porymap source unchanged.
   if i<4:
    top=es[i+4]&1023
    if np.all(np.array(t.tiles[top>=512][top%512],np.uint8)>0):pixels=np.zeros(64,np.uint8)
   raw=bytes(pixels[::2]|pixels[1::2]<<4)
   if raw not in lookup:
    tile_id=len(atlas);atlas.append(raw);square=pixels.reshape(8,8)
    for h in range(2):
     for v in range(2):
      variant=square[::-1 if v else 1,::-1 if h else 1].reshape(-1);key=bytes(variant[::2]|variant[1::2]<<4)
      lookup.setdefault(key,tile_id|h<<16|v<<17)
   # Compose source flips with the canonical atlas orientation. This shares
   # mirrored glyphs across private section banks without changing any pixel.
   entries[y+cy,x+cx,i]=lookup[raw]^((e&0xfc00)<<6)
# Prove orientation sharing preserves every decoded source quadrant, including
# mirrored variants introduced by different private section banks.
for section in sections:
 n=section['name'];ts=Tileset(G,n.lower(),n.lower());x0,y0,x1,y1=section['box'];grid=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y0,x1-x0)
 for cy,cx in np.ndindex(grid.shape):
  mid=int(grid[cy,cx]&1023)
  for i,e in enumerate(ts.blocks[mid>=512][mid%512]):
   tid=e&1023;source=np.array(ts.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)[::-1 if e&2048 else 1,::-1 if e&1024 else 1]
   if i<4:
    top=ts.blocks[mid>=512][mid%512][i+4]&1023
    if np.all(np.array(ts.tiles[top>=512][top%512],np.uint8)>0):source=np.zeros((8,8),np.uint8)
   ae=int(entries[y0+cy,x0+cx,i]);packed=np.frombuffer(atlas[ae&65535],np.uint8);decoded=np.empty(64,np.uint8);decoded[::2]=packed&15;decoded[1::2]=packed>>4;decoded=decoded.reshape(8,8)[::-1 if ae&(1<<17) else 1,::-1 if ae&(1<<16) else 1]
   assert np.array_equal(source,decoded),(n,cx,cy,i)
   assert e>>12==ae>>18
P=G/'data/olivine';P.mkdir(exist_ok=True);(P/'glyphs.4bpp').write_bytes(b''.join(atlas));entries.tofile(P/'entries.bin');layers.tofile(P/'layers.bin')
assert len(atlas)<65536
def border_cell(x,y):
 # Native whole-tree core across the north/west forest. Open ocean east/south.
 if x<0:
  if y<28:return x%2,y%2+2
  if y<34:return 0,31
  return 2+x%2,42+y%2
 if y<0:return 2+x%2,2+y%2
 if x>=65 or y>=54:return 2+x%2,42+y%2
 return x,y
# Actual16x16ring windows include directional native camera borders. They use
# complete existing texture/tree cores, never black or static-tileset aliases.
padded=np.zeros((H+30,W+30,8),np.uint32)
for py,px in np.ndindex(padded.shape[:2]):
 x,y=border_cell(px-15,py-15);padded[py,px]=entries[y,x]
peak=0;peakxy=None
for y in range(-15,H):
 for x in range(-15,W):
  n=len(np.unique(padded[y+15:y+31,x+15:x+31]&65535))
  if n>peak:peak=n;peakxy=[x,y]
assert peak<1008,(peak,peakxy)
text='// Generated FROM native Porymap files by olivine_city/stream.py.\n#define OLIVINE_GLYPH_COUNT '+str(len(atlas))+'\n'
text+='static const u32 sOlivineGlyphs[] = INCBIN_U32("data/olivine/glyphs.4bpp");\nstatic const u32 sOlivineEntries[54 * 65 * 8] = INCBIN_U32("data/olivine/entries.bin");\nstatic const u8 sOlivineLayers[54 * 65] = INCBIN_U8("data/olivine/layers.bin");\n'
text+='static const struct OlivineSection sOlivineSections[] = {\n'+''.join('    { MAP_GROUP(MAP_'+s['name'].upper()+'), MAP_NUM(MAP_'+s['name'].upper()+'), '+str(s['box'][0])+', '+str(s['box'][1])+' },\n' for s in sections)+'};\n';(G/'src/data/olivine.h').write_text(text)
report=dict(glyphs=len(atlas),ROM_art_bytes=len(atlas)*32+entries.nbytes+layers.nbytes,maximum_16x16_ring_glyphs=peak,peak_origin=peakxy,VRAM_slots=1008,volatile_cache_bytes=(len(atlas)+1008*2+256*8)*2+2,source='Actual native tiles, palettes, metatiles and map entries; no authoring screenshot dependency.')
(E/'stream-capacity.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

# A production build must reject an atlas left stale by subsequent native edits.
# This manifest is derived from native inputs and generated outputs, not an
# authority that can overwrite a Porymap layout.
paths=[]
for section in sections:
 n=section['name']
 paths+=list((G/'data/layouts'/n).glob('*.bin'))+[G/f'data/maps/{n}/map.json']
 paths += [p for p in G.glob('data/tilesets/*/'+n.lower()+'/**/*') if p.is_file() and p.suffix in ['.bin','.pal','.png']]
paths += [P/'glyphs.4bpp',P/'entries.bin',P/'layers.bin',G/'src/data/olivine.h']
import hashlib
(P/'source-hashes.json').write_text(json.dumps({str(p.relative_to(G)):hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n') if p.suffix=='.pal' else p.read_bytes()).hexdigest() for p in sorted(paths)},indent=2)+'\n')
