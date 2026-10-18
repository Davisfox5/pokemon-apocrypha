"""Read-only final native comparisons against the preceding approved-face build."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G,B,P=map(Path,sys.argv[1:4]);S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';D=E/'receiving-joins';D.mkdir(exist_ok=True)
def render(game):
 t=Tileset(game,'route33','route33');g=np.fromfile(game/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);im=np.array(t.map_image(g.ravel().tolist(),34));attrs=np.array([t.attrs[int(m>=512)][m%512] for m in g.ravel()&1023]);return t,g,im,attrs
t,g,now,attrs=render(G);bt,bg,before,ba=render(B);r=json.loads((E/'receiving-joins.json').read_text());assert np.array_equal(g&0xfc00,bg&0xfc00);assert np.array_equal(attrs,ba);assert np.array_equal(now,np.array(Image.open(P/'JohtoRoute33.png').convert('RGB')));assert np.array_equal(now,np.array(Image.open(S/'receiving-joins/target.png').convert('RGB')))
allowed=np.zeros((464,544),bool)
for x,y,role in r['corners']:
 allowed[y-8:y+16,x:x+16]=True
for x,y,w,h in [(160,32,24,16),(200,128,16,24),(216,40,16,16),(344,96,16,24),(376,184,24,24),(408,240,16,24),(288,152,40,36),(288,184,56,32),(392,224,32,28),(424,296,64,28)]:allowed[y:y+h,x:x+w]=True
for v in json.loads((E/'terrain-depth.json').read_text())['profiles']:
 if not v['name'].startswith('southeast upper'):allowed[v['face_top']-2:v['face_top'],v['x0']:v['x1']]=True
changed=np.any(now!=before,2);assert not np.any(changed&~allowed)
# Straight shared face pixels outside receiving joins remain immutable.
straight=np.zeros_like(allowed)
for v in json.loads((E/'terrain-depth.json').read_text())['placements']:
 if v['tile'] in ['R02','R04']:straight[v['y']:v['y']+16,v['x']:v['x']+16]=True
stable=straight&~allowed;assert np.array_equal(now[stable],before[stable])
# Moved front interiors retain their complete source body textures unchanged.
for x0,x1,old_y,new_y in [(408,424,232,236),(440,472,304,308)]:assert np.array_equal(now[new_y:new_y+16,x0:x1],before[old_y:old_y+16,x0:x1])
# Inspect original/previous/current in complete receiving context, not isolated tiles.
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);ref=Image.open(S/'hgss-reference.png').convert('RGB')
for name,box in [('entrance',(280,144,344,220)),('north-corners',(144,24,440,192)),('southeast-levels',(344,184,512,368)),('west-front',(144,24,224,192)),('summit-step',(312,80,408,144))]:
 w,h=box[2]-box[0],box[3]-box[1];scale=4 if name=='entrance' else 2;sheet=Image.new('RGB',((w*scale+16)*3,h*scale+40),'#223039');d=ImageDraw.Draw(sheet)
 for i,(title,im) in enumerate([('HGSS',ref),('Previous',Image.fromarray(before)),('Current',Image.fromarray(now))]):
  x=8+i*(w*scale+16);d.text((x,6),title,font=font,fill='white');sheet.paste(im.crop(box).resize((w*scale,h*scale),Image.Resampling.NEAREST),(x,32))
 sheet.save(D/(name+'.png'))
Image.fromarray(now).resize((1088,928),Image.Resampling.NEAREST).save(E/'tree-free-map-2x.png')
sheet=Image.new('RGB',(2208,1000),'#223039');d=ImageDraw.Draw(sheet)
for x,title,im in [(8,'HGSS reference',ref),(1112,'Native receiving joins / tree-free review',Image.fromarray(now))]:d.text((x,10),title,font=font,fill='white');sheet.paste(im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST),(x,46))
sheet.save(E/'tree-free-reference-comparison.png')
# Every affected native square has an auditable old/new block and independent physics.
ledger=[]
for y,x in np.argwhere(changed.reshape(29,16,34,16).any((1,3))):ledger.append(dict(x=int(x),y=int(y),previous_metatile=int(bg[y,x]&1023),current_metatile=int(g[y,x]&1023),collision=int(g[y,x]>>10&3),elevation=int(g[y,x]>>12),attributes=int(attrs[y*34+x])))
(E/'receiving-join-cells.json').write_text(json.dumps(ledger,indent=2)+'\n')
report=dict(baseline_engine='f3022508260da8dbe88277549a39398056a16c9a',native_cells=986,changed_cells=len(ledger),changed_pixels=int(changed.sum()),changes_outside_reviewed_regions=0,unchanged_straight_face_pixels=int(stable.sum()),straight_face_RGB_errors=0,SE_relocated_front_RGB_errors=0,Porymap_RGB_errors=0,collision_changes=0,elevation_changes=0,decoded_attribute_changes=0,warp_files='unchanged',original_levels='Overview-inferred visual terraces; not decoded DS height or collision data',limits=['Trees remain intentionally absent with reserved forest/fruit collision.','SE hidden lower footing is an earlier interpretation; original foliage obscures its source.','Taller receiving elbows use existing native mountain modules; the16px shared catalog does not contain those24px joins.','Sign-obscured approach ground is inferred from adjacent dirt and grass boundaries.'])
(E/'receiving-joins-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
