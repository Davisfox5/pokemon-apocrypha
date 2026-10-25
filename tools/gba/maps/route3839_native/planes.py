"""Read original HGSS cells, height planes and terrain faces for Routes38/39."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'tools/hoennconv'),str(ROOT/'tools/mapeditor')]
from hgss_map import MapChunk
from mapdata import MapMatrix
import narc
RAW=Path(sys.argv[1]);GL=Path(sys.argv[2]);S=ROOT/'gba/art/route38-39-native/source';S.mkdir(parents=True,exist_ok=True)
land=narc.load(RAW/'land.narc');mm=MapMatrix.load(RAW/'matrix.bin')
def gltf_triangles(p):
 d=json.loads(p.read_text());b=(p.parent/d['buffers'][0]['uri']).read_bytes()
 def accessor(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];n={'VEC3':3,'VEC2':2,'VEC4':4,'SCALAR':1,'MAT4':16}[a['type']];return np.frombuffer(b,dtype=dt,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 result=[]
 for m in d['meshes']:
  for prim in m['primitives']:
   name=d['materials'][prim['material']]['name']
   if not name.startswith(('wall01','wall_area06','road01','slope','grass_slope')):continue
   pos=accessor(prim['attributes']['POSITION']);ids=accessor(prim['indices']).reshape(-1,3)
   for tri in ids:result.append(dict(material=name,xyz=(pos[tri]/16).tolist()))
 return result
models={54:'map09_05c',55:'map10_05c',56:'map08_05c',57:'map08_06c'};records=[]
for route,placements,W,H in [(38,[(54,0,0),(55,32,0)],64,32),(39,[(56,0,0),(57,0,32)],32,64)]:
 typ=np.zeros((H,W),np.uint8);col=typ.copy();height=np.full((H,W),np.nan);rise=np.zeros((H,W),bool);grass_ramp=rise.copy();road=Image.new('L',(W*16,H*16));walls=road.copy();mx=np.zeros((H,W));mz=mx.copy();top=np.full((H,W),-1.);bottom=np.full((H,W),99.);triangles=[]
 for mid,ox,oy in placements:
  c=MapChunk.parse(land[mid]);typ[oy:oy+32,ox:ox+32]=np.array(c.types,np.uint8).reshape(32,32);col[oy:oy+32,ox:ox+32]=np.array(c.collisions,np.uint8).reshape(32,32)
  blob=c.bdhc;pc,vc,hc,plc,_,_=struct.unpack_from('<6H',blob,4);off=16;pts=np.array([struct.unpack_from('<2i',blob,off+i*8) for i in range(pc)])/65536;off+=pc*8;vec=np.array([struct.unpack_from('<3i',blob,off+i*12) for i in range(vc)])/4096;off+=vc*12;dist=np.array(struct.unpack_from('<'+'i'*hc,blob,off))/65536;off+=hc*4
  for i in range(plc):
   p1,p2,v,di=struct.unpack_from('<4H',blob,off+i*8);x0,z0=pts[p1]+16;x1,z1=pts[p2]+16;a,b,cc=vec[v]
   for y,x in np.ndindex(32,32):
    if x0<=x+.5<x1 and z0<=y+.5<z1:
     height[y+oy,x+ox]=-(a*(x+.5-16)+cc*(y+.5-16)+dist[di])/b
     if abs(a)+abs(cc)>.01:rise[y+oy,x+ox]=True
  for t in gltf_triangles(GL/(models[mid]+'.gltf')):
   q=np.array(t['xyz']);q[:,0]+=ox+16;q[:,2]+=oy+16;triangles.append(dict(material=t['material'],xyz=q.tolist()))
   ps=[(float(v[0]*16),float(v[2]*16)) for v in q];name=t['material']
   if name.startswith('road01'):ImageDraw.Draw(road).polygon(ps,fill=255)
   if name=='grass_slope':
    for y,x in np.ndindex(H,W):
     if q[:,0].min()<=x+.5<q[:,0].max() and q[:,2].min()<=y+.5<q[:,2].max():grass_ramp[y,x]=True
   if not name.startswith(('wall01','wall_area06')):continue
   ImageDraw.Draw(walls).polygon(ps,fill=255);norm=np.cross(q[1]-q[0],q[2]-q[0]);nlen=np.linalg.norm(norm[[0,2]])
   if norm[1]<0:norm=-norm
   # Every occupied native square gets the original face normal and rise span.
   xa=max(0,int(np.floor(q[:,0].min())));xb=min(W,int(np.ceil(q[:,0].max())));ya=max(0,int(np.floor(q[:,2].min())));yb=min(H,int(np.ceil(q[:,2].max())))
   for y in range(ya,yb):
    for x in range(xa,xb):
     top[y,x]=max(top[y,x],float(q[:,1].max()));bottom[y,x]=min(bottom[y,x],float(q[:,1].min()))
     if nlen>.01:mx[y,x]+=norm[0]/nlen;mz[y,x]+=norm[2]/nlen
  records.append(dict(member=mid,matrix_xy=[next(i%mm.width for i,v in enumerate(mm.models) if v==mid),next(i//mm.width for i,v in enumerate(mm.models) if v==mid)],sha256=hashlib.sha256(land[mid]).hexdigest(),bdhc_sha256=hashlib.sha256(blob).hexdigest()))
 known=np.isfinite(height);from scipy.ndimage import distance_transform_edt
 ids=distance_transform_edt(~known,return_distances=False,return_indices=True);height[~known]=height[tuple(ids[:,~known])]
 wallarea=np.array(walls)>0;roadarea=np.array(road)>0;wcover=wallarea.reshape(H,16,W,16).transpose(0,2,1,3).mean((2,3));rcover=roadarea.reshape(H,16,W,16).transpose(0,2,1,3).mean((2,3))
 np.savez(S/f'route{route}-original.npz',types=typ,collision=col,height=height,height_known=known,incline=rise,grass_ramp=grass_ramp,wall_coverage=wcover,road_coverage=rcover,normal_x=mx,normal_z=mz,wall_top=top,wall_bottom=bottom)
 (S/f'route{route}-terrain-mesh.json').write_text(json.dumps(triangles,separators=(',',':'))+'\n')
 # Readable original material and collision bytes, before any adaptation.
 for name,a in [('types',typ),('collision',col)]:
  (S/f'route{route}-original-{name}.txt').write_text('\n'.join(' '.join(f'{v:02x}' for v in row) for row in a)+'\n')
(S/'reference.json').write_text(json.dumps(dict(original_repository='pret/pokeheartgold',source_commit='6988158691eb6178cff697cda0428045ddcba5fb',land_path='files/a/0/6/5',land_sha256=hashlib.sha256((RAW/'land.narc').read_bytes()).hexdigest(),members=records,grid='one original16-unit DS cell to one native16px cell; Route38 64x32, Route39 32x64',material_rule='Original material, traversal byte and height are independent. Road dirt is read at 8px from foreground-free original textures, not a footstep flag or road-mesh bounds. Missing ground beneath removed foreground is lawn, declared as uncertain and excluded from original-match claims.',height_rule='BDHC plane equation with original vector/4096 and distance/65536; unknown blocking backing inferred explicitly.'),indent=2)+'\n')
print('Original material, traversal, height and terrain-face records written')
