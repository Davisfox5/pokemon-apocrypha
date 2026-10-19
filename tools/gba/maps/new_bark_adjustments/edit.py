"""Scoped editor: move committed blocks, append variants; never rebuild the town."""
from pathlib import Path
import sys,json,struct,shutil
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
from claude_cherrygrove import ground,hgss
from claude_routes.layouts import plan
G=Path(sys.argv[1]);OUT=ROOT/'gba/art/new-bark-adjustments';S=OUT/'source';E=OUT/'evidence'
for rel in ['data/layouts/NewBarkTown/map.bin','data/maps/NewBarkTown/map.json','data/tilesets/secondary/new_bark']:
 target=S/'baseline'/rel
 if not target.exists():
  target.parent.mkdir(parents=True,exist_ok=True)
  if (G/rel).is_dir():shutil.copytree(G/rel,target)
  else:shutil.copyfile(G/rel,target)
base=S/'baseline'
# Restore the two unsupported experimental banks; they never become source changes.
for bank in [13,14]:shutil.copyfile(base/f'data/tilesets/secondary/new_bark/palettes/{bank:02}.pal',G/f'data/tilesets/secondary/new_bark/palettes/{bank:02}.pal')
shutil.copytree(G/'data/tilesets/primary/cherrygrove',base/'data/tilesets/primary/cherrygrove',dirs_exist_ok=True);t=Tileset(base,'new_bark','cherrygrove');old=np.fromfile(base/'data/layouts/NewBarkTown/map.bin','<u2').reshape(50,36);g=old.copy()
# Ground plan describes only existing terrain and the explicitly edited paths.
p=plan(30,24,[('.',0,9,28,5),('P',0,12,28,2),('P',11,10,6,3),('.',7,4,10,6),('.',17,8,11,3),('.',8,14,16,7),('P',10,14,3,7),('P',12,19,12,3),('P',22,14,2,6),('.',1,18,9,2),('W',28,12,2,3)])
q=np.full((50,36),'T',dtype='<U1');q[:24,6:]=p;q[9:14,:6]='.';q[12:14,:6]='P';q[22:42,7:29]='.';q[7:12,16:18]='P';q[21:41,16:18]='P';q[31:33,9:28]='P';q[40:42,9:28]='P';q[29:32,10:12]='P';q[29:32,25:27]='P';q[38:41,10:12]='P';q[38:41,25:27]='P';q[12:39,34:]='W';q[38:,30:]='W'
oldq=q.copy();q[22:42,7:29]='.';q[22:41,16:18]='P';q[30:32,9:29]='P';q[29:32,9:11]='P';q[39:41,11:26]='P';q[37:41,11:13]='P'
cells=np.zeros(q.shape,np.int8);cells[q=='P']=ground.PATH;cells[q=='W']=ground.SEA
from cherrygrove_synthesis import refine
m=np.repeat(np.repeat(cells,16,0),16,1);gy,gx=np.indices(m.shape);gi=np.zeros(m.shape,np.uint8);nb=np.zeros(m.shape,np.int8)
# The legacy crop helper writes evidence. Keep those writes isolated from
# the accepted Cherrygrove sources and preserve this edit's crops locally.
from tempfile import TemporaryDirectory
with TemporaryDirectory() as tmp:
 isolated=Path(tmp);ref=isolated/'gba/art/johto-v1/references';ref.mkdir(parents=True)
 shutil.copyfile(ROOT/'gba/art/johto-v1/references/cherrygrove-hgss.png',ref/'cherrygrove-hgss.png')
 crops=isolated/'gba/art/cherrygrove-synthesis/references/HGSS-direct';crops.mkdir(parents=True)
 textures=refine.ground_sources(isolated,t.pals[0][0],t.pals[0][1])
 shutil.copytree(crops,S/'ground-reference',dirs_exist_ok=True)
refine.terrain(gi,nb,m==ground.GRASS,m==ground.PATH,m==ground.SEA,gx+640,gy,textures)

blocks=[tuple(a) for a in t.blocks[1]];attrs=list(t.attrs[1]);lookup={(a,attrs[i]):512+i for i,a in enumerate(blocks)}
tiles=[np.asarray(v,np.uint8).reshape(8,8) for pool in t.tiles for v in pool];tilelookup={}
# Door animations own VRAM tiles 1008-1023. Use only unreferenced zero
# padding below that boundary, preserving every existing library glyph.
referenced={e&1023 for pool in t.blocks for es in pool for e in es if e}
free_tiles=[i for i in range(512,1008) if i not in referenced and not tiles[i].any()]
allocated_tiles=[]
for tid,a in enumerate(tiles):
 if 1<=tid<=92:continue
 tilelookup.setdefault(a.tobytes(),tid)
