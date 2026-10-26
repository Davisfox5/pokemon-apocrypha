"""Headless mGBA checks for Celadon City (KantoCeladonCity).

    python3 tools/gba/maps/celadon_elements/runtime.py ENGINE_CHECKOUT OUT_DIR

Each phase is a fresh emulator process:
    write  new game; stand in front of the Center, the services, the hotel, the Game Corner,
           its prize corner, the Gardens and the cafe, in the market, in the Gardens' beds,
           on the footbridge and at both road ends; cross the footbridge end to end; find the
           canal's fence solid; jump the Gardens' ledge; stand behind three roofs; read the
           seven signs; enter and leave the Center (both floors) and every room (the hotel up
           its stairs and down again); visit Cherrygrove, Olivine and Saffron and come back;
           ordinary flash save
    read   cold flash reload of that save
    menu   title screen -> Continue

Every capture also dumps VRAM, BG palettes and BG registers. The map layers (BG1-BG3) are
rebuilt from that dump (Olivine's runtime_elements) and must match the decoded native map
pixel for pixel, in the city and in every room (the regression towns' animated sea set
aside). Behind a roof, BG1 (the layer above the player) must cover the player's cell; in
front of a building it must leave the player's two cells clear.
"""
from __future__ import annotations
import hashlib, json, os, shlex, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

import common as C
import check as K                                   # noqa: E402
import install as I                                 # noqa: E402
import interiors as IN                              # noqa: E402
import pack as P                                    # noqa: E402
sys.path.append(str(C.HERE.parent))
import runtime_elements as RE                       # noqa: E402  (Olivine's VRAM decoding and harness)
sys.path[:] = [p for p in sys.path if p != str(C.OLIVINE)] + [str(C.OLIVINE)]   # it puts its folder first

ROOT = C.ROOT
# MapProof indices (sMapProofMaps): Saffron's maps are gMapGroup_Kanto (group 81) 0-5 from
# index 54; Celadon's follow, 6-15, in install.py's order.
KANTO0 = 54
CITY, CENTER, UPSTAIRS, SERVICES, HOTEL, HOTEL_UP, GAME_CORNER, PRIZE_ROOM, GARDENS, CAFE = range(60, 70)
ROOM_INDEX = dict(services=SERVICES, hotel_1f=HOTEL, hotel_2f=HOTEL_UP, game_corner=GAME_CORNER, prize_room=PRIZE_ROOM,
                  gardens=GARDENS, cafe=CAFE)
SAFFRON, OLIVINE = 54, 50
KANTO_GROUP, CHERRYGROVE_GROUP = 81, 80
SAVE = (CITY, 47, 15)
DOORS = {name: xy for xy, name in P.DOORS.items()}

def arrival_xy(room):
    i = I.arrival(room)
    return list(IN.ROOMS[room][2])[i]

def room_trip(room, door, tag):
    """In by the city door, out by the exit mat the door lands on."""
    dx, dy = DOORS[door]
    ax, ay = arrival_xy(room)
    return [('go', CITY, dx, dy + 1), ('north', 1, None), ('wait', 400), ('at', ROOM_INDEX[room], ax, ay), ('shot', f'room-{tag}'),
            ('go', ROOM_INDEX[room], ax, ay - 1), ('south', 2, None), ('wait', 400), ('at', CITY, dx, dy + 1), ('shot', f'{tag}-exit')]

def walk_behind():
    """Walkable cells where a building's roof draws over the player (layer type normal), one
    per building, nearest the street."""
    trav = json.loads((C.SRC / 'elements/traversal.json').read_text())
    owner = np.load(C.SRC / 'elements/compose.npz')['owner']
    picked = {}
    for c in trav:
        if c['foot'] != 'open' or c['layer'] != 'normal':
            continue
        x, y = c['x'], c['y']
        names = set(owner[y * 16:y * 16 + 16, x * 16:x * 16 + 16].ravel().tolist()) - {''}
        names = {n for n in names if not n.startswith(('tree', 'post'))}
        for n in names:
            picked.setdefault(n, (x, y))
    want = ('services', 'hotel', 'gamecorner', 'gardens', 'cafe', 'house_6')
    return {f'behind-{n}-roof': picked[n] for n in want if n in picked}

BEHIND = walk_behind()

