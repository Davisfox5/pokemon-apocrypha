"""Prior three-section draft, kept for reference; superseded by the element build (elements.py, pack.py,
install_elements.py). Its evidence lives in evidence/sections-draft/.

Headless mGBA checks for Blackthorn City: movement, section crossings, doors, signs, saves.

Each phase is a fresh emulator process:
    write  new game; walk the town, cross both section lines in both directions, jump a ledge
           and fail to climb it, bump buildings, cliffs and water, read three signs, enter and
           leave the Center (both floors) and the Mart, record camera views; ordinary flash save
    read   cold flash reload of that save
    menu   title screen -> Continue

Every capture also dumps VRAM, BG palettes and BG registers; the map layers (BG1-BG3) are rebuilt
from that dump and must match the decoded native city image pixel for pixel. That proves the
streamed city view draws each section's own native tiles, across section lines and in the camera
margin, and that another city (Cherrygrove) still draws through the ordinary renderer.

    python3 tools/gba/maps/blackthorn/runtime.py ENGINE_CHECKOUT OUT_DIR
"""
from __future__ import annotations
import hashlib, json, os, re, shlex, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from claude_routes.runtime import TEMPLATE          # noqa: E402

S1, S2, S3, CENTER, UPSTAIRS, MART = 43, 44, 45, 46, 47, 48
ROW0 = {S1: 0, S2: 24, S3: 44}
SAVE = (S3, 30, 6)

