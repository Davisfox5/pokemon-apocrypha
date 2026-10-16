"""Project HGSS sign models into tile-aligned GBA art; trace side-stair treads.

The model geometry and texture snapshots are read-only extractions. Rendering is
orthographic, nearest-neighbor, with a fixed map-lighting conversion and a one-pixel
silhouette outline. Ground-shadow material h_kage is deliberately excluded.
"""
from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image
from johto_common.trees import rgba,sha
ROOT=Path(__file__).resolve().parents[4]
REF=ROOT/'gba/art/johto-common/scenery/references'
SIGN_NAMES={31:('P13','HGSS gray information plaque'),32:('P14','HGSS green rounded sign'),
            33:('P15','HGSS gym marker'),34:('P16','HGSS blue information board')}
STAIR_COLORS={(88,80,48):(80,80,80),(112,112,80):(104,104,104),
              (136,144,104):(136,136,136),(152,152,120):(160,160,160),
              (176,184,144):(192,192,192)}
STAIR_TOP=[8,8,8,8,8,8,7,4,4,4,4,3,0,0,0,48]

def extract(donor):
    sys.path.insert(0,str(ROOT/'tools/regionport'))
    from mdlview import Model
    REF.mkdir(parents=True,exist_ok=True);records=[]
    for number,(key,label) in SIGN_NAMES.items():
        rel=f'files/fielddata/build_model/bm_field/bm_field_{number:08d}.bin'
        path=donor/rel;m=Model(path.read_bytes());faces=[]
        for mat,face in m.faces():
            name=m.tex_name(mat)
            if name=='h_kage':continue
            texture=m.texture_image(mat);assert texture is not None
            texture.save(REF/(name+'.png'))
            faces.append(dict(texture=name,vertices=[list(p) for p,u in face],uv=[list(u) for p,u in face]))
        records.append(dict(id=key,label=label,model_id=number,donor_path=rel,
            donor_sha256=sha(path),faces=faces))
    (REF/'sign-models.json').write_text(json.dumps(dict(credit='Game Freak / Nintendo / Creatures',
        extraction='Decoded Model.faces() geometry; h_kage ground shadow omitted. No donor files modified.',models=records),indent=2)+'\n')

def render_sign(record):
    out=np.zeros((32,32,4),np.uint8);depth=np.full((32,32),-1e9)
    for face in record['faces']:
        tex=rgba(REF/(face['texture']+'.png'));verts=np.array(face['vertices']);uv=np.array(face['uv'])
        screen=np.column_stack((16+verts[:,0]*16,30-verts[:,1]*16*.68+verts[:,2]*16*.74))
        dep=verts[:,1]*.74+verts[:,2]*.68
        for j in range(1,len(verts)-1):
            ids=[0,j,j+1];ps=screen[ids];matrix=np.vstack((ps.T,np.ones(3)))
            if abs(np.linalg.det(matrix))<1e-8:continue
            inv=np.linalg.inv(matrix)
            for y in range(max(0,int(ps[:,1].min())),min(32,int(ps[:,1].max())+1)):
                for x in range(max(0,int(ps[:,0].min())),min(32,int(ps[:,0].max())+1)):
                    weights=inv@np.array([x+.5,y+.5,1])
                    if min(weights)<-1e-8:continue
                    z=weights@dep[ids]
                    if z<depth[y,x]:continue
                    u,v=weights@uv[ids]
                    c=tex[int(np.floor(v))%len(tex),int(np.floor(u))%tex.shape[1]].copy()
                    if not c[3]:continue
                    c[:3]=(np.round(c[:3].astype(float)*.82/8)*8).astype(np.uint8)
                    out[y,x]=c;depth[y,x]=z
    # HGSS edge marking is a render effect, absent from the texture itself.
    # Recreate its dark silhouette at native sprite scale, including post gaps.
    inside=out[:,:,3]>0;outline=np.zeros_like(inside)
    outline[1:]|=inside[:-1];outline[:-1]|=inside[1:]
    outline[:,1:]|=inside[:,:-1];outline[:,:-1]|=inside[:,1:]
    out[outline&~inside]=(32,32,32,255)
    assert not out[0,:,3].any() and not out[:,0,3].any() and not out[:,-1,3].any()
    return out

def sign_assets():
    data=json.loads((REF/'sign-models.json').read_text())
    for record in data['models']:
        yield record,render_sign(record)

def side_stairs():
    path=ROOT/'gba/art/route36/source/hgss-reference.png'
    a=rgba(path)[346:394,232:248].copy();b=a.copy();mask=np.zeros((48,16),bool)
    for old,new in STAIR_COLORS.items():
        matched=np.all(a[:,:,:3]==old,axis=2);mask|=matched;b[matched,:3]=new
    for x,top in enumerate(STAIR_TOP):mask[:top,x]=False
    b[~mask]=0
    return a,b

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--extract-signs-from',type=Path,required=True)
    extract(p.parse_args().extract_signs_from)
