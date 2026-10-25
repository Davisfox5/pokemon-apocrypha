"""Exercise every audited reachable open->blocked edge with real game input."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import runtime
r=runtime.r;cases=json.loads((HERE.parents[3]/'gba/art/ecruteak-city/evidence/gate-alignment/boundary-cases.json').read_text());steps=[]
for i,c in enumerate(cases):steps.append(' go(%d,%d,%d);step(%s,1);at(%d,%d,%d,"boundary-%04d");'%(c['map'],c['x'],c['y'],c['direction'],c['map'],c['x'],c['y'],i))
steps.append(' go(51,41,8);')
start=r.MAIN.index(' go(51,41,8);shot("central-avenue")');end=r.MAIN.index('  unsigned status=call("TrySavingData"')
r.MAIN=r.MAIN[:start]+'\n'.join(steps)+'\n'+r.MAIN[end:]
if __name__=='__main__':r.main()
