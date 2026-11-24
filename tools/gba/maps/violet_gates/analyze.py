import numpy as np, sys
from PIL import Image
from ts import TS
S='/tmp/claude-0/-home-user/85ee60ab-0025-575e-abae-bfbdaa5ee7ac/scratchpad/'
B=TS('/home/user/pokeemerald-expansion'); O=TS(S+'old')
b=np.array(Image.open(S+'violet-base.png')).astype(int); o=np.array(Image.open(S+'violet-old.png')).astype(int)
d=(b!=o).any(-1).reshape(72,16,80,16).sum((1,3))
win=np.zeros((72,80),bool); win[18:38,0:12]=1; win[46:66,64:80]=1; win[0:3,33:47]=1; win[70:72,:]=1
def fam(c):
    r,g,bb=c[...,0],c[...,1],c[...,2]
    return np.where(g>r+20,1,np.where((r-bb>40),2,0))
fc=(fam(b)!=fam(o)).reshape(72,16,80,16).sum((1,3))
EXTRA={(7,29),(72,51),(73,51),(72,57),(71,59)}
R=sorted(EXTRA|set((x,y) for y,x in np.argwhere((d>=45)&win))|set((x,y) for x in range(0,7) for y in range(25,32))|set((x,y) for x in range(73,80) for y in range(53,60)))
# base library of layer tiles as rendered
lib={0:{},1:{}}  # lower/upper: key bytes -> entry
for m in set(int(v)&1023 for v in B.w.ravel()):
    E=B.ents(m)
    for i,e in enumerate(E):
        lw=i<4
        for fl in (0,1024,2048,3072):
            ee=(e&~3072)|((e^fl)&3072)
            k=B.rgba(ee,lw).tobytes()
            lib[0 if lw else 1].setdefault(k,ee)
libarr={l:[(np.frombuffer(k,int).reshape(8,8,4),e) for k,e in lib[l].items()] for l in (0,1)}
new={0:[],1:[]}; stats={'exact':0,'snap':0,'new':0,'blank':0}
plan={}
for (x,y) in R:
    E=O.ents(int(O.w[y,x])); out=[]
    for i,e in enumerate(E):
        lw=i<4; r=O.rgba(e,lw)
        if not lw and (r[...,3]==0).all(): out.append(('e',0)); stats['blank']+=1; continue
        k=r.tobytes()
        if k in lib[0 if lw else 1]: out.append(('e',lib[0 if lw else 1][k])); stats['exact']+=1; continue
        best=None
        for t,ee in libarr[0 if lw else 1]:
            diff=((t!=r).any(-1)).sum()
            if best is None or diff<best[0]: best=(diff,ee,t[...,:3])
        if best[0]<=6 and (x,y) not in EXTRA: out.append(('e',best[1])); stats['snap']+=1; continue
        out.append(('n',r)); stats['new']+=1
        L=new[0 if lw else 1]
        if not any(((q!=r).any(-1)).sum()==0 or ((q[:,::-1]!=r).any(-1)).sum()==0 or ((q[::-1]!=r).any(-1)).sum()==0 or ((q[::-1,::-1]!=r).any(-1)).sum()==0 for q in L): L.append(r)
    plan[(x,y)]=out
print(len(R),stats,'unique new lower',len(new[0]),'upper',len(new[1]))
import pickle; pickle.dump((R,plan,new),open('plan.pkl','wb'))
