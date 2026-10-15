"""Lossless palette-index alignment across hardware tiles.
A palette index is a label, not a color: swapping labels and palette entries
preserves exact RGB while allowing identical pixel patterns to share storage.
"""
import numpy as np
from claude_cherrygrove.pixel import Palette


class Probe:
    def __init__(self):self.raw={}
    def tile(self,bank,arr,pos=None):
        variants=[arr,arr[:,::-1],arr[::-1],arr[::-1,::-1]]
        key=min(a.tobytes() for a in variants)
        self.raw.setdefault(bank,{})[key]=np.frombuffer(key,np.uint8).reshape(8,8)
        return 0
    def metatile(self,entries,attr):return 0


def optimize(probe, fixed=()):
    arrays={k:np.array([[a,a[:,::-1],a[::-1],a[::-1,::-1]] for a in v.values()]) for k,v in probe.raw.items()}
    maps={k:np.arange(16,dtype=np.uint8) for k in arrays}
    def keys(k,m):
        return {min(a.tobytes() for a in row) for row in m[arrays[k]]}
    sets={k:keys(k,maps[k]) for k in arrays}
    before=len(set().union(*sets.values()))
    for iteration in range(6):
        changed=False
        for k in sorted(arrays,key=lambda b:len(sets[b])):
            if k in fixed:continue
            others=set().union(*(s for b,s in sets.items() if b!=k))
            score=len(others|sets[k]);best=maps[k];bestset=sets[k]
            for a in range(1,16):
                for b in range(a+1,16):
                    trial=maps[k].copy();trial[a],trial[b]=trial[b],trial[a]
                    trialset=keys(k,trial);n=len(others|trialset)
                    if n<score:score=n;best=trial;bestset=trialset
            if not np.array_equal(best,maps[k]):
                maps[k]=best;sets[k]=bestset;changed=True
        if not changed:break
    after=len(set().union(*sets.values()))
    # Pair swaps cannot cross a plateau when a repeated shape needs several
    # labels changed together. Match entire tile patterns, keeping transparency
    # fixed, and propose the corresponding bijection in one step.
    def signature(a):
        labels={0:0};out=[]
        for v in a.ravel():
            v=int(v)
            if v not in labels:labels[v]=len(labels)
            out.append(labels[v])
        return bytes(out)
    for iteration in range(6):
        changed=False
        for k in sorted(arrays,key=lambda b:len(sets[b])):
            if k in fixed:continue
            others=set().union(*(s for b,s in sets.items() if b!=k))
            patterns={}
            for raw in others:
                a=np.frombuffer(raw,np.uint8)
                patterns.setdefault(signature(a),[]).append(a)
            candidates=set()
            for variants in arrays[k]:
                for a in variants:
                    for target in patterns.get(signature(a),[]):
                        fixed=dict(zip(map(int,a.ravel()),map(int,target)))
                        fixed[0]=0
                        trial=maps[k].copy();available=set(range(16))-set(fixed.values())
                        for source,value in fixed.items():trial[source]=value
                        pending=[]
                        for source in range(16):
                            if source in fixed:continue
                            old=int(maps[k][source])
                            if old in available:trial[source]=old;available.remove(old)
                            else:pending.append(source)
                        for source,value in zip(pending,sorted(available)):trial[source]=value
                        candidates.add(trial.tobytes())
            score=len(others|sets[k]);best=maps[k];bestset=sets[k]
            for raw in sorted(candidates):
                trial=np.frombuffer(raw,np.uint8);trialset=keys(k,trial)
                n=len(others|trialset)
                if n<score:score=n;best=trial.copy();bestset=trialset
            if not np.array_equal(best,maps[k]):
                maps[k]=best;sets[k]=bestset;changed=True
        if not changed:break
    after=len(set().union(*sets.values()))
    return maps,{'unique_tiles_before':before,'unique_tiles_after':after,'saved_tiles':before-after,'palette_indices':{str(k):v.tolist() for k,v in maps.items()}}


def apply_palettes(pals,maps):
    for bank,lut in maps.items():
        assert sorted(map(int,lut))==list(range(16)) and lut[0]==0
        old=pals[bank].gba();colors=[None]*15
        for i in range(1,16):colors[int(lut[i])-1]=old[i]
        pals[bank]=Palette(bank,colors,[str(i) for i in range(15)])
        assert np.array_equal(np.array(pals[bank].gba())[lut],np.array(old))
