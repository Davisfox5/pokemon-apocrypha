"""Headless mGBA checks for Saffron City ten years on (v2, HGSS's plan) and its new interiors.

Each phase is a fresh emulator process:
    write  new game; stand in front of the station, Silph, the lab wing, both Dojo doors,
           the Copycat's and Mr. Psychic's houses, the Center, the Mart and the north gate;
           bump the station's, Silph's, the houses' and the gates' doors and the city's
           exits (solid until their interiors and routes exist) and the east gate's corner;
           stand behind the lab wing's roof, the Mart, a Dojo sign, a street lamp, the city
           sign, a Silph board and the east gate; read the six signs; enter and leave the
           Center (both floors) and the Mart; enter the Dojo by the Fighting door, walk
           across the one hall and leave by the Psychic door, then in by the Psychic door
           and out again; enter the lab by both door cells and leave; visit Cherrygrove and
           Olivine and come back; ordinary flash save
    read   cold flash reload of that save
    menu   title screen -> Continue

Every capture also dumps VRAM, BG palettes and BG registers. The map layers (BG1-BG3) are
rebuilt from that dump and must match the decoded native map pixel for pixel, the Dojo's
and the lab's frames included (Saffron and its rooms play no tileset animation; the
regression towns' animated sea is set aside as in olivine_elements/runtime_elements.py).
Behind a roof, BG1 (the layer above the player) must cover the player's cell; in front of
a building it must leave the player's two cells clear.

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
import interiors as I                               # noqa: E402
import install as N                                 # noqa: E402

# MapProof indices (sMapProofMaps); Saffron's maps are gMapGroup_Kanto (group 81) 0-5
CITY, CENTER, UPSTAIRS, MART, DOJO, LAB = 54, 55, 56, 57, 58, 59
KANTO_GROUP, CHERRYGROVE_GROUP = 81, 80
OLIVINE = 50
SAVE = (CITY, 14, 52)

STEPS = [
    # In front of every door: BG1 clear over the player.
    ('view', CITY, 10, 17, 'station-front'), ('view', CITY, 28, 38, 'silph-front'), ('view', CITY, 37, 42, 'lab-front'),
    ('view', CITY, 41, 13, 'fighting-dojo-front'), ('view', CITY, 48, 13, 'psychic-dojo-front'),
    ('view', CITY, 17, 27, 'copycat-house-front'), ('view', CITY, 43, 51, 'mr-psychic-front'),
    ('view', CITY, 14, 51, 'center-approach'), ('view', CITY, 38, 27, 'mart-approach'), ('view', CITY, 20, 6, 'north-gate-front'),
    ('view', CITY, 56, 48, 'east-gate'), ('view', CITY, 1, 48, 'west-exit'), ('view', CITY, 20, 60, 'south-exit'),
    ('view', CITY, 44, 14, 'dojo-plaza'), ('view', CITY, 30, 44, 'silph-plaza'),
    # Walk behind: the top layer covers the player's cell, the base below stays solid.
    ('go', CITY, 36, 34), ('shot', 'behind-lab-roof'), ('south', 1, None), ('at', CITY, 36, 34),
    ('go', CITY, 38, 21), ('shot', 'behind-mart'), ('south', 1, None), ('at', CITY, 38, 21),
    ('go', CITY, 43, 15), ('shot', 'behind-dojo-sign'), ('south', 1, None), ('at', CITY, 43, 15),
    ('go', CITY, 36, 13), ('shot', 'behind-lamp'), ('south', 1, None), ('at', CITY, 36, 13),
    ('go', CITY, 23, 17), ('shot', 'behind-city-sign'), ('south', 1, None), ('at', CITY, 23, 17),
    ('go', CITY, 26, 41), ('shot', 'behind-silph-board'), ('south', 1, None), ('at', CITY, 26, 41),
    ('go', CITY, 57, 47), ('shot', 'behind-east-gate'), ('south', 1, None), ('at', CITY, 57, 47),
    # Solid: the station's, Silph's, the houses' and the gates' doors, the city's exits, the
    # east gate's corner.
    ('go', CITY, 10, 17), ('north', 1, 'station-door-solid'), ('at', CITY, 10, 17),
    ('go', CITY, 28, 38), ('north', 1, None), ('at', CITY, 28, 38),
    ('go', CITY, 17, 27), ('north', 1, None), ('at', CITY, 17, 27),
    ('go', CITY, 43, 51), ('north', 1, None), ('at', CITY, 43, 51),
    ('go', CITY, 20, 6), ('north', 1, None), ('at', CITY, 20, 6),
    ('go', CITY, 56, 48), ('east', 1, None), ('at', CITY, 56, 48),
    ('go', CITY, 56, 50), ('east', 1, None), ('at', CITY, 56, 50),
    ('go', CITY, 1, 48), ('west', 1, None), ('at', CITY, 1, 48),
    ('go', CITY, 20, 60), ('south', 1, None), ('at', CITY, 20, 60),
    # The six signs.
] + [('sign', CITY, x, y, 'sign-' + label[:-4].lower()) for label, (x, y), _ in N.SIGNS] + [
    # Center: in, upstairs and back, out. Mart: in and out.
    ('go', CITY, 14, 51), ('north', 1, None), ('wait', 400), ('map', CENTER, 'center-entry'), ('shot', 'center-interior'),
    ('go', CENTER, 2, 6), ('west', 1, None), ('wait', 400), ('map', UPSTAIRS, 'center-upstairs'), ('shot', 'center-upstairs'),
    ('west', 1, None), ('wait', 400), ('map', CENTER, 'center-stair-return'),
    ('go', CENTER, 7, 7), ('south', 2, None), ('wait', 400), ('at', CITY, 14, 51), ('shot', 'center-exit'),
    ('go', CITY, 38, 27), ('north', 1, None), ('wait', 400), ('map', MART, 'mart-entry'), ('shot', 'mart-interior'),
    ('go', MART, 3, 6), ('south', 2, None), ('wait', 400), ('at', CITY, 38, 27), ('shot', 'mart-exit'),
    # The Dojo: in by the Fighting door, across the one hall on foot, out by the Psychic door.
    ('go', CITY, 41, 13), ('north', 1, None), ('wait', 400), ('map', DOJO, 'dojo-entry-fighting'), ('at', DOJO, 6, 14),
    ('shot', 'dojo-hall-fighting'), ('north', 3, None), ('east', 11, None), ('at', DOJO, 17, 11), ('shot', 'dojo-hall-psychic'),
    ('south', 4, None), ('wait', 400), ('at', CITY, 48, 13), ('shot', 'psychic-dojo-exit'),
    ('north', 1, None), ('wait', 400), ('map', DOJO, 'dojo-entry-psychic'), ('at', DOJO, 17, 14),
    ('south', 1, None), ('wait', 400), ('at', CITY, 48, 13),
    # The lab: in by each door cell, out again.
    ('go', CITY, 37, 42), ('north', 1, None), ('wait', 400), ('map', LAB, 'lab-entry-west'), ('at', LAB, 7, 9), ('shot', 'lab-interior'),
    ('north', 2, None), ('at', LAB, 7, 7), ('shot', 'lab-interior-walk'), ('south', 3, None), ('wait', 400), ('at', CITY, 37, 42),
    ('shot', 'lab-exit'),
    ('go', CITY, 38, 42), ('north', 1, None), ('wait', 400), ('map', LAB, 'lab-entry-east'), ('at', LAB, 7, 9),
    ('south', 1, None), ('wait', 400), ('at', CITY, 37, 42),
    # Other towns through the ordinary renderer, then back.
    ('view', 0, 50, 17, 'regression-cherrygrove'), ('view', OLIVINE, 16, 35, 'regression-olivine'),
    ('view', CITY, 14, 52, 'return-to-saffron'),
]
WALK_BEHIND = {'behind-lab-roof': (36, 34), 'behind-mart': (38, 21), 'behind-dojo-sign': (43, 15), 'behind-lamp': (36, 13),
               'behind-city-sign': (23, 17), 'behind-silph-board': (26, 41), 'behind-east-gate': (57, 47)}
IN_FRONT = ('station-front', 'silph-front', 'lab-front', 'fighting-dojo-front', 'psychic-dojo-front', 'copycat-house-front',
            'mr-psychic-front', 'center-approach', 'center-exit', 'mart-approach', 'mart-exit', 'north-gate-front',
            'psychic-dojo-exit', 'lab-exit')
ROOM_FRAMES = {'dojo-hall-': 'dojo', 'lab-interior': 'lab'}

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

def room_padded(img):
    """An interior's decode with its black border (every border cell is the black edge's
    metatile, the room's bottom-left cell) beyond the edges."""
    h, w = img.shape[0] // 16, img.shape[1] // 16
    P = 16
    black = img[(h - 1) * 16:h * 16, 0:16]
    out = np.tile(black, (h + 2 * P, w + 2 * P, 1)).astype(np.int32)
    out[P * 16:(P + h) * 16, P * 16:(P + w) * 16] = img
    return out, P * 16

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    city = np.array(Image.open(ROOT / 'gba/art/saffron-kanto/evidence/native.png').convert('RGB')).astype(np.int32) >> 3
    city = RE.padded(city, N.BORDER_TREE)
    rooms = {k: room_padded(I.decode(np.load(ROOT / f'gba/art/saffron-kanto/source/interiors/{k}.npz')).astype(np.int32) >> 3)
             for k in ('dojo', 'lab')}
    olivine = RE.padded(np.array(Image.open(ROOT / 'gba/art/olivine-elements/evidence/elements/native-C.png').convert('RGB')).astype(np.int32) >> 3,
                        (40, 58))
    from tiles import Tileset
    cg = np.frombuffer((game / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), '<u2')
    cherry = (np.array(Tileset(game, 'cherrygrove', 'cherrygrove').map_image(cg.tolist(), 80).convert('RGB')).astype(np.int32) >> 3, 0)
    results = []
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        room = next((v for k, v in ROOM_FRAMES.items() if tag.startswith(k)), None)
        if room is None and any(t in tag for t in ('center-interior', 'center-upstairs', 'mart-interior', 'continue-menu')):
            continue
        ref, pad = (rooms[room] if room else cherry if tag.startswith('regression-cherrygrove')
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
    return results

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
