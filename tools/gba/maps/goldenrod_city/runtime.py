"""Goldenrod exterior, seamless-section camera and ordinary-save qualification."""
from pathlib import Path
import sys,json,argparse,os,subprocess,shlex,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent;R=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
sections=json.loads((R/'gba/art/goldenrod-city/evidence/sections.json').read_text())
def section(x,y):
 for i,s in enumerate(sections):
  a,b,c,d=s['box']
  if a<=x<c and b<=y<d:return 51+i,x-a,y-b
 raise ValueError((x,y))
def go(x,y):return 'go(%d,%d,%d);'%section(x,y)
def at(x,y,label):return 'at(%d,%d,%d,"%s");'%(*section(x,y),label)
steps=[]
# The long waterfront avenue crosses three section boundaries in both directions.
steps.append(go(16,29)+'shot("Radio-plaza");')
for x in [20,21,28,40,41,42,48,56,62,63,70]:
 last=16 if len(steps)==1 else prev
 steps.append(f'step(RIGHT,{x-last});'+at(x,29,f'avenue-east-{x}')+f'shot("avenue-east-{x}");');prev=x
for x in [63,62,42,41,21,20,16]:
 steps.append(f'step(LEFT,{prev-x});'+at(x,29,f'avenue-west-{x}')+f'shot("avenue-west-{x}");');prev=x
# Main north/south avenue: under the original elevated train track and back.
steps.append(go(58,48)+'shot("south-arrival");')
prev=48
for y in [43,42,41,36,29,28,27,24,23,22,21,20,19,15,14,13,10,8]:
 steps.append(f'step(UP,{prev-y});'+at(58,y,f'avenue-north-{y}')+f'shot("avenue-north-{y}");');prev=y
for y in [14,20,23,28,42,48]:
 steps.append(f'step(DOWN,{y-prev});'+at(58,y,f'avenue-south-{y}')+f'shot("avenue-south-{y}");');prev=y
steps.append(go(62,5)+'step(UP,1);'+at(62,4,'northern-fence-approach')+'step(UP,1);'+at(62,4,'original-picket-fence-blocks')+'shot("northern-fence");')
steps.append(go(61,4)+'step(LEFT,1);'+at(61,4,'north-gate-side-wall-blocks')+'shot("north-gate-side");')
steps.append(go(58,47)+'shot("arch-north");')
prev=47
for y in [48,49,50,51,52]:
 steps.append(f'step(DOWN,{y-prev});'+at(58,y,f'arch-south-{y}')+f'shot("arch-south-{y}");');prev=y
for y in [51,50,49,48,47]:
 steps.append(f'step(UP,{prev-y});'+at(58,y,f'arch-north-{y}')+f'shot("arch-north-{y}");');prev=y
for name,x,y,dx,dy in [('arch-west-pillar',56,50,-1,0),('arch-east-pillar',60,50,1,0),('Radio-door',16,25,0,-1),('station-door',47,26,0,-1),('Gym-door',66,15,0,-1),('flower-shop',71,13,0,-1),('Game-Corner',51,35,0,-1),('department-store',65,41,0,-1),('bike-shop',70,46,0,-1),('Center',52,41,0,-1),('north-underground',47,15,0,-1),('south-underground',47,46,0,-1),('seawall',8,35,-1,0),('eastern-cliff',80,27,1,0)]:
 key='UP' if dy<0 else 'DOWN' if dy>0 else 'LEFT' if dx<0 else 'RIGHT'
 steps.append(go(x,y)+f'shot("{name}");step({key},1);'+at(x,y,name+'-closed-or-barrier'))
# Cache lifecycle: leave the city, then return through an ordinary map load.
steps.append(go(77,52)+'shot("southeast-native-trees");')
steps.append('go(50,20,18);shot("Azalea-regression");'+go(58,48)+at(58,48,'return-to-Goldenrod')+'shot("save-Goldenrod");')
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
main=(start+'\n'.join(steps)+end).replace('at(11,27,18', 'at(%d,%d,%d'%section(58,48)).replace('cold-reload-new-bark','cold-reload-Goldenrod')
# Check runtime VRAM references and atlas identity in every actually visible frame.
# Dump native BG/VRAM separately from sprites for exact source comparison.
extra=r'''
static void verify(const char *tag) {
 unsigned over=c->busRead32(c,sym("gGoldenrodCacheOverflows"));
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
 wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','TrySavingData','LoadGameSave','ArePlayerFieldControlsLocked','gMain','CB2_Overworld','gSaveBlock2Ptr','gSaveBlock1Ptr','gPlayerAvatar','gObjectEvents','gGoldenrodCacheOverflows','sGpuRegBuffer'}
 symbols={r[2]:r[0] for line in raw.splitlines() if len(r:=line.split())==3 and r[2] in wanted};assert symbols.keys()==wanted
 (O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()));results=[]
 for phase in ['write','read','menu']:
  result=subprocess.run([str(O/'runtime'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O),phase],capture_output=True,text=True,timeout=600);(O/(phase+'.jsonl')).write_text(result.stdout);results.append(dict(phase=phase,exit_code=result.returncode,stderr=result.stderr,observations=[json.loads(l) for l in result.stdout.splitlines() if l.startswith('{')]))
  (O/'results.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),phases=results),indent=2)+'\n')
  for ppm in O.glob('*.ppm'):Image.open(ppm).save(ppm.with_suffix('.png'));ppm.unlink()
  print(phase,result.returncode,result.stderr[-1000:],flush=True)
  if result.returncode:raise SystemExit(result.returncode)
