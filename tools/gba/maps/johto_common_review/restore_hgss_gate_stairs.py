"""Restore HGSS staircase pixels; only round source colors to GBA RGB555."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
import refine_gates as base
PREV=base.OUT.parent/'refinement-3';OUT=PREV.parent/'refinement-4'
SOURCE=base.ROOT/'gba/art/violet-city/source/hgss-reference.png'

def main():
 OUT.mkdir(exist_ok=True)
 old=Image.open(PREV/'G02.png').convert('RGBA');a=np.array(old)
 raw=np.array(Image.open(SOURCE).convert('RGBA').crop((0,416,112,528)))
 # Use actual source step faces, nosings, risers and perimeter. Preserve the
 # cleaned building/plinth; source trees and paving are outside these masks.
 stone=[(22,22,22),(37,37,37),(80,80,72),(96,96,96),(112,112,112),(144,144,144),(140,148,140),(189,189,189)]
 teals=np.array([(24,80,64),(24,112,104),(32,144,136),(48,160,152),(56,176,176),(80,192,192)])
 # Restore the source hood above the flight as well, so the copied stair
 # joins its original contour rather than the earlier redrawn canopy.
 a[28:76,92:112]=0
 hood_colors={(66,189,189),(41,156,148),(24,115,90),(33,123,107)}
 for y in range(28,76):
  for x in range(92,102):
   c=tuple(raw[y,x,:3])
   if c in hood_colors:
    a[y,x,:3]=teals[((teals-np.array(c))**2).sum(1).argmin()];a[y,x,3]=255
   elif c==(22,22,22):
    a[y,x]=(24,24,24,255)
 mask=np.zeros(a.shape[:2],bool)
 for x0,x1,y0,y1 in [(92,112,62,96),(0,4,74,96)]:
  for y in range(y0,y1):
   for x in range(x0,x1):
    c=tuple(raw[y,x,:3])
    if c in stone:
     a[y,x,:3]=np.minimum((raw[y,x,:3].astype(int)+4)//8*8,248);a[y,x,3]=255;mask[y,x]=True
    elif x>=96 or y<94:
     r,g,b=c
     if g>r+30 and b>r+20:
      a[y,x,:3]=teals[((teals-np.array(c))**2).sum(1).argmin()];a[y,x,3]=255
     else:a[y,x]=0
 # The previous redraw extended two pixels below the actual flight.
 a[96:98,96:112]=0
 im=Image.fromarray(a)
 front=Image.open(PREV/'G01a.png').convert('RGBA')
 base.OUT=OUT;base.front=lambda:(front,front);base.side=lambda:(old,im);base.main(max_colors=255)
 quantized=np.minimum((raw[:,:,:3].astype(int)+4)//8*8,248)
 assert np.array_equal(a[mask,:3],quantized[mask])
 assert np.array_equal(a[:,:92][:,4:],np.array(old)[:,:92][:,4:])
 report=json.loads((OUT/'validation.json').read_text())
 report['G02'].update({'source':'gba/art/violet-city/source/hgss-reference.png','source_crop':[0,416,112,528],'hgss_stair_pixels':int(mask.sum()),'source_stair_pixel_errors_after_rgb555_rounding':0,'method':'Direct source pixels, no scaling or redrawing; RGB555 rounding only on stonework','main_building_preserved':True})
 report['G01a']['identical_to_refinement_3']=True
 (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 Image.fromarray(raw).save(OUT/'HGSS-reference-crop.png')
 board=Image.new('RGB',(864,540),(235,238,237));d=ImageDraw.Draw(board);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
 d.text((24,18),'G02 / HGSS staircase',font=font,fill=(24,36,38));full=im.resize((448,448),Image.Resampling.NEAREST);board.paste(full,(24,58),full)
 d.text((510,18),'Source steps / native copy',font=font,fill=(24,36,38));detail=im.crop((88,24,112,104)).resize((144,480),Image.Resampling.NEAREST);board.paste(detail,(586,52),detail);board.save(OUT/'G02-close-up.png')
 compare=Image.new('RGB',(672,366),(235,238,237));d=ImageDraw.Draw(compare)
 for i,(title,asset) in enumerate([('HGSS reference',Image.fromarray(raw)),('Revised G02',im)]):
  d.text((i*336+16,10),title,font=font,fill=(24,36,38));crop=asset.crop((88,58,112,100)).resize((168,294),Image.Resampling.NEAREST);compare.paste(crop,(i*336+84,52),crop)
 compare.save(OUT/'HGSS-stairs-comparison.png')
if __name__=='__main__':main()
