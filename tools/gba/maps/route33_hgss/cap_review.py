"""Read-only independent native/Porymap review of the cap-only revision."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G,B,P=map(Path,sys.argv[1:4]);S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';D=E/'cap-blend';D.mkdir(exist_ok=True)
def render(game):
 t=Tileset(game,'route33','route33');g=np.fromfile(game/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);im=np.array(t.map_image(g.ravel().tolist(),34));attrs=np.array([t.attrs[int(m>=512)][m%512] for m in g.ravel()&1023]);return t,g,im,attrs
t,g,now,attrs=render(G);bt,bg,before,ba=render(B);lock=np.array(Image.open(S/'cap-blend/approved-face-lock.png'))>0;cap=np.array(Image.open(S/'cap-blend/cap-mask.png'))>0;changed=np.any(now!=before,2)
assert np.array_equal(now[lock],before[lock]);assert not np.any(changed&~cap);assert np.array_equal(g,bg);assert np.array_equal(attrs,ba);assert np.array_equal(now,np.array(Image.open(P/'JohtoRoute33.png').convert('RGB')));assert np.array_equal(now,np.array(Image.open(S/'cap-blend/target.png').convert('RGB')))
# The only source changes are private glyphs, private metatile entries and the
# formerly unused transition palette. Unchanged layout/attributes preserve physics.
files=subprocess.check_output(['git','-C',str(G),'diff','--name-only','74e91ff1','--'],text=True).splitlines();allowed={'data/tilesets/primary/route33/metatiles.bin','data/tilesets/primary/route33/tiles.png','data/tilesets/primary/route33/palettes/04.pal','data/tilesets/secondary/route33/palettes/04.pal'};assert set(files)==allowed,files
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);ref=Image.open(S/'hgss-reference.png').convert('RGB')
for name,box in [('north-joins',(144,24,440,192)),('southeast-joins',(344,184,512,368)),('west-front',(0,0,192,80))]:
 w,h=box[2]-box[0],box[3]-box[1];sheet=Image.new('RGB',((w*2+16)*3,h*2+56),'#202b32');d=ImageDraw.Draw(sheet)
 for i,(title,im) in enumerate([('HGSS reference',ref),('Approved faces / before',Image.fromarray(before)),('Blended tops / current',Image.fromarray(now))]):
  x=8+i*(w*2+16);d.text((x,8),title,font=font,fill='white');sheet.paste(im.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x,40))
 sheet.save(D/(name+'.png'))
Image.fromarray(before).resize((1088,928),Image.Resampling.NEAREST).save(D/'before-map-2x.png');Image.fromarray(np.where(changed[...,None],now,np.array([32,43,50],np.uint8))).resize((1088,928),Image.Resampling.NEAREST).save(D/'changed-pixels.png')
report=dict(baseline_engine=subprocess.check_output(['git','-C',str(B),'rev-parse','HEAD'],text=True).strip(),checked_cells=986,changed_cells=int(changed.reshape(29,16,34,16).any((1,3)).sum()),changed_pixels=int(changed.sum()),approved_face_pixels=int(lock.sum()),approved_face_RGB_errors=0,changes_outside_cap_mask=0,Porymap_RGB_errors=0,native_layout_entries_changed=0,decoded_attribute_changes=0,source_files_changed=files,owner_status='Faces accepted; blended local bevels awaiting visual review. Trees intentionally remain absent; reserved forest barriers retained.')
(E/'cap-blend-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
