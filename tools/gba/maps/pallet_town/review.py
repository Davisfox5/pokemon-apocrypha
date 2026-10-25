#!/usr/bin/env python3
"""Independent source/native/editor audit and readable review sheets.
Material names are authored from the numbered original sheets, never inferred from collision.
"""
from pathlib import Path
import json,csv,hashlib,sys,subprocess
from PIL import Image,ImageDraw,ImageChops
from native import Bank,words,numbered
ROOT=Path(__file__).resolve().parents[4];E=Path(sys.argv[1]).resolve();ART=ROOT/'gba/art/pallet-town';EV=ART/'evidence'
SPECS=[('ApocPalletTown','general_frlg','pallet_town_frlg','palletoutdoor','pallettown'),('ApocPalletRedHouse1F','building_frlg','generic_building_1_frlg','palletindoor','palletredhouse'),('ApocPalletRedHouse2F','building_frlg','generic_building_1_frlg','palletindoor','palletbedroom'),('ApocPalletOakHouse','building_frlg','generic_building_2_frlg','palletindoor','palletoakhouse'),('ApocPalletLab','building_frlg','lab_frlg','palletlabprimary','palletlab')]
# Named material/structure catalog, visually reviewed against the original native metatile sheet.
TOWN={}
def tag(label,ids):
 for m in ids:TOWN[m]=label
tag('tree_canopy_trunk_root',[0xe,0xf,0x14,0x15,0x16,0x17,0x1c,0x1d,0x1e,0x1f,0x24,0x25,0x26,0x27])
tag('lawn',[8,9,0x11,0x285,0x286,0x28c,0x296,0x297,0x2be])
tag('lawn_contact_shadow',[0x288,0x28e,0x28f,0x290,0x294,0x295,0x29e,0x29f,0x2a6,0x2a7,0x2ae,0x2af,0x2c6,0x2c7,0x2cd])
tag('shore_lip_and_water',[0x123,0x12a,0x12c,0x2d1,0x2d2]);tag('water',[0x12b])
tag('flowers_on_lawn',[4]);tag('sign',[2,3,0x2a5,0x2ad]);tag('picket_fence',[0x284,0x287])
tag('home_roof_eave',[0x281,0x282,0x283,0x289,0x28a,0x28b,0x291,0x292,0x293])
tag('home_wall_window',[0x298,0x299,0x29a,0x29b,0x29c,0x2a0,0x2a1,0x2a2,0x2a4]);tag('home_entrance',[0x2a3])
tag('lab_roof_rim_chimney',[0x2a8,0x2a9,0x2ab,0x2b0,0x2b1,0x2b3,0x2b4,0x2b5,0x2b6,0x2b8,0x2b9,0x2bb,0x2bc,0x2bd])
tag('lab_wall_window',[0x2bf,0x2c0,0x2c1,0x2c2,0x2c3,0x2c4,0x2c5,0x2c8,0x2c9,0x2cb,0x2cc,0x2ce,0x2d0,0x2d8]);tag('lab_entrance',[0x2ac])
def material(n,x,y,mid):
 if n=='ApocPalletTown':return TOWN[mid]
 if mid==8:return 'void'
 # Explicit footprints measured on each original numbered reference, including mixed edge cells.
 features=[]
 if n in ('ApocPalletRedHouse1F','ApocPalletOakHouse'):
  features=[('wall_cap_face',0,0,12,1),('kitchen_sink_cabinet',1 if n.endswith('1F') else 0,1,3 if n.endswith('1F') else 2,2),('telephone',4 if n.endswith('1F') else 3,1,4 if n.endswith('1F') else 3,2),('television',6 if n.endswith('1F') else 5,1,6 if n.endswith('1F') else 5,2),('table_chairs_rug',4,3,9,6),('exit_rug',3,8,5,8)]
  if n.endswith('1F'):features += [('stairs_treads_landing',10,1,12,3),('plant',1,6,1,7),('plant',12,6,12,7)]
  else:features += [('bookshelf',11,1,12,2),('plant',0,7,0,8),('plant',12,7,12,8),('family_wall_map',9,1,9,1)]
 elif n=='ApocPalletRedHouse2F':
  features=[('wall_cap_face',1,0,11,1),('personal_computer_desk',1,1,2,2),('chair',3,1,3,2),('bookshelf',4,1,5,2),('stairs_treads_landing',8,1,10,3),('wall_notice',11,1,11,1),('bed',2,4,3,6),('rug',4,4,8,7),('television_console',6,4,6,5)]
 elif n=='ApocPalletLab':
  features=[('wall_cap_face',0,0,12,1),('research_machines',0,1,3,2),('desk',4,1,5,2),('wall_notices',6,0,7,1),('display',8,0,8,1),('bookshelf',9,1,12,2),('bookshelf',0,8,4,9),('bookshelf',8,8,12,9),('reference_books',0,3,0,4),('research_machine',1,3,2,5),('research_table',8,4,10,5),('plant',0,11,0,12),('plant',12,11,12,12),('exit_rug',5,12,7,12)]
 label='laboratory_tile_floor' if n=='ApocPalletLab' else 'wood_floor'
 for tag,x0,y0,x1,y1 in features:
  if x0<=x<=x1 and y0<=y<=y1:label=tag
 return label
