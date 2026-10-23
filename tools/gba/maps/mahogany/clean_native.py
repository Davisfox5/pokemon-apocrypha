"""Local polish of the committed Mahogany native source; never runs a layout generator.

Input must be the preserved b37519e Mahogany draft. The HGSS terrain, material
boundaries, object silhouettes, palettes and C06 remain intact. Only inward-facing
one-pixel architecture contours are strengthened, using each tile's existing ramp.
Outputs are confined to Mahogany's private tileset pair and native layout.
"""
from __future__ import annotations
import hashlib, json, struct, sys
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_convert as C
import build as B

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
OUT = ART / 'evidence/clean'
BASE = 'b37519e732ddc7d13f4412a796419308583d6bc8'
FEATURES = ('souvenir_shop', 'east_house', 'gym', 'gate', 'tower_west', 'tower_east')

def flipped(a, f):
    if f & 1: a = a[:, ::-1]
    if f & 2: a = a[::-1]
    return a

def canonical(a):
    choices = [flipped(a, f).tobytes() for f in range(4)]
    f = min(range(4), key=lambda n: choices[n])
    return choices[f], f

def read(g):
    dirs = [g/'data/tilesets/primary/mahogany', g/'data/tilesets/secondary/mahogany_town']
    pt, pm, pa = C.tileset(dirs[0]); st, sm, sa = C.tileset(dirs[1])
    pats = pt[:512] + st
    metas = {i: (list(map(int,m)), int(a)) for i,(m,a) in enumerate(zip(pm,pa))}
    metas.update({512+i: (list(map(int,m)), int(a)) for i,(m,a) in enumerate(zip(sm,sa))})
    pals = np.array([B.read_pal(dirs[b>=6]/'palettes'/f'{b:02}.pal') for b in range(16)])
    grid = np.frombuffer((g/'data/layouts/MahoganyTown/map.bin').read_bytes(),'<u2').reshape(32,32).copy()
    return dirs, pats, metas, pals, grid

