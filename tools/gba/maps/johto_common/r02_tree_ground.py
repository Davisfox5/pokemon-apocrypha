"""Remove legacy Route 36 tree backing across the complete tree footprint.

Preserve the accepted scene, including gate occlusion, tree placements and walls.
Reconstruct exposed destination terrain only, rather than repainting the map.
"""
from pathlib import Path
import argparse,json,sys,subprocess
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_refine as native
from johto_common.trees import rgba
from route36.gate_surround.build import decode,over
from claude_cherrygrove import ground
from tiles import Tileset
P=ROOT/'gba/art/johto-common/trees/route36-ground-repair'
BASE='e739facc2a5a43c88d7e1dbaecd7f2822a2d59db'
def save(p,a):Image.fromarray(a).save(p)
def dump(p,a):p.write_text(json.dumps(a,indent=2)+'\n')
def main(game,install):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()==BASE
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=game,text=True).strip()
 for d in ('source','review','evidence'):(P/d).mkdir(parents=True,exist_ok=True)
 t=Tileset(game,'johto_route36','johto_route36');grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);layers,attrs=decode(t,grid)
 before=layers[0].copy();over(before,layers[1]);save(P/'review/before-full.png',before)
 prior=ROOT/'gba/art/johto-common/rocks/r02-complete-tiles';placements=json.loads((prior/'source/tree-placements.json').read_text())
 # These seven rear gate trees predate the cliff pass and remain in place.
 placements=sorted(set(map(tuple,placements))|{(x,8) for x in (0,2,4,6)}|{(x,13) for x in (75,77,79)},key=lambda p:(p[1],p[0]))
 tree=rgba(P.parent/'source/T01.png');removed=np.full(tree.shape,255,np.uint8)
 silhouette=np.zeros_like(before);mask=np.zeros_like(before)
 for x,y in placements:over(silhouette,tree,x*16,y*16);over(mask,removed,x*16,y*16)
 # The first pass used the source removal mask, which missed backing baked
 # into neighboring composite tiles. Audit the entire footprint instead.
 # Gate-covered foliage stays occluded. The full old grass backing's palette
 # colors are rebuilt from destination terrain, protecting stone, gates and trunks.
 grass_colors=[(64,136,104),(88,176,136),(96,192,144),(104,200,152),(104,208,152)]
 work=(mask[:,:,3]>0)&(silhouette[:,:,3]==0)&np.any([np.all(before[:,:,:3]==c,2) for c in grass_colors],axis=0)
 for c in json.loads((prior/'source/placements.json').read_text()):
  y,x=c['y']*16,c['x']*16;work[y:y+16,x:x+16]=False
 # Gate shoulders retain their already reviewed local terrain transitions.
 for x,y,w,h in [(0,9,7,7),(75,15,7,7),(55,24,7,8)]:
  sl=np.s_[y*16:(y+h)*16,x*16:(x+w)*16]
  work[sl] &= np.all(before[sl][:,:,:3]==(64,136,104),2)
 cells=np.load(prior/'source/material-grid.npy')
 # Audit uncovered map-edge backing and a shadow left at a former tree origin.
 work |= np.all(before[:,:,:3]==(64,136,104),2)&(cells==ground.GRASS).repeat(16,0).repeat(16,1)
 bg,_=ground.paint(cells,wobble=True)
 pal=np.array(t.pals[1][6][1:10],int)
 for c in np.unique(bg[:,:,:3].reshape(-1,3),axis=0):bg[np.all(bg[:,:,:3]==c,2),:3]=pal[np.square(pal-c.astype(int)).sum(1).argmin()]
 work &= np.any(before!=bg,2)
 target=before.copy();target[work]=bg[work]
 assert not np.any(np.all(target[:,:,:3]==(64,136,104),2)), 'Residual backing in tree gaps'
 ac=work.reshape(32,16,82,16).any((1,3));affected=ac.repeat(16,0).repeat(16,1)
 palettes=[set(map(tuple,t.pals[i>=6][i][1:])) for i in range(13)]
 treecolors=set(map(tuple,tree[tree[:,:,3]>0,:3]))
 for cy,cx in np.argwhere(ac):
  for q in range(4):
   y=cy*16+q//2*8;x=cx*16+q%2*8;sl=np.s_[y:y+8,x:x+8];a=target[sl];colors=set(map(tuple,a[a[:,:,3]>0,:3]));pref=layers[1][sl][:,:,3]>0
   for c in treecolors:pref|=np.all(a[:,:,:3]==c,2)
   pref[work[sl]]=False
   groundcolors=set(map(tuple,a[work[sl],:3]));pairs=[(i,j) for i in range(13) for j in range(13) if colors<=palettes[i]|palettes[j] and groundcolors<=palettes[i]];assert pairs,(cx,cy,q)
   def cost(pair):return sum(int((np.all(a[:,:,:3]==c,2)&pref).sum())*(c not in palettes[pair[1]])*100+int((np.all(a[:,:,:3]==c,2)&~pref).sum())*(c not in palettes[pair[0]]) for c in colors)
   i,j=min(pairs,key=cost);lo=np.zeros_like(a);hi=np.zeros_like(a)
   for c in colors:
    m=np.all(a[:,:,:3]==c,2)
    if c in palettes[i] and c in palettes[j]:lo[m&~pref]=a[m&~pref];hi[m&pref]=a[m&pref]
    else:(lo if c in palettes[i] else hi)[m]=a[m]
   layers[0][sl]=lo;layers[1][sl]=hi
 assert np.array_equal(target[~work],before[~work])
 for c in json.loads((prior/'source/placements.json').read_text()):
  y,x=c['y']*16,c['x']*16;assert np.array_equal(target[y:y+16,x:x+16],before[y:y+16,x:x+16])
 # Native tile-index zero is transparent; no destination shade remains in the
 # upper layer of the reconstructed pixels.
 assert not layers[1][work,3].any()
 layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts'];uses=[l for l in layouts if l['primary_tileset']=='gTileset_JohtoRoute36Primary'];assert len(uses)==1
 used=set((grid&1023).ravel())|set(np.fromfile(game/uses[0]['border_filepath'],'<u2')&1023)
 retained=set((grid[~ac]&1023).ravel())|set(np.fromfile(game/uses[0]['border_filepath'],'<u2')&1023)
 free=[i for i in range(len(t.blocks[0])) if i not in retained];live={0}
 for mid in used:live.update(v&1023 for v in t.blocks[int(mid>=512)][int(mid)%512])
 free_tiles=[i for i in range(512,sum(len(v) for v in t.tiles)) if i not in live]
 save(P/'review/native-full.png',target);save(P/'source/tree-foreground.png',silhouette);save(P/'source/removal-mask.png',np.dstack([work.astype('uint8')*255]*4));dump(P/'source/tree-placements.json',placements)
 report=dict(base_engine=BASE,installed=install,runtime_tested=False,tree_master='T01',existing_tree_origins=len(placements),moved_trees=0,replaced_backing_pixels=int(work.sum()),affected_cells=int(ac.sum()),unchanged_rock_cells=102,collision_changes=[],attribute_changes=[],outside_scope_pixel_changes=0)
 native.P=P
 if install:report.update(native.append_native(game,layers,affected,grid,attrs,reusable_ids=free,reusable_tile_ids=free_tiles))
 dump(P/'evidence/structure.json',report)
 for name,box in [('forest',(512,0,864,512)),('gates',(1152,176,1312,400)),('south',(752,320,1024,512))]:
  sheet=Image.new('RGBA',((box[2]-box[0])*4,(box[3]-box[1])*2))
  for i,a in enumerate((before,target)):sheet.paste(Image.fromarray(a).crop(box).resize(((box[2]-box[0])*2,(box[3]-box[1])*2),Image.Resampling.NEAREST),(i*(box[2]-box[0])*2,0))
  sheet.save(P/'review'/(name+'-comparison.png'))
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args();main(a.engine,a.install)
