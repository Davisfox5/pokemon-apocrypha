"""Contextual R02 terrain contacts; preserves accepted wall/stairs and movement."""
from pathlib import Path
import argparse,json,sys,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_refine as native
from route36.gate_surround.build import decode,over
from johto_common.trees import rgba
from claude_cherrygrove import ground
from tiles import Tileset
P=ROOT/'gba/art/johto-common/rocks/r02-transitions';BASE='833a9c4355be0b191e676963f5f8d39930560fb6';BOX=(192,272,544,432)
def save(a,p):Image.fromarray(a).save(p)
def dump(p,a):p.write_text(json.dumps(a,indent=2)+'\n')
def terrain(game):
 cells=np.load(ROOT/'gba/art/johto-common/rocks/r02-joins/source/material-grid.npy');mask=np.repeat(np.repeat(cells==ground.PATH,16,0),16,1)
 # Round 90-degree turns by at most three pixels, keeping tile-center topology.
 for y in range(1,cells.shape[0]):
  for x in range(1,cells.shape[1]):
   q=cells[y-1:y+1,x-1:x+1]==ground.PATH;n=int(q.sum())
   if n not in (1,3):continue
   minority=n==1;dy,dx=np.argwhere(q==minority)[0]
   for v in range(4):
    for u in range(4):
     if (3.5-u)**2+(3.5-v)**2>16:
      yy=y*16+(v if dy else -v-1);xx=x*16+(u if dx else -u-1);mask[yy,xx]=not minority
 ys,xs=np.indices(mask.shape);tex=ground.textures();art=np.zeros((*mask.shape,4),np.uint8);art[:,:,3]=255
 for selected,m in [(~mask,ground.GRASS),(mask,ground.PATH)]:
  t=tex[m];art[selected,:3]=t[ys[selected]%t.shape[0],xs[selected]%t.shape[1]]
 for selected,other,ramp in [(~mask,mask,[(88,176,136),(96,192,144)]),(mask,~mask,[(184,168,128),(216,184,128)])]:
  dist=ground._chamfer(other,3)
  for i,c in enumerate(ramp):art[selected&(dist==i+1),:3]=c
 pal=np.array(Tileset(game,'claude_route30','cherrygrove').pals[0][0][1:],int)
 for c in np.unique(art[:,:,:3].reshape(-1,3),axis=0):
  green=int(c[1])>int(c[0])+10;choices=pal[(pal[:,1]>pal[:,0]+10)==green];chosen=choices[np.square(choices-c.astype(int)).sum(1).argmin()];art[np.all(art[:,:,:3]==c,2),:3]=chosen
 return art,mask

