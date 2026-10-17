"""Local native Route33 edit using pinned shared masters, never screenshot tracing.
Preview first; --install reuses only storage unreferenced by retained map/border IDs.
"""
from pathlib import Path
import sys,json,struct,hashlib,argparse
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';M=S/'shared-masters';OUT=S/'shared-asset-repair';OUT.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('engine',type=Path);p.add_argument('--install',action='store_true');args=p.parse_args();G=args.engine
lock=json.loads((S/'previous-214e38cf/native-edit-lock.json').read_text())['files']
for f,h in lock.items():
 if Path(f).name in ['events.inc','connections.inc','header.inc']:continue
 data=(G/f).read_bytes();assert h in [hashlib.sha256(data).hexdigest(),hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()],('Changed native source; stop',f)
prov=json.loads((M/'provenance.json').read_text())
for r in prov['files']:assert hashlib.sha256((M/r['file']).read_bytes()).hexdigest()==r['sha256']
t=Tileset(G,'route33','route33');grid=np.fromfile(G/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);original_grid=grid.copy()
blocks=[list(b) for b in t.blocks[0]];attrs=list(t.attrs[0]);oldattrs=attrs.copy();glyphs=[np.array(a,np.uint8).reshape(8,8) for a in t.tiles[0]+t.tiles[1]];pals={i:np.array(t.pals[int(i>=6)][i],np.uint8) for i in range(16)}
bg=np.zeros((464,544,4),np.uint8);fg=bg.copy();banks=np.zeros((2,58,68),np.uint8);entries=np.zeros((29,34,8),np.uint16)
for y in range(29):
 for x in range(34):
  es=blocks[int(grid[y,x]&1023)];entries[y,x]=es
  for l in range(2):
   for q in range(4):
    v=es[l*4+q];a=glyphs[v&1023]
    if v&1024:a=a[:,::-1]
    if v&2048:a=a[::-1]
    yy=y*16+q//2*8;xx=x*16+q%2*8;dst=(bg if l==0 else fg)[yy:yy+8,xx:xx+8];mask=a>0;dst[mask,:3]=pals[v>>12][a[mask]];dst[mask,3]=255;banks[l,yy//8,xx//8]=v>>12
oldbg=bg.copy();oldfg=fg.copy();usedbanks=set(int(v)>>12 for v in entries.ravel() if v);assert 4 not in usedbanks
load=lambda n:np.array(Image.open(M/(n+'.png')).convert('RGBA'))
front=load('front');west=load('face-west');east=load('face-east');sw=load('corner-east');se=load('corner-west')
placements=[];work=np.zeros((464,544),bool)
def over(dst,a,x,y):
 h,w=a.shape[:2];d=dst[y:y+h,x:x+w];m=a[...,3]>0;d[m]=a[m]
def record(name,a,x,y,role,backing=None,layer=0):
 h,w=a.shape[:2];sl=np.s_[y:y+h,x:x+w]
 if backing is not None:(bg if layer==0 else fg)[sl]=backing
 over(bg if layer==0 else fg,a,x,y);work[sl]=True
 placements.append(dict(master=name,x=x,y=y,width=w,height=h,role=role,layer=layer))
# Independent existing native terrain, aligned by destination phase. No new crops.
lawn=oldbg[224:240,320:336].copy();top=oldbg[144:160,176:192].copy()
def terrain(tile,x,y,w,h):
 return np.array([[tile[(yy+y)%16,(xx+x)%16] for xx in range(w)] for yy in range(h)],np.uint8)
# A: the front face must end at the forest boundary. Fill the narrow raised top
# above it, then use ONE complete shared front course, not a face plus a fake skirt.
bg[24:32,:160]=terrain(top,0,24,160,8);work[24:32,:160]=True
for x in range(0,160,32):record('front',front,x,32,'A / south-facing wall behind full crowns',terrain(lawn,x,32,32,16))
# B is a plateau cap, NOT an exposed wall face. Continue the immediately adjacent
# native top/shoulder quadrants. A reflected front would invent a dark beam here.
bg[40:48,216:432]=oldbg[48:56,216:432];work[40:48,216:432]=True
placements.append(dict(master='existing native adjacent cap quadrants',x=216,y=40,width=216,height=8,role='B / rock-top cap, no exposed rear face',layer=0,donor=[216,48,432,56]))
# E/F/G form ONE receiving wall. Complete the existing plateau under the former
# low face, then run shared side/front/corner modules around that same footprint.
bg[320:344,424:488]=terrain(top,424,320,64,24);work[320:344,424:488]=True
# The southeast rear is also a top cap. Keep the four-pixel separating lawn below
# the northern mountain; copy receiving top/shoulder quadrants rather than a face.
bg[192:200,360:504]=oldbg[200:208,360:504];work[192:200,360:504]=True
placements.append(dict(master='existing native adjacent cap quadrants',x=360,y=192,width=144,height=8,role='E / separate rock-top cap',layer=0,donor=[360,200,504,208]))
# The cap's exposed ends are side shoulders, using the same upper quadrants and
# shared convex tip mask as their continuation. No old-color eight-pixel collars.
for name,master,x,tip in [('face-west',west,360,'NW'),('face-east',east,488,'NE')]:
 a=master[:8].copy();a[np.array(Image.open(M/('tip-mask-'+tip+'.png')))[:8]>0]=0
 record(name+' upper quadrants + shared '+tip+' tip',a,x,192,'E / cap-to-side shoulder',terrain(lawn,x,192,16,8))
