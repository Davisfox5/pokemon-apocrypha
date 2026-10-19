"""Exact two-layer packing at blocked tree joins; no RGB approximation.

Cover files are verified against every actual patch before encoding. Open cells
keep their original foreground mask and priority. Native Porytiles still compiles
and independently verifies the result; these files are not native tile IDs.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image

def encode(S,bg,fg,solid,areas):
 mask=np.zeros(bg.shape[:2],bool)
 for x,y,xx,yy in areas:mask[y:yy,x:xx]=True
 changes=[];above=np.load(S/'tree-closure/above.npy')
 # Covered pixels never reveal their background, even beside a player.
 for y,x in np.ndindex(52,72):
  if solid[y,x]:
   a=bg[y*16:y*16+16,x*16:x*16+16];b=fg[y*16:y*16+16,x*16:x*16+16];a[b[...,3]>0]=0
 for bank,y0,y1,short in [('ecruteak_temple',0,432,'temple'),('ecruteak_city',432,832,'city')]:
  cover=json.loads((S/'tree-closure'/(short+'-flexible-cover.json')).read_text());pals=[set(map(tuple,p)) for p in cover['banks']]
  assert len(pals)==13 and all(len(p)<=15 for p in pals)
  for y in range(y0,y1,8):
   for x in range(0,1152,8):
    sl=np.s_[y:y+8,x:x+8];a=bg[sl].copy();b=fg[sl].copy();ca=set(map(tuple,a[a[...,3]>0,:3]));cb=set(map(tuple,b[b[...,3]>0,:3]))
    if any(ca<=p for p in pals) and any(cb<=p for p in pals):continue
    assert (mask[sl].any() or cover.get('allow_all_blocked',False)) and solid[y//16,x//16] and not (above[y//16,x//16] and y//16<51 and not solid[y//16+1,x//16]),('Open foreground must stay intact',x,y)
    target=a.copy();m=b[...,3]>0;target[m]=b[m];cs=set(map(tuple,target[...,:3].reshape(-1,3)));opts=[]
    for i,pa in enumerate(pals):
     for j,pb in enumerate(pals):
      if not cs<=pa|pb:continue
      keep=np.array([tuple(c) not in pa or (bool(mm) and tuple(c) in pb) for c,mm in zip(target[...,:3].reshape(-1,3),m.ravel())]).reshape(8,8)
      back=target.copy();back[keep,:3]=sorted(pa)[0];front=target.copy();front[~keep]=0
      score=(int((keep==m).sum()),-int(keep.sum()),-i,-j);opts.append((score,back,front,i,j))
    assert opts,('No exact palette pair',bank,x,y)
    _,back,front,i,j=max(opts,key=lambda z:z[0]);check=back.copy();check[front[...,3]>0]=front[front[...,3]>0];assert np.array_equal(check,target)
    bg[sl]=back;fg[sl]=front;changes.append(dict(x=x,y=y,banks=[i,j]))
  inp=S/bank;(inp/'exact-palette-cover.json').write_text(json.dumps(cover,indent=2)+'\n');out=inp/'palette-overrides';out.mkdir(exist_ok=True)
  for i,p in enumerate(pals):
   lines=['-']+[' '.join(map(str,c)) for c in sorted(p)]+['-']*(15-len(p));(out/f'{i:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(lines)+'\n')
 return changes

def finish(S,bg,fg,solid):
 """Deduplicate blocked background glyphs without changing visible pixels."""
 hidden=[];single=[];above=np.load(S/'tree-closure/above.npy')
 for y in range(0,832,8):
  for x in range(0,1152,8):
   if solid[y//16,x//16] and (fg[y:y+8,x:x+8,3]>0).all():bg[y:y+8,x:x+8]=0;hidden.append([x,y])
 banks={n:[set(map(tuple,p)) for p in json.loads((S/n/'exact-palette-cover.json').read_text())['banks']] for n in ['ecruteak_temple','ecruteak_city']}
 baseline=np.array(Image.open(S/'tree-closure/baseline/background.png'));restored=[]
 for y in range(0,832,8):
  pals=banks['ecruteak_temple' if y<432 else 'ecruteak_city']
  for x in range(0,1152,8):
   if not solid[y//16,x//16]:continue
   a=bg[y:y+8,x:x+8];m=a[...,3]>0
   if not m.any() or m.all():continue
   candidate=baseline[y:y+8,x:x+8];cs=set(map(tuple,candidate[...,:3].reshape(-1,3)))
   if (candidate[...,3]>0).all() and np.array_equal(a[m,:3],candidate[m,:3]) and any(cs<=p for p in pals):a[:]=candidate;restored.append([x,y])
   else:
    colors=set(map(tuple,a[m,:3]))
    if len(colors)==1:a[~m]=list(next(iter(colors)))+[255];restored.append([x,y])
 for y in range(0,832,8):
  pals=banks['ecruteak_temple' if y<432 else 'ecruteak_city']
  for x in range(0,1152,8):
   if not solid[y//16,x//16] or (above[y//16,x//16] and y//16<51 and not solid[y//16+1,x//16]):continue
   a=bg[y:y+8,x:x+8];b=fg[y:y+8,x:x+8];m=b[...,3]>0;target=a.copy();target[m]=b[m];cs=set(map(tuple,target[...,:3].reshape(-1,3)))
   if m.any() and any(cs<=p for p in pals):a[:]=target;b[:]=0;single.append([x,y])
 return dict(fully_hidden_blocked_background_quadrants=hidden,single_bank_blocked_quadrants=single,restored_hidden_background_patterns=restored)
