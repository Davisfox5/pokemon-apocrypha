"""Headless mGBA checks for Saffron City ten years on (KantoSaffronCity, v3).

Each phase is a fresh emulator process:
    write  new game; stand in front of the station, Silph, its lab, both Dojo doors, the
           League office, the Copycat's and Mr. Psychic's houses, the Center, the Mart and
           the fountain garden, and at the four gates; bump the station's front and door,
           Silph's lobby door, the Copycat's door and the north and west gates (solid until
           their interiors and routes exist); walk under the Magnet Train's deck; walk the length of Silph's back and stand behind its roof and its
           dome, the lab's roof, the station, the
           Dojo's west end, a grove tree, the Copycat's house, the Center and the
           Mart; read the ten signs; watch the Center's door slide open; enter and leave the
           Center (both floors) and the Mart; enter the Dojo by the Fighting door and leave
           by the Psychic mat, enter by the Psychic door and leave by the Fighting mat; enter
           and leave the lab; visit Cherrygrove and Olivine and come back; ordinary flash save
    read   cold flash reload of that save
    menu   title screen -> Continue

Every capture also dumps VRAM, BG palettes and BG registers. The map layers (BG1-BG3) are
rebuilt from that dump and must match the decoded native map pixel for pixel, in the city
and in the Dojo hall and the lab (Saffron plays no tileset animation; the regression towns'
animated sea is set aside as in olivine_elements/runtime_elements.py). Behind a roof, BG1
(the layer above the player) must cover the player's cell; in front of a building it must
leave the player's two cells clear. The door frames must show FireRed's sliding door as
install.py indexes it into the door's banks (graphics/door_anims/kanto_saffron_sliding.png).

    python3 tools/gba/maps/saffron/runtime.py ENGINE_CHECKOUT OUT_DIR
"""
from __future__ import annotations
import hashlib, json, os, shlex, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent / 'olivine_elements'), str(HERE.parent)]
import runtime_elements as RE                       # noqa: E402  (VRAM decoding, the harness template)
import check as K                                   # noqa: E402

# MapProof indices (sMapProofMaps); Saffron's maps are gMapGroup_Kanto (group 81) 0-5
CITY, CENTER, UPSTAIRS, MART, DOJO, LAB = 54, 55, 56, 57, 58, 59
KANTO_GROUP, CHERRYGROVE_GROUP = 81, 80
OLIVINE = 50
SAVE = (CITY, 24, 40)
DOOR_SHOTS = 15

