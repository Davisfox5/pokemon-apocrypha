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
P=ROOT/'gba/art/johto-common/rocks/r02-groves';BASE='6f68aaf57b3c2f117c341d13ba485d9f9ed4e9aa'
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
 placements=json.loads((ROOT/'gba/art/johto-common/rocks/r02-elevation/source/tree-placements.json').read_text())
 # Rebuild complete bands rather than independently shifting individual crowns.
 # Two-cell horizontal pitch and two-cell row pitch match the accepted forest.
 removed=[p for p in placements if (p[1]==14 and 15<=p[0]<=30) or (p[1] in (15,17) and 33<=p[0]<=42) or (p[1]==25 and 11<=p[0]<=31) or (p[1]==11 and 16<=p[0]<=32) or p==[31,1]]
 added=[[x,14] for x in range(15,30,2)]
 added += [[x,y] for y in (15,17) for x in range(34,43,2)]
 added += [[x,25] for x in [11,15,17,19,21,23,25,27,29]]
 # Leave the southern wall cell free of crowns; the next forest row stays intact.
 added += [[x,11] for x in range(15,30,2)] + [[33,11],[30,1]]
 final=[p for p in placements if p not in removed]+added
 tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png');trees=np.zeros_like(target)
 # Review footprint intersections, not just tree/rock pixel intersections.
 footprint=np.zeros((32,82),np.uint8)
 for x,y in sorted(final,key=lambda p:(p[1],p[0])):
  footprint[max(0,y+1):min(32,y+3),x:x+2]+=1
  over(trees,tree,x*16,y*16)
 for x,y in removed+added:work[max(0,y*16):min(512,y*16+48),x*16:x*16+32]=True
 # Owner explicitly requested the right wall continue to the northern map edge.
 work[0:416,512:528]=True
 target[work]=bg[work]
 rock=np.zeros_like(target);strip=rgba(ROOT/'gba/art/johto-common/rocks/r02-joins/source/wall-and-stairs.png')
 for x,y0 in [(224,80),(512,0)]:
  for y in range(y0,416,16):over(rock,strip[y-288:y-272] if y>=288 else strip[(y-288)%32:(y-288)%32+16],x,y)
 m=work&(rock[:,:,3]>0);target[m]=rock[m]
 m=work&(trees[:,:,3]>0);target[m]=trees[m]
 assert not np.any((trees[:,:,3]>0)&(rock[:,:,3]>0)), 'tree/vertical-rock intersection'
 # The reviewed forest has no overlapping 2x2 trunk/ground footprints.
 # Other parts of the map retain their existing layout unchanged.
 check=np.zeros_like(footprint,bool)
 for x,y in added:check[max(0,y+1):min(32,y+3),x:x+2]=True
 assert not np.any((footprint>1)&check), ('overlapping footprints',np.argwhere((footprint>1)&check).tolist())
 # Existing forest barriers remain; new wall cells and new trunk cells block.
 for y in range(0,21):grid[y,32]=(grid[y,32]&0xf3ff)|0xc00
 for x,y in added:
  for yy in range(max(0,y+1),min(32,y+3)):
   for xx in range(x,x+2):grid[yy,xx]=(grid[yy,xx]&0xf3ff)|0xc00
 # Keep a one-cell grass rim beside the realigned grove. It connects the
 # northern clearing to the existing grass/path and eastward stair crossing.
 for y in range(11,18):grid[y,31]&=0xf3ff
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
 report=dict(base_engine=BASE,installed=install,runtime_tested=False,tree_wall_overlap_pixels=0,overlapping_rebuilt_tree_footprints=0,removed_trees=removed,added_trees=added,wall_north_row=0,stairs_rise='east on both flights',attribute_changes=changes,collision_changes=collision,affected_cells=int(ac.sum()))
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
 for name,a in [('original',ref),('before',before),('map',target)]:save(P/'review'/(name+'.png'),a[128:480,160:720])
 sheet=Image.new('RGB',(3408,770),'#202d37');d=ImageDraw.Draw(sheet);font=ImageFont.truetype(native.FONT,20)
 for i,(name,label) in enumerate([('original','HGSS: GROVE BOUNDARIES'),('before','PREVIOUS: COMPRESSED TREE PLACEMENT'),('map','ALIGNED ROWS / CONTINUOUS UPPER WALL')]):
  x=i*1136+8;d.text((x,10),label,font=font,fill='white');sheet.paste(Image.open(P/'review'/(name+'.png')).resize((1120,704),Image.Resampling.NEAREST),(x,42))
 sheet.save(P/'review/comparison.png')
 reviewed=set(map(tuple,np.argwhere(ac)))
 for y,x in list(reviewed):
  for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
   if 0<=yy<32 and 0<=xx<82:reviewed.add((yy,xx))
 dump(P/'evidence/cell-review.json',[dict(x=int(x),y=int(y),changed=bool(ac[y,x]),material='stone/stair' if x in [14,32] else 'tree/landing/ground',review='pending') for y,x in sorted(reviewed)])
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args();main(a.engine,a.install)
