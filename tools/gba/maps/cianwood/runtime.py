"""Headless native frames, movement, Center transitions and ordinary flash save."""
from pathlib import Path
import sys,re,subprocess,json,os,hashlib,shlex
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent))
from claude_routes.runtime import TEMPLATE

MAIN=r'''
int main(int argc,char**argv){
 if(argc!=5)return 2;
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"cianwood-native-proof");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/cianwood.sav",out);
 if(strcmp(argv[4],"write")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1792584000000LL;c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"read")){
  need(call("LoadGameSave",0)==1,"load-game-save");call("MapProof_Resume",0);frames(300,0);at(43,15,37,"cold-flash-reload");shot("cold-flash-reload");
 }else if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);shot("continue-menu");frames(1,A);frames(300,0);at(43,15,37,"ordinary-continue");shot("ordinary-continue");
 }else{
  call("MapProof_Boot",0);frames(240,0);
  {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
  go(43,15,20);shot("inlet-and-studio");step(DOWN,18);at(43,15,38,"central-beach-south");shot("southern-beach");step(UP,18);at(43,15,20,"central-beach-return");
  go(43,9,18);step(LEFT,1);at(43,9,18,"west-cliff-blocks");shot("cliff-contact");
  go(43,28,32);step(RIGHT,2);at(43,29,32,"sea-blocks-foot-travel");shot("shore-contact");
  go(43,7,10);shot("north-residence");go(43,12,13);shot("north-clearing");
  go(43,14,26);shot("gym-forecourt");go(43,23,27);shot("house-and-flower-stands");
  read_sign(43,10,16,"city-sign");read_sign(43,13,27,"gym-sign");read_sign(43,17,24,"studio-sign");
  go(43,25,37);shot("center-approach");step(UP,1);frames(400,0);observe("center-entry");need(state[2]==44,"center-entry");shot("center-interior");
  go(44,2,6);step(LEFT,1);frames(400,0);observe("center-upstairs");need(state[2]==45,"center-upstairs");shot("center-upstairs");
  step(LEFT,1);frames(400,0);observe("center-stair-return");need(state[2]==44,"center-stair-return");
  go(44,7,7);step(DOWN,2);frames(400,0);at(43,25,37,"center-exterior-return");shot("center-return");
  go(43,15,37);shot("save-on-beach");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''

def main(game,out):
    out.mkdir(parents=True,exist_ok=True)
    prefix=TEMPLATE.split('int main(')[0].replace('RUNTIME_C',str(ROOT/'tools/gba/maps/runtime.c'))
    prefix=prefix.replace('#undef main','#undef main\n#define A 1\n#define B 2\n#define RIGHT 16\n#define LEFT 32\n#define UP 64\n#define DOWN 128')
    prefix=re.sub(r'static void pos\([^\n]+',r'''static void pos(unsigned*m,unsigned*x,unsigned*y){
 unsigned sb=c->busRead32(c,sym("gSaveBlock1Ptr"));unsigned id=c->busRead8(c,sym("gPlayerAvatar")+5);unsigned ob=sym("gObjectEvents")+id*0x24;
 *m=c->busRead8(c,sb+5);*x=(short)c->busRead16(c,ob+0x10)-7;*y=(short)c->busRead16(c,ob+0x12)-7;
}''',prefix)
    source=out/'runtime.c';source.write_text(prefix+MAIN)
    subprocess.run(['cc',str(source),*shlex.split(os.environ.get('MGBA_FLAGS','-lmgba')),'-o',str(out/'runtime')],check=True)
    raw=subprocess.check_output([os.environ.get('ARM_NM','arm-none-eabi-nm'),str(game/'pokeemerald.elf')],text=True)
    wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','TrySavingData','LoadGameSave','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gSaveBlock2Ptr','gSaveBlock1Ptr','gPlayerAvatar','gObjectEvents'}
    syms={r[2]:r[0] for line in raw.splitlines() if len(r:=line.split())==3 and r[2] in wanted};assert syms.keys()==wanted
    (out/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in syms.items()))
    env=dict(os.environ)
    results=[]
    for phase in ('write','read','menu'):
        r=subprocess.run([str(out/'runtime'),str(game/'pokeemerald.gba'),str(out/'symbols.txt'),str(out),phase],capture_output=True,text=True,env=env,timeout=300)
        (out/(phase+'.jsonl')).write_text(r.stdout);results.append(dict(phase=phase,exit_code=r.returncode,stderr=r.stderr,observations=[json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]))
        (out/'results.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((game/'pokeemerald.gba').read_bytes()).hexdigest(),phases=results),indent=2)+'\n')
        for ppm in out.glob('*.ppm'):Image.open(ppm).save(ppm.with_suffix('.png'));ppm.unlink()
        if r.returncode:raise SystemExit(r.stderr)
    print('Movement, signs, Center warps, flash reload and Continue passed.')

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
