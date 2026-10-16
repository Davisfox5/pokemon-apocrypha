"""Native R02 cleanup from HGSS geometry, reviewed by cell and quadrant.
Writes a separate review directory; --install writes only the named engine worktree.
"""
from pathlib import Path
import argparse,json,sys,struct,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.trees import rgba,sha,indexed
from johto_common import r02_pilot as old
from route36.gate_surround.build import decode,over
from claude_cherrygrove import ground
from tiles import Tileset,palette
P=ROOT/'gba/art/johto-common/rocks/r02-refined';REF=old.REF;BASE=old.BASE
FONT='/System/Library/Fonts/Supplemental/Arial.ttf';BOX=(160,288,352,416)

def save(a,p):p.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(a).save(p)
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def extract(donor):
 sys.path[:0]=[str(ROOT/'tools/hoennconv'),str(ROOT/'tools/regionport')]
 import narc
 from mdlview import Model
 from nsbtx import Tex0
 blob=narc.load(donor/'files/a/0/6/5')[47];m=Model(blob[blob.index(b'BMD0'):]);textureblob=narc.load(donor/'files/a/0/4/4')[6];t=Tex0(textureblob)
 faces=[];seen=set();textures={}
 for mat,f in m.faces():
  name=m.tex_name(mat);v=np.array([p for p,u in f])
  if name not in ['wall01_d','wall01_g','slope'] or v[:,0].min()<-14.01 or v[:,0].max()>-12.99:continue
  key=(name,tuple(f))
  if key in seen:continue
  seen.add(key);faces.append(dict(texture=name,vertices=v.tolist(),uv=[u for p,u in f]))
  if name not in textures:
   pal=next(p for p in t.palettes if p.name==m.mat_pal[mat]);t.pal_for=lambda _,p=pal:p
   a=t.render(next(e for e in t.textures if e.name==name));a.save(P/'source'/(name+'.png'));textures[name]=m.mat_pal[mat]
 dump(P/'source/geometry.json',dict(faces=faces,palettes=textures,model_member=47,texture_member=6,
  donor_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=donor,text=True).strip(),
  model_sha256=hashlib.sha256(blob).hexdigest(),texture_sha256=hashlib.sha256(textureblob).hexdigest(),
  selection='West Route 36 cliff and stair faces x=-14..-13; props/trees/ground excluded.'))

