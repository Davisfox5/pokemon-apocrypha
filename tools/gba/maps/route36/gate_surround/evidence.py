"""Publish inspected native map, background runtime and Porymap evidence."""
from pathlib import Path
import sys,json,shutil,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[5];OUT=ROOT/'gba/art/route36/gate-surround';E=OUT/'evidence';game=Path(sys.argv[1]);run=Path(sys.argv[2]);pory=Path(sys.argv[3])
r=json.loads((run/'results.json').read_text());assert all(p['exit_code']==0 for p in r['phases']);assert r['rom_sha256']==hashlib.sha256((game/'pokeemerald.gba').read_bytes()).hexdigest()
for name,expected in [('JohtoRoute36',E/'native-overview.png'),('VioletCity',ROOT/'gba/art/violet-city/evidence/native-overview.png')]:assert np.array_equal(np.array(Image.open(pory/(name+'.png')).convert('RGB')),np.array(Image.open(expected).convert('RGB'))),name
shutil.copy2(pory/'JohtoRoute36.png',E/'porymap-overview.png');shutil.copy2(run/'results.json',E/'runtime.json')
shots=['park-gate-layering','violet-gate-layering','park-rear-trees','park-foreground-trees','violet-rear-trees','violet-foreground-trees','west-gate-interior','violet-return','title-continue']
(E/'gameplay').mkdir(exist_ok=True)
for name in shots:shutil.copy2(run/(name+'.png'),E/'gameplay'/(name+'.png'))
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
board=Image.new('RGB',(992,420),(235,238,237));d=ImageDraw.Draw(board)
for i,name in enumerate(shots[:2]):
 x=12+i*492;d.text((x,14),'National Park gate' if i==0 else 'Violet gate',font=font,fill=(24,36,38));im=Image.open(run/(name+'.png'));board.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,50))
d.text((12,388),'Built ROM / background emulator captures',font=font,fill=(24,36,38));board.save(E/'gameplay-close-ups.png')
full=Image.open(E/'native-overview.png');board=Image.new('RGB',(1200,554),(235,238,237));d=ImageDraw.Draw(board)
for i,(title,box) in enumerate([('National Park gate',(0,112,192,336)),('Violet gate',(1120,208,1312,432)),('Alph gate',(832,288,1024,512))]):
 d.text((i*400+16,16),title,font=font,fill=(24,36,38));board.paste(full.crop(box).resize((384,448),Image.Resampling.NEAREST),(i*400+8,56))
d.text((16,518),'Native map / foreground crowns and solid tree backgrounds',font=font,fill=(24,36,38));board.save(E/'gate-close-ups.png')
full.resize((2624,1024),Image.Resampling.NEAREST).save(E/'native-overview-2x.png')
report=json.loads((E/'structure.json').read_text());report.update(runtime_tested=True,rom_sha256=r['rom_sha256'],runtime_phases={p['phase']:p['exit_code'] for p in r['phases']},porymap_native_pixel_errors=0,desktop_emulator_opened=False)
(E/'structure.json').write_text(json.dumps(report,indent=2)+'\n')
print('Native/Porymap map equality and all background runtime phases verified.')
