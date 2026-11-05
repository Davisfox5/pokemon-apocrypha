"""Route 7 as built, end to end, for the owner: the engine's native decode (world.py) from
Celadon's east edge across the connection and along the route to the gate, the gate room
(gate_room.py's decode) and Saffron's west gate it leads to (Saffron's accepted native image).

    python3 tools/gba/maps/route7/route_map.py

Writes gba/art/route7/evidence/route-map.png (2x).
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
import interiors as IN         # noqa: E402

FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
S, CEL = 2, 10                                    # scale; Celadon columns shown

def main():
    native = Image.open(WD.OUT / 'native.png').convert('RGB')
    strip = native.crop(((WD.CW - CEL) * 16, R.OY * 16, (WD.CW + R.MW) * 16, (R.OY + R.MH) * 16))
    room = Image.fromarray(IN.decode(dict(np.load(R.SRC / 'interiors/gate.npz'))))
    saffron = Image.open(R.ROOT / 'gba/art/saffron-kanto/evidence/native.png').convert('RGB').crop((0, 18 * 16, 14 * 16, 36 * 16))
    W = (strip.width + 40 + max(room.width, saffron.width)) * S + 160
    H = strip.height * S + 40
    sheet = Image.new('RGB', (W, H), (24, 28, 36))
    sheet.paste(strip.resize((strip.width * S, strip.height * S), Image.NEAREST), (0, 40))
    x = strip.width * S + 40 * S
    sheet.paste(room.resize((room.width * S, room.height * S), Image.NEAREST), (x, 80))
    ys = 80 + room.height * S + 60
    sheet.paste(saffron.resize((saffron.width * S, saffron.height * S), Image.NEAREST), (x, ys))
    d = ImageDraw.Draw(sheet)
    sx = CEL * 16 * S
    d.line([sx, 40, sx, H], fill=(255, 220, 60), width=3)
    d.text((8, 10), 'Celadon (east edge)', font=FONT, fill=(255, 255, 255))
    d.text((sx + 8, 10), 'Route 7 (33 x 32), as the engine streams it', font=FONT, fill=(255, 255, 255))
    d.text((x, 50), 'Gate room (FireRed\'s)', font=FONT, fill=(255, 255, 255))
    d.text((x, ys - 30), 'Saffron west gate (FireRed\'s)', font=FONT, fill=(255, 255, 255))
    gx, gy = (CEL + 25) * 16 * S, (17 + 1) * 16 * S + 40
    d.line([gx, gy, x, 80 + 5 * 16 * S + 8], fill=(255, 140, 60), width=4)
    d.line([x + room.width * S - 20, 80 + 5 * 16 * S + 8, x + 8 * 16 * S, ys + 9 * 16 * S], fill=(255, 140, 60), width=4)
    sheet.save(R.EV / 'route-map.png')
    print(sheet.size)

if __name__ == '__main__':
    main()
