"""Assemble an editable terrain-only Olivine from reusable 16px metatiles.
The original HGSS overview defines connected relative terrain levels. No whole-map
image is sampled or sliced into map tiles. Native map IDs/connections stay fixed.
Run on the named baseline, or use --preview to inspect without native mutation.
"""
from pathlib import Path
import sys,json,struct,hashlib,subprocess,csv
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/olivine-city/source';A=S/'base-terrain';E=S.parent/'evidence';O=E/'base-terrain';D=A/'textures';W,H=65,54
BASE='c1363f3f147e4b61028da9f8a86f9ababda10280'
preview='--preview' in sys.argv
if not preview:
 assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
 assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True),'Use a clean isolated baseline; preserve native edits.'
# HGSS surface topology and explicit high/low-side native cliff grammar.
from foundation_elevation import build,cliffs,REGIONS,SURFACES
sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
mat,levels=build();wall,cliff_ledger=cliffs(mat,levels)
geometry=dict(surfaces=SURFACES,raised_regions=REGIONS,cliffs=cliff_ledger,stairs=[],props=[],registration=dict(cells=[W,H],tile_pixels=16,reference='source/hgss-reference.png',method='HGSS overview trace; connected relative levels; 16px grid adaptation, occluded returns inferred. Not extracted DS heights.'))
geometry['rocks']=[[5,40],[5,42],[0,44],[2,44],[4,45],[6,45],[8,45],[10,46],[12,46],[14,47],[16,47],[29,47],[31,46],[33,45],[35,45],[37,45],[39,44],[41,44],[43,44],[45,43],[47,43],[49,43],[51,43],[53,43],[55,42],[57,42],[59,42],[61,42],[63,41],[62,20],[63,23],[62,25],[63,27],[62,29],[63,31],[62,33],[63,35],[62,37],[63,39]]
(A/'geometry.json').write_text(json.dumps(geometry,indent=2)+'\n')
textures={n:Image.open(D/(n+'.png')).convert('RGB') for n in ['grass','paving','water','dock','sand','shore-rock']}
donor=Tileset(G)
# Original Gen 3 silhouette, cap, shading and orientation retained exactly;
# six donor rock colors are mapped once to the established warm Johto ramp.
remap={(131,131,139):(104,72,56),(98,65,82):(104,72,56),(131,90,90):(128,88,64),(156,115,115):(160,112,80),(189,148,139):(192,144,96),(222,180,164):(216,176,120)}
def donor_rock(mid):
 ar=np.array(donor.render(mid));out=np.zeros((16,16,4),np.uint8)
 for rgb,color in remap.items():
  m=np.all(ar==rgb,2);out[m,:3]=color;out[m,3]=255
 assert np.any(out[...,3]),mid
 return Image.fromarray(out)
rockdonors={mid:donor_rock(mid) for mid in set(v[0] for v in wall.values())|{0x71}}
textures['rock-palette']=Image.fromarray(np.array(list(remap.values()),np.uint8).reshape(1,-1,3))
# Normal material cores repeat with a stable phase. Canonical edge masks below
# become reusable metatiles; no world image is used to look up a pixel.
def core(n,x,y):
 t=textures['grass' if n=='rock outcrop' else n];return t.crop(((x*16)%t.width,(y*16)%t.height,(x*16)%t.width+16,(y*16)%t.height+16)).copy()
rock=np.array(textures['shore-rock'].resize((32,32),Image.Resampling.LANCZOS));rockmask=(rock[...,0].astype(int)>rock[...,2].astype(int)-12)&(rock[...,0]>75)&(rock[...,2]<225);from scipy.ndimage import label, binary_fill_holes
labs,n=label(rockmask);sizes=np.bincount(labs.ravel());sizes[0]=0;rockmask=binary_fill_holes(labs==sizes.argmax());rockrgba=np.dstack((rock,rockmask.astype(np.uint8)*255));rockimg=Image.fromarray(rockrgba)
rockcells={}
for x,y in geometry['rocks']:
 footprint=[(x+dx,y+dy) for dy in range(2) for dx in range(2)]
 if not all(0<=xx<W and 0<=yy<H and mat[yy,xx]=='water' and (xx,yy) not in wall and (xx,yy) not in rockcells for xx,yy in footprint):continue
 for dy in range(2):
  for dx in range(2):
   if x+dx<W and y+dy<H and mat[y+dy,x+dx]=='water':rockcells[x+dx,y+dy]=rockimg.crop((dx*16,dy*16,dx*16+16,dy*16+16))
