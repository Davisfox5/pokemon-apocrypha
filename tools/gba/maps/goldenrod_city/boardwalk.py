"""Guarded Goldenrod boardwalk expansion and owner-approved civic additions.
Does not replay the authoring generator or alter unrelated maps/palettes/IDs.
"""
from pathlib import Path
import sys,json,subprocess,struct,io
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=R/'gba/art/goldenrod-city/source';E=S.parent/'evidence';O=E/'boardwalk';O.mkdir(exist_ok=True)
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='fdaf387b1ef1b0704e4f6a2f4ac0c24444d900a7'
assert subprocess.run(['git','-C',str(G),'diff','--quiet','HEAD']).returncode==0,'Preserve existing native edits; use the immutable baseline worktree.'
subprocess.run(['python3',str(G/'tools/goldenrod/check.py')],check=True)
def baseline_source(name):
 return subprocess.check_output(['git','-C',str(R),'show','bcfb58b5458a36e3ccd625079dbb507bcf9e8a47:gba/art/goldenrod-city/source/'+name])
sections=json.loads((E/'sections.json').read_text());bg=np.zeros((896,1344,4),np.uint8);fg=bg.copy();records=[]
for s in sections:
 n=s['name'];x,y,x1,y1=s['box'];t=Tileset(G,n.lower(),n.lower());g=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x)
 for cy,cx in np.ndindex(g.shape):
  mid=int(g[cy,cx]&1023)
  for i,e in enumerate(t.blocks[mid>=512][mid%512]):
   tid=e&1023;a=np.array(t.tiles[tid>=512][tid%512]).reshape(8,8);a=a[::-1] if e&2048 else a;a=a[:,::-1] if e&1024 else a;p=np.array(t.pals[(e>>12)>=6][e>>12],np.uint8);v=np.dstack([p[a],np.where(a>0,255,0).astype(np.uint8)]);xx=(x+cx)*16+i%2*8;yy=(y+cy)*16+(i%4)//2*8;(fg if i>=4 else bg)[yy:yy+8,xx:xx+8]=v
 records.append((s,t,g))
oldbg=bg.copy();oldfg=fg.copy();before=bg[...,:3].copy();m=fg[...,3]>0;before[m]=fg[m,:3];Image.fromarray(before).save(O/'before.png')
D=S/'boardwalk'
solid=np.load(io.BytesIO(baseline_source('solid.npy')));above=np.load(io.BytesIO(baseline_source('above.npy')));mat=np.load(io.BytesIO(baseline_source('material.npy')))
# Only four genuinely unused city-bank10entries are extended. Accepted tree
# indices1..11 and every other palette remain unchanged.
for _,t,g in records:
 for cy,cx in np.ndindex(g.shape):
  mid=int(g[cy,cx]&1023)
  for e in t.blocks[mid>=512][mid%512]:
   if e>>12==10:assert max(t.tiles[(e&1023)>=512][(e&1023)%512])<12
 for pals in t.pals:pals[10][12:16]=[(160,208,200),(216,80,32),(240,232,216),(240,192,104)]
# The approved new development alone expands the HGSS shoreline.
deck=np.zeros((56,84),bool);deck[6:15,22:39]=True;deck[15,22:38]=True;deck[15:26,34:38]=True;deck[26,35:37]=True
wood=np.array(Image.open(D/'deck.png'));yy,xx=np.indices((896,1344));dm=deck.repeat(16,0).repeat(16,1);bg[dm]=wood[yy[dm]%16,xx[dm]%32];fg[dm]=0;solid[deck]=False;above[deck]=False;mat[deck]='timber boardwalk';solid[26,34:38]=False
# Remove residual rock strip on the preserved narrow city-side shore; keep the
# neighboring tower's existing upper-layer silhouette intact.
pave=oldbg[480:496,160:176].copy()
for y in range(128,288):
 for x in range(624,632):bg[y,x]=pave[y%16,x%16]
for y in range(240,288):
 for x in range(608,624):bg[y,x]=pave[y%16,x%16]
