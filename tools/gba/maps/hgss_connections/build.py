#!/usr/bin/env python3
"""HGSS exterior recreation using Claude's native-cutout/Porymap compiler.
Preserves the earlier campus proposal and all owner/Claude map cells.
"""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from johto_connections import build as b
from claude_cherrygrove import banks,ground,hgss
from claude_routes import art as ra
from claude_routes.layouts import plan
from tiles import Tileset
ROOT=HERE.parents[3];OUT=ROOT/'gba/art/hgss-connections';REF=OUT/'references'

def crop(name,box,bg,largest=1):
    a=np.asarray(Image.open(REF/(name+'-hgss.png')).convert('RGBA').crop(box)).copy()
    return ra.cutout(a,bg,tol=12,keep_largest=largest)

def assets(kind,base,shared):
    a=dict(base);pals=dict(shared)
    if kind=='new_bark':
        bg=ra.GRASS30+ra.PATH+ra.TREE+hgss.SHADOW_COLORS
        lab=crop('new-bark',(160,32,272,128),bg)
        # The rendered entrance is two pixels off-grid. Move only its frame.
        hgss.shift_rect(lab,50,72,16,24,-2)
        home=crop('new-bark',(256,240,352,320),bg)
        hgss.shift_rect(home,24,56,16,24,8)
        groups=[banks.Bank(6,'ELM','secondary').add('institute',lab),
                banks.Bank(9,'UPPER_HOME','secondary').add('annex',crop('new-bark',(328,64,440,176),bg)),
                banks.Bank(12,'HOMES','secondary').add('west_house',crop('new-bark',(80,208,160,288),bg)).add('east_house',home)]
    else:
        bg=ra.GRASS30+ra.PATH+ra.TREE+hgss.SHADOW_COLORS
        groups=[banks.Bank(12,'GATE','secondary').add('gate',crop('route31',(0,160,96,256),bg)),
                banks.Bank(9,'CLIFF','secondary').add('cave',crop('route31',(768,144,880,224),bg)).add('bridge',np.asarray(Image.open(REF/'route31-hgss.png').convert('RGBA').crop((534,256,566,304)))).add('rock',np.asarray(Image.open(REF/'route31-hgss.png').convert('RGBA').crop((928,32,960,80)))),
                banks.Bank(6,'TALL','secondary')]
        sl=ra.tall_slices()
        for n in (0,1):
            for s in (0,1):
                for w in (0,1):
                    for e in (0,1):groups[-1].add(f'tall{n}{s}{w}{e}',ra.tall_cell(sl,n,s,w,e))
        groups.append(banks.Bank(7,'LEDGES','secondary'))
        for name,piece in ra.ledges().items():groups[-1].add(name,piece)
    for group in groups:a.update(group.build());pals[group.bank]=group.palette
    return a,pals

def layout(kind):
    if kind=='new_bark':return plan(30,24,[
        ('.',0,9,28,5),('P',0,12,28,2),('P',11,10,6,3),
        ('.',7,4,10,6),('.',17,8,11,3),('.',8,14,16,7),
        ('P',10,14,3,7),('P',12,19,12,3),('P',22,14,2,6),
        ('.',1,18,9,2),('W',28,12,2,3),
    ])
    return plan(63,30,[
        ('.',0,11,34,7),('P',0,14,24,2),('P',22,16,12,2),
        ('W',26,7,8,9),('T',20,11,4,3),
        ('.',7,18,26,6),('G',7,19,14,4),('G',23,20,10,4),
        ('G',21,23,10,3),('_',7,18,14,1),('_',23,19,3,1),('_',29,19,4,1),
        ('.',36,12,19,6),('.',36,18,6,10),('P',38,23,2,7),('.',34,16,2,3),
        ('G',42,22,9,4),('G',44,26,9,2),
        ('#',48,0,15,13),('#',46,2,2,8),('#',44,4,2,3),
    ])

BUILDINGS=[('institute',16,2,3),('annex',26,4,None),('west_house',11,13,2),('east_house',22,15,2)]
SIGNS={'new_bark':[('Institute',15,8),('Town',19,13)],'route31':[('Route',10,13),('Cave',51,13)]}

