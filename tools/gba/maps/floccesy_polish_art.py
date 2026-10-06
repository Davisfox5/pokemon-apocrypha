"""Reference-led roof, railing, park and forest-opening native art modules.
All modifications are RGB composition only; caller locks every map property.
"""
import numpy as np
from PIL import Image,ImageDraw

def polish(scene,pals,spec,grid,R,A,lawn,floor):
 N=A/'native';N.mkdir(exist_ok=True)
 rgb5=lambda c:tuple((round(v*31/255)<<3)|(round(v*31/255)>>2) for v in c)
 oldp=[p[:] for p in pals]
 # Restrained fired-clay ramps, keeping facade colors and palette budgets.
 for bank,updates in {
  7:{8:(205,94,53),9:(183,73,42),10:(157,58,36),11:(136,49,32),14:(116,44,31),15:(82,36,28)},
  8:{3:(200,100,58),5:(185,81,44),6:(159,65,36),9:(143,54,33),10:(124,46,29),11:(104,40,27),12:(82,32,24)},
  9:{5:(239,96,65),6:(229,78,49),7:(201,76,58),8:(24,82,156),9:(215,61,41),10:(200,49,33),11:(179,41,32),12:(153,32,32),13:(132,27,32)},
  11:{4:(214,107,65),5:(205,94,53),8:(190,80,45),9:(177,70,41),10:(160,60,37),11:(144,53,33),12:(123,48,33),13:(99,40,29)}
 }.items():
  for ink,c in updates.items():pals[bank][ink]=rgb5(c)
 # Shared clay colors make repeated roof courses reuse identical native tiles.
 for dest,source in [(3,8),(5,9),(9,10)]:pals[8][dest]=pals[7][source]
 for dest,source in [(5,8),(8,9),(10,10)]:pals[11][dest]=pals[7][source]
 for dest,source in [(5,6),(7,9),(10,11),(12,13)]:pals[9][dest]=pals[9][source]
 # Recolor existing palette pixels before selectively replacing roofs.
 prior=scene.copy()
 for bank in (7,8,9,11):
  for i,c in enumerate(oldp[bank]):
   if c!=pals[bank][i]:scene[np.all(prior==c,axis=2)]=pals[bank][i]
 def ground_rect(x,y,w,h):
  for yy in range(y,y+h):
   for xx in range(x,x+w):scene[yy,xx]=floor(xx,yy)
 def paste(im,x,y):
  a=np.asarray(im);mask=a[:,:,3]>0;area=scene[y:y+im.height,x:x+im.width];area[mask]=a[:,:,:3][mask]
 for b in spec['buildings']+[dict(style='tower',x=19,y=44,pixel_dx=0)]:
  style=b['style'];bank={'house':7,'alder':8,'center':9,'tower':10,'shed':11}[style]
  src=np.asarray(Image.open(R/f'gba/art/floccesy-v4/native/{style}.png').convert('RGBA')).copy();original=src.copy();hh,ww=src.shape[:2]
  # Source tower uses the older color ramp; load it directly for exact mapping.
  from tiles import Tileset
  if style=='tower':
   ts=Tileset(R/'tools/vendor/gba/floccesy-detailed-work','floccesy','floccesy');colors=ts.pals[1][10]
  else:colors=oldp[bank]
  for idx,c in enumerate(colors):src[np.all(original[:,:,:3]==c,axis=2),:3]=pals[bank][idx]
  mapped=src.copy()
  for v in range(hh):
   for u in range(ww):
    r,g,bl,alpha=map(int,original[v,u]);red=alpha and r>120 and r>g*1.4 and r>bl*1.35
    if style in ('house','shed','alder') and red:
     # Even tile courses, staggered narrow vertical joints, restrained highlights.
     bright,mid,dark={'house':(8,9,10),'shed':(5,8,10),'alder':(3,5,9)}[style]
     row=v%8;col=(u+(v//8%2)*8)%16
     ink=dark if row==7 or col==15 else bright if row==0 else mid
     # Consistent shaded right roof plane; no random sparkling pixels.
     if u>ww//2 and ink==bright:ink=mid
     elif u>ww//2 and ink==mid:ink=dark
     src[v,u,:3]=pals[bank][ink]
    elif style=='center' and red:
     # Smooth enamel panels with controlled seams, following original silhouette.
     dist=abs(u-ww/2);ink=6 if dist<24 else 9 if dist<49 else 11
     if u%16 in (0,1):ink=min(13,ink+1)
     elif u%16==2:ink=max(5,ink-1)
     if v>65:ink=min(13,ink+1)
     src[v,u,:3]=pals[bank][ink]
    elif False:
     ink=12 if v%6==5 or (u+(v//6%2)*4)%8==7 else 5 if v%6==0 else 10
     src[v,u,:3]=pals[bank][ink]
  if style in ('house','shed'):
   rm=Image.new('L',(ww,hh));rd=ImageDraw.Draw(rm)
   if style=='house':
    rd.polygon([(0,40),(54,6),(111,40),(111,77),(82,77),(56,53),(29,77),(0,77)],fill=1)
    rd.rectangle((74,11,89,42),fill=0) # chimney
    rd.rectangle((51,5,60,57),fill=0) # terracotta ridge coping
   else:
    rd.polygon([(0,23),(55,3),(111,23),(111,82),(55,65),(0,82)],fill=1)
    rd.rectangle((53,3,60,65),fill=0)
   m=np.asarray(rm)>0
   for v,u in zip(*np.nonzero(m)):
    bright,mid,dark=(8,9,10) if style=='house' else (5,8,10)
    row=v%8;col=(u+(v//8%2)*8)%16
    ink=dark if row==7 or col==15 else bright if row==0 else mid
    if u>56:ink=dark if ink==mid else mid if ink==bright else dark
    src[v,u,:3]=pals[bank][ink];src[v,u,3]=255
  if style in ('house','shed'):
   if style=='house':pass
   else:
    for v in range(4,65):
     for u in range(54,60):
      ink=5 if u==54 else 10 if u==59 or v%8==7 else 8
      src[v,u,:3]=pals[11][ink];src[v,u,3]=255
  if style=='center':
   alpha=original[:,:,3]>0
   for v in range(80):
    for u in range(ww):
     if not alpha[v,u]:continue
     ink=6 if 50<=u<=93 else 9 if 20<=u<=123 else 11
     if u%16==0:ink=min(13,ink+1)
     elif u%16==1:ink=max(5,ink-1)
     if v>=70:ink=min(13,ink+1)
     if u==0 or u==ww-1 or not alpha[v,max(0,u-1)] or not alpha[v,min(ww-1,u+1)]:ink=13
     src[v,u,:3]=pals[bank][ink]
   ri=Image.fromarray(src);rd=ImageDraw.Draw(ri)
   rd.polygon([(53,56),(61,51),(83,51),(91,56)],fill=(*pals[bank][15],255));rd.rectangle((63,53,81,55),fill=(*pals[bank][4],255));src=np.asarray(ri).copy()
  if style=='alder':
   for v in range(17,72):
    for u in range(10,102):
     if (28<=u<=82 and v>=40) or (43<=u<=68 and v>=28):continue
     row=v%8;col=(u+(v//8%2)*8)%16
     ink=9 if row==7 or col==15 else 3 if row==0 else 5
     src[v,u,:3]=pals[bank][ink];src[v,u,3]=255
  if style=='alder':
   ri=Image.fromarray(src);rd=ImageDraw.Draw(ri);p=pals[8]
   rd.rectangle((8,8,103,17),fill=(*p[7],255));rd.rectangle((8,9,103,14),fill=(*p[2],255));rd.line((8,9,103,9),fill=(*p[1],255))
   for xx in range(10,104,16):
    rd.rectangle((xx,5,xx+5,12),fill=(*p[7],255));rd.rectangle((xx+1,5,xx+4,10),fill=(*p[2],255));rd.line((xx+1,5,xx+4,5),fill=(*p[1],255))
   # A clean timber dormer replaces the fragmented generated ornament.
   for yy in range(27,45):
    for xx in range(39,74):
     ink=9 if yy%8==7 or (xx+(yy//8%2)*8)%16==15 else 3 if yy%8==0 else 5
     rd.point((xx,yy),fill=(*p[ink],255))
   rd.polygon([(40,44),(56,30),(72,44)],fill=(*p[7],255));rd.polygon([(45,42),(56,34),(67,42)],fill=(*p[2],255));rd.line((40,43,56,29,72,43),fill=(*p[1],255),width=1)
   for xx in (1,104):
    rd.rectangle((xx,0,xx+6,23),fill=(*p[7],255));rd.rectangle((xx+1,1,xx+4,22),fill=(*p[2],255));rd.rectangle((xx,0,xx+6,3),fill=(*p[1],255))
   src=np.asarray(ri).copy()
  if style=='tower':
   rm=Image.new('L',(ww,hh));rd=ImageDraw.Draw(rm);rd.polygon([(3,29),(40,17),(77,29),(77,48),(3,48)],fill=1)
   m=np.asarray(rm)>0
   for v,u in zip(*np.nonzero(m)):
    ink=12 if v%8==7 or (u+(v//8%2)*4)%8==7 else 5 if v%8==0 else 10
    src[v,u,:3]=pals[bank][ink];src[v,u,3]=255
   ri=Image.fromarray(src);rd=ImageDraw.Draw(ri)
   for end in [(3,48),(77,48),(40,48)]:rd.line([(40,17),end],fill=(*pals[bank][8],255),width=2)
   rd.line((3,48,77,48),fill=(*pals[bank][14],255));src=np.asarray(ri).copy()
  im=Image.fromarray(src);im.save(N/f'{style}.png');gx=b['x']*16+b['pixel_dx'];gy=b['y']*16
  # Clear the building rectangle before placing its complete silhouette. Trees
  # behind a roof must never become holes in roof pixels or fragments on eaves.
  limit={'house':78,'shed':86,'alder':72,'center':82,'tower':49}[style]
  overlay=src.copy();overlay[limit:,:,3]=0
  paste(Image.fromarray(overlay),gx,gy)
  # Canopy and roof can share a hardware quad. Shade tiny lawn gaps using
  # the foliage ramp so the junction needs only those two opaque palettes.
  greens=set(pals[12][1:]);leaves=set(pals[6][1:]);roof=set(pals[bank][1:])
  for yy in range(gy//8*8,(gy+limit+7)//8*8,8):
   for xx in range(gx//8*8,(gx+ww+7)//8*8,8):
    q=scene[yy:yy+8,xx:xx+8];cs=set(map(tuple,q.reshape(-1,3)))
    if cs&leaves and cs&roof and cs&greens:
     for v in range(8):
      for u in range(8):
       c=tuple(q[v,u])
       if c in greens:q[v,u]=pals[6][3]
 # Regular glass modules remove fragmented reflections below the Center roof.
 b=next(b for b in spec['buildings'] if b['style']=='center');gx=b['x']*16+b['pixel_dx'];gy=b['y']*16
 for v in range(84,101):
  for u in range(21,124):
   if 61<=u<=84:continue
   ink=15 if u%16==0 or v in (84,100) else 8 if u%16==15 else 4
   if (u+v)%16 in (4,5):ink=2
   scene[gy+v,gx+u]=pals[9][ink]
 # Native rail modules: two rails, square capped posts, narrow contact shadows.
 def fence(x,y,vertical=False):
  im=Image.new('RGBA',(16,16));d=ImageDraw.Draw(im);p=pals[4]
  if not vertical:
   for top in (6,11):
    d.rectangle((0,top,15,top+2),fill=(*p[11],255));d.line((0,top,15,top),fill=(*p[3],255))
   d.rectangle((5,2,9,15),fill=(*p[11],255));d.rectangle((5,2,7,13),fill=(*p[2],255));d.rectangle((4,1,10,3),fill=(*p[3],255));d.line((4,1,10,1),fill=(*p[7],255))
  else:
   d.rectangle((6,0,9,15),fill=(*p[11],255));d.line((6,0,6,15),fill=(*p[3],255));d.line((8,0,8,15),fill=(*p[2],255))
   d.rectangle((5,2,9,13),fill=(*p[11],255));d.rectangle((5,2,7,11),fill=(*p[2],255));d.rectangle((4,1,10,3),fill=(*p[3],255));d.line((4,1,10,1),fill=(*p[7],255))
  for v in range(16):
   for u in range(16):scene[y*16+v,x*16+u]=pals[12][lawn(u,v,x,y)]
  paste(im,x*16,y*16);im.save(N/('rail-side.png' if vertical else 'rail-front.png'))
 for x in range(16,26):fence(x,28)
 for y in range(29,38):
  for x in (16,25):fence(x,y,True)
 for y in range(28,31):fence(46,y,True)
 # The woodland opening is framed by the same mature trees as its forest.
 gate=Image.new('RGBA',(80,64));d=ImageDraw.Draw(gate)
 d.rounded_rectangle((22,20,58,63),radius=12,fill=(*pals[6][15],255))
 d.rectangle((26,43,54,63),fill=(*pals[6][15],255))
 tree=np.asarray(Image.open(R/'gba/art/floccesy-v4/native/tree.png').convert('RGBA')).copy()
 from tiles import Tileset
 tp=Tileset(R/'tools/vendor/gba/floccesy-detailed-work','floccesy','floccesy').pals[1][6];org=tree.copy()
 for idx,c in enumerate(tp):tree[np.all(org[:,:,:3]==c,axis=2),:3]=pals[6][idx]
 ti=Image.fromarray(tree);gate.alpha_composite(ti,(0,0));gate.alpha_composite(ti,(32,0))
 d=ImageDraw.Draw(gate);d.rounded_rectangle((25,24,55,63),radius=10,fill=(*pals[6][15],255));d.rectangle((25,42,55,63),fill=(*pals[6][15],255))
 gate.save(N/'forest-opening.png');ground_rect(31*16,10*16,80,64);paste(gate,31*16,10*16)
 # Restore the reference's sheltered pocket park: a rounded gravel walk and
 # bench apron, with grouped planting rather than scattered isolated props.
 x0,y0,w,h=34*16,43*16,13*16,11*16
 shape=Image.new('1',(w,h));d=ImageDraw.Draw(shape)
 d.rounded_rectangle((80,0,143,47),radius=8,fill=1)
 d.line([(112,32),(112,48),(48,112),(48,144)],fill=1,width=40)
 for cx,cy in [(112,32),(112,48),(48,112),(48,144)]:d.ellipse((cx-20,cy-20,cx+20,cy+20),fill=1)
 path=np.asarray(shape)
 for v in range(h):
  for u in range(w):
   xx=x0+u;yy=y0+v;x,y=xx//16,yy//16
   if path[v,u]:
    ink=1
    if any(not(0<=u+dx<w and 0<=v+dy<h) or not path[v+dy,u+dx] for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]):ink=10
    scene[yy,xx]=pals[1][ink]
   else:scene[yy,xx]=pals[12][lawn(xx%16,yy%16,x,y)]
 # Repeated gravel detail only inside full ground quads keeps curved edges clean.
 for vy in range(0,h,8):
  for ux in range(0,w,8):
   if path[vy:vy+8,ux:ux+8].all():
    scene[y0+vy+4,x0+ux+2]=pals[1][3]
    scene[y0+vy+4,x0+ux+3]=pals[1][2]
 # A proper slatted bench in the original 48x24 footprint.
 bench=Image.new('RGBA',(48,24));d=ImageDraw.Draw(bench);p=pals[4]
 for yy in (3,7,11):
  d.rectangle((3,yy,44,yy+2),fill=(*p[8],255));d.line((3,yy,44,yy),fill=(*p[10],255))
 for xx in (5,40):d.rectangle((xx,2,xx+2,21),fill=(*p[11],255))
 d.rectangle((1,14,46,17),fill=(*p[8],255));d.line((1,14,46,14),fill=(*p[10],255));d.line((1,18,46,18),fill=(*p[11],255))
 bench.save(N/'park-bench.png');paste(bench,40*16,44*16)
 # Rounded, leaf-textured hedge clumps at the existing blocked positions.
 hedge=Image.new('RGBA',(16,32));d=ImageDraw.Draw(hedge);d.rectangle((1,3,14,30),fill=(*pals[6][11],255));d.rectangle((1,3,11,28),fill=(*pals[6][5],255));d.polygon([(1,3),(4,0),(14,0),(11,3)],fill=(*pals[6][3],255));d.line((2,6,2,23),fill=(*pals[6][4],255))
 for u,v in [(6,4),(9,7),(5,10),(9,14),(6,18),(10,22),(6,25)]:d.line((u,v,u+2,v),fill=(*pals[6][4],255));d.point((u,v-1),fill=(*pals[6][2],255))
 hedge.save(N/'hedge.png')
 for y in (43,46,49):paste(hedge,46*16,y*16)
 # The bin remains in its exact blocked cell; make its lid and ribs readable.
 bin=Image.new('RGBA',(16,16));d=ImageDraw.Draw(bin);d.rectangle((4,4,12,14),fill=(*pals[4][5],255));d.rectangle((5,4,10,13),fill=(*pals[4][1],255));d.line((6,6,6,12),fill=(*pals[4][3],255));d.line((9,6,9,12),fill=(*pals[4][3],255));d.ellipse((3,1,13,6),fill=(*pals[4][3],255));d.rectangle((6,2,10,3),fill=(*pals[4][11],255));paste(bin,45*16,46*16);bin.save(N/'bin.png')
 # Group low flowers on lawn around the sheltered seating; none on the path.
 flower=Image.open(R/'gba/art/floccesy-v4/native/flowers.png').convert('RGBA')
 for x,y in [(38,44),(38,45),(43,44),(44,44),(43,50),(44,50),(35,52),(36,53)]:
  u,v=x*16-x0,y*16-y0
  if not path[v:v+16,u:u+16].any():paste(flower,x*16,y*16)
 Image.fromarray(scene).save(A/'evidence/authored-polish.png')
 return scene
