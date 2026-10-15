"""Guarded native packing: exact foreground rocks, doors, boulders and shores first.
Reproducible authoring provenance for owner-authorized cave corrections; never
replay over changed committed layouts or editable assets.
"""
from pathlib import Path
from collections import Counter
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
from config import FLOORS
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);key=sys.argv[2];c=FLOORS[key];W,H=c['size'];S=ROOT/f'gba/art/union-cave-{key}/source';E=S.parent/'evidence'
def digest(p):
 b=p.read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if p.suffix=='.pal' else b).hexdigest()
manifest=S/'generated-files.json'
if (G/'data/tilesets/primary'/c['set']).exists():
 assert manifest.exists(),'Preserve existing cave source without a matching manifest'
 changed=[p for p,h in json.loads(manifest.read_text()).items() if Path(p).name not in ['header.inc','events.inc','connections.inc'] and (not (G/p).exists() or digest(G/p)!=h)]
 if changed:
  import subprocess
  baseline=S/'previous-6abf7e84/generated-files.json';head=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()
  exact_base=key=='1f' and head=='6abf7e84e27828356c1bb390b048611c1997d4e4' and baseline.exists() and all((G/p).exists() and digest(G/p)==h for p,h in json.loads(baseline.read_text()).items())
  refinement_base=S/'previous-de6922a/generated-files.json'
  exact_refinement=head=='de6922a964721aceb11147bcac6acadc477d4538' and refinement_base.exists() and all((G/p).exists() and digest(G/p)==h for p,h in json.loads(refinement_base.read_text()).items())
  assert exact_base or exact_refinement,('Preserve owner edits',changed)
else:
 assert not (G/'data/layouts'/c['name']).exists() and not (G/'data/maps'/c['name']).exists(),('Preserve existing floor without private source manifest',c['name'])
if '--check-only' in sys.argv:print(key,'owned-source guard passed');raise SystemExit(0)
a=np.array(Image.open(S/'clean-terrain.png').convert('RGB'));lab=np.load(S/'hgss-pixel-materials.npy').copy();plan=np.array([list(row) for row in (S/'hgss-material-grid.txt').read_text().splitlines()]);blocked=np.load(S/'hgss-foot-blocked.npy').copy();props=lab=='O';yy,xx=np.indices(lab.shape)
# Every foreground rock is a complete source silhouette. Keep palette-separated
# ground beneath it, rather than allowing palette compression to hollow its center.
floor_sample=np.array(Image.open(ROOT/'gba/art/union-cave-1f/source/hgss-reference.png').convert('RGB'))[288:304,96:112];bg=a.copy();bg[props]=floor_sample[yy[props]%16,xx[props]%16];bg_lab=lab.copy();bg_lab[props]='.'
# Original HGSS Union Cave stone-step texture, adapted at its native warp footprint.
# The old c['ladders'] name is retained for stable registered coordinate data only.
up_stairs={'1f':set(),'b1f':{(31,35),(4,48),(4,5),(4,12)},'b2f':{(4,5)}}[key]
special=np.zeros(lab.shape,bool);stairmask=np.zeros(lab.shape,bool);doormask=np.zeros(lab.shape,bool)
for x0,y0,x1,y1 in c['stone_boxes']:special[y0:y1,x0:x1]=True
for x,y in c['ladders']:
 sl=np.s_[y*16:y*16+16,x*16:x*16+16];direction='up' if (x,y) in up_stairs else 'down';piece=np.array(Image.open(S/'native-assets'/f'hgss-stone-stairs-{direction}.png').convert('RGB'));bg[sl]=piece;props[sl]=False;lab[sl]='S';bg_lab[sl]='S';special[sl]=True;stairmask[sl]=True;plan[y,x]='S';blocked[y,x]=False
for x,y in c['doors']:
 doormask[max(0,(y-1)*16):min(H*16,(y+1)*16),max(0,(x-1)*16):min(W*16,(x+2)*16)]=True;plan[y,x]='.';blocked[y,x]=False
