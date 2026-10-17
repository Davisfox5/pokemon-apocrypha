from pathlib import Path
import sys,json,re,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.rollout_review import scene
from johto_common.rollout import P,dump
from tiles import Tileset
B=Path(sys.argv[1]);G=Path(sys.argv[2]);EXPORT=Path(sys.argv[3]);C=json.load(open(P/'source/initial-inventory.json'));checks=[]
for c in C:
 name=c['map'];a,*_=scene(G,c);p=np.array(Image.open(EXPORT/(name+'.png')).convert('RGBA'));assert np.array_equal(a,p),name;checks.append({'map':name,'porymap_exact':True})
layouts=json.load(open(G/'data/layouts/layouts.json'))['layouts'];graphics=(G/'src/data/tilesets/graphics.h').read_text()
for name in ['VioletCityEntrance','CherrygroveRegionalPreview29','CherrygroveRegionalPreview30']:
 l=next(l for l in layouts if l['name']==name+'_Layout');sym='gTilesetTiles_'+l['secondary_tileset'].removeprefix('gTileset_');sec=re.search(re.escape(sym)+r'\[\].*?"data/tilesets/secondary/([^/]+)/tiles.png"',graphics)[1];c=dict(map=name,layout=l,primary='cherrygrove',secondary=sec)
 a,g,at,_=scene(B,c);b,h,bt,_=scene(G,c);assert np.array_equal(a,b) and np.array_equal(at,bt) and np.array_equal(g,h);checks.append({'map':name,'unrelated_preview_exact':True})
for pri in ['cherrygrove','johto_cherrygrove','johto_route36']:
 path='data/tilesets/primary/'+pri+'/tiles.png';a=np.array(Image.open(B/path));b=np.array(Image.open(G/path));assert np.array_equal(a[:40],b[:40]) # 80 graphics, then reserve through 92 below
 for i in range(93):
  y,x=i//16*8,i%16*8;assert np.array_equal(a[y:y+8,x:x+8],b[y:y+8,x:x+8]),(pri,i)
 checks.append({'primary':pri,'animation_graphics_0_through_92_unchanged':True})
reg=json.load(open(ROOT/'gba/art/johto-common/approved-tilesets.json'))
for v in reg['masters']:assert hashlib.sha256((ROOT/v['path']).read_bytes()).hexdigest()==v['sha256']
checks.append({'canonical_master_hashes_verified':len(reg['masters'])});dump(P/'evidence/shared-checks.json',checks);print('PASS',len(checks),'checks')
