"""Headless mGBA checks for the element-built Mahogany Town (one native map).

Each phase is a fresh emulator process:
    write  new game; views across the town, jump the south and the west ledge and fail to
           climb back, bump the Center, the unbuilt Gym, shop and house doors, the unbuilt
           Route 43 gate, a tree, a low wall and the mountain, stand behind the Center's roof
           row, the Gym's roof edge, the souvenir shop's roof and the antenna tree, stand in
           front of every building, read the two signs, enter and leave the Center (both
           floors), visit Cherrygrove and come back; ordinary flash save
    read   cold flash reload of that save
    menu   title screen -> Continue

Every capture also dumps VRAM, BG palettes and BG registers. The map layers (BG1-BG3) are
rebuilt from that dump and must match the decoded native map pixel for pixel; for the
walk-behind captures, BG1 (the layer drawn above the player) must hold the object's
pixels over the player's own cell, and in front of a building BG1 must leave the player's
two cells clear.

    python3 tools/gba/maps/mahogany/runtime_elements.py ENGINE_CHECKOUT OUT_DIR [STYLE]   # STYLE C by default
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

CITY, CENTER, UPSTAIRS = 43, 44, 45      # gMapGroup_Cherrygrove ids (install_elements prints them)
STYLE = sys.argv[3] if len(sys.argv) > 3 else 'C'
SAVE = (CITY, 22, 25)
BORDER = (0, 0)                                     # install_elements.BORDER

MAIN = r'''
int main(int argc,char**argv){
 if(argc!=5)return 2;
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"mahogany-native-proof");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/mahogany.sav",out);
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
  go(SAVE_MAP,SAVE_X,SAVE_Y);at(SAVE_MAP,SAVE_X,SAVE_Y,"save-in-town");shot("save-in-town");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''

# (action, args): view = go + shot; north/south/east/west = step n (+ shot); at = position check; sign = read a sign
STEPS = [
    ('view', CITY, 16, 16, 'town-centre'), ('view', CITY, 22, 24, 'center-approach'), ('view', CITY, 11, 24, 'gym-front'),
    ('view', CITY, 16, 15, 'shop-front'), ('view', CITY, 25, 15, 'east-house-front'), ('view', CITY, 12, 6, 'gate-front'),
    ('view', CITY, 3, 11, 'west-lawn'), ('view', CITY, 17, 9, 'north-road'), ('view', CITY, 30, 16, 'east-road'),
    ('view', CITY, 15, 26, 'south-road'), ('view', CITY, 5, 23, 'gym-lawn-west'), ('view', CITY, 18, 23, 'center-lawn'),
    ('view', CITY, 0, 13, 'west-edge'),
    # Walk behind: the top layer covers the player's cell, the base stays solid.
    ('go', CITY, 22, 19), ('shot', 'behind-center'), ('south', 1, None), ('at', CITY, 22, 19),
    ('go', CITY, 10, 18), ('shot', 'behind-gym-roof'), ('south', 1, None), ('at', CITY, 10, 18),
    ('go', CITY, 15, 10), ('shot', 'behind-shop-roof'), ('south', 1, None), ('at', CITY, 15, 10),
    ('go', CITY, 21, 13), ('shot', 'behind-antenna-tree'), ('west', 1, None), ('at', CITY, 21, 13),
    # Ledges: jump south and west, and fail to climb back.
    ('go', CITY, 10, 11), ('south', 1, 'ledge-jump-south'), ('at', CITY, 10, 13), ('north', 1, None), ('at', CITY, 10, 13),
    ('go', CITY, 7, 10), ('west', 1, 'ledge-jump-west'), ('at', CITY, 5, 10), ('east', 1, None), ('at', CITY, 5, 10),
    ('go', CITY, 5, 20), ('south', 1, 'ledge-jump-gym-lawn'), ('at', CITY, 5, 22), ('north', 1, None), ('at', CITY, 5, 22),
    # Blocked: the Center body, the unbuilt Gym, shop and house doors, the unbuilt gate, a tree, a wall, the mountain.
    ('go', CITY, 21, 24), ('north', 1, None), ('at', CITY, 21, 24),
    ('go', CITY, 11, 24), ('north', 1, None), ('at', CITY, 11, 24),
    ('go', CITY, 16, 15), ('north', 1, None), ('at', CITY, 16, 15),
    ('go', CITY, 25, 15), ('north', 1, None), ('at', CITY, 25, 15),
    ('go', CITY, 12, 6), ('north', 1, None), ('at', CITY, 12, 6),
    ('go', CITY, 16, 8), ('north', 1, None), ('at', CITY, 16, 8),
    ('go', CITY, 5, 10), ('north', 1, None), ('at', CITY, 5, 10),
    ('go', CITY, 3, 18), ('west', 1, None), ('at', CITY, 3, 18),
    ('go', CITY, 15, 26), ('south', 1, None), ('at', CITY, 15, 26),
    # Signs.
    ('sign', CITY, 4, 12, 'town-sign'), ('sign', CITY, 8, 24, 'gym-sign'),
    # Center: in, upstairs and back, out.
    ('go', CITY, 22, 24), ('north', 1, None), ('wait', 400), ('map', CENTER, 'center-entry'), ('shot', 'center-interior'),
    ('go', CENTER, 2, 6), ('west', 1, None), ('wait', 400), ('map', UPSTAIRS, 'center-upstairs'), ('shot', 'center-upstairs'),
    ('west', 1, None), ('wait', 400), ('map', CENTER, 'center-stair-return'),
    ('go', CENTER, 7, 7), ('south', 2, None), ('wait', 400), ('at', CITY, 22, 24), ('shot', 'center-exit'),
    # Another town through the ordinary renderer, then back.
    ('view', 0, 50, 17, 'regression-cherrygrove'), ('view', CITY, 22, 25, 'return-to-mahogany'),
]
WALK_BEHIND = {'behind-center': (22, 19), 'behind-gym-roof': (10, 18), 'behind-shop-roof': (15, 10),
               'behind-antenna-tree': (21, 13)}
# In front of a building the player's head (the cell above its feet) overlaps the building's
# base row; that row is behind the player, so BG1 must leave both of its cells clear.
IN_FRONT = ('center-approach', 'center-exit', 'gym-front', 'shop-front', 'east-house-front', 'gate-front')

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
    old = 'static void shot(const char*t){screenshot(out,t);}'
    assert old in prefix
    prefix = prefix.replace(old, r'''static void vram(const char*t){char p[2048];snprintf(p,sizeof(p),"%s/vram-%s.bin",out,t);FILE*f=fopen(p,"wb");
 for(unsigned a=0x06000000;a<0x06010000;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 for(unsigned a=0x05000000;a<0x05000200;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 unsigned short r[13];r[0]=c->busRead16(c,0x04000000);for(int i=0;i<4;i++)r[1+i]=c->busRead16(c,0x04000008+2*i);
 unsigned g=sym("sGpuRegBuffer");for(int i=0;i<8;i++)r[5+i]=c->busRead16(c,g+0x10+2*i);fwrite(r,2,13,f);fclose(f);}
static void shot(const char*t){screenshot(out,t);vram(t);char o[128];snprintf(o,sizeof(o),"shot:%s",t);observe(o);}''')
    return prefix + MAIN.replace('BODY', body())

def padded(img, border):
    """A decoded native map with its 2x2 border block beyond the edges (the camera sees it).
    The border index follows the cell's parity, as GetBorderBlockAt does."""
    H, W = img.shape[0] // 16, img.shape[1] // 16
    P = 16
    out = np.zeros(((H + 2 * P) * 16, (W + 2 * P) * 16, 3), np.int32)
    for py in range(H + 2 * P):
        for px in range(W + 2 * P):
            x, y = px - P, py - P
            if not (0 <= x < W and 0 <= y < H):
                x, y = border[0] + (x & 1), border[1] + (y & 1)
            out[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = img[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
    return out, P * 16

def expected():
    city = np.array(Image.open(ROOT / f'gba/art/mahogany-town/evidence/elements/native-{STYLE}.png').convert('RGB')).astype(np.int32) >> 3
    return padded(city, BORDER)

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
    city = expected()
    from tiles import Tileset
    cg = np.frombuffer((game / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), '<u2')
    cherry = (np.array(Tileset(game, 'cherrygrove', 'cherrygrove').map_image(cg.tolist(), 80).convert('RGB')).astype(np.int32) >> 3, 0)
    results = []
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        if any(t in tag for t in ('interior', 'upstairs', 'continue-menu')):
            continue
        ref, pad = cherry if tag.startswith('regression-cherrygrove') else city
        shot = map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        o = positions[tag]
        x0, y0 = o['x'] * 16 - 112 + pad, o['y'] * 16 - 72 + pad
        d = (ref[y0:y0 + 160, x0:x0 + 240] != shot).any(-1)
        anim = animated(p)                                   # CherrygrovePrimary's sea tiles 1-92 animate (Cherrygrove only)
        r = dict(frame=tag, mismatched_map_layer_pixels=int((d & ~anim).sum()),
                 pixels_on_animated_water=int(anim.sum()), animated_water_pixels_differing_from_frame_0=int((d & anim).sum()),
                 camera_origin_px=[int(x0 - pad), int(y0 - pad)])
        if tag in WALK_BEHIND:                              # the player's cell is at screen (112, 72)
            r['bg1_pixels_over_player_cell'] = int(bg1(p)[72:88, 112:128].sum())
        if tag in IN_FRONT:                                 # head cell (112, 56) and feet cell (112, 72)
            r['bg1_pixels_over_player'] = int(bg1(p)[56:88, 112:128].sum())
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
    assert all(behind.values()) and not any(front.values()), (behind, front)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
