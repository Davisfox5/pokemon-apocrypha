#!/usr/bin/env python3
"""Deterministic GBA format import of imagegen-authored Johto samples.

No illustration is drawn here: alpha becomes index zero, generated pixels are
sampled onto the target grid, colors become RGB555, then 8x8 4bpp tile data.
"""
import json, struct, hashlib
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'gba/art/johto-v1'
OUT = ART / 'native'
OUT.mkdir(exist_ok=True)
ASSETS = [('house', 'house-final.png', 80, 64, 8),
          ('center', 'center.png', 64, 64, 10),
          ('tree', 'tree-alpha.png', 32, 48, 6)]
manifest = {'format': 'GBA 4bpp, 8x8 row-major tiles, RGB555 palettes; index 0 transparent',
            'alpha_threshold': 224, 'resampling': 'nearest', 'assets': []}
for name, file, w, h, bank in ASSETS:
    src = ART / 'generated' / file
    im = Image.open(src)
    assert im.mode == 'RGBA', (name, im.mode)
    mask = im.getchannel('A').point(lambda a: 255 if a >= 224 else 0)
    bounds = mask.getbbox()
    rgb = im.convert('RGB').crop(bounds).resize((w, h), Image.Resampling.NEAREST)
    alpha = mask.crop(bounds).resize((w, h), Image.Resampling.NEAREST)
    # Palette selection sees only opaque pixels, so transparent RGB noise cannot
    # spend a color slot. No dithering: a GBA object needs stable pixel clusters.
    visible = [c for c, a in zip(rgb.getdata(), alpha.getdata()) if a]
    strip = Image.new('RGB', (len(visible), 1)); strip.putdata(visible)
    q = strip.quantize(colors=15, method=Image.Quantize.MEDIANCUT,
                       dither=Image.Dither.NONE)
    rawpal = q.getpalette()
    colors = [(0, 0, 0)]
    for i in sorted(set(q.getdata())):
        c = tuple(round(rawpal[i*3+j]*31/255)*255//31 for j in range(3))
        if c not in colors[1:]: colors.append(c)
    ncolors = len(colors)-1
    colors += [(0, 0, 0)]*(16-len(colors))
    indexed = Image.new('P', (w, h)); indexed.putpalette([v for c in colors for v in c] + [0]*720)
    data = [0 if not a else min(range(1, ncolors+1),
            key=lambda i: sum((c[j]-colors[i][j])**2 for j in range(3)))
            for c, a in zip(rgb.getdata(), alpha.getdata())]
    indexed.putdata(data); indexed.info['transparency'] = 0
    indexed.save(OUT / (name+'.png'), transparency=0)
    (OUT / (name+'.pal')).write_text('JASC-PAL\n0100\n16\n' +
            '\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
    (OUT / (name+'.gbapal')).write_bytes(struct.pack('<16H',
            *[sum(round(c[j]*31/255) << (j*5) for j in range(3)) for c in colors]))
    tiles = [bytes(indexed.crop((x,y,x+8,y+8)).getdata())
             for y in range(0,h,8) for x in range(0,w,8)]
    packed = bytes(t[i] | t[i+1]<<4 for t in tiles for i in range(0,64,2))
    assert bytes(v for b in packed for v in (b&15,b>>4)) == b''.join(tiles)
    (OUT / (name+'.4bpp')).write_bytes(packed)
    manifest['assets'].append(dict(name=name, source=str(src.relative_to(ROOT)),
        source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(), source_bounds=bounds,
        width=w, height=h, palette_bank=bank, opaque_colors=len(set(data)-{0}),
        tile_count=len(tiles), unique_tiles=len(set(tiles)), packed_bytes=len(packed)))

(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
# Inspection board uses the actual indexed PNGs, not the large generator output.
board = Image.new('RGB', (1000, 620), '#15262b'); draw = ImageDraw.Draw(board)
draw.text((24,18), 'JOHTO / CHERRYGROVE - NATIVE GBA ART SAMPLES', fill='#fff2d4')
draw.text((24,42), 'Retrieved HGSS reference', fill='#b4cdca')
draw.text((310,42), 'Imported 4bpp asset (nearest-neighbor enlargement)', fill='#b4cdca')
draw.text((810,42), 'Native size', fill='#b4cdca')
for row, a in enumerate(manifest['assets']):
    n=a['name'];y=75+row*175
    refname={'house':'house','center':'center','tree':'trees'}[n]
    ref=Image.open(ART/'references'/f'{refname}-hgss-reference.png').convert('RGB')
    ref.thumbnail((220,140),Image.Resampling.NEAREST);board.paste(ref,(24,y))
    sprite=Image.open(OUT/(n+'.png')).convert('RGBA')
    board.paste(sprite.resize((a['width']*2,a['height']*2),Image.Resampling.NEAREST),(330,y),sprite.resize((a['width']*2,a['height']*2),Image.Resampling.NEAREST))
    board.paste(sprite,(820,y+20),sprite)
    draw.text((520,y+30), n.upper(), fill='#fff2d4')
    draw.text((520,y+55), f"{a['width']} x {a['height']} px | {a['opaque_colors']} colors", fill='#b4cdca')
    draw.text((520,y+75), f"{a['unique_tiles']} unique 8x8 tiles", fill='#b4cdca')
draw.text((24,602), 'Design proposal. Reference: Pokemon HGSS / Game Freak, Nintendo, Creatures. Native import: Apocrypha.',fill='#b4cdca')
board.save(ART/'comparison.png')
print(json.dumps(manifest,indent=2))
