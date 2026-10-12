// Headless qualification. UI actions are ordinary buttons. Named service calls
// below are explicit fixtures for future authored card/call/gift events, not
// evidence those events already exist in the opening chapter.
#define main unused_qualification_main
#include "runtime.c"
#undef main
static const char *romPath,*outPath;
static void tap(unsigned k){frames(3,k);frames(70,0);}
static unsigned invoke(const char *name,unsigned a,unsigned b,unsigned d,unsigned e){
 unsigned regs[16],cpsr=rd("cpsr");char rn[8];for(int i=0;i<16;i++){sprintf(rn,"r%d",i);regs[i]=rd(rn);}
 wr("cpsr",0x3f);wr("sp",0x03007c00);wr("r0",a);wr("r1",b);wr("r2",d);wr("r3",e);wr("lr",0x09ffff01);wr("pc",sym(name)&~1u);
 unsigned result=0,done=0;for(unsigned n=0;n<2000000;n++){unsigned pc=rd("pc");if(pc>=0x09ffff00&&pc<=0x09ffff08){result=rd("r0");done=1;break;}c->step(c);}if(!done)exit(31);
 wr("cpsr",cpsr);for(int i=0;i<15;i++){sprintf(rn,"r%d",i);wr(rn,regs[i]);}wr("pc",regs[15]-((cpsr&32)?2:4));return result;
}
static unsigned gear(void){return c->busRead32(c,sym("gSaveBlock3Ptr"))+4;}
static unsigned byte(const char*n){return c->busRead8(c,sym(n));}
#define CHECK(x) do{if(!(x)){fprintf(stderr,"failed line %d: %s\n",__LINE__,#x);exit(40);}printf("{\"check\":\"%s\",\"pass\":true}\n",#x);}while(0)
static void boot(const void*data,size_t size){
 c=mCoreFind(romPath);CHECK(c&&c->init(c));mCoreConfigInit(&c->config,"apoc-gear-services");c->setVideoBuffer(c,pixels,240);CHECK(mCoreLoadFile(c,romPath));CHECK(c->savedataRestore(c,data,size,false));c->reset(c);frames(600,0);
 int arrived=0;for(int i=0;i<100;i++){tap(1);if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld")&&!call("ArePlayerFieldControlsLocked",0)){arrived=1;break;}}CHECK(arrived);
}
static void opengear(void){tap(8);while(c->busRead8(c,sym("sStartMenuCursorPos")))tap(64);tap(128);tap(1);frames(180,0);}
static void app(unsigned a){for(int i=0;i<5&&byte("sApp")!=a;i++)tap(256);CHECK(byte("sApp")==a);}
static void savecold(void){
 tap(2);tap(2);frames(180,0);tap(8);while(c->busRead8(c,sym("sStartMenuCursorPos")))tap(64);tap(128);tap(128);tap(1);for(int i=0;i<20;i++)tap(1);for(int i=0;i<8&&call("ArePlayerFieldControlsLocked",0);i++)tap(2);
 void*data=NULL;size_t size=c->savedataClone(c,&data);CHECK(size==131072);char path[2048];snprintf(path,sizeof(path),"%s/services-save.sav",outPath);FILE*f=fopen(path,"wb");CHECK(f&&fwrite(data,1,size,f)==size);fclose(f);c->deinit(c);boot(data,size);free(data);opengear();
}
int main(int argc,char**argv){
 if(argc!=5)return 2;romPath=argv[1];outPath=argv[4];FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);unsigned char data[131072];f=fopen(argv[3],"rb");CHECK(f&&fread(data,1,sizeof(data),f)==sizeof(data));fclose(f);struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);boot(data,sizeof(data));
 CHECK(call("VarGet",0x40F7)==4);CHECK(call("FlagGet",0x20));CHECK(call("CountTotalItemQuantityInBag",28)==1);
 opengear();CHECK(c->busRead32(c,gear())==0x41504731);CHECK(!(c->busRead8(c,gear()+12)&1));CHECK(c->busRead8(c,gear()+16)&1);
 app(2);screenshot(outPath,"map-card-locked");
 // Explicit card fixture; the world art and regional crops are inspected at native size.
 call("ApocGear_GiveMapCard",0);tap(16);CHECK(byte("sMapRegion")==6);screenshot(outPath,"map-world-overview");tap(1);CHECK(byte("sZoom")==1);screenshot(outPath,"map-world-detail");tap(1);tap(8);CHECK(byte("sMapRegion")==1);screenshot(outPath,"map-region-1");tap(8);CHECK(byte("sMapRegion")==2);screenshot(outPath,"map-johto-overview");tap(1);CHECK(byte("sZoom")==1);screenshot(outPath,"map-johto-detail");tap(16);tap(128);tap(4);CHECK(byte("sNoteMode")==1);tap(1);unsigned nx=byte("sMapX"),ny=byte("sMapY");CHECK(invoke("ApocGear_GetNote",2,nx,ny,0)==1);tap(2);screenshot(outPath,"map-note");
 for(int i=0;i<4;i++){tap(8);char tag[50];sprintf(tag,"map-region-%u",byte("sMapRegion"));screenshot(outPath,tag);}CHECK(byte("sMapRegion")==6);tap(8);CHECK(byte("sMapRegion")==1);
 app(3);tap(8);CHECK(c->busRead8(c,gear()+16)&2);tap(1);CHECK(byte("sCall")==1);tap(8);CHECK(c->busRead8(c,gear()+15)==10);screenshot(outPath,"phone-connected");tap(2);tap(4);CHECK(byte("sPhoneHistory"));screenshot(outPath,"phone-history");tap(2);
 // Queue and one-time gift service fixture, only against registered Mom.
 CHECK(!call("ApocGear_QueueCall",74));CHECK(call("ApocGear_QueueCall",0));frames(100,0);screenshot(outPath,"phone-incoming");tap(1);CHECK(c->busRead8(c,gear()+14)==255);tap(2);
 CHECK(invoke("ApocGear_SetGift",0,28,0,0));CHECK(!invoke("ApocGear_SetGift",0,28,0,0));frames(140,0);tap(1);CHECK(byte("sCall"));screenshot(outPath,"phone-gift-before");printf("gift_before call=%u row=%u flags=%u item=%u qty=%u\n",byte("sCall"),byte("sPhoneHistory"),c->busRead8(c,gear()+16),c->busRead16(c,gear()+632),call("CountTotalItemQuantityInBag",28));tap(4);screenshot(outPath,"phone-gift-after");printf("gift_after call=%u flags=%u item=%u qty=%u\n",byte("sCall"),c->busRead8(c,gear()+16),c->busRead16(c,gear()+632),call("CountTotalItemQuantityInBag",28));CHECK(call("CountTotalItemQuantityInBag",28)==2);CHECK(!call("ApocGear_ClaimGift",0));tap(2);
 app(1);tap(64);tap(1); // select preset zero after old save's preset one
 printf("tune=%u preset0=%u preset23=%u\n",call("VarGet",0x40F9),call("VarGet",0x40FA),call("VarGet",0x40FB));CHECK((call("VarGet",0x40F9)&127)==17);tap(32);tap(4);CHECK(byte("sRadioText"));screenshot(outPath,"radio-live-report");tap(2);
 tap(128);tap(1);tap(4);screenshot(outPath,"radio-daily-music");tap(2);
 tap(128);tap(1);tap(4);screenshot(outPath,"radio-variety");tap(2);
 tap(128);tap(1);tap(4);screenshot(outPath,"radio-password");unsigned password=(c->busRead16(c,sym("gLocalTime"))+call("GetDayOfWeek",0))%4;while(byte("sQuizChoice")!=password)tap(16);tap(1);CHECK(c->busRead8(c,gear()+932)==1);screenshot(outPath,"radio-password-complete");tap(2);
 savecold();CHECK(c->busRead8(c,gear()+12)&1);CHECK(c->busRead8(c,gear()+16)&2);CHECK(invoke("ApocGear_GetNote",2,nx,ny,0)==1);CHECK(c->busRead8(c,gear()+932)==1);CHECK(call("CountTotalItemQuantityInBag",28)==2);CHECK(c->busRead8(c,gear()+13)>=3);screenshot(outPath,"cold-continue-services");
 tap(2);tap(2);frames(180,0);
 for(int i=0;i<4;i++){frames(32,16);frames(20,0);frames(32,32);frames(20,0);frames(32,128);frames(20,0);frames(32,64);frames(20,0);}
 CHECK(c->busRead8(c,gear()+15)==0);CHECK(c->busRead8(c,gear()+14)==0);frames(300,0);for(int i=0;i<8&&call("ArePlayerFieldControlsLocked",0);i++)tap(2);opengear();screenshot(outPath,"callback-open-debug");printf("callback app=%u call=%u cb=%x locked=%u\n",byte("sApp"),byte("sCall"),c->busRead32(c,sym("gMain")+4),call("ArePlayerFieldControlsLocked",0));app(3);screenshot(outPath,"phone-callback-after-walking");tap(2);tap(2);frames(100,0);opengear();app(3);CHECK(c->busRead8(c,gear()+16)&4);screenshot(outPath,"phone-missed-call");
 // Corruption fixture affects only the new record; ordinary save/house state survives.
 c->busWrite8(c,gear()+400,c->busRead8(c,gear()+400)^1);call("ApocGear_EnsureState",0);CHECK(call("VarGet",0x40F7)==4);CHECK(call("FlagGet",0x20));CHECK(call("CountTotalItemQuantityInBag",28)==2);CHECK(c->busRead32(c,gear())==0x41504731);
 CHECK(c->busRead8(c,gear()+933)==1);frames(140,0);screenshot(outPath,"gear-corruption-recovery");tap(1);CHECK(!c->busRead8(c,gear()+933));
 for(unsigned i=0;i<100;i++)CHECK(invoke("ApocGear_SetNote",2,i*2,20,1));
 CHECK(!invoke("ApocGear_SetNote",2,1,21,1));CHECK(invoke("ApocGear_SetNote",2,0,20,0));CHECK(invoke("ApocGear_SetNote",2,1,21,1));
 for(unsigned i=1;i<75;i++)CHECK(call("ApocGear_Register",i));CHECK(!call("ApocGear_Register",75));CHECK(!invoke("ApocGear_SetNote",6,1,1,1));
 c->deinit(c);return 0;
}
