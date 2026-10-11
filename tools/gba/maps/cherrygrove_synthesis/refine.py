"""Hand-traced native silhouettes and repeatable ground motifs.
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
 for name,bank in [('tree',3),('blossom',10)]:
  a=assets[name].copy();a[a==3]=0
  canopy=np.array(Image.fromarray(a[:42]).resize((32,37),Image.Resampling.NEAREST));out=np.zeros((48,32),np.uint8)
  pals[bank][12:16]=[(64,136,104),(80,56,40),(136,96,56),(176,128,72)]
  yy,xx=np.indices((48,32));out[((xx-15.5)/11)**2+((yy-44)/2.5)**2<=1]=12
  out[32:45,12:20]=13;out[33:44,14:18]=14;out[34:43,15:17]=15
  out[44,10:22]=13;out[:37][canopy!=0]=canopy[canopy!=0];assets[name]=out
 # Explicit editable output for inspection and future manual native tile work.
 dst=root/'gba/art/cherrygrove-synthesis/refined';dst.mkdir(exist_ok=True)
 for name,bank in [('house',6),('house_mirror',6),('house2',7),('gable',6),('center',8),('mart',9),('tree',3),('blossom',10)]:
  im=Image.fromarray(assets[name],mode='P');im.putpalette([v for c in pals[bank] for v in c]+[0]*720);im.info['transparency']=0;im.save(dst/(name+'.png'))

def terrain(ni,nb,isgrass,ground,water,gx,gy):
 # A tileable 16px motif: grouped blades and tiny earth flecks, with enough
 # contrast to survive both the GBA palette and native-resolution rendering.
 ni[isgrass]=1
 for x,y in [(2,3),(10,10)]:
  ni[isgrass&(((gx%16==x)&((gy%16==y)|(gy%16==y+1)))|((gx%16==x+1)&(gy%16==y+1)))]=4
  ni[isgrass&(gx%16==x+2)&(gy%16==y)]=14
 ni[isgrass&(gx%16==6)&(gy%16==14)]=2
 ni[ground]=5
 for x,y in [(2,3),(10,11)]:
  ni[ground&((gx%16==x)|(gx%16==x+1))&(gy%16==y)]=6
  ni[ground&(gx%16==x)&(gy%16==y+1)]=7
 beach=ground&(gx<40*16);ni[beach]=11
 # Sand ripples repeat in 16px cells and follow the shoreline without changing
 # water/land collision or the existing coast geometry.
 ni[beach&((gy%16==4)&(gx%16>=3)&(gx%16<=8)|(gy%16==11)&(gx%16>=10)&(gx%16<=14))]=12
 ni[beach&((gy%16==5)&(gx%16>=4)&(gx%16<=8)|(gy%16==12)&(gx%16>=11)&(gx%16<=14))]=10
 from PIL import ImageFilter
 def dilate(m,size):return np.array(Image.fromarray(m.astype('uint8')*255).filter(ImageFilter.MaxFilter(size)))>0
 pond=water&(gx>=40*16);sea=water&~pond
 # Pond has an earthy bank with a grass lip; no ocean sand or foam on this edge.
 grasslip=isgrass&dilate(beach,5);ni[grasslip]=4
 ni[grasslip&((gx+2*gy)%5==0)]=3
 nearpond=dilate(pond,9)&isgrass;ni[nearpond]=3
 lip=dilate(pond,5)&isgrass;ni[lip]=9
 rim=dilate(pond,3)&isgrass;ni[rim]=8
 # Fine irregular wet-sand edge and a two-pixel broken foam line on the sea side.
 shore=sea&dilate(beach,5);nb[shore]=0;ni[shore]=10
 wet=beach&dilate(sea,7);ni[wet]=13
 ni[wet&(((gx+gy)%5)==0)]=12
 water[shore]=False
 return shore