def steps():
    out = []
    for door, (x, y) in DOORS.items():
        out.append(('view', CITY, x, y + 1, f'{door}-front'))
    out += [('view', CITY, 17, 27, 'market'), ('view', CITY, 12, 40, 'gardens-beds'), ('view', CITY, 27, 34, 'footbridge'),
            ('view', CITY, 59, 16, 'route7-edge'), ('view', CITY, 0, 34, 'route16-edge')]
    # The footbridge end to end, and back along another row; the canal's fence is solid.
    out += [('go', CITY, 24, 33), ('east', 7, None), ('at', CITY, 31, 33), ('go', CITY, 31, 35), ('west', 7, None),
            ('at', CITY, 24, 35), ('go', CITY, 31, 38), ('west', 1, None), ('at', CITY, 31, 38)]
    # The Gardens' ledge: south over it from the forecourt's kerb.
    out += [('go', CITY, 12, 45), ('south', 1, None), ('wait', 60), ('at', CITY, 12, 47), ('shot', 'below-the-ledge')]
    for tag, (x, y) in BEHIND.items():
        out += [('go', CITY, x, y), ('shot', tag)]
    for label, (x, y), _ in I.SIGNS:
        out.append(('sign', CITY, x, y, 'sign-' + label))
    out += [('go', CITY, 47, 14), ('north', 1, None), ('wait', 400), ('map', CENTER, 'center-entry'), ('shot', 'center-interior'),
            ('go', CENTER, 2, 6), ('west', 1, None), ('wait', 400), ('map', UPSTAIRS, 'center-upstairs'), ('shot', 'center-upstairs'),
            ('west', 1, None), ('wait', 400), ('map', CENTER, 'center-stair-return'),
            ('go', CENTER, 7, 7), ('south', 2, None), ('wait', 400), ('at', CITY, 47, 14), ('shot', 'center-exit')]
    out += room_trip('services', 'services', 'services')
    out += room_trip('game_corner', 'gamecorner', 'game-corner')
    out += room_trip('prize_room', 'prize', 'prize-room')
    out += room_trip('gardens', 'gardens', 'gardens')
    out += room_trip('cafe', 'cafe', 'cafe')
    hx, hy = DOORS['hotel']
    ax, ay = arrival_xy('hotel_1f')
    # FireRed's side stairs warp when the player stands on them and walks east.
    out += [('go', CITY, hx, hy + 1), ('north', 1, None), ('wait', 400), ('at', HOTEL, ax, ay), ('shot', 'room-hotel-lobby'),
            ('go', HOTEL, 4, 2), ('east', 1, None), ('wait', 400), ('map', HOTEL_UP, 'hotel-upstairs'), ('shot', 'room-hotel-upstairs'),
            ('go', HOTEL_UP, 4, 2), ('east', 1, None), ('wait', 400), ('map', HOTEL, 'hotel-stair-return'),
            ('go', HOTEL, ax, ay - 1), ('south', 2, None), ('wait', 400), ('at', CITY, hx, hy + 1), ('shot', 'hotel-exit')]
    out += [('view', 0, 50, 17, 'regression-cherrygrove'), ('view', OLIVINE, 16, 35, 'regression-olivine'),
            ('view', SAFFRON, 24, 40, 'regression-saffron'), ('view', CITY, 47, 15, 'return-to-celadon')]
    return out

STEPS = steps()
IN_FRONT = tuple(f'{d}-front' for d in DOORS) + ('center-exit', 'services-exit', 'game-corner-exit', 'prize-room-exit',
                                                  'gardens-exit', 'cafe-exit', 'hotel-exit', 'market', 'footbridge')
ROOM_TAGS = {'room-services': 'services', 'room-game-corner': 'game_corner', 'room-prize-room': 'prize_room',
             'room-gardens': 'gardens', 'room-cafe': 'cafe', 'room-hotel-lobby': 'hotel_1f', 'room-hotel-upstairs': 'hotel_2f'}

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
    main = RE.MAIN.replace('olivine-native-proof', 'celadon-native-proof').replace('olivine.sav', 'celadon.sav')
    return prefix + main.replace('BODY', body())

def padded(img, border):
    """A decoded map with its 2x2 border block beyond the edges (the camera sees it), the
    block's quarter chosen by the cell's parity as GetBorderBlockAt does."""
    H, W = img.shape[0] // 16, img.shape[1] // 16
    Pd = 16
    out = np.zeros(((H + 2 * Pd) * 16, (W + 2 * Pd) * 16, 3), np.int32)
    for py in range(H + 2 * Pd):
        for px in range(W + 2 * Pd):
            x, y = px - Pd, py - Pd
            if 0 <= x < W and 0 <= y < H:
                cell = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            else:
                cell = border[(y & 1) * 16:(y & 1) * 16 + 16, (x & 1) * 16:(x & 1) * 16 + 16]
            out[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = cell
    return out, Pd * 16

def saffron_border(game):
    """Saffron's 2x2 border block, drawn with its own installed pair, in 5-bit colour."""
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

def room_ref(key):
    p = dict(np.load(C.SRC / f'interiors/{key}.npz'))
    img = IN.decode(p).astype(np.int32) >> 3
    h = img.shape[0] // 16
    black = img[(h - 1) * 16:h * 16, 0:16]
    return padded(img, np.tile(black, (2, 2, 1)))

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    city_img = K.decode(game)['img'].astype(np.int32) >> 3
    bx, by = I.BORDER
    city = padded(city_img, city_img[by * 16:by * 16 + 32, bx * 16:bx * 16 + 32])
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
        anim = RE.animated(p, last)
        r = dict(frame=tag, mismatched_map_layer_pixels=int((d & ~anim).sum()), pixels_on_animated_water=int(anim.sum()),
                 camera_origin_px=[int(x0 - pad), int(y0 - pad)])
        if tag in BEHIND:                                   # the player's cell is at screen (112, 72)
            r['bg1_pixels_over_player_cell'] = int(RE.bg1(p)[72:88, 112:128].sum())
        if tag in IN_FRONT:                                 # head cell (112, 56) and feet cell (112, 72)
            r['bg1_pixels_over_player'] = int(RE.bg1(p)[56:88, 112:128].sum())
        results.append(r)
    return results

def main(game, out):
    out.mkdir(parents=True, exist_ok=True)
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
    behind = {f['frame']: f.get('bg1_pixels_over_player_cell') for f in frames if 'bg1_pixels_over_player_cell' in f}
    front = {f['frame']: f['bg1_pixels_over_player'] for f in frames if 'bg1_pixels_over_player' in f}
    print(json.dumps(dict(rom_sha256=rom, frames=len(frames), frames_with_background_mismatch=len(bad), walk_behind_bg1=behind,
                          in_front_bg1_over_player=front)))
    for f in bad:
        print('  mismatch', f)
    # Keep only the captures and results: the harness binary, its source, the symbols,
    # the VRAM dumps and the save are rebuilt each run and never committed.
    for p in [out / 'runtime', out / 'runtime.c', out / 'symbols.txt', *out.glob('vram-*.bin'), *out.glob('*.sav')]:
        p.unlink(missing_ok=True)
    assert not bad and all(behind.values()) and not any(front.values()), (behind, front)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
