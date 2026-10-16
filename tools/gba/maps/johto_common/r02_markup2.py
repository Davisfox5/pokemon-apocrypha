"""Apply owner-marked three-level cliff courses while preserving native stairs."""
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
P=ROOT/'gba/art/johto-common/rocks/r02-markup2';BASE='c5ef879f46dd2cac5b4e9fd62494da752bcd7fb7'
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
 # Continue the receiving dirt beneath the western gate stair apron.
 cells[14:16,6:8]=ground.PATH
 bg,mat=ground.paint(cells,wobble=True)
 pal=np.array(t.pals[1][6][1:10],int)
 for c in np.unique(bg[:,:,:3].reshape(-1,3),axis=0):bg[np.all(bg[:,:,:3]==c,2),:3]=pal[np.square(pal-c.astype(int)).sum(1).argmin()]
 target=before.copy();work=np.zeros(before.shape[:2],bool)
 placements=json.loads((ROOT/'gba/art/johto-common/rocks/r02-contours/source/tree-placements.json').read_text())
 moves=[];removed=[];added=[]
 for x,y in placements:
  dx=dy=0
  if (x,y) in ((28,-1),(30,-1),(30,1)):dx=1
  elif (x,y) in ((33,11),(33,13)):dx=-1
  elif y in (23,25) and 15<=x<=29:dx=1
  elif y in (23,25,27,29) and x>=62:dx=-1
  elif y==22 and x in (38,40,42):dy=1
  # Complete the adjoining southern forest without planting on the new walls.
  elif x in (9,11) and y in (26,28,30):dx=1
  elif y in (27,29) and 13<=x<=29:dx=1
  if x==31 and y in (27,29):
   removed.append([x,y]);moves.append(dict(before=[x,y],after=None,reason='remove tree intersecting red wall extension'));continue
  if dx or dy:
   removed.append([x,y]);added.append([x+dx,y+dy]);moves.append(dict(before=[x,y],after=[x+dx,y+dy]))
 # Continue shifted eastern rows beyond the map edge, keeping the forest sealed.
 added += [[81,y] for y in (23,25,27,29)]
 final=[p for p in placements if p not in removed]+added
 dump(P/'source/tree-moves.json',moves)
 tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png');trees=np.zeros_like(target);footprint=np.zeros((32,82),np.uint8)
 for x,y in sorted(final,key=lambda p:(p[1],p[0])):
  footprint[max(0,y+1):min(32,y+3),x:x+2]+=1
  over(trees,tree,x*16,y*16)
 for x,y in removed+added:work[max(0,y*16):min(512,y*16+48),x*16:x*16+32]=True
 # User markup registered to the 1312x512 native map (photo is 1280x499).
 # Red is two boundaries: 0->1 and 1->2. Green deletes the prior north run.
 work[26*16:,8*16:9*16]=True
 rock=np.zeros_like(target);strip=rgba(ROOT/'gba/art/johto-common/rocks/r02-joins/source/wall-and-stairs.png')
 front=rgba(ROOT/'gba/art/johto-common/rocks/r02-context/source/front.png');corner=rgba(ROOT/'gba/art/johto-common/rocks/r02-context/source/corner-west.png')
 wallcells=set();families={}
 def tile(x,y,art,family):
  work[y*16:y*16+16,x*16:x*16+16]=True;over(rock,art,x*16,y*16);wallcells.add((x,y));families[x,y]=family
 def vertical(x,y0,y1,family,stairs=False):
  for y in range(y0,y1+1):tile(x,y,strip[(y-18)*16:(y-17)*16] if stairs and y>=18 else strip[(y%2)*16:(y%2+1)*16],family)
 def horizontal(y,x0,x1,family):
  for x in range(x0,x1+1):tile(x,y,front[:,(x%2)*16:(x%2+1)*16],family)
 # Lower rise. Its southwest turn encloses higher ground to the south/east.
 horizontal(4,0,13,'lower 0->1 front');tile(14,4,corner,'lower 0->1 outer corner')
 vertical(14,5,24,'lower 0->1 side',True)
 horizontal(25,9,14,'lower 0->1 rear rim')
 vertical(9,26,31,'lower 0->1 relocated side')
 # Use the same native rock ramp for the rear edge; its shading is reversed
 # locally to show raised ground on its southern side.
 for x in range(9,15):
  art=front[:,(x%2)*16:(x%2+1)*16][::-1].copy();tile(x,25,art,'lower 0->1 rear rim')
 tile(9,25,corner,'lower southwest turn')
 work[25*16:26*16,8*16:9*16]=True;inner=strip[16:32].copy();inner[:8,:]=front[::-1,:16][:8];tile(14,25,inner,'lower inner join: rear rim into side')
 # Upper rise stacks directly above/beside the lower rise in the northwest,
 # then turns between the tree rows before stepping east to the right stairs.
 horizontal(3,0,14,'upper 1->2 front');tile(15,3,corner,'upper 1->2 outer corner')
 vertical(15,4,13,'upper 1->2 side')
 horizontal(14,15,30,'upper 1->2 front');tile(31,14,corner,'upper 1->2 outer corner')
 inner=strip[:16].copy();inner[8:,:]=front[8:,16:32];tile(15,14,inner,'upper inner join: side into front')
 vertical(31,15,15,'upper 1->2 side')
 inner=strip[:16].copy();inner[8:,:]=front[8:,16:32];tile(31,16,inner,'upper inner step: side into front');tile(32,16,corner,'upper 1->2 outer step')
 vertical(32,17,25,'upper 1->2 side',True)
 vertical(32,26,31,'upper 1->2 southern extension')
 work[13*16:16*16,6*16:8*16]=True
 target[work]=bg[work]
 m=work&(rock[:,:,3]>0);target[m]=rock[m]
 m=work&(trees[:,:,3]>0);target[m]=trees[m]
 # Preserve the installed western gate over its repaired terrain apron.
 gates=rgba(ROOT/'gba/art/route36/gate-surround/source/gate-layer.png')
 m=work&(gates[:,:,3]>0);m[:,112:]=False;target[m]=before[m]
 assert not np.any((trees[:,:,3]>0)&(rock[:,:,3]>0)), ('tree/vertical-rock intersection',np.argwhere((trees[:,:,3]>0)&(rock[:,:,3]>0))[:8].tolist())
 check=np.zeros_like(footprint,bool)
 for x,y in added:check[max(0,y+1):min(32,y+3),x:x+2]=True
 assert not np.any((footprint>1)&check), ('overlapping footprints',np.argwhere((footprint>1)&check).tolist())
 # Restore grass traversal in the deleted section; preserve the actual map edge.
 for y in range(25,32):grid[y,8]&=0xf3ff
 # Rebuild collision in the changed grove rows from their real trunk footprint.
 for x,y in removed+added:
  for yy in range(max(1,y+1),min(31,y+3)):
   for xx in range(max(0,x),min(82,x+2)):
    if footprint[yy,xx]:grid[yy,xx]=(grid[yy,xx]&0xf3ff)|0xc00
    elif (xx,yy) not in wallcells:grid[yy,xx]&=0xf3ff
 for x,y in wallcells:
  if (x in (14,32) and y in (21,22,23)):continue
  grid[y,x]=(grid[y,x]&0xf3ff)|0xc00;attrs[y,x]&=0xff00
 # Explicit design heights are separate from GBA elevation routing flags.
 heights=np.ones((32,82),np.uint8)
 heights[5:25,:14]=0;heights[26:,:9]=0;heights[:3,:]=2;heights[:14,16:]=2;heights[:16,32:]=2;heights[:,33:]=2
 heights[25,9:15]=1
 np.save(P/'source/terrain-levels.npy',heights)
 dump(P/'source/wall-layout.json',{'lower_boundary':[[0,4],[14,4],[14,25],[9,25],[9,31]],'upper_boundary':[[0,3],[15,3],[15,14],[31,14],[31,16],[32,16],[32,31]],'deleted_green':{'x':8,'y':[25,31]},'yellow_repaired':[[15,14],[31,16],[14,25],[6,13],[6,14]],'levels':[0,1,2],'source':'owner annotated photo; hand-drawn lines snapped to native 16px cells','cells':[dict(x=x,y=y,family=families[x,y]) for x,y in sorted(wallcells)]})
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
 report=dict(base_engine=BASE,installed=install,runtime_tested=False,tree_wall_overlap_pixels=0,overlapping_rebuilt_tree_footprints=0,removed_trees=removed,added_trees=added,terrain_levels=[0,1,2],stairs_rise='0 to 1 west; 1 to 2 east',attribute_changes=changes,collision_changes=collision,affected_cells=int(ac.sum()))
 # Reclaim only secondary tile slots unreferenced by live map/border blocks.
 live_tiles={0}
 for mid in used:
  block=t.blocks[int(mid>=512)][int(mid)%512]
  live_tiles.update(v&1023 for v in block)
 free_tiles=[i for i in range(512,sum(len(v) for v in t.tiles)) if i not in live_tiles]
 native.P=P
 if install:report.update(native.append_native(game,layers,affected,grid,attrs,reusable_ids=free,reusable_tile_ids=free_tiles))
 report['collision_elevation_changes']=len(collision)
 dump(P/'evidence/structure.json',report);np.save(P/'source/material-grid.npy',cells);dump(P/'source/tree-placements.json',final)
 save(P/'source/installed-west-facing-stair-section.png',strip);save(P/'source/mirrored-east-facing-stair-section.png',strip[:,::-1])
 ref=rgba(native.REF);save(P/'review/original-full.png',ref)
 for name,a in [('original',ref),('before',before),('map',target)]:save(P/'review'/(name+'.png'),a[:512,:576])
 sheet=Image.new('RGB',(3480,1080),'#202d37');d=ImageDraw.Draw(sheet);font=ImageFont.truetype(native.FONT,20)
 for i,(name,label) in enumerate([('original','HGSS REFERENCE'),('before','PREVIOUS CONTOURS'),('map','SECOND MARKUP / ONE-TILE TREE SHIFTS')]):
  x=i*1160+8;d.text((x,10),label,font=font,fill='white');sheet.paste(Image.open(P/'review'/(name+'.png')).resize((1152,1024),Image.Resampling.NEAREST),(x,42))
 sheet.save(P/'review/comparison.png')
 reviewed=set(map(tuple,np.argwhere(ac)))
 for y,x in list(reviewed):
  for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
   if 0<=yy<32 and 0<=xx<82:reviewed.add((yy,xx))
 dump(P/'evidence/cell-review.json',[dict(x=int(x),y=int(y),changed=bool(ac[y,x]),material='stone/stair' if x in [14,32] else 'tree/landing/ground',review='pending') for y,x in sorted(reviewed)])
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args();main(a.engine,a.install)
