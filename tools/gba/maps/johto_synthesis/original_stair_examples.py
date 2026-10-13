"""Original Emerald map context for the exact 0xaf/0xcf stair donor."""
from pathlib import Path
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'tools/gba/maps'))
from tiles import Tileset
G = ROOT/'tools/vendor/gba/cherrygrove-synthesis-work'
OUT = ROOT/'gba/art/johto-synthesis/reference-review'
layouts = json.loads((G/'data/layouts/layouts.json').read_text())['layouts']
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
board = Image.new('RGB', (1008, 816), (23,29,36))
draw = ImageDraw.Draw(board)
examples = [
    ('Route112', 'lavaridge', 'Route 112 / mountain entrance', (13,36), (20,41)),
    ('MossdeepCity', 'mossdeep', 'Mossdeep / Space Center terraces', (58,13), (63,18)),
    ('MossdeepCity', 'mossdeep', 'Mossdeep / western beach access', (19,20), (25,24)),
    ('Route115', 'fallarbor', 'Route 115 / southern cliff steps', (6,66), (10,70)),
]
for i, (name, secondary, title, origin, stairs) in enumerate(examples):
    layout = next(v for v in layouts if v['name'] == name+'_Layout')
    grid = np.frombuffer((G/layout['blockdata_filepath']).read_bytes(), '<u2')
    cells = (grid & 1023).reshape(layout['height'], layout['width'])
    sx,sy = stairs
    assert tuple(cells[sy,sx:sx+2]) == (0xaf,0xcf), (name,stairs)
    image = Tileset(G,secondary).map_image(grid,layout['width'])
    x,y = origin
    crop = image.crop((x*16,y*16,x*16+240,y*16+160))
    px,py = 16+(i%2)*496,16+(i//2)*376
    draw.text((px,py), title, font=font, fill='white')
    board.paste(crop.resize((480,320),Image.Resampling.NEAREST),(px,py+32))
draw.text((16,772),'Original Emerald tiles and layouts, decoded directly; shown at 2x. Event sprites omitted.',font=small,fill=(195,205,215))
draw.text((16,794),'No rotation, mirroring, recoloring or replacement rock. All four use the same stair tiles.',font=small,fill=(195,205,215))
board.save(OUT/'original-emerald-stair-examples.png')
print(OUT/'original-emerald-stair-examples.png')
