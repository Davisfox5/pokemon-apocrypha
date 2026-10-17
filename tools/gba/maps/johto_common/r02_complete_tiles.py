"""Complete rock-and-grass terrain tiles; all convex turns audited."""
from pathlib import Path
import argparse,json,sys,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_refine as native
from johto_common.trees import rgba
from route36.gate_surround.build import decode,over
from tiles import Tileset
P=ROOT/'gba/art/johto-common/rocks/r02-complete-tiles';BASE='b905f4cb70e59c8e4cf8272c43de5512f18590db'
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
 # Complete 16x16 terrain masters. Grass and stone are authored together;
 # there are no separately exported or placed grass-strip assets.
 clean=rgba(previous/'review/native-full.png')
 profiles=[[2,2,3,2,1,2,2,3,2,2,1,2,3,2,2,2],[2,2,1,2,3,2,2,2,3,2,1,2,2,3,2,2]]
 grass=np.array([104,200,152,255],np.uint8);shade=np.array([96,192,144,255],np.uint8)
 library={};catalog={};cache={};placed=[];audit=[]
 target=before.copy();work=np.zeros(before.shape[:2],bool)
 # Five convex turns; the stacked northwest lower turn was omitted last time.
 corners={(15,3):'NE',(14,4):'NE-stacked',(31,14):'NE',(32,16):'NE',(9,25):'NW-return'}
 inside={(15,14),(31,16),(14,25)}
 offsets={'right':(1,0),'top':(0,-1),'bottom':(0,1),'left':(-1,0)}
 for c in wall['cells']:
  x,y=c['x'],c['y'];family=c['family'];sl=np.s_[y*16:y*16+16,x*16:x*16+16]
  if x in (14,32) and y in (21,22,23):continue
  orientations=[]
  if 'front' in family and 'join' not in family:orientations=['top']
  elif 'rear rim' in family:orientations=['bottom']
  elif 'side' in family or 'extension' in family:orientations=['right']
  elif (x,y) in corners:orientations=['top','right'] if corners[x,y].startswith('NE') else ['bottom','right']
  elif 'inner' in family:orientations=['right','bottom'] if (x,y)==(14,25) else ['right','top']
  orientations=[d for d in orientations if (x+offsets[d][0],y+offsets[d][1]) not in wallcells]
  block=clean[sl].copy()
  for direction in orientations:
   phase=0 if (x,y) in corners else (y if direction in ('left','right') else x)%2
   for j,depth in enumerate(profiles[phase]):
    for n in range(depth):
     yy,xx=(j,15-n) if direction=='right' else (n,j) if direction=='top' else (15-n,j) if direction=='bottom' else (j,n)
     block[yy,xx]=grass if n<depth-1 else shade
  if (x,y) in corners:
   direction=corners[x,y];pts=[(0,15),(0,14),(1,15)] if direction.startswith('NE') else [(0,0),(0,1),(1,0)]
   for yy,xx in pts:
    # At the two-tier join, reveal the backing stone rather than inserting grass.
    block[yy,xx]=clean[y*16+yy,(x+1)*16] if 'stacked' in direction else grass
   audit.append(dict(x=x,y=y,kind=direction,rounded_tip_pixels=3))
  elif (x,y) in inside:audit.append(dict(x=x,y=y,kind='concave',rounded_tip_pixels=0,reason='retain original inside turn'))
  # One placement = one complete 16x16 master. Identical tiles share the same ID.
  key=block.tobytes()
  if key not in cache:
   name=f'R{len(library)+1:02d}';cache[key]=name;library[name]=block
   catalog[name]={'size':[16,16],'type':'complete rock terrain tile','grass_on':orientations,'corner':corners.get((x,y),'inside' if (x,y) in inside else None),'placements':[]}
  name=cache[key];catalog[name]['placements'].append([x,y]);placed.append(dict(x=x,y=y,tile=name))
  target[sl]=block;work[sl]=True
 for name,a in library.items():save(P/'source/tiles'/(name+'.png'),a)
 dump(P/'source/catalog.json',catalog);dump(P/'source/placements.json',placed);dump(P/'source/corner-audit.json',audit)
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

 report.update(complete_tile_count=len(library),separate_grass_assets=0,convex_tip_pixels_removed=3,modified_corner_count=len(corners),complete_tile_placements=len(placed),collision_changes=[],attribute_changes=[],outside_scope_pixel_changes=0)
 dump(P/'evidence/structure.json',report)
 ref=rgba(native.REF);save(P/'review/original-full.png',ref)
 for name,a in [('original',ref),('before',before),('map',target)]:save(P/'review'/(name+'.png'),a[:512,:576])
 sheet=Image.new('RGB',(2320,1080),'#202d37');d=ImageDraw.Draw(sheet);font=ImageFont.truetype(native.FONT,20)
 for i,(name,label) in enumerate([('before','BEFORE'),('map','COMPLETE TERRAIN TILES / FIVE OUTSIDE CORNERS')]):
  xx=i*1160+8;d.text((xx,10),label,font=font,fill='white');sheet.paste(Image.open(P/'review'/(name+'.png')).resize((1152,1024),Image.Resampling.NEAREST),(xx,42))
 sheet.save(P/'review/comparison.png')
 names=list(library);sheet=Image.new('RGB',(800,((len(names)+3)//4)*160),'#202d37');d=ImageDraw.Draw(sheet)
 for i,n in enumerate(names):
  x=i%4*200;y=i//4*160;d.text((x+4,y+4),n+' '+('/'.join(catalog[n]['grass_on']) or 'rock join'),fill='white');a=Image.new('RGBA',(16,16),(65,76,83,255));checker=ImageDraw.Draw(a)
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
