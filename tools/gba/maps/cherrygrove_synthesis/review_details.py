"""Capture targeted native views and assemble unretouched review boards."""
from pathlib import Path
import sys,subprocess,json,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];OUT=Path(sys.argv[1]).resolve();EV=R/'gba/art/cherrygrove-synthesis/evidence';G=R/'tools/vendor/gba/cherrygrove-synthesis-work';D=OUT/'details';D.mkdir(exist_ok=True)
subprocess.run(['cc',str(Path(__file__).with_name('detail_views.c')),'-I/opt/homebrew/include','-L/opt/homebrew/lib','-lmgba','-o',str(OUT/'detail-views')],check=True)
subprocess.run([str(OUT/'detail-views'),str(G/'pokeemerald.gba'),str(OUT/'water/symbols.txt'),str(D)],check=True)
board=Image.new('RGB',(960,696),(28,34,37));draw=ImageDraw.Draw(board)
for i,(name,label) in enumerate([('pond','Pond bank'),('shore','Ocean shore'),('southeast','Southeast grove'),('gable','Complete gable and side walls')]):
 im=Image.open(D/('detail-'+name+'.ppm')).convert('RGB');im.save(EV/('detail-'+name+'.png'));x=i%2*480;y=i//2*348;draw.text((x+8,y+7),label,fill='white');board.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,y+28))
board.save(EV/'detail-review.png')
board=Image.new('RGB',(960,348),(28,34,37));draw=ImageDraw.Draw(board)
for row,door in enumerate([0,4]):
 draw.text((8,row*174+2),'Player entrance' if row==0 else 'Center entrance',fill='white')
 for col,frame in enumerate([0,8,16,24]):board.paste(Image.open(OUT/f'door-{door}-{frame:03}.png'),(col*240,row*174+14))
board.save(EV/'door-runtime-review.png')
(EV/'detail-captures.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),source='libmGBA runtime.c screenshot; no pixel edits',coordinates=[[68,8],[36,16],[66,26],[54,20]]),indent=2)+'\n')
