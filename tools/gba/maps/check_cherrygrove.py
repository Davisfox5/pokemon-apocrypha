#!/usr/bin/env python3
"""Build/run the isolated town's instrumented mGBA acceptance checks."""
import argparse,subprocess,json,hashlib,os,shlex,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('game',type=Path);p.add_argument('output',type=Path);p.add_argument('--toolchain',type=Path,required=True);p.add_argument('--runtime-source',type=Path,default=ROOT/'tools/gba/maps/cherrygrove_runtime.c');a=p.parse_args()
game=a.game.resolve();out=a.output.resolve();assert game!=ROOT/'game' and (game/'.git').is_dir();out.mkdir(parents=True,exist_ok=False)
binary=out/'runtime'
flags = shlex.split(os.environ.get('MGBA_FLAGS', ''))
if not flags and shutil.which('pkg-config') and subprocess.run(['pkg-config', '--exists', 'mgba']).returncode == 0:
 flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'mgba'], text=True))
if not flags and Path('/opt/homebrew/opt/mgba').exists():
 flags = ['-I/opt/homebrew/opt/mgba/include', '-L/opt/homebrew/opt/mgba/lib', '-lmgba']
if not flags: flags = ['-lmgba']
subprocess.run(['cc',str(a.runtime_source.resolve()),*flags,'-o',str(binary)],check=True)
lines=subprocess.check_output([str(a.toolchain.resolve()/'bin/arm-none-eabi-nm'),str(game/'pokeemerald.elf')],text=True)
wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','TrySavingData','LoadGameSave','ArePlayerFieldControlsLocked'}
symbols={r[2]:r[0] for l in lines.splitlines() if len(r:=l.split())==3 and r[2] in wanted};assert symbols.keys()==wanted
(out/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
results=[]
for phase in ['write','read','menu']:
 r=subprocess.run([str(binary),str(game/'pokeemerald.gba'),str(out/'symbols.txt'),str(out),phase],capture_output=True,text=True,timeout=180)
 (out/(phase+'.jsonl')).write_text(r.stdout)
 results.append(dict(phase=phase,exit_code=r.returncode,stderr=r.stderr,observations=[json.loads(l) for l in r.stdout.splitlines()]))
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 for file in out.glob('*.ppm'):Image.open(file).save(file.with_suffix('.png'))
 print(phase,r.returncode,r.stderr,flush=True)
 assert r.returncode==0,results[-1]
print('Town runtime and cold-reload checks passed.')
