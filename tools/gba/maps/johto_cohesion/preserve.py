#!/usr/bin/env python3
"""Freeze exact reproducible engine source, checks and visuals; no ROM/save in Git."""
import subprocess,json,hashlib,sys,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'gba/art/johto-cohesion'
def git(g,*args):return subprocess.check_output(['git','-c','core.autocrlf=false','-C',str(g),*args],stderr=subprocess.DEVNULL)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 g,source,checks=map(lambda p:Path(p).resolve(),sys.argv[1:4]);assert g!=ROOT/'game'
 ev=OUT/'evidence';ev.mkdir(exist_ok=True)
 preserved=[]
 paths=['data/layouts/CherrygroveCity/map.bin','data/layouts/CherrygroveCity/border.bin','data/maps/CherrygroveCity/map.json','data/maps/CherrygroveCity/scripts.inc','include/constants/flags.h','src/data/wild_encounters.json','src/data/heal_locations.json']
 paths+=git(g,'ls-tree','-r','--name-only','routes-baseline','data/tilesets/primary/cherrygrove').decode().splitlines()
 for p in paths:
  old=git(g,'show','routes-baseline:'+p);new=(g/p).read_bytes()
  assert old==new or (p.endswith('.pal') and old.splitlines()==new.splitlines()),p
  preserved.append(p)
 for route in [29,30]:
  p=f'data/maps/CherrygroveRoute{route}Approach/scripts.inc';assert git(g,'show','routes-baseline:'+p)==(g/p).read_bytes();preserved.append(p)
  p=f'data/maps/CherrygroveRoute{route}Approach/map.json';old=json.loads(git(g,'show','routes-baseline:'+p));new=json.loads((g/p).read_text());assert all(new[k]==v for k,v in old.items() if k!='connections');preserved.append(p)
 git(g,'add','data','include/regions.h','src/data/tilesets','src/data/region_map','src/apocrypha_map_proof.c')
 files=git(g,'diff','--cached','--name-only','routes-baseline').decode().splitlines();manifest={}
 for p in files:
  a,b=(g/p).read_bytes(),(source/p).read_bytes()
  assert a==b or (p.endswith('.pal') and a.splitlines()==b.splitlines()),('reproduction',p)
  manifest[p]=digest(g/p)
 patch=ROOT/'gba/johto-cohesion.patch';patch.write_bytes(git(g,'diff','--cached','--binary','routes-baseline'))
 subprocess.run(['git','-C',str(g),'apply','--reverse','--check',str(patch)],check=True)
 (ev/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (ev/'preservation.json').write_text(json.dumps(dict(preserved=preserved,baseline=git(g,'rev-parse','routes-baseline').decode().strip(),source_files=len(files),patch_sha256=digest(patch),fresh_generator_match=True,reverse_apply_check=True),indent=2)+'\n')
 results=json.loads((checks/'results.json').read_text());assert all(p['exit_code']==0 for p in results['phases']);assert results['rom_sha256']==digest(g/'pokeemerald.gba')
 shutil.copy2(checks/'results.json',ev/'runtime.json')
 for p in checks.glob('*.png'):shutil.copy2(p,ev/p.name)
 for key,names in {
  'new-bark-native':['enlarged-institute','southern-home-1','southern-home-2','southern-home-3','southern-home-4','southern-housing-street'],
  'routes-native':['route29-native-grass','route29-gate','route30-mr-pokemon','route30-berry-house','route30-grass-walk','route30-stair-landing','route31-bridge','dark-cave-exterior','violet-arrival'],
  'connections-native':['cherrygrove-route29-seam','new-bark-seam','cherrygrove-route30-seam','route31-seam'],
 }.items():
  cols=3 if len(names)>4 else len(names);rows=(len(names)+cols-1)//cols;board=Image.new('RGB',(cols*240,rows*184),(35,37,40));d=ImageDraw.Draw(board)
  for i,name in enumerate(names):
   x,y=i%cols*240,i//cols*184;d.text((x+4,y+5),name,fill='white');board.paste(Image.open(checks/(name+'.png')).convert('RGB'),(x,y+24))
  board.save(ev/(key+'.png'))
 comparisons=OUT/'comparisons';comparisons.mkdir(exist_ok=True)
 for name,old in [('route29','claude-routes/route29'),('route30','claude-routes/route30'),('route31','johto-polish/route31'),('new_bark','johto-polish/new_bark'),('violet_entrance','johto-polish/violet_entrance')]:
  a=Image.open(ROOT/'gba/art'/f'{old}-overview.png').convert('RGB');b=Image.open(OUT/(name+'-overview.png')).convert('RGB');board=Image.new('RGB',(a.width+b.width+24,max(a.height,b.height)+32),(34,37,40));board.paste(a,(0,32));board.paste(b,(a.width+24,32));d=ImageDraw.Draw(board);d.text((4,8),'PREVIOUS / REJECTED',fill='white');d.text((a.width+28,8),'CORRECTION PROPOSAL',fill='white');board.save(comparisons/(name+'.png'))
 print(json.dumps({'source_files':len(files),'patch':str(patch),'source_match':True}))
if __name__=='__main__':main()
