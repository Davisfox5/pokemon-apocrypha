#!/usr/bin/env python3
"""Instrumented mGBA walking/transition/save checks on the ordinary compiled ROM.
No savestates, no production entrypoint changes. MGBA_FLAGS can select local libmgba.
"""
from pathlib import Path
import json,os,shlex,subprocess,sys,struct,shutil
from collections import deque
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pallet_rebuild'))
from native import words
ROOT=Path(__file__).resolve().parents[4]
E=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve();OUT.mkdir(parents=True,exist_ok=True)
shutil.copyfile(E/'pokeemerald.gba',OUT/'runtime-input.gba')
NAMES=['ApocPalletTown','ApocPalletRedHouse1F','ApocPalletRedHouse2F','ApocPalletOakHouse','ApocPalletLab']
LS=json.loads((E/'data/layouts/layouts.json').read_text())['layouts'];MS={43+i:json.loads((E/f'data/maps/{n}/map.json').read_text()) for i,n in enumerate(NAMES)}
GR={};DIMS={}
for i,m in MS.items():
 l=next(l for l in LS if l['id']==m['layout']);GR[i]=words(E/l['blockdata_filepath']);DIMS[i]=(l['width'],l['height'])
KEY={(1,0):16,(-1,0):32,(0,-1):64,(0,1):128}
def grid(i,p):
 x,y=p;w,h=DIMS[i];return GR[i][y*w+x] if 0<=x<w and 0<=y<h else 0x3fff
def route(i,a,b):
 blocked={(v['x'],v['y']) for v in MS[i]['object_events']+MS[i]['warp_events']};prev={a:None};q=deque([a])
 while q:
  p=q.popleft()
  if p==b:break
  for dx,dy in KEY:
   z=(p[0]+dx,p[1]+dy);v=grid(i,z)
   if not(v&0xc00) and v>>12==3 and z not in blocked and z not in prev:prev[z]=(p,KEY[dx,dy]);q.append(z)
 assert b in prev,(i,a,b)
 steps=[];p=b
 while prev[p] is not None:
  pp,key=prev[p];steps.append(f'step({key});at({i},{p[0]},{p[1]},"walk");');p=pp
 return '\n'.join(reversed(steps))
# Native coordinates, continuous walks through every room and both sides of each warp.
tour='go(43,17,18);shot("town-center");\n'+route(43,(17,18),(17,1))+'\nshot("north-route-socket");\n'+route(43,(17,1),(7,13))+'\nstep(64);needmap(44,"red-home-enter");at(44,8,12,"red-arrival");step(64);at(44,8,11,"red-approach");shot("red-home");\n'
tour+=route(44,(8,11),(8,5))+'\nshot("red-room-upper");\n'+route(44,(8,5),(14,3))+'\nstep(16);at(44,15,3,"upstairs-landing");step(16);needmap(45,"bedroom-enter");at(45,13,3,"bedroom-arrival");step(128);at(45,13,4,"stairs-away");\n'
tour+=route(45,(13,4),(10,5))+'\nshot("bedroom-upper");\n'+route(45,(10,5),(7,10))+'\nshot("bedroom");\n'+route(45,(7,10),(13,4))+'\nstep(64);at(45,13,3,"downstairs-landing");step(32);needmap(44,"downstairs-return");at(44,15,3,"stairs-return");step(32);at(44,14,3,"stairs-step-away");\n'
tour+=route(44,(14,3),(8,11))+'\nstep(128);at(44,8,12,"red-exit");step(128);needmap(43,"red-return");at(43,7,13,"red-return-position");shot("red-yard");\n'
tour+=route(43,(7,13),(25,13))+'\nstep(64);needmap(46,"oak-enter");at(46,8,12,"oak-arrival");step(64);at(46,8,11,"oak-approach");\n'
tour+=route(46,(8,11),(12,11))+'\nshot("oak-home");actor_visible(1,"oak-visible","gObjectEventPal_NpcWhite");interact(64,"oak-dialogue");\n'+route(46,(12,11),(7,6))+'\nshot("oak-upper");\n'+route(46,(7,6),(8,11))+'\nstep(128);at(46,8,12,"oak-exit");step(128);needmap(43,"oak-return");at(43,25,13,"oak-return-position");\n'
tour+=route(43,(25,13),(25,24))+'\nstep(64);needmap(47,"lab-enter");at(47,9,16,"lab-arrival");step(64);at(47,9,15,"lab-approach");shot("lab-entrance");\n'
tour+=route(47,(9,15),(9,10))+'\nshot("lab-research");actor_visible(1,"blue-visible","gObjectEventPal_NpcGreen");interact(64,"blue-dialogue");\n'+route(47,(9,10),(10,7))+'\nshot("lab-upper");\n'+route(47,(10,7),(9,15))+'\nstep(128);at(47,9,16,"lab-exit");step(128);needmap(43,"lab-return");at(43,25,24,"lab-return-position");\n'
tour+=route(43,(25,24),(10,28))+'\ninteract(64,"red-memorial");shot("flower-garden");\n'+route(43,(10,28),(16,29))+'\nshot("shore-approach");\n'
# Each non-warp collision edge is independently exercised. Elevation-1 water checked separately.
blocks=[]
for i,m in MS.items():
 w,h=DIMS[i];forbidden={(v['x'],v['y']) for v in m['warp_events']+m['object_events']}
 for y in range(h):
  for x in range(w):
   if grid(i,(x,y))&0xc00 or grid(i,(x,y))>>12!=3 or (x,y) in forbidden:continue
   for (dx,dy),key in KEY.items():
    z=x+dx,y+dy
    if grid(i,z)&0xc00 and z not in forbidden and 0<=z[0]<w and 0<=z[1]<h:
     blocks.append(f'go({i},{x},{y});step({key});at({i},{x},{y},"blocked-edge");')
