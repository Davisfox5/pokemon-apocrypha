"""The apartment block as a plan for the owner (2026-11-03: "a full apartment complex": an
upscale lobby on 1F, an elevator and stairs, four floors of two apartments each, and the
penthouse at the top). Every cell is a FireRed metatile; a piece set on another room's floor has
its floor pixels swapped for this room's (FireRed's bed on Copycat's cream floor).

    python3 tools/gba/maps/celadon_elements/apartments_plan.py

    1F           the lobby: HGSS's Condominiums 1F as built (interiors.apartments_grid), with a
                 seating area and a painting added
    2F-5F        one hall on every floor, FireRed's Condominiums pieces: stairs down and up at
                 either end of the back wall, apartment A's door, the elevator with its call
                 panel, apartment B's door
    apartment A  Copycat's house 1F (Saffron): kitchen, dining table on its rug, TV; a bedroom
                 corner where its stairs were (Copycat 2F's desk, PC and shelves, Pallet's bed)
    apartment B  Copycat's house 2F: living room with the TV on its rug, desk and PC; a kitchen
                 where its stairs were (Copycat 1F's fridge and sink), Pallet's bed
    6F           the penthouse: the whole floor, elevator and stairs opening into it, in
                 FireRed's Condominiums pieces (lounge, bookcases, desk, bed, display cabinet),
                 a door out to its roof terrace (HGSS's Condominiums roof, its planters)
    elevator     one car for every floor (FireRed's Dept Store elevator)

Writes gba/art/celadon-elements/evidence/apartments/*.png and evidence/apartments-plan.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C                                  # noqa: E402
sys.path.append(str(C.HERE.parent / 'saffron'))
import frlg                                         # noqa: E402
import interiors as I                               # noqa: E402

ENG = C.ROOT.parent / 'pokeemerald-expansion'
OUT = C.EV / 'apartments'
LAYOUTS = {l['name']: l for l in json.loads((ENG / 'data/layouts/layouts.json').read_text())['layouts'] if l}
PAIRS = dict(K=frlg.Pair(ENG, 'building_frlg', 'condominiums_frlg'), G=frlg.Pair(ENG, 'building_frlg', 'generic_building_1_frlg'))
def grid(name):
    l = LAYOUTS[name]
    return (np.frombuffer((ENG / l['blockdata_filepath']).read_bytes(), '<u2').reshape(l['height'], l['width']).astype(int) & 0x3FF)
SRC = dict(K1=('K', grid('CeladonCity_Condominiums_1F_Layout')), K2=('K', grid('CeladonCity_Condominiums_2F_Layout')),
           K3=('K', grid('CeladonCity_Condominiums_3F_Layout')), KR=('K', grid('CeladonCity_Condominiums_Roof_Layout')),
           C1=('G', grid('SaffronCity_CopycatsHouse_1F_Layout')), C2=('G', grid('SaffronCity_CopycatsHouse_2F_Layout')),
           P2=('G', grid('PalletTown_PlayersHouse_2F_FRLG_Layout')))
FLOOR = dict(K=0x281, G=0xA9)
FLOOR_SHADES = {}

def shades():
    """Pallet 2F's floor in all its cells (its shaded edge too), for the floor swap."""
    pair, g = SRC['P2']
    out = set()
    for m in {int(g[y, x]) for y, x in ((3, 0), (6, 0), (7, 0), (3, 5), (8, 5))}:
        out |= {tuple(v) for v in flat(pair, m).reshape(-1, 3).tolist()}
    FLOOR_SHADES['G'] = out

def flat(pair, m):
    b, t = PAIRS[pair].cell(m)
    out = b.copy(); a = t[..., 3] > 0; out[a] = t[..., :3][a]
    return out

