"""Transition review: grass boundaries, complete plateau path, existing stair probes."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_joins_runtime as prior
r=prior.r
r.MAIN=r.MAIN.replace(' go(44,15,22);shot("save-location");',r'''
 go(44,19,21);step(UP,1);at(44,19,20,"raised-grass-entry");shot("grass-landing-edge");
 step(DOWN,1);at(44,19,21,"raised-grass-return");
 go(44,25,22);step(UP,1);at(44,25,21,"east-grass-entry");shot("grass-east-edge");
 step(DOWN,1);at(44,25,22,"east-grass-return");
 step(RIGHT,6);at(44,31,22,"plateau-east-approach");shot("plateau-east-approach");
 step(RIGHT,2);at(44,33,22,"existing-east-stair-out");
 step(LEFT,2);at(44,31,22,"existing-east-stair-return");
 go(44,15,22);shot("save-location");
''')
if __name__=='__main__':r.main()
