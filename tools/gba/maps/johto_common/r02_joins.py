"""Repair R02 wall completeness, shared rise and raised landing on the current candidate."""
from pathlib import Path
import argparse,json,sys,subprocess,re
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_refine as native
from johto_common.trees import rgba,indexed
from route36.gate_surround.build import decode,over
from claude_cherrygrove import ground
from tiles import Tileset
BASE='285b577993906c76c8d96ed38eedb5e2c955b714'
P=ROOT/'gba/art/johto-common/rocks/r02-joins';SOURCE=ROOT/'gba/art/johto-common/rocks/r02-refined/source'
BOX=(160,288,352,416)
def save(a,p):Image.fromarray(a).save(p)
def dump(p,a):p.write_text(json.dumps(a,indent=2)+'\n')
def foreground():
 # The second native texture band is fully unobscured stone. Unlike the previous
 # material color-key, this complete side plane cannot leave holes in the wall.
 tex=rgba(SOURCE/'wall01_d.png');tex[:,:,:3]=np.round(tex[:,:,:3].astype(float)*.8/8).clip(0,31)*8
 rock=np.zeros((128,16,4),np.uint8)
 for y in range(128):
  for x in range(16):
   rock[y,x]=tex[17+round((15-x)*13/15),(y+x)%32]
 assert (rock[:,:,3]==255).all()
 # Project original slope model directly with a common 16px cliff rise. Width
 # along the opening is 32px. Never resize the final projection vertically.
 model=json.loads((SOURCE/'geometry.json').read_text());slope=rgba(SOURCE/'slope.png')
 stairs=np.zeros_like(rock);depth=np.full((128,16),-1e9)
 for f in model['faces']:
  if f['texture']!='slope':continue
  ps=np.array(f['vertices']);uv=np.array(f['uv']);screen=np.column_stack(((ps[:,0]+14)*16,64+(ps[:,2]-8.0625)*(32/2.875)-(ps[:,1]-1)*16));dep=ps[:,1]+ps[:,2]
  for j in range(1,len(ps)-1):
   ids=[0,j,j+1];v=screen[ids];mat=np.vstack((v.T,np.ones(3)))
   if abs(np.linalg.det(mat))<1e-8:continue
   inv=np.linalg.inv(mat)
   for y in range(max(0,int(v[:,1].min())),min(128,int(v[:,1].max())+1)):
    for x in range(max(0,int(v[:,0].min())),min(16,int(v[:,0].max())+1)):
     w=inv@np.array([x+.5,y+.5,1]);z=w@dep[ids]
     if w.min()<-1e-7 or z<depth[y,x]:continue
     u,vv=w@uv[ids];c=slope[int(np.floor(vv))%32,int(np.floor(u))%32].copy();c[:3]=np.round(c[:3].astype(float)*.8/8).clip(0,31)*8
     stairs[y,x]=c;depth[y,x]=z
 over(rock,stairs);save(rock,P/'source/wall-and-stairs.png');save(stairs,P/'source/stairs.png')
 for y in range(8):save(rock[y*16:y*16+16],P/'source'/f'wall-{y}.png')
 return rock

def terrain(game):
 plan=np.load(ROOT/'gba/art/route36/source/plan.npy');cells=np.full(plan.shape,ground.GRASS,np.int8);cells[np.isin(plan,['P','S'])]=ground.PATH;cells[19:22,53:75]=ground.PATH
 # Raised landing one full row north, followed by a two-cell path bend back to
 # the existing plateau route. This is a bend on the upper plane, not a slope.
 cells[21:24,15:20]=ground.GRASS;cells[21:23,15:18]=ground.PATH;cells[21:24,18:20]=ground.PATH
 profiles=ground.PROFILES[(ground.GRASS,ground.PATH)];wave=ground.WAVE
 ground.PROFILES[(ground.GRASS,ground.PATH)]=([(88,176,136),(96,192,144)],[(184,168,128),(216,184,128)]);ground.WAVE=[int(np.sign(v)) for v in wave]
 art,material=ground.paint(cells,wobble=True);ground.PROFILES[(ground.GRASS,ground.PATH)]=profiles;ground.WAVE=wave
 gp=np.array(Tileset(game,'claude_route30','cherrygrove').pals[0][0][1:],int)
 for c in np.unique(art[:,:,:3].reshape(-1,3),axis=0):
  green=int(c[1])>int(c[0])+10;choices=gp[(gp[:,1]>gp[:,0]+10)==green];chosen=choices[np.square(choices-c.astype(int)).sum(1).argmin()];art[np.all(art[:,:,:3]==c,axis=2),:3]=chosen
 np.save(P/'source/material-grid.npy',cells);return art