class Room:
    """A room as cells, each (pair, metatile) or a piece carried from another floor."""
    def __init__(self, pair, w, h, fill):
        self.pair = pair
        self.img = np.zeros((h * 16, w * 16, 3), np.uint8)
        self.w, self.h = w, h
        for y in range(h):
            for x in range(w):
                self.put(x, y, pair, fill)
    def put(self, x, y, pair, m, from_floor=None):
        c = flat(pair, m)
        if from_floor is not None:                                 # the source room's floor colours take this room's floor
            cols = {tuple(v) for v in flat(pair, from_floor).reshape(-1, 3).tolist()} | FLOOR_SHADES.get(pair, set())
            dst = flat(self.pair, FLOOR[self.pair])
            same = np.array([[tuple(v) in cols for v in row] for row in c.tolist()])
            c[same] = dst[same]
        self.img[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = c
    def stamp(self, src, sx, sy, w, h, dx, dy, floor=None):
        pair, g = SRC[src]
        for yy in range(h):
            for xx in range(w):
                self.put(dx + xx, dy + yy, pair, int(g[sy + yy, sx + xx]), floor)
    def cells(self, xy, pair, m):
        for x, y in xy:
            self.put(x, y, pair, m)

def condo_shell(w, h):
    r = Room('K', w, h, 0x281)
    for x in range(w):
        r.put(x, 0, 'K', 0x289); r.put(x, 1, 'K', 0x291); r.put(x, 2, 'K', 0x282); r.put(x, h - 1, 'K', 0x8)
    for y in range(3, h - 1):
        r.put(0, y, 'K', 0x282)
    return r
def doorway(r, x):
    for i, (a, b) in enumerate(((0x2db, 0x2e3), (0x2dc, 0x2e4), (0x2eb, 0x2ec))):
        r.put(x + i, 0, 'K', a); r.put(x + i, 1, 'K', b)
def panel(r, x): r.put(x, 0, 'K', 0x28b); r.put(x, 1, 'K', 0x293)
def window(r, x): r.put(x, 0, 'K', 0x2f8); r.put(x, 1, 'K', 0x2f9)
def painting(r, x): r.stamp('K2', 1, 5, 2, 2, x, 0) if False else (r.put(x, 0, 'K', 0x2b8), r.put(x + 1, 0, 'K', 0x2b9), r.put(x, 1, 'K', 0x2c0), r.put(x + 1, 1, 'K', 0x2c1))
def plant(r, x, y, wall=False): r.put(x, y - 1, 'K', 0x2ca if wall else 0x2c9); r.put(x, y, 'K', 0x2d1)
def stairs_down(r, x): r.stamp('K2', 0, 0, 2, 4, x, 0)        # FireRed Condominiums 2F's stairs down
def stairs_up(r, x):                                           # FireRed Condominiums 1F's stairs up, its window left out
    r.stamp('K1', 4, 0, 3, 4, x, 0); r.put(x, 0, 'K', 0x289); r.put(x, 1, 'K', 0x291)
def sofa_set(r, x, y): r.stamp('K2', 1, 7, 5, 4, x, y)        # sofa, octagon table
def bookcase(r, x, y): r.stamp('K2', 5, 5, 2, 4, x, y)
def desk(r, x, y): r.stamp('K3', 0, 8, 3, 2, x, y)
def bed_on(r, x, y): r.stamp('P2', 1, 5, 2, 2, x, y, floor=0x1)  # Pallet's bed, its olive floor swapped

def _init():
    shades()

def lobby():
    r = Room('K', 15, 14, 0x281)
    g = I.apartments_grid().astype(int) & 0x3FF
    for y in range(14):
        for x in range(15):
            r.put(x, y, 'K', int(g[y, x]))
    painting(r, 6)                                             # upscale: a painting on the back wall
    sofa_set(r, 1, 4)                                          # and a seating area in the open west half
    return r

def hall():
    r = condo_shell(17, 9)
    stairs_down(r, 0); doorway(r, 3); doorway(r, 7); panel(r, 10); doorway(r, 11); stairs_up(r, 14)
    plant(r, 6, 3); plant(r, 13, 7); plant(r, 2, 7)
    return r

def apartment_a():
    pair, g = SRC['C1']
    h, w = g.shape
    r = Room('G', w, h, 0xA9)
    for y in range(h):
        for x in range(w):
            r.put(x, y, 'G', int(g[y, x]))
    for x in range(9, 13):                                     # the stairs out: a bedroom corner
        r.put(x, 0, 'G', int(g[0, 9])); r.put(x, 1, 'G', int(g[1, 9])); r.put(x, 2, 'G', int(g[2, 8]))
        if x >= 10: r.put(x, 3, 'G', 0xA9)
    r.stamp('C2', 1, 0, 4, 3, 9, 0)                            # Copycat 2F's desk, PC and shelves
    bed_on(r, 10, 4)
    return r

def apartment_b():
    pair, g = SRC['C2']
    h, w = g.shape
    a = SRC['C1'][1]
    r = Room('G', w, h + 1, 0xA9)
    for y in range(h):
        for x in range(w):
            r.put(x, y, 'G', int(g[y, x]))
    for x in range(7, w):                                      # the stairs out: a kitchen
        r.put(x, 2, 'G', int(g[2, 6])); r.put(x, 3, 'G', 0xA9)
    r.stamp('C1', 1, 0, 3, 3, 7, 0)                            # Copycat 1F's fridge and sink
    bed_on(r, 9, 5)
    my, mx = [(y, x) for y in range(a.shape[0]) for x in range(a.shape[1]) if a[y, x] in (0xE7,)][0]
    for i in range(w):
        r.put(i, h, 'G', 0x8)
    r.stamp('C1', mx - 1, my, 3, 2, 3, h - 1)                  # Copycat 1F's mat and exit
    return r

def penthouse():
    r = condo_shell(17, 13)
    stairs_down(r, 0); window(r, 3); painting(r, 4); doorway(r, 7); panel(r, 10); window(r, 14)
    for i, col in enumerate(((0x2ba, 0x2c2, 0x2bc), (0x2bb, 0x2c3, 0x2bd))):   # a display cabinet
        for y, m in enumerate(col):
            r.put(12 + i, y, 'K', m)
    r.stamp('K1', 1, 9, 4, 5, 7, 5)                            # a dining table with its stools
    bookcase(r, 15, 2)
    sofa_set(r, 2, 5)
    desk(r, 12, 5)
    bed_on(r, 13, 9)
    plant(r, 0, 11); plant(r, 16, 11); plant(r, 9, 11)
    for x, m in ((6, 0x2e8), (7, 0x2e9), (8, 0x2ea)):           # the terrace door: a mat out to the roof
        r.put(x, 11, 'K', m)
    for x, m in ((6, 0x1a), (7, 0x1b), (8, 0x1c)):
        r.put(x, 12, 'K', m)
    return r

def terrace():
    g = SRC['KR'][1]
    W, H = 17, 12
    r = Room('K', W, H, 0x306)
    for x in range(W):
        r.put(x, 0, 'K', 0x328); r.put(x, 1, 'K', 0x320); r.put(x, H - 1, 'K', 0x320)
    for y in range(2, H - 1):
        r.put(0, y, 'K', 0x321); r.put(W - 1, y, 'K', 0x322)
    r.put(0, 1, 'K', 0x319); r.put(W - 1, 1, 'K', 0x31a); r.put(0, H - 1, 'K', 0x329); r.put(W - 1, H - 1, 'K', 0x32a)
    for x in range(6, 11):                                     # the penthouse's wall and its door onto the terrace
        r.put(x, 2, 'K', 0x289); r.put(x, 3, 'K', 0x291)
    for i, (a, b) in enumerate(((0x2db, 0x2e3), (0x2dc, 0x2e4), (0x2eb, 0x2ec))):
        r.put(7 + i, 2, 'K', a); r.put(7 + i, 3, 'K', b)
    for x, y in ((2, 5), (2, 8), (13, 5), (13, 8), (7, 8)):
        r.stamp('KR', 11, 4, 2, 2, x, y)                       # HGSS's roof planters, FireRed's
    return r

def elevator():
    sp = frlg.Pair(ENG, 'building_frlg', 'condominiums_frlg')
    sd = ENG / 'data/tilesets/secondary/silph_co_frlg'
    sm = np.frombuffer((sd / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    sp.meta.update({frlg.NT + i: [int(v) for v in sm[i]] for i in range(len(sm))})
    PAIRS['S'] = sp
    g = grid('CeladonCity_DepartmentStore_Elevator_Layout')
    r = Room('S', g.shape[1], g.shape[0], int(g[3, 2]))
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            r.put(x, y, 'S', int(g[y, x]))
    return r

def main():
    _init()
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob('*.png'):
        f.unlink()
    rooms = dict(lobby=lobby(), hall=hall(), apartment_a=apartment_a(), apartment_b=apartment_b(), penthouse=penthouse(),
                 terrace=terrace(), elevator=elevator())
    for k, r in rooms.items():
        Image.fromarray(r.img).save(OUT / f'{k}.png')
    sheet(rooms)

def sheet(rooms):
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    S = 2
    big = lambda k: Image.fromarray(rooms[k].img).resize((rooms[k].w * 16 * S, rooms[k].h * 16 * S), Image.NEAREST)
    # the stack: floor boxes, top to bottom
    stack = [('Roof', 'Penthouse terrace (private)'), ('6F', 'Penthouse'), ('5F', 'Apartments 5A, 5B'), ('4F', 'Apartments 4A, 4B'),
             ('3F', 'Apartments 3A, 3B'), ('2F', 'Apartments 2A, 2B'), ('1F', 'Lobby, door to Celadon (28, 14)')]
    bw, bh = 330, 46
    st = Image.new('RGB', (bw + 230, len(stack) * (bh + 8) + 40), (16, 18, 24)); d = ImageDraw.Draw(st)
    d.text((10, 6), 'The building', font=F, fill=(255, 230, 120))
    for i, (fl, what) in enumerate(stack):
        y = 34 + i * (bh + 8)
        d.rectangle((10, y, 10 + bw, y + bh), outline=(200, 200, 200), fill=(40, 46, 60))
        d.text((20, y + 6), fl, font=F, fill=(255, 255, 255)); d.text((70, y + 8), what, font=f, fill=(230, 230, 230))
        if fl != 'Roof':
            d.text((20, y + 27), 'stairs' if fl in ('1F', '6F') else 'stairs down, up', font=f, fill=(150, 200, 255))
        d.rectangle((bw + 40, y, bw + 90, y + bh), outline=(255, 200, 120), fill=(70, 56, 40) if fl != 'Roof' else (16, 18, 24))
        if fl != 'Roof':
            d.text((bw + 44, y + 14), 'lift', font=f, fill=(255, 220, 160))
    d.text((bw + 100, 40), 'One elevator\nstops at every\nfloor, 1F-6F;\nthe terrace is\nthrough the\npenthouse', font=f, fill=(220, 220, 220))
    panels = [('1F  Lobby', 'lobby', ["HGSS's Condominiums 1F (built): elevator, board,", "display cabinet, stairs up; a seating area and a", "painting added for an upscale lobby"]),
              ('2F-5F  Hall (the same on every floor)', 'hall', ["Stairs down (left) and up (right), apartment A's door,", "the elevator with its call panel, apartment B's door"]),
              ('Apartment A (2A-5A)', 'apartment_a', ["Copycat's house 1F (Saffron): kitchen, dining table,", "TV; a bedroom corner where its stairs were (desk, PC,", "shelves from its 2F, Pallet's bed)"]),
              ('Apartment B (2B-5B)', 'apartment_b', ["Copycat's house 2F: living room, TV on its rug, desk", "and PC; a kitchen where its stairs were, a bed"]),
              ('6F  Penthouse', 'penthouse', ["The whole floor: elevator and stairs open into it;", "lounge, dining table, display cabinet, bookcase, desk,", "bed, plants; the mat at the front leads to the terrace"]),
              ('Roof  Penthouse terrace', 'terrace', ["HGSS's Condominiums roof: planters, the penthouse's", "door; private, reached only through the penthouse"]),
              ('Elevator', 'elevator', ["One car (FireRed's Dept Store elevator), a floor menu", "for 1F-6F"])]
    blocks = []
    for title, k, notes in panels:
        im = big(k)
        b = Image.new('RGB', (im.width + 470, im.height + 34), (24, 28, 36)); dd = ImageDraw.Draw(b)
        dd.text((6, 4), title, font=F, fill=(255, 230, 120)); b.paste(im, (6, 28))
        for i, n in enumerate(notes):
            dd.text((im.width + 20, 34 + i * 19), n, font=f, fill=(235, 235, 235))
        blocks.append(b)
    cols = [[blocks[0], blocks[1], blocks[6]], [blocks[2], blocks[3]], [blocks[4], blocks[5]]]
    colw = [max(b.width for b in c) for c in cols]
    H = max(st.height, max(sum(b.height + 12 for b in c) for c in cols)) + 60
    W = st.width + sum(colw) + 20 * (len(cols) + 2)
    o = Image.new('RGB', (W, H), (16, 18, 24)); d = ImageDraw.Draw(o)
    d.text((12, 10), "Celadon apartments: an upscale apartment block (plan; only the lobby's room is built)", font=F, fill=(255, 255, 255))
    o.paste(st, (12, 40))
    x = st.width + 30
    for c, cw in zip(cols, colw):
        y = 40
        for b in c:
            o.paste(b, (x, y)); y += b.height + 12
        x += cw + 20
    o.save(C.EV / 'apartments-plan.png')
    print(o.size)

if __name__ == '__main__':
    main()
