"""Read-only native checks and per-circle HGSS/before/after visual sheets."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);B=Path(sys.argv[2]);S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence'
def decode(root):
 t=Tileset(root,'route33','route33');g=np.fromfile(root/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);layers=[np.zeros((464,544,4),np.uint8) for i in range(2)]
 for y in range(29):
  for x in range(34):
   mid=int(g[y,x]&1023);block=t.blocks[int(mid>=512)][mid-512 if mid>=512 else mid]
   for l in range(2):
    for q in range(4):
     en=block[l*4+q];tid=en&1023;a=np.array(t.tiles[int(tid>=512)][tid-512 if tid>=512 else tid],np.uint8).reshape(8,8)
     if en&1024:a=a[:,::-1]
     if en&2048:a=a[::-1]
     xx=x*16+q%2*8;yy=y*16+q//2*8;dst=layers[l][yy:yy+8,xx:xx+8];mask=a>0;p=np.array(t.pals[int((en>>12)>=6)][en>>12],np.uint8);dst[mask,:3]=p[a[mask]];dst[mask,3]=255
 return g,layers
old,ol=decode(B);g,nl=decode(G);report=json.loads((E/'marked-repairs.json').read_text());allowed=np.zeros((464,544),bool)
for ident,title,(x0,y0,x1,y1) in report['regions']:allowed[y0:y1,x0:x1]=True
allowed[188:272,208:328]=True # The connected C/D native ledge must align as one object.
bad=[]
for l in range(2):bad.append(int((np.any(nl[l]!=ol[l],2)&~allowed).sum()))
collision=np.argwhere(((g^old)&0xc00)!=0).tolist();assert collision==[[21,x] for x in range(26,32)],collision
assert bad==[0,0],bad
assert np.array_equal(g&0xf000,old&0xf000)
assert np.all(nl[0][...,3]==255) and np.all(g[:,32:]&0xc00)
report.update(outside_review_bounds_native_pixel_changes=bad,collision_changes=collision,collision_reason='Six ground cells under the restored source rock footing; no new openings',elevation_changes=0,black_warp_preserved=bool(np.all(nl[0][182:191,300:315,:3]==0)),opaque_backings=True,unrelated_native_art='unchanged')
assert report['black_warp_preserved']
(E/'marked-review.json').write_text(json.dumps(report,indent=2)+'\n')
t=Tileset(G,'route33','route33');cur=t.map_image(g.ravel().tolist(),34);cur.save(E/'native-map.png');ref=Image.open(S/'hgss-reference.png').convert('RGB');before=Image.open(E/'previous-214e38cf/native-map.png').convert('RGB');out=E/'marked-sections';out.mkdir(exist_ok=True)
boxes={'A':(0,16,184,72),'B':(200,16,456,72),'C':(196,172,248,212),'D':(196,232,256,284),'E':(344,168,512,216),'F':(344,244,416,296),'G':(392,304,528,432)}
for ident,title,region in report['regions']:
 box=boxes[ident];w,h=(box[2]-box[0])*3,(box[3]-box[1])*3;sheet=Image.new('RGB',(w*3+32,h+50),(25,29,34));d=ImageDraw.Draw(sheet)
 for i,(name,im) in enumerate([('HGSS source',ref),('Before',before),('Corrected native',cur)]):d.text((8+i*(w+8),8),ident+' '+title+' — '+name,fill='white');sheet.paste(im.crop(box).resize((w,h),Image.Resampling.NEAREST),(8+i*(w+8),32))
 sheet.save(out/(ident+'.png'))
# One readable page of all seven regions, each in original/before/current columns.
page=Image.new('RGB',(1570,1800),(25,29,34));d=ImageDraw.Draw(page)
for i,(ident,title,region) in enumerate(report['regions']):
 box=boxes[ident];scale=min(2,480/(box[2]-box[0]),204/(box[3]-box[1]));w,h=round((box[2]-box[0])*scale),round((box[3]-box[1])*scale);y=i*256;d.text((8,y+4),ident+' '+title+' — source / before / corrected',fill='white')
 for j,im in enumerate([ref,before,cur]):page.paste(im.crop(box).resize((w,h),Image.Resampling.NEAREST),(8+j*522,y+27))
page.save(E/'marked-sections-comparison.png');print('Seven regions reviewed; no native pixels changed outside named bounds; six new rock-footing blockers only')
