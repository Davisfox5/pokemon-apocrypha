"""Second selected-gate pass: contiguous entrance, complete stairs, clean edges."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import refine_gates as base
ROOT=base.ROOT;PREV=base.OUT;OUT=PREV.parent/'refinement-2';OUT.mkdir(exist_ok=True)

def finish_side():
 old=Image.open(PREV/'G02.png').convert('RGBA');im=old.copy();d=ImageDraw.Draw(im)
 ink=(48,48,56,255);stone=(104,112,104,255);nosing=(184,184,176,255)
 deep=(24,80,64,255);shade=(24,112,104,255);teal=(32,144,136,255)
 face=(48,160,152,255);light=(56,176,176,255);glint=(80,192,192,255)
 wall_edge=(88,72,56,255);wall_light=(216,200,168,255)
 # Back of the building: consistent one-pixel shoulders and clipped corners,
 # removing broken source fringe while preserving the main roof planes.
 d.line((5,12,15,12),fill=wall_edge);d.line((80,12,90,12),fill=wall_edge)
 d.line((4,13,4,27),fill=wall_edge);d.line((91,13,91,27),fill=wall_edge)
 d.line((5,13,15,13),fill=wall_light);d.line((80,13,90,13),fill=wall_light)
 d.point((4,12),fill=(0,0,0,0));d.point((91,12),fill=(0,0,0,0))
 # Smooth only the two upper corners, retaining the original 64px roof span.
 for x,y in [(16,3),(17,3),(16,4),(78,3),(79,3),(79,4)]:d.point((x,y),fill=(0,0,0,0))
 d.line((18,3,77,3),fill=deep);d.line((17,4,17,5),fill=deep);d.line((78,4,78,5),fill=deep)
 # Clear the old overlaid strips in the side assembly; rebuild on an opaque
 # backing, so the porch recess cannot reveal the preview background.
 d.rectangle((92,28,111,96),fill=(0,0,0,0))
 d.polygon([(91,64),(102,64),(111,67),(111,97),(96,95),(91,95)],fill=ink)
 # Recess behind the awning; the narrow teal inner jamb meets the landing.
 d.rectangle((92,74,99,88),fill=ink);d.line((92,75,92,87),fill=shade)
 d.polygon([(93,87),(99,87),(103,90),(103,92),(93,90)],fill=stone)
 # Three complete treads. Vertical risers mean east-west travel; each flight
 # end advances two pixels down the screen, following the HGSS perspective.
 for k,x in enumerate((100,104,108)):
  top=65+k;bottom=89+2*k
  d.rectangle((x,top,x+3,bottom+3),fill=ink)
  d.rectangle((x+1,top+1,x+2,bottom),fill=stone)
  d.line((x+1,top+1,x+1,bottom-1),fill=nosing)
  d.line((x+1,top,x+2,top),fill=stone)
  d.line((x,bottom+1,x+2,bottom+1),fill=stone)
 # Continuous lower return ties the stairs into the existing teal plinth.
 d.polygon([(91,90),(99,90),(103,92),(107,94),(111,96),(111,97),(96,95),(91,95)],fill=ink)
 d.line([(93,90),(99,91),(103,93),(107,95),(110,96)],fill=stone)
 # One coherent rounded canopy contour; no bright slivers outside its rim.
 rim=[(91,28),(94,28),(98,29),(101,31),(103,34),(103,64),(102,68),(100,72),(97,75),(94,76),(91,76)]
 d.polygon(rim,fill=deep)
 d.polygon([(92,30),(95,30),(98,31),(100,33),(101,35),(101,64),(100,68),(98,71),(95,73),(92,74)],fill=teal)
 d.polygon([(92,31),(95,31),(98,32),(99,34),(100,36),(100,63),(99,67),(97,70),(94,72),(92,72)],fill=face)
 d.line([(93,31),(95,31),(98,33),(99,35),(99,63),(98,67),(96,70)],fill=light)
 # Rear-facing edge of the clipped opposite hood follows a single stepped
 # rim; remove the old isolated gray fleck at its lower wall join.
 d.line([(0,29),(2,29),(2,28),(4,28)],fill=deep)
 d.rectangle((0,75,3,87),fill=stone);d.line((0,75,0,87),fill=ink)
 d.line((1,87,3,87),fill=ink)
 a=np.array(im);prior=np.array(old)
 assert np.array_equal(a[7:59,20:76],prior[7:59,20:76]),'Roof interior changed'
 # Check the actual gap locations reported by the owner, not a broad bbox.
 assert (a[77:88,92:100,3]==255).all(),'Open porch hole'
 assert (a[91:95,92:97,3]==255).all(),'Open hole below stairs'
 assert (a[67:74,104:112,3]==255).all(),'Open hole at stair top'
 return old,im

def main():
 old,im=finish_side();front=Image.open(PREV/'G01a.png').convert('RGBA')
 # Reuse only the existing export/board helper; no previous files are changed.
 base.OUT=OUT;base.front=lambda:(front,front);base.side=lambda:(old,im);base.main()
 report=json.loads((OUT/'validation.json').read_text());report['G02']['main_roof_preserved']=False;report['G02']['main_roof_interior_preserved']=True
 report['G02']['closed_gaps']=['porch recess','upper stair joint','underside landing joint'];report['G01a']['identical_to_refinement_1']=True
 (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 # Direct close-up for owner review: whole gate plus the entrance at 6x.
 b=Image.new('RGB',(864,540),(235,238,237));d=ImageDraw.Draw(b)
 font='/System/Library/Fonts/Supplemental/Arial.ttf';f=ImageFont.truetype(font,22);s=ImageFont.truetype(font,16)
 d.text((24,18),'G02 / revised',font=f,fill=(24,36,38));a=im.resize((448,448),Image.Resampling.NEAREST);b.paste(a,(24,58),a)
 d.text((510,18),'Awning and stairs / 6x',font=f,fill=(24,36,38));a=im.crop((88,24,112,104)).resize((144,480),Image.Resampling.NEAREST);b.paste(a,(586,52),a)
 b.save(OUT/'G02-close-up.png')
if __name__=='__main__':main()
