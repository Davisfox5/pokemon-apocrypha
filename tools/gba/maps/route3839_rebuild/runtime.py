"""Walk corrected stairs, grass ramp, earth junction and every wall boundary."""
from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
steps='''
 go(53,57,12);shot("route38-east");step(LEFT,10);at(53,47,12,"route38-square-main-path");
 go(53,12,10);step(UP,6);at(53,12,4,"route38-square-upper-path");shot("route38-upper-path");
 go(53,10,21);shot("route38-west-corner");
 go(53,30,21);shot("route38-raised-southern-bank");step(DOWN,5);at(53,30,26,"route38-bank-approach");step(DOWN,1);at(53,30,26,"route38-bank-blocks");
 go(54,19,24);shot("farm-stair-head");
'''
for x in range(18,21):steps+=f' go(54,{x},24);step(DOWN,5);at(54,{x},29,"farm-stairs-down-{x}");shot("farm-stair-foot-{x}");step(UP,5);at(54,{x},24,"farm-stairs-up-{x}");\n'
for x in range(22,25):steps+=f' go(54,{x},55);shot("south-stair-head-{x}");step(DOWN,4);at(54,{x},59,"south-stairs-down-{x}");shot("south-stair-foot-{x}");step(UP,4);at(54,{x},55,"south-stairs-up-{x}");\n'
for x in range(6,15):steps+=f' go(54,{x},24);step(DOWN,5);at(54,{x},29,"grass-ramp-down-{x}");step(UP,5);at(54,{x},24,"grass-ramp-up-{x}");\n'
steps+='''
 go(54,9,28);shot("lower-farm-paddock");
 go(54,24,35);shot("east-wall-upper");step(RIGHT,1);at(54,24,35,"east-wall-blocks");
 go(54,24,48);shot("east-wall-compound-corner");
 go(54,8,42);shot("west-wall-middle");
 go(54,11,52);shot("west-wall-lower-corner");
 go(54,17,42);step(DOWN,3);at(54,17,45,"removed-jump-ledges-flat");step(UP,3);at(54,17,42,"removed-jump-ledges-return");
'''
for y in range(11,14):steps+=f' go(53,2,{y});step(LEFT,3);at(54,31,{y},"west-junction-{y}");shot("west-junction-{y}");step(LEFT,1);at(54,30,{y},"west-junction-walk-{y}");step(RIGHT,2);at(53,0,{y},"east-junction-{y}");step(RIGHT,2);at(53,2,{y},"earth-ramp-return-{y}");shot("earth-ramp-{y}");\n'
if '--boundary-part' in sys.argv:
 i=sys.argv.index('--boundary-part');part=int(sys.argv[i+1]);del sys.argv[i:i+2];cases=json.loads((HERE.parents[3]/'gba/art/route38-39-rebuild/evidence/boundary-cases.json').read_text());steps='\n'.join(' go(%d,%d,%d);step(%s,1);at(%d,%d,%d,"boundary-%04d");'%(c['map'],c['x'],c['y'],c['direction'],c['map'],c['x'],c['y'],j) for j,c in enumerate(cases) if j%2==part)
steps+=' go(54,19,23);shot("save-route39");\n';r.MAIN=(start+steps+end).replace('at(11,27,18','at(54,19,23').replace('cold-reload-new-bark','cold-reload-corrected-route39')
if __name__=='__main__':r.main()
