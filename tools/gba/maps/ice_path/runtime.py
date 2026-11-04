"""Headless mGBA checks for Ice Path and its doors on Route 44 and Blackthorn.

    python3 tools/gba/maps/ice_path/runtime.py ENGINE_CHECKOUT OUT_DIR

Dark Cave's harness (dark_cave/runtime.py, Route 46's runtime_convert: one fresh emulator process
per phase, write / cold read / title Continue). Every capture on an Ice Path floor must rebuild,
from its VRAM dump, to the installed floor decoded natively, its border block beyond its edges.
Route 44 and Blackthorn captures check the player's position only (check.py proves neither map
changed a pixel).

Steps: a view of every floor; both doors walked both ways (Route 44's mouth and Blackthorn's);
every ladder pair walked down and back up; every stair flight walked up and back down; a B1F hole dropped through to its B2F cell; an ice
slide on 1F and one on B2F, each run until it stops where the floor's own cells say (a slide stops
on the last ice cell before a blocked cell, or on the first cell off the ice); a B1F Strength
boulder pushed into a hole by a planned sequence of real moves (planner(): the player slides on
ice as Gen 3 does), after which its own flag is set and its B2F copy's flag clear; the B3F Rock
Smash rock blocks; ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import hashlib, importlib.util, json, os, shlex, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
def _load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(sp); sys.modules[name] = mod; sp.loader.exec_module(mod)
    return mod

sys.path.insert(0, str(HERE))
P = _load('pack', HERE / 'pack.py')                 # Ice Path's own (route46/ has a pack.py too)
I = _load('install', HERE / 'install.py')
sys.path.insert(1, str(HERE.parent / 'route46')); sys.path.insert(2, str(HERE.parent))
import runtime_convert as RC                        # noqa: E402
spec = importlib.util.spec_from_file_location('dark_cave_check', HERE.parent / 'dark_cave/check.py')
sys.path.insert(0, str(HERE.parent / 'dark_cave'))
DC = importlib.util.module_from_spec(spec); spec.loader.exec_module(DC)

BLACKTHORN, ROUTE44, F1, B1, B2, B3 = 43, 60, 62, 63, 64, 65    # sMapProofMaps indices = gMapGroup_Cherrygrove ids
FLOORS = {F1: 'IcePath_1F', B1: 'IcePath_B1F', B2: 'IcePath_B2F', B3: 'IcePath_B3F'}
SIDE = {F1: '1f', B1: 'b1f', B2: 'b2f', B3: 'b3f'}
STRENGTH = 2185                                      # FLAG_SYS_USE_STRENGTH: SYSTEM_FLAGS (0x860) + 0x29
DIRS = dict(north=(0, -1), south=(0, 1), west=(-1, 0), east=(1, 0))

def grid(game, m):
    w, h = P.SIZE[SIDE[m]]
    d = DC.decode(game, FLOORS[m], 'ice_path', 'ice_path', w, h)
    names = {v: k for k, v in P.behaviors(game).items()}
    beh = np.vectorize(lambda v: names[int(v)])(d['beh'])
    return beh, d['coll']

def slide(beh, coll, x, y, dx, dy, block=()):
    """Gen 3 ForcedMovement_Slip: one step, then on ice keep going until the next cell is blocked or off the ice."""
    H, W = beh.shape
    free = lambda a, b: 0 <= a < W and 0 <= b < H and not coll[b, a] and (a, b) not in block
    if not free(x + dx, y + dy):
        return x, y
    x, y = x + dx, y + dy
    while beh[y, x] == 'MB_ICE' and free(x + dx, y + dy):
        x, y = x + dx, y + dy
    return x, y

def find_slide(beh, coll, min_len=4):
    """A floor cell beside the ice and a direction whose slide runs at least min_len cells."""
    H, W = beh.shape
    best = None
    for y in range(H):
        for x in range(W):
            if coll[y, x] or beh[y, x] != 'MB_CAVE':
                continue
            for name, (dx, dy) in DIRS.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and beh[ny, nx] == 'MB_ICE' and not coll[ny, nx]:
                    ex, ey = slide(beh, coll, x, y, dx, dy)
                    n = abs(ex - x) + abs(ey - y)
                    if n >= min_len and (best is None or n > best[0]):
                        best = (n, (x, y), name, (ex, ey))
    return best

def planner(beh, coll, boulders, start_boulder, holes, limit=400000):
    """Breadth-first over (boulder, player) for one boulder into any hole; the other boulders stand
    still; the player slides on ice, and after a push steps into the boulder's old cell (the harness
    holds the direction until the player moves). Returns (start cell, [direction, ...], hole)."""
    H, W = beh.shape
    others = set(boulders) - {start_boulder}
    open_ = lambda a, b: 0 <= a < W and 0 <= b < H and not coll[b, a] and (a, b) not in others and beh[b, a] not in ('MB_LADDER', 'MB_MT_PYRE_HOLE')
    bx, by = start_boulder
    starts = [(bx - dx, by - dy) for dx, dy in DIRS.values() if open_(bx - dx, by - dy)]
    best = None
    for p0 in starts:
        q = deque([((bx, by), p0, ())]); seen = {((bx, by), p0)}
        while q and len(seen) < limit:
            b, p, path = q.popleft()
            if best and len(path) >= len(best[1]):
                break
            for name, (dx, dy) in DIRS.items():
                nx, ny = p[0] + dx, p[1] + dy
                if (nx, ny) == b:                              # push
                    tx, ty = b[0] + dx, b[1] + dy
                    if 0 <= tx < W and 0 <= ty < H and not coll[ty, tx] and (tx, ty) not in others and beh[ty, tx] != 'MB_LADDER':
                        if (tx, ty) in holes:
                            if not best or len(path) + 1 < len(best[1]):
                                best = (p0, list(path) + [name], (tx, ty))
                            continue
                        # the harness holds the direction until the player moves: after the push the player
                        # steps into the boulder's old cell (and slides on, if it is ice, up to the boulder)
                        np_ = slide(beh, coll, p[0], p[1], dx, dy, block=others | {(tx, ty)})
                        st = ((tx, ty), np_)
                        if st not in seen:
                            seen.add(st); q.append(((tx, ty), np_, path + (name,)))
                    continue
                if not open_(nx, ny):
                    continue
                np_ = slide(beh, coll | 0, p[0], p[1], dx, dy, block=others | {b})
                st = (b, np_)
                if st not in seen and np_ != p:
                    seen.add(st); q.append((b, np_, path + (name,)))
    return best

def steps(game):
    out = []
    for m in FLOORS:
        w, h = P.SIZE[SIDE[m]]
        ev = json.loads((game / f'data/maps/{FLOORS[m]}/map.json').read_text())
        wx, wy = ev['warp_events'][0]['x'], ev['warp_events'][0]['y']
        out.append(('view', m, wx, min(h - 1, wy + 1) if m in (F1,) else wy, f'view-{SIDE[m]}'))
    # the doors: Route 44's mouth and Blackthorn's, each walked in and back out
    out += [('go', ROUTE44, 89, 10), ('north', 1, None), ('wait', 300), ('at', F1, 11, 58), ('shot', 'arrive-from-route44'),
            ('south', 1, None), ('wait', 300), ('at', ROUTE44, 89, 10), ('shot', 'back-on-route44'),
            ('go', BLACKTHORN, 57, 17), ('north', 1, None), ('wait', 300), ('at', F1, 55, 40), ('shot', 'arrive-from-blackthorn'),
            ('south', 1, None), ('wait', 300), ('at', BLACKTHORN, 57, 17), ('shot', 'back-in-blackthorn')]
    # every ladder pair: onto the ladder, arrive on its partner, step off and back on
    maps = {m: json.loads((game / f'data/maps/{FLOORS[m]}/map.json').read_text()) for m in FLOORS}
    ids = {v: k for k, v in FLOORS.items()}
    done = set()
    for m, mj in maps.items():
        beh, coll = grid(game, m)
        for i, wv in enumerate(mj['warp_events']):
            if beh[wv['y'], wv['x']] != 'MB_LADDER' or (m, i) in done:
                continue
            dm = ids[{v: k for k, v in I.IDS.items()}[wv['dest_map']]]
            back = maps[dm]['warp_events'][int(wv['dest_warp_id'])]
            done |= {(m, i), (dm, int(wv['dest_warp_id']))}
            # step onto the ladder from a free floor cell beside it
            approach = next(((wv['x'] - dx, wv['y'] - dy, n) for n, (dx, dy) in DIRS.items()
                             if 0 <= wv['y'] - dy < beh.shape[0] and 0 <= wv['x'] - dx < beh.shape[1]
                             and not coll[wv['y'] - dy, wv['x'] - dx] and beh[wv['y'] - dy, wv['x'] - dx] in ('MB_CAVE', 'MB_ICE')), None)
            if approach is None:
                continue
            ax, ay, n = approach
            out += [('go', m, ax, ay), (n, 1, None), ('wait', 300), ('at', dm, back['x'], back['y']),
                    ('shot', f'ladder-{SIDE[m]}-{wv["x"]}-{wv["y"]}')]
    # a B1F hole: walked into, the player lands on HGSS's B2F cell
    (hx, hy), (lx, ly) = I.DROPS[0]
    beh1, coll1 = grid(game, B1)
    ax, ay, n = next(((hx - dx, hy - dy, nm) for nm, (dx, dy) in DIRS.items() if not coll1[hy - dy, hx - dx] and beh1[hy - dy, hx - dx] == 'MB_CAVE'))
    out += [('go', B1, ax, ay), (n, 1, None), ('wait', 400), ('at', B2, lx, ly), ('shot', 'dropped-to-b2f')]
    # ice slides on 1F and B2F
    for m in (F1, B2):
        beh, coll = grid(game, m)
        n, (sx, sy), name, (ex, ey) = find_slide(beh, coll)
        out += [('go', m, sx, sy), (name, 1, None), ('wait', 120), ('at', m, ex, ey), ('shot', f'slid-{SIDE[m]}')]
    # a Strength boulder into a hole, by real moves
    b1 = maps[B1]['object_events']
    boulders = [(o['x'], o['y']) for o in b1 if 'BOULDER' in o['graphics_id']]
    holes = {h for h, _ in I.DROPS}
    plans = []
    for o in b1:
        if not o['trainer_type'].startswith('FLAG_'):
            continue
        pl = planner(beh1, coll1, boulders, (o['x'], o['y']), holes)
        if pl:
            plans.append((len(pl[1]), o, pl))
    plans.sort(key=lambda t: t[0])
    if plans:
        _, o, (p0, moves, hole) = plans[0]
        out += [('go', B1, p0[0], p0[1]), ('strength',)] + [(mv, 1, None) for mv in moves] + [('wait', 200), ('shot', 'boulder-in-hole'),
                ('flagis', o['flag'], 1, 'b1f-boulder-gone'), ('flagis', o['trainer_type'], 0, 'b2f-boulder-shown')]
    # every stair flight walked up through its wall and back down
    for m in FLOORS:
        led = json.loads((I.SRC / f'assemble/{SIDE[m]}-ledger.json').read_text())['cells']
        st = {(c['x'], c['y']) for c in led if c.get('piece') == 'stairs'}
        for x, y in sorted(st):
            if (x - 1, y) in st:
                continue
            out += [('go', m, x, y + 1), ('north', 2, None), ('at', m, x, y - 1), ('shot', f'stairs-{SIDE[m]}-{x}-{y}'),
                    ('south', 2, None), ('at', m, x, y + 1)]
    # B3F's Rock Smash rock blocks
    out += [('go', B3, 10, 13), ('north', 1, None), ('at', B3, 10, 13), ('shot', 'rock-smash-rock')]
    return out

SAVE = (F1, 11, 57)

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
        d = DC.decode(game, name, 'ice_path', 'ice_path', w, h)
        border = set(np.frombuffer((game / f'data/layouts/{name}/border.bin').read_bytes(), '<u2').tolist())
        maps[k] = cave_canvas(d['img'].astype(np.int32) >> 3, d['grid'].astype(np.int32), border.pop() & 1023)
    results = []
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        o = positions.get(tag)
        if tag in RC.INTERIOR or o is None or o['map'] not in maps:     # the Continue menu is not a map frame
            continue
        ref, pad = maps[o['map']]
        shot = RC.map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        x0, y0 = o['x'] * 16 - 112 + pad, o['y'] * 16 - 72 + pad
        d = (ref[y0:y0 + 160, x0:x0 + 240] != shot).any(-1)
        results.append(dict(frame=tag, map=o['map'], position=[o['x'], o['y']], mismatched_map_layer_pixels=int(d.sum())))
    return results

def main(game, out):
    out.mkdir(parents=True, exist_ok=True)
    plan = steps(game)
    flagnum = {k: int(v.split('0x')[1], 16) for k, v in I.FLAGS.items()}
    body = []
    for s in plan:
        if s[0] == 'strength':
            body.append(f'call("FlagSet",{STRENGTH});')
        elif s[0] == 'flagis':
            body.append(f'need(call("FlagGet",{flagnum[s[1]]})=={s[2]},"{s[3]}");')
        else:
            RC.STEPS = [s]
            body.append(RC.body())
    RC.STEPS = []
    RC.SAVE = SAVE
    src_text = RC.generate().replace('  \n  go(SAVE_MAP', '  ' + '\n  '.join(body) + '\n  go(SAVE_MAP')
    assert '\n  '.join(body) in src_text
    src_text = src_text.replace('"route46-native-proof"', '"ice-path-native-proof"').replace('route46.sav', 'ice-path.sav')
    src = out / 'runtime.c'; src.write_text(src_text)
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '-lmgba'))
    subprocess.run(['cc', '-O1', str(src), *flags, '-o', str(out / 'runtime')], check=True)
    raw = subprocess.check_output([os.environ.get('ARM_NM', 'arm-none-eabi-nm'), str(game / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'MapProof_Resume', 'gMapProofState', 'TrySavingData',
              'LoadGameSave', 'ArePlayerFieldControlsLocked', 'gMain', 'CB2_Overworld', 'gSaveBlock2Ptr', 'sGpuRegBuffer',
              'sWarpDestination', 'DoWarp', 'gPlayerAvatar', 'FlagSet', 'FlagGet'}
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

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
