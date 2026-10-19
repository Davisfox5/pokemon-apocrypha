"""One-shot native Radio equipment and background-independent Center correction.
Does not replay the authoring generator or alter unrelated maps/palettes/IDs.
"""
from pathlib import Path
import sys,json,subprocess,struct,io
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=R/'gba/art/goldenrod-city/source';E=S.parent/'evidence';O=E/'center-radio';O.mkdir(exist_ok=True)
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='bb54d528df4f26d457b3b1c5f43bf4de41b3b50f'
subprocess.run(['python3',str(G/'tools/goldenrod/check.py')],check=True)
def baseline_source(name):
 return subprocess.check_output(['git','-C',str(R),'show','19c905799ead42f1099797e2555212d573825fc8:gba/art/goldenrod-city/source/'+name])
sections=json.loads((E/'sections.json').read_text());bg=np.zeros((896,1344,4),np.uint8);fg=bg.copy();records=[]
for s in sections:
 n=s['name'];x,y,x1,y1=s['box'];t=Tileset(G,n.lower(),n.lower());g=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x)
 for cy,cx in np.ndindex(g.shape):
  mid=int(g[cy,cx]&1023)
  for i,e in enumerate(t.blocks[mid>=512][mid%512]):
   tid=e&1023;a=np.array(t.tiles[tid>=512][tid%512]).reshape(8,8);a=a[::-1] if e&2048 else a;a=a[:,::-1] if e&1024 else a;p=np.array(t.pals[(e>>12)>=6][e>>12],np.uint8);v=np.dstack([p[a],np.where(a>0,255,0).astype(np.uint8)]);xx=(x+cx)*16+i%2*8;yy=(y+cy)*16+(i%4)//2*8;(fg if i>=4 else bg)[yy:yy+8,xx:xx+8]=v
 records.append((s,t,g))
oldbg=bg.copy();oldfg=fg.copy();before=bg[...,:3].copy();m=fg[...,3]>0;before[m]=fg[m,:3];Image.fromarray(before).save(O/'before.png')
ref=np.array(Image.open(S/'hgss-reference.png'))
# Restore the original neighborhood instead of a rectangular replacement pad.
bg[568:672,776:896,:3]=ref[568:672,776:896]&248
fg[568:664,784:880]=0
# Remove only the source Center silhouette; restore local gold paving underneath.
mask=Image.new('L',(1344,896));d=ImageDraw.Draw(mask);d.rectangle((790,568,879,663),fill=255);mm=np.array(mask)>0
# Clear narrow gold-paving donor between source Center and curb, above lamp.
pave=ref[560:568,800:816]&248
yy,xx=np.indices(mm.shape);bg[mm,:3]=pave[(yy[mm]-560)%8,(xx[mm]-800)%16]
# Recover intact neighboring wall and full lamp from their original context.
bg[576:664,776:790,:3]=ref[576:664,776:790]&248
bg[620:664,872:896,:3]=ref[620:664,872:896]&248
center=np.array(Image.open(S/'masters/center.png'));center[...,:3]&=248
# Half-metatile adjustment respects the HGSS opening and clears the lamp.
x,y=792,576;a=fg[y:y+80,x:x+80];cm=center[...,3]>0;a[cm]=center[cm]
# Radio: separate equipment from the roof beneath, so silver dishes can use
# their own native palette without forcing silver through the water/teal ramp.
equipment=Image.new('RGBA',(1344,896));ed=ImageDraw.Draw(equipment)
# Each old dish is removed from its own deck, with complete silhouettes retained.
for box,color in [((230,216,249,243),(8,64,88)),((263,208,282,236),(8,64,88)),((177,281,203,307),(80,80,88))]:
 x0,y0,x1,y1=box;bg[y0:y1,x0:x1,:3]=color;fg[y0:y1,x0:x1]=0
# Preserve a narrow cream rim beside the two upper dishes.
for x0,x1 in [(225,230),(280,284)]:
 bg[216:250,x0:x1,:3]=(224,224,216);fg[216:250,x0:x1]=0
bg[250:254,225:284,:3]=(224,224,216);fg[250:254,225:284]=0
bg[208:214,272:282]=oldbg[208:214,304:314]
# Three instances of one clean bowl/support master. Rear-facing dish is mirrored.
def dish():
 a=Image.new('RGBA',(24,30));d=ImageDraw.Draw(a)
 outline=(80,80,88,255);rim=(224,224,216,255);silver=(192,192,184,255);shade=(136,152,152,255);inner=(168,160,144,255)
 d.polygon([(10,20),(13,20),(15,27),(19,27),(19,29),(6,29),(6,27),(10,26)],fill=outline)
 d.polygon([(11,20),(12,20),(13,27),(9,27)],fill=shade)
 d.ellipse((2,0,21,23),fill=outline);d.ellipse((3,1,20,21),fill=rim);d.ellipse((5,3,19,20),fill=shade);d.ellipse((5,3,17,18),fill=silver)
 d.arc((5,3,18,19),200,325,fill=inner,width=1)
 d.line([(5,19),(12,12),(12,9)],fill=outline,width=2);d.line([(5,18),(11,12)],fill=rim,width=1);d.rectangle((10,8,13,10),fill=outline);d.point((11,8),fill=rim)
 return a
