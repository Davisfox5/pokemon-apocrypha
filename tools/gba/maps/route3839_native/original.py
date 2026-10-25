"""Fresh original HGSS reference render; shared accepted renderer, independent route grid."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
p=ROOT/'tools/gba/maps/route29_catalog/hgss_render.py';spec=importlib.util.spec_from_file_location('original_hgss_renderer',p);R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
class TerrainOnly:
 def __init__(self,model):self.model=model
 def __getattr__(self,n):return getattr(self.model,n)
 def faces(self):
  return [(mid,vs) for mid,vs in self.model.faces() if self.model.mat_tex.get(mid,'').startswith(('grass','road','wall','cliff','slope','r_climb'))]
PHG=Path(sys.argv[1]);S=ROOT/'gba/art/route38-39-native/source';S.mkdir(exist_ok=True,parents=True)
for route in [38,39]:
 R.AREA_BANK=7;R.HEADER_ID=route+4;R.MATERIAL_NAMES.clear();R.SNAP=False
 d=S/f'route{route}-hgss';d.mkdir(exist_ok=True)
 r=R.render(PHG);r['full'].save(d/'original.png');r['terrain'].save(d/'terrain.png');r['fg'].save(d/'foreground.png')
 land,tex,models,chunks,meta=R.load(PHG);W,H=r['types'].shape[1],r['types'].shape[0];flat=R.Canvas(W*16,H*16);cleared=R.Canvas(W*16,H*16)
 for c in chunks:
  ch=R.hgss_map.MapChunk.parse(land[c['land']]);ox,oz=c['cx']*32,c['cz']*32
  R.draw_model(flat,R.mdlview.Model(ch.model),tex,lambda x,y,z,ox=ox,oz=oz:(x+16+ox,y,z+16+oz),-1,None,flat=True)
  R.draw_model(cleared,TerrainOnly(R.mdlview.Model(ch.model)),tex,lambda x,y,z,ox=ox,oz=oz:(x+16+ox,y,z+16+oz),-1,None,flat=True)
 Image.fromarray(np.clip(flat.rgb,0,255).astype(np.uint8)).save(d/'flat.png')
 Image.fromarray(np.clip(cleared.rgb,0,255).astype(np.uint8)).save(d/'cleared-flat.png')
 np.savez_compressed(d/'cleared.npz',height=cleared.height,material=cleared.mat,names=np.array(R.MATERIAL_NAMES),rgb=cleared.rgb.astype(np.uint8),defined=cleared.depth>-1e8)
 np.savez_compressed(d/'decoded.npz',height=flat.height,material=flat.mat,names=np.array(R.MATERIAL_NAMES),rgb=flat.rgb.astype(np.uint8),types=r['types'],collision=r['collision'])
 (d/'reference.json').write_text(json.dumps(dict(route=route,source_repository='pret/pokeheartgold',revision='6988158691eb6178cff697cda0428045ddcba5fb',px_per_original_cell=16,native_offset=[0,0],chunks=chunks,meta=meta,buildings=r['buildings'],archive_sha256={a:hashlib.sha256((PHG/a).read_bytes()).hexdigest() for a in ['files/a/0/6/5','files/a/0/4/2','files/a/0/4/4','files/a/0/4/0']}),indent=2)+'\n')
 print(route,W,H,meta,'materials',R.MATERIAL_NAMES)
