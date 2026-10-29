"""Headless mGBA checks for Celadon round 6 (the streamed city, celadon_view.c).

    python3 tools/gba/maps/celadon_elements/runtime6.py ENGINE_CHECKOUT OUT_DIR

Each phase is a fresh emulator process (Olivine's harness, runtime_elements):
    write  new game; stand at every door, in the market, on the three bridges, in the
           Arboretum and at both road ends; walk the main road, the west avenue, the cross
           street, the terraces' lane, the Arboretum's walk and the promenade end to end with a capture every few steps (the glyph
           cache and the palette banks turning over as the camera moves); stand behind a
           stall, a house, the cafe, a lamp, the blossom pool, a bench and a tree; read the
           five signs; try the two doors with no room yet (they stay shut); enter and leave
           the Center (both floors), the services, the hotel (up its stairs and down), the
           Game Corner, its prize room up the stairs, and the cafe; visit Cherrygrove,
           Olivine and Saffron and come back; ordinary flash save
    read   cold flash reload of that save
    menu   title screen -> Continue
Every capture also dumps VRAM, BG palettes and BG registers. The map layers (BG1-BG3) are
rebuilt from that dump and must match stream6.py's decode pixel for pixel in 5-bit colour
(the fountains' animated glyph slots set aside), in the city and in every room: so every
streamed glyph and every streamed palette bank is right wherever the camera has been.
Behind an object BG1 must cover the player's cell; in front of a door it must leave the
player's two cells clear.
"""
from __future__ import annotations
import hashlib, json, os, shlex, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

import common as C
import stream6 as S
import install as I
import install6 as I6
import interiors as IN
sys.path.append(str(C.HERE.parent))
import runtime_elements as RE                       # noqa: E402  (Olivine's VRAM decoding and harness)
sys.path[:] = [p for p in sys.path if p != str(C.OLIVINE)] + [str(C.OLIVINE)]

ROOT = C.ROOT
W, H = S.W, S.H
KANTO0 = 54
CITY, CENTER, UPSTAIRS, SERVICES, HOTEL, HOTEL_UP, GAME_CORNER, PRIZE_ROOM, GARDENS, CAFE = range(60, 70)
ROOM_INDEX = dict(services=SERVICES, hotel_1f=HOTEL, hotel_2f=HOTEL_UP, game_corner=GAME_CORNER, prize_room=PRIZE_ROOM,
                  gardens=GARDENS, cafe=CAFE)
SAFFRON, OLIVINE = 54, 50
KANTO_GROUP, CHERRYGROVE_GROUP = 81, 80
REPORT = json.loads((S.OUT / 'stream.json').read_text())
INSTALL = json.loads((S.OUT / 'install.json').read_text())
DOORS = {k: tuple(v) for k, v in REPORT['doors'].items()}
SAVE = (CITY, DOORS['center'][0], DOORS['center'][1] + 1)
PIN_BASE = 1008 - REPORT['glyphs_pinned']

def arrival_xy(room):
    return list(IN.ROOMS[room][2])[I.arrival(room)]

def room_trip(room, door, tag):
    """In by the city door, out by the exit mat the door lands on."""
    dx, dy = DOORS[door]
    ax, ay = arrival_xy(room)
    return [('go', CITY, dx, dy + 1), ('north', 1, None), ('wait', 400), ('at', ROOM_INDEX[room], ax, ay), ('shot', f'room-{tag}'),
            ('go', ROOM_INDEX[room], ax, ay - 1), ('south', 2, None), ('wait', 400), ('at', CITY, dx, dy + 1), ('shot', f'{tag}-exit')]

WALK_BEHIND = {f'behind-{k}': tuple(REPORT['walk_behind'][k]) for k in
               ('stall_14_24', 'house_g1', 'cafe', 'lamp_19_33', 'blossom', 'bench_7_42')}
WALK_BEHIND['behind-tree'] = tuple(next(v for k, v in REPORT['walk_behind'].items() if k.startswith('tree') and v[1] > 36))

def walk(x, y, moves, tag):
    """From (x, y), each (direction, steps) in turn, a capture after each."""
    out = [('go', CITY, x, y), ('shot', f'{tag}-0')]
    for i, (d, n) in enumerate(moves):
        out.append((d, n, f'{tag}-{i + 1}'))
    return out

