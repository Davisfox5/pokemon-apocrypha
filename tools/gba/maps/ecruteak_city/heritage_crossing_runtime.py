"""Drive every native paired district crossing both ways, including side motion."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import runtime
r=runtime.r;d=json.loads((HERE.parents[3]/'gba/art/ecruteak-city/source/heritage/district-crossings.json').read_text());steps=[]
for x in d['columns']:
 steps.append(' go(51,%d,0);step(UP,1);frames(300,0);at(52,%d,26,"north-crossing-%02d");step(DOWN,1);frames(300,0);at(51,%d,0,"south-crossing-%02d");'%(x,x,x,x,x))
for x in [28,29,38,39]:steps.append(' go(51,%d,0);step(UP,1);at(51,%d,0,"blocked-northern-root-%02d");'%(x,x,x))
steps+=[' go(52,41,26);step(LEFT,1);at(52,40,26,"north-edge-sideways-stays");',' go(51,41,0);step(LEFT,1);at(51,40,0,"south-edge-sideways-stays");',' go(51,41,8);']
start=r.MAIN.index(' go(51,41,8);shot("central-avenue")');end=r.MAIN.index('  unsigned status=call("TrySavingData"');r.MAIN=r.MAIN[:start]+'\n'.join(steps)+'\n'+r.MAIN[end:]
if __name__=='__main__':r.main()