def render():
 model=json.loads((P/'source/geometry.json').read_text());tex={n:rgba(P/'source'/(n+'.png')) for n in model['palettes']}
 out=np.zeros((224,16,4),np.uint8);depth=np.full((224,16),-1e9);material=np.zeros((224,16),np.uint8)
 for f in model['faces']:
  ps=np.array(f['vertices']);uv=np.array(f['uv']);screen=np.column_stack(((ps[:,0]+14)*16,(ps[:,2]-1)*16-(ps[:,1]-1)*12));dep=ps[:,1]+ps[:,2];a=tex[f['texture']]
  for j in range(1,len(ps)-1):
   ids=[0,j,j+1];v=screen[ids];matrix=np.vstack((v.T,np.ones(3)))
   if abs(np.linalg.det(matrix))<1e-8:continue
   inv=np.linalg.inv(matrix)
   for y in range(max(0,int(v[:,1].min())),min(224,int(v[:,1].max())+1)):
    for x in range(max(0,int(v[:,0].min())),min(16,int(v[:,0].max())+1)):
     w=inv@np.array([x+.5,y+.5,1]);z=w@dep[ids]
     if w.min()<-1e-7 or z<depth[y,x]:continue
     u,vv=w@uv[ids];c=a[int(np.floor(vv))%a.shape[0],int(np.floor(u))%a.shape[1]].copy()
     # Exact source texture classes: green bank entries are terrain backing,
     # never rock. Keep this material mask separate from the face geometry.
     terrain=f['texture']!='slope' and int(c[1])>int(c[0])+15
     c[:3]=(np.round(c[:3].astype(float)*.8/8)*8).clip(0,248).astype(np.uint8)
     out[y,x]=c;depth[y,x]=z;material[y,x]=1 if terrain else 3 if f['texture']=='slope' else 2
 out[material==1]=0
 save(out,P/'source/projected-wall-and-stairs.png')
 face=out[32:64].copy();assert np.array_equal(out[32:48],out[64:80]),'source repeat phase'
 # Fit the complete rendered flight and BOTH shoulders to the existing 4-cell
 # envelope. No color-key crop or reconstruction from tree-obscured screenshots.
 flight=np.array(Image.fromarray(out[92:178]).resize((16,64),Image.Resampling.NEAREST))
 # One shared source palette; no per-quadrant quantization or invented color.
 colors=np.unique(np.concatenate([face.reshape(-1,4),flight.reshape(-1,4)]),axis=0)
 print('foreground colors',sum(c[3]>0 for c in colors))
 strip=np.zeros((160,16,4),np.uint8)
 for y in range(80):strip[y]=face[(y+12)%32]
 # The source face turns away beneath foliage at its last four rows. The
 # receiving wall continues straight: use the compatible complete face phase.
 costs=[np.abs(face[i].astype(int)-flight[59].astype(int)).sum() for i in range(32)]
 phase=int(np.argmin(costs))
 for y in range(4):flight[60+y]=face[(phase+y)%32]
 over(strip,flight,0,80)
 for y in range(16):strip[144+y]=face[(phase+4+y)%32]
 parts={f'face-{i}':face[i*16:(i+1)*16].copy() for i in range(2)}
 parts.update({f'stair-{i}':flight[i*16:(i+1)*16].copy() for i in range(4)})
 # Source treads and structural walls have distinct palettes if needed; their
 # full RGBA masters remain lossless. Native palettes are assigned per 8px tile.
 for name,a in parts.items():
  a[a[...,3]==0]=0;save(a,P/'source'/(name+'.png'))
  if len(np.unique(a[a[...,3]>0,:3],axis=0))<=15:indexed(a,P/'source'/(name+'.idx.png'))
 save(strip,P/'source/assembled-section.png')
 return strip,parts

