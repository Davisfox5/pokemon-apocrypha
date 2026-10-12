#!/usr/bin/env python3
"""Compare all camera/transition-visible cells under either native tileset."""
import sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from tiles import Tileset
from claude_routes import seams
G=Path(sys.argv[1]).resolve();ROOT=Path(__file__).resolve().parents[4]
r,rs=seams.read_layout(G,'CherrygroveRoute30Approach',35,86);rr=seams.reachable(rs,(8,85))
rt=Tileset(G,'claude_route30','cherrygrove');reports=[]
for name,secondary,w,h,ox,oy,start in [('CherrygroveCity','cherrygrove',80,48,-35,86,(43,0)),('JohtoRoute31','route31',63,30,-28,-30,(38,29))]:
 n,ns=seams.read_layout(G,name,w,h);nr=seams.reachable(ns,start);nw,rw,pairs=seams.crossing_windows(ns,rs,-ox,-oy)
 masks=[('neighbor',n,seams.visible_across(rr,ns.shape,ox,oy)|nw),('route30',r,seams.visible_across(nr,rs.shape,-ox,-oy)|rw)]
 nt=Tileset(G,secondary,'cherrygrove');tested=set();errors=[]
 for side,grid,mask in masks:
  for mid in np.unique(grid[mask]):
   mid=int(mid);tested.add(mid)
   a=np.asarray(rt.render(mid));b=np.asarray(nt.render(mid))
   count=int(np.any(a!=b,2).sum())
   if count:errors.append({'side':side,'metatile':mid,'different_pixels':count})
 reports.append({'neighbor':name,'crossing_pairs':pairs,'unique_metatiles_compared':len(tested),'errors':errors})
 assert not errors,(name,errors)
(ROOT/'gba/art/route30-rebuild/evidence/seam-assets.json').write_text(json.dumps(reports,indent=2)+'\n')
print('Both connected tilesets render all visible seam metatiles identically')
