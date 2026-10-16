"""Validate reference provenance, complete source images and catalog links."""
from pathlib import Path
import argparse,hashlib,json,re,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.trees import rgba,sha
from johto_common.rock_native import Native
from tiles import Tileset
P=ROOT/'gba/art/johto-common/rocks'
def main(donors):
    catalog=json.loads((P/'catalog.json').read_text());ids=set();records=catalog['records']
    for r in records:
        assert r['id'] not in ids;ids.add(r['id']);path=P/r['image'];a=Image.open(path)
        assert list(a.size)==r['size'] and sha(path)==r['sha256']
        for key in ['full','metatiles']:
            if r.get(key):assert (P/r[key]).is_file()
        source=r['source']
        if source.get('path'):assert sha(ROOT/source['path'])==source['sha256']
        if source.get('source_piece_ids'):assert all((P/'pieces'/f'{k}.png').exists() for k in source['source_piece_ids'])
    raw=json.loads((P/'source-data/records.json').read_text())
    for r in raw:
        a=Image.open(P/'source-data'/r['file']).convert('RGBA')
        digest=hashlib.sha256(a.tobytes()+str(a.size).encode()).hexdigest();assert digest==r['pixel_sha256']
        assert np.array_equal(np.array(a),rgba(P/'pieces'/f'{r["id"]}.png')),r['id']
    assert not json.loads((P/'source-data/errors.json').read_text())
    # Compare native decoding against the established Emerald decoder, including
    # a primary rock wall and secondary cave samples from each selected map.
    for r in records:
        if r['group']!='Emerald':continue
        game=donors/'pokeemerald';layout=next(l for l in json.loads((game/'data/layouts/layouts.json').read_text())['layouts'] if l['name']==r['source']['layout'])
        n=Native(game,layout);other=Tileset(game,Path(n.paths[1]).name,Path(n.paths[0]).name)
        for mid in r['metatile_ids']:assert np.array_equal(n.tile(mid),np.array(other.render(mid))), (r['id'],mid)
    text=(P/'review.html').read_text()
    for target in re.findall(r'href="([^"]+)"',text):assert (P/target).exists(),target
    assert text.count('<article ')==len(records)
    print(f'PASS: {len(records)} catalog entries; {len(raw)} complete source images; hashes, native Emerald decoding and all links valid; no unresolved palettes')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--donors',type=Path,required=True);main(p.parse_args().donors)
