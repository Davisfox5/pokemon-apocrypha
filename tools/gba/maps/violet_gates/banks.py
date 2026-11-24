import pickle,numpy as np
from ts import TS
B=TS('/home/user/pokeemerald-expansion')
R,plan,new=pickle.load(open('plan.pkl','rb'))
# colours used elsewhere per bank (after removal of R cells; island keeps bank 2)
Rs=set(R)
use={b:set() for b in range(13)}
for y in range(72):
  for x in range(80):
    if (x,y) in Rs: continue
    for i,e in enumerate(B.ents(int(B.w[y,x]))):
      idx=set(np.unique(B.idx(e)).tolist())
      if i>=4: idx.discard(0)
      use[e>>12]|={tuple(int(v) for v in B.pals[e>>12][k]) for k in idx if k}
for out in plan.values():
  for k,v in out:
    if k=='e' and v:
      idx=set(np.unique(B.idx(v)).tolist())-{0}
      use[v>>12]|={tuple(int(c) for c in B.pals[v>>12][k]) for k in idx}
tiles=[(l,r) for l in (0,1) for r in new[l]]
sets=[frozenset(tuple(int(c) for c in p[:3]) for p in r.reshape(-1,4) if p[3]) for l,r in tiles]
pickle.dump((use,tiles,sets),open('banks.pkl','wb'))
print({b:15-len(u) for b,u in use.items()})
fits={i:[b for b in range(13) if len(use[b]|s)<=15] for i,s in enumerate(sets)}
print('tiles with no bank fitting alone:',sum(1 for v in fits.values() if not v))
allc=set().union(*sets); print('distinct colours',len(allc))
