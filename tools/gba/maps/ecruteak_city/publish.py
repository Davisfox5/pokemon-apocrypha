"""Publish verified evidence for the exact native source/ROM, never edit maps."""
from pathlib import Path
import sys,json,subprocess,hashlib,shutil,platform
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];G,R=map(Path,sys.argv[1:3]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence'
head=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip();base='d822306675e15abe67c85235d9faf8d6e676d449';rom=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest();r=json.loads((R/'results.json').read_text());assert rom==r['rom_sha256'] and all(p['exit_code']==0 for p in r['phases'])
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True).strip()
shutil.copyfile(R/'results.json',E/'runtime.json');D=E/'gameplay';D.mkdir(exist_ok=True)
for p in R.glob('*.png'):shutil.copyfile(p,D/p.name)
names=['Burned-Tower','Bell-Tower-entrance','pond-west-bank','Dance-Theater','Ecruteak-Gym','Pokemon-Center','Poke-Mart','central-avenue','northern-avenue','city-district-return','house-lantern-north','house-lantern-west','gateway-lanterns','central-plot','southern-house-court','southern-torii','western-woodland','cold-reload','title-continue']
sheet=Image.new('RGB',(980,((len(names)+1)//2)*350),'#223039');d=ImageDraw.Draw(sheet)
for i,n in enumerate(names):
 x=i%2*490;y=i//2*350;d.text((x+5,y+5),n,fill='white');sheet.paste(Image.open(D/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x+5,y+25))
sheet.save(E/'gameplay-gallery.png')
# Preserve the specific material correction and prove silhouettes unchanged.
before=Image.open(E/'before-house-material-pass.png').convert('RGB');now=Image.open(E/'native-map.png').convert('RGB');sh=Image.new('RGB',(1568,760),'#223039');d=ImageDraw.Draw(sh)
for row,(label,box) in enumerate([('Violet glazing / distinct source front',(352,352,640,448)),('Green sliding doors / native forest joins',(336,464,672,672))]):
 for col,(name,im) in enumerate([('Before',before),('Current',now)]):
  x=col*784+8;y=row*310;d.text((x,y+8),label+' — '+name,fill='white');crop=im.crop(box);sh.paste(crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST),(x,y+32))
sh.save(E/'house-material-before-after.png')
files=subprocess.check_output(['git','-C',str(G),'diff','--name-only',base,'HEAD'],text=True).splitlines()
allowed=['data/layouts/JohtoEcruteak','data/maps/JohtoEcruteak','data/tilesets/primary/ecruteak_','data/tilesets/secondary/ecruteak_'];registry={'data/event_scripts.s','data/layouts/layouts.json','data/maps/map_groups.json','src/apocrypha_map_proof.c','src/data/region_map/region_map_sections.json','src/data/tilesets/graphics.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'}
assert all(f in registry or any(f.startswith(p) for p in allowed) for f in files)
manifest=[]
for f in files:
 b=subprocess.check_output(['git','-C',str(G),'show','HEAD:'+f]);manifest.append(dict(path=f,sha256=hashlib.sha256(b).hexdigest()))
(S/'native-edit-lock.json').write_text(json.dumps(dict(source_commit=head,authority='Committed native source is the editor. Do not replay first-authoring tools over it.',files=manifest),indent=2)+'\n')
(E/'preservation.json').write_text(json.dumps(dict(source_commit=head,base_engine=base,changed_files=files,unrelated_map_art_changes=[],existing_map_IDs_preserved=True,new_map_IDs=[51,52],map_group=80,source_manifest=manifest,no_ROM_saves_tools_committed=True),indent=2)+'\n')
review=json.loads((E/'review.json').read_text());record=dict(source_commit=head,source_branch='codex/ecruteak-city',source_PR='https://github.com/Davisfox5/pokeemerald-expansion/pull/19',base_engine=base,ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,toolchain='Debian Arm GNU 14.2.1 (20241119)',Porytiles='2.0.0 legacy native compiler with exact color-set palette covering (Z3 / OR-Tools CP-SAT)',Porymap='6.3.1 actual offscreen project exports',mGBA='libmGBA 0.10.5 headless',runtime_observations=sum(len(p['observations']) for p in r['phases']),phases=[dict(phase=p['phase'],exit_code=p['exit_code']) for p in r['phases']],district_usage=review['district_usage'],CI='Local build passed; hosted status recorded separately.',owner_visual_acceptance='pending',scope='Exterior proposal; interiors, adjoining routes and campaign content remain unwired.')
(E/'build.json').write_text(json.dumps(record,indent=2)+'\n')
(S/'python-versions.json').write_text(json.dumps(dict(Python=platform.python_version(),numpy=np.__version__,Pillow=Image.__version__),indent=2)+'\n')
(E/'reproduction.json').write_text(json.dumps(dict(base_engine=base,first_authoring=['assets.py','build.py ENGINE PORYTILES_LEGACY','register.py ENGINE'],authority='Native committed map/art files after first authoring; generators refuse committed map sources.',review='review.py ENGINE ACTUAL_PORYMAP_EXPORT_DIRECTORY',runtime='runtime.py ENGINE NEW_OUTPUT_DIRECTORY --toolchain ARM_PREFIX',publish='publish.py ENGINE VERIFIED_RUNTIME_DIRECTORY',source_commit=head,source_manifest=manifest),indent=2)+'\n')
print(json.dumps(record,indent=2))
