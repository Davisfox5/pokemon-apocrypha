"""Kanto gatehouse options for the owner's call: HGSS's own gate model (247), the one HGSS uses in
Johto and Kanto alike, given a Kanto colourway on its own textures (AGENTS.md: the HGSS model is
the base; the story changes it on its own textures).

    python3 tools/gba/maps/route7/gates.py

    A  HGSS's gate as it is (teal), what Route 7 has now; Johto's gates are the same building
    B  Kanto's FireRed family: the teal roof, walls and step in the seamed grey-blue metal of
       FireRed's own Kanto gatehouses (the one Saffron already draws at its west edge), its
       facade in their yellow brick; the glass band kept
    C  Kanto steel and glass (DESIGN.md: "cooler institutional steel and glass; restrained,
       corporate"): a graphite steel roof and frame, a pale concrete step, the facade glazed
       with the model's own window glass

Each colour of a texture goes to the target ramp's colour at the same place in the texture's own
light-to-dark order, so every line of the texture stays. Writes evidence/gate-options.png (the
three at 3x, then each in place on Route 7's lot) and source/art/gate-{b,c}.png.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
sys.path.insert(0, str(HERE))
import compose as R            # noqa: E402  (before art, which puts Celadon's tools first on the path)
import gen3_art as G3          # noqa: E402
import art as A                # noqa: E402

FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
# FireRed's gatehouse (Saffron's west gate, its native pixels), light to dark
FR_METAL = [(231, 239, 239), (206, 222, 239), (173, 189, 206), (148, 165, 181), (123, 123, 132), (90, 90, 115), (66, 74, 107)]
FR_BRICK = [(239, 231, 140), (231, 222, 165), (214, 198, 132), (198, 173, 107), (148, 107, 107), (123, 74, 74)]
STEEL = [(176, 184, 196), (140, 150, 166), (108, 118, 136), (82, 90, 108), (60, 66, 82), (44, 48, 62)]
CONCRETE = [(232, 232, 226), (210, 210, 204), (186, 186, 182), (160, 160, 158), (128, 128, 128)]

lum = lambda c: 3 * c[0] + 4 * c[1] + 2 * c[2]

def remap(t, pick, ramp):
    """The texture's colours that `pick` selects onto `ramp`, by their light-to-dark order."""
    out = t.copy()
    a = t[..., 3] > 0
    cols = sorted({tuple(int(v) for v in c) for c in t[..., :3][a] if pick(c)}, key=lambda c: -lum(c))
    for i, c in enumerate(cols):
        j = round(i * (len(ramp) - 1) / max(1, len(cols) - 1))
        m = a & np.all(t[..., :3] == c, -1)
        out[m, :3] = ramp[j]
    return out

teal = lambda c: int(c[1]) > int(c[0]) + 30 and int(c[2]) > int(c[0]) + 20
tan = lambda c: int(c[0]) >= int(c[2]) + 25 and int(c[0]) > 150
brown = lambda c: int(c[0]) >= int(c[2]) + 25 and int(c[0]) <= 150

FR_WALL = [(231, 239, 239), (206, 222, 239), (173, 189, 206), (148, 165, 181)]

def split(t, left, right):
    """gate_p2 holds the frame round the roof (its left 32 texels) and the facade band under the
    windows (the rest): each its own treatment."""
    out = left(t.copy())
    out[:, 32:] = right(t.copy())[:, 32:]
    return out

def retex_b():
    return {'gate': lambda t: remap(remap(remap(t, teal, FR_METAL), tan, FR_WALL), brown, FR_METAL[3:]),
            'gate_p2': lambda t: split(t, lambda u: remap(u, lambda c: True, FR_WALL),
                                       lambda u: remap(remap(u, tan, FR_BRICK), brown, FR_BRICK[3:]))}

