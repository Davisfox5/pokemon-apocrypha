"""Narrow forest refinement of native 116ea801; no terrain-generator replay.

Rows are counted from the registered HGSS overview. Canopy overlap is visual;
trunk footprints remain separate. Current cliffs, stairs and non-tree art are
inputs, with explicit ground restoration only where moved trees expose it.
"""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G,PT=map(Path,sys.argv[1:3]);S=ROOT/'gba/art/olivine-city/source'
PREV=S/'terrain-reset';T=S/'forest-refinement';E=S.parent/'evidence/forest-refinement'
T.mkdir(exist_ok=True);E.mkdir(exist_ok=True);(T/'masters').mkdir(exist_ok=True)
BASE='116ea8011c958d10bf5d61daf2d879cca9e8a184'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
tracked=subprocess.check_output(['git','-C',str(G),'ls-files','data/layouts/JohtoOlivineCity','data/layouts/JohtoOlivineQuay','data/tilesets/primary/olivine_city','data/tilesets/secondary/olivine_city','data/tilesets/primary/olivine_quay','data/tilesets/secondary/olivine_quay'],text=True).splitlines()
def digest(raw,p):return hashlib.sha256(raw.replace(b'\r\n',b'\n') if p.endswith('.pal') else raw).hexdigest()
last=json.loads((T/'last-output.json').read_text()) if (T/'last-output.json').exists() else {}
for p in tracked:
 raw=(G/p).read_bytes();baseline=subprocess.check_output(['git','-C',str(G),'show',BASE+':'+p])
 assert digest(raw,p) in [digest(baseline,p),last.get(p)],'Unrecognized native change: '+p
assembly=json.loads((S.parent/'evidence/terrain-reset/assembly.json').read_text())
bg=np.array(Image.open(PREV/'background.png').convert('RGBA'));oldfg=np.array(Image.open(PREV/'foreground.png').convert('RGBA'))
solid=np.load(PREV/'solid.npy');beh=np.load(PREV/'behaviors.npy');above=np.load(PREV/'above.npy');mat=np.load(PREV/'material-grid.npy');ground=np.load(PREV/'ground-material-grid.npy')
wall=np.array(Image.open(PREV/'wall-mask.png'))>0;rock=np.array(Image.open(PREV/'rock-layer.png'))
W,H=72,56;OX,OY=64,16;Y,X=np.indices(bg.shape[:2]);SX,SY=X-OX,Y-OY
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (S/'masters').glob('*.png')}
for a in art.values():a[...,:3]&=248
if not (T/'baseline-verified.json').exists():
 for d in assembly['districts']:
  ts=Tileset(G,d['tileset'],d['tileset']);grid=np.fromfile(G/'data/layouts'/d['map']/'map.bin','<u2');im=np.array(ts.map_image(grid.tolist(),W));y=d['global_y']*16;h=d['height']*16;expected=bg[y:y+h].copy();m=oldfg[y:y+h,:,3]>0;expected[m]=oldfg[y:y+h][m];assert np.array_equal(im,expected[...,:3])
 (T/'baseline-verified.json').write_text(json.dumps(dict(commit=BASE,decoded_pixel_errors=0),indent=2)+'\n')

