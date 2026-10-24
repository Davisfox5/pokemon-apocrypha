"""Fresh Mahogany native construction from original geography and shared Johto art.

No earlier Mahogany layout, rendered map, layers, palette or tileset is an input.
The only geographic input is the newly decoded original land_data chunk 85.
"""
from pathlib import Path
import json,sys,os
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent))
ART=ROOT/'gba/art/mahogany-rebuild';SRC=ART/'source';EV=ART/'evidence'
APP=ROOT/'gba/art/cherrygrove-synthesis/refined'
N=36;O=2;PX=16

def rgba(p):return np.array(Image.open(p).convert('RGBA'))
def stamp(dst,a,x,y):
    h,w=a.shape[:2];m=a[...,3]>0;dst[y:y+h,x:x+w][m]=a[m]
def rgb5(a):return ((a.astype(np.uint16)>>3)<<3).astype(np.uint8)
def save(a,p):Image.fromarray(a).save(p)

def towers():
    im=Image.new('RGBA',(32,64));d=ImageDraw.Draw(im)
    dark=(64,61,45);wood=(130,109,68);light=(176,150,94);shadow=(91,87,55)
    d.ellipse((3,56,29,63),fill=(84,119,75,255))
    for x in (6,23):
        d.rectangle((x,29,x+3,58),fill=dark);d.rectangle((x+1,30,x+2,57),fill=wood)
    d.line((9,35,24,53),fill=dark,width=4);d.line((8,36,23,54),fill=wood,width=2)
    d.line((24,35,9,53),fill=dark,width=4);d.line((24,36,9,54),fill=light,width=2)
    d.rectangle((3,26,29,34),fill=dark);d.rectangle((4,26,28,31),fill=wood)
    for x in range(5,29,4):d.line((x,27,x,31),fill=light)
    d.polygon([(1,5),(15,0),(30,5),(30,26),(1,26)],fill=(75,48,35))
    d.rectangle((3,7,28,24),fill=(155,62,34));d.rectangle((5,8,26,21),fill=(190,85,42))
    d.line((4,23,27,23),fill=(112,47,29),width=2)
    d.line((6,9,6,20),fill=(215,114,57));d.line((9,8,25,8),fill=(224,131,69))
    d.rectangle((13,9,19,17),fill=(95,81,57));d.rectangle((14,10,18,16),fill=(173,183,126));d.line((16,10,16,16),fill=(238,228,158))
    return np.array(im)

