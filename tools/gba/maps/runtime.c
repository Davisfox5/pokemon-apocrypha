// Headless mGBA qualification of the isolated ordinary ROM, including cold flash reload.
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static struct mCore *c;
static color_t pixels[240*160];
static char names[128][80];static unsigned addrs[128], ns;
static unsigned sym(const char *name) { for(unsigned i=0;i<ns;i++) if(!strcmp(name,names[i])) return addrs[i]; fprintf(stderr,"missing symbol %s\n",name);exit(20); }
static void wr(const char *n,unsigned v) { if(!c->writeRegister(c,n,&v))exit(21); }
static unsigned rd(const char *n) { unsigned v;if(!c->readRegister(c,n,&v))exit(22);return v; }
static void quiet(struct mLogger*l,int cat,enum mLogLevel level,const char*f,va_list args) { if(level&(mLOG_FATAL|mLOG_ERROR))vfprintf(stderr,f,args); }
static unsigned call(const char *name,unsigned arg) {
 unsigned regs[16], cpsr=rd("cpsr");char rn[8];for(int i=0;i<16;i++){sprintf(rn,"r%d",i);regs[i]=rd(rn);}
 wr("cpsr",0x3f);wr("sp",0x03007c00);wr("r0",arg);wr("lr",0x09ffff01);wr("pc",sym(name)&~1u);
 unsigned result=0;int done=0;
 for(unsigned n=0;n<200000000;n++){unsigned pc=rd("pc");if(pc>=0x09ffff00&&pc<=0x09ffff08){result=rd("r0");done=1;break;}c->step(c);}
 if(!done){fprintf(stderr,"call timeout %s pc=%x\n",name,rd("pc"));exit(23);}
 wr("cpsr",cpsr);for(int i=0;i<15;i++){sprintf(rn,"r%d",i);wr(rn,regs[i]);}wr("pc",regs[15]-((cpsr&32)?2:4));return result;
}
static void frames(int n,unsigned keys){c->setKeys(c,keys);for(int i=0;i<n;i++)c->runFrame(c);c->setKeys(c,0);}
static void screenshot(const char *out,const char *tag){char p[2048];snprintf(p,sizeof(p),"%s/%s.ppm",out,tag);FILE*f=fopen(p,"wb");fprintf(f,"P6\n240 160\n255\n");for(int i=0;i<240*160;i++){unsigned v=pixels[i];fputc(v&255,f);fputc((v>>8)&255,f);fputc((v>>16)&255,f);}fclose(f);}
static unsigned state[10];
static void observe(const char*tag){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");for(int i=0;i<10;i++)state[i]=c->busRead32(c,a+4*i);printf("{\"step\":\"%s\",\"region\":%u,\"group\":%u,\"map\":%u,\"x\":%u,\"y\":%u,\"frlg_layout\":%u,\"width\":%u,\"height\":%u,\"interaction\":%u,\"mapsec\":%u}\n",tag,state[0],state[1],state[2],state[3],state[4],state[5],state[6],state[7],state[8],state[9]);fflush(stdout);}
int main(int argc,char**argv){
 if(argc!=6){fprintf(stderr,"runtime ROM SYMBOLS OUT write|read REGION\n");return 2;}int region=atoi(argv[5]);
 FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 3;mCoreConfigInit(&c->config,"apocrypha-map-proof");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 4;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/region-%d.sav",argv[3],region);
 if(!strcmp(argv[4],"read")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 5;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 6;}
 c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"write")){
  call("MapProof_Boot",0);frames(240,0);observe("new-game");screenshot(argv[3],"new-game");
  if(region){call("MapProof_Enter",region);frames(180,0);}observe("arrived");char tag[80];sprintf(tag,"region-%d",region);screenshot(argv[3],tag);
  if(region==1){frames(48,16);frames(8,0);observe("collision-right");if(state[3]!=11||state[4]!=11)return 30;}
  unsigned expected[]={3,2,1,4,5};if(state[0]!=expected[region]||state[1]!=(unsigned)(75+region))return 31;
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 7;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
  if(region==1){frames(16,128);frames(8,0);frames(256,16);frames(16,0);observe("edge-connection-east");screenshot(argv[3],"connection-east");if(state[1]!=78)return 34;frames(256,32);frames(16,0);observe("edge-connection-west");if(state[1]!=76)return 35;}
  if(region==0){frames(8,64);frames(8,0);frames(1,1);frames(90,0);observe("npc-dialogue");screenshot(argv[3],"npc-dialogue");for(int i=0;i<8;i++){frames(1,1);frames(25,0);}frames(180,0);observe("npc-script-warp");if(state[1]!=76)return 32;}
 }else{unsigned status=call("LoadGameSave",0);printf("{\"load_status\":%u}\n",status);if(status!=1)return 8;call("MapProof_Resume",0);frames(240,0);observe("cold-reload");char tag[80];sprintf(tag,"reload-%d",region);screenshot(argv[3],tag);if(state[1]!=(unsigned)(75+region))return 33;}
 c->deinit(c);return 0;
}
