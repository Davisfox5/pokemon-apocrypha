"""Shared Cherrygrove architecture and native HGSS encounter-grass conversion.
No donor-render background keying is used for the encounter-grass family.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'gba/art/johto-cohesion'

def texture_source():
    sys.path.insert(0,str(ROOT/'tools/hoennconv'))
    import narc
    from nsbtx import Tex0
    archive=ROOT/'tools/vendor/hgss-map-reference/files/a/0/4/4'
    OUT.mkdir(parents=True,exist_ok=True)
    cached=OUT/'references/egrass.png'
    if not archive.exists():
        return np.asarray(Image.open(cached).convert('RGBA')).copy()
    t=Tex0(narc.load(archive)[2]);e=next(e for e in t.textures if e.name=='egrass')
    im=t.render(e).convert('RGBA');im.save(cached)
    (OUT/'provenance.json').write_text(json.dumps({'repository':'https://github.com/Davisfox5/pokeheartgold','hgss_revision':'9d8b7591f09b65804da2fb2dfd56f320633e0d36','original_art_credit':'Game Freak / Nintendo / Creatures','egrass_png_sha256':hashlib.sha256(cached.read_bytes()).hexdigest(),'archive':'files/a/0/4/4','member':2,'texture':'egrass','archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'strategy':'native 16-pixel TEX0 decode, stepped blade boundary masks; Cherrygrove indexed building modules reused'},indent=2)+'\n')
    return np.asarray(im).copy()

_SOURCE=None
def tall_slices():
    global _SOURCE
    if _SOURCE is None:
        _SOURCE=texture_source()
        # HGSS's source texture is lit by its DS material. Restore the measured
        # route-render shadow/highlight ladder, snapped to native five-bit RGB.
        source=np.unique(_SOURCE[...,:3].reshape(-1,3),axis=0)
        source=sorted(source,key=lambda v:int(v.sum()))
        ladder=[(32,112,80),(32,120,88),(40,136,80),(56,152,88),(64,168,112),(80,192,120)]
        original=_SOURCE[...,:3].copy()
        for old,new in zip(source,ladder):_SOURCE[...,:3][np.all(original==old,axis=2)]=new
    return _SOURCE

def tall_cell(src,n,s,w,e):
    a=src.copy();yy,xx=np.indices((16,16));keep=np.ones((16,16),bool)
    # Bladed edges have irregular but periodic outlines. Interior cells remain
    # uninterrupted texture; no mirrored half-cell or bottom stripe is repeated.
    top=np.array([3,2,3,1,0,2,3,2,1,0,2,3,1,2,0,1])
    bottom=np.array([1,2,0,1,2,1,0,2,1,3,2,0,1,2,1,0])
    side=np.array([2,1,2,0,1,0,2,1,0,1,0,2,1,0,1,0])
    if not n:keep &= yy>=top[xx]
    if not s:keep &= yy<16-bottom[xx]
    if not w:keep &= xx>=side[yy]
    if not e:keep &= xx<16-side[yy]
    a[...,3]=keep*255
    return a

def pad(a,w,h,x=0,y=0):
    out=np.zeros((h,w,4),np.uint8);out[y:y+a.shape[0],x:x+a.shape[1]]=a;return out

def architecture(base):
    house=base['house'].to_rgba();gable=base['gable'].to_rgba()
    # Large institute: two low residential wings around a higher central gable.
    # All roof, window, siding and shadow pixels come from accepted Cherrygrove.
    # Extend the accepted house shell by 128 pixels. End walls, roof rim,
    # window and single entrance stay intact; only interior roof/siding repeat.
    lab=np.zeros((80,208,4),np.uint8)
    lab[:,:16]=house[:,:16];lab[:,192:]=house[:,64:80]
    for x in range(16,192,16):lab[:,x:x+16]=house[:,16:32]
    # A continuous tiled roof plane, single eave and clean shared timber wall.
    # Tile texture is cut from the accepted roof, not its diagonal outer edge.
    tex=house[16:24,24:32]
    for y in range(8,40,8):
        for x in range(16,192,8):lab[y:y+8,x:x+8]=tex
    # Preserve native side faces; the long eave is one continuous horizontal run.
    for x in range(16,192,8):
        lab[40:56,x:x+8]=house[40:56,48:56]
        lab[56:80,x:x+8]=house[56:80,8:16]
    for x in (32,64,128,160):lab[56:72,x:x+16]=house[56:72,48:64]
    lab[56:80,96:112]=house[56:80,16:32]
    return dict(institute=lab,annex=gable,west_house=house,east_house=house,
                staff_a=house,staff_b=gable,
                gate29=pad(gable,144,144,32,64),
                mr_pokemon=pad(gable,112,96,16,16),
                berry_house=pad(house,96,80,0,0),gate31=pad(gable,96,96,0,16))

def cliff_modules():
    """One exposed face per terrace; crops never span adjoining elevations."""
    im=Image.open(ROOT/'gba/art/hgss-connections/references/route31-hgss.png').convert('RGBA')
    boxes={'plateau':(928,32,960,64),'face':(928,112,960,144),
           'west_face':(758,112,774,144),'cliff_corner':(824,160,856,192),
           'cave_mouth':(824,176,872,224)}
    return {k:np.asarray(im.crop(v)).copy() for k,v in boxes.items()}
