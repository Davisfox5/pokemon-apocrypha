"""Headless native walking, layering, doors and ordinary save/Continue proof."""
from pathlib import Path
import hashlib,json,os,shlex,subprocess,sys
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from claude_routes.runtime import TEMPLATE
from render_native import render
from build import ART,N,O

def source():
    prefix=TEMPLATE.split('int main(')[0].replace('RUNTIME_C',str(ROOT/'tools/gba/maps/runtime.c'))
    prefix=prefix.replace('#undef main','#undef main\n#define UP 64\n#define DOWN 128\n#define LEFT 32\n#define RIGHT 16\n#define A 1\n#define B 2\n')
    prefix=prefix.replace('static void shot(const char*t){screenshot(out,t);}',r'''static void shot(const char*t){
 screenshot(out,t);char file[2048],tag[128];snprintf(file,sizeof(file),"%s/vram-%s.bin",out,t);FILE*f=fopen(file,"wb");
 for(unsigned a=0x06000000;a<0x06010000;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 for(unsigned a=0x05000000;a<0x05000200;a+=4){unsigned v=c->busRead32(c,a);fwrite(&v,4,1,f);}
 unsigned short r[13];r[0]=c->busRead16(c,0x04000000);for(int i=0;i<4;i++)r[1+i]=c->busRead16(c,0x04000008+i*2);
 for(int i=0;i<8;i++)r[5+i]=c->busRead16(c,sym("sGpuRegBuffer")+0x10+i*2);fwrite(r,2,13,f);fclose(f);
 snprintf(tag,sizeof(tag),"shot:%s",t);observe(tag);
}''')
    views=[('town-square',16,16),('center-front',22,24),('gym-front',11,24),('shop-front',16,15),('east-house',25,15),('gate',12,6),('west-lawn',3,11),('north-forest',17,9),('east-road',30,16),('south-terrace',15,26),('gym-lawn',5,23),('center-lawn',18,23),('west-exit',0,13),('north-canopies',18,-1),('south-groves',14,29)]
    body=''
    for tag,x,y in views:body+=f'go(43,{x+O},{y+O});shot("{tag}");\n'
    body+='go(43,24,21);shot("behind-center-roof");step(DOWN,1);at(43,24,21,"center-body-blocks");\n'
    for x,y,key,xx,yy in [(10,11,'DOWN',10,13),(7,10,'LEFT',5,10),(5,20,'DOWN',5,22)]:
        rev={'DOWN':'UP','LEFT':'RIGHT'}[key]
        body+=f'go(43,{x+2},{y+2});step({key},1);at(43,{xx+2},{yy+2},"ledge-jump-{x}-{y}");step({rev},1);at(43,{xx+2},{yy+2},"ledge-return-blocked-{x}-{y}");\n'
    for x,y in [(11,24),(16,15),(25,15),(12,6),(21,24)]:body+=f'go(43,{x+2},{y+2});step(UP,1);at(43,{x+2},{y+2},"original-barrier-{x}-{y}");\n'
    for tag,x,y in [('town-sign',4,12),('shop-sign',14,14),('gym-sign',8,24)]:body+=f'read_sign(43,{x+2},{y+2},"{tag}");\n'
    body+='''go(43,24,26);step(UP,1);frames(400,0);observe("center-entry");need(state[2]==44,"center-entry");shot("center-interior");
 go(44,2,6);step(LEFT,1);frames(400,0);observe("stairs-up");need(state[2]==45,"stairs-up");shot("center-upstairs");
 step(LEFT,1);frames(400,0);observe("stairs-down");need(state[2]==44,"stairs-down");
 go(44,7,7);step(DOWN,2);frames(400,0);at(43,24,26,"center-return");shot("center-return");
 go(43,24,26);for(int t=0;t<90;t++){frames(1,t<20?UP:0);char tag[80];sprintf(tag,"door-frame-%03d",t);screenshot(out,tag);}frames(300,0);
 go(43,24,27);shot("save-in-town");
'''
    main=r'''
int main(int argc,char**argv){
 if(argc!=5)return 2;out=argv[3];FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"fresh-mahogany");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/mahogany.sav",out);
 if(strcmp(argv[4],"write")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1792843200000LL;c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"write")){
  call("MapProof_Boot",0);frames(240,0);
  {unsigned s=c->busRead32(c,sym("gSaveBlock2Ptr"));unsigned char name[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};for(int i=0;i<8;i++)c->busWrite8(c,s+i,name[i]);}
  BODY
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t n=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||n!=131072||!f||fwrite(data,1,n,f)!=n)return 11;fclose(f);free(data);printf("{\"ordinary_save_bytes\":%zu,\"save_status\":%u}\n",n,status);
 }else if(!strcmp(argv[4],"read")){
  need(call("LoadGameSave",0)==1,"flash-load");call("MapProof_Resume",0);frames(300,0);at(43,24,27,"cold-reload");shot("cold-reload");
 }else{
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);frames(1,A);frames(300,0);at(43,24,27,"title-continue");shot("title-continue");
 }
 c->deinit(c);return 0;
}
'''
    return prefix+main.replace('BODY',body)

