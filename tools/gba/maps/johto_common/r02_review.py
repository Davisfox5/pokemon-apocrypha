"""Coordinate-labelled native cell sheets, keeping original/before/after separate."""
from pathlib import Path
import sys,json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'gba/art/johto-common/rocks/r02-refined'
F='/System/Library/Fonts/Supplemental/Arial.ttf'
full=(P/'review/original-full.png').exists()
images=[Image.open(P/'review'/f'{n}.png').convert('RGB') for n in (['original-full','before-full','native-full'] if full else ['original','before','map'])]
records=json.loads((P/'evidence/cell-review.json').read_text())
xmin=0 if full else min(r['x'] for r in records);ymin=0 if full else min(r['y'] for r in records)
for page in range(math.ceil(len(records)/24)):
 sheet=Image.new('RGB',(1200,540),'#202d37');d=ImageDraw.Draw(sheet);d.text((12,8),f'R02 / cells {page*24+1}-{min(len(records),page*24+24)} / original | previous candidate | corrected',font=ImageFont.truetype(F,18),fill='white')
 for i,r in enumerate(records[page*24:page*24+24]):
  x=i%6*200+8;y=i//6*126+38;d.text((x,y),f"({r['x']}, {r['y']})",font=ImageFont.truetype(F,14),fill='white');cx=(r['x']-xmin)*16;cy=(r['y']-ymin)*16
  for j,im in enumerate(images):sheet.paste(im.crop((cx,cy,cx+16,cy+16)).resize((64,64),Image.Resampling.NEAREST),(x+j*64,y+22))
  d.text((x,y+91),r['material'],font=ImageFont.truetype(F,11),fill='#c5d3dd')
 sheet.save(P/'review'/f'cells-{page+1}.png')