# Start with whole route tour; edge checks in a separate phase to preserve manageable evidence.
TEMPLATE=r'''
#define main unused_map_qualification_main
#include "COMMON"
#undef main
static const char*out;
static void shot(const char*t){screenshot(out,t);observe(t);}
static void need(int ok,const char*t){if(!ok){observe(t);fprintf(stderr,"FAILED %s\n",t);shot("failed");exit(40);}}
static void go(unsigned m,unsigned x,unsigned y){call("MapProof_Enter",m|(x<<8)|(y<<16));frames(360,0);}
static void at(unsigned m,unsigned x,unsigned y,const char*t){observe(t);need(state[1]==80&&state[2]==m&&state[3]==x&&state[4]==y,t);}
static void needmap(unsigned m,const char*t){observe(t);need(state[1]==80&&state[2]==m,t);}
static void step(unsigned key){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState"),m=c->busRead32(c,a+8),x=c->busRead32(c,a+12),y=c->busRead32(c,a+16);int changed=0;for(int i=0;i<32&&!changed;i++){frames(2,key);call("MapProof_ReadState",0);changed=c->busRead32(c,a+8)!=m||c->busRead32(c,a+12)!=x||c->busRead32(c,a+16)!=y;}frames(150,0);}
static void interact(unsigned key,const char*t){frames(2,key);frames(12,0);frames(1,1);frames(300,0);need(call("ArePlayerFieldControlsLocked",0),t);shot(t);for(int i=0;i<40&&call("ArePlayerFieldControlsLocked",0);i++){frames(1,2);frames(40,0);}need(!call("ArePlayerFieldControlsLocked",0),"dialogue-closes");}
static void actor_visible(unsigned local,const char*tag,const char*palette){
 unsigned objects=sym("gObjectEvents"),sprites=sym("gSprites");int found=0;
 for(unsigned i=0;i<16;i++){unsigned o=objects+i*36,f=c->busRead32(c,o);if((f&1)&&c->busRead8(c,o+8)==local){unsigned gfx=c->busRead16(c,o+4),sp=c->busRead8(c,o+35),info=c->busRead32(c,sym("gObjectEventGraphicsInfoPointers")+4*gfx);need(info>=0x08000000&&info<0x0a000000,"actor-graphics-defined");need(sp<64&&!(f&0x6000)&&!(c->busRead8(c,sprites+sp*68+62)&4),tag);unsigned bank=c->busRead16(c,sprites+sp*68+4)>>12;for(unsigned k=1;k<16;k++)need(c->busRead16(c,0x05000200+bank*32+k*2)==c->busRead16(c,sym(palette)+k*2),"actor-original-palette");found=1;}}
 need(found,tag);
}
static void dump_art(unsigned map){char path[2048];sprintf(path,"%s/vram-%u.bin",out,map);FILE*f=fopen(path,"wb");for(unsigned i=0;i<32768;i++)fputc(c->busRead8(c,0x06000000+i),f);fclose(f);sprintf(path,"%s/palette-%u.bin",out,map);f=fopen(path,"wb");for(unsigned i=0;i<416;i++)fputc(c->busRead8(c,0x05000000+i),f);fclose(f);}
static int anim(unsigned t){return ANIMATED;}
static unsigned hash(int moving){unsigned v=2166136261u;for(unsigned t=0;t<1008;t++)if(anim(t)==moving)for(unsigned j=0;j<32;j++)v=(v^c->busRead8(c,0x06000000+t*32+j))*16777619u;return v;}
int main(int argc,char**argv){
 if(argc!=6)return 2;out=argv[3];const char*phase=argv[4];unsigned map=atoi(argv[5]);FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);need(c&&c->init(c),"init");mCoreConfigInit(&c->config,"pallet-town");c->setVideoBuffer(c,pixels,240);need(mCoreLoadFile(c,argv[1]),"load");
 char flash[2048];snprintf(flash,sizeof(flash),"%s/map-%u.sav",out,map);
 if(!strcmp(phase,"read")||!strcmp(phase,"menu")){unsigned char data[131072];f=fopen(flash,"rb");need(f&&fread(data,1,sizeof(data),f)==sizeof(data),"read-save");fclose(f);need(c->savedataRestore(c,data,sizeof(data),false),"restore");}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);
 if(!strcmp(phase,"menu")){
  frames(1,8);frames(180,0);frames(1,1);frames(300,0);frames(1,1);frames(180,0);shot("continue-menu");frames(1,1);frames(300,0);needmap(map,"continue-loaded");shot("title-continue");
 }else if(!strcmp(phase,"read")){
  need(call("LoadGameSave",0)==1,"ordinary-load");call("MapProof_Resume",0);frames(240,0);needmap(map,"cold-reload");shot("cold-reload");
 }else{
  call("MapProof_Boot",0);frames(240,0);
  if(!strcmp(phase,"tour")){TOUR}
  else if(!strcmp(phase,"blocks")){BLOCKS printf("{\"blocked_edges_passed\":BLOCKCOUNT}\n");}
  else if(!strcmp(phase,"doors")){
   for(unsigned i=0;i<3;i++){
    unsigned x=i==0?7:25,y=i==2?24:13;go(43,x,y);
    for(unsigned t=0;t<40;t++){frames(2,t<12?64:0);if(t%2==0){char tag[50];sprintf(tag,"door-%u-frame-%02u",i,t);screenshot(out,tag);}}
    frames(240,0);needmap(i==0?44:i==1?46:47,"animated-door-arrival");
   }
  }
  else if(!strcmp(phase,"water")){
   go(43,16,29);step(128);at(43,16,29,"water-blocks-foot");
   go(43,16,31);call("SetPlayerAvatarTransitionFlags",8);frames(30,0);step(16);at(43,17,31,"surf-east");step(32);at(43,16,31,"surf-west");step(64);at(43,16,30,"surf-shore");step(64);at(43,16,29,"surf-dismount");need(call("TestPlayerAvatarFlags",1)&&!call("TestPlayerAvatarFlags",8),"dismounted-on-foot");shot("surf-shore");
   go(43,16,35);call("SetPlayerAvatarTransitionFlags",8);frames(30,0);shot("southern-water-border");step(128);at(43,16,35,"unwired-south-boundary-closed");
   go(43,16,29);call("SetPlayerAvatarTransitionFlags",1);frames(30,0);unsigned stable=hash(0),water=hash(1);
   frames(8,0);need(hash(0)==stable&&hash(1)!=water,"only-water-animates");shot("hgss-water-next-phase");frames(56,0);need(hash(0)==stable&&hash(1)==water,"water-loop-is-seamless");shot("hgss-water-full-loop");printf("{\"frames\":64,\"hgss_water\":\"animated\",\"nonwater_vram_unchanged\":true}\n");
  }
  unsigned sx=map==43?17:map==45?7:map==47?9:8,sy=map==43?18:map==45?10:map==47?15:11;go(map,sx,sy);at(map,sx,sy,"save-spot");
  char tag[40];sprintf(tag,"save-map-%u",map);shot(tag);dump_art(map);unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");need(status==1&&size==131072&&f&&fwrite(data,1,size,f)==size,"ordinary-save");fclose(f);free(data);printf("{\"save_map\":%u,\"flash_bytes\":%zu,\"status\":%u}\n",map,size,status);
 }
 c->deinit(c);return 0;
}
'''

