"""Render original map references and an uninstalled native-palette proposal."""
from pathlib import Path
import copy, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'tools/gba/maps'))
from tiles import Tileset

DONOR = ROOT/'tools/vendor/gba/cherrygrove-synthesis-work'
GAME = ROOT/'tools/vendor/gba/johto-synthesis-work'
OUT = ROOT/'gba/art/johto-synthesis/reference-review'
OUT.mkdir(exist_ok=True)
HGSS = ROOT/'gba/art/hgss-connections/references/route31-hgss.png'
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)

def layout(game, name):
    layouts = json.loads((game/'data/layouts/layouts.json').read_text())['layouts']
    l = next(v for v in layouts if v['name'] == name+'_Layout')
    grid = np.frombuffer((game/l['blockdata_filepath']).read_bytes(), '<u2')
    return l, grid

def render(game, name, secondary, primary='general', recolor=False):
    l, grid = layout(game, name)
    tiles = Tileset(game, secondary, primary)
    if recolor:
        # Change palette data only, in memory. Tile indices and maps are untouched.
        colors = tiles.pals[1][8]
        tiles.pals[1][8] = [warm.get(tuple(c), c) for c in colors]
    return tiles.map_image(grid, l['width'])

original = [(98,65,82), (131,90,90), (156,115,115), (189,148,139), (222,180,164)]
target = [(104,72,56), (136,96,64), (160,120,80), (184,136,104), (208,160,104)]
warm = dict(zip(original, target))
reference_pixels = np.asarray(Image.open(HGSS).convert('RGB'))[155:188,820:930]
for color in target:
    assert np.any(np.all(reference_pixels == color, axis=-1)), color

route112 = render(DONOR, 'Route112', 'lavaridge')
mossdeep = render(DONOR, 'MossdeepCity', 'mossdeep')
route112.save(OUT/'emerald-route112-original.png')
mossdeep.save(OUT/'emerald-mossdeep-original.png')

# Confirm these are the exact native stair IDs, rather than similar artwork.
_, grid = layout(DONOR, 'Route112')
grid = (grid & 1023).reshape(60,40)
assert np.array_equal(grid[41:44,20:22], [[0xaf,0xcf]]*3)
_, grid = layout(DONOR, 'MossdeepCity')
grid = (grid & 1023).reshape(40,80)
assert np.array_equal(grid[18:20,63:66], [[0xaf,0xcf,0xcf]]*2)

board = Image.new('RGB', (1008,456), (23,29,36))
d = ImageDraw.Draw(board)
for col, (title, source, box) in enumerate([
    ('Emerald Route 112 / same stair tiles', route112, (224,576,464,752)),
    ('Mossdeep City / exact donor location', mossdeep, (928,208,1168,384)),
]):
    x = 16+col*496
    d.text((x,16), title, font=font, fill='white')
    board.paste(source.crop(box).resize((480,352), Image.Resampling.NEAREST), (x,48))
d.text((16,416), 'Original Emerald map layouts and tiles, decoded at native resolution. Crops shown at 2x.', font=small, fill=(195,205,215))
board.save(OUT/'emerald-stairs-context.png')

def connected(recolor):
    upper = render(GAME, 'JohtoRoute31', 'route31', 'cherrygrove', recolor)
    lower = render(GAME, 'CherrygroveRoute30Approach', 'claude_route30', 'cherrygrove', recolor)
    result = Image.new('RGB', (upper.width, upper.height+64))
    result.paste(upper, (0,0))
    result.paste(lower.crop((0,0,lower.width,64)), (28*16,upper.height))
    return upper, result

plain, connected_plain = connected(False)
colored, connected_colored = connected(True)
colored.save(OUT/'route31-hgss-palette-preview.png')
before, after = np.asarray(plain), np.asarray(colored)
changed = np.any(before != after, axis=-1)
allowed = np.zeros(changed.shape, dtype=bool)
for a,b in warm.items():
    mask = np.all(before == a, axis=-1)
    allowed |= mask
    assert np.all(after[changed & mask] == b)
assert not np.any(changed & ~allowed)

board = Image.new('RGB', (1008,848), (23,29,36))
d = ImageDraw.Draw(board)
for col, (title, source) in enumerate([
    ('Current / original Emerald colors', connected_plain),
    ('Proposal / HGSS rock colors', connected_colored),
]):
    x = 16+col*496
    d.text((x,16), title, font=font, fill='white')
    for row, box in enumerate([(448,192,688,352),(464,352,704,512)]):
        board.paste(source.crop(box).resize((480,320), Image.Resampling.NEAREST), (x,48+row*336))
    for i,c in enumerate(original if col==0 else target):
        d.rectangle((x+i*54,738,x+i*54+45,764), fill=c)
d.text((16,786), 'Palette preview only: original tile shapes, gray stairs, layout and ground remain unchanged.', font=small, fill=(195,205,215))
d.text((16,812), 'Five warm colors sampled from the original HGSS Route 31 cliff. Not installed in the game.', font=small, fill=(195,205,215))
board.save(OUT/'emerald-rock-hgss-palette-comparison.png')

report = dict(
    installed=False, source_game_art='Nintendo / Game Freak / Creatures',
    hgss_source='https://archives.bulbagarden.net/media/upload/d/d8/Johto_Route_31_HGSS.png',
    hgss_sha256=hashlib.sha256(HGSS.read_bytes()).hexdigest(),
    palette_sample_rectangle=[820,155,930,188],
    palette_map=[dict(emerald=a, hgss=b) for a,b in warm.items()],
    native_stair_metatiles=['0x0af','0x0cf'],
    verified_placements=['Route112 x20..21 y41..43','MossdeepCity x63..65 y18..19'],
    proposal_changed_pixels=int(changed.sum()), other_pixels_unchanged=True,
    note='Static native-map decode and in-memory palette preview; no ROM build or emulator capture.',
)
(OUT/'provenance.json').write_text(json.dumps(report, indent=2)+'\n')
print('Saved original Emerald references and isolated HGSS palette preview:', OUT)
