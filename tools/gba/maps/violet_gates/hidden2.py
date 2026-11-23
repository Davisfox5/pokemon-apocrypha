exec(open('hidden.py').read().split('removed=set()')[0])
import pickle
T4={}
def var(t):
    if t not in T4:
        i=B.tile(t); T4[t]=[(0,i),(1024,i[:,::-1]),(2048,i[::-1]),(3072,i[::-1,::-1])]
    return T4[t]
def canf(a,b):
    ib=B.tile(b)
    for fl,ia in var(a):
        ok=True
        for layer,bank,mk in us[b]:
            pa=B.pals[bank][ia]; pb=B.pals[bank][ib]
            # index 0 on the lower layer shows the backdrop
            ca=np.where((ia==0)[...,None],B.pals[0][0],pa); cb=np.where((ib==0)[...,None],B.pals[0][0],pb)
            if not (ca[mk]==cb[mk]).all(): ok=False;break
        if ok: return fl
    return None
removed={};targets=set()
allt=sorted(us)
for b in low:
    if b in targets: continue
    for a in allt:
        if a==b or a in removed: continue
        fl=canf(a,b)
        if fl is not None: removed[b]=(a,fl); targets.add(a); break
print('merges',len(removed))
pickle.dump(removed,open('merges2.pkl','wb'))
