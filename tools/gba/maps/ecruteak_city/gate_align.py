"""Move only the southern torii one native tile east on clean b89ae5d5."""
from pathlib import Path
import json,sys,subprocess,shutil,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'gate-alignment';B=D/'baseline';G=Path(sys.argv[1]);PT=Path(sys.argv[2])
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='b89ae5d5f14878b0b759ba04a495d50a676b6e6b'
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True).strip(),'Preserve native edits.'
B.mkdir(parents=True,exist_ok=True)
for n in ['background.png','foreground.png','solid.npy','material-grid.npy']:
 if not (B/n).exists():shutil.copyfile(S/n,B/n)
for n in ['assembly.json','native-map.png']:
 if not (B/n).exists():shutil.copyfile(E/n,B/n)
if not (B/'above.npy').exists():shutil.copyfile(S/'tree-closure/above.npy',B/'above.npy')
bg=np.array(Image.open(B/'background.png'));fg=np.array(Image.open(B/'foreground.png'));solid=np.load(B/'solid.npy');mat=np.load(B/'material-grid.npy');ground=np.load(S/'ground-material-grid.npy');roots=np.load(S/'tree-footprints.npy');above=np.load(B/'above.npy');r=json.loads((B/'assembly.json').read_text());art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (S/'masters').glob('*.png')};p=next(p for p in r['placements'] if p['name']=='south-gate');assert [p['x'],p['y']]==[624,688];p['x']+=16;p['source_xy'][0]+=16
l,t,rr,bb=624,688,720,752;bg[t:bb,l:rr]=np.array(Image.open(S/'tree-closure/baseline/background.png'))[t:bb,l:rr];fg[t:bb,l:rr]=0
# Forest first, gate last: complete canopies stay behind the moved gate.
ps=[p for p in r['placements'] if p['name']!='south-gate']+[p]
for q in ps:
 a=art[q['name']];h,w=a.shape[:2];x=max(l,q['x']);y=max(t,q['y']);xx=min(rr,q['x']+w);yy=min(bb,q['y']+h)
 if x>=xx or y>=yy:continue
 v=a[y-q['y']:yy-q['y'],x-q['x']:xx-q['x']];m=v[...,3]>0;fg[y:yy,x:xx][m]=v[m]
solid[43:47,39:45]=roots[43:47,39:45]>0;mat[43:47,39:45]=ground[43:47,39:45];mat[43:47,39:45][roots[43:47,39:45]>0]='T';above[43:47,39:45]=False
for q in r['trees']:
 if 43<=q['y']<47:
  for x in [q['x'],q['x']+1]:
   if 39<=x<45:above[q['y'],x]=True
# The beam is overhead. Only the two narrow posts below asset row 39 block feet.
a=art['south-gate'];postcells=sorted(set(((640+int(x))//16,(688+int(y))//16) for y,x in np.argwhere(a[...,3]>0) if y>=39))
for x,y in postcells:solid[y,x]=True
for y,x in np.argwhere(a[...,3]>0):
 mat[(688+y)//16,(640+x)//16]='B'
 if y<39:above[(688+y)//16,(640+x)//16]=True
assert np.where(~solid[45])[0].tolist()==[41,42]
# The shifted roof/canopy join needs an exact mixed-material bank. Reuse
# the existing verified layer packer, confined to this city's private tileset.
np.save(D/'above.npy',above);np.save(S/'tree-closure/above.npy',above)
protected=(~solid)|(above&solid&np.vstack([~solid[1:],np.zeros((1,72),bool)]));pm=protected.repeat(16,0).repeat(16,1);before_fg=fg.copy()
from tree_layers import encode,finish
encoded=encode(S,bg,fg,solid,[(l,t,rr,bb)],bank_names=['ecruteak_city'],covers_dir=D,preserve_existing=True)
finishing=finish(S,bg,fg,solid,bank_names=['ecruteak_city'])
assert np.array_equal(fg[pm],before_fg[pm]),'Preserve exposed foreground priority.'
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
np.save(S/'solid.npy',solid);np.save(S/'material-grid.npy',mat);np.save(D/'above.npy',above);np.save(S/'tree-closure/above.npy',above);(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
(D/'edit-report.json').write_text(json.dumps(dict(baseline_source='b89ae5d5f14878b0b759ba04a495d50a676b6e6b',before=[624,688],after=[640,688],offset_native_cells=[1,0],changed_art_box=[l,t,rr,bb],post_blocked_cells=postcells,only_gate_passage_columns=[41,42],overhead_beam_last_asset_row=38,tree_and_other_building_placements_unchanged=True,exact_local_encoding=encoded,packing_finish=finishing,master_hashes={n:hashlib.sha256((S/'masters'/(n+'.png')).read_bytes()).hexdigest() for n in art}),indent=2)+'\n')
from palette_order import preserve
(D/'palette-slot-order.json').write_text(json.dumps(preserve(G,S,B),indent=2)+'\n')
from compile_refinement import compile_native
compile_native(G,PT,S,E,bg,fg,solid,np.load(S/'behaviors.npy'),above,r)
