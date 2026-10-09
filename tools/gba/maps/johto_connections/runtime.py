#!/usr/bin/env python3
"""Native walking, doors, collision, dialogue and cold-save checks for the isolated map preview."""
import argparse,hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from claude_routes.runtime import TEMPLATE
ROOT=HERE.parents[3]

MAIN=r'''
int main(int argc,char**argv){
 if(argc!=5)return 2;
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"johto-connections");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/johto.sav",out);
 if(strcmp(argv[4],"write")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1791460800000LL;c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"read")){
  need(call("LoadGameSave",0)==1,"load-game-save");call("MapProof_Resume",0);frames(240,0);at(11,27,18,"cold-reload-new-bark");shot("cold-reload");
 }else if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);shot("continue-menu");frames(1,A);frames(300,0);at(11,27,18,"ordinary-title-continue");shot("title-continue");
 }else{
  call("MapProof_Boot",0);frames(240,0);observe("new-game");
  {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
  // Actual east connection, camera moving both ways.
  go(9,96,16);step(RIGHT,1);at(9,97,16,"route29-east-edge");shot("route29-before-crossing");
  step(RIGHT,1);at(11,0,16,"route29-to-new-bark");shot("new-bark-seam-0");
  for(int i=1;i<=8;i++){char t[50];step(RIGHT,1);sprintf(t,"new-bark-seam-%d",i);shot(t);}
  at(11,8,16,"new-bark-west-lane");step(LEFT,9);at(9,97,16,"new-bark-to-route29");shot("route29-return");
  // Reach Elm on ordinary walking input, not a warp helper.
  step(RIGHT,28);at(11,27,16,"campus-courtyard");shot("campus-courtyard");
  step(UP,5);frames(360,0);observe("institute-door");need(state[2]==14,"institute-entry");shot("institute-reception");
  step(DOWN,2);frames(360,0);observe("institute-exit");need(state[2]==11,"institute-return");shot("institute-return");
  // Separate houses must return to their own front doors.
  go(11,16,25);step(UP,1);frames(360,0);observe("west-house-entry");need(state[2]==15,"west-house-entry");step(DOWN,1);frames(360,0);at(11,16,25,"west-house-return");
  go(11,35,25);step(UP,1);frames(360,0);observe("east-house-entry");need(state[2]==18,"east-house-entry");step(DOWN,1);frames(360,0);at(11,35,25,"east-house-return");
  go(11,35,11);step(UP,1);at(11,35,11,"annex-closed");shot("annex-and-equipment");
  go(11,26,26);step(DOWN,2);at(11,26,26,"terrace-railing-blocks");shot("coastal-terrace");
  read_sign(11,21,13,"institute-sign");
  go(11,19,19);tap(UP);frames(1,A);frames(400,0);need(locked(),"researcher-dialogue");shot("researcher-dialogue");close_dialog();
  // Route 30's real north connection and its return.
  go(10,10,0);shot("route30-before-crossing");step(UP,1);at(12,38,29,"route30-to-route31");shot("route31-seam-0");
  for(int i=1;i<=8;i++){char t[50];step(UP,1);sprintf(t,"route31-seam-%d",i);shot(t);}
  at(12,38,21,"route31-south-lane");step(DOWN,9);at(10,10,0,"route31-to-route30");shot("route30-return");
  // Walk to the Violet gate along the main route, past grass and the pond.
  step(UP,11);at(12,38,19,"route31-junction");shot("route31-junction");
  step(LEFT,31);at(12,7,19,"route31-west-lane");step(UP,4);frames(360,0);observe("violet-gate-entry");need(state[2]==16,"violet-gate-entry");shot("violet-gate-interior");
  step(UP,1);step(LEFT,11);step(DOWN,2);frames(360,0);observe("violet-arrival");need(state[2]==13,"violet-arrival");shot("violet-arrival");
  // Return through the same gate.
  go(13,22,14);step(UP,1);frames(360,0);observe("violet-return-gate");need(state[2]==16,"violet-return-gate");
  step(UP,1);step(RIGHT,11);step(DOWN,2);frames(360,0);observe("violet-return-route31");need(state[2]==12,"violet-return-route31");
  go(12,36,9);shot("dark-cave-exterior");step(UP,1);frames(360,0);observe("dark-cave-entry");need(state[2]==17,"dark-cave-entry");shot("dark-cave-room");
  step(DOWN,1);frames(360,0);observe("dark-cave-return");need(state[2]==12,"dark-cave-return");
  go(12,24,17);step(DOWN,1);at(12,24,19,"route31-ledge-jump");step(UP,1);at(12,24,19,"route31-ledge-blocks-uphill");
  go(12,12,22);step(RIGHT,1);at(12,12,22,"route31-pond-blocks");
  read_sign(12,25,20,"route31-sign");read_sign(12,33,13,"dark-cave-sign");
  go(11,27,18);at(11,27,18,"save-at-new-bark");shot("save-at-new-bark");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''

FILM=r'''
int main(int argc,char**argv){
 if(argc!=5)return 2;
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"johto-motion");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1791460800000LL;c->reset(c);frames(600,0);
 call("MapProof_Boot",0);frames(240,0);go(11,10,17);
 for(int i=0;i<120;i++){frames(1,RIGHT);if(i%4==0){char tag[60];sprintf(tag,"walk-%03d",i);shot(tag);}}
 frames(60,0);observe("campus-walk-end");need(state[2]==11&&state[3]>10,"walk-moves-across-campus");
 c->deinit(c);return 0;
}
'''

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('game',type=Path);p.add_argument('output',type=Path);p.add_argument('--toolchain',type=Path,required=True);p.add_argument('--film-only',action='store_true',help='Capture native walking frames without changing the acceptance save');args=p.parse_args()
    game=args.game.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    prefix=TEMPLATE.split('int main(')[0].replace('RUNTIME_C',str(ROOT/'tools/gba/maps/runtime.c'))
    prefix=prefix.replace('frames(120,0)','frames(400,0)')
    prefix=prefix.replace('#undef main','#undef main\n#define A 1\n#define B 2\n#define RIGHT 16\n#define LEFT 32\n#define UP 64\n#define DOWN 128')
    source=out/'runtime.c';source.write_text(prefix+(FILM if args.film_only else MAIN))
    subprocess.run(['cc',str(source),*shlex.split(os.environ.get('MGBA_FLAGS','-lmgba')),'-o',str(out/'runtime')],check=True)
    raw=subprocess.check_output([str(args.toolchain.resolve()/'bin/arm-none-eabi-nm'),str(game/'pokeemerald.elf')],text=True)
    wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','TrySavingData','LoadGameSave','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gSaveBlock2Ptr'}
    symbols={r[2]:r[0] for line in raw.splitlines() if len(r:=line.split())==3 and r[2] in wanted};assert symbols.keys()==wanted
    (out/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
    results=[]
    for phase in (['film'] if args.film_only else ['write','read','menu']):
        r=subprocess.run([str(out/'runtime'),str(game/'pokeemerald.gba'),str(out/'symbols.txt'),str(out),phase],capture_output=True,text=True,timeout=300)
        (out/(phase+'.jsonl')).write_text(r.stdout)
        results.append(dict(phase=phase,exit_code=r.returncode,stderr=r.stderr,observations=[json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]))
        (out/'results.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((game/'pokeemerald.gba').read_bytes()).hexdigest(),phases=results),indent=2)+'\n')
        for ppm in out.glob('*.ppm'):Image.open(ppm).save(ppm.with_suffix('.png'));ppm.unlink()
        print(phase,r.returncode,r.stderr[-1000:],flush=True)
        if r.returncode:raise SystemExit(r.returncode)
    if args.film_only:
        frames=[Image.open(file).convert('RGB') for file in sorted(out.glob('walk-*.png'))]
        assert len(frames)==30
        frames[0].save(out/'campus-walk.gif',save_all=True,append_images=frames[1:],duration=67,loop=0)

if __name__=='__main__':main()
