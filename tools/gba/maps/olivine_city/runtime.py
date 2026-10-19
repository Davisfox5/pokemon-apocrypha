"""Olivine ordinary walking, barriers, district travel and cold flash Continue."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from johto_connections import runtime as r
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
steps=r'''
 go(53,28,20);shot("northern-avenue");step(UP,3);at(53,28,17,"north-avenue-walking");
 go(53,19,17);shot("civic-hall");step(UP,1);at(53,19,17,"civic-hall-closed");
 go(53,23,24);shot("central-house");step(UP,1);at(53,23,24,"central-house-closed");
 go(53,37,18);shot("northeastern-residences");step(UP,1);at(53,37,18,"west-residence-closed");
 go(53,42,18);step(UP,1);at(53,42,18,"east-residence-closed");
 go(53,41,22);step(UP,3);at(53,41,19,"north-facing-stair-ascent");shot("east-stair-head");step(DOWN,3);at(53,41,22,"stair-return");
 go(53,28,24);step(DOWN,1);frames(300,0);at(54,28,1,"city-to-quay");shot("quay-north-arrival");step(UP,1);frames(300,0);at(53,28,24,"quay-to-city-return");
 go(54,15,5);shot("harbor-cafe");step(UP,1);at(54,15,5,"cafe-interior-pending");
 go(54,20,5);shot("Pokemon-Center");step(UP,1);at(54,20,5,"Center-interior-pending");
 go(54,36,6);shot("Poke-Mart");step(UP,1);at(54,36,6,"Mart-interior-pending");
 go(54,42,9);shot("lighthouse-ramp-west");step(RIGHT,6);at(54,48,9,"ramp-eastward-crossing");shot("lighthouse-terrace");step(LEFT,6);at(54,42,9,"ramp-westward-return");
 go(54,50,8);shot("lighthouse-door");step(UP,1);at(54,50,8,"lighthouse-interior-pending");
 go(54,43,3);step(RIGHT,1);at(54,43,3,"lighthouse-cliff-side-blocks");shot("east-stair-lane");
 go(54,14,13);shot("quay-furniture");step(UP,1);at(54,14,13,"bench-footprint-blocks");
 go(54,18,13);step(DOWN,1);at(54,18,13,"quayside-railing-blocks");shot("sailboat-and-railing");
 go(54,31,16);step(RIGHT,1);at(54,31,16,"pier-water-blocks-foot-travel");shot("pier-water-edge");
 go(54,28,16);step(DOWN,1);frames(300,0);at(55,28,1,"quay-to-ferry-pier");shot("ferry-pier-arrival");step(UP,1);frames(300,0);at(54,28,16,"ferry-pier-return");
 go(55,29,7);shot("ferry-terminal");step(UP,1);at(55,29,7,"ferry-service-pending");
 go(55,26,9);step(LEFT,1);at(55,26,9,"terminal-platform-sea-barrier");step(DOWN,2);at(55,26,10,"southern-exit-unwired");shot("southern-pier");
 go(53,28,1);step(UP,1);at(53,28,1,"Route39-unwired-boundary");shot("Route39-approach");
 go(54,1,7);step(LEFT,1);at(54,1,7,"Route40-unwired-boundary");shot("Route40-beach");
 go(54,28,8);shot("save-Olivine");
'''
r.MAIN=(start+steps+end).replace('at(11,27,18','at(54,28,8').replace('cold-reload-new-bark','cold-reload-Olivine')
if __name__=='__main__':r.main()
