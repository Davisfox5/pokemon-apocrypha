"""Survey how each outdoor element (trees, tall grass, water, cliffs, ledges, grass, dirt) is drawn
across engine checkouts, cluster near-identical versions, and write one comparison board per element.
Usage: python3 survey_elements.py OUT_DIR"""
import sys, json, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent),str(HERE.parents[2]/'hoennconv')]
import map_gate as G
import numpy as np
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw
OUT=Path(sys.argv[1]); OUT.mkdir(parents=True,exist_ok=True)
# Worktrees to survey: (label, engine checkout). Edit to match the open PR branches.
SRC=[('#39','/home/user/engine-pr39'),('#57','/home/user/wt-claude-project-thread-ejp431'),('#34','/home/user/wt-claude-route29-hgss-decoded'),
     ('#7','/home/user/wt-codex-new-bark-layout-adjustments'),('#44 chain','/home/user/wt-codex-routes3839-complete'),('#20','/home/user/wt-codex-goldenrod-city'),
     ('#56','/home/user/wt-claude-slowpoke-well'),('F chain','/home/user/wt-claude-dragons-den'),('#48 chain','/home/user/wt-claude-route-7'),('#45','/home/user/wt-codex-pallet-native-revision')]
def mbnames(p):
    names,n={},0
    for line in (Path(p)/'include/constants/metatile_behaviors.h').read_text().split('enum',1)[1].split('}',1)[0].splitlines():
        m=re.match(r'\s*(MB_\w+)\s*(?:=\s*(\w+))?\s*,',line)
        if m:
            if m.group(2): n=int(m.group(2),0)
            names[n]=m.group(1); n+=1
    return names
KEYS=('Johto','Cherrygrove','Violet','NewBark','Goldenrod','Olivine','Cianwood','Mahogany','Blackthorn','LakeOfRage','Azalea','Ecruteak','Route4','Kanto','Pallet','Route3')
seen=set(); units={}  # el -> list of (map, src, img np)
def add(el,name,src,arr):
    units.setdefault(el,[]).append(dict(map=name,src=src,img=arr)); (OUT/'units').mkdir(exist_ok=True); Image.fromarray(arr.clip(0,255).astype(np.uint8)).save(OUT/'units'/f'{el}_{name}.png')
