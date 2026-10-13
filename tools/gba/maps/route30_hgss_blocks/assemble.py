#!/usr/bin/env python3
"""Author native blockdata from the independent HGSS block survey.
Only the separate connection adapter reads prior Gen 3 blockdata.
"""
from pathlib import Path
import sys,json,shutil,struct
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE))
from tiles import Tileset,palette
from claude_cherrygrove.pixel import Palette,Canvas
from claude_cherrygrove import build as native,ground
from claude_routes import build as packing,seams
import assets,shared_seams,ground_native,layers
ROOT=HERE.parents[3];OUT=ROOT/'gba/art/route30-hgss-blocks';S=OUT/'source';EV=OUT/'evidence';W,H=35,86

def snapshot(game):
 base=S/'seam-baseline'
 if not base.exists():
  for folder in ['data/tilesets/primary/cherrygrove','data/tilesets/secondary/claude_route30','data/tilesets/secondary/cherrygrove','data/tilesets/secondary/route31']:
   shutil.copytree(game/folder,base/folder)
  p=base/'data/layouts/CherrygroveRoute30Approach';p.mkdir(parents=True);shutil.copyfile(game/'data/layouts/CherrygroveRoute30Approach/map.bin',p/'map.bin')
 for sec in ['cherrygrove','route31']:
  folder=f'data/tilesets/secondary/{sec}'
  if not (base/folder).exists():shutil.copytree(game/folder,base/folder)
 return base

