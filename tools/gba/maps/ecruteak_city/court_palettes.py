"""Exact thirteen-bank cover for the locally refined Ecruteak layers.
Requires ortools 9.10; each 8px patch must retain every authored color.
"""
import json
from ortools.sat.python import cp_model

def solve(inp,patches):
 cs=sorted(set.union(*(set(p) for p in patches)));ci={c:i for i,c in enumerate(cs)};model=cp_model.CpModel();banks=[[model.NewBoolVar(f'b{b}c{i}') for i in range(len(cs))] for b in range(13)]
 for bank in banks:model.Add(sum(bank)<=15)
 choices=[]
 for j,p in enumerate(patches):
  row=[model.NewBoolVar(f'p{j}b{b}') for b in range(13)];model.AddExactlyOne(row);choices.append(row)
  for b in range(13):
   for c in p:model.AddImplication(row[b],banks[b][ci[c]])
 # Remove irrelevant colors: every allocated shade belongs to an assigned patch.
 for b in range(13):
  for c,i in ci.items():model.Add(banks[b][i]<=sum(choices[j][b] for j,p in enumerate(patches) if c in p))
 # Warm hints preserve the old allocation where suitable; they impose no color
 # approximation or hard constraint on the new material families.
 cache=inp/'exact-palette-cover.json'
 if cache.exists():
  old=[set(map(tuple,p)) for p in json.loads(cache.read_text())['banks']]
  for b in range(13):
   for c,i in ci.items():model.AddHint(banks[b][i],int(c in old[b]))
  for j,p in enumerate(patches):
   best=min(range(13),key=lambda b:(len(p-old[b]),-len(p&old[b])))
   for b in range(13):model.AddHint(choices[j][b],int(b==best))
 solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=180;solver.parameters.num_search_workers=8;solver.parameters.random_seed=23
 status=solver.Solve(model);print(inp.name,solver.StatusName(status),flush=True)
 assert status in [cp_model.OPTIMAL,cp_model.FEASIBLE],'Exact native palette cover did not fit; no detail may be silently discarded.'
 result=[[c for c,v in zip(cs,bank) if solver.Value(v)] for bank in banks]
 assert all(any(set(p)<=set(bank) for bank in result) for p in patches)
 out=inp/'palette-overrides';out.mkdir(exist_ok=True)
 for i,pal in enumerate(result):
  lines=['-']+[' '.join(map(str,c)) for c in pal]+['-']*(15-len(pal));(out/f'{i:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(lines)+'\n')
 cache.write_text(json.dumps(dict(maximal_patches=len(patches),colors=len(cs),solver='OR-Tools CP-SAT 9.10.4067 exact color-set covering',banks=[[list(map(int,c)) for c in p] for p in result]),indent=2)+'\n')
