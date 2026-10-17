"""Reusable native rock lips and minimal convex tips; no placement/behavior changes."""
from pathlib import Path
import argparse,json,sys,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_refine as native
from johto_common.trees import rgba
from route36.gate_surround.build import decode,over
from tiles import Tileset
P=ROOT/'gba/art/johto-common/rocks/r02-shared-rims';BASE='3f94e996f228fce092cdc732309636632dc5cae7'
def dump(p,a):p.write_text(json.dumps(a,indent=2)+'\n')
def save(p,a):Image.fromarray(a).save(p)
def main(game,install):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()==BASE
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=game,text=True).strip()
 for d in ['source','source/tiles','review','evidence']:(P/d).mkdir(parents=True,exist_ok=True)
 t=Tileset(game,'johto_route36','johto_route36');grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);layers,attrs=decode(t,grid);oldgrid=grid.copy();oldattrs=attrs.copy();before=layers[0].copy();over(before,layers[1]);save(P/'review/before-full.png',before)
 previous=ROOT/'gba/art/johto-common/rocks/r02-markup2'
 cells=np.load(previous/'source/material-grid.npy');placements=json.loads((previous/'source/tree-placements.json').read_text())
 trees=np.zeros_like(before);tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png')
 for x,y in sorted(placements,key=lambda p:(p[1],p[0])):over(trees,tree,x*16,y*16)
 wall=json.loads((previous/'source/wall-layout.json').read_text());wallcells={(c['x'],c['y']) for c in wall['cells']}
 strip=rgba(ROOT/'gba/art/johto-common/rocks/r02-joins/source/wall-and-stairs.png')
 front=rgba(ROOT/'gba/art/johto-common/rocks/r02-context/source/front.png')
 corner=rgba(ROOT/'gba/art/johto-common/rocks/r02-context/source/corner-west.png')
 # All placements share TWO authored 16px profiles; rotations reuse the same masks.
 profiles=[[1,1,2,2,1,1,1,2,1,1,2,2,1,1,1,1],[1,1,1,2,2,1,1,1,2,1,1,1,2,2,1,1]]
 grass=np.array([104,200,152,255],np.uint8);shade=np.array([88,176,136,255],np.uint8)
 library={};catalog={}
 for k,profile in enumerate(profiles):
  rim=np.zeros((16,16,4),np.uint8)
  for j,depth in enumerate(profile):
   for n in range(depth):rim[j,15-n]=grass if n==0 else shade
  for direction,a in [('right',rim),('top',np.rot90(rim,1).copy()),('left',rim[:,::-1].copy()),('bottom',np.rot90(rim,-1).copy())]:
   name=f'grass-lip-{direction}-{k}';library[name]=a;catalog[name]={'type':'transparent grass-to-rock transition','profile':k,'high_side':direction,'max_width_pixels':2}
 # A radius-two stepped tip removes only THREE pixels of a 16x16 corner.
 clip=np.zeros((16,16),bool);clip[0,15]=clip[0,14]=clip[1,15]=True
 for name,mask in [('NE',clip),('NW',clip[:,::-1]),('SE',clip[::-1]),('SW',clip[::-1,::-1])]:
  save(P/'source/tiles'/('tip-mask-'+name+'.png'),np.where(mask,255,0).astype(np.uint8))
  catalog['tip-mask-'+name]={'type':'outside corner alpha mask','removed_pixels':3,'radius_pixels':2}
 target=before.copy();work=np.zeros(before.shape[:2],bool);placed=[];corners={(15,3):'NE',(31,14):'NE',(32,16):'NE',(9,25):'NW'}
 for c in wall['cells']:
  x,y=c['x'],c['y'];family=c['family'];sl=np.s_[y*16:y*16+16,x*16:x*16+16]
  if x in (14,32) and y in (21,22,23):continue
  orientations=[]
  if 'front' in family and 'join' not in family:orientations=['top']
  elif 'rear rim' in family:orientations=['bottom']
  elif 'side' in family or 'extension' in family:orientations=['right']
  elif (x,y) in corners:orientations=['top','right'] if corners[x,y]=='NE' else ['bottom','right']
  elif 'inner' in family:orientations=['right','bottom'] if (x,y)==(14,25) else ['right','top']
  # Interior stacked seams are rock-to-rock, so never paint grass into them.
  offsets={'right':(1,0),'top':(0,-1),'bottom':(0,1),'left':(-1,0)}
  orientations=[d for d in orientations if (x+offsets[d][0],y+offsets[d][1]) not in wallcells]
  block=before[sl].copy();refs=[]
  for direction in orientations:
   phase=0 if (x,y) in corners else (y if direction in ('left','right') else x)%2;name=f'grass-lip-{direction}-{phase}';rim=library[name]
   m=rim[:,:,3]>0;block[m]=rim[m];refs.append(name)
  if (x,y) in corners:
   direction=corners[x,y];mask=clip if direction=='NE' else clip[:,::-1];block[mask]=grass;refs.append('tip-mask-'+direction)
  if refs:
   target[sl]=block;work[sl]=True;placed.append(dict(x=x,y=y,family=family,modules=refs))
 # Publish actual reusable rock pieces, as well as independent transparent lips.
 for phase in range(2):
  for direction,base in [('west',strip[phase*16:(phase+1)*16].copy()),('south',front[:,phase*16:(phase+1)*16].copy())]:
   rim=library[f'grass-lip-{"right" if direction=="west" else "top"}-{phase}'];over(base,rim);name=f'face-{direction}-{phase}';library[name]=base;catalog[name]={'type':'rock face with reusable grass lip','phase':phase}
  library[f'face-east-{phase}']=library[f'face-west-{phase}'][:,::-1].copy();catalog[f'face-east-{phase}']={'type':'mirrored side reference','source':f'face-west-{phase}'}
  library[f'face-north-{phase}']=library[f'face-south-{phase}'][::-1].copy();catalog[f'face-north-{phase}']={'type':'rear rim reference','source':f'face-south-{phase}'}
 rounded=corner.copy();over(rounded,library['grass-lip-top-0']);over(rounded,library['grass-lip-right-0']);rounded[clip]=0
 library['outside-corner-NW']=rounded[:,::-1].copy();catalog['outside-corner-NW']={'type':'mirrored shared convex corner','source':'outside-corner-NE'}
 library['outside-corner-NE']=rounded;catalog['outside-corner-NE']={'type':'shared convex corner','removed_pixels':3,'source':'r02-context/source/corner-west.png'}
 for name,a in library.items():save(P/'source/tiles'/(name+'.png'),a)
 dump(P/'source/catalog.json',catalog);dump(P/'source/placements.json',placed);dump(P/'source/profiles.json',profiles)
 # No tree silhouettes, stair pixels, inner-corner geometry or map behavior changed.
 assert not np.any(work&(trees[:,:,3]>0))
 assert np.array_equal(target[~work],before[~work])
 # Changed visual cells are enough to encode the amended footprint/behaviors.
 ac=work.reshape(32,16,82,16).any((1,3));affected=ac.repeat(16,0).repeat(16,1)
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
 report=dict(base_engine=BASE,installed=install,runtime_tested=False,tree_wall_overlap_pixels=0,overlapping_rebuilt_tree_footprints=0,terrain_levels=[0,1,2],stairs_rise='0 to 1 west; 1 to 2 east',attribute_changes=changes,collision_changes=collision,affected_cells=int(ac.sum()))
 # Reclaim only secondary tile slots unreferenced by live map/border blocks.
 live_tiles={0}
 for mid in used:
  block=t.blocks[int(mid>=512)][int(mid)%512]
  live_tiles.update(v&1023 for v in block)
 free_tiles=[i for i in range(512,sum(len(v) for v in t.tiles)) if i not in live_tiles]
 native.P=P
 if install:report.update(native.append_native(game,layers,affected,grid,attrs,reusable_ids=free,reusable_tile_ids=free_tiles))
 report['collision_elevation_changes']=len(collision)
 dump(P/'evidence/structure.json',report);np.save(P/'source/material-grid.npy',cells);dump(P/'source/tree-placements.json',placements)
 save(P/'source/installed-west-facing-stair-section.png',strip);save(P/'source/mirrored-east-facing-stair-section.png',strip[:,::-1])

 report.update(shared_edge_profiles=2,convex_tip_pixels_removed=3,modified_corner_count=len(corners),shared_module_placements=len(placed),collision_changes=[],attribute_changes=[],outside_scope_pixel_changes=0)
 dump(P/'evidence/structure.json',report)
 ref=rgba(native.REF);save(P/'review/original-full.png',ref)
 for name,a in [('original',ref),('before',before),('map',target)]:save(P/'review'/(name+'.png'),a[:512,:576])
 sheet=Image.new('RGB',(2320,1080),'#202d37');d=ImageDraw.Draw(sheet);font=ImageFont.truetype(native.FONT,20)
 for i,(name,label) in enumerate([('before','BEFORE'),('map','SHARED RIMS / THREE-PIXEL CORNER TIPS')]):
  xx=i*1160+8;d.text((xx,10),label,font=font,fill='white');sheet.paste(Image.open(P/'review'/(name+'.png')).resize((1152,1024),Image.Resampling.NEAREST),(xx,42))
 sheet.save(P/'review/comparison.png')
 names=list(library);sheet=Image.new('RGB',(800,((len(names)+3)//4)*160),'#202d37');d=ImageDraw.Draw(sheet)
 for i,n in enumerate(names):
  x=i%4*200;y=i//4*160;d.text((x+4,y+4),n,fill='white');a=Image.new('RGBA',(16,16),(65,76,83,255));checker=ImageDraw.Draw(a)
  for cy in range(0,16,4):
   for cx in range(0,16,4):
    if (cx+cy)//4%2:checker.rectangle((cx,cy,cx+3,cy+3),fill=(90,101,108,255))
  a.alpha_composite(Image.fromarray(library[n]));sheet.paste(a.resize((112,112),Image.Resampling.NEAREST),(x+40,y+28))
 sheet.save(P/'review/shared-tiles.png')
 reviewed=set(map(tuple,np.argwhere(ac)))
 for y,x in list(reviewed):
  for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
   if 0<=yy<32 and 0<=xx<82:reviewed.add((yy,xx))
 dump(P/'evidence/cell-review.json',[dict(x=int(x),y=int(y),changed=bool(ac[y,x]),material='rock/grass lip',review='pending') for y,x in sorted(reviewed)])
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args();main(a.engine,a.install)
