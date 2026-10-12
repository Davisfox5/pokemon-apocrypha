#!/usr/bin/env python3
"""Losslessly recover the preserved single-cel indexed adult Gold documents.

Formats verified against the local Aseprite source: app/crash/write_document.cpp
and doc/{image_io,palette_io,cel_data_io}. No drawing or palette conversion.
"""
import hashlib, json, re, shutil, struct, zlib
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'assets/src/trainers/recovered-gold'
OUT = BASE/'recovered'
OUT.mkdir(parents=True, exist_ok=True)
def newest(folder, prefix):
    return max(folder.glob(prefix+'-*'), key=lambda p:int(p.suffix[1:]))
def checked(path):
    data=path.read_bytes()
    assert data[:4]==b'FINE', path
    return data
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
reports=[]
for folder in sorted((BASE/'aseprite-backups').glob('*/*')):
    if not folder.is_dir() or not list(folder.glob('doc-*')):continue
    docfile=newest(folder,'doc');doc=checked(docfile)
    original=re.search(rb'/private/tmp/[^\x00]+?\.png',doc).group().decode()
    palfile=newest(folder,'pal');pal=checked(palfile)
    frame,ncolors=struct.unpack_from('<HH',pal,4)
    assert frame==0 and len(pal)==8+4*ncolors
    colors=[tuple(pal[i:i+4]) for i in range(8,len(pal),4)]
    sprfile=newest(folder,'spr');spr=checked(sprfile)
    mode,width,height,mask,frames=struct.unpack_from('<BHHII',spr,4)
    assert mode==2 and frames==1 and ncolors<=256
    celfile=newest(folder,'celdata');cel=checked(celfile)
    ident,x,y,cw,ch,opacity,imgid=struct.unpack_from('<IiiiiBI',cel,4)
    assert opacity==255
    imgfile=max(folder.glob(f'img-{imgid}.*'),key=lambda p:int(p.suffix[1:]))
    data=checked(imgfile)
    iid,fmt,iw,ih,imask,length=struct.unpack_from('<IBHHII',data,4)
    assert iid==imgid and fmt==2 and imask==mask and len(data)==21+length
    assert (iw,ih)==(cw,ch) and 0<=x<=width-iw and 0<=y<=height-ih
    pixels=zlib.decompress(data[21:]);assert len(pixels)==iw*ih
    image=Image.frombytes('P',(iw,ih),pixels)
    rgb=[v for color in colors for v in color[:3]]
    image.putpalette(rgb)
    canvas=Image.new('P',(width,height),mask);canvas.putpalette(rgb)
    canvas.paste(image,(x,y))
    result=OUT/f'{folder.parent.name}-doc{folder.name}.png'
    canvas.save(result,transparency=mask)
    decoded=Image.open(result)
    assert decoded.crop((x,y,x+iw,y+ih)).tobytes()==pixels
    assert decoded.getpalette()[:3*ncolors]==rgb
    assert decoded.info['transparency']==mask
    inputs=[docfile,palfile,sprfile,celfile,imgfile]
    reports.append(dict(session=folder.parent.name,document=folder.name,original_path=original,
        recovered_file=str(result.relative_to(ROOT)),canvas=[width,height],cel_bounds=[x,y,iw,ih],
        palette_size=ncolors,transparent_index=mask,pixel_roundtrip=True,
        sha256=sha(result),inputs={str(p.relative_to(BASE)):sha(p) for p in inputs}))

latest=next(r for r in reports if r['session']=='20260625-003641-36760')
destination=ROOT/'assets/src/trainers/overworld/gold_adult_ow_grid.png'
shutil.copyfile(ROOT/latest['recovered_file'],destination)
im=Image.open(destination).convert('RGBA')
preview=Image.new('RGBA',im.size,'#25333c');preview.alpha_composite(im)
preview.convert('RGB').resize((768,512),Image.Resampling.NEAREST).save(BASE/'gold-preview.png')
(BASE/'recovery.json').write_text(json.dumps(dict(
    recovered_on='2026-09-13',source='Aseprite recovery backups; original temporary PNGs unavailable',
    latest_grid=str(destination.relative_to(ROOT)),cell_size=[32,32],grid=[6,4],
    color_quantization_applied=False,documents=reports),indent=2)+'\n')
print(f'Recovered {len(reports)} documents; latest Gold sheet: {destination}')
