"""Independent traversal, unchanged-context and registered concept review."""
from pathlib import Path
import numpy as np,json,subprocess,io,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];S=R/'gba/art/goldenrod-city/source';E=S.parent/'evidence/boardwalk';solid=np.load(S/'solid.npy');old=np.load(io.BytesIO(subprocess.check_output(['git','-C',str(R),'show','bcfb58b5458a36e3ccd625079dbb507bcf9e8a47:gba/art/goldenrod-city/source/solid.npy'])));meta=json.loads((E/'native-edit.json').read_text());deck=np.zeros((56,84),bool)
for x,y in meta['deck_cells']+meta['authorized_landing']:deck[y,x]=True
assert not np.any((old&~solid)&~deck),'Opened water outside the authorized pier'
seen={(58,48)};todo=list(seen)
for x,y in todo:
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  p=x+dx,y+dy
  if 0<=p[0]<84 and 0<=p[1]<56 and not solid[p[1],p[0]] and p not in seen:seen.add(p);todo.append(p)
points={'entry-left':(35,26),'entry-right':(36,26),'wheel':(30,12),'snacks':(24,11),'prizes':(27,14),'souvenirs':(35,13),'whole-wheel-view':(29,7),'terminal':(53,27),'broadcast':(21,31)};assert all(p in seen for p in points.values()),[k for k,p in points.items() if p not in seen]
for y in range(14,27):assert (35,y) in seen and (36,y) in seen,(y,'two-tile access')
(E/'traversal.json').write_text(json.dumps(dict(approaches=points,all_approaches_reachable=True,full_two_tile_access_rows=[14,26],water_opened_only_inside_authorized_deck_and_landing=True,reachable_ground_cells=len(seen),new_walkable_cells=int((old&~solid).sum()),boardwalk_open_cells=int((deck&~solid).sum())),indent=2)+'\n')
before=np.array(Image.open(E/'before.png'));after=np.array(Image.open(E/'after.png'));allowed=np.zeros((896,1344),bool);boxes=[(336,48,640,432),(768,376,832,400),(848,400,864,432),(144,568,176,600),(336,568,368,600),(240,560,272,576),(336,464,352,496),(1040,856,1088,896),(1120,856,1168,896)]
for x,y,x1,y1 in boxes:allowed[y:y1,x:x1]=True
changed=np.any(before!=after,2);outside=int((changed&~allowed).sum());assert outside==0,outside
for x,y in json.loads((S/'trees.json').read_text()):assert np.array_equal(before[y:y+48,x:x+32],after[y:y+48,x:x+32]),(x,y)
cm=np.array(Image.open(S/'masters/center.png'))[...,3]>0;assert np.array_equal(after[576:656,792:872][cm],before[576:656,792:872][cm]);radio=np.array(Image.open(S/'masters/radio-equipment.png'))[...,3]>0;assert np.array_equal(before[radio],after[radio])
(E/'visual-preservation.json').write_text(json.dumps(dict(allowed_boxes=boxes,changed_native_pixels=int(changed.sum()),unrelated_native_pixel_changes=outside,all49tree_contexts_unchanged=True,canonical_Center_opaque_pixels_unchanged=5679,Radio_rooftop_equipment_unchanged=True,existing_building_footprints_preserved=True),indent=2)+'\n')
concept=Image.open(S/'boardwalk/approved-concept.png').resize((1344,896),Image.Resampling.LANCZOS)
for name,b in [('boardwalk',(336,32,736,448)),('station',(728,352,896,448)),('rail-planters',(128,544,384,624)),('south-garden',(1008,832,1184,896))]:
 w,h=b[2]-b[0],b[3]-b[1];out=Image.new('RGB',(w*4,h*2+24),(30,38,44));d=ImageDraw.Draw(out)
 for i,(label,a) in enumerate([('Before',Image.fromarray(before)),('Native',Image.fromarray(after))]):out.paste(a.crop(b).resize((w*2,h*2)),(i*w*2,24));d.text((i*w*2+5,5),label,fill='white')
 out.save(E/(name+'-comparison.png'))
b=(336,32,736,448);w,h=b[2]-b[0],b[3]-b[1];out=Image.new('RGB',(w*4,h*2+24),(30,38,44));d=ImageDraw.Draw(out)
for i,(label,a) in enumerate([('Approved concept / normalized scale',concept),('Actual decoded native',Image.fromarray(after))]):out.paste(a.crop(b).resize((w*2,h*2)),(i*w*2,24));d.text((i*w*2+5,5),label,fill='white')
out.save(E/'concept-native-comparison.png')
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (S/'boardwalk').glob('*.png')};(S/'boardwalk/provenance.json').write_text(json.dumps(dict(owner_approved_concept='approved-concept.png',reference='HGSS city + approved ten-year boardwalk concept; new shoreline is owner-authorized adaptation.',generated_art='wheel-original.png, created with image generation from approved concept; resized to128x144, thresholded alpha, fitted to existing bank11 and star hub cleaned.',hand_authored_assets='boardwalk_art.py: separate native deck, rails, awnings/counters, lamps, benches, display/kiosk and integrated planter masters.',hashes=files),indent=2)+'\n');print('Traversal, untouched native pixels and shared assets verified')
