"""Integrate approved gates and depth-sorted native trees on Route 36 only."""
from pathlib import Path
import sys,json,subprocess,tempfile,shutil,struct,tarfile,io,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from route36 import build as route,trace
from claude_cherrygrove import ground
from tiles import Tileset,palette
BASE='162c41c8b5987973480f7a276e63a196dfc1bf07'
OUT=ROOT/'gba/art/route36/gate-surround';SRC=OUT/'source';E=OUT/'evidence'
R=ROOT/'gba/art/route36/source';GATES=ROOT/'gba/art/johto-common-review/gates/refinement-4'
W,H=82,32
class Captured(Exception):pass

def dump(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n')
def over(dst,src,x=0,y=0):
 h,w=src.shape[:2];x0,y0=max(0,x),max(0,y);x1,y1=min(dst.shape[1],x+w),min(dst.shape[0],y+h)
 if x1<=x0 or y1<=y0:return
 s=src[y0-y:y1-y,x0-x:x1-x];p=dst[y0:y1,x0:x1];m=s[:,:,3]>0;p[m]=s[m]
def rgba(path):return np.array(Image.open(path).convert('RGBA'))
def decode(t,grid):
 result=[np.zeros((H*16,W*16,4),np.uint8) for _ in range(2)];attrs=np.zeros((H,W),np.uint16)
 for y in range(H):
  for x in range(W):
   mid=int(grid[y,x]&1023);entries=t.blocks[mid>=512][mid%512];attrs[y,x]=t.attrs[mid>=512][mid%512]
   for layer in range(2):
    for q in range(4):
     en=entries[layer*4+q];tid=en&1023;ids=np.array(t.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)
     if en&1024:ids=ids[:,::-1]
     if en&2048:ids=ids[::-1]
     p=result[layer][y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8];m=ids>0;p[m,:3]=np.array(t.pals[en>>12>=6][en>>12],np.uint8)[ids[m]];p[m,3]=255
 return result,attrs

def scenery(game):
 captured={};original_blit=route.native.MapCanvas.blit;original_pack=route.layers.pack;original_paint=ground.paint
 def blit(self,c,px,py,flip=False):
  if c.pal.bank not in (9,10):original_blit(self,c,px,py,flip)
 def capture(comp,packer,pals,grid,source_dir,**kwargs):
  mc=comp['canvas'];a,_=ground.paint(comp['cells'])
  for bank in np.unique(mc.bank):
   if bank<0:continue
   m=mc.bank==bank;a[m,:3]=np.array(pals[int(bank)].gba(),np.uint8)[mc.idx[m]]
  captured['rgba']=a;raise Captured()
 with tempfile.TemporaryDirectory(prefix='gate-scenery-') as tmp:
  s=Path(tmp)/'source';s.mkdir();e=Path(tmp)/'evidence';e.mkdir()
  for name in ('approved-front-gate.png','generated-files.json','hgss-reference.png'):shutil.copy2(R/name,s/name)
  route.S=s;route.E=e;route.OUT=Path(tmp);trace.S=s;trace.E=e
  route.native.MapCanvas.blit=blit;route.layers.pack=capture
  try:route.main(game)
  except Captured:pass
  finally:route.native.MapCanvas.blit=original_blit;route.layers.pack=original_pack;ground.paint=original_paint
 return captured['rgba']

def main(game,install=False):
 SRC.mkdir(parents=True,exist_ok=True);E.mkdir(exist_ok=True)
 # Reproducible baseline is a pinned source commit, never the previous preview.
 with tempfile.TemporaryDirectory(prefix='route36-baseline-') as tmp:
  archive=subprocess.check_output(['git','archive',BASE,'data/layouts/JohtoRoute36','data/tilesets/primary/johto_route36','data/tilesets/secondary/johto_route36'],cwd=game)
  with tarfile.open(fileobj=io.BytesIO(archive)) as tf:tf.extractall(tmp,filter='data')
  baseline=Path(tmp);grid=np.fromfile(baseline/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(H,W).copy();t=Tileset(baseline,'johto_route36','johto_route36');layers,attrs=decode(t,grid)
  original=np.array(t.map_image(grid.ravel().tolist(),W).convert('RGB'))
 background=scenery(game);tree=rgba(R/'materials/tree.png');features=json.loads((R/'features.json').read_text());gates=features['gates']
 rear=[[x,8] for x in (0,2,4,6)]+[[x,13] for x in (75,77,79)]
 back_add=np.zeros_like(background)
 for x,y in rear:over(back_add,tree,x*16,y*16)
 over(background,back_add)
 gate_layer=np.zeros_like(background);front_layer=np.zeros_like(background);affected=np.zeros((H,W),bool)
 front_trees=[]
 for gate in gates:
  x,y=gate['at'];im=Image.open(GATES/('G01a.png' if gate['name']=='Alph gate' else 'G02.png')).convert('RGBA')
  if gate['flip']:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  over(gate_layer,np.array(im),x*16,y*16);affected[y:y+im.height//16,x:x+7]=True
  for tx,ty in features['trees']:
   if ty>=y+5 and tx<x+7 and tx+2>x and ty<y+im.height//16:
    if [tx,ty] not in front_trees:front_trees.append([tx,ty])
 for x,y in rear:affected[y:y+3,x:x+2]=True
 for x,y in front_trees:over(front_layer,tree,x*16,y*16)
 target=background.copy();over(target,gate_layer);over(target,front_layer)
 # Compose two native layers per 8px quarter. Southern crowns are always the
 # upper layer; gates cover northern trees. Opaque foreground hides its backing.
 for cy,cx in np.argwhere(affected):
  for dy in (0,8):
   for dx in (0,8):
    y,x=cy*16+dy,cx*16+dx;sl=np.s_[y:y+8,x:x+8]
    front=front_layer[sl];gate=gate_layer[sl];bg=background[sl]
    if front[:,:,3].any():bottom=bg.copy();over(bottom,gate);top=front.copy()
    elif gate[:,:,3].any():bottom=bg.copy();top=gate.copy()
    else:bottom=bg.copy();top=np.zeros_like(bottom)
    bottom[top[:,:,3]>0]=0
    for part in (bottom,top):
     count=len(np.unique(part[part[:,:,3]>0,:3],axis=0));assert count<=15,('quarter palette',cx,cy,dx,dy,count)
    layers[0][sl]=bottom;layers[1][sl]=top
 # Seal the tree-lined backs and the true plinth/crown row, retaining stairs.
 solid=(grid&0xc00)!=0;oldsolid=solid.copy()
 for x,y in rear:solid[y+1:y+3,x:x+2]=True;attrs[y,x:x+2]&=0x0fff
 solid[9:15,0:7]=True;solid[15,0:6]=True
 solid[15:22,75:82]=True;solid[20,75]=False
 for x,y in front_trees:attrs[y,x:x+2]&=0x0fff
 # Artwork and collision remain separate; only the known gate threshold warps.
 assert attrs[20,75]&255==0x62
 final=layers[0].copy();over(final,layers[1]);assert np.array_equal(final[affected.repeat(16,0).repeat(16,1),:3],target[affected.repeat(16,0).repeat(16,1),:3])
 outside=~affected.repeat(16,0).repeat(16,1);assert np.array_equal(final[outside,:3],original[outside])
 Image.fromarray(final[:,:,:3]).save(E/'native-overview.png');Image.fromarray(original).save(E/'before.png')
 for name,a in [('gate-layer',gate_layer),('foreground-trees',front_layer),('rear-trees',back_add)]:Image.fromarray(a).save(SRC/(name+'.png'))
 # Store reusable, source-sized tree plates separately from the gate artwork.
 for name,box in [('west-tree-background',(0,128,128,176)),('east-tree-background',(1200,208,1312,256)),('west-tree-foreground',(0,240,112,288)),('east-tree-foreground',(1200,336,1312,384))]:Image.fromarray(back_add if 'background' in name else front_layer).crop(box).save(SRC/(name+'.png'))
 unique={};blocks=[];ids=np.zeros((H,W),np.uint16)
 for y in range(H):
  for x in range(W):
   parts=[a[y*16:(y+1)*16,x*16:(x+1)*16] for a in layers];key=(parts[0].tobytes(),parts[1].tobytes(),int(attrs[y,x]))
   if key not in unique:unique[key]=len(blocks);blocks.append((parts,int(attrs[y,x])))
   ids[y,x]=unique[key]
 assert len(blocks)<512,('metatile budget',len(blocks))
 src=SRC/'porytiles';src.mkdir(exist_ok=True);ah=(len(blocks)+7)//8*16
 for layer,name in [(0,'bottom'),(1,'middle')]:
  a=np.zeros((ah,128,4),np.uint8)
  for i,(parts,attr) in enumerate(blocks):a[i//8*16:i//8*16+16,i%8*16:i%8*16+16]=parts[layer]
  Image.fromarray(a).save(src/(name+'.png'))
 Image.new('RGBA',(128,ah)).save(src/'top.png')
 dest=SRC/'compiled'
 subprocess.run(['porytiles-legacy','compile-primary','-dual-layer','-tiles-primary-override=1008','-pals-primary-override=13','-best-branches=smart','-o',str(dest),str(src),str(game/'include/constants/metatile_behaviors.h')],check=True)
 # Preserve the legacy palettes' RGB888 spelling (some donors expand 5-bit
 # channels to 255, others to 248). Both encode to identical RGB555 values.
 colors=np.unique(final[:,:,:3].reshape(-1,3),axis=0);spellings={}
 for color in colors:
  key=tuple(color//8*8);value=tuple(map(int,color))
  assert key not in spellings or spellings[key]==value
  spellings[key]=value
 for p in (dest/'palettes').glob('*.pal'):
  lines=p.read_text().splitlines();lines[3:]=[' '.join(map(str,spellings.get(tuple(map(int,line.split())),tuple(map(int,line.split()))))) for line in lines[3:]]
  p.write_text('\n'.join(lines)+'\n')
 sheet=Image.open(dest/'tiles.png');tilecount=sheet.width//8*(sheet.height//8);assert tilecount<=1008
 compiled=list(struct.iter_unpack('<8H',(dest/'metatiles.bin').read_bytes()))[:len(blocks)]
 decoded=np.zeros_like(final)
 for y in range(H):
  for x in range(W):
   for layer in range(2):
    for q,en in enumerate(compiled[ids[y,x]][layer*4:layer*4+4]):
     tid=en&1023;ix=np.array(sheet.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)))
     if en&1024:ix=ix[:,::-1]
     if en&2048:ix=ix[::-1]
     p=decoded[y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8];m=ix>0;p[m,:3]=np.array(palette(dest/'palettes'/f'{en>>12:02}.pal'),np.uint8)[ix[m]];p[m,3]=255
 Image.fromarray(decoded[:,:,:3]).save(E/'decoded.png')
 delta=np.abs(decoded[:,:,:3].astype(int)-final[:,:,:3].astype(int))
 assert not delta.any(),('Native compiler pixel mismatch',int(np.any(delta,2).sum()),int(delta.max()),np.argwhere(np.any(delta,2))[:10].tolist())
 report={'base_engine_commit':BASE,'preview_only':not install,'native_pixel_errors':0,'outside_gate_areas_pixel_changes':0,'approved_gate_source_unchanged':True,'rear_trees_added':rear,'foreground_trees':front_trees,'changed_collision_cells_xy':np.argwhere(solid!=oldsolid)[:,::-1].tolist(),'metatiles':len(blocks),'tile_slots':tilecount,'palette_banks':sorted({en>>12 for b in compiled for en in b if en&1023}),'runtime_tested':False}
 dump(E/'structure.json',report);np.save(SRC/'solid.npy',solid);np.save(SRC/'attributes.npy',attrs);np.save(SRC/'affected.npy',affected)
 if install:
  for part in ('primary','secondary'):
   folder=game/'data/tilesets'/part/'johto_route36'
   start,end=(0,512) if part=='primary' else (512,tilecount)
   chunk=sheet.crop((0,start//16*8,128,max(start//16*8+8,(end+15)//16*8))) if end>start else Image.new('P',(128,8))
   chunk.putpalette(sheet.getpalette());chunk.save(folder/'tiles.png',bits=4)
   for bank in range(13):
    file=folder/'palettes'/f'{bank:02}.pal'
    if (part=='primary' and bank<6) or (part=='secondary' and bank>=6):shutil.copy2(dest/'palettes'/f'{bank:02}.pal',file)
    else:file.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(file.relative_to(game))],cwd=game))
   bs=compiled if part=='primary' else [(0,)*8];ats=[b[1] for b in blocks] if part=='primary' else [0]
   (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bs));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(ats),*ats))
  newgrid=ids|(grid&0xf000)|np.where(solid,0xc00,0).astype(np.uint16)
  (game/'data/layouts/JohtoRoute36/map.bin').write_bytes(newgrid.astype('<u2').tobytes());(game/'data/layouts/JohtoRoute36/border.bin').write_bytes(newgrid[6:8,60:62].astype('<u2').tobytes())
  check=np.array(Tileset(game,'johto_route36','johto_route36').map_image(newgrid.ravel().tolist(),W));assert np.array_equal(check,final[:,:,:3])
  # Maintain the established authored-state guard so ordinary generators refuse
  # to overwrite this handoff unless deliberately extended for these layers.
  manifest=json.loads((R/'generated-files.json').read_text())
  for path in manifest:manifest[path]=route.digest(game/path)
  dump(R/'generated-files.json',manifest)
 print(json.dumps(report))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),'--install' in sys.argv)
