"""Use a copy of the first-pass flash save with the corrected geometry."""
from pathlib import Path
import sys,shutil,subprocess,json,hashlib
from PIL import Image
G,old,normal,out=map(Path,sys.argv[1:5]);out.mkdir(exist_ok=False);shutil.copyfile(old,out/'johto.sav');before=hashlib.sha256(old.read_bytes()).hexdigest()
s=(normal/'runtime.c').read_text().replace('at(54,19,23,','at(54,25,20,')
s=s.replace('shot("title-continue");','shot("title-continue");step(LEFT,2);at(54,23,20,"legacy-save-walk-left");step(DOWN,2);at(54,23,22,"legacy-save-walk-south");shot("legacy-save-movement");')
(out/'runtime.c').write_text(s);shutil.copyfile(normal/'symbols.txt',out/'symbols.txt')
subprocess.run(['cc',str(out/'runtime.c'),'-I/workspace/deps/root/usr/include','-L/workspace/deps/root/usr/lib/x86_64-linux-gnu','-Wl,-rpath,/workspace/deps/root/usr/lib/x86_64-linux-gnu','-lmgba','-o',str(out/'runtime')],check=True)
results=[]
for phase in ['read','menu']:
 r=subprocess.run([str(out/'runtime'),str(G/'pokeemerald.gba'),str(out/'symbols.txt'),str(out),phase],capture_output=True,text=True,timeout=120);(out/(phase+'.jsonl')).write_text(r.stdout);results.append(dict(phase=phase,exit_code=r.returncode,stderr=r.stderr,observations=[json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]));assert not r.returncode,r.stderr
for p in out.glob('*.ppm'):Image.open(p).save(p.with_suffix('.png'));p.unlink()
assert hashlib.sha256(old.read_bytes()).hexdigest()==before
(out/'results.json').write_text(json.dumps(dict(original_save_sha256=before,rom_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),original_preserved=True,phases=results),indent=2)+'\n');print(results)
