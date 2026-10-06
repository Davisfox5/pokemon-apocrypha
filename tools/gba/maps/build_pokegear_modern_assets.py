"""Native modern Pokégear interface assets for the existing Pokégear application.
Reference: original B/W default skin, not B2W2's circular layout.
Pokégear identity: physical casing, glass display, app tabs and radio dial.
B/W reference informs contrast and finish rather than the navigation geometry.
"""
from pathlib import Path
from math import cos, sin, pi
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[3]
out=root/'tools/vendor/gba/opening-house-work/graphics/apoc_pokegear'
art=root/'gba/art/pokegear-modern'
out.mkdir(exist_ok=True);art.mkdir(exist_ok=True)
# Native palette: transparent, panel, text, accent, black, background,
# honeycomb, dim teal, light bevel, grey, muted teal, white, amber, green,
# crimson, shadow. Runtime changes only panel/background/accent for styles.
colors=[(0,0,0),(16,24,24),(232,248,248),(0,192,200),(8,8,8),
        (8,16,16),(16,40,32),(24,64,64),(144,216,232),(88,104,104),
        (40,96,88),(248,248,248),(232,160,24),(8,176,96),(176,40,72),(8,32,40)]
PANEL,TEXT,ACCENT,BLACK,BG,GRID,DIM,BEVEL,GREY,MUTED,WHITE,AMBER,GREEN,RED,SHADOW=range(1,16)
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
  # Crisp mobile handset: chamfered frame, screen, speaker and home key.
  d.line((x-3,y-7,x+3,y-7,x+4,y-6,x+4,y+6,x+3,y+7,x-3,y+7,x-4,y+6,x-4,y-6,x-3,y-7),fill=col)
  d.line((x-1,y-5,x+1,y-5),fill=col)
  d.rectangle((x-2,y-3,x+2,y+3),outline=col)
  d.point((x,y+5),fill=col)
 else:
  d.ellipse((x-6,y-6,x+6,y+6),outline=col);d.ellipse((x-2,y-2,x+2,y+2),outline=col)
  for xx,yy in [(0,-8),(7,-4),(7,4),(0,8),(-7,4),(-7,-4)]:d.point((x+xx,y+yy),fill=col)
def shell():
 im=Image.new('P',(240,160),BG);im.putpalette(sum((list(c) for c in colors),[])+[0]*720);d=ImageDraw.Draw(im)
 # A physical Pokégear bezel: grey bevel, recessed display, orange index notch.
 d.rectangle((0,0,239,159),fill=SHADOW)
 d.polygon([(0,10),(10,0),(229,0),(239,10),(239,149),(229,159),(10,159),(0,149)],fill=GREY)
 d.polygon([(3,11),(11,3),(228,3),(236,11),(236,148),(228,156),(11,156),(3,148)],fill=BLACK)
 d.line((11,3,228,3,236,11),fill=BEVEL)
 d.line((3,11,3,148,11,156),fill=MUTED)
 d.polygon([(229,5),(234,10),(229,15)],fill=AMBER)
 # Clock/status band is always visible above a separate glass app display.
 d.rectangle((10,9,226,27),fill=PANEL)
 d.line((11,28,225,28),fill=DIM)
 d.line((82,12,82,24),fill=DIM)
 d.rectangle((11,32,228,127),fill=BG)
 for yy in range(33,128,4):d.line((12,yy,227,yy),fill=BLACK)
 d.line((11,32,228,32),fill=SHADOW)
 # Quiet corner marks and display hinge details keep a hardware character.
 for x,y,dx,dy in [(11,33,1,1),(228,33,-1,1),(11,127,1,-1),(228,127,-1,-1)]:
  d.line((x,y,x+dx*5,y),fill=DIM);d.line((x,y,x,y+dy*5),fill=DIM)
 d.rectangle((10,131,228,152),fill=PANEL)
 d.line((11,130,227,130),fill=DIM)
 # Recognizable field-device tabs, rounded icons with a mechanical index.
 for i,x in enumerate((28,74,120,166,212)):
  if i>0:d.line((x-23,135,x-23,149),fill=DIM)
  icon(d,i,x,142)
 d.line((14,154,226,154),fill=SHADOW)
 return im
bg=shell();radio=bg.copy();d=ImageDraw.Draw(radio)
# Pokégear globe dial rather than the C-Gear's connectivity modules.
d.ellipse((81,39,159,117),fill=BLACK,outline=BEVEL)
d.ellipse((85,43,155,113),outline=DIM)
for dy in (-18,0,18):
 yy=78+dy;half=round((34**2-dy**2)**0.5);d.line((120-half,yy,120+half,yy),fill=DIM)
for width in (28,52):d.ellipse((120-width//2,44,120+width//2,112),outline=DIM)
for a in range(0,360,30):
 x=120+round(cos(a*pi/180)*35);y=78+round(sin(a*pi/180)*35)
 xx=120+round(cos(a*pi/180)*32);yy=78+round(sin(a*pi/180)*32)
 d.line((x,y,xx,yy),fill=ACCENT)
for x,y in [(28,53),(212,53),(28,103),(212,103)]:
 d.ellipse((x-12,y-12,x+12,y+12),fill=PANEL,outline=DIM)
 d.arc((x-9,y-9,x+9,y+9),205,335,fill=BEVEL)
for name,im in [('shell',bg),('radio',radio)]:
 data=bytearray()
 for ty in range(20):
  for tx in range(30):
   vals=list(im.crop((tx*8,ty*8,tx*8+8,ty*8+8)).getdata())
   data.extend(a|(b<<4) for a,b in zip(vals[::2],vals[1::2]))
 (out/(name+'.bin')).write_bytes(data)
 im.save(art/(name+'-native.png'));im.resize((960,640),Image.Resampling.NEAREST).save(art/(name+'-preview.png'))
(out/'shell.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
