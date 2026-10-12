#!/usr/bin/env python3
"""Route 30 authored edit operation; no historical map generator is replayed.
The new blueprint is composed from reference measurements and approved pixels.
Native IDs visible from neighbouring maps are reserved at their original values.
Use porygon to apply the proposed block grid after inspecting proposal.png.
"""
import json,sys,struct,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from tiles import Tileset,palette
from claude_cherrygrove.pixel import Canvas,Palette
from claude_cherrygrove import build as native,ground,banks
from claude_routes import build as pool,seams
from johto_polish.build import pack_cells
ROOT=HERE.parents[3];OUT=ROOT/'gba/art/route30-rebuild';BASE=OUT/'source/baseline';ASSETS=ROOT/'gba/art/cherrygrove-synthesis/refined'

def load_palette(bank,game):
 kind='primary/cherrygrove' if bank<6 else 'secondary/claude_route30'
 return Palette(bank,palette(game/f'data/tilesets/{kind}/palettes/{bank:02}.pal')[1:],[f'c{i}' for i in range(15)])

def stamp_source(t,grid,cx,cy,w,h,selected,pals):
 """Decode the selected scenery bank, retaining source indices and alpha."""
 cs={b:Canvas(w*16,h*16,pals[b]) for b in selected}
 for y in range(h):
  for x in range(w):
   mid=int(grid[cy+y,cx+x]&1023);entries=t.blocks[mid>=512][mid-512 if mid>=512 else mid]
   for layer in range(2):
    for q in range(4):
     e=entries[layer*4+q];b=e>>12;tid=e&1023
     if b not in cs:continue
     a=np.array(t.tiles[tid>=512][tid-512 if tid>=512 else tid],np.uint8).reshape(8,8)
     if e&2048:a=a[::-1]
     if e&1024:a=a[:,::-1]
     xx,yy=x*16+q%2*8,y*16+q//2*8;dest=cs[b].px[yy:yy+8,xx:xx+8];m=a>0;dest[m]=a[m]
 return [c for c in cs.values() if c.px.any()]

