"""Guarded first Route33 authoring. Original HGSS materials; accepted shared art.
Never replay over an existing native map. Editable native source is authoritative.
"""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset,palette
from claude_cherrygrove import ground
from claude_cherrygrove.pixel import Palette
G=Path(sys.argv[1]);S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';W,H=34,29
if (G/'data/maps/JohtoRoute33').exists():
 guard=json.loads((S/'authoring-guard.json').read_text());assert all(hashlib.sha256((G/p).read_bytes()).hexdigest()==h for p,h in guard.items()),'Preserve owner native edits'
 assert '--uncommitted-authoring' in sys.argv,'Native source is authoritative; no replay' 
if (G/'data/maps/JohtoRoute33').exists() and (S/'native-edit-lock.json').exists() and '--uncommitted-authoring' not in sys.argv:raise SystemExit('Final native map: edit directly, never replay.')
# Local copies of the established art, not dependencies on an editable workbench.
A=S/'shared-art';ref=np.array(Image.open(S/'hgss-reference.png').convert('RGB'));pad=np.zeros((H*16,W*16,3),np.uint8);pad[:]=[104,208,152];pad[:ref.shape[0],:ref.shape[1]]=ref
pals={i:np.array(palette(G/f'data/tilesets/{"primary" if i<6 else "secondary"}/cherrygrove/palettes/{i:02}.pal'),np.uint8) for i in range(16)}
pals[12]=np.array(palette(G/'data/tilesets/secondary/route32/palettes/12.pal'),np.uint8)
pals[9]=np.array([[0,0,0],[40,128,224]]+[[40,128,224]]*14,np.uint8)
# Accepted original Cherrygrove ground painter, copied native indexed terrain strips.
tex={k:np.array(Image.open(A/f'{k}.png').convert('RGB')) for k in ['grass','path']}
yy,xx=np.indices((H*16,W*16));bg=tex['grass'][yy%tex['grass'].shape[0],xx%tex['grass'].shape[1]].copy();fg=np.zeros((H*16,W*16,4),np.uint8);fh=np.zeros((H*16,W*16),np.uint8)
mat=np.full((H,W),'.','<U1');solid=np.zeros((H,W),bool);beh=np.zeros((H,W),np.uint16);above=np.zeros((H,W),bool)
# Pixel-registered original geography, independent material and traversal ledgers.
cliffpoly=[(0,0),(360,0),(360,40),(435,40),(435,187),(159,187),(159,40),(0,40)]
rightpoly=[(360,191),(504,191),(504,335),(411,335),(411,285),(385,285),(360,264)]
maskim=Image.new('1',(W*16,H*16));d=ImageDraw.Draw(maskim);d.polygon(cliffpoly,fill=1);d.polygon(rightpoly,fill=1);cm=np.array(maskim,bool)
# The mouth is open ground under a real rock overhang; no surrogate door panel.
cm[172:189,296:317]=False
bg[cm]=pad[cm]
bg[160:192,288:328]=pad[160:192,288:328]
# Path at the western Azalea approach, original width/rounded eastern end.
pathim=Image.new('1',(W*16,H*16));d=ImageDraw.Draw(pathim);d.rounded_rectangle((-20,280,241,309),radius=12,fill=1);pm=np.array(pathim,bool)
bg[pm]=tex['path'][yy[pm]%tex['path'].shape[0],xx[pm]%tex['path'].shape[1]]
# Native terrain rim: retain source profile where HGSS grass meets the dirt road.
for y in range(276,314):
 for x in range(0,247):
  if 0<=y<ref.shape[0] and x<ref.shape[1] and (abs(y-280)<4 or abs(y-309)<4 or x>236):bg[y,x]=ref[y,x]
# Each original cliff cell blocks on foot; the real mouth is the sole exception.
for y in range(H):
 for x in range(W):
  if cm[y*16:(y+1)*16,x*16:(x+1)*16].mean()>.35:mat[y,x]='R';solid[y,x]=True
  if pm[y*16:(y+1)*16,x*16:(x+1)*16].mean()>.35:mat[y,x]='P'
# Cave at (19,11), with original two-cell approach and unclipped arch.
mat[11,19]='C';solid[11,19]=False;beh[11,19]=97
# Matched native ground behind the mouth; no HGSS black fill below the threshold.
apron=Image.new('1',(W*16,H*16));ImageDraw.Draw(apron).polygon([(296,191),(320,191),(334,192),(315,203),(290,203),(291,193)],fill=1);ap=np.array(apron,bool);bg[ap]=tex['path'][yy[ap]%tex['path'].shape[0],xx[ap]%tex['path'].shape[1]];mat[12,18:21]='P'
# Eastern sea belongs to the source framing, not an accessible new water route.
water=xx>=512;bg[:,512:544]=ref[(yy[:,512:544]%32),512+(xx[:,512:544]%16)];solid[:,32:]=True;mat[:,32:]='W'
# Existing coherent HGSS-derived native tall-grass family; measured original block.
mat[19:22,:20]='G';beh[19:22,:20]=2
for y,x in zip(*np.where(mat=='G')):
 bits=''.join(str(int(0<=a<H and 0<=b<W and mat[a,b]=='G')) for a,b in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)])
 im=np.array(Image.open(A/f'grass-{bits}.png').convert('RGBA'));sl=bg[y*16:y*16+16,x*16:x*16+16];m=im[...,3]>0;sl[m]=im[m,:3]