if key=='1f':doormask[896:944,432:480]=True
special|=doormask
r,g,b=bg.transpose(2,0,1).astype(int);qb=np.zeros((H*2,W*2),np.int8)
for y in range(H*2):
 for x in range(W*2):
  sl=np.s_[y*8:y*8+8,x*8:x*8+8];l=bg_lab[sl]
  if stairmask[sl].any() or (special[sl].any() and not doormask[sl].any()):bank=5
  elif doormask[sl].any():bank=4
  elif (l=='W').sum()>=12:bank=2
  else:bank=int((l=='R').sum()>=24)
  qb[y,x]=0 if bank in [0,1] else bank
pb=np.repeat(np.repeat(qb,8,0),8,1);pals=[];idx=[]
# One shared rock/floor/water ramp prevents palette-bank seams at quadrant joins.
ramps={}
for material,n in [('R',10),('.',4),('W',4)]:
 px=bg[bg_lab==material]
 if not len(px):px=floor_sample.reshape(-1,3)
 if material=='R':
  # Reserve bright plateau shades; a whole-image palette otherwise collapses
  # their subtle texture to a flat fill under the much larger dark-wall area.
  parts=[]
  for select,num in [(px.mean(1)<120,7),(px.mean(1)>=120,3)]:
   sample=px[select] if select.any() else px
   im=Image.fromarray(sample.reshape(-1,1,3)).quantize(colors=num,method=Image.Quantize.MEDIANCUT)
   parts.extend(np.array(im.getpalette()[:num*3]).reshape(num,3).tolist())
  ramps[material]=np.array(parts)&248
 else:
  im=Image.fromarray(px.reshape(-1,1,3)).quantize(colors=n,method=Image.Quantize.MEDIANCUT)
  ramps[material]=np.array(im.getpalette()[:n*3]).reshape(n,3)&248
shared=np.vstack(([0,0,0],ramps['R'],ramps['.'],[0,0,0]))
shared_water=np.vstack(([0,0,0],ramps['R'],ramps['W'],[0,0,0]))
for bank in range(6):
 pixels=a[props] if bank==3 else bg[pb==bank]
 if len(pixels)==0:pixels=floor_sample.reshape(-1,3)
 q=Image.fromarray(pixels.reshape(-1,1,3)).quantize(colors=14,method=Image.Quantize.MEDIANCUT);co=np.array((q.getpalette()+[0]*42)[:42],int).reshape(14,3)&248;co=np.vstack(([0,0,0],co,[0,0,0]));pals.append(co)
 if bank in [0,1,2]:co=(shared_water if bank==2 else shared).copy();pals[-1]=co
 if key=='1f' and bank==4:co=np.array(json.loads((S/'native-assets/approved-entrance-palette.json').read_text()));pals[-1]=co
 src=a if bank==3 else bg;d=((src.astype(np.int32)[...,None,:]-co[None,None,:,:])**2).sum(3);d[...,0]=1000000000;idx.append(d.argmin(2).astype(np.uint8))
