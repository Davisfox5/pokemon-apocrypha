"""Local tree/gate closure patch against clean, owner-reviewed c8a826 source."""
from pathlib import Path
import sys,json,subprocess,shutil,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'tree-closure';B=D/'baseline';M=S/'masters';W,H=72,52
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='c8a8267606411bd62a6274ed0e5f430b1b2f7e80'
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True).strip(),'Preserve uncommitted native edits.'
D.mkdir(exist_ok=True)
if not B.exists():
 B.mkdir()
 for n in ['background.png','foreground.png','solid.npy','behaviors.npy','material-grid.npy','ground-material-grid.npy','tree-footprints.npy']:shutil.copyfile(S/n,B/n)
 for n in ['assembly.json','native-map.png']:shutil.copyfile(E/n,B/n)
bg=np.array(Image.open(B/'background.png'));fg=np.array(Image.open(B/'foreground.png'));solid=np.load(B/'solid.npy');mat=np.load(B/'material-grid.npy');ground=np.load(B/'ground-material-grid.npy');beh=np.load(B/'behaviors.npy');r=json.loads((B/'assembly.json').read_text());art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')};above=np.zeros((H,W),bool)
for n,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 t=Tileset(G,bank,bank);g=np.fromfile(G/'data/layouts'/n/'map.bin','<u2').reshape(h,W)
 for y,x in np.ndindex(h,W):mid=int(g[y,x]&1023);above[y+y0,x]=(t.attrs[mid>=512][mid%512]&0x3000)==0
names={'tree-hgss','maple-hgss','maple-amber','maple-autumn'};original=r['trees'];trees=[];moves=[]
for t in original:
 q=t.copy();x,y=t['x'],t['y']
 if (x in [0,2,4,6] and y>=30) or (x in [64,66,68,70] and y>=38):q['y']+=1;moves.append(dict(name=t['name'],before=[x,y],after=[x,q['y']]))
 trees.append(q)
added=[]
def add(n,x,y,reason,behind=False):
 t=dict(name=n,x=x,y=y);assert not any(p['x']==x and p['y']==y for p in trees);trees.append(t);added.append(dict(**t,reason=reason,behind_landmark=behind))
for y in [6,8,10,12,14]:add('tree-hgss',18,y,'Close west woodland to Burned Tower stone boundary')
for x in [22,24,26,28,30]:add('maple-autumn',x,4,'Complete autumn grove behind Burned Tower roof',True)
for x in [34,36,38,40,42,44]:add('maple-autumn',x,10,'Bring Bell entrance grove down to roof line',True)
for x in [0,2,4,6]:
 add('tree-hgss',x,22,'West gate northern forest shoulder',True);add('tree-hgss',x,29,'West gate southern forest shoulder')
for x in [64,66,68,70]:
 add('tree-hgss',x,28,'East gate northern forest shoulder',True);add('tree-hgss',x,37,'East gate southern forest shoulder')
for y in [44,46,48]:
 add('tree-hgss',38,y,'Seal southern torii west flank',True)
 for x in [44,46,48,50]:add('tree-hgss',x,y,'Seal southern torii east woodland',x==44)
def roots(entries):
 a=np.zeros((H,W),np.uint8)
 for t in entries:
  x,y=t['x'],t['y'];assert 0<=x and x+2<=W and 0<=y and y+3<=H;a[y+1:y+3,x:x+2]+=1
 assert a.max()==1,'Distinct full roots are required.'
 return a
oldroots=roots(original);newroots=roots(trees);removed=(oldroots>0)&(newroots==0);solid[removed]=False;mat[removed]='.';solid[newroots>0]=True;mat[newroots>0]='T'
# Closed, unwired gate walls meet the forest bands. Keep the city-facing
# approaches at west (7,25) and east (65,33); no route/warp behavior is invented.
solid[25:30,1:7]=True;mat[25:30,1:7]='B';solid[31:38,66:72]=True;mat[31:38,66:72]='B'
solid[0]=True;solid[-1]=True;solid[:,0]=True;solid[:,-1]=True
# The outer torii post/woodland join is closed; columns 40-42 stay open.
solid[44,39]=True;mat[44,39]='B'
for t in trees:
 if (t in [dict(name=a['name'],x=a['x'],y=a['y']) for a in added]) or any(m['after']==[t['x'],t['y']] for m in moves):above[t['y'],t['x']:t['x']+2]=True
