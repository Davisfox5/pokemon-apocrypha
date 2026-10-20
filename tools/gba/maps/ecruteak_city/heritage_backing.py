"""Retain original ground and court edges during local tree/fixture replacement."""
from pathlib import Path
import json,numpy as np
from PIL import Image
S=Path(__file__).resolve().parents[4]/'gba/art/ecruteak-city/source';B=S/'heritage/baseline';E=S.parent/'evidence';r=json.loads((B/'assembly.json').read_text());bg=np.array(Image.open(S/'background.png'));oldbg=np.array(Image.open(B/'background.png'));owner=np.zeros(bg.shape[:2],int);colors=set();changed=[]
for i,p in enumerate(r['placements']):
 a=np.array(Image.open(B/'masters'/(p['name']+'.png')));h,w=a.shape[:2];owner[p['y']:p['y']+h,p['x']:p['x']+w][a[...,3]>0]=i+1
 if p['name'] in ['tree-hgss','maple-hgss','maple-autumn','maple-amber','house-lantern','shrine-lantern','south-gate']:changed.append(i+1);colors.update(map(tuple,a[a[...,3]>0,:3]))
mask=np.load(S/'heritage/changed-pixels.npz')['mask'];original_art=np.isin(owner,changed);rest=mask&~original_art
# Also retain genuine original ground hidden under former foreground pixels.
old_art_color=np.zeros(bg.shape[:2],bool)
for c in colors:old_art_color|=np.all(oldbg[...,:3]==c,2)
rest|=mask&original_art&~old_art_color&(oldbg[...,3]>0)
# Keep the new court and approach ground as explicitly authored.
rest[240:352,912:992]=False;rest[336:352,896:992]=False;rest[352:384,944:976]=False
bg[rest]=oldbg[rest];Image.fromarray(bg).save(S/'background.png');fg=np.array(Image.open(S/'foreground.png'));out=bg.copy();out[fg[...,3]>0]=fg[fg[...,3]>0];Image.fromarray(out).save(S/'heritage/preview.png');print('Retained original court/wall backing',int(rest.sum()))
