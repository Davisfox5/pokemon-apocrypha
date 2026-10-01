"""Unified B2W2-inspired field atlas from five game Town Map references.
Keeps the source geometry; standardizes terrain color, map symbols and texture.
No overworld collision, route adjacency, warps, or encounters are touched.
"""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
from colorsys import rgb_to_hsv
import json
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'gba/art/pokegear-gen5-atlas';ART.mkdir(parents=True,exist_ok=True)
SRC=ROOT/'gba/art/pokegear-services/references'
OUT=ROOT/'tools/vendor/gba/opening-house-work/graphics/apoc_pokegear'
FILES=['Kanto_Pallet_Town_Map.png','Johto_Cherrygrove_City_Map.png','Hoenn_Littleroot_Town_Map.png','Sinnoh_Sandgem_Town_Map.png','Unova_Floccesy_Town_Map.png']
# Single material/palette system based on the B2W2 color and value hierarchy.
P=[(13,28,39),(22,68,91),(47,128,160),(20,52,43),(37,88,57),
   (77,128,82),(126,149,96),(80,94,99),(160,168,145),
   (219,171,98),(233,206,148),(195,89,77),(70,160,143),
   (218,230,211),(5,13,18),(255,247,225)]
def classify(c,region):
 r,g,b=c;h,s,v=rgb_to_hsv(r/255,g/255,b/255)
 if v<.18:return 0
 if s<.18:
  if v>.78:return 13
  return 7 if v<.55 else 8
 if .49<h<.70 or (b>r*1.15 and b>g*1.04):return 1 if v<.42 else 2
 if .22<h<.50:
  if v<.32:return 3
  return 4 if v<.58 else 5 if v<.77 else 6
 if h>.93 or h<.055:
  if s>.25:return 11 if v>.35 else 7
 if .055<=h<=.22:
  if v<.4:return 7
  if s<.30:return 8
  return 9 if v<.81 else 10
 if .70<h<.95:return 7 if v<.65 else 13
 return 8
def atlas(path,region):
 image=Image.open(path);image.seek(0);frame0=image.convert('RGB');image.seek(min(1,image.n_frames-1));frame1=image.convert('RGB')
 marker=ImageChops.difference(frame0,frame1).getbbox()
 w,h=frame1.size;scale=min(208/w,128/h);nw,nh=round(w*scale),round(h*scale);ox=(208-nw)//2;oy=(128-nh)//2
 scaled=frame1.resize((nw,nh),Image.Resampling.NEAREST)
 dst=Image.new('P',(208,128),0);dst.putpalette(sum((list(x) for x in P),[])+[0]*720)
 pix=dst.load();sp=scaled.load()
 for y in range(nh):
  for x in range(nw):
   material=classify(sp[x,y],region)
   # Structured micro-texture, shared across all five regions. It conveys
   # ground at GBA resolution without changing the source's shape.
   hx=(x*19+y*37+region*11)&15
   if material==1 and hx==0:material=2
   elif material==4 and hx==0:material=5
   elif material==5 and hx==0:material=6
   elif material==9 and hx==0:material=10
   pix[x+ox,y+oy]=material
 # Subtle 16px cartography grid and unified town/route dot language.
 dr=ImageDraw.Draw(dst)
 for x in range(ox+16,ox+nw,16):
  for y in range(oy+16,oy+nh,16):
   if pix[x,y] not in (0,1,2):dr.point((x,y),fill=8)
 cx=round((marker[0]+marker[2])/2*scale)+ox;cy=round((marker[1]+marker[3])/2*scale)+oy
 # The selected location in each reference is replaced by a common node.
 dr.ellipse((cx-4,cy-4,cx+4,cy+4),fill=14,outline=15)
 dr.rectangle((cx-1,cy-1,cx+1,cy+1),fill=11)
 return dst,(cx,cy)
proof=[]
for region,name in enumerate(FILES,1):
 im,pin=atlas(SRC/name,region)
 im.save(ART/f'atlas-{region}.png')
 vals=list(im.getdata());(OUT/f'atlas{region}.bin').write_bytes(bytes(a|(b<<4) for a,b in zip(vals[::2],vals[1::2])))
 (OUT/f'atlas{region}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in P)+'\n')
 proof.append({'region':region,'source':name,'pin':pin,'size':[208,128]})
(ART/'atlas-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
print(proof)
