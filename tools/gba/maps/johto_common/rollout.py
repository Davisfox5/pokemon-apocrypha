"""Bounded native rollout of approved shared Johto foregrounds.
Read current maps; retain layouts, behavior and all pixels outside explicit masks.
Never replay historical map generators over authored work.
"""
from pathlib import Path
import sys,json,struct,argparse,subprocess,re
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
from johto_service_buildings.build import decode
from johto_common.trees import rgba
from route36.gate_surround.build import over
from claude_cherrygrove import ground
P=ROOT/'gba/art/johto-common/rollout';BASE='5b80e625d1'
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def save(p,a):p.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(a).save(p)
def origins(scene,art):
 """Detect native source anchors, including overlapping and clipped crowns."""
 pad=48;a=np.pad(scene,((pad,pad),(pad,pad),(0,0)));h,w=a.shape[:2];candidates=np.zeros((h,w),bool)
 for coords in [[(43,15),(42,16),(40,14),(36,10),(36,21),(34,8),(34,23)],[(5,15),(8,10),(8,21),(12,8),(12,23),(16,5),(16,26),(20,10),(20,21)]]:
  m=np.ones((h,w),bool)
  for yy,xx in coords:
   if not art[yy,xx,3]:continue
   hit=np.all(a[:,:,:3]==art[yy,xx,:3],2)&(a[:,:,3]>0);shift=np.zeros_like(hit);shift[:h-yy,:w-xx]=hit[yy:,xx:];m&=shift
  candidates|=m
 result=[]
 for y,x in np.argwhere(candidates):
  yy,xx=y-pad,x-pad
  if yy<=-48 or xx<=-32 or yy>=scene.shape[0] or xx>=scene.shape[1] or y+48>h or x+32>w:continue
  crop=a[y:y+48,x:x+32];mask=(art[:,:,3]>0)&(crop[:,:,3]>0);count=mask.sum()
  if count<80:continue
  score=float((np.all(crop[:,:,:3]==art[:,:,:3],2)&mask).sum()/count)
  if score>.5:result.append((int(xx),int(yy),score))
 return sorted(result,key=lambda v:(v[1],v[0]))
