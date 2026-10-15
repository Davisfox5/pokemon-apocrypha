"""Validate native pixel preservation and independent terrain in scenery exports."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.trees import rgba
P=ROOT/'gba/art/johto-common/scenery'

def main():
    entries=json.loads((P/'catalog.json').read_text())['assets'];ids=set()
    billboard=np.array(Image.open(ROOT/'gba/art/johto-cohesion/references/egrass_u.png').convert('RGBA'))
    foliage=(billboard[...,3]>0)&~np.all(billboard[...,:3]==(123,123,123),axis=2)
    changed=removed=0
    for r in entries:
        key=r['id'];assert key not in ids;ids.add(key)
        a=rgba(P/r['input']);b=rgba(P/r['master']);keep=b[...,3]>0
        assert a.shape==b.shape and np.all(a[keep,3]>0),key
        assert np.array_equal(a[keep,:3],b[keep,:3]), ('Changed source color',key)
        assert set(np.unique(b[...,3]))<={0,255} and np.all(b[~keep]==0),key
        assert np.array_equal(b,rgba(P/f'source/{key}.idx.png')), ('Native palette round trip',key)
        assert hashlib.sha256((P/r['master']).read_bytes()).hexdigest()==r['sha256'],key
        count=int(((a[...,3]>0)&~keep).sum());assert count==r['removed_background_pixels'],key
        removed+=count;changed+=count>0
        if key.startswith('N'):
            assert np.array_equal(a,b), ('Native object animation changed',key)
            indices=np.array(Image.open(P/f'source/{key}.idx.png'))
            assert hashlib.sha256(indices.tobytes()).hexdigest()==r['native_index_sha256'], ('Native OBJ palette indices changed',key)
        if key.startswith('G'):
            blades=(a[...,3]>0)&~np.all(a[...,:3]==(32,112,80),axis=2)
            assert np.all(keep[blades]), ('Grass blade removed',key)
            assert np.all(keep[foliage&(a[...,3]>0)]), ('HGSS shaded foliage removed',key)
        if key in ['P03','P04']:
            assert not np.any(keep&np.all(b[...,:3]==(56,184,232),axis=2)),key
        if key in ['L11','L12','L13']:
            assert not np.any(keep&np.all(b[...,:3]==(72,152,112),axis=2)),key
    assert len(ids)==51
    print(f'PASS: {len(ids)} assets; {changed} terrain masks separated; {removed} background pixels cleared; retained colors, 4bpp exports and native animation sheets exact')

if __name__=='__main__':main()