def append_native(game,layers,affected,grid,attrs,reusable_ids=None,reusable_tile_ids=None):
 """Append tiles/metatiles and only unused palettes; preserve every existing ID."""
 t=Tileset(game,'johto_route36','johto_route36');folders=[game/'data/tilesets'/k/'johto_route36' for k in ['primary','secondary']]
 tilelist=[np.array(v,np.uint8).reshape(8,8) for v in t.tiles[0]]+[np.array(v,np.uint8).reshape(8,8) for v in t.tiles[1]]
 palettes=[t.pals[i>=6][i] for i in range(13)];used={v>>12 for b in t.blocks[0]+t.blocks[1] for v in b if v&1023};newbanks={};tilecache={a.tobytes():i for i,a in enumerate(tilelist)}
 free_ids=list(reusable_ids or []);reused_ids=[];free_tiles=list(reusable_tile_ids or []);reused_tiles=[]
 blocks=list(t.blocks[0]);attrib=list(t.attrs[0]);cache={(b,a):i for i,(b,a) in enumerate(zip(blocks,attrib))};newgrid=grid.copy()
 def tile(a):
  m=a[...,3]>0
  if not m.any():return 0
  colors=set(map(tuple,a[m,:3].tolist()));assert len(colors)<=15,('hardware quarter colors',len(colors))
  bank=next((i for i in sorted(used) if colors<=set(map(tuple,palettes[i][1:]))),None)
  if bank is None:
   bank=next((i for i,c in newbanks.items() if len(c|colors)<=15),None)
   if bank is None:bank=next(i for i in range(13) if i not in used);newbanks[bank]=set();used.add(bank)
   # Append colors to existing slots of this new bank; never change prior slots.
   for c in sorted(colors-newbanks[bank]):palettes[bank][len(newbanks[bank])+1]=c;newbanks[bank].add(c)
  colorids={tuple(c):i for i,c in enumerate(palettes[bank]) if i};ix=np.zeros((8,8),np.uint8)
  for c in colors:ix[m&np.all(a[:,:,:3]==c,axis=2)]=colorids[c]
  for vf in [0,1]:
   for hf in [0,1]:
    b=(ix[::-1] if vf else ix);b=b[:,::-1] if hf else b;k=b.tobytes()
    if k in tilecache:
     tid=tilecache[k]
     if tid in free_tiles:free_tiles.remove(tid)
     return tid|hf<<10|vf<<11|bank<<12
  if free_tiles:
   tid=free_tiles.pop(0);oldkey=tilelist[tid].tobytes()
   if tilecache.get(oldkey)==tid:tilecache.pop(oldkey)
   tilelist[tid]=ix;reused_tiles.append(tid)
  else:tid=len(tilelist);assert tid<1008;tilelist.append(ix)
  tilecache[ix.tobytes()]=tid;return tid|bank<<12
 for y,x in np.argwhere(affected.reshape(32,16,82,16).any((1,3))):
  entries=[]
  for layer in layers:
   for q in range(4):entries.append(tile(layer[y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8]))
  key=(tuple(entries),int(attrs[y,x]));mid=cache.get(key)
  if mid is None:
   if free_ids:
    mid=free_ids.pop(0);oldkey=(blocks[mid],attrib[mid])
    if cache.get(oldkey)==mid:cache.pop(oldkey)
    blocks[mid]=key[0];attrib[mid]=key[1];reused_ids.append(mid)
   else:mid=len(blocks);assert mid<512;blocks.append(key[0]);attrib.append(key[1])
   cache[key]=mid
  elif mid in free_ids:free_ids.remove(mid)
  newgrid[y,x]=int(grid[y,x]&0xfc00)|mid
 for i,folder in enumerate(folders):
  tiles=tilelist[:512] if i==0 else tilelist[512:];h=max(8,(len(tiles)+15)//16*8);a=np.zeros((h,128),np.uint8)
  for j,v in enumerate(tiles):a[j//16*8:j//16*8+8,j%16*8:j%16*8+8]=v
  im=Image.fromarray(a).convert('P');im.putpalette(Image.open(folder/'tiles.png').getpalette());im.save(folder/'tiles.png')
  for bank in newbanks:
   if (bank>=6)==bool(i):(folder/'palettes'/f'{bank:02d}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in palettes[bank])+'\n')
 folders[0].joinpath('metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks));folders[0].joinpath('metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrib),*attrib));newgrid.astype('<u2').tofile(game/'data/layouts/JohtoRoute36/map.bin')
 assert np.array_equal(grid&0xfc00,newgrid&0xfc00)
 native=Tileset(game,'johto_route36','johto_route36');image=np.array(native.map_image(newgrid.ravel().tolist(),82).convert('RGBA'));target=layers[0].copy();over(target,layers[1]);assert np.array_equal(image[:,:,:3],target[:,:,:3]),'native mismatch'
 save(image,P/'review/native-full.png')
 return dict(reused_unreferenced_tiles=reused_tiles,reused_unreferenced_metatiles=reused_ids,tile_slots=len(tilelist),appended_tiles=len(tilelist)-sum(len(v) for v in t.tiles),appended_metatiles=len(blocks)-len(t.blocks[0]),new_palette_banks=sorted(newbanks),native_pixel_errors=0,collision_elevation_changes=0)

def main(game,donor,install):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()==BASE
 assert not subprocess.check_output(['git','status','--porcelain','--','data/layouts/JohtoRoute36','data/tilesets/primary/johto_route36','data/tilesets/secondary/johto_route36'],cwd=game,text=True).strip(), 'Preserve existing native edits; reproduce on a clean baseline.'
 for n in ['source','review','evidence']:(P/n).mkdir(parents=True,exist_ok=True)
 extract(donor);strip,parts=render();route=ROOT/'gba/art/route36/source'
 t=Tileset(game,'johto_route36','johto_route36');grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);layers,attrs=decode(t,grid);before=layers[0].copy();over(before,layers[1]);save(before,P/'review/before-full.png')
 plan=np.load(route/'plan.npy');cells=np.full(plan.shape,ground.GRASS,np.int8);cells[np.isin(plan,['P','S'])]=ground.PATH;cells[19:22,53:75]=ground.PATH
 # Destination underlay: original accepted texture cores, 2px local edge ramp.
 # Do not nearest-match whole 8x8 ground tiles: that was introducing scallops.
 profiles=ground.PROFILES[(ground.GRASS,ground.PATH)];ground.PROFILES[(ground.GRASS,ground.PATH)]=([(88,176,136),(96,192,144)],[(184,168,128),(216,184,128)])
 wave=ground.WAVE;ground.WAVE=[int(np.sign(v)) for v in wave]
 terrain,_=ground.paint(cells,wobble=True);ground.WAVE=wave;ground.PROFILES[(ground.GRASS,ground.PATH)]=profiles
 # Keep the exact existing ground ramp across the preview boundary. Match
 # pixels within each material, never substitute differently shaped 8px tiles.
 gp=np.array(Tileset(game,'claude_route30','cherrygrove').pals[0][0][1:],int)
 for color in np.unique(terrain[:,:,:3].reshape(-1,3),axis=0):
  green=int(color[1])>int(color[0])+10
  choices=gp[(gp[:,1]>gp[:,0]+10)==green]
  chosen=choices[np.square(choices-color.astype(int)).sum(1).argmin()]
  terrain[np.all(terrain[:,:,:3]==color,axis=2),:3]=chosen
 # Replace only the registered rock/stair column plus the adjoining ground band.
 # Original foreground scenery is identified from decoded layers and exact
 # ground bank colors, then retained. No object is removed from the map.
 x,y,x1,y1=BOX;region=np.s_[y:y1,x:x1];affected=np.zeros(before.shape[:2],bool);affected[region]=True
 groundcolors=set(map(tuple,Tileset(game,'claude_route30','cherrygrove').pals[0][0][1:]));bgmask=np.zeros(before.shape[:2],bool)
 for c in groundcolors:bgmask|=np.all(before[:,:,:3]==c,axis=2)
 for a in layers:
  for c in groundcolors:
   m=affected&np.all(a[:,:,:3]==c,axis=2)&(a[:,:,3]>0);a[m,:3]=terrain[m,:3]
 trees=np.zeros_like(before);tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png')
 for tx,ty in json.loads((route/'features.json').read_text())['trees']:
  if tx*16<240 and tx*16+32>224 and ty*16<416 and ty*16+48>288:over(trees,tree,tx*16,ty*16)
 rock=np.zeros_like(before);over(rock,strip,224,256)
 for yy in range(288,416,8):
  for xx in [224,232]:
   sl=np.s_[yy:yy+8,xx:xx+8];bg=terrain[sl].copy();over(bg,rock[sl]);fg=trees[sl].copy();bg[fg[:,:,3]>0]=0
   if not fg[:,:,3].any():bg=terrain[sl].copy();fg=rock[sl].copy();bg[fg[:,:,3]>0]=0
   for a in [bg,fg]:assert len(np.unique(a[a[:,:,3]>0,:3],axis=0))<=15,(xx,yy,'palette overflow')
   layers[0][sl]=bg;layers[1][sl]=fg
 target=layers[0].copy();over(target,layers[1]);assert np.array_equal(target[~affected],before[~affected]);save(target,P/'review/native-target.png')
 sample=target[region];assembly=terrain[region].copy();over(assembly,rock[region]);ref=rgba(REF)[region];prior=rgba(ROOT/'gba/art/johto-common/rocks/r02-pilot/review/map-crop.png')
 for name,a in [('original',ref),('before',prior),('rebuilt',assembly),('map',sample)]:save(a,P/'review'/(name+'.png'))
 z=3;sheet=Image.new('RGB',(1824,490),'#202d37');d=ImageDraw.Draw(sheet)
 for i,(title,a,note) in enumerate([('ORIGINAL HGSS / R02',ref,'Reference: original contours and material'),('REBUILT / COMPLETE GEOMETRY',assembly,'Original rock and stair textures; independent ground'),('ON ROUTE 36',sample,'Existing tree footprints and movement grid retained')]):
  xx=i*608+16;d.text((xx,15),title,font=ImageFont.truetype(FONT,21),fill='white');sheet.paste(Image.fromarray(a).convert('RGB').resize((576,384),Image.Resampling.NEAREST),(xx,52));d.text((xx,451),note,font=ImageFont.truetype(FONT,15),fill='#c5d3dd')
 sheet.save(P/'review/comparison.png')
 # Grid and cell ledger cover EVERY square shown, including unchanged scenery.
 board=Image.new('RGB',(1220,640),'#202d37');d=ImageDraw.Draw(board)
 for col,(label,a) in enumerate([('HGSS original',ref),('Corrected native',sample)]):
  xx=col*608+32;yy=46;d.text((xx,10),label,font=ImageFont.truetype(FONT,20),fill='white');board.paste(Image.fromarray(a).convert('RGB').resize((576,384),Image.Resampling.NEAREST),(xx,yy))
  for c in range(13):d.line((xx+c*48,yy,xx+c*48,yy+384),fill='#25313a')
  for r in range(9):d.line((xx,yy+r*48,xx+576,yy+r*48),fill='#25313a')
  for c in range(12):d.text((xx+c*48+15,yy+388),str(c+10),fill='white')
  for r in range(8):d.text((xx-22,yy+r*48+18),str(r+18),fill='white')
 d.multiline_text((32,476),'Columns 10-21 / rows 18-25. 16x16 cells; 8x8 quadrants reviewed separately.\nSource reference is a rendered projection; native topology stays unchanged.\nCliff source geometry x=-14..-13 is placed in native column 14.\nHGSS foliage occlusion is excluded from source-terrain claims.',font=ImageFont.truetype(FONT,19),fill='white',spacing=8);board.save(P/'review/grid.png')
 ledger=[]
 for cy in range(18,26):
  for cx in range(10,22):
   a=before[cy*16:cy*16+16,cx*16:cx*16+16];b=target[cy*16:cy*16+16,cx*16:cx*16+16]
   label='west cliff face' if cx==14 and cy not in [21,22,23,24] else 'stair and rock shoulder' if cx==14 else {'P':'dirt approach','G':'tall grass','T':'tree footprint','.':'ordinary grass'}.get(str(plan[cy,cx]),'terrain')
   ledger.append(dict(x=cx,y=cy,material=label,source_reference_box=[cx*16,cy*16,cx*16+16,cy*16+16],source_occlusion=str(plan[cy,cx])=='T',native_collision=int(grid[cy,cx]>>10&3),native_elevation=int(grid[cy,cx]>>12),behavior=int(attrs[cy,cx]&255),changed_pixels=int(np.any(a!=b,2).sum()),review='pending visual inspection',quadrants=[dict(x=cx*2+qx,y=cy*2+qy,colors=[len(np.unique(layer[cy*16+qy*8:cy*16+qy*8+8,cx*16+qx*8:cx*16+qx*8+8][layer[cy*16+qy*8:cy*16+qy*8+8,cx*16+qx*8:cx*16+qx*8+8,3]>0,:3],axis=0)) for layer in layers]) for qy in range(2) for qx in range(2)]))
 dump(P/'evidence/cell-review.json',ledger)
 report=dict(base_engine=BASE,reference_sha256=sha(REF),outside_review_rectangle_changes=0,map_cells_reviewed=len(ledger),quadrants_reviewed=len(ledger)*4,installed=install,runtime_tested=False)
 if install:report.update(append_native(game,layers,affected,grid,attrs))
 dump(P/'evidence/structure.json',report);print(json.dumps(report))

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--engine',type=Path,required=True);a.add_argument('--donor',type=Path,required=True);a.add_argument('--install',action='store_true');v=a.parse_args();main(v.engine,v.donor,v.install)
