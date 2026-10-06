// Visit every collision-reachable exterior tile and check its settled game view.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
int main(int argc,char**argv){
 if(argc!=5)return 2;
 FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"boundary-audit");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 char path[2048];snprintf(path,sizeof(path),"%s/boundary-tiles.tsv",argv[3]);f=fopen(path,"r");if(!f)return 6;
 unsigned map,x,y,count=0,failures=0,maxblack=0;
 while(fscanf(f,"%u %u %u",&map,&x,&y)==3){
  call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);
  call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");for(int i=0;i<10;i++)state[i]=c->busRead32(c,a+4*i);
  unsigned black=0,largest=0;unsigned char marked[240*160]={0};int queue[240*160];
  for(int i=0;i<240*160;i++)if(!(pixels[i]&0xffffff))black++;
  for(int i=0;i<240*160;i++)if(!marked[i]&&!(pixels[i]&0xffffff)){
   unsigned head=0,tail=0;queue[tail++]=i;marked[i]=1;
   while(head<tail){int p=queue[head++],near[]={p-240,p+240,p-1,p+1};for(int d=0;d<4;d++){int n=near[d];if(n<0||n>=240*160||(d==2&&p%240==0)||(d==3&&p%240==239)||marked[n]||(pixels[n]&0xffffff))continue;marked[n]=1;queue[tail++]=n;}}
   if(tail>largest)largest=tail;
  }
  if(black>maxblack)maxblack=black;
  unsigned square=0,prev[241]={0};
  for(int yy=0;yy<160;yy++){unsigned row[241]={0};for(int xx=0;xx<240;xx++)if(!(pixels[yy*240+xx]&0xffffff)){unsigned n=row[xx]<prev[xx]?row[xx]:prev[xx];if(prev[xx+1]<n)n=prev[xx+1];row[xx+1]=n+1;if(n+1>square)square=n+1;}memcpy(prev,row,sizeof(prev));}
  const unsigned doors[][2]={{35,17},{43,9},{44,31},{46,19},{53,9},{56,24},{57,31}};int door=0;for(int i=0;i<7;i++)if(map==0&&x==doors[i][0]&&y==doors[i][1])door=1;
  int bad=state[1]!=80||state[2]!=map||state[3]!=x||state[4]!=(y+door)||square>=16;
  printf("{\"map\":%u,\"x\":%u,\"y\":%u,\"actual_map\":%u,\"actual_x\":%u,\"actual_y\":%u,\"black_pixels\":%u,\"largest_black_component\":%u,\"passed\":%s}\n",map,x,y,state[2],state[3],state[4],black,largest,bad?"false":"true");fflush(stdout);
  if(bad || largest>=256 || (map==0&&((x==63&&(y==3||y==16))||(x==59&&y==25)||(x==59&&y==10)||(x==18&&y==18)||(x==50&&y==32)||(x==71&&y==18))) || (map==9&&x==11&&y==18)||(map==10&&x==36&&y==12)){
   char tag[80];snprintf(tag,sizeof(tag),"boundary-%u-%u-%u",map,x,y);screenshot(argv[4],tag);
  }
  failures+=bad;count++;
 }
 fclose(f);fprintf(stderr,"Visited %u tiles; failures %u; maximum black pixels %u\n",count,failures,maxblack);c->deinit(c);return failures?7:0;
}
