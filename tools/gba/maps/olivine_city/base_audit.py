"""Exhaustive native walking edges and sprite-layer compositing at every open cell.
All ordinary city walking is continuous after one starting placement. A separate
initial placement qualifies each raised surface isolated by the removed stairs.
Diagnostic OBJ-only frames are never presented as normal gameplay footage.
"""
from pathlib import Path
from collections import deque
import sys,json,subprocess,os,shlex,ast,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import base_runtime as r
G,O,T=map(Path,sys.argv[1:4]);O.mkdir(parents=True,exist_ok=False);S=r.R/'gba/art/olivine-city/source';E=S.parent/'evidence/base-terrain'
solid=np.load(S/'solid.npy');H,W=solid.shape;directions=[(1,0,'RIGHT'),(0,1,'DOWN'),(-1,0,'LEFT'),(0,-1,'UP')];keys={(dx,dy):key for dx,dy,key in directions};opposite={'RIGHT':'LEFT','LEFT':'RIGHT','UP':'DOWN','DOWN':'UP'};seen=set();tested=set();parts=[];components=[];poses=[];sys.setrecursionlimit(20000)
def move(a,b,key,label):
 parts.append(f'step({key},1);'+r.at(*b,label));tested.add((a[0],a[1],key))
def dfs(p,parent=None):
 seen.add(p);poses.append(p);parts.append(f'inspect("cell-{p[0]:02}-{p[1]:02}");')
 for dx,dy,key in directions:
  q=p[0]+dx,p[1]+dy
  if q==parent:continue
  valid=0<=q[0]<W and 0<=q[1]<H and not solid[q[1],q[0]]
  if not valid:
   move(p,p,key,f'blocked-{p[0]}-{p[1]}-{key}');continue
  if q not in seen:
   move(p,q,key,f'walk-{q[0]}-{q[1]}');dfs(q,p);move(q,p,opposite[key],f'return-{p[0]}-{p[1]}')
  elif (p[0],p[1],key) not in tested:
   move(p,q,key,f'edge-{q[0]}-{q[1]}');move(q,p,opposite[key],f'edge-return-{p[0]}-{p[1]}')
starts=[(24,32)]+[(int(x),int(y)) for y,x in np.argwhere(~solid) if (int(x),int(y))!=(24,32)]
for start in starts:
 if start in seen:continue
 before=len(seen);parts.append(r.go(*start));dfs(start);components.append(dict(start=list(start),cells=len(seen)-before,ordinary_reachable=start==(24,32)))
