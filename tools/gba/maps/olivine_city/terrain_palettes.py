"""Exact RGB5 bank covering for the native terrain revision; no recoloring."""
from pathlib import Path
import numpy as np,json
from PIL import Image
from ortools.sat.python import cp_model
def cover(inp,source,mods):
 sets=set()
 for n in ['bottom','middle']:
  a=np.array(Image.open(inp/f'{n}.png').convert('RGBA'))
  for y in range(0,len(a),8):
   for x in range(0,a.shape[1],8):
    q=a[y:y+8,x:x+8];sets.add(frozenset(map(tuple,q[q[...,3]>0,:3])))
 assert max(map(len,sets))<=15,'A quadrant itself exceeds a native bank.'
 ss=sorted([v for v in sets if not any(v<w for w in sets)],key=lambda v:(-len(v),sorted(v)));cs=sorted(set.union(*(set(v) for v in ss)));ci={c:i for i,c in enumerate(cs)};B=13
 m=cp_model.CpModel();vs=[[m.new_bool_var(f'b{b}c{i}') for i in range(len(cs))] for b in range(B)];assign=[]
 for row in vs:m.add(sum(row)<=15)
 def colors(n):
  q=np.array(Image.open(source/'masters'/f'{n}.png').convert('RGBA'));return set(map(tuple,q[q[...,3]>0,:3]&248))&set(cs)
 def split(n):
  import z3
  q=np.array(Image.open(source/'masters'/f'{n}.png').convert('RGBA'));parts=[]
  for y in range(0,len(q),8):
   for x in range(0,q.shape[1],8):
    p=q[y:y+8,x:x+8];parts.append(set(map(tuple,p[p[...,3]>0,:3]&248)))
  cc=sorted(set.union(*parts));z=z3.Solver();v=[[z3.Bool(f'{n}{b}_{i}') for i in range(len(cc))] for b in range(2)]
  for row in v:z.add(z3.PbLe([(vv,1) for vv in row],15))
  for p in parts:z.add(z3.Or(*[z3.And(*[row[cc.index(c)] for c in p]) for row in v]))
  assert z.check()==z3.sat;model=z.model();return [{c for c,vv in zip(cc,row) if z3.is_true(model.eval(vv))}&set(cs) for row in v]
 stone=set(map(tuple,mods['front'][mods['front'][...,3]>0,:3]))&set(cs)
 if 'city' in inp.name:
  groups=[colors('tree'),colors('house'),colors('house-pair'),*split('civic-hall'),colors('lighthouse'),colors('water')|colors('sea-rock'),colors('bunting'),stone|colors('grass'),stone|colors('paving')]
 elif 'quay' in inp.name:
  groups=[colors('tree'),colors('cafe'),colors('lighthouse'),colors('mart'),*split('center'),colors('water')|colors('sea-rock'),colors('bunting')|colors('boat')|colors('umbrella'),stone|colors('grass'),stone|colors('paving')]
 else:groups=[colors('terminal'),colors('water')|colors('sea-rock'),colors('deck')]
 assert all(len(g)<=15 for g in groups),list(map(len,groups))
 # Generate exact palette candidates from compatible patch unions. Solving a
 # set cover removes interchangeable-bank symmetry without changing any RGB5
 # pixel. Intact material groups are candidates, never mandatory constraints.
 import random
 rng=random.Random(20261019);bits=[sum(1<<ci[c] for c in p) for p in ss];allmask=(1<<len(bits))-1;candidates={}
 topcols=set(map(tuple,mods['plateau-top'][...,:3].reshape(-1,3)))&set(cs)
 groups += [stone|topcols|colors('grass'),stone|topcols|colors('paving')]
 from tiles import palette
 oldstone=set()
 for n in ['cliff-front','cliff-side','cliff-top','cliff-toe','cliff-left']:
  oldstone |= colors(n)
 newstone=stone|topcols
 for f in (source.parent/'evidence'/(inp.name+'-compiled')/'palettes').glob('*.pal'):
  p=set(palette(f)[1:])&set(cs);groups.append(p);replaced=(p-oldstone)|newstone
  if len(replaced)<=15:groups.append(replaced)
 seeds=bits+[sum(1<<ci[c] for c in p) for p in groups if p and len(p)<=15]
 for seed in seeds:
  for trial in range(160):
   bank=seed
   for step in range(16):
    fits=[]
    for p in bits:
     union=bank|p
     if union!=bank and union.bit_count()<=15:
      overlap=(bank&p).bit_count();added=(p&~bank).bit_count();score=overlap*2.5-added*.5+p.bit_count()*.2+rng.random()*4
      fits.append((score,union))
    if not fits:break
    bank=max(fits)[1]
   cov=sum(1<<i for i,p in enumerate(bits) if p&bank==p)
   if cov not in candidates or bank.bit_count()<candidates[cov].bit_count():candidates[cov]=bank
 # Candidate dominance is exact on covered quadrants, not a visual heuristic.
 keep=[]
 for cov,bank in sorted(candidates.items(),key=lambda v:-v[0].bit_count()):
  if not any(cov&c==cov for c,_ in keep):keep.append((cov,bank))
 model=cp_model.CpModel();choose=[model.new_bool_var(f'palette{i}') for i in range(len(keep))]
 for i in range(len(bits)):model.add(sum(v for v,(cov,_) in zip(choose,keep) if cov>>i&1)>=1)
 model.add(sum(choose)<=13);model.minimize(sum(choose));solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=60;solver.parameters.num_search_workers=5;status=solver.solve(model)
 print(inp.name,'colors',len(cs),'patches',len(ss),'candidates',len(keep),solver.status_name(status),flush=True)
 assert status in (cp_model.OPTIMAL,cp_model.FEASIBLE),'No exact bank cover; revise local joins instead of flattening terrain.'
 banks=[b for v,(_,b) in zip(choose,keep) if solver.value(v)];out=inp/'palette-overrides';out.mkdir(exist_ok=True);pals=[]
 for i in range(13):
  bit=banks[i] if i<len(banks) else 0;pal=[c for j,c in enumerate(cs) if bit>>j&1];pal=pal or [(0,0,0)];pals.append(pal);lines=['-']+[' '.join(map(str,c)) for c in pal]+['-']*(15-len(pal));(out/f'{i:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(lines)+'\n')
 (inp/'exact-palette-cover.json').write_text(json.dumps(dict(solver='OR-Tools exact candidate set cover',maximal_patches=len(ss),colors=len(cs),candidate_count=len(keep),banks=[[list(map(int,c)) for c in p] for p in pals]),indent=2)+'\n')