def bg(dump):
    raw=dump.read_bytes();v=np.frombuffer(raw[:0x10000],np.uint8);p=np.frombuffer(raw[0x10000:0x10200],'<u2').astype(int);r=np.frombuffer(raw[0x10200:],'<u2').astype(int)
    rgb=np.stack([p&31,(p>>5)&31,p>>10],-1).reshape(16,16,3);out=np.broadcast_to(rgb[0,0],(160,240,3)).copy();masktop=np.zeros((160,240),bool)
    yy,xx=np.mgrid[0:160,0:240];layers=[]
    for b in (1,2,3):
        ctl=r[1+b];layers.append((ctl&3,b,((ctl>>2)&3)*0x4000,((ctl>>8)&31)*0x800,r[5+2*b]&511,r[6+2*b]&511))
    for priority,b,cb,sb,ho,vo in sorted(layers,reverse=True):
        X=(xx+ho)&255;Y=(yy+vo)&255;e=v.view('<u2')[sb//2+Y//8*32+X//8].astype(int);tx=np.where(e&1024,7-X%8,X%8);ty=np.where(e&2048,7-Y%8,Y%8);q=v[cb+(e&1023)*32+ty*4+tx//2];ix=np.where(tx%2,q>>4,q&15);m=ix>0;out[m]=rgb[e[m]>>12,ix[m]]
        if b==1:masktop=m
    return out,masktop

def main(game,out):
    out.mkdir(exist_ok=True,parents=True);(out/'runtime.c').write_text(source());flags=shlex.split(os.environ.get('MGBA_FLAGS','-lmgba'));subprocess.run(['cc','-O1',str(out/'runtime.c'),*flags,'-o',str(out/'runtime')],check=True)
    wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','gMain','CB2_Overworld','gSaveBlock2Ptr','TrySavingData','LoadGameSave','ArePlayerFieldControlsLocked','sGpuRegBuffer'}
    lines=subprocess.check_output(['arm-none-eabi-nm',str(game/'pokeemerald.elf')],text=True);syms={s[2]:s[0] for l in lines.splitlines() if len(s:=l.split())==3 and s[2] in wanted};assert syms.keys()==wanted
    (out/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in syms.items()));phases=[]
    for phase in ['write','read','menu']:
        r=subprocess.run([str(out/'runtime'),str(game/'pokeemerald.gba'),str(out/'symbols.txt'),str(out),phase],capture_output=True,text=True,timeout=600)
        phases.append(dict(phase=phase,exit_code=r.returncode,stderr=r.stderr,observations=[json.loads(s) for s in r.stdout.splitlines() if s.startswith('{')]))
        for p in out.glob('*.ppm'):Image.open(p).save(p.with_suffix('.png'));p.unlink()
        (out/'results.json').write_text(json.dumps(dict(phases=phases),indent=2)+'\n')
        if r.returncode:raise SystemExit(r.stderr)
    native=np.array(render(game,'MahoganyTown')).astype(int)>>3;P=16;expected=np.zeros(((N+P*2)*16,(N+P*2)*16,3),int)
    for y in range(-P,N+P):
        for x in range(-P,N+P):
            ax=x if 0<=x<N and 0<=y<N else x&1;ay=y if 0<=x<N and 0<=y<N else y&1
            expected[(y+P)*16:(y+P+1)*16,(x+P)*16:(x+P+1)*16]=native[ay*16:(ay+1)*16,ax*16:(ax+1)*16]
    shots={o['step'][5:]:o for p in phases for o in p['observations'] if o.get('step','').startswith('shot:')};checks=[]
    for tag,o in shots.items():
        if o['map']!=43 or 'sign' in tag:continue
        actual,top=bg(out/f'vram-{tag}.bin');x=o['x']*16-112+P*16;y=o['y']*16-72+P*16;want=expected[y:y+160,x:x+240];bad=int((actual!=want).any(-1).sum());assert bad==0,(tag,bad)
        checks.append(dict(frame=tag,background_pixel_mismatches=bad,foreground_over_player=int(top[72:88,112:128].sum())))
        Image.fromarray((actual<<3|actual>>2).astype('uint8')).save(out/f'bg-{tag}.png')
    assert next(c for c in checks if c['frame']=='behind-center-roof')['foreground_over_player']>0
    result=dict(rom_sha256=hashlib.sha256((game/'pokeemerald.gba').read_bytes()).hexdigest(),phases=phases,native_background_checks=checks)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(rom_sha256=result['rom_sha256'],frames=len(checks),native_pixel_mismatches=0,ordinary_save_and_continue=True)))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