assert len(seen)==int((~solid).sum());assert len(tested)==len(seen)*4
prefix=r.prefix.replace('frames(moved?40:8,0)','frames(moved?18:8,0)').replace('frames(16,0);}','frames(4,0);}')
extra=r.extra+r'''
static void inspect(const char *tag){
 shot(tag);
 char path[2048];snprintf(path,sizeof(path),"%s/%s.objects",out,tag);FILE *f=fopen(path,"wb");
 for(unsigned a=0x7000000;a<0x7000400;a++)fputc(c->busRead8(c,a),f);
 for(unsigned a=0x6010000;a<0x6018000;a++)fputc(c->busRead8(c,a),f);
 for(unsigned a=0x5000200;a<0x5000400;a++)fputc(c->busRead8(c,a),f);
 for(unsigned a=0x50;a<0x56;a++)fputc(c->busRead8(c,sym("sGpuRegBuffer")+a),f);
 unsigned control=c->busRead16(c,0x4000000);fputc(control,f);fputc(control>>8,f);fclose(f);
 unsigned dc=c->busRead16(c,0x4000000),pal=c->busRead16(c,0x5000000),faded=c->busRead16(c,sym("gPlttBufferFaded")),unfaded=c->busRead16(c,sym("gPlttBufferUnfaded"));
 c->busWrite16(c,sym("gPlttBufferFaded"),0x7c1f);c->busWrite16(c,sym("gPlttBufferUnfaded"),0x7c1f);
 c->busWrite16(c,0x5000000,0x7c1f);c->busWrite16(c,0x4000000,dc&~0x0f00);frames(2,0);
 need((c->busRead16(c,0x4000000)&0x0f00)==0,"diagnostic-backgrounds-disabled");
 char name[100];sprintf(name,"%s-objects",tag);screenshot(out,name);
 need(c->busRead16(c,0x5000000)==0x7c1f,"diagnostic-magenta-backdrop");
 c->busWrite16(c,sym("gPlttBufferFaded"),faded);c->busWrite16(c,sym("gPlttBufferUnfaded"),unfaded);c->busWrite16(c,0x5000000,pal);c->busWrite16(c,0x4000000,dc);frames(2,0);
}
'''
body=r'''
int main(int argc,char**argv){
 if(argc!=4)return 2;out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"olivine-every-cell-audit");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1791460800000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
TESTS
 need(c->busRead32(c,sym("gOlivineCacheOverflows"))==0,"no-cache-overflow");c->deinit(c);return 0;
}
'''.replace('TESTS','\n'.join(parts));(O/'audit.c').write_text(prefix+extra+body)
subprocess.run(['cc',str(O/'audit.c'),*shlex.split(os.environ.get('MGBA_FLAGS','-lmgba')),'-o',str(O/'audit')],check=True)
wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','gMapProofState','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gOlivineCacheOverflows','gGoldenrodCacheOverflows','sGpuRegBuffer','gPlttBufferFaded','gPlttBufferUnfaded'};raw=subprocess.check_output([str(T/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);symbols={a[2]:a[0] for l in raw.splitlines() if len(a:=l.split())==3 and a[2] in wanted};assert symbols.keys()==wanted;(O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
result=subprocess.run([str(O/'audit'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O)],capture_output=True,text=True,timeout=600);(O/'movement.jsonl').write_text(result.stdout);assert result.returncode==0,result.stderr
# Import only the independent native BG decoder, not a second walking tour.
tree=ast.parse((HERE/'verify_frames.py').read_text());fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='decode');scope=dict(np=np);exec(compile(ast.Module(body=[fun],type_ignores=[]),'decode','exec'),scope);decode=scope['decode']
native=np.array(Image.open(S.parent/'evidence/native-map.png').convert('RGB'));fg=np.array(Image.open(S/'shared-foreground.png'));above=np.repeat(np.repeat(np.load(S/'above.npy'),16,axis=0),16,axis=1);top=(fg[...,3]>0)&above
# Match the runtime's exact native border policy.
from border import border_cell
pad=20*16;padded=np.zeros((native.shape[0]+pad*2,native.shape[1]+pad*2,3),np.uint8);padded_top=np.zeros(padded.shape[:2],bool)
for y in range(-20,H+20):
 for x in range(-20,W+20):
  cx,cy=border_cell(x,y);py,px=y*16+pad,x*16+pad;padded[py:py+16,px:px+16]=native[cy*16:cy*16+16,cx*16:cx*16+16];padded_top[py:py+16,px:px+16]=top[cy*16:cy*16+16,cx*16:cx*16+16]
def window(x,y):
 xx=x*16-112+pad;yy=y*16-72+pad;return padded[yy:yy+160,xx:xx+240],padded_top[yy:yy+160,xx:xx+240]

