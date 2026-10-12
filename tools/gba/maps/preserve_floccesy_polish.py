#!/usr/bin/env python3
"""Preserve the roof, fence, park and forest-opening revision over the cleanup pass."""
from pathlib import Path
import subprocess,json,hashlib,zipfile,shutil,re,struct
from tiles import Tileset
R=Path(__file__).resolve().parents[3];A=R/'gba/art/floccesy-polish';E=A/'evidence'
base=R/'tools/vendor/gba/floccesy-cleanup-work';work=R/'tools/vendor/gba/floccesy-polish-work'
roots=['data/layouts/FloccesyTown/map.bin','data/tilesets/primary/floccesy','data/tilesets/secondary/floccesy','graphics/door_anims/floccesy','src/field_door.c']
parts=[];changed=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for root in roots:
 p=base/root;files=[p] if p.is_file() else sorted(f for f in p.rglob('*') if f.is_file())
 for p in files:
  rel=p.relative_to(base);q=work/rel
  if p.read_bytes()==q.read_bytes():continue
  result=subprocess.run(['git','diff','--no-index','--binary','--src-prefix=a/','--dst-prefix=b/','--',str(p.relative_to(R)),str(q.relative_to(R))],cwd=R,capture_output=True);assert result.returncode==1
  diff=result.stdout.replace(('a/'+str(base.relative_to(R))+'/').encode(),b'a/').replace(('b/'+str(work.relative_to(R))+'/').encode(),b'b/');parts.append(diff);changed.append(str(rel))
patch=R/'gba/floccesy-polish.patch';patch.write_bytes(b''.join(parts))
subprocess.run(['git','apply','--check',str(patch)],cwd=base,check=True);subprocess.run(['git','apply','--reverse','--check',str(patch)],cwd=work,check=True)
# Door implementation is identical after removing only the regenerated art references.
def door_logic(path):
 s=path.read_text();s=re.sub(r'\.metatileNum=\d+', '.metatileNum=ART',s)
 return re.sub(r'(sFloccesyDoorPal_\w+\[20\] = )\{[^}]*\}',r'\1{ART}',s)
assert door_logic(base/'src/field_door.c')==door_logic(work/'src/field_door.c')
for root in ('data/maps','data/layouts'):
 for p in (base/root).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(base)
  if str(rel)=='data/layouts/FloccesyTown/map.bin':continue
  assert p.read_bytes()==(work/rel).read_bytes(),rel
before=struct.unpack('<4368H',(base/'data/layouts/FloccesyTown/map.bin').read_bytes());after=struct.unpack('<4368H',(work/'data/layouts/FloccesyTown/map.bin').read_bytes())
bt=Tileset(base,'floccesy','floccesy');at=Tileset(work,'floccesy','floccesy');ba=bt.attrs[0]+bt.attrs[1];aa=at.attrs[0]+at.attrs[1]
assert all((x&0xfc00)==(y&0xfc00) and ba[x&1023]==aa[y&1023] for x,y in zip(before,after))
blocks=at.blocks[0]+at.blocks[1];used=set(e&1023 for n in after for e in blocks[n&1023])
assert len(used)<=1008 and all(e>>12<13 for n in after for e in blocks[n&1023])
doors=json.loads((E/'doors.json').read_text());layout=json.loads((A/'layout.json').read_text())
for d,b in zip(doors,layout['buildings']):
 x,y=b['door'];assert d['name']==b['name'] and d['metatile']==after[y*56+x]&1023
report=dict(base=str(base.relative_to(R)),patch=str(patch.relative_to(R)),patch_sha256=sha(patch),patch_bytes=patch.stat().st_size,changed_files=changed,forward_reverse_checks=True,all_cell_exploration_properties_identical=True,all_event_and_script_files_identical=True,all_other_layout_binaries_identical=True,door_logic_identical=True,door_art_references_match_map=True,referenced_tile_patterns=len(used),metatiles=len(blocks),supported_palettes_only=True,base_rom_sha256=sha(base/'pokeemerald.gba'),rom_sha256=sha(work/'pokeemerald.gba'))
(E/'preservation.json').write_text(json.dumps(report,indent=2)+'\n')
pkg=R/'tools/vendor/gba/Floccesy-polish-20260926';pkg.mkdir(exist_ok=True);shutil.copy2(work/'pokeemerald.gba',pkg/'Floccesy.gba');shutil.copy2(R/'tools/vendor/gba/polish-sample-proof/clock.sav',pkg/'Floccesy.sav')
(pkg/'README.txt').write_text('Floccesy roof, fence, park and forest-opening revision. Load the matching ROM/save and choose Continue beside the clock tower. Clean roof planes and ridge details, corrected canopy ordering, rebuilt fences, landscaped park and shaded woodland opening. All exploration properties, events, NPC routes and warps are preserved. Isolated preview; active Porymap source was not changed.\n')
with zipfile.ZipFile(pkg.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for name in ('Floccesy.gba','Floccesy.sav','README.txt'):z.write(pkg/name,name)
with zipfile.ZipFile(pkg.with_suffix('.zip')) as z:assert hashlib.sha256(z.read('Floccesy.gba')).hexdigest()==report['rom_sha256']
print(json.dumps({k:v for k,v in report.items() if k!='changed_files'},indent=2))
