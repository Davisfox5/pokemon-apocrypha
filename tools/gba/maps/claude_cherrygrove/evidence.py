#!/usr/bin/env python3
"""Turn a runtime check directory into review evidence for gba/art/claude-cherrygrove/evidence.

- structure.json: BFS reachability from the spawn to every door approach, both exits and every NPC start
- movement.json: per-resident positions/directions from the walk phase, frame/palette/collision assertions
- walking-tour.gif, in-game-tour.png, doors-in-game.png, dialogue.png, title-continue.png
"""
from __future__ import annotations
import json, struct, sys
from collections import deque
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from claude_cherrygrove import layout as L, cast  # noqa: E402

ROOT = HERE.parents[3]
EV = ROOT / 'gba/art/claude-cherrygrove/evidence'

def structure(game):
    W, H = L.W, L.H
    grid = struct.unpack('<' + 'H' * (W * H), (game / 'data/layouts/CherrygroveCity/map.bin').read_bytes())
    blocked = lambda x, y: bool(grid[y * W + x] & 0xC00)
    seen = {tuple(L.SPAWN)}; q = deque(seen)
    while q:
        x, y = q.popleft()
        for xx, yy in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            if 0 <= xx < W and 0 <= yy < H and not blocked(xx, yy) and (xx, yy) not in seen: seen.add((xx, yy)); q.append((xx, yy))
    report = dict(reachable_cells=len(seen))
    for b in L.BUILDINGS:
        dx, dy = L.door_of(b); report[f'door_{b["name"]}'] = (dx, dy + 1) in seen and (dx, dy) in seen
    report['north_exit'] = all((x, 0) in seen for x in range(*L.NORTH_EXIT))
    report['east_exit'] = all((W - 1, y) in seen for y in range(*L.EAST_EXIT))
    for npc in cast.NPCS: report[f'npc_{npc["id"]}'] = tuple(npc['pos']) in seen
    report['pier_end_reachable'] = (L.PIER['x0'] + 1, L.PIER['y']) in seen
    deck = {(x, y) for x in range(L.PIER['x0'], L.PIER['x1']) for y in (L.PIER['y'], L.PIER['y'] + 1)}
    report['sea_blocked'] = all(blocked(x, y) for y in range(6, 28) for x in range(0, L.shore(y) - 1) if (x, y) not in deck)
    return report

def movement(out):
    rows = [json.loads(l) for l in (out / 'walk.jsonl').read_text().splitlines() if l.startswith('{')]
    samples = [r for r in rows if 'objects' in r]; inter = [r for r in rows if 'interaction' in r]
    W, H = L.W, L.H
    grid = struct.unpack('<' + 'H' * (W * H), (out.parent / 'claude-cherrygrove/data/layouts/CherrygroveCity/map.bin').read_bytes())
    blocked = lambda x, y: bool(grid[y * W + x] & 0xC00)
    directions = {1: {9, 10, 11}, 2: {0, 7, 8}, 3: {1, 2, 3}, 4: {4, 5, 6}}
    per = {}; lag = 0; prior = {}
    for row in samples:
        objs = row['objects']
        assert len({o['palette'] for o in objs}) == len(objs), ('palette clash', row)
        for o in objs:
            assert not o['hflip'] and o['frame'] >= 0, o
            assert not blocked(o['x'], o['y']), ('npc on blocked cell', o)
            key = (row['view'], o['gfx']); old = prior.get(key)
            if o['frame'] not in directions[o['facing']]:
                assert old and old['facing'] != o['facing'] and o['frame'] in directions[old['facing']], o; lag += 1
            prior[key] = o
            d = per.setdefault(o['gfx'], dict(positions=set(), facings=set()))
            d['positions'].add((o['x'], o['y'])); d['facings'].add(o['facing'])
    summary = {g: dict(cells_visited=len(d['positions']), facings=sorted(d['facings'])) for g, d in per.items()}
    return dict(samples=len(samples), engine_frames=len(samples) * 4, residents_observed=len(per), one_sample_turn_upload_lag=lag,
                actual_obj_vram_frames_verified=True, no_horizontal_mirroring=True, distinct_palettes=True, collision_clear=True,
                residents=summary, interactions=inter)

def board(out, names, path, cols=3, labels=None):
    W, H = 480, 320
    img = Image.new('RGB', (cols * (W + 8) + 8, ((len(names) + cols - 1) // cols) * (H + 24) + 8), (32, 36, 44)); d = ImageDraw.Draw(img)
    for i, n in enumerate(names):
        p = out / (n + '.png')
        if not p.exists(): continue
        im = Image.open(p).resize((W, H), Image.Resampling.NEAREST); x = 8 + (i % cols) * (W + 8); y = 8 + (i // cols) * (H + 24)
        img.paste(im, (x, y + 16)); d.text((x, y + 2), labels[i] if labels else n, fill='white')
    img.save(path)

def main():
    game = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve(); EV.mkdir(parents=True, exist_ok=True)
    walk = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else out   # optional separate walk-phase directory
    s = structure(game); (EV / 'structure.json').write_text(json.dumps(s, indent=2) + '\n'); print(json.dumps(s, indent=2))
    failed = [k for k, v in s.items() if k != 'reachable_cells' and not v]
    if failed: print('STRUCTURE FAILURES:', failed)
    if (walk / 'walk.jsonl').exists():
        m = movement(walk); (EV / 'movement.json').write_text(json.dumps(m, indent=2) + '\n')
        print('movement:', m['samples'], 'samples,', m['residents_observed'], 'residents,', len(m['interactions']), 'conversations')
        frames = [Image.open(walk / f'view-{v}-{i:03}.png').resize((480, 320), Image.Resampling.NEAREST) for v in range(4) for i in range(0, 120, 2)]
        frames[0].save(EV / 'walking-tour.gif', save_all=True, append_images=frames[1:], duration=130, loop=0, optimize=True)
        for v in range(4): Image.open(walk / f'view-{v}-000.png').save(EV / f'view-{v}-native.png')
        board(walk, [f'view-{v}-000' for v in range(4)], EV / 'in-game-tour.png', cols=2,
              labels=['Home street: player house, Kestra', 'Shops: Mart and Pokemon Center', "Gold's yard: Gold and Silver", 'Blossom park'])
        board(walk, [f'{n["id"].lower()}-dialogue' for n in cast.NPCS], EV / 'dialogue.png', cols=4, labels=[n['id'] for n in cast.NPCS])
    shots = ['town-spawn', 'home-street', 'shops', 'gold-yard', 'park', 'beach', 'pier', 'cliff-corner', 'cliff', 'route29', 'route30', 'bedroom']
    board(out, shots, EV / 'places.png', cols=3)
    for n in shots:
        if (out / f'{n}.png').exists(): Image.open(out / f'{n}.png').save(EV / f'{n}.png')
    doors = [f'door-{i}-{t:03}' for i in (0, 4, 5) for t in (0, 12, 18, 24)]
    board(out, doors, EV / 'doors-in-game.png', cols=4)
    board(out, ['boot-before-start', 'continue-menu', 'ordinary-continue', 'cold-reload', 'mart-menu', 'home'], EV / 'save-continue.png', cols=3)
    results = json.loads((out / 'results.json').read_text())
    (EV / 'runtime.json').write_text(json.dumps([dict(phase=r['phase'], exit_code=r['exit_code'], observations=r['observations']) for r in results], indent=2) + '\n')
    print('evidence written to', EV)
    if failed: sys.exit(1)

if __name__ == '__main__':
    main()
