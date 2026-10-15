"""Readable source/material/native comparisons for the terrain-type correction."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/route32-hgss-blocks/source';E=S.parent/'evidence'
ref=Image.open(S/'hgss-reference.png').convert('RGB');native=Image.open(E/'native-map.png').convert('RGB');old=Image.open(E/'previous-5627255/native-map.png').convert('RGB')
colors={'.':'#80b878','P':'#d8c080','G':'#327848','R':'#987050','W':'#6098c0','D':'#a89878','S':'#b8b8b8','_':'#605040','X':'#454b50','?':'#e050e0'}
source=np.array([list(r) for r in (S/'hgss-material-grid.txt').read_text().splitlines()]);actual=np.load(S/'native-visible-materials.npy');source[actual=='X']='X'
def typed(a):
 out=Image.new('RGB',(480,2000));d=ImageDraw.Draw(out)
 for y,row in enumerate(a):
  for x,c in enumerate(row):d.rectangle((x*16,y*16,x*16+15,y*16+15),fill=colors.get(c,'magenta'))
 return out
traced=typed(source);decoded=typed(actual)
for part in range(5):
 out=Image.new('RGB',(2000,490),'#1a2125');d=ImageDraw.Draw(out)
 for j,(im,title,box) in enumerate([(ref,'Original HGSS',(0,part*400,480,(part+1)*400)),(native,'Native reconstruction',(16,part*400+16,496,(part+1)*400+16)),(traced,'HGSS ground-type trace',(0,part*400,480,(part+1)*400)),(decoded,'Actual decoded native types',(0,part*400,480,(part+1)*400))]):
  x=10+j*500;d.text((x,8),title,fill='white');out.paste(im.crop(box),(x,30))
 d.text((10,440),'Rows %d-%d | lawn: light green; tall grass: dark green; dirt: tan; rock: brown; water: blue; dock: gray-brown; stairs: gray; ledge: dark brown'%(part*25,part*25+24),fill='white');d.text((10,462),'Dark gray: foreground/occlusion excluded from ground audit. Source is a visual trace, not extracted DS data.',fill='white');out.save(E/f'material-comparison-{part+1}.png')
out=Image.new('RGB',(1580,2110),'#1a2125');d=ImageDraw.Draw(out)
for x,im,title in [(10,ref,'Original HGSS'),(535,old,'Previous 5627255'),(1060,native,'Terrain-type correction')]:out.paste(im,(x,40));d.text((x,10),title,fill='white')
out.save(E/'material-before-after.png')
regions=[('Grass and dirt boundaries',(240,320,464,576)),('Western two-level rock pillar',(144,688,320,816)),('Railway: dirt underpass and coast',(0,992,480,1136)),('Water, islet and gray boulders',(368,1104,480,1408)),('Center forecourt and forest ground',(144,1504,400,1760)),('Cave forecourt, rock face and ledges',(128,1808,368,1952))]
out=Image.new('RGB',(1060,2020),'#1a2125');d=ImageDraw.Draw(out)
for i,(title,box) in enumerate(regions):
 y=10+i*334;d.text((10,y),title+' | HGSS',fill='white');d.text((540,y),'Native',fill='white')
 for x,im,b in [(10,ref,box),(540,native,tuple(v+16 for v in box))]:
  c=im.crop(b);scale=min(2,500/c.width,300/c.height);out.paste(c.resize((round(c.width*scale),round(c.height*scale)),Image.Resampling.NEAREST),(x,y+23))
out.save(E/'material-details.png')