master=dish();master.save(S/'masters/radio-dish.png')
for i,(x,y) in enumerate([(230,216),(260,208),(178,280)]):equipment.alpha_composite(master.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if i==1 else master,(x,y))
# Repair water only where the old broad rod sat; draw a thin straight metal mast.
for y in range(130,175):
 for x in range(252,259):bg[y,x]=oldbg[y,x-16];fg[y,x]=0
ed=ImageDraw.Draw(equipment);ed.rectangle((254,130,256,183),fill=(80,80,88,255));ed.line((254,131,254,179),fill=(216,216,208,255));ed.line((255,132,255,181),fill=(136,152,152,255));ed.rectangle((250,181,260,184),fill=(80,80,88,255));ed.line((251,181,259,181),fill=(192,192,184,255))
a=np.array(equipment);m=a[...,3]>0
# Opaque roof duplicates are unnecessary beneath separate equipment; retain the
# unchanged deck in BG and give each silver fixture its own transparent FG.
for wy,wx in np.argwhere(m.reshape(56,16,84,16).any(axis=(1,3))):fg[wy*16:wy*16+16,wx*16:wx*16+16]=0
fg[m]=a[m];equipment.save(S/'masters/radio-equipment.png');mask.save(O/'original-center-removal-mask.png')
lamp=ref[624:664,872:896];lm=(lamp[...,2].astype(int)>lamp[...,0].astype(int)+3)&(lamp[...,1]>=lamp[...,0]);target=fg[624:664,872:896];target[lm,:3]=lamp[lm]&248;target[lm,3]=255
solid=np.load(io.BytesIO(baseline_source('solid.npy')));above=np.load(io.BytesIO(baseline_source('above.npy')));mat=np.load(io.BytesIO(baseline_source('material.npy')))
solid[39:41,49:55]=True;solid[41,55]=True
above[36:39,49:55]=True;above[39:41,55]=True;above[39,54]=True
mat[36:41,49:55]='shared Center';mat[41,55]='prop'
features=json.loads(baseline_source('features.json'))
for f in features:
 if 'Center' in f['name']:
  f['native_box']=[792,576,872,656];f['facade']=[792,624,872,656];f['adaptation']='Unchanged transparent canonical prefab fitted8pxleft; original neighbor/lamp restored independently, no rectangular pad attached.'
(S/'features.json').write_text(json.dumps(features,indent=2)+'\n')
(S/'center-placement.json').write_text(json.dumps(dict(origin=[792,576],size=[80,80],building='masters/center.png',background='Native local ground; separate from building alpha.',opaque_pixels=5679,transparent_pixels=721,approach=[52,41]),indent=2)+'\n')
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
  for bank in ([5] if force_bank==5 else [oldentry>>12]+[b for b in range(13) if b!=oldentry>>12]):
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
    if not np.array_equal(a,old):
     force_bank=5 if i<4 and 776<=xx<792 and 576<=yy<664 else -1;es[i]=encode(a,es[i])
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
 m=desired[...,3]>0;intent_errors.append(int(np.any(desired[m,:3]!=actual[m,:3],axis=1).sum()))
Image.fromarray(quantized[0][...,:3]).save(S/'native-ground.png');Image.fromarray(quantized[1]).save(S/'shared-foreground.png');np.save(S/'solid.npy',solid);np.save(S/'above.npy',above);np.save(S/'material.npy',mat)
after=quantized[0][...,:3].copy();m=quantized[1][...,3]>0;after[m]=quantized[1][m,:3];Image.fromarray(after).save(O/'after.png')
# Actual decoded native pixels, not the design preview, form review comparisons.
for name,box in [('center',(712,552,912,688)),('radio',(168,120,320,324))]:
 w,h=box[2]-box[0],box[3]-box[1];out=Image.new('RGB',(w*6,h*3+24),(24,32,40));d=ImageDraw.Draw(out)
 for i,(label,im) in enumerate([('Before',before),('After native',after)]):out.paste(Image.fromarray(im).crop(box).resize((w*3,h*3)),(i*w*3,24));d.text((i*w*3+4,5),label,fill='white')
 out.save(O/(name+'-before-after.png'))
em=np.array(equipment)[...,3]>0;assert np.array_equal(after[em],np.array(equipment)[em,:3]),'Equipment must retain its clean silver palette'
cm=center[...,3]>0;assert np.array_equal(after[576:656,792:872][cm],center[cm,:3]),'Center artwork must remain exact'
(O/'review.json').write_text(json.dumps(dict(baseline='bb54d528df4f26d457b3b1c5f43bf4de41b3b50f',sections=stats,palette_fitted_layer_pixels=intent_errors,Center_opaque_pixels_exact=5679,Center_origin=[792,576],ground_donor=[800,560,816,568],neighbors_restored_from_registered_HGSS=True,dishes='Three copies of one transparent24x30native dish master, one mirrored; roof deck restored separately.',antenna='Straight3pxmetal mast; old7pxbar removed and water restored.',scope='Radio rooftop equipment and Center placement/neighbor context only; existing palette banks unchanged.'),indent=2)+'\n');print(stats,intent_errors)
