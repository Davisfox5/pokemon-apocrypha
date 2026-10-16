"""Extract and clean current Johto scenery foregrounds without changing maps.
Preserves native pixels, object frames and terrain-independent masks. Never loads
retired tree art or earlier prop-design alternatives. Pillow + NumPy only.
"""
from pathlib import Path
from collections import deque
import sys,json,hashlib,argparse,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
from johto_common.trees import rgba,indexed,sha
OUT=ROOT/'gba/art/johto-common/scenery'


def clear_color(a,color,external=False,protect=None):
    a=a.copy(); candidate=np.all(a[...,:3]==color,axis=-1)|(a[...,3]==0)
    if protect is not None:candidate[protect]=False
    mask=candidate
    if external:
        h,w=candidate.shape;mask=np.zeros((h,w),bool);todo=deque()
        for y,x in zip(*np.nonzero(candidate)):
            if y in (0,h-1) or x in (0,w-1) or a[y,x,3]==0:mask[y,x]=True;todo.append((y,x))
        while todo:
            y,x=todo.popleft()
            for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                yy,xx=y+dy,x+dx
                if 0<=yy<h and 0<=xx<w and candidate[yy,xx] and not mask[yy,xx]:mask[yy,xx]=True;todo.append((yy,xx))
    a[mask,3]=0
    return a


def decode(game,map_name,primary,secondary):
    t=Tileset(game,secondary,primary)
    layout=next(v for v in json.loads((game/'data/layouts/layouts.json').read_text())['layouts'] if v['name']==map_name+'_Layout')
    h,w=layout['height'],layout['width'];grid=np.fromfile(game/layout['blockdata_filepath'],dtype='<u2').reshape(h,w)
    out=np.zeros((h*16,w*16,4),np.uint8);bank=np.full((h*16,w*16),-1,int)
    for y in range(h):
        for x in range(w):
            mid=int(grid[y,x]&1023)
            for layer in range(2):
                for q in range(4):
                    e=t.blocks[mid>=512][mid%512][layer*4+q];tid=e&1023;b=e>>12
                    a=np.array(t.tiles[tid>=512][tid%512]).reshape(8,8)
                    if e&1024:a=a[:,::-1]
                    if e&2048:a=a[::-1]
                    sl=np.s_[y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8]
                    colors=np.array(t.pals[b>=6][b],np.uint8)[a]
                    out[sl][a>0,:3]=colors[a>0];out[sl][a>0,3]=255;bank[sl][a>0]=b
    return out,bank