def main(game,install):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()==BASE
 assert not subprocess.check_output(['git','status','--porcelain','--','data/layouts/JohtoRoute36','data/tilesets/primary/johto_route36','data/tilesets/secondary/johto_route36'],cwd=game,text=True).strip(),'Preserve current work'
 for d in ['source','review','evidence']:(P/d).mkdir(parents=True,exist_ok=True)
 t=Tileset(game,'johto_route36','johto_route36');grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);layers,attrs=decode(t,grid);oldattrs=attrs.copy();oldgrid=grid.copy();before=layers[0].copy();over(before,layers[1]);save(before,P/'review/before-full.png')
 bg=terrain(game);fg=np.zeros_like(bg);over(fg,foreground(),224,288)
 tree_layer=np.zeros_like(bg);tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png')
 for x,y in json.loads((ROOT/'gba/art/route36/source/features.json').read_text())['trees']:over(tree_layer,tree,x*16,y*16)
 affected=np.zeros(bg.shape[:2],bool);affected[288:416,224:240]=True;affected[320:384,240:320]=True
 # Restore the full source tree over the completed wall; never use a tree-cut
 # silhouette as the wall itself. Keep all existing tree coordinates.
 over(fg,tree_layer)
 for cy,cx in np.argwhere(affected.reshape(32,16,82,16).any((1,3))):
  for q in range(4):
   y=cy*16+q//2*8;x=cx*16+q%2*8;sl=np.s_[y:y+8,x:x+8];bottom=bg[sl].copy();top=fg[sl].copy()
   # Shift the complete existing tall-grass bottom border one row north, using
   # all original pixels including the adjacent terrain fringe.
   if cy==20 and 15<=cx<20:
    bottom=layers[0][y+16:y+24,x:x+8].copy();top=layers[1][y+16:y+24,x:x+8].copy()
   bottom[top[:,:,3]>0]=0
   # A tree can overlap the rock. Keep trees on top and the complete wall below.
   if cx==14 and tree_layer[sl][:,:,3].any():
    bottom=bg[sl].copy();wall=rgba(P/'source/wall-and-stairs.png')[y-288:y-280,x-224:x-216];over(bottom,wall);top=tree_layer[sl].copy();bottom[top[:,:,3]>0]=0
   layers[0][sl]=bottom;layers[1][sl]=top
 target=layers[0].copy();over(target,layers[1]);assert np.array_equal(target[~affected],before[~affected]);save(target,P/'review/native-target.png')
 tree_mask=np.zeros(before.shape[:2],bool)
 for c in np.unique(tree[tree[:,:,3]>0,:3],axis=0):tree_mask |= np.all(before[:,:,:3]==c,axis=2)
 assert np.array_equal(before[tree_mask],target[tree_mask]),'Existing tree pixels must remain intact'
 # Use expansion's existing diagonal side-stair behavior so the actor rises
 # with the art. No custom engine movement logic or new warp is introduced.
 names=re.findall(r'^\s*(MB_\w+)\s*,', (game/'include/constants/metatile_behaviors.h').read_text(),re.M);mb={n:i for i,n in enumerate(names)}
 for y,n in [(21,'MB_SIDEWAYS_STAIRS_LEFT_SIDE_TOP'),(22,'MB_SIDEWAYS_STAIRS_LEFT_SIDE'),(23,'MB_SIDEWAYS_STAIRS_LEFT_SIDE_BOTTOM')]:attrs[y,14]=(attrs[y,14]&0xff00)|mb[n]
 grid[21,14]&=0xf3ff
 for x in range(15,20):attrs[21,x]&=0xff00
 # Newly drawn grass south of landing is regular grass; the texture never
 # silently inherits tall-grass behavior. Ground elevation flags stay constant.
 np.save(P/'source/attributes.npy',attrs)
 changes=[dict(x=int(x),y=int(y),before=int(oldattrs[y,x]),after=int(attrs[y,x])) for y,x in np.argwhere(attrs!=oldattrs)]
 native.P=P
 report=dict(base_engine=BASE,shared_rise_pixels=16,stair_opening_pixels=32,source_wall_band=[0,17,32,31],wall_interior_transparent_pixels=0,changed_existing_tree_pixels=0,raised_landing=dict(x=[15,18],y=[21,23],path_bend_x=[18,20]),attribute_changes=changes,collision_changes=[dict(x=int(x),y=int(y),before=int(oldgrid[y,x]>>10&3),after=int(grid[y,x]>>10&3)) for y,x in np.argwhere((oldgrid&0xfc00)!=(grid&0xfc00))],outside_affected_pixel_changes=0,installed=install,runtime_tested=False)
 if install:report.update(native.append_native(game,layers,affected,grid,attrs))
 report['collision_elevation_changes']=len(report['collision_changes']);dump(P/'evidence/structure.json',report)
 ref=rgba(native.REF);assembly=bg.copy();over(assembly,rgba(P/'source/wall-and-stairs.png'),224,288)
 for n,a in [('original',ref),('before',before),('map',target),('rebuilt',assembly)]:save(a[288:416,160:352],P/'review'/(n+'.png'))
 font=ImageFont.truetype(native.FONT,20);sheet=Image.new('RGB',(1824,490),'#202d37');d=ImageDraw.Draw(sheet)
 for i,(name,label) in enumerate([('original','ORIGINAL HGSS / R02'),('rebuilt','COMPLETE WALL + SHARED 16px RISE'),('map','NATIVE MAP / RAISED LANDING')]):
  x=16+i*608;d.text((x,15),label,font=font,fill='white');sheet.paste(Image.open(P/'review'/(name+'.png')).resize((576,384),Image.Resampling.NEAREST),(x,52))
 d.text((16,455),'Wall, stair shoulders and raised path now share one height offset.',font=font,fill='white');sheet.save(P/'review/comparison.png')
 # Fixed-size sheets allow close review of every affected cell and neighbors.
 records=[]
 for y in range(18,26):
  for x in range(10,22):records.append(dict(x=x,y=y,changed=bool(affected[y*16:y*16+16,x*16:x*16+16].any()),material='stair' if x==14 and 21<=y<=23 else 'side wall' if x==14 else 'raised landing / grass border' if 15<=x<20 and 20<=y<24 else 'retained neighbor',collision=int(grid[y,x]>>10&3),elevation=int(grid[y,x]>>12),behavior=int(attrs[y,x]&255),review='pending visual inspection'))
 for r in records:
  x,y=r['x']*16,r['y']*16;r['quadrants']=[dict(offset=[dx,dy],opaque_colors_per_layer=[len(np.unique(z[y+dy:y+dy+8,x+dx:x+dx+8][z[y+dy:y+dy+8,x+dx:x+dx+8,3]>0,:3],axis=0)) for z in layers]) for dy in [0,8] for dx in [0,8]]
 dump(P/'evidence/cell-review.json',records);print(json.dumps(report,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--engine',type=Path,required=True);a.add_argument('--install',action='store_true');v=a.parse_args();main(v.engine,v.install)