def main(g):
    for rel in ['data/layouts/MahoganyTown/map.bin',
                'data/tilesets/primary/mahogany/tiles.png',
                'data/tilesets/primary/mahogany/metatiles.bin',
                'data/tilesets/secondary/mahogany_town/tiles.png',
                'data/tilesets/secondary/mahogany_town/metatiles.bin',
                'data/tilesets/secondary/mahogany_town/metatile_attributes.bin']:
        original=subprocess.check_output(['git','-C',str(g),'show',BASE+':'+rel])
        if (g/rel).read_bytes()!=original:
            raise SystemExit('Native source differs from the preserved draft; edit it directly. Refusing to replay: '+rel)
    OUT.mkdir(parents=True, exist_ok=True)
    before = C.decode(g)[0]
    Image.fromarray(before).save(OUT/'before.png')
    dirs, pats, metas, pals, grid = read(g)
    owners = np.load(ART/'source/convert/layers.npz',allow_pickle=True)['owner']
    # An inward contour changes no silhouette or receiving ground. The lit rim
    # immediately inside it and every original material texture remain visible.
    contour = np.zeros((512,512),bool)
    for name in FEATURES:
        m = owners == name
        interior = np.ones_like(m)
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
            neighbor = np.roll(m,(dy,dx),(0,1))
            if dy<0: neighbor[-1]=False
            if dy>0: neighbor[0]=False
            if dx<0: neighbor[:,-1]=False
            if dx>0: neighbor[:,0]=False
            interior &= neighbor
        contour |= m & ~interior
    new = []
    changed = np.zeros((512,512),bool)
    patterns = {bytes(64):0}
    entries = {}
    for y,x in np.ndindex(32,32):
        mid = int(grid[y,x]&1023)
        old, attr = metas[mid]
        ents=[]
        for i,e in enumerate(old):
            q=i%4; yy=y*16+(q//2)*8; xx=x*16+(q%2)*8
            ix=flipped(np.array(pats[e&1023]).copy(), (e>>10)&3).copy()
            bank=e>>12
            mask=contour[yy:yy+8,xx:xx+8] & (ix>0) if i>=4 else np.zeros((8,8),bool)
            for py,px in zip(*np.where(mask)):
                c=pals[bank,ix[py,px]].astype(float)
                ramp=pals[bank,1:].astype(float)
                # Material-coloured edge, not an unrelated black/green alias.
                target=c*.58
                cost=((ramp-target)**2).sum(-1)
                dark=int(cost.argmin())+1
                if np.dot(pals[bank,dark],[.21,.72,.07]) < np.dot(c,[.21,.72,.07])*.86:
                    ix[py,px]=dark
                    changed[yy+py,xx+px]=True
            key,f=canonical(ix)
            if key not in patterns: patterns[key]=len(patterns)
            ents.append(patterns[key]|(f<<10)|(bank<<12))
        entries[(x,y)]=(ents,attr)
    n=len(patterns)
    if n>1008: raise SystemExit(f'Contour needs {n}/1008 tiles; do not sacrifice terrain to fit.')
    pat=np.zeros((n,8,8),np.uint8)
    for key,i in patterns.items():pat[i]=np.frombuffer(key,np.uint8).reshape(8,8)
    # Preserve existing metatile IDs where possible; append only cell-specific
    # variants. Untouched maps never use this private pair.
    variants=defaultdict(Counter)
    for y,x in np.ndindex(32,32):
        ents,attr=entries[x,y]; variants[int(grid[y,x]&1023)][tuple(ents)+(attr,)]+=1
    used_ids={}
    result={}
    for mid,counts in variants.items():
        preferred=counts.most_common(1)[0][0]; result[mid]=(list(preferred[:8]),preferred[8]); used_ids[mid,preferred]=mid
    # Include border cells and currently unreferenced native entries, remapped
    # from their original pixels so their source remains reviewable.
    for mid,(old,attr) in metas.items():
        if mid in result:continue
        ents=[]
        for e in old:
            key,f=canonical(flipped(np.array(pats[e&1023]),(e>>10)&3))
            if key not in patterns:
                patterns[key]=len(patterns)
                pat=np.concatenate([pat,np.frombuffer(key,np.uint8).reshape(1,8,8)])
            ents.append(patterns[key]|(f<<10)|((e>>12)<<12))
        result[mid]=(ents,attr)
    next_id=max(512,max(result)+1)
    for y,x in np.ndindex(32,32):
        ents,attr=entries[x,y]; key=tuple(ents)+(attr,); original=int(grid[y,x]&1023)
        if (original,key) not in used_ids:
            used_ids[original,key]=next_id;result[next_id]=(ents,attr);next_id+=1
        grid[y,x]=(int(grid[y,x])&~1023)|used_ids[original,key]
    if len(pat)>1008 or next_id>1024: raise SystemExit(('native budget exceeded',len(pat),next_id))
    for part,d in enumerate(dirs):
        ps=pat[:512] if part==0 else pat[512:]
        buf=np.zeros((((len(ps)+15)//16)*8,128),np.uint8)
        for i,p in enumerate(ps):buf[i//16*8:i//16*8+8,i%16*8:i%16*8+8]=p
        im=Image.fromarray(buf,'P');im.putpalette([v for i in range(16) for v in (i*17,)*3]+[0]*720);im.save(d/'tiles.png',bits=4)
        ids=range(0,len(metas.keys() & set(range(512)))) if part==0 else range(512,next_id)
        (d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*result[i][0]) for i in ids))
        (d/'metatile_attributes.bin').write_bytes(b''.join(struct.pack('<H',result[i][1]) for i in ids))
    (g/'data/layouts/MahoganyTown/map.bin').write_bytes(grid.astype('<u2').tobytes())
    after=C.decode(g)[0]
    actual=(after!=before).any(-1)
    assert not (actual & ~contour).any(), 'Polish escaped original architecture silhouettes'
    assert not (actual & (owners=='pokemon_center')).any(), 'C06 changed'
    Image.fromarray(after).save(OUT/'native.png')
    for name in FEATURES:
        m=owners==name;ys,xs=np.where(m);box=(max(0,xs.min()-8),max(0,ys.min()-8),min(512,xs.max()+9),min(512,ys.max()+9))
        b=Image.fromarray(before).crop(box);a=Image.fromarray(after).crop(box)
        out=Image.new('RGB',(b.width*2,b.height+20),(28,34,38));out.paste(b,(0,20));out.paste(a,(b.width,20));draw=ImageDraw.Draw(out);draw.text((3,3),'Previous',fill='white');draw.text((b.width+3,3),'Clean native',fill='white');out.resize((out.width*3,out.height*3),Image.Resampling.NEAREST).save(OUT/f'{name}-review.png')
    report=dict(base_engine=BASE,tiles=len(pat),limit=1008,changed_pixels=int(actual.sum()),
                changed_by_feature={n:int((actual&(owners==n)).sum()) for n in FEATURES},
                terrain_pixels_changed=0,center_pixels_changed=0,palettes_changed=False,
                geometry='Original silhouettes, material grid, cliff heights, roots and traversal retained')
    (OUT/'polish.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__': main(Path(sys.argv[1]).resolve())
