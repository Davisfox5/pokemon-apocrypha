"""Preserve the complete isolated source as a portable patch; exclude ROM/save/tools."""
from pathlib import Path
import os,subprocess,tempfile,hashlib,json
R=Path(__file__).resolve().parents[4];G=R/'tools/vendor/gba/cherrygrove-synthesis-work';A=R/'gba/art/cherrygrove-synthesis'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='cherrygrove-source-index-') as d:
 env=dict(os.environ,GIT_INDEX_FILE=str(Path(d)/'index'))
 def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false','-C',str(G),*args],env=env)
 git('read-tree','HEAD');new=[p for p in git('ls-files','--others','--exclude-standard','-z').decode().split('\0') if p]
 assert all(p.startswith(('data/','graphics/','src/','include/')) for p in new),new
 raw=[str(p.relative_to(G)) for folder in ['johto_restart','sandgem','floccesy'] for p in (G/'graphics/door_anims'/folder).glob('*.4bpp')]
 git('add','-N','-f','--',*new,*raw);data=git('diff','--binary','--no-ext-diff');patch=R/'gba/cherrygrove-synthesis.patch';patch.write_bytes(data);git('apply','--reverse','--check',str(patch));git('read-tree','HEAD');git('apply','--cached','--check',str(patch))
 (A/'evidence/patch.json').write_text(json.dumps(dict(base=git('rev-parse','HEAD').decode().strip(),standalone=True,includes_preserved_existing_owner_work=True,bytes=len(data),sha256=sha(patch),forward_check=True,reverse_check=True),indent=2)+'\n')
 print('Portable source patch:',len(data),'bytes')
