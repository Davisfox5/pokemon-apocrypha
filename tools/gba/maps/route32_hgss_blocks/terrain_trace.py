"""Original-HGSS material tracing, separate from foot collision.
Classify visible source colors; keep explicit continuity only under occluders.
Never samples a native map to decide HGSS material identity.
"""
from pathlib import Path
import json,csv
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label as connected_components
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=ROOT/'gba/art/route32-hgss-blocks';S=OUT/'source';E=OUT/'evidence'
COLORS={'.':(104,208,160),'P':(224,200,136),'G':(40,136,80),'R':(184,136,104),'W':(40,104,248),'D':(176,144,104),'S':(192,192,192),'_':(104,72,56),'T':(88,112,40),'B':(240,96,64),'H':(72,72,88),'?':(224,64,224)}
raw=np.array(Image.open(S/'hgss-reference.png').convert('RGB'));rgb=raw[:2000,:480].astype(int);r,g,b=rgb.transpose(2,0,1)
labels=np.full((2000,480),'?',dtype='<U1')
lawn=(g>=168)&(b>=128)&(g-r>=48);labels[lawn]='.'
tall=np.isin(rgb.view([('',rgb.dtype)]*3).reshape(rgb.shape[:2]),np.array([(16,96,64),(32,112,80),(32,120,88),(40,136,80),(56,152,88),(64,168,112),(80,192,120)],dtype=rgb.dtype).view([('',rgb.dtype)]*3).ravel());labels[tall]='G'
path=(r>=184)&(g>=168)&(r-g>=8)&(r-g<=40)&(g-b>=40);labels[path]='P'
# The visible dirt stub beneath the railway is darkened by the bridge shadow.
sy,sx=np.indices(r.shape);shadow_path=(sy>=1024)&(sy<1136)&(sx<144)&(r>=96)&(g>=80)&(r-g>=8)&(r-g<32)&(g-b>=28)
labels[shadow_path]='P'
rock=(r>=80)&(r-g>=32)&(g>=b)&(r-b>=40)
rc,rn=connected_components(rock);sizes=np.bincount(rc.ravel());rock &= sizes[rc]>=128;labels[rock]='R'
water=(b-r>=48)&(b-g>=24)
wc,wn=connected_components(water);sizes=np.bincount(wc.ravel());water &= sizes[wc]>=512;labels[water]='W'
woods=(g>r)&(b<80);labels[woods]='T'
# Known occluding original features. They are not path/water/rock training pixels.
labels[80:192,:96]='B';labels[1632:1728,272:360]='B';labels[1040:1104]='H'
# Sprites/props are separate features, never evidence for soil or water.
fixed_boxes=[(344,40,360,96),(384,40,400,96),(208,1832,248,1880),(374,1104,404,1210)]
for x0,y0,x1,y1 in fixed_boxes:labels[y0:y1,x0:x1]='B'
# Keep actual terrain visible around a sprite; masking its whole rectangle would
# erase the grassy notch beside a trainer or manufacture a rectangular soil shelf.
rock_palette=set()
for x0,y0,x1,y1 in [(290,420,330,452),(282,520,350,544),(262,448,279,510),(348,448,368,510),(200,680,280,720),(96,1776,144,1816)]:
 patch=rgb[y0:y1,x0:x1];rr,gg,bb=patch.transpose(2,0,1);valid=(rr>=80)&(rr-gg>=32)&(rr-bb>=40)
 for c in patch[valid]:rock_palette.add(tuple(c))
figures=[(452,296,480,336),(352,368,384,416),(328,560,360,608),(272,728,304,776),
 (184,1144,216,1192),(224,1172,256,1216),(304,1288,336,1344),(40,1264,72,1312),
 (160,1480,200,1536),(224,1640,256,1696),(312,1872,344,1920)]
for x0,y0,x1,y1 in figures:
 v=labels[y0:y1,x0:x1];q=rgb[y0:y1,x0:x1];known=np.array([tuple(c) in rock_palette for c in q.reshape(-1,3)]).reshape(v.shape)
 keep=np.isin(v,['.','P','G','W'])|((v=='R')&known);v[~keep]='B'
props=[(224,104,256,152),(320,224,352,272),(176,1936,216,1984),(320,1856,352,1896),(280,1920,320,1960)]
for x0,y0,x1,y1 in props:
 v=labels[y0:y1,x0:x1];v[~np.isin(v,['.','P','G','W'])]='B'
