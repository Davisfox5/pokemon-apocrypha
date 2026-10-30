#!/usr/bin/env python3
"""Headless mGBA checks for Violet City's cleanup (Cherrygrove's runtime.py harness; one emulator run).

    MGBA_FLAGS='-I... -L... -lmgba ...' python3 tools/gba/maps/violet_city/runtime.py ENGINE OUT

Into the east gate and back out, into the west gate and back out, a walk down the north road, over the
north bridge, across the landing and the south bridge to the main street, the lake blocking on foot, the
hall's front blocking at its door and the lawn its old west wing gave back walkable.
Every capture is compared with the installed native decode outside the player sprite: results.json
records the share of identical pixels per frame.
"""
from __future__ import annotations
import json, os, shlex, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE)]
import violet as V                                   # noqa: E402

VIOLET, EAST_GATE, WEST_GATE = 43, 33, 45            # sMapProofMaps / map group indices (src/apocrypha_map_proof.c)

TEMPLATE = r'''
#define main unused_map_qualification_main
#include "RUNTIME_C"
#undef main
#define RIGHT 16
#define LEFT 32
#define UP 64
#define DOWN 128
static const char *out;
static void shot(const char*t){screenshot(out,t);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");printf("{\"shot\":\"%s\",\"map\":%u,\"x\":%u,\"y\":%u}\n",t,c->busRead32(c,a+8),c->busRead32(c,a+12),c->busRead32(c,a+16));fflush(stdout);}
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void need(int ok,const char*tag){if(!ok){fprintf(stderr,"FAILED %s (map %u at %u,%u)\n",tag,state[2],state[3],state[4]);shot(tag);exit(40);}}
static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);need(state[2]==map&&state[3]==x&&state[4]==y,tag);}
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static void step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<32&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?40:8,0);frames(16,0);}
static void walk(unsigned key,int n,const char*name){char t[64];for(int i=0;i<n;i++){step(key);sprintf(t,"%s-%d",name,i);shot(t);}}
int main(int argc,char**argv){
 if(argc!=4){fprintf(stderr,"runtime ROM SYMBOLS OUT\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"violet-city");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 call("MapProof_Boot",0);frames(240,0);observe("new-game");
 // the east gate and back
 go(VIOLET,74,57);at(VIOLET_NUM,74,57,"east-front");shot("east-front");
 step(UP);frames(240,0);observe("east-gate");need(state[2]==EAST_NUM,"into-east-gate");shot("east-gate-inside");
 go(VIOLET,74,57);at(VIOLET_NUM,74,57,"east-front-again");
 // the west gate and back
 go(VIOLET,6,30);at(VIOLET_NUM,6,30,"west-front");shot("west-front");
 step(LEFT);step(LEFT);frames(240,0);observe("west-gate");need(state[2]==WEST_NUM,"into-west-gate");shot("west-gate-inside");
 // the north road, both bridges and the landing, south to the main street
 go(VIOLET,39,13);at(VIOLET_NUM,39,13,"north-road");shot("north-road");
 walk(DOWN,30,"south");
 observe("main-street");need(state[2]==VIOLET_NUM&&state[3]==39&&state[4]==43,"walked-south-to-the-main-street");
 printf("{\"walked\":\"north-road-to-main-street\"}\n");
 // the lake blocks on foot
 go(VIOLET,30,15);step(DOWN);at(VIOLET_NUM,30,15,"lake-blocks");shot("lake-blocks");
 // the hall: its door blocks from the spur, the lawn its old west wing gave back is open
 go(VIOLET,57,42);step(UP);at(VIOLET_NUM,57,42,"hall-blocks");shot("hall-front");
 go(VIOLET,47,40);step(RIGHT);step(RIGHT);at(VIOLET_NUM,49,40,"old-wing-open");shot("old-wing");
 c->deinit(c);return 0;
}
'''

def generate():
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    return src.replace('#define RIGHT 16\n', f'#define RIGHT 16\n#define VIOLET {VIOLET}\n#define VIOLET_NUM {VIOLET}\n#define EAST_NUM {EAST_GATE}\n#define WEST_NUM {WEST_GATE}\n', 1)

def parity(engine, outdir, shots):
    img, _, _ = V.decode(engine)
    pad = 16 * 16
    canvas = np.full((img.shape[0] + 2 * pad, img.shape[1] + 2 * pad, 3), -1, np.int16)
    canvas[pad:pad + img.shape[0], pad:pad + img.shape[1]] = img
    canvas = np.where(canvas >= 0, canvas >> 3, -1)
    sprite = np.zeros((160, 240), bool); sprite[40:96, 96:144] = True
    res = []
    for s in shots:
        f = outdir / f"{s['shot']}.png"
        if s['map'] != VIOLET or not f.exists():
            continue
        frame = np.array(Image.open(f).convert('RGB')).astype(np.int16) >> 3
        x0, y0 = pad + s['x'] * 16 - 112, pad + s['y'] * 16 - 72
        cc = canvas[y0:y0 + 160, x0:x0 + 240]
        valid = (cc[..., 0] >= 0) & ~sprite
        res.append(dict(shot=s['shot'], x=s['x'], y=s['y'], identical=round(float(((cc == frame).all(-1) & valid).sum() / max(1, valid.sum())), 4)))
    return res

def main():
    engine = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / 'violet_runtime.c').write_text(generate())
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(out / 'violet_runtime.c'), *flags, '-o', str(out / 'runtime')], check=True)
    lines = subprocess.check_output([shutil.which('arm-none-eabi-nm'), str(engine / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'gMapProofState'}
    symbols = {r[2]: r[0] for l in lines.splitlines() if len(r := l.split()) == 3 and r[2] in wanted}
    assert symbols.keys() == wanted, wanted - symbols.keys()
    (out / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in symbols.items()))
    r = subprocess.run([str(out / 'runtime'), str(engine / 'pokeemerald.gba'), str(out / 'symbols.txt'), str(out)],
                       capture_output=True, text=True, timeout=5400)
    (out / 'run.jsonl').write_text(r.stdout)
    for file in out.glob('*.ppm'):
        Image.open(file).save(file.with_suffix('.png')); file.unlink()
    obs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
    res = dict(exit_code=r.returncode, stderr=r.stderr[-2000:], parity=parity(engine, out, [o for o in obs if 'shot' in o]))
    (out / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(r.returncode, r.stderr[-600:])
    sys.exit(r.returncode)

if __name__ == '__main__':
    main()
