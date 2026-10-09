#!/usr/bin/env python3
"""Preserve qualified source patch, native review captures and an ignored playable package."""
import argparse,hashlib,io,json,shutil,struct,subprocess,sys,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from claude_routes.preserve import board
ROOT=HERE.parents[3];ART=ROOT/'gba/art/johto-connections';EV=ART/'evidence'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(game,*args):return subprocess.check_output(['git','-C',str(game),*args])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('game',type=Path);p.add_argument('check',type=Path);p.add_argument('--baseline',default='routes-baseline');a=p.parse_args();game=a.game.resolve();check=a.check.resolve();EV.mkdir(parents=True,exist_ok=True)
    assert game!=ROOT/'game' and (game/'.git').exists(),'Use the isolated workbench, never production game/'
    result=json.loads((check/'results.json').read_text())
    assert len(result['phases'])==3 and all(r['exit_code']==0 for r in result['phases'])
    assert result['rom_sha256']==sha(game/'pokeemerald.gba'),'ROM changed after runtime checks'
    original=lambda f:git(game,'show',a.baseline+':'+f)
    checked={}
    for f in ['data/maps/CherrygroveCity/map.json','data/maps/CherrygroveCity/scripts.inc','data/layouts/CherrygroveCity/map.bin','data/layouts/CherrygroveCity/border.bin','include/constants/flags.h','src/data/wild_encounters.json']:
        assert original(f)==(game/f).read_bytes(),('preserved source changed',f)
        checked[f]=sha(game/f)
    for route in [29,30]:
        for file in ['map.bin','border.bin']:
            f=f'data/layouts/CherrygroveRoute{route}Approach/{file}';assert original(f)==(game/f).read_bytes();checked[f]=sha(game/f)
        for file in ['scripts.inc']:
            f=f'data/maps/CherrygroveRoute{route}Approach/{file}';assert original(f)==(game/f).read_bytes();checked[f]=sha(game/f)
        f=f'data/maps/CherrygroveRoute{route}Approach/map.json';old=json.loads(original(f));new=json.loads((game/f).read_text())
        assert all(new[k]==v for k,v in old.items() if k!='connections')
        assert all(c in new['connections'] for c in old['connections'])
        folder=f'data/tilesets/secondary/claude_route{route}'
        oldblocks=original(folder+'/metatiles.bin');newblocks=(game/folder/'metatiles.bin').read_bytes();assert newblocks[:len(oldblocks)]==oldblocks
        oldattrs=original(folder+'/metatile_attributes.bin');assert (game/folder/'metatile_attributes.bin').read_bytes()[:len(oldattrs)]==oldattrs
        oldimg=np.array(Image.open(io.BytesIO(original(folder+'/tiles.png'))));newimg=np.array(Image.open(game/folder/'tiles.png'))
        for tid in set(e&1023 for b in struct.iter_unpack('<8H',oldblocks) for e in b if (e&1023)>=512):
            i=tid-512;y,x=(i//16)*8,(i%16)*8;assert np.array_equal(oldimg[y:y+8,x:x+8],newimg[y:y+8,x:x+8]),(route,tid)
        for i in range(16):
            f=folder+f'/palettes/{i:02}.pal';assert original(f).splitlines()==(game/f).read_bytes().splitlines()
        checked[folder]='All original metatiles, attributes, referenced pixels and palettes identical'
    for file in ['tiles.png','metatiles.bin','metatile_attributes.bin']+[f'palettes/{i:02}.pal' for i in range(16)]:
        f='data/tilesets/primary/cherrygrove/'+file;old=original(f);new=(game/f).read_bytes()
        assert old.splitlines()==new.splitlines() if file.endswith('.pal') else old==new
        checked[f]=sha(game/f)
    (EV/'preservation.json').write_text(json.dumps(checked,indent=2)+'\n')
    # The isolated workbench ignores ROMs, saves, tools and generated build outputs.
    subprocess.run(['git','-C',str(game),'add','-A'],check=True,capture_output=True)
    paths=git(game,'diff','--cached','--name-only',a.baseline).decode().splitlines()
    assert all(not f.endswith(('.gba','.sav','.elf','.exe')) and not f.startswith(('build/','tools/')) for f in paths),paths
    patch=ROOT/'gba/johto-connections.patch';patch.write_bytes(git(game,'diff','--cached','--binary',a.baseline))
    subprocess.run(['git','-C',str(game),'apply','--binary','--reverse','--check',str(patch)],check=True)
    shutil.copyfile(check/'results.json',EV/'runtime.json')
    board(check,[('campus-courtyard','Campus courtyard'),('institute-return','Elm institute entrance'),('annex-and-equipment','Annex and equipment'),('coastal-terrace','Coastal terrace'),('researcher-dialogue','Researcher'),('institute-reception','Institute reception')],EV/'new-bark-in-game.png',cols=3,z=2,title='New Bark: native engine captures, 2x')
    board(check,[('route30-before-crossing','Route 30 north stairs'),('route31-junction','Route 31 junction'),('dark-cave-exterior','Dark Cave entrance'),('dark-cave-room','Bounded cave room'),('violet-gate-interior','Violet east gate'),('violet-arrival','Violet arrival court')],EV/'route31-in-game.png',cols=3,z=2,title='Route to Violet: native engine captures, 2x')
    board(check,[(f'new-bark-seam-{i}',f'Route 29 / New Bark, step {i}') for i in [0,2,4,6,8]]+[('route29-return','Return to Route 29')]+[(f'route31-seam-{i}',f'Route 30 / Route 31, step {i}') for i in [0,2,4,6,8]]+[('route30-return','Return to Route 30')],EV/'seams-in-game.png',cols=4,z=1,title='Walking the connections in the engine')
    board(check,[('save-at-new-bark','Before save'),('cold-reload','Cold flash reload'),('title-continue','Title-screen Continue')],EV/'save-continue.png',cols=3,z=1,title='Ordinary flash save, separate emulator processes')
    package=ROOT/'tools/vendor/gba/Apocrypha-routes-NewBark-preview.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(game/'pokeemerald.gba','Apocrypha-routes-NewBark.gba');z.write(check/'johto.sav','Apocrypha-routes-NewBark.sav')
        z.writestr('README.txt','Apocrypha map/art preview, October 8, 2026.\nKeep the .gba and .sav together. Continue starts in New Bark; New Game starts in Cherrygrove.\nWalk east via Route 29 to New Bark, or north via Routes 30/31 to Violet\'s east entrance.\nThis is an isolated art preview, not Chapter 1 campaign integration. Violet city beyond the entrance, full Dark Cave, trainers and new interior art remain pending.\n')
    record=dict(parent_branch='codex/gba-source-handoff',parent_revision='9195267',upstream='e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7',compiler='Arm GNU 14.2.1 (Debian 15:14.2.rel1-1)',emulator='libmGBA 0.10.5',rom_sha256=sha(game/'pokeemerald.gba'),patch_sha256=sha(patch),package_sha256=sha(package),source_paths=len(paths),runtime_phases=[r['phase'] for r in result['phases']],shared_primary_unchanged=True)
    (EV/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

if __name__=='__main__':main()
