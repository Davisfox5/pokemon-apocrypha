"""Narrow native additions: visitable interiors and facade-specific door frames.

The house/shop/foyer interiors are explicitly review proposals made from existing
Gen 3 interior modules, not claims of HGSS interior reconstruction. No campaign
scripts, trainer battles, item rewards or economy are imported from donors.
"""
from pathlib import Path
import copy, json, struct, sys
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import clean_native as N
import check_convert as C
import build as B

ROOT=HERE.parents[3]
OUT=ROOT/'gba/art/mahogany-town/evidence/clean'
NEW=[('MahoganySouvenirShop','MAP_MAHOGANY_SOUVENIR_SHOP',(16,14),'LAYOUT_MART',(3,7)),
     ('MahoganyEastHouse','MAP_MAHOGANY_EAST_HOUSE',(25,14),'LAYOUT_HOUSE1',(3,8)),
     ('MahoganyGymLobby','MAP_MAHOGANY_GYM_LOBBY',(11,23),'LAYOUT_MAHOGANY_GYM_LOBBY',(5,9)),
     ('MahoganyRoute43Gate','MAP_MAHOGANY_ROUTE43_GATE',(12,5),'LAYOUT_MAHOGANY_ROUTE43_GATE',(3,8))]

def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')

def add_layout(g,layouts,name,src,grid):
    d=g/'data/layouts'/name;d.mkdir(parents=True,exist_ok=True)
    (d/'map.bin').write_bytes(grid.astype('<u2').tobytes())
    (d/'border.bin').write_bytes((g/src['border_filepath']).read_bytes())
    l=copy.deepcopy(src);l.update(id='LAYOUT_'+''.join('_'+c if c.isupper() and i else c for i,c in enumerate(name)).upper(),
        name=name+'_Layout',width=grid.shape[1],height=grid.shape[0],build_target='emerald',border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin')
    layouts['layouts'].append(l)

def main(g):
    OUT.mkdir(parents=True,exist_ok=True)
    maps=g/'data/maps'; groups=read(maps/'map_groups.json');layouts=read(g/'data/layouts/layouts.json')
    if any(n in groups['gMapGroup_Cherrygrove'] for n, *_ in NEW):raise SystemExit('Entrances already installed; edit native files directly.')
    by={l['id']:l for l in layouts['layouts']}
    # Ice-coloured Gen 3 foyer. Static floor, full walls and complete statues;
    # no copied Sootopolis stairs, falling-ice behavior, trainer or badge scripts.
    src=by['LAYOUT_SOOTOPOLIS_CITY_GYM_1F']
    old=np.frombuffer((g/src['blockdata_filepath']).read_bytes(),'<u2').reshape(26,17)
    room=np.tile(old[23,3:14],(10,1))
    room[:,3]=0x323e;room[:,7]=0x323e
    room[0]=old[21,3:14];room[0,2:9]=0x0652
    room[1]=old[22,3:14];room[1,8]=0x3247
    room[2:9,2:9]=0x323e
    room[9]=old[25,3:14]
    for x in (3,7):room[6:9,x:x+2]=old[23:26,6:8]
    room[9,2:5]=0x323e;room[9,7:9]=0x323e
    room[9,5:7]=[0x0006,0x0007]
    add_layout(g,layouts,'MahoganyGymLobby',src,room)
    # A native gatehouse vestibule; its northern connection awaits Route 43.
    src=by['LAYOUT_HOUSE1']
    gate=np.frombuffer((g/src['blockdata_filepath']).read_bytes(),'<u2').reshape(9,10).copy()
    gate[4:6,2:7]=0x323e
    add_layout(g,layouts,'MahoganyRoute43Gate',src,gate)
    write(g/'data/layouts/layouts.json',layouts)
    town=read(maps/'MahoganyTown/map.json')
    template=read(maps/'CherrygroveGardenHouse/map.json')
    ids={}
    for name,mid,(x,y),layout,(ix,iy) in NEW:
        warp=len(town['warp_events']);ids[name]=len(groups['gMapGroup_Cherrygrove'])
        groups['gMapGroup_Cherrygrove'].append(name)
        town['warp_events'].append(dict(x=x,y=y,elevation=0,dest_map=mid,dest_warp_id='0'))
        if name=='MahoganyRoute43Gate':town['warp_events'].append(dict(x=13,y=5,elevation=0,dest_map=mid,dest_warp_id='1'))
        m=copy.deepcopy(template);m.update(id=mid,name=name,layout=layout,region_map_section='MAPSEC_MAHOGANY_TOWN',music='MUS_GYM' if 'Gym' in name else 'MUS_VERDANTURF',warp_events=[],object_events=[],bg_events=[],coord_events=[])
        for dx in (0,1):m['warp_events'].append(dict(x=ix+dx,y=iy,elevation=0,dest_map='MAP_MAHOGANY_TOWN',dest_warp_id=str(warp+(dx if 'Gate' in name else 0))))
        if 'Gate' in name:
            m['warp_events'][1]['x']=4
        write(maps/name/'map.json',m)
        (maps/name/'scripts.inc').write_text(f'{name}_MapScripts::\n    .byte 0\n')
        p=g/'data/event_scripts.s';s=p.read_text();s+=f'\n.include "data/maps/{name}/scripts.inc"\n';p.write_text(s)
    write(maps/'map_groups.json',groups);write(maps/'MahoganyTown/map.json',town)
    # Enable only the actual entrances; duplicate metatiles so unrelated cells
    # sharing the prior blocked entry keep their original behavior and layers.
    dirs,pats,metas,pals,grid=N.read(g)
    attrs=np.frombuffer((dirs[1]/'metatile_attributes.bin').read_bytes(),'<u2').tolist()
    sm=np.frombuffer((dirs[1]/'metatiles.bin').read_bytes(),'<u2').reshape(-1,8).tolist()
    for x,y in [(16,14),(25,14),(11,23),(12,5),(13,5)]:
        old=int(grid[y,x]&1023);ents,attr=metas[old];sm.append(ents);attrs.append((attr&~255)|(96 if y==5 else 105));new=512+len(sm)-1
        grid[y,x]=(3<<12)|new
    (dirs[1]/'metatiles.bin').write_bytes(np.array(sm,'<u2').tobytes());(dirs[1]/'metatile_attributes.bin').write_bytes(np.array(attrs,'<u2').tobytes())
    (g/'data/layouts/MahoganyTown/map.bin').write_bytes(grid.astype('<u2').tobytes())
    # Existing test adapter receives appended stable IDs, never a new bootstrap
    # or a changed new-game location in shared source.
    p=g/'src/apocrypha_map_proof.c';s=p.read_text();anchor='MAP_MAHOGANY_CENTER_UPSTAIRS};'
    assert anchor in s;s=s.replace(anchor,'MAP_MAHOGANY_CENTER_UPSTAIRS, '+', '.join(r[1] for r in NEW)+'};');p.write_text(s)
    # Every animated facade keeps its native static context. Three moving-door
    # frames use the pair's existing palettes; closed frames restore actual metas.
    native=C.decode(g)[0];decl=['extern const struct Tileset gTileset_MahoganyTown;','extern const struct Tileset gTileset_MahoganyPrimary;'];table=[]
    quads=[(x+dx,y+dy) for x,y in [(0,0),(0,16),(16,0),(16,16)] for dx,dy in [(0,0),(8,0),(0,8),(8,8)]]
    for tag,x,y,width in [('Center',22,23,16),('Shop',16,14,22),('House',25,14,22),('Gym',11,23,18)]:
        closed=native[(y-1)*16:(y+1)*16,x*16:(x+2)*16].copy();fs=[]
        # Door panels slide inward; the surrounding wall and lintel never move.
        top=12 if tag=='Center' else 8;bottom=30
        for n in (1,2,3):
            f=closed.copy();f[top:bottom,1:width]=[32,40,48]
            keep=(width-1)*(3-n)//3
            if keep:f[top:bottom,1:keep+1]=closed[top:bottom,np.linspace(1,width-1,keep).astype(int)]
            fs.append(f)
        banks=[]
        for qx,qy in quads:
            px=np.concatenate([f[qy:qy+8,qx:qx+8].reshape(-1,3) for f in fs]).astype(int)
            costs=[((px[:,None,:]-pals[b,1:].astype(int))**2).sum(-1).min(-1).sum() for b in range(13)]
            banks.append(int(np.argmin(costs)))
        raw=bytearray()
        for f in fs:
            for (qx,qy),bank in zip(quads,banks):
                px=f[qy:qy+8,qx:qx+8].reshape(-1,3).astype(int);ix=((px[:,None,:]-pals[bank,1:].astype(int))**2).sum(-1).argmin(-1)+1
                raw.extend(int(ix[k])|(int(ix[k+1])<<4) for k in range(0,64,2))
        path=f'graphics/door_anims/mahogany/{tag}.4bpp';p=g/path;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(raw)
        decl.append(f'static const u8 sMahoganyDoor_{tag}[] = INCBIN_U8("{path}");\nstatic const u8 sMahoganyDoorPal_{tag}[20] = {{'+','.join(map(str,banks+[0]*4))+'};')
        mid=int(grid[y,x]&1023);sym='MahoganyPrimary' if mid<512 else 'MahoganyTown'
        table.append(f'    {{.metatileNum={mid}, .tileset=&gTileset_{sym}, .sound=DOOR_SOUND_SLIDING, .size=DOOR_SIZE_2x2_LEFT, .tiles=sMahoganyDoor_{tag}, .palettes=sMahoganyDoorPal_{tag}}},')
    p=g/'src/field_door.c';s=p.read_text();marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{';s=s.replace(marker,'// Mahogany native facade doors\n'+'\n'.join(decl)+'\n'+marker+'\n'+'\n'.join(table));p.write_text(s)
    Image.fromarray(native).save(OUT/'native.png')
    (OUT/'entrances.json').write_text(json.dumps(dict(appended_map_ids=ids,door_animation_count=4,
        traversal_changes=[[16,14],[25,14],[11,23],[12,5],[13,5]],
        interior_scope='Native Gen 3 room proposals; no campaign, trainers, rewards or shop inventory',
        connections_not_built=['Route 42','Route 43 beyond gate vestibule','Route 44']),indent=2)+'\n')
    print(json.dumps(ids))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
