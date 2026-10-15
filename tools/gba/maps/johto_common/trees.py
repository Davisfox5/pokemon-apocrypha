"""Extract terrain-free Johto tree masters; preserve source RGB and native pixels.

Run with --engine pointing to the pinned production engine checkout. This builds
an asset review pack only: it never writes map blocks, engine graphics or palettes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/gba/maps'))
from claude_routes import art
OUT = ROOT / 'gba/art/johto-common/trees'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(path):
    im = Image.open(path)
    a = np.array(im.convert('RGBA'))
    if im.mode == 'P':
        a[..., 3] = np.where(np.array(im) == 0, 0, 255)
    return a


def without(a, colors):
    b = a.copy()
    for color in colors:
        b[..., 3][np.all(b[..., :3] == color, axis=-1)] = 0
    return b


def indexed(a, path):
    # Exact palette, no quantization: all surviving source RGB is preserved.
    colors = sorted(set(map(tuple, a[a[..., 3] > 0, :3].tolist())))
    assert len(colors) <= 15, (path, len(colors))
    ix = np.zeros(a.shape[:2], np.uint8)
    for n, color in enumerate(colors, 1):
        ix[np.all(a[..., :3] == color, axis=-1) & (a[..., 3] > 0)] = n
    im = Image.fromarray(ix).convert('P')
    palette = [0, 0, 0] + [v for c in colors for v in c]
    im.putpalette(palette + [0] * (768-len(palette)))
    im.save(path, transparency=0)
    assert np.array_equal(rgba(path), a)
    return len(colors)


def build(engine):
    (OUT/'source').mkdir(parents=True, exist_ok=True)
    (OUT/'review').mkdir(exist_ok=True)
    records, originals, clean = [], {}, {}
    def add(key, title, before, after, sources, method, **extra):
        assert before.shape == after.shape
        keep = after[...,3] > 0
        assert np.all(before[...,3][keep] > 0)
        assert np.array_equal(before[keep,:3], after[keep,:3])
        assert set(np.unique(after[...,3])) <= {0,255}
        after = after.copy(); after[~keep] = 0
        Image.fromarray(after).save(OUT/'source'/f'{key}.png')
        count = indexed(after, OUT/'source'/f'{key}.idx.png')
        mask = np.where((before[...,3]>0) & ~keep,255,0).astype(np.uint8)
        if mask.any() or not (OUT/'review'/f'{key}-removed-mask.png').exists():
            Image.fromarray(mask).save(OUT/'review'/f'{key}-removed-mask.png')
        records.append(dict(id=key, label=title, size=[after.shape[1],after.shape[0]],
            master=f'source/{key}.png', indexed=f'source/{key}.idx.png',
            opaque_colors=count, removed_ground_pixels=int((mask>0).sum()),
            retained_pixels=int(keep.sum()), source_files=sources, cleanup=method,
            sha256=sha(OUT/'source'/f'{key}.png'), **extra))
        originals[key], clean[key] = before, after

    for key,name,title in [('T01','tree','Large green tree'),('T02','blossom','Pink tree / Cherrygrove only')]:
        path=ROOT/f'gba/art/cherrygrove-synthesis/refined/{name}.png'
        before=rgba(path)
        add(key,title,before,without(before,[(64,136,104)]),
            [{'path':str(path.relative_to(ROOT)), 'sha256':sha(path)}],
            'Approved Cherrygrove design only. Its 197 ground-shadow pixels were removed before this catalog rebuild; source RGB and the original 32x48 canvas are retained.',
            restriction='Cherrygrove only' if key=='T02' else 'Johto shared',
            anchor=[16,43])

    # Exact native HGSS pixel crops. Do not palette-map fruit trees through the
    # olive large-tree palette: that destroys their emerald-green foliage.
    fruit = [
        ('T03',29,(20,9,3,4),(10,24,42,56),
         [(88,120,96),(80,120,96)], 'Apricorn / green fruit'),
        ('T04',30,(20,4,3,2),(8,0,40,32),
         [(72,112,88),(72,104,80),(64,96,80)], 'Apricorn / pink fruit'),
    ]
    for key,route,cell,box,shadow,title in fruit:
        raw=art.cells(route,*cell)
        # Foliage and trunk have disjoint RGB from lawn and cast ground shadow.
        # Restrict to the tree's measured bounds to exclude neighboring objects.
        before=np.zeros_like(raw)
        bounds=(18,25,36,51) if route==29 else (16,5,34,29)
        x0,y0,x1,y1=bounds
        before[y0:y1,x0:x1]=raw[y0:y1,x0:x1]
        allowed = [(56,64,72),(128,184,96),(152,216,120),(24,80,48),
                   (32,128,72),(24,104,56),(56,152,96),(40,144,80),
                   (24,120,64),(16,120,56),(120,80,64),(160,120,104)] if route==29 else [
                   (56,64,64),(232,136,184),(240,200,208),(24,80,48),
                   (32,128,64),(24,104,56),(56,152,88),(40,144,72),
                   (24,120,64),(16,120,56),(120,80,64),(160,120,96)]
        match=lambda cols: np.any(np.all(before[...,:3,None]==np.array(cols).T,axis=2),axis=-1)
        before[...,3]=np.where(match(allowed+shadow),255,0)
        after=without(before,shadow)
        l,t,r,b=box; before=before[t:b,l:r];after=after[t:b,l:r]
        path=art.REFS/f'route{route}-hgss.png'
        add(key,title,before,after,[{'path':str(path.relative_to(ROOT)), 'sha256':sha(path)}],
            'Exact foliage, fruit and trunk color mask from original HGSS render; remove cast ground shadow; no resampling or recoloring.',
            source_cells=list(cell), source_grid_origin=list(art.ORIGIN[route]),
            crop_within_cells=list(box), anchor=[17,25] if route==29 else [17,29],
            note='Green-fruit extraction extends the old 48px crop to preserve the bottom of the trunk.' if route==29 else 'Replaces damaged olive-palette conversion; native placement needs separate palette allocation.')

    for key,name,title in [('T05','cuttable_tree','Cut tree / native Emerald')]:
        path=engine/f'graphics/object_events/pics/misc/{name}.png'
        a=rgba(path)
        Image.fromarray(a[:,:16]).save(OUT/'source/T05-intact.png')
        add(key,title,a,a,[{'engine_path':str(path.relative_to(engine)), 'sha256':sha(path)}],
            'Preserve existing palette-index-zero transparency and every animation pixel.',
            frames=a.shape[1]//16, frame_size=[16,16],
            status='Already transparent; unchanged pixels',
            usage='Native Cut object used on Route 30 approach')

    manifest=dict(status='Owner-approved tree artwork; native map rollout pending',
        map_scope=['New Bark Town','Route 29','Cherrygrove City','Route 30','Route 31','Violet City','Route 36'],
        engine_revision='6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf',
        credits='Original artwork Game Freak / Nintendo / Creatures; derived from preserved project references and engine sprites.',
        rule='Transparent object foreground over independently authored destination terrain. Palette index zero is transparent; never flatten donor ground into masters.',
        assets=records)
    (OUT/'catalog.json').write_text(json.dumps(manifest,indent=2)+'\n')
    reviews(records,originals,clean)
    print(json.dumps({r['id']:{k:r[k] for k in ['size','removed_ground_pixels','opaque_colors']} for r in records},indent=2))


def reviews(records, originals, clean):
    fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
    font=ImageFont.truetype(fontpath,18);small=ImageFont.truetype(fontpath,14)
    headers=['Transparent','Grass','Dirt','Rock face']
    textures={}
    for name,rel in [('Grass','gba/art/cherrygrove-synthesis/references/HGSS-direct/grass-source.png'),
                     ('Dirt','gba/art/cherrygrove-synthesis/references/HGSS-direct/path-source.png')]:
        textures[name]=Image.open(ROOT/rel).convert('RGBA')
    # Actual Route 30 HGSS wall interior, read from the route reference.
    textures['Rock face']=Image.open(ROOT/'gba/art/claude-routes/references/route30-hgss.png').convert('RGBA').crop((342,20,358,36))
    width=884; rowh=186
    sheet=Image.new('RGB',(width,110+rowh*len(records)), '#202833');d=ImageDraw.Draw(sheet)
    d.text((20,15),'JOHTO TREES — terrain-free master review',font=font,fill='white')
    d.text((20,43),'3x native pixels • shared Cherrygrove design • native Cut tree shown intact',font=small,fill='#bacbd7')
    for i,h in enumerate(headers):d.text((20+i*216,79),h,font=font,fill='#e8d7a9')
    for row,record in enumerate(records):
        key=record['id'];y=110+row*rowh
        d.text((20,y),key+'  '+record['label'],font=font,fill='white')
        for col,kind in enumerate(headers):
            a=clean[key]
            if key=='T05': a=a[:,:16]  # Only intact frame in the object catalog.
            h,w=a.shape[:2];base=Image.new('RGBA',(68,50));pix=base.load()
            for yy in range(50):
                for xx in range(68):
                    pix[xx,yy]=((66,76,88,255) if (xx//4+yy//4)%2 else (49,58,69,255))
            if kind in textures:
                tex=textures[kind]
                for yy in range(0,50,tex.height):
                    for xx in range(0,68,tex.width):base.paste(tex,(xx,yy))
            base.alpha_composite(Image.fromarray(a),((68-w)//2,50-h))
            sheet.paste(base.convert('RGB').resize((204,150),Image.Resampling.NEAREST),(20+col*216,y+26))
    sheet.save(OUT/'review/trees-over-terrain.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    build(parser.parse_args().engine.resolve())
