"""Verify the Route 31 pond/divider correction against its pre-edit geometry."""
from compose import *
import hashlib,json,subprocess,io
from collections import deque
G=Path(sys.argv[1]).resolve();EV=OUT/'evidence'
before=json.loads((EV/'divider-baseline.json').read_text());comps=all_comps()
for name,(c,_) in comps.items():
 mask=np.ones((c['H'],c['W']),bool)
 if name=='route31':mask[3:30,26:35]=False
 for k in ('solid','behavior','cells'):
  assert hashlib.sha256(c[k][mask].tobytes()).hexdigest()==before['outside_scope'][name][k],(name,k)
 previous=Image.open(io.BytesIO(subprocess.check_output(['git','show',before['baseline_commit']+':gba/art/johto-synthesis/evidence/'+name+'.png'],cwd=ROOT))).convert('RGB')
 current=Image.open(EV/(name+'.png')).convert('RGB');a=np.array(previous);b=np.array(current)
 mask=np.ones(a.shape[:2],bool)
 if name=='route31':mask[48:480,400:576]=False
 assert np.array_equal(a[mask],b[mask]),('unrelated art changed',name)
c,p=comps['route31'];a=assets()[0]
assert (c['cells'][6:15,26:33]==ground.SEA).all()
assert (c['cells'][15,26:33]==ground.GRASS).all(),'no lawn between pond and dirt'
assert (c['solid'][3:16,33:35]).all() and c['solid'][18:30,33:35].all()
assert not c['solid'][16:18,33:35].any()
assert (c['cells'][16:18,33:35]==ground.PATH).all()
assert (c['behavior'][6:15,26:33]==16).all()
# Every tree beside the divider is whole; no rock replaces a crown or trunk.
mc=c['canvas'];tree_checks=0
for x,y,t in oldart.forest(c['plan'],a['tree']):
 if not (448<=x<592):continue
 m=t.px>0;sl=np.s_[y:y+t.h,x:x+t.w]
 assert (mc.bank[sl][m]==3).all() and np.array_equal(mc.idx[sl][m],t.px[m]),('rock over tree',x,y)
 tree_checks+=1
report=dict(baseline_commit=before['baseline_commit'],outside_scope_unchanged=True,
 pond_cells=[26,6,33,15],pond_shift_north_pixels=16,lawn_row_before_path=15,
 divider_cells=[33,3,35,30],crossing_cells=[33,16,35,18],
 full_trees_checked=tree_checks,face_direction='east',high_ground='west')
(EV/'divider-structure.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
