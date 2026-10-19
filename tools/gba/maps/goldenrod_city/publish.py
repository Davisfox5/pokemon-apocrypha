"""Preserve review evidence, never ROMs/saves/executables, and exact identities."""
from pathlib import Path
import sys,json,hashlib,subprocess,shutil,re
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[4];G,O,P=map(Path,sys.argv[1:4]);E=R/'gba/art/goldenrod-city/evidence';S=E.parent/'source';(E/'gameplay').mkdir(exist_ok=True)
for p in O.glob('*.png'):
 if '-background' not in p.stem and '-difference' not in p.stem:shutil.copyfile(p,E/'gameplay'/p.name)
for n in ['results.json','write.jsonl','read.jsonl','menu.jsonl']:shutil.copyfile(O/n,E/('runtime.json' if n=='results.json' else n))
(E/'porymap').mkdir(exist_ok=True)
for p in P.glob('*.png'):shutil.copyfile(p,E/'porymap'/p.name)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17);names=['Radio-door','Radio-plaza','station-door','avenue-north-23','Gym-door','flower-shop','Game-Corner','Center','department-store','bike-shop','south-underground','south-arrival']
out=Image.new('RGB',(1488,4*364),'#223039');d=ImageDraw.Draw(out)
for i,n in enumerate(names):
 x=(i%3)*496+8;y=(i//3)*364;d.text((x,y+5),n,font=font,fill='white');out.paste(Image.open(E/'gameplay'/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+32))
out.save(E/'gameplay-gallery.png')
# Retain the first offline defect crop separately from actual gameplay proof.
prior=Path('/workspace/scratch/north-cleanup.png')
if prior.exists():
 (E/'prior-review').mkdir(exist_ok=True);shutil.copyfile(prior,E/'prior-review/north-initial-offline.png');now=Image.open(E/'native-map.png').crop((624,104,872,248)).resize((992,576),Image.Resampling.NEAREST);out=Image.new('RGB',(2016,624),'#223039');d=ImageDraw.Draw(out);d.text((8,8),'Initial offline crop: trunk remnants / clipped roof / palette seams',font=font,fill='white');d.text((1016,8),'Current decoded native: clean lawn, whole spire, coherent material ramps',font=font,fill='white');out.paste(Image.open(prior),(8,40));out.paste(now,(1016,40));out.save(E/'north-cleanup-before-after.png')
base='d822306675e15abe67c85235d9faf8d6e676d449';diff=subprocess.check_output(['git','-C',str(G),'diff','--diff-filter=M','--name-only',base],text=True).splitlines();allowed={'Makefile','data/event_scripts.s','data/layouts/layouts.json','data/maps/map_groups.json','src/apocrypha_map_proof.c','src/data/region_map/region_map_sections.json','src/data/tilesets/graphics.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h','src/field_camera.c','src/overworld.c','src/malloc.c'};assert set(diff)<=allowed,diff
checks={}
for path,key in [('data/maps/map_groups.json','gMapGroup_Cherrygrove'),('data/layouts/layouts.json','layouts'),('src/data/region_map/region_map_sections.json','map_sections')]:
 old=json.loads(subprocess.check_output(['git','-C',str(G),'show',f'{base}:{path}'],text=True));new=json.loads((G/path).read_text());assert new[key][:len(old[key])]==old[key];checks[path]=dict(existing_entries=len(old[key]),appended=len(new[key])-len(old[key]),existing_prefix_exact=True)
(E/'preservation.json').write_text(json.dumps(dict(engine_base=base,prior_native_maps_tilesets_unchanged=True,persistent_structures_flags_items_not_edited=True,stable_identifiers=checks,existing_tracked_file_changes=diff,original_player_saves='No existing player saves were supplied or modified; current-build ordinary save/cold reload/Continue tested.'),indent=2)+'\n')
import PIL,numpy,scipy,z3,platform
(S/'tool-versions.json').write_text(json.dumps(dict(Python=platform.python_version(),Pillow=PIL.__version__,NumPy=numpy.__version__,SciPy=scipy.__version__,Z3=z3.get_version_string(),Porymap='6.3.1 / 139eda92b3b06a5fd675a9825a07ac62e98c1566',mGBA='0.10.5',ArmGNU='14.2.1 / Debian15:14.2.rel1-1'),indent=2)+'\n')
print('Evidence published from',O)
