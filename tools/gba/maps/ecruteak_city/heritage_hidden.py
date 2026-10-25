"""Reuse exact compatible BG glyphs only behind opaque foreground pixels.
All visible RGBA and every foreground alpha/priority pixel are invariant, including
walkable cells. No nearest-color substitution or visible texture loss occurs.
"""
from pathlib import Path
import json,collections,numpy as np
from PIL import Image
S=Path(__file__).resolve().parents[4]/'gba/art/ecruteak-city/source';bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));before=bg.copy();reports=[]
for bank,y0,y1 in [('ecruteak_temple',0,432),('ecruteak_city',432,832)]:
 patches=[bg[y:y+8,x:x+8].copy() for y in range(y0,y1,8) for x in range(0,1152,8)];freq=collections.Counter(p.tobytes() for p in patches);freq[bytes(256)]+=1
 candidates=[np.frombuffer(b,np.uint8).reshape(8,8,4) for b,n in freq.most_common()];ca=np.array(candidates);cache={};changed=0
 # For a fixed foreground mask, choose one already existing BG pattern for each
 # exact visible signature. Frequent existing patterns win deterministically.
 for y in range(y0,y1,8):
  for x in range(0,1152,8):
   a=bg[y:y+8,x:x+8];hidden=fg[y:y+8,x:x+8,3]>0
   if not hidden.any():continue
   key=hidden.tobytes()
   if key not in cache:
    lookup={}
    for i,v in enumerate(ca[:,~hidden,:]):lookup.setdefault(v.tobytes(),i)
    cache[key]=lookup
   idx=cache[key][a[~hidden].tobytes()];new=ca[idx]
   if not np.array_equal(a,new):a[:]=new;changed+=1
 after={bg[y:y+8,x:x+8].tobytes() for y in range(y0,y1,8) for x in range(0,1152,8)};reports.append(dict(bank=bank,nonempty_BG_patterns_before=len(patches) and len(freq)-1,after=len(after),reused_hidden_patches=changed))
mask=fg[...,3]>0;assert np.array_equal(bg[~mask],before[~mask]);Image.fromarray(bg).save(S/'background.png');(S/'heritage/hidden-glyph-reuse.json').write_text(json.dumps(dict(reports=reports,visible_RGBA_changes=0,foreground_changes=0),indent=2)+'\n');print(reports)
