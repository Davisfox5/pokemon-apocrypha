"""Apply the reviewed two-glyph B1F corner repair directly to native source.
No layout/tileset repacking. Reproduction: exact ab04d979 engine + preserved
previous-ab04d979 hub source. Refuse changed engine assets or owner edits.
"""
from pathlib import Path
import sys,json,hashlib,struct,subprocess,shutil
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/union-cave-b1f/source';E=S.parent/'evidence';B=S/'previous-ab04d979'
def digest(p):
 b=p.read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if p.suffix=='.pal' else b).hexdigest()
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True),'Preserve current owner edits'
head=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip();assert head=='ab04d9792ea5c36233a3ef2ff0c410b46b6658b6',('Use isolated exact ab04d979 baseline',head)
manifest=json.loads(((B if (B/'generated-files.json').exists() else S)/'generated-files.json').read_text());assert all((G/p).exists() and digest(G/p)==h for p,h in manifest.items())
B.mkdir(exist_ok=True)
for n in ['clean-terrain.png','hgss-pixel-materials.npy','generated-files.json','native-glyph-order.json']:
 if not (B/n).exists():shutil.copy2(S/n,B/n)
D=E/'finish-review';D.mkdir(exist_ok=True)
if not (D/'before-junction-native-map.png').exists():shutil.copy2(E/'native-map.png',D/'before-junction-native-map.png')
t=Tileset(G,'union_cave_b1f','union_cave_b1f');grid=np.fromfile(G/'data/layouts/UnionCaveB1F/map.bin','<u2').reshape(52,36);before=t.map_image(list(map(int,grid.ravel())),36)
a=np.array(Image.open(B/'clean-terrain.png').convert('RGB'));lab=np.load(B/'hgss-pixel-materials.npy').copy();order=json.loads((B/'native-glyph-order.json').read_text());dictionary=order['glyphs'];changes=[]
# Both contaminated native glyphs occur at just one placed quadrant. Their
# unobscured fourth column supplies the continuous same-row face/base ramp.
# Keep the full corner: replacing the lower quadrant with flat floor would cut
# a notch through the face. Extend the verified ramp into only its final 3 cols.
p=G/'data/tilesets/secondary/union_cave_b1f/tiles.png';sheet=Image.open(p);pixels=np.array(sheet).copy()
for tx,ty,q,expected in [(23,16,3,712),(23,17,1,708)]:
 mid=int(grid[ty,tx])&1023;en=t.blocks[0][mid][q];assert en==expected and int(((grid&1023)==mid).sum())==1
 placed=sum((e&1023)==expected for part in t.blocks for block in part for e in block);assert placed==1
 local=expected-512;sx=local%16*8;sy=local//16*8;piece=pixels[sy:sy+8,sx:sx+8].copy();piece[:,5:8]=piece[:,4:5];pixels[sy:sy+8,sx:sx+8]=piece
 bank=en>>12;x=tx*16+q%2*8;y=ty*16+q//2*8;a[y:y+8,x:x+8]=np.array(t.pals[0][bank],np.uint8)[piece]
 dictionary[expected][1]=piece.tobytes().hex();changes.append({'cell':[tx,ty],'metatile':mid,'quadrant':q,'native_glyph':expected,'changed_columns':[5,6,7],'donor':'unobscured same-row column 4; preserve full face and base ramp'})
updated=Image.fromarray(pixels,'P');updated.putpalette(sheet.getpalette());updated.save(p)
Image.fromarray(a).save(S/'clean-terrain.png');np.save(S/'hgss-pixel-materials.npy',lab);(S/'native-glyph-order.json').write_text(json.dumps(order,indent=2)+'\n')
t=Tileset(G,'union_cave_b1f','union_cave_b1f');after=t.map_image(list(map(int,grid.ravel())),36);aa=np.array(after);bb=np.array(before);ys,xs=np.where(np.any(aa!=bb,2));assert xs.min()>=381 and xs.max()<384 and ys.min()>=264 and ys.max()<280;assert aa[264:280,376:384].max(2).min()>=32
report={'base_commit':head,'cause':'raw terrain donor overlapped the original trainer boundary, leaving black/skin pixels in a cliff corner','repair':'two unique native glyphs cleaned within their rock face/base plane using the unobscured same-row ramp; preserve complete corner','native_edits':changes,'changed_native_RGB_pixels':len(xs),'changed_native_bounds':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'map_collision_elevation_warp_definitions_changed':False,'untouched_1f_b2f_and_shared_tilesets':True,'new_glyphs_or_repacking':False};(D/'junction-repair.json').write_text(json.dumps(report,indent=2)+'\n')
after.save(E/'native-map.png')
(S/'generated-files.json').write_text(json.dumps({p:digest(G/p) for p in manifest},indent=2)+'\n')
(S/'native-edit-lock.json').write_text(json.dumps({'reason':'reviewed direct native corner edits follow the packed baseline; never replay the packer over them','baseline_commit':head,'reproduction':'fix_b1f_junction.py on exact isolated baseline + previous-ab04d979 source; preserves owner edits','source':'native glyph pixels are the editing authority'},indent=2)+'\n')
print(json.dumps(report))