# Paint the upper groves behind their roofs, in ordinary north/south canopy
# order. Front trees remain in front. The complete shared masters stay intact.
def behind(t):
 x,y=t['x'],t['y']
 return (x in [38,44] and y>=44) or (x in [22,24,26,28,30] and y<=4) or (x in [34,36,38,40,42,44] and y<=10) or (x in [0,2,4,6] and y<=22) or (x in [64,66,68,70] and y<=28)
def placement(t):return dict(name=t['name'],x=t['x']*16,y=t['y']*16,source_xy=[t['x']*16-64,t['y']*16-16],role='complete forest crown / distinct root footprint')
oldp=r['placements'];ids=[i for i,p in enumerate(oldp) if p['name'] in names];assert len(ids)==max(ids)-min(ids)+1
prefix=[placement(t) for t in sorted(trees,key=lambda t:(t['y'],t['x'])) if behind(t)];front=[placement(t) for t in sorted(trees,key=lambda t:(t['y'],t['x'])) if not behind(t)];placements=prefix+oldp[:min(ids)]+front+oldp[max(ids)+1:]
# Only changed tree neighborhoods are reassembled. Architecture encoded on
# separate layers elsewhere, all courts, and the accepted art remain untouched.
areas=[(288,64,512,272),(544,128,736,208),(0,320,128,832),(1024,416,1152,832),(608,688,832,832)]
mask=np.zeros(fg.shape[:2],bool)
for x0,y0,x1,y1 in areas:mask[y0:y1,x0:x1]=True
fg[mask]=0
for p in placements:
 a=art[p['name']];h,w=a.shape[:2];v=mask[p['y']:p['y']+h,p['x']:p['x']+w]&(a[...,3]>0);fg[p['y']:p['y']+h,p['x']:p['x']+w][v]=a[v]
# Keep tree/architecture overlap families on separate native layers wherever
# the entire cell is blocked. This retains colors and the front object's mask.
def layer(ps):
 out=np.zeros_like(fg)
 for p in ps:
  a=art[p['name']];h,w=a.shape[:2];m=a[...,3]>0;out[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m]
 return out
def comp(a,b):
 out=a.copy();m=b[...,3]>0;out[m]=b[m];return out
