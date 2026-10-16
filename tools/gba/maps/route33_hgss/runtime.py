"""Route33 native travel, ledges, barriers, visual sites and ordinary saves."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
steps=r'''
 go(49,19,12);shot("cave-approach");step(UP,1);frames(360,0);at(46,28,58,"route33-to-cave");step(UP,1);at(46,28,57,"southern-cave-inward");shot("south-cave-interior");step(DOWN,2);frames(360,0);at(49,19,11,"cave-to-route33");step(DOWN,1);at(49,19,12,"cave-clear-threshold");shot("cave-return");
 step(RIGHT,2);step(DOWN,6);at(49,21,18,"walk-around-source-ledge");step(LEFT,17);at(49,4,18,"road-to-Azalea-approach");shot("western-road");step(LEFT,3);at(49,1,18,"west-road-end");step(LEFT,1);at(49,1,18,"Azalea-unbuilt-boundary");
 go(49,16,15);step(DOWN,1);at(49,16,17,"south-ledge-jump");step(UP,1);at(49,16,17,"south-ledge-blocked-return");shot("south-ledge");
 go(49,14,14);step(LEFT,1);at(49,12,14,"west-ledge-jump");step(RIGHT,1);at(49,12,14,"west-ledge-blocked-return");shot("west-ledge");
 go(49,6,14);step(LEFT,1);at(49,6,14,"western-forest-footprint");shot("west-forest");
 go(49,21,13);step(UP,2);at(49,21,12,"northern-cliff-barrier");shot("northern-cliff");
 go(49,25,19);step(RIGHT,1);at(49,25,19,"eastern-cliff-barrier");shot("eastern-cliff-corner");
 go(49,8,20);step(RIGHT,5);at(49,13,20,"tall-grass-walk");shot("tall-grass");step(DOWN,1);at(49,13,21,"southern-grass-row");step(DOWN,1);at(49,13,22,"canopy-over-player");step(DOWN,1);at(49,13,22,"southern-root-barrier");shot("southern-woods");
 go(49,22,20);shot("apricorn-clearing");step(DOWN,1);at(49,22,20,"apricorn-footprint");
 go(49,31,13);step(RIGHT,1);at(49,31,13,"water-boundary-controlled-block-probe");go(49,25,19);shot("shoreline");
 go(49,20,18);shot("save-route33");
'''
r.MAIN=(start+steps+end).replace('at(11,27,18','at(49,20,18').replace('cold-reload-new-bark','cold-reload-route33')
if __name__=='__main__':r.main()
