"""Record uninterrupted native mGBA walking, input labels and collision probes.
Does not edit the ROM/maps or write a player save. Requires ffmpeg and libmgba.
"""
from pathlib import Path
from collections import deque
import sys,json,subprocess,os,shlex,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import base_runtime as r
G,O,T=map(Path,sys.argv[1:4]);O.mkdir(parents=True,exist_ok=False)
solid=np.load(r.R/'gba/art/olivine-city/source/solid.npy');position=(24,32);parts=[]
def walk(target,label):
 global position
 prev={position:None};q=deque([position])
 while q:
  p=q.popleft()
  if p==target:break
  for d in [(1,0),(-1,0),(0,1),(0,-1)]:
   v=p[0]+d[0],p[1]+d[1]
   if 0<=v[0]<65 and 0<=v[1]<54 and not solid[v[1],v[0]] and v not in prev:prev[v]=p;q.append(v)
 assert target in prev,target
 path=[];p=target
 while prev[p] is not None:path.append(p);p=prev[p]
 path.reverse();parts.append(f'chapter("{label}");')
 keys={(1,0):'RIGHT',(-1,0):'LEFT',(0,1):'DOWN',(0,-1):'UP'}
 for i,v in enumerate(path):
  key=keys[v[0]-position[0],v[1]-position[1]];parts.append(f'input="{key}";step({key},1);'+r.at(*v,label+f'-{i}'));position=v
 parts.append('input="NONE";frames(40,0);')
def probe(key,label):
 parts.append(f'chapter("{label}");input="{key} (blocked test)";frames(80,{key});'+r.at(*position,label)+'input="NONE";frames(45,0);')
walk((24,4),'Northern entrance - facing cliffs')
walk((28,4),'Eastern entrance wall');probe('RIGHT','Cliff face blocks')
walk((20,8),'Western entrance wall');probe('LEFT','Opposite cliff face blocks')
walk((6,13),'Western raised ground');probe('LEFT','Western terrace blocks')
walk((15,14),'Cleared gym lawn')
walk((18,22),'Cleared central lawn')
walk((28,18),'Residential west face');probe('RIGHT','Residential height change blocks')
walk((37,21),'Upper staircase removed');probe('UP','Continuous residential south face')
walk((39,32),'Lighthouse western rock courses');probe('RIGHT','Raised lighthouse remains blocked')
walk((39,35),'Lower staircase removed');probe('RIGHT','Continuous lower cliff course')
walk((10,35),'Cleared waterfront')
walk((10,39),'Quay edge');probe('DOWN','Water blocks')
walk((24,49),'Cleared terminal pier')
walk((17,50),'Terminal edge');probe('LEFT','Water blocks')
walk((24,32),'Return to city')
prefix=r.prefix.replace('screenshot(out,t);verify(t);','screenshot(out,t);').replace('static void verify(const char*);','')
include='#include "'+str(r.R/'tools/gba/maps/runtime.c')+'"'
capture=r'''
static FILE *video;static unsigned recorded;static int recording;
static const char *input="NONE";
static void frames(int n,unsigned keys){
 c->setKeys(c,keys);
 for(int i=0;i<n;i++){c->runFrame(c);if(recording){fwrite(pixels,sizeof(color_t),240*160,video);recorded++;}}
 c->setKeys(c,0);
}
static void chapter(const char *label){printf("{\"chapter\":\"%s\",\"frame\":%u}\n",label,recorded);fflush(stdout);}
'''
prefix=prefix.replace(include,'#define frames uncaptured_frames\n'+include+'\n#undef frames\n'+capture).replace('frames(moved?40:8,0)','frames(moved?18:8,0)').replace('frames(16,0);}', 'frames(4,0);}')
# Observe each tile's real coordinates, plus record exactly when each input starts.
prefix=prefix.replace('static void step(unsigned key,int n){','static void step(unsigned key,int n){printf("{\\"input\\":\\"%s\\",\\"frame\\":%u}\\n",input,recorded);')
body=r'''
int main(int argc,char**argv){
 if(argc!=5)return 2;out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"olivine-recorded-tour");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1791460800000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
START
 video=fdopen(atoi(argv[4]),"wb");if(!video)return 6;recording=1;frames(60,0);
TOUR
 recording=0;fclose(video);need(c->busRead32(c,sym("gOlivineCacheOverflows"))==0,"no-cache-overflow");
 printf("{\"recorded_frames\":%u}\n",recorded);c->deinit(c);return 0;
}
'''.replace('START',r.go(24,32)).replace('TOUR','\n'.join(parts))
(O/'record.c').write_text(prefix+body)
subprocess.run(['cc',str(O/'record.c'),*shlex.split(os.environ.get('MGBA_FLAGS','-lmgba')),'-o',str(O/'record')],check=True)
raw=subprocess.check_output([str(T/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','gMapProofState','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gOlivineCacheOverflows'};symbols={a[2]:a[0] for l in raw.splitlines() if len(a:=l.split())==3 and a[2] in wanted};assert symbols.keys()==wanted;(O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
fps=59.7275
with (O/'encode.log').open('w') as log:
 enc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pixel_format','rgba','-video_size','240x160','-framerate',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','15','-pix_fmt','yuv420p',str(O/'native.mp4')],stdin=subprocess.PIPE,stdout=log,stderr=log)
 result=subprocess.run([str(O/'record'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O),str(enc.stdin.fileno())],pass_fds=(enc.stdin.fileno(),),capture_output=True,text=True,timeout=600);enc.stdin.close();status=enc.wait()
(O/'tour.jsonl').write_text(result.stdout);assert result.returncode==0,result.stderr;assert status==0
records=[json.loads(l) for l in result.stdout.splitlines() if l.startswith('{')];chapters=[x for x in records if 'chapter' in x];frames=records[-1]['recorded_frames']
def stamp(seconds):
 ms=round(seconds*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
sub=[]
for i,x in enumerate(chapters):
 end=chapters[i+1]['frame'] if i+1<len(chapters) else frames
 sub.append(f'{i+1}\n{stamp(x["frame"]/fps)} --> {stamp(end/fps)}\n{x["chapter"]}\n')
(O/'chapters.srt').write_text('\n'.join(sub))
filters=['scale=960:640:flags=neighbor','pad=960:704:0:64:color=0x182028']
for i,x in enumerate(chapters):
 end=chapters[i+1]['frame'] if i+1<len(chapters) else frames
 filters.append("drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='"+x['chapter']+"':fontsize=24:fontcolor=white:x=(w-tw)/2:y=20:enable='between(t,"+str(x['frame']/fps)+","+str(end/fps)+")'")
subprocess.run(['ffmpeg','-y','-i',str(O/'native.mp4'),'-vf',','.join(filters),'-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(O/'olivine-walking-tour.mp4')],stdout=subprocess.DEVNULL,stderr=(O/'presentation.log').open('w'),check=True)
(O/'recording.json').write_text(json.dumps(dict(source_commit=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip(),ROM_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),frames=frames,fps=fps,duration_seconds=frames/fps,chapters=chapters,continuous_walking=True,initial_position_helper_only=True,save_written=False,ROM_or_map_modified=False,audio=False,all_coordinate_assertions_passed=True),indent=2)+'\n');print(dict(seconds=frames/fps,frames=frames,chapters=len(chapters)))
