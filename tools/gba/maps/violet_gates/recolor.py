import pickle,numpy as np
from PIL import Image
from ts import TS
S='/tmp/claude-0/-home-user/85ee60ab-0025-575e-abae-bfbdaa5ee7ac/scratchpad/'
B=TS('/home/user/pokeemerald-expansion'); O=TS(S+'old')
use,tiles,sets=pickle.load(open('banks.pkl','rb'))
gate=set(tuple(int(c) for c in p) for p in O.pals[10][1:])
U={b:set(u) for b,u in use.items()}; U[2]=set(gate)
rest=[i for i,s in enumerate(sets) if not s<=gate]
restbank={}
for i in sorted(rest,key=lambda i:-len(sets[i])):
    opts=[(len(U[b]|sets[i])-len(U[b]),b) for b in range(13) if b!=2 and len(U[b]|sets[i])<=15]
    _,b=min(opts); U[b]|=sets[i]; restbank[i]=b
# island: remove island's own contribution from U (non-bank2 banks) -> recompute use without island
isl=[(x,y) for x in range(47,51) for y in range(22,27)]
img=np.array(Image.open(S+'violet-base.png')).astype(int)
def nearest(px,cols):
    C=np.array(sorted(cols)); d=((px[:,None,:]-C[None])**2).sum(-1); return C[d.argmin(1)],d.min(1)
out=img.copy(); choice={}
for (x,y) in isl:
    E=B.ents(int(B.w[y,x]))
    for q in range(4):
        for layer,i in ((0,q),(1,4+q)):
            e=E[i]; r=B.rgba(e,layer==0)
            m=r[...,3]>0
            if not m.any(): continue
            px=r[m][:,:3]
            best=None
            for b in range(13):
                cols=U[b]|(set() if b==2 else set())
                if not cols: continue
                nc,err=nearest(px,cols)
                if best is None or err.sum()<best[0]: best=(err.sum(),b,nc)
            choice[(x,y,i)]=(best[1],best[0])
    # render composite of recoloured cell
for k,v in sorted(choice.items(), key=lambda kv:-kv[1][1])[:10]: print(k,v)
pickle.dump((U,restbank,choice),open('recolor.pkl','wb'))
