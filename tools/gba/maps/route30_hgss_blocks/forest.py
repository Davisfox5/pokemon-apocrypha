"""Whole Cherrygrove trees; allow measured forest margins to absorb open lawn."""
import numpy as np

def arrange(plan,protected,features):
 p=plan.copy();h,w=p.shape;claimed=np.zeros(p.shape,bool);positions=[]
 # An odd-width outer wood cannot hold another complete two-cell tree.
 # Shift its separating wall into spare ground, without narrowing the road.
 for y in list(range(36,63))+list(range(64,74)):
  if p[y,3]=='#' and p[y,4] in ['T','.','G']:
   p[y,3]='T';p[y,4]='#'
 for y in range(1,46):
  if p[y,33]=='#' and p[y,34]=='#':p[y,33]='T'
 reserved=np.zeros(p.shape,bool)
 for house in features['houses']:
  x,y=house['x'],house['y'];reserved[y:y+6,x:x+5]=True
 for sign in features['signs']:
  x,y=sign['at'];reserved[max(0,y-1):y+2,max(0,x-1):x+2]=True
 for x,y in features['apricorns']:reserved[max(0,y-1):y+1,x:x+1]=True
 for x,y in [(20,44),(21,44),(18,6),(18,7)]:reserved[y,x]=True
 for tree in features['divider_trees']:
  x,y=tree['x'],tree['y'];reserved[y:y+3,x:x+2]=True
 allowed=np.isin(p,['T','.','G'])&~protected&~reserved
 # Two-row ground courses keep front/rear canopy overlaps consistent. Each
 # course is scored as a whole so odd forest strips absorb one lawn column.
 for y in range(0,h-2,2):
  candidates=[]
  for x in range(w-1):
   if not allowed[y+1:y+3,x:x+2].all():continue
   if not (np.isin(p[y,x:x+2],['T','.','G','#'])&~protected[y,x:x+2]&~reserved[y,x:x+2]).all():continue
   target=int(np.count_nonzero(p[y+1:y+3,x:x+2]=='T'))
   if target<1:continue
   cost=int(np.count_nonzero(p[y+1:y+3,x:x+2]!='T'))
   candidates.append((-target,cost,x))
  for _,cost,x in sorted(candidates):
   if claimed[y+1:y+3,x:x+2].any():continue
   claimed[y+1:y+3,x:x+2]=True;positions.append((x,y));p[y+1:y+3,x:x+2]='T'
 canvases=np.zeros(p.shape,bool)
 for x,y in positions:canvases[y:y+3,x:x+2]=True
 # Narrow terrain remnants remain physical barriers, using complete native
 # rock tiles rather than a cropped crown or an invisible blocked lawn tile.
 remnants=(p=='T')&~canvases&~protected&~reserved
 p[remnants]='R'
 return p,positions,{'whole_trees':len(positions),'open_ground_absorbed':int(np.count_nonzero((plan!='T')&(p=='T'))),'native_rock_boundary_cells':int(remnants.sum()),'partial_tree_fillers':0,'outer_wall_adjustment':'west wall column 3 to 4 in lower woods; east wall retains column 34, column 33 absorbed into woods'}