# Dock/stair source silhouettes disambiguate their brown/gray from rock and path.
import sys
sys.path.insert(0,str(HERE));import build as initial,refine
for key,ch in [('dock','D'),('stairs','S')]:
 mask=Image.new('1',(480,2000));d=ImageDraw.Draw(mask)
 for poly in initial.TRACES[key]:d.polygon(poly,fill=1)
 chosen=np.array(mask,bool);labels[chosen]=ch
old=np.array([list(row) for row in (S/'material-revision-baseline/hgss-cell-grid.txt').read_text().splitlines()]);plan=old.copy();counts={};fractions=np.zeros((125,30,6),float);classes=['.','P','G','R','W','D'];changes=[];confidence=np.zeros((125,30))
for y in range(125):
 for x in range(30):
  pix=labels[y*16:y*16+16,x*16:x*16+16];occluded=np.isin(pix,['T','B','H']).sum();available=int(256-occluded)
  values={c:int((pix==c).sum()) for c in classes};fractions[y,x]=[values[c]/max(1,available) for c in classes]
  if available<80 or old[y,x] in 'DS_':continue
  best=max(values,key=values.get);confidence[y,x]=values[best]/max(1,available)
  # Actual tall-grass blades include ordinary-lawn pixels between tufts.
  if values['G']/available>=.24 and values['R']/available<.45 and values['W']/available<.45:best='G'
  # Refuse to infer ground through sprites or uncertain mixed edge pixels.
  # An old trace is not evidence for dirt/grass where no such pixels exist.
  # Shadowed lawn below a crown must not survive as an isolated dirt dot.
  unsupported_ground=old[y,x] in ['P','G'] and values[old[y,x]]<12 and values['.']>=32
  if unsupported_ground:best='.'
  if values[best]/available<.38 and not unsupported_ground:continue
  plan[y,x]=best
  if best!=old[y,x]:changes.append({'source':[x,y],'old':old[y,x],'material':best,'visible_pixels':available,'support':round(values[best]/available,3)})
# Source tree bodies stay on ordinary lawn, independent of the foreground canopy.
foot=json.loads((S/'hgss-tree-footprints.json').read_text())
for x,y in foot['anchors']:
 plan[y+1:min(125,y+3),x:min(30,x+2)]='.'
