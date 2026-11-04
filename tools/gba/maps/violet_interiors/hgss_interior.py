"""Render an HGSS interior from the game's own data at 16 px per tile (route29_catalog/hgss_render.py's
projection), for Violet's interiors: the Pokemon School, the gym, Sprout Tower 1F-3F and the houses.

    python3 tools/gba/maps/violet_interiors/hgss_interior.py PATH/TO/pokeheartgold OUT_DIR

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'route29_catalog')]
import hgss_render as R                 # noqa: E402

# name: (map header, area data bank, matrix file)
ROOMS = {
    'school': ('MAP_VIOLET_POKEMON_SCHOOL', 61, 'map_matrix_0102_T22R0301.bin'),
    'gym': ('MAP_VIOLET_GYM', 28, 'map_matrix_0087_T22GYM0101.bin'),
    'sprout1': ('MAP_SPROUT_TOWER_1F', 77, 'map_matrix_0012_D15R0101.bin'),
    'sprout2': ('MAP_SPROUT_TOWER_2F', 77, 'map_matrix_0013_D15R0102.bin'),
    'sprout3': ('MAP_SPROUT_TOWER_3F', 77, 'map_matrix_0014_D15R0103.bin'),
    'house_nw': ('MAP_VIOLET_NORTHWEST_HOUSE', 25, 'map_matrix_0095_T28R0201.bin'),
    'house_unused': ('MAP_VIOLET_UNUSED', 25, 'map_matrix_0066_T20R0301.bin'),
}

def loader(area_bank, matrix, models_by_kind):
    def load(phg):
        a = phg / 'files/a'
        land = R.narc.load(a / '0/6/5')
        area = R.narc.load(a / '0/4/2')[area_bank]
        bld_set, map_set = struct.unpack_from('<HH', area, 0)
        tex0 = R.Tex0(R.narc.load(a / '0/4/4')[map_set])
        models = models_by_kind[area[6]]          # the area's model archive: 0 room models (bm_room), 1 field models (Sprout Tower's d15 objects)
        d = (phg / 'files/fielddata/mapmatrix/map_matrix' / matrix).read_bytes()
        w, h, has_hdr, has_alt, nl = d[:5]
        p = 5 + nl
        if has_hdr: p += 2 * w * h
        if has_alt: p += w * h
        lid = struct.unpack_from('<%dH' % (w * h), d, p)
        cells = [(x, z) for z in range(h) for x in range(w) if lid[z * w + x] != 0xFFFF]
        chunks = [dict(cx=x, cz=z, land=lid[z * w + x]) for x, z in cells]
        return land, tex0, models, chunks, dict(area_bank=area_bank, map_texture_set=map_set, building_texture_set=bld_set,
                                                matrix=matrix, area_raw=list(area[:8]))
    return load

def main(phg, out, names=None):
    out.mkdir(parents=True, exist_ok=True)
    kinds = {0: R.narc.load(phg / 'files/a/1/4/8'), 1: R.narc.load(phg / 'files/a/0/4/0')}
    for name, (hdr, bank, matrix) in ROOMS.items():
        if names and name not in names:
            continue
        R.load = loader(bank, matrix, kinds)
        R.SNAP = True
        r = R.render(phg)
        r['full'].save(out / f'{name}.png')
        np.savez(out / f'{name}-permissions.npz', types=r['types'], collision=r['collision'])
        (out / f'{name}.json').write_text(json.dumps(dict(header=hdr, meta=r['meta'], buildings=r['buildings']), indent=1, default=str) + '\n')
        print(name, r['full'].size, len(r['buildings']), 'props', r['meta'])

if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:] or None)
