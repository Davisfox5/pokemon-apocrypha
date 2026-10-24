"""Register decoded HGSS Route 29 (zone R29) events onto native 16x16 cells.

Reads pret/pokeheartgold source data, not a screenshot: the R29 zone events,
the EVERYWHERE map matrix and the English sign text. HGSS overworld tiles and
Gen 3 metatiles are both 16 px, so one HGSS tile is one native cell.

    python3 tools/gba/maps/route29_catalog/hgss_events.py PATH/TO/pokeheartgold OUT.json

Coordinates are relative to Route 29's matrix block.
Terrain, buildings and collision come from land_data (hgss_render.py).
"""
import json, re, struct, subprocess, sys
from pathlib import Path

ZONE = 'R29'
HEADER_ID = 33   # MAP_ROUTE_29

def matrix_block(phg):
    d = (phg / 'files/fielddata/mapmatrix/map_matrix/map_matrix_0000_EVERYWHERE.bin').read_bytes()
    w, h, has_hdr, has_alt, nl = d[:5]
    p = 5 + nl
    hdr = struct.unpack_from('<%dH' % (w * h), d, p); p += 2 * w * h
    if has_alt: p += w * h
    land = struct.unpack_from('<%dH' % (w * h), d, p)
    cells = [(x, z) for z in range(h) for x in range(w) if hdr[z * w + x] == HEADER_ID]
    xs, zs = [c[0] for c in cells], [c[1] for c in cells]
    neighbours = {}
    for name, (dx, dz) in dict(west=(-1, 0), east=(1, 0), north=(0, -1), south=(0, 1)).items():
        found = sorted({hdr[(z + dz) * w + x + dx] for x, z in cells
                        if (x + dx, z + dz) not in cells and 0 <= x + dx < w and 0 <= z + dz < h} - {0})
        neighbours[name] = found
    return dict(chunks=[dict(x=x, z=z, land_data=land[z * w + x]) for x, z in cells],
                origin=[min(xs) * 32, min(zs) * 32],
                size=[(max(xs) - min(xs) + 1) * 32, (max(zs) - min(zs) + 1) * 32],
                neighbour_headers=neighbours)

def messages(phg):
    text = (phg / 'files/msgdata/msg/msg_0373_R29.gmm').read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(r'<row id="(msg_0373_R29_\d+)"[^>]*>.*?<language name="English">(.*?)</language>', text, re.S):
        out[m.group(1)] = re.sub(r'\\[rnf]', ' ', m.group(2)).strip()
    return out

def sign_messages(phg):
    script = (phg / 'files/fielddata/script/scr_seq/scr_seq_0225_R29.s').read_text()
    out = {}
    for m in re.finditer(r'^scr_seq_R29_(\d+):\n\s+\w+(?:Ex)?\s+[^\n]*?(msg_0373_R29_\d+)', script, re.M):
        out[int(m.group(1))] = m.group(2)
    return out

def main(phg, dest):
    block = matrix_block(phg)
    ox, oz = block['origin']
    ev = json.loads((phg / 'files/fielddata/eventdata/zone_event/030_R29.json').read_text())
    msg, sign = messages(phg), sign_messages(phg)
    local = lambda e: [e['x'] - ox, e['z'] - oz]
    warps = [dict(index=i, cell=local(e), dest=e['header'], anchor=e['anchor']) for i, e in enumerate(ev['warps'])]
    signs = []
    for e in ev['bgs']:
        m = re.search(r'_(\d+) \+ 1', e['scriptId'])
        if not m:                                   # hidden items name a std script instead
            signs.append(dict(cell=local(e), script=e['scriptId'], bg_type=e['type'], text=''))
            continue
        sid = int(m.group(1))
        signs.append(dict(cell=local(e), script=f'scr_seq_R29_{sid:03}', bg_type=e['type'], text=msg.get(sign.get(sid), '')))
    objects = [dict(id=e['id'], sprite=e['spriteId'], cell=local(e), facing=e['facingDirection'],
                    movement=e['movement'], flag=e['eventFlag']) for e in ev['objects']]
    rev = subprocess.run(['git', '-C', str(phg), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    out = dict(source=dict(repository='pret/pokeheartgold', revision=rev,
                           files=['files/fielddata/eventdata/zone_event/030_R29.json',
                                  'files/fielddata/mapmatrix/map_matrix/map_matrix_0000_EVERYWHERE.bin',
                                  'files/fielddata/script/scr_seq/scr_seq_0225_R29.s',
                                  'files/msgdata/msg/msg_0373_R29.gmm'],
                           note='Decoded event data. Terrain/collision (land_data) is not in the repository.'),
               matrix=block, warps=warps, signs=signs, objects=objects)
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    Path(dest).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(dict(origin=block['origin'], size=block['size'], warps=len(warps), signs=len(signs), objects=len(objects))))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2])
