"""Lossless approved C06/M01 placement over a pinned native engine revision.
No resize, RGB quantization, or regeneration of unrelated map artwork.
Cherrygrove gets a private native pair; its animated tile IDs remain intact.
"""
from pathlib import Path
import sys, json, struct, subprocess, tempfile, tarfile, io, shutil, re, hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
BASE='5bea9770ed752a9e7d8c763b64f2adb1c73300a9'
OUT=ROOT/'gba/art/johto-common/service-installation'; E=OUT/'evidence'
CENTER=ROOT/'gba/art/johto-center/source/building.png'
MART=ROOT/'gba/art/johto-mart/source/building.png'
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def rgba(p):return np.array(Image.open(p).convert('RGBA'))
def file_digest(p):
 data=p.read_bytes()
 if p.suffix in ('.pal','.h','.json'):data=data.replace(b'\r\n',b'\n')
 return hashlib.sha256(data).hexdigest()
def overlay(a,b):
 m=b[:,:,3]>0;a[m]=b[m]
def decode(t,grid):
 h,w=grid.shape;layers=[np.zeros((h*16,w*16,4),np.uint8) for _ in range(2)];banks=np.full((h*16,w*16),-1,np.int8);entries=np.zeros((h,w,8),np.uint16);attrs=np.zeros((h,w),np.uint16)
 for y,x in np.ndindex(h,w):
  mid=int(grid[y,x]&1023);entries[y,x]=t.blocks[mid>=512][mid%512];attrs[y,x]=t.attrs[mid>=512][mid%512]
  for i,e in enumerate(entries[y,x]):
   e=int(e);tid=e&1023;b=e>>12;q=i%4;ix=np.array(t.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)
   if e&1024:ix=ix[:,::-1]
   if e&2048:ix=ix[::-1]
   sl=np.s_[y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8];p=layers[i//4][sl];m=ix>0;p[m,:3]=np.array(t.pals[b>=6][b],np.uint8)[ix[m]];p[m,3]=255;banks[sl][m]=b
 return layers,banks,entries,attrs

def main(game):
 guard=OUT/'generated-files.json'
 if guard.exists():
  expected=json.loads(guard.read_text());changed=[p for p,digest in expected.items() if not (game/p).exists() or file_digest(game/p)!=digest]
  if changed:raise SystemExit('Authored engine files changed since shared building installation; reconcile before rebuilding: '+', '.join(changed))
 E.mkdir(parents=True,exist_ok=True); reports={}
 paths=['data/layouts/CherrygroveCity','data/layouts/VioletCity','data/tilesets/primary/cherrygrove','data/tilesets/secondary/cherrygrove','data/tilesets/primary/violet_city','data/tilesets/secondary/violet_city','src/field_door.c','src/data/tilesets','data/layouts/layouts.json']
 with tempfile.TemporaryDirectory(prefix='service-baseline-') as tmp:
  base=Path(tmp)
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE,*paths],cwd=game))) as tf:tf.extractall(tmp,filter='data')
  facade=Tileset(base,'cherrygrove','cherrygrove').pals[1][11]
  center=rgba(CENTER);mart=rgba(MART);cset=set(map(tuple,center[center[:,:,3]>0,:3]));roof=sorted(cset-set(facade[1:]));assert len(roof)==6
  for name,oldname,newname,h in [('CherrygroveCity','cherrygrove','johto_cherrygrove',48),('VioletCity','violet_city','violet_city',72)]:
   cg=name=='CherrygroveCity';w=80;t=Tileset(base,oldname,oldname);grid=np.fromfile(base/f'data/layouts/{name}/map.bin','<u2').reshape(h,w).copy();oldgrid=grid.copy()
   layers,banks,entries,attrs=decode(t,grid);oldattrs=attrs.copy();original=layers[0].copy();overlay(original,layers[1]);background=original.copy();front=np.zeros_like(original);affected=np.zeros((h,w),bool)
   pals=[list(t.pals[b>=6][b]) for b in range(13)]
   if cg:
    pals[8]=[(0,0,0)]+roof+[(0,0,0)]*9
    mp=Image.open(ROOT/'gba/art/johto-mart/source/building.indexed.png');pals[9]=[tuple(v) for v in np.array(mp.getpalette()[:48]).reshape(16,3).tolist()]
    specs=[('center',center,(59,5),(58,4,7,6),(61,9),'C01'),('mart',mart,(49,4),(50,6,6,5),(51,9),'M02')]
   else:
    pals[8]=facade.copy();pals[0][5:11]=roof
    specs=[('center',center,(47,51),(46,50,7,6),(49,55),'C02')]
   # Use a literal existing clear 32px ground patch at matching native phase.
   gx,gy=(56,3) if cg else (46,48)
   grass=original[gy*16:(gy+2)*16,gx*16:(gx+2)*16].copy()
   assert np.all(grass[:,:,1]>grass[:,:,0]),('donor must be grass',name)
   assert set(map(tuple,grass[:,:,:3].reshape(-1,3))) <= set(t.pals[0][0][1:]),('grass donor',name)
   for style,art,(ax,ay),(ox,oy,ow,oh),door,oldid in specs:
    affected[oy:oy+oh,ox:ox+ow]=True;ah,aw=art.shape[:2];affected[ay:ay+ah//16,ax:ax+aw//16]=True
    # Visible terrain survives exactly; replace only the old building's pixels.
    sl=np.s_[oy*16:(oy+oh)*16,ox*16:(ox+ow)*16]
    old=background[sl];bb=banks[sl]
    # These bounded old footprints contain only their building and terrain.
    # Violet paving is palette 1; grass is palette 0 in both cities.
    terrain=np.isin(bb,[0] if cg else [0,1])
    if style=='center':oldmask=rgba(ROOT/f'gba/art/johto-common-review/service-buildings/assets/{oldid}.png')[:,:,3]>0
    else:
     oldmask=np.zeros(bb.shape,bool);oldmask[:64,:80]=rgba(ROOT/'gba/art/cherrygrove-synthesis/refined/mart.png')[:,:,3]>0
     sign=np.array(Image.open(ROOT/'gba/art/cherrygrove-synthesis/references/B/mart_sign.idx.png'))>0;oldmask[16:80,64:96]|=sign
    terrain &= ~oldmask
    yy,xx=np.indices(bb.shape);fill=grass[(yy+(oy-gy)*16)%32,(xx+(ox-gx)*16)%32]
    old[~terrain]=fill[~terrain]
    if cg:
     # Older iterations left terrain-colored facade fragments beyond their
     # retained alpha masks. Restore the entire former building footprint.
     old[:min(oh*16, (10-oy)*16)]=fill[:min(oh*16, (10-oy)*16)]
     if style=='mart':
      # Preserve the true doorway path; remove the old pole sign at x54..55
      # using the adjacent uninterrupted grass-to-road border at x56..57.
      background[10*16:11*16,54*16:56*16]=original[10*16:11*16,56*16:58*16]
    # The existing Violet apron continues beneath the projecting facade.
    if not cg:
     stone=original[56*16:57*16,48*16:49*16]
     for cy in range(54,56):
      for cx in range(47,52):
       ps=np.s_[cy*16:(cy+1)*16,cx*16:(cx+1)*16];mask=~terrain[(cy-oy)*16:(cy-oy+1)*16,(cx-ox)*16:(cx-ox+1)*16];background[ps][mask]=stone[mask]
    overlay(front[ay*16:ay*16+ah,ax*16:ax*16+aw],art)
    grid[oy:oy+oh,ox:ox+ow]=(grid[oy:oy+oh,ox:ox+ow]&1023)|0x3000;attrs[oy:oy+oh,ox:ox+ow]=0x1000
    for cy in range(ah//16):
     for cx in range(aw//16):
      x,y=ax+cx,ay+cy
      if style=='mart':
       vt=Tileset(base,'violet_city','violet_city');vg=np.fromfile(base/'data/layouts/VioletCity/map.bin','<u2').reshape(72,80);v=int(vg[35+cy,19+cx]);mid=v&1023;flags=v&0xfc00;at=vt.attrs[mid>=512][mid%512]
      else:flags=0x3000|(0xc00 if cy>=1 else 0);at=0x1000 if cy else 0
      grid[y,x]=(grid[y,x]&1023)|flags;attrs[y,x]=at
    dx,dy=door
    if cg:grid[dy,dx]&=1023;attrs[dy,dx]=0x1069
    else:grid[dy,dx]|=0x3c00;attrs[dy,dx]=oldattrs[dy,dx]
   if cg:
    # Rebuild the terrain as its own layer. Extend each existing road branch
    # beneath the transparent entrance instead of cutting ground at the sprite
    # rectangle. The texture phase and shaded edge strips are the same HGSS
    # materials used by the surrounding Cherrygrove road.
    from PIL import ImageFilter
    material=ROOT/'gba/art/cherrygrove-synthesis/references/HGSS-direct'
    pal=np.array(t.pals[0][0],int)
    def material_indices(filename):
     rgb=np.array(Image.open(material/filename).convert('RGB'),int)
     return (((rgb[:,:,None,:]-pal[None,None,1:,:])**2).sum(-1).argmin(-1)+1).astype(np.uint8)
    grass_tex=material_indices('grass-source.png');path_tex=material_indices('path-source.png');edge_tex=material_indices('path-edge-source.png')
    edge_rgb=np.array(Image.open(material/'path-edge-source.png').convert('RGB'));inside=(edge_rgb[:,:,0]>edge_rgb[:,:,1])&(edge_rgb[:,:,0]>150);anchors=np.array([np.flatnonzero(row)[-1] for row in inside])
    path=(banks==0)&(original[:,:,0]>original[:,:,1])
    for style,art,(ax,ay),(ox,oy,ow,oh),(dx,dy),oldid in specs:
     path[oy*16:(oy+oh)*16,ox*16:(ox+ow)*16]=False
     path[ay*16:ay*16+art.shape[0],ax*16:ax*16+art.shape[1]]=False
    for _,_,_,_,(dx,dy),_ in specs:
     path[(dy-1)*16:(dy+2)*16,dx*16:(dx+2)*16]=True
     affected[dy:dy+3,dx-1:dx+3]=True
    coarse=np.repeat(np.repeat(path.reshape(h,16,w,16).mean(axis=(1,3))>=.5,16,0),16,1)
    smooth=np.array(Image.fromarray(coarse.astype(np.uint8)*255).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(2)))>=128
    yy,xx=np.indices(smooth.shape);idx=grass_tex[yy%32,xx%32].copy();idx[smooth]=path_tex[yy[smooth]%32,xx[smooth]%32]
    # Exact Euclidean distance within seven pixels is sufficient for the
    # five-pixel edge band and its one-pixel gradient; distant cells are unused.
    padded=np.pad(smooth,7,mode='edge');dist2=np.full(smooth.shape,64,np.uint8)
    for sy in range(-7,8):
     for sx in range(-7,8):
      d=sy*sy+sx*sx
      if not 0<d<=49:continue
      other=padded[7+sy:7+sy+smooth.shape[0],7+sx:7+sx+smooth.shape[1]];m=(other!=smooth)&(dist2>d);dist2[m]=d
    signed=np.sqrt(dist2.astype(float))*np.where(smooth,-1,1);ny,nx=np.gradient(signed);phase=(np.where(abs(nx)>=abs(ny),yy,xx)%8)//4*4;col=np.clip(anchors[phase]+np.rint(signed).astype(int),0,edge_tex.shape[1]-1);band=abs(signed)<=5;idx[band]=edge_tex[phase[band],col[band]]
    terrain=pal[idx].astype(np.uint8);mask=affected.repeat(16,0).repeat(16,1);background[mask,:3]=terrain[mask];background[mask,3]=255
   # Editable placement layers explicitly retain transparent building pixels.
   for style,art,(ax,ay),_,door,_ in specs:
    folder=OUT/'placements'/name;folder.mkdir(parents=True,exist_ok=True);hh,ww=art.shape[:2]
    Image.fromarray(background[ay*16:ay*16+hh,ax*16:ax*16+ww]).save(folder/f'{style}-ground.png')
    Image.fromarray(art).save(folder/f'{style}-building.png')
   final=background.copy();overlay(final,front)
   outside=~affected.repeat(16,0).repeat(16,1);assert np.array_equal(final[outside],original[outside])
   # Preserve every existing indexed layer outside the bounded footprints.
   raw=[np.array(v,np.uint8).reshape(8,8) for v in t.tiles[0]+t.tiles[1]];lookup={}
   for i,a in enumerate(raw):lookup.setdefault(a.tobytes(),i)
   # Use tuples to avoid confusing temporary tile IDs with hardware flip bits.
   cells={}
   def encode(a):
    colors=set(map(tuple,a[a[:,:,3]>0,:3])); candidates=[b for b,p in enumerate(pals) if colors<=set(p[1:])]
    if not colors:return (0,0,0)
    assert candidates,('no exact palette',name,colors)
    b=candidates[0];p={c:i for i,c in enumerate(pals[b]) if i and c!=(0,0,0)};ix=np.zeros((8,8),np.uint8)
    for yy,xx in np.argwhere(a[:,:,3]>0):ix[yy,xx]=p[tuple(a[yy,xx,:3])]
    for v,bits in [(ix,0),(ix[:,::-1],1024),(ix[::-1],2048),(ix[::-1,::-1],3072)]:
     if v.tobytes() in lookup:return (lookup[v.tobytes()],bits,b)
    idx=len(raw);raw.append(ix);lookup[ix.tobytes()]=idx;return (idx,0,b)
   for y,x in np.argwhere(affected):
    es=[None]*8
    for q in range(4):
     sl=np.s_[y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8];bg=background[sl].copy();fg=front[sl]
     es[q]=encode(bg);es[q+4]=encode(fg)
    cells[(int(x),int(y))]=es
   # Keep current metatile IDs for all unmodified cells and all door lookups.
   bs=list(t.blocks[0])+[(0,)*8]*(512-len(t.blocks[0]))+list(t.blocks[1]);ats=list(t.attrs[0])+[0]*(512-len(t.attrs[0]))+list(t.attrs[1]);used=set(map(int,(oldgrid&1023).ravel()))
   border=np.fromfile(base/f'data/layouts/{name}/border.bin','<u2');used|=set(map(int,border&1023))
   bs=[[(e&1023,e&3072,e>>12) for e in b] if i in used else [(0,0,0)]*8 for i,b in enumerate(bs)]
   reuse={};doorids={tuple(d):int(oldgrid[d[1],d[0]]&1023) for _,_,_,_,d,_ in specs}
   for (x,y),es in cells.items():
    key=(tuple(es),int(attrs[y,x]))
    if (x,y) in doorids:mid=doorids[x,y];bs[mid]=es;ats[mid]=int(attrs[y,x])
    elif key in reuse:mid=reuse[key]
    else:mid=len(bs);bs.append(es);ats.append(int(attrs[y,x]));reuse[key]=mid
    grid[y,x]=(grid[y,x]&0xfc00)|mid
   used=set(map(int,(grid&1023).ravel()))|set(map(int,border&1023))
   for i in range(len(bs)):
    if i not in used:bs[i]=[(0,0,0)]*8;ats[i]=0
   # Hidden pixels below an opaque upper tile can reuse an existing backing.
   # This changes no rendered pixel or sprite-layer attribute; animated cells
   # are excluded. Prefer already frequent patterns to reclaim native slots.
   from collections import Counter
   frequencies=Counter(v for b in bs for v in b if v[0])
   candidates={p:[v for v,n in frequencies.most_common() if v[2]==p and not(cg and v[0]<93)] for p in range(13)}
   def oriented(v):
    tid,f,p=v;a=raw[tid]
    if f&1024:a=a[:,::-1]
    if f&2048:a=a[::-1]
    return a
   for b in bs:
    for q in range(4):
     lower,upper=b[q],b[q+4]
     if not lower[0] or not upper[0] or (cg and (lower[0]<93 or upper[0]<93)):continue
     visible=oriented(upper)==0
     if not visible.any():b[q]=(0,0,0);continue
     current=oriented(lower)
     for candidate in candidates[lower[2]]:
      if np.array_equal(oriented(candidate)[visible],current[visible]):b[q]=candidate;break
   # Lossless label permutations share identical patterns across palette banks.
   # Bank 1 and reserved animated tiles retain their established indices.
   from violet_city.packing import Probe,optimize
   probe=Probe()
   for b in bs:
    for tid,flip,pal in b:
     if tid:probe.tile(pal,raw[tid])
   luts,optimization=optimize(probe,fixed=(1,) if cg else ())
   for bank,lut in luts.items():
    before=pals[bank].copy();after=before.copy()
    for i,j in enumerate(lut):after[int(j)]=before[i]
    pals[bank]=after
   converted={}
   for b in bs:
    for i,(tid,flip,pal) in enumerate(b):
     if not tid or (cg and tid<93):continue
     key=(tid,pal)
     if key not in converted:
      converted[key]=len(raw);raw.append(luts.get(pal,np.arange(16,dtype=np.uint8))[raw[tid]])
     b[i]=(converted[key],flip,pal)
   dump(OUT/f'{name}-palette-remap.json',{str(k):v.tolist() for k,v in luts.items()})
   # Original water IDs 1..92 and their pixels are reserved, including flips.
   reserved=93 if cg else 1;newtiles=raw[:reserved];dedup={raw[0].tobytes():0};mapping={i:(i,0) for i in range(reserved)}
   for b in bs:
    for tid,flip,pal in b:
     if tid not in mapping:
      a=raw[tid];found=None
      for v,bits in [(a,0),(a[:,::-1],1024),(a[::-1],2048),(a[::-1,::-1],3072)]:
       if v.tobytes() in dedup:found=(dedup[v.tobytes()],bits);break
      if found is None:found=(len(newtiles),0);dedup[a.tobytes()]=found[0];newtiles.append(a)
      mapping[tid]=found
   packed=[tuple(mapping[tid][0]|(flip^mapping[tid][1])|pal<<12 for tid,flip,pal in b) for b in bs]
   assert len(newtiles)<=1008,(name,'tile capacity',len(newtiles));assert len(bs)<=1024
   for part in range(2):
    folder=game/f'data/tilesets/{"secondary" if part else "primary"}/{newname}';folder.mkdir(parents=True,exist_ok=True);(folder/'palettes').mkdir(exist_ok=True)
    count=min(512,max(1,len(newtiles)-part*512));sheet=Image.new('P',(128,(count+15)//16*8));sheet.putpalette([v for i in range(256) for v in (i,i,i)])
    for i,a in enumerate(newtiles[part*512:part*512+512]):sheet.paste(Image.fromarray(a,'P'),(i%16*8,i//16*8))
    sheet.save(folder/'tiles.png',bits=4)
    pbs=packed[part*512:(part+1)*512] or [(0,)*8];pat=ats[part*512:(part+1)*512] or [0]
    (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in pbs));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(pat),*pat))
    for b in range(16):
     p=pals[b] if b<13 else t.pals[part][b];(folder/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in p)+'\n')
   if not cg:
    for part in ('primary','secondary'):
     for b in range(16):
      if (part=='primary' and b<6) or (part=='secondary' and 6<=b<13):continue
      rel=f'data/tilesets/{part}/violet_city/palettes/{b:02}.pal';(game/rel).write_bytes((base/rel).read_bytes())
   (game/f'data/layouts/{name}/map.bin').write_bytes(grid.astype('<u2').tobytes())
   check=np.array(Tileset(game,newname,newname).map_image(grid.ravel().tolist(),w));assert np.array_equal(check,final[:,:,:3]),(name,'pixel equality')
   Image.fromarray(check).save(E/f'{name}.png');Image.fromarray(original[:,:,:3]).save(E/f'{name}-before.png')
   np.save(OUT/f'{name}-affected.npy',affected)
   reports[name]={'tile_slots':len(newtiles),'metatiles':len(bs),'unchanged_pixels_outside_footprints':True,'exact_native_pixel_roundtrip':True,'door_tiles':[list(d) for d in doorids],'collision_changes_xy':np.argwhere((grid&0xfc00)!=(oldgrid&0xfc00))[:,::-1].tolist(),'source_assets_unchanged':True}
  # Append private Cherrygrove declarations. Existing primary/secondary and all
  # maps using them stay untouched; the existing sea callback remains shared.
  for filename in ('headers.h','graphics.h','metatiles.h'):
   path=game/'src/data/tilesets'/filename;s=(base/'src/data/tilesets'/filename).read_text();chunks=[]
   pattern=r'(?:const (?:struct Tileset|u16|u32) g[^\n]*Cherrygrove[^;]*?;)' if filename!='headers.h' else r'const struct Tileset gTileset_Cherrygrove(?:Primary)? = .*?;'
   for m in re.finditer(pattern,s,re.S):
    chunk=m.group();chunk=chunk.replace('Cherrygrove','JohtoCherrygrove').replace('/cherrygrove/','/johto_cherrygrove/').replace('InitTilesetAnim_JohtoCherrygrovePrimary','InitTilesetAnim_CherrygrovePrimary');chunks.append(chunk)
   assert chunks,(filename,'declarations');path.write_text(s+'\n// Approved shared Johto service buildings; private Cherrygrove pair.\n'+'\n'.join(chunks)+'\n')
  layouts=json.loads((base/'data/layouts/layouts.json').read_text())
  for l in layouts['layouts']:
   if l['name']=='CherrygroveCity_Layout':l['primary_tileset']='gTileset_JohtoCherrygrovePrimary';l['secondary_tileset']='gTileset_JohtoCherrygrove'
  dump(game/'data/layouts/layouts.json',layouts)
  # Other Cherrygrove door graphics still have identical palettes and IDs.
  fd=(base/'src/field_door.c').read_text();fd=fd.replace('extern const struct Tileset gTileset_Cherrygrove;','extern const struct Tileset gTileset_Cherrygrove;\nextern const struct Tileset gTileset_JohtoCherrygrove;')
  rows=[line for line in fd.splitlines() if '.tileset=&gTileset_Cherrygrove,' in line]
  assert len(rows)==7
  fd=fd.replace(rows[0], '\n'.join(line.replace('&gTileset_Cherrygrove,','&gTileset_JohtoCherrygrove,').replace('sRestartDoor','sSharedDoor') for line in rows)+'\n'+rows[0])
  (game/'src/field_door.c').write_text(fd)
  dump(E/'structure.json',{'base_engine_commit':BASE,'maps':reports})
 print(json.dumps(reports,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
