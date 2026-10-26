#!/usr/bin/env python3
"""Headless mGBA checks for Cherrygrove's cleanup (Route 30's runtime.py harness; one emulator run).

    MGBA_FLAGS='-I... -L... -lmgba ...' python3 tools/gba/maps/cherrygrove_town/runtime.py ENGINE OUT

Every house door: from the cell below it, walk in (the open animation captured on its frames), check the
interior loads, walk out, check the player stands outside the door again. The Mart and Center doors the
same. East along the road into Route 29 and back (its window and the town's, frame by frame), and the
pond blocks on foot. Every capture is compared with the installed native decode (Cherrygrove with Route 29
beside it) outside the player sprite: results.json records the share of identical pixels per frame.
"""
from __future__ import annotations
import json, os, shlex, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / 'route30_catalog')]
from seams import layout                                     # noqa: E402

TOWN, R29 = 0, 9
DOORS = dict(PlayerHouse=(43, 17, 1), GoldHouse=(54, 19, 2), NeighborHouse=(64, 24, 3), Mart=(51, 9, 5),
             PokemonCenter=(61, 9, 6), HarborHouse=(52, 31, 11), GardenHouse=(65, 31, 12))
EAST_ROW, POND_FROM = 18, (64, 5)                            # the east road's middle row; the lawn west of the pond

TEMPLATE = r'''
#define main unused_map_qualification_main
#include "RUNTIME_C"
#undef main
#define A 1
#define B 2
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
static void door(const char*name,unsigned x,unsigned y,unsigned inside){
 char t[96];go(0,x,y+1);sprintf(t,"%s-front",name);at(0,x,y+1,t);shot(t);
 c->setKeys(c,UP);for(int i=0;i<24;i++){c->runFrame(c);if(i==5||i==9||i==13){sprintf(t,"%s-opening-%d",name,i);screenshot(out,t);printf("{\"frame\":\"%s\"}\n",t);}}c->setKeys(c,0);
 frames(240,0);observe(name);sprintf(t,"%s-inside",name);need(state[2]==inside,t);shot(t);
 c->setKeys(c,DOWN);frames(4,DOWN);c->setKeys(c,0);frames(300,0);observe(name);sprintf(t,"%s-back-outside",name);
 need(state[2]==0&&state[3]==x&&(state[4]==y||state[4]==y+1),t);shot(t);
}
int main(int argc,char**argv){
 if(argc!=4){fprintf(stderr,"runtime ROM SYMBOLS OUT\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"cherrygrove-town");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 call("MapProof_Boot",0);frames(240,0);observe("new-game");
 DOORS_CALLS
 // East along the road into Route 29 and back.
 go(0,74,EAST_ROW);at(0,74,EAST_ROW,"east-road");shot("east-road");
 for(int i=0;i<8;i++){step(RIGHT);char t[64];sprintf(t,"east-%d",i);shot(t);}
 observe("in-route-29");need(state[2]==9,"crossed-into-route-29");
 for(int i=0;i<8;i++){step(LEFT);char t[64];sprintf(t,"west-%d",i);shot(t);}
 at(0,74,EAST_ROW,"back-in-cherrygrove");shot("back-in-cherrygrove");
 printf("{\"walked\":\"Cherrygrove-Route29-and-back\"}\n");
 // The pond blocks on foot.
 go(0,POND_X,POND_Y);step(RIGHT);at(0,POND_X,POND_Y,"pond-blocks");shot("pond-blocks");
 c->deinit(c);return 0;
}
'''

def generate():
    calls = ''.join(f'door("{n}",{x},{y},{inside});' for n, (x, y, inside) in DOORS.items())
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c')).replace('DOORS_CALLS', calls)
    return src.replace('#define A 1\n', f'#define A 1\n#define EAST_ROW {EAST_ROW}\n#define POND_X {POND_FROM[0]}\n#define POND_Y {POND_FROM[1]}\n', 1)

def world(engine):
    """The town's native decode with Route 29 to its east, as the connection joins them."""
    def img(lid):
        words, t = layout(engine, lid)
        return np.array(t.map_image(words.ravel().tolist(), words.shape[1]).convert('RGB'))
    cg, r29 = img('LAYOUT_CHERRYGROVE_CITY'), img('LAYOUT_CHERRYGROVE_ROUTE29_APPROACH')
    pad = 16 * 16
    canvas = np.zeros((pad + max(cg.shape[0], r29.shape[0]) + pad, pad + cg.shape[1] + r29.shape[1] + pad, 3), np.int16) - 1
    canvas[pad:pad + cg.shape[0], pad:pad + cg.shape[1]] = cg
    canvas[pad:pad + r29.shape[0], pad + cg.shape[1]:pad + cg.shape[1] + r29.shape[1]] = r29
    return canvas, {TOWN: (pad, pad), R29: (pad + cg.shape[1], pad)}

def parity(engine, outdir, shots):
    canvas, origin = world(engine)
    canvas = np.where(canvas >= 0, canvas >> 3, -1)
    sprite = np.zeros((160, 240), bool); sprite[40:96, 96:144] = True
    res = []
    for s in shots:
        f = outdir / f"{s['shot']}.png"
        if s['map'] not in origin or not f.exists():
            continue
        frame = np.array(Image.open(f).convert('RGB')).astype(np.int16) >> 3
        ox, oy = origin[s['map']]
        x0, y0 = ox + s['x'] * 16 - 112, oy + s['y'] * 16 - 72
        cc = canvas[y0:y0 + 160, x0:x0 + 240]
        valid = (cc[..., 0] >= 0) & ~sprite
        res.append(dict(shot=s['shot'], map=s['map'], x=s['x'], y=s['y'], identical=round(float(((cc == frame).all(-1) & valid).sum() / max(1, valid.sum())), 4)))
    return res

def main():
    engine = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / 'town_runtime.c').write_text(generate())
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(out / 'town_runtime.c'), *flags, '-o', str(out / 'runtime')], check=True)
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