behind_layer=layer(prefix);architecture=layer(oldp[:min(ids)]);near_layer=layer(front+oldp[max(ids)+1:]);upper=comp(architecture,near_layer);layered=[]
for y0,y1,bank in [(0,432,'ecruteak_temple'),(432,832,'ecruteak_city')]:
 pals=[set(map(tuple,p)) for p in json.loads((B/(bank+'-exact-palette-cover.json')).read_text())['banks']]
 for y in range(y0,y1,8):
  for x in range(0,1152,8):
   sl=np.s_[y:y+8,x:x+8]
   if not mask[sl].any() or not solid[y//16,x//16]:continue
   a=bg[sl];b=fg[sl];ca=set(map(tuple,a[a[...,3]>0,:3]));cb=set(map(tuple,b[b[...,3]>0,:3]))
   if any(ca<=p for p in pals) and any(cb<=p for p in pals):continue
   target=comp(a,b);opts=[]
   base=comp(a,behind_layer[sl])
   for aa,bb in [(base,upper[sl]),(comp(base,architecture[sl]),near_layer[sl])]:
    if not np.array_equal(comp(aa,bb),target):continue
    cs=[set(map(tuple,q[q[...,3]>0,:3])) for q in [aa,bb]]
    if max(map(len,cs))>15:continue
    score=(max(map(len,cs)),sum(map(len,cs)));opts.append((score,aa.copy(),bb.copy()))
   if opts:
    _,aa,bb=min(opts,key=lambda z:z[0]);bg[sl]=aa;fg[sl]=bb;layered.append([x,y])
# Reuse existing native palette pairs for opaque blocked joins. This changes
# layer encoding only: every visible RGB pixel remains exact. Open canopy tiles
# retain their original ground/foreground priority.
encoded=[];deferred=[]
for y0,y1,bank in [(0,432,'ecruteak_temple'),(432,832,'ecruteak_city')]:
 pals=[set(map(tuple,p)) for p in json.loads((B/(bank+'-exact-palette-cover.json')).read_text())['banks']]
 for y in range(y0,y1,8):
  for x in range(0,1152,8):
   sl=np.s_[y:y+8,x:x+8];a=bg[sl].copy();b=fg[sl].copy();ca=set(map(tuple,a[a[...,3]>0,:3]));cb=set(map(tuple,b[b[...,3]>0,:3]))
   if any(ca<=p for p in pals) and any(cb<=p for p in pals):continue
   assert mask[sl].any(),('Unexpected change outside tree neighborhoods',x,y)
   if not solid[y//16,x//16]:deferred.append([x,y,'open canopy priority retained']);continue
   full=a.copy();m=b[...,3]>0;full[m]=b[m];colors=set(map(tuple,full[...,:3].reshape(-1,3)));opts=[]
   for i,pa in enumerate(pals):
    for j,pb in enumerate(pals):
     if not colors<=pa|pb:continue
     keep=np.array([tuple(c) in pb for c in full[...,:3].reshape(-1,3)]).reshape(8,8);score=int((keep&m).sum());opts.append((score,i,j))
   if not opts:deferred.append([x,y,'exact cover needs native allocation']);continue
   _,i,j=max(opts);pa,pb=pals[i],pals[j];keep=np.array([tuple(c) not in pa or (bool(mm) and tuple(c) in pb) for c,mm in zip(full[...,:3].reshape(-1,3),m.ravel())]).reshape(8,8);back=full.copy();default=sorted(pa)[0];back[keep,:3]=default;front=full.copy();front[~keep]=0;bg[sl]=back;fg[sl]=front;encoded.append([x,y,i,j])
# Hidden background pixels in blocked joins carry no visible texture. Fill
# them from that patch's visible ramp so they consume no extra native shades.
hidden=[]
for y in range(0,832,8):
 for x in range(0,1152,8):
  sl=np.s_[y:y+8,x:x+8]
  if not mask[sl].any() or not solid[y//16,x//16]:continue
  a=bg[sl];b=fg[sl];visible=a[b[...,3]==0,:3]
  if not len(visible):continue
  shade=sorted(set(map(tuple,visible)))[0];m=b[...,3]>0
  if m.any():a[m,:3]=shade;hidden.append([x,y])
np.save(S/'tree-closure/above.npy',above)
protect=above&solid;protect[-1]=False;protect[:-1]&=~solid[1:]
np.save(D/'exposed-mask.npy',protect);exposed=np.zeros_like(fg);pm=protect.repeat(16,0).repeat(16,1);exposed[pm]=fg[pm];Image.fromarray(exposed).save(D/'exposed-foreground.png')
from tree_layers import encode,finish
flexible=encode(S,bg,fg,solid,areas)
finishing=finish(S,bg,fg,solid)
assert np.array_equal(fg[pm],exposed[pm])
r['trees']=trees;r['placements']=placements
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
for n,a in [('solid',solid),('material-grid',mat),('tree-footprints',newroots)]:np.save(S/(n+'.npy'),a)
(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m];Image.fromarray(comp).save(D/'preview.png')
(D/'edit-report.json').write_text(json.dumps(dict(baseline_source='c8a8267606411bd62a6274ed0e5f430b1b2f7e80',added=added,moved=moves,tree_count=len(trees),changed_regions_native_pixels=areas,shared_master_hashes={n:hashlib.sha256((M/(n+'.png')).read_bytes()).hexdigest() for n in art},gate_scope='Existing gates remain closed/unwired; forest and wall collision close north/south bypasses while keeping city-facing approaches.',root_overlap_cells=0,blocked_join_encoding=encoded,exact_cover_joins=deferred,tree_architecture_layer_joins=layered,hidden_blocked_join_encoding=hidden,flexible_blocked_join_encoding=flexible,**finishing),indent=2)+'\n')
from compile_refinement import compile_native
compile_native(G,Path(sys.argv[2]),S,E,bg,fg,solid,beh,above,r)
