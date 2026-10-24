# Historical geometry for the guarded first foundation installation only.
# Current native corrections use elevation.py and corner_revision.py.
"""Olivine HGSS relative surfaces and native Emerald directional cliff grammar.

Coordinates trace the 1035x858 overview on a 65x54 native grid. Heights are
interpreted relative levels, NOT extracted DS terrain. Former tree/roof-covered
returns are completed from the visible adjoining courses. No generated concept
is a geometry authority. The coastal footing is below the two upper terraces.
"""
import numpy as np
from PIL import Image, ImageDraw
W,H=65,54
# Polygon edges lie BETWEEN cells. Each course is a nested raised surface,
# never an undirected line. Ocean=-1, city/quay=0, residential=1, lighthouse=2.
REGIONS=[
 dict(name='western woodland terrace',level=1,polygon=[[0,0],[20,0],[20,11],[6,11],[6,29],[0,29]]),
 dict(name='residential terrace and lower lighthouse course',level=1,polygon=[[29,0],[65,0],[65,17],[58,17],[58,21],[56,21],[56,24],[54,24],[54,27],[56,27],[56,36],[54,36],[54,39],[40,39],[40,21],[35,21],[35,25],[33,25],[33,26],[29,26]]),
 dict(name='upper woodland and lighthouse terrace',level=2,polygon=[[31,0],[65,0],[65,15],[55,15],[55,17],[53,17],[53,36],[52,36],[52,37],[42,37],[42,13],[41,13],[41,12],[34,12],[34,11],[31,11]]),
 dict(name='northern high woodland',level=3,polygon=[[33,0],[65,0],[65,6],[33,6]])
]
LAND=[[0,0],[65,0],[65,19],[59,19],[59,22],[57,22],[57,25],[55,25],[55,27],[57,27],[57,36],[55,36],[55,41],[39,41],[39,40],[0,40]]
SURFACES=[
 ['grass',LAND],
 ['sand',[[0,29],[6,29],[6,40],[0,40]]],
 ['sand',[[21,0],[29,0],[29,6],[21,6]]],
 ['paving',[[20,6],[29,6],[29,26],[33,26],[33,25],[35,25],[35,21],[40,21],[40,34],[6,34],[6,11],[20,11]]],
 ['grass',[[9,13],[22,13],[22,16],[12,16],[12,22],[9,22]]],
 ['grass',[[16,22],[27,22],[27,24],[16,24]]],
 ['grass',[[9,28],[21,28],[21,31],[9,31]]],
 ['grass',[[29,28],[34,28],[34,31],[29,31]]],
 ['dock',[[6,34],[40,34],[40,40],[27,40],[27,46],[29,46],[29,52],[27,52],[27,54],[22,54],[22,52],[17,52],[17,46],[22,46],[22,40],[6,40]]]
]
def mask(poly):
 im=Image.new('1',(W*2,H*2));ImageDraw.Draw(im).polygon([(x*2,y*2) for x,y in poly],fill=1)
 return np.array(im)[1::2,1::2]

def build():
 material=np.full((H,W),'water',dtype='<U24');height=np.full((H,W),-1,np.int8)
 for name,poly in SURFACES:
  m=mask(poly);material[m]=name;height[m]=0
 for region in REGIONS:
  m=mask(region['polygon']);assert np.all(height[m]>=region['level']-1),region['name']
  height[m]=region['level'];material[m]='grass'
 # Retain the original western quay rock outcrop as one complete raised block.
 height[34:40,2:6]=1;material[34:40,2:6]='rock outcrop'
 return material,height
# These are original General metatiles. Never flip a complete cliff vertically:
# that would turn a cap into a foot and reverse the perceived elevation.
STRAIGHTS={'W':0x70,'E':0x72,'N':0x69,'S':0x79}
CORNERS={frozenset('NW'):0x68,frozenset('NE'):0x6a,frozenset('SW'):0x78,frozenset('SE'):0x7a}
INSIDE={'NW':0x73,'NE':0x74,'SW':0x76,'SE':0x77}
DIRECTIONS={'N':(0,-1),'E':(1,0),'S':(0,1),'W':(-1,0)}
def cliffs(material,height):
 result={};ledger=[]
 for y,x in np.ndindex(height.shape):
  h=int(height[y,x])
  if h<0 or (h==0 and (x<39 or material[y,x]!='grass')):continue
  def lower(dx,dy):
   xx,yy=x+dx,y+dy
   return 0<=xx<W and 0<=yy<H and height[yy,xx]<h
  edges=[k for k,(dx,dy) in DIRECTIONS.items() if lower(dx,dy)]
  diagonal=[k for k,(dx,dy) in {'NW':(-1,-1),'NE':(1,-1),'SW':(-1,1),'SE':(1,1)}.items() if lower(dx,dy)]
  if len(edges)==1:mid=STRAIGHTS[edges[0]];kind=edges[0]+' face'
  elif len(edges)==2:
   assert frozenset(edges) in CORNERS,(x,y,edges,'thin ridge needs widening')
   mid=CORNERS[frozenset(edges)];kind=''.join(edges)+' convex corner'
  elif not edges and diagonal:
   assert len(diagonal)==1,(x,y,diagonal,'ambiguous inside corner')
   mid=INSIDE[diagonal[0]];kind=diagonal[0]+' concave corner'
  else:
   assert len(edges)<3,(x,y,edges,'unsupported cliff tip')
   continue
  # Use the low-side material only for the donor's transparent exterior pixels.
  lower_material=[str(material[y+dy,x+dx]) for dx,dy in DIRECTIONS.values() if lower(dx,dy)]
  under=next((n for n in ['paving','dock','sand','water','grass'] if n in lower_material),'grass')
  result[x,y]=(mid,under);ledger.append(dict(x=x,y=y,high_level=h,low_sides=edges,orientation=kind,donor_metatile=hex(mid),under=under))
 return result,ledger
