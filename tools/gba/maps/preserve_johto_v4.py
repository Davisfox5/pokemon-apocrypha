#!/usr/bin/env python3
"""Export only v4 above the four preserved preview patches, using a private index."""
from pathlib import Path
import os,subprocess,tempfile,hashlib,json
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-v4-game';A=R/'gba/art/johto-v4'
patches=[R/'gba'/p for p in ['johto-art-v3.patch','johto-npc-v1.patch','johto-cast-v1.patch','regional-scale-v1.patch']]
def run(args,env,**kw):return subprocess.check_output(['git','-C',str(G),*args],env=env,**kw)
with tempfile.TemporaryDirectory(prefix='johto-v4-index-') as d:
 env=dict(os.environ,GIT_INDEX_FILE=str(Path(d)/'index'))
 def base():
  run(['read-tree','HEAD'],env)
  for p in patches:run(['apply','--cached',str(p)],env)
 base()
 changed=run(['ls-files','--others','--exclude-standard','-z'],env).decode().split('\0');changed=[p for p in changed if p]
 raw=[str(p.relative_to(G)) for directory in [G/'graphics/tilesets/johto_v4',G/'graphics/door_anims/johto_v4'] for p in directory.glob('*.4bpp')]
 if changed+raw:run(['add','-N','-f','--',*changed,*raw],env)
 patch=run(['diff','--binary','--no-ext-diff'],env);assert patch
 out=R/'gba/johto-v4.patch';out.write_bytes(patch)
 run(['apply','--reverse','--check',str(out)],env)
 base();run(['apply','--cached','--check',str(out)],env)
 report=dict(patch=str(out.relative_to(R)),bytes=len(patch),sha256=hashlib.sha256(patch).hexdigest(),base=run(['rev-parse','HEAD'],env).decode().strip(),prior_patches=[str(p.relative_to(R)) for p in patches],forward_check=True,reverse_check=True)
 (A/'evidence/patch.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
