#!/usr/bin/env python3
"""Headless mGBA checks for Johto's Center and Mart (johto_shops.py): in each town the nurse answers across her
counter, and both Mart counters open their shop (the Discount Corner's prices at three quarters).

    MGBA_FLAGS='-I... -L... -lmgba ...' python3 tools/gba/maps/violet_interiors/shops_runtime.py ENGINE OUT
"""
from __future__ import annotations
import json, os, shlex, shutil, subprocess, sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE)]
import johto_shops as JS                  # noqa: E402
import importlib.util as _u                # noqa: E402
_s = _u.spec_from_file_location('interiors_runtime', HERE / 'runtime.py'); RT = _u.module_from_spec(_s); _s.loader.exec_module(RT)

KEYS = dict(A=1, B=2, RIGHT=16, LEFT=32, UP=64, DOWN=128)
TEMPLATE = r'''
#define main unused_map_qualification_main
#include "RUNTIME_C"
#undef main
static const char *out;
static void tap(unsigned k){c->setKeys(c,k);for(int i=0;i<4;i++)c->runFrame(c);c->setKeys(c,0);frames(20,0);}
static void talk(unsigned map,unsigned x,unsigned y,unsigned face,int presses,const char*tag){
 call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);observe(tag);
 tap(face);tap(1);frames(90,0);
 for(int i=0;i<presses;i++){tap(1);frames(90,0);}
 char t[96];sprintf(t,"talk-%s",tag);screenshot(out,t);
 call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");unsigned inter=c->busRead32(c,a+4*8);
 printf("{\"test\":\"%s\",\"ok\":%d,\"interaction\":%u,\"at\":[%u,%u]}\n",tag,state[3]==x&&state[4]==y,inter,state[3],state[4]);fflush(stdout);
 for(int i=0;i<8;i++){tap(2);frames(30,0);}}
int main(int argc,char**argv){
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"johto-shops");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
TESTS
 return 0;}
'''

def main():
    engine, outdir = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    idx = RT.proof_index(engine)
    nx, ny = JS.NURSE
    ax, ay = JS.CLERK_A
    bx, by = JS.CLERK_B
    tests = ''
    for town in JS.TOWNS:
        up = 'MAP_' + JS.snake(f'{town}PokemonCenter')
        mart = 'MAP_' + JS.snake(f'{town}Mart')
        tests += f' talk({idx[up]},{nx},{ny + 2},{KEYS["UP"]},1,"{town}-nurse");\n'
        for k in (6, 7):
            tests += f' talk({idx[up]},{nx},{ny + 2},{KEYS["UP"]},{k},"{town}-nurse-heal-{k}");\n'
        tests += f' talk({idx[mart]},{ax + 2},{ay},{KEYS["LEFT"]},1,"{town}-standard");\n'
        tests += f' talk({idx[mart]},{bx - 2},{by},{KEYS["RIGHT"]},1,"{town}-second");\n'
        tests += f' talk({idx[mart]},{ax + 2},{ay},{KEYS["LEFT"]},3,"{town}-standard-list");\n'
        tests += f' talk({idx[mart]},{bx - 2},{by},{KEYS["RIGHT"]},4,"{town}-second-list");\n'
    import sinnoh_shops as SS
    for town in SS.TOWNS:
        c = 'MAP_' + JS.snake(f'{town}PokemonCenter')
        tests += f' talk({idx[c]},{SS.NURSE[0]},{SS.NURSE[1] + 2},{KEYS["UP"]},1,"{town}-nurse");\n'
    if outdir.exists(): shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c')).replace('TESTS', tests)
    (outdir / 'shops.c').write_text(src)
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(outdir / 'shops.c'), *flags, '-o', str(outdir / 'shops')], check=True)
    lines = subprocess.check_output([shutil.which('arm-none-eabi-nm'), str(engine / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'gMapProofState'}
    syms = {r[2]: r[0] for l in lines.splitlines() if len(r := l.split()) == 3 and r[2] in wanted}
    (outdir / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in syms.items()))
    r = subprocess.run([str(outdir / 'shops'), str(engine / 'pokeemerald.gba'), str(outdir / 'symbols.txt'), str(outdir)],
                       capture_output=True, text=True, timeout=1800)
    for f in outdir.glob('*.ppm'):
        Image.open(f).save(f.with_suffix('.png')); f.unlink()
    res = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{"test"')]
    (outdir / 'results.json').write_text(json.dumps(dict(exit=r.returncode, stderr=r.stderr[-1500:], tests=res), indent=1) + '\n')
    print(r.returncode, sum(t['ok'] for t in res), '/', len(res), r.stderr[-400:])

if __name__ == '__main__':
    main()
