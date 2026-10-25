"""Independent logical material ledger for repaired receiving planes."""
import numpy as np
def update_ground(ground,assembly):
 g=ground.copy();H,W=g.shape
 def box(x,y,w,h,label):
  for cy,cx in np.ndindex(H,W):
   sx,sy=cx*16-64,cy*16-16
   area=max(0,min(sx+16,x+w)-max(sx,x))*max(0,min(sy+16,y+h)-max(sy,y))
   if area>256*.3:g[cy,cx]=label
 box(248,120,192,152,'C')
 for p in assembly['rock_placements']:box(p['x']-64,p['y']-16,16,16,'R')
 for r in [(616,552,160,112),(776,432,160,112)]:box(*r,'P')
 for x,y,w,h,door in [(288,344,120,80,None),(448,344,120,80,None),(288,448,120,88,336),(448,448,120,88,None),(624,440,128,96,688),(792,448,128,88,840),(288,560,120,96,352),(448,560,120,96,528),(632,560,128,96,696),(784,560,128,96,864)]:
  box(x,y,w,h,'C')
  if door is not None:box(door-16,y+h-8,32,16,'P')
 return g
