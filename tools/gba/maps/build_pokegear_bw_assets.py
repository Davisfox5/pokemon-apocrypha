"""Native C-Gear-style interface assets for the existing Pokégear application.
Reference: original B/W default skin, not B2W2's circular layout.
No networking services or campaign mechanics are introduced by this adapter.
"""
from pathlib import Path
from math import cos, sin, pi
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[3]
out=root/'tools/vendor/gba/opening-house-work/graphics/apoc_pokegear'
art=root/'gba/art/pokegear-bw'
out.mkdir(exist_ok=True);art.mkdir(exist_ok=True)
# Native palette: transparent, panel, text, accent, black, background,
# honeycomb, dim teal, light bevel, grey, muted teal, white, amber, green,
# crimson, shadow. Runtime changes only panel/background/accent for styles.
colors=[(0,0,0),(16,24,24),(232,248,248),(0,192,200),(8,8,8),
        (8,16,16),(16,40,32),(24,64,64),(144,216,232),(88,104,104),
        (40,96,88),(248,248,248),(232,160,24),(8,176,96),(176,40,72),(8,32,40)]
PANEL,TEXT,ACCENT,BLACK,BG,GRID,DIM,BEVEL,GREY,MUTED,WHITE,AMBER,GREEN,RED,SHADOW=range(1,16)
def hexagon(x,y,r):
 return [(round(x+r*cos(i*pi/3)),round(y+r*sin(i*pi/3))) for i in range(6)]
def linehex(d,x,y,r,col,width=1):
 pts=hexagon(x,y,r);d.line(pts+[pts[0]],fill=col,width=width)
def icon(d,i,x,y,col=TEXT):
 # Button glyphs are 13 native pixels: fine-line hardware UI, not overworld art.
 if i==0:
  d.ellipse((x-6,y-6,x+6,y+6),outline=col);d.line((x,y-4,x,y,x+3,y+2),fill=col)
 elif i==1:
  d.rectangle((x-6,y-3,x+6,y+5),outline=col);d.line((x-4,y-3,x+3,y-7),fill=col);d.ellipse((x-4,y,x-2,y+2),outline=col)
  for yy in (0,2):d.line((x+1,y+yy,x+4,y+yy),fill=col)
 elif i==2:
  d.line((x-6,y+5,x-6,y-5,x-2,y-3,x+2,y-5,x+6,y-3,x+6,y+6,x+2,y+4,x-2,y+6,x-6,y+5),fill=col)
  d.line((x-2,y-3,x-2,y+6),fill=col);d.line((x+2,y-5,x+2,y+4),fill=col)
 elif i==3:
  d.line((x-5,y-6,x-6,y-2,x-4,y+2,x,y+6,x+4,y+6,x+6,y+3),fill=col,width=2)
  d.line((x-5,y-6,x-2,y-4,x-4,y-2),fill=col,width=2);d.line((x+6,y+3,x+3,y,x+1,y+3),fill=col,width=2)
 else:
  linehex(d,x,y,6,col);d.ellipse((x-2,y-2,x+2,y+2),outline=col)
  for xx,yy in [(0,-8),(7,-4),(7,4),(0,8),(-7,4),(-7,-4)]:d.point((x+xx,y+yy),fill=col)
def shell():
 im=Image.new('P',(240,160),BG);im.putpalette(sum((list(c) for c in colors),[])+[0]*720);d=ImageDraw.Draw(im)
 # B/W's flat-top honeycomb, low-contrast green bed and three accent groups.
 for col in range(12):
  for row in range(7):
   x=col*22-1;y=35+row*25+(12 if col%2 else 0)
   linehex(d,x,y,14,GRID)
 for x,y,c in [(42,46,RED),(42,71,RED),(42,96,RED),(120,46,DIM),(120,71,DIM),(120,96,DIM),(198,46,AMBER),(198,71,AMBER),(198,96,AMBER)]:
  linehex(d,x,y,13,c)
 # Angled hardware casing with layered silver/cyan bevels, as in the donor.
 pts=[(1,18),(18,1),(222,1),(238,18),(238,142),(222,158),(18,158),(1,142),(1,18)]
 d.line(pts,fill=BEVEL,width=2)
 pts=[(4,19),(19,4),(221,4),(235,19),(235,141),(220,155),(20,155),(4,141),(4,19)]
 d.line(pts,fill=ACCENT)
 d.rectangle((19,5,220,24),fill=BLACK);d.line((14,27,225,27),fill=DIM)
 d.rectangle((9,130,230,153),fill=BLACK);d.line((10,129,229,129),fill=DIM)
 # Replace the network modules with the five real field-device applications.
 for i,x in enumerate((28,74,120,166,212)):
  linehex(d,x,142,14,DIM);icon(d,i,x,142)
 return im
bg=shell();radio=bg.copy();d=ImageDraw.Draw(radio)
# Circular dial remains functional, now drawn in the C-Gear's dark/cyan UI.
d.ellipse((81,39,159,117),fill=BLACK,outline=BEVEL);d.ellipse((85,43,155,113),outline=DIM)
for a in range(0,360,30):
 x=120+round(cos(a*pi/180)*35);y=78+round(sin(a*pi/180)*35)
 xx=120+round(cos(a*pi/180)*31);yy=78+round(sin(a*pi/180)*31)
 d.line((x,y,xx,yy),fill=ACCENT)
for x,y in [(28,53),(212,53),(28,103),(212,103)]:
 d.polygon(hexagon(x,y,16),fill=BLACK);linehex(d,x,y,16,DIM);linehex(d,x,y,13,ACCENT)
for name,im in [('shell',bg),('radio',radio)]:
 data=bytearray()
 for ty in range(20):
  for tx in range(30):
   vals=list(im.crop((tx*8,ty*8,tx*8+8,ty*8+8)).getdata())
   data.extend(a|(b<<4) for a,b in zip(vals[::2],vals[1::2]))
 (out/(name+'.bin')).write_bytes(data)
 im.save(art/(name+'-native.png'));im.resize((960,640),Image.Resampling.NEAREST).save(art/(name+'-preview.png'))
(out/'shell.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
