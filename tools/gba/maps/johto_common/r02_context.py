"""Neighbor-aware R02 borders, continuous rock faces and reusable mirrors."""
from pathlib import Path
import argparse,json,sys,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_refine as native
from route36.gate_surround.build import decode,over
from johto_common.trees import rgba,indexed,sha
from claude_cherrygrove import ground
from tiles import Tileset
P=ROOT/'gba/art/johto-common/rocks/r02-context';BASE='5b14c523c1a0688f3c291b485998bd91fd05dc86';BOX=(192,240,560,432)
def save(a,p):Image.fromarray(a).save(p)
def dump(p,a):p.write_text(json.dumps(a,indent=2)+'\n')
def main(game,install):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()==BASE
 assert not subprocess.check_output(['git','status','--porcelain','--','data/layouts/JohtoRoute36','data/tilesets/primary/johto_route36','data/tilesets/secondary/johto_route36'],cwd=game,text=True).strip()
 for n in ['source','review','evidence']:(P/n).mkdir(parents=True,exist_ok=True)
 t=Tileset(game,'johto_route36','johto_route36');grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);layers,attrs=decode(t,grid);before=layers[0].copy();over(before,layers[1]);save(before,P/'review/before-full.png')
 cells=np.load(ROOT/'gba/art/johto-common/rocks/r02-joins/source/material-grid.npy').copy();cells[21:24,14]=ground.PATH;cells[21:24,32]=ground.PATH
 # Restore the established contour and complete original material ramp. No
 # blur, straightening, morphological rounding or global edge simplification.
 terrain,mat=ground.paint(cells,wobble=True)
 pal=np.array(t.pals[1][6][1:10],int)
 for c in np.unique(terrain[:,:,:3].reshape(-1,3),axis=0):
  chosen=pal[np.square(pal-c.astype(int)).sum(1).argmin()];terrain[np.all(terrain[:,:,:3]==c,2),:3]=chosen
 prior=rgba(ROOT/'gba/art/johto-common/rocks/r02-joins/review/native-full.png')
 base=before.copy();objects=np.zeros_like(base);work=np.zeros(base.shape[:2],bool);grass=(attrs&255)==2;plan=np.load(ROOT/'gba/art/route36/source/plan.npy');contexts=[]
 def label(x,y):
  if not (0<=x<82 and 0<=y<32):return 'outside'
  if (attrs[y,x]&255) in (0x49,0x4a,0x4b,0x4c,0x4d,0x4e) or (x==32 and y in (22,23)):return 'stairs'
  if plan[y,x]=='R':return 'rock'
  if grass[y,x]:return 'tall grass'
  if cells[y,x]==ground.PATH:return 'dirt'
  return 'lawn'
 scenery=ROOT/'gba/art/johto-common/scenery'
 for y in range(17,24):
  for x in range(15,32):
   sl=np.s_[y*16:y*16+16,x*16:x*16+16];base[sl]=prior[sl] if y>=20 else before[sl];work[sl]=True
   neighbors={d:label(xx,yy) for d,xx,yy in [('N',x,y-1),('S',x,y+1),('W',x-1,y),('E',x+1,y)]};bits=''.join(str(int(v=='tall grass')) for v in neighbors.values())
   if grass[y,x]:
    asset=rgba(scenery/'source'/f'G{int(bits,2):02d}.png')
    # Preserve the actual pre-smoothing path contour. Remove only the prior
    # plant pixels so a changed neighbor mask cannot leave obsolete blades.
    for c in np.unique(rgba(scenery/'source/G15.png')[:,:,:3].reshape(-1,3),axis=0):
     m=np.all(prior[sl][:,:,:3]==c,2)
     if c.any():base[sl][m]=terrain[sl][m]
    envelope=rgba(scenery/'inputs'/f'G{int(bits,2):02d}.png')[:,:,3]>0
    base[sl][envelope&(asset[:,:,3]==0),:3]=(32,112,80);over(objects,asset,x*16,y*16)
   contexts.append(dict(x=x,y=y,material=label(x,y),neighbors=neighbors,grass_master=f'G{int(bits,2):02d}' if grass[y,x] else None,path_contour='exact pre-smoothing native ground pixels from 833a9c4355',edge_rule='material interface only; rock and stair foreground terminate/cover ground edges'))
 # Reuse the accepted complete side plane; its diagonal grain keeps phase along
 # the entire wall. Mirrors are actual flipped source arrays, not approximations.
 strip=rgba(ROOT/'gba/art/johto-common/rocks/r02-joins/source/wall-and-stairs.png');west=strip[:32].copy();east=west[:,::-1].copy();tex=rgba(ROOT/'gba/art/johto-common/rocks/r02-refined/source/wall01_d.png');tex[:,:,:3]=np.round(tex[:,:,:3].astype(float)*.8/8).clip(0,31)*8
 front=np.array(Image.fromarray(tex[17:31]).resize((32,16),Image.Resampling.NEAREST));corner=west[:16].copy()
 # Local corner joins the horizontal front plane to the vertical side plane.
 for y in range(16):
  for x in range(16):
   if x<15-y:corner[y,x]=front[y,x]
 assets={'face-west':west,'face-east':east,'front':front,'corner-west':corner,'corner-east':corner[:,::-1].copy(),'stair-section-west':strip,'stair-section-east':strip[:,::-1].copy()}
 for n,a in assets.items():save(a,P/'source'/(n+'.png'));indexed(a,P/'source'/(n+'.idx.png')) if len(np.unique(a[a[:,:,3]>0,:3],axis=0))<=15 else None
 assert np.array_equal(assets['face-east'],assets['face-west'][:,::-1]);assert np.array_equal(assets['corner-east'],assets['corner-west'][:,::-1]);assert np.array_equal(assets['stair-section-east'],assets['stair-section-west'][:,::-1])
 def area(x0,y0,x1,y1):base[y0:y1,x0:x1]=terrain[y0:y1,x0:x1];work[y0:y1,x0:x1]=True
 # Entire western vertical run, its upper bend and connected horizontal face.
 area(0,64,240,80)
 for x in range(0,224,16):over(objects,front[:,x%32:x%32+16],x,64)
 over(objects,corner,224,64)
 for y in range(80,416,16):
  area(224,y,240,y+16)
  a=strip[y-288:y-272] if y>=288 else west[(y-288)%32:(y-288)%32+16]
  over(objects,a,224,y)
 # Right-facing wall keeps its existing stair flight/footprint. Rebuild the
 # stone beneath/around that transparent flight, without changing movement.
 for y in range(256,416,16):area(512,y,528,y+16);over(objects,east[(y-288)%32:(y-288)%32+16],512,y)
 east_stairs=rgba(ROOT/'gba/art/route36/source/materials/stair-east.png');over(objects,east_stairs,512,336)
 # Context for upper rims follows which side is raised; no fixed green strip
 # is painted beside dirt or a stair. Contacts are background, separate art.
 for x,direction,y0 in [(224,1,80),(512,-1,256)]:
  for y in range(y0,416):
   if (x==224 and 336<=y<384) or (x==512 and 336<=y<384):continue
   high=x+16 if direction==1 else x-1;low=x-1 if direction==1 else x+16
   for px,c in [(high,(88,176,136)),(low,(96,192,144))]:
    if 0<=px<base.shape[1] and mat[y,px]==ground.GRASS and not grass[y//16,px//16]:base[y,px,:3]=c;work[y,px]=True
 # Preserve existing tree canopies/trunks exactly at their current coordinates.
 tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png');tree_mask=np.zeros(base.shape[:2],bool)
 for c in np.unique(tree[tree[:,:,3]>0,:3],axis=0):tree_mask|=np.all(before[:,:,:3]==c,2)
 # Native quarters use two EXISTING palette-compatible layers. Reuse pairs of
 # banks when a new grass/rock/tree join needs colors from different families.
 palettes=[set(map(tuple,t.pals[i>=6][i][1:])) for i in range(13)]
 ac=work.reshape(32,16,82,16).any((1,3));affected=ac.repeat(16,0).repeat(16,1)
 for cy,cx in np.argwhere(ac):
  for q in range(4):
   y=cy*16+q//2*8;x=cx*16+q%2*8;sl=np.s_[y:y+8,x:x+8]
   if not work[sl].any():continue
   final=base[sl].copy();over(final,objects[sl]);final[tree_mask[sl]]=before[sl][tree_mask[sl]]
   colors=set(map(tuple,final[final[:,:,3]>0,:3]));preferred_top=tree_mask[sl].copy()
   if grass[cy,cx]:preferred_top |= objects[sl][:,:,3]>0
   pairs=[(i,j) for i in range(13) for j in range(13) if colors<=palettes[i]|palettes[j]];assert pairs,('palette join',cx,cy,q,colors)
   def cost(pair):
    return sum(int((np.all(final[:,:,:3]==c,2)&preferred_top).sum())*(c not in palettes[pair[1]])*100+int((np.all(final[:,:,:3]==c,2)&~preferred_top).sum())*(c not in palettes[pair[0]]) for c in colors)
   pair=min(pairs,key=cost);bottom=np.zeros_like(final);top=np.zeros_like(final)
   for c in colors:
    m=np.all(final[:,:,:3]==c,2)
    if c in palettes[pair[0]] and c in palettes[pair[1]]:bottom[m&~preferred_top]=final[m&~preferred_top];top[m&preferred_top]=final[m&preferred_top]
    else:(bottom if c in palettes[pair[0]] else top)[m]=final[m]
   layers[0][sl]=bottom;layers[1][sl]=top
 target=layers[0].copy();over(target,layers[1]);assert np.array_equal(target[~affected],before[~affected]);assert np.array_equal(target[tree_mask],before[tree_mask]);save(target,P/'review/native-target.png')
 np.save(P/'source/material-grid.npy',cells);dump(P/'source/contexts.json',contexts);dump(P/'source/catalog.json',{'assets':[{ 'id':n,'file':n+'.png','sha256':sha(P/'source'/(n+'.png')),'mirror':n.replace('east','west') if 'east' in n else None} for n in assets],'foreground_background':'All source assets contain stone/stairs only; destination terrain is separate.','east_stair_in_map':'Existing gray 16x48 flight preserved; mirrored full assembly saved for later reuse.'})
 native.P=P;report=dict(base_engine=BASE,installed=install,runtime_tested=False,existing_tree_pixels_changed=0,collision_elevation_changes=0,behavior_changes=0,outside_affected_pixel_changes=0,affected_cells=int(ac.sum()),mirrors_exact=True,path_smoothing=False,wall_runs={'west':[14,5,25],'north_front':[0,4,13],'east':[32,16,25]},palette_repacked=False)
 if install:report.update(native.append_native(game,layers,affected,grid,attrs))
 dump(P/'evidence/structure.json',report)
 x0,y0,x1,y1=BOX;ref=rgba(native.REF)
 for n,a in [('original',ref),('before',before),('map',target)]:save(a[y0:y1,x0:x1],P/'review'/(n+'.png'))
 font=ImageFont.truetype(native.FONT,20);sheet=Image.new('RGB',(2256,465),'#202d37');d=ImageDraw.Draw(sheet)
 for i,(n,title) in enumerate([('original','ORIGINAL HGSS'),('before','PREVIOUS / FLATTENED BORDERS'),('map','CONTEXTUAL BORDERS + BOTH FACES')]):
  x=i*752+8;d.text((x,10),title,font=font,fill='white');sheet.paste(Image.open(P/'review'/(n+'.png')).resize((736,384),Image.Resampling.NEAREST),(x,42))
 sheet.save(P/'review/comparison.png')
 # Reference sheet includes the complete terrain-free source and its mirrors.
 sheet=Image.new('RGB',(1000,710),'#202d37');d=ImageDraw.Draw(sheet)
 for i,(name,a) in enumerate(assets.items()):
  x=15+i*140;d.text((x,10),name,font=ImageFont.truetype(native.FONT,13),fill='white');im=Image.fromarray(a).resize((a.shape[1]*4,a.shape[0]*4),Image.Resampling.NEAREST);sheet.paste(im,(x,42),im)
 sheet.save(P/'review/mirrors.png')
 # Review only the full affected bounding area as strips, avoiding hundreds of
 # unrelated center-map cells: native affected cells plus cardinal neighbors.
 reviewed=set(map(tuple,np.argwhere(ac)))
 for y,x in list(reviewed):
  for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
   if 0<=yy<32 and 0<=xx<82:reviewed.add((yy,xx))
 records=[]
 for y,x in sorted(reviewed):records.append(dict(x=int(x),y=int(y),changed=bool(ac[y,x]),material=label(x,y),neighbors={d:label(xx,yy) for d,xx,yy in [('N',x,y-1),('S',x,y+1),('W',x-1,y),('E',x+1,y)]},collision=int(grid[y,x]>>10&3),elevation=int(grid[y,x]>>12),behavior=int(attrs[y,x]&255),review='pending inspection'))
 dump(P/'evidence/cell-review.json',records);print(json.dumps(report,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--engine',type=Path,required=True);a.add_argument('--install',action='store_true');v=a.parse_args();main(v.engine,v.install)
