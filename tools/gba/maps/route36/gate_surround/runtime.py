"""Reuse Route 36's background ROM tour with fresh paths and gate barriers."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from route36 import runtime as previous
legs=json.loads((ROOT/'gba/art/route36/gate-surround/evidence/walk-plan.json').read_text());walk=[]
for leg in legs:
 for key,x,y in leg['steps']:walk.append(f' step({key},1);at(44,{x},{y},"gate-walk-{len(walk):03}");')
 walk.append('shot("'+leg['name']+'");')
previous.r.MAIN=previous.r.MAIN.replace('\n'.join(previous.walk),'\n'.join(walk))
previous.r.MAIN=previous.r.MAIN.replace(' go(44,68,20);shot("save-at-route36");',r'''
 go(44,7,11);step(UP,1);at(44,7,11,"park-rear-trees-block");shot("park-rear-trees");
 go(44,6,15);step(LEFT,1);at(44,6,15,"park-front-trees-block");shot("park-foreground-trees");
 go(44,74,15);step(RIGHT,1);at(44,74,15,"violet-rear-trees-block");shot("violet-rear-trees");
 go(44,74,21);step(RIGHT,1);at(44,74,21,"violet-front-trees-block");shot("violet-foreground-trees");
 go(44,74,20);shot("violet-gate-layering");
 go(44,7,14);shot("park-gate-layering");
 go(44,68,20);shot("save-at-route36");''')
if __name__=='__main__':previous.r.main()
