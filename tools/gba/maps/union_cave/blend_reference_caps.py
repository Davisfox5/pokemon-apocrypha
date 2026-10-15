"""Keep original textured walls; align mixed-boundary ramps with their wall bank.
Native palette-bank edits only, no texture/geometry simplification or repacking.
Use the GBA secondary palette banks 6..9 to retain floor/water alongside original
bright/mid/dark cap shades. Guard current owned native files before editing.
"""
from pathlib import Path
import sys,json,hashlib,struct
from collections import defaultdict
import numpy as np
from PIL import Image
from config import FLOORS
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1])
def digest(p):
 b=p.read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if p.suffix=='.pal' else b).hexdigest()
for key,c in FLOORS.items():
 S=ROOT/f'gba/art/union-cave-{key}/source';manifest=json.loads((S/'generated-files.json').read_text());assert all((G/p).exists() and digest(G/p)==h for p,h in manifest.items()),('Preserve owner edits',key)
for key,c in FLOORS.items():
 S=ROOT/f'gba/art/union-cave-{key}/source';manifest=json.loads((S/'generated-files.json').read_text());W,H=c['size'];a=np.array(Image.open(S/'previous-de6922a/clean-terrain.png').convert('RGB'));lab=np.load(S/'previous-de6922a/hgss-pixel-materials.npy');g=np.fromfile(G/'data/layouts'/c['name']/'map.bin','<u2').reshape(H,W);pals=[]
 for n in range(3):pals.append(np.array([list(map(int,l.split())) for l in (G/'data/tilesets/primary'/c['set']/'palettes'/f'{n:02}.pal').read_text().splitlines()[3:19]],np.uint8))
 wall=pals[1];new={}
 for n,(light,dark) in enumerate([(1,2),(2,4),(4,6)],6):co=pals[0].copy();co[1]=wall[light];co[2]=wall[dark];new[n]=co
 co=pals[2].copy()
 for index in [1,2,3,4,6,8,10]:co[index]=wall[((wall.astype(int)-co[index].astype(int))**2).sum(1).argmin()]
 new[9]=co
 for typ in ['primary','secondary']:
  folder=G/'data/tilesets'/typ/c['set']/'palettes'
  for n,co in new.items():(folder/f'{n:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,r)) for r in co)+'\n')
 samples=defaultdict(list)
 for y in range(H):
  for x in range(W):
   m=int(g[y,x])&1023
   for q in range(4):
    yy=y*16+q//2*8;xx=x*16+q%2*8;l=lab[yy:yy+8,xx:xx+8];p=a[yy:yy+8,xx:xx+8];warm=(l=='R')&(p[...,0]>=p[...,1])&(p[...,1]>=p[...,2]);values=p[warm]
    if len(values)>=4:samples[m,q].extend(values.mean(1).tolist())
 count=defaultdict(int)
 for part,typ in enumerate(['primary','secondary']):
  p=G/'data/tilesets'/typ/c['set']/'metatiles.bin';blocks=[list(v) for v in struct.iter_unpack('<8H',p.read_bytes())]
  for index,block in enumerate(blocks):
   for q in range(4):
    bank=block[q]>>12;v=samples.get((part*512+index,q),[])
    if not v:continue
    if bank==0:shade=float(np.median(v));newbank=6 if shade>=122 else (7 if shade>=108 else 8)
    elif bank==2:newbank=9
    else:continue
    block[q]=(block[q]&0x0fff)|(newbank<<12);count[newbank]+=1
  p.write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks))
 (S/'cap-blend.json').write_text(json.dumps({'method':'retain original 14-shade wall bank and all indexed texture patterns; share its exact shades with mixed floor/water boundaries using additional native palette banks','palette_banks':list(new),'changed_metatile_quadrants':dict(count),'glyph_shape_or_collision_edits':False,'no_global_smoothing_or_flat_fill':True},indent=2)+'\n')
 (S/'generated-files.json').write_text(json.dumps({p:digest(G/p) for p in manifest},indent=2)+'\n');print(key,dict(count))
