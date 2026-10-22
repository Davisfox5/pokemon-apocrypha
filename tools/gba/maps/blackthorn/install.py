"""Install the new Blackthorn City exterior and its Center and Mart into an engine checkout.

First authoring only: refuses to run if any Blackthorn map already exists, so it can
never replay over owner edits. Existing map, layout and tileset IDs are untouched;
new maps are appended to gMapGroup_Cherrygrove.

    python3 tools/gba/maps/blackthorn/install.py ENGINE_CHECKOUT
    python3 tools/gba/maps/blackthorn/stream.py ENGINE_CHECKOUT     # then derive the city view
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import build as B                                   # noqa: E402

EV = B.EV
SECTIONS = B.SECTIONS
W = B.W

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

# Section-local coordinates of the HGSS events (city row minus section start row).
SIGNS = [  # HGSS bg events with text that names a place; the tutor-house and trainer-tip signs stay unscripted props
    ('CitySign', (52, 42), 'BLACKTHORN CITY\\nA Quiet Mountain Retreat'),
    ('GymSign', (26, 25), 'BLACKTHORN CITY POKéMON GYM'),
    ('DenSign', (31, 6), "DRAGON'S DEN AHEAD"),
]
DOORS = [  # (cell, destination map, destination warp)
    ((B.CENTER_ORIGIN[0] + B.CENTER_DOOR[0], B.CENTER_ORIGIN[1] + B.CENTER_DOOR[1]), 'MAP_BLACKTHORN_POKEMON_CENTER', '0'),
    ((B.MART_ORIGIN[0] + B.MART_DOOR[0], B.MART_ORIGIN[1] + B.MART_DOOR[1]), 'MAP_BLACKTHORN_MART', '0'),
]
INTERIORS = [('CherrygrovePokemonCenter', 'BlackthornPokemonCenter'), ('CherrygroveCenterUpstairs', 'BlackthornCenterUpstairs'),
             ('CherrygroveMart', 'BlackthornMart')]

def section_of(y):
    return next(i for i, (_, y0, y1) in enumerate(SECTIONS) if y0 <= y < y1)

def jasc(colors):
    return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'

def main(g):
    names = [n for n, _, _ in SECTIONS]
    if any((g / 'data/maps' / n).exists() for n in names + [b for _, b in INTERIORS]):
        raise SystemExit('Blackthorn maps exist: edit native source; never replay over owner edits.')
    z = np.load(EV / 'packing-work.npz')
    entries, attr, pats, pal = z['entries'], z['attr'], z['patterns'], z['palettes']
    coll, elev = z['collision'], z['elevation']
    center_pal = (g / 'data/tilesets/secondary/cherrygrove/palettes/08.pal').read_text()
    mart_pal = (B.SRC / 'shared-art/poke-mart.pal').read_text().replace('\r\n', '\n')
    assert B.read_pal(B.SRC / 'shared-art/pokemon-center.pal') == B.read_pal(g / 'data/tilesets/secondary/cherrygrove/palettes/08.pal')
    gfx = metas = heads = ''
    layouts = read(g / 'data/layouts/layouts.json')
    report = []
    for si, (name, y0, y1) in enumerate(SECTIONS):
        sub, sat = entries[y0:y1], attr[y0:y1]
        h = y1 - y0
        used = sorted(set((sub & 0xFFFF).ravel().tolist()) | {0})
        lid = {p: i for i, p in enumerate(used)}                     # pattern 0 stays tile 0 (blank)
        assert len(used) <= B.TILE_LIMIT
        def native(e):
            e = int(e)
            return lid[e & 0xFFFF] | (((e >> 16) & 1) << 10) | (((e >> 17) & 1) << 11) | ((e >> 20) << 12)
        blocks, attrs, index = [], [], {}
        grid = np.zeros((h, W), np.uint16)
        for y in range(h):
            for x in range(W):
                es = tuple(native(e) for e in sub[y, x])
                key = (es, int(sat[y, x]))
                if key not in index:
                    index[key] = len(blocks); blocks.append(es); attrs.append(int(sat[y, x]))
                mid = index[key]
                grid[y, x] = mid | (int(coll[y0 + y, x]) << 10) | (int(elev[y0 + y, x]) << 12)
        assert len(blocks) <= 1024
        folder = name.lower().replace('city', '_city')                 # blackthorn_city01
        sym = name
        for part, kind, s in ((0, 'primary', sym + 'Primary'), (1, 'secondary', sym)):
            d = g / f'data/tilesets/{kind}/{folder}'
            (d / 'palettes').mkdir(parents=True, exist_ok=True)
            tiles = [pats[p] for p in used[part * 512:(part + 1) * 512]]
            rows = max(1, (len(tiles) + 15) // 16)
            buf = np.zeros((rows * 8, 128), np.uint8)
            for i, t in enumerate(tiles):
                buf[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
            im = Image.fromarray(buf, 'P'); im.putpalette([v for i in range(16) for v in (i * 17,) * 3] + [0] * 720)
            im.save(d / 'tiles.png', bits=4)
            for bank in range(16):
                if bank == B.CENTER_BANK:
                    text = center_pal
                elif bank == B.MART_BANK:
                    text = mart_pal
                else:
                    text = jasc([tuple(int(v) for v in pal[bank][i]) for i in range(16)])
                (d / 'palettes' / f'{bank:02}.pal').write_text(text)
            bs = blocks[part * 512:(part + 1) * 512] or [(0,) * 8]
            ats = attrs[part * 512:(part + 1) * 512] or [0x1000]
            (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in bs))
            (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(ats), *ats))
            gfx += (f'\nconst u32 gTilesetTiles_{s}[] = INCGFX_U32("data/tilesets/{kind}/{folder}/tiles.png", ".4bpp.fastSmol");\n'
                    f'const u16 gTilesetPalettes_{s}[][16] = {{\n' +
                    ''.join(f'    INCGFX_U16("data/tilesets/{kind}/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
            metas += (f'\nconst u16 gMetatiles_{s}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatiles.bin");\n'
                      f'const u16 gMetatileAttributes_{s}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatile_attributes.bin");\n')
            heads += (f'\nconst struct Tileset gTileset_{s} = {{ .isCompressed = TRUE, .isSecondary = {"FALSE" if part == 0 else "TRUE"}, '
                      f'.tiles = gTilesetTiles_{s}, .palettes = gTilesetPalettes_{s}, .metatiles = gMetatiles_{s}, '
                      f'.metatileAttributes = gMetatileAttributes_{s}, .callback = NULL }};\n')
        ld = g / f'data/layouts/{name}'
        ld.mkdir(parents=True)
        (ld / 'map.bin').write_bytes(grid.astype('<u2').tobytes())
        # Border: the section's own west-edge mountain, on the 2x2 phase GetBorderBlockAt uses.
        assert y0 % 2 == 0
        border = [int(grid[i >> 1, i & 1] & 1023) for i in range(4)]
        (ld / 'border.bin').write_bytes(struct.pack('<4H', *border))
        layouts['layouts'].append(dict(id=layout_id(name), name=f'{name}_Layout', width=W, height=h,
                                       primary_tileset=f'gTileset_{sym}Primary', secondary_tileset=f'gTileset_{sym}',
                                       border_filepath=f'data/layouts/{name}/border.bin',
                                       blockdata_filepath=f'data/layouts/{name}/map.bin', layout_version='emerald'))
        report.append(dict(section=name, rows=[y0, y1], tiles=len(used), primary_tiles=min(512, len(used)),
                           secondary_tiles=max(0, len(used) - 512), metatiles=len(blocks)))
    write(g / 'data/layouts/layouts.json', layouts)
    for p, text in (('src/data/tilesets/graphics.h', gfx), ('src/data/tilesets/metatiles.h', metas), ('src/data/tilesets/headers.h', heads)):
        with (g / p).open('a') as f:
            f.write('\n// Blackthorn City: three native sections, private tileset pairs, one shared palette set.' + text)

    # Maps.
    template = read(g / 'data/maps/CherrygroveCity/map.json')
    for si, (name, y0, y1) in enumerate(SECTIONS):
        conns = []
        if si > 0: conns.append(dict(map=map_id(SECTIONS[si - 1][0]), offset=0, direction='up'))
        if si < len(SECTIONS) - 1: conns.append(dict(map=map_id(SECTIONS[si + 1][0]), offset=0, direction='down'))
        m = dict(template)
        m.update(id=map_id(name), name=name, layout=layout_id(name), music='MUS_FALLARBOR', region_map_section='MAPSEC_BLACKTHORN_CITY',
                 weather='WEATHER_NONE', map_type='MAP_TYPE_CITY', allow_cycling=True, allow_running=True, show_map_name=True,
                 connections=conns, object_events=[], warp_events=[], coord_events=[], bg_events=[])
        for (x, y), dest, warp in DOORS:
            if y0 <= y < y1:
                m['warp_events'].append(dict(x=x, y=y - y0, elevation=0, dest_map=dest, dest_warp_id=warp))
        script = f'{name}_MapScripts::\n    .byte 0\n'
        for label, (x, y), text in SIGNS:
            if y0 <= y < y1:
                m['bg_events'].append(dict(type='sign', x=x, y=y - y0, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',
                                           script=f'BlackthornCity_{label}'))
                script += (f'\nBlackthornCity_{label}::\n    msgbox BlackthornCity_{label}_Text, MSGBOX_SIGN\n    end\n'
                           f'\nBlackthornCity_{label}_Text:\n    .string "{text}$"\n')
        write(g / f'data/maps/{name}/map.json', m)
        (g / f'data/maps/{name}/scripts.inc').write_text(script)
    door_section = section_of(DOORS[0][0][1])
    city_map = map_id(SECTIONS[door_section][0])
    for old, new in INTERIORS:
        text = json.dumps(read(g / f'data/maps/{old}/map.json'))
        for a, b in (('CherrygrovePokemonCenter', 'BlackthornPokemonCenter'), ('CherrygroveCenterUpstairs', 'BlackthornCenterUpstairs'),
                     ('CherrygroveMart', 'BlackthornMart'), ('MAP_CHERRYGROVE_POKEMON_CENTER', 'MAP_BLACKTHORN_POKEMON_CENTER'),
                     ('MAP_CHERRYGROVE_CENTER_UPSTAIRS', 'MAP_BLACKTHORN_CENTER_UPSTAIRS'), ('MAP_CHERRYGROVE_MART', 'MAP_BLACKTHORN_MART'),
                     ('MAP_CHERRYGROVE_CITY', city_map), ('MAPSEC_CHERRYGROVE_CITY', 'MAPSEC_BLACKTHORN_CITY')):
            text = text.replace(a, b)
        m = json.loads(text)
        for w in m['warp_events']:
            if w['dest_map'] == city_map:
                w['dest_warp_id'] = '0' if new == 'BlackthornPokemonCenter' else '1'
        # Porymap writes custom header fields last, sorted; match it so a first save is a no-op.
        for k in sorted(k for k in ('region', 'build_target') if k in m):
            m[k] = m.pop(k)
        write(g / f'data/maps/{new}/map.json', m)
        s = (g / f'data/maps/{old}/scripts.inc').read_text().replace(old, new)
        (g / f'data/maps/{new}/scripts.inc').write_text(s)
    all_new = names + [b for _, b in INTERIORS]
    groups = read(g / 'data/maps/map_groups.json')
    groups['gMapGroup_Cherrygrove'].extend(all_new)
    write(g / 'data/maps/map_groups.json', groups)
    with (g / 'data/event_scripts.s').open('a') as f:
        for n in all_new:
            f.write(f'\n.include "data/maps/{n}/scripts.inc"\n')
    p = g / 'src/data/region_map/region_map_sections.json'; r = read(p)
    sec = dict(r['map_sections'][-1]); sec.update(id='MAPSEC_BLACKTHORN_CITY', name='BLACKTHORN CITY'); r['map_sections'].append(sec); write(p, r)
    p = g / 'include/regions.h'; s = p.read_text()
    s = s.replace('    case MAPSEC_CHERRYGROVE_CITY:', '    case MAPSEC_BLACKTHORN_CITY: return REGION_JOHTO;\n    case MAPSEC_CHERRYGROVE_CITY:', 1); p.write_text(s)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_CHERRYGROVE_REGIONAL_PREVIEW_30};'
    assert anchor in s
    s = s.replace(anchor, 'MAP_CHERRYGROVE_REGIONAL_PREVIEW_30, ' + ', '.join(map_id(n) for n in all_new) + '};'); p.write_text(s)
    ids = {n: groups['gMapGroup_Cherrygrove'].index(n) for n in all_new}
    write(EV / 'capacity.json', dict(sections=report, tile_limit=B.TILE_LIMIT, metatile_limit=1024, palette_banks=13, map_ids=ids))
    print('Installed Blackthorn:', json.dumps(report), ids)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
