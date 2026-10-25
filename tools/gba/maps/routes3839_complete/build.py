"""Fresh Route 38/39 native source authoring; original HGSS geometry, shared Johto catalog art.
Run only on the isolated pre-route baseline. Committed native maps become authoritative.
"""
from pathlib import Path
import os,sys,json,shutil,importlib.util
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]; TOOLS=ROOT/'tools/gba/maps'
sys.path[:0]=[str(TOOLS/'route31_catalog'),str(TOOLS)]
import reference as Ref, assemble as A, rock as Rock, pack as Pack
spec=importlib.util.spec_from_file_location('farm_buildings',TOOLS/'route30_catalog/buildings.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
R=Ref.R; B.R=R
PHG=Path(os.environ.get('HGSS_SOURCE','/workspace/scratch/route3839-original'));ENGINE=Path(os.environ.get('ROUTES_ENGINE','/workspace/routes3839-complete'));ART=ROOT/'gba/art/routes3839-complete'

def setup(n):
 s=ART/f'source/route{n}'; ev=ART/f'evidence/route{n}';ev.mkdir(parents=True,exist_ok=True)
 w,h=(64,32) if n==38 else (32,64)
 for k,v in dict(W=w,H=h,HW=w,HH=h,PAD0=h,COL0=0,ROW0=0,SRC=s,XPHASE=0,YPHASE=0).items():setattr(Ref,k,v)
 for k,v in dict(W=w,H=h,HW=w,HH=h,XPHASE=0,YPHASE=0,LOCAL=s/'local-art').items():setattr(A,k,v)
 A.LOCAL.mkdir(exist_ok=True);Pack.W=w;Pack.H=h
 R.AREA_BANK=7;R.HEADER_ID=n+4;R.MATERIAL_NAMES.clear();Ref._TD.clear();Ref.WALLS=('wall01_g','wall01_d','cliff01gs','wall_area06','wall01_h','r_climb');Ref.GATE_MODEL=-1
 (s/'hgss').mkdir(exist_ok=True);shutil.copyfile(s/'permissions.npz',s/'hgss/hgss-permissions.npz')
 return s,ev,w,h

def build(n):
 s,ev,w,h=setup(n)
 info=json.loads((s/'original.json').read_text());ox,oz=np.array(info['meta']['matrix_origin'])*32
 raw=json.loads((PHG/f'files/fielddata/eventdata/zone_event/{n+1:03}_R{n}.json').read_text())
 local=lambda e:[int(e['x']-ox),int(e['z']-oz)]
 events=dict(signs=[dict(cell=local(e),bg_type=e['type']) for e in raw['bgs']],objects=[dict(cell=local(e),sprite=e['spriteId']) for e in raw['objects']],warps=[dict(cell=local(e),destination=e['header']) for e in raw['warps']])
 cells=Ref.ledger(PHG,info,events)
 # Material authority is terrain, building footprints, and original blocked bytes independently.
 for b in info['buildings']:
  if b['model'] not in (112,113):continue
  x0,y0,x1,y1=b['footprint']
  for y in range(max(0,int(y0)),min(h,int(np.ceil(y1)))):
   for x in range(max(0,int(x0)),min(w,int(np.ceil(x1)))):
    if cells[y][x]['blocked']:cells[y][x]['lab']='B'
 for e in events['warps']:
  x,y=e['cell'];cells[y][x]['lab']='D'
 # Original stair collision 6 includes grass slopes; preserve those as lawn ramps.
 for row in cells:
  for c in row:
   if c['blocked'] and c['material']=='r_climb':c['lab']='R'
   if c['lab']=='^' and c['material']=='grass_slope':c['lab']='.'
 woods=Ref.woods_mask(cells);roots,detected=Ref.tree_roots(woods,cells)
 # This three-row woodland shoulder has its original trunks on row 10.
 # Shift the two complete 2x2 roots south inside the same blocked footprint.
 if n==38:roots=[(x,9) if (x,y) in [(26,8),(28,8)] else (x,y) for x,y in roots]
 grid=Ref.material_grid(cells,woods,roots,events)
 for e in events['warps']:
  x,y=e['cell'];grid[y][x]='D'
 (s/'ledger.json').write_text(json.dumps(dict(registration=dict(px_per_cell=16,origin=[0,0]),cells=cells),indent=1)+'\n')
 (s/'events.json').write_text(json.dumps(events,indent=2)+'\n')
 (s/'trees.json').write_text(json.dumps(dict(roots=roots,detected=detected),indent=1)+'\n')
 (s/'material-grid.txt').write_text('\n'.join(f'{y:03} '+''.join(row) for y,row in enumerate(grid))+'\n')
 road=A.road_texture(ENGINE);q=A.ground_quadrants(PHG,cells)
 # Square native tile boundaries, with the shared small corner/rim profile. No wave/diagonal paths.
 A.G.WAVE=[0]*32
 bottom,mat,tex=A.paint_ground(q,road)
 d,isrock=Rock.terraces(cells,0)
 bottom,rock,pieces=Rock.rock_frlg(cells,d,isrock,bottom,Rock.frlg_pieces(ENGINE),dict(grass=tex[A.G.GRASS],sand=tex[A.G.PATH]))
 m=rock[...,3]>0;bottom[m]=rock[m,:3]
 flat=np.zeros((h*16,w*16,4),np.uint8);top=np.zeros_like(flat);owner=np.full((h*16,w*16),'',object)
 def lay(a):A.over(flat,a,0,0)
 light=A.light_lawn(PHG);flower=A.flowers(PHG)
 for a,tones in [(light,3),(flower,6)]:lay(A.apply_tones(a,A.reduce_tones([a],set(),tones)))
 stairs,stair_list=A.stairs(grid);m=stairs[...,3]>0;bottom[m]=stairs[m,:3]
 # Fences retain HGSS's explicit original material silhouette and connected post positions.
 z=np.load(s/'materials.npz');names=list(z['names']);gm=z['material'];src=np.array(Image.open(s/'ground.png').convert('RGB'))
 fence=np.zeros_like(flat);m=gm==names.index('fence_a');fence[m,:3]=src[m];fence[m,3]=255
 fence=A.apply_tones(fence,A.reduce_tones([fence],set(),5));lay(fence)
 tg=A.rgba(A.SHARED/'G15.png')
 for y in range(h):
  for x in range(w):
   if grid[y][x]=='G':A.over(flat,tg,x*16,y*16)
 la,ledge_list=A.ledges(grid);lay(la)
 # The shared ledge composer handles south/east; mirror its east family for west-facing ledges.
 mirrored=[[('E' if c=='Q' else 'Q' if c=='E' else c) for c in row[::-1]] for row in grid]
 west_layer,_=A.ledges(mirrored);west_layer=west_layer[:,::-1].copy()
 for y in range(h):
  for x in range(w):
   if grid[y][x]=='Q' or (grid[y][x]=='J' and y>0 and grid[y-1][x]=='Q'):
    flat[y*16:(y+1)*16,x*16:(x+1)*16]=west_layer[y*16:(y+1)*16,x*16:(x+1)*16]
 tree=A.cherry_tree(ENGINE,tex[A.G.GRASS]);objs=[dict(name=f'tree_{i}',xy=[x*16,(y-1)*16],art=tree,root=[x,y]) for i,(x,y) in enumerate(roots)]
 for b in info['buildings']:
  if b['model'] in (31,32,34):
   x,y=int(b['pos'][0]),int(b['pos'][2]);a=A.rgba(A.SHARED/('P14.png' if b['model']==32 else 'P13.png'))
   objs.append(dict(name=f'sign_{x}_{y}',xy=[x*16-8,(y+1)*16-a.shape[0]],art=a))
 if n==39:
  models=R.load(PHG)[2]
  house=next(b for b in info['buildings'] if b['model']==112);door=next(b for b in info['buildings'] if b['model']==114)
  parts=[(112,(0,0,0)),(114,tuple(np.array(door['pos'])-np.array(house['pos'])))]
  for name,parts,width,x,base in [('farmhouse',parts,144,48,80),('silo',[(113,(0,0,0))],64,24,31*16)]:
   a,_=B.view(models,parts,width);a=B.finish(a,B.sprite_palette(a));a=B.reuse_tiles(a,x%8)
   Image.fromarray(a).save(A.LOCAL/f'{name}.png');objs.append(dict(name=name,xy=[x,base-a.shape[0]],art=a))
 for o in objs:o['base']=o['xy'][1]+o['art'].shape[0]
 for o in sorted(objs,key=lambda o:(o['base'],o['xy'][0])):A.over(top,o['art'],*o['xy'],owner,o['name'])
 trav=Pack.traversal(ENGINE,[[('g' if c in 'DWV' else c) for c in row] for row in grid],cells)
 # Keep original solid bytes authoritative, including narrow fences missed by dominant-material labels.
 for y in range(h):
  for x in range(w):
   c=cells[y][x];t=trav[y,x]
   if c['blocked'] and c['lab'] not in 'LQE':t.update(foot='blocked',collision=1,elevation=0)
   if c['lab']=='D' and not c['blocked']:t.update(foot='open',collision=0,elevation=3)
 above=Pack.above_player(trav,top,owner)
 view=bottom.copy()
 for a in [flat,top]:m=a[...,3]>0;view[m]=a[m,:3]
 Image.fromarray(view).save(ev/'composed.png')
 np.savez_compressed(s/'layers.npz',ground=bottom,flat=flat,top=top,owner=owner.astype(str),above=above,quadrants=q,terrace=d)
 (s/'traversal.json').write_text(json.dumps(trav.tolist(),indent=1)+'\n')
 (s/'placements.json').write_text(json.dumps(dict(objects=[{k:v for k,v in o.items() if k!='art'} for o in objs],stairs=stair_list,ledges=ledge_list),indent=1,default=int)+'\n')
 for y in range(0,h,16):
  for x in range(0,w,16):
   Ref.numbered(view,x,y,min(x+16,w),min(y+16,h),2,grid,f'Route {n} native composition').save(ev/f'grid-{x}-{y}.png')
 print('COMPOSED',n,len(roots),'trees',len(stair_list),'stair cells',flush=True)
if __name__=='__main__':
 for n in map(int,sys.argv[1:] or [38,39]):build(n)
