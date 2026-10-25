#!/usr/bin/env python3
"""Decode Pallet's HGSS room meshes and bm_room models. No reference archive writes.
Only the room and isolated props are reference data; the renderer's off-room fill is excluded.
"""
from pathlib import Path
import hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'route29_catalog'))
import hgss_render as R
P=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve()
for name,matrix in [('Red1F',246),('Red2F',247),('OakHouse',248),('Lab',250)]:
 def load(phg,matrix=matrix):
  a=phg/'files/a';land=R.narc.load(a/'0/6/5');area=R.narc.load(a/'0/4/2')[43];build,ms=struct.unpack_from('<HH',area)
  texture=R.Tex0(R.narc.load(a/'0/4/4')[ms]);models=R.narc.load(phg/'files/fielddata/build_model/bm_room.narc')
  p=next((phg/'files/fielddata/mapmatrix/map_matrix').glob(f'map_matrix_{matrix:04d}*'));d=p.read_bytes();w,h,headers,alt,nl=d[:5];off=5+nl+(2*w*h if headers else 0)+(w*h if alt else 0);ids=struct.unpack_from('<'+'H'*(w*h),d,off)
  return land,texture,models,[dict(cx=x,cz=y,land=ids[y*w+x]) for y in range(h) for x in range(w)],dict(area_bank=43,map_texture_set=ms,building_texture_set=build,matrix=matrix)
 R.load=load;dest=OUT/name;R.main(P,dest)
 p=dest/'hgss-render.json';j=json.loads(p.read_text());j['source']['archives'].pop('files/a/0/4/0');f='files/fielddata/build_model/bm_room.narc';j['source']['archives'][f]=hashlib.sha256((P/f).read_bytes()).hexdigest();j['scope']='Off-room nearest fill excluded; only original mesh surfaces and isolated props are used.';p.write_text(json.dumps(j,indent=2)+'\n')
