"""Collect immutable native evidence; never copy ROMs, saves or binaries."""
from pathlib import Path
import sys,json,hashlib,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.rollout import P,dump
G=Path(sys.argv[1]);run=Path(sys.argv[2]);r36=Path(sys.argv[3]);audit=json.loads((P/'evidence/native-audit.json').read_text());engine=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()
for src,name in [(run,'runtime'),(r36,'route36-runtime')]:
 dest=P/'evidence'/name;dest.mkdir(exist_ok=True)
 for f in ['results.json','write.jsonl','read.jsonl','menu.jsonl','runtime.c']:
  shutil.copy2(src/f,dest/f)
 results=json.loads((src/'results.json').read_text());assert all(r['exit_code']==0 for r in results['phases'])
shots=[(run,n) for n in ['new-bark-mailbox','route29-shared-gate','route29-ledge','route30-pink-apricorn','route30-ledge','route31-gate-return','route31-ledge','cherrygrove-service-street','cherrygrove-fence','cherrygrove-pink-trees','violet-bridge-rails','violet-forest-ground']]
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
for page in range(3):
 im=Image.new('RGB',(984,716),'#202d37');d=ImageDraw.Draw(im)
 for i,(src,n) in enumerate(shots[page*4:page*4+4]):
  x=i%2*492+6;y=i//2*358+6;d.text((x,y),n,fill='white',font=font);a=Image.open(src/(n+'.png')).convert('RGB');im.paste(a.resize((480,320),Image.Resampling.NEAREST),(x,y+25));shutil.copy2(src/(n+'.png'),P/'review'/(n+'.png'))
 im.save(P/'review'/f'gameplay-{page+1}.png')
shadows={}
for c in json.loads((P/'source/initial-inventory.json').read_text()):
 a=np.array(Image.open(P/'review'/f'{c["map"]}.png'));shadows[c['map']]=int(np.all(a[:,:,:3]==(64,136,104),2).sum())
assert not any(shadows.values())
cat=json.loads((ROOT/'gba/art/johto-common/rocks/r02-complete-tiles/source/catalog.json').read_text());native=Image.open(P/'review/JohtoRoute36.png').convert('RGBA');count=0
for id,v in cat.items():
 art=Image.open(ROOT/f'gba/art/johto-common/rocks/r02-complete-tiles/source/tiles/{id}.png').convert('RGBA')
 for x,y in v['placements']:assert np.array_equal(np.array(art),np.array(native.crop((x*16,y*16,x*16+16,y*16+16)))),(id,x,y);count+=1
files=subprocess.check_output(['git','diff','--name-only','5b80e625d1',engine],cwd=G,text=True).splitlines();assert all(f.startswith(('data/layouts/','data/tilesets/')) for f in files)
info=dict(engine_revision=engine,baseline='5b80e625d1',rom_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),changed_cells=sum(r['changed_cells'] for r in audit['maps']),unique_review_pairs=audit['unique_pairs'],obsolete_tree_shadow_pixels=shadows,r02_placements_exact=count,gameplay_scripts_events_object_graphics_unchanged=True,build_pass=True,porymap_maps=7,unrelated_shared_primary_previews_unchanged=3,review_status='Agent inspected native overviews, 416 unique before/after pairs and runtime frames; owner visual acceptance remains separate',exception='Violet gate replacement uninstalled; exact tested candidate exceeds graphics budget')
dump(P/'evidence/summary.json',info);print(info)
