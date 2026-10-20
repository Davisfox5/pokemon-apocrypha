"""Olivine exterior, seamless-section camera and ordinary-save qualification."""
from pathlib import Path
import sys,json,argparse,os,subprocess,shlex,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent;R=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
sections=json.loads((R/'gba/art/olivine-city/evidence/sections.json').read_text())
def section(x,y):
 for i,s in enumerate(sections):
  a,b,c,d=s['box']
  if a<=x<c and b<=y<d:return 63+i,x-a,y-b
 raise ValueError((x,y))
def go(x,y):return 'go(%d,%d,%d);'%section(x,y)
def at(x,y,label):return 'at(%d,%d,%d,"%s");'%(*section(x,y),label)
steps=[]
# Construct a continuous walking tour through the independently authored ledger.
# Runtime coordinate assertions, not this BFS, establish actual movement.
from collections import deque
import numpy as np
solid=np.load(R/'gba/art/olivine-city/source/solid.npy');position=(24,32)
steps.append(go(*position)+'shot("arrival");')
def route(target,tag):
 global position
 prev={position:None};q=deque([position])
 while q:
  p=q.popleft()
  if p==target:break
  for d in [(1,0),(-1,0),(0,1),(0,-1)]:
   v=p[0]+d[0],p[1]+d[1]
   if 0<=v[0]<65 and 0<=v[1]<54 and not solid[v[1],v[0]] and v not in prev:prev[v]=p;q.append(v)
 assert target in prev,(position,target)
 path=[];p=target
 while prev[p]!=None:path.append(p);p=prev[p]
 path.reverse();keys={(1,0):'RIGHT',(-1,0):'LEFT',(0,1):'DOWN',(0,-1):'UP'}
 for i,v in enumerate(path):
  key=keys[v[0]-position[0],v[1]-position[1]]
  steps.append(f'step({key},1);'+at(*v,tag+f'-walk-{i}'))
  if i%6==0:steps[-1]+=f'shot("{tag}-walk-{i}");'
  position=v
 steps.append(f'shot("{tag}");')
features=json.loads((R/'gba/art/olivine-city/source/features.json').read_text())
for i,f in enumerate(features):
 target=tuple(f['door_approach']);tag=f'building-{i+1:02}'
 route(target,tag);steps.append('step(UP,1);'+at(*target,tag+'-door-closed'))
for x,y,key,tag in [(26,21,'UP','upper-avenue-rail'),(10,21,'UP','west-rail'),(24,1,'UP','north-route-boundary'),(1,31,'LEFT','west-route-boundary'),(7,38,'DOWN','quay-railing'),(22,42,'LEFT','pier-water'),(46,35,'DOWN','lighthouse-retaining-wall'),(48,34,'UP','lighthouse-sign'),(10,38,'UP','promenade-table')]:
 route((x,y),tag);steps.append(f'step({key},1);'+at(x,y,tag+'-blocks'))
route((13,21),'festival-gate');steps.append('step(UP,1);'+at(13,20,'festival-gate-open'));position=(13,20)
route((50,25),'lighthouse-back');route((24,32),'return-to-city')
# Renderer lifecycle through prior accepted maps; return for an ordinary save.
steps.append('go(60,16,6);shot("Goldenrod-regression");go(50,20,18);shot("Azalea-regression");'+go(24,32)+at(24,32,'return-to-Olivine')+'shot("save-Olivine");')
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
main=(start+'\n'.join(steps)+end).replace('at(11,27,18', 'at(%d,%d,%d'%section(24,32)).replace('cold-reload-new-bark','cold-reload-Olivine')
# Save the same native viewport snapshot that the ordinary save menu records.
main=main.replace('unsigned status=call("TrySavingData",0);','call("SaveMapView",0);unsigned status=call("TrySavingData",0);')
# On cold reload, physically verify the new lamp base and cleared old post area.
read_checks='step(UP,4);step(RIGHT,4);'+at(28,28,'cold-lamp-approach')+'step(UP,1);'+at(28,28,'cold-new-lamp-blocks')+'step(LEFT,1);step(UP,3);step(RIGHT,2);'+at(29,25,'cold-old-post-cleared')
main=main.replace('shot("cold-reload");','shot("cold-reload");'+read_checks)
# Check runtime VRAM references and atlas identity in every actually visible frame.
# Dump native BG/VRAM separately from sprites for exact source comparison.
extra=r'''
static void verify(const char *tag) {
 unsigned over=c->busRead32(c,sym("gOlivineCacheOverflows"))+c->busRead32(c,sym("gGoldenrodCacheOverflows"));
 need(over==0,"no-cache-overflow");
 char p[2048];snprintf(p,sizeof(p),"%s/%s.vram",out,tag);FILE*f=fopen(p,"wb");
 for(unsigned a=0x6000000;a<0x6010000;a++)fputc(c->busRead8(c,a),f);fclose(f);
 snprintf(p,sizeof(p),"%s/%s.pal",out,tag);f=fopen(p,"wb");for(unsigned a=0x5000000;a<0x5000200;a++)fputc(c->busRead8(c,a),f);fclose(f);
 snprintf(p,sizeof(p),"%s/%s.scroll",out,tag);f=fopen(p,"wb");for(unsigned a=8;a<32;a++)fputc(c->busRead8(c,sym("sGpuRegBuffer")+a),f);fclose(f);
}
'''
# A fresh process per write/read/menu phase; source helpers are the existing
# project harness. Every screenshot records cache overflow state.
prefix=r.TEMPLATE.split('int main(')[0].replace('RUNTIME_C',str(R/'tools/gba/maps/runtime.c'));prefix=prefix.replace('#undef main','#undef main\n#define A 1\n#define B 2\n#define RIGHT 16\n#define LEFT 32\n#define UP 64\n#define DOWN 128')
prefix=prefix.replace('static void shot(const char*t){screenshot(out,t);}', 'static void verify(const char*);\nstatic void shot(const char*t){screenshot(out,t);verify(t);}')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('game',type=Path);p.add_argument('output',type=Path);p.add_argument('--toolchain',type=Path,required=True);a=p.parse_args();G=a.game.resolve();O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
 (O/'runtime.c').write_text(prefix+extra+main)
 subprocess.run(['cc',str(O/'runtime.c'),*shlex.split(os.environ.get('MGBA_FLAGS','-lmgba')),'-o',str(O/'runtime')],check=True)
 raw=subprocess.check_output([str(a.toolchain.resolve()/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True)
 wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','TrySavingData','SaveMapView','LoadGameSave','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gSaveBlock2Ptr','gSaveBlock1Ptr','gPlayerAvatar','gObjectEvents','gOlivineCacheOverflows','gGoldenrodCacheOverflows','sGpuRegBuffer'}
 symbols={r[2]:r[0] for line in raw.splitlines() if len(r:=line.split())==3 and r[2] in wanted};assert symbols.keys()==wanted
 (O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()));results=[]
 for phase in ['write','read','menu']:
  result=subprocess.run([str(O/'runtime'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O),phase],capture_output=True,text=True,timeout=600);(O/(phase+'.jsonl')).write_text(result.stdout);results.append(dict(phase=phase,exit_code=result.returncode,stderr=result.stderr,observations=[json.loads(l) for l in result.stdout.splitlines() if l.startswith('{')]))
  (O/'results.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),phases=results),indent=2)+'\n')
  for ppm in O.glob('*.ppm'):Image.open(ppm).save(ppm.with_suffix('.png'));ppm.unlink()
  print(phase,result.returncode,result.stderr[-1000:],flush=True)
  if result.returncode:raise SystemExit(result.returncode)
