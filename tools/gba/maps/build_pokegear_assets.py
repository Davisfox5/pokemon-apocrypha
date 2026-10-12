"""Retile verified HGSS screen fragments for the GBA single-screen gear shell."""
from pathlib import Path
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[3]
src=Image.open(root/'gba/art/pokegear/references/hgss-radio-dual.png').convert('RGB')
out=root/'tools/vendor/gba/opening-house-work/graphics/apoc_pokegear';out.mkdir(exist_ok=True)
# Preserve actual HGSS tuner, preset buttons and tab icons. New single-screen
# placement is needed: DS has 384 vertical pixels, GBA has 160.
blue=(40,64,232);ink=(0,0,0);white=(248,248,248)
bg=Image.new('RGB',(240,160),blue);d=ImageDraw.Draw(bg)
d.rectangle((0,0,239,23),fill=(64,80,104));d.line((0,23,239,23),fill=white,width=2)
for y in [26,28,128,130]:d.line((0,y,239,y),fill=(40,56,168))
# Five real app icons, reduced to 32x20, with spacing for button navigation.
for i,(x0,x1) in enumerate([(34,127),(155,239),(267,355),(381,469),(503,602)]):
 icon=src.crop((x0,853,x1,920)).resize((32,22),Image.Resampling.NEAREST)
 # Strip the source's static radio selection brackets; runtime draws selection.
 for iy in range(icon.height):
  for ix in range(icon.width):
   r,g,b=icon.getpixel((ix,iy))
   if r>150 and g<100 and b<100:icon.putpixel((ix,iy),white)
 bg.paste(icon,(8+46*i,137))
d.rectangle((0,133,239,134),fill=white)
radio=bg.copy()
globe=src.crop((158,538,452,830)).resize((84,84),Image.Resampling.NEAREST)
radio.paste(globe,(78,36))
for x,y in [(14,46),(193,46),(14,96),(193,96)]:
 radio.paste(src.crop((41,587,114,647)).resize((30,25),Image.Resampling.NEAREST),(x,y))
# Shared 16-color palette, independent from field tiles and palettes.
sample=Image.new('RGB',(240,320));sample.paste(bg,(0,0));sample.paste(radio,(0,160))
q=sample.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
pal=[0,0,0]+q.getpalette()[:45]
# Text colors reserved deliberately: index 1 panel, 2 white, 3 gold, 4 black.
colors=[(0,0,0),(64,80,104),(248,248,248),(248,192,24),(8,16,24),(40,64,232),(32,48,160),(40,104,168),(104,160,216),(144,176,200),(184,192,208),(216,216,224),(240,128,48),(40,176,88),(184,40,40),(88,96,112)]
palette=Image.new('P',(1,1));palette.putpalette(sum((list(c) for c in colors),[])+[0]*720)
for name,img in [('shell',bg),('radio',radio)]:
 q=img.quantize(palette=palette,dither=Image.Dither.NONE)
 # Transform bitmap into 8x8 tiles expected by CopyToWindowPixelBuffer.
 data=bytearray()
 for ty in range(20):
  for tx in range(30):
   vals=list(q.crop((tx*8,ty*8,tx*8+8,ty*8+8)).getdata())
   data.extend(a|(b<<4) for a,b in zip(vals[::2],vals[1::2]))
 (out/(name+'.bin')).write_bytes(data)
 q.resize((960,640),Image.Resampling.NEAREST).save(root/'gba/art/pokegear'/(name+'-retiled.png'))
(out/'shell.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
