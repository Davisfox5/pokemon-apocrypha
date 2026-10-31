"""Register decoded HGSS Dark Cave events (zones D42R0101 and D42R0102) onto native 16x16 cells.

Reads pret/pokeheartgold source data, not a screenshot: each zone's events and the NPC's
English text. Each Dark Cave map has a matrix of its own whose origin is its top-left
chunk, so HGSS event coordinates are native cell coordinates as they stand.

    python3 tools/gba/maps/dark_cave/hgss_events.py PATH/TO/pokeheartgold OUT_DIR

Writes OUT_DIR/route45-side.json and OUT_DIR/route31-side.json.
Terrain and collision come from land_data (hgss_render.py).
"""
import json, re, subprocess, sys
from pathlib import Path

ZONES = {'route45-side': ('120_D42R0101', 'MAP_DARK_CAVE_ROUTE_45_SIDE'),
         'route31-side': ('169_D42R0102', 'MAP_DARK_CAVE_ROUTE_31_SIDE')}
MSG = 'files/msgdata/msg/msg_0127_D42R0101.gmm'

def messages(phg):
    text = (phg / MSG).read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(r'<row id="(msg_0127_D42R0101_\d+)"[^>]*>.*?<language name="English">(.*?)</language>', text, re.S):
        out[m.group(1)] = re.sub(r'\\[rnf]', ' ', m.group(2)).strip()
    return out

def main(phg, dest):
    rev = subprocess.run(['git', '-C', str(phg), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    msg = messages(phg)
    for side, (zone, header) in ZONES.items():
        ev = json.loads((phg / f'files/fielddata/eventdata/zone_event/{zone}.json').read_text())
        warps = [dict(index=i, cell=[e['x'], e['z']], dest=e['header'], anchor=e['anchor']) for i, e in enumerate(ev['warps'])]
        hidden = [dict(cell=[e['x'], e['z']], script=e['scriptId'], bg_type=e['type']) for e in ev['bgs']]
        objects = [dict(id=e['id'], sprite=e['spriteId'], cell=[e['x'], e['z']], facing=e['facingDirection'],
                        movement=e['movement'], flag=e['eventFlag'], script=e['scriptId']) for e in ev['objects']]
        out = dict(source=dict(repository='pret/pokeheartgold', revision=rev,
                               files=[f'files/fielddata/eventdata/zone_event/{zone}.json', MSG],
                               note='Decoded event data. Terrain/collision (land_data) is not in the repository.'),
                   header=header, warps=warps, hidden_items=hidden, objects=objects,
                   messages=msg if side == 'route45-side' else {})
        p = Path(dest) / f'{side}.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
        print(side, dict(warps=len(warps), hidden=len(hidden), objects=len(objects)))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2])
