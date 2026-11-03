"""The apartment block's floor plans, drawn from scratch (owner, 2026-11-03: "draw out a rough
floor plan from scratch, then build accordingly using elements from the games"; a mixture of
real-world layouts and what the game can do; HGSS's model styling).

    python3 tools/gba/maps/celadon_elements/apartments_floorplans.py

One square is one step (one Gen 3 cell). What the game can do sets the rules: each floor is one
map; a wall running east-west is seen face on (two squares: its top and its face, the north
wall with its windows), a wall running north-south from above (one square); a doorway is a
one-square gap; the elevator is a door with its call
panel; the stairs stand against the north wall. Rooms are sized as a real flat would be, at the
game's scale. Furniture is HGSS's own room models (a/1/4/8, numbered as in
evidence/apartments/hgss-furniture.png), each drawn at its footprint.

    1F    lobby: street door, concierge desk, mail wall, lounge, the core
    2F-5F a studio (west) and a two-bedroom (east) either side of the core (elevator, stairs)
    6F    the penthouse: the whole floor, the core opening into its foyer
    roof  the penthouse's terrace, up its private stairs

Writes gba/art/celadon-elements/evidence/apartments/floorplans.png.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'gba/art/celadon-elements/evidence/apartments'
S = 22                                        # pixels per square
W, H = 31, 16                                 # every floor: 31 x 16 squares

COL = dict(core=(208, 214, 226), living=(236, 222, 190), kitchen=(222, 232, 208), bed=(214, 222, 240), bath=(204, 236, 236),
           closet=(226, 214, 236), lobby=(236, 230, 210), terrace=(200, 226, 180), study=(232, 216, 204))
WALL, NWALL = (60, 64, 80), (96, 104, 124)

# furniture: (label, HGSS model, w, h)
F = dict(bed=('bed', 17, 1, 2), tv=('TV', 19, 1, 1), stove=('stove/sink', 20, 2, 1), fridge=('fridge', 21, 1, 1),
         plant=('plant', 23, 1, 1), pc=('PC desk', 24, 2, 1), books=('bookcase', 39, 1, 1), shelf=('shelf', 48, 2, 1),
         wardrobe=('wardrobe', 64, 2, 1), table=('table', 94, 2, 2), dining=('dining table', 98, 3, 2),
         coffee=('coffee table', 96, 2, 1), stool=('stool', 89, 1, 1), round=('round table', 111, 2, 2),
         planter=('planter', 114, 2, 1), tree=('tree', 123, 1, 1), painting=('painting', 139, 2, 1),
         counter=('counter', 9, 3, 1), seat=('seat', 81, 1, 1), cabinet=('cabinet', 37, 2, 1), mail=('mail wall', 49, 2, 1),
         clock=('clock', 16, 1, 1), lamp=('lamp', 157, 1, 1))

def plan_core(p, stairs_up=True, stairs_down=True, elevator=True):
    """The core, x 11-16: elevator and stairs on the north wall, the corridor to the units' doors."""
    p['rooms'].append(((11, 2, 16, 14), 'core', 'elevator lobby'))
    if elevator:
        p['fixtures'].append(((11, 0, 12, 1), 'elevator'))
        p['furniture'].append(('lamp', 11, 2)) if False else None
    if stairs_down:
        p['fixtures'].append(((13, 0, 14, 3), 'stairs down'))
    if stairs_up:
        p['fixtures'].append(((15, 0, 16, 3), 'stairs up'))
    p['walls'] += [(10, 2, 10, 14), (17, 2, 17, 14)]

def new(title):
    return dict(title=title, rooms=[], walls=[], doors=[], furniture=[], fixtures=[], notes=[])

