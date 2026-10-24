"""Compile the fresh editable layer atlas through Porytiles, preserving material roles."""
from pathlib import Path
import json,sys,subprocess,os
import numpy as np
from PIL import Image
from build import ART,SRC,EV,N
from collections import Counter

PORY=Path(os.environ.get('PORYTILES','porytiles-legacy'))

def color_fit(bottom,upper,owners):
    green=[(112,216,168),(112,208,168),(96,184,152),(104,200,160),(88,168,136),(80,152,120)]
    path=[(232,208,144),(224,192,144),(224,176,144)]
    soil=[(176,160,112),(152,144,112),(128,136,120)]
    ground=green+path+soil+[(248,248,216),(216,232,200),(200,216,184)]
    stone=[(c[0]>>3<<3,c[1]>>3<<3,c[2]>>3<<3) for c in np.array(Image.open(ART/'reference/textures/cliff01gs.png').convert('RGB')).reshape(-1,3)]
    stone=[c for c,_ in Counter(stone).most_common(11)]+[(112,80,64),(144,96,72),(160,112,80),(88,64,48)]
    mixed=green[:3]+path[:3]+stone[:7]+[(112,80,64),(88,64,48)]
    tree=np.array(Image.open(ART.parent/'cherrygrove-synthesis/refined/tree.png').convert('RGBA'))
    treepal=list(dict.fromkeys(map(tuple,((tree[...,:3]>>3)<<3)[tree[...,3]>0])))
    props=[(56,64,48),(88,72,40),(128,104,64),(176,144,88),(112,48,24),(176,72,32),(216,112,56),(48,80,40),(80,112,48),(128,152,80),(216,224,192),(216,208,152),(152,160,128),(72,120,80),(232,192,120)]
    blend=[(48,80,40),(64,104,48),(88,120,48),(112,136,48),(136,160,56),(72,120,80)]+props[:7]+[(216,208,152),(216,224,192)]
    gym=[(48,48,40),(80,64,40),(112,80,48),(144,112,64),(176,144,88),(208,176,112),(232,208,144),(192,88,24),(232,144,48),(56,72,88),(88,128,144),(80,168,192),(152,208,208),(232,240,216),(176,184,168)]
    pals={0:ground,1:stone,2:treepal,3:props,4:mixed,5:blend,7:gym}
    def fit(a,pal):
        a=a.copy();m=a[...,3]>0;p=np.array(pal,int);c=a[...,:3].astype(int);idx=((c[...,None,:]-p)**2).sum(-1).argmin(-1);a[m,:3]=p[idx[m]];return a
    behaviors=np.load(SRC/'layers.npz')['behavior']
    for ty in range(N*2):
        for tx in range(N*2):
            sl=np.s_[ty*8:ty*8+8,tx*8:tx*8+8];a=bottom[sl];rgb=a[...,:3].astype(int)
            greens=(rgb[...,1]>rgb[...,0]+10)&(rgb[...,1]>rgb[...,2]+10)
            stones=(rgb[...,0]>rgb[...,1]+24)&(rgb[...,1]>rgb[...,2]+12)&(rgb[...,0]<225)
            ledge=int(behaviors[ty//2,tx//2]) in (57,59)
            bank=4 if ledge or (greens.any() and stones.any()) else 1 if stones.sum()>20 else 0
            bottom[sl]=fit(a,pals[bank])
            who=set(owners[sl].ravel())-{''};arch=who&{'souvenir-shop','east-house','gym','pokemon-center','route43-gate'}
            if not arch and who:
                is_tree=all(n.startswith('tree-') for n in who)
                has_tree=any(n.startswith('tree-') for n in who)
                upper[sl]=fit(upper[sl],pals[2 if is_tree else 5 if has_tree else 3])
    # Architecture uses its own coherent ramps. The locked shared Center is
    # exact; it is left for Porytiles to assign across two secondary banks.
    for name,bank in [('souvenir-shop',6),('east-house',6),('gym',7),('route43-gate',10)]:
        m=owners==name;px=upper[...,:3][m];im=Image.fromarray(px.reshape(-1,1,3));q=im.quantize(colors=15,method=Image.Quantize.MEDIANCUT);pp=np.array(q.getpalette(),np.uint8).reshape(-1,3)[:15];pp=(pp>>3)<<3
        if bank in pals:pp=np.array(pals[bank],np.uint8)
        pals[bank]=list(map(tuple,pp));upper[m,:3]=pp[((px.astype(int)[:,None,:]-pp.astype(int))**2).sum(-1).argmin(-1)]
    return bottom,upper,pals

def palfile(path,colors):
    colors=list(dict.fromkeys(tuple(int(v)>>3<<3 for v in c) for c in colors))[:15]
    lines=['-']+[' '.join(map(str,c)) for c in colors];lines += ['-']*(16-len(lines))
    path.write_text('JASC-PAL\n0100\n16\n'+'\n'.join(lines)+'\n')

def main(game):
    z=np.load(SRC/'layers.npz');bottom=z['bottom'].copy();upper=z['upper'].copy();owners=z['owner'];above=z['above'];behavior=z['behavior']
    # Native RGB5 colours are used before the compiler sees the assets.
    bottom[...,:3]=(bottom[...,:3]>>3)<<3;upper[...,:3]=(upper[...,:3]>>3)<<3
    bottom,upper,palettes=color_fit(bottom,upper,owners)
    catalogs=[{},{}];grid=np.zeros((N,N),np.uint16);records=[[],[]]
    for y,x in np.ndindex(N,N):
        sl=np.s_[y*16:(y+1)*16,x*16:(x+1)*16];a,b=bottom[sl],upper[sl];who=set(owners[sl].ravel())
        secondary=bool(who&{'souvenir-shop','east-house','gym','pokemon-center','route43-gate'})
        typ=0 if above[y,x] else 1;bh=int(behavior[y,x]);key=(a.tobytes(),b.tobytes(),typ,bh)
        c=catalogs[secondary]
        if key not in c:c[key]=len(c);records[secondary].append((a.copy(),b.copy(),typ,bh))
        grid[y,x]=c[key]+(512 if secondary else 0)
    for part in (0,1):
        rec=records[part];path=SRC/('primary' if part==0 else 'secondary');path.mkdir(exist_ok=True)
        h=((len(rec)+7)//8)*16;layers=[np.zeros((h,128,4),np.uint8) for _ in range(3)];rows=['id,behavior']
        for i,(bg,fg,typ,bh) in enumerate(rec):
            x=i%8*16;y=i//8*16
            layers[1 if typ==0 else 0][y:y+16,x:x+16]=bg
            layers[2 if typ==0 else 1][y:y+16,x:x+16]=fg
            label={0:'MB_NORMAL',57:'MB_JUMP_WEST',59:'MB_JUMP_SOUTH',96:'MB_NON_ANIMATED_DOOR',105:'MB_ANIMATED_DOOR'}[bh]
            rows.append(f'{i},{label}')
        for name,a in zip(('bottom','middle','top'),layers):Image.fromarray(a).save(path/(name+'.png'))
        (path/'attributes.csv').write_text('\n'.join(rows)+'\n')
        overrides=path/'palette-overrides';overrides.mkdir(exist_ok=True)
        for bank,pal in palettes.items():
            if (bank<6)==(part==0):palfile(overrides/f'{bank:02}.pal',pal)
    np.save(SRC/'map-metatiles.npy',grid)
    out=game/'data/tilesets';primary=out/'primary/mahogany_rebuild';secondary=out/'secondary/mahogany_rebuild'
    primary.mkdir(exist_ok=True);secondary.mkdir(exist_ok=True)
    common=['-dual-layer','-tiles-total-override=1008','-target-base-game=pokeemerald']
    commands=[[str(PORY),'compile-primary',*common,'-o',str(primary),str(SRC/'primary'),str(game/'include/constants/metatile_behaviors.h')],
              [str(PORY),'compile-secondary',*common,'-o',str(secondary),str(SRC/'secondary'),str(SRC/'primary'),str(game/'include/constants/metatile_behaviors.h')]]
    for i,cmd in enumerate(commands):
        r=subprocess.run(cmd,capture_output=True,text=True);(EV/f'porytiles-{i}.log').write_text(r.stdout+r.stderr)
        print('Porytiles',i,'exit',r.returncode, 'metatiles',len(records[i]))
        if r.returncode:print(r.stderr[-6000:]);raise SystemExit(r.returncode)
    (EV/'compile.json').write_text(json.dumps(dict(commands=commands,metatiles=[len(r) for r in records]),indent=2)+'\n')

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
