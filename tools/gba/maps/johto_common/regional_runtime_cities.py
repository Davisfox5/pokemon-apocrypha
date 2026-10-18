"""Shared cliff visual/step probes plus unchanged service-door/save regressions."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_service_buildings import runtime as prior
r=prior.r
r.MAIN=r.MAIN.replace(' go(0,56,10);shot("save-at-cherrygrove");',r'''
 go(0,20,6);shot("coast-west");step(DOWN,1);at(0,20,6,"coast-cap-blocked");step(DOWN,1);at(0,20,6,"coast-front-blocked");shot("coast-barrier");
 go(0,37,6);shot("coast-end");
 go(29,32,17);shot("route31-west-stair-landing");step(RIGHT,3);at(29,35,17,"route31-stairs-east");shot("route31-east-stair-landing");step(LEFT,3);at(29,32,17,"route31-stairs-west");
 go(29,38,27);shot("route31-south-stair-head");step(DOWN,2);at(29,38,29,"route31-south-stairs-down");step(UP,2);at(29,38,27,"route31-south-stairs-up");
 go(29,52,14);shot("dark-cave-rock-front");step(UP,1);frames(360,0);observe("dark-cave-entry");need(state[2]==34,"dark-cave-entry");step(DOWN,1);frames(360,0);observe("dark-cave-return");need(state[2]==29,"dark-cave-return");shot("dark-cave-return");
 go(29,58,14);shot("dark-cave-east-rock");go(29,44,7);shot("dark-cave-west-rock");
 go(0,56,10);shot("save-at-cherrygrove");
''')
if __name__=='__main__':r.main()
