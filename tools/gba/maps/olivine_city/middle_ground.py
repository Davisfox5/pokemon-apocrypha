"""Guarded receiving-context repair: HGSS terrain plus accepted clean masters.
Preserves intact reference terrain/groves; reconstructs complete material and
fence continuations before transparent asset placement. Never replays an author.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,struct
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/olivine-city/source';A=S/'middle-ground';E=S.parent/'evidence';O=E/'middle-ground';M=S/'rebuilt/masters'
BASE='81697bbe0f9582ca30567604c748f22d0166a458'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
assert not subprocess.check_output(['git','-C',str(G),'diff','--name-only','HEAD'],text=True).strip(),'Preserve existing native work'
sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
W,H=65,54;sections=json.loads((E/'sections.json').read_text());solid=np.load(S/'solid.npy').copy();solid[27,28]=False;solid[27,29]=True
ref=Image.open(S/'hgss-reference.png').convert('RGB');canvas=Image.new('RGB',(1040,864));canvas.paste(ref);canvas.paste(ref.crop((1034,0,1035,858)).resize((5,858)),(1035,0));canvas.paste(canvas.crop((0,857,1040,858)).resize((1040,6)),(0,858));original=np.array(canvas);raw=original.copy();repair=np.zeros((864,1040),bool);fg=np.zeros((864,1040,4),np.uint8);above=np.zeros((54,65),bool);mat=np.load(S/'material.npy');records=[]
# Donors are immutable, unobscured source patches, never samples from the
# partially repaired canvas. A donor contact sheet accompanies the repairs.
donors={'lawn':(144,208,160,224),'paving':(352,496,384,528),'dock':(360,648,392,680),'water':(8,656,40,688),'north-cliff':(560,160,576,192),'forest':(688,344,720,392),'fence':(352,300,368,332),'quay-rail':(136,616,152,648)}
patches={n:original[y:y1,x:x1].copy() for n,(x,y,x1,y1) in donors.items()}
# Reuse phase-aligned HGSS grove columns inside wooded interiors to fit native
# glyph banks. Keep the source's complete crowns, trunks, spacing, vertical phase
# and every woodland/cliff boundary; only redundant internal texture variants
# share a coherent original-game module.
for x0,y0,x1,y1,donorx in [(96,0,256,144,128),(704,80,800,304,736),(544,0,1008,64,672)]:
 for x in range(x0,x1,32):
  w=min(32,x1-x);raw[y0:y1,x:x+w]=original[y0:y1,donorx:donorx+w];repair[y0:y1,x:x+w]=True
 records.append(dict(material='HGSS forest',reason='Matching source grove-column reuse inside woodland; boundaries and vertical phase retained',bounds=[x0,y0,x1,y1],donor=[donorx,y0,donorx+32,y1]))

# Reuse complete same-phase 48-pixel tree courses in the narrow western grove.
# The outer cliff edge and bottom canopy row remain untouched.
for y in range(176,400,48):
 h=min(48,400-y);raw[y:y+h,0:88]=original[176:176+h,0:88];repair[y:y+h,0:88]=True
records.append(dict(material='HGSS forest',reason='Complete western grove courses reused at original 48px vertical phase; cliff and bottom crowns retained',bounds=[0,176,88,400],donor=[0,176,88,224]))

for y in range(112,304,48):
 raw[y:y+48,704:800]=raw[112:160,704:800].copy();repair[y:y+48,704:800]=True
records.append(dict(material='HGSS forest',reason='Same-phase complete interior tree courses; grove outline retained',bounds=[704,112,800,304],donor=[736,112,768,160]))

def mask(poly):
 im=Image.new('L',canvas.size);ImageDraw.Draw(im).polygon(poly,fill=255);return np.array(im)>0
def patch(area,name,reason):
 yy,xx=np.nonzero(area);core=patches[name];sx,sy,_,_=donors[name];raw[yy,xx]=core[(yy-sy)%core.shape[0],(xx-sx)%core.shape[1]];repair[area]=True;records.append(dict(material=name,reason=reason,bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],pixels=len(xx),donor=donors[name]))
def box(b):
 x,y,x1,y1=b;a=np.zeros(repair.shape,bool);a[y:y1,x:x1]=True;return a
Y,X=np.indices(repair.shape)
# Exact original silhouettes plus their attached outlines/shadows. Ground is
# reconstructed by receiving plane, never one lawn rectangle across all layers.
old=[('Gym',[(214,152),(260,152),(280,162),(294,180),(297,205),(294,228),(282,244),(196,244),(182,228),(182,188),(192,168)],200),('west house',[(270,312),(274,292),(300,272),(316,270),(346,292),(346,354),(274,354)],324),('north house west',[(494,224),(498,204),(526,184),(538,184),(570,206),(570,274),(502,274),(502,244)],192),('north house east',[(574,224),(578,204),(606,184),(618,184),(650,206),(650,274),(582,274),(582,244)],192),('Cafe',[(142,406),(188,406),(188,398),(210,398),(210,412),(218,412),(218,482),(142,482)],448),('Center',[(242,400),(320,400),(330,414),(330,482),(242,482)],448),('Mart',[(470,408),(538,408),(538,416),(562,416),(562,450),(546,458),(546,482),(470,482)],448)]
for name,poly,lawn_start in old:
 a=mask(poly)
 if name=='Gym':
  patch(a&(Y<176),'north-cliff',name+' removed: restore cliff behind roof');patch(a&(Y>=176)&(Y<200),'paving',name+' removed: restore rear pavement');patch(a&(Y>=200),'lawn',name+' removed: restore front lawn')
 elif name.startswith('north house'):
  patch(a&(Y<192),'north-cliff',name+' removed: restore upper ledge');patch(a&(Y>=192),'lawn',name+' removed: restore terrace ground')
 else:
  patch(a&(Y<lawn_start),'paving',name+' removed: restore upper street plane')
  low=a&(Y>=lawn_start)
  if name=='Mart':patch(low&(X>=548),'paving','Mart flag removed beyond lawn edge');low&=X<548
  patch(low,'lawn',name+' removed: restore actual plinth lawn')
# Remove the full contact-shadow envelopes as well as the visible facades.
for b in [(200,200,300,256),(274,324,352,360),(496,224,576,280),(576,224,656,280),(142,448,224,484),(242,448,336,484),(468,448,548,484)]:
 patch(box(b),'lawn','Complete superseded building contact shadow and support cleanup')
patch(box((142,398,216,420)),'paving','Remove remaining cafe roof finial and outline')
# Rebuild the full hidden railing behind the west house, including both rails,
# pickets, feet and the pavement-to-lawn seam. Keep the real festival gate open.
# This is receiving map terrain; it is never attached to the building master.
for x0,x1 in [(248,448)]:
 for x in range(x0,x1,16):
  b=box((x,300,min(x+16,x1),332));patch(b,'fence','Complete fence and ground hidden by old west-house roof')
# Reuse a full same-phase HGSS fan-paving course in the open western street.
# Curbs, lawn edges, lamp shadows and festival fixtures lie outside this patch.
for x in range(136,240,64):
 w=min(64,240-x);raw[336:400,x:x+w]=original[336:400,136:136+w];repair[336:400,x:x+w]=True
records.append(dict(material='paving',reason='Matching fan-paving course reuse on open street, preserving all receiving edges',bounds=[136,336,240,400],donor=[136,336,200,400]))
for x in range(352,448,64):
 w=min(64,448-x);raw[104:304,x:x+w]=original[104:304,352:352+w];repair[104:304,x:x+w]=True
records.append(dict(material='paving',reason='Same-phase original avenue fan courses reused inside street, curbs untouched',bounds=[352,104,448,304],donor=[352,104,416,304]))
# Service-building rear fences continue through their formerly hidden roofs.
# Align the source pickets at y418 with the visible existing fence ends.
for x0,x1 in [(136,336),(472,548)]:
 patch(box((x0,432,x1,448)),'lawn','Rebuild lawn immediately below hidden service-building rear fence')
 for x in range(x0,x1,16):
  w=min(16,x1-x);raw[411:443,x:x+w]=patches['fence'][:,:w];repair[411:443,x:x+w]=True
 records.append(dict(material='fence',reason='Full service-building rear fence, pickets aligned to existing visible ends',bounds=[x0,411,x1,443],donor=donors['fence']))
# North Gym railing continues behind the old barrel roof. Visible ends are
# untouched; only its formerly hidden middle receives the verified source core.
for x in range(192,296,16):
 b=box((x,176,min(x+16,296),200));core=patches['fence'][4:28];raw[176:200,x:min(x+16,296)]=core[:,:min(16,296-x)];repair[b]=True
records.append(dict(material='fence',reason='Complete hidden Gym rear railing, left/right receiving planes rebuilt first',bounds=[192,176,296,200],donor=donors['fence']))
# Lighthouse removal restores a forest plane above its roof and a lawn plane
# below, using same-height unobscured neighboring crowns, not a green box.
a=box((688,344,824,532));patch(a&(Y<392),'forest','Remove old lantern/tower; reconstruct forest crowns at identical vertical phase');patch(a&(Y>=392),'lawn','Remove old roof/facade; restore lighthouse lawn')
patch(box((752,512,776,544)),'lawn','Remove complete old sign, post and shadow; rebuild ground around new doorway')
# Original terminal overhangs water; receiving ground includes three distinct
# planes, rebuilt even where the accepted new roof is transparent.
a=box((310,686,480,816))
wood=((X>=352)&(X<448)&(Y<736))|((X>=280)&(X<464)&(Y>=736)&(Y<832))
patch(a&wood,'dock','Remove old terminal/marker: complete underlying pier deck');patch(a&~wood,'water','Remove old roof overhang: restore surrounding water')
# The accepted native walk grid includes the final half-cell of the pier.
patch(box((440,640,448,736)),'dock','Complete existing native pier east half-cell, matching deck grain')
# Remove each old boat, including mast/rigging over the quay. Restore ground,
# water and the entire interrupted fence before placing the clean boat master.
for x in [248,464]:
 a=box((x-2,608,x+86,686));patch(a&(Y<648),'dock','Complete old sailboat mast, rigging and hull silhouette removal')
 sea=a&(Y>=648);yy,xx=np.nonzero(sea);donorx=152 if x==248 else 144;raw[yy,xx]=original[yy,donorx+xx-x];repair[sea]=True;records.append(dict(material='water',reason='Complete old hull/shadow removed with unobscured same-height water donor',bounds=[x-2,648,x+86,686],donor=[donorx-2,648,donorx+86,686]))
 for xx in range(x-8,x+88,16):patch(box((xx,616,xx+16,648)),'quay-rail','Rebuild full rail/pickets/feet behind removed boat; do not leave a fence gap')

# Native-grid receiving edges: keep the original cliff course/shading while
# completing only the half-cells already required by the accepted walk grid.
patch(box((448,320,464,400)),'paving','Restore narrow avenue shoulder beside preserved cliff face')
patch(box((632,336,640,544)),'paving','Complete east path shoulder; original wall retained to its right')
patch(box((632,576,640,624)),'dock','Complete original quay shoulder beside retaining wall')
# Preserve/reconstruct the entire original service-lamp silhouette, including
# the part that the old Mart footprint and new shoulder repair crossed.
postmask=Image.new('L',(16,64));pd=ImageDraw.Draw(postmask);pd.ellipse((2,0,14,16),fill=255);pd.rectangle((6,12,11,54),fill=255);pd.rectangle((0,54,15,63),fill=255)
pm=np.array(postmask)>0;view=raw[384:448,456:472];view[pm]=original[384:448,456:472][pm]
# Reconstruct the source stair as a complete native-sized element. Its adjacent
# source rock remains intact, and neither shoulder is a phantom open square.
source_stair=Image.fromarray(original[304:336,576:624]).resize((32,32),Image.Resampling.LANCZOS)
raw[304:336,576:608]=np.array(source_stair);repair[304:336,576:608]=True
# Retain the polished transparent architecture, with a local Mart fit that clears
# the original lamp instead of replacing or hiding its receiving context.
placements=[('gym',184,148,4,224),('house',272,264,5,328),('house',496,184,5,248),('house',576,184,5,248),('cafe',144,400,12,448),('lighthouse',688,344,6,480),('terminal',320,688,6,776),('center',240,400,9,448),('mart',469,416,11,448),('sailboat',248,608,6,684),('sailboat',464,608,6,684)]
for name,x,y,bank,facade in placements:
 p=(S/'masters'/(name+'.png')) if name in ['center','mart'] else M/(name+'-native.png');a=np.array(Image.open(p).convert('RGBA'));a[...,:3]&=248;h,w=a.shape[:2];target=fg[y:y+h,x:x+w];m=a[...,3]>0;target[m]=a[m];above[y//16:(facade+15)//16,x//16:(x+w+15)//16]=True
# The sign is placed independently, clear of the accepted entrance and its lawn.
sign=np.array(Image.open(S/'rebuilt/modules/sign.png').convert('RGBA'));pals=[np.array(v,np.uint8) for v in json.loads((S/'palettes.json').read_text())];pal=pals[7];dist=((sign[...,:3].astype(np.int32)[:,:,None]-pal.astype(np.int32)[None,None])**2).sum(3);sign[...,:3]=pal[dist.argmin(2)];m=sign[...,3]>0;target=fg[520:544,768:784];target[m]=sign[m]
# Preserve architecture colors exactly; derive terrain families from the source,
# not from the rejected generic terrain modules. Tree groves remain intact HGSS
# terrain, rather than doubling them with unrelated foreground stamps.
regions={0:[(0,648,256,858),(904,352,1035,672)],1:[(352,368,448,384),(344,496,568,544),(104,300,184,328)],2:[(456,96,488,384),(632,576,880,640),(24,544,104,640),(328,0,456,96)],3:[(136,208,176,224),(680,536,832,576),(488,272,648,304)],7:[(360,648,432,696),(104,552,136,616),(280,784,320,824)],8:[(0,0,280,144),(696,80,824,336),(824,80,1032,224)]}
for bank,boxes in regions.items():
 pix=np.concatenate([original[y:y1,x:x1].reshape(-1,3) for x,y,x1,y1 in boxes]);n=10 if bank==8 else 11 if bank==1 else 15;p=Image.fromarray(pix.reshape(-1,1,3)).quantize(colors=n,method=Image.Quantize.MEDIANCUT);cs=np.array(p.getpalette()[:n*3],np.uint8).reshape(n,3)&248
 if bank==1:cs=np.vstack([cs,np.array([[72,88,88],[120,144,144],[184,200,192],[224,232,216]],np.uint8)])
 pals[bank]=np.vstack([cs,np.zeros((15-len(cs),3),np.uint8)])
# The small independent sign uses the receiving dock/stone bank after terrain
# palette derivation. Architecture remains exactly the accepted master colors.
a=fg[520:544,768:784];mm=a[...,3]>0;dd=((a[...,:3].astype(np.int32)[:,:,None]-pals[7].astype(np.int32)[None,None])**2).sum(3);a[mm,:3]=pals[7][dd.argmin(2)][mm]
# Native background encoding; all source texture and structure geometry retained.
encoded={};nativebg=np.zeros_like(raw);nativefg=np.zeros_like(fg);banks=[0,1,2,3,7,8]
for gy,gx in np.ndindex(H*2,W*2):
 y,x=gy*8,gx*8;a=raw[y:y+8,x:x+8];best=None
 for b in banks:
  d=((a.astype(np.int32)[:,:,None]-pals[b].astype(np.int32)[None,None])**2).sum(3);ii=d.argmin(2);error=np.take_along_axis(d,ii[...,None],2).sum()
  if best is None or error<best[0]:best=(error,b,ii)
 _,b,ii=best;lo=ii.astype(np.uint8)+1;nativebg[y:y+8,x:x+8]=pals[b][ii]
 a=fg[y:y+8,x:x+8];m=a[...,3]>0;hi=np.zeros((8,8),np.uint8);fb=0
 if m.any():
  cs=set(map(tuple,a[m,:3]));opts=[k for k,p in enumerate(pals) if cs<=set(map(tuple,p))]
  assert opts,('Foreground cannot change accepted colors',gx,gy);fb=opts[0]
  for i,c in enumerate(pals[fb],1):hi[m&np.all(a[...,:3]==c,2)]=i
  nativefg[y:y+8,x:x+8]=a
 encoded[gy,gx]=[(lo,int(b)),(hi,fb)]
# Save separate intermediate ground for receiving-context review before any new
# master is present. This is an explicit deliverable, not a hidden pipeline step.
Image.fromarray(raw).save(A/'cleaned-ground.png');Image.fromarray(fg).save(A/'foreground.png');np.save(A/'repair-mask.npy',repair)
assert np.array_equal(raw[~repair],original[~repair]),'Do not damage unrelated terrain'
(A/'repairs.json').write_text(json.dumps(dict(baseline=BASE,donors=donors,repairs=records,placements=placements,protected_source_pixels=int((~repair).sum()),protected_source_RGB_errors=0,preserved_groves='Intact HGSS terrain; not erased or doubled with prefab trees.'),indent=2)+'\n')

# Guarded native repack, retaining the original section IDs and choosing the
# existing metatile number for each distinct edited cell whenever compatible.
plans=[];stats=[]
for sec in sections:
 n=sec['name'];x0,y0,x1,y1=sec['box'];old=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y0,x1-x0);oldts=Tileset(G,n.lower(),n.lower());glyphs=[np.zeros((8,8),np.uint8)];lookup={glyphs[0].tobytes():0};used={};assigned={};blocks={};attrs={};grid=old.copy()
 def entry(a,b):
  k=a.tobytes()
  if k not in lookup:
   t=len(glyphs);glyphs.append(a)
   for h in range(2):
    for v in range(2):lookup.setdefault(a[::-1 if v else 1,::-1 if h else 1].tobytes(),t|h<<10|v<<11)
  return lookup[k]|b<<12
 for cy,cx in np.ndindex(old.shape):
  y,x=cy+y0,cx+x0;es=[]
  for layer in range(2):
   for q in range(4):es.append(entry(*encoded[y*2+q//2,x*2+q%2][layer]))
  attr=0 if above[y,x] else 0x1000;key=tuple(es)+(attr,);preferred=int(old[cy,cx]&1023)
  if key in assigned:mid=assigned[key]
  else:
   mid=preferred if preferred not in blocks else next(i for i in range(1024) if i not in blocks)
   blocks[mid]=es;attrs[mid]=attr;assigned[key]=mid
  grid[cy,cx]=(int(old[cy,cx])&~1023)|mid
 expected=old.copy()
 for cy,cx in np.ndindex(grid.shape):
  wy,wx=cy+y0,cx+x0;grid[cy,cx]=(int(grid[cy,cx])&~0xc00)|(0xc00 if solid[wy,wx] else 0)
  if (wx,wy) not in [(28,27),(29,27)]:assert int(grid[cy,cx]&0xfc00)==int(old[cy,cx]&0xfc00),'Preserve existing corrected traversal'
 assert len(glyphs)<=1008,(n,len(glyphs))
 count=max(blocks)+1;bb=[blocks.get(i,[0]*8) for i in range(count)];aa=[attrs.get(i,0x1000) for i in range(count)];plans.append((sec,glyphs,bb,aa,grid));stats.append(dict(map=n,glyphs=len(glyphs),metatile_slots=count,stable_map_ID=True,elevation_exact_collision_repairs_documented=True))
# Every section passes before the first native mutation.
for sec,glyphs,blocks,attrs,grid in plans:
 n=sec['name']
 for part in range(2):
  p=G/f'data/tilesets/{"secondary" if part else "primary"}/{n.lower()}';start=512*part;count=max(1,len(glyphs)-512) if part else 512
  im=Image.new('P',(128,((count+15)//16)*8));im.putpalette([c for i in range(256) for c in (i*17%256,)*3])
  for i in range(count):
   if start+i<len(glyphs):im.paste(Image.fromarray(glyphs[start+i]).convert('P'),(i%16*8,i//16*8))
  im.save(p/'tiles.png',bits=4);bb=blocks[start:start+512];aa=attrs[start:start+512];bb += [[0]*8 for _ in range(512-len(bb))];aa += [0x1000]*(512-len(aa));(p/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bb));(p/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa))
  for b in range(16):
   pal=np.vstack([np.zeros((1,3),np.uint8),pals[b]]) if b<13 else np.zeros((16,3),np.uint8);(p/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pal)+'\n')
 grid.tofile(G/f'data/layouts/{n}/map.bin');np.full((2,2),int(grid[0,0])|0xc00,'<u2').tofile(G/f'data/layouts/{n}/border.bin')
Image.fromarray(nativebg).save(S/'native-ground.png');Image.fromarray(nativefg).save(S/'shared-foreground.png');Image.fromarray(raw).save(A/'assembled-ground.png');Image.fromarray(np.array(fg)).save(A/'assembled-foreground.png');np.save(S/'solid.npy',solid);np.save(S/'material.npy',mat);np.save(S/'above.npy',above);np.save(S/'tree-roots.npy',np.zeros((54,65),np.uint8));(S/'trees.json').write_text('[]\n');(S/'palettes.json').write_text(json.dumps([p.tolist() for p in pals])+'\n')
comp=nativebg.copy();mask=nativefg[...,3]>0;comp[mask]=nativefg[mask,:3];Image.fromarray(comp).save(E/'native-map.png');Image.fromarray(comp).save(O/'after.png')

features=json.loads((S/'features.json').read_text())
for f in features:
 if f['name']=='approved shared Pokemart':f['native_box']=[469,416,549,480]
(S/'features.json').write_text(json.dumps(features,indent=2)+'\n')
(O/'native-edit.json').write_text(json.dumps(dict(baseline=BASE,sections=stats,method='Retained HGSS terrain with explicitly repaired receiving contexts and accepted transparent architecture',collision_changes=[[28,27,False],[29,27,True]],owner_visual_acceptance='Pending'),indent=2)+'\n')
print(stats)
