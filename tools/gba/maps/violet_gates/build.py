"""Install the Violet gatehouse exteriors (as at fork 68ef781f) into base Violet, recolouring the lake island."""
import pickle,json,struct,sys,numpy as np
from pathlib import Path
from PIL import Image
from ts import TS
S='/tmp/claude-0/-home-user/85ee60ab-0025-575e-abae-bfbdaa5ee7ac/scratchpad/'
ENG=Path(sys.argv[1]); BASE=TS(str(ENG)); O=TS(S+'old')
R,plan,_=pickle.load(open('plan.pkl','rb')); mg=pickle.load(open('merges2.pkl','rb'))
U,restbank,choice=pickle.load(open('recolor.pkl','rb'))
Rs=set(R); ISL=[(x,y) for x in range(47,51) for y in range(22,27)]; Is=set(ISL)
GATEBANK_OLD=10; GB=2
mt=[list(map(list,BASE.mt[0])),list(map(list,BASE.mt[1]))]
attr=[list(BASE.attr[0]),list(BASE.attr[1])]
sheets=[BASE.sheets[0].copy(),BASE.sheets[1].copy()]
pals={b:BASE.pals[b].copy() for b in range(13)}
w=BASE.w.copy()
def ents(m): m&=1023; return mt[0][m] if m<512 else mt[1][m-512]
# 1) invisible lower merges, in place
for part in (0,1):
    for E in mt[part]:
        for q in range(4):
            t=E[q]&1023
            if t in mg: a_,fl_=mg[t]; E[q]=(E[q]&0xF000)|a_|(((E[q]&3072)^fl_))
# 2) references kept
keep=set(); pidx={b:set() for b in range(13)}
def note(e,lower):
    keep.add(e&1023); i=set(np.unique(tileidx(e&1023)).tolist())
    if not lower: i.discard(0)
    pidx[e>>12].update(i)
