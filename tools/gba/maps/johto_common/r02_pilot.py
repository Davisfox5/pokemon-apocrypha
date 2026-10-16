"""Rebuild an R02 side-cliff pilot; compile a review crop without editing the engine.

Native source art is traced into reusable 16px modules. Terrain remains independent.
The resulting map preview is decoded from Porytiles output, not a ROM screenshot.
"""
from pathlib import Path
import argparse, hashlib, json, struct, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/gba/maps'))
from johto_common.trees import rgba, sha, indexed
from johto_common.hgss_props import side_stairs
from claude_cherrygrove import ground, banks
from claude_cherrygrove.pixel import Palette
from route30_hgss_blocks import ground_native
from route36.gate_surround.build import decode, over
from tiles import Tileset, palette

OUT = ROOT / 'gba/art/johto-common/rocks/r02-pilot'
REF = ROOT / 'gba/art/route36/source/hgss-reference.png'
BASE = '6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf'
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
BOX = (160, 288, 352, 416)


def save(a, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a).save(path)


def rock_mask(a):
    r, g, b = a[..., :3].astype(int).transpose(2, 0, 1)
    # Scoped to explicit source rectangles; excludes lawn, foliage and path.
    return (r > g + 15) & (g > b + 12) & (r <= 184) & (b <= 104)


def modules():
    source = rgba(REF)
    face = source[300:332, 232:248].copy()
    mask = rock_mask(face)
    face[~mask] = 0
    repairs = []
    # The source tree hides the left edge. Extend that row's exposed rock into
    # the occluded margin, retaining its texture/color and the visible right rim.
    for y in range(32):
        xs = np.where(mask[y])[0]
        assert len(xs)
        for x in range(int(xs[0])):
            face[y, x] = face[y, xs[0]]
            repairs.append([x, y, int(xs[0]), y])
    # 64px stair surround retains the original projecting upper/lower rock lips.
    surround = source[336:400, 232:248].copy()
    surround[~rock_mask(surround)] = 0
    _, stair = side_stairs()
    flight = np.zeros_like(surround)
    over(flight, stair, 0, 10)
    surround[flight[..., 3] > 0] = 0
    bank = banks.Bank(8, 'R02_ROUNDED_ROCK', 'secondary')
    bank.keep((184,136,104), (160,120,88), (136,96,72), (104,72,56))
    bank.add('face', face).add('surround', surround)
    art = bank.build()
    clean_face = art['face'].to_rgba(); clean_surround = art['surround'].to_rgba()
    parts = {'face-a': clean_face[:16], 'face-b': clean_face[16:]}
    parts.update({f'stair-rock-{i}': clean_surround[i*16:(i+1)*16] for i in range(4)})
    parts.update({f'stair-tread-{i}': flight[i*16:(i+1)*16] for i in range(4)})
    for name, a in parts.items():
        a[a[...,3] == 0] = 0
        save(a, OUT/'source'/f'{name}.png')
        indexed(a, OUT/'source'/f'{name}.idx.png')
    # Original 16x48 clean stair master is unchanged; its 10px source anchor is
    # retained in the reusable 16x64 assembly rather than clipping the lips.
    strip = np.zeros((160,16,4), np.uint8)
    for y in range(0,80,16):over(strip, parts['face-a' if y%32 == 0 else 'face-b'], 0, y)
    over(strip, clean_surround, 0, 80)
    over(strip, flight, 0, 80)
    over(strip, parts['face-b'], 0, 144)
    save(strip, OUT/'source/west-section.png')
    save(face, OUT/'source/face-before-palette.png')
    save(surround, OUT/'source/surround-before-palette.png')
    return parts, strip, dict(reference=str(REF.relative_to(ROOT)), reference_sha256=sha(REF),
        face_source_box=[232,300,248,332], surround_source_box=[232,336,248,400],
        occlusion_repairs=repairs, palette=bank.palette.colors,
        rock_palette_changed_pixels=int(np.any(face!=clean_face,2).sum()+np.any(surround!=clean_surround,2).sum()),
        source_stair_master_sha256=sha(ROOT/'gba/art/johto-common/scenery/source/S04.png'))


