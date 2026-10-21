"""Cianwood exterior: HGSS geometry, explicit cell ledger, native GBA art.

Run only to create a NEW Cianwood layout. Never replay over owner-edited source.
The reference is an orthographic screenshot trace, not extracted collision data.
"""
from pathlib import Path
import json, sys, struct, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/cianwood-city'
W, H = 35, 42

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')

def gba(a):
    return (np.asarray(a, dtype=np.int32) >> 3) * 255 // 31

def main(game):
    src = Image.open(OUT/'references/cianwood-hgss.png').convert('RGB')
    art = Image.new('RGB', (W*16, H*16))
    art.paste(src)
    # Source ends mid-ocean and one pixel short of the final metatile row.
    art.paste(src.crop((534,0,544,671)), (550,0))
    art.paste(art.crop((0,670,560,671)), (0,671))
    # Reuse accepted shared Center pixels and palette. Preserve the local sand.
    center = Image.open(ROOT/'gba/art/cherrygrove-synthesis/refined/center.png').convert('RGBA')
    sand = np.asarray(src.crop((208,336,240,368)))
    a = np.asarray(art).copy()
    for y in range(496,592):
        for x in range(352,464):
            a[y,x] = sand[y%32,x%32]
    art = Image.fromarray(a)
    art.paste(center, (352,496), center)
    a = gba(art)
    # All three ordinary HGSS blue-roof residences share one complete module.
    # Cell-align its receiving footprints; keep the pharmacy and studio distinct.
    house=src.crop((280,416,360,496)).convert('RGBA')
    hh=np.asarray(house).copy();hh[:48,40:]=hh[:48,:40][:,::-1];house=Image.fromarray(hh)
    hm=Image.new('L',(80,80));hd=ImageDraw.Draw(hm)
    hd.polygon([(39,1),(73,17),(73,53),(69,53),(69,77),(7,77),(7,53),(5,53),(5,18)],fill=255)
    house.putalpha(hm)
    aa=Image.fromarray(a.astype('uint8'))
    # Trace each old silhouette before restoring only the covered local ground.
    for origin,points,ground in [
        ((56,80),[(39,1),(75,18),(75,56),(72,56),(72,82),(7,82),(7,57),(4,57),(4,19)],(176,96)),
        ((280,416),[(39,1),(75,18),(75,56),(72,56),(72,82),(7,82),(7,57),(4,57),(4,19)],(208,336)),
        ((104,480),[(39,1),(75,18),(75,56),(72,56),(72,82),(7,82),(7,57),(4,57),(4,19)],(208,336)),
    ]:
        ox,oy=origin
        mask=Image.new('L',(80,88));ImageDraw.Draw(mask).polygon(points,fill=255)
        bg=Image.new('RGB',(80,88));sample=src.crop((ground[0],ground[1],ground[0]+16,ground[1]+16))
        for yy in range(0,88,16):
            for xx in range(0,80,16):bg.paste(sample,(xx,yy))
        aa.paste(bg,origin,mask);aa.paste(house,origin,house)
    a=gba(aa)
    # Shared blue roof module on the pharmacy; preserve its distinct shop front.
    a[512:568,248:328]=a[416:472,280:360]
    # The gym's curved roof uses mirrored construction, with its entrance and
    # original facade kept separately below the roof course.
    a[344:400,168:224]=a[344:400,112:168][:,::-1]
    a[336:368,320:352]=a[336:368,288:320][:,::-1]
    # Compact repeated surface cores first. Never replace a mixed boundary tile
    # or a landmark. Source cliff edges, foam, stones and silhouettes stay intact.
    protected=np.zeros(a.shape[:2],bool)
    for x0,y0,x1,y1 in [(48,80,144,176),(112,336,224,448),(288,320,384,400),(288,416,352,496),(112,480,192,560),(256,512,336,592),(352,496,464,592),(400,352,448,496),(144,240,192,288),(208,464,256,496)]:
        protected[y0:y1,x0:x1]=True
    r,g,b=a.transpose(2,0,1)
    water=(b>g+12)&(g>r+15)&(r<125)
    beach=(r>190)&(g>190)&(b>125)&(r>b+15)
    lawn=(g>r+16)&(g>b+10)
    rock=(r>g+12)&(g>b+10)&(r<240)
    # Full landmark bounds are reviewed, but their background is not part of
    # the foreground asset. Flood from the outside; retain enclosed pale trim.
    from collections import deque
    bg=beach|lawn|water
    for x0,y0,x1,y1 in [(48,80,144,176),(112,336,224,448),(288,320,384,400),
            (280,416,360,504),(104,480,192,568),(256,512,336,592),
            (352,496,464,592),(400,352,448,496),(144,240,192,288),(208,464,256,496)]:
        m=bg[y0:y1,x0:x1];seen=np.zeros(m.shape,bool);q=deque()
        for y,x in zip(*np.nonzero(m)):
            if x in (0,m.shape[1]-1) or y in (0,m.shape[0]-1):q.append((y,x));seen[y,x]=True
        while q:
            y,x=q.popleft()
            for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
                ny,nx=y+dy,x+dx
                if 0<=ny<m.shape[0] and 0<=nx<m.shape[1] and m[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;q.append((ny,nx))
        protected[y0:y1,x0:x1]=~seen
    for ox,oy in [(56,80),(280,416),(104,480)]:
        protected[oy:oy+88,ox:ox+80]=False
        protected[oy:oy+80,ox:ox+80]=np.asarray(hm)>0
    protected[512:600,248:336]=False
    protected[512:568,248:328]=np.asarray(hm)[:56]>0
    protected[568:592,256:336]=True
    # Complete western cliff entrance: retain hood, inner shadow, sill and the
    # surrounding receiving wall together, rather than painting over the opening.
    protected[272:320,112:144]=True
    # Repeat the same source texture at a stable world phase inside terrain
    # masks, retaining the reference's complete material silhouette. This is
    # native modular terrain, rather than packing thousands of screenshot tiles.
    samples={'water':a[400:432,496:528].copy(),
             'beach':gba(src.crop((192,224,208,240))),
             'lawn':np.tile(np.array([[[98,189,139],[98,189,139]],[[98,189,139],[106,197,147]]]),(8,8,1))}
    yy,xx=np.indices(a.shape[:2])
    for material,mask in [('water',water),('beach',beach),('lawn',lawn)]:
        tex=samples[material];m=mask & ~protected
        a[m]=tex[yy[m]%tex.shape[0],xx[m]%tex.shape[1]]
    cliff=Image.new('L',(560,672));cd=ImageDraw.Draw(cliff)
    cd.polygon([(0,0),(320,0),(320,88),(272,88),(272,128),(240,128),
        (240,136),(176,136),(160,128),(144,128),(144,96),(128,80),
        (64,80),(48,80),(48,192),(96,200),(112,216),
        (112,240),(128,248),(144,272),(144,344),(128,352),
        (112,368),(112,608),(144,608),(176,624),(176,640),
        (464,640),(464,672),(0,672)],fill=255)
    cm=np.asarray(cliff)>0
    # Keep the actual material contact fringe, not the polygon approximation.
    cm &= ~protected
    interior=cm.copy()
    front=Image.new('L',(560,672));fd=ImageDraw.Draw(front)
    for box in [(0,16,80,32),(80,8,224,32),(32,48,96,64),
        (128,32,272,56),(160,64,320,88),(160,112,272,136),
        (32,80,48,192),(80,208,112,240),(128,272,144,336),
        (96,368,112,608),(0,640,176,672),(176,656,464,672)]:fd.rectangle(box,fill=255)
    fm=np.asarray(front)>0
    fm |= cm&(~np.roll(cm,-16,axis=0)|~np.roll(cm,-16,axis=1))
    for plane,mask,box in [('cap',interior&~fm,(0,112,16,128)),('front',interior&fm,(128,32,144,48))]:
        tex=gba(src.crop(box));a[mask]=tex[yy[mask]%16,xx[mask]%16]
    # The west cliff has two separate vertical courses, not one broad flat cap.
    # Use the original side-face texture on the corresponding orientation.
    side=Image.new('L',(560,672));sd=ImageDraw.Draw(side)
    for box in [(32,80,48,192),(32,200,48,624),(96,368,112,608),
                (128,272,144,336)]:sd.rectangle(box,fill=255)
    sm=(np.asarray(side)>0)&interior
    tex=gba(src.crop((32,224,48,240)));a[sm]=tex[yy[sm]%16,xx[sm]%16]
    rock &= ~cm
    cores={}
    for ty in range(H*2):
        for tx in range(W*2):
            sl=np.s_[ty*8:ty*8+8,tx*8:tx*8+8]
            if protected[sl].any():continue
            for material,mask in [('water',water),('beach',beach),('lawn',lawn),('rock',rock)]:
                if not mask[sl].all():continue
                patch=a[sl]
                # Wall planes and major shading transitions are protected from
                # ordinary top-face texture reuse.
                if material=='rock':
                    # Distinct bright cap / shaded wall planes remain separate.
                    band=int(patch.mean()//32)
                else:band=0
                key=(material,band,tx%2,ty%2)
                if key not in cores:cores[key]=patch.copy()
                else:a[sl]=cores[key]
                break
    # Rebuild the continuous shoreline as a small, phase-aligned terrain family.
    # The native cell silhouette follows the HGSS inlet and long eastern beach;
    # no screenshot's wave/foam noise is allowed to become hundreds of edge tiles.
    from scipy.ndimage import distance_transform_edt
    land=Image.new('L',(560,672));ld=ImageDraw.Draw(land)
    coast=[(0,0),(328,0),(328,160),(320,176),(320,192),(288,208),
        (256,224),(256,256),(280,256),(280,288),(296,304),(320,312),
        (352,320),(472,320),(472,671),(0,671)]
    rounded=[]
    for n,point in enumerate(coast):
        p=np.array(point,dtype=float)
        if n in (0,1,14,15):rounded.append(tuple(p));continue
        prev=np.array(coast[n-1],float);nxt=np.array(coast[(n+1)%len(coast)],float)
        radius=min(8,np.linalg.norm(prev-p)/2,np.linalg.norm(nxt-p)/2)
        start=p+(prev-p)/np.linalg.norm(prev-p)*radius;end=p+(nxt-p)/np.linalg.norm(nxt-p)*radius
        for t in np.linspace(0,1,9):rounded.append(tuple((1-t)**2*start+2*(1-t)*t*p+t*t*end))
    ld.polygon(rounded,fill=255)
    lm=np.asarray(land)>0
    old=a.copy()
    for mask,material in [(lm,'beach'),(~lm,'water')]:
        tex=samples[material];a[mask]=tex[yy[mask]%tex.shape[0],xx[mask]%tex.shape[1]]
    # The actual reference grass patches retain their original outlines.
    gm=lawn&lm&~cm&~protected
    tex=samples['lawn'];a[gm]=tex[yy[gm]%16,xx[gm]%16]
    edge=distance_transform_edt(~lm)
    a[(edge>0)&(edge<=2)]=(222,246,230)
    a[(edge>2)&(edge<=4)]=(106,197,222)
    a[cm|protected]=old[cm|protected]
    # Repeated offshore barrier boulders are complete source silhouettes, using
    # one gray module and its warm end-cap palette, rather than partial crops.
    stone=np.asarray(src.crop((400,32,432,64)).convert('RGBA')).copy()
    stone[:,16:]=stone[:,:16][:,::-1]
    sr,sg,sb=stone[:,:,:3].astype(int).transpose(2,0,1)
    stone[(sb>sr+12)&(sb>sg+6),3]=0
    for i,(sx,sy) in enumerate([(448,8),(480,-8),(528,-16),(400,32),(448,32),
            (352,64),(384,64),(416,64),(448,64),(392,80),(384,112),
            (416,144),(432,160),(416,192),(416,224),(416,256),
            (400,272),(400,296),(320,56)]):
        s=stone.copy()
        if i>=17:
            shade=s[:,:,:3].mean(-1)
            s[:,:,:3]=np.stack([np.minimum(232,shade*1.15),shade*.82,shade*.55],-1).astype('uint8')
        top=max(0,sy);bottom=min(672,sy+32);right=min(560,sx+32)
        cut=s[top-sy:bottom-sy,:right-sx];m=cut[:,:,3]>0
        a[top:bottom,sx:right][m]=gba(cut[:,:,:3])[m]
    small=np.asarray(src.crop((176,624,208,640)))
    m=(small[:,:,0].astype(int)>small[:,:,1]+12)&(small[:,:,1].astype(int)>small[:,:,2]+10)
    a[624:640,176:208][m]=gba(small)[m]
    plant=np.asarray(src.crop((168,208,184,224)))
    pr,pg,pb=plant.astype(int).transpose(2,0,1);pm=(pg>pr+12)&(pg>pb+12)
    for px,py in [(200,160),(168,208),(256,192),(248,304),(184,448),
                  (208,512),(240,496),(336,608),(168,592),(256,424)]:
        a[py:py+16,px:px+16][pm]=gba(plant)[pm]
    # Small original landmarks are not terrain texture: retain the lone pebble
    # below the north end-cap and the distinct rocks along the southern rim.
    pebble=np.asarray(src.crop((336,88,352,104)));pr,pg,pb=pebble.astype(int).transpose(2,0,1)
    pm=(abs(pr-pg)<20)&(abs(pg-pb)<25)&(pr>50)
    a[88:104,336:352][pm]=gba(pebble)[pm]
    for px,py in [(112,624),(336,640),(280,648)]:
        patch=gba(src.crop((px,py,px+16,py+16)));sy,sx=np.indices((16,16));mask=(sx-8)**2+(sy-8)**2<=49
        a[py:py+16,px:px+16][mask]=patch[mask]
    rockmask=Image.new('L',(32,32));ImageDraw.Draw(rockmask).polygon([(9,1),(21,1),(30,15),(26,27),(8,30),(1,24),(1,13)],fill=255)
    rm=np.asarray(rockmask)>0;a[624:656,48:80][rm]=gba(src.crop((48,624,80,656)))[rm]
    # Deliberate source texture stays editable separately from native reduction.
    art=Image.fromarray(a.astype('uint8'))
    # Palette training groups retain distinct material/shading ramps, including
    # mixed shore and rock/grass joins. No tile substitutions across materials.
    boxes = [
        [(176,336,256,416),(176,576,256,608),(176,96,256,128)],
        [(0,0,304,80),(0,192,112,608),(0,608,176,672)],
        [(480,80,544,624),(352,112,448,224)],
        [(48,80,144,176),(112,480,192,560),(288,416,352,496)],
        [(112,336,224,448)],
        [(288,320,384,400),(256,512,336,592)],
        [(240,192,336,320),(448,320,480,640),(304,0,336,128)],
        [(384,0,480,112),(400,128,464,320),(112,592,304,656)],
        [],
        [(400,352,448,496),(144,240,192,288),(208,464,256,496)],
        [(112,176,176,336),(128,592,336,656),(160,80,288,144)],
        [(96,336,240,448),(32,64,160,192)],
    ]
    palettes = []
    for i,bs in enumerate(boxes):
        if i == 8:
            lines=(game/'data/tilesets/secondary/cherrygrove/palettes/08.pal').read_text().splitlines()[3:19]
            p=[tuple(map(int,s.split())) for s in lines][1:]
        else:
            pixels=np.concatenate([a[y0:y1,x0:x1].reshape(-1,3) for x0,y0,x1,y1 in bs])
            im=Image.fromarray(pixels.astype('uint8').reshape(-1,1,3))
            colors=12 if i in (0,1,2,6,7,9,10,11) else 15
            qi=im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
            p=gba(np.array(qi.getpalette()[:colors*3]).reshape(colors,3)).tolist()
            p += [p[-1]]*(15-len(p))
        palettes.append(np.asarray(p, dtype=np.int32))
    tiles=[np.zeros((8,8),np.uint8)];lookup={tiles[0].tobytes():(0,0)}
    def put_tile(ix):
        for hf,vf,bits in [(0,0,0),(1,0,1024),(0,1,2048),(1,1,3072)]:
            v=ix[::-1] if vf else ix;v=v[:,::-1] if hf else v
            if v.tobytes() in lookup:return lookup[v.tobytes()][0],bits
        tid=len(tiles);tiles.append(ix.copy());lookup[ix.tobytes()]=(tid,0);return tid,0
    entries=np.zeros((H*2,W*2),np.uint32)
    tile_ids=np.zeros_like(entries);flags=np.zeros_like(entries)
    err=[]
    for ty in range(H*2):
        for tx in range(W*2):
            rgb=a[ty*8:ty*8+8,tx*8:tx*8+8]
            candidates=[]
            for bank,p in enumerate(palettes):
                dist=((rgb[:,:,None,:]-p)**2).sum(-1)
                ix=dist.argmin(-1)
                candidates.append((float(np.take_along_axis(dist,ix[...,None],-1).mean()),bank,(ix+1).astype('uint8')))
            # Accepted Center's opaque pixels are never re-quantized to another bank.
            alpha=np.asarray(center)[max(0,ty*8-496):max(0,ty*8-496)+8,max(0,tx*8-352):max(0,tx*8-352)+8,3] if 352<=tx*8<464 and 496<=ty*8<592 else None
            best=min(candidates,key=lambda v:v[0])
            if alpha is not None and alpha.shape==(8,8) and np.all(alpha):best=candidates[8]
            error,bank,ix=best;err.append(error)
            hit=put_tile(ix)
            tile_ids[ty,tx]=hit[0];flags[ty,tx]=hit[1]|bank<<12
            entries[ty,tx]=hit[0]|hit[1]|bank<<12
    # The approved Center keeps its original indexed foreground and native bank
    # byte for byte. Separate the sand underneath from the transparent outline.
    top_ids=np.zeros_like(tile_ids);top_flags=np.zeros_like(flags)
    ci=np.asarray(Image.open(ROOT/'gba/art/cherrygrove-synthesis/refined/center.png')).astype('uint8')
    for cy in range(0,96,8):
        for cx in range(0,112,8):
            fg=ci[cy:cy+8,cx:cx+8]
            if not fg.any():continue
            ty,tx=(496+cy)//8,(352+cx)//8
            tid,bits=put_tile(fg);top_ids[ty,tx]=tid;top_flags[ty,tx]=bits|(8<<12)
            tex=samples['beach'];rgb=tex[(np.arange(8)[:,None]+cy)%tex.shape[0],(np.arange(8)[None,:]+cx)%tex.shape[1]]
            costs=[]
            for bank,p in enumerate(palettes):
                ds=((rgb[:,:,None,:]-p)**2).sum(-1);ix=ds.argmin(-1);costs.append((float(np.take_along_axis(ds,ix[...,None],-1).mean()),bank,(ix+1).astype('uint8')))
            _,bank,ix=min(costs,key=lambda t:t[0]);tid,bits=put_tile(ix);tile_ids[ty,tx]=tid;flags[ty,tx]=bits|bank<<12
    # Remove patterns superseded by the exact two-layer Center before banking.
    used=sorted(set(tile_ids.ravel().tolist())|set(top_ids.ravel().tolist()));remap={old:new for new,old in enumerate(used)}
    tiles=[tiles[i] for i in used];tile_ids=np.vectorize(remap.__getitem__)(tile_ids);top_ids=np.vectorize(remap.__getitem__)(top_ids)
    print('Native unique 8x8 patterns:',len(tiles),'quantization mean error',np.mean(err),flush=True)
    np.savez(OUT/'evidence/packing-work.npz',entries=entries,tile_ids=tile_ids,flags=flags,top_ids=top_ids,top_flags=top_flags,tiles=np.array(tiles),palettes=np.array(palettes),protected=protected,land=lm,cliff=cm,front=fm,grass=gm)
    art.save(OUT/'evidence/composed-source.png')
    # Registration sheet for independent manual material / traversal review.
    registered=Image.new('RGB',(560,672));registered.paste(src)
    sheet=registered.resize((W*32,H*32),Image.Resampling.NEAREST)
    d=ImageDraw.Draw(sheet)
    for x in range(W):
        d.line((x*32,0,x*32,H*32),fill=(80,90,100),width=1)
        d.text((x*32+2,2),str(x),fill='white',stroke_width=1,stroke_fill='black')
    for y in range(H):
        d.line((0,y*32,W*32,y*32),fill=(80,90,100),width=1)
        d.text((1,y*32+3),str(y),fill='white',stroke_width=1,stroke_fill='black')
    sheet.save(OUT/'evidence/reference-grid.png')

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