# Remove the superseded waterfront flag post across the new access join.
bg[384:416,528:544]=oldbg[384:416,496:512];bg[416:432,528:560]=np.tile(pave,(1,2,1));bg[416:432,592:608]=pave;fg[384:432,528:560]=0;fg[416:432,592:608]=0
# Old duplicated roof-background pixels included the former bank fragments.
fg[240:264,608:632]=0;fg[264:280,608:624]=0
# Restore clean water behind the wheel and under new piles before adding timber.
water=oldbg[64:96,384:416].copy()
for y in range(48,96):
 for x in range(432,560):bg[y,x]=water[y%32,x%32]
for y in range(256,288):
 for x in range(352,544):bg[y,x]=water[y%32,x%32]
# Deck front fascia and piles sit below the floor, above the actual water.
for x in range(352,544):
 for y in range(256,264):bg[y,x]=[144,104,56,255] if y<260 else [56,48,48,255]
for x in range(360,544,32):
 for y in range(264,276):bg[y,x:x+5]=[120,72,40,255];bg[y,x:x+1]=[168,136,96,255]
# Railing masters connect at shared tile edges, with an open southern entry.
rails={s:np.array(Image.open(D/('rail-'+s+'.png'))) for s in ['N','S','W','E']}
def paste(a,x,y,clear=False):
 if isinstance(a,str):a=np.array(Image.open(D/(a+'.png')))
 h,w=a.shape[:2]
 if clear:
  fg[y//8*8:(y+h+7)//8*8,x//8*8:(x+w+7)//8*8]=0
 target=fg[y:y+h,x:x+w];m=a[...,3]>0;target[m]=a[m]
 return a
for y,x in np.argwhere(deck):
 for label,dx,dy in [('N',0,-1),('S',0,1),('W',-1,0),('E',1,0)]:
  if deck[y+dy,x+dx] or y==26:continue
  if label=='S' and y==26 and x in [35,36]:continue
  paste(rails[label],int(x*16),int(y*16));solid[y,x]=True;mat[y,x]='boardwalk railing'
# Large scenery and compact stalls remain independent RGBA masters.
wheel=paste('wheel',432,48);wheelmask=np.zeros((896,1344),bool);wheelmask[48:192,432:560]=wheel[...,3]>0
above[3:12,27:35]=True;solid[10:12,28:34]=True;mat[3:12,27:35]='Ferris wheel / deck';mat[10:12,28:34]='wheel supports'
placements=[('snacks',368,128),('prizes',416,176),('souvenirs',544,160)]
for name,x,y in placements:
 paste(name,x,y);above[y//16:(y+48)//16,x//16:(x+48)//16]=True;solid[(y+32)//16:(y+48)//16,x//16:(x+48)//16]=True;mat[y//16:(y+48)//16,x//16:(x+48)//16]='market awning/counter'
for x,y in [(360,208),(592,320),(544,384),(592,384)]:
 paste('lantern',x,y);above[y//16:(y+32)//16,x//16]=True;solid[(y+16)//16,x//16]=True
# Station departure display uses the old plaque's mounting position; kiosk is
# beside, not across, the real entrance at world47,26.
paste('departures',768,376,True);above[23:25,48:52]=True;paste('ticket-kiosk',848,400,True);above[25:27,53]=True;solid[26,53]=True;mat[26,53]='ticket kiosk'
paste('broadcast',336,464,True);above[29:31,21]=True;solid[30,21]=True;mat[30,21]='broadcast display'
paste('bench',240,560,True);solid[35,15:17]=True;mat[35,15:17]='bench'
# Replace complete original rail spans, including caps and legs, then join the
# new masonry retaining beds to the untouched neighboring rails.
ground=oldbg[480:496,160:176].copy()
planters=[('planter',144,568),('planter',336,568),('retaining-planter',1040,856),('retaining-planter',1120,856)]
for name,x,y in planters:
 a=np.array(Image.open(D/(name+'.png')));h,w=a.shape[:2]
 for py in range(y,y+h):
  for px in range(x,x+w):bg[py,px]=ground[(py-576)%16,(px-144)%16]
 fg[y:y+h,x:x+w]=0;paste(a,x,y);above[y//16:(y+h+15)//16,x//16:(x+w)//16]=True
 solid[(y+8)//16:(y+h+15)//16,x//16:(x+w)//16]=True;mat[y//16:(y+h+15)//16,x//16:(x+w)//16]='planter/fence'
# Design preview is retained before palette fitting; actual native output is
# decoded independently below, and Porymap/runtime provide separate parity.
preview=bg[...,:3].copy();m=fg[...,3]>0;preview[m]=fg[m,:3];Image.fromarray(preview).save(O/'design.png')
# Preserve current native source IDs. Clone only changed metatiles and append
# required index glyphs to free hardware slots, with per-quadrant palette fitting.
quantized=[np.zeros_like(bg),np.zeros_like(fg)];stats=[];pending=[]
for s,t,g in records:
 n=s['name'];x,y,x1,y1=s['box'];tiles=[[np.array(v,np.uint8).reshape(8,8) for v in part] for part in t.tiles];blocks=[list(v) for v in t.blocks];attrs=[list(v) for v in t.attrs];look={a.tobytes():i*512+j for i,part in enumerate(tiles) for j,a in enumerate(part)};changedcells=0
 kept=set([0])
 for cy,cx in np.ndindex(g.shape):
  mid=int(g[cy,cx]&1023)
  for i,e in enumerate(t.blocks[mid>=512][mid%512]):
   yy=(y+cy)*16+(i%4)//2*8;xx=(x+cx)*16+i%2*8
   if np.array_equal((fg if i>=4 else bg)[yy:yy+8,xx:xx+8],(oldfg if i>=4 else oldbg)[yy:yy+8,xx:xx+8]):kept.add(e&1023)
 free=[i*512+j for i,part in enumerate(tiles) for j in range(len(part)) if i*512+j not in kept]
 # Free slots are absent from every unchanged live map quadrant. Preserve all
 # existing IDs/art still used by unchanged cells.
 look={}
 def register(a,gid):
  for flipped,flag in [(a,0),(a[:,::-1],0x400),(a[::-1],0x800),(a[::-1,::-1],0xc00)]:look.setdefault(flipped.tobytes(),gid|flag)
 for i,part in enumerate(tiles):
  for j,a in enumerate(part):
   if i*512+j in kept:register(a,i*512+j)
 def encode(a,oldentry):
  mask=a[...,3]>0
  if not mask.any():return 0
  rgb=a[...,:3].astype(int);best=None
  for bank in ([11] if force_bank==11 else [oldentry>>12]+[b for b in range(13) if b!=oldentry>>12]):
   pal=np.array(t.pals[bank>=6][bank],int);dist=((rgb[:,:,None]-pal[None,None,1:])**2).sum(axis=3);idx=dist.argmin(axis=2)+1;err=int(dist.min(axis=2)[mask].sum())
   if best is None or err<best[0]:best=(err,idx,bank)
   if err==0:break
  err,idx,bank=best;idx=idx.astype(np.uint8);idx[~mask]=0;k=idx.tobytes()
  if k not in look:
   if free:
    gid=free.pop(0);tiles[gid>=512][gid%512]=idx;register(idx,gid)
   else:
    part=0 if len(tiles[0])<512 else 1
    assert len(tiles[part])<(512 if part==0 else 496),(n,'glyph capacity')
    gid=part*512+len(tiles[part]);tiles[part].append(idx);register(idx,gid)
  pal=np.array(t.pals[bank>=6][bank],np.uint8);v=np.dstack([pal[idx],np.where(idx>0,255,0).astype(np.uint8)])
  return look[k]|bank<<12
 for cy,cx in np.ndindex(g.shape):
  wx,wy=x+cx,y+cy;sl=np.s_[wy*16:wy*16+16,wx*16:wx*16+16];mid=int(g[cy,cx]&1023);es=list(blocks[mid>=512][mid%512]);changed=not np.array_equal(bg[sl],oldbg[sl]) or not np.array_equal(fg[sl],oldfg[sl]);attr=attrs[mid>=512][mid%512];newattr=(attr&~0xf000)|(0 if above[wy,wx] else 0x1000)
  if changed:
   for i in range(8):
    yy=wy*16+(i%4)//2*8;xx=wx*16+i%2*8;a=(fg if i>=4 else bg)[yy:yy+8,xx:xx+8];old=(oldfg if i>=4 else oldbg)[yy:yy+8,xx:xx+8]
    if not np.array_equal(a,old):
     force_bank=11 if i>=4 and wheelmask[yy:yy+8,xx:xx+8].any() else -1;es[i]=encode(a,es[i])
  if changed or newattr!=attr:
   part=0 if len(blocks[0])<512 else 1;newmid=part*512+len(blocks[part]);assert newmid<1024;blocks[part].append(tuple(es));attrs[part].append(newattr);g[cy,cx]=(int(g[cy,cx])&~1023)|newmid;changedcells+=1
  g[cy,cx]=(int(g[cy,cx])&~0xc00)|(0xc00 if solid[wy,wx] else 0)
 pending.append((s,t,g,tiles,blocks,attrs,changedcells));stats.append(dict(map=n,changed_metatiles=changedcells,glyphs=[len(v) for v in tiles]))
# All sections must fit BEFORE mutating any native source.
for s,t,g,tiles,blocks,attrs,changedcells in pending:
 n=s['name']
 for part,d in enumerate(t.dirs):
  if changedcells:
   sheet=Image.new('P',(128,((len(tiles[part])+15)//16)*8));sheet.putpalette(Image.open(d/'tiles.png').getpalette())
   for i,a in enumerate(tiles[part]):sheet.paste(Image.fromarray(a).convert('P'),(i%16*8,i//16*8))
   sheet.save(d/'tiles.png',bits=4)
   (d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in blocks[part]));(d/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs[part]),*attrs[part]))
  pal=t.pals[part][10];(d/'palettes/10.pal').write_bytes(('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pal)+'\n').replace('\n','\r\n').encode())
 g.tofile(G/f'data/layouts/{n}/map.bin')
# Derive expected RGB layers from the edited native files (quantization is explicit).
for s,_,_ in records:
 n=s['name'];x,y,x1,y1=s['box'];t=Tileset(G,n.lower(),n.lower());g=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x)
 for cy,cx in np.ndindex(g.shape):
  mid=int(g[cy,cx]&1023)
  for i,e in enumerate(t.blocks[mid>=512][mid%512]):
   tid=e&1023;a=np.array(t.tiles[tid>=512][tid%512]).reshape(8,8);a=a[::-1] if e&2048 else a;a=a[:,::-1] if e&1024 else a;pal=np.array(t.pals[(e>>12)>=6][e>>12],np.uint8);xx=(x+cx)*16+i%2*8;yy=(y+cy)*16+(i%4)//2*8;quantized[i>=4][yy:yy+8,xx:xx+8]=np.dstack([pal[a],np.where(a>0,255,0).astype(np.uint8)])
after=quantized[0][...,:3].copy();m=quantized[1][...,3]>0;after[m]=quantized[1][m,:3]
assert np.array_equal(after[wheelmask],preview[wheelmask]),'Ferris wheel colors changed'
Image.fromarray(quantized[0][...,:3]).save(S/'native-ground.png');Image.fromarray(quantized[1]).save(S/'shared-foreground.png');np.save(S/'solid.npy',solid);np.save(S/'above.npy',above);np.save(S/'material.npy',mat);Image.fromarray(after).save(O/'after.png')
(O/'native-edit.json').write_text(json.dumps(dict(baseline='fdaf387b1ef1b0704e4f6a2f4ac0c24444d900a7',sections=stats,palette_extension='Only unused city-bank10slots12..15; all existing used colors preserved.',deck_cells=np.argwhere(deck)[:,::-1].tolist(),wheel_box=[432,48,560,192],stalls=placements,planters=planters,entrance=[[35,26],[36,26]],authorized_landing=[[x,26] for x in range(34,38)],bikes=False,ride_animation=False,market_services=False),indent=2)+'\n');print(stats)

from boardwalk_events import apply
apply(G)
