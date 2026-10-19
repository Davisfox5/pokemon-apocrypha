"""Convert the reviewed edited atlas into native, palette-indexable masters.

Individual bounds are explicit: the image editor did not preserve atlas cells.
This is an import adapter, not a map generator. Placement remains independent.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import label

ROOT=Path(__file__).resolve().parents[4]
S=ROOT/'gba/art/olivine-city/source'; T=S/'asset-cleanup'
atlas=Image.open(T/'edited-atlas.png').convert('RGBA')
# Generated bounds / native visible bounds. Foot baselines remain registered.
specs={
 'civic-hall':((48,99,303,294),(8,25,119,98)),
 'house':((394,98,560,293),(4,0,74,81)),
 'house-pair':((700,104,857,294),(3,12,73,94)),
 'cafe':((995,98,1189,292),(3,4,74,74)),
 'lighthouse':((52,328,297,699),(5,3,121,181)),
 'terminal':((338,423,687,667),(8,8,166,112)),
 'boat':((747,450,960,643),(3,1,77,71)),
 'umbrella':((1046,507,1183,621),(5,2,56,44)),
 'bench':((84,819,265,884),(7,4,74,24)),
 'bunting':((354,765,719,902),(4,3,146,56)),
 'rail':((792,824,962,884),(0,6,32,21)),
 'land-rock':((1074,807,1175,898),(2,6,30,32)),
 'sea-rock':((116,1065,237,1158),(0,4,32,30)),
 'olivine-tree':((414,994,584,1195),(3,8,46,56)),
}
report=[]
for name,(box,target) in specs.items():
 p=S/'forest-refinement/masters'/f'{name}.png'
 if not p.exists():p=S/'masters'/f'{name}.png'
 old=np.array(Image.open(p).convert('RGBA'));pal=np.unique(old[old[...,3]>0,:3],axis=0)
 # Both residences use a single material ramp. Drop redundant roof shades in
 # favor of legible glazing and a distinct door panel. No shared art is edited.
 if name in ['house','house-pair']:
  pal=np.array([(8,64,40),(16,80,40),(24,112,56),(32,136,64),(64,144,80),
   (32,32,32),(64,56,32),(96,88,72),(144,128,96),(184,168,128),
   (32,80,112),(48,104,152),(120,152,184),(184,200,200),(208,168,64)],np.uint8)
 if name=='cafe':
  pal=np.array([(40,16,16),(56,24,24),(88,24,32),(112,40,40),(128,56,56),
   (64,56,32),(96,88,64),(144,128,96),(192,168,96),(216,200,144),
   (32,40,40),(88,104,104),(144,176,184),(184,200,200),(208,168,64)],np.uint8)
 if name=='terminal':
  pal=np.array([(24,56,120),(32,64,88),(48,128,176),(48,152,208),(88,168,216),(120,192,216),
   (48,48,40),(88,64,64),(112,112,104),(136,136,128),(184,184,168),(216,216,200),
   (144,56,40),(208,104,56),(208,168,64)],np.uint8)
 if name=='lighthouse':
  pal=np.array([(32,40,48),(72,72,72),(112,112,104),(144,144,136),(176,176,160),(216,216,200),
   (0,48,104),(16,72,136),(24,96,168),(48,120,192),(88,152,208),(136,184,208),
   (96,80,56),(16,32,64),(200,216,216)],np.uint8)
 if name=='civic-hall':
  pal=np.array([c for c in pal if tuple(c) not in [(104,104,104),(168,168,168)]],np.uint8)
 x,y,x1,y1=target;src=atlas.crop(box)
 # Alpha threshold is required by GBA 1-bit transparency. BOX integrates
 # coverage without a dark/colored transparent matte leaking into the art.
 a=np.array(src.resize((x1-x,y1-y),Image.Resampling.BOX));mask=a[...,3]>=180
 ids,n=label(mask);counts=np.bincount(ids.ravel());counts[0]=0
 mask &= counts[ids]>=3
 out=np.zeros_like(old);v=a[mask,:3].astype(int)
 # Color mapping is deterministic and preserves whole native silhouettes.
 rgb=pal[np.argmin(((v[:,None]-pal.astype(int))**2).sum(2),1)]
 q=out[y:y1,x:x1];q[mask,:3]=rgb;q[mask,3]=255
 if name=='lighthouse':
  # The HGSS parapet is modular architecture. Rebuild its repeated blue
  # courses in native quadrants instead of importing uneven resampled panels.
  # Corner blocks and the tower silhouette stay independent and complete.
  dark=(16,72,136,255);blue=(24,96,168,255);lit=(48,120,192,255);edge=(88,152,208,255)
  left=np.empty((8,16,4),np.uint8);left[:]=blue
  left[:,0:2]=edge;left[:,14:16]=dark;left[0,2:14]=edge;left[1:7,2:12]=lit;left[7,2:14]=dark
  right=left.copy();right[:,0:2]=dark;right[:,14:16]=edge
  for yy in range(72,128,8):out[yy:yy+8,8:24]=left;out[yy:yy+8,104:120]=right
  front=np.empty((24,8,4),np.uint8);front[:]=blue
  front[0]=edge;front[1:12,1:7]=lit;front[1:12,0]=dark
  front[12:14]=edge;front[14:16]=dark
  front[16:24]=(32,40,48,255);front[16:22,1:6]=blue;front[16:22,1]=lit;front[22,1:6]=dark
  for xx in range(24,104,8):out[128:152,xx:xx+8]=front
  # Equal front windows use the same complete frame, with consistent lighting.
  out[152:176,80:112]=out[152:176,16:48]
  # Continuous recessed door panels, without isolated generated black specks.
  out[106:117,57:71]=(32,40,48,255)
  out[160:176,58:78]=(32,40,48,255);out[160:162,58:78]=(16,32,64,255)
  out[172:176,58:78]=(72,72,72,255)
 Image.fromarray(out).save(T/'masters'/f'{name}.png')
 report.append(dict(name=name,edited_atlas_bounds=box,native_bounds=target,
  native_canvas=[old.shape[1],old.shape[0]],palette=pal.tolist(),
  alpha_threshold=180,origin='Edited atlas, HGSS architectural reference; explicit native registration'))
(T/'asset-import.json').write_text(json.dumps(report,indent=2)+'\n')
