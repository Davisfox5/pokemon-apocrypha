"""Guarded direct native fix: southern arch occlusion and its physical pillars.
Only baseline200ffd16; preserve every unrelated native tile, ID and source map.
"""
from pathlib import Path
import sys,json,struct,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/goldenrod-city/source';E=S.parent/'evidence'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='200ffd16fe13379600fcc8cb939d3e7de7ddf835','Use the preserved arch baseline; never replay over later native edits.'
subprocess.run(['python3',str(G/'tools/goldenrod/check.py')],check=True)
name='GoldenrodCity10';dirs=[G/f'data/tilesets/{side}/{name.lower()}' for side in ['primary','secondary']];p=G/f'data/layouts/{name}/map.bin';grid=np.fromfile(p,'<u2').reshape(14,21);old=grid.copy();tiles=[];blocks=[];attrs=[];pal=[]
for d in dirs:
 im=np.array(Image.open(d/'tiles.png'));tiles.append([im[y:y+8,x:x+8] for y in range(0,im.shape[0],8) for x in range(0,im.shape[1],8)]);blocks.append(list(struct.iter_unpack('<8H',(d/'metatiles.bin').read_bytes())));attrs.append(list(struct.unpack('<'+'H'*((d/'metatile_attributes.bin').stat().st_size//2),(d/'metatile_attributes.bin').read_bytes())))
 for i in range(16):pal.append([tuple(map(int,l.split())) for l in (d/'palettes'/f'{i:02}.pal').read_text().splitlines()[3:19]])
# Complete measured stone cap. The road in the opening remains transparent.
m=Image.new('L',(1344,896));ImageDraw.Draw(m).polygon([(890,784),(898,776),(919,768),(949,768),(970,776),(979,784),(979,802),(970,794),(948,785),(921,785),(901,794),(890,802)],fill=255);mask=np.array(m)>0
lookup={a.tobytes():i for i,a in enumerate(tiles[1])};nextid=512+len(tiles[1]);changes=[];fg=np.array(Image.open(S/'shared-foreground.png'))
def glyph(a,bank):
 global nextid
 k=a.tobytes()
 if k not in lookup:lookup[k]=nextid-512;tiles[1].append(a);nextid+=1
 return 512+lookup[k]|bank<<12
for wy in range(48,51):
 for wx in range(55,62):
  sl=np.s_[wy*16:wy*16+16,wx*16:wx*16+16];cm=mask[sl]
  if not cm.any():continue
  y,x=wy-42,wx-42;mid=int(grid[y,x]&1023);es=list(blocks[mid>=512][mid%512]);attr=attrs[mid>=512][mid%512];assert all((e&1023)==0 for e in es[4:])
  for q in range(4):
   my,mx=q//2*8,q%2*8;qm=cm[my:my+8,mx:mx+8]
   if not qm.any():continue
   e=es[q];a=tiles[(e&1023)>=512][(e&1023)%512];a=a[::-1] if e&2048 else a;a=a[:,::-1] if e&1024 else a;cap=a.copy();cap[~qm]=0;es[q+4]=glyph(cap,e>>12)
   target=fg[wy*16+my:wy*16+my+8,wx*16+mx:wx*16+mx+8]
   for i,c in enumerate(pal[e>>12]):target[qm&(cap==i)]=[*c,255]
  newmid=len(blocks[0]);assert newmid<512;blocks[0].append(tuple(es));attrs[0].append(attr&~0xf000);grid[y,x]=newmid|(int(grid[y,x])&~1023);changes.append([wx,wy])
solid=np.load(S/'solid.npy');above=np.load(S/'above.npy');mat=np.load(S/'material.npy')
for x,y in changes:above[y,x]=True;mat[y,x]='stone arch cap'
for wx in [55,61]:
 for wy in range(49,52):grid[wy-42,wx-42]|=0xc00;solid[wy,wx]=True;mat[wy,wx]='arch pillar'
assert nextid<=1008
for i,d in enumerate(dirs):
 if i==1:
  sheet=Image.new('P',(128,((len(tiles[i])+15)//16)*8));sheet.putpalette([v for j in range(256) for v in (j*17%256,)*3])
  for j,a in enumerate(tiles[i]):sheet.paste(Image.fromarray(a,mode='P'),(j%16*8,j//16*8))
  sheet.save(d/'tiles.png',bits=4)
 (d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks[i]));(d/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs[i]),*attrs[i]))
grid.tofile(p);np.save(S/'solid.npy',solid);np.save(S/'above.npy',above);np.save(S/'material.npy',mat);Image.fromarray(fg).save(S/'shared-foreground.png');m.save(S/'arch-cap-mask.png')
(E/'arch-native-fix.json').write_text(json.dumps({'baseline':'200ffd16fe13379600fcc8cb939d3e7de7ddf835','upper_layer_cells':changes,'pillar_cells':[[x,y] for x in [55,61] for y in range(49,52)],'unchanged_static_RGB':'Cap duplicates the existing native lower-layer pixels; only sprite occlusion changes.','native_glyphs':nextid,'metatiles':len(blocks[0]),'scope':'Southern arch only. Other map IDs/metatile IDs and prior map sources preserved.'},indent=2)+'\n');print(changes,nextid)
