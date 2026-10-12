#!/usr/bin/env python3
"""Preserve reproducible native source and qualified captures, excluding ROM/save."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'gba/art/johto-native-refinement'
def git(g,*args):return subprocess.check_output(['git','-c','core.autocrlf=false','-C',str(g),*args])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    game,repro,checks=map(lambda v:Path(v).resolve(),sys.argv[1:4])
    assert game!=ROOT/'game'
    preserved=['data/layouts/CherrygroveCity/map.bin','data/layouts/CherrygroveCity/border.bin',
               'data/maps/CherrygroveCity/map.json','data/maps/CherrygroveCity/scripts.inc',
               'include/constants/flags.h','src/data/wild_encounters.json','src/data/heal_locations.json']
    preserved+=git(game,'ls-tree','-r','--name-only','routes-baseline','data/tilesets/primary/cherrygrove').decode().splitlines()
    for p in preserved:
        old=git(game,'show','routes-baseline:'+p);new=(game/p).read_bytes()
        assert old==new or (p.endswith('.pal') and old.splitlines()==new.splitlines()),p
    for route in (29,30):
        p=f'data/maps/CherrygroveRoute{route}Approach/scripts.inc'
        assert git(game,'show','routes-baseline:'+p)==(game/p).read_bytes();preserved.append(p)
        p=f'data/maps/CherrygroveRoute{route}Approach/map.json'
        old=json.loads(git(game,'show','routes-baseline:'+p));new=json.loads((game/p).read_text())
        assert all(new[k]==v for k,v in old.items() if k!='connections');preserved.append(p)
    git(game,'add','data','include/regions.h','src/data/tilesets','src/data/region_map','src/apocrypha_map_proof.c')
    files=git(game,'diff','--cached','--name-only','routes-baseline').decode().splitlines()
    manifest={}
    for p in files:
        assert (game/p).read_bytes()==(repro/p).read_bytes(),('fresh reproduction differs',p)
        manifest[p]=sha(game/p)
    patch=ROOT/'gba/johto-native-refinement.patch'
    patch.write_bytes(git(game,'diff','--cached','--binary','routes-baseline'))
    git(game,'apply','--reverse','--check',str(patch))
    ev=OUT/'evidence';ev.mkdir(parents=True,exist_ok=True)
    (ev/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ev/'preservation.json').write_text(json.dumps(dict(preserved=preserved,source_files=len(files),
        baseline=git(game,'rev-parse','routes-baseline').decode().strip(),patch_sha256=sha(patch),
        upstream='e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7',
        fresh_generator_match=True,reverse_apply_check=True,porymap_gui_roundtrip=False),indent=2)+'\n')
    results=json.loads((checks/'results.json').read_text())
    assert all(v['exit_code']==0 for v in results['phases'])
    assert results['rom_sha256']==sha(game/'pokeemerald.gba')
    shutil.copy2(checks/'results.json',ev/'runtime.json')
    for p in checks.glob('*.png'):shutil.copy2(p,ev/p.name)
    names=['enlarged-institute','southern-housing-street','route30-grass-walk',
           'route29-gate','route30-mr-pokemon','dark-cave-exterior']
    board=Image.new('RGB',(720,368),(35,37,40));d=ImageDraw.Draw(board)
    for i,name in enumerate(names):
        x,y=i%3*240,i//3*184;d.text((x+4,y+5),name,fill='white')
        board.paste(Image.open(checks/(name+'.png')).convert('RGB'),(x,y+24))
    board.save(ev/'native-gameplay.png')
    print(json.dumps(dict(source_files=len(files),patch=str(patch),fresh_match=True)))
if __name__=='__main__':main()