def typical():
    p = new('2F-5F  (the same on each floor)')
    plan_core(p)
    p['doors'] += [(10, 12), (17, 12)]                        # the units' front doors off the core
    p['furniture'] += [('plant', 14, 13), ('painting', 13, 8) if False else ('plant', 12, 13)]
    # the studio, x 0-9: kitchen on the north wall, dining, living, sleeping, bath and closet
    p['rooms'] += [((0, 2, 9, 9), 'living', 'studio: living / kitchen'), ((5, 10, 9, 14), 'bed', 'sleeping'),
                   ((0, 10, 3, 14), 'bath', 'bath')]
    p['walls'] += [(0, 8, 3, 9), (4, 8, 4, 14)]
    p['doors'] += [(2, 8), (2, 9)]
    p['furniture'] += [('fridge', 0, 1), ('stove', 1, 1), ('stove', 3, 1), ('tv', 7, 1), ('books', 9, 1),
                       ('table', 1, 4), ('stool', 0, 5), ('stool', 3, 5), ('seat', 6, 5), ('seat', 8, 5), ('coffee', 6, 3),
                       ('bed', 8, 11), ('wardrobe', 5, 10), ('plant', 9, 6)]
    p['notes'] += ['Studio: kitchen along the window wall, a table for two, TV with seats facing it; sleeping', 'area behind, the bath walled off with its own door (a door only: no bath pieces in the game)']
    # the two-bedroom, x 18-30: bedrooms along the north (windows), bath between, open living to the south
    p['rooms'] += [((18, 2, 21, 5), 'bed', 'bedroom 1'), ((23, 2, 25, 5), 'bath', 'bath'), ((27, 2, 30, 5), 'bed', 'bedroom 2'),
                   ((18, 8, 30, 14), 'living', 'living / dining / kitchen')]
    p['walls'] += [(22, 2, 22, 5), (26, 2, 26, 5), (18, 6, 30, 7)]
    p['doors'] += [(20, 6), (20, 7), (24, 6), (24, 7), (28, 6), (28, 7)]
    p['furniture'] += [('bed', 18, 3), ('pc', 20, 1), ('wardrobe', 27, 1), ('bed', 30, 3), ('books', 29, 1),
                       ('stove', 26, 9), ('stove', 28, 9), ('fridge', 30, 9), ('dining', 26, 11), ('stool', 25, 12), ('stool', 29, 12),
                       ('tv', 20, 9), ('seat', 19, 12), ('seat', 21, 12), ('coffee', 19, 10), ('plant', 18, 14), ('plant', 30, 14)]
    p['notes'] += ['Two-bedroom: two bedrooms and the bath on the window side off a short hall; one open', 'room for living (TV, seats), dining (table for four) and the kitchen run along its far wall']
    return p

def lobby():
    p = new('1F  lobby')
    plan_core(p, stairs_down=False)
    p['walls'] = [w for w in p['walls'] if w not in ((10, 2, 10, 14), (17, 2, 17, 14))]
    p['rooms'] = [((0, 2, 30, 14), 'lobby', 'lobby')]
    p['rooms'] += [((0, 2, 5, 5), 'study', 'concierge office')]
    p['walls'] += [(6, 2, 6, 7), (0, 6, 5, 7)]
    p['doors'] += [(3, 6), (3, 7)]
    p['fixtures'] += [((13, 15, 15, 15), 'street door (28, 14)')]
    p['furniture'] += [('counter', 7, 8), ('pc', 1, 1), ('shelf', 3, 1), ('mail', 18, 1), ('mail', 20, 1), ('mail', 22, 1),
                       ('painting', 25, 1), ('round', 24, 9), ('seat', 23, 9), ('seat', 26, 9), ('seat', 24, 11), ('seat', 25, 11),
                       ('tree', 18, 13), ('tree', 30, 13), ('tree', 0, 13), ('plant', 10, 13), ('plant', 17, 13), ('clock', 8, 1)]
    p['notes'] += ['Lobby: in from the street at the south; the concierge desk facing the door with the office', 'behind it; the mail wall and a lounge on the east side; the elevator and stairs straight ahead']
    return p

