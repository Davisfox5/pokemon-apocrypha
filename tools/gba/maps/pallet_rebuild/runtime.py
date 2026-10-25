#!/usr/bin/env python3
"""Instrumented mGBA walking/transition/save checks on the ordinary compiled ROM.
No savestates, no production entrypoint changes. MGBA_FLAGS can select local libmgba.
"""
from pathlib import Path
import json,os,shlex,subprocess,sys,struct
from collections import deque
from PIL import Image
from native import words
ROOT=Path(__file__).resolve().parents[4]
E=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve();OUT.mkdir(parents=True,exist_ok=True)
NAMES=['ApocPalletTown','ApocPalletRedHouse1F','ApocPalletRedHouse2F','ApocPalletOakHouse','ApocPalletLab']
LS=json.loads((E/'data/layouts/layouts.json').read_text())['layouts'];MS={43+i:json.loads((E/f'data/maps/{n}/map.json').read_text()) for i,n in enumerate(NAMES)}
GR={};DIMS={}
for i,m in MS.items():
 l=next(l for l in LS if l['id']==m['layout']);GR[i]=words(E/l['blockdata_filepath']);DIMS[i]=(l['width'],l['height'])
KEY={(1,0):16,(-1,0):32,(0,-1):64,(0,1):128}
def grid(i,p):
 x,y=p;w,h=DIMS[i];return GR[i][y*w+x] if 0<=x<w and 0<=y<h else 0x3fff
