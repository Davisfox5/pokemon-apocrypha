#!/usr/bin/env python3
"""Author Route 29 from an independent HGSS survey, with explicit adapters."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE))
from tiles import Tileset,palette
from claude_cherrygrove.pixel import Palette
from claude_cherrygrove import build as native,ground
from claude_routes import build as packing,seams
import assets,ground_native,layers,forest
ROOT=HERE.parents[3];OUT=ROOT/'gba/art/route29-hgss-blocks';S=OUT/'source';E=OUT/'evidence';W,H=98,48

def assemble(game):
 base=S/'baseline'
 if not base.exists():
  for folder in ['data/tilesets/primary/cherrygrove','data/tilesets/secondary/claude_route29','data/tilesets/secondary/cherrygrove','data/tilesets/secondary/new_bark','data/layouts/CherrygroveRoute29Approach']:
   shutil.copytree(game/folder,base/folder)
 old=np.fromfile(base/'data/layouts/CherrygroveRoute29Approach/map.bin','<u2').reshape(H,W);oldsolid=(old&0xc00)!=0;t=Tileset(base,'claude_route29','cherrygrove')
 p=np.full((H,W),'T',dtype='<U1');rows=(S/'blocks.txt').read_text().splitlines();p[2:36]=np.array([list(row) for row in rows]);f=json.loads((S/'structures.json').read_text())
 # Restore the HGSS gate proportions and original woodland opening.
 f['gate']['reference_native_box']=[50,5,5,7]
 f['gate'].update(x=49,y=4,width=6,height=8)
 f['gate_flank_trees']=[(x,y) for x in (47,55) for y in (2,4,6,8)]
 f['fixed_trees']=json.loads((S/'gate-tree-baseline.json').read_text())['trees']
 p[p=='H']='.'
 p[4:12,49:55]='H'
 f['signs'][0]['reference_at']=f['signs'][0]['at'];f['signs'][0]['at']=[12,17];p[17,12]='!'
 protected=np.zeros(p.shape,bool);protected[:,:10]=True;protected[:,88:]=True;protected[29:]=True
 protected[25:29,54:64]=True
 reserve=set(int(v&1023) for v in old[protected] if v&1023>=512);visible_primary=set(int(v&1023) for v in old[protected] if v&1023<512)
 pals={i:Palette(i,palette(base/f'data/tilesets/{"primary/cherrygrove" if i<6 else "secondary/claude_route29"}/palettes/{i:02}.pal')[1:],[f'c{j}' for j in range(15)]) for i in range(16)}
 reserved_banks={en>>12 for mid in reserve for en in t.blocks[1][mid-512] if en}|{en>>12 for mid in visible_primary for en in t.blocks[0][mid] if en};assert not reserved_banks&{6,7,8,12},reserved_banks
 pals[6]=Palette(6,palette(base/'data/tilesets/secondary/cherrygrove/palettes/06.pal')[1:],[f'cg{j}' for j in range(15)])
 f['walk_cells']=[(x,26) for x in range(29,86)]+[(29,y) for y in range(21,27)]+[(20,y) for y in range(14,23)]+[(21,14)]+[(57,y) for y in range(22,27)]+[(x,22) for x in range(53,58)]+[(53,y) for y in range(12,23)]+[(52,12)]
 f['walk_cells'] += [(x,17) for x in range(53,65)]+[(64,y) for y in range(12,18)]+[(x,12) for x in range(64,73)]+[(72,y) for y in range(12,23)]+[(x,20) for x in range(70,73)]
 p,positions,forest_report=forest.arrange(p,protected,f);cells=np.full((H,W),ground.GRASS,np.int8);cells[p=='P']=ground.PATH;solid=np.isin(p,list('TR#H!AW_'));solid[protected]=oldsolid[protected];beh=np.zeros(p.shape,np.uint8)
 # Forest-edge lawns can reveal extra town cells. Reserve their original
 # metatile identities as well as the crossing cache glyphs.
 route_reach=seams.reachable(solid,(0,18))
 for name,sec,w,h,ox,oy in [('CherrygroveCity','cherrygrove',80,48,-80,0),('NewBarkTown','new_bark',36,50,98,6)]:
  ng,ns=seams.read_layout(game,name,w,h)
  visible=seams.visible_across(route_reach,ns.shape,ox,oy)
  neighbor=Tileset(game,sec,'cherrygrove')
  for mid in np.unique(ng[visible]):
   mid=int(mid)
   assert t.blocks[int(mid>=512)][mid-512 if mid>=512 else mid]==neighbor.blocks[int(mid>=512)][mid-512 if mid>=512 else mid],('Baseline neighbor metatile differs',name,mid)
   (reserve if mid>=512 else visible_primary).add(mid)
 reserved_banks|={en>>12 for mid in reserve for en in t.blocks[1][mid-512] if en}
 assert not reserved_banks&{6,7,8,12},reserved_banks
 a=assets.create(pals,Tileset(game,'cherrygrove','cherrygrove'),game);mc=native.MapCanvas(W,H);fore=native.MapCanvas(W,H)
 def put(c,x,y):mc.blit(c,x*16,y*16)
 def put_fore(c,x,y):put(c,x,y);fore.blit(c,x*16,y*16)
 def neighbors(ch,x,y):return ''.join(str(int(0<=xx<W and 0<=yy<H and p[yy,xx]==ch)) for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)])
 for y in range(H):
  for x in range(W):
   if protected[y,x]:continue
   ch=p[y,x]
   if ch=='G':put(a['grass-'+neighbors('G',x,y)],x,y);beh[y,x]=2
   elif ch in ['#','R']:put(a['cliff-west-0' if ch=='#' else 'cliff-cap-0'],x,y)
   elif ch=='_':
    kind='left' if x==0 or p[y,x-1]!='_' else 'right' if x+1==W or p[y,x+1]!='_' else 'middle';put(a['ledge-'+kind],x,y);beh[y,x]=59
 for x,y,w,h in f['flower_boxes']:
  for yy in range(y,y+h):
   for xx in range(x,x+w):
    if not protected[yy,xx] and p[yy,xx]=='.':put(a['flower-'+str((xx+yy)%4)],xx,yy)
 mc.background_bank=mc.bank.copy();mc.background_idx=mc.idx.copy()
 opaque=a['tree'].px>0;silhouette=np.zeros((H*16,W*16),bool);overlaps=0
 for x,y in sorted(positions,key=lambda q:(q[1],q[0])):
  for xx,yy in positions:
   if (x,y)==(xx,yy):continue
   assert x+2<=xx or xx+2<=x or y+3<=yy+1 or yy+3<=y+1,'Illegal tree ground overlap'
  region=silhouette[y*16:y*16+48,x*16:x*16+32];overlap=region&opaque;assert not overlap[16:].any(),'Illegal crown overlap';overlaps+=int(overlap.sum());region|=opaque;put_fore(a['tree'],x,y);mc.above[y,x:x+2]=True
 g=f['gate'];x,y=g['x'],g['y'];gw,gh=g['width'],g['height'];put_fore(a['gate'],x,y);solid[y:y+gh,x:x+gw]=True;mc.above[y:y+3,x:x+gw]=True
 for sign in f['signs']:
  x,y=sign['at']
  if protected[y,x]:continue
  put_fore(a['sign'],x,y-1);solid[y,x]=True;beh[y,x]=29;mc.above[y-1,x]=True
 for x,y in f['apricorns']:
  if not protected[y,x]:put_fore(a['apricorn'],x,y-1);solid[y,x]=True;mc.above[y-1,x]=True
 mc.fore_bank=fore.bank;mc.fore_idx=fore.idx;comp={'W':W,'H':H,'cells':cells,'solid':solid,'behavior':beh,'canvas':mc,'tag':'HGSS-Route29-independent'}
 class NativePrimary(packing.Primary):
  def find(self,bank,arr):
   hit=super().find(bank,arr)
   if hit is not None:return hit
   for tid,raw in enumerate(self.tiles):
    if tid in self.animated:continue
    for hf in range(2):
     for vf in range(2):
      candidate=(raw[::-1] if vf else raw)[:,::-1] if hf else (raw[::-1] if vf else raw)
      if np.array_equal(candidate,arr):return tid|(hf<<10)|(vf<<11)
   return None
 primary=NativePrimary(game,92,511);packer=packing.RoutePacker(pals,primary);packer.reserve([np.asarray(v,np.uint8).reshape(8,8) for v in t.tiles[1]],t.blocks[1],t.attrs[1],reserve)
 for mid in visible_primary:
  for en in t.blocks[0][mid]:
   tid=en&1023
   if tid>=512:
    arr=np.asarray(t.tiles[1][tid-512],np.uint8).reshape(8,8);packer.sec_tiles[tid]=arr;packer.slookup.setdefault(arr.tobytes(),tid)
 # Preserve neighbor glyphs cached just outside the visible crossing camera.
 imported_cache_tiles=set()
 for name,sec,w,h,ox,oy in [('CherrygroveCity','cherrygrove',80,48,-80,0),('NewBarkTown','new_bark',36,50,98,6)]:
  ng,ns=seams.read_layout(game,name,w,h);neighbor=Tileset(game,sec,'cherrygrove');window,_,_=seams.crossing_windows(ns,solid,-ox,-oy);window|=seams.visible_across(route_reach,ns.shape,ox,oy)
  for mid in np.unique(ng[window]):
   for en in neighbor.blocks[int(mid>=512)][int(mid)-512 if mid>=512 else int(mid)]:
    tid=en&1023
    if tid>=512:
     arr=np.asarray(neighbor.tiles[1][tid-512],np.uint8).reshape(8,8)
     assert np.array_equal(arr,np.asarray(t.tiles[1][tid-512],np.uint8).reshape(8,8)),('Baseline seam glyph differs',name,tid)
     packer.sec_tiles[tid]=arr;packer.slookup.setdefault(arr.tobytes(),tid);imported_cache_tiles.add(tid)
 provenance=ground_native.install(game,pals);grid=np.zeros(p.shape,np.uint16);layer_report=layers.pack(comp,packer,pals,grid,S);grid[protected]=old[protected]
 nt,nb=packing.write_route_tileset(game,'claude_route29',packer,pals)
 for bank in range(16):
  if bank not in [6,7,8,12]:shutil.copyfile(base/f'data/tilesets/secondary/claude_route29/palettes/{bank:02}.pal',game/f'data/tilesets/secondary/claude_route29/palettes/{bank:02}.pal')
 (S/'proposed-map.bin').write_bytes(grid.astype('<u2').tobytes());np.save(S/'plan.npy',p);np.save(S/'protected.npy',protected);np.save(S/'solid.npy',solid)
 image=Tileset(game,'claude_route29','cherrygrove').map_image(grid.ravel().tolist(),W);image.save(E/'native-proposal.png')
 rgb=np.asarray(image);expected_rgb=np.zeros_like(rgb);mask=(mc.fore_bank>=0)&~np.repeat(np.repeat(protected,16,0),16,1)
 for bank in np.unique(mc.fore_bank):
  if bank>=0:
   selected=mc.fore_bank==bank;expected_rgb[selected]=np.asarray(pals[int(bank)].gba(),np.uint8)[mc.fore_idx[selected]]
 errors=int(np.count_nonzero(np.any(rgb!=expected_rgb,axis=2)&mask));assert errors==0,('Foreground color/mask errors',errors)
 report={'reference_cells':3332,'applied_HGSS_rows':[0,26],'native_offset_y':2,'preserved_coast_rows':[29,47],'town_adapter_columns':[[0,9],[88,97]],'forest':forest_report,'trees':positions,'ground':provenance,'layers':layer_report,'tiles':nt,'metatiles':nb,'reserved_palette_banks':sorted(reserved_banks),'illegal_tree_ground_overlaps':0,'permitted_canopy_overlap_pixels':overlaps,'neighbor_layouts_changed':False,'native_features':f}
 (E/'assembly.json').write_text(json.dumps(report,indent=2)+'\n');print('Route29 packed:',nt,nb,'whole trees:',len(positions),'reserved banks:',reserved_banks)
if __name__=='__main__':assemble(Path(sys.argv[1]).resolve())
