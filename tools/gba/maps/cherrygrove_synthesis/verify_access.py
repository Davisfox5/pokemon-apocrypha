"""Run expanded collision and exact travel assertions against a freshly built ROM."""
from pathlib import Path
import sys,subprocess,json,hashlib,time
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=R/'tools/vendor/gba/cherrygrove-synthesis-work';E=R/'gba/art/cherrygrove-synthesis/evidence';O=Path(sys.argv[1]).resolve();TC=Path(sys.argv[2]).resolve();O.mkdir(parents=True,exist_ok=False)
flags=['-I/opt/homebrew/include','-L/opt/homebrew/lib','-lmgba']
def run(args,**kw):return subprocess.run(list(map(str,args)),check=True,**kw)
run([sys.executable,Path(__file__).with_name('check_access.py')])
lines=subprocess.check_output([str(TC/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','gMapProofState','ArePlayerFieldControlsLocked','SetPlayerAvatarTransitionFlags','GetPlayerFacingDirection'};rows=[l.split() for l in lines.splitlines()];(O/'symbols.txt').write_text(''.join(f'{r[2]} {r[0]}\n' for r in rows if len(r)==3 and r[2] in wanted))
rom_hash=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest()
results={}
for name,src,tsv in [('travel',Path(__file__).with_name('access_runtime.c'),'access-warps.tsv'),('collision',R/'tools/gba/maps/johto_collision_runtime.c','access-probes.tsv')]:
 run(['cc',src,*flags,'-o',O/name]);start=time.monotonic()
 with (O/(name+'.jsonl')).open('w') as f:run([O/name,G/'pokeemerald.gba',O/'symbols.txt',E/tsv,O],stdout=f)
 rows=[json.loads(l) for l in (O/(name+'.jsonl')).read_text().splitlines()];assert rows and all(r['passed'] for r in rows)
 (E/('access-'+name+'.jsonl')).write_text((O/(name+'.jsonl')).read_text());results[name]=dict(passed=len(rows),seconds=round(time.monotonic()-start,2))
assert hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest()==rom_hash,'ROM changed during validation'
for f in O.glob('*.ppm'):Image.open(f).save(f.with_suffix('.png'))
# Actual runtime door entry/return evidence, seven buildings with both exits tested.
board=Image.new('RGB',(960,7*184),(25,30,34));d=ImageDraw.Draw(board)
for row,mid in enumerate([1,2,3,5,6,11,12]):
 for col,tag in enumerate([f'door-{mid}-enter',f'door-{mid}-exit-0']):
  x=col*480;y=row*184;d.text((x+8,y+4),tag,fill='white');board.paste(Image.open(O/(tag+'.png')),(x+120,y+22))
board.save(E/'door-access-review.png')
(E/'access-runtime.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),checks=results,probe_sha256={n:hashlib.sha256((E/n).read_bytes()).hexdigest() for n in ['access-probes.tsv','access-warps.tsv']},desktop_emulator_launched=False,scope='Isolated Cherrygrove and its two approach maps; actual input, no desktop emulator.'),indent=2)+'\n')
print(json.dumps(results))
