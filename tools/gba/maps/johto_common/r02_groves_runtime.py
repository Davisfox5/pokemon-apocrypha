"""Aligned forest rows: stair regression plus the upper Route37 passage."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_elevation_runtime as prior
r=prior.r
r.MAIN=r.MAIN.replace(' go(44,15,22);shot("save-location");',r'''
 go(44,19,3);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(DOWN,1);step(RIGHT,1);step(RIGHT,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);at(44,31,17,"north-clearing-grove-rim");shot("upper-wall");
 step(LEFT,7);step(DOWN,5);at(44,24,22,"north-clearing-through-grass");step(RIGHT,7);step(RIGHT,2);at(44,33,21,"north-route-existing-stairs");step(RIGHT,11);at(44,44,21,"route37-east-clearing");shot("divider-upper-passage");
 go(44,20,17);shot("aligned-west-grove");
 go(44,39,20);shot("aligned-east-grove");
 go(44,31,14);step(RIGHT,1);at(44,31,14,"extended-wall-blocks");
 go(44,15,22);shot("save-location");
''')
if __name__=='__main__':r.main()
