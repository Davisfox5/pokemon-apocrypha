"""One-shot, guarded native building/tree refinement of owner-reviewed f439df1.
Does not replay the authoring generator or alter unrelated maps/palettes/IDs.
"""
from pathlib import Path
import sys,json,subprocess,struct,io
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_erosion
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=R/'gba/art/goldenrod-city/source';E=S.parent/'evidence';O=E/'refinement';O.mkdir(exist_ok=True)
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='f439df15cc6f4c95df2846da353c9e4e2549fcd2'
subprocess.run(['python3',str(G/'tools/goldenrod/check.py')],check=True)
def baseline_source(name):
 return subprocess.check_output(['git','-C',str(R),'show','3b550ae79ea719f65e267249dc3af2b1c015202c:gba/art/goldenrod-city/source/'+name])
sections=json.loads((E/'sections.json').read_text());bg=np.zeros((896,1344,4),np.uint8);fg=bg.copy();records=[]
for s in sections:
 n=s['name'];x,y,x1,y1=s['box'];t=Tileset(G,n.lower(),n.lower());g=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x)
 for cy,cx in np.ndindex(g.shape):
  mid=int(g[cy,cx]&1023)
  for i,e in enumerate(t.blocks[mid>=512][mid%512]):
   tid=e&1023;a=np.array(t.tiles[tid>=512][tid%512]).reshape(8,8);a=a[::-1] if e&2048 else a;a=a[:,::-1] if e&1024 else a;p=np.array(t.pals[(e>>12)>=6][e>>12],np.uint8);v=np.dstack([p[a],np.where(a>0,255,0).astype(np.uint8)]);xx=(x+cx)*16+i%2*8;yy=(y+cy)*16+(i%4)//2*8;(fg if i>=4 else bg)[yy:yy+8,xx:xx+8]=v
 records.append((s,t,g))
