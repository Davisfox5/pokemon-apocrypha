"""Install the fresh exterior and approved Center without touching other maps."""
from pathlib import Path
import copy,json,sys,numpy as np
from build import SRC,N,O

def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(d,indent=2)+'\n')

def main(g):
    groups=read(g/'data/maps/map_groups.json')
    if 'MahoganyTown' in groups['gMapGroup_Cherrygrove']:raise SystemExit('Fresh installer refuses an existing Mahogany layout. Edit native source directly.')
    names=['MahoganyTown','MahoganyPokemonCenter','MahoganyCenterUpstairs'];ids=['MAP_MAHOGANY_TOWN','MAP_MAHOGANY_POKEMON_CENTER','MAP_MAHOGANY_CENTER_UPSTAIRS']
    groups['gMapGroup_Cherrygrove']+=names;write(g/'data/maps/map_groups.json',groups)
    for kind,sym in [('primary','MahoganyRebuildPrimary'),('secondary','MahoganyRebuild')]:
        d=g/'data/tilesets'/kind/'mahogany_rebuild'
        for n in range(13,16):(d/'palettes'/f'{n:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
        with (g/'src/data/tilesets/graphics.h').open('a') as f:
            f.write(f'\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/mahogany_rebuild/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'    INCGFX_U16("data/tilesets/{kind}/mahogany_rebuild/palettes/{n:02}.pal", ".gbapal"),\n' for n in range(16))+'};\n')
        with (g/'src/data/tilesets/metatiles.h').open('a') as f:
            f.write(f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/mahogany_rebuild/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/mahogany_rebuild/metatile_attributes.bin");\n')
        with (g/'src/data/tilesets/headers.h').open('a') as f:
            f.write(f'\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"FALSE" if kind=="primary" else "TRUE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')
    grid=np.load(SRC/'map-metatiles.npy');z=np.load(SRC/'layers.npz');solid=z['solid'].copy()
    # Only the Center is an implemented destination in this exterior-focused
    # reconstruction. Preserve closed buildings until their actual interiors exist.
    for x,y in [(16,14),(25,14),(11,23),(12,5),(13,5)]:solid[y+O,x+O]=1
    # Shared C06's roof overhang and the row freed by its shorter native profile.
    solid[18+O:20+O,20+O:25+O]=0
    p=g/'data/layouts/MahoganyTown';p.mkdir(exist_ok=True)
    cells=grid.astype(np.uint16)|(solid.astype(np.uint16)<<10)|(3<<12)
    (p/'map.bin').write_bytes(cells.astype('<u2').tobytes());(p/'border.bin').write_bytes(np.array([grid[0,0],grid[0,1],grid[1,0],grid[1,1]],'<u2').tobytes())
    layouts=read(g/'data/layouts/layouts.json');layouts['layouts'].append(dict(id='LAYOUT_MAHOGANY_TOWN',name='MahoganyTown_Layout',width=N,height=N,primary_tileset='gTileset_MahoganyRebuildPrimary',secondary_tileset='gTileset_MahoganyRebuild',border_filepath='data/layouts/MahoganyTown/border.bin',blockdata_filepath='data/layouts/MahoganyTown/map.bin',build_target='emerald',layout_version='emerald'));write(g/'data/layouts/layouts.json',layouts)
    sec=g/'src/data/region_map/region_map_sections.json';regions=read(sec)
    s=copy.deepcopy(regions['map_sections'][-1]);s.update(id='MAPSEC_MAHOGANY_TOWN',name='MAHOGANY TOWN');regions['map_sections'].append(s);write(sec,regions)
    p=g/'include/regions.h';text=p.read_text();anchor='    case MAPSEC_CHERRYGROVE_CITY: return REGION_JOHTO;';text=text.replace(anchor,anchor+'\n    case MAPSEC_MAHOGANY_TOWN: return REGION_JOHTO;');p.write_text(text)
    town=read(g/'data/maps/CherrygroveCity/map.json');town.update(id=ids[0],name=names[0],layout='LAYOUT_MAHOGANY_TOWN',region_map_section='MAPSEC_MAHOGANY_TOWN',music='MUS_VERDANTURF',connections=None,object_events=[],warp_events=[dict(x=22+O,y=23+O,elevation=0,dest_map=ids[1],dest_warp_id='0')],coord_events=[],bg_events=[])
    for label,x,y in [('TownSign',4,12),('ShopSign',14,14),('GymSign',8,24)]:town['bg_events'].append(dict(type='sign',x=x+O,y=y+O,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script='MahoganyTown_'+label))
    for k in ('build_target','region'):town[k]=town.pop(k)
    write(g/'data/maps/MahoganyTown/map.json',town)
    pory='mapscripts MahoganyTown_MapScripts {}\n'
    for label,msg in [('TownSign','MAHOGANY TOWN\\nHome of the Ninja'),('ShopSign','MAHOGANY SOUVENIR SHOP'),('GymSign','MAHOGANY POKEMON GYM')]:
        pory+=f'\nscript MahoganyTown_{label} {{\n    msgbox(MahoganyTown_{label}_Text, MSGBOX_SIGN)\n    end\n}}\ntext MahoganyTown_{label}_Text {{\n    "{msg}"\n}}\n'
    (g/'data/maps/MahoganyTown/scripts.pory').write_text(pory)
    for src,dst in [('CherrygrovePokemonCenter','MahoganyPokemonCenter'),('CherrygroveCenterUpstairs','MahoganyCenterUpstairs')]:
        m=read(g/'data/maps'/src/'map.json');text=json.dumps(m)
        for a,b in [('CherrygrovePokemonCenter','MahoganyPokemonCenter'),('CherrygroveCenterUpstairs','MahoganyCenterUpstairs'),('MAP_CHERRYGROVE_POKEMON_CENTER',ids[1]),('MAP_CHERRYGROVE_CENTER_UPSTAIRS',ids[2]),('MAP_CHERRYGROVE_CITY',ids[0]),('MAPSEC_CHERRYGROVE_CITY','MAPSEC_MAHOGANY_TOWN')]:text=text.replace(a,b)
        m=json.loads(text)
        for w in m['warp_events']:
            if w['dest_map']==ids[0]:w['dest_warp_id']='0'
        write(g/'data/maps'/dst/'map.json',m)
        (g/'data/maps'/dst/'scripts.inc').write_text((g/'data/maps'/src/'scripts.inc').read_text().replace(src,dst))
    with (g/'data/event_scripts.s').open('a') as f:
        for name in names:f.write(f'\n.include "data/maps/{name}/scripts.inc"\n')
    p=g/'src/apocrypha_map_proof.c';text=p.read_text();text=text.replace('MAP_CHERRYGROVE_REGIONAL_PREVIEW_30};','MAP_CHERRYGROVE_REGIONAL_PREVIEW_30, '+', '.join(ids)+'};');p.write_text(text)
    print('Fresh Mahogany source installed; other map IDs/tilesets preserved.')

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