MAIN = r'''
int main(int argc,char**argv){
 if(argc!=5)return 2;
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"blackthorn-native-proof");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/blackthorn.sav",out);
 if(strcmp(argv[4],"write")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1792584000000LL;c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"read")){
  need(call("LoadGameSave",0)==1,"load-game-save");call("MapProof_Resume",0);frames(300,0);at(SAVE_MAP,SAVE_X,SAVE_Y,"cold-flash-reload");shot("cold-flash-reload");
 }else if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);shot("continue-menu");frames(1,A);frames(300,0);at(SAVE_MAP,SAVE_X,SAVE_Y,"ordinary-continue");shot("ordinary-continue");
 }else{
  call("MapProof_Boot",0);frames(240,0);
  {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
  BODY
  report();
  go(SAVE_MAP,SAVE_X,SAVE_Y);at(SAVE_MAP,SAVE_X,SAVE_Y,"save-in-town");shot("save-in-town");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''

# (action, args): view = go + shot; walk = step n; at = position check; sign = read a sign
STEPS = [
    # Town views and the shared buildings.
    ('view', S3, 30, 6, 'town-centre'), ('view', S3, 34, 5, 'center-approach'), ('view', S3, 27, 5, 'mart-approach'),
    ('view', S3, 20, 9, 'south-gate-trees'), ('view', S3, 23, 14, 'bridge'), ('view', S3, 45, 6, 'east-shore'),
    ('view', S3, 13, 2, 'west-town'), ('view', S2, 44, 17, 'east-house'), ('view', S2, 21, 14, 'west-house'),
    ('view', S2, 30, 12, 'central-rocks'), ('view', S2, 52, 10, 'east-path'), ('view', S2, 56, 2, 'ice-path-approach'),
    ('view', S1, 57, 18, 'ice-path-mouth'), ('view', S2, 28, 1, 'gym-forecourt'), ('view', S1, 22, 23, 'gym-lawn-west'),
    ('view', S1, 32, 5, 'dragons-den-mouth'), ('view', S3, 23, 19, 'south-edge-bridge'),
    # Section 3 -> 2 -> 3 across the row 43/44 line, then 2 -> 1 -> 2 across 23/24.
    ('go', S3, 22, 2), ('north', 1, 'cross-32-0'), ('at', S3, 22, 1), ('north', 1, 'cross-32-1'), ('at', S3, 22, 0),
    ('north', 1, 'cross-32-2'), ('at', S2, 22, 19), ('north', 1, 'cross-32-3'), ('at', S2, 22, 18),
    ('south', 1, 'cross-23-0'), ('at', S2, 22, 19), ('south', 1, 'cross-23-1'), ('at', S3, 22, 0), ('south', 1, 'cross-23-2'), ('at', S3, 22, 1),
    ('go', S2, 22, 2), ('north', 1, 'cross-21-0'), ('at', S2, 22, 1), ('north', 1, 'cross-21-1'), ('at', S2, 22, 0),
    ('north', 1, 'cross-21-2'), ('at', S1, 22, 23), ('south', 1, 'cross-12-0'), ('at', S2, 22, 0), ('south', 1, 'cross-12-1'), ('at', S2, 22, 1),
    # Ledges (HGSS jump-south cells), both directions.
    ('go', S2, 14, 12), ('south', 1, 'ledge-jump'), ('at', S2, 14, 14), ('north', 1, None), ('at', S2, 14, 14),
    ('go', S2, 20, 15), ('south', 1, None), ('at', S2, 20, 17), ('north', 1, None), ('at', S2, 20, 17),
    # Blocked: the shared Mart body, cliffs and the pond edge (no Surf).
    ('go', S3, 31, 5), ('north', 1, None), ('at', S3, 31, 5),
    ('go', S3, 24, 4), ('east', 1, None), ('at', S3, 24, 4),
    ('go', S3, 10, 2), ('west', 1, None), ('at', S3, 10, 2),
    ('go', S1, 22, 23), ('north', 1, None), ('at', S1, 22, 23),
    ('go', S1, 32, 5), ('north', 1, None), ('at', S1, 32, 5),
    ('go', S1, 57, 17), ('north', 1, None), ('at', S1, 57, 17),
    # Signs.
    ('sign', S2, 52, 18, 'city-sign'), ('sign', S2, 26, 1, 'gym-sign'), ('sign', S1, 31, 6, 'den-sign'),
    # Center: in, upstairs and back, out; Mart: in and out.
    ('go', S3, 34, 5), ('north', 1, None), ('wait', 400), ('map', CENTER, 'center-entry'), ('shot', 'center-interior'),
    ('go', CENTER, 2, 6), ('west', 1, None), ('wait', 400), ('map', UPSTAIRS, 'center-upstairs'), ('shot', 'center-upstairs'),
    ('west', 1, None), ('wait', 400), ('map', CENTER, 'center-stair-return'),
    ('go', CENTER, 7, 7), ('south', 2, None), ('wait', 400), ('at', S3, 34, 5), ('shot', 'center-exit'),
    ('go', S3, 27, 5), ('north', 1, None), ('wait', 400), ('map', MART, 'mart-entry'), ('shot', 'mart-interior'),
    ('go', MART, 3, 6), ('south', 2, None), ('wait', 400), ('at', S3, 27, 5), ('shot', 'mart-exit'),
    # Another city: its own renderer, then back to Blackthorn with a fresh view cache.
    ('view', 0, 50, 17, 'regression-cherrygrove'), ('view', S3, 30, 6, 'return-to-blackthorn'),
]

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
            out.append(f'observe("{s[2]}");need(state[2]=={s[1]},"{s[2]}");')
        elif k == 'shot':
            out.append(f'shot("{s[1]}");')
    return '\n  '.join(out)

def generate():
    prefix = TEMPLATE.split('int main(')[0].replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    defines = ('#define A 1\n#define B 2\n#define RIGHT 16\n#define LEFT 32\n#define UP 64\n#define DOWN 128\n'
               f'#define SAVE_MAP {SAVE[0]}\n#define SAVE_X {SAVE[1]}\n#define SAVE_Y {SAVE[2]}\n')
    prefix = prefix.replace('#undef main', '#undef main\n' + defines, 1)
    # Each capture also dumps VRAM, BG palettes, BG control and the scroll shadow
    # registers (HOFS/VOFS are write-only, so the game's sGpuRegBuffer is read).
    # The map layers BG1-BG3 are rebuilt from that dump offline: no sprites, no text.
    old = 'static void shot(const char*t){screenshot(out,t);}'
    assert old in prefix
    prefix = prefix.replace(old, r'''static void vram(const char*t){char p[2048];snprintf(p,sizeof(p),"%s/vram-%s.bin",out,t);FILE*f=fopen(p,"wb");
 for(unsigned a=0x06000000;a<0x06010000;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 for(unsigned a=0x05000000;a<0x05000200;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 unsigned short r[13];r[0]=c->busRead16(c,0x04000000);for(int i=0;i<4;i++)r[1+i]=c->busRead16(c,0x04000008+2*i);
 unsigned g=sym("sGpuRegBuffer");for(int i=0;i<8;i++)r[5+i]=c->busRead16(c,g+0x10+2*i);fwrite(r,2,13,f);fclose(f);}
static void shot(const char*t){screenshot(out,t);vram(t);char o[128];snprintf(o,sizeof(o),"shot:%s",t);observe(o);}''')
    report = ('static void report(void){unsigned o=c->busRead32(c,sym("gCityViewOverflows")),u=c->busRead32(c,sym("gCityViewUploads"));'
              'printf("{\\"city_view_overflows\\":%u,\\"city_view_uploads\\":%u}\\n",o,u);need(o==0,"city-view-overflow");}\n')
    return prefix + report + MAIN.replace('BODY', body())

def expected_city(game):
    """The decoded native city padded with the view's own camera-margin tables."""
    img = np.array(Image.open(ROOT / 'gba/art/blackthorn-city/evidence/sections-draft/native.png').convert('RGB')).astype(np.int32) >> 3
    d = game / 'data/city_views/blackthorn'
    t = {k: np.frombuffer((d / f'margin-{k}.bin').read_bytes(), np.uint8) for k in ('north', 'south', 'west', 'east')}
    rock = tuple(int(v) for v in re.search(r'\.rockX = (\d+), \.rockY = (\d+)', (game / 'src/data/city_views/blackthorn.h').read_text()).groups())
    H, W = img.shape[0] // 16, img.shape[1] // 16
    P = 16
    def cell(x, y):
        ix, iy = 0 <= x < W, 0 <= y < H
        if ix and iy: return x, y
        s = 255 if not ix and not iy else int(t['west'][y] if x < 0 else t['east'][y] if x >= W else t['north'][x] if y < 0 else t['south'][x])
        if s == 255: return rock[0] + (x & 1), rock[1] + (y & 1)
        return (s + (x & 1), y) if not ix else (x, s + (y & 1))
    out = np.zeros(((H + 2 * P) * 16, (W + 2 * P) * 16, 3), np.int32)
    for py in range(H + 2 * P):
        for px in range(W + 2 * P):
            x, y = cell(px - P, py - P)
            out[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
    return out, P * 16

def map_layers(dump):
    """Rebuild the visible BG1-BG3 (the map layers) from a VRAM / palette / register dump."""
    raw = dump.read_bytes()
    vram = np.frombuffer(raw[:0x10000], np.uint8)
    pal = np.frombuffer(raw[0x10000:0x10200], '<u2').astype(np.int32)
    regs = np.frombuffer(raw[0x10200:0x10200 + 26], '<u2').astype(np.int32)
    rgb = np.stack([pal & 31, (pal >> 5) & 31, (pal >> 10) & 31], -1).reshape(16, 16, 3)
    dispcnt, cnt, scroll = regs[0], regs[1:5], regs[5:13]
    out = np.broadcast_to(rgb[0, 0], (160, 240, 3)).copy()
    layers = []
    for bg in (1, 2, 3):
        if not dispcnt & (0x100 << bg):
            continue
        c = cnt[bg]
        assert (c >> 14) == 0 and not c & 0x80, 'expected 256x256 4bpp text BGs'
        layers.append(((c & 3), bg, ((c >> 2) & 3) * 0x4000, ((c >> 8) & 31) * 0x800, scroll[2 * bg] & 511, scroll[2 * bg + 1] & 511))
    ys, xs = np.mgrid[0:160, 0:240]
    for prio, bg, cbase, sbase, hofs, vofs in sorted(layers, reverse=True):     # back to front
        X, Y = (xs + hofs) & 255, (ys + vofs) & 255
        entry = vram.view('<u2')[sbase // 2 + (Y // 8) * 32 + X // 8].astype(np.int32)
        tile, hf, vf, pb = entry & 1023, (entry >> 10) & 1, (entry >> 11) & 1, entry >> 12
        px = np.where(hf, 7 - X % 8, X % 8); py = np.where(vf, 7 - Y % 8, Y % 8)
        byte = vram[cbase + tile * 32 + py * 4 + px // 2]
        ix = np.where(px % 2, byte >> 4, byte & 15)
        m = ix > 0
        out[m] = rgb[pb[m], ix[m]]
    return out

def check_frames(out, game, phases):
    """Compare each overworld capture's rebuilt map layers with the padded native city."""
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    blackthorn = expected_city(game)
    # Cherrygrove, drawn by the ordinary renderer from its own native tiles.
    from tiles import Tileset
    cg = np.frombuffer((game / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), '<u2')
    cherry = (np.array(Tileset(game, 'cherrygrove', 'cherrygrove').map_image(cg.tolist(), 80).convert('RGB')).astype(np.int32) >> 3, 0)
    results = []
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        if any(t in tag for t in ('interior', 'upstairs', 'continue-menu')):
            continue
        city, pad = cherry if tag.startswith('regression-cherrygrove') else blackthorn
        shot = map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        # The camera keeps the player's cell at screen (112, 72): the origin follows
        # from the position logged with the capture, no search involved.
        o = positions[tag]
        if tag.startswith('regression-cherrygrove'):
            gx, gy = o['x'], o['y']
        else:
            gx, gy = o['x'], o['y'] + ROW0[o['map']]
        x0, y0 = gx * 16 - 112 + pad, gy * 16 - 72 + pad
        n = int((city[y0:y0 + 160, x0:x0 + 240] != shot).any(-1).sum())
        results.append(dict(frame=tag, mismatched_map_layer_pixels=n, camera_origin_px=[int(x0 - pad), int(y0 - pad)]))
    return results

def main(game, out):
    out.mkdir(parents=True, exist_ok=True)
    src = out / 'runtime.c'; src.write_text(generate())
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '-lmgba'))
    subprocess.run(['cc', '-O1', str(src), *flags, '-o', str(out / 'runtime')], check=True)
    raw = subprocess.check_output([os.environ.get('ARM_NM', 'arm-none-eabi-nm'), str(game / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'MapProof_Resume', 'gMapProofState', 'TrySavingData',
              'LoadGameSave', 'ArePlayerFieldControlsLocked', 'gMain', 'CB2_Overworld', 'gSaveBlock2Ptr', 'gCityViewOverflows',
              'gCityViewUploads', 'sGpuRegBuffer'}
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

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
