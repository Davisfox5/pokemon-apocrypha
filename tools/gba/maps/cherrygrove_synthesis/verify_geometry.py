"""Review tight wall footprints and layered eaves in the actual GBA renderer."""
from pathlib import Path
import sys,subprocess,json,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=R/'tools/vendor/gba/cherrygrove-synthesis-work';E=R/'gba/art/cherrygrove-synthesis/evidence';O=Path(sys.argv[1]).resolve();TC=Path(sys.argv[2]).resolve();O.mkdir(parents=True,exist_ok=False)
flags=['-I/opt/homebrew/include','-L/opt/homebrew/lib','-lmgba'];rom_hash=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest()
buildings=json.loads((E/'integration.json').read_text())['maps'][0]['buildings'];cases=[]
for b in buildings:
 x,y,w,h=b['wall_footprint'];cx=x+w//2
 cases += [(b['name']+'-behind',cx,b['y']-1,128,cx,y-1),
           (b['name']+'-side',x-1,y+h//2,16,x-1,y+h//2),
           (b['name']+'-front',x,b['door'][1]+1,64,x,b['door'][1]+1)]
cases += [('dock-path',39,19,0,39,19),('center-entrance',61,10,0,61,10)]
(O/'cases.tsv').write_text(''.join(' '.join(map(str,p))+'\n' for p in cases))
lines=subprocess.check_output([str(TC/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','gMapProofState'};rows=[l.split() for l in lines.splitlines()];(O/'symbols.txt').write_text(''.join(f'{r[2]} {r[0]}\n' for r in rows if len(r)==3 and r[2] in wanted))
subprocess.run(['cc',str(Path(__file__).with_name('geometry_runtime.c')),*flags,'-o',str(O/'runtime')],check=True)
with (O/'results.jsonl').open('w') as f:r=subprocess.run([str(O/'runtime'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O/'cases.tsv'),str(O)],stdout=f)
for p in O.glob('*.ppm'):Image.open(p).save(p.with_suffix('.png'))
board=Image.new('RGB',(720,len(buildings)*184),(26,32,35));d=ImageDraw.Draw(board)
for row,b in enumerate(buildings):
 for col,kind in enumerate(['behind','side','front']):
  name=b['name']+'-'+kind;x=col*240;y=row*184;d.text((x+4,y+4),name,fill='white');board.paste(Image.open(O/(name+'.png')),(x,y+24))
board.save(E/'building-collision-review.png')
focus=Image.new('RGB',(960,708),(26,32,35));draw=ImageDraw.Draw(focus)
for i,(name,title) in enumerate([('center-entrance','Centered Pokemon Center entrance'),('dock-path','Dirt path meets the dock'),('PlayerHouse-behind','Walk behind the roof; walls stay solid'),('GoldHouse-side','Closer access along the side walls')]):
 x=i%2*480;y=i//2*354;draw.text((x+8,y+8),title,fill='white');focus.paste(Image.open(O/(name+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+28))
focus.save(E/'door-dock-collision-review.png')
assert r.returncode==0,'Wall approach failure; inspect results and native captures'
assert hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest()==rom_hash
(E/'building-collision-runtime.json').write_text(json.dumps(dict(rom_sha256=rom_hash,cases=[json.loads(l) for l in (O/'results.jsonl').read_text().splitlines()]),indent=2)+'\n')
print('Verified',len(cases)-2,'wall approaches and two detail views')
