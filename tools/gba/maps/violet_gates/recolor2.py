import pickle,numpy as np
from PIL import Image
from ts import TS
S='/tmp/claude-0/-home-user/85ee60ab-0025-575e-abae-bfbdaa5ee7ac/scratchpad/'
B=TS('/home/user/pokeemerald-expansion')
U,restbank,_=pickle.load(open('recolor.pkl','rb'))
U={b:set(v) for b,v in U.items()}
print({b:15-len(v) for b,v in U.items()})
isl=[(x,y) for x in range(47,51) for y in range(22,27)]
items=[]  # (key, pixels Nx3)
for (x,y) in isl:
    E=B.ents(int(B.w[y,x]))
    for i,e in enumerate(E):
        r=B.rgba(e,i<4); m=r[...,3]>0
        if m.any(): items.append(((x,y,i),r[m][:,:3]))
def err(px,cols):
    C=np.array(sorted(cols)); return ((px[:,None,:]-C[None])**2).sum(-1).min(1).sum()
def total(U):
    t=0;ch={}
    for k,px in items:
        best=min((err(px,U[b]),b) for b in range(13) if U[b]); t+=best[0]; ch[k]=best[1]
    return t,ch
cand=set()
for k,px in items: cand|={tuple(int(v) for v in p) for p in px}
cur,_=total(U); print('start err',cur)
while True:
    best=None
    for b in range(13):
        if len(U[b])>=15: continue
        for c in cand-U[b]:
            U[b].add(c); t,_=total(U); U[b].discard(c)
            if best is None or t<best[0]: best=(t,b,c)
    if best is None or best[0]>=cur: break
    cur=best[0]; U[best[1]].add(best[2]); print('add',best[2],'to',best[1],'err',cur)
t,ch=total(U)
pickle.dump((U,restbank,{k:(b,0) for k,b in ch.items()}),open('recolor.pkl','wb'))
