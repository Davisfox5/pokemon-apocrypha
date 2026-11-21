#!/usr/bin/env python3
"""Headless capture of the tall-grass rustle field effect while walking Route 29's grass.

    MGBA_FLAGS='-lmgba' python3 tools/gba/dexnav/runtime.py ENGINE OUT

ENGINE is a built pokeemerald-expansion checkout (apocrypha branch). One emulator run:
new game, the start menu shows POKeGEAR, every Pokegear app tab, the DexNav app opens the
expansion's DexNav screen and B returns to the gear, then the player walks Route 29's grass
until a hidden Pokemon is detected and the rustle frames are captured. Writes PNGs,
run.jsonl and results.json to OUT; exits non-zero on any failed check.
"""
from __future__ import annotations
import json, os, shlex, shutil, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
ROUTE29 = 9                     # index in sMapProofMaps (src/apocrypha_map_proof.c)
START_X, START_Y = 22, 18       # middle of Route 29's large grass patch
FLAG_POKEGEAR, FLAG_SEARCHING = 0x20, 0x21
VAR_STEPS = 0x40FE

TEMPLATE = r'''
#define main unused_map_qualification_main
#include "RUNTIME_C"
#undef main
#define A 1
#define B 2
#define START 8
#define RIGHT 16
#define LEFT 32
#define UP 64
#define DOWN 128
#define R 256
static const char *out;
static unsigned call2(const char *name,unsigned a,unsigned b){
 unsigned regs[16], cpsr=rd("cpsr");char rn[8];for(int i=0;i<16;i++){sprintf(rn,"r%d",i);regs[i]=rd(rn);}
 wr("cpsr",0x3f);wr("sp",(regs[13]-128)&~7u);wr("r0",a);wr("r1",b);wr("lr",0x09ffff01);wr("pc",sym(name)&~1u);
 unsigned result=0;int done=0;
 for(unsigned n=0;n<200000000;n++){unsigned pc=rd("pc");if(pc>=0x09ffff00&&pc<=0x09ffff08){result=rd("r0");done=1;break;}c->step(c);}
 if(!done){fprintf(stderr,"call timeout %s\n",name);exit(23);}
 wr("cpsr",cpsr);for(int i=0;i<15;i++){sprintf(rn,"r%d",i);wr(rn,regs[i]);}wr("pc",regs[15]-((cpsr&32)?2:4));return result;}
static void shot(const char*t){screenshot(out,t);printf("{\"shot\":\"%s\"}\n",t);fflush(stdout);}
static void need(int ok,const char*tag){if(!ok){fprintf(stderr,"FAILED %s\n",tag);shot(tag);exit(40);}printf("{\"check\":\"%s\",\"ok\":1}\n",tag);fflush(stdout);}
static void press(unsigned k,int wait){frames(3,k);frames(wait,0);}
int main(int argc,char**argv){
 if(argc!=4){fprintf(stderr,"runtime ROM SYMBOLS OUT\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"dexnav");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 call("MapProof_Boot",0);frames(240,0);
 need(call("FlagGet",FLAG_POKEGEAR)==1,"new-game-has-pokegear");
 call("MapProof_Enter",ROUTE29|(START_X<<8)|(START_Y<<16));frames(360,0);observe("route29");
 need(state[3]==START_X&&state[4]==START_Y,"at-route29-grass");shot("route29");
 for(int s=0;s<6;s++){unsigned key=(s&1)?LEFT:RIGHT;
  for(int k=0;k<24;k++){frames(2,k<8?key:0);char t[32];sprintf(t,"step%d-%02d",s,k);screenshot(out,t);} }
 c->deinit(c);return 0;
}
'''

def main():
    engine = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    for k, v in dict(ROUTE29=ROUTE29, START_X=START_X, START_Y=START_Y, FLAG_POKEGEAR=FLAG_POKEGEAR,
                     FLAG_SEARCHING=FLAG_SEARCHING, VAR_STEPS=VAR_STEPS).items():
        src = src.replace('#define A 1\n', f'#define {k} {v}\n#define A 1\n', 1)
    (out / 'rustle_runtime.c').write_text(src)
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(out / 'rustle_runtime.c'), *flags, '-o', str(out / 'runtime')], check=True)
    lines = subprocess.check_output([shutil.which('arm-none-eabi-nm'), str(engine / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'gMapProofState', 'FlagGet', 'VarSet'}
    symbols = {r[2]: r[0] for l in lines.splitlines() if len(r := l.split()) == 3 and r[2] in wanted}
    assert symbols.keys() == wanted, wanted - symbols.keys()
    (out / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in symbols.items()))
    r = subprocess.run([str(out / 'runtime'), str(engine / 'pokeemerald.gba'), str(out / 'symbols.txt'), str(out)],
                       capture_output=True, text=True, timeout=3600)
    (out / 'run.jsonl').write_text(r.stdout)
    for file in out.glob('*.ppm'):
        Image.open(file).save(file.with_suffix('.png')); file.unlink()
    (out / 'results.json').write_text(json.dumps(dict(exit_code=r.returncode, stderr=r.stderr[-2000:]), indent=1) + '\n')
    print(r.returncode, r.stderr[-600:])
    sys.exit(r.returncode)

if __name__ == '__main__':
    main()
