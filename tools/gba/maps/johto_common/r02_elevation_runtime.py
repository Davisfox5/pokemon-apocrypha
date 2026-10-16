"""Both flights climb east, each lane returns, walls block and saves persist."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_transitions_runtime as prior
r=prior.r
r.MAIN=r.MAIN.replace('33,22,"existing-east-stair-out"','33,21,"east-stair-climbs"').replace('31,22,"existing-east-stair-return"','31,22,"east-stair-descends-back"')
r.MAIN=r.MAIN.replace(' go(44,15,22);shot("save-location");',r'''
 go(44,31,22);shot("right-low-approach");step(RIGHT,1);at(44,32,21,"right-upper-lane-step");shot("right-step");
 step(RIGHT,1);at(44,33,21,"right-upper-landing");shot("right-high-landing");
 step(RIGHT,2);at(44,35,21,"right-path-to-grass");step(LEFT,4);at(44,31,22,"right-full-return");
 go(44,31,23);step(RIGHT,2);at(44,33,22,"right-lower-lane-climbs");step(LEFT,2);at(44,31,23,"right-lower-lane-descends");
 go(44,31,21);step(RIGHT,1);at(44,31,21,"right-top-shoulder-blocks");
 go(44,33,23);step(LEFT,1);at(44,33,23,"right-bottom-shoulder-blocks");
 go(44,31,20);step(RIGHT,1);at(44,31,20,"right-wall-blocks-west");
 go(44,33,20);step(LEFT,1);at(44,33,20,"right-wall-blocks-east");shot("right-clear-wall");
 go(44,15,17);shot("left-clear-wall");
 go(44,15,22);shot("save-location");
''')
if __name__=='__main__':r.main()