def penthouse():
    p = new('6F  penthouse')
    plan_core(p, stairs_up=True)
    p['rooms'][0] = ((11, 2, 16, 14), 'core', 'foyer')
    p['doors'] += [(10, 5), (17, 5), (10, 11), (17, 11)]
    p['fixtures'] = [f for f in p['fixtures'] if f[1] != 'stairs up'] + [((15, 0, 16, 3), 'stairs up to the terrace')]
    p['rooms'] += [((0, 2, 9, 14), 'living', 'great room: living / dining / kitchen')]
    p['furniture'] += [('fridge', 0, 1), ('stove', 1, 1), ('stove', 3, 1), ('counter', 1, 4), ('stool', 1, 5), ('stool', 3, 5),
                       ('dining', 6, 3), ('stool', 5, 4), ('stool', 9, 4), ('tv', 7, 1) if False else ('painting', 7, 1),
                       ('tv', 4, 9), ('seat', 3, 12), ('seat', 5, 12), ('coffee', 3, 10), ('tree', 0, 13), ('tree', 9, 13), ('lamp', 0, 9)]
    p['rooms'] += [((18, 2, 22, 5), 'study', 'study'), ((24, 2, 30, 5), 'bed', 'master bedroom'), ((18, 8, 30, 8), 'core', 'hall'),
                   ((18, 11, 22, 14), 'bed', 'guest bedroom'), ((24, 11, 26, 14), 'closet', 'closet'), ((28, 11, 30, 14), 'bath', 'bath')]
    p['walls'] += [(23, 2, 23, 5), (18, 6, 30, 7), (18, 9, 30, 10), (23, 11, 23, 14), (27, 11, 27, 14)]
    p['doors'] = [d for d in p['doors'] if d not in ((17, 5), (17, 11))] + [(17, 8)]
    p['doors'] += [(20, 6), (20, 7), (27, 6), (27, 7), (20, 9), (20, 10), (25, 9), (25, 10), (29, 9), (29, 10)]
    p['furniture'] += [('books', 18, 1), ('books', 19, 1), ('pc', 21, 1), ('cabinet', 18, 4),
                       ('wardrobe', 24, 1), ('bed', 29, 2), ('plant', 30, 1) if False else ('painting', 26, 1), ('plant', 24, 5),
                       ('bed', 22, 11), ('wardrobe', 18, 13), ('plant', 18, 11), ('shelf', 24, 13), ('plant', 30, 8)]
    p['notes'] += ['Penthouse: the elevator and stairs open into a private foyer; the great room to the west (kitchen', 'with an island, dining for six, living); to the east a hall to the study and the master bedroom, the guest',
                   'room, a closet and the bath; the stairs up go to its own roof terrace']
    return p

def roof():
    p = new('Roof  the penthouse terrace')
    p['rooms'] = [((0, 2, 30, 14), 'terrace', 'terrace')]
    p['fixtures'] += [((15, 0, 16, 3), 'stairs down (penthouse)')]
    p['rooms'] += [((11, 2, 17, 5), 'core', 'stair house')]
    p['furniture'] += [('planter', 1, 3), ('planter', 1, 7), ('planter', 1, 11), ('planter', 27, 3), ('planter', 27, 7), ('planter', 27, 11),
                       ('round', 7, 8), ('seat', 6, 8), ('seat', 9, 8), ('round', 21, 8), ('seat', 20, 8), ('seat', 23, 8),
                       ('tree', 14, 12), ('tree', 4, 13), ('tree', 26, 13)]
    p['notes'] += ["Terrace: HGSS's Condominiums roof, the penthouse's own: planters along its edges, two tables"]
    return p

def draw(p):
    FN = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
    FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
    pad = 28
    im = Image.new('RGB', (W * S + 2 * pad, H * S + 2 * pad + 60), (250, 250, 246)); d = ImageDraw.Draw(im)
    X = lambda x: pad + x * S
    Y = lambda y: pad + 22 + y * S
    d.text((pad, 4), p['title'], font=FB, fill=(20, 24, 32))
    d.rectangle((X(0), Y(0), X(W) - 1, Y(H) - 1), fill=(236, 236, 230))
    for (x0, y0, x1, y1), kind, label in p['rooms']:
        d.rectangle((X(x0), Y(y0), X(x1 + 1) - 1, Y(y1 + 1) - 1), fill=COL[kind])
    for x in range(W + 1):
        d.line([(X(x), Y(0)), (X(x), Y(H))], fill=(214, 214, 208))
    for y in range(H + 1):
        d.line([(X(0), Y(y)), (X(W), Y(y))], fill=(214, 214, 208))
    d.rectangle((X(0), Y(0), X(W) - 1, Y(2) - 1), fill=NWALL)                     # the north wall, face on
    d.rectangle((X(0), Y(H - 1), X(W) - 1, Y(H) - 1), fill=WALL)                 # the south wall
    for (x0, y0, x1, y1) in p['walls']:
        d.rectangle((X(x0), Y(y0), X(x1 + 1) - 1, Y(y1 + 1) - 1), fill=WALL)
    for x, y in p['doors']:
        d.rectangle((X(x), Y(y), X(x + 1) - 1, Y(y + 1) - 1), fill=(250, 196, 90))
    for (x0, y0, x1, y1), label in p['fixtures']:
        d.rectangle((X(x0), Y(y0), X(x1 + 1) - 1, Y(y1 + 1) - 1), fill=(120, 150, 210) if 'elev' in label else (176, 176, 196) if 'stairs' in label else (250, 196, 90), outline=(40, 40, 60))
        if 'stairs' in label:
            for k in range(y0 * S, (y1 + 1) * S, 5):
                d.line([(X(x0), Y(0) + k), (X(x1 + 1) - 1, Y(0) + k)], fill=(120, 120, 140))
        d.text((X(x0) + 2, Y(y1 + 1) - 12 if y1 > 1 else Y(y0) + 2), label, font=FN, fill=(10, 10, 30))
    for (x0, y0, x1, y1), kind, label in p['rooms']:
        if label:
            d.text((X(x0) + 3, Y(y1 + 1) - 13), label, font=FN, fill=(70, 60, 50))
    for name, x, y in p['furniture']:
        label, mid, w, h = F[name]
        d.rectangle((X(x) + 2, Y(y) + 2, X(x + w) - 3, Y(y + h) - 3), fill=(255, 255, 255), outline=(150, 90, 40), width=2)
        d.text((X(x) + 4, Y(y) + 4), label if w * S > 40 or len(label) < 6 else label[:5], font=FN, fill=(110, 60, 20))
    for i, n in enumerate(p['notes']):
        d.text((pad, Y(H) + 6 + i * 14), n, font=FN, fill=(30, 30, 40))
    return im

