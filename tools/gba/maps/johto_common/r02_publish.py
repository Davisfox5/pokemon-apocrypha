"""Collect final R02 native/Porymap/headless evidence, excluding ROMs and saves."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,shutil,hashlib,subprocess,argparse
ROOT=Path(__file__).resolve().parents[4];P=ROOT/'gba/art/johto-common/rocks/r02-refined'
def main(engine,run,pory,names=None):
 names=names or ['west-approach','step-center','east-landing','north-wall','lower-wall','title-continue']
 assert len(names)==6, 'Choose six gameplay panels'
 rt=json.loads((run/'results.json').read_text());assert all(v['exit_code']==0 for v in rt['phases']);assert rt['rom_sha256']==hashlib.sha256((engine/'pokeemerald.gba').read_bytes()).hexdigest()
 assert np.array_equal(np.array(Image.open(pory/'JohtoRoute36.png').convert('RGB')),np.array(Image.open(P/'review/native-full.png').convert('RGB')))
 (P/'evidence/gameplay').mkdir(exist_ok=True)
 for name in sorted(set(names+['west-approach','step-center','east-landing','upper-row','north-wall','raised-side','lower-wall','cold-reload','title-continue'])):shutil.copy2(run/(name+'.png'),P/'evidence/gameplay'/(name+'.png'))
 shutil.copy2(run/'results.json',P/'evidence/runtime.json');shutil.copy2(pory/'JohtoRoute36.png',P/'evidence/porymap.png')
 for f in ['write','read','menu']:shutil.copy2(run/(f+'.jsonl'),P/'evidence'/(f+'.jsonl'))
 sheet=Image.new('RGB',(1488,740),'#202d37');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
 for i,n in enumerate(names):
  x=i%3*496+8;y=i//3*368+8;d.text((x,y),n,font=font,fill='white');sheet.paste(Image.open(run/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+30))
 sheet.save(P/'review/gameplay.png')
 r=json.loads((P/'evidence/structure.json').read_text());r.update(runtime_tested=True,rom_sha256=rt['rom_sha256'],porymap_native_pixel_errors=0,engine_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=engine,text=True).strip(),production_installed=False,review_checkout_installed=True,desktop_emulator_opened=False)
 (P/'evidence/structure.json').write_text(json.dumps(r,indent=2)+'\n')
 print('Final native/Porymap equality and all runtime phases pass.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('engine',type=Path);p.add_argument('runtime',type=Path);p.add_argument('porymap',type=Path);p.add_argument('--pack',type=Path);p.add_argument('--shots',nargs=6);v=p.parse_args();P=v.pack.resolve() if v.pack else P;main(v.engine,v.runtime,v.porymap,v.shots)
