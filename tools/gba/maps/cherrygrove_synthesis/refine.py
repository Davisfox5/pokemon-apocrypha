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
 # Center the HGSS facade on the existing warp's eight-pixel centerline.
 # The source's glass center is x50; the native entrance center is x56.
 original=assets['center'];center=np.zeros((96,112),dtype=np.uint8)
 center[:,6:102]=original
 # Fit the glass leaf to one native movement cell, keeping its source pixels
 # and broadening the adjacent casing instead of animating grass beside it.
 leaf=np.array(Image.fromarray(original[79:89,40:60]).resize((16,10),Image.Resampling.NEAREST))
 center[79:89,46:48]=center[79:89,45:46]
 center[79:89,64:66]=center[79:89,66:67]
 center[79:89,48:64]=leaf
 assets['center']=center
 trace('mart',(658,20,738,84),[(8,3),(60,3),(67,7),(67,36),(63,41),(63,58),(59,63),(5,63),(5,58),(3,39),(3,8)],9)
 # The separate sign overlaps the reference roof. Restore its hidden symmetric
 # corner from the left side before placing the sign as its own native asset.
 a=assets['mart'];a[12:37,58:68]=a[12:37,2:12][:,::-1]
 # Whole foreground tree from the HGSS map, including its model-rendered trunk
 # and shadow. The DS leaf texture alone does not contain that model geometry.
 tree_rgb=np.array(ref.crop((624,46,664,94)))
 mask=Image.new('1',(40,48));ImageDraw.Draw(mask).polygon([(18,0),(21,0),(23,3),(25,6),(28,8),(31,10),(33,13),(36,15),(39,18),(39,24),(37,27),(36,31),(33,34),(34,39),(32,43),(27,46),(23,47),(14,47),(9,45),(5,42),(3,38),(3,32),(1,28),(2,25),(0,22),(0,15),(3,12),(5,10),(9,7),(12,5),(14,2)],fill=1)
 # Repair the under-cut right shoulder with the intact left shoulder of this
 # same HGSS tree. Copy only the missing silhouette pixels, never the trunk.
 matte=np.array(mask,dtype=np.uint8)
 for y in range(20):
  for x in range(20,40):
   if matte[y,39-x] and not matte[y,x]:
    matte[y,x]=1;tree_rgb[y,x]=tree_rgb[y,39-x]
 rgba=np.dstack([tree_rgb,matte*255])
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

def ground_sources(root,pal,sea_pal):
 ref=Image.open(root/'gba/art/johto-v1/references/cherrygrove-hgss.png').convert('RGB')
 boxes={'grass':(472,116,504,148),'path':(568,52,600,84),'sand':(408,148,424,164)}
 result={};dst=root/'gba/art/cherrygrove-synthesis/references/HGSS-direct'
 for name,box in boxes.items():
  im=ref.crop(box);im.save(dst/(name+'-source.png'));rgb=np.array(im,dtype=int);p=np.array(pal[1:],int)
  result[name]=(((rgb[...,None,:]-p)**2).sum(-1).argmin(-1)+1).astype(np.uint8)
 # Literal 32px-long HGSS transition strips, aligned per row at the material
 # boundary. Their colours and irregular band widths survive the GBA conversion.
 edge_boxes={'path-edge':(592,52,624,84),'sand-edge':(432,164,480,196),'water-edge':(368,164,400,196)}
 edges={}
 for name,box in edge_boxes.items():
  rgb=np.array(ref.crop(box),dtype=int);Image.fromarray(rgb.astype('uint8')).save(dst/(name+'-source.png'))
  if name=='path-edge':inside=(rgb[...,0]>rgb[...,1])&(rgb[...,0]>150)
  else:inside=(rgb[...,0]>=rgb[...,1]-8)&(rgb[...,0]>180)
  anchors=np.array([np.flatnonzero(row)[0 if name=='water-edge' else -1] for row in inside])
  colors=sea_pal[1:] if name=='water-edge' else pal[1:]
  pp=np.array(colors,int);ids=((rgb[...,None,:]-pp)**2).sum(-1).argmin(-1)
  edges[name]=dict(idx=(ids%15+1).astype('uint8'),bank=np.full(ids.shape,int(name=='water-edge'),dtype='uint8'),anchors=anchors)
 result['_edges']=edges
 rgb=np.array(ref.crop(boxes['sand']),int);pp=np.array(sea_pal[1:],int)
 result['_sand_sea']=(((rgb[...,None,:]-pp)**2).sum(-1).argmin(-1)+1).astype('uint8')
 result['_sand_lookup']=(((np.array(pal,int)[:,None,:]-pp)**2).sum(-1).argmin(-1)+1).astype('uint8')
 import json,hashlib
 (dst/'provenance.json').write_text(json.dumps(dict(source='gba/art/johto-v1/references/cherrygrove-hgss.png',sha256=hashlib.sha256((root/'gba/art/johto-v1/references/cherrygrove-hgss.png').read_bytes()).hexdigest(),tree_box=[624,46,664,94],tree_shoulder_repair='Missing upper-right alpha pixels filled by reflecting source pixels from the same tree left shoulder, rows 0..19; trunk untouched',ground_boxes=boxes,edge_boxes=edge_boxes,center_native_alignment=dict(shift_x=6,canvas=[112,96],glass=[48,79,64,89],warp_center_x=56),transition_sampling='Source rows 0 and 4 supply four-pixel edge repeats; profiles follow rounded 16px paths. Shared 8px edge modules allow at most one-pixel contour correction. Ground interiors remain literal source crops.',adaptation='Tree: outlined alpha matte and horizontal nearest-neighbour fit to 32x48. Ground: source pixels, nearest existing C ground palette and B coastal palette, repeated at native scale. Pink foliage uses existing B palette; trunk and shadow colours are shared.'),indent=2)+'\n')
 return result