def new_materials():
 # HGSS TEX0 egrass was decoded and preserved before the archive cleanup.
 raw=np.asarray(Image.open(ROOT/'gba/art/johto-cohesion/references/egrass.png').convert('RGBA')).copy()
 original=raw[...,:3].copy();colors=sorted(np.unique(original.reshape(-1,3),axis=0),key=lambda v:int(v.sum()))
 for old,new in zip(colors,[(32,112,80),(32,120,88),(40,136,80),(56,152,88),(64,168,112),(80,192,120)]):raw[...,:3][np.all(original==old,axis=2)]=new
 yy,xx=np.indices((16,16));raws={}
 for n in range(2):
  for s in range(2):
   for w in range(2):
    for e in range(2):
     a=raw.copy();mask=np.ones((16,16),bool)
     edge=np.array([3,2,3,1,0,2,3,2,1,0,2,3,1,2,0,1])
     if not n:mask&=yy>=edge[xx]
     if not s:mask&=yy<16-(edge[xx]%3)
     if not w:mask&=xx>=edge[yy]%3
     if not e:mask&=xx<16-(edge[yy]%3)
     a[...,3]=mask*255;raws[f'grass{n}{s}{w}{e}']=a
 # Freshwater texture is a native-scale source crop, not animated coastal foam.
 ref=np.asarray(Image.open(ROOT/'gba/art/claude-routes/references/route30-hgss.png').convert('RGB'))
 water=ref[788:820,358:390].copy();water=(water//8)*8
 for n in range(2):
  for s in range(2):
   for w in range(2):
    for e in range(2):
     a=np.zeros((16,16,4),np.uint8);a[...,:3]=water[:16,:16];a[...,3]=255
     distance=np.full((16,16),16)
     if not n:distance=np.minimum(distance,yy)
     if not s:distance=np.minimum(distance,15-yy)
     if not w:distance=np.minimum(distance,xx)
     if not e:distance=np.minimum(distance,15-xx)
     a[distance==0,3]=0;a[distance==1,:3]=(104,208,152);a[distance==2,:3]=(160,168,112);a[distance==3,:3]=(104,112,80);a[distance==4,:3]=(88,184,208)
     if not n and not w:a[yy+xx<7,3]=0
     if not n and not e:a[yy+15-xx<7,3]=0
     if not s and not w:a[15-yy+xx<7,3]=0
     if not s and not e:a[30-yy-xx<7,3]=0
     raws[f'pond{n}{s}{w}{e}']=a
 # The authored grass family has been compiled by Porytiles. Decode its
 # native output and require exact opaque pixels before importing it into the
 # route's free palette bank. Existing tilesets are never passed to Porytiles.
 compiled=OUT/'source/porytiles-native'
 if compiled.exists():
  tiles=pool.read_tiles(compiled/'tiles.png');blocks=list(struct.iter_unpack('<8H',(compiled/'metatiles.bin').read_bytes()));cp={int(v.stem):palette(v) for v in (compiled/'palettes').glob('*.pal')}
  names=[key for key in raws if key.startswith('grass')]
  for i,name in enumerate(names):
   c=np.zeros((16,16,4),np.uint8)
   for layer in range(2):
    for q in range(4):
     en=blocks[i][layer*4+q];arr=tiles[en&1023].copy()
     if en&1024:arr=arr[:,::-1]
     if en&2048:arr=arr[::-1]
     y,x=q//2*8,q%2*8;part=c[y:y+8,x:x+8];m=arr>0;part[m,:3]=np.asarray(cp[en>>12],np.uint8)[arr[m]];part[m,3]=255
   assert np.array_equal(c[...,3],raws[name][...,3]) and np.array_equal(c[c[...,3]>0],raws[name][raws[name][...,3]>0]),name
   raws[name]=c
 (OUT/'source/materials').mkdir(exist_ok=True)
 for name,a in raws.items():Image.fromarray(a).save(OUT/'source/materials'/(name+'.png'))
 return raws

def edit(game):
 spec=json.loads((OUT/'source/layout.json').read_text());W,H=spec['width'],spec['height'];p=np.full((H,W),'T',dtype='<U1')
 for phase in ['.','T','A','P','G','W','_']:
  if phase=='A':
   for opening in spec['openings']:
    x,y,w,h=opening['rect'];p[y:y+h,x:x+w]='.'
  for ch,x,y,w,h in spec['operations']:
   if ch==phase:p[y:y+h,x:x+w]=ch
 # Restore the measured HGSS terrain categories in the actual route area.
 # The old renderer is not run; the independent geometry stencil is a source
 # reference. Native art, footprints and metatiles are authored in this edit.
 hgss=json.loads((OUT/'source/hgss-navigation.json').read_text());reference=np.full((74,35),'T',dtype='<U1')
 for ch,x,y,w,h in hgss['measurements']:reference[y:y+h,x:x+w]=ch
 for y in range(70):
  for x in range(W):
   ch=reference[y,x]
   p[y,x]='P' if ch in 'P=' else '#' if ch in '#|^abcF' else ch if ch in 'TGW_' else '.'
 p[2:46,32:34]='#';p[7:27,15]='#';p[29:35,7]='#';p[35,4:9]='#';p[36:65,4]='#'
 for house in spec['houses']:p[house['y']:house['y']+5,house['x']:house['x']+5]='.'
 t=Tileset(BASE,'claude_route30','cherrygrove');pals={b:load_palette(b,game) for b in range(16)}
 old=np.frombuffer((BASE/'data/layouts/CherrygroveRoute30Approach/map.bin').read_bytes(),'<u2').reshape(H,W).copy();oldsolid=(old&0xC00)!=0
 # Both directions are analysed against the committed source before painting.
 layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts'];protected=np.zeros((H,W),bool);reserve=set();visible_primary=set();rreach=seams.reachable(oldsolid,(8,H-1))
 for name,ox,oy,start in [('CherrygroveCity',-35,86,(43,0)),('JohtoRoute31',-28,-30,(38,29))]:
  l=next(l for l in layouts if l['name']==name+'_Layout');ng,ns=seams.read_layout(game,name,l['width'],l['height']);nr=seams.reachable(ns,start)
  protected|=seams.visible_across(nr,(H,W),-ox,-oy);nw,rw,_=seams.crossing_windows(ns,oldsolid,-ox,-oy);protected|=rw
  neighbor_visible=seams.visible_across(rreach,ns.shape,ox,oy)|nw
  reserve|={int(v) for v in ng[neighbor_visible] if v>=512}
  visible_primary|={int(v) for v in ng[neighbor_visible] if v<512}
 # The accepted town-approach extension is outside the original HGSS
 # route. Preserve its complete width instead of splicing individual cells.
 protected[70:]=True
 p[70:]=np.where(oldsolid[70:],'T','.')
 # Preserve complete old tree rectangles when a camera boundary intersects
 # them. A partial protected metatile strip cannot cut an existing crown.
 baseline_tree=stamp_source(t,old,0,0,W,H,[3],pals)[0].px
 tree_px=np.asarray(Image.open(ASSETS/'tree.png'));tree_mask=tree_px>0
 fixed_tree_footprints=[]
 for y in range(H-2):
  for x in range(W-1):
   candidate=baseline_tree[y*16:y*16+48,x*16:x*16+32]
   if np.array_equal(candidate[tree_mask],tree_px[tree_mask]) and protected[y:y+3,x:x+2].any():
    protected[y:y+3,x:x+2]=True;fixed_tree_footprints.append([x*16,y*16,32,48])
 reserve|={int(v&1023) for v in old[protected] if v&1023>=512}
 visible_primary|={int(v&1023) for v in old[protected] if v&1023<512}

 reserved_banks={e>>12 for mid in reserve for e in t.blocks[1][mid-512] if e}
 reserved_banks|={e>>12 for mid in visible_primary for e in t.blocks[0][mid] if e}
 assert not reserved_banks&{12},reserved_banks
 raw=new_materials();A={}
 # Emerald reserves background banks 13–15 for other engine graphics.
 # Use the sole free map bank 12 for grass and pond together; pin the donor
 # grass ladder and ground anchors, then fit the small water vocabulary.
 b=banks.Bank(12,'route30_materials','secondary')
 for key,rgba in raw.items():b.add(key,rgba)
 b.keep(*[(32,112,80),(32,120,88),(40,136,80),(56,152,88),(64,168,112),(80,192,120)])
 for i,c in enumerate([(104,208,152),(96,200,152),(96,192,144)]):b.add('lawn'+str(i),np.array([[list(c)+[255]]],np.uint8)).keep(c)
 A.update(b.build());pals[12]=b.palette
 # Approved indexed art is used without resizing, new perspective or color-keying.
 for key,bank in [('tree',3),('gable',6),('house2',7)]:
  px=np.asarray(Image.open(ASSETS/(key+'.png'))).copy();c=Canvas(px.shape[1],px.shape[0],pals[bank]);c.px=px;A[key]=c
 cells=np.full((H,W),ground.GRASS,np.int8);cells[p=='P']=ground.PATH
 solid=np.isin(p,['T','#']);behavior=np.zeros((H,W),np.uint8);mc=native.MapCanvas(W,H);objects=[]
 def obj(c,x,y,sort=None):objects.append((y+c.h if sort is None else sort,x,y,c))
 # Grass and pond boundaries use complete cells, never mirrored half textures.
 for y in range(H):
  for x in range(W):
   ch=p[y,x]
   if ch in 'GW':
    nb=lambda yy,xx:0<=yy<H and 0<=xx<W and p[yy,xx]==ch
    key=('grass' if ch=='G' else 'pond')+''.join(str(int(v)) for v in [nb(y-1,x),nb(y+1,x),nb(y,x-1),nb(y,x+1)])
    obj(A[key],x*16,y*16,-2);behavior[y,x]=2 if ch=='G' else 16
    if ch=='W':solid[y,x]=True
 # The accepted native tree owns a complete 2x3-cell rectangle. Neither
 # silhouettes nor footprint rectangles may overlap. Protected connection
 # artwork is already occupied and cannot receive a second tree.
 obstacles=np.zeros((H,W),bool)
 rock_stamps=[([12,0,23,2],[12,0],[2,8]),([32,2,2,44],[32,2],[2]),([15,5,2,23],[15,5],[2,5]),([7,28,7,1],[7,28],[2]),([7,29,1,7],[7,29],[2]),([4,35,5,1],[4,35],[2]),([4,36,1,29],[4,36],[2]),([5,63,25,1],[5,63],[2])]
 for box,at,bs in rock_stamps:
  x,y,w,h=box
  for c in stamp_source(t,old,x,y,w,h,bs,pals):
   cell_mask=(c.px>0).reshape(h,16,w,16).any(axis=(1,3))
   obstacles[at[1]:at[1]+h,at[0]:at[0]+w]|=cell_mask
 for entry in spec['stairs']:
  x,y,w,h=entry['source'];xx,yy=entry['at'];obstacles[yy:yy+h,xx:xx+w]=True
 for x,y in spec['signs']:obstacles[y-1:y+1,x]=True
 occupied=protected|obstacles;positions=[];footprints=[]
 def fit(x,y):
  return (0<=x and 0<=y and x+2<=W and y+3<=H
          and (p[y:y+3,x:x+2]=='T').all()
          and not occupied[y:y+3,x:x+2].any())
 def place(x,y):
  occupied[y:y+3,x:x+2]=True;positions.append((x*16,y*16))
  footprints.append([int(x*16),int(y*16),32,48])
 for y in range(0,H,3):
  for x in range(0,W,2):
   if fit(x,y):place(x,y)
 for y,x in zip(*np.nonzero((p=='T')&~occupied)):
  if occupied[y,x]:continue
  for yy,xx in [(y,x),(y-1,x),(y-2,x)]:
   if fit(xx,yy):place(xx,yy);break
 opaque=np.zeros((H*16,W*16),bool)
 allowed=np.repeat(np.repeat((p=='T')&~(protected|obstacles),16,0),16,1)
 for px,py in sorted(positions,key=lambda v:(v[1],v[0])):
  mask=A['tree'].px>0;region=opaque[py:py+48,px:px+32]
  assert not (region&mask).any(),'Overlapping tree silhouettes'
  assert allowed[py:py+48,px:px+32][mask].all(),'Tree spills outside forest footprint'
  region|=mask;obj(A['tree'],px,py)
 (OUT/'evidence/tree-footprints.json').write_text(json.dumps({
  'geometry':spec['tree_geometry'],'footprint_rectangles':footprints,
  'footprint_overlaps':0,'silhouette_overlap_pixels':0,
  'non_forest_pixels':0,'clipped_instances':0,
  'protected_connection_cells':int(protected.sum())},indent=2)+'\n')
 # Registered native rock/step art is decoded from the current route, not donor
 # model cutouts. The landform and crossing coordinates retain HGSS topology.
 for box,at,bs in rock_stamps:
  x,y,w,h=box
  for c in stamp_source(t,old,x,y,w,h,bs,pals):obj(c,at[0]*16,at[1]*16,-1)
  if box[0] in (4,32):solid[y:y+h,x:x+w]=True
 solid[7:27,15]=True
 for entry in spec['stairs']:
  x,y,w,h=entry['source'];xx,yy=entry['at']
  for c in stamp_source(t,old,x,y,w,h,[2,5,8],pals):obj(c,xx*16,yy*16,-1)
  solid[yy:yy+h,xx:xx+w]=np.isin(p[yy:yy+h,xx:xx+w],['T','#','W']);cells[yy:yy+h,xx:xx+w]=ground.PATH
 # All ledges have deliberate continuous ends, retaining the original jump rule.
 ledges=stamp_source(t,old,8,20,5,1,[11,2],pals)
 for y in range(H):
  xs=np.where(p[y]=='_')[0]
  for x in xs:
   # Native end/corner fragments are reassembled from the measured ledge strip.
   source_x=0 if x==xs.min() else 4 if x==xs.max() else 2
   for src in ledges:
    c=Canvas(16,16,src.pal);c.px=src.px[:,source_x*16:(source_x+1)*16].copy();obj(c,x*16,y*16,-1)
   solid[y,x]=True;behavior[y,x]=59
 for house in spec['houses']:
  x,y=house['x'],house['y'];c=A[house['asset']];obj(c,x*16,y*16);solid[y:y+5,x:x+5]=True
 for x,y in spec['signs']:
  for c in stamp_source(t,old,x,y-1,1,2,[5],pals):obj(c,x*16,(y-1)*16)
  solid[y,x]=True;behavior[y,x]=29;mc.above[y-1,x]=True
 for (x,y,w,h) in [(20,4,3,3),(21,33,3,2),(17,53,3,2),(12,23,3,3),(12,56,3,2)]:
  for c in stamp_source(t,old,x,y,w,h,[4],pals):obj(c,x*16,y*16)
 for _,x,y,c in sorted(objects,key=lambda v:(v[0],v[1])):mc.blit(c,x,y)
 mc.under_bank=mc.bank.copy();mc.under_idx=mc.idx.copy()
 comp={'W':W,'H':H,'cells':cells,'solid':solid,'behavior':behavior,'canvas':mc,'tag':'route30-rebuild'}
 primary=pool.Primary(game,92,511);packer=pool.RoutePacker(pals,primary)
 # Seed only fixed IDs; free Route 30 slots can be reauthored independently.
 packer.reserve([np.array(v,np.uint8).reshape(8,8) for v in t.tiles[1]],t.blocks[1],t.attrs[1],reserve)
 # Primary metatiles can reference secondary graphics. Camera transitions
 # retain those tile entries; preserve their actual tile IDs too.
 primary_secondary_tiles=set()
 for mid in visible_primary:
  for entry in t.blocks[0][mid]:
   tid=entry&1023
   if tid>=512:
    arr=np.asarray(t.tiles[1][tid-512],np.uint8).reshape(8,8)
    if tid in packer.sec_tiles:assert np.array_equal(packer.sec_tiles[tid],arr)
    packer.sec_tiles[tid]=arr;packer.slookup.setdefault(arr.tobytes(),tid)
    primary_secondary_tiles.add(tid)

 grid=old.copy();pack_cells(comp,packer,pals,~protected,grid)
 # Shared artwork IDs stay fixed, but unintended forest gaps must not remain
 # walkable simply because a neighbouring camera can see their pixels.
 grid[protected&np.isin(p,['T','#'])]|=0xC00
 # Interior forest restrictions are categorical, even where a sprite's alpha
 # would leave a visible sliver of lawn between two silhouettes.
 assert ((grid[p=='T']&0xC00)!=0).all(), 'Unintended walkable forest gap'
 reference_forest=(reference[:70]=='T')
 actual_walkable=(grid[:70]&0xC00)==0
 assert not (reference_forest&actual_walkable).any(), 'HGSS forest shortcut'
 # Only map palette banks 0–12 are loaded by Emerald.
 for word in np.unique(grid&1023):
  entries=packer.primary.blocks[int(word)] if word<512 else packer.sec_blocks[int(word)][0]
  assert all(entry>>12<13 for entry in entries), 'Reserved engine palette used by map artwork'
 nt,nb=pool.write_route_tileset(game,'claude_route30',packer,pals)
 for bank in range(16):
  if bank !=12:shutil.copyfile(BASE/f'data/tilesets/secondary/claude_route30/palettes/{bank:02}.pal',game/f'data/tilesets/secondary/claude_route30/palettes/{bank:02}.pal')
 # Applying blockdata through porygon is separate from the authored preview.
 (OUT/'source/proposed-map.bin').write_bytes(grid.astype('<u2').tobytes());np.save(OUT/'source/plan.npy',p)
 # Decode the actual engine tileset, not the source canvas, for review.
 image=Tileset(game,'claude_route30','cherrygrove').map_image(grid.ravel().tolist(),W);image.save(OUT/'evidence/proposal.png')
 check=np.repeat(np.repeat(~protected,16,0),16,1)&(mc.bank>=0);expected=np.zeros_like(np.asarray(image))
 for bank in np.unique(mc.bank):
  if bank>=0:
   m=mc.bank==bank;expected[m]=np.asarray(pals[int(bank)].gba(),np.uint8)[mc.idx[m]]
 errors=np.any(np.asarray(image)!=expected,2)&check;assert not errors.any(),int(errors.sum())
 (OUT/'evidence/editor.json').write_text(json.dumps({'protected_connection_cells':int(protected.sum()),'protected_palette_banks':sorted(reserved_banks),'secondary_tile_span':nt,'secondary_metatile_span':nb,'scenery_pixels_verified':int(check.sum()),'scenery_pixel_errors':int(errors.sum()),'forest_trees':len(set(positions)),'preserved_complete_tree_footprints':fixed_tree_footprints,'primary_metatile_secondary_tiles_reserved':len(primary_secondary_tiles)},indent=2)+'\n')
 print('Authored preview saved; blockdata not yet applied',nt,nb)
if __name__=='__main__':edit(Path(sys.argv[1]).resolve())
