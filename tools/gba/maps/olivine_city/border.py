"""Native terrain continuation beyond the current isolated Olivine exterior.
Mirrored by OlivineViewMetatile in the engine; gameplay captures verify parity.
"""
def border_cell(x,y):
 if y<0:return min(64,max(0,x)),y%2
 if y>=54:
  if 22<=x<27:return x,52+y%2
  return 2+x%2,42+y%2
 if x<0:
  if y<40:return 0,y
  return 2+x%2,42+y%2
 if x>=65:
  if y<19:return 64,y
  return 2+x%2,42+y%2
 return x,y