rawtiles=[];labels=[];positions=[];lookup={};indices=np.zeros((H,W),np.uint16);solid=np.zeros((H,W),bool);physical=mat.copy()
for y,x in np.ndindex(H,W):
 name=str(mat[y,x]);im=core(name,x,y);d=ImageDraw.Draw(im)
 # Lawn/paving curbs follow actual tile neighbors. Their tangent and corner
 # shapes are individual modules; fully clear floor stays fully clear.
 if name=='grass':
  neighbors={(dx,dy):0<=x+dx<W and 0<=y+dy<H and mat[y+dy,x+dx]=='paving' for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]}
  for (dx,dy),yes in neighbors.items():
   if yes:
    line=(0,0,15,0) if dy==-1 else (0,15,15,15) if dy==1 else (0,0,0,15) if dx==-1 else (15,0,15,15);d.line(line,fill=(80,128,104),width=2)
 if name=='dock':
  for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]:
   if 0<=x+dx<W and 0<=y+dy<H and mat[y+dy,x+dx]=='water':
    line=(0,0,15,0) if dy==-1 else (0,15,15,15) if dy==1 else (0,0,0,15) if dx==-1 else (15,0,15,15);d.line(line,fill=(112,112,88),width=2)
 solid[y,x]=name=='water'
 if name=='rock outcrop':im=donor_rock(0x71).convert('RGB');solid[y,x]=True
 if (x,y) in wall:
  mid,under=wall[x,y];im=core(under,x,y).convert('RGBA');im.alpha_composite(rockdonors[mid]);im=im.convert('RGB')
  physical[y,x]='cliff';solid[y,x]=True
 if (x,y) in rockcells and (x,y) not in wall:
  im=im.convert('RGBA');im.alpha_composite(rockcells[x,y]);im=im.convert('RGB');physical[y,x]='shore rock';solid[y,x]=True
 # No route connections yet: invisible edge guard only on the outermost cells.
 if x in [0,W-1] or y in [0,H-1]:solid[y,x]=True
 key=im.tobytes()
 if key not in lookup:lookup[key]=len(rawtiles);rawtiles.append(np.array(im));labels.append(str(physical[y,x]));positions.append([x,y])
 indices[y,x]=lookup[key]
