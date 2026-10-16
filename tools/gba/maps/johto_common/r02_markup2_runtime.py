"""Owner contours: restored north route, three terraces and southwest bend."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_elevation_runtime as prior
r=prior.r
r.MAIN=r.MAIN.replace('go(44,15,17);shot("left-clear-wall")','go(44,24,20);shot("left-clear-wall")')
r.MAIN=r.MAIN.replace(' go(44,15,22);shot("save-location");',r'''
 go(44,19,3);shot("stacked-northwest");step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(DOWN,1);step(RIGHT,1);step(RIGHT,1);step(DOWN,1);step(RIGHT,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(RIGHT,1);step(RIGHT,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(RIGHT,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);step(DOWN,1);at(44,44,21,"north-connection-after-tree-shifts");
 go(44,31,9);step(RIGHT,2);at(44,33,9,"green-wall-removed");shot("restored-grass");
 go(44,34,14);shot("upper-wall-turn");
 go(44,13,24);step(LEFT,6);at(44,7,24,"southwest-approach");step(DOWN,1);at(44,7,25,"southwest-turn");shot("southwest-corner");
 step(RIGHT,1);at(44,8,25,"old-green-wall-open");step(RIGHT,1);at(44,8,25,"new-southwest-wall-blocks");step(DOWN,3);at(44,8,28,"southwest-exit");shot("color-corrected-wall");
 go(44,33,23);shot("south-wall-extension");
 go(44,58,23);shot("east-forest-shift");
 go(44,8,14);step(LEFT,1);at(44,7,14,"west-gate-apron");shot("gate-apron");
 go(44,15,22);shot("save-location");
''')
if __name__=='__main__':r.main()
