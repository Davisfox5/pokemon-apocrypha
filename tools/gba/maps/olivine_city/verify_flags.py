"""Pixel-check real sprite/flag overlaps, not just sprite-free background parity."""
from pathlib import Path
import sys,subprocess,os,shlex,json
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent));import runtime as r
G,O,T=map(Path,sys.argv[1:4]);O.mkdir(parents=True,exist_ok=False)
prefix=r.prefix.replace('screenshot(out,t);verify(t);','screenshot(out,t);').replace('static void verify(const char*);','')
poses=[('central',24,25),('west',10,18),('west-right',14,18),('west-pennant',13,18)];parts=[r.go(x,y)+f'shot("{n}");' for n,x,y in poses]
body=r'''
int main(int argc,char**argv){
 if(argc!=4)return 2;out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"olivine-flags-proof");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1791460800000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
POSES
 need(c->busRead32(c,sym("gOlivineCacheOverflows"))==0,"no-overflow");c->deinit(c);return 0;
}
'''.replace('POSES','\n'.join(parts));(O/'proof.c').write_text(prefix+body)
subprocess.run(['cc',str(O/'proof.c'),*shlex.split(os.environ.get('MGBA_FLAGS','-lmgba')),'-o',str(O/'proof')],check=True)
wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','gMapProofState','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gOlivineCacheOverflows'};raw=subprocess.check_output([str(T/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);symbols={a[2]:a[0] for l in raw.splitlines() if len(a:=l.split())==3 and a[2] in wanted};assert symbols.keys()==wanted;(O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
subprocess.run([str(O/'proof'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O)],check=True,timeout=60)
S=r.R/'gba/art/olivine-city/source';E=S.parent/'evidence/flag-alpha-cleanup';mask=np.array(Image.open(S/'flag-foreground-mask.png'))>0;native=np.array(Image.open(S.parent/'evidence/native-map.png'));results=[]
previous_mask=np.array(Image.open(E/'previous-mask.png'))>0;cleared=previous_mask&~mask
for name,x,y in poses:
 im=Image.open(O/(name+'.ppm')).convert('RGB');a=np.array(im)&248;xx=x*16-112;yy=y*16-72;target=native[yy:yy+160,xx:xx+240];m=mask[yy:yy+160,xx:xx+240];errors=int(np.any(a[m]!=target[m],1).sum());assert errors==0,(name,errors)
 sprite=np.any(a!=target,2);assert sprite.sum()>0,'Player must remain visible outside flag silhouette'
 # Visible player pixels must reach the flag's edge, proving the pose overlaps
 # the cutout rather than merely standing elsewhere in the screenshot.
 near=np.zeros_like(m);near[1:]|=m[:-1];near[:-1]|=m[1:];near[:,1:]|=m[:,:-1];near[:,:-1]|=m[:,1:];assert np.any(sprite&near)
 cleared_pixels=cleared[yy:yy+160,xx:xx+240];visible_through_cleared=int((sprite&cleared_pixels).sum());assert visible_through_cleared>0,(name,'Player must show through removed background')
 im.save(E/(name+'-underpass.png'));results.append(dict(span=name,world=[x,y],foreground_pixels=int(m.sum()),foreground_RGB_errors=errors,visible_player_pixels=int(sprite.sum()),sprite_touches_flag_edge=True,player_pixels_through_cleared_background=visible_through_cleared))
(E/'sprite-occlusion.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
