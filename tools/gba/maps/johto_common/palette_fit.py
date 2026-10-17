"""Exact bounded palette allocation. Requires z3-solver; never changes RGB."""
import json,sys
from z3 import Bool,BoolVal,And,Or,SolverFor,PbLe,Implies,sat
v=json.load(open(sys.argv[1]));pals=[set(map(tuple,p)) for p in v['palettes']];qs=[set(map(tuple,q)) for q in v['quarters']];slots=v['free_slots']
qs=[q for q in qs if not any(q<=pals[i]|pals[j] for i in range(13) for j in range(i,13))]
qs=[q for q in qs if not any(q<r for r in qs)]
s=SolverFor("QF_FD");s.set(timeout=180000);x={}
def has(c,b):
 if c in pals[b]:return BoolVal(True)
 if not slots[b]:return BoolVal(False)
 return x.setdefault((c,b),Bool('c'+'_'.join(map(str,c))+'b'+str(b)))
for k,q in enumerate(qs):
 choices=[]
 for i in range(13):
  for j in range(i,13):
   if len(q-pals[i]-pals[j])>slots[i]+(slots[j] if i!=j else 0):continue
   pick=Bool(f'q{k}_{i}_{j}');choices.append(pick)
   s.add(Implies(pick,And([Or(has(c,i),has(c,j)) for c in q])))
 s.add(Or(choices))
for b in range(13):
 vs=[a for (c,bb),a in x.items() if b==bb]
 if vs:s.add(PbLe([(a,1) for a in vs],slots[b]))
print('quarters',len(qs),'variables',len(x),flush=True);status=s.check();print(status,flush=True)
if status!=sat:raise SystemExit(2)
m=s.model();out={str(b):[list(c) for (c,bb),a in x.items() if b==bb and bool(m.eval(a,model_completion=True))] for b in range(13)};json.dump(out,open(sys.argv[2],'w'),indent=2)
