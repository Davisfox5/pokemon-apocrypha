#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib,zipfile,shutil
R=Path(__file__).resolve().parents[3];A=R/'gba/art/floccesy-clock-sample';E=A/'evidence'
base=R/'tools/vendor/gba/floccesy-detailed-work';fixed=R/'tools/vendor/gba/floccesy-clock-baseline-work';sample=R/'tools/vendor/gba/floccesy-clock-sample-work'
roots=['data/layouts/FloccesyTown/map.bin','data/tilesets/primary/floccesy','data/tilesets/secondary/floccesy']
reports=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for left,right,name in [(base,fixed,'floccesy-clock-palette-fix'),(fixed,sample,'floccesy-clock-sample')]:
 parts=[];changed=[]
 for root in roots:
  p=left/root;files=[p] if p.is_file() else sorted(f for f in p.rglob('*') if f.is_file())
  for p in files:
   rel=p.relative_to(left);q=right/rel
   if p.read_bytes()==q.read_bytes():continue
   result=subprocess.run(['git','diff','--no-index','--binary','--src-prefix=a/','--dst-prefix=b/','--',str(p.relative_to(R)),str(q.relative_to(R))],cwd=R,capture_output=True);assert result.returncode==1
   diff=result.stdout.replace(('a/'+str(left.relative_to(R))+'/').encode(),b'a/').replace(('b/'+str(right.relative_to(R))+'/').encode(),b'b/');parts.append(diff);changed.append(str(rel))
 patch=R/f'gba/{name}.patch';patch.write_bytes(b''.join(parts));subprocess.run(['git','apply','--check',str(patch)],cwd=left,check=True);subprocess.run(['git','apply','--reverse','--check',str(patch)],cwd=right,check=True)
 reports.append(dict(patch=str(patch.relative_to(R)),base=str(left.relative_to(R)),sha256=sha(patch),bytes=patch.stat().st_size,changed_files=changed,forward_reverse_checks=True))
(E/'patches.json').write_text(json.dumps(reports,indent=2)+'\n')
# All event sources are preserved across the art pass, including NPCs and warps.
for root in ('data/maps','data/layouts'):
 for p in (base/root).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(base)
  if str(rel)=='data/layouts/FloccesyTown/map.bin':continue
  assert p.read_bytes()==(sample/rel).read_bytes(),rel
(E/'preservation.json').write_text(json.dumps({'all_map_event_and_script_files_byte_identical':True,'all_layouts_except_fl oc cesy_graphics_assignment_byte_identical':True,'base_rom_sha256':sha(base/'pokeemerald.gba'),'corrected_baseline_rom_sha256':sha(fixed/'pokeemerald.gba'),'sample_rom_sha256':sha(sample/'pokeemerald.gba')},indent=2).replace('fl oc cesy','floccesy')+'\n')
pkg=R/'tools/vendor/gba/Floccesy-clock-sample-20260926';pkg.mkdir(exist_ok=True);shutil.copy2(sample/'pokeemerald.gba',pkg/'Floccesy.gba');shutil.copy2(R/'tools/vendor/gba/clock-sample-proof/clock.sav',pkg/'Floccesy.sav')
(pkg/'README.txt').write_text('Floccesy native clock-garden sample. Load the matching ROM and save, then choose Continue. Starts beside the clock tower. All exploration data is preserved from v4. The preview also corrects unsupported v4 foliage palette references. This is an isolated visual sample; no active editor source was changed.\n')
with zipfile.ZipFile(pkg.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for name in ('Floccesy.gba','Floccesy.sav','README.txt'):z.write(pkg/name,name)
print('Two reversible source patches and isolated playable package verified.')
