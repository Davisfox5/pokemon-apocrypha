"""Ecruteak exterior movement and ordinary flash-save/cold-Continue checks."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from johto_connections import runtime as r
start=r.MAIN[:r.MAIN.index('  // Actual east connection')]
end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
steps=r'''
 go(51,41,8);shot("central-avenue");
 step(UP,7);at(51,41,1,"northbound-city-avenue");step(UP,1);frames(300,0);at(52,41,25,"temple-district-entry");shot("northern-avenue");
 step(DOWN,1);frames(300,0);at(51,41,1,"city-return");shot("city-district-return");
 go(52,25,18);step(UP,4);at(52,25,14,"Burned-Tower-stair-axis");shot("Burned-Tower");step(UP,1);at(52,25,14,"tower-interior-pending");
 step(DOWN,4);at(52,25,18,"tower-stair-return");step(LEFT,1);at(52,24,18,"tower-south-court");
 go(52,22,19);step(UP,1);at(52,22,19,"terrace-fence-blocks");
 go(52,17,15);step(RIGHT,1);at(52,17,15,"Burned-Tower-west-grove-blocks");shot("tower-west-apron");
 go(52,45,13);step(UP,1);at(52,45,13,"Bell-entrance-back-grove-blocks");shot("Bell-entrance-grove");
 go(52,32,19);step(UP,1);at(52,32,19,"restored-east-terrace-fence-blocks");shot("restored-terrace-fence");
 go(52,41,18);shot("Bell-Tower-entrance");step(UP,1);at(52,41,18,"Bell-Tower-interior-pending");
 go(52,44,20);shot("pond-west-bank");step(RIGHT,1);at(52,44,20,"pond-blocks-foot-travel");
 go(51,47,7);shot("Dance-Theater");step(UP,1);at(51,47,7,"theater-interior-pending");
 go(51,26,14);shot("Ecruteak-Gym");step(UP,1);at(51,26,14,"Gym-interior-pending");
 go(51,47,14);shot("Pokemon-Center");step(UP,1);at(51,47,14,"Center-interior-pending");
 go(51,56,7);shot("Poke-Mart");step(UP,1);at(51,56,7,"Mart-interior-pending");
 go(51,41,16);step(DOWN,3);at(51,41,19,"southern-torii-passage");shot("southern-torii");step(LEFT,1);at(51,41,19,"torii-left-post-blocks");step(RIGHT,1);at(51,42,19,"torii-opening-right");step(RIGHT,1);at(51,42,19,"torii-right-post-blocks");
 go(51,19,10);step(LEFT,1);at(51,18,10,"west-forest-edge");step(LEFT,1);at(51,18,10,"west-forest-blocks");shot("western-woodland");
 go(52,21,25);step(RIGHT,1);at(52,21,25,"north-house-lantern-base-blocks");shot("house-lantern-north");
 go(51,21,5);step(RIGHT,1);at(51,21,5,"west-house-lantern-base-blocks");shot("house-lantern-west");
 go(52,18,24);shot("gateway-lanterns");
 go(51,35,4);step(DOWN,1);step(LEFT,2);at(51,33,5,"central-empty-plot-open");shot("central-plot");
 go(51,36,14);shot("southern-house-court");
 go(52,8,25);step(LEFT,1);at(52,7,25,"west-gate-approach");step(LEFT,1);at(52,7,25,"west-gate-wall-blocks");step(UP,1);at(52,7,25,"west-gate-north-bypass-blocks");shot("west-gate-closure");
 go(51,8,3);step(LEFT,1);at(51,8,3,"west-gate-south-bypass-blocks");
 go(51,64,6);step(RIGHT,1);at(51,65,6,"east-gate-approach");step(RIGHT,1);at(51,65,6,"east-gate-wall-blocks");shot("east-gate-closure");
 go(51,65,4);step(UP,1);at(51,65,4,"east-gate-north-bypass-blocks");
 go(51,64,10);step(DOWN,1);at(51,64,10,"east-gate-south-bypass-blocks");
 go(51,38,17);step(DOWN,1);at(51,38,17,"torii-west-bypass-blocks");
 go(51,44,17);step(DOWN,1);at(51,44,17,"torii-east-bypass-blocks");
 go(51,39,16);step(DOWN,1);at(51,39,17,"old-gate-ghost-collision-cleared");step(DOWN,1);at(51,39,17,"left-tree-root-stays-blocked");
 go(51,40,17);step(DOWN,1);at(51,40,17,"moved-left-post-north-blocks");
 go(51,43,17);step(DOWN,1);at(51,43,17,"moved-right-post-north-blocks");
 go(51,40,20);step(UP,1);at(51,40,20,"moved-left-post-south-blocks");
 go(51,43,20);step(UP,1);at(51,43,20,"moved-right-post-south-blocks");
 go(51,42,16);step(DOWN,6);at(51,42,22,"torii-right-lane-southbound");step(UP,6);at(51,42,16,"torii-right-lane-northbound");
 go(51,41,16);step(DOWN,6);at(51,41,22,"torii-center-southbound-open");shot("torii-woodland-closure");step(UP,6);at(51,41,16,"torii-center-northbound-open");
 go(51,41,8);shot("save-Ecruteak");
'''
r.MAIN=(start+steps+end).replace('at(11,27,18','at(51,41,8').replace('cold-reload-new-bark','cold-reload-Ecruteak')
if __name__=='__main__':r.main()
