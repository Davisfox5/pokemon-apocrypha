"""Route 7's review sheet: HGSS's decoded render beside the native decode (world.py's, the route's
cells), both at 2x with a coordinate-labelled cell grid (AGENTS.md: coordinate-labelled review
sheets, readable source/native comparisons).

    python3 tools/gba/maps/route7/review.py

Writes gba/art/route7/evidence/review.png and review-seam.png (Celadon's east edge and the route's
west end, native, the seam marked).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
sys.path.insert(0, str(HERE))
import compose as R            # noqa: E402
import world as WD             # noqa: E402

S = 2
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)

def grid(img, x0, label=True):
    d = ImageDraw.Draw(img, 'RGBA')
    for x in range(R.MW + 1):
        d.line([x0 + x * 16 * S, 18, x0 + x * 16 * S, 18 + R.MH * 16 * S], fill=(255, 255, 255, 60))
    for y in range(R.MH + 1):
        d.line([x0, 18 + y * 16 * S, x0 + R.MW * 16 * S, 18 + y * 16 * S], fill=(255, 255, 255, 60))
    for x in range(0, R.MW, 2):
        d.text((x0 + x * 16 * S + 2, 4), str(x), font=FONT, fill=(255, 255, 255))
    for y in range(0, R.MH, 2):
        d.text((x0 + 2, 18 + y * 16 * S + 2), str(y), font=FONT, fill=(255, 255, 0), stroke_width=1, stroke_fill=(0, 0, 0))

def main():
    hg = Image.open(R.SRC / 'hgss/hgss-render.png').convert('RGB')
    native = Image.open(WD.OUT / 'native.png').convert('RGB')
    route = native.crop((WD.CW * 16, R.OY * 16, (WD.CW + R.MW) * 16, (R.OY + R.MH) * 16))
    w, h = R.MW * 16 * S, R.MH * 16 * S
    sheet = Image.new('RGB', (2 * w + 24, h + 40), (24, 28, 36))
    sheet.paste(hg.resize((32 * 16 * S, h), Image.NEAREST), (0, 18))
    sheet.paste(route.resize((w, h), Image.NEAREST), (w + 24, 18))
    grid(sheet, 0); grid(sheet, w + 24)
    d = ImageDraw.Draw(sheet)
    d.text((4, h + 22), "HGSS Route 7 (decoded render, pret/pokeheartgold)", font=FONT, fill=(230, 230, 230))
    d.text((w + 28, h + 22), 'Native decode (world.py), as the engine streams it', font=FONT, fill=(230, 230, 230))
    sheet.save(R.EV / 'review.png')
    seam = native.crop(((WD.CW - 10) * 16, (R.OY + 10) * 16, (WD.CW + 12) * 16, (R.OY + 26) * 16)).resize((22 * 16 * 3, 16 * 16 * 3), Image.NEAREST)
    d = ImageDraw.Draw(seam)
    d.line([10 * 48, 0, 10 * 48, seam.height], fill=(255, 220, 60), width=2)
    seam.save(R.EV / 'review-seam.png')
    print(sheet.size, seam.size)

if __name__ == '__main__':
    main()
