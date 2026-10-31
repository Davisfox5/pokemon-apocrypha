"""Headless mGBA checks for Dark Cave and its doors on Routes 45 and 46.

    python3 tools/gba/maps/dark_cave/runtime.py ENGINE_CHECKOUT OUT_DIR

The harness is Route 46's (route46/runtime_convert.py: one fresh emulator process per phase,
write / cold read / title Continue; every capture dumps VRAM, BG palettes and registers). Every
capture on a Dark Cave map must rebuild, from that dump, to the installed map decoded natively
(check.decode) pixel for pixel, the void border block beyond its edges; Route 45 and Route 46
captures are rebuilt against Route 46's expected maps (runtime_convert.expected).

Steps: the caves dark, as HGSS has them without Flash (FLAG_SYS_USE_FLASH clear: Gen 3 narrows
the view through its window registers; the map layers are unchanged); FLAG_SYS_USE_FLASH set,
views across both maps (set again after each step outdoors, which clears it, as Gen 3 does); all three wired doors walked both ways (Route 45's mouth to the Route 45
side's exit and back, the Route 45 side's exit to the Route 31 side's hole and back, the Route 31
side's exit to Route 46's mouth and back); a south ledge jumped one way; Surf on both pools (a warp
onto water starts Surf); the Rock Smash rock beside the Route 46 door and the Strength boulder block
a player on foot; Route 31's exit stays solid; ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import hashlib, json, os, shlex, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'route46')); sys.path.insert(0, str(HERE.parent))
import check as C                                   # noqa: E402
import runtime_convert as RC                        # noqa: E402

ROUTE45, ROUTE46, S45, S31 = 47, 48, 49, 50          # sMapProofMaps indices = gMapGroup_Cherrygrove ids
CAVES = {S45: 'DarkCaveRoute45Side', S31: 'DarkCaveRoute31Side'}
FLASH = 2184                                         # FLAG_SYS_USE_FLASH: SYSTEM_FLAGS (0x500 + 864) + 0x28

STEPS = [
    # Dark: no Flash yet.
    ('view', S45, 58, 4, 'dark-route45-side-entrance'), ('view', S31, 30, 6, 'dark-route31-side-pool'),
    ('flash',),
    ('view', S45, 58, 4, 'route45-side-entrance'), ('view', S45, 40, 9, 'route45-side-north-hall'),
    ('view', S45, 30, 28, 'route45-side-plateaus'), ('view', S45, 45, 33, 'route45-side-lake'),
    ('view', S45, 8, 30, 'route45-side-west-ledges'), ('view', S45, 20, 50, 'route45-side-south'),
    ('view', S45, 6, 55, 'route45-side-hole-exit'),
    ('view', S31, 10, 15, 'route31-side-west-cavern'), ('view', S31, 26, 6, 'route31-side-hole'),
    ('view', S31, 40, 14, 'route31-side-north'), ('view', S31, 48, 30, 'route31-side-east-hall'),
    ('view', S31, 46, 45, 'route31-side-south-hall'), ('view', S31, 55, 54, 'route31-side-route46-exit'),
    ('view', S31, 6, 24, 'route31-side-route31-exit'),
    # Route 45's mouth north into the Route 45 side; its exit south back out.
    ('go', ROUTE45, 10, 7), ('north', 1, None), ('wait', 300), ('at', S45, 60, 4), ('shot', 'arrive-from-route45'),
    ('south', 1, None), ('wait', 300), ('at', ROUTE45, 10, 7), ('shot', 'back-on-route45'), ('flash',),
    # The Route 45 side's exit south down to the Route 31 side's hole; north back up.
    ('go', S45, 6, 56), ('south', 1, None), ('at', S45, 6, 57), ('south', 1, None), ('wait', 300), ('at', S31, 26, 5),
    ('shot', 'arrive-from-route45-side'), ('north', 1, None), ('wait', 300), ('at', S45, 6, 57), ('shot', 'back-on-route45-side'),
    # The Route 31 side's exit south to Route 46's mouth; north back in.
    ('go', S31, 55, 55), ('south', 1, None), ('at', S31, 55, 56), ('south', 1, None), ('wait', 300), ('at', ROUTE46, 20, 10),
    ('shot', 'arrive-on-route46'), ('north', 1, None), ('wait', 300), ('at', S31, 55, 56), ('shot', 'back-in-route31-side'),
    ('flash',),                                     # Route 46 is outdoors: Gen 3 cleared Flash there
    # A south ledge, one way.
    ('go', S45, 8, 22), ('south', 1, None), ('at', S45, 8, 24), ('shot', 'ledge-jumped-south'), ('north', 1, None), ('at', S45, 8, 24),
    # Surf: a warp onto water starts it.
    ('go', S45, 40, 33), ('surfing', 1, 'route45-side-lake'), ('shot', 'surfing-route45-side-lake'),
    ('go', S31, 20, 9), ('surfing', 1, 'route31-side-pool'), ('shot', 'surfing-route31-side-pool'),
    # Field obstacles block a player on foot; Route 31's exit stays solid.
    ('go', S31, 55, 54), ('north', 1, None), ('at', S31, 55, 54), ('shot', 'rock-smash-rock'),
    ('go', S31, 28, 21), ('north', 1, None), ('at', S31, 28, 21), ('shot', 'strength-boulder'),
    ('go', S31, 5, 25), ('south', 1, None), ('at', S31, 5, 25), ('shot', 'route31-exit-solid'),
]
SAVE = (S31, 26, 5)

def cave_canvas(img, grid, border):
    """A cave map as the camera sees it: 16 cells of its border block (a black void metatile) beyond
    each edge."""
    Hh, Ww = img.shape[0] // 16, img.shape[1] // 16
    y, x = np.argwhere((grid & 1023) == border)[0]
    void = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
    P = 16
    out = np.tile(void, (Hh + 2 * P, Ww + 2 * P, 1))
    out[P * 16:(P + Hh) * 16, P * 16:(P + Ww) * 16] = img
    return out, P * 16

def expected(game):
    maps = RC.expected(game)
    for k, name in CAVES.items():
        d = C.decode(game, name, 'dark_cave', 'dark_cave', C.W, C.H)
        border = set(np.frombuffer((game / f'data/layouts/{name}/border.bin').read_bytes(), '<u2').tolist())
        assert len(border) == 1, border
        maps[k] = cave_canvas(d['img'].astype(np.int32) >> 3, d['grid'].astype(np.int32), border.pop() & 1023)
    return maps

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    maps = expected(game)
    results = []
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        if tag in RC.INTERIOR:
            continue
        o = positions[tag]
        ref, pad = maps[o['map']]
        shot = RC.map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        x0, y0 = o['x'] * 16 - 112 + pad, o['y'] * 16 - 72 + pad
        anim = RC.animated(p) if o['map'] not in CAVES else np.zeros((160, 240), bool)   # CherrygrovePrimary's sea on the routes
        d = (ref[y0:y0 + 160, x0:x0 + 240] != shot).any(-1)
        results.append(dict(frame=tag, map=o['map'], position=[o['x'], o['y']], mismatched_map_layer_pixels=int((d & ~anim).sum()),
                            animated_water_pixels_skipped=int(anim.sum())))
    return results

def main(game, out):
    out.mkdir(parents=True, exist_ok=True)
    RC.STEPS = [s for s in STEPS if s[0] != 'flash']
    RC.SAVE = SAVE
    body = []
    for s in STEPS:                                  # RC.body() renders every step but the flash one
        if s[0] == 'flash':
            body.append(f'call("FlagSet",{FLASH});')
        else:
            RC.STEPS = [s]
            body.append(RC.body())
    RC.STEPS = []
    src_text = RC.generate().replace('  \n  go(SAVE_MAP', '  ' + '\n  '.join(body) + '\n  go(SAVE_MAP')
    assert '\n  '.join(body) in src_text
    src_text = src_text.replace('"route46-native-proof"', '"dark-cave-native-proof"').replace('route46.sav', 'dark-cave.sav')
    assert f'#define SAVE_MAP {SAVE[0]}' in src_text
    src = out / 'runtime.c'; src.write_text(src_text)
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '-lmgba'))
    subprocess.run(['cc', '-O1', str(src), *flags, '-o', str(out / 'runtime')], check=True)
    raw = subprocess.check_output([os.environ.get('ARM_NM', 'arm-none-eabi-nm'), str(game / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'MapProof_Resume', 'gMapProofState', 'TrySavingData',
              'LoadGameSave', 'ArePlayerFieldControlsLocked', 'gMain', 'CB2_Overworld', 'gSaveBlock2Ptr', 'sGpuRegBuffer',
              'sWarpDestination', 'DoWarp', 'gPlayerAvatar', 'FlagSet'}
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
            (out / 'results.json').write_text(json.dumps(dict(phases=phases), indent=2) + '\n')
            raise SystemExit(f'{phase} failed: {r.stderr}')
    frames = check_frames(out, game, phases)
    rom = hashlib.sha256((game / 'pokeemerald.gba').read_bytes()).hexdigest()
    (out / 'results.json').write_text(json.dumps(dict(rom_sha256=rom, phases=phases, background_parity=frames), indent=2) + '\n')
    bad = [f for f in frames if f['mismatched_map_layer_pixels']]
    print(json.dumps(dict(rom_sha256=rom, frames=len(frames), frames_with_background_mismatch=len(bad))))
    for f in bad:
        print('  mismatch', f)
    assert not bad

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
