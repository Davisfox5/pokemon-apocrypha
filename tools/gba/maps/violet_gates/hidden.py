import numpy as np
from collections import defaultdict
from ts import TS
B=TS('/home/user/pokeemerald-expansion')
used=set(int(v)&1023 for v in B.w.ravel())
# usages: tile -> list of (layer, bank, flip, visible mask)
us=defaultdict(list)
for m in used:
    E=B.ents(m)
    for q in range(4):
        lo,up=E[q],E[4+q]
        vis=(B.idx(up)==0)
        # mask in tile's own orientation
        f=lo&3072; mk=vis
        if f&1024: mk=mk[:,::-1]
        if f&2048: mk=mk[::-1]
        us[lo&1023].append((0,lo>>12,mk))
        us[up&1023].append((1,up>>12,np.ones((8,8),bool)))
def col(t,bank,layer):
    i=B.tile(t); c=B.pals[bank][i].astype(int)
    if layer==0: c[i==0]=B.pals[0][0]
    else: c[i==0]=-1
    return c
tiles=sorted(us)
# B replaceable by A (same orientation) if all usages agree on visible pixels
def can(a,b):
    for layer,bank,mk in us[b]:
        ca=col(a,bank,layer); cb=col(b,bank,layer)
        if not (ca[mk]==cb[mk]).all(): return False
    return True
# lower-only-used tiles candidates
low=[t for t in tiles if all(l==0 for l,_,_ in us[t])]
# group by fully-visible pixels signature quickly: try pairs only among tiles sharing a bank
bybank=defaultdict(list)
for t in low:
    for _,bk,_ in us[t]: bybank[bk].append(t)
removed=set()
for bk,ts in bybank.items():
    ts=sorted(set(ts))
    for b in ts:
        if b in removed: continue
        for a in ts:
            if a==b or a in removed: continue
            if can(a,b): removed.add(b); break
print('lower tiles mergeable invisibly:',len(removed))