def assemble(game):
 base=snapshot(game);old=np.fromfile(base/'data/layouts/CherrygroveRoute30Approach/map.bin',dtype='<u2').reshape(H,W)
 oldsolid=(old&0xc00)!=0;t=Tileset(base,'claude_route30','cherrygrove');p=np.full((H,W),'T',dtype='<U1')
 rows=(S/'blocks.txt').read_text().splitlines();assert len(rows)==74 and all(len(row)==W for row in rows);p[:74]=np.array([list(row) for row in rows]);p[74:]= 'T';p[74:76,7:10]='P';p[76:,8:11]='P';p[74:76,25:33]='W'
 feature=json.loads((S/'structures.json').read_text());pals={i:Palette(i,palette(base/f'data/tilesets/{"primary/cherrygrove" if i<6 else "secondary/claude_route30"}/palettes/{i:02}.pal')[1:],[f'c{j}' for j in range(15)]) for i in range(16)}
 # Integration boundary, separate from the independently traced HGSS core.
 protected=np.zeros((H,W),bool);cg_protected=np.zeros((H,W),bool);reserve=set();visible_primary=set();rreach=seams.reachable(oldsolid,(8,85))
 for name,sec,w,h,ox,oy,start in [('CherrygroveCity','cherrygrove',80,48,-35,86,(43,0)),('JohtoRoute31','route31',63,30,-28,-30,(38,29))]:
  ng,ns=seams.read_layout(game,name,w,h);nr=seams.reachable(ns,start);nw,rw,_=seams.crossing_windows(ns,oldsolid,-ox,-oy);view=rw|seams.visible_across(nr,(H,W),-ox,-oy);protected|=view
  if sec=='cherrygrove':cg_protected|=view
  nv=nw|seams.visible_across(rreach,ns.shape,ox,oy);reserve|={int(v) for v in ng[nv] if v>=512};visible_primary|={int(v) for v in ng[nv] if v<512}
 # Extend camera masks to full crowns, preventing partial old/new tree splices.
 bk=np.full((H*16,W*16),-1,np.int8);ix=np.zeros((H*16,W*16),np.uint8)
 for y in range(H):
  for x in range(W):
   mid=int(old[y,x]&1023)
   for layer in range(2):
    for q in range(4):
     en=t.blocks[int(mid>=512)][mid-512 if mid>=512 else mid][layer*4+q];tid=en&1023;bank=en>>12;arr=np.asarray(t.tiles[int(tid>=512)][tid-512 if tid>=512 else tid],np.uint8).reshape(8,8)
     if en&1024:arr=arr[:,::-1]
     if en&2048:arr=arr[::-1]
     yy,xx=y*16+q//2*8,x*16+q%2*8;m=arr>0;bk[yy:yy+8,xx:xx+8][m]=bank;ix[yy:yy+8,xx:xx+8][m]=arr[m]
 tree=np.asarray(Image.open(ROOT/'gba/art/cherrygrove-synthesis/refined/tree.png'));opaque=tree>0;fixed=[]
 for y in range(H-2):
  for x in range(W-1):
   if not protected[y:y+3,x:x+2].any():continue
   region=ix[y*16:y*16+48,x*16:x*16+32];banks=bk[y*16:y*16+48,x*16:x*16+32]
   if (banks[opaque]==3).all() and np.array_equal(region[opaque],tree[opaque]):
    protected[y:y+3,x:x+2]=True;fixed.append([x*16,y*16,32,48])
    if cg_protected[y:y+3,x:x+2].any():cg_protected[y:y+3,x:x+2]=True
 reserve|={int(v&1023) for v in old[protected] if v&1023>=512};visible_primary|={int(v&1023) for v in old[protected] if v&1023<512}
 reserved_banks={en>>12 for mid in reserve for en in t.blocks[1][mid-512] if en}|{en>>12 for mid in visible_primary for en in t.blocks[0][mid] if en};assert 12 not in reserved_banks,reserved_banks
 a=assets.create(pals,Tileset(game,'cherrygrove','cherrygrove'));mc=native.MapCanvas(W,H);cells=np.full((H,W),ground.GRASS,np.int8);cells[np.isin(p,['P','S'])]=ground.PATH;solid=np.isin(p,list('T#H!AW_K'));beh=np.zeros((H,W),np.uint8)
 fore=native.MapCanvas(W,H)
 def put(c,x,y):mc.blit(c,x*16,y*16)
 def put_fore(c,x,y,dx=0,dy=0):mc.blit(c,x*16+dx,y*16+dy);fore.blit(c,x*16+dx,y*16+dy)
 under=np.full(p.shape,'.',dtype='<U1');under[:74]=np.array([list(row) for row in (S/'terrain.txt').read_text().splitlines()])

 def neighbors(ch,x,y):return ''.join(str(int(0<=xx<W and 0<=yy<H and p[yy,xx]==ch)) for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)])
 for y in range(H):
  for x in range(W):
   ch=p[y,x]
   if ch=='T':pass
   elif ch=='G':
    c=a['grass-'+neighbors(ch,x,y)]
    put(c,x,y);beh[y,x]=2
   elif ch=='W':put(a['pond-'+str(sum((1<<i)*int(v) for i,v in enumerate(neighbors(ch,x,y))))+'-'+str((y%2)*2+x%2)],x,y);beh[y,x]=16
   elif ch=='#' or (ch=='H' and under[y,x]=='#'):
    if x==15 and 6<=y<28:kind='west'
    elif (x==3 and y>=36) or (x in [33,34] and y<46):kind='east'
    else:kind='face' if y>0 and under[y-1,x]=='#' else 'cap'
    put(a[f'cliff-{kind}-{(x+y)%2}'],x,y)
   elif ch=='_':put(a['ledge-'+str(x%2)],x,y);beh[y,x]=59
 for stair in feature['stairs']:
  x,y,w,h=stair['rect']
  for yy in range(y,y+h):
   for xx in range(x,x+w):
    c=a['step-'+('left' if xx==x else 'right' if xx==x+w-1 else 'middle')]
    if stair.get('orientation')=='east-west':
     rotated=Canvas(16,16,c.pal);rotated.px=np.rot90(c.px).copy();c=rotated
    put(c,xx,yy);solid[yy,xx]=False
 for x,y,w,h in feature['flower_boxes']:
  for yy in range(y,y+h):
   for xx in range(x,x+w):
    if p[yy,xx]=='.':put(a['flower-'+str((xx+yy)%4)],xx,yy)
 mc.background_bank=mc.bank.copy();mc.background_idx=mc.idx.copy()
 def tree_fore(c,x,y):
  clean=Canvas(c.w,c.h,c.pal);clean.px=c.px.copy();sy,sx=np.indices(clean.px.shape);shadow=np.isin(clean.px,[3,12])&((x+sx//16)==13)&np.isin(p[y+sy//16,x+sx//16],['c']);clean.px[shadow]=0
  # Ground shadows stay below the player and are not foreground canopy masks.
  yy,xx=np.nonzero(shadow);gy,gx=yy+y*16,xx+x*16
  mc.background_bank[gy,gx]=3;mc.background_idx[gy,gx]=c.px[yy,xx]
  put_fore(clean,x,y)
 # Footprints own 2x2 ground cells; the native 2x3 sprite has a one-row upper
 # canopy. Only that canopy may cover the preceding tree's bottom row.
 occupied=np.zeros((H,W),bool);positions=[];tree_votes=np.load(S/'tree-source-fractions.npy')
 def fits(x,y):
  return 0<=x and 0<=y and x+2<=W and y+3<=H and (p[y+1:y+3,x:x+2]=='T').all() and all(p[y,xx]=='T' or (y<74 and p[y,xx] in '.G#' and tree_votes[y,xx]>.10) for xx in range(x,x+2)) and not occupied[y+1:y+3,x:x+2].any() and not cg_protected[y:y+3,x:x+2].any()
 def place(x,y):occupied[y+1:y+3,x:x+2]=True;positions.append((int(x),int(y)))
 for y in range(0,H,2):
  for x in range(0,W,2):
   if fits(x,y):place(x,y)
 for y,x in zip(*np.nonzero((p=='T')&~occupied)):
  if occupied[y,x]:continue
  for yy,xx in [(y-1,x),(y-2,x),(y,x)]:
   if fits(xx,yy):place(xx,yy);break
 silhouette=np.zeros((H*16,W*16),bool);allowed_overlap=0
 for x,y in sorted(positions,key=lambda q:(q[1],q[0])):
  for xx,yy in positions:
   if (xx,yy)==(x,y):continue
   assert x+2<=xx or xx+2<=x or y+3<=yy+1 or yy+3<=y+1,('overlapping tree ground footprints',(x,y),(xx,yy))
  region=silhouette[y*16:y*16+48,x*16:x*16+32];overlap=region&opaque
  assert not overlap[16:].any(),'Overlap outside permitted upper canopy';allowed_overlap+=int(overlap.sum());region|=opaque;tree_fore(a['tree'],x,y);mc.above[y,x:x+2]=True
 tree_canvases=np.zeros((H,W),bool)
 for x,y in positions:tree_canvases[y:y+3,x:x+2]=True
 for y,x in zip(*np.nonzero((p=='T')&~tree_canvases&~cg_protected)):
  c=a['woodland-margin-'+str(sum((1<<i)*int(v) for i,v in enumerate(neighbors('T',int(x),int(y)))))]
  if protected[y,x]:
   c=Canvas(16,16,pals[3]);c.px=a['tree'].px[8:24,8:24].copy()
  put_fore(c,int(x),int(y));mc.above[y,x]=True
 # The HGSS divider's trunk strip is one cell wide; the western canopy
 # overhang covers a walkable ledge-bypass strip. Reuse complete CG sprites,
 # with reference-measured physical footprints rather than whole-sprite walls.
 for tree in feature['divider_trees']:
  x,y=tree['x'],tree['y'];tree_fore(a['tree'],x,y)
  gx,gy,gw,gh=tree['ground_rect'];solid[gy:gy+gh,gx:gx+gw]=True
  mc.above[y:y+3,x]=True;mc.above[y,x:x+2]=True
 for house in feature['houses']:

  x,y=house['x'],house['y'];put_fore(a[house['asset']],x,y);solid[y:y+5,x:x+5]=(under[y:y+5,x:x+5]=='#')
  if house['asset']=='gable':solid[y+1:y+5,x+1:x+5]=True
  else:solid[y+1:y+5,x+1:x+5]=True
  mc.above[y,x:x+5]=True;mc.above[y:y+5,x]=True
 for sign in feature['signs']:
  x,y=sign['at'];put_fore(a['sign'],x,y-1);solid[y,x]=True;beh[y,x]=29;mc.above[y-1,x]=True
 for x,y in feature['apricorns']:put_fore(a['apricorn'],x,y-1);solid[y,x]=True;mc.above[y-1,x]=True
 for cut in feature['cut_barriers']:
  x,y=cut['ground'];dx,dy=cut['native_canvas_offset'];put_fore(a['cut-barrier'],x,y,dx,dy);solid[y,x]=True;mc.above[y-1,x:x+2]=True
 mc.fore_bank=fore.bank;mc.fore_idx=fore.idx
 mc.under_bank=mc.bank.copy();mc.under_idx=mc.idx.copy();comp={'W':W,'H':H,'cells':cells,'solid':solid,'behavior':beh,'canvas':mc,'tag':'independent-HGSS-blocks'}
 class NativePrimary(packing.Primary):
  def find(self,bank,arr):
   found=super().find(bank,arr)
   if found is not None:return found
   # A matching animated tile must not hide an existing static duplicate.
   for tid,raw in enumerate(self.tiles):
    if tid in self.animated:continue
    for hf in range(2):
     for vf in range(2):
      candidate=(raw[::-1] if vf else raw)[:,::-1] if hf else (raw[::-1] if vf else raw)
      if np.array_equal(candidate,arr):return tid|(hf<<10)|(vf<<11)
   return None
 primary=NativePrimary(game,92,511);packer=packing.RoutePacker(pals,primary);packer.reserve([np.asarray(v,np.uint8).reshape(8,8) for v in t.tiles[1]],t.blocks[1],t.attrs[1],reserve)
 packer.reserved_metatile_ids=set(reserve)
 for mid in visible_primary:
  for en in t.blocks[0][mid]:
   tid=en&1023
   if tid>=512:
    arr=np.asarray(t.tiles[1][tid-512],np.uint8).reshape(8,8);packer.sec_tiles[tid]=arr;packer.slookup.setdefault(arr.tobytes(),tid)
 ground_provenance=ground_native.install(game,pals)
 grid=np.zeros((H,W),np.uint16);layer_report=layers.pack(comp,packer,pals,grid,S)
 core=np.zeros(p.shape,bool);core[:74]=True
 assert not cg_protected[:74].any(), 'CG compatibility would override the HGSS core'
 grid[cg_protected]=(old[cg_protected]&0xf3ff)|(np.where(solid[cg_protected],0xc00,0).astype(np.uint16))
 shared=shared_seams.synchronize(game,base,grid,primary,packer,solid)
 assert ((grid[(p=='T')&core]&0xc00)!=0).all(),'Reference forest shortcut'
 for word in np.unique(grid&1023):
  entries=primary.blocks[int(word)] if word<512 else packer.sec_blocks[int(word)][0];assert all(en>>12<13 for en in entries)
 nt,nb=packing.write_route_tileset(game,'claude_route30',packer,pals)
 if layer_report['composited_terrain_palette']==7:shutil.copyfile(game/'data/tilesets/secondary/claude_route30/palettes/07.pal',game/'data/tilesets/secondary/route31/palettes/07.pal')
 for bank in range(16):
  if bank not in [7,12]:shutil.copyfile(base/f'data/tilesets/secondary/claude_route30/palettes/{bank:02}.pal',game/f'data/tilesets/secondary/claude_route30/palettes/{bank:02}.pal')
 (S/'proposed-map.bin').write_bytes(grid.astype('<u2').tobytes());np.save(S/'plan.npy',p);np.save(S/'protected.npy',protected)
 image=Tileset(game,'claude_route30','cherrygrove').map_image(grid.ravel().tolist(),W);image.save(EV/'native-proposal.png')
 pix=np.asarray(image);expected=np.zeros_like(pix);check=(mc.fore_bank>=0)&~np.repeat(np.repeat(cg_protected,16,0),16,1)
 for bank in np.unique(mc.bank):
  if bank>=0:m=mc.bank==bank;expected[m]=np.asarray(pals[int(bank)].gba(),np.uint8)[mc.idx[m]]
 error=np.any(pix!=expected,2)&check;assert not error.any(),int(error.sum())
 (EV/'assembly.json').write_text(json.dumps({'reference_blocks':2590,'reference_rows':74,'native_width':W,'native_height':H,'integration_adapter_rows':[74,85],'shared_seam_support':shared,'ground_provenance':ground_provenance,'protected_connection_cells':int(protected.sum()),'core_cells_copied_from_previous_Gen3_layout':int(cg_protected[:74].sum()),'northern_palette_adapter_cells':0,'layer_report':layer_report,'reserved_palette_banks':sorted(reserved_banks),'new_tree_positions':positions,'previous_boundary_tree_rectangles':fixed,'exclusive_tree_ground_cells':[2,2],'tree_canvas_cells':[2,3],'permitted_upper_canopy_overlap_pixels':allowed_overlap,'divider_tree_ground_footprints':[q['ground_rect'] for q in feature['divider_trees']],'illegal_ground_footprint_overlaps':0,'scenery_pixel_errors':0,'tiles':nt,'metatiles':nb,'layout_source':'source/blocks.txt, independently surveyed from source/hgss-reference.png; prior Gen 3 blockdata is consulted only to reserve old library IDs for compatibility; it does not supply the reconstructed layout'},indent=2)+'\n')
 print('HGSS-block proposal packed',nt,nb,'new trees',len(positions))
if __name__=='__main__':assemble(Path(sys.argv[1]).resolve())