def terrain(ni,nb,isgrass,ground,water,gx,gy,textures,dock_path=False):
 from PIL import ImageFilter
 from scipy.ndimage import distance_transform_edt
 safe=isgrass|ground
 # Align path coverage to native movement cells and round their joins.
 # This changes drawn borders only; metatile collision and door cells are fixed.
 h,w=ground.shape
 coarse=np.repeat(np.repeat(ground.reshape(h//16,16,w//16,16).mean(axis=(1,3))>=0.5,16,0),16,1)
 coarse[:, :40*16]=ground[:, :40*16]
 smooth=np.array(Image.fromarray(coarse.astype('uint8')*255).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(2.0)))>=128
 smooth &= safe
 beach=smooth&(gx<40*16);path=smooth&~beach
 def pattern(name):
  a=textures[name];return a[gy%a.shape[0],gx%a.shape[1]]
 ni[safe]=pattern('grass')[safe]
 ni[path]=pattern('path')[path];ni[beach]=pattern('_sand_sea')[beach];nb[beach]=1
 def edge(mask,name,allowed,width=7,reverse=False):
  signed=distance_transform_edt(~mask)-distance_transform_edt(mask)
  normal_y,normal_x=np.gradient(signed)
  phase=(np.where(abs(normal_x)>=abs(normal_y),gy,gx)%8)//4*4
  src=textures['_edges'][name]
  col=src['anchors'][phase]+np.rint(-signed if reverse else signed).astype(int)
  col=np.clip(col,0,src['idx'].shape[1]-1)
  band=(abs(signed)<=width)&allowed
  ni[band]=src['idx'][phase[band],col[band]];nb[band]=src['bank'][phase[band],col[band]]
  return band
 # Rounded soil/grass joins carry the actual HGSS shaded, irregular edge bands.
 edge(path,'path-edge',safe&(gx>=40*16),5)
 edge(beach,'sand-edge',safe&(gx<40*16),3)
 # Shoreline strips include the original foam and wet sand. Leave all distant
 # animated sea pixels and existing harbor props alone.
 sea=water&(gx<40*16)
 nearsea=distance_transform_edt(~sea)<=8
 nearbeach=distance_transform_edt(~beach)<=8
 shore=edge(beach,'water-edge',(sea&nearbeach)|(beach&nearsea),5,True)
 water[shore]=(nb[shore]==1)&np.isin(ni[shore],[1,2,3,4,5,6,9,10])
 sandbank=beach&(nb==0)&(ni>=10)
 ni[sandbank]=textures['_sand_lookup'][ni[sandbank]];nb[sandbank]=1
 # The pond keeps its established shape, with a smoothly measured earth bank.
 pond=water&(gx>=40*16)
 edge(pond,'path-edge',safe&(gx>=40*16),5)
 # The harbor approach is dirt right up to the first wooden plank. This
 # bounded material override changes no land/water or collision geometry.
 if dock_path:
  approach=safe&(gx>=38*16)&(gx<40*16)&(gy>=18*16)&(gy<20*16)
  ni[approach]=pattern('path')[approach];nb[approach]=0
  water[approach]=False
 return shore
