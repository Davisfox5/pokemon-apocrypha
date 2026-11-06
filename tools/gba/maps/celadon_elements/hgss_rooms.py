"""HGSS's rooms, decoded from the game's data, for rooms the city builds from HGSS's (owner,
2026-11-01: the apartments' room built off HGSS's Celadon Condominiums).

    python3 tools/gba/maps/celadon_elements/hgss_rooms.py PATH/TO/pokeheartgold

An HGSS room is one land_data chunk on its own one-cell map matrix, its furniture placed from the
room models (a/1/4/8) and drawn with its area's texture set. This points Olivine's renderer at
that: the room's matrix, its area bank, the room models. Per room it writes
gba/art/celadon-elements/source/hgss-rooms/<room>/ (hgss_render's render, permissions, materials
and furniture placements) and events.json (warps, signs, objects in room cells).

    condominiums_1f   MAP_CELADON_CONDOMINIUMS_1F (T07R0201): HGSS's Condominiums ground floor
    condominiums_2f, _3f, _roof, _roof_room, _left_elevator, _right_elevator: the rest of the
                      building (T07R0202-0207)
    dept_store_1f ... _5f, _roof, _elevator: HGSS's Celadon Dept Store (T07R0101-0107), for the
                      market's services building
"""
from __future__ import annotations
import json, re, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / 'olivine_elements'))
import hgss_render as R        # noqa: E402

OUT = ROOT / 'gba/art/celadon-elements/source/hgss-rooms'
ROOMS = dict(condominiums_1f='MAP_CELADON_CONDOMINIUMS_1F', condominiums_2f='MAP_CELADON_CONDOMINIUMS_2F',
             condominiums_3f='MAP_CELADON_CONDOMINIUMS_3F', condominiums_roof='MAP_CELADON_CONDOMINIUMS_ROOF',
             condominiums_roof_room='MAP_CELADON_CONDOMINIUMS_ROOF_ROOM',
             condominiums_left_elevator='MAP_CELADON_CONDOMINIUMS_LEFT_ELEVATOR',
             condominiums_right_elevator='MAP_CELADON_CONDOMINIUMS_RIGHT_ELEVATOR',
             # the Dept Store, for the market's services building (owner, 2026-11-06)
             dept_store_1f='MAP_CELADON_DEPARTMENT_STORE_1F', dept_store_2f='MAP_CELADON_DEPARTMENT_STORE_2F',
             dept_store_3f='MAP_CELADON_DEPARTMENT_STORE_3F', dept_store_4f='MAP_CELADON_DEPARTMENT_STORE_4F',
             dept_store_5f='MAP_CELADON_DEPARTMENT_STORE_5F', dept_store_roof='MAP_CELADON_DEPARTMENT_STORE_ROOF',
             dept_store_elevator='MAP_CELADON_DEPARTMENT_STORE_ELEVATOR')

def header(phg, name):
    text = (phg / 'src/data/map_headers.h').read_text()
    m = re.search(rf'\[{name}\] = \{{(.*?)\}},', text, re.S)
    body = m.group(1)
    get = lambda k: re.search(rf'\.{k} = (\w+)', body).group(1)
    return dict(area=int(get('areaDataBank')), matrix=get('matrixId'), events=get('eventsBank'))

def loader(matrix_file, area_bank):
    def load(phg):
        a = phg / 'files/a'
        land = R.narc.load(a / '0/6/5')
        area = R.narc.load(a / '0/4/2')[area_bank]
        bld_set, map_set = struct.unpack_from('<HH', area, 0)
        tex0 = R.Tex0(R.narc.load(a / '0/4/4')[map_set])
        outdoor = area[6] == 1                           # the area's outdoor flag: field models, else room models
        models = R.narc.load(a / ('0/4/0' if outdoor else '1/4/8'))
        d = matrix_file.read_bytes()
        w, h, has_hdr, has_alt, nl = d[:5]
        p = 5 + nl
        if has_hdr: p += 2 * w * h
        if has_alt: p += w * h
        lid = struct.unpack_from('<%dH' % (w * h), d, p)
        chunks = [dict(cx=i % w, cz=i // w, land=lid[i]) for i in range(w * h)]
        return land, tex0, models, chunks, dict(area_bank=area_bank, map_texture_set=map_set, building_texture_set=bld_set,
                                                matrix=matrix_file.name)
    return load

def main(phg):
    for room, name in ROOMS.items():
        h = header(phg, name)
        mfile = phg / 'files/fielddata/mapmatrix/map_matrix' / (h['matrix'].replace('NARC_map_matrix_', '').replace('_bin', '') + '.bin')
        R.load = loader(mfile, h['area'])
        out = OUT / room
        R.main(phg, out)
        evname = h['events'].replace('NARC_zone_event_', '').replace('_bin', '')
        ev = json.loads((phg / f'files/fielddata/eventdata/zone_event/{evname}.json').read_text())
        keep = dict(warps=[dict(cell=[e['x'], e['z']], dest=e['header'], anchor=e['anchor']) for e in ev.get('warps', [])],
                    signs=[dict(cell=[e['x'], e['z']], script=e['scriptId']) for e in ev.get('bgs', [])],
                    objects=[dict(sprite=e['spriteId'], cell=[e['x'], e['z']], facing=e['facingDirection'], movement=e['movement'])
                             for e in ev.get('objects', [])],
                    source=dict(header=name, area_bank=h['area'], matrix=mfile.name, events=f'zone_event/{evname}.json'))
        (out / 'events.json').write_text(json.dumps(keep, indent=2) + '\n')
        print(room, h, len(keep['warps']), 'warps')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
