#!/usr/bin/env python3
"""Compare real mGBA traversal and captures for the native clock sample."""
from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[3];A=R/'gba/art/floccesy-materials/evidence'
T=R/'tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi/bin/arm-none-eabi-nm'
exe=R/'tools/vendor/gba/floccesy-clock-runtime'
subprocess.run(['cc',str(R/'tools/gba/maps/floccesy_clock_runtime.c'),'-I/opt/homebrew/opt/mgba/include','-L/opt/homebrew/opt/mgba/lib','-lmgba','-o',str(exe)],check=True)
wanted=set('MapProof_Boot MapProof_Enter MapProof_ReadState MapProof_Resume gMapProofState TrySavingData LoadGameSave ArePlayerFieldControlsLocked gObjectEvents gSprites PlayerFaceDirection'.split())
observations={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for variant in ('sample','baseline'):
 g=R/('tools/vendor/gba/floccesy-materials-work' if variant=='sample' else 'tools/vendor/gba/floccesy-clock-sample-work');o=R/f'tools/vendor/gba/materials-{variant}-proof';o.mkdir(exist_ok=True)
 text=subprocess.check_output([str(T),str(g/'pokeemerald.elf')],text=True);symbols={p[2]:p[0] for l in text.splitlines() if len(p:=l.split())==3 and p[2] in wanted};assert symbols.keys()==wanted
 (o/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
 for old in o.glob('walk-*.ppm'):old.unlink()
 observations[variant]={}
 for phase in ('write','read','menu'):
  result=subprocess.run([str(exe),str(g/'pokeemerald.gba'),str(o/'symbols.txt'),str(o),phase],capture_output=True,text=True,timeout=120)
  (o/f'{phase}.jsonl').write_text(result.stdout);assert result.returncode==0,(variant,phase,result.stderr,result.stdout)
  observations[variant][phase]=[json.loads(l) for l in result.stdout.splitlines()]
 for tag in ('clock','street','clock-reload','npc-dialogue'):Image.open(o/f'{tag}.ppm').save(A/f'{variant}-{tag}-in-game.png')
 frames=[Image.open(p).convert('RGB') for p in sorted(o.glob('walk-*.ppm'))]
 frames[0].save(A/f'{variant}-walk.gif',save_all=True,append_images=frames[1:],duration=67,loop=0)
 observations[variant]['rom_sha256']=sha(g/'pokeemerald.gba')
assert observations['sample']['write']==observations['baseline']['write']
assert observations['sample']['read']==observations['baseline']['read']
assert observations['sample']['menu']==observations['baseline']['menu']
(A/'runtime.json').write_text(json.dumps({'matching_traversal_and_reload':True,'observations':observations},indent=2)+'\n')
for tag in ('clock','street'):
 out=Image.new('RGB',(480,180),(24,28,32));d=ImageDraw.Draw(out)
 for i,variant in enumerate(('baseline','sample')):
  im=Image.open(A/f'{variant}-{tag}-in-game.png');out.paste(im,(i*240,20));d.text((i*240+6,4),'Previous sample' if i==0 else 'Revised town',fill='white')
 out.save(A/f'{tag}-comparison.png')
print('Both builds: identical traversal, wall blocking, exit, street movement and cold save reload.')
