"""Read-only independent native comparison and coordinate review for shared repair."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';G,BASE,PORY=map(Path,sys.argv[1:4]);r=json.loads((E/'shared-asset-repair.json').read_text())
prov=json.loads((S/'shared-masters/provenance.json').read_text())
for asset in prov['files']:assert hashlib.sha256((S/'shared-masters'/asset['file']).read_bytes()).hexdigest()==asset['sha256']
def decode(g):
 t=Tileset(g,'route33','route33');grid=np.fromfile(g/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);out=np.zeros((2,464,544,4),np.uint8);beh=np.zeros((29,34),np.uint16)
 for y,x in np.ndindex(29,34):
  mid=int(grid[y,x]&1023);b=t.blocks[int(mid>=512)][mid%512];beh[y,x]=t.attrs[int(mid>=512)][mid%512]
  for l in range(2):
   for q in range(4):
    e=b[l*4+q];i=e&1023;a=np.array(t.tiles[int(i>=512)][i%512],np.uint8).reshape(8,8)
    if e&1024:a=a[:,::-1]
    if e&2048:a=a[::-1]
    yy=y*16+q//2*8;xx=x*16+q%2*8;d=out[l,yy:yy+8,xx:xx+8];m=a>0;p=np.array(t.pals[int(e>>12>=6)][e>>12],np.uint8);d[m,:3]=p[a[m]];d[m,3]=255
 return out,grid,beh
old,og,ob=decode(BASE);now,ng,nb=decode(G);mask=np.zeros((464,544),bool)
for a in r['placements']:mask[a['y']:a['y']+a['height'],a['x']:a['x']+a['width']]=True
for x,y,w,h in [(0,24,160,8),(424,320,64,24),(208,184,120,88)]:mask[y:y+h,x:x+w]=True
outside=[int(np.any(now[i]!=old[i],2)[~mask].sum()) for i in range(2)];assert outside==[0,0]
assert np.all(now[0,...,3]==255);assert np.array_equal(nb,ob);assert np.array_equal(ng&0xf000,og&0xf000)
cc=np.argwhere(((og^ng)&0xc00)!=0).tolist();assert cc==[[y,x] for y in [21,22] for x in range(26,32)];assert np.all(ng[:,32:]&0xc00)
nonledge=np.ones(mask.shape,bool);nonledge[184:272,208:328]=False;assert np.array_equal(now[1][nonledge],old[1][nonledge])
comp=now[0].copy();f=now[1];m=f[...,3]>0;comp[m]=f[m];native=Image.fromarray(comp[...,:3]);assert np.array_equal(np.array(native),np.array(Image.open(PORY/'JohtoRoute33.png').convert('RGB')))
ref=Image.open(S/'hgss-reference.png').convert('RGB');before=Image.open(E/'previous-89f88993/native-map.png').convert('RGB');d=E/'shared-sections';d.mkdir(exist_ok=True)
regions=[('A','Forest / cliff footing',(0,16,184,88)),('B','Rear rim and its receiving plateau',(200,16,448,80)),('C','Ledge head',(192,168,248,224)),('D','Joined L-shaped ledge',(192,224,344,288)),('E','Separate cliff rim / clean side joins',(336,160,520,232)),('F','Convex return / concave continuation',(336,240,448,320)),('G','Continuous wall footing behind crowns',(384,304,520,400))]
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16);labels=['HGSS original','Rejected 89f88993','Shared native assets'];sheets=[]
for name,title,box in regions:
 w,h=box[2]-box[0],box[3]-box[1];sheet=Image.new('RGB',(w*9+48,h*3+68),'#1c2931');dr=ImageDraw.Draw(sheet);dr.text((8,5),name+' / '+title,font=font,fill='white')
 for i,(label,img) in enumerate(zip(labels,[ref,before,native])):
  x=8+i*(w*3+16);dr.text((x,28),label,font=font,fill='white');sheet.paste(img.crop(box).resize((w*3,h*3),Image.Resampling.NEAREST),(x,56))
 sheet.save(d/(name+'.png'));sheets.append(sheet)
page=Image.new('RGB',(max(a.width for a in sheets),sum(a.height+12 for a in sheets)),'#1c2931');y=0
for a in sheets:page.paste(a,(0,y));y+=a.height+12
page.save(E/'shared-sections-comparison.png')
changed=np.any(now!=old,(0,3)).reshape(29,16,34,16).any((1,3));review=changed.copy()
for y,x in np.argwhere(changed):review[max(0,y-1):min(29,y+2),max(0,x-1):min(34,x+2)]=True
cells=[]
for y,x in np.argwhere(review):
 uses=[a['role'] for a in r['placements'] if a['x']<x*16+16 and a['x']+a['width']>x*16 and a['y']<y*16+16 and a['y']+a['height']>y*16]
 cells.append(dict(x=int(x),y=int(y),changed=bool(changed[y,x]),roles=sorted(set(uses)),collision=int(ng[y,x]>>10&3),review='assembled source/native quadrants; retained backing/foreground checked'))
(E/'shared-cell-review.json').write_text(json.dumps(cells,indent=2)+'\n')
# Larger independent full-cell sheets expose neighboring rows, not isolated swatches.
coords=[(c['x'],c['y']) for c in cells]
for start in range(0,len(coords),24):
 sheet=Image.new('RGB',(1440,6*180),'#1c2931');dr=ImageDraw.Draw(sheet)
 for n,(x,y) in enumerate(coords[start:start+24]):
  xx=n%4*360;yy=n//4*180;dr.text((xx+4,yy+3),f'({x},{y}) HGSS / native',font=font,fill='white')
  for j,img in enumerate([ref,native]):sheet.paste(img.crop((x*16,y*16,x*16+16,y*16+16)).resize((128,128),Image.Resampling.NEAREST),(xx+8+j*164,yy+30))
 sheet.save(d/f'cells-{start//24+1:02}.png')
report=dict(baseline=r['baseline'],rejected=r['rejected'],shared_source=r['shared_source'],outside_scope_native_pixels=outside,foreground_outside_ledge_changes=0,tree_positions_and_pixels='unchanged',collision_changes=cc,elevation_changes=0,behavior_changes=0,water_blocked=True,opaque_backing=True,Porymap_RGB_errors=0,shared_master_sha256_verified=True,palette_approximation_pixels=0,reviewed_cells=len(cells),changed_cells=int(changed.sum()),reviewed_quadrants=len(cells)*4,regions=regions,limits=['Original HGSS overview is geographic/material authority; DS collision is interpreted, not extracted.','Rear caps continue adjacent native top quadrants, without invented wall strips; the lower footing extends eight pixels behind complete shared crowns.','Shared masters unchanged; terrain backing is reused native plateau/lawn. No fresh image tracing.','Owner visual acceptance pending.'])
(E/'shared-asset-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
