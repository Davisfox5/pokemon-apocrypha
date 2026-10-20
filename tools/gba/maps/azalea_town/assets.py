"""Extract only missing Azalea-specific foregrounds from the HGSS reference.
Canonical project masters are copied unchanged; no foliage/ground baked into art.
"""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/azalea-town/source';M=S/'masters';ref=Image.open(S/'hgss-reference.png').convert('RGB');report=[]
def extract(name,box,polys):
 a=np.array(ref.crop(box));mask=Image.new('L',(box[2]-box[0],box[3]-box[1]));d=ImageDraw.Draw(mask)
 for poly in polys:d.polygon([(x-box[0],y-box[1]) for x,y in poly],fill=255)
 m=np.array(mask)>0;r,g,b=a.astype(int).transpose(2,0,1);
 if name!='gym':m&=~((g>r+7)&(g>b+7))
 # Source-overview colors are reduced locally; protect outline/roof/window contrast.
 q=Image.fromarray(a[m].reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pal=np.array(q.getpalette()[:45],np.uint8).reshape(15,3)&248
 out=np.zeros((*m.shape,4),np.uint8);v=a[m].astype(int);out[m,:3]=pal[np.argmin(np.sum((v[:,None,:]-pal.astype(int))**2,2),1)];out[m,3]=255
 Image.fromarray(out).save(M/(name+'.png'));report.append({'name':name,'reference_box':box,'silhouette_polygons':polys,'opaque_pixels':int(m.sum()),'native_RGB5_colors':len(set(map(tuple,out[m,:3]))),'source':'HGSS reference, missing local architecture; grass, flowers, characters and shadows outside silhouette excluded'})
extract('kurt',(120,80,224,176),[[(160,91),(210,111),(210,151),(202,154),(202,172),(139,172),(139,153),(126,150),(126,116)]])
extract('house',(440,248,536,352),[[(456,280),(511,280),(523,287),(523,314),(517,317),(517,340),(456,340),(456,317),(449,312),(449,289)],[(504,259),(515,259),(515,280),(504,280)]])
extract('gym',(192,288,320,384),[[(239,291),(269,291),(305,307),(313,329),(313,352),(305,365),(275,373),(230,373),(206,367),(198,355),(198,320),(207,306)]])
extract('well',(672,176,736,240),[[(697,181),(710,181),(718,187),(720,201),(716,214),(711,218),(711,225),(695,225),(695,216),(688,209),(686,197),(689,187)],[(680,180),(686,180),(686,221),(680,221)],[(722,180),(728,180),(728,221),(722,221)]])
(S/'local-asset-provenance.json').write_text(json.dumps(report,indent=2)+'\n')

# Local house variants share one native ramp; reserve contrast for roof grain,
# walls, windows and the chimney rather than spend two near-identical palettes.
ims=[np.array(Image.open(M/(n+'.png')).convert('RGBA')) for n in ['kurt','house']];pixels=np.concatenate([im[im[...,3]>0,:3] for im in ims]);q=Image.fromarray(pixels.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pal=np.array(q.getpalette()[:45],np.uint8).reshape(15,3)&248
for name,im in zip(['kurt','house'],ims):
 m=im[...,3]>0;v=im[m,:3].astype(int);im[m,:3]=pal[np.argmin(np.sum((v[:,None]-pal.astype(int))**2,2),1)];Image.fromarray(im).save(M/(name+'.png'))
# Missing well art uses the existing gray-marker and wooden-sign shade family.
cs=set()
for n in ['P12','P13','P15']:
 im=np.array(Image.open(M/(n+'.png')).convert('RGBA'));cs|=set(map(tuple,im[im[...,3]>0,:3]&248))
assert len(cs)==15;pal=np.array(sorted(cs),np.uint8);im=np.array(Image.open(M/'well.png').convert('RGBA'));m=im[...,3]>0;v=im[m,:3].astype(int);im[m,:3]=pal[np.argmin(np.sum((v[:,None]-pal.astype(int))**2,2),1)];Image.fromarray(im).save(M/'well.png')
# Keep the small stone chimney gray instead of merging it into straw-roof gold.
im=np.array(Image.open(M/'house.png').convert('RGBA'));raw=np.array(ref.crop((440,248,536,352)));pal=np.array(sorted(set(map(tuple,np.array(Image.open(M/'P13.png').convert('RGBA'))[np.array(Image.open(M/'P13.png').convert('RGBA'))[...,3]>0,:3]&248))),np.uint8)
for y in range(11,32):
 for x in range(64,76):
  if im[y,x,3]:im[y,x,:3]=pal[np.argmin(np.sum((pal.astype(int)-raw[y,x].astype(int))**2,1))]
Image.fromarray(im).save(M/'house.png')
extract('logs',(208,104,240,152),[[(217,114),(225,117),(228,126),(221,132),(212,129),(210,121)],[(216,135),(225,138),(228,146),(218,151),(210,146),(210,141)]])
im=np.array(Image.open(M/'logs.png').convert('RGBA'));k=np.array(Image.open(M/'kurt.png').convert('RGBA'));pal=np.array(sorted(set(map(tuple,k[k[...,3]>0,:3]))),np.uint8);m=im[...,3]>0;v=im[m,:3].astype(int);im[m,:3]=pal[np.argmin(np.sum((v[:,None]-pal.astype(int))**2,2),1)];Image.fromarray(im).save(M/'logs.png')
(S/'local-asset-provenance.json').write_text(json.dumps({'assets':report,'native_cleanup':['Kurt and ordinary house share a15-color local straw/wood ramp.','Well is fitted to exact existing P12/P13/P15 stone/wood shades.','House chimney retains a gray stone ramp.','Gym emblem is opaque green architectural art, not removed as lawn.','Woodpiles use Kurt house shades and contain no forest background.']},indent=2)+'\n')
# Small well-court stone uses its actual original silhouette and the already
# accepted larger native boulder's stone palette; no terrain square as filler.
extract('small-boulder',(664,224,688,248),[[(671,225),(679,226),(684,233),(682,240),(674,243),(668,239),(666,233)]])
im=np.array(Image.open(M/'small-boulder.png').convert('RGBA'));b=np.array(Image.open(M/'boulder.png').convert('RGBA'));pal=np.array(sorted(set(map(tuple,b[b[...,3]>0,:3]))),np.uint8);m=im[...,3]>0;v=im[m,:3].astype(int);im[m,:3]=pal[np.argmin(np.sum((v[:,None]-pal.astype(int))**2,2),1)];Image.fromarray(im).save(M/'small-boulder.png')
# Save the final list after all local foregrounds are authored.
p=S/'local-asset-provenance.json';data=json.loads(p.read_text());data['assets']=report;p.write_text(json.dumps(data,indent=2)+'\n')
