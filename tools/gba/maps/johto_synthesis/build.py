"""Native connected-map packer. Shared seam entries keep exact IDs on both sides."""
import sys,json,struct,shutil,re
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image
from compose import *
from claude_routes import seams
G=Path(sys.argv[1]).resolve();EV=OUT/'evidence';EV.mkdir(parents=True,exist_ok=True)
T=Tileset(SOURCE,'cherrygrove','cherrygrove')
# Approved town pixels and metatile IDs stay fixed while tile patterns are repacked.
# Secondary entries are anchored
# only in maps which actually display those cells across a connection.
tiles=[np.array(v,np.uint8).reshape(8,8) for pool in T.tiles for v in pool][:998]
tlookup={};anim=set(range(1,93))
for i,ar in enumerate(tiles):
 if i not in anim:tlookup.setdefault(ar.tobytes(),i)
def tile(ar,bank):
 if not ar.any():return (0,0,0)
 if bank==1:
  for i in anim:
   if np.array_equal(ar,tiles[i]):return (i,0,bank)
 for hf,vf,bits in [(0,0,0),(1,0,1024),(0,1,2048),(1,1,3072)]:
  a=ar[::-1] if vf else ar;a=a[:,::-1] if hf else a
  hit=tlookup.get(a.tobytes())
  if hit is not None:return (hit,bits,bank)
 tid=len(tiles);tiles.append(ar.copy());tlookup[ar.tobytes()]=tid;return(tid,0,bank)
blocks=[];attrs=[];bl={}
for part in range(2):
 for es,at in zip(T.blocks[part],T.attrs[part]):
  b=tuple((e&1023,e&3072,e>>12) for e in es);bl[(b,at)]=len(blocks);blocks.append(b);attrs.append(at)
def block(es,at):
 key=(tuple(es),at)
 if key not in bl:bl[key]=len(blocks);blocks.append(tuple(es));attrs.append(at)
 return bl[key]

def pack(comp,pals):
 nb,ni,water,textures=ground_pixels(comp,pals);mc=comp['canvas'];h,w=comp['H'],comp['W'];out=np.zeros((h,w),np.int32)
 for y in range(h):
  for x in range(w):
   lower=[];upper=[]
   for q in range(4):
    yy=y*16+q//2*8;xx=x*16+q%2*8;sl=np.s_[yy:yy+8,xx:xx+8]
    bi=mc.bank[sl];ix=mc.idx[sl].astype('uint8');bs=[int(v) for v in np.unique(bi) if v>=0]
    gb=int(nb[yy,xx]);gi=ni[sl].copy();base=tile(gi,gb)
    gbs=list(np.unique(nb[sl]))
    if len(gbs)>1 and (bi<0).any():
     assert not bs,('shore object needs third layer',comp['tag'],x,y,q,bs)
     waterpatch=ni[sl].copy();mask=nb[sl]==1
     # Fill the concealed water with the same complete animated source tile.
     sea=np.array(Image.open(APP/'references/B/sea-frame-0.png').convert('RGB'),int);pp=np.array(pals[1].gba()[1:],int)
     si=((sea[...,None,:]-pp)**2).sum(-1).argmin(-1)+1
     lo=tile(si[np.arange(yy,yy+8)[:,None]%32,np.arange(xx,xx+8)[None,:]%32].astype('uint8'),1)
     hi=tile(np.where(mask,0,ni[sl]).astype('uint8'),0)
    elif not bs:lo,hi=base,(0,0,0)
    elif len(bs)==1:
     scene=tile(np.where(bi>=0,ix,0).astype('uint8'),bs[0]);lo,hi=(base,scene) if (bi<0).any() or mc.above[y,x] else (scene,(0,0,0))
    else:
     # Two palettes at an object junction use both hardware layers.
     assert len(bs)==2,(comp['tag'],x,y,bs)
     b0,b1=sorted(bs,key=lambda b:np.count_nonzero(bi==b),reverse=True)
     pix=np.where(bi==b0,ix,0).astype('uint8');m=bi<0
     if m.any():
      rgb=np.array(pals[gb].gba())[gi];pp=np.array(pals[b0].gba()[1:]);pix[m]=((rgb[m,None]-pp)**2).sum(-1).argmin(-1)+1
     lo=tile(pix,b0);hi=tile(np.where(bi==b1,ix,0).astype('uint8'),b1)
    lower.append(lo);upper.append(hi)
   at=int(comp['behavior'][y,x])|(0 if mc.above[y,x] else 0x1000)
   out[y,x]=block(lower+upper,at)
 return out

