#!/usr/bin/env python3
"""Headless mGBA checks for Fuchsia City (KantoFuchsiaCity).

    MGBA_FLAGS='-lmgba' PATH=ARM_BIN:$PATH python3 tools/gba/maps/fuchsia_city/runtime.py ENGINE OUT

New game, then the player is placed on the map and captured at review spots across the whole city; a walk
from the Pal Park hall down the main path to the west exit and across to the Route 15 gate, every step
checked; every door and gate exit refuses the player (no interiors or routes yet); the pens and the pond
fence block. Each capture is compared with the native decode at the camera position, outside the player
sprite: results.json records the share of identical pixels per frame.
"""
from __future__ import annotations
import json, os, re, shlex, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE.parent), str(ROOT / 'tools/hoennconv')]
A, B, RIGHT, LEFT, UP, DOWN = 1, 2, 16, 32, 64, 128

SPOTS = [  # (x, y, tag): review captures
    (30, 20, 'pal-park-hall'), (20, 28, 'west-pens'), (42, 33, 'east-pens'), (16, 34, 'mart'),
    (22, 42, 'west-path'), (16, 57, 'gym-row'), (40, 52, 'warden-house'), (54, 38, 'route15-gate'),
    (20, 60, 'route19-gate'), (5, 52, 'west-walkway'), (2, 42, 'west-exit'), (44, 40, 'east-pond'),
]
WALK = ([(DOWN, 'S')] * 22 + [(LEFT, 'W')] * 28 + [(RIGHT, 'E')] * 28 + [(UP, 'N')] * 3 + [(RIGHT, 'E')] * 26)
WALK_START = (30, 20)
BLOCKS = [  # (x, y, key, tag): the player stands at x, y and must not move
    (30, 20, UP, 'hall-door-solid'), (25, 56, UP, 'center-door-solid'), (11, 56, UP, 'gym-door-solid'),
    (16, 56, UP, 'house-door-solid'), (38, 52, UP, 'warden-door-solid'), (13, 33, UP, 'mart-door-solid'),
    (56, 39, RIGHT, 'route15-gate-solid'), (19, 60, DOWN, 'route19-gate-solid'), (15, 27, UP, 'pen-blocks'),
    (36, 40, DOWN, 'pond-fence-blocks'),
]

TEMPLATE = r'''
#define main unused_map_qualification_main
#include "@RUNTIME_C@"
#undef main
@DEFINES@
static const char *out;
static void shot(const char*t){screenshot(out,t);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");printf("{\"shot\":\"%s\",\"map\":%u,\"x\":%u,\"y\":%u}\n",t,c->busRead32(c,a+8),c->busRead32(c,a+12),c->busRead32(c,a+16));fflush(stdout);}
static void go(unsigned x,unsigned y){call("MapProof_Enter",FI|(x<<8)|(y<<16));frames(360,0);}
static void need(int ok,const char*tag){if(!ok){fprintf(stderr,"FAILED %s (map %u at %u,%u)\n",tag,state[2],state[3],state[4]);shot(tag);exit(40);}}
static void at(unsigned x,unsigned y,const char*tag){observe(tag);need(state[2]==FMAP&&state[3]==x&&state[4]==y,tag);}
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static void step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<32&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?40:8,0);frames(16,0);}
static int locked(void){return call("ArePlayerFieldControlsLocked",0);}
static int overworld(void){unsigned cb=c->busRead32(c,sym("gMain")+4);return (cb&~1u)==(sym("CB2_Overworld")&~1u);}
int main(int argc,char**argv){
 if(argc!=4){fprintf(stderr,"runtime ROM SYMBOLS OUT\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"fuchsia");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 call("MapProof_Boot",0);frames(240,0);observe("new-game");
 @SPOTS@
 go(WX,WY);at(WX,WY,"walk-start");
 {unsigned x=WX,y=WY;@WALK@}
 printf("{\"walked\":%d}\n",NWALK);
 @BLOCKS@
 c->deinit(c);return 0;
}
'''

def map_number(engine):
    """MAP_KANTO_FUCHSIA_CITY's number inside its group (the state reports map numbers)."""
    groups = json.loads((engine / 'data/maps/map_groups.json').read_text())
    return groups['gMapGroup_KantoFuchsia'].index('KantoFuchsiaCity')

