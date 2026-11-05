"""Route 7's change plot (AGENTS.md, "Planning a new town: the change plot", step 7).

    python3 tools/gba/maps/route7/plot.py

One image: HGSS's Route 7 (decoded render, 2x) with its zones, the story's numbered changes,
the cycleway and the walking road as lines, Celadon's native east edge beside it where the map
connection joins, and Saffron's FireRed west gate the gatehouse room leads to. Writes
gba/art/route7/evidence/plan.png.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route7'
CEL = ROOT / 'gba/art/celadon-elements/evidence/v6/engine/native.png'
SAF = ROOT / 'gba/art/saffron-kanto/evidence/native.png'
S = 32                                   # plot pixels per cell
CEL_COLS, CEL_DY = 8, 1                  # Celadon x 56-63; Celadon row = Route 7 row + 1
SAF_COLS, SAF_DY = 10, 11                # Saffron x 0-9; drawn beside the gate, rows shifted 11
GAP = 3                                  # cells between Route 7 and the Saffron strip
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)

ZONES = [   # (x0, y0, x1, y1) in Route 7 cells, label
    ((0, 14, 4, 20), 'Celadon level'),
    ((5, 0, 15, 14), 'Woods'),
    ((15, 2, 24, 14), 'Tall grass'),
    ((21, 0, 28, 6), 'Rock outcrop'),
    ((25, 10, 33, 21), 'Saffron gate'),
    ((12, 20, 17, 25), 'Underground Path'),
    ((12, 23, 21, 28), 'Lawn'),
    ((4, 20, 12, 32), 'Rock outcrop'),
]
CHANGES = [  # (x, y) cell centre, number
    ((1.5, 17.0), 1), ((4.5, 14.2), 2), ((14.0, 16.5), 3), ((26.5, 12.5), 4),
    ((13.5, 21.2), 5), ((19.5, 9.5), 6), ((9.5, 12.7), 7), ((0.5, 27.0), 8),
]
TEXT = [
    '1  Celadon\'s main road comes on at its own width: 3 rows of paving, the 2-lane cycleway (HGSS\'s 4-row road widened to 5)',
    '2  HGSS\'s terrace step down from Celadon (x 4): one Gen 3 rock terrace north and south, the road passing through',
    '3  HGSS\'s dirt road on to the gate, the cycleway beside it as its own painted lane (Celadon plan: "from Route 7, to Saffron")',
    '4  The Saffron gate: HGSS model 247 at 45 deg on its lot, woods tight round it; it takes the road and lane in at its west door',
    '    door -> new gatehouse room (FireRed\'s Route 7 gate room) -> Saffron\'s west gate (8, 27), which opens',
    '5  The Underground Path entrance (model 339), sealed as HGSS has it; its notice board and the locked door sign',
    '6  Tall grass whole-cell; wild table from KANTO_BATTLES R07 (Rattata, Spearow, Growlithe, rare Plusle/Minun/Shinx, lv 16-19)',
    '7  Cherrygrove\'s standard tree in staggered rows; FRLG ledges on HGSS\'s ledges; FRLG rock in HGSS\'s ramp',
    '8  Map connection to Celadon (Route 7 row = Celadon row - 1), drawn by Celadon\'s streamer on both sides of the seam;',
    '    no connection to Saffron: the gate room is the way through, as in FireRed',
    'Out of this pass: the gate guard and his line (Ch5 5.5c), trainers, the Mental Herb and hidden item, the cafe honey, the Underground Path inside',
]

def main():
    hg = Image.open(ART / 'source/hgss/hgss-render.png').convert('RGB')
    W, H = 33, 32
    left, right = CEL_COLS, GAP + SAF_COLS
    img = Image.new('RGB', ((left + W + right) * S, H * S + 30 + len(TEXT) * 20 + 16), (24, 28, 36))
    cel = Image.open(CEL).convert('RGB')
    img.paste(cel.crop(((64 - CEL_COLS) * 16, CEL_DY * 16, 64 * 16, (CEL_DY + H) * 16)).resize((CEL_COLS * S, H * S), Image.NEAREST), (0, 0))
    img.paste(hg.resize((32 * S, 32 * S), Image.NEAREST), (left * S, 0))
    saf = Image.open(SAF).convert('RGB')
    y0 = 8
    img.paste(saf.crop((0, (y0 + SAF_DY) * 16, SAF_COLS * 16, (y0 + SAF_DY + 14) * 16)).resize((SAF_COLS * S, 14 * S), Image.NEAREST),
              ((left + W + GAP) * S, y0 * S))
    d = ImageDraw.Draw(img, 'RGBA')
    X = lambda x: (left + x) * S
    # the added column for the gate's east wall
    d.rectangle([X(32), 0, X(33) - 1, H * S - 1], fill=(40, 44, 56, 255))
    for yy in range(0, H * S, 12):
        d.line([X(32), yy, X(33), yy + 12], fill=(90, 96, 110, 255), width=2)
    d.text((X(32) + 3, 2), '+1', font=SMALL, fill=(230, 230, 230))
    # seams
    d.line([X(0), 0, X(0), H * S], fill=(255, 220, 80, 255), width=3)
    d.text((6, 4), 'Celadon (native, v6)', font=FONT, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    sx = (left + W + GAP) * S
    d.text((sx + 4, y0 * S - 22), "Saffron's west gate (FireRed, accepted)", font=SMALL, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    # zones
    for (x0, y0z, x1, y1), name in ZONES:
        d.rectangle([X(x0), y0z * S, X(x1) - 1, y1 * S - 1], outline=(255, 255, 255, 200), width=2)
        d.text((X(x0) + 4, y0z * S + 3), name, font=SMALL, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    # walking road and cycleway (rows 15-17 paving/dirt, 18-19 lane)
    for xx in range(-CEL_COLS * S, 25 * S, 24):
        d.line([X(0) + xx, 16.5 * S, X(0) + xx + 12, 16.5 * S], fill=(255, 255, 255, 230), width=4)
    d.line([0, 19 * S, X(25.3), 19 * S], fill=(40, 200, 200, 255), width=8)
    d.text((X(6), 19 * S + 6), 'cycleway', font=FONT, fill=(40, 230, 230), stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((X(6), 16.5 * S - 24), 'road', font=FONT, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    # gate room link
    gy = 16.5 * S
    d.line([X(33), gy, sx + 8 * S, (27 - SAF_DY + 0.5) * S], fill=(255, 140, 60, 255), width=4)
    d.text((X(33) + 6, gy - 22), 'gate room', font=SMALL, fill=(255, 180, 120), stroke_width=2, stroke_fill=(0, 0, 0))
    # numbered changes
    for (x, y), n in CHANGES:
        cx, cy = X(x), y * S
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(220, 40, 60, 255), outline=(255, 255, 255, 255), width=2)
        d.text((cx, cy), str(n), font=FONT, fill=(255, 255, 255), anchor='mm')
    ty = H * S + 12
    for t in TEXT:
        d.text((10, ty), t, font=SMALL, fill=(235, 235, 235))
        ty += 20
    out = ART / 'evidence'
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / 'plan.png')
    print(img.size)

if __name__ == '__main__':
    main()