def steps():
    out = []
    for door, (x, y) in DOORS.items():
        out.append(('view', CITY, x, y + 1, f'{door}-front'))
    out += [('view', CITY, 12, 27, 'market'), ('view', CITY, 22, 18, 'main-bridge'), ('view', CITY, 22, 35, 'cross-bridge'),
            ('view', CITY, 22, 41, 'footbridge'), ('view', CITY, 41, 44, 'blossom-plaza'), ('view', CITY, 14, 44, 'pond-west'),
            ('view', CITY, 52, 27, 'terraces'), ('view', CITY, 50, 33, 'cafe-lane'), ('view', CITY, 63, 18, 'route7-edge'),
            ('view', CITY, 0, 36, 'route16-edge'), ('view', CITY, 8, 15, 'dept-store-west')]
    out += [('go', CITY, 12, 33)] + [x for f in range(8) for x in (('wait', 10), ('shot', f'fountain-{f}'))]
    out += [('go', CITY, 41, 45)] + [x for f in range(8) for x in (('wait', 10), ('shot', f'blossom-{f}'))]
    # The camera's long walks: the main road west, the avenue south, the cross street east,
    # the terraces' lane, down the Arboretum's walk and along the promenade
    out += walk(60, 17, [('west', 6)] * 9, 'walk-road')
    out += walk(7, 17, [('south', 4)] * 5, 'walk-avenue')
    out += walk(7, 35, [('east', 6)] * 8, 'walk-cross')
    out += walk(46, 27, [('east', 4)] * 3, 'walk-lane')
    out += walk(12, 37, [('south', 3)] * 4, 'walk-arboretum')
    out += walk(5, 41, [('east', 6)] * 9, 'walk-promenade')
    for tag, (x, y) in WALK_BEHIND.items():
        out += [('go', CITY, x, y), ('shot', tag)]
    for label, (x, y) in INSTALL['city']['signs'].items():
        out.append(('sign', CITY, x, y, 'sign-' + label))
    # The doors with no room yet stay shut.
    for name in ('apartments', 'house_g0'):
        x, y = S.PL.DOORS[name]
        out += [('go', CITY, x, y + 1), ('north', 1, None), ('wait', 60), ('at', CITY, x, y + 1)]
    cx, cy = DOORS['center']
    out += [('go', CITY, cx, cy + 1), ('north', 1, None), ('wait', 400), ('map', CENTER, 'center-entry'), ('shot', 'center-interior'),
            ('go', CENTER, 2, 6), ('west', 1, None), ('wait', 400), ('map', UPSTAIRS, 'center-upstairs'), ('shot', 'center-upstairs'),
            ('west', 1, None), ('wait', 400), ('map', CENTER, 'center-stair-return'),
            ('go', CENTER, 7, 7), ('south', 2, None), ('wait', 400), ('at', CITY, cx, cy + 1), ('shot', 'center-exit')]
    out += room_trip('services', 'dept_store', 'services')
    out += room_trip('game_corner', 'gamecorner', 'game-corner')
    # The prize counter: up the Game Corner's stairs (FireRed's side stairs warp walking east).
    out += [('go', GAME_CORNER, 15, 2), ('east', 1, None), ('wait', 400), ('map', PRIZE_ROOM, 'prize-room-entry'),
            ('shot', 'room-prize-room'), ('go', PRIZE_ROOM, 4, 7), ('south', 2, None), ('wait', 400),
            ('map', GAME_CORNER, 'prize-room-return'), ('shot', 'game-corner-stairs')]
    out += room_trip('cafe', 'cafe', 'cafe')
    hx, hy = DOORS['hotel']
    ax, ay = arrival_xy('hotel_1f')
    out += [('go', CITY, hx, hy + 1), ('north', 1, None), ('wait', 400), ('at', HOTEL, ax, ay), ('shot', 'room-hotel-lobby'),
            ('go', HOTEL, 4, 2), ('east', 1, None), ('wait', 400), ('map', HOTEL_UP, 'hotel-upstairs'), ('shot', 'room-hotel-upstairs'),
            ('go', HOTEL_UP, 4, 2), ('east', 1, None), ('wait', 400), ('map', HOTEL, 'hotel-stair-return'),
            ('go', HOTEL, ax, ay - 1), ('south', 2, None), ('wait', 400), ('at', CITY, hx, hy + 1), ('shot', 'hotel-exit')]
    out += [('view', 0, 50, 17, 'regression-cherrygrove'), ('view', OLIVINE, 16, 35, 'regression-olivine'),
            ('view', SAFFRON, 24, 40, 'regression-saffron'), ('view', CITY, SAVE[1], SAVE[2], 'return-to-celadon')]
    return out

