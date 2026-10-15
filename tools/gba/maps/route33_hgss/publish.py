"""Publish existing actual headless proof; does not change engine source."""
from pathlib import Path
import sys,json,hashlib,shutil,subprocess
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];G=Path(sys.argv[1]);R=Path(sys.argv[2]);E=ROOT/'gba/art/route33-hgss/evidence';S=E.parent/'source'
head=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip();rom=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest();results=json.loads((R/'results.json').read_text());assert results['rom_sha256']==rom and all(p['exit_code']==0 for p in results['phases'])
shutil.copyfile(R/'results.json',E/'runtime.json');D=E/'gameplay';D.mkdir(exist_ok=True)
for f in R.glob('*.png'):shutil.copyfile(f,D/f.name)
names=['cave-approach','cave-return','south-cave-interior','western-road','south-ledge','west-ledge','west-forest','northern-cliff','eastern-cliff-corner','tall-grass','southern-woods','apricorn-clearing','title-continue'];a=Image.new('RGB',(980,((len(names)+1)//2)*350),(25,29,34));d=ImageDraw.Draw(a)
for i,n in enumerate(names):
 x=i%2*490;y=i//2*350;d.text((x+5,y+5),n,fill='white');a.paste(Image.open(R/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x+5,y+25))
a.save(E/'gameplay-gallery.png');files=subprocess.check_output(['git','-C',str(G),'diff','--name-only','fc1017f','HEAD'],text=True).splitlines()
allowed={'data/event_scripts.s','data/layouts/layouts.json','data/maps/UnionCaveRoute32Entrance/map.json','data/maps/map_groups.json','data/tilesets/secondary/union_cave/metatile_attributes.bin','src/apocrypha_map_proof.c','src/data/region_map/region_map_sections.json','src/data/tilesets/graphics.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'}
assert all(f in allowed or f.startswith(('data/maps/JohtoRoute33/','data/layouts/JohtoRoute33/','data/tilesets/primary/route33/','data/tilesets/secondary/route33/')) for f in files)
b={'source_commit':head,'source_branch':'codex/route33-hgss','dependency':'fc1017fecad147879de460fcb9727ff63862598b','rom_sha256':rom,'ROM_bytes':(G/'pokeemerald.gba').stat().st_size,'toolchain':'Arm GNU 14.2','Porymap':'6.3.1 offscreen actual project export','Porytiles':'legacy 2.0.0; standalone representative both-bank round-trip with 13 palette capacity, not an engine primary repack','mGBA':'libmGBA 0.10.5 headless','phases':[{k:p[k] for k in ['phase','exit_code']} for p in results['phases']],'observations':sum(len(p['observations']) for p in results['phases']),'CI':'PR draft; no workflow runs returned at publication','owner_visual_acceptance':'pending'};(E/'build.json').write_text(json.dumps(b,indent=2)+'\n')
(E/'preservation.json').write_text(json.dumps({'source_commit':head,'base':b['dependency'],'changed_files':files,'unrelated_map_art_changes':[],'cave_art_and_collision':'unchanged','cave_behavior':'only unique south threshold metatile889 low behavior byte -> MB_SOUTH_ARROW_WARP101','cave_warps':'append ID3, retain original IDs0..2 and all stair pairs','new_map_ID':49,'no_ROM_save_tool_binaries_committed':True},indent=2)+'\n')
print(json.dumps(b,indent=2))
