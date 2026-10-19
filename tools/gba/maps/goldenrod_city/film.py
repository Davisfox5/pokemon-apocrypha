"""Native continuous walking clips; isolated emulator, no save modification."""
from pathlib import Path
import sys,subprocess,os,shlex,hashlib,json
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent));import runtime as r
G,O,T=map(Path,sys.argv[1:4]);O.mkdir(parents=True,exist_ok=False)
prefix=r.prefix.replace('screenshot(out,t);verify(t);','screenshot(out,t);').replace('static void verify(const char*);','')
body=r'''
int main(int argc,char**argv){
 if(argc!=4)return 2;out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"goldenrod-film");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1791460800000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
FILMS
 need(c->busRead32(c,sym("gGoldenrodCacheOverflows"))==0,"continuous-walk-no-overflows");c->deinit(c);return 0;
}
'''
clips=[('avenue-seam',39,28,'RIGHT',128),('railway-underpass',58,30,'UP',240),('southern-arch',58,47,'DOWN',112)];parts=[]
for name,x,y,key,n in clips:
 parts.append(r.go(x,y)+f'for(int i=0;i<{n};i++){{frames(1,{key});if(i%4==0){{char t[80];sprintf(t,"{name}-%03d",i);shot(t);}}}}frames(32,0);observe("{name}-end");')
(O/'film.c').write_text(prefix+body.replace('FILMS','\n'.join(parts)));subprocess.run(['cc',str(O/'film.c'),*shlex.split(os.environ.get('MGBA_FLAGS','-lmgba')),'-o',str(O/'film')],check=True)
raw=subprocess.check_output([str(T/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','gMapProofState','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gGoldenrodCacheOverflows'};symbols={a[2]:a[0] for l in raw.splitlines() if len(a:=l.split())==3 and a[2] in wanted};assert symbols.keys()==wanted;(O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()));result=subprocess.run([str(O/'film'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O)],capture_output=True,text=True,timeout=600);(O/'film.jsonl').write_text(result.stdout);assert result.returncode==0,result.stderr
E=r.R/'gba/art/goldenrod-city/evidence';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15);sheet=Image.new('RGB',(1216,3*204),'#223039');d=ImageDraw.Draw(sheet);report=[]
for row,(name,x,y,key,n) in enumerate(clips):
 files=sorted(O.glob(name+'-*.ppm'));frames=[Image.open(p).convert('RGB') for p in files];assert len(frames)==n//4
 frames[0].save(E/(name+'-walk.gif'),save_all=True,append_images=frames[1:],duration=67,loop=0,disposal=2)
 for col,i in enumerate([0,len(frames)//4,len(frames)//2,len(frames)*3//4,len(frames)-1]):
  xx=col*240+8;yy=row*204;d.text((xx,yy+4),name+' / '+str(i*4)+'f',font=font,fill='white');sheet.paste(frames[i],(xx,yy+28))
 report.append(dict(clip=name,input_frames=n,captured_frames=len(frames),sampling='1/4 native60Hzframes; GIF67ms',save_file_written=False))
sheet.save(E/'walking-contact-sheet.png');(E/'walking-film.json').write_text(json.dumps(dict(ROM_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),exit_code=result.returncode,observations=[json.loads(l) for l in result.stdout.splitlines() if l.startswith('{')],clips=report,cache_overflows=0),indent=2)+'\n');print('Native walking clips',report)