# The observed dirt above/below the overhead bridge is one continuous road.
plan[65:69,1:4]='P'
# Keep agreed complete stock-stair placements and their actual rock corners.
plan[58:61,8:10]='S';plan[58,9]='R';plan[60,8]='R';plan[86:88,5:8]='S'
# Original cave forecourt has two separated one-way lips, not a single dirt field.
plan[118,11:14]='_';plan[118,15:17]='_';plan[119,11:17]='P'
# Map visible rock at 8px quadrant resolution: native metatiles contain four
# hardware tiles, so internal terrace faces need not be rounded to whole cells.
roles=np.full((250,60),'.',dtype='<U1');darkness=np.zeros(roles.shape)
left_colors={(88,64,48),(96,72,56),(112,88,64),(120,88,64),(136,104,80),(144,112,80),(160,128,96),(168,128,96),(176,136,96)}
for my in range(250):
 for mx in range(60):
  if plan[my//2,mx//2]!='R':continue
  pix=rgb[my*8:my*8+8,mx*8:mx*8+8];lab=labels[my*8:my*8+8,mx*8:mx*8+8];rock=lab=='R';n=int(rock.sum())
  dark=float(((pix[...,0]<168)&rock).sum()/max(1,n));darkness[my,mx]=dark
  left_fraction=sum(tuple(v) in left_colors for v in pix[rock])/max(1,n)
  roles[my,mx]='l' if n>=16 and left_fraction>=.28 and dark>=.24 else 'f' if n>=16 and dark>=.42 else 't'
# Reject isolated front chips in soil. True faces extend across an adjacent quadrant.
f=roles=='f';neighbor=np.zeros_like(f)
neighbor[:,1:]|=f[:,:-1];neighbor[:,:-1]|=f[:,1:];neighbor[1:]|=f[:-1];neighbor[:-1]|=f[1:];roles[f&~neighbor]='t'
# The narrow eastern edge of each landform uses the east-facing Emerald piece.
for my in range(250):
 for mx in range(60):
  if roles[my,mx] not in ['f','l'] or darkness[my,mx]<.35:continue
  cx=mx//2;cy=my//2
  if cx==29 or plan[cy,cx+1]!='R':roles[my,mx]='r'
np.save(S/'hgss-rock-quadrant-observations.npy',roles)
# Color observations propose faces; coherent architectural planes decide the edit.
# Applying every dark texture chip would create disconnected wall fragments.
planes=[{'name':'western pillar upper drop','box':[192,712,296,728],'role':'f'},
 {'name':'western pillar lower terrace','box':[192,728,272,760],'role':'t'},
 {'name':'western pillar lower drop','box':[192,760,272,776],'role':'f'},
 {'name':'central pillar front','box':[280,512,352,544],'role':'f'},
 {'name':'cave upper shelf front','box':[176,1832,272,1848],'role':'f'}]
authored=np.full(roles.shape,'.',dtype='<U1')
for q in planes:
 x0,y0,x1,y1=q['box'];authored[y0//8:y1//8,x0//8:x1//8]=q['role']
authored[230:234,26:30]='.' # original cave arch/opening is a distinct feature, not plain wall
np.save(S/'hgss-rock-quadrants.npy',authored)
(S/'hgss-rock-planes.json').write_text(json.dumps({'source':'original HGSS cliff-plane boundaries, inspected against 8px palette observations','existing_exterior_geometry':'accepted continuous cliff edge/side/corner family retained','planes':planes},indent=2)+'\n')
# Underlay is explicit: a ledge is not ordinary grass simply because it is blocked.
underlay=plan.copy();underlay[plan=='_']='.';underlay[44,19:21]='P';underlay[118,11:14]='P';underlay[118,15:17]='P'
(S/'hgss-ground-underlay.txt').write_text('\n'.join(''.join(row) for row in underlay)+'\n')
np.save(S/'hgss-material-pixel-labels.npy',labels);np.save(S/'hgss-material-confidence.npy',confidence)
(S/'hgss-material-grid.txt').write_text('\n'.join(''.join(row) for row in plan)+'\n')
(S/'hgss-material-trace.json').write_text(json.dumps({'reference':'hgss-reference.png','source_cell_size':16,'native_offset':[1,1],'method':'visible original HGSS terrain palette; explicit dock/stair silhouettes; trees, buildings and railway excluded from ground inference','classes':{'.':'ordinary grass','P':'dirt path','G':'tall grass','R':'rock landform (surface roles traced separately)','W':'water','D':'wood deck','S':'Emerald placeholder stairs','_':'south-facing jump ledge'},'pixel_suggestions':changes,'rock_surface_roles':{'t':'rock top/soil','f':'front wall face','l':'west-facing wall','r':'east-facing wall'},'rock_role_resolution_px':8,'material_changes':[{'source':[int(x),int(y)],'old':old[y,x],'material':plan[y,x]} for y,x in np.argwhere(old!=plan)],'source_tree_roots_preserved':True,'unobserved_ground':'prior measured HGSS trace continuity, not native map colors','not_decoded_DS_collision':True},indent=2)+'\n')
# The material comparison is deliberately categorical rather than red/green solidity.
old_rgb=np.zeros((2000,480,3),np.uint8);new_rgb=old_rgb.copy()
for ch,col in COLORS.items():
 old_rgb[np.repeat(np.repeat(old==ch,16,0),16,1)]=col;new_rgb[np.repeat(np.repeat(plan==ch,16,0),16,1)]=col
for n in range(5):
 out=Image.new('RGB',(1500,440),(26,33,37));out.paste(Image.fromarray(raw[n*400:(n+1)*400,:480]),(12,28));out.paste(Image.fromarray(old_rgb[n*400:(n+1)*400]),(510,28));out.paste(Image.fromarray(new_rgb[n*400:(n+1)*400]),(1008,28));d=ImageDraw.Draw(out);d.text((12,8),f'HGSS source rows {n*25}-{n*25+24}',fill='white');d.text((510,8),'Previous terrain assignment',fill='white');d.text((1008,8),'New source material trace',fill='white');out.save(E/f'material-trace-{n+1}.png')
changed=np.argwhere(old!=plan);print('Changed material cells',len(changed));print('Pairs',{f'{a}->{b}':int(((old==a)&(plan==b)).sum()) for a in classes+['_'] for b in classes+['_'] if a!=b and ((old==a)&(plan==b)).any()})

# Promote the reviewed material trace to the shared source-cell ledger. Collision
# is derived from terrain plus explicit footprints, never used to choose material.
(S/'hgss-cell-grid.txt').write_text((S/'hgss-material-grid.txt').read_text())
expected=np.isin(plan,list('RW_'))
for x,y in foot['anchors']:
 expected[y+1:min(125,y+3),x:min(30,x+2)]=True
expected[5:12,0:6]=True;expected[103:107,17:22]=True;expected[3:6,21]=True;expected[3:6,24]=True
for q in foot['props']+foot['signs']:
 x,y=q['source_cell'];expected[y,x]=True
np.save(S/'hgss-reference-blocked.npy',expected)
