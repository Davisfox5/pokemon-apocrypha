"""Read four original HGSS chunks only; orthogonal road mesh + BDHC planes.
Requires apicula-converted glTFs. This reads original data, never native layouts.
"""
from pathlib import Path
import sys,json,struct,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'tools/mapeditor'),str(ROOT/'tools/hoennconv')]
from mapdata import MapMatrix
from hgss_map import MapChunk
import narc
D=Path(sys.argv[1]);GL=Path(sys.argv[2]);S=ROOT/'gba/art/route38-39-terrain/source/refinement';E=S.parent.parent/'evidence/refinement'
land=narc.load(D/'land.narc');matrix=MapMatrix.load(D/'matrix.bin')
def triangles(p):
 d=json.loads(p.read_text());b=(p.parent/d['buffers'][0]['uri']).read_bytes()
 def acc(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];n={'VEC3':3,'VEC2':2,'VEC4':4,'SCALAR':1,'MAT4':16}[a['type']];return np.frombuffer(b,dtype=dt,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 out=[]
 for m in d['meshes']:
  for pr in m['primitives']:
   name=d['materials'][pr['material']]['name'];pos=acc(pr['attributes']['POSITION']);ind=acc(pr['indices']).reshape(-1,3)
   for tri in ind:
    if name.startswith(('road01','wall01','wall_area06','slope','grass_slope','allpeak')):out.append(dict(material=name,xyz=(pos[tri]/16).tolist()))
 return out
provenance=[]
for mid,name in [(54,'map09_05c'),(55,'map10_05c'),(56,'map08_05c'),(57,'map08_06c')]:
 c=MapChunk.parse(land[mid]);b=c.bdhc;pc,vc,hc,plc,sc,ac=struct.unpack_from('<6H',b,4);o=16
 pts=np.array([struct.unpack_from('<2i',b,o+i*8) for i in range(pc)])/65536;o+=pc*8
 vec=np.array([struct.unpack_from('<3i',b,o+i*12) for i in range(vc)])/4096;o+=vc*12
 hs=np.array(struct.unpack_from('<'+'i'*hc,b,o))/65536;o+=hc*4
 planes=[]
 for i in range(plc):
  p1,p2,v,h=struct.unpack_from('<4H',b,o+i*8);planes.append(dict(rect=[*(pts[p1]+16),*(pts[p2]+16)],normal=vec[v].tolist(),distance=float(hs[h])))
 # The four extra BDHC arrays are retained in the scoped raw source member.
 (S/f'chunk{mid}.bdhc').write_bytes(b)
 (S/f'chunk{mid}-geometry.json').write_text(json.dumps(dict(member=mid,planes=planes,triangles=triangles(GL/(name+'.gltf'))),separators=(',',':'))+'\n')
 # Cross-check plane sign/scale against the original building's Y coordinate.
 anchors=[]
 for i in range(0,len(c.buildings),48):
  model=struct.unpack_from('<I',c.buildings,i)[0];x,y,z=[struct.unpack_from('<i',c.buildings,i+j)[0]/65536 for j in [4,8,12]]
  anchors.append(dict(model=model,x=x+16,y=y,z=z+16))
 provenance.append(dict(member=mid,model=name,original_chunk_sha256=hashlib.sha256(land[mid]).hexdigest(),bdhc_sha256=hashlib.sha256(b).hexdigest(),building_height_anchors=anchors,coordinate_rule='model XYZ /16 world units; BDHC point/65536 gives16-unit tiles, normal/4096; y=-(nx*x+nz*z+d)/ny; local origin+16'))
(S/'original-source.json').write_text(json.dumps(dict(repository='pret/pokeheartgold',land_path='files/a/0/6/5',land_sha256=hashlib.sha256((D/'land.narc').read_bytes()).hexdigest(),matrix_path='files/fielddata/mapmatrix/map_matrix/map_matrix_0000_EVERYWHERE.bin',matrix_sha256=hashlib.sha256((D/'matrix.bin').read_bytes()).hexdigest(),members=provenance,scope='only map members54..57; no original terrain collision claim for cleared foreground',mesh_conversion='apicula 0.1.1-dev glTF, source revision recorded in README'),indent=2)+'\n')
print('Extracted four original height tables and terrain meshes')