# The unobscured eastern shore crown is 44px wide, versus the unsuitable 28px
# visible shared crown. Preserve original leaf clusters, unscaled, in its native
# RGB5 tree palette. An explicit silhouette excludes the adjacent cliff entirely.
ref=np.array(Image.open(S/'hgss-reference.png').convert('RGB'))
donor=(876,264,924,328)
outline=[(900,272),(904,274),(905,279),(910,281),(913,286),(917,289),(918,294),(921,297),(920,301),(917,304),(916,309),(912,312),(908,314),(904,316),(903,319),(897,319),(895,316),(891,314),(887,312),(884,308),(881,305),(880,300),(879,296),(881,292),(884,288),(887,284),(890,280),(895,278),(897,274)]
mask=Image.new('L',(48,64));ImageDraw.Draw(mask).polygon([(x-876,y-264) for x,y in outline],fill=255);m=np.array(mask)>0
palette=np.unique(art['tree'][art['tree'][...,3]>0,:3],axis=0)
palette=np.array([c for c in palette if tuple(c) not in [(64,64,40),(88,104,32),(88,112,32)]],np.uint8)
a=ref[264:328,876:924].astype(int);tree=np.zeros((64,48,4),np.uint8);tree[m,:3]=palette[np.argmin(((a[m,None,:]-palette.astype(int))**2).sum(2),1)];tree[m,3]=255
art['olivine-tree']=tree;Image.fromarray(tree).save(T/'masters/olivine-tree.png')
(T/'tree-provenance.json').write_text(json.dumps(dict(authority='HGSS Olivine overview',donor=list(donor),outline=outline,palette='Eight shades from the accepted Johto tree RGB5 ladder; near-duplicate shades consolidated locally, retaining leaf clusters and trunk',geometric_scaling=False,reason='Original broad overlapping crowns and 32 by approximately 24px spacing; the previous narrow 32px master and 32px row pitch exposed old tree-shaped cliff occlusions.'),indent=2)+'\n')
# Harmonize the independently quantized local residences with one existing
# roof/timber/window palette. No shared Center/Mart asset or geometry changes.
house_before=art['house'].copy();hm=house_before[...,3]>0
hp=np.unique(art['house-pair'][art['house-pair'][...,3]>0,:3],axis=0)
hv=house_before[hm,:3].astype(int);art['house'][hm,:3]=hp[np.argmin(((hv[:,None]-hp.astype(int))**2).sum(2),1)]
Image.fromarray(art['house']).save(T/'masters/house.png')
(T/'house-palette.json').write_text(json.dumps(dict(master='house',palette_authority='existing local house-pair',geometry_changes=0,changed_pixels=int(np.any(house_before!=art['house'],2).sum()),reason='Consistent roof and timber ramps across local residences; reserves native palette space for complete broad crowns at roof joins'),indent=2)+'\n')

# Measured rows, explicitly separated from map-edge completion. Coordinates
# denote crown centers / apex, before registration. Rounding to the 8px glyph
# grid keeps whole leaf clusters; no image resampling or count-based culling.
rows=[];new=[]
def row(name,centers,apex,reference_count=None,padding=()):
 centers=list(centers);padding=list(padding)
 rows.append(dict(name=name,source_apex_y=apex,source_centers_x=centers,reference_count=len(centers) if reference_count is None else reference_count,native_reference_count=len(centers),padding_centers_x=padding,native_total=len(centers)+len(padding)))
 for cx in centers+padding:new.append(dict(name='olivine-tree',x=cx-24+OX,y=apex-8+OY,source_xy=[cx-24,apex-8],role=name,padding=cx in padding))
row('NW cropped back row completed',range(4,261,32),-8,padding=[-28])
row('NW separated middle row',range(52,277,32),24)
row('NW upper dense row',range(36,293,32),72)
row('NW lower dense row',range(36,293,32),96)
row('west border upper', [4],24,padding=[-28])
row('west border upper join',[4],48,padding=[-28])
row('west border north join',[4],72,padding=[-28])
row('west border dense join',[4],96,padding=[-28])
for i,y in enumerate([120,144,168,200,224,248,272,296,320,344,368,392]):row(f'west border {i+1:02}',[4,36,68],y,padding=[-28])
row('Route 39 west sentinel',[324],-8)
row('NE cropped back row completed',range(548,1029,32),-8,padding=[1060])
row('NE high terrace front',range(548,1029,32),16,padding=[1060])
row('NE lower terrace back',range(548,1029,32),80,padding=[1060])
row('NE lower terrace front',range(580,1029,32),104,padding=[1060])
row('residential west sentinel',[532],128)
row('residential shelf pair',[628,660],152)
for i,y in enumerate([128,152,176]):row(f'east forest broad {i+1}',range(708,1029,32),y,padding=[1060])
row('east forest shoulder',range(708,838,32),200)
for i,y in enumerate([224,248,272,296,320,344]):row(f'lighthouse grove {i+1}',[708,740,772,804],y)
row('stair courtyard pair',[500,532],296)
row('stair courtyard middle',[500],320)
row('stair courtyard front',[500],344)
row('east shore upper',[884],224)
row('east shore outer',[900],272)
row('east shore inner',[852],288)
row('east shore south back',[868],440)
row('east shore south front',[868],464)
new.sort(key=lambda p:(p['y'],p['x']))
(T/'tree-rows.json').write_text(json.dumps(rows,indent=2)+'\n')