STEPS = [
    # In front of every building: BG1 clear over the player.
    ('view', CITY, 25, 15, 'station-front'), ('view', CITY, 33, 31, 'silph-front'), ('view', CITY, 42, 31, 'lab-front'),
    ('view', CITY, 40, 13, 'fighting-door-front'), ('view', CITY, 45, 13, 'psychic-door-front'),
    ('view', CITY, 47, 22, 'league-office-front'), ('view', CITY, 19, 22, 'copycat-house-front'),
    ('view', CITY, 43, 39, 'mr-psychic-front'), ('view', CITY, 24, 39, 'center-approach'),
    ('view', CITY, 40, 22, 'mart-approach'), ('view', CITY, 44, 15, 'dojo-plaza'), ('view', CITY, 34, 43, 'fountain-garden'),
    ('view', CITY, 34, 6, 'north-gate'), ('view', CITY, 34, 45, 'south-gate'),
    ('view', CITY, 9, 27, 'west-gate'), ('view', CITY, 57, 27, 'east-gate'),
    # Walk behind: the top layer covers the player's cell, what is below stays solid.
    ('go', CITY, 30, 15), ('shot', 'behind-silph-roof'), ('south', 1, None), ('at', CITY, 30, 16),
    ('shot', 'behind-silph-roof-deep'), ('south', 1, None), ('at', CITY, 30, 16),
    ('go', CITY, 33, 16), ('shot', 'behind-silph-dome'), ('south', 1, None), ('at', CITY, 33, 16),
    ('go', CITY, 28, 16), ('east', 10, None), ('at', CITY, 38, 16),            # the whole back of Silph on foot, behind its roof
    ('go', CITY, 15, 12), ('shot', 'under-magnet-train'),
    ('go', CITY, 16, 15), ('north', 5, None), ('at', CITY, 16, 10),             # under the Magnet Train's deck, end to end
    ('go', CITY, 40, 23), ('shot', 'behind-lab-roof'), ('south', 1, None), ('at', CITY, 40, 23),
    ('go', CITY, 28, 13), ('shot', 'behind-station'), ('west', 1, None), ('at', CITY, 28, 13),
    ('go', CITY, 36, 6), ('shot', 'behind-dojo-west-end'), ('east', 1, None), ('at', CITY, 36, 6),
    ('go', CITY, 15, 40), ('shot', 'behind-grove-tree'), ('south', 1, None), ('at', CITY, 15, 40),
    ('go', CITY, 19, 17), ('shot', 'behind-copycat-house'), ('south', 1, None), ('at', CITY, 19, 17),
    ('go', CITY, 24, 34), ('shot', 'behind-center'), ('south', 1, None), ('at', CITY, 24, 34),
    ('go', CITY, 40, 18), ('shot', 'behind-mart'), ('south', 1, None), ('at', CITY, 40, 18),
    # Solid: the station's front and door, Silph's lobby door, the Copycat's door, the
    # north and west gates.
    ('go', CITY, 21, 14), ('north', 1, None), ('at', CITY, 21, 14),
    ('go', CITY, 25, 15), ('north', 1, 'station-door-solid'), ('at', CITY, 25, 15),
    ('go', CITY, 33, 31), ('north', 1, 'silph-door-solid'), ('at', CITY, 33, 31),
    ('go', CITY, 19, 22), ('north', 1, None), ('at', CITY, 19, 22),
    ('go', CITY, 34, 6), ('north', 1, None), ('at', CITY, 34, 6),
    ('go', CITY, 9, 27), ('west', 1, None), ('at', CITY, 9, 27),
    # The ten signs.
    ('sign', CITY, 30, 12, 'sign-city'), ('sign', CITY, 25, 14, 'sign-station'), ('sign', CITY, 42, 14, 'sign-fighting-dojo'),
    ('sign', CITY, 50, 14, 'sign-psychic-dojo'), ('sign', CITY, 49, 22, 'sign-league-office'), ('sign', CITY, 29, 31, 'sign-silph'),
    ('sign', CITY, 13, 25, 'sign-silph-magnet-train'), ('sign', CITY, 18, 30, 'sign-tips-great-ball'),
    ('sign', CITY, 54, 25, 'sign-tips-full-heal'), ('sign', CITY, 40, 38, 'sign-mr-psychic'),
    # The Center's door slides open; in, upstairs and back, out. Mart: in and out.
    ('door', CITY, 24, 39, 'center-door'), ('wait', 400), ('map', CENTER, 'center-entry'), ('shot', 'center-interior'),
    ('go', CENTER, 2, 6), ('west', 1, None), ('wait', 400), ('map', UPSTAIRS, 'center-upstairs'), ('shot', 'center-upstairs'),
    ('west', 1, None), ('wait', 400), ('map', CENTER, 'center-stair-return'),
    ('go', CENTER, 7, 7), ('south', 2, None), ('wait', 400), ('at', CITY, 24, 39), ('shot', 'center-exit'),
    ('go', CITY, 40, 22), ('north', 1, None), ('wait', 400), ('map', MART, 'mart-entry'), ('shot', 'mart-interior'),
    ('go', MART, 3, 6), ('south', 2, None), ('wait', 400), ('at', CITY, 40, 22), ('shot', 'mart-exit'),
    # The Dojo: one hall, in by either door, out by the other school's mat.
    ('go', CITY, 40, 13), ('north', 1, None), ('wait', 400), ('at', DOJO, 6, 14), ('shot', 'dojo-hall-fighting'),
    ('go', DOJO, 18, 13), ('south', 2, None), ('wait', 400), ('at', CITY, 45, 13), ('shot', 'dojo-out-psychic'),
    ('north', 1, None), ('wait', 400), ('at', DOJO, 18, 14), ('shot', 'dojo-hall-psychic'),
    ('go', DOJO, 6, 13), ('south', 2, None), ('wait', 400), ('at', CITY, 40, 13), ('shot', 'dojo-out-fighting'),
    # Silph's lab: in and out.
    ('go', CITY, 42, 31), ('north', 1, None), ('wait', 400), ('at', LAB, 7, 9), ('shot', 'lab-hall'),
    ('go', LAB, 7, 8), ('south', 2, None), ('wait', 400), ('at', CITY, 42, 31), ('shot', 'lab-exit'),
    # Other towns through the ordinary renderer, then back.
    ('view', 0, 50, 17, 'regression-cherrygrove'), ('view', OLIVINE, 16, 35, 'regression-olivine'),
    ('view', CITY, 24, 40, 'return-to-saffron'),
]
WALK_BEHIND = {'under-magnet-train': (15, 12), 'behind-silph-roof': (30, 15), 'behind-silph-roof-deep': (30, 16), 'behind-silph-dome': (33, 16), 'behind-lab-roof': (40, 23), 'behind-station': (28, 13), 'behind-dojo-west-end': (36, 6),
               'behind-grove-tree': (15, 40), 'behind-copycat-house': (19, 17), 'behind-center': (24, 34), 'behind-mart': (40, 18)}