def build(game):
    expected='6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf'
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()
    assert actual==expected, ('Use pinned engine revision for native extraction',actual,expected)
    subprocess.run(['git','diff','--quiet','HEAD','--','data/layouts/CherrygroveCity','data/layouts/NewBarkTown','data/tilesets/primary/cherrygrove','data/tilesets/primary/johto_cherrygrove','data/tilesets/secondary/johto_cherrygrove','data/tilesets/secondary/new_bark','graphics/object_events/pics/misc/ball_poke.png','graphics/object_events/pics/misc/pushable_boulder.png','graphics/object_events/pics/misc/breakable_rock.png'],cwd=game,check=True)
    for folder in ['source','review','inputs']:(OUT/folder).mkdir(parents=True,exist_ok=True)
    records=[];originals={};clean={}
    def add(key,label,category,a,b,provenance,method,**extra):
        assert a.shape==b.shape
        keep=b[...,3]>0
        expected=a.copy()
        for old,new in extra.get('color_repairs',[]):expected[np.all(a[...,:3]==old,axis=2),:3]=new
        assert np.all(a[keep,3]>0) and np.array_equal(expected[keep,:3],b[keep,:3])
        assert set(np.unique(b[...,3])) <= {0,255}
        removed=int(((a[...,3]>0)&~keep).sum())
        a=a.copy();a[a[...,3]==0]=0;b=b.copy();b[~keep]=0
        Image.fromarray(a).save(OUT/f'inputs/{key}.png')
        Image.fromarray(b).save(OUT/f'source/{key}.png')
        native=b.copy()
        for old,new in extra.get('indexed_color_map',[]):native[np.all(b[...,:3]==old,axis=2)&keep,:3]=new
        colors=indexed(native,OUT/f'source/{key}.idx.png')
        extra['master_opaque_colors']=len(np.unique(b[keep,:3],axis=0))
        if provenance.get('engine_path'):
            # Native OBJ graphics share an engine palette: retain their original
            # index ordering, not merely equivalent decoded RGBA colors.
            native=Image.open(game/provenance['engine_path']).copy()
            palette=native.getpalette();palette[:3]=[0,0,0];native.putpalette(palette)
            native.save(OUT/f'source/{key}.idx.png',transparency=0)
            extra['native_indices_preserved']=True
            extra['native_index_sha256']=hashlib.sha256(np.array(native).tobytes()).hexdigest()

        if 'aliases' in extra:
            extra['aliases']=[p for p in extra['aliases'] if (ROOT/p).exists() and np.array_equal(rgba(ROOT/p),a)]
        records.append(dict(id=key,label=label,category=category,size=[b.shape[1],b.shape[0]],
            master=f'source/{key}.png',sha256=sha(OUT/f'source/{key}.png'),input=f'inputs/{key}.png',
            removed_background_pixels=removed,opaque_colors=colors,method=method,provenance=provenance,**extra))
        originals[key]=a;clean[key]=b
    def file(key,label,cat,rel,operation=None,method='Existing foreground already transparent; native pixels retained.',**extra):
        path=ROOT/rel;a=rgba(path);b=operation(a) if operation else a.copy()
        add(key,label,cat,a,b,dict(path=rel,sha256=sha(path)),method,**extra)
    def material(area,name):return f'gba/art/{area}/source/materials/{name}.png'
    # Actual current Route 30 ledges; unused ledge-0/1 source remnants excluded.
    for i,n in enumerate(['left','middle','right']):
        file(f'L0{i+1}',f'Emerald ledge / {n}','ledges',material('route30-hgss-blocks','ledge-'+n),
             placement='Current Route 30 set. Left, middle, right form one continuous ledge.')
    violet=rgba(ROOT/material('violet-city','ledge'))
    same=next((r for r in records if np.array_equal(clean[r['id']],violet)),None)
    if same:same['aliases']=[material('violet-city','ledge')]
    else:file('L04','Violet ledge','ledges',material('violet-city','ledge'))
    # The currently used Route 29/31 warm palette is an existing authoring module.
    from johto_synthesis.terrain import emerald
    warm,_=emerald(game)
    for i,n in enumerate(['ledge_l','ledge_a','ledge_r']):
        a=warm[n].to_rgba();b=clear_color(a,(72,152,112))
        add(f'L1{i+1}',f'Warm Johto ledge / {n.rsplit("_",1)[1]}','ledges',a,b,
            dict(generator='tools/gba/maps/johto_synthesis/terrain.py',source_metatile=[0xd5,0x87,0xd6][i]),
            'Remove the explicit terrain-colored contact shadow; preserve all stone pixels.',
            placement='Existing Route 29/31 native Emerald ledge family; selection not standardized yet.')
    for i,n in enumerate(['left','middle','right']):
        file(f'S0{i+1}',f'North/south steps / {n}','stairs',material('route30-hgss-blocks','step-'+n))
    from johto_common.hgss_props import side_stairs,STAIR_COLORS,sign_assets,REF
    stair_source,stair_clean=side_stairs()
    for key,direction,flip in [('S04','west',False),('S05','east',True)]:
        a=stair_source[:,::-1].copy() if flip else stair_source.copy()
        b=stair_clean[:,::-1].copy() if flip else stair_clean.copy()
        add(key,'Diagonal side stairs / descend '+direction,'stairs',a,b,
            dict(path='gba/art/route36/source/hgss-reference.png',crop=[232,346,248,394],mirrored=flip),
            'Trace actual HGSS stepped treads; remove adjoining rock, trees, lawn and path. Map five tread shades to neutral stone.',
            color_repairs=[[list(k),list(v)] for k,v in STAIR_COLORS.items()],
            placement='16x48 canvas, original HGSS diagonal profile. Separate ground and cliff behind it. Art review only; map elevation/collision not installed.')
    for key,label,n in [('P01','Violet sign','sign'),('P02','Violet bridge post','bridge_post')]:
        file(key,label,'props',material('violet-city',n))
    for key,n in [('P03','rail_left'),('P04','rail_right')]:
        file(key,'Violet '+n.replace('_',' '),'props',material('violet-city',n),
             lambda a:clear_color(a,(56,184,232)),
             'Remove exact cyan donor-water pixels; keep every neutral stone/metal pixel.')
    file('P05','Route sign','props',material('route30-hgss-blocks','sign'))
    file('W01','Violet lily pads','water',material('violet-city','lily_pads'))
    for i in range(4):
        file('F0'+str(i+1),'Route flowers / animation '+str(i),'plants',material('route30-hgss-blocks','flower-'+str(i)),
             animation_frame=i,animation_family='route flowers')
    # The source billboard supplies the true plant silhouette, including dark
    # leaf interiors that share the flat-ground RGB after palette conversion.
    billboard=np.array(Image.open(ROOT/'gba/art/johto-cohesion/references/egrass_u.png').convert('RGBA'))
    foliage=(billboard[...,3]>0)&~np.all(billboard[...,:3]==(123,123,123),axis=2)
    for i in range(16):
        file('G'+format(i,'02d'),'Tall grass / '+format(i,'04b'),'grass',material('route30-hgss-blocks','grass-'+format(i,'04b')),
             lambda a:clear_color(a,(32,112,80),True,protect=foliage&(a[...,3]>0)),
             'Remove exterior-connected flat dark-green backing outside the original HGSS egrass_u plant silhouette. Preserve the entire shaded plant and all brighter blade pixels.',
             neighbor_order='north,south,west,east',neighbor_bits=format(i,'04b'),
             mask_reference=dict(path='gba/art/johto-cohesion/references/egrass_u.png',sha256=sha(ROOT/'gba/art/johto-cohesion/references/egrass_u.png')),
             aliases=[material('route36','grass-'+format(i,'04b')),material('violet-city','grass-'+format(i,'04b'))])
    # Extract current installed art, avoiding older Cherrygrove reference variants.
    for map_name,primary,secondary,spec in [
        ('CherrygroveCity','johto_cherrygrove','johto_cherrygrove',[
            ('P06','Cherrygrove sign','props',(800,240,816,256),None),
            ('P07','Cherrygrove bench','props',(1056,128,1088,144),None),
            ('P08','Cherrygrove fence','props',(1008,224,1072,240),None),
            ('F05','Cherrygrove flower bed','plants',(1008,192,1072,224),None),
            ('W02','Cherrygrove water rock','water',(320,224,336,240),None),
            ('W03','Cherrygrove reef','water',(160,208,256,272),None)]),
        ('NewBarkTown','cherrygrove','new_bark',[
            ('P11','New Bark windmill','props',(384,48,416,112),[4]),
            ('F06','New Bark flowers','plants',(128,288,192,320),[4])])]:
        native,banks=decode(game,map_name,primary,secondary)
        for key,label,cat,box,allowed in spec:
            x,y,r,b=box;a=native[y:b,x:r].copy();bb=banks[y:b,x:r];out=a.copy()
            terrain=np.isin(bb,[0,1]) if allowed is None else ~np.isin(bb,allowed)
            out[terrain,3]=0
            if key=='P06':out=clear_color(out,(132,132,132))
            repairs=[]
            if key=='P08':
                # These two pixels are continuous metal highlights, not turf.
                # Neutralize their inherited cyan cast; retain fence geometry.
                repairs=[[[140,189,189],[180,180,180]],[[115,173,189],[160,160,160]]]
                for old,new in repairs:out[np.all(out[...,:3]==old,axis=2),:3]=new
            assert (out[...,3]>0).any(),key
            add(key,label,cat,a,out,dict(engine_map=map_name,crop=list(box),primary=primary,secondary=secondary),
                'Decode current native map pixels; remove destination terrain palette pixels.'+(' Clear gray donor-ground outside the sign frame.' if key=='P06' else ''),
                allowed_banks=allowed,color_repairs=repairs)
    # Restore the letterbox from the actual HGSS render before its colors were
    # collapsed into the shared native prop palette. Both anchors reuse one box.
    ref=ROOT/'gba/art/johto-v1/references/cherrygrove-hgss.png'
    raw=rgba(ref)[191:215,695:707].copy()
    mask=np.zeros((24,12),bool);mask[:19]=True;mask[0]=False;mask[0,2:9]=True;mask[19:24,4:8]=True
    # Keep full source RGB in RGBA; only native export merges close shade steps.
    palette=np.array([(32,32,32),(96,96,96),(112,16,0),(136,32,8),
        (152,56,32),(192,64,32),(200,72,40),(232,88,48),(232,112,56),
        (240,120,64),(128,120,120),(152,152,144),(168,168,160),
        (176,184,168),(184,192,184)],dtype=np.int32)
    native_map=[]
    for color in np.unique(raw[mask,:3],axis=0):
        near=palette[np.argmin(((palette-color.astype(int))**2).sum(axis=1))]
        if not np.array_equal(color,near):native_map.append([color.tolist(),near.tolist()])
    for key,top in [('P09',0),('P10',8)]:
        a=np.zeros((24+top,16,4),np.uint8);a[top:,4:]=raw
        b=a.copy();b[top:,4:,3]=mask*255
        add(key,'HGSS red mailbox / '+('north anchor' if top==0 else 'house anchor'),'props',a,b,
            dict(path=str(ref.relative_to(ROOT)),sha256=sha(ref),crop=[695,191,707,215]),
            'Trace original red letterbox and complete post; remove grass, cast shadow and neighboring house pixel. Restore original red front and narrow dark slot.',
            indexed_color_map=native_map,placement='One shared letterbox with two existing canvas anchors. RGBA retains original HGSS colors; indexed export merges similar shade steps into 15 colors.')
    # Original Johto wooden town sign. Bounds follow board, upper peg and post,
    # rather than guessing terrain colors that are also used in the timber.
    a=rgba(ref)[130:162,662:694].copy();b=a.copy();mask=np.zeros((32,32),bool)
    mask[4:9,5:9]=True;mask[8:19,0:15]=True;mask[19:23,5:9]=True
    b[~mask,3]=0
    add('P12','HGSS wooden signpost','props',a,b,
        dict(path=str(ref.relative_to(ROOT)),sha256=sha(ref),crop=[662,130,694,162]),
        'Trace complete original wooden board, upper peg and support post. Remove all donor lawn, path and cast ground shadow.',preview_box=[0,0,16,32])
    for record,a in sign_assets():
        add(record['id'],record['label'],'props',a,a.copy(),
            dict(model_id=record['model_id'],donor_path=record['donor_path'],donor_sha256=record['donor_sha256'],
                 geometry='references/sign-models.json',geometry_sha256=sha(REF/'sign-models.json'),
                 textures=[dict(path='references/'+n+'.png',sha256=sha(REF/(n+'.png'))) for n in sorted({f['texture'] for f in record['faces']})]),
            'Orthographic native-scale render of HGSS model geometry and original texture. Omit ground-shadow material; add HGSS-style silhouette outline. RGB555-compatible tones and transparent palette index zero.',
            placement='32x32 / four 16x16 map cells; baseline at y=30. Sign appearance only; text and interaction remain map scripts.',
            review_state='New HGSS sign style for owner review')
    for key,name,label,h in [('N01','ball_poke','Item ball',32),('N02','pushable_boulder','Strength boulder',16),('N03','breakable_rock','Rock Smash rock',16)]:
        path=game/f'graphics/object_events/pics/misc/{name}.png';a=rgba(path)
        add(key,label,'native',a,a.copy(),dict(engine_path=str(path.relative_to(game)),sha256=sha(path)),
            'Native palette-index-zero transparency; full original animation sheet preserved.',
            preview_box=[0,0,16,h],frame_size=[16,h],frames=a.shape[1]//16)
    manifest=dict(status='Source foreground cleanup for review; no native maps or ROM changed',
        engine_revision='6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf',
        map_scope=['New Bark','Route 29','Cherrygrove','Route 30','Route 31','Violet','Route 36'],
        absent_categories=['No standalone reeds, lamps or bushes confirmed in these current maps; no historical substitutes added.'],
        excluded=['Shoreline and path transitions: terrain modules, not standalone props.','Structural cliff faces and bridge decking retain their solid surfaces.','Unused ledge-0/1 draft exports.'],
        credits='Game Freak / Nintendo / Creatures originals; existing project adaptations retained.',assets=records)
    (OUT/'catalog.json').write_text(json.dumps(manifest,indent=2)+'\n')
    review(records,originals,clean)
    print(json.dumps(dict(assets=len(records),changed=sum(r['removed_background_pixels']>0 for r in records),removed=sum(r['removed_background_pixels'] for r in records)),indent=2))


def review(records,originals,clean):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
    small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
    tex={n:Image.open(ROOT/f'gba/art/cherrygrove-synthesis/references/HGSS-direct/{f}-source.png').convert('RGBA') for n,f in [('Grass','grass'),('Dirt','path')]}
    tex['Water']=Image.open(ROOT/'gba/art/cherrygrove-synthesis/references/B/sea-frame-0.png').convert('RGBA').crop((0,0,32,32))
    groups={'ledges':['ledges'],'stairs':['stairs'],'props':['props'],'plants':['plants'],'grass':['grass'],'water':['water'],'native':['native']}
    for name,cats in groups.items():
        rows=[r for r in records if r['category'] in cats]
        # Four frame strip stays preserved; show the intact object in native rows.
        for page in range((len(rows)+5)//6):
            selected=rows[page*6:page*6+6];canvas=Image.new('RGB',(1040,90+len(selected)*200),'#202833');d=ImageDraw.Draw(canvas)
            d.text((16,12),'JOHTO / '+name.upper()+' — transparent foreground review',font=font,fill='white')
            d.text((16,39),'Original/source     |     Cleaned on checkerboard     |     Cleaned on grass     |     Cleaned on '+('water' if name=='water' else 'dirt'),font=small,fill='#becad5')
            for row,r in enumerate(selected):
                key=r['id'];yy=76+row*200;d.text((16,yy),key+'  '+r['label'],font=font,fill='white')
                for col,bg in enumerate(['Before','Clear','Grass','Water' if name=='water' else 'Dirt']):
                    a=originals[key] if col==0 else clean[key]
                    if r.get('preview_box'):
                        x,y,x1,y1=r['preview_box'];a=a[y:y1,x:x1]
                    h,w=a.shape[:2];scale=min(4,240//w,160//h);tw,th=max(60,w),max(40,h)
                    base=Image.new('RGBA',(tw,th));px=base.load()
                    for y in range(th):
                        for x in range(tw):px[x,y]=(65,75,87,255) if (x//4+y//4)%2 else (48,57,68,255)
                    if bg in tex:
                        t=tex[bg]
                        for y in range(0,th,t.height):
                            for x in range(0,tw,t.width):base.paste(t,(x,y))
                    base.alpha_composite(Image.fromarray(a),((tw-w)//2,(th-h)//2))
                    im=base.resize((tw*scale,th*scale),Image.Resampling.NEAREST).convert('RGB');canvas.paste(im,(16+col*258,yy+28))
            canvas.save(OUT/f'review/{name}-{page+1}.png')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);build(p.parse_args().engine.resolve())
