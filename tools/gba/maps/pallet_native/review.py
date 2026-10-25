"""Independent native decode, original FRLG material trace, Porymap parity and preservation."""
from pathlib import Path
import sys,json,hashlib,subprocess,csv
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];E=Path(sys.argv[1]);PORY=Path(sys.argv[2]);A=ROOT/'gba/art/pallet-native';S=A/'source';V=A/'evidence'
sys.path.insert(0,str(ROOT/'tools/gba/maps/pallet_rebuild'))
from native import Bank,words,numbered
import reference,materials
# Decode original donor data again; the rejected layout is not the reference.
reference.SOURCE=S;reference.EV=V;reference.ART=A;reference.main(E)
sets=[('ApocPalletTown','palletoutdoor','pallettown'),('ApocPalletRedHouse1F','palletindoor','palletredhouse'),('ApocPalletRedHouse2F','palletbedroomprimary','palletbedroom'),('ApocPalletOakHouse','palletoakprimary','palletoakhouse'),('ApocPalletLab','palletlabprimary','palletlab')]
layouts=json.loads((E/'data/layouts/layouts.json').read_text())['layouts'];results=[]
for name,pr,se in sets:
 l=next(l for l in layouts if l['name']==name+'_Layout');grid=words(E/l['blockdata_filepath']);b=Bank(E,'primary/'+pr,'secondary/'+se,False);im=b.map(grid,l['width'])
 target=Image.open(S/name/'ground-native.png').convert('RGBA');target.alpha_composite(Image.open(S/name/'foreground-native.png').convert('RGBA'))
 assert np.array_equal(np.array(target.convert('RGB')),np.array(im)),name
 assert np.array_equal(np.array(Image.open(PORY/(name+'.png')).convert('RGB')),np.array(im)),(name,'Porymap')
 cells=json.loads((S/name/'cells.json').read_text())
 for c,v in zip(cells,grid):assert (c['collision'],c['elevation'],c['behavior'])==((v>>10)&3,v>>12,b.attr(v&1023)&255),(name,c)
 original=json.loads((S/name/'traversal.json').read_text())
 with (S/name/'frlg-material-traversal.csv').open('w') as f:
  wr=csv.writer(f,lineterminator="\n");wr.writerow(['reference_x','reference_y','material','collision','elevation','behavior','registration'])
  for c in original:wr.writerow([c['x'],c['y'],materials.material(name,c['x'],c['y'],c['metatile']),c['collision'],c['elevation'],c['behavior'],'landmark reference; expanded layout, not one-to-one'])
 ref=json.loads((S/name/'reference.json').read_text());ref['native_offset']=None;ref['expansion']='Owner-requested spatial redesign; original landmarks retained, receiving cells separately authored';(S/name/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
 before=Image.open(ROOT/f'gba/art/pallet-town-rebuild/evidence/{name}-native.png').convert('RGB');frlg=Image.open(S/name/'frlg.png').convert('RGB')
 sheet=Image.new('RGB',(frlg.width+im.width+24,max(frlg.height,im.height)+28),(32,40,48));draw=ImageDraw.Draw(sheet);draw.text((0,4),'FRLG reference',fill='white');draw.text((frlg.width+24,4),'Native GBA spatial revision',fill='white');sheet.paste(frlg,(0,28));sheet.paste(im,(frlg.width+24,28));sheet.save(V/(name+'-reference-comparison.png'))
 sheet=Image.new('RGB',(before.width+im.width+24,max(before.height,im.height)+28),(32,40,48));draw=ImageDraw.Draw(sheet);draw.text((0,4),'Previous native draft',fill='white');draw.text((before.width+24,4),'Native GBA revision',fill='white');sheet.paste(before,(0,28));sheet.paste(im,(before.width+24,28));sheet.save(V/(name+'-before-after.png'))
 results.append(dict(map=name,native_cells=len(grid),reference_cells=len(original),pixel_differences=0,porymap_pixel_differences=0,authored_traversal_mismatches=0,reference_registration='landmarks and material comparison; explicit spatial redesign',visual_acceptance='owner review pending'))
base='2722eaf7601ec02dc5a684fa8cdef9206c0dc377';prior='b02c5c97c070368592fc1b60c0c679aa816d5a79'
for file,key in [('data/maps/map_groups.json',None),('data/layouts/layouts.json','layouts')]:
 old=json.loads(subprocess.check_output(['git','-C',str(E),'show',base+':'+file]));new=json.loads((E/file).read_text())
 if key:assert old[key]==new[key][:len(old[key])]
 else:
  for k,v in old.items():assert (new[k][:len(v)] if isinstance(v,list) else new[k])==v
# No source outside the explicitly reviewed paths may change relative to the rejected Pallet build.
changed=subprocess.check_output(['git','-c','core.safecrlf=false','-C',str(E),'diff','--name-only',prior],text=True).splitlines()
allowed=['data/layouts/ApocPallet','data/layouts/layouts.json','data/maps/ApocPallet','data/tilesets/primary/pallet','data/tilesets/secondary/pallet','graphics/door_anims/pallet_hgss/','src/field_door.c','src/fieldmap.c','src/tileset_anims.c','src/data/object_events/object_event_graphics.h','src/data/object_events/object_event_pic_tables.h','src/data/object_events/object_event_graphics_info.h','src/data/object_events/object_event_graphics_info_pointers.h','src/event_object_movement.c']
assert all(any(p.startswith(a) for a in allowed) for p in changed),[p for p in changed if not any(p.startswith(a) for a in allowed)]
manifest={}
for p in changed+['data/layouts/ApocPalletTown/camera_border.bin']:
 f=E/p
 if f.exists():manifest[p]=hashlib.sha256(f.read_bytes().replace(b'\r\n',b'\n') if f.suffix=='.pal' else f.read_bytes()).hexdigest()
ref=json.loads((S/'reference.json').read_text());ref['maps']=[json.loads((S/n/'reference.json').read_text()) for n,p,t in sets];(S/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
(V/'native-audit.json').write_text(json.dumps(results,indent=2)+'\n');(V/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(V/'preservation.json').write_text(json.dumps(dict(production_base=base,previous_pallet=prior,stable_map_ids=list(range(43,48)),group=80,unrelated_maps_layouts_unchanged=True,changed_paths=changed,old_saves_untouched=True,pallet_coordinate_save_migration=False),indent=2)+'\n')
print('Native/Porymap pixels and all',sum(r['native_cells'] for r in results),'authored cells verified. Original reference separately traced:',sum(r['reference_cells'] for r in results))
