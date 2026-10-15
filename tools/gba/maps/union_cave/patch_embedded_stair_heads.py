"""Restore full HGSS embedded stair heads/treads with a local native palette.
Keep the original surrounding wall texture; repair the complete 24x16 stair/cap
join instead of forcing its highlights through a floor-only palette. Guarded
owned-source edit, with no extra floor marker or layout/warp changes.
"""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
from config import FLOORS
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1])
heads={'1f':[(4,5,'west'),(8,57,'east')],'b1f':[(32,35,'east'),(3,48,'west'),(30,46,'east'),(3,5,'west'),(3,12,'west')],'b2f':[(3,5,'west')]}
def digest(p):
 b=p.read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if p.suffix=='.pal' else b).hexdigest()
for key,c in FLOORS.items():
 S=ROOT/f'gba/art/union-cave-{key}/source';m=json.loads((S/'stair-head-input-fingerprints.json').read_text());assert all((G/p).exists() and digest(G/p)==h for p,h in m.items()),('Preserve owner edits',key)
for key,c in FLOORS.items():
 S=ROOT/f'gba/art/union-cave-{key}/source';W,H=c['size'];source=np.array(Image.open(S/'previous-de6922a/clean-terrain.png').convert('RGB'));g=np.fromfile(G/'data/layouts'/c['name']/'map.bin','<u2').reshape(H,W).copy();blocks=[];attrs=[];tiles=[];sheets=[]
 for typ in ['primary','secondary']:
  d=G/'data/tilesets'/typ/c['set'];im=Image.open(d/'tiles.png');sheets.append(im);tiles.extend(np.array(im.crop((x,y,x+8,y+8)),np.uint8) for y in range(0,256,8) for x in range(0,128,8));blocks.extend(list(v) for v in struct.iter_unpack('<8H',(d/'metatiles.bin').read_bytes()));attrs.extend(struct.unpack('<512H',(d/'metatile_attributes.bin').read_bytes()))
 patches=[];rgb=[]
 for x,y,side in heads[key]:
  x0=x*16-8 if side=='west' else x*16;y0=y*16-8;patch=source[y0:y0+16,x0:x0+24].copy();patches.append((x0,y0,patch));rgb.append(patch.reshape(-1,3))
 pixels=np.concatenate(rgb);q=Image.fromarray(pixels.reshape(-1,1,3)).quantize(colors=14,method=Image.Quantize.MEDIANCUT);co=np.array(q.getpalette()[:42],int).reshape(14,3)&248;co=np.vstack(([0,0,0],co,[0,0,0])).astype(np.uint8)
 used=set(map(int,(g&1023).ravel()));positions={};records=[]
 for x0,y0,patch in patches:
  for yy in range(0,16,8):
   for xx in range(0,24,8):
    x=(x0+xx)//16;y=(y0+yy)//16;m=int(g[y,x])&1023
    if int(((g&1023)==m).sum())>1:
     new=next(i for i in range(1024) if i not in used);used.add(new);blocks[new]=blocks[m].copy();attrs[new]=attrs[m];g[y,x]=(int(g[y,x])&~1023)|new;m=new
    n=((y0+yy)%16//8)*2+(x0+xx)%16//8;piece=patch[yy:yy+8,xx:xx+8];loss=((piece.astype(np.int32)[...,None,:]-co.astype(np.int32)[None,None,:,:])**2).sum(3);loss[...,0]=10**9;positions[m,n]=loss.argmin(2).astype(np.uint8)
  records.append([x0,y0,x0+24,y0+16])
 # Free the replaced head glyphs first, so this local edit stays within static VRAM.
 for m,n in positions:blocks[m][n]=0
 def glyph(p):
  ids={en&1023 for m in set(map(int,(g&1023).ravel())) for en in blocks[m]}
  for tid in sorted(ids):
   for k,a in enumerate([tiles[tid],tiles[tid][:,::-1],tiles[tid][::-1],tiles[tid][::-1,::-1]]):
    if np.array_equal(a,p):return tid|[0,1024,2048,3072][k]
  tid=next((i for i in range(1,1008) if i not in ids),None);assert tid is not None,('Stair head budget',key,len(ids));tiles[tid]=p.copy();return tid
 for (m,n),p in positions.items():blocks[m][n]=glyph(p)|(10<<12)
 for part,typ in enumerate(['primary','secondary']):
  d=G/'data/tilesets'/typ/c['set'];im=Image.new('P',(128,256));im.putpalette(sheets[part].getpalette())
  for i,p in enumerate(tiles[part*512:(part+1)*512]):im.paste(Image.fromarray(p,'P'),(i%16*8,i//16*8))
  im.save(d/'tiles.png');(d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks[part*512:(part+1)*512]));(d/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*attrs[part*512:(part+1)*512]));(d/'palettes/10.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,row)) for row in co)+'\n')
 g.astype('<u2').tofile(G/'data/layouts'/c['name']/'map.bin');np.save(S/'native-metatile-grid.npy',g)
 report={'reference':'unobscured original HGSS terrain, preserved de6922a clean source','full_head_pixel_boxes':records,'palette_bank':10,'reason':'retain real upper treads and complete wall/cap join with sufficient native shades; no floor marker tile','map_collision_or_warp_changes':False};(S/'stair-head-finish.json').write_text(json.dumps(report,indent=2)+'\n')
 p=S/'reference-finish.json';j=json.loads(p.read_text());j['local_edits'].extend({'embedded_head_join':True,'reference_pixel_box':box} for box in records);p.write_text(json.dumps(j,indent=2)+'\n')
 manifest=json.loads((S/'generated-files.json').read_text());(S/'generated-files.json').write_text(json.dumps({p:digest(G/p) for p in manifest},indent=2)+'\n');print(key,'stair head glyphs',len(positions))