# Pack by EXACT material silhouette, not unrestricted independent RGB similarity.
# Every original wall/floor/water/void mask has a representative. Texture reuse
# may simplify shading inside one material, never replace a corner with floor.
keys=[];fore=[];p0=[];black=(0,bytes(64),b'F');groups={}
for y in range(0,H*16,8):
 for x in range(0,W*16,8):
  sl=np.s_[y:y+8,x:x+8];bank=int(qb[y//8,x//8]);shape=bg_lab[sl].astype('S1').tobytes();k=(bank,idx[bank][sl].tobytes(),shape);fp=np.where(props[sl],idx[3][sl],0).astype(np.uint8);fk=(3,fp.tobytes(),b'F') if fp.any() else black;keys.append(k);fore.append(fk)
  groups.setdefault((bank,shape),[]).append(k)
  if special[sl].any():p0.append(k)
counts=Counter(keys+fore);selected=list(dict.fromkeys([black]+fore+p0))
for group,ks in groups.items():
 if not any(k in selected for k in ks):selected.append(Counter(ks).most_common(1)[0][0])
# Keep the compact original floor and water texture cores intact.
for material in [b'.'*64,b'W'*64]:
 for (bank,shape),ks in groups.items():
  if shape==material:
   for k,n in Counter(ks).most_common(12):
    if k not in selected:selected.append(k)
# Preserve the compact bright plateau family as well as floor/water cores.
for (bank,shape),ks in groups.items():
 if shape==b'R'*64:
  bright=[k for k in ks if pals[bank][np.frombuffer(k[1],np.uint8)].mean()>=120]
  for k,n in Counter(bright).most_common(12):
   if k not in selected:selected.append(k)
mandatory=len(selected);assert mandatory<=1008,('Exact feature/material-mask budget',mandatory)
# Spend spare tiles on the worst remaining shade/edge mismatch, rather than raw
# frequency (which favors repeated flat ground and starves rare corner shading).
weight=np.ones((8,8,3),np.int64);weight[[0,-1],:]=4;weight[:,[0,-1]]=4;weight=weight.ravel();models=[]
for (bank,shape),ks in groups.items():
 unique=list(dict.fromkeys(ks));rgb=np.array([pals[bank][np.frombuffer(k[1],np.uint8)] for k in unique],np.int64).reshape(len(unique),192);norm=(rgb*rgb*weight).sum(1)
 chosen=[i for i,k in enumerate(unique) if k in selected];best=np.full(len(unique),10**12,np.int64)
 for i in chosen:best=np.minimum(best,norm+norm[i]-2*(rgb@(rgb[i]*weight)))
 models.append((unique,rgb,norm,best,np.sqrt([counts[k] for k in unique])))
while len(selected)<1008:
 winners=[(float((best*freq).max()),n,int((best*freq).argmax())) for n,(unique,rgb,norm,best,freq) in enumerate(models)]
 score,n,i=max(winners)
 if score<=0:break
 unique,rgb,norm,best,freq=models[n];selected.append(unique[i]);best[:]=np.minimum(best,norm+norm[i]-2*(rgb@(rgb[i]*weight)))
canonical=S/'native-glyph-order.json'
if canonical.exists():
 rows=json.loads(canonical.read_text())['glyphs']
 if rows and len(rows[0])==3 and json.loads(canonical.read_text()).get('packing_revision')==10:
  saved=[(int(bank),bytes.fromhex(px),bytes.fromhex(mask)) for bank,px,mask in rows]
  if len(saved)==len(set(saved)) and len(saved)<=1008 and set(saved).issubset(counts) and set(selected[:mandatory]).issubset(saved):selected=saved
lookup={k:i for i,k in enumerate(selected)};approximated=[];shape_errors=0
for (bank,shape),ks in groups.items():
 options=[(i,np.frombuffer(p,np.uint8)) for i,(b,p,m) in enumerate(selected) if b==bank and m==shape and all(v>0 for v in p)];assert options,(bank,shape)
 ids=np.array([i for i,p in options]);rgb=np.array([pals[bank][p] for i,p in options],np.int32).reshape(len(options),192)
 weight=np.ones((8,8,3),np.int32);weight[[0,-1],:]=4;weight[:,[0,-1]]=4;weight=weight.ravel();norm=(rgb*rgb*weight).sum(1)
 for k in dict.fromkeys(ks):
  if k in lookup:continue
  px=np.frombuffer(k[1],np.uint8);v=pals[bank][px].astype(np.int32).reshape(192);loss=norm+(v*v*weight).sum()-2*(rgb@(v*weight));j=int(loss.argmin());lookup[k]=int(ids[j]);approximated.append(k)
  shape_errors+=int(selected[int(ids[j])][2]!=k[2])
assert shape_errors==0
water_plane=plan=='W'
roots={tuple(pt) for f in json.loads((S/'stalagmite-footprints.json').read_text()) for pt in f['root_cells']}
for yy0,xx0 in zip(*np.where(plan=='O')):
 piece=lab[yy0*16:yy0*16+16,xx0*16:xx0*16+16]
 if (int(xx0),int(yy0)) not in roots and int((piece=='W').sum())>=96 and int((piece=='R').sum())<80 and int((piece=='X').sum())<32:water_plane[yy0,xx0]=True;blocked[yy0,xx0]=True
np.save(S/'native-water-plane.npy',water_plane)
opaque_BG_errors=sum(any(v==0 for v in selected[lookup[k]][1]) for k in keys);assert opaque_BG_errors==0,opaque_BG_errors
entries=[];attrs=[];mids={};grid=np.zeros((H,W),'<u2');behavior_grid=np.zeros((H,W),np.uint8)
for y in range(H):
 for x in range(W):
  bottom=[];top=[]
  for q in range(4):
   i=(y*2+q//2)*W*2+x*2+q%2;k=keys[i];f=fore[i];bottom.append(lookup[k]|(k[0]<<12));top.append(lookup[f]|(f[0]<<12))
  behavior=97 if (x,y) in c['ladders'] else (101 if key=='1f' and (x,y)==(28,19) else (16 if water_plane[y,x] else 0));behavior_grid[y,x]=behavior;attr=behavior|(0 if props[y*16:y*16+16,x*16:x*16+16].any() else 0x1000);mk=tuple(bottom+top)+(attr,)
  if mk not in mids:mids[mk]=len(entries);entries.append(tuple(bottom+top));attrs.append(attr)
  grid[y,x]=mids[mk]|(0x1000 if water_plane[y,x] else 0x3000)|(0xc00 if blocked[y,x] and not water_plane[y,x] else 0)
assert len(entries)<=1024,('Metatile budget',len(entries))
for part,typ in enumerate(['primary','secondary']):
 d=G/'data/tilesets'/typ/c['set'];(d/'palettes').mkdir(parents=True,exist_ok=True);im=Image.new('P',(128,256));im.putpalette([int(v) for co in pals[0] for v in co]+[0]*720)
 for i,(bank,p,shape) in enumerate(selected[part*512:(part+1)*512]):im.paste(Image.fromarray(np.frombuffer(p,np.uint8).reshape(8,8),'P'),(i%16*8,i//16*8))
 im.save(d/'tiles.png')
 for n in range(16):(d/'palettes'/f'{n:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,co)) for co in pals[n if n<6 else 0])+'\n')
 es=entries[part*512:(part+1)*512]+[(0,)*8]*max(0,512-len(entries[part*512:(part+1)*512]));at=attrs[part*512:(part+1)*512]+[0]*max(0,512-len(attrs[part*512:(part+1)*512]));(d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*e) for e in es));(d/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*at))
d=G/'data/layouts'/c['name'];d.mkdir(exist_ok=True);grid.tofile(d/'map.bin');np.full(4,0x3c00,'<u2').tofile(d/'border.bin');np.save(S/'native-metatile-grid.npy',grid);np.save(S/'native-material-grid.npy',plan);np.save(S/'native-foot-blocked.npy',blocked)
(S/'hgss-material-grid.txt').write_text('\n'.join(''.join(row) for row in plan)+'\n');np.save(S/'hgss-foot-blocked.npy',blocked)
t=Tileset(G,c['set'],c['set']);native=t.map_image(list(map(int,grid.ravel())),W);native.save(E/'native-map.png')
# Verify all retained foreground rock pixels in actual decoded output.
rgb=np.array(native);expected=pals[3][idx[3]].astype(np.uint8);errors=int(np.any(rgb[props]!=expected[props],1).sum());assert errors==0,errors
report={'raw_glyphs':len(counts),'static_glyphs':len(selected),'metatiles':len(entries),'required_feature_geometry_and_core_glyphs':mandatory,'approximated_background_texture_glyphs':len(approximated),'foreground_rock_RGB_errors':errors,'transparent_background_quadrants':opaque_BG_errors,'foreground_rock_pixels':int(props.sum()),'native_palettes':6,'foreground_policy':'complete original rock silhouettes in native foreground; collision restricted to explicit base footprints','exact_regions':['all foreground formations','all HGSS stone steps','every wall/floor/water/void material silhouette','beige boulders','both lighted exterior entrances'],'material_silhouette_substitution_errors':shape_errors,'wall_cleanup':'bounded same-material pixel cleanup; shape-constrained native packing; border-weighted shade matching','water':'native Surf behavior; static artwork'};(E/'packing.json').write_text(json.dumps(report,indent=2)+'\n')
# Save the next owned-source fingerprint only after a complete successful render.
paths=[p for folder in [d,G/'data/tilesets/primary'/c['set'],G/'data/tilesets/secondary'/c['set'],G/'data/maps'/c['name']] if folder.exists() for p in folder.rglob('*') if p.is_file() and p.name not in ['header.inc','events.inc','connections.inc']];manifest.write_text(json.dumps({str(p.relative_to(G)):digest(p) for p in paths},indent=2)+'\n')
canonical.write_text(json.dumps({'packing_revision':10,'purpose':'exact owner correction dictionary; geometry constraints retained','glyphs':[[bank,px.hex(),shape.hex()] for bank,px,shape in selected]},indent=2)+'\n')
print(key,json.dumps(report))
