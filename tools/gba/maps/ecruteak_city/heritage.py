"""One-time native heritage architecture patch, pinned to reviewed 10387445.
Asset conversion uses the approved concept sheet; no source layout replay.
Run prepare first, then solve exact native palette covers and run pack separately.
"""
from pathlib import Path
import sys,json,subprocess,shutil,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'heritage';B=D/'baseline';M=S/'masters';G=Path(sys.argv[1]);BASE='103874452f101ba3f597cafcca73c1aa1e32998d'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True).strip(),'Preserve native edits.'
assert not B.exists(),'One-time source patch already prepared; preserve its baseline.'
D.mkdir(exist_ok=True);B.mkdir();shutil.copytree(M,B/'masters')
for n in ['background.png','foreground.png','solid.npy','behaviors.npy','material-grid.npy','ground-material-grid.npy','tree-footprints.npy']:shutil.copyfile(S/n,B/n)
for n in ['assembly.json','native-map.png']:shutil.copyfile(E/n,B/n)
shutil.copyfile(S/'tree-closure/above.npy',B/'above.npy')
for bank in ['ecruteak_city','ecruteak_temple']:shutil.copyfile(S/bank/'exact-palette-cover.json',B/(bank+'-cover.json'))
shutil.copyfile(sys.argv[2],D/'approved-assets.png');shutil.copyfile('/workspace/generated_images/exec-a6984221-5f35-405a-981f-90492b9efb5d.png',D/'approved-concept.png')
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')};bg=np.array(Image.open(B/'background.png'));fg=np.array(Image.open(B/'foreground.png'));solid=np.load(B/'solid.npy');ground=np.load(B/'ground-material-grid.npy');mat=np.load(B/'material-grid.npy');above=np.load(B/'above.npy');r=json.loads((B/'assembly.json').read_text());oldps=r['placements'];oldart={k:v.copy() for k,v in art.items()};Y,X=np.indices(bg.shape[:2]);regions=[]
def save(n,a):art[n]=a;Image.fromarray(a).save(M/(n+'.png'))
def nearest(a,pal):
 a=a.copy();p=np.array(pal,np.int16);v=a[...,:3].astype(np.int16);idx=np.argmin(((v[:,:,None,:]-p[None,None,:,:]).astype(np.int32)**2).sum(3),2);a[...,:3]=p[idx];a[...,3]=np.where(a[...,3]>=128,255,0);a[a[...,3]==0]=0;return a
# All foliage variants share precisely the approved green alpha/geometry.
green=art['tree-hgss'];leaves=[(56,56,32),(64,72,32),(80,96,32),(96,120,32),(112,144,32),(136,168,40)]
for name,ramp in [('tree-amber',[(80,56,32),(112,72,32),(152,96,32),(192,128,40),(224,160,48),(240,192,80)]),('tree-autumn',[(80,40,24),(112,48,24),(152,56,24),(192,72,32),(224,96,40),(240,128,56)])]:
 a=green.copy()
 for c,d in zip(leaves,ramp):a[np.all(green[...,:3]==c,2)&(green[...,3]>0),:3]=d
 save(name,a);assert np.array_equal(a[...,3],green[...,3])
# Isolate each generated architectural prototype; map once to the accepted
# house material palette before it becomes game art. No whole-map resampling.
sheet=np.array(Image.open(D/'approved-assets.png').convert('RGBA'));labs,n=label(sheet[...,3]>128);parts=[]
for i in range(1,n+1):
 yy,xx=np.where(labs==i)
 if len(xx)>1000:parts.append((xx.min(),yy.min(),xx.max()+1,yy.max()+1))
parts.sort();assert len(parts)==3,parts
pal=sorted(set(map(tuple,art['house'][art['house'][...,3]>0,:3])))
for (name,size),box in zip([('heritage-shrine',(48,64)),('red-lantern',(16,32)),('offering-counter',(32,16))],parts):
 a=np.array(Image.fromarray(sheet).crop(box).resize(size,Image.Resampling.LANCZOS));a=nearest(a,pal);save(name,a)
# Match the approved red timber vocabulary without changing the torii silhouette.
a=nearest(art['south-gate'],pal);save('heritage-torii',a)
# Scaffolding is built from a compact repeating timber module, not a new tower.
a=Image.new('RGBA',(16,112));draw=ImageDraw.Draw(a)
for x in [2,12]:
 draw.rectangle((x,0,x+2,111),fill=(48,40,32,255));draw.line((x+1,0,x+1,111),fill=(184,168,128,255))
