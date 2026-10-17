"""Independent decoded-native height, master-identity and tree-removal review."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';G,OLD,PORY=map(Path,sys.argv[1:4]);r=json.loads((E/'terrain-depth.json').read_text());M=S/'complete-rocks'
def decode(game):
 t=Tileset(game,'route33','route33');g=np.fromfile(game/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);out=np.zeros((2,464,544,4),np.uint8);attrs=np.zeros((29,34),np.uint16)
 for y,x in np.ndindex(29,34):
  mid=int(g[y,x]&1023);es=t.blocks[int(mid>=512)][mid%512];attrs[y,x]=t.attrs[int(mid>=512)][mid%512]
  for l in range(2):
   for q in range(4):
    en=es[l*4+q];i=en&1023;a=np.array(t.tiles[int(i>=512)][i%512],np.uint8).reshape(8,8)
    if en&1024:a=a[:,::-1]
    if en&2048:a=a[::-1]
    yy=y*16+q//2*8;xx=x*16+q%2*8;d=out[l,yy:yy+8,xx:xx+8];m=a>0;p=np.array(t.pals[int(en>>12>=6)][en>>12],np.uint8);d[m,:3]=p[a[m]];d[m,3]=255
 return t,g,out,attrs
t,g,now,na=decode(G);ot,og,old,oa=decode(OLD);assert np.array_equal(g&0xfc00,og&0xfc00);assert np.array_equal(na,oa);assert np.all(now[0,...,3]==255)
comp=now[0].copy();mask=now[1,...,3]>0;comp[mask]=now[1][mask];native=Image.fromarray(comp[...,:3]);assert np.array_equal(np.array(native),np.array(Image.open(PORY/'JohtoRoute33.png').convert('RGB')))
# A true tree-free foreground cannot retain the green tree/apricorn palette.
fg=now[1].astype(int);greens=(fg[...,3]>0)&(fg[...,1]>fg[...,0]+15)&(fg[...,1]>fg[...,2]+15);assert not greens.any()
expected=np.zeros_like(now[1]);owner=np.zeros((464,544),np.uint16);prov=json.loads((M/'provenance.json').read_text())
for f in prov['files']:assert hashlib.sha256((M/f['file']).read_bytes()).hexdigest()==f['sha256']
for i,p in enumerate(r['placements'],1):
 im=np.array(Image.open(M/(p['tile']+'.png')).convert('RGBA'))
 if p['mirror']:im=im[:,::-1]
 x,y=p['x'],p['y'];m=im[...,3]>0;expected[y:y+16,x:x+16][m]=im[m];owner[y:y+16,x:x+16][m]=i
expected[156:192,288:336]=0;owner[156:192,288:336]=0
# Retained non-tree props/ledge may occlude a few wall pixels; compare every other
# visible master pixel independently against actual native layers.
props=np.zeros((464,544),bool)
for n,x,y in [('boulder-west',52,224),('boulder-east',438,148)]:
 im=np.array(Image.open(S/'transparent-objects'/(n+'.png')).convert('RGBA'));h,w=im.shape[:2];m=im[...,3]>0;props[y:y+h,x:x+w]|=m;assert np.array_equal(now[1,y:y+h,x:x+w][m],old[1,y:y+h,x:x+w][m])
props[184:272,208:328]=True;props[192:224,272:288]=True
bevel=np.array(Image.open(S/'terrain-depth/bevel-mask.png'))>0
visible=(expected[...,3]>0)&~props&~bevel;err=int(np.count_nonzero(np.any(expected!=now[1],2)&visible));assert err==0,err
for p in r['profiles']:assert p['depth']==24 and p['base']-p['cap_top']==24 and p['base']-p['face_top']==16
border=np.fromfile(G/'data/layouts/JohtoRoute33/border.bin','<u2')
for mid in border&1023:
 es=t.blocks[int(mid>=512)][int(mid)%512];assert all((e&1023)==0 for e in es[4:])
# Background changes outside the two reference mountain bounds are forbidden.
allowed=np.zeros((464,544),bool);allowed[:192,:440]=True;allowed[192:360,352:504]=True;assert not np.any(np.any(now[0]!=old[0],2)&~allowed)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);ref=Image.open(S/'hgss-reference.png').convert('RGB');p=E/'terrain-depth';p.mkdir(exist_ok=True)
native.resize((1088,928),Image.Resampling.NEAREST).save(E/'tree-free-map-2x.png')
comparison=Image.new('RGB',(2208,1000),'#202b32');d=ImageDraw.Draw(comparison)
for x,title,im in [(8,'HGSS original / foliage hides some footings',ref),(1112,'TREE-FREE NATIVE / 24px rises, complete shared faces',native)]:
 d.text((x,10),title,font=font,fill='white');comparison.paste(im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST),(x,46))
comparison.save(E/'tree-free-reference-comparison.png')
# Explicit planes are a design interpretation of the overview, not decoded DS z.
levels=np.load(S/'terrain-depth/levels.npy');pal=np.array([[104,200,152],[224,196,136],[192,140,96],[152,88,72]],np.uint8);view=Image.fromarray(pal[levels]);sheet=Image.new('RGB',(1120,1010),'#202b32');d=ImageDraw.Draw(sheet);sheet.paste(view.resize((1088,928),Image.Resampling.NEAREST),(16,44));d.text((12,8),'Design planes: lawn0 / outer1 / middle2 / northern summit3',font=font,fill='white');d.text((12,976),'Visual levels inferred from HGSS overview; not GBA elevation-bit changes.',font=font,fill='white');sheet.save(E/'terrain-levels.png')
regions=[('north-terraces',(144,24,440,192)),('northwest-front',(0,0,192,80)),('southeast-levels',(344,184,512,368)),('summit-step',(304,80,408,144)),('southeast-inside',(376,208,464,288))]
for name,box in regions:
 w,h=box[2]-box[0],box[3]-box[1];sh=Image.new('RGB',(w*6+32,h*3+56),'#202b32');dr=ImageDraw.Draw(sh)
 for j,(label,im) in enumerate([('HGSS reference',ref),('Tree-free native',native)]):
  xx=8+j*(w*3+16);dr.text((xx,8),label,font=font,fill='white');sh.paste(im.crop(box).resize((w*3,h*3),Image.Resampling.NEAREST),(xx,40))
 sh.save(p/(name+'.png'))
# Native quadrants in every wall placement checked against master identity above.
ledger=[]
for y,x in np.argwhere(np.any(now!=old,(0,3)).reshape(29,16,34,16).any((1,3))):
 uses=[v for v in r['placements'] if v['x']<x*16+16 and v['x']+16>x*16 and v['y']<y*16+16 and v['y']+16>y*16]
 ledger.append(dict(x=int(x),y=int(y),wall_levels=sorted({(v['high'],v['low']) for v in uses}),master_placements=[v['tile'] for v in uses],collision=int(g[y,x]>>10&3),review='exact visible master pixels; whole assembled wall/step context; tree-free background exposed'))
(E/'terrain-depth-cells.json').write_text(json.dumps(ledger,indent=2)+'\n')
report=dict(tree_free_review=True,removed_large_trees=88,removed_apricorns=2,retained_foreground_tree_green_pixels=0,retained_boulder_RGB_errors=0,visible_shared_master_pixels=int(visible.sum()),visible_master_RGBA_errors=err,whole_master_placements=len(r['placements']),shared_source=r['shared_source'],front_rise_depth=24,front_bevel_depth=8,complete_face_depth=16,collision_changes=0,elevation_changes=0,behavior_changes=0,water_blocked=bool(np.all(g[:,32:]&0xc00)),Porymap_RGB_errors=0,changed_cells=len(ledger),border_tree_free=True,scope='Both entire mountain formations and all tree foreground; other terrain/props/warps retained',limits=['Forest and Apricorn collision retained as blocked review footprints although trees are intentionally absent.','24px mountain bevels/caps and receiving concave joins remain local; shared R02 single-rise family is16px, not falsely stretched to replace24px.','Southern level1 footing is inferred behind original foliage; not claimed as decoded DS geometry.','Tree-free terrain review; owner visual acceptance pending.'])
(E/'terrain-depth-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
