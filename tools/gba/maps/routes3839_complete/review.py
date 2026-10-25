"""Independent original traversal audit, native decode/Porymap agreement and numbered comparisons."""
from pathlib import Path
import os,sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'tools/gba/maps/route31_catalog'),str(ROOT/'tools/gba/maps')]
import reference as R
from tiles import Tileset
G=Path(os.environ.get('ROUTES_ENGINE','/workspace/routes3839-complete'));A=ROOT/'gba/art/routes3839-complete';E=A/'evidence';report={}
t=Tileset(G,'routes3839_complete','routes3839_complete')
for n,w,h in [(38,64,32),(39,32,64)]:
 s=A/f'source/route{n}';native=np.array(Image.open(E/f'route{n}/native.png').convert('RGB'));orig=np.array(Image.open(s/'original.png').convert('RGB'))
 words=np.fromfile(G/f'data/layouts/JohtoRoute{n}/map.bin','<u2').reshape(h,w);perm=np.load(s/'permissions.npz');solid=(words>>10)&3;expected=(perm['collision']&128)>0
 assert np.array_equal(solid>0,expected),(n,np.argwhere((solid>0)!=expected).tolist())
 assert np.array_equal(native,np.array(Image.open(E/f'porymap/JohtoRoute{n}.png').convert('RGB')))
 attrs=np.array(t.attrs[0]+t.attrs[1]);beh=attrs[words&1023]&255
 from pack import behaviors
 mb=behaviors(G)
 for typ,name in [(2,'MB_TALL_GRASS'),(59,'MB_JUMP_SOUTH'),(56,'MB_JUMP_EAST'),(57,'MB_JUMP_WEST')]:
  mask=perm['types']==typ;assert (beh[mask]==mb[name]).all(),(n,name,np.argwhere(mask&(beh!=mb[name])).tolist())
 side=Image.new('RGB',(w*16*2,h*16+24),(28,33,38));side.paste(Image.fromarray(orig),(0,24));side.paste(Image.fromarray(native),(w*16,24));d=ImageDraw.Draw(side);d.text((8,5),f'Route {n}: original HGSS',fill='white');d.text((w*16+8,5),'Actual native map / Porymap',fill='white');side.save(E/f'route{n}/comparison.png')
 for y in range(0,h,16):
  for x in range(0,w,16):
   o=R.numbered(orig,x,y,min(x+16,w),min(y+16,h),2,title=f'Route {n}: original');v=R.numbered(native,x,y,min(x+16,w),min(y+16,h),2,title=f'Route {n}: native')
   pair=Image.new('RGB',(o.width+v.width,o.height));pair.paste(o,(0,0));pair.paste(v,(o.width,0));pair.save(E/f'route{n}/compare-grid-{x}-{y}.png')
 cells=json.loads((s/'ledger.json').read_text())['cells'];uncertain=[[x,y] for y,row in enumerate(cells) for x,c in enumerate(row) if c['material']=='none']
 report[str(n)]=dict(cells=w*h,original_solid_cells=int(expected.sum()),collision_differences=0,tall_grass_cells=int((perm['types']==2).sum()),ledge_cells=int(np.isin(perm['types'],[56,57,59]).sum()),behavior_differences=0,porymap_exact=True,unknown_ground_cells=uncertain,material_review='Original terrain-material ledger, native decoded pixels and numbered original/native sheets. Pixel equality establishes packing fidelity, not independent material accuracy or owner acceptance.')
(E/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
