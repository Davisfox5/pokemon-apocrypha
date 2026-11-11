"""Headless mGBA checks for a Johto cave and its mouth on its town (Mt. Mortar's harness).

    python3 tools/gba/maps/<cave>/runtime.py ENGINE_CHECKOUT OUT_DIR

Dark Cave's harness (dark_cave/runtime.py, Route 46's runtime_convert: one fresh emulator process per
phase, write / cold read / title Continue). Every capture on a cave floor must rebuild, from its VRAM
dump, to the installed floor decoded natively, its border block beyond its edges. Town captures check
the player's position only (check.py proves the town changed no pixel).

Steps: a view of every floor; the town's mouth walked in and back out; every warp inside walked into,
the player arriving on its HGSS partner; a surfer on the cave's water (a warp onto water starts Surf);
a puddle walked through where the cave has one; an east and a west ledge jumped where it has them;
ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import hashlib, importlib.util, json, os, shlex, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
import cave                                         # noqa: E402
import cave_pack as P                               # noqa: E402
import cave_install as I                            # noqa: E402
sys.path.insert(1, str(HERE.parent / 'route46')); sys.path.insert(2, str(HERE.parent))
import runtime_convert as RC                        # noqa: E402
spec = importlib.util.spec_from_file_location('dark_cave_check', HERE.parent / 'dark_cave/check.py')
sys.path.insert(0, str(HERE.parent / 'dark_cave'))
DC = importlib.util.module_from_spec(spec); spec.loader.exec_module(DC)

DIRS = dict(north=(0, -1), south=(0, 1), west=(-1, 0), east=(1, 0))
KEY = dict(north='UP', south='DOWN', west='LEFT', east='RIGHT')
WALKABLE = ('MB_CAVE', 'MB_PUDDLE')
FLOORS, SIDE, TOWN = {}, {}, None                   # sMapProofMaps indices (= the map group's ids), set by main()

def grid(game, m):
    w, h = P.SIZE[SIDE[m]]
    d = DC.decode(game, FLOORS[m], cave.TILESET_DIR, cave.TILESET_DIR, w, h)
    names = {v: k for k, v in P.behaviors(game).items()}
    return np.vectorize(lambda v: names[int(v)])(d['beh']), d['coll']

def steps(game):
    out = []
    maps = {m: json.loads((game / f'data/maps/{FLOORS[m]}/map.json').read_text()) for m in FLOORS}
    grids = {m: grid(game, m) for m in FLOORS}
    for m in FLOORS:
        wv = maps[m]['warp_events'][0]
        out.append(('view', m, wv['x'], wv['y'], f'view-{SIDE[m]}'))
    ids = {v: k for k, v in FLOORS.items()}
    names = {v: k for k, v in I.IDS.items()}
    # the town's mouth: walked in, the player on the cave's exit cell; walked back out
    tw = json.loads((game / f"data/maps/{cave.TOWN['map']}/map.json").read_text())['warp_events']
    for wv in tw:
        if wv['dest_map'] not in names or names[wv['dest_map']] not in ids:
            continue
        m = ids[names[wv['dest_map']]]
        back = maps[m]['warp_events'][int(wv['dest_warp_id'])]
        b = grids[m][0][back['y'], back['x']]
        out += [('go', TOWN, wv['x'], wv['y'] + 1), ('north', 1, None), ('wait', 300), ('at', m, back['x'], back['y']),
                ('shot', f'mouth-{wv["x"]}-{wv["y"]}')]
        leave = 'south' if b == 'MB_SOUTH_ARROW_WARP' else None
        if leave is None:                            # a ladder: step off it, then back onto it
            ap = next(((back['x'] + dx, back['y'] + dy, n) for n, (dx, dy) in DIRS.items()
                       if not grids[m][1][back['y'] + dy, back['x'] + dx] and grids[m][0][back['y'] + dy, back['x'] + dx] in WALKABLE))
            opp = dict(north='south', south='north', east='west', west='east')[ap[2]]
            out += [(ap[2], 1, None), ('wait', 60), (opp, 1, None)]
        else:
            out += [(leave, 1, None)]
        out += [('wait', 300), ('at', TOWN, wv['x'], wv['y'] + 1), ('shot', f'town-after-{wv["x"]}-{wv["y"]}')]
    # every warp inside: walked into, the player arriving on its HGSS partner (a door's arrival steps out south)
    done = set()
    for m, mj in maps.items():
        beh, coll = grids[m]
        H, W = beh.shape
        for i, wv in enumerate(mj['warp_events']):
            dname = names.get(wv['dest_map'])
            if dname not in ids or (m, i) in done:
                continue
            dm = ids[dname]
            back = maps[dm]['warp_events'][int(wv['dest_warp_id'])]
            done.add((m, i))
            b, x, y = beh[wv['y'], wv['x']], wv['x'], wv['y']
            if b == 'MB_SOUTH_ARROW_WARP':
                walk = [('go', m, x, y), ('south', 1, None)]
            elif b == 'MB_NON_ANIMATED_DOOR':
                walk = [('go', m, x, y + 1), ('north', 1, None)]
            else:
                ap = next(((x - dx, y - dy, n) for n, (dx, dy) in DIRS.items() if 0 <= x - dx < W and 0 <= y - dy < H
                           and not coll[y - dy, x - dx] and beh[y - dy, x - dx] in WALKABLE), None)
                if ap is None:
                    continue
                walk = [('go', m, ap[0], ap[1]), (ap[2], 1, None)]
            dbeh = grids[dm][0][back['y'], back['x']]
            ay = back['y'] + (1 if dbeh == 'MB_NON_ANIMATED_DOOR' else 0)
            out += walk + [('wait', 300), ('at', dm, back['x'], ay), ('shot', f'warp-{SIDE[m]}-{x}-{y}')]
    # a surfer on the cave's water
    side, sx, sy = cave.SURF
    m = {v: k for k, v in SIDE.items()}[side]
    out += [('go', m, sx, sy), ('surfing', 1, 'on-the-water'), ('shot', 'surfing')]
    # a puddle walked through
    for m in FLOORS:
        beh, coll = grids[m]
        H, W = beh.shape
        c = next(((x, y) for y in range(H) for x in range(1, W) if beh[y, x] == 'MB_PUDDLE' and beh[y, x - 1] in WALKABLE
                  and not coll[y, x - 1]), None)
        if c:
            out += [('go', m, c[0] - 1, c[1]), ('east', 1, None), ('wait', 30), ('at', m, c[0], c[1]), ('shot', 'puddle')]
            break
    # an east and a west ledge, jumped one way
    for b, n in (('MB_JUMP_EAST', 'east'), ('MB_JUMP_WEST', 'west'), ('MB_JUMP_SOUTH', 'south')):
        dx, dy = DIRS[n]
        for m in FLOORS:
            beh, coll = grids[m]
            H, W = beh.shape
            c = next(((x - dx, y - dy) for y in range(1, H - 1) for x in range(1, W - 1) if beh[y, x] == b
                      and beh[y - dy, x - dx] in WALKABLE and not coll[y - dy, x - dx] and not coll[y + dy, x + dx]), None)
            if c:
                out += [('go', m, c[0], c[1]), (n, 1, None), ('wait', 60), ('at', m, c[0] + 2 * dx, c[1] + 2 * dy), ('shot', f'ledge-{n}')]
                break
    return out

def cave_canvas(img, grid_, border):
    Hh, Ww = img.shape[0] // 16, img.shape[1] // 16
    y, x = np.argwhere((grid_ & 1023) == border)[0]
    void = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
    Pd = 16
    out = np.tile(void, (Hh + 2 * Pd, Ww + 2 * Pd, 1))
    out[Pd * 16:(Pd + Hh) * 16, Pd * 16:(Pd + Ww) * 16] = img
    return out, Pd * 16

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    maps = {}
    for k, name in FLOORS.items():
        w, h = P.SIZE[SIDE[k]]
        d = DC.decode(game, name, cave.TILESET_DIR, cave.TILESET_DIR, w, h)
        border = set(np.frombuffer((game / f'data/layouts/{name}/border.bin').read_bytes(), '<u2').tolist())
        maps[k] = cave_canvas(d['img'].astype(np.int32) >> 3, d['grid'].astype(np.int32), border.pop() & 1023)
    results = []
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        o = positions.get(tag)
        if tag in RC.INTERIOR or o is None or o['map'] not in maps:
            continue
        ref, pad = maps[o['map']]
        shot = RC.map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        x0, y0 = o['x'] * 16 - 112 + pad, o['y'] * 16 - 72 + pad
        win = ref[y0:y0 + 160, x0:x0 + 240]
        d = (win != shot).any(-1)
        if o.get('dialog'):
            d[112:] = False
        results.append(dict(frame=tag, map=o['map'], position=[o['x'], o['y']], mismatched_map_layer_pixels=int(d.sum())))
    return results

def main(game, out):
    global TOWN
    cap = json.loads((P.EV / 'capacity.json').read_text())
    for side, name in I.MAPS.items():
        FLOORS[cap['map_ids'][name]] = name
        SIDE[cap['map_ids'][name]] = side
    TOWN = cap['map_ids'][cave.TOWN['map']]
    out.mkdir(parents=True, exist_ok=True)
    plan = steps(game)
    RC.STEPS = plan
    RC.SAVE = ({v: k for k, v in SIDE.items()}[cave.SAVE[0]], cave.SAVE[1], cave.SAVE[2])
    src_text = RC.generate()
    src_text = src_text.replace('"route46-native-proof"', f'"{cave.TOOL}-native-proof"').replace('route46.sav', f'{cave.TOOL}.sav')
    src = out / 'runtime.c'; src.write_text(src_text)
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '-lmgba'))
    subprocess.run(['cc', '-O1', str(src), *flags, '-o', str(out / 'runtime')], check=True)
    raw = subprocess.check_output([os.environ.get('ARM_NM', 'arm-none-eabi-nm'), str(game / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'MapProof_Resume', 'gMapProofState', 'TrySavingData',
              'LoadGameSave', 'ArePlayerFieldControlsLocked', 'gMain', 'CB2_Overworld', 'gSaveBlock2Ptr', 'sGpuRegBuffer',
              'sWarpDestination', 'DoWarp', 'gPlayerAvatar'}
    syms = {r[2]: r[0] for line in raw.splitlines() if len(r := line.split()) == 3 and r[2] in wanted}
    assert syms.keys() == wanted, wanted - syms.keys()
    (out / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in syms.items()))
    phases = []
    for phase in ('write', 'read', 'menu'):
        r = subprocess.run([str(out / 'runtime'), str(game / 'pokeemerald.gba'), str(out / 'symbols.txt'), str(out), phase],
                           capture_output=True, text=True, timeout=1800)
        obs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
        phases.append(dict(phase=phase, exit_code=r.returncode, stderr=r.stderr.strip(), observations=obs))
        for ppm in out.glob('*.ppm'):
            Image.open(ppm).save(ppm.with_suffix('.png')); ppm.unlink()
        if r.returncode:
            (out / 'results.json').write_text(json.dumps(dict(phases=phases, steps=[list(map(str, s)) for s in plan]), indent=2) + '\n')
            raise SystemExit(f'{phase} failed: {r.stderr}')
    frames = check_frames(out, game, phases)
    rom = hashlib.sha256((game / 'pokeemerald.gba').read_bytes()).hexdigest()
    (out / 'results.json').write_text(json.dumps(dict(rom_sha256=rom, steps=[list(map(str, s)) for s in plan], phases=phases,
                                                      background_parity=frames), indent=2) + '\n')
    bad = [f for f in frames if f['mismatched_map_layer_pixels']]
    print(json.dumps(dict(rom_sha256=rom, frames=len(frames), frames_with_background_mismatch=len(bad))))
    for f in bad:
        print('  mismatch', f)
    assert not bad