for label,p in SRC:
    eng=G.Engine(Path(p)); mb=mbnames(p); cache={}
    for name,m in sorted(eng.by_name.items()):
        if m.get('map_type') not in ('MAP_TYPE_ROUTE','MAP_TYPE_TOWN','MAP_TYPE_CITY') or name in seen: continue
        if not any(k in name for k in KEYS) or name.startswith('MapProof') or 'Preview' in name: continue
        seen.add(name)
        lay=eng.layouts[m['layout']]; raw=eng.grid(lay); g=raw&1023; col=(raw>>10)&3; ts=eng.tileset(lay)
        def px(mid):
            if mid not in cache:
                part,idx=(1,mid-512) if mid>=512 else (0,mid)
                cache[mid]=np.asarray(ts.render(int(mid)).convert("RGB")).astype(np.int16) if idx<len(ts.blocks[part]) else None
            return cache[mid]
        if any(px(v) is None for v in np.unique(g)): print('skip broken',name); continue
        img=np.asarray(G.native_image(eng,m).convert('RGB')).astype(np.int16)
        if ((img[...,0]>240)&(img[...,1]<20)&(img[...,2]>240)).mean()>0.002: print('skip magenta',name); continue
        bn=np.vectorize(lambda v:mb.get(int(G.behavior(ts,int(v)) or 0),''))(g)
        mean={mid:px(mid).reshape(-1,3).mean(0) for mid in np.unique(g)}
        R,Gc,B=[np.vectorize(lambda v,i=i:mean[v][i])(g) for i in range(3)]
        def interior(mk,n=4):
            for y in range(g.shape[0]-n+1):
                for x in range(g.shape[1]-n+1):
                    if mk[y:y+n,x:x+n].all(): return img[y*16:(y+n)*16,x*16:(x+n)*16]
        def edgewin(mk,w=8,h=6):
            e=mk&~(np.roll(mk,1,0)&np.roll(mk,-1,0)&np.roll(mk,1,1)&np.roll(mk,-1,1))
            best,b=-1,(0,0)
            for y in range(max(1,g.shape[0]-h+1)):
                for x in range(max(1,g.shape[1]-w+1)):
                    s=e[y:y+h,x:x+w].sum()
                    if s>best: best,b=s,(x,y)
            x,y=b; return img[y*16:(y+h)*16,x*16:(x+w)*16]
        sets={'tall_grass':bn=='MB_TALL_GRASS','sea_water':np.isin(bn,['MB_OCEAN_WATER','MB_DEEP_WATER']),
              'ground_grass':(col==0)&(bn=='MB_NORMAL')&(Gc>R*1.15)&(Gc>B),
              'dirt_path':(col==0)&(bn=='MB_NORMAL')&(R>Gc)&(R>B*1.1)}
        for el,mk in sets.items():
            a=interior(mk)
            if a is None:
                a2=interior(mk,2)
                if a2 is not None: a=np.tile(a2,(2,2,1))
            if a is not None and a.shape==(64,64,3): add(el,name,label,a)
        pw=bn=='MB_POND_WATER'
        if pw.sum()>=6: add('pond_water',name,label,edgewin(pw))
        # ledges: most common south ledge as 3-wide strip with the cell above/below
        mk=bn=='MB_JUMP_SOUTH'
        if mk.sum()>=3:
            ys,xs=np.where(mk&np.roll(mk,1,1)&np.roll(mk,-1,1))
            if len(ys):
                y,x=ys[len(ys)//2],xs[len(xs)//2]
                if 1<=y<g.shape[0]-1 and 1<=x<g.shape[1]-1: add('ledges',name,label,img[(y-1)*16:(y+2)*16,(x-1)*16:(x+2)*16])
        # trees: 4x4 cell crop fully inside collision greenery
        tr=(col!=0)&(Gc>R*1.1)&(Gc>B)
        ok=None
        for y in range(g.shape[0]-3):
            for x in range(g.shape[1]-3):
                if tr[y:y+4,x:x+4].all(): ok=(x,y);break
            if ok: break
        if ok: x,y=ok; add('trees',name,label,img[y*16:y*16+64,x*16:x*16+64])
        # rock: 8x6 window with most rock edge (corner-rich)
        cm=np.stack([R,Gc,B],-1)
        rk=(col!=0)&(bn=='MB_NORMAL')&(np.abs(cm-np.array([196,150,112])).sum(-1)<70)
        if rk.sum()>=12:
            up=np.roll(rk,1,0);dn=np.roll(rk,-1,0);lf=np.roll(rk,1,1);rt=np.roll(rk,-1,1)
            corner=rk&((up^dn)&(lf^rt))
            best,b=-1,(0,0)
            for y in range(max(1,g.shape[0]-5)):
                for x in range(max(1,g.shape[1]-7)):
                    s_=corner[y:y+6,x:x+8].sum()*3+rk[y:y+6,x:x+8].sum()*0.2
                    if s_>best: best,b=s_,(x,y)
            x,y=b
            if best>=6: add('rock',name,label,img[y*16:y*16+96,x*16:x*16+128])
def dist(a,b,shift=False):
    if a.shape!=b.shape: return 999
    if not shift: return np.abs(a-b).mean()
    A=a[:32,:32]; return min(np.abs(A-b[sy:sy+32,sx:sx+32]).mean() for sy in (0,16,32) for sx in (0,16,32))
TH={'trees':14,'tall_grass':5,'ground_grass':6,'dirt_path':6,'sea_water':8}
summary={}
for el,us in units.items():
    cl=[]
    for u in us:
        for c in cl:
            if el not in ('rock','pond_water') and dist(c['img'],u['img'],el in ('trees','tall_grass','sea_water','ground_grass','dirt_path'))<TH.get(el,12): c['maps'].append(u['map']); break
        else: cl.append(dict(img=u['img'],maps=[u['map']]))
    cl.sort(key=lambda c:-len(c['maps']))
    s=4 if el not in ('rock','pond_water') else 2
    h,w=cl[0]['img'].shape[:2]; cw,ch=max(w*s,260),h*s; cols=4 if el not in ('rock','pond_water') else 3
    rows=(len(cl)+cols-1)//cols
    sheet=Image.new('RGB',(cols*(cw+24)+24,rows*(ch+64)+24),(28,28,32)); d=ImageDraw.Draw(sheet)
    for i,c in enumerate(cl):
        X=24+(i%cols)*(cw+24); Y=24+(i//cols)*(ch+64)
        im=Image.fromarray(c['img'].clip(0,255).astype(np.uint8)); sheet.paste(im.resize((im.width*s,im.height*s),Image.NEAREST),(X,Y+50))
        d.text((X,Y),f"{chr(65+i)}  {len(c['maps'])} map(s)",fill=(255,255,255))
        t=', '.join(c['maps']); d.text((X,Y+14),t[:44],fill=(190,190,190)); d.text((X,Y+28),t[44:88]+('...' if len(t)>88 else ''),fill=(190,190,190))
    sheet.save(OUT/f'{el}.png'); summary[el]=[dict(variant=chr(65+i),maps=c['maps']) for i,c in enumerate(cl)]
json.dump(summary,open(OUT/'variants.json','w'),indent=1)
for el,v in summary.items(): print(el,len(v),[len(x['maps']) for x in v])