water=json.loads((ROOT/'gba/art/pallet-native/source/water-animation.json').read_text())
TEMPLATE=TEMPLATE.replace('ANIMATED','||'.join('t=='+str(t) for t in water['tiles']))
src=TEMPLATE.replace('COMMON',str(ROOT/'tools/gba/maps/runtime.c')).replace('TOUR',tour).replace('BLOCKS','\n'.join(blocks)).replace('BLOCKCOUNT',str(len(blocks)))
(OUT/'runtime.c').write_text(src)
import hashlib
(OUT/'input-identity.json').write_text(json.dumps(dict(
 source_commit=subprocess.check_output(['git','-C',str(E),'rev-parse','HEAD'],text=True).strip(),
 rom_sha256=hashlib.sha256((OUT/'runtime-input.gba').read_bytes()).hexdigest(),
 elf_sha256=hashlib.sha256((E/'pokeemerald.elf').read_bytes()).hexdigest(),
 fixture_sha256=hashlib.sha256(src.encode()).hexdigest()),indent=2)+'\n')
flags=shlex.split(os.environ.get('MGBA_FLAGS','-lmgba'));subprocess.run(['cc','-O1',str(OUT/'runtime.c'),*flags,'-o',str(OUT/'runtime')],check=True)
nm=subprocess.check_output(['arm-none-eabi-nm',str(E/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','TrySavingData','LoadGameSave','ArePlayerFieldControlsLocked','SetPlayerAvatarTransitionFlags','TestPlayerAvatarFlags','gObjectEvents','gSprites','gObjectEventGraphicsInfoPointers','gObjectEventPal_NpcWhite','gObjectEventPal_NpcGreen'}
symbols={s[2]:s[0] for l in nm.splitlines() if len(s:=l.split())==3 and s[2] in wanted};assert symbols.keys()==wanted
(OUT/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
results=[]
phases=[('tour',43),('doors',43),('blocks',43),('water',43)]+[(p,m) for m in range(43,48) for p in ['write','read','menu']]
if len(sys.argv)>3:phases=[(sys.argv[3],int(sys.argv[4]) if len(sys.argv)>4 else 43)]
for phase,m in phases:
 r=subprocess.run([str(OUT/'runtime'),str(OUT/'runtime-input.gba'),str(OUT/'symbols.txt'),str(OUT),phase,str(m)],capture_output=True,text=True,timeout=2400)
 (OUT/f'{phase}-{m}.jsonl').write_text(r.stdout);(OUT/f'{phase}-{m}.stderr').write_text(r.stderr)
 for f in OUT.glob('*.ppm'):Image.open(f).save(OUT/f'{phase}-{m}-{f.stem}.png');f.unlink()
 results.append(dict(phase=phase,map=m,exit_code=r.returncode,stderr=r.stderr[-2000:],observations=len(r.stdout.splitlines())))
 (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(phase,m,r.returncode,r.stderr[-1000:],flush=True)
 if r.returncode:sys.exit(r.returncode)
