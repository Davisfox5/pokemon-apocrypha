"""Measured HGSS silhouettes; masks never key away roof/wall colors.
Native source pixels, hand-defined outlines, protected windows/doors, reusable terrain.
"""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from claude_cherrygrove import banks,hgss
ROOT=Path(__file__).resolve().parents[4]
REF=ROOT/'gba/art/hgss-connections/references'
OUT=ROOT/'gba/art/johto-polish/native'

def masked(name,box,polygon):
    im=Image.open(REF/(name+'-hgss.png')).convert('RGBA').crop(box)
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(polygon,fill=255)
    im.putalpha(mask);return np.asarray(im).copy()

def windmill(name,box,head,pole,base):
    im=Image.open(REF/(name+'-hgss.png')).convert('RGBA').crop(box);a=np.asarray(im).copy()
    mask=Image.new('L',im.size);d=ImageDraw.Draw(mask);d.polygon(head,fill=255);d.rectangle(pole,fill=255)
    rgb=a[...,:3].astype(int)
    neutral=(rgb[...,1]-rgb[...,2]<=28)&(rgb[...,1]-rgb[...,0]<=30)&(rgb[...,0]-rgb[...,2]<=40)
    keep=(np.asarray(mask)>0)&neutral
    bm=Image.new('L',im.size);ImageDraw.Draw(bm).rectangle(base,fill=255);keep|=np.asarray(bm)>0
    a[...,3]=keep*255;return a

def new_bark():
    lab=masked('new-bark',(160,32,272,144),[(8,9),(23,7),(57,7),(91,23),(91,38),(108,38),(108,101),(5,101),(5,12)])
    # Source door frame is x50..66: align it to cell column 3, preserving its border.
    hgss.shift_rect(lab,50,77,16,24,-2)
    # Bottom padding is transparent: door behavior belongs to the wall's final row.
    lab[104:]=0
    upper=masked('new-bark',(320,64,432,176),[(19,31),(59,0),(78,13),(107,30),(107,99),(17,99),(17,88),(10,88),(10,80),(17,74)])
    west=masked('new-bark',(80,208,160,288),[(4,18),(38,1),(73,14),(73,70),(10,70),(10,57),(3,57)])
    # Keep the real source doorway, aligned to one movement cell.
    hgss.shift_rect(west,23,48,16,22,9)
    east=masked('new-bark',(256,240,352,320),[(4,18),(43,0),(67,10),(82,22),(82,64),(6,64),(6,49),(3,49)])
    hgss.shift_rect(east,23,43,16,21,9)
    # Windmill blades, pole, base are separate assets: the roof is not punched out.
    wind=windmill('new-bark',(136,224,184,304),[(26,0),(30,0),(30,8),(26,14),(26,18),(22,24),(21,28),(16,27),(17,21),(14,21),(13,18),(4,17),(3,13),(7,12),(16,16),(19,10),(24,7)],(21,20,25,66),(17,64,30,72))
    labwind=windmill('new-bark',(264,24,312,112),[(26,0),(30,0),(29,14),(22,24),(19,29),(17,34),(12,34),(12,30),(16,27),(14,26),(6,24),(2,20),(2,17),(8,17),(16,22),(21,17),(24,11)],(21,27,25,73),(15,70,34,81))
    red=masked('new-bark',(144,104,160,136),[(9,5),(14,5),(15,12),(15,23),(9,23),(9,13),(7,13),(7,9)])
    blue=masked('new-bark',(264,72,280,128),[(7,13),(11,12),(13,15),(13,49),(6,49),(6,16)])
    fence=masked('new-bark',(120,72,168,144),[(3,8),(42,8),(42,64),(5,64),(5,26),(0,24),(0,14)])
    # Fence only; connected building pixels are explicitly excluded.
    fence[:,40:]=0;fence[27:,9:]=0
    return dict(institute=lab,annex=upper,west_house=west,east_house=east,wind=wind,labwind=labwind,red_mailbox=red,blue_mailbox=blue,lab_fence=fence)

def route31():
    cliff=masked('route31',(720,0,1008,224),[(168,0),(287,0),(287,191),(161,191),(161,214),(39,214),(39,97),(24,97),(24,46),(32,25),(103,25),(103,13),(168,13)])
    wall=masked('route31',(504,112,568,480),[(33,0),(58,0),(58,142),(50,160),(30,168),(30,333),(61,333),(61,359),(8,359),(8,296),(20,280),(20,0)])
    gate=masked('route31',(0,160,96,256),[(0,4),(75,4),(79,15),(79,53),(88,53),(88,86),(0,86)])
    bridge=masked('route31',(528,240,576,304),[(8,16),(34,6),(39,15),(39,39),(33,52),(9,63),(5,55),(5,32)])
    # Pond's blue water and earthy shore are a separate material, not coastal sea foam.
    apricorn=masked('route31',(320,192,352,240),[(8,9),(17,9),(18,13),(21,13),(21,19),(17,22),(17,31),(13,31),(13,24),(8,22),(7,17)])
    return dict(cliff=cliff,wall=wall,gate=gate,bridge=bridge,apricorn=apricorn)

def export(raw,canvases):
    OUT.mkdir(parents=True,exist_ok=True)
    for name,rgba in raw.items():Image.fromarray(rgba).save(OUT/(name+'-source.png'))
    for name,c in canvases.items():
        if name in raw:Image.fromarray(c.to_rgba()).save(OUT/(name+'-gba.png'))

if __name__=='__main__':
    for raw in [new_bark(),route31()]:
        group=banks.Bank(9,'inspection','secondary')
        for k,v in raw.items():group.add(k,v)
        cvs=group.build();export(raw,cvs)
        for k,c in cvs.items():
            unique={c.px[y:y+8,x:x+8].tobytes() for y in range(0,c.h,8) for x in range(0,c.w,8)}
            print(k,len(unique))


def cliff_modules():
    im=Image.open(REF/'route31-hgss.png').convert('RGBA')
    # Texture, exposed face and corner cuts are distinct; each remains native scale.
    boxes={'plateau':(928,32,960,64),'face':(928,144,960,192),
           'west_face':(758,112,774,160),'cliff_corner':(824,128,856,176),
           'cave_mouth':(824,176,872,224)}
    return {k:np.asarray(im.crop(v)).copy() for k,v in boxes.items()}


def pond_modules():
    im=Image.open(REF/'route31-hgss.png').convert('RGBA')
    boxes={'lake0':(424,136,440,152),'lake1':(440,136,456,152),
           'lake2':(424,152,440,168),'lake3':(440,152,456,168),
           'lake_n':(440,112,456,128),'lake_w':(408,144,424,160),
           'lake_s':(488,248,504,264),'lake_nw':(408,112,424,128),
           'lake_sw':(456,248,472,264)}
    return {k:np.asarray(im.crop(v)).copy() for k,v in boxes.items()}
