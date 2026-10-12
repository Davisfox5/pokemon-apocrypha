"""Apply the preserved patch to a fresh source checkout and verify every file."""
from pathlib import Path
import sys, subprocess, json, hashlib
ROOT=Path(__file__).resolve().parents[4]
G=ROOT/'tools/vendor/gba/johto-synthesis-work'
OUT=ROOT/'gba/art/johto-synthesis'
DEST=Path(sys.argv[1]).resolve()
PATCH=ROOT/'gba/johto-synthesis.patch'
base=json.loads((OUT/'evidence/patch.json').read_text())['base']
def run(*args):return subprocess.check_output(list(map(str,args)),text=True)
if DEST.exists():
 assert run('git','-C',DEST,'rev-parse','HEAD').strip()==base
 run('git','-c','core.autocrlf=false','-C',DEST,'apply','--reverse','--check',PATCH)
else:
 run('git','-C',G,'worktree','add','--detach',DEST,base)
 run('git','-c','core.autocrlf=false','-C',DEST,'apply','--check',PATCH)
 run('git','-c','core.autocrlf=false','-C',DEST,'apply',PATCH)
manifest={}
files=[line.split('\t',2)[2] for line in run('git','apply','--numstat',PATCH).splitlines()]
for name in files:
 source=G/name;copy=DEST/name
 assert source.exists()==copy.exists(),name
 if source.exists():
  a,b=source.read_bytes(),copy.read_bytes()
  if name.endswith('.pal'):a,b=a.replace(b'\r\n',b'\n'),b.replace(b'\r\n',b'\n')
  assert a==b,name
  manifest[name]=hashlib.sha256(a).hexdigest()
names=json.loads((G/'data/maps/map_groups.json').read_text())['gMapGroup_Cherrygrove']
maps={}
for name in names:
 m=json.loads((G/'data/maps'/name/'map.json').read_text());maps[m['id']]=m
warps=0
for m in maps.values():
 for w in m['warp_events']:
  assert w['dest_map'] in maps,(m['name'],w)
  assert 0<=int(w['dest_warp_id'])<len(maps[w['dest_map']]['warp_events']),(m['name'],w)
  warps+=1
report=dict(base=base,files_reproduced=len(files),palette_line_endings_normalized=True,
            patch_sha256=hashlib.sha256(PATCH.read_bytes()).hexdigest(),
            maps=len(maps),warp_destinations_validated=warps)
(OUT/'evidence/source-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
(OUT/'evidence/warp-references.json').write_text(json.dumps(dict(maps=len(maps),valid_warp_references=warps),indent=2)+'\n')
(OUT/'evidence/reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