# Full 32x48 accepted Cherrygrove trees. Roots never overlap; supported canopy rows every32px.
tree=np.array(Image.open(A/'tree.png').convert('RGBA'));positions=[];roots=np.zeros((H,W),np.uint8)
def put(im,x,y,hint=8):
 h,w=im.shape[:2];assert x>=0 and y>=0 and x+w<=W*16 and y+h<=H*16
 dst=fg[y:y+h,x:x+w];m=im[...,3]>0;dst[m]=im[m];fh[y:y+h,x:x+w][m]=hint
def trees(x,y):
 positions.append([x,y]);put(tree,x*16,y*16,3);assert not roots[y+1:y+3,x:x+2].any();roots[y+1:y+3,x:x+2]=1
 solid[y+1:y+3,x:x+2]=True;mat[y+1:y+3,x:x+2]='T';above[y,x:x+2]=True
# Source western woods taper before the road, leaving the boulder and lawn open.
for y in range(2,11,2):
 for x in range(0,10,2):trees(x,y)
for x in range(0,6,2):trees(x,12)
# Upper east forest fits the stepped rock silhouette; complete crowns at the map edge.
for x in [24,26,28,30]:trees(x,0)
for y in range(2,10,2):
 for x in [28,30]:trees(x,y)
# The southern woods form a closed barrier. First row overlaps only the original grass fringe.
for y in range(22,27,2):
 for x in range(0,32,2):trees(x,y)

# Full bottom canopies need one last row of solid roots: source canvas deliberately extends16px.
solid[-1,:]=True;mat[-1,:]='T'
# Original southwest and eastern boulders; clean polygon masks contain only stone.
for box,poly in [((54,226,86,258),[(14,1),(23,5),(30,25),(24,30),(4,29),(0,22),(6,9)]),((439,151,471,183),[(11,0),(24,4),(31,24),(24,31),(5,30),(0,22),(5,7)])]:
 x0,y0,x1,y1=box;im=np.dstack([ref[y0:y1,x0:x1],np.zeros((32,32),np.uint8)]);m=Image.new('L',(32,32));ImageDraw.Draw(m).polygon(poly,fill=255);im[...,3]=np.array(m);put(im,x0,y0);cx,cy=(x0+16)//16,(y0+22)//16;solid[cy,cx]=True;mat[cy,cx]='O';above[(y0)//16,cx]=True