for y in range(8,112,24):
 draw.rectangle((0,y,15,y+3),fill=(88,72,56,255));draw.line((0,y,15,y),fill=(184,168,128,255));draw.line((3,y+4,12,min(111,y+23)),fill=(128,112,96,255),width=2)
save('restoration-scaffold',np.array(a))
# A small hanging archive scroll, sharing the same house/lantern materials.
a=Image.new('RGBA',(16,32));draw=ImageDraw.Draw(a);draw.rectangle((1,2,14,4),fill=(48,40,32,255));draw.rectangle((3,5,12,25),fill=(184,168,128,255));draw.rectangle((3,26,12,27),fill=(88,72,56,255));draw.line((7,8,7,21),fill=(64,56,24,255));draw.line((6,11,10,11),fill=(64,56,24,255));draw.line((5,17,9,17),fill=(64,56,24,255));save('archive-scroll',np.array(a))
# All new geometry is a local adaptation of the accepted current map.
cleared={(58,14),(60,14),(58,16),(60,16)};rename={'maple-hgss':'tree-hgss','maple-amber':'tree-amber','maple-autumn':'tree-autumn'}
r['trees']=[dict(t,name=rename.get(t['name'],t['name'])) for t in r['trees'] if (t['x'],t['y']) not in cleared]
newps=[]
for p in oldps:
 q=p.copy();n=p['name']
 if n in ['tree-hgss','maple-hgss','maple-amber','maple-autumn']:
  if (p['x']//16,p['y']//16) in cleared:continue
  q['name']=rename.get(n,n)
 if n in ['house-lantern','shrine-lantern']:
  q['name']='red-lantern';q['x']=(p['x']//16)*16;q['y']=(p['y']//16)*16
 if n=='south-gate':q.update(name='heritage-torii',x=632,y=688)
 newps.append(q)
def add(n,x,y,role):newps.append(dict(name=n,x=x,y=y,source_xy=None,role=role))
add('restoration-scaffold',336,112,'Tower restoration: west upright course')
add('restoration-scaffold',480,112,'Tower restoration: east upright course')
add('heritage-shrine',544,464,'Central wayside shrine with south-facing stone steps')
add('offering-counter',520,528,'Unattended wrapped-offering counter; inspection only')
add('archive-scroll',608,368,'Traditional archive identification; no new NPCs')
add('heritage-shrine',928,256,'Pond shrine: eastern cleared grove, south-facing steps')
add('red-lantern',912,304,'Pond shrine western approach light')
add('red-lantern',976,304,'Pond shrine eastern approach light')
add('red-lantern',672,512,'Theater western approach light')
add('red-lantern',816,512,'Theater eastern approach light')
add('P12',976,336,'Pond shrine public inscription')
# The tower sign already sits beside its approach, not in a new cluttered worksite.
# Owner pixels identify all old shapes that need removal, including palette-split BG.
owner=np.zeros(bg.shape[:2],np.int32)
for i,p in enumerate(oldps):
 a=oldart[p['name']];h,w=a.shape[:2];v=owner[p['y']:p['y']+h,p['x']:p['x']+w];v[a[...,3]>0]=i+1
changed_names={'tree-hgss','maple-hgss','maple-amber','maple-autumn','house-lantern','shrine-lantern','south-gate'}
mask=np.zeros(bg.shape[:2],bool)
for i,p in enumerate(oldps):
 if p['name'] in changed_names:mask|=owner==i+1
# New features and changed old feature bounds are reassembled at their full joins.
for p in newps:
 if p not in oldps:
  a=art[p['name']];h,w=a.shape[:2];mask[p['y']:p['y']+h,p['x']:p['x']+w]=True
# Restore hidden original terrain only at removed/changed art; preserve all court
# and wall join pixels outside these shapes. All affected canopy backing is lawn.
for yy,xx in np.argwhere(mask):
 code=ground[yy//16,xx//16];name={'P':'paving','C':'court','W':'water'}.get(str(code),'grass');a=art[name];bg[yy,xx]=a[(yy-16)%len(a),(xx-64)%a.shape[1]]
fg[mask]=0
# Preserve complete ground edges along the new pond shrine court.
def ground_rect(x,y,w,h,n,code):
 a=art[n];bg[y:y+h,x:x+w]=a[(Y[y:y+h,x:x+w]-16)%len(a),(X[y:y+h,x:x+w]-64)%a.shape[1]];fg[y:y+h,x:x+w]=0;mask[y:y+h,x:x+w]=True;ground[y//16:(y+h)//16,x//16:(x+w)//16]=code
# Small warm stone court east of the existing water, linked to the broad south bank.
ground_rect(912,240,80,112,'court','C');ground_rect(896,336,96,16,'paving','P')
# Reassemble only affected pixels in the accepted placement order. This preserves
# which trees sit behind buildings; new structures follow existing foreground.
for p in newps:
 a=art[p['name']];h,w=a.shape[:2];m=(a[...,3]>0)&mask[p['y']:p['y']+h,p['x']:p['x']+w];fg[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m]
# Tree-foot collision remains two cells wide and two cells deep, with exact roots.
roots=np.zeros((52,72),np.uint8)
for t in r['trees']:roots[t['y']+1:t['y']+3,t['x']:t['x']+2]+=1
assert roots.max()==1
oldroots=np.load(B/'tree-footprints.npy');removed=(oldroots>0)&(roots==0);solid[removed]=False;mat[removed]=ground[removed];above[removed]=False
solid[roots>0]=True;mat[roots>0]='T'
for t in r['trees']:above[t['y'],t['x']:t['x']+2]=True
# New shrine body is solid; its actual bottom tread is walkable, allowing a close
# front inspection. Lantern chambers are foreground; only footing cells block.
features=[]
def block(x,y,w,h,n):solid[y:y+h,x:x+w]=True;mat[y:y+h,x:x+w]=n;above[y:y+h,x:x+w]=False
for x,y in [(34,29),(58,16)]:block(x,y,3,3,'B');features.append(dict(name='shrine',x=x,y=y,width=3,solid_rows=3,front=[x+1,y+3]))
block(32,33,2,1,'B')
# All lamp bases map to their own visible bottom 16px cell; their caps stay above.
# Old lantern bases coincide with these same placements (no phantom old footing).
for p in newps:
 if p['name']=='red-lantern':
  x,y=p['x']//16,p['y']//16;block(x,y+1,1,1,'L');above[y,x]=True
# The gate sits on an 8px half-cell visual offset: symmetry is independent of
# its two whole-cell walking lanes. The solid posts join the forest on both sides.
solid[43:47,39:45]=roots[43:47,39:45]>0;mat[43:47,39:45]=ground[43:47,39:45];mat[43:47,39:45][roots[43:47,39:45]>0]='T';above[43:47,39:45]=False
for t in r['trees']:
 if t['y'] in [44,46]:above[t['y'],t['x']:t['x']+2]=True
a=art['heritage-torii']
for yy,xx in np.argwhere(a[...,3]>0):
 x,y=(632+xx)//16,(688+yy)//16;mat[y,x]='B'
 if yy>=39:solid[y,x]=True
 else:above[y,x]=True
assert np.where(~solid[45])[0].tolist()==[41,42]
# Archive scroll overlays the established blocked building edge; no added NPCs.
r['placements']=newps;r['heritage_adaptations']=['Identical approved green master geometry for all leaf colors','Four complete trees removed east of pond for a traditional shrine court','One red lantern master across the city','Central shrine and unattended offering counter','Restoration scaffolding and public notice','Southern arch centered at an 8px offset, native lanes 41/42 preserved']
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
for n,a in [('solid',solid),('material-grid',mat),('ground-material-grid',ground),('tree-footprints',roots)]:np.save(S/(n+'.npy'),a)
np.save(S/'tree-closure/above.npy',above);np.save(D/'above.npy',above);np.savez_compressed(D/'changed-pixels.npz',mask=mask)
(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');preview=bg.copy();m=fg[...,3]>0;preview[m]=fg[m];Image.fromarray(preview).save(D/'preview.png')
(D/'edit-report.json').write_text(json.dumps(dict(baseline_source=BASE,approved_concept='Simplified owner-approved concept; no characters, flower beds or statues',asset_provenance='Image-generated architectural sheet derived from owner-approved concept; native RGB5 conversion to existing house palette',cleared_trees=sorted(cleared),tree_count=len(r['trees']),shrine_geometry=features,gate_visual_center_x=672,gate_position=[632,688],gate_passage_columns=[41,42],materials='Existing green tree master, existing local wood/roof palette, native court/paving textures',new_master_hashes={n:hashlib.sha256((M/(n+'.png')).read_bytes()).hexdigest() for n in ['heritage-shrine','red-lantern','offering-counter','restoration-scaffold','archive-scroll','heritage-torii','tree-autumn','tree-amber']}),indent=2)+'\n')
print('Prepared heritage source',len(r['trees']),'complete trees, no NPCs')
