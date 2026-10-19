"""Exact RGB5 palette covering; Porytiles remains the native compiler."""
import numpy as np
from pathlib import Path
from PIL import Image
import z3,json,sys
def cover(inp,refinement=False):
 sets=set()
 for n in ['bottom','middle']:
  a=np.array(Image.open(inp/f'{n}.png').convert('RGBA'))
  for y in range(0,len(a),8):
   for x in range(0,a.shape[1],8):
    q=a[y:y+8,x:x+8];sets.add(frozenset(map(tuple,q[q[...,3]>0,:3])))
 ss=sorted([v for v in sets if not any(v<w for w in sets)],key=lambda v:(-len(v),sorted(v)))
 cs=sorted(set.union(*(set(v) for v in ss)));ci={c:i for i,c in enumerate(cs)}
 sol=z3.Solver();sol.set(timeout=180000 if refinement else 60000)
 vs=[[z3.Bool(f'b{b}c{i}') for i in range(len(cs))] for b in range(13)]
 for row in vs:sol.add(z3.PbLe([(v,1) for v in row],15))
 for s in ss:sol.add(z3.Or(*[z3.And(*[row[ci[c]] for c in s]) for row in vs]))
 # Fix intact material ramps first. This removes arbitrary bank permutations
 # without guessing colors or letting nearest-tile substitution damage edges.
 M=inp.parent/'masters'
 def colors(name):
  a=np.array(Image.open(M/f'{name}.png').convert('RGBA'));return set(map(tuple,a[a[...,3]>0,:3]&248))
 green=colors('tree-hgss')|colors('maple-hgss') if refinement else colors('tree')
 autumn=colors('maple-amber')|colors('maple-autumn') if refinement else colors('tree-amber')|colors('tree-autumn')
 burned=colors('burned-tower');bell=colors('bell-entrance')
 if refinement:
  if len(burned)>15:burned-={(24,56,40),(40,80,48)}
  if len(bell)>15:bell-={(72,64,112),(128,120,176),(88,24,8),(120,40,16),(152,56,32),(176,80,40),(208,112,64)}
 groups=([green,autumn,burned,bell,colors('house')] if 'temple' in inp.name else [green]+[colors(n) for n in ['house','gym','dance-theater','south-gate','mart']])
 # The approved gate/Center masters use two banks each, kept exact.
 for name in (['gate'] if 'temple' in inp.name else ['gate','center']):
  a=np.array(Image.open(M/f'{name}.png').convert('RGBA'));pieces=[]
  for y in range(0,len(a),8):
   for x in range(0,a.shape[1],8):
    q=a[y:y+8,x:x+8];pieces.append(set(map(tuple,q[q[...,3]>0,:3]&248)))
  cc=sorted(set.union(*pieces));s=z3.Solver();v=[[z3.Bool(f'{name}a{b}i{i}') for i in range(len(cc))] for b in range(2)]
  for row in v:s.add(z3.PbLe([(vv,1) for vv in row],15))
  for p in pieces:s.add(z3.Or(*[z3.And(*[row[cc.index(c)] for c in p]) for row in v]))
  assert s.check()==z3.sat;m=s.model();groups.extend({c for c,vv in zip(cc,row) if z3.is_true(m.eval(vv))} for row in v)
 assert all(len(p)<=15 for p in groups),list(map(len,groups))
 for b,p in enumerate(groups):
  for c in p:
   if c in ci:sol.add(vs[b][ci[c]])
 if refinement:
  for b in range(len(groups),12):
   le=z3.BoolVal(True)
   for i in reversed(range(len(cs))):le=z3.Or(z3.And(z3.Not(vs[b][i]),vs[b+1][i]),z3.And(vs[b][i]==vs[b+1][i],le))
   sol.add(le)
 status=sol.check();print(inp.name,status,flush=True)
 assert status==z3.sat,'No loss of detail permitted: revise local material joins instead.'
 model=sol.model();out=inp/'palette-overrides';out.mkdir(exist_ok=True);pals=[]
 for i,row in enumerate(vs):
  pal=[c for c,v in zip(cs,row) if z3.is_true(model.eval(v))];pals.append(pal)
  lines=['-']+[' '.join(map(str,c)) for c in pal]+['-']*(15-len(pal))
  (out/f'{i:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(lines)+'\n')
 (inp/'exact-palette-cover.json').write_text(json.dumps({'maximal_patches':len(ss),'colors':len(cs),'banks':[[list(map(int,c)) for c in p] for p in pals]},indent=2)+'\n')
if __name__=='__main__':cover(Path(sys.argv[1]))
