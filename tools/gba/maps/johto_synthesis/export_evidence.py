"""Package actual emulator captures; no mockup pixels are used in the review."""
from pathlib import Path
import sys,json,shutil,hashlib,subprocess,io
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];EV=ROOT/'gba/art/johto-synthesis/evidence'
proof=Path(sys.argv[1]).resolve()
r=json.loads((proof/'results.json').read_text());assert len(r['phases'])==3 and all(p['exit_code']==0 for p in r['phases'])
extra=json.loads((EV/'extra-runtime.json').read_text())
assert extra['rom_sha256']==r['rom_sha256'] and extra['passed'], 'Boundary proof must match the final ROM'
patch=ROOT/'gba/johto-synthesis.patch';repro=json.loads((EV/'reproduction.json').read_text())
assert repro['patch_sha256']==hashlib.sha256(patch.read_bytes()).hexdigest()
shutil.copyfile(proof/'results.json',EV/'runtime.json')
shots=[('route31-cave','Dark Cave: arch and stepped rock'),('route31-bridge','Route 31: bridge and rock divide'),
       ('route29-grass','Route 29: native Emerald ledges and grass'),('route30-lower-stairs-east','Route 30: restored lower stairs'),
       ('route30-plateau-bridge','Route 30: plateau crossing'),('new-bark-windmills','New Bark: windmills on grass')]
board=Image.new('RGB',(1008,1132),(23,29,36));d=ImageDraw.Draw(board)
try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
except OSError:font=ImageFont.load_default()
for i,(name,label) in enumerate(shots):
 im=Image.open(proof/(name+'.png')).convert('RGB');assert im.size==(240,160)
 x=16+(i%2)*496;y=16+(i//2)*368
 d.text((x,y),label,font=font,fill=(235,240,244));board.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,y+28))
 shutil.copyfile(proof/(name+'.png'),EV/(name+'-runtime.png'))
d.text((16,1110),'Native GBA captures | Background libmGBA | ROM '+r['rom_sha256'][:16],font=font,fill=(180,190,200))
board.save(EV/'runtime-review.png')
# Same native camera positions on the previous and current ROMs.
baseline='1016f4a6feb3f9e743f05fd559385c63a02be41e'
comparison=Image.new('RGB',(1008,1148),(23,29,36));d=ImageDraw.Draw(comparison)
for row,(name,label) in enumerate([('route29-grass','Grass and ledges'),
                                  ('route31-cave','Dark Cave rock foot'),
                                  ('route30-plateau-bridge','Rock and woodland crossing')]):
    previous=subprocess.check_output(['git','show',baseline+':gba/art/johto-synthesis/evidence/'+name+'-runtime.png'],cwd=ROOT)
    for col,im in enumerate([Image.open(io.BytesIO(previous)),Image.open(proof/(name+'.png'))]):
        x=16+col*496;y=16+row*368
        d.text((x,y),label+(' / Before' if col==0 else ' / Revised'),font=font,fill=(235,240,244))
        comparison.paste(im.convert('RGB').resize((480,320),Image.Resampling.NEAREST),(x,y+28))
d.text((16,1120),'Background GBA captures; identical camera positions. Current ROM '+r['rom_sha256'][:12],font=font,fill=(180,190,200))
comparison.save(EV/'terrain-review.png')
previous=subprocess.check_output(['git','show','6ce0635d04d023073a93fcfab1301ec8cf307981:gba/art/johto-synthesis/evidence/route31-cave-runtime.png'],cwd=ROOT)
current=Image.open(proof/'route31-cave.png').convert('RGB')
crowns=Image.open(proof/'route31-crowns.png').convert('RGB')
cave=Image.new('RGB',(1008,772),(23,29,36));d=ImageDraw.Draw(cave)
views=[('Dark Cave / Before',Image.open(io.BytesIO(previous))),
       ('Dark Cave / Revised',current),('Rock behind the tree crowns',crowns)]
for i,(label,im) in enumerate(views):
 x=16+i%2*496;y=16+i//2*368
 d.text((x,y),label,font=font,fill=(235,240,244))
 cave.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,y+28))
d.text((512,384),'Shaded threshold and freestanding sign',font=font,fill=(235,240,244))
cave.paste(current.crop((88,24,168,104)).resize((320,320),Image.Resampling.NEAREST),(592,412))
d.text((16,750),'Actual background GBA captures | ROM '+r['rom_sha256'][:16],font=font,fill=(180,190,200))
cave.save(EV/'cave-review.png');shutil.copyfile(proof/'route31-crowns.png',EV/'route31-crowns-runtime.png')
shutil.copyfile(proof/'route31-cave-sign.png',EV/'route31-cave-sign-runtime.png')
# Current divider correction, using the same native camera for before/after.
previous=subprocess.check_output(['git','show','5d50fbbd53fff3b535be9a10a07b7eb49ff1c005:gba/art/johto-synthesis/evidence/route31-bridge-runtime.png'],cwd=ROOT)
divider=Image.new('RGB',(1008,772),(23,29,36));d=ImageDraw.Draw(divider)
views=[('Pond crossing / Before',Image.open(io.BytesIO(previous))),
       ('Pond crossing / Revised',Image.open(proof/'route31-bridge.png')),
       ('Pond above the path',Image.open(proof/'route31-pond.png')),
       ('Southern wall and complete trees',Image.open(proof/'route31-divider-south.png'))]
for i,(label,im) in enumerate(views):
 x=16+i%2*496;y=16+i//2*368;d.text((x,y),label,font=font,fill=(235,240,244))
 divider.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,y+28))
d.text((16,750),'Actual background GBA captures | ROM '+r['rom_sha256'][:16],font=font,fill=(180,190,200))
divider.save(EV/'divider-review.png')
for name in ('route31-divider','route31-pond','route31-divider-south'):
 shutil.copyfile(proof/(name+'.png'),EV/(name+'-runtime.png'))
# Explicitly isolated local package; no emulator process is started.
pkg=ROOT/'tools/vendor/gba/Johto-synthesis-preview';pkg.mkdir(exist_ok=True)
source=ROOT/'tools/vendor/gba/johto-synthesis-work/pokeemerald.gba'
assert hashlib.sha256(source.read_bytes()).hexdigest()==r['rom_sha256']
shutil.copyfile(source,pkg/'Apocrypha-Johto-synthesis.gba')
(pkg/'README.txt').write_text('Isolated Johto map review. No owner save is included.\nROM SHA256: '+r['rom_sha256']+'\nSee gba/art/johto-synthesis/README.md for source and validation.\n')
print('Exported six native captures and isolated local ROM package')
