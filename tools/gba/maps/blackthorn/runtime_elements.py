"""Headless mGBA checks for the element-built Blackthorn City (one native map).

Each phase is a fresh emulator process:
    write  new game; walk the town, jump two ledges and fail to climb them, bump the
           shared Mart, cliffs, water and the gate-post bases, stand behind a gate post, a
           house and the standing stone, read three signs, enter and leave the Center
           (both floors) and the Mart, visit Cherrygrove and come back; ordinary flash save
    read   cold flash reload of that save
    menu   title screen -> Continue

Every capture also dumps VRAM, BG palettes and BG registers. The map layers (BG1-BG3) are
rebuilt from that dump and must match the decoded native map pixel for pixel; for the
walk-behind captures, BG1 (the layer drawn above the player) must hold the object's
pixels over the player's own cell.

    python3 tools/gba/maps/blackthorn/runtime_elements.py ENGINE_CHECKOUT OUT_DIR [STYLE]   # STYLE C by default
"""
from __future__ import annotations
import hashlib, json, os, shlex, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from claude_routes.runtime import TEMPLATE          # noqa: E402
import runtime as R                                 # map_layers()  # noqa: E402

CITY, CENTER, UPSTAIRS, MART = 43, 44, 45, 46
STYLE = sys.argv[3] if len(sys.argv) > 3 else 'C'
SAVE = (CITY, 30, 50)

STEPS = [
    ('view', CITY, 30, 50, 'town-centre'), ('view', CITY, 34, 49, 'center-approach'), ('view', CITY, 27, 49, 'mart-approach'),
    ('view', CITY, 23, 52, 'south-gate'), ('view', CITY, 23, 58, 'bridge'), ('view', CITY, 45, 50, 'east-shore'),
    ('view', CITY, 13, 46, 'west-town'), ('view', CITY, 44, 41, 'east-house'), ('view', CITY, 21, 38, 'west-house'),
    ('view', CITY, 30, 36, 'central-rocks'), ('view', CITY, 52, 34, 'east-path'), ('view', CITY, 56, 26, 'ice-path-approach'),
    ('view', CITY, 57, 18, 'ice-path-mouth'), ('view', CITY, 28, 25, 'gym-forecourt'), ('view', CITY, 22, 24, 'gym-lawn-west'),
    ('view', CITY, 32, 5, 'dragons-den-mouth'), ('view', CITY, 23, 63, 'south-edge-bridge'), ('view', CITY, 3, 3, 'north-west-corner'),
    # Walk behind: the top layer covers the player's cell, the base stays solid.
    ('go', CITY, 21, 51), ('shot', 'behind-gate-post'), ('south', 1, None), ('at', CITY, 21, 51),
    ('go', CITY, 25, 51), ('shot', 'behind-gate-post-east'), ('south', 1, None), ('at', CITY, 25, 51),
    ('go', CITY, 20, 33), ('shot', 'behind-west-house'), ('south', 1, None), ('at', CITY, 20, 33),
    ('go', CITY, 23, 34), ('shot', 'behind-standing-stone'), ('south', 1, None), ('at', CITY, 23, 34),
    # Ledges (HGSS jump-south cells), both directions.
    ('go', CITY, 14, 36), ('south', 1, 'ledge-jump'), ('at', CITY, 14, 38), ('north', 1, None), ('at', CITY, 14, 38),
    ('go', CITY, 20, 39), ('south', 1, None), ('at', CITY, 20, 41), ('north', 1, None), ('at', CITY, 20, 41),
    # Blocked: the shared Mart body, cliffs, the pond edge (no Surf) and both unbuilt caves.
    ('go', CITY, 31, 49), ('north', 1, None), ('at', CITY, 31, 49),
    ('go', CITY, 24, 48), ('east', 1, None), ('at', CITY, 24, 48),
    ('go', CITY, 10, 46), ('west', 1, None), ('at', CITY, 10, 46),
    ('go', CITY, 22, 23), ('north', 1, None), ('at', CITY, 22, 23),
    ('go', CITY, 32, 5), ('north', 1, None), ('at', CITY, 32, 5),
    ('go', CITY, 57, 17), ('north', 1, None), ('at', CITY, 57, 17),
    # Signs.
    ('sign', CITY, 52, 42, 'city-sign'), ('sign', CITY, 26, 25, 'gym-sign'), ('sign', CITY, 31, 6, 'den-sign'),
    # Center: in, upstairs and back, out; Mart: in and out.
    ('go', CITY, 34, 49), ('north', 1, None), ('wait', 400), ('map', CENTER, 'center-entry'), ('shot', 'center-interior'),
    ('go', CENTER, 2, 6), ('west', 1, None), ('wait', 400), ('map', UPSTAIRS, 'center-upstairs'), ('shot', 'center-upstairs'),
    ('west', 1, None), ('wait', 400), ('map', CENTER, 'center-stair-return'),
    ('go', CENTER, 7, 7), ('south', 2, None), ('wait', 400), ('at', CITY, 34, 49), ('shot', 'center-exit'),
    ('go', CITY, 27, 49), ('north', 1, None), ('wait', 400), ('map', MART, 'mart-entry'), ('shot', 'mart-interior'),
    ('go', MART, 3, 6), ('south', 2, None), ('wait', 400), ('at', CITY, 27, 49), ('shot', 'mart-exit'),
    ('view', 0, 50, 17, 'regression-cherrygrove'), ('view', CITY, 30, 50, 'return-to-blackthorn'),
]
WALK_BEHIND = {'behind-gate-post': (21, 51), 'behind-gate-post-east': (25, 51), 'behind-west-house': (20, 33),
               'behind-standing-stone': (23, 34)}