# Recompose recorded foreground ownership. Non-tree geometry/order is retained;
# the local house palette is harmonized above. Timber comes from native input.
fg=np.zeros_like(oldfg);without_trees=np.zeros_like(oldfg);oldtree=np.zeros(bg.shape[:2],bool);newtree=oldtree.copy();prop_scope=oldtree.copy();placements=[]
def stamp(p,target):
 a=art[p['name']];h,w=a.shape[:2];x,y=p['x'],p['y'];m=a[...,3]>0
 assert 0<=x and 0<=y and x+w<=W*16 and y+h<=H*16
 target[y:y+h,x:x+w][m]=a[m]
for p in assembly['placements']:
 if p['name']=='tree':
  a=art['tree'];oldtree[p['y']:p['y']+48,p['x']:p['x']+32]|=a[...,3]>0
for n in new:
 stamp(n,fg);placements.append(n);newtree[n['y']:n['y']+64,n['x']:n['x']+48]|=tree[...,3]>0
for p in assembly['placements']:
 if p['name']=='tree':
  continue
 if p['name']=='land-rock' and p['source_xy'] in [[848,256],[848,448]]:
  a=art['land-rock'];h,w=a.shape[:2];x,y=p['x'],p['y'];prop_scope[y:y+h,x:x+w]|=a[...,3]>0
  p=dict(p);sx,sy=([832,256] if p['source_xy']==[848,256] else [848,416]);p.update(x=sx+OX,y=sy+OY,source_xy=[sx,sy],role='shore boulder reseated at HGSS rock socket; clears full tree crown')
  prop_scope[p['y']:p['y']+h,p['x']:p['x']+w]|=a[...,3]>0
 if p['name'] in ['stairs','ramp']:
  x,y=p['x'],p['y'];w,h=(48,24) if p['name']=='stairs' else (64,64)
  # The reference-shaped ramp's top rail projects one pixel above its original
  # placement rectangle; preserve that complete tip from the native input.
  if p['name']=='ramp':y-=1;h+=1
  fg[y:y+h,x:x+w]=oldfg[y:y+h,x:x+w];without_trees[y:y+h,x:x+w]=oldfg[y:y+h,x:x+w]
 else:stamp(p,fg);stamp(p,without_trees)
 if p['name']=='house':
  h,w=art['house'].shape[:2];prop_scope[p['y']:p['y']+h,p['x']:p['x']+w]|=np.any(art['house']!=house_before,2)
 placements.append(p)

# Undo hidden-background optimizations only beneath old/new crowns. Restore
# their actual wall material where the current accepted contour says stone.
scope=oldtree|newtree|prop_scope
grass=art['grass'][SY%16,SX%16]
receiving=grass.copy()
# Coastal crowns cross a sand receiving strip; never restore them as a grass
# silhouette. The whole shore strip is completed by the understory pass below.
shore=(SX>=850)&(SX<888)&(SY>=380)&(SY<568)
receiving[shore]=art['sand'][SY[shore]%16,SX[shore]%16]
west_beach=(SX<104)&(SY>=468)&(SY<650)
receiving[west_beach]=art['sand'][SY[west_beach]%16,SX[west_beach]%16]
bg[scope]=receiving[scope];bg[scope&wall]=rock[scope&wall]
from forest_understory import rebuild
terrain_scope,terrain_ledger=rebuild(bg,rock,wall,art,ref);scope|=terrain_scope
(T/'understory-reconstruction.json').write_text(json.dumps(terrain_ledger,indent=2)+'\n')
from forest_textures import tidy
texture_scope,texture_report=tidy(bg,rock,wall,fg,ref,PREV);scope|=texture_scope
(T/'texture-joins.json').write_text(json.dumps(texture_report,indent=2)+'\n')
# Native root occupancy, independent of the wider overlapping canopy. One
# 16px deep trunk row matches the reference's 24px row pitch without ghost roots.
oldroots=np.load(S/'tree-footprints.npy')>0
oldroots|=terrain_scope.reshape(H,16,W,16).any(axis=(1,3))
for y,x in zip(*np.where(oldroots)):
 sl=np.s_[y*16:y*16+16,x*16:x*16+16]
 pixels=bg[sl][...,:3];water_colors=np.unique(art['water'][...,:3].reshape(-1,3),axis=0)
 iswater=np.any(np.all(pixels[:,:,None,:]==water_colors,3),2).mean()>.5
 sand_colors=np.unique(art['sand'][...,:3].reshape(-1,3),axis=0)
 issand=(np.any(np.all(pixels[:,:,None,:]==sand_colors,3),2)&~wall[sl]).mean()>.5
 isrock=wall[sl].mean()>.28
 solid[y,x]=isrock or iswater;beh[y,x]=16 if iswater else 0
 ground[y,x]='R' if isrock else 'W' if iswater else 'S' if issand else '.';mat[y,x]=ground[y,x];above[y,x]=False