def route(i,a,b):
 if i==43:a=(a[0],a[1]+1);b=(b[0],b[1]+1)
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
# Continuous on-foot tours per floor, with both directions of every actual building/stair transition.
tour='go(43,12,10);shot("town-center");\n'+route(43,(12,10),(12,0))+'\nshot("north-route-socket");\n'+route(43,(12,0),(6,8))+'''\nstep(64);needmap(44,"red-home-enter");shot("red-home-enter");\n'''
# Expected entry square is checked at runtime; start planning from native door destination (4,7).
tour+='at(44,4,8,"red-home-arrival");step(64);at(44,4,7,"red-home-approach");\n'+route(44,(4,7),(9,2))+'''\nstep(16);at(44,10,2,"stairs-visible-entrance");step(16);needmap(45,"red-stairs-up");shot("red-bedroom");\n'''
# The stair lands at (10,2). Move away, then return over the actual stair.
tour+='at(45,10,2,"bedroom-arrival");step(128);at(45,10,3,"stairs-step-away");\n'+route(45,(10,3),(2,7))+'\nshot("bedroom-south");\n'+route(45,(2,7),(10,3))+'''\nstep(64);at(45,10,2,"downstairs-visible-entrance");step(32);needmap(44,"red-stairs-down");shot("red-stairs-down");\n'''
# Follow-up route starts at actual 1F stair destination (10,2), using leftwards approach.
tour+='at(44,10,2,"stairs-down-arrival");step(32);at(44,9,2,"stairs-away");\n'+route(44,(9,2),(4,7))+'''\nstep(128);at(44,4,8,"red-exit-mat");step(128);needmap(43,"red-home-exit");at(43,6,8,"red-return");shot("red-home-exit");\n'''
tour+=route(43,(6,8),(15,8))+'''\nstep(64);needmap(46,"oak-home-enter");at(46,4,8,"oak-home-arrival");step(64);at(46,4,7,"oak-home-approach");shot("oak-home");\n'''+route(46,(4,7),(8,7))+'''\ninteract(64,"oak-dialogue");\n'''+route(46,(8,7),(4,7))+'''\nstep(128);at(46,4,8,"oak-exit-mat");step(128);needmap(43,"oak-home-exit");at(43,15,8,"oak-return");\n'''
tour+=route(43,(15,8),(16,14))+'''\nstep(64);needmap(47,"lab-enter");at(47,6,12,"lab-arrival");step(64);at(47,6,11,"lab-approach");shot("lab-enter");\n'''+route(47,(6,11),(6,5))+'''\ninteract(64,"blue-dialogue");\nshot("lab-research");\n'''+route(47,(6,5),(6,11))+'''\nstep(128);at(47,6,12,"lab-exit-mat");step(128);needmap(43,"lab-exit");at(43,16,14,"lab-return");shot("lab-exit");\n'''
tour+=route(43,(16,14),(5,15))+'''\ninteract(64,"red-memorial");\n'''+route(43,(5,15),(8,16))+'''\nshot("shore-approach");\n'''
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
static void dump_art(unsigned map){char path[2048];sprintf(path,"%s/vram-%u.bin",out,map);FILE*f=fopen(path,"wb");for(unsigned i=0;i<32768;i++)fputc(c->busRead8(c,0x06000000+i),f);fclose(f);sprintf(path,"%s/palette-%u.bin",out,map);f=fopen(path,"wb");for(unsigned i=0;i<416;i++)fputc(c->busRead8(c,0x05000000+i),f);fclose(f);}
static int anim(unsigned t){return t==54||t==55||t==56||t==57||t==58||t==59||t==60||t==61||t==837||t==840||t==841||t==843||t==852||t==853||t==854||t==855;}
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
    unsigned x=i==0?6:i==1?15:16,y=i==2?15:9;go(43,x,y);
    for(unsigned t=0;t<40;t++){frames(2,t<12?64:0);if(t%2==0){char tag[50];sprintf(tag,"door-%u-frame-%02u",i,t);screenshot(out,tag);}}
    frames(240,0);needmap(i==0?44:i==1?46:47,"animated-door-arrival");
   }
  }
  else if(!strcmp(phase,"water")){
   go(43,8,16);step(128);at(43,8,16,"water-blocks-foot");
   go(43,8,18);call("SetPlayerAvatarTransitionFlags",8);frames(30,0);step(16);at(43,9,18,"surf-east");step(32);at(43,8,18,"surf-west");step(32);at(43,7,18,"surf-west-shore");step(32);at(43,6,18,"surf-dismounts-onto-lawn");need(call("TestPlayerAvatarFlags",1)&&!call("TestPlayerAvatarFlags",8),"dismounted-on-foot");shot("surf-shore");
   go(43,8,16);call("SetPlayerAvatarTransitionFlags",1);frames(30,0);unsigned stable=hash(0),water=hash(1);
   frames(8,0);need(hash(0)==stable&&hash(1)!=water,"only-water-animates");shot("hgss-water-next-phase");frames(56,0);need(hash(0)==stable&&hash(1)==water,"water-loop-is-seamless");shot("hgss-water-full-loop");printf("{\"frames\":64,\"hgss_water\":\"animated\",\"nonwater_vram_unchanged\":true}\n");
  }
  unsigned sx=map==43?12:map==45?2:6,sy=map==43?11:map==45?7:map==47?11:7;go(map,sx,sy);at(map,sx,sy,"save-spot");
  char tag[40];sprintf(tag,"save-map-%u",map);shot(tag);dump_art(map);unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");need(status==1&&size==131072&&f&&fwrite(data,1,size,f)==size,"ordinary-save");fclose(f);free(data);printf("{\"save_map\":%u,\"flash_bytes\":%zu,\"status\":%u}\n",map,size,status);
 }
 c->deinit(c);return 0;
}
'''

# Every explicit go/at in the retained generic fixture uses original exterior coordinates.
# route() already emits native coordinates and is protected until substitution.
import re
pattern=r'(go|at)\(43,(\d+),(\d+)'
def shift(m):return f'{m[1]}(43,{m[2]},{int(m[3])+1}'
TEMPLATE=re.sub(pattern,shift,TEMPLATE)
# Explicit tour strings need the same translation, while route walk observations are already native.
tour=';'.join(stmt if '"walk"' in stmt else re.sub(pattern,shift,stmt) for stmt in tour.split(';'))
src=TEMPLATE.replace('COMMON',str(ROOT/'tools/gba/maps/runtime.c')).replace('TOUR',tour).replace('BLOCKS','\n'.join(blocks)).replace('BLOCKCOUNT',str(len(blocks)))
(OUT/'runtime.c').write_text(src)
import hashlib
(OUT/'input-identity.json').write_text(json.dumps(dict(
 source_commit=subprocess.check_output(['git','-C',str(E),'rev-parse','HEAD'],text=True).strip(),
 rom_sha256=hashlib.sha256((E/'pokeemerald.gba').read_bytes()).hexdigest(),
 elf_sha256=hashlib.sha256((E/'pokeemerald.elf').read_bytes()).hexdigest(),
 fixture_sha256=hashlib.sha256(src.encode()).hexdigest()),indent=2)+'\n')
flags=shlex.split(os.environ.get('MGBA_FLAGS','-lmgba'));subprocess.run(['cc','-O1',str(OUT/'runtime.c'),*flags,'-o',str(OUT/'runtime')],check=True)
nm=subprocess.check_output(['arm-none-eabi-nm',str(E/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','TrySavingData','LoadGameSave','ArePlayerFieldControlsLocked','SetPlayerAvatarTransitionFlags','TestPlayerAvatarFlags'}
symbols={s[2]:s[0] for l in nm.splitlines() if len(s:=l.split())==3 and s[2] in wanted};assert symbols.keys()==wanted
(OUT/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
results=[]
phases=[('tour',43),('doors',43),('blocks',43),('water',43)]+[(p,m) for m in range(43,48) for p in ['write','read','menu']]
if len(sys.argv)>3:phases=[(sys.argv[3],int(sys.argv[4]) if len(sys.argv)>4 else 43)]
for phase,m in phases:
 r=subprocess.run([str(OUT/'runtime'),str(E/'pokeemerald.gba'),str(OUT/'symbols.txt'),str(OUT),phase,str(m)],capture_output=True,text=True,timeout=2400)
 (OUT/f'{phase}-{m}.jsonl').write_text(r.stdout);(OUT/f'{phase}-{m}.stderr').write_text(r.stderr)
 for f in OUT.glob('*.ppm'):Image.open(f).save(OUT/f'{phase}-{m}-{f.stem}.png');f.unlink()
 results.append(dict(phase=phase,map=m,exit_code=r.returncode,stderr=r.stderr[-2000:],observations=len(r.stdout.splitlines())))
 (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(phase,m,r.returncode,r.stderr[-1000:],flush=True)
 if r.returncode:sys.exit(r.returncode)
