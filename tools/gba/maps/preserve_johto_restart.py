#!/usr/bin/env python3
"""Preserve a standalone engine patch directly above clean Emerald town baseline."""
from pathlib import Path
import os,subprocess,tempfile,json,hashlib
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';A=R/'gba/art/johto-restart'
with tempfile.TemporaryDirectory(prefix='johto-restart-index-') as d:
 env=dict(os.environ,GIT_INDEX_FILE=str(Path(d)/'index'))
 def git(*args):return subprocess.check_output(['git','-C',str(G),*args],env=env)
 git('read-tree','HEAD')
 new=git('ls-files','--others','--exclude-standard','-z').decode().split('\0');new=[p for p in new if p]
 raw=[str(p.relative_to(G)) for p in (G/'graphics/door_anims/johto_restart').glob('*.4bpp')]
 git('add','-N','-f','--',*new,*raw)
 data=git('diff','--binary','--no-ext-diff');patch=R/'gba/johto-restart.patch';patch.write_bytes(data)
 git('apply','--reverse','--check',str(patch));git('read-tree','HEAD');git('apply','--cached','--check',str(patch))
 report=dict(standalone_patch=True,requires_previous_art_patches=False,rejected_v4_inputs=False,base=git('rev-parse','HEAD').decode().strip(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),forward_check=True,reverse_check=True)
 (A/'evidence/patch.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