# Clear the old upper canopy priority where no non-tree feature owns the cell.
for p in assembly['trees']:
 x,y=p['x'],p['y'];above[y,x:x+2]=False
roots=np.zeros((H,W),np.uint8);trees=[]
for p in new:
 x,y=p['x'],p['y'];cx=(x+12)//16;cy=(y+48)//16
 roots[cy:cy+1,cx:cx+2]+=1;solid[cy:cy+1,cx:cx+2]=True;beh[cy:cy+1,cx:cx+2]=0;mat[cy:cy+1,cx:cx+2]='T'
 above[y//16:cy,(x+3)//16:(x+45+15)//16]=True
 trees.append(dict(name='olivine-tree',pixel_x=x,pixel_y=y,root_box=[cx,cy,cx+2,cy+1],row=p['role'],padding=p['padding']))
assert roots.max()==1,'Trunks overlap; do not silently drop a tree.'
for p in placements:
 if p['name']=='land-rock':
  x0,y0=(p['x']+8)//16,(p['y']+16)//16;x1,y1=(p['x']+24+15)//16,(p['y']+32+15)//16
  solid[y0:y1,x0:x1]=True;beh[y0:y1,x0:x1]=0;mat[y0:y1,x0:x1]='R'
solid[0]=True;solid[-1]=True;solid[:,0]=True;solid[:,-1]=True

# Preserve stair/ramp traversal and architecture priority exactly. A broader
# crown may occlude another crown, but it cannot change a building's layer rule.
oldabove=np.load(PREV/'above.npy');oldmat=np.load(PREV/'material-grid.npy')
nonforest=np.isin(oldmat,['B','A','S','F']);above[nonforest]=oldabove[nonforest]
assembly['trees']=trees;assembly['placements']=placements
assembly['tree_master_directory']='forest-refinement/masters';assembly['tree_row_ledger']='tree-rows.json'
Image.fromarray(bg).save(T/'receiving-surfaces.png')
uncovered=bg.copy();m=without_trees[...,3]>0;uncovered[m]=without_trees[m]
Image.fromarray(uncovered).save(E/'trees-hidden.png')
from reset_tiles import hidden_background
for y in range(0,H*16,8):
 for x in range(0,W*16,8):
  sl=np.s_[y:y+8,x:x+8]
  if np.all(fg[sl][...,3]==255):bg[sl]=grass[sl]
hidden=hidden_background(bg,fg)
(T/'hidden-background-reuse.json').write_text(json.dumps(hidden,indent=2)+'\n')
for name,a in [('background',bg),('foreground',fg),('rock-layer',rock)]:Image.fromarray(a).save(T/(name+'.png'))
for name,a in [('wall-mask',wall),('scope-mask',scope)]:Image.fromarray((a*255).astype(np.uint8)).save(T/(name+'.png'))
for name,a in [('above',above),('solid',solid),('behaviors',beh),('material-grid',mat),('ground-material-grid',ground),('tree-footprints',roots)]:np.save(T/(name+'.npy'),a)
composite=bg.copy();m=fg[...,3]>0;composite[m]=fg[m];Image.fromarray(composite).save(E/'native-proposal.png')
(E/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
print('trees',len(trees),'rows',len(rows),flush=True)
if '--preview' in sys.argv:raise SystemExit(0)
rockpal=np.array([(88,56,32),(112,72,40),(136,88,48),(152,104,56),(176,128,72),(192,152,96),(216,184,120)],np.uint8)
mods={'front':np.dstack([rockpal.reshape(1,-1,3),np.full((1,len(rockpal)),255,np.uint8)]),'plateau-top':art['cliff-top']}
from compile_planes import compile_planes
stats=compile_planes(G,PT,S,T,E,assembly,bg,fg,above,solid,beh,mods)
(T/'last-output.json').write_text(json.dumps({p:digest((G/p).read_bytes(),p) for p in tracked},indent=2)+'\n')
print(json.dumps(stats,indent=2))