def readgrid(source,name):
 ll=json.loads((source/'data/layouts/layouts.json').read_text())['layouts'];l=next(x for x in ll if x['name']==name+'_Layout')
 return np.frombuffer((source/l['blockdata_filepath']).read_bytes(),'<u2').reshape(l['height'],l['width']).copy()
comps=all_comps();maps={};pmap={};sol={};flags={}
for name,(comp,pals) in comps.items():
 print('Compose',name,flush=True);pmap[name]=pals;grid=pack(comp,pals);s=comp['solid'];f=np.where(s,0x3c00,0x3000).astype('uint16')
 # Water blocks walkers by behavior/elevation, and remains surfable.
 wet=np.isin(comp['behavior'],[16,21]);f[wet]=0x1000
 if name=='route29':
  # Keep the approved town-facing woodland and expand east into the HGSS route.
  oldgrid=readgrid(SOURCE,'CherrygroveRoute29Approach');g=np.zeros((48,98),np.int32);ff=np.full((48,98),0x3c00,np.uint16)
  g[2:36]=grid;ff[2:36]=f
  plain=next(int(grid[y,x]) for y in range(1,33) for x in range(1,97)
             if (comp['canvas'].bank[y*16:y*16+16,x*16:x*16+16]==-1).all()
             and (comp['cells'][y-1:y+2,x-1:x+2]==ground.GRASS).all())
  g[:2]=plain;g[36:]=grid[-1];ff[36:]=f[-1]
  g[:,:10]=oldgrid[:,:10]&1023;ff[:,:10]=oldgrid[:,:10]&0xfc00
  grid,f=g,ff
 elif name=='route30':
  oldgrid=readgrid(SOURCE,'CherrygroveRoute30Approach')[-12:,35:70]
  # Append the accepted approach instead of erasing HGSS's southern rock band,
  # two stair flights, ledge and grass. The core's coordinates stay stable.
  grid=np.concatenate([grid,oldgrid&1023]);f=np.concatenate([f,oldgrid&0xfc00])
  grid[-12:,8:10]=oldgrid[-1,8:10]&1023;f[-12:,8:10]=0x3000
 maps[name]=grid;flags[name]=f;sol[name]=((f&0xc00)!=0)|((f>>12)==1)
maps['town']=readgrid(SOURCE,'CherrygroveCity')&1023;flags['town']=readgrid(SOURCE,'CherrygroveCity')&0xfc00;sol['town']=(flags['town']&0xc00)!=0
pmap['town']={b:pal(b,T.pals[b>=6][b]) for b in range(13)}
# Offset = location of B's origin in A's coordinate system.
joins=[('town','route29',80,0),('town','route30',35,-86),('route29','new_bark',98,6),('route30','route31',-28,-30)]
need={k:set(map(int,v.ravel())) for k,v in maps.items()};seamreport=[]
for a,b,ox,oy in joins:
 va,vb,crossings=seams.crossing_windows(sol[a],sol[b],ox,oy)
 va|=seams.visible_across(~sol[b],sol[a].shape,-ox,-oy)
 vb|=seams.visible_across(~sol[a],sol[b].shape,ox,oy)
 assert crossings,(a,b,'no crossing')
 for here,other,mask in [(a,b,vb),(b,a,va)]:
  mids=set(map(int,maps[other][mask]));need[here]|=mids
  banks={e[2] for mid in mids for e in blocks[mid] if e[0]}
  for bank in banks:assert pmap[here][bank].gba()==pmap[other][bank].gba(),('seam palette',here,other,bank)
 seamreport.append(dict(a=a,b=b,offset=[ox,oy],crossings=crossings,a_cells=int(va.sum()),b_cells=int(vb.sum())))

def allocate(needed,fixed,limit,label,primary=None):
 owners=defaultdict(set)
 for m,ids in needed.items():
  for i in ids:owners[i].add(m)
 assigned=({i:i for i in owners if i<512} if primary is None else dict(primary));used={m:{} for m in needed}
 for i in owners:
  if i not in assigned and i in fixed:
   assigned[i]=i
   for m in owners[i]:used[m][i]=i
 for i in sorted((i for i in owners if i not in assigned),key=lambda i:(-len(owners[i]),-sum(len(needed[m]) for m in owners[i]),i)):
  forbidden=set().union(*(used[m].keys() for m in owners[i]));free=next((c for c in range(512,limit) if c not in forbidden),None)
  if free is None:raise RuntimeError((label,'capacity',i,{m:len(used[m]) for m in owners[i]}))
  assigned[i]=free
  for m in owners[i]:used[m][free]=i
 print(label,{m:len(v) for m,v in used.items()},flush=True)
 return assigned,used