def proof_index(engine, const):
    lst = re.search(r'sMapProofMaps\[\] = \{([^}]*)\}', (engine / 'src/apocrypha_map_proof.c').read_text()).group(1)
    return [s.strip() for s in lst.split(',')].index(const)

def generate(engine):
    fi, fmap = proof_index(engine, 'MAP_KANTO_FUCHSIA_CITY'), map_number(engine)
    spots = ''.join(f'go({x},{y});at({x},{y},"{t}");shot("{t}");\n ' for x, y, t in SPOTS)
    walk, (x, y) = [], WALK_START
    for i, (k, d) in enumerate(WALK):
        dx, dy = {RIGHT: (1, 0), LEFT: (-1, 0), DOWN: (0, 1), UP: (0, -1)}[k]
        x, y = x + dx, y + dy
        tag = f'walk-{i:03d}'
        walk.append(f'step({k});at({x},{y},"{tag}");need(overworld()&&!locked(),"walk-no-interruption");' + (f'shot("{tag}");' if i % 10 == 9 else ''))
    blocks = ''.join(f'go({x},{y});step({k});at({x},{y},"{t}");shot("{t}");\n ' for x, y, k, t in BLOCKS)
    src = (TEMPLATE.replace('@RUNTIME_C@', str(ROOT / 'tools/gba/maps/runtime.c'))
           .replace('@DEFINES@', f'#define FI {fi}\n#define FMAP {fmap}\n#define WX {WALK_START[0]}\n#define WY {WALK_START[1]}\n#define NWALK {len(WALK)}')
           .replace('@SPOTS@', spots).replace('@WALK@', '\n '.join(walk)).replace('@BLOCKS@', blocks))
    return src, fmap

def parity(engine, outdir, shots, fmap):
    import map_gate as g
    e = g.Engine(engine)
    img = np.array(g.native_image(e, e.by_name['KantoFuchsiaCity'])).astype(np.int16) >> 3
    pad = 16 * 16
    canvas = np.zeros((img.shape[0] + 2 * pad, img.shape[1] + 2 * pad, 3), np.int16) - 1
    canvas[pad:pad + img.shape[0], pad:pad + img.shape[1]] = img
    sprite = np.zeros((160, 240), bool); sprite[40:96, 96:144] = True
    res = []
    for s in shots:
        f = outdir / f"{s['shot']}.png"
        if s['map'] != fmap or not f.exists():
            continue
        frame = np.array(Image.open(f).convert('RGB')).astype(np.int16) >> 3
        x0, y0 = pad + s['x'] * 16 - 112, pad + s['y'] * 16 - 72
        cc = canvas[y0:y0 + 160, x0:x0 + 240]
        valid = (cc[..., 0] >= 0) & ~sprite
        same = ((cc == frame).all(-1) & valid).sum() / max(1, valid.sum())
        res.append(dict(shot=s['shot'], x=s['x'], y=s['y'], identical=round(float(same), 4)))
    return res

def main():
    engine = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    src, fmap = generate(engine)
    (out / 'fuchsia_runtime.c').write_text(src)
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(out / 'fuchsia_runtime.c'), *flags, '-o', str(out / 'runtime')], check=True)
    nm = shutil.which('arm-none-eabi-nm')
    lines = subprocess.check_output([nm, str(engine / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'gMapProofState', 'ArePlayerFieldControlsLocked', 'gMain', 'CB2_Overworld'}
    symbols = {r[2]: r[0] for l in lines.splitlines() if len(r := l.split()) == 3 and r[2] in wanted}
    assert symbols.keys() == wanted, wanted - symbols.keys()
    (out / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in symbols.items()))
    r = subprocess.run([str(out / 'runtime'), str(engine / 'pokeemerald.gba'), str(out / 'symbols.txt'), str(out)],
                       capture_output=True, text=True, timeout=3600)
    (out / 'run.jsonl').write_text(r.stdout)
    for file in out.glob('*.ppm'):
        Image.open(file).save(file.with_suffix('.png')); file.unlink()
    obs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
    res = dict(exit_code=r.returncode, stderr=r.stderr[-2000:], observations=len(obs),
               parity=parity(engine, out, [o for o in obs if 'shot' in o], fmap))
    (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(r.returncode, r.stderr[-600:])
    worst = min((p['identical'] for p in res['parity']), default=None)
    print('frames', len(res['parity']), 'worst identical share', worst)
    sys.exit(r.returncode)

if __name__ == '__main__':
    main()