def compose(kind,p,a):
    p=p.copy();h,w=p.shape
    if kind=='new_bark':
        for name,x,y,_ in BUILDINGS:c=a[name];p[y:y+c.h//16,x:x+c.w//16]='.'
    else:p[9:16,:6]='.';p[9:14,48:55]='.'
    mc=b.town.MapCanvas(w,h);cells=np.full((h,w),ground.GRASS,np.int8);solid=p=='T';behavior=np.zeros((h,w),np.uint8)
    cells[p=='P']=ground.PATH;cells[p=='W']=ground.SEA;solid[p=='W']=True;behavior[p=='W']=16
    objects=[];doors=[]
    def obj(name,x,y):
        c=a[name];objects.append((y*16+c.h,x*16,y*16,c))
    for x in range(0,w,2):
        for yp in range((-24 if kind=='new_bark' else -16),h*16,24):
            lo,hi=max(0,yp//16),min(h,(yp+31)//16+1)
            if hi>lo and (p[lo:hi,x:min(w,x+2)]=='T').all():
                c=a['tree'];objects.append((yp+c.h,x*16,yp,c))
    if kind=='new_bark':
        for name,x,y,dx in BUILDINGS:
            c=a[name];obj(name,x,y);solid[y:y+c.h//16,x:x+c.w//16]=True
            if dx is not None:
                xx,yy=x+dx,y+c.h//16-1;solid[yy,xx]=False;behavior[yy,xx]=105;doors.append((name,xx,yy))
        for x,y in [(8,18),(23,9)]:obj('daisies',x,y)
    else:
        obj('bridge',34,16);obj('gate',0,10);solid[10:16,:6]=True;solid[15,4]=False;behavior[15,4]=105;doors.append(('gate',4,15))
        for y in range(0,13,3):
            for x in range(44,63,2):
                if p[y,x]=='#':obj('rock',x,y)
        solid[p=='#']=True
        obj('cave',48,9);solid[9:14,48:55]=True;solid[13,52]=False;behavior[13,52]=97;doors.append(('cave',52,13))
    for y in range(h):
        for x in range(w):
            if p[y,x]=='G':
                nb=lambda yy,xx:0<=yy<h and 0<=xx<w and p[yy,xx]=='G'
                obj(f'tall{int(nb(y-1,x))}{int(nb(y+1,x))}{int(nb(y,x-1))}{int(nb(y,x+1))}',x,y);behavior[y,x]=2
            elif p[y,x]=='_':obj('ledge_a' if x%2==0 else 'ledge_b',x,y);solid[y,x]=True;behavior[y,x]=59
    for _,x,y in SIGNS[kind]:obj('sign',x,y-1);solid[y,x]=True;behavior[y,x]=29;mc.above[y-1,x]=True
    for _,px,py,c in sorted(objects,key=lambda o:(o[3].pal.bank not in (3,10),o[0],o[1])):
        if c.pal.bank not in (3,10):
            # Hidden foliage is removed under the aligned asset footprint, as in native layer factoring.
            x0,y0=max(0,px),max(0,py);x1,y1=min(w*16,px+c.w),min(h*16,py+c.h)
            mc.bank[y0:y1,x0:x1]=-1;mc.idx[y0:y1,x0:x1]=0
        mc.blit(c,px,py)
    return dict(W=w,H=h,canvas=mc,cells=cells,solid=solid,behavior=behavior,tag=kind,signs=SIGNS[kind],doors=doors)

def main():
    game=Path(sys.argv[1]).resolve();assert game!=ROOT/'game'
    assert not (game/'data/maps/NewBarkTown').exists(),'Use a fresh routes-baseline worktree.'
    base,shared=b.town.build_assets();primary=b.routes.Primary(game,78,511);compiled={};report={};OUT.mkdir(parents=True,exist_ok=True)
    symbols=b.register_tilesets(game,['new_bark','route31','violet_entrance'])
    for kind in ['new_bark','route31','violet_entrance']:
        if kind=='violet_entrance':p=b.L.violet_entrance();a,pals=b.assets(kind,base,shared);comp=b.compose(kind,p,a)
        else:
            p=layout(kind)
            if kind=='new_bark':
                # Six-cell approach keeps the existing Route 29 camera window on shared terrain.
                q=np.full((24,36),'T',dtype='<U1');q[:,6:]=p;q[9:14,:6]='.';q[12:14,:6]='P';p=q
            a,pals=assets(kind,base,shared)
            if kind=='route31':
                # Tall grass is visible across Route 30, so index against its exact existing bank.
                target=b.Palette(6,b.palette(game/'data/tilesets/secondary/claude_route30/palettes/06.pal')[1:],[f'c{i}' for i in range(15)])
                source=np.asarray(pals[6].gba()[1:],dtype=int);dest=np.asarray(target.gba()[1:],dtype=int)
                mapping=np.concatenate(([0],((source[:,None]-dest[None])**2).sum(2).argmin(1)+1))
                for key,c in a.items():
                    if key.startswith('tall'):c.px=mapping[c.px].astype('uint8');c.pal=target
                pals[6]=target
            comp=compose(kind,p,a)
        if kind=='new_bark':packer,grid,join=b.pack_connected(game,kind,comp,pals,'CherrygroveRoute29Approach','claude_route29',(98,4),(0,12),(97,16),primary)
        elif kind=='route31':packer,grid,join=b.pack_connected(game,kind,comp,pals,'CherrygroveRoute30Approach','claude_route30',(-28,-30),(38,29),(10,0),primary)
        else:packer=b.routes.RoutePacker(pals,primary);grid=np.zeros(p.shape,np.uint16);b.pack_cells(comp,packer,pals,np.ones(p.shape,bool),grid);join={}
        assert packer.conflicts==0,(kind,packer.conflict_cells[:3])
        nt,nb=b.routes.write_route_tileset(game,kind,packer,pals);compiled[kind]=(comp,grid)
        report[kind]=dict(width=comp['W'],height=comp['H'],tiles=nt,metatiles=nb,doors=comp['doors'],**join)
        Tileset(game,kind,'cherrygrove').map_image(grid.ravel().tolist(),comp['W']).save(OUT/(kind+'-overview.png'))
        (OUT/(kind+'-collision.txt')).write_text('\n'.join(''.join('#' if v else '.' for v in row) for row in comp['solid'])+'\n')
    b.write_maps(game,b.load_json(game/'data/layouts/layouts.json'),compiled,symbols)
    # Door locations come from the authored plans, never the retired campus proposal.
    for name,kind in [('NewBarkTown','new_bark'),('JohtoRoute31','route31')]:
        path=game/f'data/maps/{name}/map.json';m=b.load_json(path)
        for warp,(_,x,y) in zip(m['warp_events'],compiled[kind][0]['doors']):warp.update(x=x,y=y)
        if kind=='new_bark':m['connections'][0]['offset']=-4;m['object_events']=[]
        b.save_json(path,m)
    path=game/'data/maps/CherrygroveRoute29Approach/map.json';m=b.load_json(path)
    for c in m['connections']:
        if c['map']=='MAP_NEW_BARK_TOWN':c['offset']=4
    b.save_json(path,m)
    report['references']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in REF.glob('*.png')}
    b.save_json(OUT/'build-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