STEPS = steps()
IN_FRONT = tuple(f'{d}-front' for d in DOORS) + ('center-exit', 'services-exit', 'game-corner-exit', 'cafe-exit', 'hotel-exit')
ROOM_TAGS = {'room-services': 'services', 'room-game-corner': 'game_corner', 'game-corner-stairs': 'game_corner',
             'room-prize-room': 'prize_room', 'room-cafe': 'cafe', 'room-hotel-lobby': 'hotel_1f', 'room-hotel-upstairs': 'hotel_2f'}

def body():
    keys = dict(north='UP', south='DOWN', east='RIGHT', west='LEFT')
    out = []
    for s in STEPS:
        k = s[0]
        if k == 'view':
            out.append(f'go({s[1]},{s[2]},{s[3]});shot("{s[4]}");')
        elif k == 'go':
            out.append(f'go({s[1]},{s[2]},{s[3]});')
        elif k in keys:
            out.append(f'step({keys[k]},{s[1]});' + (f'shot("{s[2]}");' if s[2] else ''))
        elif k == 'at':
            out.append(f'at({s[1]},{s[2]},{s[3]},"at-{s[1]}-{s[2]}-{s[3]}");')
        elif k == 'sign':   # face the sign from below, then wait for the whole text to print
            out.append(f'go({s[1]},{s[2]},{s[3]}+1);tap(UP);frames(1,A);frames(360,0);need(locked(),"{s[4]}");shot("{s[4]}");close_dialog();')
        elif k == 'wait':
            out.append(f'frames({s[1]},0);')
        elif k == 'map':
            out.append(f'observe("{s[2]}");need(state[1]=={KANTO_GROUP}&&state[2]=={s[1] - KANTO0},"{s[2]}");')
        elif k == 'shot':
            out.append(f'shot("{s[1]}");')
    return '\n  '.join(out)

def generate():
    prefix = RE.TEMPLATE.split('int main(')[0].replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    defines = ('#define A 1\n#define B 2\n#define RIGHT 16\n#define LEFT 32\n#define UP 64\n#define DOWN 128\n'
               f'#define SAVE_MAP {SAVE[0]}\n#define SAVE_X {SAVE[1]}\n#define SAVE_Y {SAVE[2]}\n')
    prefix = prefix.replace('#undef main', '#undef main\n' + defines, 1)
    old = 'static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);need(state[1]==80&&state[2]==map&&state[3]==x&&state[4]==y,tag);}'
    assert old in prefix
    prefix = prefix.replace(old, 'static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);'
                            f'unsigned grp=map>={KANTO0}?{KANTO_GROUP}:{CHERRYGROVE_GROUP},num=map>={KANTO0}?map-{KANTO0}:map;'
                            'need(state[1]==grp&&state[2]==num&&state[3]==x&&state[4]==y,tag);}')
    old = 'static void shot(const char*t){screenshot(out,t);}'
    assert old in prefix
    prefix = prefix.replace(old, r'''static void vram(const char*t){char p[2048];snprintf(p,sizeof(p),"%s/vram-%s.bin",out,t);FILE*f=fopen(p,"wb");
 for(unsigned a=0x06000000;a<0x06010000;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 for(unsigned a=0x05000000;a<0x05000200;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 unsigned short r[13];r[0]=c->busRead16(c,0x04000000);for(int i=0;i<4;i++)r[1+i]=c->busRead16(c,0x04000008+2*i);
 unsigned g=sym("sGpuRegBuffer");for(int i=0;i<8;i++)r[5+i]=c->busRead16(c,g+0x10+2*i);fwrite(r,2,13,f);fclose(f);}
static void shot(const char*t){screenshot(out,t);vram(t);char o[128];snprintf(o,sizeof(o),"shot:%s",t);observe(o);}''')
    main = RE.MAIN.replace('olivine-native-proof', 'celadon6-native-proof').replace('olivine.sav', 'celadon6.sav')
    return prefix + main.replace('BODY', body())

PAD = 16

