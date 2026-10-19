"""Solve exact thirteen-bank covers with flexible layers only at blocked joins.
Run with PYTHONPATH containing ortools 9.10: tree_cover.py BANK OUTPUT_DIRECTORY.
This is a read-only solver; tree_layers.py verifies and applies its cover.
"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from ortools.sat.python import cp_model
S=Path(__file__).resolve().parents[4]/'gba/art/ecruteak-city/source';bank=sys.argv[1];out=Path(sys.argv[2]);out.mkdir(exist_ok=True);y0,y1=(0,432) if 'temple' in bank else (432,832)
a=np.array(Image.open(S/'background.png'));f=np.array(Image.open(S/'foreground.png'));solid=np.load(S/'solid.npy');mask=np.zeros(a.shape[:2],bool)
for x,y,xx,yy in json.loads((S/'tree-closure/edit-report.json').read_text())['changed_regions_native_pixels']:mask[y:yy,x:xx]=True
above=np.load(S/'tree-closure/above.npy')
hard=set();flex=set()
for y in range(y0,y1,8):
 for x in range(0,1152,8):
  aa=a[y:y+8,x:x+8];bb=f[y:y+8,x:x+8]
  if (mask[y:y+8,x:x+8].any() or '--all-blocked' in sys.argv) and solid[y//16,x//16] and not (above[y//16,x//16] and y//16<51 and not solid[y//16+1,x//16]):
   q=aa.copy();q[bb[...,3]>0]=bb[bb[...,3]>0];flex.add(frozenset(tuple(map(int,c)) for c in q[...,:3].reshape(-1,3)))
  else:
   for q in [aa,bb]:hard.add(frozenset(tuple(map(int,c)) for c in q[q[...,3]>0,:3]))
hard=sorted([p for p in hard if not any(p<t for t in hard)],key=lambda p:(-len(p),sorted(p)));flex=sorted([p for p in flex if not any(p<t for t in flex)],key=lambda p:(-len(p),sorted(p)));cs=sorted(set(c for p in hard+flex for c in p));ci={c:i for i,c in enumerate(cs)};old=[set(map(tuple,b)) for b in json.loads((S/bank/'exact-palette-cover.json').read_text())['banks']];m=cp_model.CpModel();vs=[[m.NewBoolVar(f'b{b}c{i}') for i in range(len(cs))] for b in range(13)]
for row in vs:m.Add(sum(row)<=15)
used=set()
for j,p in enumerate(hard):
 row=[m.NewBoolVar(f'h{j}b{b}') for b in range(13)];m.AddExactlyOne(row)
 best=min(range(13),key=lambda b:(len(p-old[b]),-len(p&old[b])))
 for b in range(13):
  for c in p:m.AddImplication(row[b],vs[b][ci[c]])
  m.AddHint(row[b],int(b==best))
 fits=[b for b in range(13) if p<=old[b] and b not in used]
 if len(p)>=8 and fits:b=fits[0];m.Add(row[b]==1);used.add(b)
pairs=[(b,k) for b in range(13) for k in range(b,13)]
for j,p in enumerate(flex):
 row=[m.NewBoolVar(f'f{j}pair{i}') for i in range(len(pairs))];m.AddExactlyOne(row);best=min(range(len(pairs)),key=lambda i:len(p-(old[pairs[i][0]]|old[pairs[i][1]])))
 for i,(b,k) in enumerate(pairs):
  for c in p:m.AddBoolOr([row[i].Not(),vs[b][ci[c]],vs[k][ci[c]]])
  m.AddHint(row[i],int(i==best))
for b in range(13):
 for c,i in ci.items():m.AddHint(vs[b][i],int(c in old[b]))
s=cp_model.CpSolver();s.parameters.max_time_in_seconds=180;s.parameters.num_search_workers=8;s.parameters.random_seed=19
print(bank,'hard',len(hard),'flex',len(flex),'anchors',used,flush=True);status=s.Solve(m);print(s.StatusName(status),flush=True)
assert status in [cp_model.OPTIMAL,cp_model.FEASIBLE]
banks=[[c for c,v in zip(cs,row) if s.Value(v)] for row in vs];(out/'exact-palette-cover.json').write_text(json.dumps(dict(banks=banks,solver='Exact flexible blocked-join layer packing',hard_patches=len(hard),flexible_patches=len(flex),allow_all_blocked='--all-blocked' in sys.argv,protect_exposed=True),indent=2)+'\n')