IN_FRONT = ('station-front', 'silph-front', 'lab-front', 'fighting-door-front', 'psychic-door-front', 'league-office-front',
            'copycat-house-front', 'mr-psychic-front', 'center-approach', 'center-exit', 'mart-approach', 'mart-exit',
            'fountain-garden', 'dojo-out-psychic', 'dojo-out-fighting', 'lab-exit')
ROOM_TAGS = {'dojo-hall': 'dojo', 'lab-hall': 'lab'}

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
        elif k == 'door':   # walk up to the door (facing it), press into it, capture every two frames
            out.append(f'go({s[1]},{s[2]},{s[3]}+1);step(UP,1);frames(2,UP);' +
                       ''.join(f'frames(2,0);shot("{s[4]}-{i:02}");' for i in range(DOOR_SHOTS)))
        elif k == 'wait':
            out.append(f'frames({s[1]},0);')
        elif k == 'map':
            out.append(f'observe("{s[2]}");need(state[1]=={KANTO_GROUP}&&state[2]=={s[1] - CITY},"{s[2]}");')
        elif k == 'shot':
            out.append(f'shot("{s[1]}");')
    return '\n  '.join(out)

def generate():
    prefix = RE.TEMPLATE.split('int main(')[0].replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    defines = ('#define A 1\n#define B 2\n#define RIGHT 16\n#define LEFT 32\n#define UP 64\n#define DOWN 128\n'
               f'#define SAVE_MAP {SAVE[0]}\n#define SAVE_X {SAVE[1]}\n#define SAVE_Y {SAVE[2]}\n')
    prefix = prefix.replace('#undef main', '#undef main\n' + defines, 1)
    # Positions: a MapProof index names a Cherrygrove-group map (its own map number) or,
    # from CITY on, a Kanto-group one.
    old = 'static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);need(state[1]==80&&state[2]==map&&state[3]==x&&state[4]==y,tag);}'
    assert old in prefix
    prefix = prefix.replace(old, 'static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);'
                            f'unsigned grp=map>={CITY}?{KANTO_GROUP}:{CHERRYGROVE_GROUP},num=map>={CITY}?map-{CITY}:map;'
                            'need(state[1]==grp&&state[2]==num&&state[3]==x&&state[4]==y,tag);}')
    old = 'static void shot(const char*t){screenshot(out,t);}'
    assert old in prefix
    prefix = prefix.replace(old, r'''static void vram(const char*t){char p[2048];snprintf(p,sizeof(p),"%s/vram-%s.bin",out,t);FILE*f=fopen(p,"wb");
 for(unsigned a=0x06000000;a<0x06010000;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 for(unsigned a=0x05000000;a<0x05000200;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 unsigned short r[13];r[0]=c->busRead16(c,0x04000000);for(int i=0;i<4;i++)r[1+i]=c->busRead16(c,0x04000008+2*i);
 unsigned g=sym("sGpuRegBuffer");for(int i=0;i<8;i++)r[5+i]=c->busRead16(c,g+0x10+2*i);fwrite(r,2,13,f);fclose(f);}
static void shot(const char*t){screenshot(out,t);vram(t);char o[128];snprintf(o,sizeof(o),"shot:%s",t);observe(o);}''')
    main = RE.MAIN.replace('olivine-native-proof', 'saffron-native-proof').replace('olivine.sav', 'saffron.sav')
    return prefix + main.replace('BODY', body())