def encode(game,config,t,grid,attrs,layers,target,changed):
 """Write secondary-only replacements, keeping shared primary/animation IDs."""
 h,w=grid.shape;ac=changed.reshape(h,16,w,16).any((1,3));oldgrid=grid.copy();palettes=[list(t.pals[i>=6][i]) for i in range(13)]
 raw=[np.array(v,np.uint8).reshape(8,8) for group in t.tiles for v in group];raw+= [np.zeros((8,8),np.uint8) for _ in range(1008-len(raw))]
 blocks=list(t.blocks[1]);ats=list(t.attrs[1]);border=np.fromfile(game/config['layout']['border_filepath'],'<u2')&1023
 retained=set((grid[~ac]&1023).ravel())|set(border);live={0}|(set() if config["primary"]=="violet_city" else set(range(1,93)))
 for mid in retained:live.update(v&1023 for v in t.blocks[int(mid>=512)][int(mid)%512])
 private=config['primary'] in ['johto_cherrygrove','violet_city']
 if private:
  layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts'];assert sum(v['primary_tileset']==config['layout']['primary_tileset'] for v in layouts)==1
 shared_free=[]
 if not private:
  all_live={0}|(set() if config["primary"]=="violet_city" else set(range(1,93)));layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts'];graphics=(game/'src/data/tilesets/graphics.h').read_text()
  for ll in layouts:
   if ll['primary_tileset']!=config['layout']['primary_tileset']:continue
   symbol='gTilesetTiles_'+ll['secondary_tileset'].removeprefix('gTileset_')
   match=re.search(re.escape(symbol)+r'\[\].*?"data/tilesets/secondary/([^/]+)/tiles.png"',graphics);assert match,ll
   tt=Tileset(game,match[1],config['primary']);mids=set(np.fromfile(game/ll['blockdata_filepath'],'<u2')&1023)|set(np.fromfile(game/ll['border_filepath'],'<u2')&1023)
   for mid in mids:all_live.update(e&1023 for e in tt.blocks[int(mid>=512)][mid%512])
  shared_free=[i for i in range(93,512) if i not in all_live]
 free_tiles=[i for i in range((1 if config["primary"]=="violet_city" else 93) if private else 512,1008) if i not in live]+shared_free;free_blocks=[i for i in range(512,1024) if i not in retained]
 cache={v.tobytes():i for i,v in enumerate(raw)};blockcache={(tuple(v),int(a)):i+512 for i,(v,a) in enumerate(zip(blocks,ats))};colorbanks=[set(map(tuple,p[1:])) for p in palettes]
 usednew=set();usedblocks=set()
 def tile(a):
  m=a[:,:,3]>0
  if not m.any():return 0
  colors=set(map(tuple,a[m,:3]));bank=next((i for i,p in enumerate(colorbanks) if colors<=p),None);assert bank is not None,('palette',config['map'],colors)
  ids={}
  for i,c in enumerate(palettes[bank]):
   if i:ids.setdefault(tuple(c),i)
  ix=np.zeros((8,8),np.uint8)
  for c in colors:ix[m&np.all(a[:,:,:3]==c,2)]=ids[c]
  for ar,bits in [(ix,0),(ix[:,::-1],1024),(ix[::-1],2048),(ix[::-1,::-1],3072)]:
   tid=cache.get(ar.tobytes())
   if tid is not None:
    if tid in free_tiles:free_tiles.remove(tid)
    usednew.add(tid);return tid|bits|bank<<12
  assert free_tiles,('tile capacity',config['map']);tid=free_tiles.pop(0)
  key=raw[tid].tobytes()
  if cache.get(key)==tid:cache.pop(key)
  raw[tid]=ix;cache[ix.tobytes()]=tid;usednew.add(tid);return tid|bank<<12
 for cy,cx in np.argwhere(ac):
  es=[]
  for layer in layers:
   for q in range(4):
    y,x=cy*16+q//2*8,cx*16+q%2*8;es.append(tile(layer[y:y+8,x:x+8]))
  key=(tuple(es),int(attrs[cy,cx]));mid=blockcache.get(key)
  if mid is None:
   assert free_blocks,('metatile capacity',config['map']);mid=free_blocks.pop(0)
   while len(blocks)<=mid-512:blocks.append((0,)*8);ats.append(0)
   old=(tuple(blocks[mid-512]),int(ats[mid-512]))
   if blockcache.get(old)==mid:blockcache.pop(old)
   blocks[mid-512]=tuple(es);ats[mid-512]=int(attrs[cy,cx]);blockcache[key]=mid
  elif mid in free_blocks:free_blocks.remove(mid)
  usedblocks.add(mid);grid[cy,cx]=(int(grid[cy,cx])&0xfc00)|mid
 folder=game/'data/tilesets/secondary'/config['secondary'];im=Image.new('P',(128,248));im.putpalette(Image.open(folder/'tiles.png').getpalette())
 for i,a in enumerate(raw[512:1008]):im.paste(Image.fromarray(a),(i%16*8,i//16*8))
 im.save(folder/'tiles.png',bits=4)
 if private or any(i<512 for i in usednew&set(shared_free)):
  dest=game/'data/tilesets/primary'/config['primary']/'tiles.png';im=Image.new('P',(128,256));im.putpalette(Image.open(dest).getpalette())
  for i,a in enumerate(raw[:512]):im.paste(Image.fromarray(a),(i%16*8,i//16*8))
  im.save(dest,bits=4)
 for bank in t.new_banks:
  dest=folder if bank>=6 else game/'data/tilesets/primary'/config['primary']
  (dest/'palettes'/f'{bank:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in t.pals[bank>=6][bank])+'\n')
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in blocks));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(ats),*ats));grid.astype('<u2').tofile(game/config['layout']['blockdata_filepath'])
 check=Tileset(game,config['secondary'],config['primary']);im=np.array(check.map_image(grid.ravel().tolist(),w));assert np.array_equal(im,target[:,:,:3]),('native mismatch',config['map'])
 _,_,_,actual=decode(check,grid);assert np.array_equal(actual,attrs);assert np.array_equal(oldgrid&0xfc00,grid&0xfc00)
 return dict(changed_cells=int(ac.sum()),native_pixel_errors=0,behavior_errors=0,collision_elevation_errors=0,secondary_metatile_count=len(blocks),free_graphic_slots=len(free_tiles))
def split(target,layers,changed,t,foreground):
 h,w=target.shape[:2];ac=changed.reshape(h//16,16,w//16,16).any((1,3));pals=[set(map(tuple,t.pals[i>=6][i][1:])) for i in range(13)]
 quarters=[(int(cy),int(cx),q) for cy,cx in np.argwhere(ac) for q in range(4)]
 if getattr(t,'sort_complexity',False):
  def complexity(v):
   cy,cx,q=v;y,x=cy*16+q//2*8,cx*16+q%2*8;return -len(np.unique(target[y:y+8,x:x+8,:3].reshape(-1,3),axis=0))
  quarters.sort(key=complexity)
 for cy,cx,q in quarters:
  y,x=cy*16+q//2*8,cx*16+q%2*8;sl=np.s_[y:y+8,x:x+8];a=target[sl];colors=set(map(tuple,a[a[:,:,3]>0,:3]));pref=layers[1][sl][:,:,3]>0;pref|=foreground[sl];pref[changed[sl]&~foreground[sl]]=False
  pairs=[(i,j) for i in range(13) for j in range(13) if colors<=pals[i]|pals[j]]
  if not pairs:
   options=[]
   for ii in range(13):
    for jj in ([10,12,11,6,7,8,9,4,1,2,3,5,0] if getattr(t,'allow_primary_palettes',False) else [10,12,11,6,7,8]):
     missing=colors-(pals[ii]|pals[jj])
     if len(missing)<=len(t.free_slots[jj]):options.append((len(missing),ii,jj,missing))
   if options:
    _,ii,jj,missing=min(options,key=lambda v:v[0])
    for c in sorted(missing):t.pals[jj>=6][jj][t.free_slots[jj].pop(0)]=c
    t.new_banks.add(jj)
    if jj in t.free_banks:t.free_banks.remove(jj)
    pals[jj]=set(map(tuple,t.pals[jj>=6][jj][1:]));pairs=[(ii,jj)]
  if not pairs and getattr(t,'allow_primary_palettes',False):
   options=[]
   for ii in range(13):
    for jj in range(ii+1,13):
     missing=colors-(pals[ii]|pals[jj])
     if len(missing)<=len(t.free_slots[ii])+len(t.free_slots[jj]):options.append((len(missing),ii,jj,missing))
   if options:
    _,ii,jj,missing=min(options,key=lambda v:v[0])
    for c in sorted(missing):
     b=jj if t.free_slots[jj] else ii;t.pals[b>=6][b][t.free_slots[b].pop(0)]=c;t.new_banks.add(b)
     if b in t.free_banks:t.free_banks.remove(b)
     pals[b]=set(map(tuple,t.pals[b>=6][b][1:]))
    pairs=[(ii,jj)]
  if not pairs:
   repair=changed[sl]&~foreground[sl];fixed=set(map(tuple,a[~repair,:3]));options=[]
   for ii in range(13):
    for jj in range(13):
     if not fixed<=pals[ii]|pals[jj]:continue
     grasscolors=np.array([c for c in pals[ii]|pals[jj] if c[1]>c[0]+30 and c[1]>c[2]+20 and c[1]>=160],int)
     if not len(grasscolors):continue
     src=a[repair,:3].astype(int);d=np.square(src[:,None]-grasscolors).sum(2);mapped=grasscolors[d.argmin(1)]
     if len(src) and np.abs(src-mapped).max()<=16:options.append((int(d.min(1).sum()),ii,jj,mapped))
   if options:
    _,ii,jj,mapped=min(options,key=lambda v:v[0]);a[repair,:3]=mapped;colors=set(map(tuple,a[a[:,:,3]>0,:3]));pairs=[(ii,jj)]
  if not pairs:
   assert len(colors)<=15 and t.free_banks,('two bank fit',cx,cy,q,colors)
   bank=t.free_banks.pop(0);t.pals[1][bank]=[(0,0,0)]+sorted(colors)+[(0,0,0)]*(15-len(colors));pals[bank]=colors;t.new_banks.add(bank);t.free_slots[bank]=list(range(len(colors)+1,16));pairs=[(bank,bank)]
  def cost(p):return sum(int((np.all(a[:,:,:3]==c,2)&pref).sum())*(c not in pals[p[1]])*100+int((np.all(a[:,:,:3]==c,2)&~pref).sum())*(c not in pals[p[0]]) for c in colors)
  i,j=min(pairs,key=cost);lo=np.zeros_like(a);hi=np.zeros_like(a)
  for c in colors:
   m=np.all(a[:,:,:3]==c,2)
   if c in pals[i] and c in pals[j]:lo[m&~pref]=a[m&~pref];hi[m&pref]=a[m&pref]
   else:(lo if c in pals[i] else hi)[m]=a[m]
  # Keep a reusable complete ground tile under opaque crowns instead of
  # spending hundreds of slots on canopy-shaped holes in the lower layer.
  hidden=(lo[:,:,3]==0)&(hi[:,:,3]>0)&foreground[sl]
  for c in pals[i]:
   m=hidden&np.all(t.background[sl][:,:,:3]==c,2);lo[m]=t.background[sl][m]
  layers[0][sl]=lo;layers[1][sl]=hi

def main(game):
 configs=json.loads((P/'source/initial-inventory.json').read_text());reports=[]
 for config in configs:
  name=config['map']
  if name=='JohtoRoute36':continue
  t=Tileset(game,config['secondary'],config['primary']);l=config['layout'];grid=np.fromfile(game/l['blockdata_filepath'],'<u2').reshape(l['height'],l['width']);layers,banks,es,attrs=decode(t,grid);before=layers[0].copy();over(before,layers[1]);target=before.copy();t.free_banks=[b for b in range(6,13) if b not in set((es.ravel()>>12).tolist())];t.new_banks=set()
  used_indices={i:{0} for i in range(13)}
  border=np.fromfile(game/l['border_filepath'],'<u2')&1023
  for mid in set((grid&1023).ravel())|set(border):
   for e in t.blocks[int(mid>=512)][mid%512]:
    tid=e&1023;used_indices[e>>12].update(t.tiles[int(tid>=512)][tid%512])
  t.free_slots={i:[j for j in range(1,16) if j not in used_indices[i]] for i in range(13)}
  foliage=np.zeros_like(before);foot=np.zeros_like(before);placements=[];pink=np.zeros_like(before)
  for id in ['T01','T02']:
   art=rgba(ROOT/f'gba/art/johto-common/trees/source/{id}.png');positions=origins(before,art)
   for x,y,score in positions:
    over(foliage,art,x,y);over(foot,np.full(art.shape,255,np.uint8),x,y);placements.append(dict(asset=id,x=x,y=y,score=score))
    if id=='T02' and name!='CherrygroveCity':over(pink,rgba(ROOT/'gba/art/johto-common/trees/source/T01.png'),x,y)
  # Existing independently-authored terrain around objects stays untouched.
  # Reconstruct only grass-colored legacy tree backing within full footprints.
  grass=ground.textures()[ground.GRASS];pal=np.array(t.pals[0][0][1:],int);texture=pal[np.square(grass[:,:,None,:].astype(int)-pal).sum(3).argmin(2)]
  ys,xs=np.indices(before.shape[:2]);bg=texture[ys%texture.shape[0],xs%texture.shape[1]]
  colors={(64,136,104),(88,176,136),(96,192,144),(104,200,152),(104,208,152)}
  match=np.any([np.all(before[:,:,:3]==c,2) for c in colors],axis=0)
  work=(foot[:,:,3]>0)&(foliage[:,:,3]==0)&match
  target[work,:3]=bg[work];target[work,3]=255
  # Recolor existing pink specimens outside Cherrygrove with identical green
  # silhouettes, preserving any occluding neighboring architecture.
  pinkcolors=set(map(tuple,rgba(ROOT/'gba/art/johto-common/trees/source/T02.png').reshape(-1,4)[:,:3]))
  recolor=(pink[:,:,3]>0)&np.any([np.all(before[:,:,:3]==c,2) for c in pinkcolors if c!=(0,0,0)],axis=0);target[recolor]=pink[recolor]
  t.background=np.dstack([bg,np.full(bg.shape[:2],255,np.uint8)])
  changed=np.any(target!=before,2);split(target,layers,changed,t,foliage[:,:,3]>0)
  info=encode(game,config,t,grid,attrs,layers,target,changed)
  save(P/'review'/f'{name}-before.png',before);save(P/'review'/f'{name}.png',target);save(P/'source'/f'{name}-repair-mask.png',np.dstack([changed.astype('uint8')*255]*4));dump(P/'source'/f'{name}-trees.json',placements)
  info.update(map=name,tree_count=len(placements),pink_recolored_pixels=int(recolor.sum()),changed_pixels=int(changed.sum()));reports.append(info);print(info,flush=True)
 dump(P/'evidence/trees.json',reports)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);a=p.parse_args();main(a.engine)