def retex_c(glass):
    def glazed(t):
        out = remap(t, lambda c: True, CONCRETE)
        a = t[..., 3] > 0
        g = np.tile(glass, (t.shape[0] // glass.shape[0] + 1, t.shape[1] // glass.shape[1] + 1, 1))[:t.shape[0], :t.shape[1]]
        panel = a.copy(); panel[:, ::16] = False; panel[::16] = False      # mullions every 16 texels
        out[panel] = g[panel]
        out[a & ~panel, :3] = STEEL[2]
        return out
    return {'gate': lambda t: remap(remap(remap(t, teal, STEEL), tan, CONCRETE), brown, STEEL[2:]),
            'gate_p2': lambda t: split(t, lambda u: remap(u, lambda c: True, CONCRETE), glazed)}

# FireRed's gatehouse brick (Saffron's west gate, its native pixels): 4 px courses, 8 px bricks
# with a one-pixel light joint, every other course offset half a brick and a shade lighter.
BRICK = ["yyyyyyyy", "ymmmmmmm", "ymmmmmmm", "ymmmmmmm", "yyyyyyyy", "ddddyddd", "ddddyddd", "ddddyddd"]
BRICK_RGB = dict(y=(231, 222, 165), m=(214, 198, 132), d=(198, 173, 107))

def bricks(img):
    """B's facade band (the pixels in FireRed's brick colours) laid with FireRed's brick, from the
    band's own top row, so the gate's front reads as FireRed's gatehouses do."""
    out = img.copy()
    band = np.isin(img[..., :3].reshape(-1, 3).view([('', np.uint8)] * 3), np.array(FR_BRICK, np.uint8).view([('', np.uint8)] * 3)).reshape(img.shape[:2])
    band &= img[..., 3] > 0
    ys, xs = np.nonzero(band)
    y0, x0 = ys.min(), xs.min()
    for y, x in zip(ys, xs):
        out[y, x, :3] = BRICK_RGB[BRICK[(y - y0) % 8][(x - x0) % 8]]
    return out

def render(retex=None):
    img, _ = G3.convert(MODS, [(247, (0, 0, 0))], scale=16.0, pitch=45.0, retex=retex, finish=True, n=14)
    return img

def in_place(sprite):
    """The route's picture with this gate on HGSS's lot (the composed ground and trees)."""
    kind = R.ledger()[0]
    gr = R.ground(kind)
    objs = R.objects(kind)
    pic = gr.copy()
    for o in objs:
        img = sprite if o['fam'] == 'gate' else o['img']
        from common import put
        put(pic, img, o['X'], o['Y'] + (o['img'].shape[0] - img.shape[0] if o['fam'] == 'gate' else 0))
    y0 = (R.OY + 10) * 16
    return pic[y0:y0 + 13 * 16, 17 * 16:R.MW * 16]

def main():
    global MODS
    MODS = A.models()
    import buildings as Bd
    glass = Bd.model_texture(MODS, 247, 'gate_3')
    opts = [('A  HGSS gate as is (Johto and Kanto alike)', render()),
            ('B  Kanto, FireRed\'s family (metal roof, yellow brick)', bricks(render(retex_b()))),
            ('C  Kanto steel and glass (DESIGN.md)', render(retex_c(glass)))]
    Image.fromarray(opts[1][1]).save(R.SRC / 'art/gate-b.png'); Image.fromarray(opts[2][1]).save(R.SRC / 'art/gate-c.png')
    frlg = np.array(Image.open(R.ROOT / 'gba/art/saffron-kanto/evidence/native.png').convert('RGB'))[24 * 16:30 * 16, 1 * 16:9 * 16]
    places = [in_place(img) for _, img in opts]
    S = 3
    pw, ph = places[0].shape[1] * 2, places[0].shape[0] * 2
    W = max(len(opts) * (130 * S + 20) + frlg.shape[1] * S + 20, len(opts) * (pw + 12))
    H = 30 + 110 * S + 40 + ph + 20
    sheet = Image.new('RGB', (W, H), (24, 28, 36))
    d = ImageDraw.Draw(sheet)
    x = 10
    for label, img in opts:
        tile = Image.new('RGBA', (img.shape[1], img.shape[0]), (120, 200, 150, 255))
        tile.alpha_composite(Image.fromarray(img))
        sheet.paste(tile.convert('RGB').resize((img.shape[1] * S, img.shape[0] * S), Image.NEAREST), (x, 30 + (110 - img.shape[0]) * S))
        d.text((x, 8), label, font=FONT, fill=(240, 240, 240))
        x += 130 * S + 20
    sheet.paste(Image.fromarray(frlg).resize((frlg.shape[1] * S, frlg.shape[0] * S), Image.NEAREST), (x, 30 + 110 * S - frlg.shape[0] * S))
    d.text((x, 8), "Saffron's west gate now (FireRed's)", font=FONT, fill=(240, 240, 240))
    y = 30 + 110 * S + 30
    for i, p in enumerate(places):
        sheet.paste(Image.fromarray(p).resize((pw, ph), Image.NEAREST), (10 + i * (pw + 12), y))
        d.text((14 + i * (pw + 12), y + 4), 'ABC'[i] + ' on Route 7', font=FONT, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    sheet.save(R.EV / 'gate-options.png')
    print(sheet.size)

if __name__ == '__main__':
    main()