oldbg=bg.copy();oldfg=fg.copy();before=bg[...,:3].copy();m=fg[...,3]>0;before[m]=fg[m,:3];Image.fromarray(before).save(O/'before.png')
features=json.loads((S/'features.json').read_text());findings=[]
# Review-local cleanup: replace only isolated low-contrast single pixels with a
# surrounding plane's dominant shade. Never blur silhouettes or interpolate colors.
for f in features:
 x,y,x1,y1=f['reference_box'];changed=0
 if 'Center' in f['name']:continue
 for layer in [bg,fg]:
  a=layer[y:y1,x:x1];orig=a.copy();h,w=a.shape[:2]
  for yy in range(2,h-2):
   for xx in range(2,w-2):
    c=orig[yy,xx];ns=orig[yy-1:yy+2,xx-1:xx+2].reshape(9,4);colors,counts=np.unique(ns,axis=0,return_counts=True);j=counts.argmax();v=colors[j]
    if c[3] and v[3] and counts[j]>=7 and not np.array_equal(c,v) and np.max(np.abs(c[:3].astype(int)-v[:3].astype(int)))<=48:
     a[yy,xx]=v;changed+=1
 # Gold highrise roofs share a clean, measured tile-grid master. Keep existing
 # vent, outline, bevel and shaded side masks; only the interior gold plane changes.
 tower=('highrise' in f['name'].lower() or 'tower' in f['name'].lower()) and f['name'] not in ['Radio Tower','Station annex']
 if tower or f['name'] in ['Flower Shop','Department annex']:
  for layer in [bg,fg]:
   a=layer[y:(min(y+56,y1) if not tower else y1),x:x1];rgb=a[...,:3].astype(int);gold=(rgb[...,0]>170)&(rgb[...,1]>125)&(rgb[...,2]<160)&(rgb[...,0]>rgb[...,2]+55)&(a[...,3]>0);inside=binary_erosion(gold,iterations=1)
   # Native bank6 ramp, chosen from the existing roof, no new colors.
   p=np.array(records[0][1].pals[1][6]);valid=p[(p[:,0]>170)&(p[:,1]>125)&(p[:,2]<160)&(p[:,0].astype(int)>p[:,2].astype(int)+55)]
   if len(valid)>1:
    valid=valid[np.argsort(valid.sum(axis=1))];base=valid[len(valid)//2];light=valid[-1];dark=valid[0];yy,xx=np.indices(gold.shape);paint=np.empty_like(a[...,:3]);paint[:]=base;paint[(xx%6==0)|(yy%5==0)]=dark;paint[(xx%6==1)&(yy%5!=0)]=light;changed+=int(np.any(a[...,:3][inside]!=paint[inside],axis=1).sum());a[...,:3][inside]=paint[inside]
 findings.append(dict(name=f['name'],reference_box=f['reference_box'],changed_layer_pixels=changed,review='Roof rim, vent, side face, facade, baseline and adjacent ground compared with registered HGSS crop. Canonical Center preserved.' if tower else 'Silhouette, roof/wall join, windows, door, side face and ground compared; isolated low-contrast speckle only.'))
# Remove clipped source trees and the solitary mismatched placement. Rebuild the
# receiving strip using unobscured native fence/lawn at the same vertical phase.
bg[800:832,1296:1344]=oldbg[768:800,1296:1344]
bg[832:896,1184:1328]=np.tile(oldbg[832:896,1088:1120],(1,5,1))[:,:144]
fg[832:896,1184:1328]=0
# Previous native tree at1296,832 is also completely erased above, including roots.
trees=json.loads(baseline_source('trees.json'));trees.remove([1296,832]);trees += [[x,848] for x in [1184,1216,1248,1280]]
tree=np.array(Image.open(S/'masters/tree.png').convert('RGBA'));tree[...,:3]&=248
for x,y in trees[-4:]:
 a=fg[y:y+48,x:x+32];mask=tree[...,3]>0;a[mask]=tree[mask]
solid=np.load(io.BytesIO(baseline_source('solid.npy')));above=np.load(io.BytesIO(baseline_source('above.npy')));mat=np.load(io.BytesIO(baseline_source('material.npy')));roots=np.zeros_like(solid,dtype=np.uint8)
for x,y in trees:roots[y//16+1:y//16+3,x//16:x//16+2]+=1
assert roots.max()==1
solid[roots>0]=True
for wy in range(52,56):
 for wx in range(74,83):
  if wx<82 and wy==53:above[wy,wx]=True
  elif wx<82:above[wy,wx]=False
  mat[wy,wx]='forest roots' if roots[wy,wx] else 'paving' if wy<54 else 'lawn'
# Preserve current native source IDs. Clone only changed metatiles and append
# required index glyphs to free hardware slots, with per-quadrant palette fitting.
quantized=[np.zeros_like(bg),np.zeros_like(fg)];stats=[]
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
 look={a.tobytes():i*512+j for i,part in enumerate(tiles) for j,a in enumerate(part) if i*512+j in kept}
 def encode(a,oldentry):
  mask=a[...,3]>0
  if not mask.any():return 0
  rgb=a[...,:3].astype(int);best=None
  for bank in [oldentry>>12]+[b for b in range(13) if b!=oldentry>>12]:
   pal=np.array(t.pals[bank>=6][bank],int);dist=((rgb[:,:,None]-pal[None,None,1:])**2).sum(axis=3);idx=dist.argmin(axis=2)+1;err=int(dist.min(axis=2)[mask].sum())
   if best is None or err<best[0]:best=(err,idx,bank)
   if err==0:break
  err,idx,bank=best;idx=idx.astype(np.uint8);idx[~mask]=0;k=idx.tobytes()
  if k not in look:
   if free:
    gid=free.pop(0);tiles[gid>=512][gid%512]=idx;look[k]=gid
   else:
    part=0 if len(tiles[0])<512 else 1
    assert len(tiles[part])<(512 if part==0 else 496),(n,'glyph capacity')
    look[k]=part*512+len(tiles[part]);tiles[part].append(idx)
  pal=np.array(t.pals[bank>=6][bank],np.uint8);v=np.dstack([pal[idx],np.where(idx>0,255,0).astype(np.uint8)])
  return look[k]|bank<<12
 for cy,cx in np.ndindex(g.shape):
  wx,wy=x+cx,y+cy;sl=np.s_[wy*16:wy*16+16,wx*16:wx*16+16];mid=int(g[cy,cx]&1023);es=list(blocks[mid>=512][mid%512]);changed=not np.array_equal(bg[sl],oldbg[sl]) or not np.array_equal(fg[sl],oldfg[sl]);attr=attrs[mid>=512][mid%512];newattr=(attr&~0xf000)|(0 if above[wy,wx] else 0x1000)
  if changed:
   for i in range(8):
    yy=wy*16+(i%4)//2*8;xx=wx*16+i%2*8;a=(fg if i>=4 else bg)[yy:yy+8,xx:xx+8];old=(oldfg if i>=4 else oldbg)[yy:yy+8,xx:xx+8]
    if not np.array_equal(a,old):es[i]=encode(a,es[i])
  if changed or newattr!=attr:
   part=0 if len(blocks[0])<512 else 1;newmid=part*512+len(blocks[part]);assert newmid<1024;blocks[part].append(tuple(es));attrs[part].append(newattr);g[cy,cx]=(int(g[cy,cx])&~1023)|newmid;changedcells+=1
  g[cy,cx]=(int(g[cy,cx])&~0xc00)|(0xc00 if solid[wy,wx] else 0)
 for part,d in enumerate(t.dirs):
  if changedcells:
   sheet=Image.new('P',(128,((len(tiles[part])+15)//16)*8));sheet.putpalette(Image.open(d/'tiles.png').getpalette())
   for i,a in enumerate(tiles[part]):sheet.paste(Image.fromarray(a).convert('P'),(i%16*8,i//16*8))
   sheet.save(d/'tiles.png',bits=4)
  (d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in blocks[part]));(d/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs[part]),*attrs[part]))
 g.tofile(G/f'data/layouts/{n}/map.bin');stats.append(dict(map=n,changed_metatiles=changedcells,glyphs=[len(v) for v in tiles]))
# Derive expected RGB layers from the edited native files (quantization is explicit).
for s,_,_ in records:
 n=s['name'];x,y,x1,y1=s['box'];t=Tileset(G,n.lower(),n.lower());g=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x)
 for cy,cx in np.ndindex(g.shape):
  mid=int(g[cy,cx]&1023)
  for i,e in enumerate(t.blocks[mid>=512][mid%512]):
   tid=e&1023;a=np.array(t.tiles[tid>=512][tid%512]).reshape(8,8);a=a[::-1] if e&2048 else a;a=a[:,::-1] if e&1024 else a;pal=np.array(t.pals[(e>>12)>=6][e>>12],np.uint8);xx=(x+cx)*16+i%2*8;yy=(y+cy)*16+(i%4)//2*8;quantized[i>=4][yy:yy+8,xx:xx+8]=np.dstack([pal[a],np.where(a>0,255,0).astype(np.uint8)])
intent_errors=[]
for desired,actual in zip([bg,fg],quantized):
 mask=desired[...,3]>0;intent_errors.append(int(np.any(desired[mask,:3]!=actual[mask,:3],axis=1).sum()))
assert sum(intent_errors)<512,('Unexpected palette reduction drift',intent_errors)
Image.fromarray(quantized[0][...,:3]).save(S/'native-ground.png');Image.fromarray(quantized[1]).save(S/'shared-foreground.png');np.save(S/'solid.npy',solid);np.save(S/'above.npy',above);np.save(S/'material.npy',mat);np.save(S/'tree-roots.npy',roots);(S/'trees.json').write_text(json.dumps(trees)+'\n')
after=quantized[0][...,:3].copy();m=quantized[1][...,3]>0;after[m]=quantized[1][m,:3];Image.fromarray(after).save(O/'after.png')
ref=Image.open(S/'hgss-reference.png');bim=Image.fromarray(before);aim=Image.fromarray(after);masters=S/'refined-buildings';masters.mkdir(exist_ok=True)
for i,f in enumerate(features):
 box=f['reference_box'];w,h=box[2]-box[0],box[3]-box[1];sheet=Image.new('RGB',(w*6,h*2+24),(25,30,35));d=ImageDraw.Draw(sheet)
 for j,(label,im) in enumerate([('HGSS',ref),('Before',bim),('After',aim)]):sheet.paste(im.crop(box).resize((w*2,h*2)),(j*w*2,24));d.text((j*w*2+4,4),label,fill='white')
 sheet.save(O/f'building-{i:02}.png');aim.crop(box).save(masters/f'{i:02}.png')
box=(1136,800,1344,896);sheet=Image.new('RGB',(832,216),(25,30,35));sheet.paste(bim.crop(box).resize((416,192)),(0,24));sheet.paste(aim.crop(box).resize((416,192)),(416,24));d=ImageDraw.Draw(sheet);d.text((4,4),'Before: clipped source trees',fill='white');d.text((420,4),'After: complete native trees',fill='white');sheet.save(O/'trees-before-after.png')
(O/'review.json').write_text(json.dumps(dict(baseline='f439df15cc6f4c95df2846da353c9e4e2549fcd2',palette_fitted_layer_pixels=intent_errors,buildings=findings,sections=stats,tree_repair='Removed clipped HGSS tree strip and solitary native placement; same-phase unobscured fence/lawn donor, four complete native32x48trees at1184,1216,1248,1280 y848. Preserved boundary barriers.',palette_policy='Existing13banks unchanged; no color interpolation.',scope='Exterior art only; no campaign or service changes.'),indent=2)+'\n');print(stats)
