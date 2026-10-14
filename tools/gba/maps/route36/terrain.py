"""Native Emerald directional cliffs; HGSS palette and measured side stair frame."""
import numpy as np
from PIL import Image
from claude_cherrygrove.pixel import Canvas,Palette
from claude_cherrygrove import banks
from tiles import Tileset

def create(game,pals,materials,source):
 donor=Tileset(game)
 mids={'wall-west':0x73,'wall-east':0x75,'wall-south':0x7c,'corner-sw':0x7b,'corner-se':0x7d}
 # RGB555 equivalents of the owner-approved Emerald/HGSS palette comparison.
 warm={(96,64,80):(104,72,56),(128,88,88):(136,96,72),(152,112,112):(160,120,88),(184,144,136):(184,136,104),(216,176,160):(208,160,112)}
 rasters={}
 for name,mid in mids.items():
  rgb=np.asarray(donor.render(mid)).copy();a=np.dstack((rgb,np.full((16,16),255,np.uint8)))
  a[:,:,3][(rgb[:,:,1].astype(int)>rgb[:,:,0].astype(int)+15)&(rgb[:,:,1].astype(int)>rgb[:,:,2].astype(int)+15)]=0
  # Decoder presents RGB555 expanded to 255; normalize before palette mapping.
  original=(rgb//8)*8
  for old,new in warm.items():a[:,:,:3][np.all(original==old,axis=2)]=new
  rasters[name]=a
 bank=banks.Bank(8,'EMERALD_ROCK_HGSS_EARTH','secondary')
 for name,a in rasters.items():bank.add(name,a)
 # Original 16x48 side-stair opening, precisely outlined to remove adjoining
 # lawn, trees and path. Opposite facing flight is mirrored at native scale.
 rgb=np.asarray(Image.open(source/'hgss-reference.png').convert('RGBA'))[346:394,232:248].copy()
 from PIL import ImageDraw
 mask=Image.new('1',(16,48));d=ImageDraw.Draw(mask);d.polygon([(0,8),(15,0),(15,36),(0,47)],fill=1)
 rgb[:,:,3]=np.asarray(mask,dtype=np.uint8)*255
 # Replace the greenish treads with a neutral native stone tread ladder,
 # keeping HGSS's framed east/west silhouette and correct slope direction.
 for y in range(48):
  for x in range(16):
   r,g,b=map(int,rgb[y,x,:3])
   if rgb[y,x,3] and g>=r and g>b:
    v=(r+g+b)//3
    rgb[y,x,:3]=(104,112,104) if v<100 else (144,152,136) if v<145 else (192,192,168)
 bank.add('stair-west',rgb).add('stair-east',rgb[:,::-1].copy())
 out=bank.build();pals[8]=bank.palette
 for name,c in out.items():Image.fromarray(c.to_rgba()).save(materials/(name+'.png'))
 return out
