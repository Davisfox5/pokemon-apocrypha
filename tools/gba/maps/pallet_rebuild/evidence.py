"""Publish real emulator captures/results, excluding ROMs, saves and executables."""
from pathlib import Path
import hashlib,json,shutil,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];A=ROOT/'gba/art/pallet-town-rebuild';V=A/'evidence';R=Path(sys.argv[1])
results=json.loads((R/'results.json').read_text());assert len(results)==19 and all(r['exit_code']==0 for r in results)
(V/'runtime').mkdir(exist_ok=True)
for p in R.iterdir():
    if p.suffix in ['.png','.jsonl','.json']:shutil.copyfile(p,V/'runtime'/p.name)
shutil.copyfile(R/'runtime.c',A/'source/runtime-fixture.c')
shots=['tour-43-town-center','tour-43-red-home-enter','tour-43-red-bedroom','tour-43-oak-home','tour-43-oak-dialogue','tour-43-lab-enter',
       'tour-43-blue-dialogue','tour-43-red-memorial','tour-43-shore-approach','water-43-surf-shore','water-43-hgss-water-next-phase','menu-47-title-continue']
im=Image.new('RGB',(1440,1376),'#202830');draw=ImageDraw.Draw(im)
for i,n in enumerate(shots):
    src=Image.open(R/(n+'.png'));x,y=(i%3)*480,(i//3)*344
    draw.text((x+5,y+5),n,fill='white');im.paste(src.resize((480,320),Image.Resampling.NEAREST),(x,y+24))
im.save(V/'gameplay-review.png')
for door in range(3):
    sheet=Image.new('RGB',(1440,180),'#202830');draw=ImageDraw.Draw(sheet)
    for i,t in enumerate([0,2,4,6,8,10]):
        src=Image.open(R/f'doors-43-door-{door}-frame-{t:02}.png');sheet.paste(src,(i*240,20));draw.text((i*240+5,3),f'Frame {t*2}',fill='white')
    sheet.save(V/f'door-{door}-gameplay.png')
identity=json.loads((R/'input-identity.json').read_text());preserved=json.loads((V/'preservation.json').read_text())
assert identity['source_commit']==preserved['engine_commit'] and identity['rom_sha256']==preserved['rom_sha256']
assert hashlib.sha256((R/'runtime.c').read_bytes()).hexdigest()==identity['fixture_sha256']
print('Published all 19 final-source runtime phases and their exact input identity.')
