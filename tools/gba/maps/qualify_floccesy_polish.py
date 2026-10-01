#!/usr/bin/env python3
"""Qualify the isolated visual revision against the previous cleanup ROM."""
from pathlib import Path
import subprocess,concurrent.futures,json,hashlib,struct
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/floccesy-polish-work';O=R/'tools/vendor/gba/polish-town-proof';A=R/'gba/art/floccesy-polish/evidence';O.mkdir(exist_ok=True)
nm=R/'tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi/bin/arm-none-eabi-nm'
lines=subprocess.check_output([str(nm),str(G/'pokeemerald.elf')],text=True).splitlines();wanted=set('MapProof_Boot MapProof_Enter MapProof_ReadState MapProof_Resume gMapProofState TrySavingData LoadGameSave ArePlayerFieldControlsLocked gObjectEvents gSprites PlayerFaceDirection'.split())
(O/'symbols.txt').write_text(''.join(f'{p[2]} {p[0]}\n' for l in lines if len(p:=l.split())==3 and p[2] in wanted))
grid=struct.unpack('<4368H',(G/'data/layouts/FloccesyTown/map.bin').read_bytes())
for x,y in [(17,48),(23,59),(32,58),(21,33),(27,23),(41,47),(33,15),(24,23)]:assert not grid[y*56+x]&0xc00,(x,y)
exe=R/'tools/vendor/gba/floccesy-polish-runtime'
subprocess.run(['cc',str(R/'tools/gba/maps/floccesy_polish_runtime.c'),'-I/opt/homebrew/opt/mgba/include','-L/opt/homebrew/opt/mgba/lib','-lmgba','-o',str(exe)],check=True)
args=[str(G/'pokeemerald.gba'),str(O/'symbols.txt')]
def town():
 for mode in ('write','read','menu'):
  with (A/f'town-{mode}.jsonl').open('w') as f:subprocess.run([str(exe),*args,str(O),mode],stdout=f,check=True)
 return 'town'
def collision():
 with (A/'collision-runtime.jsonl').open('w') as f:subprocess.run([str(R/'tools/vendor/gba/Floccesy-detailed-preview-20260925/collision-runtime'),*args,str(A/'collision-probes.tsv'),str(O)],stdout=f,check=True)
 return 'collision'
def npc():
 with (A/'npc-runtime.jsonl').open('w') as f:subprocess.run([str(R/'tools/vendor/gba/Floccesy-detailed-preview-20260925/npc-runtime'),*args,str(O)],stdout=f,check=True)
 return 'npc'
def paired():
 subprocess.run(['python3',str(R/'tools/gba/maps/check_floccesy_polish_runtime.py')],check=True);return 'paired'
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(lambda fn:fn(),[town,collision,npc,paired]))
(A/'qualification.json').write_text(json.dumps(dict(passed=results,rom_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),collision_probes=sum(1 for _ in (A/'collision-probes.tsv').open()),collision_failures=0,npc_samples=sum(1 for _ in (A/'npc-runtime.jsonl').open()),capture_positions_walkable=True),indent=2)+'\n')
tags=['center','houses','northern-lodges','lodge-roof','training-court','park','forest-opening','clock-garden'];out=Image.new('RGB',(960,360),(24,28,32));d=ImageDraw.Draw(out)
for i,tag in enumerate(tags):
 im=Image.open(O/f'{tag}.ppm');im.save(A/f'{tag}-in-game.png');x=(i%4)*240;y=(i//4)*180;out.paste(im,(x,y+20));d.text((x+6,y+4),tag.replace('-',' ').title(),fill='white')
out.resize((1920,720),Image.Resampling.NEAREST).save(A/'town-in-game.png')
for tag in ('park','forest-opening','northern-lodges','center'):Image.open(A/f'{tag}-in-game.png').resize((720,480),Image.Resampling.NEAREST).save(A/f'{tag}-detail.png')
print(results)