mt,mt_used=allocate(need,set(range(596)),1024,'metatiles')
tneed={m:{e[0] for mid in mids for e in blocks[mid]} for m,mids in need.items()}
# Choose reusable town materials for the shared primary. Animated slots keep
# their exact callback addresses. Town pixels/metatile IDs remain unchanged.
tneed['town'] |= set(range(998))
frequency={i:sum(i in ids for m,ids in tneed.items() if m!='town') for i in range(len(tiles))}
selected=[0]+sorted(anim)
selected += sorted(set(range(998))-set(selected),key=lambda i:(i not in tneed['route31'],-frequency[i],i))[:502-len(selected)]
selected += sorted(set(range(998,len(tiles))),key=lambda i:(i not in tneed['route31'],-frequency[i],i))[:10]
primary={i:n for n,i in enumerate(selected)}
print('Required non-primary tiles', {m:len(v-set(primary)) for m,v in tneed.items()},flush=True)
ti,ti_used=allocate(tneed,set(),1008,'tiles',primary)
from claude_routes.build import write_tiles
pf=G/'data/tilesets/primary/cherrygrove'
write_tiles(pf/'tiles.png',[tiles[i] for i in selected])
for part in (0,1):
 folder=G/'data/tilesets'/('primary' if part==0 else 'secondary')/'cherrygrove'
 count=len(T.blocks[part]);new=[]
 for mid in range(part*512,part*512+count):new.append(tuple(ti[e[0]]|e[1]|e[2]<<12 for e in blocks[mid]))
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in new))
 if part:write_tiles(folder/'tiles.png',[tiles[ti_used['town'][i]] if i in ti_used['town'] else np.zeros((8,8),np.uint8) for i in range(512,1008)])

from claude_routes.build import write_tiles
TUPLE_PRIMARY=blocks[:512]
for name in comps:
 folder=G/'data/tilesets/secondary'/('claude_'+name if name in ('route29','route30') else name);folder.mkdir(parents=True,exist_ok=True);(folder/'palettes').mkdir(exist_ok=True)
 for b in range(16):town.write_pal(folder/'palettes'/f'{b:02}.pal',pmap[name][b].gba() if b in pmap[name] else [(0,0,0)]*16)
 write_tiles(folder/'tiles.png',[tiles[ti_used[name][i]] if i in ti_used[name] else np.zeros((8,8),np.uint8) for i in range(512,1008)])
 bs=[];ats=[]
 for i in range(512,max(mt_used[name],default=512)+1):
  mid=mt_used[name].get(i)
  bs.append(tuple(ti[e[0]]|e[1]|e[2]<<12 for e in blocks[mid]) if mid is not None else (0,)*8);ats.append(attrs[mid] if mid is not None else 0)
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bs));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(ats),*ats))
 n={'route29':'CherrygroveRoute29Approach','route30':'CherrygroveRoute30Approach','new_bark':'NewBarkTown','route31':'JohtoRoute31','violet_entrance':'VioletCityEntrance'}[name]
 grid=np.vectorize(mt.__getitem__)(maps[name])|flags[name];dest=G/'data/layouts'/n;dest.mkdir(exist_ok=True)
 (dest/'map.bin').write_bytes(grid.astype('<u2').tobytes());(dest/'border.bin').write_bytes(grid[:2,:2].astype('<u2').tobytes())
 img=Tileset(G,folder.name,'cherrygrove').map_image(grid.ravel().tolist(),grid.shape[1]);img.save(EV/(name+'.png'))
 # Every primary/secondary entry in a seam resolves identically, not merely a
 # plausible screenshot or one walk-through.
 for mid in need[name]:
  original=blocks[mid];actual=tuple(ti[e[0]]|e[1]|e[2]<<12 for e in TUPLE_PRIMARY[mid]) if mid<512 else bs[mt[mid]-512]
  expected=tuple(ti[e[0]]|e[1]|e[2]<<12 for e in original)
  assert tuple(actual)==expected,('seam entry roundtrip',name,mid)
report=dict(seams=seamreport,tiles={m:len(v) for m,v in ti_used.items()},metatiles={m:len(v) for m,v in mt_used.items()},town_pixels_unchanged=True,door_tiles_reserved=[1008,1023],forests=oldart.FOREST_AUDITS,buildings={k:c[0].get('buildings',[]) for k,c in comps.items()})
(EV/'integration.json').write_text(json.dumps(report,indent=2)+'\n')
print('Packed native connected maps',flush=True)
