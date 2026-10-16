"""Correct the receiving geometry: both stairs rise east; trees occupy ground."""
from pathlib import Path
import argparse,json,sys,subprocess,re
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_refine as native
from johto_common.trees import rgba
from route36.gate_surround.build import decode,over
from claude_cherrygrove import ground
from tiles import Tileset
P=ROOT/'gba/art/johto-common/rocks/r02-elevation';BASE='492da86574614f83e1c9e99c3d5de9686029b8e5'
def dump(p,a):p.write_text(json.dumps(a,indent=2)+'\n')
def save(p,a):Image.fromarray(a).save(p)
def main(game,install):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()==BASE
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=game,text=True).strip()
 for d in ['source','review','evidence']:(P/d).mkdir(parents=True,exist_ok=True)
 t=Tileset(game,'johto_route36','johto_route36');grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);layers,attrs=decode(t,grid);oldgrid=grid.copy();oldattrs=attrs.copy();before=layers[0].copy();over(before,layers[1]);save(P/'review/before-full.png',before)
 cells=np.load(ROOT/'gba/art/johto-common/rocks/r02-context/source/material-grid.npy').copy()
 # Right approach is lower; east landing is raised one row like the left flight.
 cells[21:23,33:35]=ground.PATH;cells[23,33:35]=ground.GRASS
 bg,mat=ground.paint(cells,wobble=True)
 pal=np.array(t.pals[1][6][1:10],int)
 for c in np.unique(bg[:,:,:3].reshape(-1,3),axis=0):bg[np.all(bg[:,:,:3]==c,2),:3]=pal[np.square(pal-c.astype(int)).sum(1).argmin()]
 target=before.copy();work=np.zeros(before.shape[:2],bool)
 placements=json.loads((ROOT/'gba/art/route36/source/features.json').read_text())['trees'];moves={(14,14):(15,14),(32,15):(33,15),(32,17):(33,17),(13,25):(12,25),(31,25):(30,25)}
 tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png');trees=np.zeros_like(target)
 for x,y in placements:
  nx,ny=moves.get((x,y),(x,y));over(trees,tree,nx*16,ny*16)
  if (x,y) in moves:
   for xx,yy in [(x,y),(nx,ny)]:work[yy*16:yy*16+48,xx*16:xx*16+32]=True
 work[256:416,512:528]=True;work[320:400,528:576]=True
 # Ground is rebuilt only under moved objects and the corrected receiving landing.
 target[work]=bg[work]
 rock=np.zeros_like(target);strip=rgba(ROOT/'gba/art/johto-common/rocks/r02-joins/source/wall-and-stairs.png')
 for x,y0 in [(224,80),(512,256)]:
  for y in range(y0,416,16):over(rock,strip[y-288:y-272] if y>=288 else strip[(y-288)%32:(y-288)%32+16],x,y)
 # Both wall planes and flights have the same orientation: higher to the east.
 m=work&(rock[:,:,3]>0);target[m]=rock[m]
 m=work&(trees[:,:,3]>0);target[m]=trees[m]
 # A whole tree is moved, never cropped against the cliff silhouette.
 assert not np.any((trees[:,:,3]>0)&(rock[:,:,3]>0)), 'tree/vertical-rock intersection'
 # The relocated lower trunks remain forest barriers. Remove orphan old trunk
 # blocking only where no replacement canopy/trunk occupies the same cells.
 names=re.findall(r'^\s*(MB_\w+)\s*,',(game/'include/constants/metatile_behaviors.h').read_text(),re.M);mb={n:i for i,n in enumerate(names)}
 for y,n in [(21,'MB_SIDEWAYS_STAIRS_LEFT_SIDE_TOP'),(22,'MB_SIDEWAYS_STAIRS_LEFT_SIDE'),(23,'MB_SIDEWAYS_STAIRS_LEFT_SIDE_BOTTOM')]:attrs[y,32]=(attrs[y,32]&0xff00)|mb[n]
 grid[21,32]&=0xf3ff
 for y in [21,22]:
  for x in [33,34]:grid[y,x]&=0xf3ff;attrs[y,x]&=0xff00
 # Existing tree blocked footprints stay barriers; moved new trunks also block.
 for (x,y),(nx,ny) in moves.items():
  for yy in range(ny+1,ny+3):
   for xx in range(nx,nx+2):grid[yy,xx]=(grid[yy,xx]&0xf3ff)|0xc00
 # Changed visual cells are enough to encode the amended footprint/behaviors.
 ac=work.reshape(32,16,82,16).any((1,3));ac|=(grid!=oldgrid)|(attrs!=oldattrs);affected=ac.repeat(16,0).repeat(16,1)
 palettes=[set(map(tuple,t.pals[i>=6][i][1:])) for i in range(13)]
 for cy,cx in np.argwhere(ac):
  for q in range(4):
   y=cy*16+q//2*8;x=cx*16+q%2*8;sl=np.s_[y:y+8,x:x+8];a=target[sl];colors=set(map(tuple,a[a[:,:,3]>0,:3]));pref=trees[sl][:,:,3]>0
   pairs=[(i,j) for i in range(13) for j in range(13) if colors<=palettes[i]|palettes[j]];assert pairs,(cx,cy,q,colors)
   def cost(pair):return sum(int((np.all(a[:,:,:3]==c,2)&pref).sum())*(c not in palettes[pair[1]])*100+int((np.all(a[:,:,:3]==c,2)&~pref).sum())*(c not in palettes[pair[0]]) for c in colors)
   i,j=min(pairs,key=cost);lo=np.zeros_like(a);hi=np.zeros_like(a)
   for c in colors:
    m=np.all(a[:,:,:3]==c,2)
    if c in palettes[i] and c in palettes[j]:lo[m&~pref]=a[m&~pref];hi[m&pref]=a[m&pref]
    else:(lo if c in palettes[i] else hi)[m]=a[m]
   layers[0][sl]=lo;layers[1][sl]=hi
 save(P/'review/native-target.png',target);save(P/'review/native-full.png',target)
 # Only this dedicated layout uses these banks. Reuse orphan historical metatile
 # IDs, never referenced IDs or the border. Preserve every live map entry elsewhere.
 layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts'];uses=[l for l in layouts if l['primary_tileset']=='gTileset_JohtoRoute36Primary'];assert len(uses)==1
 used=set((oldgrid&1023).ravel())|set(np.fromfile(game/uses[0]['border_filepath'],'<u2')&1023);free=[i for i in range(len(t.blocks[0])) if i not in used]
 changes=[dict(x=int(x),y=int(y),before=int(oldattrs[y,x]),after=int(attrs[y,x])) for y,x in np.argwhere(attrs!=oldattrs)]
 collision=[dict(x=int(x),y=int(y),before=int(oldgrid[y,x]>>10&3),after=int(grid[y,x]>>10&3)) for y,x in np.argwhere((grid&0xc00)!=(oldgrid&0xc00))]
 report=dict(base_engine=BASE,installed=install,runtime_tested=False,tree_wall_overlap_pixels=0,tree_moves=[dict(before=list(a),after=list(b)) for a,b in moves.items()],stairs_rise='east on both flights',attribute_changes=changes,collision_changes=collision,existing_paths_outside_landing_unchanged=True,affected_cells=int(ac.sum()))
 native.P=P
 if install:report.update(native.append_native(game,layers,affected,grid,attrs,reusable_ids=free))
 report['collision_elevation_changes']=len(collision)
 dump(P/'evidence/structure.json',report);np.save(P/'source/material-grid.npy',cells);dump(P/'source/tree-placements.json',[list(moves.get(tuple(p),tuple(p))) for p in placements])
 save(P/'source/installed-west-facing-stair-section.png',strip);save(P/'source/mirrored-east-facing-stair-section.png',strip[:,::-1])
 ref=rgba(native.REF);save(P/'review/original-full.png',ref)
 for name,a in [('original',ref),('before',before),('map',target)]:save(P/'review'/(name+'.png'),a[208:448,176:608])
 sheet=Image.new('RGB',(2640,550),'#202d37');d=ImageDraw.Draw(sheet);font=ImageFont.truetype(native.FONT,20)
 for i,(name,label) in enumerate([('original','HGSS: BOTH CROSSINGS RISE EAST'),('before','PREVIOUS: WRONG EAST FLIGHT / TREES'),('map','CORRECTED: SHARED FLIGHT / CLEAR FACES')]):
  x=i*880+8;d.text((x,10),label,font=font,fill='white');sheet.paste(Image.open(P/'review'/(name+'.png')).resize((864,480),Image.Resampling.NEAREST),(x,42))
 sheet.save(P/'review/comparison.png')
 reviewed=set(map(tuple,np.argwhere(ac)))
 for y,x in list(reviewed):
  for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
   if 0<=yy<32 and 0<=xx<82:reviewed.add((yy,xx))
 dump(P/'evidence/cell-review.json',[dict(x=int(x),y=int(y),changed=bool(ac[y,x]),material='stone/stair' if x in [14,32] else 'tree/landing/ground',review='pending') for y,x in sorted(reviewed)])
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args();main(a.engine,a.install)