def gate():
    im=Image.new('RGBA',(96,96));d=ImageDraw.Draw(im)
    edge=(58,73,66);teal=(48,139,130);tlight=(95,187,166);cream=(231,221,181);shade=(169,159,125)
    d.rectangle((9,29,86,87),fill=edge);d.rectangle((11,30,84,86),fill=teal)
    for x in (12,75):
        d.rectangle((x,29,x+8,85),fill=(38,116,108))
        for y in range(33,85,12):d.rectangle((x+1,y,x+6,y+7),fill=tlight)
    d.rectangle((22,31,73,84),fill=cream);d.rectangle((23,32,72,37),fill=shade)
    for x in range(25,72,12):
        d.rectangle((x,40,x+9,54),fill=(62,116,127));d.rectangle((x+1,41,x+8,52),fill=(106,185,210));d.line((x+1,47,x+7,41),fill=(204,232,221),width=2)
    d.rectangle((29,59,66,66),fill=edge);d.rectangle((30,58,65,63),fill=tlight)
    d.rectangle((32,67,63,87),fill=(48,53,49))
    for y in (82,87,92):d.rectangle((32,y,63,y+3),fill=(152,151,134));d.line((34,y,61,y),fill=(207,201,174))
    d.polygon([(3,8),(15,0),(80,0),(92,8),(92,29),(3,29)],fill=(104,81,54))
    d.polygon([(5,9),(16,2),(79,2),(90,9),(90,25),(5,25)],fill=(189,151,91))
    for y in range(5,25,6):
        d.line((9,y,87,y),fill=(147,111,67))
        for x in range(10+(y//6%2)*6,87,12):d.line((x,y+1,x,y+4),fill=(222,183,114))
    d.line((4,27,91,27),fill=(231,199,135));d.line((16,2,79,2),fill=(238,207,147))
    return np.array(im)

def antenna():
    im=Image.new('RGBA',(48,64));d=ImageDraw.Draw(im)
    d.ellipse((14,52,35,63),fill=(124,94,53));d.ellipse((16,52,33,59),fill=(82,69,40));d.rectangle((23,42,26,56),fill=(104,82,45))
    colors=[(52,83,44),(75,108,52),(99,133,66),(130,158,82)]
    for y,w in [(18,9),(25,12),(33,16),(42,18)]:
        d.polygon([(24,y-13),(24-w,y+6),(17,y+6),(17,y+9),(31,y+9),(31,y+6),(24+w,y+6)],fill=colors[0])
        d.polygon([(24,y-11),(24-w+3,y+4),(24,y+1),(24+w-4,y+4)],fill=colors[1])
        d.line((24,y-9,19,y+1),fill=colors[2],width=2)
    d.line((24,0,24,15),fill=(60,68,59),width=3);d.line((24,0,24,14),fill=(216,222,195))
    d.line((14,4,22,13),fill=(60,68,59),width=3);d.line((15,3,22,11),fill=(216,222,195))
    d.line((33,4,26,12),fill=(60,68,59),width=3);d.line((33,3,27,10),fill=(216,222,195))
    return np.array(im)

def sign():
    im=Image.new('RGBA',(16,32));d=ImageDraw.Draw(im);d.rectangle((7,14,9,29),fill=(88,88,53));d.ellipse((3,27,13,31),fill=(72,125,86));d.rectangle((1,5,14,20),fill=(91,94,61));d.rectangle((2,5,13,17),fill=(220,210,158));d.line((3,7,12,7),fill=(248,239,189))
    for y in (10,13,16):d.line((4,y,11-(y%2),y),fill=(161,149,101))
    return np.array(im)

def original_terrain(phg):
    """Reconstruct original material surfaces, omitting tree mesh and all models.

    The receiving ground is independently complete before a building is placed.
    Native trees replace the removed terrain-mesh tree materials; original
    cliff caps/fronts/side faces keep their real texture coordinates and joins.
    """
    import hgss_reference as R
    land,tex,models,chunks,meta=R.load(phg)
    ch=R.hgss_map.MapChunk.parse(land[85]);model=R.mdlview.Model(ch.model)
    class Surfaces:
        def __getattr__(self,n):return getattr(model,n)
        def faces(self):return [(mid,v) for mid,v in model.faces() if not model.mat_tex.get(mid,'').startswith('tree01')]
    cv=R.Canvas(512,512)
    grass=rgba(ART/'reference/textures/grass01gs.png')[...,:3]
    yy,xx=np.mgrid[0:512,0:512];cv.rgb=grass[yy%grass.shape[0],xx%grass.shape[1]].astype('float32')
    clear=R.draw_model(cv,Surfaces(),tex,lambda x,y,z:(x+16,y,z+16),-1,None)
    for p,uv,d,mat,hgt,steep in sorted(clear,key=lambda v:max(v[2])):cv.tri(p,uv,d,mat,-2,blend=True)
    # Receiving-context repairs are made before replacement trees. These are
    # original forest patches/flat mountain tops; exposed cliff faces and their
    # complete outside corners remain the original mesh surfaces.
    repairs=[]
    for box,material in [((0,7,9,9),'grass'),((5,5,9,7),'grass'),((25,5,29,11),'grass'),
                         ((28,12,32,15),'grass'),((0,17,2,21),'grass'),
                         ((26,19,32,27),'stone'),((0,28,32,32),'stone')]:
        x0,y0,x1,y1=[v*16 for v in box];yy,xx=np.mgrid[y0:y1,x0:x1]
        tile=rgba(ART/'reference/textures'/('grass01gs.png' if material=='grass' else 'cliff01gs.png'))[...,:3]
        cv.rgb[y0:y1,x0:x1]=tile[yy%tile.shape[0],xx%tile.shape[1]]
        repairs.append(dict(box=list(box),material=material,reason='Complete receiving plane after original tree mesh removal'))
    # The stone-top groves have actual lawn under their roots. Make coherent
    # pockets from the original trunk rows, joining adjacent roots into one bed.
    data=np.load(ART/'reference/topdown.npz');types=data['types'];mat=data['material'];names=data['names']
    mask=Image.new('L',(512,512));d=ImageDraw.Draw(mask)
    for y in range(19,32):
        for x in range(32):
            q=mat[y*16:y*16+16,x*16:x*16+16];u,c=np.unique(q,return_counts=True);v=int(u[np.argmax(c)])
            if types[y,x]==6 and v>=0 and names[v]=='tree01_un':
                d.rounded_rectangle((x*16,(y-1)*16,(x+1)*16+3,(y+1)*16-1),radius=4,fill=255)
    m=np.array(mask)>0;yy,xx=np.mgrid[0:512,0:512];g=grass[yy%grass.shape[0],xx%grass.shape[1]];cv.rgb[m]=g[m]
    # Clean, unobscured courses on the same original wall, with the same
    # orientation and height. Rebuild full joins exposed by smaller native trees.
    stone=rgba(ART/'reference/textures/cliff01gs.png')[...,:3]
    face=rgba(ART/'reference/textures/wall01_d.png')[...,:3]
    # North-facing native rim: the raised surface lies SOUTH of the boundary.
    # A short north lip enters textured rock top; no inverted south-facing wall.
    cap=stone[:16].copy();cap[:5]=face[2:7];cap[5]=[156,107,74]
    for x in range(3,25):cv.rgb[27*16:28*16,x*16:(x+1)*16]=cap[:,x%2*16:(x%2+1)*16]
    for x in range(26,32):cv.rgb[18*16:19*16,x*16:(x+1)*16]=cap[:,x%2*16:(x%2+1)*16]
    road=rgba(ART/'reference/textures/road01.png')[...,:3]
    yy,xx=np.mgrid[13*16:15*16,20*16:21*16];cv.rgb[13*16:15*16,20*16:21*16]=road[yy%32,xx%32]
    save(np.dstack([cv.rgb.astype('uint8'),np.full((512,512),255,np.uint8)]),SRC/'clean-original-ground.png')
    repairs.extend([
        dict(region='stone-top groves, original rows 19..31',material='grass root pockets',reason='Joined original trunk beds underneath complete shared native trees'),
        dict(box=[3,27,25,28],material='north-facing rock rim',high_side='south',reason='Reconstruct exposed cap/front join with original wall and rock textures'),
        dict(box=[26,18,32,19],material='north-facing rock rim',high_side='south',reason='Reconstruct exposed cap/front join with original wall and rock textures'),
        dict(box=[20,13,21,15],material='dirt',reason='Restore receiving ground beneath smaller native antenna tree')])
    (SRC/'receiving-repairs.json').write_text(json.dumps(repairs,indent=2)+'\n')
    a=np.zeros((N*16,N*16,4),np.uint8)
    gy,gx=np.mgrid[0:N*16,0:N*16];stone=rgba(ART/'reference/textures/cliff01gs.png')
    a[...,:3]=stone[gy%32,gx%32,:3];a[...,3]=255
    a[O*16:(O+32)*16,O*16:(O+32)*16,:3]=cv.rgb.astype('uint8')
    # Extend only the original road ends across the new canopy apron.
    for y in range(10,16):a[(y+O)*16:(y+O+1)*16,:O*16,:3]=np.tile(cv.rgb[y*16:(y+1)*16,:16].astype('uint8'),(1,O,1))
    for y in range(15,18):a[(y+O)*16:(y+O+1)*16,(O+32)*16:,:3]=np.tile(cv.rgb[y*16:(y+1)*16,-16:].astype('uint8'),(1,O,1))
    return a

def main(game):
    EV.mkdir(exist_ok=True,parents=True);SRC.mkdir(exist_ok=True,parents=True)
    data=np.load(ART/'reference/topdown.npz');types=data['types'];collision=data['collision'];names=data['names'];mtl=data['material'];rawh=data['height']
    bg=original_terrain(Path(sys.argv[2]).resolve() if len(sys.argv)>2 else Path(os.environ['HGSS_SOURCE']))
    trunk=np.zeros((32,32),bool)
    for y,x in np.ndindex(32,32):
        q=mtl[y*16:y*16+16,x*16:x*16+16];u,c=np.unique(q,return_counts=True);v=int(u[np.argmax(c)])
        trunk[y,x]=types[y,x]==6 and v>=0 and names[v]=='tree01_un'
    trees=[]
    for ty in range(1,32):
        x=0
        while x<31:
            if trunk[ty,x] and trunk[ty,x+1]:trees.append((x,ty-1));x+=2
            else:x+=1
    upper=np.zeros_like(bg);owner=np.full((N*16,N*16),'',dtype='<U24');placed=[]
    def put(name,a,x,y,kind):
        placed.append(dict(name=name,origin_px=[x,y],size=[a.shape[1],a.shape[0]],kind=kind))
        stamp(upper,a,x,y);m=a[...,3]>0;owner[y:y+a.shape[0],x:x+a.shape[1]][m]=name
    tree=rgba(APP/'tree.png')
    for i,(x,y) in enumerate(trees):put(f'tree-{i}',tree,(x+O)*16,(y+O-1)*16,'foliage')
    house=rgba(APP/'house.png')
    # Approved native architecture, fitted on actual HGSS doorway columns.
    put('souvenir-shop',house,(15+O)*16,(10+O)*16,'architecture')
    put('east-house',house.copy(),(24+O)*16,(10+O)*16,'architecture')
    g=Image.open(SRC/'approved-gym.png').convert('RGBA')
    matte=Image.new('L',g.size);ImageDraw.Draw(matte).polygon([(8,36),(10,26),(18,16),(27,12),(44,4),(44,3),(48,3),(48,8),(79,8),(79,3),(83,3),(94,8),(105,14),(112,21),(116,28),(116,44),(119,46),(119,63),(115,75),(105,82),(84,87),(38,87),(22,84),(9,79),(4,70),(1,58),(1,47),(7,47)],fill=255)
    g.putalpha(matte)
    a=np.array(g);rr=a[...,0].astype(int);gg=a[...,1].astype(int);bb=a[...,2].astype(int);yy=np.arange(a.shape[0])[:,None]
    blue=(yy>51)&(rr>gg*1.8)&(rr>bb*1.8)&(gg<78)
    a[blue,:3]=np.array([(.28*c[0],min(190,c[0]*.8),min(225,c[0]+22)) for c in a[blue,:3]],np.uint8)
    g=Image.fromarray(a).resize((112,88),Image.Resampling.NEAREST)
    gym=np.zeros((96,112,4),np.uint8);gym[8:]=np.array(g)
    # Remove receiving lawn from the source cutout; ground is a separate map layer.
    rgb=gym[...,:3].astype(int);gym[(rgb[...,1]>rgb[...,0]+9)&(rgb[...,1]>rgb[...,2]+5),3]=0
    logo=Image.fromarray(gym);d=ImageDraw.Draw(logo)
    d.ellipse((45,53,68,69),fill=(56,72,88),outline=(176,184,168))
    font={'G':['111','100','101','101','111'],'Y':['101','101','010','010','010'],'M':['101','111','111','101','101']}
    for i,c in enumerate('GYM'):
        for yy,row in enumerate(font[c]):
            for xx,v in enumerate(row):
                if v=='1':d.point((51+i*4+xx,58+yy),fill=(232,240,216))
    gym=np.array(logo);save(gym,SRC/'gym-native.png')
    put('gym',gym,(8+O)*16,(18+O)*16,'architecture')
    put('pokemon-center',rgba(SRC/'approved-center.png'),(20+O)*16,(19+O)*16,'shared-center')
    put('route43-gate',gate(),(10+O)*16,(0+O)*16,'architecture')
    put('west-watchtower',towers(),(6+O)*16,(5+O)*16,'woodland-prop')
    put('east-watchtower',towers(),(25+O)*16,(4+O)*16,'woodland-prop')
    put('antenna-tree',antenna(),(19+O)*16,(11+O)*16,'woodland-prop')
    for i,(x,y) in enumerate([(4,12),(14,14),(8,24)]):put('sign-'+str(i),sign(),(x+O)*16,(y+O-1)*16,'sign')
    solid=np.ones((N,N),np.uint8);solid[O:O+32,O:O+32]=(collision&128)>0
    solid[O+10:O+16,:O]=0;solid[O+15:O+18,O+32:]=0
    behavior=np.zeros((N,N),np.uint8);behavior[O:O+32,O:O+32]=np.where(np.isin(types,[0x39,0x3b]),types,0)
    for x,y in [(16,14),(25,14),(11,23),(22,23),(12,5),(13,5)]:solid[y+O,x+O]=0;behavior[y+O,x+O]=96 if y==5 else 105
    solid[18+O:20+O,20+O:25+O]=0
    # Roof/canopy masks share the original base row; they never lift opaque
    # ground above the player. Draw only foreground art on the upper layer.
    above=np.zeros((N,N),bool)
    for y,x in np.ndindex(N,N):
        if solid[y,x]:continue
        who=owner[y*16:y*16+16,x*16:x*16+16];nn=set(who.ravel())-{''}
        for n in nn:
            p=next(p for p in placed if p['name']==n)
            if y<(p['origin_px'][1]+p['size'][1]-1)//16:above[y,x]=True
    composed=bg.copy();m=upper[...,3]>0;composed[m]=upper[m]
    save(composed,EV/'fresh-composition.png');save(bg,SRC/'receiving-ground.png');save(upper,SRC/'foreground.png')
    np.savez_compressed(SRC/'layers.npz',bottom=bg,upper=upper,above=above,owner=owner,solid=solid,behavior=behavior)
    plan=dict(canvas=[N,N],original=[32,32],original_to_native_offset=[O,O],trees=trees,placed=placed,
        adaptations=['Two-cell apron preserves full canopies and native border scenery.','Shared Center, adapted Gym and shared native houses fitted to original door columns.','Original gate translated to a complete 96px-high native gate sprite.'],
        provenance='Original HGSS binary geometry/materials; approved Johto masters; no rejected Mahogany native artifact read')
    (SRC/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(trees=len(trees),canvas=[N,N],placed=len(placed))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