def sprite_modes(p):
 # Decode actual OAM/OBJ VRAM. The shadow is a semitransparent OBJ; its
 # black diagnostic pixels must blend with the original BG, not the backdrop.
 raw=p.with_suffix('.objects').read_bytes();oam=np.frombuffer(raw[:1024],'<u2').reshape(128,4);v=np.frombuffer(raw[1024:33792],np.uint8);regs=np.frombuffer(raw[34304:],'<u2');one_dim=bool(int(regs[3])&64);mode=np.zeros((160,240),np.uint8);claimed=np.zeros((160,240),bool)
 dims=[[(8,8),(16,16),(32,32),(64,64)],[(16,8),(32,8),(32,16),(64,32)],[(8,16),(8,32),(16,32),(32,64)]]
 order=sorted(range(128),key=lambda i:(int(oam[i,2])>>10&3,i))
 for i in order:
  a,b,t=map(int,oam[i,:3]);shape=a>>14
  if shape==3 or (not a&256 and a&512):continue
  assert not a&256,'Unexpected affine OBJ: extend decoder before accepting evidence'
  w,h=dims[shape][b>>14];x=b&511;y=a&255;x=x-512 if x>=240 else x;y=y-256 if y>=160 else y
  if x+w<=0 or y+h<=0:continue
  yy,xx=np.indices((h,w));tx=w-1-xx if b&4096 else xx;ty=h-1-yy if b&8192 else yy
  assert not a&8192,'Unexpected 8bpp OBJ'
  addr=((t&1023)+(ty//8)*(w//8 if one_dim else 32)+tx//8)*32+(ty%8)*4+(tx%8)//2;pixels=(v[addr%32768]>>((tx%2)*4))&15
  l=max(0,x);r=min(240,x+w);u=max(0,y);d=min(160,y+h)
  if l>=r or u>=d:continue
  opaque=(pixels[u-y:d-y,l-x:r-x]>0)&~claimed[u:d,l:r];mode[u:d,l:r][opaque]=(a>>10&3)+1;claimed[u:d,l:r]|=opaque
 return mode,regs

rows=[];errors=[];total_bg=0;total_obj=0
for x,y in poses:
 p=O/f'cell-{x:02}-{y:02}';expected,layer=window(x,y);background=decode(p.with_suffix('.vram'));bg_errors=int(np.any(background!=expected,2).sum());frame=np.array(Image.open(p.with_suffix('.ppm')).convert('RGB'))&248;obj=np.array(Image.open(O/(p.name+'-objects.ppm')).convert('RGB'))&248
 object_mask=np.any(obj!=[248,0,248],2);clip=np.zeros((160,240),bool);clip[40:104,96:144]=True;object_mask&=clip;assert object_mask.sum()>100,(x,y,'missing diagnostic player')
 modes,regs=sprite_modes(p);want=obj.copy();semi=(modes==2)&object_mask
 # BLDCNT's second targets include the native BG planes; EVA/EVB from BLDALPHA.
 eva=min(16,int(regs[1])&31);evb=min(16,int(regs[1])>>8&31)
 assert int(regs[0])&0x0e00==0x0e00,(x,y,'BG second targets')
 # mGBA expands 5-bit channels before its software alpha blend. Match its
 # exact expansion, then normalize the result back to 5-bit comparison.
 expanded_obj=obj.astype(np.uint16)|(obj.astype(np.uint16)>>5)
 expanded_bg=expected.astype(np.uint16)|(expected.astype(np.uint16)>>5)
 mixed=np.minimum(255,(expanded_obj*eva+expanded_bg*evb)//16)&248
 want[semi]=mixed[semi];want[layer]=expected[layer];obj_errors=int(np.any(frame[object_mask]!=want[object_mask],1).sum());total_bg+=bg_errors;total_obj+=obj_errors;rows.append(dict(cell=[x,y],background_errors=bg_errors,sprite_layer_errors=obj_errors,player_pixels=int(object_mask.sum()),covered_player_pixels=int((object_mask&layer).sum()),visible_player_pixels=int((object_mask&~layer).sum())))
 if bg_errors or obj_errors:errors.append(rows[-1])
report=dict(ROM_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),cells_total=W*H,walkable_cells=len(poses),directed_movement_edges=len(tested),components=components,background_frames=len(poses),background_pixels=len(poses)*38400,background_RGB_errors=total_bg,sprite_layer_RGB_errors=total_obj,cache_overflows=0,diagnostic_method='At each actual player pose, compare ordinary framebuffer against a separate OBJ-only diagnostic frame. OAM identifies semitransparent shadow pixels, blended using captured coefficients and mGBA channel expansion. Disabled BG layers/magenta backdrop are diagnostic only; restored before further input.',errors=errors,poses=rows)
(E/'exhaustive-runtime.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['poses','errors']});assert not errors,errors[:5]
