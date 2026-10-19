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
 go(52,19,14);step(RIGHT,1);at(52,19,14,"tower-west-apron-face-blocks");step(DOWN,2);at(52,19,16,"tower-west-apron-walks");shot("tower-west-apron");
 go(52,41,18);shot("Bell-Tower-entrance");step(UP,1);at(52,41,18,"Bell-Tower-interior-pending");
 go(52,44,20);shot("pond-west-bank");step(RIGHT,1);at(52,44,20,"pond-blocks-foot-travel");
 go(51,47,7);shot("Dance-Theater");step(UP,1);at(51,47,7,"theater-interior-pending");
 go(51,26,14);shot("Ecruteak-Gym");step(UP,1);at(51,26,14,"Gym-interior-pending");
 go(51,47,14);shot("Pokemon-Center");step(UP,1);at(51,47,14,"Center-interior-pending");
 go(51,56,7);shot("Poke-Mart");step(UP,1);at(51,56,7,"Mart-interior-pending");
 go(51,41,16);step(DOWN,3);at(51,41,19,"southern-torii-passage");shot("southern-torii");step(LEFT,1);at(51,40,19,"torii-opening-left");step(LEFT,1);at(51,40,19,"torii-left-post-blocks");
 go(51,19,10);step(LEFT,1);at(51,18,10,"west-forest-edge");step(LEFT,1);at(51,18,10,"west-forest-blocks");shot("western-woodland");
 go(51,41,8);shot("save-Ecruteak");
'''
r.MAIN=(start+steps+end).replace('at(11,27,18','at(51,41,8').replace('cold-reload-new-bark','cold-reload-Ecruteak')
if __name__=='__main__':r.main()