def tileidx(t):
    sh=sheets[t>=512]; i=t-512 if t>=512 else t; return sh[(i//16)*8:(i//16)*8+8,(i%16)*8:(i%16)*8+8]
for y in range(72):
  for x in range(80):
    if (x,y) in Rs or (x,y) in Is: continue
    for i,e in enumerate(ents(int(w[y,x]))): note(e,i<4)
for out in plan.values():
    for i,(k,v) in enumerate(out):
        if k=='e' and v: note(v,i<4)
assert not pidx[GB]-{0}, ('bank 2 still referenced',pidx[GB])
pals[GB]=O.pals[GATEBANK_OLD].copy(); pidx[GB]=set(range(16))
free_tiles=[t for t in range(1,1008) if t not in keep]
print('free tile slots',len(free_tiles))
# palette: add colours of U into free indices
def colour_index(b,c,add=True):
    c=np.array(c)
    for k in range(1,16):
        if k in pidx[b] and (pals[b][k]==c).all(): return k
    if not add: return None
    for k in range(1,16):
        if k not in pidx[b]:
            pals[b][k]=c; pidx[b].add(k); return k
    raise SystemExit(f'bank {b} full')
for b in range(13):
    if b==GB: continue
    for c in sorted(U[b]): colour_index(b,c)
# 3) tile allocator with dedupe
store={}
def put_tile(idx):
    for fl,v in ((0,idx),(1024,idx[:,::-1]),(2048,idx[::-1]),(3072,idx[::-1,::-1])):
        k=v.tobytes()
        if k in store: return store[k],fl
    if not free_tiles: raise SystemExit('out of tiles')
    t=free_tiles.pop(0); store[idx.tobytes()]=t
    sh=sheets[t>=512]; i=t-512 if t>=512 else t
    sh[(i//16)*8:(i//16)*8+8,(i%16)*8:(i%16)*8+8]=idx
    return t,0
for t in keep: store.setdefault(tileidx(t).tobytes(),t)
def rgb_to_idx(r,b,lower):
    C=pals[b]; m=r[...,3]>0; idx=np.zeros((8,8),np.uint8)
    for yy in range(8):
        for xx in range(8):
            if not m[yy,xx]: continue
            px=r[yy,xx,:3]; ks=[k for k in sorted(pidx[b]) if k] 
            k=min(ks,key=lambda k:((C[k]-px)**2).sum()); idx[yy,xx]=k
    return idx
gate=set(tuple(int(c) for c in p) for p in O.pals[GATEBANK_OLD][1:])
newmt=[]
def add_mt(E,a):
    for n,(E2,a2) in enumerate(newmt):
        if E2==E and a2==a: return 512+len(mt[1])+n
    newmt.append((E,a)); return 512+len(mt[1])+len(newmt)-1
# 4) gate cells
for (x,y) in R:
    oe=O.ents(int(O.w[y,x])); E=[]
    for i,(k,v) in enumerate(plan[(x,y)]):
        if k=='e': E.append(v); continue
        e=oe[i]
        if e>>12==GATEBANK_OLD:
            t,fl=put_tile(O.idx(e).astype(np.uint8)); E.append(t|fl|(GB<<12))
        else:
            r=v; cs=set(tuple(int(c) for c in p[:3]) for p in r.reshape(-1,4) if p[3])
            b=min((b for b in range(13) if b!=GB and cs<=set(tuple(int(c) for c in pals[b][k]) for k in pidx[b] if k)),key=lambda b:0,default=None)
            if b is None: raise SystemExit(f'no bank for tile at {(x,y,i)}')
            t,fl=put_tile(rgb_to_idx(r,b,i<4)); E.append(t|fl|(b<<12))
    m=int(O.w[y,x])&1023; a=O.attr[m>=512][m-512 if m>=512 else m]
    w[y,x]=(int(O.w[y,x])&0xFC00)|add_mt(E,a)
# 4b) close the gap under each gate: the first tree row under the ledge moves up 8 px
def cell(x,y):
    m=int(w[y,x])&1023
    if m>=512+len(mt[1]): E,a=newmt[m-512-len(mt[1])]; return list(E),a
    return list(ents(m)), attr[m>=512][m-512 if m>=512 else m]
def idx_of(e):
    t=tileidx(e&1023)
    if e&1024: t=t[:,::-1]
    if e&2048: t=t[::-1]
    return t
def rgba_of(e,lower):
    i=idx_of(e); c=pals[e>>12][i].astype(int)
    out=np.zeros((8,8,4),int); out[...,:3]=c; out[...,3]=255
    if not lower: out[i==0]=0
    return out
LAWNBANK=0
def bank_for(cols,prefer):
    for b in prefer:
        have=set(tuple(int(v) for v in pals[b][k]) for k in pidx[b] if k)
        if len([c for c in cols if c not in have])<=sum(1 for k in range(1,16) if k not in pidx[b]):
            for c in cols: colour_index(b,c)
            return b
    raise SystemExit(('no bank',cols))
def new_tile_rgba(r,prefer,lower):
    cols=set(tuple(int(v) for v in p[:3]) for p in r.reshape(-1,4) if p[3])
    b=bank_for(cols,prefer); t,fl=put_tile(rgb_to_idx(r,b,lower)); return t|fl|(b<<12)
def is_tree_lower(e): return (e>>12)==3
def set_cell(x,y,E,a):
    w[y,x]=(int(w[y,x])&0xFC00)|add_mt(E,a)
before=len(free_tiles)
LAST=[cell(34,2)[0],cell(35,2)[0]]   # a tree's last few rows, as the end of a band draws them
for cols,L in ((range(0,6),31),(range(74,80),59)):
    T=L+1
    snap={(c,r):cell(c,r) for c in cols for r in (L,T,T+1,T+2)}
    for c in cols:
        EL,aL=snap[(c,L)]; ET,aT=snap[(c,T)]; ER,aR=snap[(c,T+1)]; EN,aN=snap[(c,T+2)]
        # ledge row: bottom half takes the crown's first tile row; the ledge's last rows go under it, on the lawn
        nl=list(EL)
        for q in (2,3):
            g=rgba_of(EL[4+q],False)
            if (g[...,3]>0).any():
                lo=rgba_of(EL[q],True); m=g[...,3]>0; lo[m]=g[m]
                nl[q]=new_tile_rgba(lo,[0,12,1,4,10,7,5,6,9],True)
            nl[4+q]=ET[4+q-2]
        set_cell(c,L,nl,aL)
        # crown row: crown's second tile row, then the trunk row's first
        nt=list(ET)
        nt[4],nt[5]=ET[6],ET[7]
        for q in (0,1):
            if is_tree_lower(ER[q]): nt[2+q]=ER[q]
            nt[6+q]=ER[4+q]
        set_cell(c,T,nt,aT)
        # trunk row: its second tile row, then whatever of the trunk ran on into the next row
        nr=[EL[0],EL[1],EL[2],EL[3],0,0,0,0]     # lawn of the same phase (two rows up)
        for q in (0,1):
            if is_tree_lower(ER[2+q]): nr[q]=ER[2+q]
            nr[4+q]=ER[6+q]
            nr[6+q]=LAST[c%2][4+q]
        set_cell(c,T+1,nr,aR)
        # the next row starts a tree of its own
        nn=list(ET)
        for q in (0,1):
            ov=rgba_of(LAST[c%2][6+q],False)
            if (ov[...,3]>0).any():
                cr=rgba_of(ET[4+q],False); m=cr[...,3]>0; ov[m]=cr[m]
                nn[4+q]=new_tile_rgba(ov,[3],False)
        set_cell(c,T+2,nn,aN)
print('gap closing used tiles',before-len(free_tiles))
# 4c) trees behind Sprout Tower's spire (columns 38-41, rows 0-2), the spire in front
LAWN=set(tuple(int(v) for v in c) for c in [(104,208,152),(104,200,152),(88,176,136),(96,192,144)])
def lawn_only(e):
    r=rgba_of(e,True); return set(tuple(int(v) for v in p[:3]) for p in r.reshape(-1,4))<=LAWN
before=len(free_tiles)
for r in (0,1,2):
    for c in (38,39,40,41):
        TE,ta=cell(34+c%2,r); CE,ca=cell(c,r); E=list(CE); touched=False
        for q in range(4):
            if not lawn_only(CE[q]): continue            # the tower itself: stays in front
            tl=rgba_of(TE[q],True); tu=rgba_of(TE[4+q],False); vu=rgba_of(CE[4+q],False)
            has_tree=(tu[...,3]>0).any() or not lawn_only(TE[q])
            if not has_tree: continue
            touched=True
            if not (vu[...,3]>0).any():
                E[q]=TE[q]; E[4+q]=TE[4+q]
            else:
                lo=rgba_of(CE[q],True) if lawn_only(TE[q]) else tl
                m=tu[...,3]>0; lo=lo.copy(); lo[m]=tu[m]
                E[q]=new_tile_rgba(lo,[3,0,12,4,10,7,1,5,6,9],True)
        if touched:
            w[r,c]=(int(w[r,34+c%2])&0xFC00)|add_mt(E,ta if not any((rgba_of(CE[4+q],False)[...,3]>0).any() for q in range(4)) else ca)
print('spire trees used tiles',before-len(free_tiles))
# 5) island recolour, then merge its closest tiles (visible pixels only) until it fits
print('slots left for island',len(free_tiles))
items=[]
for (x,y) in ISL:
    be=BASE.ents(int(BASE.w[y,x]))
    for i,e in enumerate(be):
        r=BASE.rgba(e,i<4)
        if i>=4 and not (r[...,3]>0).any(): items.append(dict(k=(x,y,i),b=None)); continue
        vis=np.ones((8,8),bool) if i>=4 else (BASE.idx(be[i+4])==0)
        b_=choice[(x,y,i)][0]; ix=rgb_to_idx(r,b_,i<4)
        # a pixel whose nearest colour in this bank is far off takes its closest-matching neighbour's colour
        P=pals[b_].astype(int); err=np.abs(P[ix]-r[...,:3]).sum(-1)*(r[...,3]>0)
        for yy,xx in np.argwhere(err>150):
            nb=[(abs(P[ix[y2,x2]]-P[ix[yy,xx]]).sum(),ix[y2,x2]) for y2,x2 in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)) if 0<=y2<8 and 0<=x2<8 and ix[y2,x2] and err[y2,x2]<=150]
            if nb: ix[yy,xx]=max(set(v for _,v in nb),key=[v for _,v in nb].count)
        items.append(dict(k=(x,y,i),b=b_,idx=ix,vis=vis))
FL=[(0,lambda v:v),(1024,lambda v:v[:,::-1]),(2048,lambda v:v[::-1]),(3072,lambda v:v[::-1,::-1])]
def in_store(idx):
    for fl,f in FL:
        if f(idx).tobytes() in store: return True
    return False
groups={}
for it in items:
    if it['b'] is None: continue
    if not it['vis'].any(): it['rep']=('store',tileidx(0).copy()); continue
    key=None
    for fl,f in FL:
        kk=(it['b'],f(it['idx']).tobytes())
        if kk in groups: key=kk;break
    if key is None: key=(it['b'],it['idx'].tobytes()); groups[key]=dict(idx=it['idx'],b=it['b'],uses=[])
    groups[key]['uses'].append(it); it['g']=key
need=[k for k,g in groups.items() if not in_store(g['idx'])]
print('island unique new tiles',len(need))
def use_cost(it,cand):
    # cheapest flip of cand drawn in this use's bank, visible pixels only, by colour distance
    P=pals[it['b']].astype(float); best=None
    for fl,f in FL:
        c=f(cand); m=it['vis']&(c!=it['idx'])
        if it['k'][2]>=4 and ((c==0)!=(it['idx']==0)).any(): 
            d=1e9
        else:
            d=float(np.sqrt(((P[c[m]]-P[it['idx'][m]])**2).sum(-1)).sum()) if m.any() else 0.0
        if best is None or d<best[0]: best=(d,c)
    return best
existing=[tileidx(t).copy() for t in sorted(keep)]
alive=set(need); repl={}
while len(alive)>len(free_tiles):
    best=None
    for k in alive:
        g=groups[k]
        cands=[groups[k2]['idx'] for k2 in alive if k2!=k and k2[0]==k[0] and k2 not in repl]+existing
        for c in cands:
            tot=0
            for it in g['uses']:
                tot+=use_cost(it,c)[0]
                if best is not None and tot>=best[0]: break
            if best is None or tot<best[0]: best=(tot,k,c)
    tot,k,c=best; alive.discard(k); repl[k]=c
    # anything that was merged into k follows it
    for k2,c2 in list(repl.items()):
        if c2 is groups[k]['idx']: repl[k2]=c
    print('island merge cost %.0f'%tot)
for (x,y) in ISL:
    E=[]
    for i in range(8):
        it=[t for t in items if t['k']==(x,y,i)][0]
        if it['b'] is None: E.append(0); continue
        if 'rep' in it: E.append(0|(it['b']<<12)); continue
        idx=it['idx']
        if it['g'] in repl: idx=use_cost(it,repl[it['g']])[1]
        t,fl=put_tile(idx.astype(np.uint8)); E.append(t|fl|(it['b']<<12))
    m=int(BASE.w[y,x])&1023; a=BASE.attr[m>=512][m-512 if m>=512 else m]
    w[y,x]=(int(BASE.w[y,x])&0xFC00)|add_mt(E,a)
print('tiles left',len(free_tiles),'new metatiles',len(newmt))
mt[1]+= [E for E,a in newmt]; attr[1]+=[a for E,a in newmt]
pickle.dump((mt,attr,sheets,pals,w),open('built.pkl','wb'))