def compile_crop(layers, game):
    h,w = layers[0].shape[:2];blocks=[];lookup={};grid=np.zeros((h//16,w//16),np.uint16)
    for y,x in np.ndindex(grid.shape):
        parts=[a[y*16:y*16+16,x*16:x*16+16].copy() for a in layers]
        key=b''.join(a.tobytes() for a in parts)
        if key not in lookup:lookup[key]=len(blocks);blocks.append(parts)
        grid[y,x]=lookup[key]
    src=OUT/'native/input';dest=OUT/'native/compiled';src.mkdir(parents=True,exist_ok=True)
    height=((len(blocks)+7)//8)*16
    for layer,name in enumerate(['bottom','middle']):
        a=np.zeros((height,128,4),np.uint8)
        for i,p in enumerate(blocks):a[i//8*16:i//8*16+16,i%8*16:i%8*16+16]=p[layer]
        save(a,src/(name+'.png'))
    Image.new('RGBA',(128,height)).save(src/'top.png')
    subprocess.run(['porytiles-legacy','compile-primary','-dual-layer','-tiles-primary-override=1008',
        '-pals-primary-override=13','-best-branches=smart','-o',str(dest),str(src),
        str(game/'include/constants/metatile_behaviors.h')],check=True)
    for palfile in (dest/'palettes').glob('*.pal'):
        palfile.write_text(palfile.read_text())  # Normalize compiler CRLF for Git.
    grid.astype('<u2').tofile(OUT/'native/preview-map.bin')
    sheet=Image.open(dest/'tiles.png');entries=list(struct.iter_unpack('<8H',(dest/'metatiles.bin').read_bytes()))
    result=np.zeros((h,w,4),np.uint8)
    for y,x in np.ndindex(grid.shape):
        for q,e in enumerate(entries[grid[y,x]]):
            tid=e&1023;ix=np.array(sheet.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)))
            if e&1024:ix=ix[:,::-1]
            if e&2048:ix=ix[::-1]
            dst=result[y*16+q%4//2*8:y*16+q%4//2*8+8,x*16+q%2*8:x*16+q%2*8+8]
            m=ix>0;dst[m,:3]=np.array(palette(dest/'palettes'/f'{e>>12:02}.pal'))[ix[m]];dst[m,3]=255
    target=layers[0].copy();over(target,layers[1])
    # Different tools expand RGB555 as either n*8 or n*255/31. Compare hardware values.
    errors=np.any(result[...,:3]//8!=target[...,:3]//8,2)
    assert not errors.any(),('native decode differs',int(errors.sum()))
    # Present source spelling after proving the exact hardware colors match.
    result[...,:3]=target[...,:3]
    return result,dict(metatiles=len(blocks),tile_slots=sheet.width*sheet.height//64,
        palette_banks=len({e>>12 for block in entries[:len(blocks)] for e in block if e&1023}),native_rgb555_pixel_errors=int(errors.sum()))


def main(game):
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=game,text=True).strip()
    for name in ['source','review','native']:(OUT/name).mkdir(parents=True,exist_ok=True)
    parts,strip,report=modules()
    route=ROOT/'gba/art/route36/source'
    grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82)
    tiles=Tileset(game,'johto_route36','johto_route36');layers,attrs=decode(tiles,grid)
    original=layers[0].copy();over(original,layers[1])
    plan=np.load(route/'plan.npy');cells=np.full(plan.shape,ground.GRASS,np.int8)
    cells[np.isin(plan,['P','S'])]=ground.PATH;cells[19:22,53:75]=ground.PATH;cells[22:24,14]=ground.PATH;cells[21:24,32]=ground.PATH
    gt=Tileset(game,'claude_route30','cherrygrove')
    pals={i:Palette(i,gt.pals[i>=6][i][1:],[str(j) for j in range(15)]) for i in range(13)}
    original_paint=ground.paint
    try:ground_native.install(game,pals);terrain,_=ground.paint(cells)
    finally:ground.paint=original_paint
    # Only the eight-cell west-face pilot is replaced. Preserve every other pixel.
    affected=np.zeros((512,1312),bool);affected[288:416,224:240]=True
    rock=np.zeros_like(original);over(rock,strip,224,256)
    trees=np.zeros_like(original);tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png')
    for x,y in json.loads((route/'features.json').read_text())['trees']:
        if x*16<240 and x*16+32>224 and y*16<416 and y*16+48>256:over(trees,tree,x*16,y*16)
    bottom=terrain.copy();over(bottom,rock)
    for y in range(288,416,8):
        for x in (224,232):
            sl=np.s_[y:y+8,x:x+8];bg=bottom[sl].copy();fg=trees[sl].copy();bg[fg[...,3]>0]=0
            if not fg[...,3].any():bg=terrain[sl].copy();fg=rock[sl].copy();bg[fg[...,3]>0]=0
            for a in (bg,fg):
                colors=len(np.unique(a[a[...,3]>0,:3],axis=0));assert colors<=15,(x,y,colors)
            layers[0][sl]=bg;layers[1][sl]=fg
    target=layers[0].copy();over(target,layers[1])
    assert np.array_equal(target[~affected],original[~affected])
    x,y,x1,y1=BOX;crop_layers=[a[y:y1,x:x1] for a in layers]
    decoded,compiled=compile_crop(crop_layers,game)
    save(decoded,OUT/'review/map-crop.png');save(original[y:y1,x:x1],OUT/'review/map-before.png')
    full=original.copy();full[y:y1,x:x1]=decoded;save(full,OUT/'review/route36-preview.png')
    # Assembly view shows the clean wall without trees masking its joins.
    assembly=terrain[y:y1,x:x1].copy();over(assembly,rock[y:y1,x:x1]);save(assembly,OUT/'review/rebuilt-section.png')
    source=rgba(REF)[y:y1,x:x1];save(source,OUT/'review/original-hgss.png')
    panels=[('1  ORIGINAL HGSS',source,'R02: untouched source-map crop'),
            ('2  REBUILT CLIFF + STAIRS',assembly,'Reusable pieces over separate ground'),
            ('3  ON ROUTE 36',decoded,'Native tiles decoded; offline map preview')]
    z=3;cw=608;sheet=Image.new('RGB',(cw*3,490),'#202d37');d=ImageDraw.Draw(sheet)
    for i,(title,a,note) in enumerate(panels):
        px=i*cw+16;d.text((px,15),title,font=ImageFont.truetype(FONT,21),fill='white')
        sheet.paste(Image.fromarray(a).convert('RGB').resize((192*z,128*z),Image.Resampling.NEAREST),(px,52))
        d.text((px,451),note,font=ImageFont.truetype(FONT,16),fill='#c5d3dd')
    sheet.save(OUT/'review/comparison.png')
    # Transparent native assets shown at 4x with a true checkerboard preview.
    sheet=Image.new('RGB',(768,310),'#202d37');d=ImageDraw.Draw(sheet)
    d.text((16,12),'R02 pilot / 16 x 16 modules / 4x nearest-neighbor',font=ImageFont.truetype(FONT,20),fill='white')
    for i,(name,a) in enumerate(parts.items()):
        x=i%5*152+16;y=i//5*128+54;bg=np.zeros((16,16,4),np.uint8);yy,xx=np.indices((16,16));bg[...,:3]=np.where(((xx//4+yy//4)%2)[...,None],185,220);bg[...,3]=255;over(bg,a)
        sheet.paste(Image.fromarray(bg).resize((64,64),Image.Resampling.NEAREST),(x,y));d.text((x,y+72),name,font=ImageFont.truetype(FONT,14),fill='white')
    sheet.save(OUT/'review/modules.png')
    report.update(compiled,engine_commit=BASE,installed=False,runtime_tested=False,
        pilot_cells=[14,18,1,8],map_crop_pixels=list(BOX),outside_pilot_pixel_changes=0,
        map_blockdata_sha256=sha(game/'data/layouts/JohtoRoute36/map.bin'),collision_and_events_changed=False,
        parts={k:dict(size=[16,16],sha256=sha(OUT/'source'/f'{k}.png')) for k in parts},
        scope='West side face and stair surround only. Upper plateau corners and other directions are not approved or built by this pilot.')
    (OUT/'evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=game,text=True).strip()
    print(json.dumps({k:report[k] for k in ['metatiles','tile_slots','native_rgb555_pixel_errors','outside_pilot_pixel_changes','installed']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);main(p.parse_args().engine)