def tile(a,bank):
 if not a.any():return 0
 for hf,vf,bits in [(0,0,0),(1,0,1024),(0,1,2048),(1,1,3072)]:
  z=a[::-1] if vf else a;z=z[:,::-1] if hf else z
  hit=tilelookup.get(z.tobytes())
  if hit is not None:return hit|bits|(bank<<12)
 assert free_tiles,'static tile capacity; door scratch slots are reserved'
 tid=free_tiles.pop(0);tiles[tid]=a.copy();allocated_tiles.append(tid);tilelookup[a.tobytes()]=tid;return tid|(bank<<12)
def meta(entries,attr):
 key=(tuple(entries),int(attr));hit=lookup.get(key)
 if hit is not None:return hit
 mid=512+len(blocks);assert mid<1024;blocks.append(tuple(entries));attrs.append(int(attr));lookup[key]=mid;return mid
changed=np.zeros(g.shape,bool)
def terrain(x,y):
 es=[tile(gi[y*16+dy:y*16+dy+8,x*16+dx:x*16+dx+8],0) for dy,dx in [(0,0),(0,8),(8,0),(8,8)]]
 g[y,x]=meta(es+[0]*4,0x1000)|0x3000;changed[y,x]=True
# Paint only the changed path boundary and source/destination building cells.
diff=oldq!=q
for y,x in np.argwhere(diff):changed[max(0,y-1):y+2,max(0,x-1):x+2]=True
moves=[dict(warp=0,source=[11,0,11,7],target=[12,0]),dict(warp=4,source=[9,26,5,5],target=[8,24]),dict(warp=5,source=[23,26,5,5],target=[24,25]),dict(warp=6,source=[9,35,5,5],target=[10,32]),dict(warp=7,source=[23,35,5,5],target=[22,34])]
for m in moves:
 x,y,w,h=m['source'];nx,ny=m['target'];changed[y:y+h,x:x+w]=True;changed[ny:ny+h,nx:nx+w]=True
for y,x in np.argwhere(changed.copy()):terrain(int(x),int(y))
for m in moves:
 x,y,w,h=m['source'];nx,ny=m['target'];g[ny:ny+h,nx:nx+w]=old[y:y+h,x:x+w]
# Lab has no backyard opening; preserve its warp behavior, block the roof footprint.
g[0:7,12:23]|=0xc00;g[6,17]&=0xf3ff
# Native complete trees flush against the lab's left edge.
for yy in (0,3):
 g[yy:yy+3,10:12]=old[0:3,6:8];changed[yy:yy+3,10:12]=True
