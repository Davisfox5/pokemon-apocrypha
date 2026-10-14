"""Actual HGSS side-facing gate; accepted north/south gate is pixel-preserved."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from claude_cherrygrove import banks
from claude_cherrygrove.pixel import Canvas,Palette
ROOT=Path(__file__).resolve().parents[4]

def create(pals,materials):
 # Preserve the owner's accepted front gate, including its exact native RGB.
 front=np.array(Image.open(materials.parent/'approved-front-gate.png').convert('RGBA'))
 colors=[tuple(map(int,c)) for c in np.unique(front[front[:,:,3]>0,:3],axis=0)]
 pals[9]=Palette(9,colors,[str(i) for i in range(len(colors))]);c=Canvas(112,128,pals[9])
 for i,color in enumerate(colors,1):c.px[np.all(front[:,:,:3]==color,axis=2)&(front[:,:,3]>0)]=i
 assets={'gate-front':c};assert np.array_equal(c.to_rgba(),front)
 # This is the actual east-west gate model in the Violet HGSS map, not a
 # front-facing facade with an entrance appended. Keep its side canopy,
 # recessed portal, perpendicular stair flight, window band and masonry.
 source=ROOT/'gba/art/violet-city/source/hgss-reference.png'
 rgb=np.array(Image.open(source).convert('RGBA'))[416:528,:112].copy()
 Image.fromarray(rgb).save(materials/'hgss-side-gate-source.png')
 mask=Image.new('1',(112,112));d=ImageDraw.Draw(mask)
 d.polygon([(16,3),(79,3),(79,12),(91,12),(91,28),(94,28),(94,29),(102,31),(102,62),(111,65),(111,95),(91,95),(91,98),(4,98),(4,89),(0,89),(0,29),(4,28),(4,12),(16,12)],fill=1)
 rgb[:,:,3]=np.array(mask,dtype=np.uint8)*255
 # The HGSS foreground trees cover a few pixels of the bottom sill. Recover
 # only those occluded pixels from the same uninterrupted masonry course.
 for y in range(89,98):
  for x in range(5,91):
   r,g,b=map(int,rgb[y,x,:3])
   if g>r+4 and b<g-20:
    rgb[y,x,:3]=rgb[min(y,94),48:64,:3][x%16]
 # Pin the actual material families. A joint median-cut palette had merged
 # the gray side stairs with brown masonry and the roof shadow with the wall.
 rgb[96:,:,3]=0
 colors=[(24,80,64),(24,112,104),(32,144,136),(48,160,152),(56,176,176),(80,192,192),
         (88,72,56),(144,120,96),(184,168,136),(216,200,168),
         (64,144,176),(112,200,224),(160,224,232),(104,112,104),(176,184,176)]
 pals[10]=Palette(10,colors,[str(i) for i in range(15)])
 c=Canvas(112,112,pals[10]);mask=rgb[:,:,3]>0;pal=np.array(colors,int)
 c.px[mask]=((rgb[mask,:3].astype(int)[:,None]-pal)**2).sum(2).argmin(1)+1
 # Material masks preserve source edge positions and source tread lines.
 for y in range(112):
  for x in range(112):
   if not mask[y,x]:continue
   if 16<=x<80 and 3<=y<62:
    c.px[y,x]=int(((rgb[y,x,:3].astype(int)-pal[:6])**2).sum(1).argmin())+1
   elif x>=91 and y>=64:
    c.px[y,x]=14+int(((rgb[y,x,:3].astype(int)-pal[13:])**2).sum(1).argmin())
 assets['gate-side']=c
 for name,c in assets.items():Image.fromarray(c.to_rgba()).save(materials/(name+'.png'))
 return assets
