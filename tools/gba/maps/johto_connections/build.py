#!/usr/bin/env python3
"""Extend the preserved Claude routes in an isolated workbench; never regenerate its town.

python3 tools/gba/maps/johto_connections/build.py tools/vendor/gba/routes-new-bark
Apply claude-cherrygrove.patch and claude-routes.patch to the workbench preset first.
"""
import json
import struct
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from claude_cherrygrove import build as town, ground, banks, hgss
from claude_cherrygrove.pixel import Palette
from claude_routes import build as routes, art as route_art, seams
from tiles import Tileset, palette
from johto_connections import art, layouts as L

ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/johto-connections'
NAMES = ['NewBarkTown','JohtoRoute31','VioletCityEntrance','NewBarkInstitute','NewBarkStaffHouse','VioletEastGate','DarkCaveEntrance']
IDS = ['NEW_BARK_TOWN','JOHTO_ROUTE31','VIOLET_CITY_ENTRANCE','NEW_BARK_INSTITUTE','NEW_BARK_STAFF_HOUSE','VIOLET_EAST_GATE','DARK_CAVE_ENTRANCE']

def load_json(p): return json.loads(p.read_text())
def save_json(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')

def assets(kind, base, shared):
    a = dict(base); pals=dict(shared)
    groups=[]
    if kind != 'route31':
        groups=[banks.Bank(6,'CAMPUS','secondary').add('institute',art.institute()).add('annex',art.institute(6,5)),
                banks.Bank(9,'EQUIPMENT','secondary').add('paving',art.paving()).add('crate',art.crate()).add('dish',art.dish())]
        house=hgss.house_a().copy()
        rgb=house[...,:3].astype(int); roof=(rgb[...,0]>rgb[...,1]+24)&(rgb[...,0]>rgb[...,2]+8)
        house[...,:3][roof]=np.stack([rgb[...,1][roof]*.75,rgb[...,0][roof]*.65,rgb[...,0][roof]*.62],axis=1).astype('uint8')
        groups.append(banks.Bank(12,'HOUSING','secondary').add('house',house))
        if kind=='violet_entrance':groups.append(banks.Bank(8,'GATE','secondary').add('gate',route_art.gate()))
    else:
        groups=[banks.Bank(8,'GATE','secondary').add('gate',route_art.gate()),
                banks.Bank(9,'CAVE','secondary').add('cave',art.cave()),
                banks.Bank(6,'TALL','secondary')]
        sl=route_art.tall_slices()
        for n in (0,1):
            for s in (0,1):
                for w in (0,1):
                    for e in (0,1): groups[-1].add(f'tall{n}{s}{w}{e}',route_art.tall_cell(sl,n,s,w,e))
        groups.append(banks.Bank(7,'LEDGE','secondary'))
        for name,piece in route_art.ledges().items(): groups[-1].add(name,piece)
    for group in groups:
        a.update(group.build());pals[group.bank]=group.palette
    return a,pals

def compose(kind, plan, a):
    plan=plan.copy()
    if kind=='new_bark':
        for name,x,y in L.NEW_BARK_BUILDINGS:
            c=a[name]
            plan[y:y+c.h//16,x:x+c.w//16]='.'
    signs=L.NEW_BARK_SIGNS if kind=='new_bark' else L.ROUTE31_SIGNS if kind=='route31' else [('Violet',13,9),('University',13,5)]
    for _,x,y in signs:
        region=plan[max(0,y-2):y+1,max(0,x-1):x+2]
        region[region=='T']='.'
        plan[y-1:y+1,x:x+1]='.'
    if kind=='route31':
        plan[6:17,2:13]='.'
        plan[3:10,33:41]='.'
    if kind=='violet_entrance':
        plan[2:9,3:10]='.'
        plan[4:15,17:28]='.'
    h,w=plan.shape; mc=town.MapCanvas(w,h)
    cells=np.full((h,w),ground.GRASS,np.int8)
    solid=plan=='T'; behavior=np.zeros((h,w),np.uint8)
    cells[plan=='P']=ground.PATH;cells[plan=='W']=ground.SEA
    solid[plan=='W']=True;behavior[plan=='W']=21
    objects=[];doors=[]
    def obj(name,x,y,above=False):
        c=a[name]; objects.append((-100 if name=='paving' or name.startswith('tall') else y*16+c.h,x*16,y*16,c))
        if above: mc.above[max(0,y):min(h,y+(c.h+15)//16),x:x+(c.w+15)//16]=True
    # Keep the Johto lattice and material palettes at every route edge.
    phase=16 if kind=='new_bark' else 8 if kind=='route31' else 0
    for x in range(0,w,2):
        for yp in range(phase-24,h*16,24):
            lo,hi=max(0,yp//16),min(h,(yp+31)//16+1)
            if hi>lo and (plan[lo:hi,x:min(w,x+2)]=='T').all():
                c=a['tree'];objects.append((yp+c.h,x*16,yp,c))
    if kind=='new_bark':
        for x in range(0,w,2): obj('cliff',x,28)
        solid[28:31]=True
        for name,x,y in L.NEW_BARK_BUILDINGS:
            obj(name,x,y); c=a[name];ww,hh=c.w//16,c.h//16
            solid[y:y+hh,x:x+ww]=True
            if name!='annex':
                dx=x+(ww//2-1 if name=='institute' else 1);dy=y+hh-1
                solid[dy,dx]=False;behavior[dy,dx]=105;doors.append((name,dx,dy))
        for x,y in [(32,12),(33,12)]:obj('crate',x,y);solid[y,x]=True
        obj('dish',39,11);solid[12,39:41]=True
        for x,y in [(23,26),(31,26)]:obj('bench',x,y);solid[y,x]=True
        for x,y in [(17,14),(36,15)]:obj('daisies',x,y)
        signs=L.NEW_BARK_SIGNS
    elif kind=='route31':
        obj('gate',3,7);solid[7:16,3:12]=True
        # Aligned southern entrance, beyond the northern wall/roof.
        solid[15,7]=False;behavior[15,7]=105;doors.append(('gate',7,15))
        obj('cave',34,4);solid[4:9,34:40]=True
        solid[8,36]=False;behavior[8,36]=97;doors.append(('cave',36,8))
        cells[plan=='W']=ground.SEA;behavior[plan=='W']=16
        signs=L.ROUTE31_SIGNS
    else:
        obj('bench',13,17);solid[17,13]=True
        obj('house',4,3);solid[3:8,4:9]=True
        obj('gate',18,5);solid[5:14,18:27]=True
        solid[13,22]=False;behavior[13,22]=105;doors.append(('gate',22,13))
        signs=[('Violet',13,9),('University',13,5)]
    for y in range(h):
        for x in range(w):
            ch=plan[y,x]
            if ch=='V':obj('paving',x,y)
            elif ch=='F':obj('fence_h',x,y);solid[y,x]=True
            elif ch=='G':
                nb=lambda yy,xx:0<=yy<h and 0<=xx<w and plan[yy,xx]=='G'
                obj(f'tall{int(nb(y-1,x))}{int(nb(y+1,x))}{int(nb(y,x-1))}{int(nb(y,x+1))}',x,y);behavior[y,x]=2
            elif ch=='_':obj('ledge_a' if x%2==0 else 'ledge_b',x,y);solid[y,x]=True;behavior[y,x]=59
    for name,x,y in signs:
        obj('sign',x,y-1);solid[y,x]=True;behavior[y,x]=29;mc.above[y-1,x]=True
    for _,px,py,c in sorted(objects,key=lambda o:(o[0],o[1])):mc.blit(c,px,py)
    return dict(W=w,H=h,canvas=mc,cells=cells,solid=solid,behavior=behavior,tag=kind,signs=signs,doors=doors)

def parts(game,name):
    folder=game/f'data/tilesets/secondary/{name}'
    ts=routes.read_tiles(folder/'tiles.png')
    bs=list(struct.iter_unpack('<8H',(folder/'metatiles.bin').read_bytes()))
    attrs=list(struct.unpack('<'+'H'*len(bs),(folder/'metatile_attributes.bin').read_bytes()))
    return ts,bs,attrs

def pack_cells(comp,packer,pals,mask,grid):
    gimg,mat=ground.paint(comp['cells']);gbank,gidx=town.index_ground(gimg,mat,pals)
    mc=comp['canvas']
    for y,x in zip(*np.nonzero(mask)):
        entries,opaque=packer.slice(mc.bank,mc.idx,x,y)
        beh=int(comp['behavior'][y,x])
        if opaque and not mc.above[y,x]:ent,attr=entries+[0]*4,beh|town.COVERED
        else:
            base,_=packer.slice(gbank,gidx,x,y)
            if not any(entries):ent,attr=base+[0]*4,beh
            else:ent,attr=base+entries,beh|(town.NORMAL if mc.above[y,x] else town.COVERED)
        grid[y,x]=packer.metatile(ent,attr)|0x3000|(0xC00 if comp['solid'][y,x] else 0)

def pack_connected(game,kind,comp,pals,neighbor,sec,origin,start,nstart,primary):
    """Copy both sides' visible entries at identical IDs; append seam additions to the neighbor.

    New art away from the crossing can then occupy other slots in its own secondary.
    This leaves the town primary unchanged and checks actual palettes across both masks.
    """
    layouts=load_json(game/'data/layouts/layouts.json')['layouts']
    nl=next(l for l in layouts if l['name']==neighbor+'_Layout')
    nm,ns=seams.read_layout(game,neighbor,nl['width'],nl['height'])
    nr=seams.reachable(ns,nstart);cr=seams.reachable(comp['solid'],start)
    ox,oy=origin
    nvis=seams.visible_across(cr,ns.shape,-ox,-oy);cvis=seams.visible_across(nr,comp['solid'].shape,ox,oy)
    nw,cw,cross=seams.crossing_windows(ns,comp['solid'],ox,oy);nvis|=nw;cvis|=cw
    ts,bs,ats=parts(game,sec)
    # Sea animation lives in the unchanged primary, and 10/11 are shared town accents.
    allpals={b:Palette(b,palette(game/f'data/tilesets/secondary/{sec}/palettes/{b:02}.pal')[1:],[f'c{i}' for i in range(15)]) for b in range(6,13)}
    npals={e>>12 for m in nm[nvis] for e in (primary.blocks[m] if m<512 else bs[m-512]) if e}
    for b in npals:
        if b>=6:pals[b]=allpals[b]
    seed=routes.RoutePacker(pals,primary);seed.reserve(ts,bs,ats,set(range(512,512+len(bs))))
    seed.next_tile=512+len(ts);seed.next_block=512+len(bs)
    grid=np.zeros(comp['solid'].shape,np.uint16)
    pack_cells(comp,seed,pals,cvis,grid)
    # Keep only entries that either map can actually show across this connection.
    keep={int(m) for m in nm[nvis] if m>=512}|{int(m&1023) for m in grid[cvis] if (m&1023)>=512}
    nt=max(seed.sec_tiles)+1-512; nb=max(seed.sec_blocks)+1-512
    ts2=[seed.sec_tiles.get(512+i,np.zeros((8,8),np.uint8)) for i in range(nt)]
    bs2=[seed.sec_blocks.get(512+i,((0,)*8,0))[0] for i in range(nb)]
    at2=[seed.sec_blocks.get(512+i,((0,)*8,0))[1] for i in range(nb)]
    folder=game/f'data/tilesets/secondary/{sec}'
    routes.write_tiles(folder/'tiles.png',ts2)
    (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bs2))
    (folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(at2),*at2))
    packer=routes.RoutePacker(pals,primary);packer.reserve(ts2,bs2,at2,keep)
    pack_cells(comp,packer,pals,~cvis,grid)
    # Every seam entry's rendered pixels must match using either secondary.
    cpals={e>>12 for m in grid[cvis]&1023 for e in (primary.blocks[m] if m<512 else packer.sec_blocks[int(m)][0]) if e}
    assert cpals<=set(range(6))|npals|{10,11},(kind,'seam palette mismatch',cpals,npals)
    for b in cpals:
        if b>=6:assert pals[b].gba()==allpals[b].gba(),(kind,b)
    return packer,grid,dict(crossings=cross,neighbor_visible_cells=int(nvis.sum()),new_visible_cells=int(cvis.sum()),neighbor_tiles_added=max(0,nt-len(ts)),neighbor_sheet_padding_removed=max(0,len(ts)-nt),neighbor_metatiles_added=nb-len(bs))

def register_tilesets(game,names):
    symbols={n:'gTileset_'+''.join(p.capitalize() for p in n.split('_')) for n in names}
    blocks={'graphics':'','metatiles':'','headers':''}
    for n,sym in symbols.items():
        suffix=sym.removeprefix('gTileset_')
        blocks['graphics']+=f'const u32 gTilesetTiles_{suffix}[] = INCGFX_U32("data/tilesets/secondary/{n}/tiles.png", ".4bpp.fastSmol");\n'
        blocks['graphics']+=f'const u16 gTilesetPalettes_{suffix}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/secondary/{n}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n'
        blocks['metatiles']+=f'const u16 gMetatiles_{suffix}[] = INCBIN_U16("data/tilesets/secondary/{n}/metatiles.bin");\nconst u16 gMetatileAttributes_{suffix}[] = INCBIN_U16("data/tilesets/secondary/{n}/metatile_attributes.bin");\n'
        blocks['headers']+=f'const struct Tileset {sym} = {{ .isCompressed=TRUE,.isSecondary=TRUE,.tiles=gTilesetTiles_{suffix},.palettes=gTilesetPalettes_{suffix},.metatiles=gMetatiles_{suffix},.metatileAttributes=gMetatileAttributes_{suffix},.callback=NULL }};\n'
    for part,block in blocks.items():
        p=game/f'src/data/tilesets/{part}.h';s=p.read_text();marker='// Johto connections\n'
        if marker in s:s=s.split(marker)[0]
        p.write_text(s.rstrip()+'\n\n'+marker+block)
    return symbols

def warp(x,y,dest,i=0):return dict(x=x,y=y,elevation=0,dest_map='MAP_'+dest,dest_warp_id=str(i))
def connection(dest,direction,offset=0):return dict(map='MAP_'+dest,direction=direction,offset=offset)

def write_maps(game,layouts_data,compiled,symbols):
    group=load_json(game/'data/maps/map_groups.json')
    for n in NAMES:
        if n not in group['gMapGroup_Cherrygrove']:group['gMapGroup_Cherrygrove'].append(n)
    save_json(game/'data/maps/map_groups.json',group)
    sections=load_json(game/'src/data/region_map/region_map_sections.json')
    secs=sections['map_sections']
    for id_,name,x,y in [('NEW_BARK_TOWN','NEW BARK TOWN',5,6),('JOHTO_ROUTE_31','ROUTE 31',3,4),('VIOLET_CITY','VIOLET CITY',2,4),('DARK_CAVE','DARK CAVE',4,4)]:
        if not any(s['id']=='MAPSEC_'+id_ for s in secs):secs.append(dict(id='MAPSEC_'+id_,name=name,x=x,y=y,width=1,height=1))
    save_json(game/'src/data/region_map/region_map_sections.json',sections)
    path=game/'include/regions.h';s=path.read_text();anchor='    case MAPSEC_CHERRYGROVE_CITY: return REGION_JOHTO;\n'
    for id_ in ['NEW_BARK_TOWN','JOHTO_ROUTE_31','VIOLET_CITY','DARK_CAVE']:
        if 'case MAPSEC_'+id_+':' not in s:s=s.replace(anchor,anchor+f'    case MAPSEC_{id_}: return REGION_JOHTO;\n')
    path.write_text(s)
    outdoor={'NewBarkTown':('NEW_BARK_TOWN','new_bark'),'JohtoRoute31':('JOHTO_ROUTE_31','route31'),'VioletCityEntrance':('VIOLET_CITY','violet_entrance')}
    spec={
        'NewBarkTown':([connection('CHERRYGROVE_ROUTE29_APPROACH','left')],[warp(27,11,'NEW_BARK_INSTITUTE'),warp(16,24,'NEW_BARK_STAFF_HOUSE'),warp(35,24,'NEW_BARK_STAFF_HOUSE')]),
        'JohtoRoute31':([connection('CHERRYGROVE_ROUTE30_APPROACH','down',28)],[warp(7,15,'VIOLET_EAST_GATE',2),warp(36,8,'DARK_CAVE_ENTRANCE')]),
        'VioletCityEntrance':(None,[warp(22,13,'VIOLET_EAST_GATE')]),
        'NewBarkInstitute':(None,[warp(6,12,'NEW_BARK_TOWN'),warp(7,12,'NEW_BARK_TOWN')]),
        'NewBarkStaffHouse':(None,[warp(3,8,'NEW_BARK_TOWN',1),warp(4,8,'NEW_BARK_TOWN',1)]),
        'VioletEastGate':(None,[warp(1,5,'VIOLET_CITY_ENTRANCE'),warp(2,5,'VIOLET_CITY_ENTRANCE'),warp(12,5,'JOHTO_ROUTE31'),warp(13,5,'JOHTO_ROUTE31')]),
        'DarkCaveEntrance':(None,[warp(4,10,'JOHTO_ROUTE31',1)]),
    }
    # Distinct interiors for the two houses: no exit that silently moves the player across town.
    NAMES2=[('NewBarkEastHouse','NEW_BARK_EAST_HOUSE')]
    if 'NewBarkEastHouse' not in group['gMapGroup_Cherrygrove']:
        group['gMapGroup_Cherrygrove'].append('NewBarkEastHouse');save_json(game/'data/maps/map_groups.json',group)
    spec['NewBarkTown'][1][2]=warp(35,24,'NEW_BARK_EAST_HOUSE')
    spec['NewBarkEastHouse']=(None,[warp(3,8,'NEW_BARK_TOWN',2),warp(4,8,'NEW_BARK_TOWN',2)])
    all_names=NAMES+['NewBarkEastHouse'];all_ids=IDS+['NEW_BARK_EAST_HOUSE']
    for n,id_ in zip(all_names,all_ids):
        m=load_json(game/'data/maps/CherrygroveGoldHouse/map.json')
        section=outdoor[n][0] if n in outdoor else ('VIOLET_CITY' if n=='VioletEastGate' else 'DARK_CAVE' if n=='DarkCaveEntrance' else 'NEW_BARK_TOWN')
        m.update(id='MAP_'+id_,name=n,region_map_section='MAPSEC_'+section,connections=spec[n][0],warp_events=spec[n][1],object_events=[],bg_events=[],coord_events=[])
        scripts=f'{n}_MapScripts::\n    .byte 0\n'
        if n in outdoor:
            kind=outdoor[n][1];comp,grid=compiled[kind];w,h=comp['W'],comp['H']
            lname='LAYOUT_'+id_;m.update(layout=lname,weather='WEATHER_SUNNY',map_type='MAP_TYPE_ROUTE' if kind=='route31' else 'MAP_TYPE_CITY',show_map_name=True,allow_cycling=True)
            folder=game/f'data/layouts/{n}';folder.mkdir(parents=True,exist_ok=True)
            (folder/'map.bin').write_bytes(grid.astype('<u2').tobytes())
            # A primary woodland border, independent of all secondary palette changes.
            border=(game/'data/layouts/CherrygroveRoute30Approach/border.bin').read_bytes();(folder/'border.bin').write_bytes(border)
            entry=dict(id=lname,name=n+'_Layout',width=w,height=h,primary_tileset='gTileset_CherrygrovePrimary',secondary_tileset=symbols[kind],border_filepath=f'data/layouts/{n}/border.bin',blockdata_filepath=f'data/layouts/{n}/map.bin',build_target='emerald',layout_version='emerald')
            layouts_data['layouts']=[l for l in layouts_data['layouts'] if l['id']!=lname]+[entry]
            texts={'Institute':'ELM POKéMON INSTITUTE\\nRECEPTION AND RESEARCH', 'Town':'NEW BARK TOWN\\nCHERRYGROVE CITY - WEST', 'Annex':'RESEARCH ANNEX\\nSTAFF ACCESS', 'Coast':'COASTAL OBSERVATION TERRACE', 'Route':'ROUTE 31\\nVIOLET CITY - WEST', 'Cave':'DARK CAVE\\nTAKE CARE IN THE DARK', 'Violet':'VIOLET CITY\\nEAST ENTRANCE', 'University':'VIOLET UNIVERSITY\\nCITY BEYOND THIS ENTRANCE'}
            for label,x,y in comp['signs']:
                sym=n+'_'+label;m['bg_events'].append(dict(type='sign',x=x,y=y,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script=sym))
                scripts+=f'\n{sym}::\n    msgbox {sym}_Text, MSGBOX_SIGN\n    end\n\n{sym}_Text:\n    .string "{texts[label]}$"\n'
        elif n=='NewBarkInstitute':m.update(layout='LAYOUT_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB',music='MUS_BIRCH_LAB')
        elif n=='VioletEastGate':
            donor=next(l for l in layouts_data['layouts'] if l['id']=='LAYOUT_ROUTE110_SEASIDE_CYCLING_ROAD_ENTRANCE')
            layout=dict(donor,id='LAYOUT_VIOLET_EAST_GATE',name='VioletEastGate_Layout',build_target='emerald')
            layouts_data['layouts']=[l for l in layouts_data['layouts'] if l['id']!=layout['id']]+[layout]
            m.update(layout=layout['id'],music='MUS_ROUTE101')
        elif n=='DarkCaveEntrance':
            # A bounded entrance room, not the whole donor tunnel or its campaign.
            donor=next(l for l in layouts_data['layouts'] if l['id']=='LAYOUT_RUSTURF_TUNNEL')
            raw=np.frombuffer((game/donor['blockdata_filepath']).read_bytes(),dtype='<u2').reshape(donor['height'],donor['width'])
            grid=raw[:12,:14].copy();wall=int(raw[0,0])|0xC00
            grid[:4,:]=wall;grid[:,13]=wall;grid[11,:]=wall
            folder=game/'data/layouts/DarkCaveEntrance';folder.mkdir(parents=True,exist_ok=True)
            (folder/'map.bin').write_bytes(grid.astype('<u2').tobytes())
            (folder/'border.bin').write_bytes((game/donor['border_filepath']).read_bytes())
            layout=dict(donor,id='LAYOUT_DARK_CAVE_ENTRANCE',name='DarkCaveEntrance_Layout',width=14,height=12,border_filepath='data/layouts/DarkCaveEntrance/border.bin',blockdata_filepath='data/layouts/DarkCaveEntrance/map.bin')
            layouts_data['layouts']=[l for l in layouts_data['layouts'] if l['id']!=layout['id']]+[layout]
            m.update(layout=layout['id'],music='MUS_CAVE_OF_ORIGIN',map_type='MAP_TYPE_UNDERGROUND')
        else:m['layout']='LAYOUT_HOUSE1'
        if n=='NewBarkTown':
            for local,(x,y,movement,text) in enumerate([(30,15,'WALK_LEFT_AND_RIGHT',"These supplies go to the annex.\\nPlease leave the path clear."),(19,18,'FACE_UP',"Professor ELM's reception is open.\\nThe research wing is for staff.")],1):
                label=f'{n}_Researcher{local}'
                m['object_events'].append(dict(local_id=f'LOCALID_NEW_BARK_RESEARCHER_{local}',graphics_id='OBJ_EVENT_GFX_SCIENTIST_1',x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_'+movement,movement_range_x=1,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=label,flag='0'))
                scripts+=f'\n{label}::\n    msgbox {label}_Text, MSGBOX_NPC\n    end\n\n{label}_Text:\n    .string "{text}$"\n'
        if n=='NewBarkInstitute':
            label=n+'_Reception'
            m['object_events'].append(dict(local_id='LOCALID_NEW_BARK_RECEPTION',graphics_id='OBJ_EVENT_GFX_SCIENTIST_1',x=9,y=9,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=label,flag='0'))
            scripts+=f'\n{label}::\n    msgbox {label}_Text, MSGBOX_NPC\n    end\n\n{label}_Text:\n    .string "Welcome to ELM\'s institute.\\nReception is just ahead.$"\n'
        save_json(game/f'data/maps/{n}/map.json',m);(game/f'data/maps/{n}/scripts.inc').write_text(scripts)
    save_json(game/'data/layouts/layouts.json',layouts_data)
    # Preserve original route events and original Cherrygrove connection offsets.
    for name,dest,direction,offset in [('CherrygroveRoute29Approach','NEW_BARK_TOWN','right',0),('CherrygroveRoute30Approach','JOHTO_ROUTE31','up',-28)]:
        p=game/f'data/maps/{name}/map.json';m=load_json(p);m['connections']=[c for c in m['connections'] if c['map']!='MAP_'+dest]+[connection(dest,direction,offset)];save_json(p,m)
    p=game/'data/event_scripts.s';s=p.read_text()
    for n in all_names:
        inc=f'.include "data/maps/{n}/scripts.inc"'
        if inc not in s:s+='\n'+inc+'\n'
    p.write_text(s)
    p=game/'src/apocrypha_map_proof.c';s=p.read_text()
    # Append only test entry points; keep original 0..10 indexes stable.
    start=s.index('const u16 sMapProofMaps[]');end=s.index(';',start)
    s=s[:start]+'const u16 sMapProofMaps[] = {'+', '.join(['MAP_'+v for v in ['CHERRYGROVE_CITY','CHERRYGROVE_PLAYER_HOUSE','CHERRYGROVE_GOLD_HOUSE','CHERRYGROVE_NEIGHBOR_HOUSE','CHERRYGROVE_TRANSPLANT_HOUSE','CHERRYGROVE_MART','CHERRYGROVE_POKEMON_CENTER','CHERRYGROVE_PLAYER_BEDROOM','CHERRYGROVE_CENTER_UPSTAIRS','CHERRYGROVE_ROUTE29_APPROACH','CHERRYGROVE_ROUTE30_APPROACH']+all_ids])+'}'+s[end:]
    import re
    s=re.sub(r'\(region & 255\) % \d+',f'(region & 255) % {11+len(all_ids)}',s);p.write_text(s)

def main():
    game=Path(sys.argv[1]).resolve();assert game!=ROOT/'game'
    if not (game/'data/tilesets/secondary/claude_route30').exists():raise SystemExit('Apply the preserved town and routes patches first.')
    OUT.mkdir(parents=True,exist_ok=True)
    # Idempotent generation requires the untouched route baseline; refuse to erase later edits.
    if (game/'data/maps/NewBarkTown').exists():raise SystemExit('Use a fresh route baseline; existing New Bark edits are never overwritten.')
    base,shared=town.build_assets()
    pf=game/'data/tilesets/primary/cherrygrove/tiles.png'
    primary=routes.Primary(game,78,511)
    before=pf.read_bytes();compiled={};report={}
    symbols=register_tilesets(game,['new_bark','route31','violet_entrance'])
    for kind,plan in [('new_bark',L.new_bark()),('route31',L.route31()),('violet_entrance',L.violet_entrance())]:
        a,pals=assets(kind,base,shared);comp=compose(kind,plan,a)
        if kind=='new_bark':
            packer,grid,join=pack_connected(game,kind,comp,pals,'CherrygroveRoute29Approach','claude_route29',(98,0),(0,16),(97,16),primary)
        elif kind=='route31':
            packer,grid,join=pack_connected(game,kind,comp,pals,'CherrygroveRoute30Approach','claude_route30',(-28,-30),(38,29),(10,0),primary)
        else:
            packer=routes.RoutePacker(pals,primary);grid=np.zeros(plan.shape,np.uint16);pack_cells(comp,packer,pals,np.ones(plan.shape,bool),grid);join={}
        assert packer.conflicts==0,(kind,packer.conflict_cells[:5])
        nt,nb=routes.write_route_tileset(game,kind,packer,pals)
        report[kind]=dict(width=comp['W'],height=comp['H'],secondary_tile_span=nt,secondary_metatile_span=nb,secondary_tiles_used=len(packer.sec_tiles),secondary_metatiles_used=len(packer.sec_blocks),doors=comp['doors'],**join)
        compiled[kind]=(comp,grid)
        Tileset(game,kind,'cherrygrove').map_image(grid.ravel().tolist(),comp['W']).save(OUT/(kind+'-overview.png'))
        (OUT/(kind+'-collision.txt')).write_text('\n'.join(''.join('#' if c else '.' for c in row) for row in comp['solid'])+'\n')
        np.save(OUT/(kind+'-plan.npy'),plan)
    assert before==pf.read_bytes(),'shared primary changed'
    write_maps(game,load_json(game/'data/layouts/layouts.json'),compiled,symbols)
    save_json(OUT/'build-report.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
