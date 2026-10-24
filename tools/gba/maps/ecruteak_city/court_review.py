"""Review actual decoded Ecruteak output against HGSS and preserved c8f961."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';B=S/'court-refinement/baseline';D=E/'court-refinement';D.mkdir(exist_ok=True)
ref=Image.open(S/'hgss-reference.png').convert('RGB');registered=Image.new('RGB',(1152,832),'#223039');registered.paste(ref,(64,16));old=Image.open(B/'native-map.png').convert('RGB');now=Image.open(E/'native-map.png').convert('RGB');r=json.loads((E/'assembly.json').read_text())
def sheet(name,box,scale=2):
 w,h=box[2]-box[0],box[3]-box[1];im=Image.new('RGB',(w*scale*3+32,h*scale+56),'#223039');d=ImageDraw.Draw(im)
 for i,(label,a) in enumerate([('HGSS original',registered),('Previous c8f961',old),('Refined native',now)]):
  x=8+i*(w*scale+8);d.text((x,6),label,fill='white');d.text((x,22),'Native cells '+str([box[0]//16,box[1]//16,box[2]//16,box[3]//16]),fill='white');im.paste(a.crop(box).resize((w*scale,h*scale),Image.Resampling.NEAREST),(x,48))
 im.save(D/(name+'.png'))
for n,box in [('northwest-court',(344,344,488,456)),('northeast-court',(504,344,648,456)),('west-house-court',(344,448,488,568)),('central-plot',(504,448,648,568)),('gym-court',(344,552,488,704)),('southwest-house-court',(504,560,648,704)),('center-court',(688,552,840,704)),('mart-court',(848,440,1000,568)),('southeast-court',(840,560,984,704)),('theater-court',(680,432,832,568)),('burned-tower',(304,96,512,320)),('temple',(536,184,752,304)),('west-gateway-lanterns',(200,368,304,448)),('east-gateway-lanterns',(920,368,1024,448))]:sheet(n,box)
sheet('whole-map',(0,0,1152,832),1)
# Canopy-free views reveal complete rock courses rather than hiding seams.
bg=np.array(Image.open(S/'background.png').convert('RGBA'));fg=np.zeros_like(bg)
for p in r['placements']:
 if p['name'] in ['tree-hgss','maple-hgss','maple-amber','maple-autumn']:continue
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=a.shape[:2];m=a[...,3]>0;fg[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m]
m=fg[...,3]>0;bg[m]=fg[m];im=Image.fromarray(bg).convert('RGB');box=(304,104,512,320);w,h=208,216;out=Image.new('RGB',(w*6+32,h*2+32),'#223039');d=ImageDraw.Draw(out)
for i,(label,a) in enumerate([('HGSS: occluded faces uncertain',registered),('Native without canopy',im),('Native with canopy',now)]):x=8+i*(w*2+8);d.text((x,6),label,fill='white');out.paste(a.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x,24))
out.save(D/'tower-without-canopies.png')
# Exact visible directional modules after later terrain/foreground placement.
bg=np.array(Image.open(S/'background.png').convert('RGBA'));fg=np.array(Image.open(S/'foreground.png').convert('RGBA'));owner=np.zeros(bg.shape[:2],np.uint16);masters={}
for i,p in enumerate(r['directional_wall_placements'],1):
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=a.shape[:2];owner[p['y']:p['y']+h,p['x']:p['x']+w][a[...,3]>0]=i;masters[i]=a
checks=[]
for i,p in enumerate(r['directional_wall_placements'],1):
 a=masters[i];h,w=a.shape[:2];visible=(owner[p['y']:p['y']+h,p['x']:p['x']+w]==i)&(fg[p['y']:p['y']+h,p['x']:p['x']+w,3]==0);assert np.array_equal(np.array(now)[p['y']:p['y']+h,p['x']:p['x']+w][visible],a[visible,:3]);checks.append(dict(**p,visible_pixels=int(visible.sum()),RGB_errors=0))
oldsolid=np.load(B/'solid.npy');solid=np.load(S/'solid.npy');changes=[dict(x=int(x),y=int(y),before=bool(oldsolid[y,x]),after=bool(solid[y,x]),reason='restored lantern support/base') for y,x in np.argwhere(oldsolid!=solid)]
shared=[]
for n in ['center','mart','gate']:
 assert (B/'masters'/(n+'.png')).read_bytes()==(S/'masters'/(n+'.png')).read_bytes();shared.append(dict(name=n,unchanged=True,sha256=hashlib.sha256((S/'masters'/(n+'.png')).read_bytes()).hexdigest()))
assert r['trees']==json.loads((B/'assembly.json').read_text())['trees']
(D/'audit.json').write_text(json.dumps(dict(baseline_source='c8f961fc5a84cce6f3c71c0db58b19f8e3a9dd29',courts=r['courts'],wall_modules=checks,collision_changes=changes,shared_masters=shared,tree_anchors_unchanged=True,central_plot='Unbuilt earth and sign are present in HGSS; no omitted building.',owner_visual_acceptance='pending',limits=['Original overview interpretation, including hidden walls; native palette reduction approximates source shades.','Interiors and neighboring routes remain unwired.']),indent=2)+'\n')
print('Reviewed',len(r['courts']),'courts;',len(checks),'directional wall modules;',len(changes),'collision edits')