def main(game,install):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()==BASE
 assert not subprocess.check_output(['git','status','--porcelain','--','data/layouts/JohtoRoute36','data/tilesets/primary/johto_route36','data/tilesets/secondary/johto_route36'],cwd=game,text=True).strip()
 for n in ['source','review','evidence']:(P/n).mkdir(parents=True,exist_ok=True)
 t=Tileset(game,'johto_route36','johto_route36');grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);layers,attrs=decode(t,grid);before=layers[0].copy();over(before,layers[1]);save(before,P/'review/before-full.png')
 terrain_art,path=terrain(game);base=before.copy();fore=np.zeros_like(base);work=np.zeros(base.shape[:2],bool)
 # Recompose every tall-grass edge against its ACTUAL current neighbors, over
 # destination terrain. Includes the entire patch so no new crop-edge seam forms.
 grass=(attrs&255)==2;scenery=ROOT/'gba/art/johto-common/scenery/source';entries=[]
 for y in range(17,24):
  for x in range(15,32):
   sl=np.s_[y*16:y*16+16,x*16:x*16+16];base[sl]=terrain_art[sl];work[sl]=True
   if grass[y,x]:
    bits=''.join(str(int(grass[yy,xx])) for xx,yy in [(x,y-1),(x,y+1),(x-1,y),(x+1,y)])
    asset=rgba(scenery/f'G{int(bits,2):02d}.png')
    # Keep the dense grass bed shaded beneath transparent blade gaps. The
    # shadow is an independent terrain layer, clipped to this grass footprint;
    # exposed exterior pixels retain the destination lawn/path transition.
    envelope=rgba(scenery.parent/'inputs'/f'G{int(bits,2):02d}.png')[:,:,3]>0
    shadow=envelope & (asset[:,:,3]==0);base[sl][shadow,:3]=(32,112,80)
    over(fore,asset,x*16,y*16);entries.append(dict(x=x,y=y,master=f'G{int(bits,2):02d}',neighbor_bits=bits))
 # Upper lawn lip and lower contact shadow remain separate from the complete
 # wall. Never cut grass-shaped holes in rock or paint greenery across stairs.
 rock=rgba(ROOT/'gba/art/johto-common/rocks/r02-joins/source/wall-and-stairs.png');stair=rgba(ROOT/'gba/art/johto-common/rocks/r02-joins/source/stairs.png')
 for y in range(288,416):
  if not stair[y-288,0,3]:
   for x,c in [(222,(96,192,144)),(223,(88,176,136))]:
    if not path[y,x]:base[y,x,:3]=c;work[y,x]=True
  if not stair[y-288,15,3] and not path[y,240]:
   # One-pixel earth lip in the adjacent ground keeps the rock's top edge
   # readable without changing its solid face. Clean source stone color only.
   base[y,240]=rock[y-288,15];work[y,240]=True
   base[y,241,:3]=(88,176,136);work[y,241]=True
 # Preserve current trees pixel-for-pixel, including crowns over ground edges.
 tree=rgba(ROOT/'gba/art/johto-common/trees/source/T01.png');tree_mask=np.zeros(base.shape[:2],bool)
 for c in np.unique(tree[tree[:,:,3]>0,:3],axis=0):tree_mask|=np.all(before[:,:,:3]==c,2)
 fore[tree_mask]=before[tree_mask]
 # Preserve original layers outside the exact affected metatiles; compose only
 # these cells. Contact shadow and turf are background; plants/trees stay above.
 changed=np.any(base!=before,2)|((fore[:,:,3]>0)&work)
 affected_cells=work.reshape(32,16,82,16).any((1,3));affected=affected_cells.repeat(16,0).repeat(16,1)
 for cy,cx in np.argwhere(affected_cells):
  for q in range(4):
   y=cy*16+q//2*8;x=cx*16+q%2*8;sl=np.s_[y:y+8,x:x+8]
   if not work[sl].any():continue
   bottom=base[sl].copy();top=fore[sl].copy();bottom[top[:,:,3]>0]=0
   layers[0][sl]=bottom;layers[1][sl]=top
 target=layers[0].copy();over(target,layers[1]);assert np.array_equal(target[~affected],before[~affected]);assert np.array_equal(target[tree_mask],before[tree_mask]);assert np.array_equal(target[288:416,224:240],before[288:416,224:240]),'Preserve accepted wall/stair surface'
 save(target,P/'review/native-target.png');save(terrain_art[272:432,192:544],P/'source/context-ground.png');save(fore[272:432,192:544],P/'source/foreground.png');dump(P/'source/grass-placement.json',entries)
 native.P=P;report=dict(base_engine=BASE,installed=install,runtime_tested=False,existing_tree_pixels_changed=0,wall_stair_pixels_changed=0,collision_elevation_changes=0,behavior_changes=0,outside_affected_pixel_changes=0,affected_cells=int(affected_cells.sum()),grass_cells=len(entries))
 if install:report.update(native.append_native(game,layers,affected,grid,attrs))
 dump(P/'evidence/structure.json',report)
 x0,y0,x1,y1=BOX;ref=rgba(native.REF)
 for n,a in [('original',ref),('before',before),('map',target)]:save(a[y0:y1,x0:x1],P/'review'/(n+'.png'))
 font=ImageFont.truetype(native.FONT,20);sheet=Image.new('RGB',(2160,410),'#202d37');d=ImageDraw.Draw(sheet)
 for i,(n,title) in enumerate([('original','ORIGINAL HGSS'),('before','PREVIOUS TRANSITIONS'),('map','REVISED NATIVE TRANSITIONS')]):
  x=i*720+8;d.text((x,10),title,font=font,fill='white');sheet.paste(Image.open(P/'review'/(n+'.png')).resize((704,320),Image.Resampling.NEAREST),(x,42))
 d.text((8,377),'Complete grass patch and rock contacts; accepted wall, stairs and movement preserved.',font=font,fill='white');sheet.save(P/'review/comparison.png')
 records=[]
 for cy in range(y0//16,y1//16):
  for cx in range(x0//16,x1//16):
   records.append(dict(x=cx,y=cy,changed=bool(affected_cells[cy,cx]),material='tall grass' if grass[cy,cx] else 'rock/stair' if cx==14 else 'terrain/contact',collision=int(grid[cy,cx]>>10&3),elevation=int(grid[cy,cx]>>12),behavior=int(attrs[cy,cx]&255),review='pending visual inspection',quadrants=[dict(offset=[dx,dy],colors=[len(np.unique(z[cy*16+dy:cy*16+dy+8,cx*16+dx:cx*16+dx+8][z[cy*16+dy:cy*16+dy+8,cx*16+dx:cx*16+dx+8,3]>0,:3],axis=0)) for z in layers]) for dy in [0,8] for dx in [0,8]]))
 dump(P/'evidence/cell-review.json',records);print(json.dumps(report,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--engine',type=Path,required=True);a.add_argument('--install',action='store_true');v=a.parse_args();main(v.engine,v.install)
