#define main unused_map_qualification_main
#include "runtime.c"
#undef main
#include "cherrygrove_art_study_probes.h"
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void expect(unsigned map,const char *tag){observe(tag);if(state[1]!=80||state[2]!=map){fprintf(stderr,"wrong map at %s\n",tag);exit(40);}}
int main(int argc,char **argv){
 if(argc!=5)return 2;FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 3;mCoreConfigInit(&c->config,"cherrygrove-art-study");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 4;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/town.sav",argv[3]);
 if(strcmp(argv[4],"write")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 5;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 6;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1790784000000LL;c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"read")){if(call("LoadGameSave",0)!=1)return 7;call("MapProof_Resume",0);frames(300,0);expect(0,"cold-save-reload");if(state[3]!=40||state[4]!=21)return 8;screenshot(argv[3],"cold-reload");}
 else if(!strcmp(argv[4],"menu")){frames(1,8);frames(180,0);frames(1,1);frames(300,0);frames(1,1);frames(180,0);frames(1,1);frames(300,0);expect(0,"ordinary-title-continue");if(state[3]!=40||state[4]!=21)return 9;screenshot(argv[3],"ordinary-continue");}
 else{
  call("MapProof_Boot",0);frames(300,0);expect(0,"new-game");screenshot(argv[3],"new-game");
  const unsigned doors[][3]={{34,17,1},{42,19,2},{48,22,3},{40,26,11},{49,27,12},{40,12,5},{46,12,6}};
  const unsigned exits[][2]={{9,8},{3,8},{3,8},{3,8},{3,8},{3,7},{7,8}};
  for(unsigned i=0;i<7;i++){
   go(0,doors[i][0],doors[i][1]+1);frames(20,64);frames(240,0);char tag[80];sprintf(tag,"door-in-%u",doors[i][2]);expect(doors[i][2],tag);screenshot(argv[3],tag);
   go(doors[i][2],exits[i][0],exits[i][1]-1);frames(20,128);frames(240,0);sprintf(tag,"door-return-%u",doors[i][2]);expect(0,tag);
  }
  go(0,36,7);frames(48,64);frames(240,0);expect(10,"north-route");frames(48,128);frames(240,0);expect(0,"north-route-return");
  go(0,56,18);frames(48,16);frames(240,0);expect(9,"east-route");frames(48,32);frames(240,0);expect(0,"east-route-return");
  go(0,23,20);frames(16,128);frames(20,0);expect(0,"island-walk");if(state[4]<=20)return 10;screenshot(argv[3],"island");
  go(0,24,22);frames(60,128);frames(20,0);observe("island-water-edge");if(state[4]>22)return 11;
  const unsigned views[][2]={{40,14},{38,20},{47,25},{23,18},{50,13},{36,26}};const char*tags[]={"center-mart","houses","southeast","harbor","pond","forest"};
  for(unsigned i=0;i<6;i++){
   go(0,views[i][0],views[i][1]);screenshot(argv[3],tags[i]);
   for(unsigned tick=0;tick<120;tick++){
    frames(8,0);printf("{\"view\":%u,\"tick\":%u,\"npcs\":[",i,tick);int comma=0;
    for(unsigned j=0;j<16;j++){unsigned o=sym("gObjectEvents")+j*0x24;if(!(c->busRead8(c,o)&1)||c->busRead16(c,o+4)<1024)continue;
     printf("%s[%u,%d,%d]",comma++?",":"",c->busRead16(c,o+4),(short)c->busRead16(c,o+0x10)-7,(short)c->busRead16(c,o+0x12)-7);}
    printf("]}\n");if(i==1&&tick%3==0){char tag[80];sprintf(tag,"walking-%03u",tick);screenshot(argv[3],tag);}
   }
  }
  for(unsigned i=0;i<sizeof(studyProbes)/sizeof(studyProbes[0]);i++){
   const unsigned *p=studyProbes[i];go(0,p[0],p[1]);frames(24,p[2]);frames(80,0);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");unsigned x=c->busRead32(c,a+12),y=c->busRead32(c,a+16);
   printf("{\"probe\":%u,\"x\":%u,\"y\":%u,\"expected_x\":%u,\"expected_y\":%u}\n",i,x,y,p[3],p[4]);if(((x!=p[0]||y!=p[1])!= (p[3]!=p[0]||p[4]!=p[1]))){fprintf(stderr,"movement probe %u failed\n",i);return 14;}
  }
  go(0,40,21);expect(0,"save-position");unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 12;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
