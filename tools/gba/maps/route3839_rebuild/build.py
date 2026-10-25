"""New terrain-only map version from decoded HGSS cells and a native cliff kit.
Independent of rejected composite renders; writes only the rebuilt private pair.
"""
from pathlib import Path
import sys,json,subprocess,struct,shutil
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt,binary_fill_holes
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);PT=Path(sys.argv[2]);S=ROOT/'gba/art/route38-39-rebuild/source';E=S.parent/'evidence';E.mkdir(exist_ok=True)
assert not subprocess.check_output(['git','-C',str(G),'ls-files','data/tilesets/primary/route3839_rebuild'],text=True).strip(),'Committed rebuild exists: edit native sources, never replay.'
from kit import assets,lawn,grass,dirt,finish_cliff
master=ROOT/'gba/art/route38-39-terrain/source/masters';stairs={n:np.array(Image.open(master/(n+'.png')).convert('RGBA')) for n in ['0xaf','0xcf']}
allpairs=[];unique={};maps=[];audits=[];adaptations=[]
for route,W,H in [(38,64,32),(39,32,64)]:
 z=np.load(S/f'route{route}-original.npz');typ=z['types'];col=z['collision'];h=z['height'].copy();known=z['height_known'];top=z['wall_top'];bottom=z['wall_bottom'];wx=z['normal_x'];wz=z['normal_z'];ramp=z['incline'].copy();gr=z['grass_ramp'];wcover=z['wall_coverage'];rcover=z['road_coverage'];mat=np.full((H,W),'L',dtype='<U1');walk=np.full((H,W),'.',dtype='<U1');wall=wcover>.12;faces=np.full((H,W),'',dtype='<U1')
 # Genuine slopes are kept; Rock Climb's blocked face is terrain, not a stair.
 ramp&=~((typ==0x4c)&((col&0x80)!=0));# Every remaining BDHC incline is a real grass/stair/earth transition.
 # Classify original materials independently of the new art/collision.
 for y,x in np.ndindex(H,W):
  t,c=int(typ[y,x]),int(col[y,x]);reason=None
  if t==0 and not(c&0x80):
   mat[y,x]='P' if rcover[y,x]>.35 else 'L'
   if (c&4==0)!=(mat[y,x]=='P'):reason='ordinary terrain flag is not a visible dirt guarantee on this route; original bound road mesh resolves the material'
  elif t==0 and c&0x80:
   mat[y,x]='P' if rcover[y,x]>.5 else 'L';reason='blocked ordinary cell: original road mesh resolves concealed ground; foreground removed unless genuine rock'
  elif t in [2,6,0x38,0x39,0x3b,0x3e]:mat[y,x]='L';reason='owner requested tall grass, forest or jump-ledge removal'
  else:mat[y,x]='P' if rcover[y,x]>.5 else 'L';reason=f'owner-cleared prop/entrance type{t:02x}; ground from original mesh context'
  if reason:adaptations.append(dict(route=route,x=x,y=y,type=t,collision=c,reason=reason))
  if ramp[y,x]:wall[y,x]=False
 # Axis-aligned directions come from original faces and are checked against
 # actual higher/lower neighboring planes before any native tile is selected.
 for y,x in np.ndindex(H,W):
  if not wall[y,x]:continue
  nx,nz=wx[y,x],wz[y,x]
  if abs(nx)+abs(nz)<.01:
   vals=[]
   for dx,dy,d in [(0,1,'S'),(0,-1,'N'),(-1,0,'W'),(1,0,'E')]:
    xx=min(W-1,max(0,x+dx*2));yy=min(H-1,max(0,y+dy*2));vals.append((h[yy,xx],d))
   faces[y,x]=min(vals)[1]
  else:faces[y,x]=('E' if nx>0 else 'W') if abs(nx)>abs(nz) else ('S' if nz>0 else 'N')
  dx,dy={'N':(0,-1),'S':(0,1),'W':(-1,0),'E':(1,0)}[faces[y,x]];hi=h[min(H-1,max(0,y-dy*2)),min(W-1,max(0,x-dx*2))];lo=h[min(H-1,max(0,y+dy*2)),min(W-1,max(0,x+dx*2))]
  if hi+.4<lo:faces[y,x]={'N':'S','S':'N','E':'W','W':'E'}[faces[y,x]]
 # A two-unit south face gets two complete courses, aligned to the source stair.
 for y,x in np.argwhere(wall.copy()):
  if faces[y,x]!='S':continue
  rise=round(float(top[y,x]-bottom[y,x]))
  if rise>=2:
   for yy in range(y,min(H,y+rise)):
    if not ramp[yy,x]:wall[yy,x]=True;faces[yy,x]='S'
 # Closed original outcrop contours keep their plateau cap, not a lawn hole.
 holes=binary_fill_holes(wall)&~wall
 # Enclosed defined grass planes are genuine terrace tops, not stone fill.
 # Only Route38's small impassable model outcrop has its cap above the
 # continuous walking-height plane underneath.
 holes&=(np.indices((H,W))[1]>=60) if route==38 else False
 wall|=holes
 for y,x in np.argwhere(holes):
  local=top[max(0,y-1):y+2,max(0,x-1):x+2];h[y,x]=round(float(local.max()));mat[y,x]='O';faces[y,x]='O';known[y,x]=False
 for y,x in np.argwhere(wall):
  if mat[y,x]!='O':mat[y,x]='R'
  walk[y,x]='X'
 for y,x in np.argwhere(ramp):mat[y,x]='A' if gr[y,x] else 'S' if route==39 else 'D';walk[y,x]='.'
 bg=np.zeros((H*16,W*16,4),np.uint8);choice=[]
 def neighbor(a,x,y,dx,dy,default=False):return a[y+dy,x+dx] if 0<=x+dx<W and 0<=y+dy<H else default
 for y,x in np.ndindex(H,W):
  phase=f'{x%2}{y%2}';base=assets[f'lawn-{phase}'];name=f'lawn-{phase}';a=base.copy();m=mat[y,x]
  if m=='P':
   mask=sum(bit for bit,dx,dy in [(1,0,-1),(2,1,0),(4,0,1),(8,-1,0)] if neighbor(mat,x,y,dx,dy,'P') in ['P','S','D']);name=f'dirt-{mask:02x}-{phase}';a=assets[name].copy()
  elif m in ['R','O']:
   if m=='O':
    name='stone-cap';a=np.array(Image.open(ROOT/'gba/art/ecruteak-city/source/masters/route32-shelf-top.png').convert('RGBA'))
   else:
    f=faces[y,x];dx,dy={'N':(0,-1),'S':(0,1),'W':(-1,0),'E':(1,0)}[f];behind=neighbor(wall,x,y,-dx,-dy,False);role='body' if behind else 'rim';name=f'{f}-{role}-{phase}';a=assets[name].copy()
    # Join two perpendicular courses with one complete corner metatile.
    around=set(str(neighbor(faces,x,y,xx,yy,'')) for xx,yy in [(0,-1),(0,1),(-1,0),(1,0)] if neighbor(wall,x,y,xx,yy,False))
    horiz=around&{'W','E'};vert=around&{'N','S'}
    empty=[not neighbor(wall,x,y,dx,dy,True) for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]]
    turn=any(empty[i] and empty[(i+1)%4] for i in range(4)) or any(not neighbor(wall,x,y,dx,dy,True) and neighbor(wall,x,y,dx,0,True) and neighbor(wall,x,y,0,dy,True) for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)])
    if horiz and vert and turn:
     fx=f if f in horiz else sorted(horiz)[0];fy=f if f in vert else sorted(vert)[0];high=('N' if fy=='S' else 'S')+('E' if fx=='W' else 'W');hx=1 if 'E' in high else -1;hy=1 if 'S' in high else -1;exposure=(1 if not neighbor(wall,x,y,hx,hy,True) else 0)|(2 if not neighbor(wall,x,y,-hx,-hy,True) else 0);name=f'corner-{high}-{exposure}-{phase}';a=assets[name].copy()
  elif m in ['S','D']:
   a=dirt[np.arange(y*16,y*16+16)[:,None]%32,np.arange(x*16,x*16+16)[None,:]%32].copy();name='earth-ramp' if m=='D' else 'stairs'
   if m=='S':
    first=not neighbor(ramp,x,y,-1,0,False);st=stairs['0xaf' if first else '0xcf'].copy();st[...,:3]&=248;mask=st[...,3]>0;a[mask]=st[mask]
  elif m=='A':
   name='grass-slope';a[12:15,:,:3]=[88,176,136]
  if m=='R':
   exposed=0
   for bit,dx1,dy1,dx2,dy2 in [(1,-1,0,0,-1),(2,1,0,0,-1),(4,1,0,0,1),(8,-1,0,0,1)]:
    if not neighbor(wall,x,y,dx1,dy1,True) and not neighbor(wall,x,y,dx2,dy2,True):exposed|=bit
   fx,fy={'N':(0,-1),'S':(0,1),'W':(-1,0),'E':(1,0)}[faces[y,x]];ground='P' if neighbor(mat,x,y,fx,fy,'L')=='P' else 'L';name,a=finish_cliff(name,a,exposed,phase,ground)
  a[...,:3]&=248;bg[y*16:(y+1)*16,x*16:(x+1)*16]=a;choice.append(dict(x=x,y=y,material=str(m),tile=name,original_height=round(float(h[y,x]),3),height_known=bool(known[y,x]),face=str(faces[y,x]) if m in ['R','O'] else None))
 solid=wall.copy();elev=np.clip(np.rint(h)*2-1,1,13).astype(np.uint8);elev[ramp]=0
 solid[0]=solid[-1]=True;solid[:,0]=solid[:,-1]=True
 if route==38:solid[11:14,0]=False
 else:solid[11:14,-1]=False
 # Separate remaining open plane boundaries are inspected before installation.
 bad=[]
 for y,x in np.ndindex(H,W):
  for dx,dy in [(1,0),(0,1)]:
   xx,yy=x+dx,y+dy
   if xx<W and yy<H and not solid[y,x] and not solid[yy,xx] and elev[y,x] and elev[yy,xx] and elev[y,x]!=elev[yy,xx]:bad.append([x,y,xx,yy,int(elev[y,x]),int(elev[yy,xx])])
 Image.fromarray(bg).save(S/f'route{route}-art.png');Image.fromarray(bg).save(E/f'route{route}-candidate.png');np.savez(S/f'route{route}-layers.npz',material=mat,solid=solid,elevation=elev,source_height=h,source_height_known=known,faces=faces)
 (S/f'route{route}-tile-ledger.json').write_text('[\n'+',\n'.join(json.dumps(v,separators=(',',':')) for v in choice)+'\n]\n');(S/f'route{route}-materials.txt').write_text('\n'.join(''.join(r) for r in mat)+'\n')
 cells=[]
 for y,x in np.ndindex(H,W):
  a=bg[y*16:(y+1)*16,x*16:(x+1)*16];key=a.tobytes()
  if key not in unique:unique[key]=len(allpairs);allpairs.append(a)
  cells.append(unique[key]|(int(elev[y,x])<<12)|(0xc00 if solid[y,x] else 0))
 maps.append((route,W,H,np.array(cells,'<u2').reshape(H,W)));audits.append(dict(route=route,open_height_seams=bad,wall_cells=int(wall.sum())))
np.savez(S/'candidate.npz',**{f'route{n}':grid for n,w,h,grid in maps},pairs=np.array(allpairs));(S/'adaptations.json').write_text('[\n'+',\n'.join(json.dumps(v,separators=(',',':')) for v in adaptations)+'\n]\n');(E/'authoring-audit.json').write_text(json.dumps(audits,indent=2)+'\n');print('Candidate metatiles',len(allpairs),json.dumps(audits))
