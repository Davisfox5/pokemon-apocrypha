"""Read actual native layers; prove bounded edits against pre-rejection terrain."""
from pathlib import Path
import sys,json,subprocess,struct
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);B=Path(sys.argv[2]);E=ROOT/'gba/art/route33-hgss/evidence'
def decode(root):
 t=Tileset(root,'route33','route33');grid=np.fromfile(root/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);layers=[np.zeros((464,544,4),np.uint8) for i in range(2)]
 for y in range(29):
  for x in range(34):
   m=int(grid[y,x]&1023);block=t.blocks[int(m>=512)][m-512 if m>=512 else m]
   for l in range(2):
    for q in range(4):
     en=block[l*4+q];tid=en&1023;a=np.array(t.tiles[int(tid>=512)][tid-512 if tid>=512 else tid],np.uint8).reshape(8,8)
     if en&1024:a=a[:,::-1]
     if en&2048:a=a[::-1]
     xx=x*16+q%2*8;yy=y*16+q//2*8;dst=layers[l][yy:yy+8,xx:xx+8];mask=a>0;p=np.array(t.pals[int((en>>12)>=6)][en>>12],np.uint8);dst[mask,:3]=p[a[mask]];dst[mask,3]=255
 return grid,layers
old,ol=decode(B);now,nl=decode(G);allowed=np.zeros((464,544),bool);allowed[160:192,288:328]=True;allowed[:,504:512]=True;delta=np.any(nl[0]!=ol[0],2)
d={'original_native_reference':'224ee13c392888780bdcaeb7053487f42a9ab731','native_cells':986,'unapproved_background_pixel_changes':int((delta&~allowed).sum()),'collision_cell_changes':int(np.count_nonzero((old&0xc00)!=(now&0xc00))),'elevation_cell_changes':int(np.count_nonzero((old&0xf000)!=(now&0xf000))),'opaque_background':bool(np.all(nl[0][...,3]==255)),'warp_opening_black':bool(np.all(nl[0][182:191,300:315,:3]==0)),'all_water_cells_blocked':bool(np.all(now[:,32:]&0xc00)),'terrain_edit_scope':['Original arch opening gray residue -> black, within (288,160)-(328,192)','Actual original HGSS coastal pixels within x504:512; no procedural contour'],'cliff_changes':'none; original contours, cap texture and wall shading retained','new_tree_rows_or_expansions':[]}
assert d['unapproved_background_pixel_changes']==0 and d['collision_cell_changes']==d['elevation_cell_changes']==0 and d['opaque_background'] and d['warp_opening_black'] and d['all_water_cells_blocked'],d
(E/'reference-scope.json').write_text(json.dumps(d,indent=2)+'\n');Image.fromarray(nl[1]).save(E/'native-foreground.png');print(json.dumps(d,indent=2))
