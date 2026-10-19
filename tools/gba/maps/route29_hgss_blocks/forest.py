"""Whole Cherrygrove trees; allow measured forest margins to absorb open lawn."""
import numpy as np

def arrange(plan,protected,features):
 p=plan.copy();h,w=p.shape;claimed=np.zeros(p.shape,bool);positions=[]
 reserved=np.zeros(p.shape,bool)
 for house in features['houses']:
  x,y=house['x'],house['y'];reserved[y:y+6,x:x+5]=True
 for sign in features['signs']:
  x,y=sign['at'];reserved[max(0,y-1):y+2,max(0,x-1):x+2]=True
 for x,y in features['apricorns']:reserved[max(0,y-1):y+1,x:x+1]=True
 g=features['gate'];x,y=g['x'],g['y'];reserved[y:y+g['height']+1,x:x+g['width']]=True
 walk=np.zeros(p.shape,bool)
 for x,y in features.get('walk_cells',[]):walk[y,x]=True
 p[walk&(p=='T')]='.'
 reserved|=walk
 # Pin complete trees beside the narrower HGSS gate; do not conceal a
 # bypass with blocked lawn or widen the building itself.
 for x,y in features.get('fixed_trees',[])+features.get('gate_flank_trees',[]):
  assert not protected[y:y+3,x:x+2].any()
  assert np.isin(p[y+1:y+3,x:x+2],['T','.','G']).all()
  assert not reserved[y+1:y+3,x:x+2].any()
  claimed[y+1:y+3,x:x+2]=True;positions.append((x,y));p[y+1:y+3,x:x+2]='T'
 allowed=np.isin(p,['T','.','G'])&~protected&~reserved
 # Two-row ground courses keep front/rear canopy overlaps consistent. Each
 # course is scored as a whole so odd forest strips absorb one lawn column.
 for y in range(0,h-2,2):
  candidates=[]
  for x in range(w-1):
   if not allowed[y+1:y+3,x:x+2].all():continue
   if not (np.isin(p[y,x:x+2],['T','.','G','#'])&~protected[y,x:x+2]&(~reserved[y,x:x+2]|walk[y,x:x+2])).all():continue
   target=int(np.count_nonzero(p[y+1:y+3,x:x+2]=='T'))
   if target<1:continue
   cost=int(np.count_nonzero(p[y+1:y+3,x:x+2]!='T'))
   candidates.append((-target,cost,x))
  for _,cost,x in sorted(candidates):
   if claimed[y+1:y+3,x:x+2].any():continue
   claimed[y+1:y+3,x:x+2]=True;positions.append((x,y));p[y+1:y+3,x:x+2]='T'
 canvases=np.zeros(p.shape,bool)
 for x,y in positions:canvases[y:y+3,x:x+2]=True
 # Unoccupied forest-edge cells become the same lawn as the neighboring
 # clearing. Rocks are terrain features, never substitutes for tree crowns.
 remnants=(p=='T')&~canvases&~protected&~reserved
 p[remnants]='.'

 return p,positions,{'whole_trees':len(positions),'open_ground_absorbed':int(np.count_nonzero((plan!='T')&(p=='T'))),'forest_edge_lawn_cells':int(remnants.sum()),'native_rock_boundary_cells':0,'partial_tree_fillers':0,'outer_wall_adjustment':'none; expand forests only into spare ground'}
