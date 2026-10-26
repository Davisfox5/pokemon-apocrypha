"""Celadon's buildings drawn as Gen 3 pixel art, part by part (round 5).

The owner turned down the model conversions (gen3_art.py) as "balloony", their roofs
smashed and their big buildings squished. These are drawn the way FireRed and Emerald draw
a building (Lilycove's Dept Store and Contest Hall, FireRed's Celadon Dept Store, its
Condominiums): a front elevation with a flat-topped roof seen from above, every edge a hard
straight line, flat fills in four- or five-step ramps lit from the upper left, one-pixel
highlights on lit edges and a dark line on shaded ones, windows as framed glass with a
diagonal glint, C06's outline round the silhouette. HGSS supplies each building's design
(its masses, colours and signature parts); Gen 3 supplies the drawing.

    dept_store()    12 x 10 cells: glass wings round a blue core with the arc emblem, the
                    yellow and red banners, a canopy over the doors
    hotel()         9 x 10: the Pokemon Hotel (HGSS's Condominiums): tan wings, a glass
                    bay up the middle in teal and lime, louvred roof
    apartments()    7 x 10: HGSS's cream tower, stepped roof plant, ribbon windows on purple
    game_corner()   12 x 8: glass-roofed, neon-banded, the arched entrance, chevrons,
                    chasing bulbs, the marquee
    prize_corner()  5 x 5
    cottage(kind)   4 x 4.5: timber-framed cottages in Celadon's colours, the cafe's family
    cafe()          5 x 4.5
"""
from __future__ import annotations
import numpy as np

OUT = (41, 41, 49)

# ----------------------------------------------------------------------------- drawing
def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)

def px(img, x, y, c):
    if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
        img[y, x, :3] = c
        img[y, x, 3] = 255

def fill(img, x0, y0, x1, y1, c):
    y0, x0 = max(y0, 0), max(x0, 0)
    if y1 > y0 and x1 > x0:
        img[y0:y1, x0:x1, :3] = c
        img[y0:y1, x0:x1, 3] = 255

def hline(img, x0, x1, y, c):
    fill(img, x0, y, x1, y + 1, c)

def vline(img, x, y0, y1, c):
    fill(img, x, y0, x + 1, y1, c)

def frame(img, x0, y0, x1, y1, c):
    hline(img, x0, x1, y0, c); hline(img, x0, x1, y1 - 1, c)
    vline(img, x0, y0, y1, c); vline(img, x1 - 1, y0, y1, c)

def slab(img, x0, y0, x1, y1, r):
    """A lit block: base fill, light top and left, dark bottom and right."""
    fill(img, x0, y0, x1, y1, r[2])
    hline(img, x0, x1, y0, r[0]); vline(img, x0, y0, y1, r[1])
    vline(img, x1 - 1, y0 + 1, y1, r[3]); hline(img, x0 + 1, x1, y1 - 1, r[3])

