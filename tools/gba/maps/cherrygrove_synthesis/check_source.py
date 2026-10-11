"""Compare the private engine with its reproduced source and previous scope."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[4];A=R/'gba/art/cherrygrove-synthesis';E=A/'evidence';G=R/'tools/vendor/gba/cherrygrove-synthesis-work';P=R/'tools/vendor/gba/cherrygrove-synthesis-reproduction'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=re.findall(r'^diff --git a/(.*?) b/',(R/'gba/cherrygrove-synthesis.patch').read_bytes().decode('latin1'),re.M)
lineend=[]
for f in files:
 a=(G/f).read_bytes();b=(P/f).read_bytes()
 if a!=b:
  assert f.endswith('.pal') and a.replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n'),f
  lineend.append(f)
old=json.loads(subprocess.check_output(['git','show','HEAD:gba/art/cherrygrove-synthesis/evidence/source-manifest.json'],cwd=R))
manifest={f:sha(G/f) for f in files};changed=[f for f,h in manifest.items() if old.get(f)!=h]
def allowed(f):
 return f.startswith(('data/tilesets/primary/cherrygrove/','data/tilesets/secondary/cherrygrove/','data/layouts/Cherrygrove','graphics/door_anims/johto_restart/')) or f in ['include/tileset_anims.h','src/data/tilesets/headers.h','src/field_door.c','src/tileset_anims.c']
assert all(allowed(f) for f in changed),changed
for f in (A/'references/E/data/maps').glob('*/map.json'):
 assert f.read_bytes()==(G/f.relative_to(A/'references/E')).read_bytes(),f
(E/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(E/'reproduction.json').write_text(json.dumps(dict(patch_files=len(files),fresh_checkout_and_generator_match=True,palette_line_endings_only=lineend,base='f09ec1de2e6754e9f9a8e02281d3d773efcfa65e'),indent=2)+'\n')
(E/'detail-preservation.json').write_text(json.dumps(dict(previous_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),events_warps_unchanged=True,non_cherrygrove_sources_unchanged=True,changed_source_paths=changed,refined_assets={p.name:sha(p) for p in (A/'refined').glob('*.png')},mask_source_sha256=sha(R/'tools/gba/maps/cherrygrove_synthesis/refine.py'),hgss_reference_sha256=sha(R/'gba/art/johto-v1/references/cherrygrove-hgss.png')),indent=2)+'\n')
print('Reproduced',len(files),'files; scoped changes:',len(changed))
