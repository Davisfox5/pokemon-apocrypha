"""Conservative manually registered foreground-occlusion ledger, not color guesses."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/route38-39-terrain/source';E=S.parent/'evidence'
# Native cell rectangles. These deliberately include boundary cells: no partly
# covered reference cell is counted as a proved original underlying material.
rects={38:{'forest':[(0,0,68,4),(0,4,10,10),(15,4,32,8),(35,5,47,10),(15,9,20,16),(23,9,27,17),(28,9,31,12),(50,4,68,9),(60,11,68,22),(0,17,7,25),(0,25,68,33),(34,21,68,25)],'buildings':[(63,5,68,11)],'tall_grass_cleared':[(15,8,29,23),(28,9,57,13)],'small_foreground':[(10,18,15,20),(22,9,24,11),(31,13,34,16),(11,4,13,6),(33,4,35,7)]},39:{'forest':[(0,0,38,4),(0,4,8,25),(0,25,6,56),(28,7,38,14),(33,18,38,56),(7,34,11,47),(7,46,15,50),(7,49,22,56),(16,20,20,24)],'buildings':[(8,4,18,10),(7,24,12,30)],'tall_grass_cleared':[(11,33,16,45)],'small_foreground':[(11,20,13,23),(13,16,16,18),(17,18,19,21),(21,17,23,19),(26,18,28,22),(21,36,25,40),(24,41,28,44),(27,11,30,14),(18,9,22,11)]}}
for n,w,h in [(38,68,33),(39,38,56)]:
 layers={}
 for kind,boxes in rects[n].items():
  m=np.zeros((h,w),bool)
  for x,y,xx,yy in boxes:m[y:yy,x:xx]=True
  layers[kind]=m
 records=[]
 for y,x in np.ndindex(h,w):
  covered=[k for k,m in layers.items() if m[y,x]];records.append(dict(x=x,y=y,reference_overlays=covered,ground_evidence='inferred beneath removed foreground' if covered else 'overview context; exposed paths/walls manually traced',original_collision='not extracted',original_height='not extracted'))
 header=json.dumps(dict(coverage_method='conservative manual rectangles; partial cells excluded, small fences/flowers also intentionally removed; this is not a material-match score',rectangles=rects[n]),indent=2)[:-1]
 (S/f'route{n}-reference-coverage.json').write_text(header+',\n"cells":[\n'+',\n'.join(json.dumps(v,separators=(',',':')) for v in records)+'\n]}\n')
 im=Image.open(E/f'route{n}-native.png').convert('RGBA');o=Image.new('RGBA',im.size);d=ImageDraw.Draw(o)
 for rec in records:
  if rec['reference_overlays']:
   x,y=rec['x']*16,rec['y']*16;d.rectangle((x,y,x+15,y+15),fill=(190,90,170,90))
 Image.alpha_composite(im,o).convert('RGB').save(E/f'route{n}-inferred-ground.png')
