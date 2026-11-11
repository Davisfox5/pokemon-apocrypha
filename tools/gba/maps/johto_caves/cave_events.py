"""Register a Johto cave's decoded HGSS events onto native cells (each floor's own matrix: HGSS event
coordinates are native cell coordinates as they stand).

    python3 tools/gba/maps/<cave>/hgss_events.py PATH/TO/pokeheartgold OUT_DIR

Writes OUT_DIR/<side>.json: warps (index for index), hidden items, objects. Terrain and collision
come from land_data (hgss_render.py).
"""
import json, subprocess
from pathlib import Path
import cave

def main(phg, dest):
    phg = Path(phg)
    rev = subprocess.run(['git', '-C', str(phg), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    for side, f in cave.FLOORS.items():
        zone = f['zone']
        ev = json.loads((phg / f'files/fielddata/eventdata/zone_event/{zone}.json').read_text())
        warps = [dict(index=i, cell=[e['x'], e['z']], dest=e['header'], anchor=e['anchor']) for i, e in enumerate(ev.get('warps', []))]
        hidden = [dict(cell=[e['x'], e['z']], script=e['scriptId'], bg_type=e['type']) for e in ev.get('bgs', [])]
        objects = [dict(id=e['id'], sprite=e['spriteId'], cell=[e['x'], e['z']], facing=e['facingDirection'],
                        movement=e['movement'], flag=e['eventFlag'], script=e['scriptId']) for e in ev.get('objects', [])]
        coords = [dict(cell=[e['x'], e['z']], script=e.get('scriptId')) for e in ev.get('coords', [])]
        out = dict(source=dict(repository='pret/pokeheartgold', revision=rev, files=[f'files/fielddata/eventdata/zone_event/{zone}.json'],
                               note='Decoded event data. Terrain/collision (land_data) is not in the repository.'),
                   header=f['header'], warps=warps, hidden_items=hidden, objects=objects, coord_triggers=coords)
        p = Path(dest) / f'{side}.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
        print(side, dict(warps=len(warps), hidden=len(hidden), objects=len(objects), coords=len(coords)))