def window(img, x0, y0, w, h, fr, gl, sill=None):
    """A Gen 3 window: a dark frame, glass lighter at the top, a diagonal white glint, a
    lit sill under it."""
    fill(img, x0, y0, x0 + w, y0 + h, fr)
    fill(img, x0 + 1, y0 + 1, x0 + w - 1, y0 + h - 1, gl[2])
    fill(img, x0 + 1, y0 + 1, x0 + w - 1, y0 + 1 + max(1, (h - 2) // 3), gl[1])
    for k in range(min(w, h)):                            # glint, lower left to upper right
        gx, gy = x0 + 2 + k, y0 + h - 3 - k
        if x0 < gx < x0 + w - 2 and y0 < gy < y0 + h - 1 and k < (min(w, h) - 2):
            px(img, gx, gy, gl[0])
            if k % 2 == 0 and gx + 1 < x0 + w - 1:
                px(img, gx + 1, gy, gl[0])
    if sill:
        hline(img, x0 - 1, x0 + w + 1, y0 + h, sill)

def outline(img, c=OUT):
    a = img[..., 3] > 0
    p = np.pad(a, 1)
    e = a & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    img[e, :3] = c

FONT = {
    'A': ["01110", "10001", "11111", "10001", "10001"], 'B': ["11110", "10001", "11110", "10001", "11110"],
    'C': ["01111", "10000", "10000", "10000", "01111"], 'D': ["11110", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "11110", "10000", "11111"], 'F': ["11111", "10000", "11110", "10000", "10000"],
    'G': ["01110", "10000", "10011", "10001", "01110"], 'H': ["10001", "10001", "11111", "10001", "10001"],
    'I': ["111", "010", "010", "010", "111"], 'L': ["10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10001", "10001"], 'N': ["10001", "11001", "10101", "10011", "10001"],
    'O': ["01110", "10001", "10001", "10001", "01110"], 'P': ["11110", "10001", "11110", "10000", "10000"],
    'R': ["11110", "10001", "11110", "10010", "10001"], 'S': ["01111", "10000", "01110", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100"], 'U': ["10001", "10001", "10001", "10001", "01110"],
    'Z': ["11111", "00010", "00100", "01000", "11111"], 'K': ["10001", "10010", "11100", "10010", "10001"],
    '.': ["0", "0", "0", "0", "1"], ' ': ["00", "00", "00", "00", "00"]}

def text_width(s):
    return sum(len(FONT[ch][0]) + 1 for ch in s) - 1

def text(img, s, x, y, c, shadow=None):
    for ch in s:
        g = FONT[ch]
        for gy, row in enumerate(g):
            for gx, v in enumerate(row):
                if v == '1':
                    if shadow:
                        px(img, x + gx, y + gy + 1, shadow)
        for gy, row in enumerate(g):
            for gx, v in enumerate(row):
                if v == '1':
                    px(img, x + gx, y + gy, c)
        x += len(g[0]) + 1

def mirror_into(img, x_mid):
    """Copy the left half onto the right, mirrored about x_mid (an exact centre line)."""
    w = img.shape[1]
    for x in range(w):
        mx = 2 * x_mid - 1 - x
        if x >= x_mid and 0 <= mx < w:
            img[:, x] = img[:, mx]

# ----------------------------------------------------------------------------- ramps
# Light to dark. Each building keeps to a few ramps so it packs into two palette banks.
TEAL = [(184, 240, 240), (104, 200, 216), (48, 152, 184), (32, 104, 144), (24, 64, 104)]
SKY = [(232, 252, 255), (168, 224, 248), (112, 184, 240), (72, 136, 208), (48, 96, 168)]
BLUE = [(168, 208, 255), (96, 152, 240), (64, 104, 216), (40, 72, 168), (32, 48, 120)]
WHITE = [(255, 255, 255), (232, 240, 248), (200, 212, 232), (152, 168, 200)]
YELLOW = [(255, 248, 176), (248, 216, 72), (224, 168, 40), (168, 112, 32)]
RED = [(255, 168, 152), (240, 80, 64), (200, 40, 48), (136, 24, 40)]
TAN = [(255, 240, 200), (240, 216, 160), (216, 184, 120), (176, 144, 88), (120, 96, 64)]
DTEAL = [(112, 176, 168), (64, 136, 136), (40, 104, 112), (24, 72, 88), (16, 48, 64)]
LIME = [(216, 248, 152), (168, 224, 96), (112, 184, 72), (72, 136, 56)]
GREEN = [(144, 216, 168), (88, 176, 128), (56, 136, 104), (32, 96, 80)]
VIOLET = [(232, 200, 255), (184, 144, 232), (136, 96, 200), (96, 64, 160), (64, 40, 112)]
CREAM = [(255, 252, 240), (248, 240, 216), (224, 216, 184), (184, 176, 144), (136, 128, 104)]
PURPLE = [(152, 96, 200), (112, 64, 168), (80, 40, 128), (56, 24, 96), (40, 16, 64)]
NEON = [(255, 224, 255), (240, 160, 255), (200, 104, 240)]
PINK = [(255, 208, 240), (248, 112, 200), (200, 56, 152)]
GOLD = [(255, 248, 184), (248, 208, 72), (208, 152, 40), (144, 96, 24)]
GREY = [(240, 240, 240), (208, 208, 216), (168, 168, 184), (120, 120, 136)]
ORANGE = [(255, 216, 152), (248, 160, 72), (216, 104, 40), (152, 64, 32)]

# ----------------------------------------------------------------------------- pieces
def glass_wall(img, x0, y0, x1, y1, cw, ch, gl, mull, slab_every=None, slab_r=None):
    """A glass curtain wall: panes cw x ch between one-pixel mullions, a glint on every
    other pane, a floor slab every slab_every rows of panes."""
    fill(img, x0, y0, x1, y1, mull)
    row = 0
    y = y0 + 1
    while y + ch <= y1:
        x = x0 + 1
        col = 0
        while x + cw <= x1:
            fill(img, x, y, x + cw, y + ch, gl[2])
            fill(img, x, y, x + cw, y + 2, gl[1])
            if (col + row) % 2 == 0:
                for k in range(min(cw, ch) - 2):
                    px(img, x + 1 + k, y + ch - 2 - k, gl[0])
            fill(img, x + cw - 1, y + 2, x + cw, y + ch, gl[3])
            x += cw + 1
            col += 1
        y += ch + 1
        row += 1
        if slab_every and row % slab_every == 0 and y + 3 <= y1:
            fill(img, x0, y - 1, x1, y + 2, slab_r[2])
            hline(img, x0, x1, y - 1, slab_r[0])
            hline(img, x0, x1, y + 1, slab_r[3])
            y += 2

def awning(img, x0, y0, w, h, col, base=WHITE):
    """A striped shop awning seen from the front: stripes, a scalloped valance."""
    for x in range(x0, x0 + w):
        r = col if ((x - x0) // 3) % 2 == 0 else base
        fill(img, x, y0, x + 1, y0 + h - 1, r[1])
        px(img, x, y0, r[0])
        px(img, x, y0 + h - 1, r[2] if (x - x0) % 3 != 1 else r[3])
    hline(img, x0, x0 + w, y0 + h - 2, col[2])

def double_door(img, x0, y0, w, h, fr, gl, mat=None):
    fill(img, x0, y0, x0 + w, y0 + h, fr)
    half = (w - 3) // 2
    for k, dx in enumerate((1, w - 1 - half)):
        fill(img, x0 + dx, y0 + 1, x0 + dx + half, y0 + h, gl[2])
        fill(img, x0 + dx, y0 + 1, x0 + dx + half, y0 + 4, gl[1])
        for j in range(min(half, h) - 3):
            px(img, x0 + dx + 1 + j, y0 + h - 3 - j, gl[0])
        vline(img, x0 + dx + (half - 2 if k == 0 else 1), y0 + h // 2 - 1, y0 + h // 2 + 2, fr)   # handles
    if mat:
        fill(img, x0 - 2, y0 + h - 2, x0 + w + 2, y0 + h, mat)

GLYPHS = [["111111", "000010", "000100", "001010", "110001", "000000"],    # banner glyphs, kana-like
          ["001000", "111111", "001001", "010001", "100110", "000000"],
          ["100100", "100100", "100100", "000100", "001000", "110000"],
          ["011110", "000000", "111111", "000100", "001000", "010000"]]

# ----------------------------------------------------------------------------- Dept Store
def dept_store():
    """192 x 176, the tallest building in town: the store below, its core raised a storey."""
    low = dept_store_body()
    w, h = low.shape[1], low.shape[0] + 16
    img = canvas(w, h)
    img[16:] = low
    core0, core1 = 62, 130
    slab(img, core0, 0, core1, 26, BLUE)
    fill(img, core0 + 4, 4, core1 - 4, 20, BLUE[3])
    for Y in range(6, 19, 4):
        hline(img, core0 + 8, core1 - 8, Y, BLUE[1])
        hline(img, core0 + 8, core1 - 8, Y + 1, BLUE[4])
    fill(img, core0, 20, core1, 26, BLUE[2]); hline(img, core0, core1, 20, BLUE[1]); hline(img, core0, core1, 25, BLUE[4])
    fill(img, core0, 26, core1, 44, BLUE[3])
    vline(img, core0, 26, 44, BLUE[1]); vline(img, core1 - 1, 26, 44, BLUE[4])
    glass_wall(img, core0 + 6, 28, core1 - 6, 42, 9, 6, SKY, BLUE[4])
    outline(img)
    return img

def dept_store_body():
    """192 x 160. HGSS's Dept Store (model 242): two glass wings in a teal frame either side
    of a taller blue core; on the core the store's white arc emblem, the yellow banner left
    and the red right, white window bands up the middle, a canopy over glass doors."""
    w, h = 192, 160
    img = canvas(w, h)
    core0, core1 = 62, 130
    # wings: glass skylight roof inside a teal parapet, a fascia, the glass wall, shop floor
    for (x0, x1) in ((0, core0), (core1, w)):
        slab(img, x0, 22, x1, 50, TEAL)                                 # parapet
        fill(img, x0 + 4, 26, x1 - 4, 44, TEAL[3])
        glass_wall(img, x0 + 4, 26, x1 - 4, 44, 7, 5, SKY, TEAL[3])     # skylight panes seen from above
        fill(img, x0, 44, x1, 50, TEAL[2]); hline(img, x0, x1, 44, TEAL[1]); hline(img, x0, x1, 49, TEAL[4])
        fill(img, x0, 50, x1, 132, TEAL[3])
        glass_wall(img, x0 + 6, 50, x1 - 6, 128, 8, 11, SKY, TEAL[3], 2, TEAL)
        for X in (x0, x1 - 6):                                          # corner piers, a lit diamond per floor
            slab(img, X, 50, X + 6, 140, TEAL)
            for Y in range(56, 132, 13):
                px(img, X + 2, Y, WHITE[0]); px(img, X + 3, Y, WHITE[0]); px(img, X + 2, Y + 1, SKY[1]); px(img, X + 3, Y - 1, SKY[1])
        # shop floor: display windows under striped awnings
        fill(img, x0 + 6, 128, x1 - 6, 152, TEAL[4])
        n = 2
        bw = (x1 - x0 - 12 - (n - 1) * 4) // n
        for k in range(n):
            X = x0 + 6 + k * (bw + 4)
            window(img, X, 134, bw, 16, TEAL[4], SKY)
            awning(img, X - 1, 128, bw + 2, 6, RED if x0 == 0 else YELLOW)
    # core: a flat roof, the emblem drum, the face
    slab(img, core0, 0, core1, 26, BLUE)
    fill(img, core0 + 4, 4, core1 - 4, 20, BLUE[3])
    for Y in range(6, 19, 4):                                            # roof plant: louvres
        hline(img, core0 + 8, core1 - 8, Y, BLUE[1])
        hline(img, core0 + 8, core1 - 8, Y + 1, BLUE[4])
    fill(img, core0, 20, core1, 26, BLUE[2]); hline(img, core0, core1, 20, BLUE[1]); hline(img, core0, core1, 25, BLUE[4])
    fill(img, core0, 26, core1, 152, BLUE[3])
    vline(img, core0, 26, 152, BLUE[1]); vline(img, core1 - 1, 26, 152, BLUE[4])
    # the emblem: a white arc on a deep disc, three ticks, set in a lit panel
    cx, cy = (core0 + core1) / 2, 50
    slab(img, core0 + 12, 28, core1 - 12, 70, BLUE)
    for y in range(28, 70):
        for x in range(core0 + 12, core1 - 12):
            d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
            if d <= 18:
                px(img, x, y, BLUE[4] if d > 16.5 else BLUE[3])
            if 9 <= d <= 14 and y + 0.5 < cy + 2:
                px(img, x, y, WHITE[0] if x < cx else WHITE[1])
    for ang in (-150, -90, -30):
        a = np.radians(ang)
        for r in np.arange(3, 8, 0.5):
            px(img, int(cx + r * np.cos(a)), int(cy + 1 + r * np.sin(a)), WHITE[0])
    fill(img, int(cx) - 2, int(cy) - 1, int(cx) + 2, int(cy) + 3, WHITE[1])
    # white window bands up the middle
    for Y in range(76, 120, 12):
        slab(img, core0 + 18, Y, core1 - 18, Y + 8, WHITE)
        window(img, core0 + 21, Y + 2, core1 - core0 - 42, 4, BLUE[4], SKY)
    # banners: yellow left, red right, hanging from rods, cut to a point
    for (bx, r, mark) in ((core0 + 3, YELLOW, RED[2]), (core1 - 15, RED, YELLOW[1])):
        hline(img, bx - 1, bx + 13, 72, GREY[3])
        for y in range(73, 124):
            tip = max(0, y - 118)
            fill(img, bx + tip, y, bx + 12 - tip, y + 1, r[1])
            px(img, bx + tip, y, r[0]); px(img, bx + 11 - tip, y, r[2])
        for k, Y in enumerate(range(78, 116, 9)):                        # the banner's glyphs
            g = GLYPHS[(k + (bx > 100)) % len(GLYPHS)]
            for gy, row in enumerate(g):
                for gx, v in enumerate(row):
                    if v == '1':
                        px(img, bx + 3 + gx, Y + gy, mark)
    # canopy with the store's name, glass doors under it
    slab(img, core0 - 2, 122, core1 + 2, 132, TEAL)
    s = 'DEPT. STORE'
    text(img, s, int(cx - text_width(s) / 2), 124, WHITE[0], TEAL[4])
    fill(img, core0 - 2, 132, core1 + 2, 134, TEAL[4])
    double_door(img, int(cx) - 16, 134, 32, 18, BLUE[4], SKY)
    window(img, core0 + 4, 136, 10, 14, BLUE[4], SKY)
    window(img, core1 - 14, 136, 10, 14, BLUE[4], SKY)
    # plinth along the whole front
    fill(img, 0, 152, w, 160, GREY[2]); hline(img, 0, w, 152, GREY[1]); hline(img, 0, w, 159, GREY[3])
    fill(img, int(cx) - 18, 152, int(cx) + 18, 160, GREY[1])            # the entrance step
    hline(img, int(cx) - 18, int(cx) + 18, 156, GREY[2])
    outline(img)
    return img

# ----------------------------------------------------------------------------- Pokemon Hotel
def potted(img, x, y, r=LIME):
    """A potted shrub, 10 x 12, its foot at (x, y)."""
    fill(img, x + 2, y - 5, x + 8, y, ORANGE[2]); hline(img, x + 2, x + 8, y - 5, ORANGE[1]); vline(img, x + 7, y - 4, y, ORANGE[3])
    for yy in range(y - 12, y - 4):
        for xx in range(x, x + 10):
            d = ((xx + 0.5 - (x + 5)) / 5) ** 2 + ((yy + 0.5 - (y - 8.5)) / 4) ** 2
            if d <= 1:
                px(img, xx, yy, r[1] if (xx - x) + (yy - (y - 12)) < 7 else r[2])
    px(img, x + 3, y - 10, r[0]); px(img, x + 6, y - 6, r[3])

def hotel():
    """144 x 160. HGSS's Condominiums (model 244), now the Pokemon Hotel: tan wings either
    side of a glass bay in teal, its floors ringed in lime with HGSS's purple strip up the
    middle; a dark teal louvred roof with the sign panel; the hotel's canopy and doors."""
    w, h = 144, 160
    img = canvas(w, h)
    b0, b1 = 50, 94                                                  # the bay
    # roof: dark teal, louvres either side of a light sign panel
    slab(img, 0, 0, w, 34, DTEAL)
    for (x0, x1) in ((6, b0 - 2), (b1 + 2, w - 6)):
        fill(img, x0, 5, x1, 27, DTEAL[3])
        for Y in range(7, 26, 3):
            hline(img, x0 + 1, x1 - 1, Y, DTEAL[1])
    slab(img, b0, 4, b1, 26, GREY)
    for Y in range(8, 24, 3):
        hline(img, b0 + 4, b1 - 4, Y, GREY[2])
    fill(img, 0, 28, w, 34, DTEAL[2]); hline(img, 0, w, 28, DTEAL[1]); hline(img, 0, w, 33, DTEAL[4])
    # tan wings: five floors of windows
    fill(img, 0, 34, w, 150, TAN[2])
    vline(img, 0, 34, 150, TAN[1]); vline(img, w - 1, 34, 150, TAN[4])
    for Y in range(34, 150, 4):
        for X in range(2 + (Y // 4) % 2 * 4, w, 8):
            px(img, X, Y + 2, TAN[3])                                # a fine render texture
    for f, Y in enumerate(range(40, 130, 18)):
        hline(img, 0, w, Y + 15, TAN[1]); hline(img, 0, w, Y + 16, TAN[3])   # floor lines
        for X in (8, 28, b1 + 8, b1 + 28):
            window(img, X, Y, 14, 11, DTEAL[4], SKY, TAN[0])
    # the bay: teal glass, lime floor rings, purple strip
    fill(img, b0, 30, b1, 150, DTEAL[3])
    vline(img, b0, 30, 150, DTEAL[1]); vline(img, b1 - 1, 30, 150, DTEAL[4])
    glass_wall(img, b0 + 3, 36, b1 - 3, 126, 9, 7, SKY, DTEAL[3], 2, LIME)
    fill(img, (b0 + b1) // 2 - 2, 34, (b0 + b1) // 2 + 2, 128, VIOLET[2])
    vline(img, (b0 + b1) // 2 - 2, 34, 128, VIOLET[1])
    # the canopy, the sign, the doors, plants either side
    slab(img, b0 - 8, 122, b1 + 8, 133, DTEAL)
    s = 'HOTEL'
    text(img, s, (b0 + b1) // 2 - text_width(s) // 2, 125, WHITE[0], DTEAL[4])
    double_door(img, (b0 + b1) // 2 - 13, 133, 26, 17, DTEAL[4], SKY)
    potted(img, b0 - 8, 150); potted(img, b1 - 2, 150)
    fill(img, 0, 150, w, 160, GREY[2]); hline(img, 0, w, 150, GREY[1]); hline(img, 0, w, 159, GREY[3])
    fill(img, (b0 + b1) // 2 - 16, 150, (b0 + b1) // 2 + 16, 160, GREY[1])
    outline(img)
    return img

# ----------------------------------------------------------------------------- Apartments
def apartments():
    """112 x 160. HGSS's cream tower (model 238), the apartments: a cream tower stepped back
    at the top, its plant room louvred, ribbon windows over purple bands; a violet annex at
    its east foot with its own door."""
    w, h = 112, 160
    img = canvas(w, h)
    t1 = 80                                                          # the tower's east face
    # roof plant room and the tower's roof
    slab(img, 0, 16, t1, 36, CREAM)
    slab(img, 6, 0, t1 - 18, 22, CREAM)
    for Y in range(3, 20, 3):
        hline(img, 9, t1 - 21, Y, CREAM[3])
    fill(img, 0, 30, t1, 36, CREAM[2]); hline(img, 0, t1, 30, CREAM[1]); hline(img, 0, t1, 35, CREAM[4])
    # tower face: six floors, ribbon windows, purple bands
    fill(img, 0, 36, t1, 150, CREAM[1])
    vline(img, 0, 36, 150, CREAM[0]); vline(img, t1 - 1, 36, 150, CREAM[3])
    for f, Y in enumerate(range(40, 136, 16)):
        window(img, 8, Y, t1 - 16, 9, VIOLET[4], SKY)
        for X in range(8 + 16, t1 - 8, 16):
            vline(img, X, Y, Y + 9, VIOLET[4])                       # mullions
        fill(img, 0, Y + 11, t1, Y + 14, VIOLET[2]); hline(img, 0, t1, Y + 11, VIOLET[1]); hline(img, 0, t1, Y + 13, VIOLET[3])
    # the annex
    slab(img, t1, 70, w, 84, VIOLET)
    fill(img, t1 + 3, 73, w - 3, 81, VIOLET[3])
    fill(img, t1, 84, w, 150, VIOLET[2])
    vline(img, w - 1, 84, 150, VIOLET[4])
    for Y in (90, 110):
        window(img, t1 + 6, Y, 9, 10, VIOLET[4], SKY, VIOLET[1])
        window(img, t1 + 18, Y, 9, 10, VIOLET[4], SKY, VIOLET[1])
    fill(img, t1 + 9, 130, t1 + 23, 150, VIOLET[4]); fill(img, t1 + 10, 131, t1 + 22, 150, DTEAL[3])
    hline(img, t1 + 10, t1 + 22, 131, DTEAL[1]); px(img, t1 + 20, 141, GOLD[1])
    # the tower's entrance
    slab(img, 18, 128, t1 - 18, 135, CREAM)
    double_door(img, t1 // 2 - 11, 135, 22, 15, VIOLET[4], SKY)
    fill(img, 0, 150, w, 160, GREY[2]); hline(img, 0, w, 150, GREY[1]); hline(img, 0, w, 159, GREY[3])
    outline(img)
    return img

# ----------------------------------------------------------------------------- Game Corner
SEVEN = ["111111", "000011", "000110", "001100", "001100", "001100", "001100"]

def bulbs(img, x0, x1, y, phase=0):
    for x in range(x0, x1):
        if (x + phase) % 3 == 0:
            px(img, x, y, GOLD[0] if ((x + phase) // 3) % 2 else WHITE[0])
        elif (x + phase) % 3 == 1:
            px(img, x, y, GOLD[2])

def game_corner():
    """192 x 136. HGSS's Game Corner (model 241) with Celadon's thrill turned up: the glass
    roof in a black-purple parapet, a neon band of chasing bulbs, the arched entrance in blue
    with a pink neon edge and gold doors, white chevrons either side, lit pilasters, and the
    marquee on the roof."""
    w, h = 192, 136
    img = canvas(w, h)
    top = 30
    # roof: parapet and glass
    slab(img, 0, top, w, top + 38, PURPLE)
    fill(img, 6, top + 4, w - 6, top + 32, PURPLE[4])
    glass_wall(img, 6, top + 4, w - 6, top + 32, 11, 6, SKY, PURPLE[3])
    # neon eave: lavender tube with chasing bulbs, a pink line under it
    fill(img, 0, top + 38, w, top + 46, NEON[1]); hline(img, 0, w, top + 38, NEON[0]); hline(img, 0, w, top + 45, NEON[2])
    bulbs(img, 1, w - 1, top + 41); bulbs(img, 1, w - 1, top + 42, 1)
    hline(img, 0, w, top + 46, PINK[1]); hline(img, 0, w, top + 47, PURPLE[4])
    # the facade
    y0, y1 = top + 48, 128
    fill(img, 0, y0, w, y1, PURPLE[3])
    for Y in range(y0, y1, 2):
        for X in range(0, w, 4):
            px(img, X + (Y // 2) % 2 * 2, Y, PURPLE[2])              # a sequinned dark wall
    cx = w // 2
    # panels either side: a slot-reel window of sevens over HGSS's white chevrons
    for (x0, x1) in ((14, 66), (w - 66, w - 14)):
        fill(img, x0, y0 + 4, x1, y1 - 4, PURPLE[4])
        frame(img, x0, y0 + 4, x1, y1 - 4, VIOLET[1])
        rx = x0 + 5
        slab(img, x0 + 3, y0 + 7, x1 - 3, y0 + 21, GOLD)
        for k in range(3):                                           # three reels, a seven on each
            X = rx + k * 14
            fill(img, X, y0 + 9, X + 12, y0 + 19, WHITE[1]); hline(img, X, X + 12, y0 + 9, WHITE[0])
            hline(img, X, X + 12, y0 + 18, WHITE[3])
            for gy, row in enumerate(SEVEN):
                for gx, v in enumerate(row):
                    if v == '1':
                        px(img, X + 3 + gx, y0 + 10 + gy, RED[2])
        for k in range(2):                                           # chevrons, bold and white
            cy0 = y0 + 25 + k * 11
            for i in range(x1 - x0 - 8):
                X = x0 + 4 + i
                d = abs(((i + 6) % 12) - 6)
                for t in range(3):
                    px(img, X, cy0 + d + t, (WHITE[0], VIOLET[0], VIOLET[2])[t])
    for (sx, sy) in ((8, y0 + 3), (w - 9, y0 + 3), (cx - 30, y0 - 2), (cx + 29, y0 - 2)):   # sparkles
        for d in range(-2, 3):
            px(img, sx + d, sy, WHITE[0] if abs(d) < 2 else GOLD[0]); px(img, sx, sy + d, WHITE[0] if abs(d) < 2 else GOLD[0])
    # pilasters with lights
    for X in (4, 70, w - 76, w - 10):
        slab(img, X, y0, X + 6, y1, VIOLET)
        for Y in range(y0 + 3, y1 - 2, 5):
            px(img, X + 2, Y, GOLD[0]); px(img, X + 3, Y, GOLD[1]); px(img, X + 2, Y + 1, GOLD[2])
    # the arch: stepped hard-edged arch in blue, pink neon edge, gold doors, a red carpet
    a0, a1, ay = cx - 22, cx + 22, y0 - 6
    for y in range(ay, y1):
        for x in range(a0, a1):
            dx = abs(x + 0.5 - cx)
            r = 22
            top_y = ay + (r - (max(r * r - dx * dx, 0)) ** 0.5) * 0.6
            if y >= top_y:
                inner = dx < 14 and y >= ay + 10 + (14 - (max(196 - dx * dx, 0)) ** 0.5) * 0.6
                px(img, x, y, (GOLD[1] if dx < 12 else GOLD[2]) if inner else (BLUE[2] if x < cx else BLUE[3]))
    for x in range(a0, a1):                                           # neon edge along the arch's crown
        for y in range(ay, y1):
            if img[y, x, 3] and tuple(img[y, x, :3]) in (BLUE[2], BLUE[3]):
                if y == ay or not img[y - 1, x, 3] or tuple(img[y - 1, x, :3]) not in (BLUE[2], BLUE[3]):
                    px(img, x, y, PINK[1]); px(img, x, y + 1, PINK[0] if x < cx else PINK[2])
                break
    for y in range(ay + 10, y1):                                      # the inner arch's edge
        for x in range(cx - 14, cx + 14):
            if tuple(img[y, x, :3]) in (GOLD[1], GOLD[2]):
                if tuple(img[y, x - 1, :3]) in (BLUE[2], BLUE[3]) or tuple(img[y - 1, x, :3]) in (BLUE[2], BLUE[3]):
                    px(img, x, y, NEON[0])
    vline(img, cx, y0 + 12, y1, GOLD[3])                              # the doors' meeting line
    for x in (cx - 9, cx + 8):
        vline(img, x, y0 + 20, y0 + 26, GOLD[3])
    fill(img, cx - 10, y1 - 2, cx + 10, y1, RED[2])
    # plinth and the carpet out to the step
    fill(img, 0, y1, w, h, PURPLE[2]); hline(img, 0, w, y1, VIOLET[1]); hline(img, 0, w, h - 1, PURPLE[4])
    fill(img, cx - 10, y1, cx + 10, h, RED[2]); vline(img, cx - 10, y1, h, RED[1]); vline(img, cx + 9, y1, h, RED[3])
    # the marquee on the roof
    mx0, mx1 = cx - 52, cx + 52
    for X in (mx0 + 10, mx1 - 12):                                     # struts
        fill(img, X, 22, X + 2, top + 6, GREY[3]); vline(img, X, 22, top + 6, GREY[2])
    slab(img, mx0, 0, mx1, 24, PURPLE)
    fill(img, mx0 + 3, 3, mx1 - 3, 21, PURPLE[4])
    bulbs(img, mx0 + 1, mx1 - 1, 1); bulbs(img, mx0 + 1, mx1 - 1, 22, 1)
    for Y in range(2, 22):
        if Y % 3 == 0:
            px(img, mx0 + 1, Y, GOLD[0]); px(img, mx1 - 2, Y, GOLD[1])
    s = 'GAME CORNER'
    text(img, s, cx - text_width(s) // 2, 9, PINK[0], PINK[2])
    for X in (mx0 + 9, mx1 - 10):                                     # coins
        for y in range(6, 18):
            for x in range(X - 6, X + 7):
                d = ((x + 0.5 - X) ** 2 + (y + 0.5 - 12) ** 2) ** 0.5
                if d <= 5.5:
                    px(img, x, y, GOLD[3] if d > 4.5 else GOLD[1] if (x - X) + (y - 12) < 0 else GOLD[2])
        vline(img, X, 9, 15, GOLD[3]); px(img, X - 2, 9, GOLD[0])
    outline(img)
    # bulbs and the neon stay bright on the outline
    return img

# ----------------------------------------------------------------------------- Prize corner
def prize_corner():
    """80 x 80. HGSS's prize corner (model 240): a purple grille roof, the neon band, lilac
    walls with a window of prizes, the orange door."""
    w, h = 80, 80
    img = canvas(w, h)
    slab(img, 0, 6, w, 36, PURPLE)
    fill(img, 5, 10, w - 5, 31, PURPLE[4])
    for X in range(8, w - 6, 5):
        fill(img, X, 11, X + 2, 30, VIOLET[2]); vline(img, X, 11, 30, VIOLET[1])
    fill(img, 0, 36, w, 42, NEON[1]); hline(img, 0, w, 36, NEON[0]); hline(img, 0, w, 41, NEON[2])
    bulbs(img, 1, w - 1, 38)
    fill(img, 0, 42, w, 74, VIOLET[1]); vline(img, 0, 42, 74, VIOLET[0]); vline(img, w - 1, 42, 74, VIOLET[3])
    s = 'PRIZES'
    slab(img, 6, 45, 6 + text_width(s) + 6, 54, PURPLE)
    text(img, s, 9, 47, GOLD[0], PURPLE[4])
    window(img, 8, 57, 26, 14, PURPLE[4], SKY)
    for i, c in enumerate((PINK[1], GOLD[1], LIME[1])):              # prizes in the window
        fill(img, 11 + i * 8, 64, 16 + i * 8, 70, c); px(img, 12 + i * 8, 65, WHITE[0])
    fill(img, 48, 52, 66, 74, PURPLE[4]); fill(img, 49, 53, 65, 74, ORANGE[2])
    hline(img, 49, 65, 53, ORANGE[1]); vline(img, 64, 54, 74, ORANGE[3]); px(img, 52, 63, GOLD[0])
    fill(img, 0, 74, w, 80, PURPLE[2]); hline(img, 0, w, 74, VIOLET[1]); hline(img, 0, w, 79, PURPLE[4])
    outline(img)
    return img

# ----------------------------------------------------------------------------- cottages
ROOFS = dict(red=[(255, 176, 152), (232, 104, 88), (192, 64, 64), (136, 40, 48), (96, 32, 40)],
             green=[(184, 232, 136), (120, 192, 96), (72, 152, 80), (48, 112, 64), (32, 72, 48)],
             orange=[(255, 216, 144), (240, 160, 80), (208, 112, 48), (152, 80, 40), (104, 56, 32)],
             teal=[(160, 232, 224), (88, 192, 192), (48, 144, 160), (32, 104, 120), (24, 72, 88)],
             brown=[(232, 184, 128), (200, 136, 80), (160, 96, 56), (120, 72, 48), (80, 48, 32)])
TIMBER = [(200, 152, 104), (160, 112, 72), (120, 80, 56), (88, 56, 40)]
PLASTER = [(255, 252, 236), (248, 236, 208), (224, 208, 176), (184, 168, 136)]
STONE = [(224, 224, 216), (192, 192, 184), (152, 152, 144), (112, 112, 112)]

def roof(img, x0, x1, y0, y1, r, gable=False):
    """A Gen 3 pitched roof seen from above the front: the front slope tall, shingle rows
    staggered, a lit ridge, verges flaring a pixel every few rows, the eave dark under it."""
    hgt = y1 - y0
    for y in range(y0, y1):
        k = (y - y0) * 4 // hgt                                     # verges flare out toward the eave
        a, b = x0 + 3 - k, x1 - 3 + k
        fill(img, a, y, b, y + 1, r[2])
        px(img, a, y, r[3]); px(img, b - 1, y, r[3])
    for y in range(y0 + 4, y1 - 2, 4):                              # shingle rows
        k = (y - y0) * 4 // hgt
        hline(img, x0 + 4 - k, x1 - 4 + k, y, r[3])
        for x in range(x0 + 4 - k + ((y // 4) % 2) * 3, x1 - 4 + k, 6):
            vline(img, x, y - 3, y, r[3])
            px(img, x + 1, y - 3, r[1])
        hline(img, x0 + 4 - k, x1 - 4 + k, y + 1, r[1])
    fill(img, x0 + 3, y0, x1 - 3, y0 + 3, r[1]); hline(img, x0 + 3, x1 - 3, y0, r[0])   # ridge
    fill(img, x0 - 1, y1 - 2, x1 + 1, y1, r[3]); hline(img, x0 - 1, x1 + 1, y1 - 1, r[4])  # eave board
    if gable:                                                        # a front gable over the door
        gx0, gx1 = gable
        gc = (gx0 + gx1) / 2
        for y in range(y0 + 6, y1 - 1):
            half = (y - (y0 + 6)) * (gx1 - gx0) / 2 / (y1 - 1 - (y0 + 6))
            a, b = int(gc - half), int(gc + half)
            fill(img, a, y, b, y + 1, PLASTER[1])
            px(img, a, y, r[3]); px(img, a - 1, y, r[1]); px(img, b, y, r[3]); px(img, b - 1, y, r[2])
        window(img, int(gc) - 4, y1 - 13, 8, 8, TIMBER[3], SKY)

def cottage(kind='red', chimney=False, gable=False, boxes=True, w=64):
    """64 x 72 (4 x 4.5 cells), the cafe's kind: a tall shingled roof in one of Celadon's
    colours, a timber frame on cream plaster, a wooden door, windows with flower boxes, a
    stone plinth."""
    h = 72
    img = canvas(w, h)
    r = ROOFS[kind]
    if chimney:
        slab(img, w - 20, 0, w - 12, 14, STONE); fill(img, w - 21, 0, w - 11, 3, STONE[2]); hline(img, w - 21, w - 11, 0, STONE[0])
    roof(img, 2, w - 2, 4, 44, r, gable=(w // 2 - 12, w // 2 + 12) if gable else False)
    # walls
    fill(img, 3, 44, w - 3, 66, PLASTER[1])
    vline(img, 3, 44, 66, PLASTER[0]); vline(img, w - 4, 44, 66, PLASTER[3])
    fill(img, 3, 44, w - 3, 47, TIMBER[1]); hline(img, 3, w - 3, 44, TIMBER[0]); hline(img, 3, w - 3, 46, TIMBER[3])
    for X in (3, w // 2 - 9, w // 2 + 7, w - 7):
        fill(img, X, 47, X + 3, 66, TIMBER[1]); vline(img, X, 47, 66, TIMBER[0]); vline(img, X + 2, 47, 66, TIMBER[2])
    # door
    dx = w // 2 - 6
    fill(img, dx, 50, dx + 12, 66, TIMBER[3]); fill(img, dx + 1, 51, dx + 11, 66, TIMBER[1])
    vline(img, dx + 6, 51, 66, TIMBER[2]); hline(img, dx + 1, dx + 11, 51, TIMBER[0]); px(img, dx + 9, 58, GOLD[1])
    # windows and boxes
    for X in (9, w - 21):
        window(img, X, 50, 12, 10, TIMBER[3], SKY)
        vline(img, X + 6, 51, 59, TIMBER[3])
        if boxes:
            fill(img, X - 1, 60, X + 13, 63, TIMBER[2]); hline(img, X - 1, X + 13, 60, TIMBER[1])
            for k, c in enumerate((RED[1], GOLD[1], PINK[1], RED[1], GOLD[1])):
                px(img, X + 1 + k * 2 + (k > 2), 59, c); px(img, X + 2 + k * 2 + (k > 2), 59, LIME[2])
    # plinth
    fill(img, 1, 66, w - 1, 72, STONE[1]); hline(img, 1, w - 1, 66, STONE[0]); hline(img, 1, w - 1, 71, STONE[3])
    fill(img, dx - 1, 66, dx + 13, 70, STONE[0]); hline(img, dx - 1, dx + 13, 69, STONE[2])  # the step
    outline(img)
    return img

def cafe():
    """80 x 72: the cafe (HGSS's restaurant, model 243): a brown shingled roof with its
    chimney, a striped awning over a wide window, the green door, the sign."""
    w, h = 80, 72
    img = canvas(w, h)
    slab(img, 10, 0, 20, 16, STONE); fill(img, 9, 0, 21, 3, STONE[2]); hline(img, 9, 21, 0, STONE[0])
    roof(img, 2, w - 2, 4, 42, ROOFS['brown'])
    fill(img, 3, 42, w - 3, 66, PLASTER[1])
    vline(img, 3, 42, 66, PLASTER[0]); vline(img, w - 4, 42, 66, PLASTER[3])
    fill(img, 3, 42, w - 3, 45, TIMBER[1]); hline(img, 3, w - 3, 42, TIMBER[0]); hline(img, 3, w - 3, 44, TIMBER[3])
    for X in (3, 40, w - 7):
        fill(img, X, 45, X + 3, 66, TIMBER[1]); vline(img, X, 45, 66, TIMBER[0]); vline(img, X + 2, 45, 66, TIMBER[2])
    s = 'CAFE'
    slab(img, 22 - (text_width(s) + 6) // 2, 45, 22 + (text_width(s) + 6) // 2 + 1, 53, TIMBER)
    text(img, s, 22 - text_width(s) // 2, 46, PLASTER[0], TIMBER[3])
    awning(img, 7, 54, 30, 5, YELLOW)
    window(img, 8, 59, 28, 7, TIMBER[3], SKY)
    fill(img, 50, 48, 66, 66, TIMBER[3]); fill(img, 51, 49, 65, 66, GREEN[2])
    hline(img, 51, 65, 49, GREEN[1]); vline(img, 58, 50, 66, GREEN[3]); window(img, 53, 51, 4, 6, GREEN[3], SKY); window(img, 59, 51, 4, 6, GREEN[3], SKY)
    px(img, 56, 58, GOLD[1])
    potted(img, 67, 66)
    fill(img, 1, 66, w - 1, 72, STONE[1]); hline(img, 1, w - 1, 66, STONE[0]); hline(img, 1, w - 1, 71, STONE[3])
    outline(img)
    return img

if __name__ == '__main__':
    import sys
    from PIL import Image
    out = sys.argv[1] if len(sys.argv) > 1 else 'kit.png'
    pieces = [dept_store(), apartments(), hotel(), game_corner(), prize_corner(), cafe()] + \
             [cottage(k, chimney=i % 2 == 0, gable=i % 3 == 1) for i, k in enumerate(('red', 'green', 'orange', 'teal'))]
    W = sum(p.shape[1] for p in pieces) + 8 * (len(pieces) + 1)
    H = max(p.shape[0] for p in pieces) + 16
    sheet = np.zeros((H, W, 4), np.uint8); sheet[..., :3] = (112, 200, 160); sheet[..., 3] = 255
    x = 8
    for p in pieces:
        a = p[..., 3] > 0
        sheet[8:8 + p.shape[0], x:x + p.shape[1]][a] = p[a]
        x += p.shape[1] + 8
    Image.fromarray(sheet).resize((W * 3, H * 3), Image.Resampling.NEAREST).save(out)
