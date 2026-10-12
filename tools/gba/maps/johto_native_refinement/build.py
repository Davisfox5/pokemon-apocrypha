#!/usr/bin/env python3
"""Cohesive route revision and expanded New Bark on the accepted town baseline.
Preserves the town, references and earlier drafts; corrects route art explicitly.
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
ROOT=HERE.parents[3];OUT=ROOT/'gba/art/johto-native-refinement';REF=ROOT/'gba/art/hgss-connections/references'

from johto_polish import art as terrain
from johto_native_refinement import art
from johto_native_refinement import routes as revised_routes
ra.tall_slices=art.tall_slices
ra.tall_cell=art.tall_cell
original_assets=b.town.build_assets
def native_assets():
    a,p=original_assets()
    a['tree']=art.source_tree();a['blossom']=art.source_tree();p[12]=a['tree'].pal
    native=OUT/'native';native.mkdir(parents=True,exist_ok=True)
    for name in ('tree','blossom'):Image.fromarray(a[name].to_rgba()).save(native/(name+'.png'))
    return a,p
b.town.build_assets=native_assets

def assets(kind,base,shared):
    import copy
    a=copy.deepcopy(base);pals=dict(shared)
    if kind=='new_bark':
        raw=art.props(base);raw.update(art.architecture(base));raw['upper_wind']=raw['wind'].copy();raw['east_mailbox']=raw['red_mailbox'].copy();groups=[]
        for bank,keys in [(6,['annex','west_house','east_house','staff_a','staff_b']), (8,['institute']),
                          (9,['labwind','upper_wind','lab_fence','red_mailbox','blue_mailbox','wind','east_mailbox'])]:
            group=banks.Bank(bank,'ARCHITECTURE','secondary')
            if bank==6:group.keep(*base['house'].pal.colors)
            else:group.keep(ground_color())
            for name in keys:group.add(name,raw[name])
            if bank!=6:group.add('__grass'+str(bank),np.array([[[104,208,152,255]]],dtype='uint8'))
            # Preserve windmill whites and the dark blue glass, as Cherrygrove protects doors.
            for name in keys:
                if 'wind' in name:
                    v=raw[name];px=v[(v[...,3]>0)&(v[...,:3].max(2)-v[...,:3].min(2)<32)&(v[...,:3].min(2)>100),:3]
                    if len(px):
                        cs,counts=np.unique(px,axis=0,return_counts=True)
                        group.keep(*[tuple(c) for c in cs[np.argsort(counts)[-3:]]])
            groups.append(group)
    else:
        raw={'gate':art.architecture(base)['gate31'],'apricorn':terrain.route31()['apricorn']};raw.update(art.cliff_modules(base));
        groups=[banks.Bank(8,'GATE','secondary').add('gate',raw['gate']).add('apricorn',raw['apricorn']),
                banks.Bank(9,'CLIFF','secondary').keep((104,208,152))]
        for key in ['cliff','plateau','face','west_face','cliff_corner','cave_mouth','bridge']:groups[-1].add(key,raw[key])
        cave=raw['cave_mouth'];cs,counts=np.unique(cave[...,:3].reshape(-1,3),axis=0,return_counts=True)
        dark=cs[(cs.mean(1)<60)&(counts>3)]
        if len(dark):groups[-1].keep(*[tuple(c) for c in dark[np.argsort(dark.mean(1))[:2]]])
        groups.append(banks.Bank(6,'TALL','secondary'))
        sl=ra.tall_slices()
        for n in (0,1):
            for ss in (0,1):
                for w in (0,1):
                    for e in (0,1):groups[-1].add(f'tall{n}{ss}{w}{e}',ra.tall_cell(sl,n,ss,w,e))
        groups.append(banks.Bank(7,'LEDGES','secondary'))
        for name,piece in ra.ledges().items():groups[-1].add(name,piece)
        for name,piece in ra.cliff_pieces().items():groups[-1].add('wall_'+name,piece)
        groups[-1].add('bankwall',raw['west_face'][:16])
    for group in groups:a.update(group.build());pals[group.bank]=group.palette
    native=OUT/'native';native.mkdir(parents=True,exist_ok=True)
    for key in raw:
        if key in a:Image.fromarray(a[key].to_rgba()).save(native/(key+'.png'))
    return a,pals

def ground_color():return (104,208,152)

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
        ('.',36,12,19,6),('.',36,18,6,10),('P',38,23,2,7),('.',33,16,3,3),
        ('G',42,22,9,4),('G',44,26,9,2),
        ('#',48,0,15,13),('#',46,2,2,8),('#',44,4,2,3),
    ])

BUILDINGS=[('institute',11,0,5),('annex',26,4,2),('west_house',11,13,1),('east_house',22,15,1),('staff_a',9,26,1),('staff_b',23,26,2),('staff_a',9,35,1),('staff_b',23,35,2)]
SIGNS={'new_bark':[('Institute',15,8),('Town',19,13)],'route31':[('Route',10,13),('Cave',51,13)]}

def pals_for(a,name):return a[name].pal

def compose(kind,p,a):
    p=p.copy();h,w=p.shape
    if kind=='new_bark':
        for name,x,y,_ in BUILDINGS:c=a[name];p[y:y+c.h//16,x:x+c.w//16]='.'
    else:p[9:16,:8]='.';p[9:14,48:55]='.'
    mc=b.town.MapCanvas(w,h);cells=np.full((h,w),ground.GRASS,np.int8);solid=p=='T';behavior=np.zeros((h,w),np.uint8)
    cells[p=='P']=ground.PATH;cells[p=='W']=ground.SEA;solid[p=='W']=True;behavior[p=='W']=16
    objects=[];doors=[]
    def obj(name,x,y):
        c=a[name];objects.append((y*16+c.h,x*16,y*16,c))
    for px,py,c in art.forest(p,a['tree']):objects.append((py+c.h,px,py,c))
    if kind=='new_bark':
        for name,x,y,dx in BUILDINGS:
            c=a[name];obj(name,x,y);solid[y:y+c.h//16,x:x+c.w//16]=True
            if dx is not None:
                xx,yy=x+dx,y+c.h//16-1;solid[yy,xx]=False;behavior[yy,xx]=105;doors.append((name if y<24 else 'staff_'+str(x)+'_'+str(y),xx,yy))
        for x,y in [(8,18),(23,9),(24,8),(25,10)]:obj('daisies',x,y)
        for name,x,y in [('labwind',24,3),('red_mailbox',9,5),('wind',17,14),('wind',28,16),('upper_wind',32,6),('east_mailbox',21,16)]:obj(name,x,y)
        for x,y in [(25,6),(9,6),(18,17),(29,19),(33,9),(21,17)]:solid[y,x]=True
    else:
        obj('gate',0,10);solid[10:16,:8]=True;solid[15,4]=False;behavior[15,4]=105;doors.append(('gate',4,15))
        from claude_cherrygrove.pixel import Canvas
        obj('cliff',45,0)
        solid[2:14,46:]=True;solid[1:12,51:]=True;solid[:10,56:]=True
        obj('cave_mouth',51,11);solid[13,52]=False;behavior[13,52]=97;doors.append(('cave',52,13))
        # Reuse Cherrygrove's primary animated sea tiles and shoreline painter.
        # The pond bank is a vertical cliff face with a wooden crossing.
        for y in range(7,28):
            if y not in (15,16,17):obj('bankwall',34,y)
        solid[7:28,33:35]=True;solid[16:19,33:36]=False
        obj('bridge',33,15);obj('apricorn',20,12);solid[14,20]=True
    for y in range(h):
        for x in range(w):
            if p[y,x]=='G':
                nb=lambda yy,xx:0<=yy<h and 0<=xx<w and p[yy,xx]=='G'
                obj(f'tall{int(nb(y-1,x))}{int(nb(y+1,x))}{int(nb(y,x-1))}{int(nb(y,x+1))}',x,y);behavior[y,x]=2
            elif p[y,x]=='_':obj('ledge_a' if x%2==0 else 'ledge_b',x,y);solid[y,x]=True;behavior[y,x]=59
    for _,x,y in SIGNS[kind]:obj('sign',x,y-1);solid[y,x]=True;behavior[y,x]=29;mc.above[y-1,x]=True
    ordered=sorted(objects,key=lambda o:(o[3].pal.bank not in (3,10,12),o[0],o[1]))
    for _,px,py,c in ordered:
        if c.pal.bank in (3,10,12):mc.blit(c,px,py)
    mc.under_bank=mc.bank.copy();mc.under_idx=mc.idx.copy()
    for _,px,py,c in ordered:
        if c.pal.bank not in (3,10,12):mc.blit(c,px,py)
    return dict(W=w,H=h,canvas=mc,cells=cells,solid=solid,behavior=behavior,tag=kind,signs=SIGNS[kind],doors=doors)

def pack_cells(comp,packer,pals,mask,grid):
    gimg,mat=ground.paint(comp['cells']);gbank,gidx=b.town.index_ground(gimg,mat,pals);mc=comp['canvas']
    for y,x in zip(*np.nonzero(mask)):
        bottom=[];top=[]
        for q in range(4):
            xx,yy=x*16+q%2*8,y*16+q//2*8
            bi=mc.bank[yy:yy+8,xx:xx+8];ix=mc.idx[yy:yy+8,xx:xx+8].astype('uint8');bs=[int(v) for v in np.unique(bi) if v>=0]
            assert len(bs)<=2,(comp['tag'],x,y,q,bs)
            def tile(bank,pixels):return packer.tile(bank,pixels)|(bank<<12) if pixels.any() else 0
            if len(bs)==2:
                # Two real hardware layers retain both indexed palettes exactly.
                lo=next((v for v in bs if v>=6),bs[0]);hi=next(v for v in bs if v!=lo)
                low=np.where(bi==lo,ix,0).astype('uint8')
                if (bi<0).any():
                    colors=np.asarray(pals[lo].gba()[1:],dtype=int);rgb=gimg[yy:yy+8,xx:xx+8,:3].astype(int)
                    low[bi<0]=((rgb[bi<0,None]-colors[None])**2).sum(2).argmin(1)+1
                if hi in (3,10,12) and hasattr(mc,'under_idx'):
                    ub=mc.under_bank[yy:yy+8,xx:xx+8];ui=mc.under_idx[yy:yy+8,xx:xx+8].astype('uint8')
                    # Whole hidden tree patterns stay reusable beneath opaque architecture.
                    bottom.append(tile(hi,np.where(ub==hi,ui,0).astype('uint8')));top.append(tile(lo,low))
                else:bottom.append(tile(lo,low));top.append(tile(hi,np.where(bi==hi,ix,0).astype('uint8')))
            else:
                scene=tile(bs[0],ix) if bs else 0
                if (bi>=0).all():bottom.append(scene);top.append(0)
                else:
                    gi=gidx[yy:yy+8,xx:xx+8].astype('uint8');gb=int(gbank[yy,xx]);bottom.append(tile(gb,gi));top.append(scene)
        beh=int(comp['behavior'][y,x]);attr=beh|(b.town.NORMAL if mc.above[y,x] else b.town.COVERED)
        grid[y,x]=packer.metatile(bottom+top,attr)|0x3000|(0xC00 if comp['solid'][y,x] else 0)

b.pack_cells=pack_cells

def main():
    game=Path(sys.argv[1]).resolve();assert game!=ROOT/'game'
    assert not (game/'data/maps/NewBarkTown/map.json').exists(),'Use a fresh routes-baseline worktree.'
    OUT.mkdir(parents=True,exist_ok=True)
    revised_routes.build(game)
    base,shared=b.town.build_assets();ra.ledges=lambda:art.ledges(base);primary=b.routes.Primary(game,78,511);compiled={};report={};OUT.mkdir(parents=True,exist_ok=True)
    symbols=b.register_tilesets(game,['new_bark','route31','violet_entrance'])
    for kind in ['new_bark','route31','violet_entrance']:
        print('Packing',kind,flush=True)
        if kind=='violet_entrance':
            p=b.L.violet_entrance();a,pals=b.assets(kind,base,shared)
            a['house']=base['house'];pals[6]=base['house'].pal;pals[12]=base['tree'].pal
            comp=b.compose(kind,p,a,forest_builder=art.forest)
        else:
            p=layout(kind)
            if kind=='new_bark':
                # Six-cell approach keeps the existing Route 29 camera window on shared terrain.
                q=np.full((50,36),'T',dtype='<U1');q[:24,6:]=p;q[9:14,:6]='.';q[12:14,:6]='P';q[22:42,7:29]='.';q[7:12,16:18]='P';q[21:41,16:18]='P';q[31:33,9:28]='P';q[40:42,9:28]='P';q[29:32,10:12]='P';q[29:32,25:27]='P';q[38:41,10:12]='P';q[38:41,25:27]='P';q[12:39,34:]='W';q[38:,30:]='W';p=q
            a,pals=assets(kind,base,shared)
            if kind=='route31':
                # Both visible terrain banks must use Route 30's exact existing palettes.
                for bank in (6,7,8):
                    target=b.Palette(bank,b.palette(game/f'data/tilesets/secondary/claude_route30/palettes/{bank:02}.pal')[1:],[f'c{i}' for i in range(15)])
                    source=np.asarray(pals[bank].gba()[1:],dtype=int);dest=np.asarray(target.gba()[1:],dtype=int)
                    mapping=np.concatenate(([0],((source[:,None]-dest[None])**2).sum(2).argmin(1)+1))
                    for key,c in a.items():
                        if c.pal.bank==bank:c.px=mapping[c.px].astype('uint8');c.pal=target
                    pals[bank]=target
            comp=compose(kind,p,a)
        if kind=='new_bark':packer,grid,join=b.pack_connected(game,kind,comp,pals,'CherrygroveRoute29Approach','claude_route29',(98,4),(0,12),(97,16),primary)
        elif kind=='route31':packer,grid,join=b.pack_connected(game,kind,comp,pals,'CherrygroveRoute30Approach','claude_route30',(-28,-30),(38,29),(10,0),primary)
        else:packer=b.routes.RoutePacker(pals,primary);grid=np.zeros(p.shape,np.uint16);b.pack_cells(comp,packer,pals,np.ones(p.shape,bool),grid);join={}
        assert packer.conflicts==0,(kind,packer.conflict_cells[:3])
        nt,nb=b.routes.write_route_tileset(game,kind,packer,pals);compiled[kind]=(comp,grid)
        report[kind]=dict(width=comp['W'],height=comp['H'],tiles=nt,metatiles=nb,doors=comp['doors'],**join)
        decoded=Tileset(game,kind,'cherrygrove').map_image(grid.ravel().tolist(),comp['W'])
        decoded.save(OUT/(kind+'-overview.png'))
        # Verify every opaque scenery pixel after packing, including mixed-bank tree/roof edges.
        rgb=np.asarray(decoded);mc=comp['canvas'];expected=np.zeros_like(rgb)
        for bank in np.unique(mc.bank):
            if bank>=0:
                pal=np.asarray(pals[int(bank)].gba(),dtype='uint8');m=mc.bank==bank;expected[m]=pal[mc.idx[m]]
        visible=mc.bank>=0;errors=np.any(rgb!=expected,axis=2)&visible
        assert not errors.any(),(kind,'scenery color mismatch',int(errors.sum()))
        report[kind]['opaque_scenery_pixels_verified']=int(visible.sum())
        report[kind]['scenery_color_mismatches']=int(errors.sum())
        (OUT/(kind+'-collision.txt')).write_text('\n'.join(''.join('#' if v else '.' for v in row) for row in comp['solid'])+'\n')
    b.write_maps(game,b.load_json(game/'data/layouts/layouts.json'),compiled,symbols)
    # Door locations come from the authored plans, never the retired campus proposal.
    for name,kind in [('NewBarkTown','new_bark'),('JohtoRoute31','route31')]:
        path=game/f'data/maps/{name}/map.json';m=b.load_json(path)
        if kind=='new_bark':
            coords={label:(x,y) for label,x,y in compiled[kind][0]['doors']}
            for warp,label in zip(m['warp_events'],['institute','west_house','east_house']):warp.update(x=coords[label][0],y=coords[label][1])
            m['warp_events'].append(b.warp(*coords['annex'],'NEW_BARK_UPPER_HOUSE'))
        else:
            for warp,(_,x,y) in zip(m['warp_events'],compiled[kind][0]['doors']):warp.update(x=x,y=y)
        if kind=='new_bark':m['connections'][0]['offset']=-4;m['object_events']=[]
        b.save_json(path,m)
    upper=b.load_json(game/'data/maps/NewBarkEastHouse/map.json')
    upper.update(id='MAP_NEW_BARK_UPPER_HOUSE',name='NewBarkUpperHouse',warp_events=[b.warp(3,8,'NEW_BARK_TOWN',3),b.warp(4,8,'NEW_BARK_TOWN',3)])
    b.save_json(game/'data/maps/NewBarkUpperHouse/map.json',upper)
    (game/'data/maps/NewBarkUpperHouse/scripts.inc').write_text('NewBarkUpperHouse_MapScripts::\n    .byte 0\n')
    group=b.load_json(game/'data/maps/map_groups.json');group['gMapGroup_Cherrygrove'].append('NewBarkUpperHouse');b.save_json(game/'data/maps/map_groups.json',group)
    path=game/'data/event_scripts.s';path.write_text(path.read_text()+'\n.include "data/maps/NewBarkUpperHouse/scripts.inc"\n')
    path=game/'src/apocrypha_map_proof.c';text=path.read_text().replace('MAP_NEW_BARK_EAST_HOUSE}', 'MAP_NEW_BARK_EAST_HOUSE, MAP_NEW_BARK_UPPER_HOUSE}').replace('% 19','% 20');path.write_text(text)
    path=game/'data/maps/CherrygroveRoute29Approach/map.json';m=b.load_json(path)
    for c in m['connections']:
        if c['map']=='MAP_NEW_BARK_TOWN':c['offset']=4
    b.save_json(path,m)
    report['references']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in REF.glob('*.png')}
    b.save_json(OUT/'build-report.json',report);print(json.dumps(report,indent=2))
    add_staff_houses(game,compiled)
    reuse={}
    for name,source in [('west_house','house'),
                        ('east_house','house'),('staff_a','house'),('staff_b','gable'),('annex','gable')]:
        pixels=np.asarray(Image.open(OUT/'native'/(name+'.png')))
        original=base[source].to_rgba()
        assert np.array_equal(pixels,original),('Cherrygrove asset drift',name)
        reuse[name]=dict(source_asset=source,rgba_sha256=hashlib.sha256(original.tobytes()).hexdigest(),pixel_differences=0)
    b.save_json(OUT/'evidence/cherrygrove-reuse.json',dict(
        baseline='gba/art/claude-cherrygrove',unchanged_assets=reuse,
        institute='Original masonry laboratory with metal roof, glazing, skylights and ventilation; one entrance'
        ,tree='Literal gba/art/claude-cherrygrove/source/tree.idx.png and bank03 palette, without resize or recolor',forest_checks=art.FOREST_AUDITS))

def add_staff_houses(game,compiled):
    townpath=game/'data/maps/NewBarkTown/map.json';m=b.load_json(townpath);group=b.load_json(game/'data/maps/map_groups.json')
    doors=[d for d in compiled['new_bark'][0]['doors'] if d[0].startswith('staff_')]
    for i,(_,x,y) in enumerate(doors):
        name='NewBarkResidence'+str(i+1);id_='NEW_BARK_RESIDENCE_'+str(i+1);wi=len(m['warp_events']);m['warp_events'].append(b.warp(x,y,id_))
        interior=b.load_json(game/'data/maps/NewBarkStaffHouse/map.json');interior.update(id='MAP_'+id_,name=name,object_events=[],warp_events=[b.warp(3,8,'NEW_BARK_TOWN',wi),b.warp(4,8,'NEW_BARK_TOWN',wi)])
        b.save_json(game/f'data/maps/{name}/map.json',interior);(game/f'data/maps/{name}/scripts.inc').write_text(name+'_MapScripts::\n    .byte 0\n');group['gMapGroup_Cherrygrove'].append(name)
        path=game/'data/event_scripts.s';path.write_text(path.read_text()+'\n.include "data/maps/'+name+'/scripts.inc"\n')
    b.save_json(townpath,m);b.save_json(game/'data/maps/map_groups.json',group)
    violet=game/'data/maps/VioletCityEntrance/map.json';vm=b.load_json(violet);vm['bg_events']=[v for v in vm['bg_events'] if 'University' not in v['script']];b.save_json(violet,vm)
    path=game/'data/maps/VioletCityEntrance/scripts.inc';path.write_text(path.read_text().split('\nVioletCityEntrance_University::')[0])
    # Exterior expansion authorizes housing, not invented dialogue or new roles.
    for name in ['NewBarkInstitute','NewBarkStaffHouse','NewBarkEastHouse']:
        path=game/f'data/maps/{name}/map.json';mi=b.load_json(path);mi['object_events']=[];b.save_json(path,mi);(game/f'data/maps/{name}/scripts.inc').write_text(name+'_MapScripts::\n    .byte 0\n')
if __name__=='__main__':main()
