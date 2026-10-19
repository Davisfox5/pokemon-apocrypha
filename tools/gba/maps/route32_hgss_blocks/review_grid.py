"""Compare independently reviewed HGSS squares with decoded native engine collision.
The HGSS side is a visual terrain/footprint trace, not extracted DS collision data.
"""
from pathlib import Path
import sys,csv,json
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
G=Path(sys.argv[1]);OUT=HERE.parents[3]/'gba/art/route32-hgss-blocks';S=OUT/'source';E=OUT/'evidence'
t=Tileset(G,'route32','route32');grid=np.fromfile(G/'data/layouts/JohtoRoute32/map.bin','<u2').reshape(128,32)
beh=np.array([t.attrs[int(v>=512)][v-512 if v>=512 else v]&255 for v in (grid&1023).ravel()]).reshape(grid.shape)
# Ordinary foot movement; one-way ledge transitions are audited separately.
actual=((grid&0xc00)!=0)|np.isin(beh,[16,21]);expected=np.load(S/'hgss-reference-blocked.npy');native=actual[1:126,1:31]
source=np.array([list(r) for r in (S/'hgss-cell-grid.txt').read_text().splitlines()])
# Owner-selected canonical Violet prefab is 112px wide, versus HGSS's 80px.
# List the 14 additional footprint squares individually: no broad exclusion mask.
adapted={(16,y) for y in range(103,108)}|{(22,y) for y in range(103,108)}|{(x,107) for x in [17,18,20,21]}
y,x=np.where(expected!=native);differences=[(int(xx),int(yy)) for xx,yy in zip(x,y)]
unexplained=[c for c in differences if c not in adapted];assert not unexplained,('Unreviewed source/native barrier difference',unexplained)
with (S/'source-native-walkability.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['source_x','source_y','native_x','native_y','source_terrain','HGSS_visual_foot_blocked','native_foot_blocked','metatile','behavior','difference_reason'])
 for sy in range(125):
  for sx in range(30):
   nx,ny=sx+1,sy+1;reason='canonical_Violet_Center_footprint' if (sx,sy) in differences else ''
   w.writerow([sx,sy,nx,ny,source[sy,sx],int(expected[sy,sx]),int(native[sy,sx]),hex(int(grid[ny,nx]&1023)),hex(int(beh[ny,nx])),reason])
report={'source_basis':'numbered original HGSS screenshot; visually reviewed terrain and rooted footprints, not DS collision binary','source_cells_reviewed':3750,'exact_binary_matches':3750-len(differences),'canonical_Center_additional_footprint_cells':[{'source':[sx,sy],'native':[sx+1,sy+1]} for sx,sy in differences],'unexplained_binary_differences':unexplained,'one_way_ledges':[{'source':[int(xx),int(yy)],'native':[int(xx+1),int(yy+1)],'direction':'south'} for yy,xx in zip(*np.where(source=='_'))],'NS_stair_pixels':'unchanged from fe8df8b','native_static_secondary_glyphs':len(t.tiles[1]),'animated_primary_slots_reserved':[1,92],'door_scratch_reserved':[1008,1023]}
(E/'grid-audit.json').write_text(json.dumps(report,indent=2)+'\n')
ref=Image.open(S/'hgss-reference.png').convert('RGB');im=t.map_image(grid.ravel().tolist(),32);im.save(E/'native-map.png')
# Readable full-size raster and quarter sheets retain the underlying artwork.
combined=Image.new('RGB',(1060,2120),(26,33,37));d=ImageDraw.Draw(combined)
combined.paste(ref,(20,48));combined.paste(im,(540,32));d.text((20,12),'HGSS: reviewed 16px source grid',fill='white');d.text((540,12),'Gen 3: decoded native collision grid',fill='white')
for sy in range(125):
 for sx in range(30):
  for ox,oy,flag in [(20,48,bool(expected[sy,sx])),(556,48,bool(native[sy,sx]))]:
   color=(232,95,85) if flag else (100,235,149)
   if (sx,sy) in differences and ox==556:color=(92,164,255)
   # A corner mark keeps trees, shoreline and stair treads visible.
   x0,y0=ox+sx*16,oy+sy*16;d.line((x0+1,y0+13,x0+3,y0+13),fill=color,width=2)
for x in range(0,31,2):
 d.text((20+x*16,2057),str(x),fill='white');d.text((556+x*16,2057),str(x+1),fill='white')
d.text((20,2090),'Green: foot floor. Red: barrier/water/ledge. Blue: 14 wider Center footprint cells.',fill='white')
combined.save(E/'source-grid-comparison.png')
for n in range(4):
 out=Image.new('RGB',(1060,560),(26,33,37));od=ImageDraw.Draw(out);out.paste(combined.crop((0,48+n*500,1060,48+(n+1)*500)),(0,32));od.text((20,8),f'HGSS source rows {n*500//16} to {(n+1)*500//16}',fill='white');od.text((540,8),'Native grid: offset +1,+1',fill='white');out.save(E/f'grid-comparison-{n+1}.png')
# Before/after is separate from reference alignment: never use the prior layout as truth.
before=Image.open(E/'previous-fe8df8b/native-map.png').convert('RGB');out=Image.new('RGB',(1060,2090),(26,33,37));out.paste(before,(12,32));out.paste(im,(536,32));od=ImageDraw.Draw(out);od.text((12,10),'Previous accepted rock pass',fill='white');od.text((536,10),'Current HGSS grid / dock / EW stair correction',fill='white');out.save(E/'grid-revision-overview.png')
# Named assemblies make a future stair replacement one asset/placement operation.
(S/'stair-placements.json').write_text(json.dumps({'units':'native 16px squares','assemblies':[{'asset':'refined-materials/stairs-ew.png','origin':[9,59],'size':[2,3],'walking_axis':'east-west','tread_source':'Emerald General 0xcf, oriented E/W','blocked_corners':[[10,59],[9,61]],'landings':[[8,60],[11,60]]},{'asset':'refined-materials/stairs-ns.png','origin':[6,87],'size':[3,2],'walking_axis':'north-south','tread_source':'Emerald General 0xaf/0xcf, unchanged','landings':[[7,86],[7,90]]}]},indent=2)+'\n')
print(json.dumps(report))
