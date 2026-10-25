"""HGSS's Celadon City (map header 55, MAP_CELADON, zone T07), decoded from the game's data.

    python3 tools/gba/maps/celadon/hgss_source.py PATH/TO/pokeheartgold

HGSS is Celadon's plan reference beside FireRed's map: what ten years of Game Freak's own
revision moved, added or removed. The build still uses FireRed's map and Gen 3 art (AGENTS.md,
Kanto towns). This writes Olivine's renderer pointed at Celadon (area data bank 15):

    source/hgss/   hgss_render.py's render, permissions, materials and building placements
    source/hgss-events.json   T07's warps, signs (English text) and objects, in map cells
"""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / 'olivine_elements'))
import hgss_render as R                     # noqa: E402
import hgss_events as E                     # noqa: E402

SRC = ROOT / 'gba/art/celadon-kanto/source'
HEADER_ID, AREA_BANK, ZONE, MSG = 55, 15, 'T07', 'msg_0491_T07'
FILES = dict(events='files/fielddata/eventdata/zone_event/052_T07.json', messages=f'files/msgdata/msg/{MSG}.gmm',
             script='files/fielddata/script/scr_seq/scr_seq_0785_T07.s')

def messages(phg):
    text = (phg / FILES['messages']).read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(rf'<row id="({MSG}_\d+)"[^>]*>.*?<language name="English">(.*?)</language>', text, re.S):
        out[m.group(1)] = re.sub(r'\\[rnf]', ' ', m.group(2)).strip()
    return out

def sign_messages(phg):
    script = (phg / FILES['script']).read_text()
    out = {}
    for m in re.finditer(rf'^scr_seq_{ZONE}_(\d+):\n(?:[^\n]*\n){{0,6}}?[^\n]*?({MSG}_\d+)', script, re.M):
        out.setdefault(int(m.group(1)), m.group(2))
    return out

def events(phg):
    E.HEADER_ID = HEADER_ID
    block = E.matrix_block(phg)
    ox, oz = block['origin']
    ev = json.loads((phg / FILES['events']).read_text())
    msg, sign = messages(phg), sign_messages(phg)
    local = lambda e: [e['x'] - ox, e['z'] - oz]
    warps = [dict(index=i, cell=local(e), dest=e['header'], anchor=e['anchor']) for i, e in enumerate(ev['warps'])]
    signs = []
    for e in ev['bgs']:
        m = re.search(r'_(\d+) \+ 1', e['scriptId'])
        sid = int(m.group(1)) if m else None
        signs.append(dict(cell=local(e), script=e['scriptId'], bg_type=e['type'], text=msg.get(sign.get(sid), '') if m else ''))
    objects = [dict(id=e['id'], sprite=e['spriteId'], cell=local(e), facing=e['facingDirection'],
                    movement=e['movement'], flag=e['eventFlag']) for e in ev['objects']]
    rev = subprocess.run(['git', '-C', str(phg), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    return dict(source=dict(repository='pret/pokeheartgold', revision=rev, files=list(FILES.values())),
                matrix=block, warps=warps, signs=signs, objects=objects)

def main(phg):
    R.HEADER_ID, R.AREA_BANK = HEADER_ID, AREA_BANK
    R.main(phg, SRC / 'hgss')
    ev = events(phg)
    (SRC / 'hgss-events.json').write_text(json.dumps(ev, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(dict(origin=ev['matrix']['origin'], size=ev['matrix']['size'], warps=len(ev['warps']),
                          signs=len(ev['signs']), objects=len(ev['objects']))))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
