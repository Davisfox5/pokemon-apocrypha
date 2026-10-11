"""Traced native silhouettes and direct HGSS map texture crops.
Coordinates refer to the preserved HGSS render; no colour-key or rectangular
background erasure touches building exteriors. Outputs retain native palettes.
"""
import numpy as np
from PIL import Image, ImageDraw

def repair_assets(root, assets, pals):
 ref=Image.open(root/'gba/art/johto-v1/references/cherrygrove-hgss.png').convert('RGB')
 def trace(name,box,points,bank):
  rgb=np.array(ref.crop(box));mask=Image.new('1',(rgb.shape[1],rgb.shape[0]));ImageDraw.Draw(mask).polygon(points,fill=1)
  p=np.array(pals[bank][1:],int);ix=(((rgb.astype(int)[...,None,:]-p)**2).sum(-1).argmin(-1)+1).astype(np.uint8)
  ix[~np.array(mask)]=0;assets[name]=ix
 trace('house',(530,110,610,190),[(0,19),(33,8),(68,8),(68,44),(65,44),(65,79),(59,79),(59,77),(33,77),(33,74),(17,74),(17,77),(11,77),(11,79),(4,79),(4,56),(0,56)],6)
 # Keep B's established door anchor by moving the full door two pixels left.
 a=assets['house'];a[56:80,15:33]=a[56:80,18:36].copy();a[56:74,33:36]=a[56:74,36:37]
 assets['house2']=a.copy();assets['house_mirror']=a[:,::-1].copy()
 # Recover the complete eaves and side walls inside the existing footprint.
 trace('gable',(693,132,773,212),[(13,25),(23,20),(23,8),(26,8),(36,14),(39,14),(45,10),(54,10),(79,24),(79,59),(77,59),(77,79),(51,79),(51,77),(31,77),(31,79),(18,79),(18,59),(13,61)],6)
 trace('center',(777,0,873,96),[(15,13),(86,13),(92,18),(93,23),(93,53),(90,59),(89,78),(85,86),(66,86),(66,88),(60,92),(60,95),(38,95),(33,91),(31,86),(14,86),(10,82),(10,59),(8,54),(8,22),(11,16)],8)
 # The entrance opening does not include the green grass below the glass leaf.
 assets['center'][89:96,41:60]=0
 trace('mart',(658,20,738,84),[(8,3),(60,3),(67,7),(67,36),(63,41),(63,58),(59,63),(5,63),(5,58),(3,39),(3,8)],9)
 # The separate sign overlaps the reference roof. Restore its hidden symmetric
 # corner from the left side before placing the sign as its own native asset.
 a=assets['mart'];a[12:37,58:68]=a[12:37,2:12][:,::-1]
 # Whole foreground tree from the HGSS map, including its model-rendered trunk
 # and shadow. The DS leaf texture alone does not contain that model geometry.
 tree_rgb=np.array(ref.crop((624,46,664,94)))
 mask=Image.new('1',(40,48));ImageDraw.Draw(mask).polygon([(18,0),(21,0),(23,3),(25,6),(28,8),(31,10),(33,13),(36,15),(39,18),(39,24),(37,27),(36,31),(33,34),(34,39),(32,43),(27,46),(23,47),(14,47),(9,45),(5,42),(3,38),(3,32),(1,28),(2,25),(0,22),(0,15),(3,12),(5,10),(9,7),(12,5),(14,2)],fill=1)
 rgba=np.dstack([tree_rgb,np.array(mask,dtype=np.uint8)*255])
 source=root/'gba/art/cherrygrove-synthesis/references/HGSS-direct';source.mkdir(exist_ok=True)
 Image.fromarray(rgba).save(source/'tree-cutout.png')
 # Fit the established two-cell width using nearest-neighbour sampling only.
 # Height, source trunk proportions and the original shadow pixels are retained.
 rgba=np.array(Image.fromarray(rgba).resize((32,48),Image.Resampling.NEAREST))
 trunk_colors=[tuple(map(int,tree_rgb[y,x])) for x,y in [(20,38),(20,40),(20,42)]]
 for bank in [3,10]:pals[bank][12:16]=[(64,136,104)]+trunk_colors
 p=np.array(pals[3][1:],int);ix=(((rgba[...,:3].astype(int)[...,None,:]-p)**2).sum(-1).argmin(-1)+1).astype(np.uint8);ix[rgba[...,3]==0]=0
 assets['tree']=ix;assets['blossom']=ix.copy()
 # Preserve the native ground-shadow colour in both foliage variants.
 pals[10][3]=pals[3][3]
 # Explicit editable output for inspection and future manual native tile work.
 dst=root/'gba/art/cherrygrove-synthesis/refined';dst.mkdir(exist_ok=True)
 for name,bank in [('house',6),('house_mirror',6),('house2',7),('gable',6),('center',8),('mart',9),('tree',3),('blossom',10)]:
  im=Image.fromarray(assets[name],mode='P');im.putpalette([v for c in pals[bank] for v in c]+[0]*720);im.info['transparency']=0;im.save(dst/(name+'.png'))

