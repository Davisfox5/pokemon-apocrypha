"""First-authoring Ecruteak masters. No changes to accepted shared PNGs.

HGSS overview masks are explicit, local architecture only. Hidden terrain is
authored separately. This is reference interpretation, not a DS data extraction.
"""
from pathlib import Path
import json, shutil, hashlib
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[4]
S=ROOT/'gba/art/ecruteak-city/source'; M=S/'masters'
M.mkdir(parents=True,exist_ok=True)
ref=Image.open(S/'hgss-reference.png').convert('RGB')
shared=[]
for name in ['tree','center','mart','gate','grass','P09-native','P12','P13','P15','F01']:
 p=ROOT/'gba/art/azalea-town/source/masters'/f'{name}.png'
 shutil.copyfile(p,M/p.name)
 shared.append(dict(name=name,source=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(S/'shared-provenance.json').write_text(json.dumps(shared,indent=2)+'\n')
report=[]
def extract(name,box,polys,colors=15):
 a=np.array(ref.crop(box));mask=Image.new('L',(box[2]-box[0],box[3]-box[1]));d=ImageDraw.Draw(mask)
 for poly in polys:d.polygon([(x-box[0],y-box[1]) for x,y in poly],fill=255)
 m=np.array(mask)>0
 q=Image.fromarray(a[m].reshape(-1,1,3)).quantize(colors=colors,method=Image.Quantize.MEDIANCUT)
 pal=np.unique(np.array(q.getpalette()[:colors*3],np.uint8).reshape(-1,3)&248,axis=0)
 out=np.zeros((*m.shape,4),np.uint8);v=a[m].astype(int)
 out[m,:3]=pal[np.argmin(np.sum((v[:,None]-pal.astype(int))**2,2),1)];out[m,3]=255
 Image.fromarray(out).save(M/f'{name}.png')
 report.append(dict(name=name,box=box,polygons=polys,colors=len(pal),origin='HGSS Ecruteak overview; explicit silhouette; native RGB5 reduction'))
# Complete silhouettes include eave ends, bases, steps and roof ridges. Tree,
# courtyard and source sign pixels are kept out of the architectural masters.
extract('house',(288,336,384,408),[[(309,342),(321,342),(321,340),(361,340),(361,343),(373,343),(373,380),(369,383),(369,399),(307,399),(307,382),(303,379),(303,350)]])
extract('house-entry',(288,448,384,528),[[(309,454),(321,454),(321,452),(361,452),(361,455),(373,455),(373,492),(369,495),(369,518),(307,518),(307,494),(303,491),(303,462)]])
extract('house-green',(472,568,568,648),[[(481,578),(492,578),(492,575),(534,575),(534,578),(548,578),(553,611),(547,614),(547,638),(480,638),(480,614),(476,610),(476,584)]])
extract('house-southeast',(808,568,904,648),[[(817,578),(828,578),(828,575),(870,575),(870,578),(884,578),(889,611),(883,614),(883,638),(816,638),(816,614),(812,610),(812,584)]])
extract('burned-tower',(288,88,432,216),[[(299,92),(399,92),(402,96),(402,141),(420,145),(423,153),(402,166),(400,173),(400,200),(360,200),(360,207),(336,207),(336,200),(304,200),(304,174),(298,173),(296,164),(296,97)]])
extract('bell-entrance',(480,184,672,280),[[(488,205),(496,205),(496,209),(539,209),(539,191),(549,191),(549,186),(659,186),(659,191),(666,191),(666,199),(661,202),(661,243),(655,247),(655,266),(551,266),(551,261),(490,261),(490,249),(485,247)]])
extract('dance-theater',(624,424,752,536),[[(633,445),(657,434),(674,434),(674,430),(709,430),(709,435),(728,435),(738,444),(739,467),(746,482),(743,496),(735,501),(735,520),(644,520),(644,500),(632,493)]])
extract('gym',(288,544,416,656),[[(329,553),(334,551),(364,552),(369,554),(391,569),(400,589),(401,605),(409,609),(409,624),(399,632),(373,638),(327,638),(304,629),(296,624),(296,607),(300,604),(300,586),(310,567)]])
extract('south-gate',(560,672,640,736),[[(564,679),(632,679),(633,687),(626,690),(626,731),(620,733),(620,710),(575,710),(575,733),(569,731),(569,690),(563,688)]])
# Original side gate's plan is east/west. Both copies share one complete master.
extract('side-gate',(0,352,64,448),[[(0,361),(32,361),(32,363),(45,363),(45,407),(56,412),(56,422),(47,424),(47,442),(39,442),(39,425),(0,425)]])
# Ecruteak's characteristic mossy stone paving; each donor is free of sprites.
extract('paving',(416,416,448,432),[[(416,416),(447,416),(447,431),(416,431)]],7)
extract('court',(456,456,472,472),[[(456,456),(471,456),(471,471),(456,471)]],5)
extract('stone-top',(272,128,288,144),[[(272,128),(287,128),(287,143),(272,143)]],6)
extract('stone-front',(272,232,304,256),[[(272,232),(303,232),(303,255),(272,255)]],8)
extract('water',(680,296,712,312),[[(680,296),(711,296),(711,311),(680,311)]],6)
extract('spring',(720,280,768,328),[[(735,280),(747,280),(754,290),(757,304),(750,313),(739,317),(731,312),(726,302),(726,291)]],12)
extract('fence',(256,264,272,280),[[(257,269),(262,268),(263,282),(257,282)],[(266,268),(271,269),(271,282),(266,282)]],7)
extract('stairs',(336,208,360,256),[[(342,212),(356,212),(356,254),(342,254)]],9)
extract('terrace',(248,120,440,264),[[(264,128),(288,122),(296,122),(296,208),(336,208),(336,256),(264,256)],[(400,122),(414,128),(428,248),(424,256),(360,256),(360,208),(400,208)]],15)
extract('grove-outcrop',(152,240,216,288),[[(168,245),(188,245),(205,253),(210,263),(205,277),(194,278),(188,273),(175,276),(160,273),(156,263)]],12)
extract('pond-boulder',(664,232,696,272),[[(674,237),(682,238),(687,246),(691,255),(690,262),(684,266),(670,265),(666,260),(668,248)]],12)
# Native foliage variants retain the approved complete T01 crown and root mask.
# Only the leaf ramp changes; trunks/outline and every alpha pixel are exact.
tree=np.array(Image.open(M/'tree.png').convert('RGBA'))
for name,ramp in [('tree-amber',[(88,64,32),(128,80,32),(176,112,40),(224,152,56),(248,192,88)]),('tree-autumn',[(80,48,32),(120,56,32),(168,72,32),(208,96,40),(240,128,64)])]:
 im=tree.copy();r,g,b=tree[...,:3].astype(int).transpose(2,0,1);leaf=(g>r)&(g>b)&(tree[...,3]>0)
 cs=sorted(set(map(tuple,tree[leaf,:3])),key=lambda c:sum(map(int,c)))
 for i,c in enumerate(cs):im[np.all(tree[...,:3]==c,2)&leaf,:3]=ramp[round(i*(len(ramp)-1)/max(1,len(cs)-1))]
 Image.fromarray(im).save(M/f'{name}.png')
 report.append(dict(name=name,source='complete shared T01',adaptation='leaf colors only; autumn grove in HGSS reference'))
# Preserve semantic window/door colors rather than letting the large terracotta
# roof dominate an automatic whole-building quantizer. All four native fronts
# share fifteen colors, with separate roof, neutral timber, glazing and door ramps.
hp=np.array([(24,24,24),(48,40,32),(88,72,56),(128,112,96),(184,168,128),(88,24,8),(120,40,16),(152,56,32),(176,80,40),(208,112,64),(72,64,112),(128,120,176),(32,80,64),(48,120,88),(80,160,112)],np.uint8)
boxes={'house':(288,336,384,408),'house-entry':(288,448,384,528),'house-green':(472,568,568,648),'house-southeast':(808,568,904,648)}
for name,box in boxes.items():
 a=np.array(Image.open(M/f'{name}.png').convert('RGBA'));raw=np.array(ref.crop(box));rr,gg,bb=raw.astype(int).transpose(2,0,1)
 for yy,xx in np.argwhere(a[...,3]>0):
  r,g,b=map(int,raw[yy,xx]);candidates=list(range(10))
  if yy>=43 and b>r+6 and b>g+6:candidates=[10,11]
  elif yy>=43 and g>r+8 and g>b+3:candidates=[12,13,14]
  elif yy>=43:candidates=list(range(5))
  p=hp[candidates];a[yy,xx,:3]=p[np.argmin(np.sum((p.astype(int)-raw[yy,xx].astype(int))**2,1))]
 Image.fromarray(a).save(M/f'{name}.png')
report.append(dict(names=list(boxes),adaptation='shared 15-color material-aware ramp, violet glazing and green sliding doors protected; no silhouette smoothing across materials'))
# Small structural materials use their neighboring ramp, preserving their exact
# masks and treads/posts instead of spending another full bank on near browns.
for name,donor in [('fence','house'),('stairs','terrace'),('grove-outcrop','terrace'),('pond-boulder','terrace')]:
 a=np.array(Image.open(M/f'{name}.png').convert('RGBA'));p=np.array(Image.open(M/f'{donor}.png').convert('RGBA'));pal=np.unique(p[p[...,3]>0,:3],axis=0)
 m=a[...,3]>0;v=a[m,:3].astype(int);a[m,:3]=pal[np.argmin(np.sum((v[:,None]-pal.astype(int))**2,2),1)];Image.fromarray(a).save(M/f'{name}.png')
 report.append(dict(name=name,adaptation='native neighboring '+donor+' material ramp; original silhouette and internal geometry preserved'))
(S/'local-asset-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
