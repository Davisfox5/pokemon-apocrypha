"""Refine selected gate candidates at native resolution; never write engine files."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from claude_cherrygrove.pixel import Palette,Canvas
OUT=ROOT/'gba/art/johto-common-review/gates/refinement-1'
ART=ROOT/'gba/art';OUT.mkdir(parents=True,exist_ok=True)

def polygon(size,points):
 m=Image.new('1',size);ImageDraw.Draw(m).polygon(points,fill=1);return np.asarray(m)

def front():
 old=Image.open(ART/'route36/source/materials/gate-front.png').convert('RGBA');im=old.copy();d=ImageDraw.Draw(im)
 ink=(48,48,56,255);teal=(32,144,136,255);light=(56,176,176,255);deep=(8,104,80,255)
 # Keep the approved body, roof, windows and doorway. The source colour-key
 # had left noisy grass/foliage fringe on the right and gaps on both verges.
 # Trace straight metal edging along the existing silhouette; no rescaling.
 d.rectangle((7,44,8,116),fill=ink);d.line((8,45,8,108),fill=teal)
 d.rectangle((94,44,95,116),fill=ink);d.line((94,45,94,108),fill=teal)
 d.line((8,43,14,43),fill=ink);d.line((88,43,94,43),fill=ink)
 d.line((9,44,14,44),fill=light);d.line((88,44,93,44),fill=light)
 # Smooth the outer return corners and recover continuous foot courses.
 d.rectangle((7,109,21,119),fill=deep);d.rectangle((79,109,95,119),fill=deep)
 d.line((7,109,7,118),fill=ink);d.line((95,109,95,118),fill=ink)
 d.line((8,119,21,119),fill=ink);d.line((79,119,94,119),fill=ink)
 d.line((10,120,21,120),fill=ink);d.line((79,120,93,120),fill=ink)
 d.line((9,108,20,108),fill=teal);d.line((80,108,93,108),fill=teal)
 # Eave returns at the lower canopy had isolated background-colour holes.
 d.point((23,96),fill=teal);d.point((78,96),fill=teal)
 a=np.asarray(im).copy();a[a[:,:,3]==0]=0
 # Important: the central body and complete hipped roof remain untouched.
 before=np.asarray(old);assert np.array_equal(a[7:94,26:76],before[7:94,26:76])
 return old,Image.fromarray(a)

def side():
 old=Image.open(ART/'route36/source/materials/gate-side.png').convert('RGBA')
 raw=np.asarray(Image.open(ART/'violet-city/source/hgss-reference.png').convert('RGBA'))[416:528,:112].copy()
 # The same family of six teals is retained. Two glazing shades free one
 # extra grayscale slot, so stairs retain shadow, tread and nosing separately.
 colors=[(24,80,64),(24,112,104),(32,144,136),(48,160,152),(56,176,176),(80,192,192),
         (88,72,56),(144,120,96),(184,168,136),(216,200,168),
         (64,144,176),(160,224,232),(48,48,56),(104,112,104),(184,184,176)]
 pal=np.array(colors,int);out=np.zeros((112,112,4),np.uint8)
 body=polygon((112,112),[(16,3),(79,3),(79,12),(91,12),(91,96),(4,96),(4,89),(0,89),(0,29),(4,28),(4,12),(16,12)])
 def shade(mask,indices):
  lookup=pal[indices];out[mask,:3]=lookup[((raw[mask,:3].astype(int)[:,None]-lookup)**2).sum(2).argmin(1)];out[mask,3]=255
 shade(body,list(range(15)))
 roof=body.copy();roof[:,:16]=False;roof[:,80:]=False;roof[:3]=False;roof[62:]=False;shade(roof,list(range(6)))
 # The left-hand hood remains clipped by the original west map boundary.
 left=body.copy();left[:,4:]=False;left[:29]=False;left[74:]=False;shade(left,list(range(6)))
 im=Image.fromarray(out);d=ImageDraw.Draw(im)
 # Occluded lower masonry is continued from the unobscured center course.
 for y in range(89,97):
  for x in range(4,92):
   r,g,b=map(int,raw[y,x,:3])
   if g>r+4 and b<g-20:
    im.putpixel((x,y),(*colors[8 if y<92 else 6],255))
 # Full teal foundation skirt, reconstructed from exposed fragments between
 # the HGSS crowns (x24..40 / x56..72). Trees are removed, not the building.
 d=ImageDraw.Draw(im)
 d.rectangle((0,89,3,95),fill=(*colors[12],255))
 trim=[(0,96),(91,96),(95,94),(95,101),(91,105),(8,105),(4,102),(0,102)]
 d.polygon(trim,fill=(*colors[0],255))
 d.polygon([(0,97),(91,97),(94,95),(94,100),(90,103),(9,103),(5,101),(0,101)],fill=(*colors[2],255))
 d.polygon([(8,97),(90,97),(90,101),(10,101),(8,100)],fill=(*colors[4],255))
 d.line((8,96,90,96),fill=(*colors[1],255))
 # Source staircase silhouette excludes the canopy and neighboring cliff.
 stairs=polygon((112,112),[(103,64),(111,66),(111,95),(91,91),(91,88),(101,88),(101,76),(103,72)])
 out=np.asarray(im).copy();shade(stairs,[12,13,14]);im=Image.fromarray(out);d=ImageDraw.Draw(im)
 d.line([(103,64),(111,66),(111,95),(91,91)],fill=(*colors[12],255),width=1)
 # Retain the true east-west riser alignment and recover missing nosing.
 d.line((104,76,104,91),fill=(*colors[14],255))
 d.line((107,68,107,92),fill=(*colors[12],255))
 d.line((108,68,108,92),fill=(*colors[14],255))
 d.line([(92,89),(103,92),(110,94)],fill=(*colors[14],255))
 # Side hood: source-shaped perimeter, restricted to teal material. In the
 # old conversion every pixel below y64 was incorrectly forced to gray.
 canopy=polygon((112,112),[(91,28),(94,28),(94,29),(98,30),(102,31),(102,65),(100,72),(96,76),(91,76)])
 out=np.asarray(im).copy();shade(canopy,list(range(6)));im=Image.fromarray(out);d=ImageDraw.Draw(im)
 d.line([(91,28),(94,28),(94,29),(98,30),(102,31),(102,65),(100,72),(96,76),(91,76)],fill=(*colors[0],255))
 d.line([(92,30),(97,31),(100,32),(100,64),(98,70)],fill=(*colors[4],255))
 # Remove color-key pinholes at the bottom wall edge above the restored trim.
 d.line((4,95,91,95),fill=(*colors[6],255))
 d.line([(0,29),(2,29),(2,28),(4,28)],fill=(*colors[0],255))
 # Preserve the main roof pixels exactly from the existing native gate.
 a=np.asarray(im).copy();prior=np.asarray(old);a[3:62,16:80]=prior[3:62,16:80]
 return old,Image.fromarray(a)

def main():
 pairs=[('G01a',*front()),('G02',*side())];report={}
 for name,old,im in pairs:
  a=np.asarray(im);colors=np.unique(a[a[:,:,3]>0,:3],axis=0);assert len(colors)<=15,(name,len(colors));assert (colors%8==0).all()
  im.save(OUT/(name+'.png'));old.save(OUT/(name+'-before.png'))
  indexed=Image.new('P',im.size);palette=[0,0,0]+colors.flatten().tolist();indexed.putpalette(palette+[0]*(768-len(palette)))
  ids=np.zeros(a.shape[:2],np.uint8)
  for i,c in enumerate(colors,1):ids[(a[:,:,3]>0)&(a[:,:,:3]==c).all(2)]=i
  indexed.putdata(ids.ravel());indexed.save(OUT/(name+'-indexed.png'),transparency=0,bits=4)
  report[name]={'colors':len(colors),'size':im.size,'changed_pixels':int(np.any(a!=np.asarray(old),2).sum()),'opaque_pixels_added':int(((a[:,:,3]>0)&(np.asarray(old)[:,:,3]==0)).sum()),'main_roof_preserved':True}
 font='/System/Library/Fonts/Supplemental/Arial.ttf';f=ImageFont.truetype(font,22);small=ImageFont.truetype(font,16)
 board=Image.new('RGB',(792,490),(235,238,237));d=ImageDraw.Draw(board)
 for i,(name,old,im) in enumerate(pairs):
  x=28+i*384;d.text((x,18),name+' / revised',font=f,fill=(24,36,38));rgba=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);board.paste(rgba,(x,64),rgba)
 d.text((28,461),'Native tile artwork • regional rollout pending review',font=small,fill=(48,60,62));board.save(OUT/'revised-gates.png')
 board=Image.new('RGB',(1104,900),(235,238,237));d=ImageDraw.Draw(board)
 for row,(name,old,im) in enumerate(pairs):
  y=row*442;d.text((20,y+12),name,font=f,fill=(24,36,38))
  for col,(label,asset) in enumerate([('Before',old),('Revised',im)]):
   x=160+col*440;d.text((x,y+12),label,font=f,fill=(24,36,38));asset=asset.resize((asset.width*3,asset.height*3),Image.Resampling.NEAREST);board.paste(asset,(x,y+48),asset)
 board.save(OUT/'before-after.png');(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
