"""Check locked Johto tree masters, active aliases and retired-file exclusion."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[4]
PACK=ROOT/'gba/art/johto-common/trees'

def rgba(p):
    im=Image.open(p);a=np.array(im.convert('RGBA'))
    if im.mode=='P':a[...,3]=np.where(np.array(im)==0,0,255)
    a[a[...,3]==0]=0
    return a


def main():
    catalog=json.loads((PACK/'catalog.json').read_text())
    assert [r['id'] for r in catalog['assets']]==['T01','T02','T03','T04','T05']
    for r in catalog['assets']:
        path=PACK/r['master'];a=rgba(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256'],path
        assert np.array_equal(a,rgba(PACK/r['indexed'])),r['id']
    for key,digest in json.loads((PACK/'locked-designs.json').read_text())['sha256'].items():
        assert hashlib.sha256((PACK/f'source/{key}.png').read_bytes()).hexdigest()==digest, ('Selected tree design changed',key)
    retirement=json.loads((PACK/'retired-assets.json').read_text())
    restored=[r['path'] for r in retirement['removed'] if (ROOT/r['path']).exists()]
    assert not restored, ('Retired Johto tree assets were restored',restored)
    for rel in retirement['active_large_tree_aliases']:
        master='T02' if Path(rel).stem=='blossom' else 'T01'
        assert np.array_equal(rgba(ROOT/rel),rgba(PACK/f'source/{master}.png')),rel
    assert np.array_equal(rgba(PACK/'source/T05.png')[:,:16],rgba(PACK/'source/T05-intact.png'))
    print(f"PASS: 5 tree masters; 5 matching large-tree aliases; {len(retirement['removed'])} retired files absent; native Cut frame preserved")

if __name__=='__main__':main()
