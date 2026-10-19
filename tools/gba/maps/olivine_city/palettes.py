"""Exact per-quadrant RGB5 covering. Never substitute unrelated native tiles."""
from pathlib import Path
import numpy as np,z3,json
from PIL import Image
def cover(inp):
 sets=set()
 for n in ['bottom','middle']:
  a=np.array(Image.open(inp/f'{n}.png').convert('RGBA'))
  for y in range(0,len(a),8):
   for x in range(0,a.shape[1],8):
    q=a[y:y+8,x:x+8];sets.add(frozenset(map(tuple,q[q[...,3]>0,:3])))
 ss=sorted([v for v in sets if not any(v<w for w in sets)],key=lambda v:(-len(v),sorted(v)));cs=sorted(set.union(*(set(v) for v in ss)));ci={c:i for i,c in enumerate(cs)}
 sol=z3.Solver();sol.set(timeout=60000);vs=[[z3.Bool(f'b{b}c{i}') for i in range(len(cs))] for b in range(13)]
 for row in vs:sol.add(z3.PbLe([(v,1) for v in row],15))
 for s in ss:sol.add(z3.Or(*[z3.And(*[row[ci[c]] for c in s]) for row in vs]))
 # Pin intact master families to remove arbitrary bank permutations. Only
 # colors actually used in this district participate; no art is recolored.
 def colors(n):
  q=np.array(Image.open(inp.parent/'masters'/f'{n}.png').convert('RGBA'));return set(map(tuple,q[q[...,3]>0,:3]&248))&set(cs)
 groups=[colors('cliff-front')|colors('paving')|colors('grass')|colors('sand'),colors('tree'),colors('water')|colors('sea-rock')]
 for n in (['cafe','lighthouse','mart'] if 'quay' in inp.name else ['terminal'] if 'harbor' in inp.name else ['house','house-pair','lighthouse']):
  p=colors(n)
  if p:groups.append(p)
 for b,p in enumerate(groups):
  for c in p:sol.add(vs[b][ci[c]])
 status=sol.check();print(inp.name,'colors',len(cs),'maximal patches',len(ss),status,flush=True);assert status==z3.sat,'Revise authored palette families; never discard silhouettes.'
 model=sol.model();out=inp/'palette-overrides';out.mkdir(exist_ok=True);pals=[]
 for i,row in enumerate(vs):
  pal=[c for c,v in zip(cs,row) if z3.is_true(model.eval(v))];pals.append(pal);lines=['-']+[' '.join(map(str,c)) for c in pal]+['-']*(15-len(pal));(out/f'{i:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(lines)+'\n')
 (inp/'exact-palette-cover.json').write_text(json.dumps(dict(maximal_patches=len(ss),colors=len(cs),banks=[[list(map(int,c)) for c in p] for p in pals]),indent=2)+'\n')
