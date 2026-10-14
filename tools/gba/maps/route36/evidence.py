"""Publish completed local checks and native emulator images, excluding ROM/save."""
from pathlib import Path
import sys,json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];E=ROOT/'gba/art/route36/evidence';run=Path(sys.argv[1]);game=Path(sys.argv[2]);pory=Path(sys.argv[3])
r=json.loads((run/'results.json').read_text());assert all(p['exit_code']==0 for p in r['phases']);assert r['rom_sha256']==hashlib.sha256((game/'pokeemerald.gba').read_bytes()).hexdigest()
shutil.copy(run/'results.json',E/'runtime.json');(E/'gameplay').mkdir(exist_ok=True)
for name in ['write','read','menu']:shutil.copy(run/(name+'.jsonl'),E/(name+'.jsonl'))
for p in run.glob('*.png'):shutil.copy(p,E/'gameplay'/p.name)
for name,expected in [('JohtoRoute36',E/'native-overview.png'),('VioletCity',ROOT/'gba/art/violet-city/evidence/native-overview.png')]:
 assert np.array_equal(np.array(Image.open(pory/(name+'.png')).convert('RGB')),np.array(Image.open(expected).convert('RGB'))),name
shutil.copy(pory/'JohtoRoute36.png',E/'porymap-overview.png');shutil.copy(pory/'VioletWestGate.png',E/'gate-interior.png')
(E/'porymap.json').write_text(json.dumps({'version':'6.3.1','maps':['JohtoRoute36','VioletWestGate','VioletCity'],'route_and_city_native_pixel_errors':0,'desktop_editor_opened':False},indent=2)+'\n')
shots=['route36-arrival','east-flowers','wooded-neck','east-stairs','grass-terrace','west-stairs','national-park','west-gate-interior','violet-return']
board=Image.new('RGB',(984,780),(24,30,40));d=ImageDraw.Draw(board)
for i,name in enumerate(shots):
 x=8+(i%3)*328;y=8+(i//3)*260;d.text((x,y),name.replace('-',' ').upper(),fill='white');im=Image.open(run/(name+'.png'));board.paste(im.resize((312,208),Image.Resampling.NEAREST),(x,y+22))
board.save(E/'gameplay-gallery.png')
(E/'build.json').write_text(json.dumps({'rom_sha256':r['rom_sha256'],'toolchain':'Arm GNU 14.2.rel1','local_build':'gmake -j1 generated; gmake -j8 TOOLCHAIN=ARM','runtime_phases':{p['phase']:p['exit_code'] for p in r['phases']},'desktop_emulator_opened':False},indent=2)+'\n')
print('Copied passing runtime evidence; native/Porymap pixel equality verified.')
