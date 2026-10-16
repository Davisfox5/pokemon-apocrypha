"""R02 raised stair flight: actual diagonal movement, both lanes, barriers, save."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_runtime as prior
r=prior.r
r.MAIN=r.MAIN.replace('14,23,"west-step-center"','14,22,"west-step-center"').replace('15,23,"west-stairs-eastward"','15,22,"west-stairs-eastward"').replace('15,22,"upper-row-eastward"','15,21,"upper-row-eastward"').replace('go(44,15,23);shot("save-location")','go(44,15,22);shot("save-location")').replace('44,15,23,"cold-reload-r02"','44,15,22,"cold-reload-r02"').replace('44,15,23,"ordinary-title-continue"','44,15,22,"ordinary-title-continue"')
r.MAIN=r.MAIN.replace(' go(44,15,22);shot("save-location");',r'''
 go(44,13,21);step(RIGHT,1);at(44,13,21,"top-shoulder-blocks");
 go(44,15,23);step(LEFT,1);at(44,15,23,"bottom-shoulder-blocks");
 go(44,15,21);step(RIGHT,4);at(44,19,21,"raised-landing-traverse");
 step(DOWN,1);step(RIGHT,3);at(44,22,22,"path-bend-joins-existing-route");shot("path-bend");
 go(44,15,22);shot("save-location");
''')
if __name__=='__main__':r.main()