def city_ref():
    """stream6's decode with the off-map cells the engine draws (stream6.outside), 5-bit."""
    img = np.array(Image.open(S.OUT / 'native.png').convert('RGB')).astype(np.int32) >> 3
    out = np.zeros(((H + 2 * PAD) * 16, (W + 2 * PAD) * 16, 3), np.int32)
    for py in range(H + 2 * PAD):
        for px in range(W + 2 * PAD):
            sx, sy = S.outside(px - PAD, py - PAD)
            out[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = img[sy * 16:sy * 16 + 16, sx * 16:sx * 16 + 16]
    return out, PAD * 16

def padded(img, border):
    h, w = img.shape[0] // 16, img.shape[1] // 16
    out = np.zeros(((h + 2 * PAD) * 16, (w + 2 * PAD) * 16, 3), np.int32)
    for py in range(h + 2 * PAD):
        for px in range(w + 2 * PAD):
            x, y = px - PAD, py - PAD
            cell = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16] if 0 <= x < w and 0 <= y < h else \
                border[(y & 1) * 16:(y & 1) * 16 + 16, (x & 1) * 16:(x & 1) * 16 + 16]
            out[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = cell
    return out, PAD * 16

def room_ref(key):
    p = dict(np.load(C.SRC / f'interiors/{key}.npz'))
    img = IN.decode(p).astype(np.int32) >> 3
    h = img.shape[0] // 16
    black = img[(h - 1) * 16:h * 16, 0:16]
    return padded(img, np.tile(black, (2, 2, 1)))

def pinned(dump):
    """Pixels any map layer draws from the fountains' pinned glyph slots."""
    raw = dump.read_bytes()
    vram = np.frombuffer(raw[:0x10000], np.uint8)
    regs = np.frombuffer(raw[0x10200:0x10200 + 26], '<u2').astype(np.int32)
    ys, xs = np.mgrid[0:160, 0:240]
    m = np.zeros((160, 240), bool)
    for bg in (1, 2, 3):
        c, hofs, vofs = regs[1 + bg], regs[5 + 2 * bg] & 511, regs[5 + 2 * bg + 1] & 511
        X, Y = (xs + hofs) & 255, (ys + vofs) & 255
        t = vram.view('<u2')[((c >> 8) & 31) * 0x400 + (Y // 8) * 32 + X // 8].astype(np.int32) & 1023
        m |= (t >= PIN_BASE) & (t < 1008)
    return m

def saffron_border(game):
    """Saffron's 2x2 border block, drawn with its own installed pair, in 5-bit colour (round 3's runtime.py)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('saffron_check', C.HERE.parent / 'saffron/check.py')
    sk = importlib.util.module_from_spec(spec)
    names = ('compose', 'pack', 'check', 'install', 'interiors')
    saved = {k: sys.modules.pop(k) for k in names if k in sys.modules}
    sys.path.insert(0, str(C.HERE.parent / 'saffron'))
    try:
        spec.loader.exec_module(sk)
        return sk.border_image(game).astype(np.int32) >> 3
    finally:
        sys.path.remove(str(C.HERE.parent / 'saffron'))
        for k in names:
            sys.modules.pop(k, None)
        sys.modules.update(saved)

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    city = city_ref()
    olivine = RE.padded(np.array(Image.open(ROOT / 'gba/art/olivine-elements/evidence/elements/native-C.png').convert('RGB')).astype(np.int32) >> 3,
                        (40, 58))
    from tiles import Tileset
    cg = np.frombuffer((game / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), '<u2')
    cherry = (np.array(Tileset(game, 'cherrygrove', 'cherrygrove').map_image(cg.tolist(), 80).convert('RGB')).astype(np.int32) >> 3, 0)
    saffron = padded(np.array(Image.open(ROOT / 'gba/art/saffron-kanto/evidence/native.png').convert('RGB')).astype(np.int32) >> 3,
                     saffron_border(game))
    results, rooms = [], {}
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        if any(t in tag for t in ('interior', 'center-upstairs', 'continue-menu')):
            continue
        room = next((k for t, k in ROOM_TAGS.items() if tag.startswith(t)), None)
        ref, pad = (rooms.setdefault(room, room_ref(room)) if room else cherry if tag.startswith('regression-cherrygrove')
                    else olivine if tag.startswith('regression-olivine') else saffron if tag.startswith('regression-saffron') else city)
        shot = RE.map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        o = positions[tag]
        x0, y0 = o['x'] * 16 - 112 + pad, o['y'] * 16 - 72 + pad
        d = (ref[y0:y0 + 160, x0:x0 + 240] != shot).any(-1)
        last = 92 if tag.startswith('regression-cherrygrove') else 16 if tag.startswith('regression-olivine') else 0
        anim = RE.animated(p, last) if last else (pinned(p) if ref is city[0] else np.zeros((160, 240), bool))
        r = dict(frame=tag, mismatched_map_layer_pixels=int((d & ~anim).sum()), pixels_on_animated=int(anim.sum()),
                 camera_origin_px=[int(x0 - pad), int(y0 - pad)])
        if tag in WALK_BEHIND:                              # the player's cell is at screen (112, 72)
            r['bg1_pixels_over_player_cell'] = int(RE.bg1(p)[72:88, 112:128].sum())
        if tag in IN_FRONT:                                 # head cell (112, 56) and feet cell (112, 72)
            r['bg1_pixels_over_player'] = int(RE.bg1(p)[56:88, 112:128].sum())
        results.append(r)
    return results

def main(game, out, check_only=False):
    out.mkdir(parents=True, exist_ok=True)
    if check_only:                                   # the last run's dumps again, without the emulator
        phases = json.loads((out / 'results.json').read_text())['phases']
        return report(out, game, phases)
    for p in out.glob('*'):
        p.unlink()
    src = out / 'runtime.c'; src.write_text(generate())
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '-lmgba'))
    subprocess.run(['cc', '-O1', str(src), *flags, '-o', str(out / 'runtime')], check=True)
    raw = subprocess.check_output([os.environ.get('ARM_NM', 'arm-none-eabi-nm'), str(game / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'MapProof_Resume', 'gMapProofState', 'TrySavingData',
              'LoadGameSave', 'ArePlayerFieldControlsLocked', 'gMain', 'CB2_Overworld', 'gSaveBlock2Ptr', 'sGpuRegBuffer'}
    syms = {r[2]: r[0] for line in raw.splitlines() if len(r := line.split()) == 3 and r[2] in wanted}
    assert syms.keys() == wanted, wanted - syms.keys()
    (out / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in syms.items()))
    phases = []
    for phase in ('write', 'read', 'menu'):
        r = subprocess.run([str(out / 'runtime'), str(game / 'pokeemerald.gba'), str(out / 'symbols.txt'), str(out), phase],
                           capture_output=True, text=True, timeout=3600)
        obs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
        phases.append(dict(phase=phase, exit_code=r.returncode, stderr=r.stderr.strip(), observations=obs))
        for ppm in out.glob('*.ppm'):
            Image.open(ppm).save(ppm.with_suffix('.png')); ppm.unlink()
        if r.returncode:
            (out / 'results.json').write_text(json.dumps(dict(phases=phases), indent=2) + '\n')
            raise SystemExit(f'{phase} failed: {r.stderr}')
    (out / 'results.json').write_text(json.dumps(dict(phases=phases), indent=2) + '\n')
    report(out, game, phases)

def report(out, game, phases):
    frames = check_frames(out, game, phases)
    rom = hashlib.sha256((game / 'pokeemerald.gba').read_bytes()).hexdigest()
    (out / 'results.json').write_text(json.dumps(dict(rom_sha256=rom, phases=phases, background_parity=frames), indent=2) + '\n')
    bad = [f for f in frames if f['mismatched_map_layer_pixels']]
    behind = {f['frame']: f.get('bg1_pixels_over_player_cell') for f in frames if 'bg1_pixels_over_player_cell' in f}
    front = {f['frame']: f['bg1_pixels_over_player'] for f in frames if 'bg1_pixels_over_player' in f}
    print(json.dumps(dict(rom_sha256=rom, frames=len(frames), frames_with_background_mismatch=len(bad), walk_behind_bg1=behind,
                          in_front_bg1_over_player=front)))
    for f in bad:
        print('  mismatch', f)
    if not os.environ.get('KEEP_DUMPS'):
        for p in [out / 'runtime', out / 'runtime.c', out / 'symbols.txt', *out.glob('vram-*.bin'), *out.glob('*.sav')]:
            p.unlink(missing_ok=True)
    assert not bad and all(behind.values()) and not any(front.values()), (behind, front)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), '--check-only' in sys.argv)