# A full wall side has direction, unlike a thin rear rim. Phase repeats from master.
for y in range(200,272,16):
 h=min(16,272-y);record('face-west',np.concatenate([west,west])[(y-192)%32:(y-192)%32+h],360,y,'F / west-facing side',terrain(lawn,360,y,16,h))
for y in range(200,344,16):record('face-east',np.concatenate([east,east])[(y-192)%32:(y-192)%32+16],488,y,'E–G / east-facing side',terrain(lawn,488,y,16,16))
rounded_sw=sw.copy();rounded_sw[np.array(Image.open(M/'tip-mask-SW.png'))>0]=0
rounded_se=se.copy();rounded_se[np.array(Image.open(M/'tip-mask-SE.png'))>0]=0
record('corner-east + shared SW tip mask',rounded_sw,360,272,'F / convex southwest return',terrain(lawn,360,272,16,16))
for x in [376,392]:record('front',front[:,(x-376)%32:(x-376)%32+16],x,272,'F / south-facing short return',terrain(lawn,x,272,16,16))
# Concave turn retains the existing receiving geometry. The continuation below it
# uses the same west-facing source; no convex corner is inserted into this notch.
for y in range(272,344,16):
 h=min(16,344-y);record('face-west',west[(y-272)%32:(y-272)%32+h],408,y,'F–G / west-facing lower side',terrain(lawn,408,y,16,h))
record('corner-east + shared SW tip mask',rounded_sw,408,344,'G / southwest footing corner',terrain(lawn,408,344,16,16))
for x in range(424,488,16):record('front',front[:,(x-424)%32:(x-424)%32+16],x,344,'G / final south-facing footing',terrain(lawn,x,344,16,16))
record('corner-west + shared SE tip mask',rounded_se,488,344,'G / southeast footing corner',terrain(lawn,488,344,16,16))
# C/D: whole transparent ledge masters. Rotation sets the raised side to the east.
# Do not redraw cap pixels or improvise a new corner out of a cliff block.
fg[184:272,208:328]=0;work[184:272,208:328]=True
for i,y in enumerate(range(184,248,16)):
 a=np.rot90(load('L11' if i==0 else 'L12'),-1).copy();record(('L11' if i==0 else 'L12')+' / clockwise',a,216,y,'C–D / west-jump ledge',layer=1)
record('L12 / clockwise',np.rot90(load('L12'),-1).copy(),216,240,'D / upright enters horizontal ledge',layer=1)
for x in range(216,328,16):record('L11' if x==216 else 'L13' if x==312 else 'L12',load('L11' if x==216 else 'L13' if x==312 else 'L12'),x,248,'D / south-jump ledge',layer=1)
# Shared source stone + unchanged destination lawn fit exactly in one spare bank.
stone=sorted(set(tuple(map(int,c)) for a in [front,west,east,sw,se] for c in a[a[...,3]>0,:3]));green=sorted(set(tuple(map(int,c)) for c in lawn[...,:3].reshape(-1,3)));assert len(stone)+len(green)<=15
pals[4]=np.array([[0,0,0]]+stone+green+[[0,0,0]]*(15-len(stone)-len(green)),np.uint8)
# Add ledge shades only to proven unused indices in the current ledge bank.
ledge=sorted(set(tuple(map(int,c)) for n in ['L11','L12','L13'] for c in load(n)[load(n)[...,3]>0,:3]))
live_indices=set()
for mid in set(map(int,original_grid.ravel()&1023))|set(map(int,np.fromfile(G/'data/layouts/JohtoRoute33/border.bin','<u2')&1023)):
 for e in blocks[mid]:
  if e>>12==2:live_indices.update(map(int,glyphs[e&1023].ravel()))
spare=[i for i in range(1,16) if i not in live_indices]
for c in ledge:
 if c not in set(map(tuple,pals[2][1:])):pals[2][spare.pop(0)]=c
# Select exact compatible banks per 8px quadrant; never approximate a master pixel.
for l,(old,now) in enumerate([(oldbg,bg),(oldfg,fg)]):
 for gy,gx in np.argwhere(np.any((now!=old).reshape(58,8,68,8,4),(1,3,4))):
  a=now[gy*8:gy*8+8,gx*8:gx*8+8];cols=set(map(tuple,a[a[...,3]>0,:3]));preferred=int(banks[l,gy,gx]);candidates=[preferred,4,2]+list(range(13));valid=[b for b in candidates if cols<=set(map(tuple,pals[b][1:]))]
  assert valid,('No exact palette',l,int(gx),int(gy),cols)
  banks[l,gy,gx]=valid[0]