def padded(img, border):
    """A decoded native map with its 2x2 border block beyond the edges (the camera sees
    it), the block's quarter chosen by the cell's parity as GetBorderBlockAt does."""
    H, W = img.shape[0] // 16, img.shape[1] // 16
    P = 16
    out = np.zeros(((H + 2 * P) * 16, (W + 2 * P) * 16, 3), np.int32)
    for py in range(H + 2 * P):
        for px in range(W + 2 * P):
            x, y = px - P, py - P
            if 0 <= x < W and 0 <= y < H:
                cell = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            else:
                cell = border[(y & 1) * 16:(y & 1) * 16 + 16, (x & 1) * 16:(x & 1) * 16 + 16]
            out[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = cell
    return out, P * 16

def door_frames(game):
    """FireRed's sliding door as install.py indexes it: its 16x16 frames, stacked, as palette indices."""
    return np.array(Image.open(game / 'graphics/door_anims/kanto_saffron_sliding.png'))

def room_ref(key):
    """A room as interiors.py decodes it, its black border cell beyond its edges, in 5-bit colour."""
    import interiors as I
    p = dict(np.load(ROOT / f'gba/art/saffron-kanto/source/interiors/{key}.npz'))
    img = I.decode(p).astype(np.int32) >> 3
    h = img.shape[0] // 16
    black = img[(h - 1) * 16:h * 16, 0:16]
    return padded(img, np.tile(black, (2, 2, 1)))

def door_drawn(dump, frames):
    """Which sliding-door frame the map draws (from the door tiles at the top of VRAM), or None."""
    raw = dump.read_bytes()
    vram = np.frombuffer(raw[:0x10000], np.uint8)
    regs = np.frombuffer(raw[0x10200:0x10200 + 26], '<u2').astype(np.int32)
    start = 1024 - 8                                           # DOOR_TILE_START_SIZE1
    ys, xs = np.mgrid[0:160, 0:240]
    used = False
    for bg in (1, 2, 3):
        c, hofs, vofs = regs[1 + bg], regs[5 + 2 * bg] & 511, regs[5 + 2 * bg + 1] & 511
        X, Y = (xs + hofs) & 255, (ys + vofs) & 255
        t = vram.view('<u2')[((c >> 8) & 31) * 0x400 + (Y // 8) * 32 + X // 8].astype(np.int32) & 1023
        used |= bool(((t >= start) & (t < start + 4)).any())
    if not used:
        return None
    def tile(i):
        b = vram[i * 32:(i + 1) * 32]
        return np.stack([b & 15, b >> 4], -1).reshape(8, 8)
    vt = [tile(start + i) for i in range(4)]
    for f in range(frames.shape[0] // 16):
        fr = frames[f * 16:(f + 1) * 16]
        want = [fr[:8, :8], fr[:8, 8:], fr[8:, :8], fr[8:, 8:]]
        if all((a == b).all() for a, b in zip(vt, want)):
            return f
    return 'unknown'

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    city = (K.decode(game)['img'].astype(np.int32) >> 3)
    city = padded(city, K.border_image(game).astype(np.int32) >> 3)
    olivine = RE.padded(np.array(Image.open(ROOT / 'gba/art/olivine-elements/evidence/elements/native-C.png').convert('RGB')).astype(np.int32) >> 3,
                        (40, 58))
    from tiles import Tileset
    cg = np.frombuffer((game / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), '<u2')
    cherry = (np.array(Tileset(game, 'cherrygrove', 'cherrygrove').map_image(cg.tolist(), 80).convert('RGB')).astype(np.int32) >> 3, 0)
    frames = door_frames(game)
    results, door, rooms = [], {}, {}
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        if tag.startswith('center-door-'):
            door[tag] = door_drawn(p, frames)
            continue
        if any(t in tag for t in ('interior', 'upstairs', 'continue-menu')):
            continue
        room = next((k for t, k in ROOM_TAGS.items() if tag.startswith(t)), None)
        ref, pad = (rooms.setdefault(room, room_ref(room)) if room else cherry if tag.startswith('regression-cherrygrove')
                    else olivine if tag.startswith('regression-olivine') else city)
        shot = RE.map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        o = positions[tag]
        x0, y0 = o['x'] * 16 - 112 + pad, o['y'] * 16 - 72 + pad
        d = (ref[y0:y0 + 160, x0:x0 + 240] != shot).any(-1)
        last = 92 if tag.startswith('regression-cherrygrove') else 16 if tag.startswith('regression-olivine') else 0
        anim = RE.animated(p, last)
        r = dict(frame=tag, mismatched_map_layer_pixels=int((d & ~anim).sum()), pixels_on_animated_water=int(anim.sum()),
                 camera_origin_px=[int(x0 - pad), int(y0 - pad)])
        if tag in WALK_BEHIND:                              # the player's cell is at screen (112, 72)
            r['bg1_pixels_over_player_cell'] = int(RE.bg1(p)[72:88, 112:128].sum())
        if tag in IN_FRONT:                                 # head cell (112, 56) and feet cell (112, 72)
            r['bg1_pixels_over_player'] = int(RE.bg1(p)[56:88, 112:128].sum())
        results.append(r)
    return results, door

def main(game, out):
    out.mkdir(parents=True, exist_ok=True)
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
    frames, door = check_frames(out, game, phases)
    rom = hashlib.sha256((game / 'pokeemerald.gba').read_bytes()).hexdigest()
    door_seen = sorted({f for f in door.values() if f is not None}, key=str)
    (out / 'results.json').write_text(json.dumps(dict(rom_sha256=rom, phases=phases, background_parity=frames,
                                                      center_door_frames=door), indent=2) + '\n')
    bad = [f for f in frames if f['mismatched_map_layer_pixels']]
    behind = {f['frame']: f.get('bg1_pixels_over_player_cell') for f in frames if 'bg1_pixels_over_player_cell' in f}
    front = {f['frame']: f['bg1_pixels_over_player'] for f in frames if 'bg1_pixels_over_player' in f}
    print(json.dumps(dict(rom_sha256=rom, frames=len(frames), frames_with_background_mismatch=len(bad), walk_behind_bg1=behind,
                          in_front_bg1_over_player=front, sliding_door_frames_seen=door_seen)))
    for f in bad:
        print('  mismatch', f)
    # Keep only the captures and results: the harness binary, its source, the symbols,
    # the VRAM dumps and the save are rebuilt each run and never committed.
    for p in [out / 'runtime', out / 'runtime.c', out / 'symbols.txt', *out.glob('vram-*.bin'), *out.glob('*.sav')]:
        p.unlink(missing_ok=True)
    assert not bad and all(behind.values()) and not any(front.values()), (behind, front)
    assert any(isinstance(f, int) and f > 0 for f in door_seen) and 'unknown' not in door_seen, door

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
