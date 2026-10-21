"""Install the new Cianwood exterior without changing any existing map/layout IDs."""
from pathlib import Path
import sys,json,struct,re
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3];OUT=ROOT/'gba/art/cianwood-city'
sys.path.insert(0,str(HERE.parent))
from tiles import Tileset

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def read(p):return json.loads(p.read_text())

def main(g):
    refresh=(g/'data/maps/CianwoodCity').exists()
    if refresh and '--update-initial-draft' not in sys.argv:raise SystemExit('Cianwood exists: edit native source; never replay over owner edits.')
    z=np.load(OUT/'evidence/packing-work.npz');ids=z['tile_ids'];fl=z['flags'];tiles=z['tiles'];pals=z['palettes']
    assert len(tiles)<=1008,len(tiles)
    entries=(ids|fl).astype('uint16')
    upper=(z['top_ids']|z['top_flags']).astype('uint16')
    w,h=35,42
    # Independent material and traversal planes. Screenshot geometry is traced;
    # hidden HGSS collision is not available and is not claimed as extracted.
    land=Image.new('L',(560,672));d=ImageDraw.Draw(land)
    d.polygon([(0,0),(328,0),(328,160),(320,176),(320,192),(288,208),(256,224),
        (256,256),(280,256),(280,288),(296,304),(320,312),(352,320),(472,320),(472,671),(0,671)],fill=1)
    cliff=Image.new('L',(560,672));d=ImageDraw.Draw(cliff)
    d.polygon([(0,0),(320,0),(320,88),(272,88),(272,128),(240,128),(240,136),
        (176,136),(160,128),(144,128),(144,96),(128,80),(64,80),(48,80),
        (48,192),(96,200),(112,216),(112,240),(128,248),(144,272),(144,344),
        (128,352),(112,368),(112,608),(144,608),(176,624),(176,640),(464,640),(464,672),(0,672)],fill=1)
    lm=z['land'].astype('uint8');cm=z['cliff'].astype('uint8')
    material=np.full((h,w),'sea',dtype=object);solid=np.zeros((h,w),bool);behavior=np.zeros((h,w),np.uint16)
    ledger=[]
    for y in range(h):
        for x in range(w):
            box=np.s_[y*16:y*16+16,x*16:x*16+16]
            if lm[y*16+8,x*16+8]:material[y,x]='sand'
            else:behavior[y,x]=16
            if cm[y*16+8,x*16+8]:material[y,x]='cliff';solid[y,x]=True;behavior[y,x]=0
            if lm[box].min()!=lm[box].max():material[y,x]='shore'
            if material[y,x]=='sand' and z['grass'][box].mean()>.5:material[y,x]='lawn'
    structures=[('north_house',4,5,8,10,(7,9)),('gym',7,22,14,27,(10,26)),
        ('studio',18,21,22,25,(20,24)),('east_house',18,26,22,31,(21,30)),
        ('west_house',7,30,11,35,(10,34)),('pharmacy',16,32,20,37,(17,36)),
        ('center',23,32,28,37,(25,36))]
    for label,x0,y0,x1,y1,door in structures:
        material[y0:y1,x0:x1]=label;solid[y0:y1,x0:x1]=True;behavior[y0:y1,x0:x1]=0
    material[17:20,7:9]='west_cliff_entrance';solid[17:20,7:9]=True;behavior[17:20,7:9]=0
    # Door glass is at source (48..64,79..89) + (352,496): cell (25,36).
    solid[36,25]=False;behavior[36,25]=0x69
    for x,y in [(10,16),(13,27),(17,24),(23,23),(14,30),(20,36)]+[(x,y) for y in (23,26,28,30) for x in (26,27)]:
        solid[y,x]=True;material[y,x]='prop'
    # The offshore barrier is solid to Surf as well as ordinary walking.
    for x,y in [(28,1),(30,0),(33,0),(25,3),(28,3),(21,6),(22,5),(24,5),(26,5),
            (28,5),(25,6),(24,8),(26,10),(27,11),(26,13),(26,15),
            (26,17),(25,18),(25,19),(20,4)]:
        solid[y,x]=True;behavior[y,x]=0;material[y,x]='offshore_rock'
    # Full cliff boundary cells are solid where the visible wall reaches its
    # contact plane; the source overview cannot reveal hidden rear collision.
    for y in range(h):
        for x in range(w):
            if material[y,x] not in ('sea','shore') and (x in (0,w-1) or y in (0,h-1)):solid[y,x]=True
    blocks=[];attrs=[];lookup={};grid=np.zeros((h,w),np.uint16)
    for y in range(h):
        for x in range(w):
            es=tuple(int(entries[y*2+dy,x*2+dx]) for dy,dx in [(0,0),(0,1),(1,0),(1,1)])+tuple(int(upper[y*2+dy,x*2+dx]) for dy,dx in [(0,0),(0,1),(1,0),(1,1)])
            attr=0x1000|int(behavior[y,x]);key=(es,attr)
            if key not in lookup:lookup[key]=len(blocks);blocks.append(es);attrs.append(attr)
            mid=lookup[key];assert mid<1024
            flags=0x3c00 if solid[y,x] else 0x1000 if behavior[y,x]==16 else 0x3000
            grid[y,x]=mid|flags
            box=np.s_[y*16:y*16+16,x*16:x*16+16]
            materials=[]
            if lm[box].any():materials.append('sand')
            if not lm[box].all():materials.append('sea/shore_lip')
            if z['grass'][box].any():materials.append('lawn')
            if cm[box].any():materials.append('cliff_front/side' if z['front'][box].any() else 'cliff_cap')
            if str(material[y,x]) not in ('sea','shore','sand','lawn','cliff'):materials.append(str(material[y,x]))
            ledger.append(dict(x=x,y=y,material=str(material[y,x]),materials=materials,foot='blocked' if solid[y,x] else 'water' if behavior[y,x]==16 else 'open',
                elevation=flags>>12,metatile=mid,behavior=int(behavior[y,x]),
                source_scope='overview trace; hidden collision unverified',mixed_shore=bool(lm[box].min()!=lm[box].max())))
    for part,kind,sym in [(0,'primary','CianwoodPrimary'),(1,'secondary','Cianwood')]:
        folder=g/f'data/tilesets/{kind}/cianwood';folder.mkdir(parents=True,exist_ok=True)
        buf=np.zeros((256,128),np.uint8)
        for i,t in enumerate(tiles[part*512:(part+1)*512]):buf[(i//16)*8:(i//16+1)*8,(i%16)*8:(i%16+1)*8]=t
        im=Image.fromarray(buf,'P');im.putpalette([v for i in range(256) for v in (i,i,i)]);im.save(folder/'tiles.png',bits=4)
        (folder/'palettes').mkdir(exist_ok=True)
        for bank in range(16):
            colors=[(0,0,0)]+[tuple(map(int,v)) for v in pals[bank]] if bank<12 else [(0,0,0)]*16
            text='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n'
            (folder/'palettes'/f'{bank:02}.pal').write_text(text)
        bs=blocks[part*512:(part+1)*512];ats=attrs[part*512:(part+1)*512]
        if not bs:bs=[(0,)*8];ats=[0x1000]
        (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bs))
        (folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(ats),*ats))
        if refresh:continue
        gfx=f'\n// Cianwood City: local tiles and palette banks.\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/cianwood/tiles.png", ".4bpp.fastSmol");\n'
        gfx+=f'const u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/{kind}/cianwood/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n'
        with (g/'src/data/tilesets/graphics.h').open('a') as f:f.write(gfx)
        with (g/'src/data/tilesets/metatiles.h').open('a') as f:f.write(f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/cianwood/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/cianwood/metatile_attributes.bin");\n')
        with (g/'src/data/tilesets/headers.h').open('a') as f:f.write(f'\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"FALSE" if part==0 else "TRUE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')
    if refresh:
        (g/'data/layouts/CianwoodCity/map.bin').write_bytes(grid.tobytes())
        write(OUT/'evidence/material-traversal-ledger.json',dict(registration=dict(origin=[0,0],scale=1,source=[550,671],native=[560,672],padding=[10,1]),cells=ledger))
        c=read(OUT/'evidence/capacity.json');c.update(tiles=len(tiles),metatiles=len(blocks));write(OUT/'evidence/capacity.json',c)
        t=Tileset(g,'cianwood','cianwood');t.map_image(grid.ravel().tolist(),w).save(OUT/'evidence/native.png')
        print('Updated initial draft:',len(tiles),'tiles;',len(blocks),'metatiles');return
    folder=g/'data/layouts/CianwoodCity';folder.mkdir();(folder/'map.bin').write_bytes(grid.tobytes())
    (folder/'border.bin').write_bytes(struct.pack('<4H',*[int(grid[1,1])]*4))
    layouts=read(g/'data/layouts/layouts.json');layouts['layouts'].append(dict(id='LAYOUT_CIANWOOD_CITY',name='CianwoodCity_Layout',width=w,height=h,primary_tileset='gTileset_CianwoodPrimary',secondary_tileset='gTileset_Cianwood',border_filepath='data/layouts/CianwoodCity/border.bin',blockdata_filepath='data/layouts/CianwoodCity/map.bin',build_target='emerald',layout_version='emerald'));write(g/'data/layouts/layouts.json',layouts)
    m=read(g/'data/maps/VioletCityEntrance/map.json');m.update(id='MAP_CIANWOOD_CITY',name='CianwoodCity',layout='LAYOUT_CIANWOOD_CITY',region_map_section='MAPSEC_CIANWOOD_CITY',music='MUS_LILYCOVE',connections=None,object_events=[],warp_events=[dict(x=25,y=36,elevation=0,dest_map='MAP_CIANWOOD_POKEMON_CENTER',dest_warp_id='0')],bg_events=[])
    for x,y,script in [(10,16,'CitySign'),(13,27,'GymSign'),(17,24,'StudioSign')]:m['bg_events'].append(dict(type='sign',x=x,y=y,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script='CianwoodCity_'+script))
    write(g/'data/maps/CianwoodCity/map.json',m)
    scripts='CianwoodCity_MapScripts::\n    .byte 0\n'
    for label,text in [('CitySign','CIANWOOD CITY'),('GymSign','CIANWOOD CITY POKEMON GYM'),('StudioSign','CIANWOOD PHOTO STUDIO')]:
        scripts+=f'\nCianwoodCity_{label}::\n    msgbox CianwoodCity_{label}_Text, MSGBOX_SIGN\n    end\n\nCianwoodCity_{label}_Text:\n    .string "{text}$"\n'
    (g/'data/maps/CianwoodCity/scripts.inc').write_text(scripts)
    names=['CianwoodCity']
    for old,new in [('CherrygrovePokemonCenter','CianwoodPokemonCenter'),('CherrygroveCenterUpstairs','CianwoodCenterUpstairs')]:
        mm=read(g/f'data/maps/{old}/map.json');ss=(g/f'data/maps/{old}/scripts.inc').read_text()
        text=json.dumps(mm).replace(old,new).replace('MAP_CHERRYGROVE_POKEMON_CENTER','MAP_CIANWOOD_POKEMON_CENTER').replace('MAP_CHERRYGROVE_CENTER_UPSTAIRS','MAP_CIANWOOD_CENTER_UPSTAIRS').replace('MAP_CHERRYGROVE_CITY','MAP_CIANWOOD_CITY').replace('MAPSEC_CHERRYGROVE_CITY','MAPSEC_CIANWOOD_CITY')
        mm=json.loads(text)
        if new=='CianwoodPokemonCenter':
            for warp in mm['warp_events']:
                if warp['dest_map']=='MAP_CIANWOOD_CITY':warp['dest_warp_id']='0'
        write(g/f'data/maps/{new}/map.json',mm);(g/f'data/maps/{new}/scripts.inc').write_text(ss.replace(old,new));names.append(new)
    groups=read(g/'data/maps/map_groups.json');groups['gMapGroup_Cherrygrove'].extend(names);write(g/'data/maps/map_groups.json',groups)
    with (g/'data/event_scripts.s').open('a') as f:
        for n in names:f.write(f'\n.include "data/maps/{n}/scripts.inc"\n')
    p=g/'src/data/region_map/region_map_sections.json';r=read(p);sec=dict(r['map_sections'][-1]);sec.update(id='MAPSEC_CIANWOOD_CITY',name='CIANWOOD CITY');r['map_sections'].append(sec);write(p,r)
    p=g/'include/regions.h';s=p.read_text();s=s.replace('    case MAPSEC_CHERRYGROVE_CITY:', '    case MAPSEC_CIANWOOD_CITY: return REGION_JOHTO;\n    case MAPSEC_CHERRYGROVE_CITY:');p.write_text(s)
    p=g/'src/apocrypha_map_proof.c';s=p.read_text();s=s.replace('MAP_CHERRYGROVE_REGIONAL_PREVIEW_30};','MAP_CHERRYGROVE_REGIONAL_PREVIEW_30, MAP_CIANWOOD_CITY, MAP_CIANWOOD_POKEMON_CENTER, MAP_CIANWOOD_CENTER_UPSTAIRS};');p.write_text(s)
    write(OUT/'evidence/material-traversal-ledger.json',dict(registration=dict(origin=[0,0],scale=1,source=[550,671],native=[560,672],padding=[10,1]),cells=ledger))
    write(OUT/'evidence/capacity.json',dict(tiles=len(tiles),tile_limit=1008,metatiles=len(blocks),metatile_limit=1024,palette_banks=12,map_ids={n:groups['gMapGroup_Cherrygrove'].index(n) for n in names}))
    t=Tileset(g,'cianwood','cianwood');t.map_image(grid.ravel().tolist(),w).save(OUT/'evidence/native.png')
    print('Installed Cianwood:',len(tiles),'tiles;',len(blocks),'metatiles')

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