ls=json.loads((E/'data/layouts/layouts.json').read_text())['layouts'];audit=[];manifest={};allids={}
for n,pr,se,np,ns in SPECS:
 ref=json.loads((ART/f'source/{n}-reference.json').read_text());old=ref['layout'];l=next(l for l in ls if l['name']==n+'_Layout');s=Bank(E,'primary/'+pr,'secondary/'+se);b=Bank(E,'primary/'+np,'secondary/'+ns,False)
 grid=words(E/l['blockdata_filepath']);original=words(E/old['blockdata_filepath']);assert len(grid)==len(original) and all((a&0xfc00)==(b&0xfc00) for a,b in zip(grid,original))
 before=s.map(original,l['width']);after=b.map(grid,l['width']);expected=Image.open(ART/('source/hgss/town-assembled.png' if n=='ApocPalletTown' else f'source/hgss/{n}/assembled.png')).convert('RGB')
 import numpy as np
 assert np.array_equal(np.array(after)>>3,np.array(expected)>>3),(n,'native differs from converted HGSS source')
 editor=Image.open(EV/f'porymap/{n}.png').convert('RGB');assert not ImageChops.difference(after,editor).getbbox()
 for file in ['map.bin','border.bin']:
  p=E/'data/layouts'/n/file;manifest[str(p.relative_to(E))]=hashlib.sha256(p.read_bytes()).hexdigest()
 for name,image in [('reference',before),('native',after)]:image.save(EV/f'{n}-{name}.png')
 numbered(after).save(EV/f'{n}-grid.png')
 rows=[];trav=[]
 m=json.loads((E/f'data/maps/{n}/map.json').read_text());warps={(w['x'],w['y']):w for w in m['warp_events']};actors={(a['x'],a['y']):a['graphics_id'] for a in m['object_events']}
 for i,v in enumerate(grid):
  x,y=i%l['width'],i//l['width'];mid=original[i]&1023;native_mid=v&1023;a=s.attr(mid);ba=b.attr(native_mid);assert a&511==ba&255
  rows.append(dict(x=x,y=y,reference_metatile=f'{mid:03x}',native_metatile=f'{native_mid:03x}',reference_material_structure=material(n,x,y,mid),native_ground_material=('water_and_shore' if mid in (0x123,0x12a,0x12b,0x12c,0x2d1,0x2d2) else 'shared_lawn') if n=='ApocPalletTown' else 'HGSS_wood_floor_wall_or_void',native_source_layers='source/hgss/town-{ground,foreground}.png' if n=='ApocPalletTown' else f'source/hgss/{n}/{{ground,foreground}}.png',background_quadrants=' '.join(f'{t:04x}' for t in b.entries(native_mid)[:4]),foreground_quadrants=' '.join(f'{t:04x}' for t in b.entries(native_mid)[4:]),layer_type=ba>>12,hgss_converted_pixels_equal=True,adaptation='HGSS artwork fitted to FRLG footprint; house roof overhang at row 3' if n=='ApocPalletTown' and y==3 and (5<=x<=9 or 14<=x<=18) else '',occluded_or_uncertain=False))
  trav.append(dict(x=x,y=y,collision=(v>>10)&3,elevation=v>>12,behavior=ba&255,foot='water' if (ba&255) in (0x15,0x10) else 'blocked' if v&0xc00 else 'open',actor=actors.get((x,y)),warp=warps.get((x,y))))
 for suffix,records in [('materials.csv',rows)]:
  with (ART/f'source/{n}-{suffix}').open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(records)
 (ART/f'source/{n}-traversal.json').write_text(json.dumps(trav,indent=1)+'\n')
 compare=Image.new('RGB',(before.width*6+30,before.height*3+36),'#202830');d=ImageDraw.Draw(compare);d.text((8,10),'ORIGINAL FRLG: decoded native data',fill='white');d.text((before.width*3+24,10),'APOCRYPHA: HGSS models in native GBA tiles',fill='white');compare.paste(before.resize((before.width*3,before.height*3),Image.Resampling.NEAREST),(0,36));compare.paste(after.resize((after.width*3,after.height*3),Image.Resampling.NEAREST),(before.width*3+30,36));compare.save(EV/f'{n}-comparison.png')
 audit.append(dict(map=n,cells=len(grid),source='HGSS models/textures and accepted shared lawn/trees',reference='FRLG layout',collision_elevation_equal=True,hgss_converted_rgb555_pixel_match=True,porymap_pixel_match=True,behavior_equal=True,uncertain_cells=0,adaptations='HGSS models/palettes, house roof overhang, coherent shared lawn, independent fresh canon events; route sockets disconnected'))
# Stable append-only allocation, original map/layout preservation and used art budgets.
base='2722eaf7601ec02dc5a684fa8cdef9206c0dc377'
for file,key in [('data/maps/map_groups.json',None),('data/layouts/layouts.json','layouts')]:
 old=json.loads(subprocess.check_output(['git','-C',str(E),'show',base+':'+file]));new=json.loads((E/file).read_text())
 if key:assert new[key][:len(old[key])]==old[key]
 else:
  for k,v in old.items():assert (new[k][:len(v)] if isinstance(v,list) else new[k])==v
# Confirm no edits to any pre-existing donor/shared asset/map file.
changed=subprocess.check_output(['git','-C',str(E),'diff','--name-only',base],text=True).splitlines()
allowed={'data/layouts/layouts.json','data/maps/map_groups.json','data/event_scripts.s','src/apocrypha_map_proof.c','src/data/tilesets/graphics.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h','src/field_door.c'}
allowed_new=('data/layouts/ApocPallet','data/maps/ApocPallet','data/tilesets/primary/pallet','data/tilesets/secondary/pallet','graphics/door_anims/pallet_hgss/')
assert all(p in allowed or p.startswith(allowed_new) or p=='porymap.project.cfg' for p in changed),set(changed)-allowed
(EV/'native-audit.json').write_text(json.dumps(audit,indent=2)+'\n');(EV/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Verified',sum(a['cells'] for a in audit),'HGSS converted native squares, original collision/elevation/behavior, and actual Porymap pixel parity.')
