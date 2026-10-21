"""Actual headless walking over new native maps, stairs, seam, ordinary flash."""
from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
steps='''
 go(53,60,12);shot("route38-east");step(LEFT,10);at(53,50,12,"route38-eastern-path");
 go(53,14,10);step(UP,5);at(53,14,5,"route38-upper-clearing");shot("route38-upper-path");
 go(53,10,20);step(LEFT,1);at(53,9,20,"route38-west-cliff-approach");step(LEFT,1);at(53,9,20,"route38-west-cliff-blocks");shot("route38-west-cliff");
 go(53,30,24);step(RIGHT,1);at(53,31,24,"route38-east-cliff-approach");step(RIGHT,1);at(53,31,24,"route38-east-cliff-blocks");shot("route38-east-cliff");
 go(54,25,24);shot("farm-stair-head");step(DOWN,5);at(54,25,29,"farm-stairs-descend");shot("farm-stair-foot");step(UP,5);at(54,25,24,"farm-stairs-ascend");
 go(54,29,49);shot("south-stair-head");step(DOWN,4);at(54,29,53,"south-stairs-descend");shot("south-stair-foot");step(UP,4);at(54,29,49,"south-stairs-ascend");
 go(54,15,22);step(LEFT,4);at(54,11,22,"former-farm-fence-cleared");shot("farm-cleared");
 go(54,12,7);step(RIGHT,5);at(54,17,7,"former-house-cleared");shot("house-cleared");
 go(54,14,37);step(DOWN,3);at(54,14,40,"former-tall-grass-cleared");shot("southern-clearing");
 go(54,24,39);step(DOWN,3);at(54,24,42,"former-ledge-cleared");step(UP,3);at(54,24,39,"former-ledge-return");
'''
for y in range(12,15):
 steps+=f' go(53,1,{y});step(LEFT,2);at(54,37,{y+2},"west-seam-{y}");shot("west-seam-{y}");step(LEFT,1);at(54,36,{y+2},"west-seam-walk-{y}");step(RIGHT,2);at(53,0,{y},"east-seam-{y}");shot("east-seam-{y}");step(RIGHT,1);at(53,1,{y},"east-seam-walk-{y}");\n'
if '--boundaries' in sys.argv:
 sys.argv.remove('--boundaries');steps='\n'.join(' go(%d,%d,%d);step(%s,1);at(%d,%d,%d,"boundary-%04d");'%(c['map'],c['x'],c['y'],c['direction'],c['map'],c['x'],c['y'],i) for i,c in enumerate(json.loads((HERE.parents[3]/'gba/art/route38-39-terrain/evidence/boundary-cases.json').read_text())))
steps+=' go(54,25,20);shot("save-route39");\n'
r.MAIN=(start+steps+end).replace('at(11,27,18','at(54,25,20').replace('cold-reload-new-bark','cold-reload-route39')
if __name__=='__main__':r.main()