def ground_sources(root,pal):
 ref=Image.open(root/'gba/art/johto-v1/references/cherrygrove-hgss.png').convert('RGB')
 boxes={'grass':(472,116,504,148),'path':(568,52,600,84),'sand':(408,148,424,164)}
 result={};dst=root/'gba/art/cherrygrove-synthesis/references/HGSS-direct'
 for name,box in boxes.items():
  im=ref.crop(box);im.save(dst/(name+'-source.png'));rgb=np.array(im,dtype=int);p=np.array(pal[1:],int)
  result[name]=(((rgb[...,None,:]-p)**2).sum(-1).argmin(-1)+1).astype(np.uint8)
 import json,hashlib
 (dst/'provenance.json').write_text(json.dumps(dict(source='gba/art/johto-v1/references/cherrygrove-hgss.png',sha256=hashlib.sha256((root/'gba/art/johto-v1/references/cherrygrove-hgss.png').read_bytes()).hexdigest(),tree_box=[624,46,664,94],ground_boxes=boxes,adaptation='Tree: outlined alpha matte and horizontal nearest-neighbour fit to 32x48. Ground: source pixels, nearest existing GBA palette, repeated at native scale. Pink foliage uses existing B palette; trunk and shadow colours are shared.'),indent=2)+'\n')
 return result

def terrain(ni,nb,isgrass,ground,water,gx,gy,textures):
 # Source texture pixels only; no authored blades, dots, grit or ripple motifs.
 def pattern(name):
  a=textures[name];return a[gy%a.shape[0],gx%a.shape[1]]
 for mask,name in [(isgrass,'grass'),(ground,'path')]:ni[mask]=pattern(name)[mask]
 beach=ground&(gx<40*16);ni[beach]=pattern('sand')[beach]
 from PIL import ImageFilter
 def dilate(m,size):return np.array(Image.fromarray(m.astype('uint8')*255).filter(ImageFilter.MaxFilter(size)))>0
 pond=water&(gx>=40*16);sea=water&~pond
 # Pond has an earthy bank with a grass lip; no ocean sand or foam on this edge.
 grasslip=isgrass&dilate(beach,5);ni[grasslip]=4

 nearpond=dilate(pond,9)&isgrass;ni[nearpond]=3
 lip=dilate(pond,5)&isgrass;ni[lip]=9
 rim=dilate(pond,3)&isgrass;ni[rim]=8
 # Preserve the existing wet-sand edge and two-pixel foam line on the sea side.
 shore=sea&dilate(beach,5);nb[shore]=0;ni[shore]=10
 wet=beach&dilate(sea,7);ni[wet]=13

 water[shore]=False
 return shore