# The one-cell lab shift consumes half of the two trees formerly on its right.
# Clear the remaining halves; the left-side pair replaces these whole trees.
for yy in range(6):terrain(23,yy)
# Remove the forest-overlapping stray mailbox by restoring the matching tree cells.
for y in (5,6):g[y,9]=old[y,7];changed[y,9]=True
for y in (16,17):terrain(21,y)
# Roof-only variants: append metatiles with new palette IDs; doors stay original.
colors={12:[(144,184,224),(136,176,216),(112,152,192),(88,128,176),(72,112,160),(56,88,144),(40,64,104),(32,48,88)],9:[(192,160,224),(184,152,216),(160,128,192),(136,104,176),(120,88,160),(104,72,144),(80,48,112),(64,40,96)]}
for bank,(x,y,nrows) in [(12,(8,24,3)),(9,(22,34,4))]:
 assert not any(e>>12==bank for row in t.blocks[1] for e in row if e)
 pal=list(t.pals[1][6])
 for index,color in zip([4,5,6,7,10,11,13,14],colors[bank]):pal[index]=color
 (G/f'data/tilesets/secondary/new_bark/palettes/{bank:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pal)+'\n')
 for yy in range(y,y+nrows):
  for xx in range(x,x+5):
   word=int(g[yy,xx]);mid=word&1023;es=t.blocks[mid>=512][mid%512];es=[(e&4095)|(bank<<12) if e>>12==6 else e for e in es];g[yy,xx]=meta(es,t.attrs[mid>=512][mid%512])|(word&0xfc00)
# Reuse the established mailbox artwork, converted to its existing prop palette.
mail=hgss.mailbox();Image.fromarray(mail).save(S/'mailbox-source.png');pp=np.array(t.pals[0][4][1:],int);midx=np.zeros(mail.shape[:2],np.uint8);mask=mail[...,3]>0;midx[mask]=((mail[mask,:3].astype(int)[:,None]-pp)**2).sum(2).argmin(1)+1
mailboxes=[(25,8),(10,17),(21,19),(13,28),(23,29),(9,36),(27,38)]
assert midx.shape==(32,16),midx.shape
for x,basey in mailboxes:
 for dy in range(2):
  y=basey-1+dy;terrain(x,y);mid=int(g[y,x]&1023);es=list(blocks[mid-512]);
  for quad in range(4):
   yy=dy*16+quad//2*8;xx=quad%2*8;es[4+quad]=tile(midx[yy:yy+8,xx:xx+8],4)
  g[y,x]=meta(es,0 if dy==0 else 0x1000)|0x3000|(0xc00 if dy else 0)
# Preserve source door identities so existing facade-specific animations remain valid.
mp=G/'data/maps/NewBarkTown/map.json';data=json.loads((base/'data/maps/NewBarkTown/map.json').read_text())
for m in moves:
 i=m['warp'];d=data['warp_events'][i];dx=m['target'][0]-m['source'][0];dy=m['target'][1]-m['source'][1];d.update(x=d['x']+dx,y=d['y']+dy);m['door']=[d['x'],d['y']]
 assert int(g[d['y'],d['x']]&1023)==int(old[d['y']-dy,d['x']-dx]&1023)
# Restore the entire original bottom forest course; the prior one-cell path
# cleanup margin must not overwrite neighboring tree crowns.
g[42:45,6:30]=old[42:45,6:30]
# Three new northern rows hold full 32x48 trees behind the lab. Existing
# town content stays pixel-for-pixel in place within its original footprint.
north=np.tile(old[0:3,6:8],(1,18));g=np.vstack([north,g]);changed=np.vstack([np.ones((3,36),bool),changed])
# Replace pink foliage with existing exact green counterparts, preserving
# shared palettes and every collision bit at the route seam.
green_lookup={}
for part in (0,1):
 for index,entries in enumerate(t.blocks[part]):green_lookup.setdefault((tuple(entries),t.attrs[part][index]),part*512+index)
green_cells=[]
for y,x in np.argwhere(np.ones(g.shape,bool)):
 word=int(g[y,x]);mid=word&1023;part=int(mid>=512);entries=blocks[mid-512] if part else t.blocks[0][mid]
 if not any(e>>12==10 for e in entries):continue
 desired=tuple((e&4095)|(3<<12) if e>>12==10 else e for e in entries)
 replacement=green_lookup[(desired,attrs[mid-512] if part else t.attrs[0][mid])]
 g[y,x]=replacement|(word&0xfc00);changed[y,x]=True;green_cells.append([int(x),int(y)])
for group in ['warp_events','object_events','coord_events','bg_events']:
 for event in data[group]:event['y']+=3
for connection in data['connections']:
 if connection['direction']=='left':connection['offset']=-3
for move in moves:move['target'][1]+=3;move['door'][1]+=3
mailboxes=[(x,y+3) for x,y in mailboxes]
lp=G/'data/layouts/layouts.json';layouts=json.loads(lp.read_text())
for layout in layouts['layouts']:
 if layout['id']=='LAYOUT_NEW_BARK_TOWN':layout['height']=53
lp.write_text(json.dumps(layouts,indent=2)+'\n')
rp=G/'data/maps/CherrygroveRoute29Approach/map.json';route=json.loads(rp.read_text())
for connection in route['connections']:
 if connection['map']=='MAP_NEW_BARK_TOWN':connection['offset']=3
rp.write_text(json.dumps(route,indent=2)+'\n')
mp.write_text(json.dumps(data,indent=2)+'\n');(G/'data/layouts/NewBarkTown/map.bin').write_bytes(g.astype('<u2').tobytes())
folder=G/'data/tilesets/secondary/new_bark';(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs));n=(len(tiles)-512+15)//16;sheet=Image.new('P',(128,n*8));sheet.putpalette(Image.open(folder/'tiles.png').getpalette())
for i,a in enumerate(tiles[512:]):sheet.paste(Image.fromarray(a,'P'),(i%16*8,i//16*8))
sheet.save(folder/'tiles.png');np.save(S/'edited-cells.npy',changed)
report={'base':'2722eaf7601ec02dc5a684fa8cdef9206c0dc377','moves':moves,'mailboxes':mailboxes,'roof_colors':{'residence1':'blue','residence4':'purple'},'secondary_tiles':len(tiles)-512,'secondary_metatiles':len(blocks),'original_referenced_tiles_and_metatile_prefixes_preserved':True,'new_glyph_slots':allocated_tiles,'door_scratch_tiles_reserved':[1008,1023],'door_metatile_ids_preserved':True,'north_forest_rows':3,'bottom_forest_course_restored':[42,44],'map_size':[36,53],'pink_tree_cells_changed_to_green':green_cells}
(E/'edit.json').write_text(json.dumps(report,indent=2)+'\n');Tileset(G,'new_bark','cherrygrove').map_image(g.ravel().tolist(),36).save(E/'new-bark.png');print(report)
