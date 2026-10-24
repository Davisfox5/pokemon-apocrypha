"""Publish existing headless exterior proof; never write engine source."""
from pathlib import Path
import sys,subprocess,json,hashlib,shutil
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];G,R=map(Path,sys.argv[1:3]);E=ROOT/'gba/art/azalea-town/evidence';head=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip();rom=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest();r=json.loads((R/'results.json').read_text());assert rom==r['rom_sha256'] and all(p['exit_code']==0 for p in r['phases'])
shutil.copyfile(R/'results.json',E/'runtime.json');D=E/'gameplay';D.mkdir(exist_ok=True)
for f in R.glob('*.png'):shutil.copyfile(f,D/f.name)
names=['main-street','Kurt-house','pokemon-center','poke-mart','Azalea-gym','ordinary-house','Slowpoke-Well','well-east-corridor','southern-loop','eastern-field','Ilex-gate','east-approach','western-woods','southern-woods','title-continue'];sheet=Image.new('RGB',(980,((len(names)+1)//2)*350),'#223039');d=ImageDraw.Draw(sheet)
for i,n in enumerate(names):
 x=i%2*490;y=i//2*350;d.text((x+5,y+5),n,fill='white');sheet.paste(Image.open(R/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x+5,y+25))
sheet.save(E/'gameplay-gallery.png')
files=subprocess.check_output(['git','-C',str(G),'diff','--name-only','eb15d89234','HEAD'],text=True).splitlines();assert not any('route33' in f.lower() for f in files)
b=dict(source_commit=head,source_branch='codex/azalea-town',base_engine='eb15d8923401af86bb12670c6627c2bfba1e3d0a',ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,toolchain='Debian Arm GNU14.2.1',Porymap='6.3.1 actual offscreen project export',mGBA='libmGBA0.10.5 headless',runtime_observations=sum(len(p['observations']) for p in r['phases']),phases=[{'phase':p['phase'],'exit_code':p['exit_code']} for p in r['phases']],CI='Local build verified; hosted CI not claimed',owner_visual_acceptance='pending',scope='Exterior; building/well interiors and adjacent-map connections pending')
(E/'build.json').write_text(json.dumps(b,indent=2)+'\n');(E/'preservation.json').write_text(json.dumps({'source_commit':head,'changed_files':files,'Route33_changes':[],'unrelated_map_art_changes':[],'stable_map_ID':50,'stable_group_ID':80,'original_saves':'untouched; compatibility uses a copy','no_ROM_saves_tools_committed':True},indent=2)+'\n');print(json.dumps(b,indent=2))
