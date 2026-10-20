"""Narrow owner-requested landmark correction on clean d5405cdc native source."""
from pathlib import Path
import sys,json,subprocess,shutil,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'landmark-finish';B=D/'baseline';G=Path(sys.argv[1]);PT=Path(sys.argv[2])
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='d5405cdcbddf65a0f9b5e19130cbd29db66cefe0'
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True).strip(),'Preserve native edits.'
B.mkdir(parents=True,exist_ok=True)
for n in ['background.png','foreground.png','solid.npy','material-grid.npy','tree-footprints.npy']:
 if not (B/n).exists():shutil.copyfile(S/n,B/n)
for n in ['assembly.json','native-map.png']:
 if not (B/n).exists():shutil.copyfile(E/n,B/n)
if not (B/'above.npy').exists():shutil.copyfile(S/'tree-closure/above.npy',B/'above.npy')
bg=np.array(Image.open(B/'background.png'));fg=np.array(Image.open(B/'foreground.png'));solid=np.load(B/'solid.npy');mat=np.load(B/'material-grid.npy');above=np.load(B/'above.npy');r=json.loads((B/'assembly.json').read_text());art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (S/'masters').glob('*.png')};names={'tree-hgss','maple-hgss','maple-amber','maple-autumn'}
if not (B/'bell-entrance.png').exists():shutil.copyfile(S/'masters/bell-entrance.png',B/'bell-entrance.png')
bell=np.array(Image.open(B/'bell-entrance.png'));oldbell=bell.copy();bell[2:4,69:180]=0
# The leaf tuft below the ridge covered a short timber edge. Recover that
# edge from the same unobscured vertical timber eight pixels below it.
bell[18:23,59:74]=oldbell[26:31,59:74];bell[18:23,59]=[32,32,32,255]
art['bell-entrance']=bell;Image.fromarray(bell).save(S/'masters/bell-entrance.png')
removed=dict(name='maple-hgss',x=32,y=16);assert r['trees'].count(removed)==1;r['trees'].remove(removed);p=next(p for p in r['placements'] if p['name']==removed['name'] and p['x']==512 and p['y']==256);r['placements'].remove(p)
areas=[(512,256,544,304),(608,200,728,208),(600,216,624,224)]
# Current architecture/forest order is preserved. Recover accepted grass hidden
# under this one tree, then reveal the original complete fence masters.
base=np.array(Image.open(S/'tree-closure/baseline/background.png'));bg[256:304,512:544]=base[256:304,512:544];fg[256:304,512:544]=0
for p in r['placements']:
 a=art[p['name']];h,w=a.shape[:2];l=max(512,p['x']);t=max(256,p['y']);rr=min(544,p['x']+w);bb=min(304,p['y']+h)
 if l>=rr or t>=bb:continue
 v=a[t-p['y']:bb-p['y'],l-p['x']:rr-p['x']];m=v[...,3]>0;fg[t:bb,l:rr][m]=v[m]
# Put the complete grove on the rear plane. Only the two roof-mask joins
# are rebuilt; the existing roof ridge, annex rail and all placements stay put.
for l,t,rr,bb in areas[1:]:
 bg[t:bb,l:rr]=base[t:bb,l:rr];fg[t:bb,l:rr]=0
 for p in r['placements']:
  a=art[p['name']];h,w=a.shape[:2];ll=max(l,p['x']);tt=max(t,p['y']);right=min(rr,p['x']+w);bottom=min(bb,p['y']+h)
  if ll>=right or tt>=bottom:continue
  v=a[tt-p['y']:bottom-p['y'],ll-p['x']:right-p['x']];m=v[...,3]>0;layer=bg if p['name'] in names else fg;layer[tt:bottom,ll:right][m]=v[m]
# The four former tree-root cells already belong to the fence; it stays solid.
roots=np.zeros((52,72),np.uint8)
for t in r['trees']:roots[t['y']+1:t['y']+3,t['x']:t['x']+2]+=1
assert roots.max()==1 and solid[17:19,32:34].all();mat[17:19,32:34]='F';above[16,32:34]=False
# Exact local palette-pair packing; no changes to other native layers.
encoded=[]
for bank,y0,y1 in [('ecruteak_temple',0,432),('ecruteak_city',432,832)]:
 pals=[set(map(tuple,p)) for p in json.loads((S/bank/'exact-palette-cover.json').read_text())['banks']]
 for l,t,rr,bb in areas:
  for y in range(max(t,y0),min(bb,y1),8):
   for x in range(l,rr,8):
    sl=np.s_[y:y+8,x:x+8];a=bg[sl].copy();b=fg[sl].copy();ca=set(map(tuple,a[a[...,3]>0,:3]));cb=set(map(tuple,b[b[...,3]>0,:3]))
    if any(ca<=p for p in pals) and any(cb<=p for p in pals):continue
    assert solid[y//16,x//16] and (not above[y//16,x//16] or (y//16<51 and solid[y//16+1,x//16]))
    target=a.copy();m=b[...,3]>0;target[m]=b[m];cs=set(map(tuple,target[...,:3].reshape(-1,3)));options=[]
    for i,pa in enumerate(pals):
     for j,pb in enumerate(pals):
      if not cs<=pa|pb:continue
      keep=np.array([tuple(c) not in pa or (bool(mm) and tuple(c) in pb) for c,mm in zip(target[...,:3].reshape(-1,3),m.ravel())]).reshape(8,8);options.append((int((keep==m).sum()),i,j,keep))
    assert options,(x,y);_,i,j,m=max(options,key=lambda v:v[:3]);back=target.copy();back[m,:3]=sorted(pals[i])[0];front=target.copy();front[~m]=0;bg[sl]=back;fg[sl]=front;encoded.append([x,y,i,j])
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
np.save(S/'tree-footprints.npy',roots);np.save(S/'material-grid.npy',mat);np.save(D/'above.npy',above);np.save(S/'tree-closure/above.npy',above);(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(D/'edit-report.json').write_text(json.dumps(dict(baseline_source='d5405cdcbddf65a0f9b5e19130cbd29db66cefe0',removed_tree=removed,tree_count=len(r['trees']),areas=areas,collision_unchanged=True,master_hashes={n:hashlib.sha256((S/'masters'/(n+'.png')).read_bytes()).hexdigest() for n in art},exact_local_layer_encoding=encoded,bell_mask_removed_source_foliage=[[69,2,180,4]],bell_timber_repair=dict(box=[59,18,74,23],donor=[59,26,74,31]),all_tree_positions_other_than_removed_unchanged=True),indent=2)+'\n')
from compile_refinement import compile_native
compile_native(G,PT,S,E,bg,fg,solid,np.load(S/'behaviors.npy'),above,r)