# Explicit family palettes, 15 opaque colors plus transparent index 0.
families=[['grass'],['paving'],['water'],['dock'],['sand'],['rock-palette'],['grass','paving'],['grass','rock-palette'],['paving','rock-palette'],['sand','rock-palette'],['water','rock-palette'],['dock','water'],['shore-rock','water']]
pals=[]
for names in families:
 pixels=np.concatenate([np.array(textures[n]).reshape(-1,3) for n in names]);pal=Image.fromarray(pixels.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pals.append(np.resize(np.array(pal.getpalette(),np.uint8),45).reshape(15,3)&248)
# Shared rock colors across every mixed bank: no quadrant-dependent cliff colors.
rock_colors=np.array(list(dict.fromkeys(remap.values())),np.uint8)
for bank,ground in [(5,None),(7,'grass'),(8,'paving'),(9,'sand'),(10,'water')]:
 if ground:
  pp=Image.fromarray(np.array(textures[ground])).quantize(colors=15-len(rock_colors),method=Image.Quantize.MEDIANCUT);gp=np.array(pp.getpalette()[:3*(15-len(rock_colors))],np.uint8).reshape(-1,3)&248
 else:gp=np.tile(rock_colors,(3,1))[:15-len(rock_colors)]
 pals[bank]=np.concatenate([rock_colors,gp])
# The water ramp is shared exactly with mixed rock quadrants, so isolated
# rock tiles cannot create rectangular water-color patches around their alpha.
wp=Image.fromarray(np.array(textures['water'])).quantize(colors=8,method=Image.Quantize.MEDIANCUT);wc=np.array(wp.getpalette()[:24],np.uint8).reshape(8,3)&248
rp=Image.fromarray(rock[rockmask].reshape(-1,1,3)).quantize(colors=7,method=Image.Quantize.MEDIANCUT);rc=np.array(rp.getpalette()[:21],np.uint8).reshape(7,3)&248
pals[2]=np.concatenate([wc,wc[:7]]);pals[12]=np.concatenate([wc,rc])
glyphs=[np.zeros((8,8),np.uint8)];glookup={glyphs[0].tobytes():0};blocks=[];rendered=[]
for im,material in zip(rawtiles,labels):
 es=[];nat=np.zeros_like(im)
 for q in range(4):
  yy,xx=q//2*8,q%2*8;rgb=im[yy:yy+8,xx:xx+8];best=None
  for b,pal in enumerate(pals):
   if material in ['cliff','rock outcrop'] and b not in [5,7,8,9,10]:continue
   if material=='water' and b!=2:continue
   if material=='shore rock' and b!=12:continue
   dist=((rgb.astype(np.int32)[:,:,None]-pal.astype(np.int32)[None,None])**2).sum(3);ii=dist.argmin(2);error=np.take_along_axis(dist,ii[...,None],2).sum()
   if best is None or error<best[0]:best=(error,b,ii)
  _,bank,ii=best;pix=(ii+1).astype(np.uint8);nat[yy:yy+8,xx:xx+8]=pals[bank][ii];key=pix.tobytes()
  if key not in glookup:
   tid=len(glyphs);glyphs.append(pix)
   for h in range(2):
    for v in range(2):glookup.setdefault(pix[::-1 if v else 1,::-1 if h else 1].tobytes(),tid|h<<10|v<<11)
  es.append(glookup[key]|bank<<12)
 blocks.append(es+[0]*4);rendered.append(nat)
print(dict(metatiles=len(blocks),glyphs=len(glyphs),open_cells=int((~solid).sum())))
assert len(blocks)<=512 and len(glyphs)<=1008
native=np.zeros((H*16,W*16,3),np.uint8)
for y,x in np.ndindex(H,W):native[y*16:y*16+16,x*16:x*16+16]=rendered[indices[y,x]]
Image.fromarray(native).save(O/'native-map.png');Image.fromarray(native).save(A/'assembled-preview.png');np.save(A/'metatile-map.npy',indices);np.save(A/'solid.npy',solid);np.save(A/'material.npy',physical);np.save(A/'cliff-level.npy',levels);np.save(A/'height.npy',levels)
# Publish a concrete metatile catalog, including usage count and sample location.
counts=np.bincount(indices.ravel(),minlength=len(blocks));sheet=Image.new('RGB',(16*48,((len(blocks)+15)//16)*48),'#182028');d=ImageDraw.Draw(sheet)
with (A/'metatile-catalog.csv').open('w') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['id','material','uses','sample_x','sample_y'])
 for i,tile in enumerate(rendered):
  x=i%16*48;y=i//16*48;sheet.paste(Image.fromarray(tile).resize((32,32),Image.Resampling.NEAREST),(x,y));d.text((x,y+32),str(i),fill='white');w.writerow([i,labels[i],int(counts[i]),*positions[i]])
sheet.save(O/'metatile-catalog.png')
if preview:raise SystemExit(0)
sections=json.loads((E/'sections.json').read_text())
for section in sections:
 n=section['name'];x,y,x1,y1=section['box'];old=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x)
 elev=((levels[y:y1,x:x1].astype(np.int16)*2+3).astype(np.uint16)<<12)
 grid=elev|indices[y:y1,x:x1]|np.where(solid[y:y1,x:x1],0xc00,0).astype(np.uint16);grid.astype('<u2').tofile(G/f'data/layouts/{n}/map.bin')
 np.full((2,2),int(grid[0,0])|0xc00,'<u2').tofile(G/f'data/layouts/{n}/border.bin')
 for part in range(2):
  folder=G/f'data/tilesets/{"secondary" if part else "primary"}/{n.lower()}';start=part*512;count=512 if part==0 else max(1,len(glyphs)-512);im=Image.new('P',(128,((count+15)//16)*8));im.putpalette([c for i in range(256) for c in (i*17%256,)*3])
  for i in range(count):
   if start+i<len(glyphs):im.paste(Image.fromarray(glyphs[start+i]).convert('P'),(i%16*8,i//16*8))
  im.save(folder/'tiles.png',bits=4);(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*(blocks[i] if i<len(blocks) else [0]*8)) for i in range(start,start+512)));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*([0x1000]*512)))
  for bank,pal in enumerate(pals):
   colors=[[0,0,0]]+pal.tolist();(folder/'palettes'/f'{bank:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
# Current source is the tile-authored terrain. Historical object masters remain.
Image.fromarray(native).save(S/'native-ground.png');Image.new('RGBA',(W*16,H*16)).save(S/'shared-foreground.png');np.save(S/'solid.npy',solid);np.save(S/'above.npy',np.zeros((H,W),bool));np.save(S/'material.npy',physical);Image.fromarray(native).save(E/'native-map.png');(S/'palettes.json').write_text(json.dumps([p.tolist() for p in pals])+'\n')
(A/'build.json').write_text(json.dumps(dict(baseline=BASE,cells=W*H,metatiles=len(blocks),glyphs=len(glyphs),reused_cells=int((counts[indices]>1).sum()),unique_cell_metatiles=int((counts==1).sum()),whole_map_image_import=False,stairs=0,foreground_objects=0,preserved_map_ids=list(range(63,76))),indent=2)+'\n')
