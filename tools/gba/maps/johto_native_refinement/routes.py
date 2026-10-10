"""Correct route art outside the protected Cherrygrove camera windows."""
import sys,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from claude_routes import build as r,layouts as L,seams
from claude_cherrygrove import layout as TL
from johto_polish.build import pack_cells
from johto_connections import build as b
from johto_native_refinement import art
from tiles import Tileset
OUT=art.OUT

def build(game):
    original_compose=r.compose
    def native_compose(route,g,A):
        comp=original_compose(route,g,A);mc=comp['canvas']
        # Rebuild only forest pixels. Preserve all authored objects and terrain.
        old=mc.bank.copy();ix=mc.idx.copy();mc.bank[:]=-1;mc.idx[:]=0
        forest_plan=comp['plan'] if 'plan' in comp else g
        for px,py,c in art.forest(forest_plan,A['tree']):
            if route==29 and px//16<=L.R29_BLOSSOM_MAX_X and c is A['tree']:
                c=A['blossom']
            mc.blit(c,px,py)
        objects=(old>=0)&~np.isin(old,[3,10])
        mc.bank[objects]=old[objects];mc.idx[objects]=ix[objects]
        comp['solid'][forest_plan=='T']=True
        return comp
    r.compose=native_compose
    base,pal=r.town.build_assets();raw=art.architecture(base)
    r.art.tall_slices=art.tall_slices;r.art.tall_cell=art.tall_cell
    r.art.orange_flowers=lambda route:base['daisies'].to_rgba()
    r.art.gate=lambda:raw['gate29'];r.art.mr_pokemon_house=lambda:raw['mr_pokemon'];r.art.berry_house=lambda:raw['berry_house']
    primary=r.Primary(game,78,511);report={}
    tm,ts=seams.read_layout(game,'CherrygroveCity',TL.W,TL.H)
    for route in (29,30):
        name=f'claude_route{route}';lname=f'CherrygroveRoute{route}Approach'
        g=L.route29() if route==29 else L.route30()
        # A two-cell landing at each stair prevents a dirt path terminating at
        # an unrelated lawn edge. Preserve stair positions and route branches.
        if route==30:
            for _,x,y,dy in L.R30_STAIRS:
                if y>1:g[y-2:y,x:x+2]='P'
                if y+3<len(g):g[y+2:y+4,x:x+2]='P'
        ox,oy=(TL.W,L.R29_TOWN_OFFSET) if route==29 else (L.R30_TOWN_OFFSET,-L.R30_H)
        A0,_,_=r.route_banks(route,base,pal,set());comp0=r.compose(route,g,A0)
        seen=seams.visible_across(seams.reachable(ts,TL.SPAWN),g.shape,ox,oy)
        tw,rw,_=seams.crossing_windows(ts,comp0['solid'],ox,oy);seen|=rw
        townseen=seams.visible_across(seams.reachable(comp0['solid'],(0,16) if route==29 else (8,len(g)-1)),ts.shape,-ox,-oy)|tw
        tiles,blocks,attrs=b.parts(game,name)
        mids={int(m) for m in tm[townseen] if m>=512}
        reserved={e>>12 for mid in mids for e in blocks[mid-512] if e}-set(range(6))-r.SHARED_BANKS
        A,pals,assignment=r.route_banks(route,base,pal,reserved)
        for bank in reserved:pals[bank]=r.Palette(bank,b.palette(game/f'data/tilesets/secondary/{name}/palettes/{bank:02}.pal')[1:],[f'c{i}' for i in range(15)])
        comp=r.compose(route,g,A);mc=comp['canvas']
        # Retain the forest underlayer before composite roofs/grass reach it.
        mc.under_bank=mc.bank.copy();mc.under_idx=mc.idx.copy()
        grid=np.frombuffer((game/f'data/layouts/{lname}/map.bin').read_bytes(),dtype='<u2').reshape(g.shape).copy()
        mids|={int(v&1023) for v in grid[seen] if v&1023>=512}
        packer=r.RoutePacker(pals,primary);packer.reserve(tiles,blocks,attrs,mids)
        pack_cells(comp,packer,pals,~seen,grid)
        nt,nb=r.write_route_tileset(game,name,packer,pals)
        (game/f'data/layouts/{lname}/map.bin').write_bytes(grid.astype('<u2').tobytes())
        decoded=Tileset(game,name,'cherrygrove').map_image(grid.ravel().tolist(),g.shape[1]);decoded.save(OUT/f'route{route}-overview.png')
        expected=np.zeros_like(np.asarray(decoded));visible=mc.bank>=0
        for bank in np.unique(mc.bank):
            if bank>=0:
                m=mc.bank==bank;expected[m]=np.asarray(pals[int(bank)].gba(),dtype='uint8')[mc.idx[m]]
        check=visible&np.repeat(np.repeat(~seen,16,axis=0),16,axis=1)
        errors=np.any(np.asarray(decoded)!=expected,axis=2)&check

        if errors.any():
            ys,xs=np.nonzero(errors);print('ERROR',route,[(int(x),int(y),int(mc.bank[y,x]),expected[y,x].tolist(),np.asarray(decoded)[y,x].tolist()) for y,x in zip(ys[:12],xs[:12])],flush=True)
        assert not errors.any(),(route,int(errors.sum()))
        report[str(route)]={'tiles':nt,'metatiles':nb,'protected_cherrygrove_cells':int(seen.sum()),'scenery_pixels_verified':int(check.sum()),'pixel_errors':int(errors.sum()),'banks':assignment}
    (OUT/'route-build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
