"""Headless mGBA checks for Mt. Mortar and its four mouths on Route 42.

    python3 tools/gba/maps/mt_mortar/runtime.py ENGINE_CHECKOUT OUT_DIR

Dark Cave's harness (dark_cave/runtime.py, Route 46's runtime_convert: one fresh emulator process
per phase, write / cold read / title Continue). Every capture on a Mt. Mortar floor must rebuild,
from its VRAM dump, to the installed floor decoded natively, its border block beyond its edges.
Route 42 captures check the player's position only (check.py proves Route 42 changed no pixel).

Steps: a view of every floor; all four Route 42 mouths walked in and back out; every other warp
(holes, exits and ladders between floors) walked into, the player arriving on its HGSS partner;
the falls (Emerald's animated waterfall: its pixels are skipped in the parity check, and two captures
16 frames apart must differ there): surfing south off the upper pool, the current carries the player
to the foot, and facing the falls from the foot, A offers Waterfall (the harness has no badges, so the game's own "can't use"
text shows); a Rock Climb wall stops a walker, and facing it, A runs the game's Rock Climb script
(the harness has no party, so its "can't" text shows); an east and a west ledge jumped one way;
ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import hashlib, importlib.util, json, os, shlex, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
def _load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(sp); sys.modules[name] = mod; sp.loader.exec_module(mod)
    return mod

sys.path.insert(0, str(HERE))
P = _load('pack', HERE / 'pack.py')                 # Mt. Mortar's own (route46/ has a pack.py too)
I = _load('install', HERE / 'install.py')
sys.path.insert(1, str(HERE.parent / 'route46')); sys.path.insert(2, str(HERE.parent))
import runtime_convert as RC                        # noqa: E402
spec = importlib.util.spec_from_file_location('dark_cave_check', HERE.parent / 'dark_cave/check.py')
sys.path.insert(0, str(HERE.parent / 'dark_cave'))
DC = importlib.util.module_from_spec(spec); spec.loader.exec_module(DC)

ROUTE42, F1E, F1B, F2, B1 = 61, 66, 67, 68, 69     # sMapProofMaps indices = gMapGroup_Cherrygrove ids
FLOORS = {F1E: 'MtMortar_1F_Entrance', F1B: 'MtMortar_1F_Back', F2: 'MtMortar_2F', B1: 'MtMortar_B1F'}
SIDE = {F1E: '1f-entrance', F1B: '1f-back', F2: '2f', B1: 'b1f'}
DIRS = dict(north=(0, -1), south=(0, 1), west=(-1, 0), east=(1, 0))
KEY = dict(north='UP', south='DOWN', west='LEFT', east='RIGHT')
WALKABLE = ('MB_CAVE',)

def grid(game, m):
    w, h = P.SIZE[SIDE[m]]
    d = DC.decode(game, FLOORS[m], 'mt_mortar', 'mt_mortar', w, h)
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
    # the four mouths on Route 42: walked in, the player on Mt. Mortar's exit cell; walked back out
    r42 = json.loads((game / 'data/maps/Route42/map.json').read_text())['warp_events']
    for wv in r42:
        if wv['dest_map'] not in names or names[wv['dest_map']] not in ids:
            continue
        m = ids[names[wv['dest_map']]]
        back = maps[m]['warp_events'][int(wv['dest_warp_id'])]
        out += [('go', ROUTE42, wv['x'], wv['y'] + 1), ('north', 1, None), ('wait', 300), ('at', m, back['x'], back['y']),
                ('shot', f'mouth-{wv["x"]}-{wv["y"]}'), ('south', 1, None), ('wait', 300), ('at', ROUTE42, wv['x'], wv['y'] + 1)]
    # every warp inside: walked into, the player arriving on its HGSS partner (a door's arrival steps out south)
    done = set()
    for m, mj in maps.items():
        beh, coll = grids[m]
        H, W = beh.shape
        for i, wv in enumerate(mj['warp_events']):
            dname = names[wv['dest_map']]
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
    # the falls: down with the current, then A at the foot offers Waterfall
    x0, x1, crest, fy = 38, 52, 18, 22
    out += [('go', F1E, 45, crest), ('surfing', 1, 'above-the-falls'), ('shot', 'falls-crest'), ('south', 1, None), ('wait', 240),
            ('at', F1E, 45, fy + 1), ('surfing', 1, 'at-the-foot'), ('shot', 'falls-foot'), ('wait', 16), ('shot', 'falls-foot-later'),
            ('face', 'north', 'waterfall-offered')]
    # Rock Climb: a wall stops a walker; A runs the game's Rock Climb script
    for m in (F1E, F1B):
        beh, coll = grids[m]
        H, W = beh.shape
        cand = [(x, y, n) for y in range(H) for x in range(W) for n, (dx, dy) in DIRS.items()
                if beh[y, x] in WALKABLE and not coll[y, x] and 0 <= x + dx < W and 0 <= y + dy < H and beh[y + dy, x + dx] == 'MB_ROCK_CLIMB']
        if cand:
            x, y, n = cand[0]
            out += [('go', m, x, y), (n, 1, None), ('at', m, x, y), ('face', n, f'rock-climb-{SIDE[m]}')]
    # an east and a west ledge, jumped one way
    beh, coll = grids[F1B]
    H, W = beh.shape
    for b, n in (('MB_JUMP_EAST', 'east'), ('MB_JUMP_WEST', 'west')):
        dx, dy = DIRS[n]
        c = next(((x - dx, y) for y in range(H) for x in range(W) if beh[y, x] == b and 0 <= x - dx < W and 0 <= x + dx < W
                  and beh[y, x - dx] in WALKABLE and not coll[y, x - dx] and not coll[y, x + dx]), None)
        if c:
            out += [('go', F1B, c[0], c[1]), (n, 1, None), ('wait', 60), ('at', F1B, c[0] + 2 * dx, c[1]), ('shot', f'ledge-{n}')]
    return out

SAVE = (F1E, 20, 45)

def cave_canvas(img, grid_, border):
    Hh, Ww = img.shape[0] // 16, img.shape[1] // 16
    y, x = np.argwhere((grid_ & 1023) == border)[0]
    void = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
    Pd = 16
    out = np.tile(void, (Hh + 2 * Pd, Ww + 2 * Pd, 1))
    out[Pd * 16:(Pd + Hh) * 16, Pd * 16:(Pd + Ww) * 16] = img
    return out, Pd * 16

FALLS_PX = (38 * 16, 19 * 16, 53 * 16, 24 * 16)       # the animated waterfall on 1F entrance (x0, y0, x1, y1 px)

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    maps = {}
    for k, name in FLOORS.items():
        w, h = P.SIZE[SIDE[k]]
        d = DC.decode(game, name, 'mt_mortar', 'mt_mortar', w, h)
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
        anim = np.zeros_like(d)
        if o['map'] == F1E:                                # the waterfall cycles through Emerald's four frames
            fx0, fy0, fx1, fy1 = FALLS_PX
            ys, xs = np.mgrid[0:160, 0:240]
            anim = (xs + x0 - pad >= fx0) & (xs + x0 - pad < fx1) & (ys + y0 - pad >= fy0) & (ys + y0 - pad < fy1)
            d &= ~anim
        if o.get('dialog'):
            d[112:] = False                               # the message box covers the bottom rows
        results.append(dict(frame=tag, map=o['map'], position=[o['x'], o['y']], mismatched_map_layer_pixels=int(d.sum()),
                            animated_waterfall_pixels_skipped=int(anim.sum())))
    return results

def waterfall_moves(out):
    """The falls animate: two captures 16 frames apart differ inside the waterfall, and nowhere else."""
    a, b = (RC.map_layers(out / f'vram-{t}.bin') for t in ('falls-foot', 'falls-foot-later'))
    diff = (a != b).any(-1)
    return dict(pixels_changed=int(diff.sum()), rows_changed=sorted({int(y) for y in np.nonzero(diff.any(1))[0]}))

def main(game, out):
    out.mkdir(parents=True, exist_ok=True)
    plan = steps(game)
    body = []
    for s in plan:
        if s[0] == 'face':                               # face a cell, press A: a script must take the player
            body.append(f'tap({KEY[s[1]]});frames(1,A);frames(360,0);need(locked(),"{s[2]}");shot("{s[2]}");close_dialog();frames(120,0);')
        else:
            RC.STEPS = [s]
            body.append(RC.body())
    RC.STEPS = []
    RC.SAVE = SAVE
    src_text = RC.generate().replace('  \n  go(SAVE_MAP', '  ' + '\n  '.join(body) + '\n  go(SAVE_MAP')
    assert '\n  '.join(body) in src_text
    src_text = src_text.replace('"route46-native-proof"', '"mt-mortar-native-proof"').replace('route46.sav', 'mt-mortar.sav')
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
    dialogs = {s[2] for s in plan if s[0] == 'face'}
    for p in phases:
        for o in p['observations']:
            if o.get('step', '')[5:] in dialogs:
                o['dialog'] = True
    frames = check_frames(out, game, phases)
    anim = waterfall_moves(out)
    rom = hashlib.sha256((game / 'pokeemerald.gba').read_bytes()).hexdigest()
    (out / 'results.json').write_text(json.dumps(dict(rom_sha256=rom, steps=[list(map(str, s)) for s in plan], phases=phases,
                                                      background_parity=frames, waterfall_animation=anim), indent=2) + '\n')
    bad = [f for f in frames if f['mismatched_map_layer_pixels']]
    assert anim['pixels_changed'] > 0, 'the waterfall does not animate'
    print(json.dumps(dict(rom_sha256=rom, frames=len(frames), frames_with_background_mismatch=len(bad))))
    for f in bad:
        print('  mismatch', f)
    assert not bad

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
