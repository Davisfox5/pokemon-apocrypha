"""Context-aware borders and continuous rock runs: native runtime evidence."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common import r02_transitions_runtime as prior
r=prior.r
r.MAIN=r.MAIN.replace(' go(44,15,22);shot("save-location");',r'''
 go(44,15,5);shot("upper-corner");
 go(44,15,22);shot("save-location");
''')
if __name__=='__main__':r.main()
