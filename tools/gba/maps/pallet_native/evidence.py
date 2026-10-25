"""Collect only reviewable source/evidence, never ROMs, saves or tool executables."""
from pathlib import Path
import sys,json,hashlib,shutil,subprocess,re
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];E=Path(sys.argv[1]);RUN=Path(sys.argv[2]);A=ROOT/'gba/art/pallet-native';V=A/'evidence';D=V/'runtime';D.mkdir(exist_ok=True)
results=json.loads((RUN/'results.json').read_text());assert len(results)==19 and all(r['exit_code']==0 for r in results)
identity=json.loads((RUN/'input-identity.json').read_text());commit=subprocess.check_output(['git','-C',str(E),'rev-parse','HEAD'],text=True).strip()
assert identity['source_commit']==commit
assert identity['rom_sha256']==hashlib.sha256((E/'pokeemerald.gba').read_bytes()).hexdigest()==hashlib.sha256((RUN/'runtime-input.gba').read_bytes()).hexdigest()
assert identity['fixture_sha256']==hashlib.sha256((RUN/'runtime.c').read_bytes()).hexdigest()
for p in RUN.iterdir():
 if p.suffix in ('.png','.json','.jsonl'):shutil.copyfile(p,D/p.name)
shutil.copyfile(RUN/'runtime.c',A/'source/runtime-fixture.c')
shots=[('tour-43-red-room-upper.png','Red home'),('tour-43-bedroom-upper.png','Bedroom'),('tour-43-oak-home.png','Oak'),('tour-43-lab-research.png','Blue'),('tour-43-red-yard.png','House entrance'),('water-43-southern-water-border.png','Southern inlet')]
im=Image.new('RGB',(744,388),(32,40,48));draw=ImageDraw.Draw(im)
for i,(name,label) in enumerate(shots):
 x=8+i%3*248;y=8+i//3*188;draw.text((x,y),label,fill='white');im.paste(Image.open(RUN/name),(x,y+20))
im.save(V/'gameplay.png')
for door in range(3):
 fs=sorted(RUN.glob(f'doors-43-door-{door}-frame-*.png'))
 sheet=Image.new('RGB',(240*4,160*2),(32,40,48))
 for i,p in enumerate(fs[::max(1,len(fs)//8)][:8]):sheet.paste(Image.open(p),(i%4*240,i//4*160))
 sheet.save(V/f'door-{door}-gameplay.png')
log=(RUN/'blocks-43.jsonl').read_text();matches=re.findall(r'"blocked_edges_passed":(\d+)',log);assert matches
build=dict(source_commit=commit,rom_sha256=identity['rom_sha256'],elf_sha256=identity['elf_sha256'],local_build_passed=True,toolchain='arm-none-eabi GCC 14.2.1',porymap='6.3.1',porytiles='2.0.0 legacy',mgba='0.10.5',gba_display=[240,160],runtime_phases=19,blocked_edges=int(matches[-1]),actor_visibility_and_original_palettes_checked=True,rom_committed=False)
(V/'build.json').write_text(json.dumps(build,indent=2)+'\n')
print(json.dumps(build,indent=2))