def generate():
    prefix = TEMPLATE.split('int main(')[0].replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    defines = ('#define A 1\n#define B 2\n#define RIGHT 16\n#define LEFT 32\n#define UP 64\n#define DOWN 128\n'
               f'#define SAVE_MAP {SAVE[0]}\n#define SAVE_X {SAVE[1]}\n#define SAVE_Y {SAVE[2]}\n')
    prefix = prefix.replace('#undef main', '#undef main\n' + defines, 1)
    old = 'static void shot(const char*t){screenshot(out,t);}'
    assert old in prefix
    prefix = prefix.replace(old, r'''static void vram(const char*t){char p[2048];snprintf(p,sizeof(p),"%s/vram-%s.bin",out,t);FILE*f=fopen(p,"wb");
 for(unsigned a=0x06000000;a<0x06010000;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 for(unsigned a=0x05000000;a<0x05000200;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 unsigned short r[13];r[0]=c->busRead16(c,0x04000000);for(int i=0;i<4;i++)r[1+i]=c->busRead16(c,0x04000008+2*i);
 unsigned g=sym("sGpuRegBuffer");for(int i=0;i<8;i++)r[5+i]=c->busRead16(c,g+0x10+2*i);fwrite(r,2,13,f);fclose(f);}
static void shot(const char*t){screenshot(out,t);vram(t);char o[128];snprintf(o,sizeof(o),"shot:%s",t);observe(o);}''')
    main = R.MAIN.replace('  report();\n', '')
    R.STEPS[:] = STEPS
    return prefix + main.replace('BODY', R.body())

