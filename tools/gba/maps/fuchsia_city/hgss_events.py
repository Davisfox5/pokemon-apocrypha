"""Register decoded HGSS Fuchsia City (zone T08) events onto native 16x16 cells.

Reads pret/pokeheartgold source data: the T08 zone events, the EVERYWHERE map matrix and the
English sign text. One HGSS tile is one native cell.

    python3 tools/gba/maps/fuchsia_city/hgss_events.py PATH/TO/pokeheartgold OUT.json

Coordinates are relative to Fuchsia's matrix block (origin HGSS tile (1184, 384)).
"""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'route32_native'))
import hgss_events as base  # noqa: E402

ZONE, HEADER_ID, MSG = 'T08', 56, 'msg_0512_T08'
FILES = ['files/fielddata/eventdata/zone_event/053_T08.json',
         'files/fielddata/mapmatrix/map_matrix/map_matrix_0000_EVERYWHERE.bin',
         'files/fielddata/script/scr_seq/scr_seq_0807_T08.s', f'files/msgdata/msg/{MSG}.gmm']

def messages(phg):
    text = (phg / FILES[3]).read_text(encoding='utf-8')
    return {m.group(1): re.sub(r'\\[rnf]', ' ', m.group(2)).strip() for m in
            re.finditer(rf'<row id="({MSG}_\d+)"[^>]*>.*?<language name="English">(.*?)</language>', text, re.S)}

def sign_messages(phg):
    script = (phg / FILES[2]).read_text()
    out = {}
    for m in re.finditer(rf'^scr_seq_{ZONE}_(\d+):\n(?:[^\n]*\n){{0,6}}?[^\n]*?({MSG}_\d+)', script, re.M):
        out.setdefault(int(m.group(1)), m.group(2))
    return out

def main(phg, dest):
    base.HEADER_ID = HEADER_ID
    block = base.matrix_block(phg)
    names = {int(m.group(2)): m.group(1) for m in
             re.finditer(r'#define\s+(MAP_\w+)\s+(\d+)', (phg / 'include/constants/maps.h').read_text())}
    block['neighbours'] = {k: [names[h] for h in v] for k, v in block.pop('neighbour_headers').items()}
    ox, oz = block['origin']
    ev = json.loads((phg / FILES[0]).read_text())
    msg, sign = messages(phg), sign_messages(phg)
    local = lambda e: [e['x'] - ox, e['z'] - oz]
    warps = [dict(index=i, cell=local(e), dest=e['header'], anchor=e['anchor']) for i, e in enumerate(ev['warps'])]
    signs = []
    for e in ev['bgs']:
        m = re.search(r'_(\d+) \+ 1', e['scriptId'])
        signs.append(dict(cell=local(e), script=e['scriptId'], bg_type=e['type'],
                          text=msg.get(sign.get(int(m.group(1))), '') if m else ''))
    objects = [dict(id=e['id'], sprite=e['spriteId'], cell=local(e), facing=e['facingDirection'],
                    movement=e['movement'], flag=e['eventFlag']) for e in ev['objects']]
    rev = subprocess.run(['git', '-C', str(phg), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    out = dict(source=dict(repository='pret/pokeheartgold', revision=rev, files=FILES), matrix=block,
               warps=warps, signs=signs, objects=objects)
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    Path(dest).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(dict(origin=block['origin'], size=block['size'], neighbours=block['neighbours'],
                          warps=len(warps), signs=len(signs), objects=len(objects))))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2])
