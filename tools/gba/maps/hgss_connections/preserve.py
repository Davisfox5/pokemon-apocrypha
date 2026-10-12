#!/usr/bin/env python3
"""Record preservation checks, source patch, native capture boards and playable review ZIP."""
import argparse,hashlib,json,subprocess,zipfile,shutil,struct,io
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];ART=ROOT/'gba/art/hgss-connections'
def git(g,*args):return subprocess.check_output(['git','-C',str(g),*args])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('game',type=Path);p.add_argument('checks',type=Path);a=p.parse_args();g=a.game.resolve();c=a.checks.resolve();assert g!=ROOT/'game';ev=ART/'evidence';ev.mkdir(parents=True,exist_ok=True)
    result=json.loads((c/'results.json').read_text());assert all(x['exit_code']==0 for x in result['phases']) and len(result['phases'])==3;assert result['rom_sha256']==sha(g/'pokeemerald.gba')
    original=lambda path:git(g,'show','routes-baseline:'+path)
    preserved=[]
    for path in ['data/layouts/CherrygroveCity/map.bin','data/layouts/CherrygroveCity/border.bin','data/maps/CherrygroveCity/map.json','data/maps/CherrygroveCity/scripts.inc','include/constants/flags.h','src/data/wild_encounters.json']:
        assert original(path)==(g/path).read_bytes();preserved.append(path)
    for route in [29,30]:
        for file in ['map.bin','border.bin']:
            path=f'data/layouts/CherrygroveRoute{route}Approach/{file}';assert original(path)==(g/path).read_bytes();preserved.append(path)
        path=f'data/maps/CherrygroveRoute{route}Approach/scripts.inc';assert original(path)==(g/path).read_bytes()
        path=f'data/maps/CherrygroveRoute{route}Approach/map.json';old=json.loads(original(path));new=json.loads((g/path).read_text());assert all(new[k]==v for k,v in old.items() if k!='connections');assert all(item in new['connections'] for item in old['connections'])
        folder=f'data/tilesets/secondary/claude_route{route}';ob=original(folder+'/metatiles.bin');assert (g/folder/'metatiles.bin').read_bytes().startswith(ob)
        assert (g/folder/'metatile_attributes.bin').read_bytes().startswith(original(folder+'/metatile_attributes.bin'))
        oi=np.asarray(Image.open(io.BytesIO(original(folder+'/tiles.png'))));ni=np.asarray(Image.open(g/folder/'tiles.png'))
        for tid in {e&1023 for bs in struct.iter_unpack('<8H',ob) for e in bs if e&1023>=512}:
            n=tid-512;y,x=n//16*8,n%16*8;assert np.array_equal(oi[y:y+8,x:x+8],ni[y:y+8,x:x+8])
        for bank in range(16):assert original(folder+f'/palettes/{bank:02}.pal').splitlines()==(g/folder/f'palettes/{bank:02}.pal').read_bytes().splitlines()
    for path in git(g,'ls-tree','-r','--name-only','routes-baseline','data/tilesets/primary/cherrygrove').decode().splitlines():assert original(path).splitlines()==(g/path).read_bytes().splitlines()
    git(g,'add','data','include/regions.h','src/data/tilesets','src/data/region_map','data/event_scripts.s','src/apocrypha_map_proof.c')
    patch=ROOT/'gba/hgss-connections.patch';patch.write_bytes(git(g,'diff','--cached','--binary','routes-baseline'));subprocess.run(['git','-C',str(g),'apply','--reverse','--check',str(patch)],check=True)
    (ev/'preservation.json').write_text(json.dumps(dict(preserved=preserved,route_art_and_events='original entries and referenced pixels unchanged',primary='unchanged',source_patch_sha256=sha(patch),reverse_apply_check=True),indent=2)+'\n')
    shutil.copy2(c/'results.json',ev/'runtime.json')
    for label,names in {'new-bark-in-game':['new-bark-seam','new-bark-square','institute-return','new-bark-east'],'route31-in-game':['route31-seam','route31-east','route31-bridge','dark-cave-exterior'],'save-continue':['save-at-new-bark','continue-menu','title-continue']}.items():
        ims=[Image.open(c/(n+'.png')).convert('RGB') for n in names];board=Image.new('RGB',(240*len(ims),160))
        for i,im in enumerate(ims):board.paste(im,(240*i,0))
        board.save(ev/(label+'.png'))
    package=Path('/workspace/library-files/Apocrypha-HGSS-connections-preview.zip');package.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(g/'pokeemerald.gba','Apocrypha-HGSS.gba');z.write(c/'johto.sav','Apocrypha-HGSS.sav')
        z.writestr('README.txt','Load the matching ROM and save, then select CONTINUE. Start in New Bark. West leads to Claude\'s Route 29 and Cherrygrove; north from Cherrygrove follows Route 30 and Route 31 to the Violet entrance. Full Violet City and full Dark Cave remain unfinished.\n')
    (ev/'package.json').write_text(json.dumps(dict(path=str(package),sha256=sha(package),rom_sha256=sha(g/'pokeemerald.gba')),indent=2)+'\n');print(package)
if __name__=='__main__':main()