def expected(game):
    """The decoded native map with its 2x2 border block beyond the edges (the camera sees it)."""
    img = np.array(Image.open(ROOT / f'gba/art/blackthorn-city/evidence/elements/native-{STYLE}.png').convert('RGB')).astype(np.int32) >> 3
    H, W = img.shape[0] // 16, img.shape[1] // 16
    P = 16
    out = np.zeros(((H + 2 * P) * 16, (W + 2 * P) * 16, 3), np.int32)
    for py in range(H + 2 * P):
        for px in range(W + 2 * P):
            x, y = px - P, py - P
            if not (0 <= x < W and 0 <= y < H):
                x, y = x & 1, y & 1                         # border.bin is the plateau's own top-left 2x2
            out[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
    return out, P * 16

def bg1(dump):
    """BG1 alone (the layer above sprites) as a coverage mask."""
    raw = dump.read_bytes()
    vram = np.frombuffer(raw[:0x10000], np.uint8)
    regs = np.frombuffer(raw[0x10200:0x10200 + 26], '<u2').astype(np.int32)
    c, hofs, vofs = regs[2], regs[5 + 2] & 511, regs[5 + 3] & 511
    cbase, sbase = ((c >> 2) & 3) * 0x4000, ((c >> 8) & 31) * 0x800
    ys, xs = np.mgrid[0:160, 0:240]
    X, Y = (xs + hofs) & 255, (ys + vofs) & 255
    e = vram.view('<u2')[sbase // 2 + (Y // 8) * 32 + X // 8].astype(np.int32)
    tile, hf, vf = e & 1023, (e >> 10) & 1, (e >> 11) & 1
    px = np.where(hf, 7 - X % 8, X % 8); py = np.where(vf, 7 - Y % 8, Y % 8)
    byte = vram[cbase + tile * 32 + py * 4 + px // 2]
    return np.where(px % 2, byte >> 4, byte & 15) > 0

def animated(dump):
    """Pixels any map layer draws from CherrygrovePrimary's animated sea tiles (1-92)."""
    raw = dump.read_bytes()
    vram = np.frombuffer(raw[:0x10000], np.uint8)
    regs = np.frombuffer(raw[0x10200:0x10200 + 26], '<u2').astype(np.int32)
    ys, xs = np.mgrid[0:160, 0:240]
    m = np.zeros((160, 240), bool)
    for bg in (1, 2, 3):
        c, hofs, vofs = regs[1 + bg], regs[5 + 2 * bg] & 511, regs[5 + 2 * bg + 1] & 511
        X, Y = (xs + hofs) & 255, (ys + vofs) & 255
        t = vram.view('<u2')[((c >> 8) & 31) * 0x400 + (Y // 8) * 32 + X // 8].astype(np.int32) & 1023
        m |= (t >= 1) & (t <= 92)
    return m

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    city = expected(game)
    from tiles import Tileset
    cg = np.frombuffer((game / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), '<u2')
    cherry = (np.array(Tileset(game, 'cherrygrove', 'cherrygrove').map_image(cg.tolist(), 80).convert('RGB')).astype(np.int32) >> 3, 0)
    results = []
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        if any(t in tag for t in ('interior', 'upstairs', 'continue-menu')):
            continue
        ref, pad = cherry if tag.startswith('regression-cherrygrove') else city
        shot = R.map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        o = positions[tag]
        x0, y0 = o['x'] * 16 - 112 + pad, o['y'] * 16 - 72 + pad
        d = (ref[y0:y0 + 160, x0:x0 + 240] != shot).any(-1)
        anim = animated(p)                                   # CherrygrovePrimary's sea tiles 1-92 animate
        r = dict(frame=tag, mismatched_map_layer_pixels=int((d & ~anim).sum()),
                 pixels_on_animated_water=int(anim.sum()), animated_water_pixels_differing_from_frame_0=int((d & anim).sum()),
                 camera_origin_px=[int(x0 - pad), int(y0 - pad)])
        if tag in WALK_BEHIND:                              # the player's cell is at screen (112, 72)
            cover = bg1(p)[72:88, 112:128]
            r['bg1_pixels_over_player_cell'] = int(cover.sum())
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
    print(json.dumps(dict(rom_sha256=rom, frames=len(frames), frames_with_background_mismatch=len(bad), walk_behind_bg1=behind)))
    for f in bad:
        print('  mismatch', f)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