def furniture_key():
    """HGSS's room models the plans use (a/1/4/8), each rendered at the city's 45 degrees with
    the Gen 3 conversion the buildings use (gen3_art.convert), labelled as in the plans."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'olivine_elements'))
    import gen3_art as G3
    import hgss_render as HR
    import numpy as np
    mods = HR.narc.load(ROOT.parent / 'pokeheartgold/files/a/1/4/8')
    FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
    used = sorted({v for v in F.values()}, key=lambda v: v[1])
    T = 150
    cols = 8
    sheet = Image.new('RGB', (cols * T, ((len(used) + cols - 1) // cols) * T + 40), (24, 28, 36)); d = ImageDraw.Draw(sheet)
    d.text((8, 8), "HGSS's room models in the plans (a/1/4/8), at the city's 45 degrees; HGSS has no sofa: 'seat' is its cushion seat",
           font=FB, fill=(255, 255, 255))
    for n, (label, mid, w, h) in enumerate(used):
        img, _ = G3.convert(mods, [(mid, (0, 0, 0))], scale=16.0, pitch=45.0, n=10)
        im = Image.fromarray(img); z = max(1, min(4, 110 // max(im.size)))
        im = im.resize((im.width * z, im.height * z), Image.NEAREST)
        x, y = (n % cols) * T, 40 + (n // cols) * T
        d.rectangle((x + 3, y + 3, x + T - 3, y + T - 3), fill=(48, 56, 72))
        sheet.paste(im, (x + (T - im.width) // 2, y + T - 26 - im.height), im)
        d.text((x + 8, y + T - 22), f'{label} ({mid})', font=FB, fill=(255, 230, 120))
    sheet.save(OUT / 'hgss-furniture.png')

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    furniture_key()
    plans = [lobby(), typical(), penthouse(), roof()]
    ims = [draw(p) for p in plans]
    w = ims[0].width
    key = Image.new('RGB', (w * 2 + 20, 130), (250, 250, 246)); d = ImageDraw.Draw(key)
    FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    FN = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    d.text((28, 10), 'Celadon apartments: floor plans (from scratch; one square = one step)', font=FB, fill=(10, 10, 20))
    items = [(NWALL, 'north wall (seen face on, windows)'), (WALL, 'inner walls (E-W face on, N-S from above)'), ((250, 196, 90), 'doorway'),
             ((120, 150, 210), 'elevator'), ((176, 176, 196), 'stairs')] + [(COL[k], k) for k in ('core', 'living', 'bed', 'bath', 'closet', 'study')]
    for i, (c, t) in enumerate(items):
        x, y = 28 + (i % 6) * 250, 46 + (i // 6) * 26
        d.rectangle((x, y, x + 18, y + 18), fill=c, outline=(40, 40, 40)); d.text((x + 26, y + 1), t, font=FN, fill=(20, 20, 30))
    d.text((28, 100), "White boxes: HGSS's room models at their footprints (evidence/apartments/hgss-furniture.png). Floors 2F-5F are the same plan.",
           font=FN, fill=(20, 20, 30))
    sheet = Image.new('RGB', (w * 2 + 20, key.height + ims[0].height * 2 + 20), (250, 250, 246))
    sheet.paste(key, (0, 0))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 2) * (w + 20), key.height + (i // 2) * (im.height + 20)))
    sheet.save(OUT / 'floorplans.png')
    print(sheet.size)

if __name__ == '__main__':
    main()
