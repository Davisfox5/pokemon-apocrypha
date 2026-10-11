"""Package actual emulator captures; no mockup pixels are used in the review."""
from pathlib import Path
import sys,json,shutil,hashlib
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
       ('route29-grass','Route 29: HGSS jump ledges'),('route30-lower-stairs-east','Route 30: restored lower stairs'),
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
# Explicitly isolated local package; no emulator process is started.
pkg=ROOT/'tools/vendor/gba/Johto-synthesis-preview';pkg.mkdir(exist_ok=True)
source=ROOT/'tools/vendor/gba/johto-synthesis-work/pokeemerald.gba'
assert hashlib.sha256(source.read_bytes()).hexdigest()==r['rom_sha256']
shutil.copyfile(source,pkg/'Apocrypha-Johto-synthesis.gba')
(pkg/'README.txt').write_text('Isolated Johto map review. No owner save is included.\nROM SHA256: '+r['rom_sha256']+'\nSee gba/art/johto-synthesis/README.md for source and validation.\n')
print('Exported six native captures and isolated local ROM package')
