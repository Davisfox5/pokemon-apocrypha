"""Apply cleaned masters to the current 8eb23f67 native Olivine source.

No geographic generator is replayed. All object positions, row counts, physical
footprints, event identities, elevations and traversability are retained.
"""
from pathlib import Path
import sys,json,subprocess,hashlib,shutil
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent))
G,PT=map(Path,sys.argv[1:3]);S=ROOT/'gba/art/olivine-city/source'
P=S/'forest-refinement';T=S/'asset-cleanup';E=S.parent/'evidence/asset-cleanup'
BASE='8eb23f6774fd937f3018d413f1fab5b6dc8d05c8'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
paths=subprocess.check_output(['git','-C',str(G),'ls-files'],text=True).splitlines()
paths=[p for p in paths if '/olivine_' in p or '/JohtoOlivine' in p]
def digest(raw,p):return hashlib.sha256(raw.replace(b'\r\n',b'\n') if p.endswith('.pal') else raw).hexdigest()
last=json.loads((T/'last-output.json').read_text()) if (T/'last-output.json').exists() else {}
for p in paths:
 base=subprocess.check_output(['git','-C',str(G),'show',BASE+':'+p]);assert digest((G/p).read_bytes(),p) in [digest(base,p),last.get(p)],'Unrecognized native edit: '+p
assembly=json.loads((S.parent/'evidence/forest-refinement/assembly.json').read_text())
oldbg=np.array(Image.open(P/'background.png').convert('RGBA'));oldfg=np.array(Image.open(P/'foreground.png').convert('RGBA'))
bg=np.array(Image.open(P/'receiving-surfaces.png').convert('RGBA'))
wall=np.array(Image.open(P/'wall-mask.png'))>0;rock=np.array(Image.open(P/'rock-layer.png').convert('RGBA'))
ground=np.load(P/'ground-material-grid.npy');Y,X=np.indices(bg.shape[:2]);sx,sy=X-64,Y-16
art={}
for folder in [S/'masters',P/'masters',T/'masters']:
 for p in folder.glob('*.png'):
  a=np.array(Image.open(p).convert('RGBA'));a[...,:3]&=248;art[p.stem]=a

