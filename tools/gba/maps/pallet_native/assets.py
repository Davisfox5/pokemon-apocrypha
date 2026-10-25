"""Render HGSS models directly with one coherent native orthographic camera.
No piecewise image stretching. Original models and textures are read-only inputs.
"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/gba/maps/route29_catalog'))
import hgss_render as R
from mesh import faces
RAW=Path('/workspace/tooling/pallet-rebuild-reference');PHG=Path('/workspace/tooling/pokeheartgold')
OUT=ROOT/'gba/art/pallet-native/source/assets';OUT.mkdir(parents=True,exist_ok=True)
field=R.narc.load(PHG/'files/a/0/4/0');rooms=R.narc.load(PHG/'files/fielddata/build_model/bm_room.narc')
meta={n:json.loads((RAW/n/'hgss-render.json').read_text()) for n in ('','Red1F','Red2F','OakHouse','Lab')}
records=[]
class LitMaterial:
    def __init__(self,base,shade):self.base=base;self.tex=base.tex;self.alpha=base.alpha;self.uid=base.uid;self.shade=shade
    def sample(self,s,t):
        a=self.base.sample(s,t).copy();a[...,:3]=np.minimum(255,a[...,:3]*self.shade).astype(np.uint8);return a

def draw_lit(canvas,m,place,owner):
    for mid,verts in faces(m,R.mdlview):
        mat=R.Material(m,mid,m.tex)
        if mat.tex is None or mat.alpha<31:continue
        world=np.array([place(*v[0]) for v in verts]);n=np.cross(world[1]-world[0],world[2]-world[0]);n=n/max(1e-8,np.linalg.norm(n))
        shade=np.clip(.68+.32*abs(n[1])+.12*abs(n[2])-.12*n[0],.60,1.03)
        color=np.mean([v[2] for v in verts],axis=0)
        lm=LitMaterial(mat,shade*color);scr=[(x*R.PX,(z-y)*R.PX) for x,y,z in world];depth=[z+y+.01*y for x,y,z in world];uv=[v[1] for v in verts]
        for tri in ([(0,1,2)] if len(verts)==3 else [(0,1,2),(0,2,3)]):
            canvas.tri([scr[i] for i in tri],[uv[i] for i in tri],[depth[i] for i in tri],lm,owner,hgt=[world[i][1] for i in tri])

def render(name,room,ids,scale=(1,0.65,0.65)):
    bs=[meta[room]['buildings'][i] for i in ids]
    anchor=bs[0]['pos'];canvas=R.Canvas(512,512);S=2
    # Supersampling resolves diagonal mesh edges before native palette assignment.
    R.PX=16*S
    for idx,b in zip(ids,bs):
        m=R.mdlview.Model((rooms if room else field)[b['model']])
        pos=b['pos'];s=b['scale']
        def place(x,y,z):
            return (8+(x*s[0]+pos[0]-anchor[0])*scale[0],(y*s[1]+pos[1]-anchor[1])*scale[1],10+(z*s[2]+pos[2]-anchor[2])*scale[2])
        draw_lit(canvas,m,place,idx)
    a=np.dstack([np.clip(canvas.rgb,0,255).astype(np.uint8),np.where(canvas.depth>-1e8,255,0).astype(np.uint8)])
    im=Image.fromarray(a).resize((256,256),Image.Resampling.BOX);a=np.array(im);a[...,3]=np.where(a[...,3]>=128,255,0);a[...,:3]&=248
    im=Image.fromarray(a);bbox=im.getbbox();im=im.crop(bbox);im.save(OUT/(name+'.png'))
    owner_boxes={}
    for idx in ids:
        ys,xs=np.where(canvas.owner==idx)
        if len(xs):owner_boxes[str(idx)]=[int(xs.min()/2)-bbox[0],int(ys.min()/2)-bbox[1],int(xs.max()/2)+1-bbox[0],int(ys.max()/2)+1-bbox[1]]
    records.append(dict(owner_boxes=owner_boxes,asset=name,room=room,instances=ids,models=[b['model'] for b in bs],camera_xyz=scale,native_size=im.size,crop=bbox))
    R.PX=16
    return im
if __name__=='__main__':
    render('house','',[3,4],(1.22,.78,.5))
    render('lab','',[5,6],(1.2,.82,.5))
    for name,ids in [('mailbox',[0]),('sign',[2]),('lab-sign',[7])]:render(name,'',ids,(1,.7,.7))
    for name,room,ids in [('kitchen','Red1F',[4,5]),('tv','Red1F',[3]),('dining','Red1F',[6,7,8,9,10]),('bookshelf','Red1F',[0]),('bed','Red2F',[0]),('desk','Red2F',[2,3]),('storage','Red2F',[5,6]),('console','Red2F',[7]),('research','Lab',[12,13]),('lab-desk','Lab',[5,6,10,11]),('research-table','Lab',[7]),('cabinet','Lab',[8]),('lab-machine','Lab',[15])]:render(name,room,ids,(1.25,.95,.9))
    for name,idx in [('sofa',101),('armchair',103),('plant',114),('coffee-table',89)]:
        meta['Red1F']['buildings'].append(dict(model=idx,pos=[0,0,0],scale=[1,1,1]))
        render(name,'Red1F',[len(meta['Red1F']['buildings'])-1],(1.25,.95,.9))
    (OUT/'models.json').write_text(json.dumps(records,indent=2)+'\n')
    ims=[Image.open(OUT/(r['asset']+'.png')).convert('RGBA') for r in records]
    big=Image.new('RGBA',(256,128),(120,152,112,255));big.alpha_composite(ims[0],(4,4));big.alpha_composite(ims[1],(120,8));big.save(OUT/'buildings.png')
