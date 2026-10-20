"""Compare mid-scroll native BG frames, including ring replacement in both directions."""
from pathlib import Path
import sys,subprocess,os,shlex,hashlib,json
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent));import runtime as r
G,O,T=map(Path,sys.argv[1:4]);O.mkdir(parents=True,exist_ok=False)
prefix=r.prefix+r.extra
body=r'''
int main(int argc,char**argv){
 if(argc!=4)return 2;out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"olivine-film");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1791460800000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
FILMS
 need(c->busRead32(c,sym("gOlivineCacheOverflows"))==0,"continuous-walk-no-overflows");c->deinit(c);return 0;
}
'''
clips=[('dense-west',13,21,'UP',160,'DOWN'),('north-avenue',24,10,'DOWN',256,'UP'),('parasol-row',8,35,'RIGHT',432,'LEFT'),('ramp',38,35,'RIGHT',160,'LEFT')];parts=[]
for name,x,y,key,n,back in clips:
 parts.append(r.go(x,y)+f'shot("{name}-0000");')
 for leg,k in enumerate([key,back]):
  parts.append(f'for(int i=0;i<{n};i++){{frames(1,{k});if(i%2==1){{char t[80];sprintf(t,"{name}-%04d",{leg*n}+i+1);shot(t);}}}}')
 parts.append('frames(32,0);')
(O/'film.c').write_text(prefix+body.replace('FILMS','\n'.join(parts)));subprocess.run(['cc',str(O/'film.c'),*shlex.split(os.environ.get('MGBA_FLAGS','-lmgba')),'-o',str(O/'film')],check=True)
raw=subprocess.check_output([str(T/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);wanted={'sGpuRegBuffer','gGoldenrodCacheOverflows','MapProof_Boot','MapProof_Enter','MapProof_ReadState','gMapProofState','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gOlivineCacheOverflows'};symbols={a[2]:a[0] for l in raw.splitlines() if len(a:=l.split())==3 and a[2] in wanted};assert symbols.keys()==wanted;(O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()));result=subprocess.run([str(O/'film'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O)],capture_output=True,text=True,timeout=600);(O/'film.jsonl').write_text(result.stdout);assert result.returncode==0,result.stderr

import ast,numpy as np
p=r.R/'tools/gba/maps/olivine_city/verify_frames.py';tree=ast.parse(p.read_text());fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='decode');scope=dict(np=np);exec(compile(ast.Module(body=[fun],type_ignores=[]),'decode','exec'),scope);decode=scope['decode']
native=np.array(Image.open(r.R/'gba/art/olivine-city/evidence/native-map.png').convert('RGB'));results=[]
H,W=54,65;top=np.zeros((864,1040),bool)
def border_cell(x,y):
 if x<0:
  if y<28:return x%2,y%2+2
  if y<34:return 0,31
  return 2+x%2,42+y%2
 if y<0:return 2+x%2,2+y%2
 if x>=65 or y>=54:return 2+x%2,42+y%2
 return x,y
pad=20*16;padded=np.zeros((native.shape[0]+pad*2,native.shape[1]+pad*2,3),np.uint8);padded_top=np.zeros(padded.shape[:2],bool)
for y in range(-20,H+20):
 for x in range(-20,W+20):
  cx,cy=border_cell(x,y);py,px=y*16+pad,x*16+pad;padded[py:py+16,px:px+16]=native[cy*16:cy*16+16,cx*16:cx*16+16];padded_top[py:py+16,px:px+16]=top[cy*16:cy*16+16,cx*16:cx*16+16]

for name,x,y,*_ in clips:
 px=x*16-112;py=y*16-72;frames=0
 for p in sorted(O.glob(name+'-*.vram')):
  now=decode(p);found=None
  offsets=[(0,0)]+[(dx,dy) for dy in range(-4,5) for dx in range(-4,5) if dx or dy]
  for dx,dy in offsets:
   xx=px+dx;yy=py+dy
   want=padded[yy+pad:yy+pad+160,xx+pad:xx+pad+240]
   if not np.array_equal(now[40:120:8,40:200:8],want[40:120:8,40:200:8]):continue
   if np.array_equal(now,want):found=(xx,yy);break
  assert found is not None,(name,p.name,'mid-scroll RGB mismatch')
  px,py=found;frames+=1
 results.append(dict(clip=name,frames=frames,pixels=frames*38400,RGB_errors=0))
report=dict(ROM_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),cache_overflows=0,sampling='Every second native frame during held input; each decoded BG must exactly match a contiguous native-world window within four pixels of previous sample.',clips=results)
(r.R/'gba/art/olivine-city/evidence/interaction-audit/scrolling-runtime.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