# Restore actual receiving materials beneath every foreground object. The
# old packed plane contains unrelated hidden glyphs; these are not terrain.
baseground=art['grass'][sy%16,sx%16].copy();gm=ground[Y//16,X//16]
for code,n in [('P','paving'),('D','deck'),('S','sand'),('W','water')]:
 a=art[n];m=gm==code;baseground[m]=a[sy[m]%len(a),sx[m]%a.shape[1]]
baseground[wall]=rock[wall]
hidden=oldfg[...,3]>0;bg[hidden]=baseground[hidden]
oldrock=np.array(Image.open(S/'masters/sea-rock.png').convert('RGBA'))
for p in assembly['placements']:
 if p['name']!='sea-rock':continue
 x,y=p['x'],p['y'];h,w=oldrock.shape[:2];m=oldrock[...,3]>0
 # A coastal metatile may contain half a pier. Its cell label cannot decide
 # the water under a boulder on the other half of that same cell.
 yy,xx=np.indices((h,w));q=art['water'][(yy+y-16)%32,(xx+x-64)%32]
 bg[y:y+h,x:x+w][m]=q[m]

# Encode existing stone vocabulary with isolated one-pixel color noise removed.
# Each 8x8 glyph is processed once, with its own material mask. Complete masks,
# edge pixels and every continuous crease are protected; no nearest-tile swap.
cache={};stone_changes=0
for y in range(0,704,8):
 for x in range(0,1152,8):
  sl=np.s_[y:y+8,x:x+8];q=rock[sl].copy();m=wall[sl]
  if not m.any():continue
  key=q.tobytes()
  if key not in cache:
   out=q.copy();pal=np.unique(q[m,:3],axis=0)
   for yy in range(1,7):
    for xx in range(1,7):
     if not m[yy-1:yy+2,xx-1:xx+2].all():continue
     v=q[yy,xx,:3].astype(int);neighbors=q[yy-1:yy+2,xx-1:xx+2,:3].reshape(-1,3)
     same=np.all(neighbors==v,1)
     if same.sum()!=1:continue
     colors,counts=np.unique(neighbors,axis=0,return_counts=True);c=colors[counts.argmax()]
     # Only adjacent ramp noise, never deep cracks or bright cap highlights.
     if counts.max()>=5 and np.abs(c.astype(int)-v).max()<=32:out[yy,xx,:3]=c
   cache[key]=out
  out=cache[key];change=np.any(out!=q,2)&m;stone_changes+=int(change.sum());rock[sl][change]=out[change];bg[sl][change]=out[change]

fg=np.zeros_like(oldfg);owner=np.zeros(bg.shape[:2],np.uint16)
for i,p in enumerate(assembly['placements'],1):
 x,y=p['x'],p['y'];n=p['name']
 if n in ['stairs','ramp']:
  # Current timber geometry has already been rebuilt against the HGSS axis.
  # Preserve complete current pixels, including the ramp's projecting top rail.
  w,h=(48,24) if n=='stairs' else (64,65)
  if n=='ramp':y-=1
  a=oldfg[y:y+h,x:x+w].copy()
  Image.fromarray(a).save(T/'masters'/f'{n}.png')
  if n=='ramp':p['y']=y;p['source_xy']=[x-64,y-16]
 else:a=art[n];h,w=a.shape[:2]
 m=a[...,3]>0;fg[y:y+h,x:x+w][m]=a[m];owner[y:y+h,x:x+w][m]=i

# Keep a compact vocabulary only for fully interior stone. Reserve unique
# glyphs for every silhouette, cap contact, corner and foreground detail.
from collections import defaultdict
from scipy.cluster.vq import kmeans2
from reset_tiles import plane
groups=defaultdict(list);texture_report=[]
for y in range(0,704,8):
 for x in range(0,1152,8):
  if wall[y:y+8,x:x+8].all():groups[(y>=416,plane(x,y))].append((y,x))
for (quay,facing),positions in groups.items():
 unique={bg[y:y+8,x:x+8].tobytes():bg[y:y+8,x:x+8].copy() for y,x in positions}
 bank=np.stack(list(unique.values()));limit={'east':20,'west':16,'front':32,'plateau':8}[facing]
 if quay:limit={'east':12,'west':10,'front':20,'plateau':8}[facing]
 if len(bank)<=limit:continue
 # Edge-weighted medoids preserve source clusters instead of blurred averages.
 weights=np.ones((8,8,1));weights[[0,-1]]=3;weights[:,[0,-1]]=3
 features=(bank[...,:3].astype(float)*weights).reshape(len(bank),-1)
 centers,assigned=kmeans2(features,limit,minit='++',iter=40,seed=43);ids=[]
 for k,c in enumerate(centers):
  ii=np.flatnonzero(assigned==k)
  if len(ii):ids.append(ii[np.argmin(((features[ii]-c)**2).sum(1))])
 reps=bank[ids];values=features[ids]
 for y,x in positions:
  q=bg[y:y+8,x:x+8];v=(q[...,:3].astype(float)*weights).reshape(-1)
  k=int(np.argmin(((values-v)**2).sum(1)));bg[y:y+8,x:x+8]=reps[k];rock[y:y+8,x:x+8]=reps[k]
 texture_report.append(dict(district='Quay' if quay else 'City',facing=facing,before=len(bank),after=len(reps),mixed_edges_changed=0))
Image.fromarray(bg).save(T/'receiving-surfaces.png')
Image.fromarray(rock).save(T/'rock-layer.png');shutil.copyfile(P/'wall-mask.png',T/'wall-mask.png')
for n in ['above','solid','behaviors','material-grid','ground-material-grid','tree-footprints']:shutil.copyfile(P/(n+'.npy'),T/(n+'.npy'))
shutil.copyfile(P/'tree-rows.json',T/'tree-rows.json')
assembly['tree_master_directory']='asset-cleanup/masters'
without=bg.copy()
for i,p in enumerate(assembly['placements'],1):
 if p['name']=='olivine-tree':continue
 m=owner==i;without[m]=fg[m]
Image.fromarray(without).save(E/'trees-hidden.png')
Image.fromarray(bg).save(E/'all-objects-hidden.png')

from reset_tiles import hidden_background
# Compact only invisible background; do not alter the complete authored plane.
for y in range(0,896,8):
 for x in range(0,1152,8):
  sl=np.s_[y:y+8,x:x+8]
  if (fg[sl][...,3]>0).all():bg[sl]=baseground[0:8,0:8]
hidden_report=hidden_background(bg,fg)
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(T/(n+'.png'))
composite=bg.copy();m=fg[...,3]>0;composite[m]=fg[m];Image.fromarray(composite).save(E/'native-proposal.png')
(E/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
(T/'conversion-review.json').write_text(json.dumps(dict(base=BASE,placements=len(assembly['placements']),stone_native_glyphs_reviewed=len(cache),stone_noise_pixels_removed=stone_changes,wall_contour_changes=0,interior_vocabulary=texture_report,hidden_background_reuse=hidden_report,collision_changes=0),indent=2)+'\n')
if '--preview' in sys.argv:raise SystemExit(0)
rockpal=np.array([(88,56,32),(112,72,40),(136,88,48),(152,104,56),(176,128,72),(192,152,96),(216,184,120)],np.uint8)
mods={'front':np.dstack([rockpal.reshape(1,-1,3),np.full((1,len(rockpal)),255,np.uint8)]),'plateau-top':art['cliff-top']}
from compile_planes import compile_planes
stats=compile_planes(G,PT,S,T,E,assembly,bg,fg,np.load(T/'above.npy'),np.load(T/'solid.npy'),np.load(T/'behaviors.npy'),mods,include_harbor=True)
(T/'last-output.json').write_text(json.dumps({p:digest((G/p).read_bytes(),p) for p in paths},indent=2)+'\n')
print(json.dumps(stats,indent=2))
