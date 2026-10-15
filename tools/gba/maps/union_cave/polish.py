"""Owner-requested pixel cleanup from the preserved de6922a source, not a layout replay.
Keeps all recorded material/collision masks; coherent native packing is refine.py.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import median_filter
from config import FLOORS
ROOT=Path(__file__).resolve().parents[4]
T=ROOT/'gba/art/union-cave-1f/source/hgss-textures'
for key,c in FLOORS.items():
 S=ROOT/f'gba/art/union-cave-{key}/source';base=S/'previous-de6922a'
 assert base.exists(),'Preserve previous source before corrections'
 a=np.array(Image.open(base/'clean-terrain.png').convert('RGB'));lab=np.load(base/'hgss-pixel-materials.npy');old=a.copy()
 # Remove single-pixel resampling speckle within the SAME material and shade.
 # Choose an existing RGB sample, never blend the wall with adjacent floor/void.
 # A one-pixel highlight on a rock tip or silhouette is retained.
 for material in ['R','O']:
  mask=lab==material;v=a.astype(int);neighbours=[]
  for dy,dx in [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(1,1),(-1,1),(1,-1)]:
   b=np.roll(v,(dy,dx),(0,1));m=np.roll(mask,(dy,dx),(0,1))&mask
   delta=np.abs(b.mean(2)-v.mean(2));neighbours.append(np.where((m&(delta<=32))[...,None],b,v))
  med=np.median(np.stack(neighbours+[v]),0).astype(np.uint8)
  # Native pixel ramps: keep deliberate high-contrast creases, smooth isolated noise.
  change=mask & (np.abs(med.astype(int).mean(2)-v.mean(2))<=20)
  a[change]=med[change]
 # Complete source-silhouette rocks are still layered separately by refine.py.
 # Two beige boulder stacks receive the same bounded interior cleanup.
 for x0,y0,x1,y1 in c['stone_boxes']:
  piece=a[y0:y1,x0:x1];sm=median_filter(piece,size=(3,3,1));d=np.max(np.abs(piece.astype(int)-sm.astype(int)),2)
  piece[d<=24]=sm[d<=24]
 if key=='1f':
  approved=np.array(Image.open(S.parent/'evidence/previous-de6922a/native-map.png').convert('RGB'))
  original_lab=np.load(base/'hgss-pixel-materials.npy')
  # Retain the approved northern light/threshold pixels unchanged.
  a[288:320,432:480]=approved[288:320,432:480]
  # Fit the southern threshold to its LOCAL rock-rim baseline (north +620px,
  # not +624px just because the warp cells are 39 rows apart). Remove the old
  # light, paste only the approved light silhouette, then replace the full rim
  # and its shoulders. Never paste the northern back wall into this open floor.
  sample=np.array(Image.open(base/'clean-terrain.png'))[288:304,96:112]
  for yy in range(900,938):
   for xx in range(440,472):a[yy,xx]=sample[yy%16,xx%16];lab[yy,xx]='.'
  light=approved[280:316,432:480];mask=light.min(2)>144
  a[900:936,432:480][mask]=light[mask]
  # Straight rim shoulders; the northern WEST corner turns south and must
  # not be pasted here (it would leave a hanging pillar under this border).
  for xx in [400,416,480,496]:
   a[932:956,xx:xx+16]=approved[312:336,480:496]
   lab[932:956,xx:xx+16]=original_lab[312:336,480:496]
  a[932:956,432:480]=approved[312:336,432:480]
  lab[932:956,432:480]=original_lab[312:336,432:480]
  # Tail below the replacement rim is void; its curved outer corners join the
  # existing local side wall, rather than leaving a second stacked rim.
  a[956:960,416:512]=0;lab[956:960,416:512]='X'

 Image.fromarray(a).save(S/'clean-terrain.png');np.save(S/'hgss-pixel-materials.npy',lab)
 # HGSS Union Cave d_level01 stone steps. Crop the solid original, reduce to the
 # native 16px warp footprint, preserve discrete treads and darker recessed end.
 step=Image.open(T/'d_level01.png').convert('RGB').resize((16,16),Image.Resampling.BOX)
 p=np.array(step);p=(p.astype(np.uint16)//8*8).astype(np.uint8)
 # The same physical stone staircase appears reversed on ascending endpoints.
 (S/'native-assets').mkdir(exist_ok=True);Image.fromarray(p).save(S/'native-assets/hgss-stone-stairs-down.png');Image.fromarray(p[::-1]).save(S/'native-assets/hgss-stone-stairs-up.png')
 report={'basis':'preserved de6922a source; original HGSS Union Cave stone-step texture d_level01.png','bounded_cleanup':'same-material neighbourhood only; keep silhouette and high-contrast creases; no blended wall/floor/void edges','pixels_cleaned':int(np.any(a!=old,2).sum()),'north_to_south_entrance_copy':{'light_source':[432,280,480,316],'light_destination':[432,900,480,936],'rim_source':[432,312,496,336],'rim_destination':[400,932,512,956],'shoulders':'straight 16px modules; omit northern west corner','baseline_translation_pixels':620,'adaptation':'fit light to southern rim; replace both shoulders and full rim; no stacked border or copied northern back wall'} if key=='1f' else None,'map_layout_collision_or_warp_ids_edited':False,'stairs':'native 16x16 stone treads; no Emerald wooden ladder'}
 (S/'polish.json').write_text(json.dumps(report,indent=2)+'\n')
print('Prepared bounded rock/wall cleanup, copied threshold and HGSS stone steps')