# G is an actual rock footing, so block its six newly occupied route cells.
grid[21:23,26:32]|=0xc00
changed=np.any(bg!=oldbg,2)|np.any(fg!=oldfg,2);cells=changed.reshape(29,16,34,16).any((1,3))
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(OUT/(n+'.png'))
preview=bg.copy();over(preview,fg,0,0);Image.fromarray(preview).save(OUT/'preview.png');t.map_image(original_grid.ravel().tolist(),34).save(OUT/'before.png')
report=dict(baseline='214e38cfb94309965e0cc58d09460e58737e00a6',rejected='89f8899335cd5182e534d8a5c4f9e5e21bb57615',shared_source=prov['commit'],placements=placements,changed_cells=int(cells.sum()),collision_changes=np.argwhere(((original_grid^grid)&0xc00)!=0).tolist(),outside_scope_pixels=int(np.count_nonzero(changed&~work)),palette_approximation_pixels=0,new_master_art=False,installed=args.install)
assert not report['outside_scope_pixels']
if args.install:
 # Only original cell entries not edited and the native border retain glyph IDs.
 used={0}
 for y,x in np.argwhere(~cells):used.update(int(v)&1023 for v in entries[y,x])
 border=np.fromfile(G/'data/layouts/JohtoRoute33/border.bin','<u2')
 for mid in border&1023:used.update(int(v)&1023 for v in blocks[int(mid)])
 free=[i for i in range(1,1008) if i not in used];lookup={};allocated=[]
 def addkeys(a,tid):
  for h in range(2):
   for v in range(2):lookup.setdefault(((a[::-1] if v else a)[:,::-1] if h else (a[::-1] if v else a)).tobytes(),tid|(h<<10)|(v<<11))
 for tid in used:addkeys(glyphs[tid],tid)
 def ent(a,b,opaque):
  idx=np.zeros((8,8),np.uint8)
  for k,c in enumerate(pals[b][1:],1):idx[np.all(a[...,:3]==c,2)&(a[...,3]>0)]=k
  assert np.all(idx[a[...,3]>0]>0)
  if not idx.any():return 0
  key=idx.tobytes()
  if key not in lookup:
   assert free,'No unreferenced native glyphs remain';tid=free.pop(0);allocated.append(tid)
   while tid>=len(glyphs):glyphs.append(np.zeros((8,8),np.uint8))
   glyphs[tid]=idx;addkeys(idx,tid)
  return lookup[key]|b<<12
 # Reuse orphan metatile slots, leaving every retained map/border entry untouched.
 mids=set(map(int,(original_grid&1023)[~cells]))|set(map(int,border&1023));free_mids=[i for i in range(len(blocks)) if i not in mids];ml={tuple(blocks[i])+(attrs[i],):i for i in mids}
 for y,x in np.argwhere(cells):
  es=[]
  for l,a in enumerate([bg,fg]):
   for q in range(4):
    yy=y*16+q//2*8;xx=x*16+q%2*8;es.append(ent(a[yy:yy+8,xx:xx+8],int(banks[l,yy//8,xx//8]),l==0))
  old=int(original_grid[y,x]&1023);attr=oldattrs[old];key=tuple(es)+(attr,)
  if key not in ml:
   i=free_mids.pop(0) if free_mids else len(blocks)
   if i==len(blocks):blocks.append(es);attrs.append(attr)
   else:blocks[i]=es;attrs[i]=attr
   ml[key]=i
  grid[y,x]=(grid[y,x]&0xfc00)|ml[key]
 assert len(blocks)<=512
 for part in range(2):
  folder=G/f'data/tilesets/{"secondary" if part else "primary"}/route33';n=512 if not part else 496;sheet=np.zeros((((n+15)//16)*8,128),np.uint8)
  for i in range(n):
   if part*512+i<len(glyphs):sheet[i//16*8:i//16*8+8,i%16*8:i%16*8+8]=glyphs[part*512+i]
  im=Image.fromarray(sheet,'P');im.putpalette([v for i in range(256) for v in (i*17%256,)*3]);im.save(folder/'tiles.png',bits=4)
  for b in [2,4]:(folder/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
 folder=G/'data/tilesets/primary/route33';(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in blocks));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs));grid.tofile(G/'data/layouts/JohtoRoute33/map.bin')
 t=Tileset(G,'route33','route33');actual=t.map_image(grid.ravel().tolist(),34);assert np.array_equal(np.array(actual),preview[...,:3]);actual.save(E/'native-map.png')
 report.update(glyph_max=max(used|set(allocated)),allocated_glyphs=len(allocated),metatiles=len(blocks));np.save(S/'solid.npy',(grid&0xc00)!=0)
(E/'shared-asset-repair.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='placements'},indent=2))