# Two original apricorn silhouettes, art only; no invented harvest mechanics.
for x0 in [360,376]:
 im=np.dstack([ref[320:352,x0:x0+16],np.zeros((32,16),np.uint8)]);m=Image.new('L',(16,32));ImageDraw.Draw(m).polygon([(6,3),(12,5),(15,13),(13,20),(10,23),(10,28),(5,28),(4,22),(0,16),(1,10)],fill=255);im[...,3]=np.array(m);put(im,x0,320,10);solid[21,x0//16]=True;mat[21,x0//16]='A';above[20,x0//16]=True
# Native Emerald ledge placeholders: west-facing vertical arm, then south-facing return.
donor=Tileset(G)
for x,y,mid,behavior in [(13,y,0x85,57) for y in range(12,16)]+[(x,16,0xd5 if x==13 else 0xd6 if x==19 else 0x87,59) for x in range(13,20)]:
 im=np.array(Image.open(A/f'emerald-{hex(mid)}.png').convert('RGBA'));rgb=im[...,:3].astype(int);m=(rgb[...,1]>rgb[...,0]+15)&(rgb[...,1]>rgb[...,2]+15);im[m,3]=0
 if x==13 and y==16:
  arm=np.array(Image.open(A/'emerald-0x85.png').convert('RGBA'));mask=arm[:12,:,3]>0;im[:12][mask]=arm[:12][mask]
 put(im,x*16,y*16,2);mat[y,x]='L';solid[y,x]=True;beh[y,x]=behavior
# Reused shared sign; no dialogue/campaign content added.
im=np.array(Image.open(A/'sign.png').convert('RGBA'));put(im,17*16,12*16,5);solid[13,17]=True;mat[13,17]='S';above[12,17]=True
solid[0]=True;solid[:,0]=True;solid[:,33]=True;solid[18:19,0]=False
# Closed Azalea endpoint pending actual destination; retain visible road without invisible exit.
solid[17:20,0]=True
# Source upper forest and blind gaps behind the ridge are off-limits even under canopy air.
solid[:3,22:32]=True;solid[3:12,27:32]=True
# Background native palettes: shared ground bank0; original cliff bank6, mixed rims7.
bank=np.zeros((H*2,W*2),np.uint8)
for y in range(H*2):
 for x in range(W*2):
  sub=cm[y*8:y*8+8,x*8:x*8+8];bank[y,x]=6 if sub.all() else 7 if sub.any() else 0
bank[19*2:22*2,:40]=12
bank[:,64:]=9
# Source outline detail is prioritized; quantize original cliff as a single continuous ramp.
for b in [6,7,9]:
 sel=np.repeat(np.repeat(bank==b,8,0),8,1);pixels=bg[sel];q=Image.fromarray(pixels.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pals[b]=np.vstack(([0,0,0],np.array(q.getpalette()[:45]).reshape(15,3)&248)).astype(np.uint8)
# Foreground each 8px quadrant gets a coherent palette based on its actual art.
fbank=np.zeros_like(bank)
for y in range(H*2):
 for x in range(W*2):
  a=fg[y*8:y*8+8,x*8:x*8+8];m=a[...,3]>0
  if not m.any():continue
  hints=set(map(int,fh[y*8:y*8+8,x*8:x*8+8][m]));fbank[y,x]=hints.pop() if len(hints)==1 else 8
for b in [8,10]:
 pixels=fg[...,:3][np.repeat(np.repeat(fbank==b,8,0),8,1)&(fg[...,3]>0)];q=Image.fromarray(pixels.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pals[b]=np.vstack(([0,0,0],np.array(q.getpalette()[:45]).reshape(15,3)&248)).astype(np.uint8)
# Native glyph deduplication, including flips, with no image-similarity substitutions.
glyphs=[np.zeros((8,8),np.uint8)];lookup={glyphs[0].tobytes():0};blocks=[];attrs=[];ml={};grid=np.zeros((H,W),np.uint16)
def entry(rgb,b,m=None):
 p=pals[b].astype(np.int32);dist=((rgb.astype(np.int32)[...,None,:]-p)**2).sum(3);dist[...,0]=10**9;idx=dist.argmin(2).astype(np.uint8)
 if m is not None:idx[~m]=0
 k=idx.tobytes()
 if k not in lookup:
  tid=len(glyphs);glyphs.append(idx)
  for hf in range(2):
   for vf in range(2):lookup.setdefault(((idx[::-1] if vf else idx)[:,::-1] if hf else (idx[::-1] if vf else idx)).tobytes(),tid|(hf<<10)|(vf<<11))
 return lookup[k]|(b<<12)
for y in range(H):
 for x in range(W):
  ents=[]
  for layer in range(2):
   for q in range(4):
    xx=x*16+q%2*8;yy=y*16+q//2*8;bb=int((bank if layer==0 else fbank)[yy//8,xx//8]);a=(bg if layer==0 else fg)[yy:yy+8,xx:xx+8];ents.append(entry(a[...,:3],bb,None if layer==0 else a[...,3]>0))
  attr=int(beh[y,x])|(0 if above[y,x] else 0x1000);key=tuple(ents)+(attr,)
  if key not in ml:ml[key]=len(blocks);blocks.append(ents);attrs.append(attr)
  grid[y,x]=ml[key]|0x3000|(0xc00 if solid[y,x] else 0)
print('native glyphs/metatiles',len(glyphs),len(blocks));assert len(glyphs)<=1008 and len(blocks)<=1024
# Store both private native banks, keeping all shared tiles and IDs unchanged.
for secondary in [False,True]:
 folder=G/f'data/tilesets/{"secondary" if secondary else "primary"}/route33';(folder/'palettes').mkdir(parents=True,exist_ok=True)
 start=512 if secondary else 0;n=max(1,len(glyphs)-start) if secondary else 512;sheet=Image.new('P',(128,((n+15)//16)*8));sheet.putpalette([v for i in range(256) for v in (i*17%256,)*3])
 for i in range(n):
  if start+i<len(glyphs):sheet.paste(Image.fromarray(glyphs[start+i],mode='P'),(i%16*8,i//16*8))
 sheet.save(folder/'tiles.png',bits=4)
 for b in range(16):(folder/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
 bb=blocks[start:start+512];aa=attrs[start:start+512]
 if not bb:bb=[[0]*8];aa=[0]
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bb));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa))
folder=G/'data/layouts/JohtoRoute33';folder.mkdir(exist_ok=True);grid.tofile(folder/'map.bin');(grid[22:24,0:2]|0xc00).tofile(folder/'border.bin')
np.save(S/'material-grid.npy',mat);np.save(S/'solid.npy',solid);np.save(S/'behaviors.npy',beh);np.save(S/'tree-footprints.npy',roots);(S/'blocks.txt').write_text('\n'.join(''.join(r) for r in mat)+'\n')
Image.fromarray(bg).save(S/'background.png');Image.fromarray(fg).save(S/'foreground.png')
(E/'assembly.json').write_text(json.dumps({'size':[W,H],'original_size':[528,463],'registration':'source origin (0,0), 16px cells; eastern16px and southern1px complete boundary art','glyphs':len(glyphs),'metatiles':len(blocks),'trees':positions,'overlapping_root_footprints':0,'cliff_polygons':[cliffpoly,rightpoly],'pending':['Azalea exterior','apricorn harvest mechanics','weather review'],'method':'Exact native flip deduplication; no nearest-tile replacement'},indent=2)+'\n')
