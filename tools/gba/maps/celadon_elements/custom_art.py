"""Celadon's own props, drawn as Gen 3 pixel art: market stalls, street lamps, the plaza
fountain and the Game Corner's marquee.

Nothing here is a shrunk render. Each piece is drawn shape by shape the way a Gen 3 artist
draws one: a light from the upper left, a three- or four-step ramp per material, one-pixel
highlights on the lit edges, a dark line where two parts meet and C06's outline colour round
the silhouette. Celadon's themes: the Rainbow City (the market's awnings), its green (the
lamps' iron), the canal's water (the fountain).

    stall(colour)   48 x 56: a striped awning with a scalloped valance, two timber posts,
                    a counter of crates with produce (apples, oranges, greens, lemons)
    lamp()          16 x 48: a green iron lamp, a fluted post on a stepped base, a glass
                    lantern lit warm, a crown and finial
    fountain()      80 x 64: a two-tier stone fountain in an octagonal basin, its water
                    rippled, jets rising from the upper bowl and falling as spray
    marquee()       96 x 28: the Game Corner's sign, a lit bulb border round a dark board,
                    GAME CORNER in pink and gold, a coin at each end
"""
from __future__ import annotations
import numpy as np

OUT = (41, 41, 49)                        # C06's outline

def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)

def px(img, x, y, c):
    if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
        img[y, x, :3] = c
        img[y, x, 3] = 255

def rect(img, x0, y0, x1, y1, c):
    img[max(y0, 0):y1, max(x0, 0):x1, :3] = c
    img[max(y0, 0):y1, max(x0, 0):x1, 3] = 255

def disc(img, cx, cy, r, ramp):
    """A lit ball: ramp light to dark, lit from the upper left, a highlight pixel."""
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r:
                lit = ((x - cx) * -0.7 + (y - cy) * -0.7) / max(r, 1)
                i = 1 if lit > 0.25 else 2 if lit > -0.45 else 3
                px(img, x, y, ramp[i])
    px(img, int(round(cx - r * 0.45)), int(round(cy - r * 0.45)), ramp[0])

def fruit(img, cx, cy, r, ramp):
    """A lit ball with its own outline in its ramp's darkest shade."""
    for y in range(int(cy - r - 2), int(cy + r + 3)):
        for x in range(int(cx - r - 2), int(cx + r + 3)):
            d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
            if d <= r + 1:
                px(img, x, y, ramp[3])
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
            if d <= r:
                lit = ((x + 0.5 - cx) * -0.7 + (y + 0.5 - cy) * -0.7) / r
                px(img, x, y, ramp[1] if lit > -0.3 else ramp[2])
    px(img, int(cx - r * 0.4), int(cy - r * 0.4), ramp[0])

def outline(img, c=OUT):
    a = img[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[edge, :3] = c

# --------------------------------------------------------------------------- stall
AWNING = dict(red=[(255, 168, 152), (240, 96, 88), (200, 56, 64), (136, 32, 48)],
              orange=[(255, 216, 136), (248, 160, 56), (216, 112, 32), (152, 72, 24)],
              green=[(184, 240, 136), (112, 208, 88), (64, 160, 64), (32, 104, 56)],
              blue=[(168, 224, 255), (88, 168, 240), (48, 112, 200), (32, 64, 136)],
              violet=[(232, 184, 255), (184, 120, 240), (136, 72, 200), (88, 40, 136)])
CREAM = [(255, 255, 240), (248, 240, 208), (216, 200, 168), (160, 144, 120)]
WOOD = [(232, 184, 120), (200, 144, 88), (160, 104, 64), (112, 72, 48)]
APPLE = [(255, 200, 192), (240, 64, 64), (192, 32, 48), (128, 24, 40)]
ORANGE = [(255, 232, 160), (248, 168, 48), (216, 120, 32), (152, 80, 24)]
GREENS = [(208, 248, 152), (120, 208, 72), (72, 152, 56), (40, 96, 48)]
LEMON = [(255, 255, 200), (248, 232, 96), (216, 184, 48), (160, 128, 40)]

def stall(colour='red'):
    w, h = 48, 56
    img = canvas(w, h)
    A = AWNING[colour]
    # posts behind the counter, then the counter, then the awning over all
    for x0 in (4, 41):
        rect(img, x0, 18, x0 + 3, 44, WOOD[2])
        rect(img, x0, 18, x0 + 1, 44, WOOD[1])
    # counter: crate top (lit plank) and front (planks, dark seams)
    rect(img, 2, 33, 46, 37, WOOD[1])
    rect(img, 2, 33, 46, 34, WOOD[0])
    rect(img, 2, 37, 46, 50, WOOD[2])
    for y in (41, 45):
        rect(img, 2, y, 46, y + 1, WOOD[3])
    for x in (2, 13, 24, 35, 45):
        rect(img, x, 37, x + 1, 50, WOOD[3])
    for x in (3, 14, 25, 36):
        rect(img, x, 38, x + 1, 41, WOOD[1])                       # lit plank ends
    # produce heaped in four crates on the counter, each fruit outlined in its own darkest
    # shade so the heap reads as separate fruit
    for i, ramp in enumerate((APPLE, ORANGE, GREENS, LEMON)):
        x0 = 3 + i * 11
        rect(img, x0, 30, x0 + 10, 34, WOOD[3])                    # crate
        rect(img, x0 + 1, 31, x0 + 9, 33, WOOD[2])
        rect(img, x0 + 1, 30, x0 + 9, 31, WOOD[1])
        for (cx, cy) in ((x0 + 5, 24.5), (x0 + 2.5, 27.5), (x0 + 7.5, 27.5)):
            fruit(img, cx, cy, 2.6, ramp)
        if ramp is APPLE or ramp is ORANGE:
            px(img, x0 + 5, 21, (88, 136, 56)); px(img, x0 + 6, 21, (120, 184, 72))  # a leaf on top
    # awning: a sloped top in stripes, a scalloped valance
    stripe = lambda x: (x // 6) % 2 == 0
    for y in range(0, 12):
        inset = (11 - y) // 3                                       # the top narrows to the back
        for x in range(inset, w - inset):
            c = (A if stripe(x) else CREAM)[1 if y < 3 else 2 if y > 9 else 1]
            px(img, x, y, c)
    for x in range(1, w - 1):
        px(img, x, 0 + (1 if x < 3 or x > w - 4 else 0), (A if stripe(x) else CREAM)[0])
    for y in range(12, 18):
        for x in range(0, w):
            c = (A if stripe(x) else CREAM)[2 if y < 14 else 1]
            px(img, x, y, c)
    for x in range(0, w):
        px(img, x, 12, (A if stripe(x) else CREAM)[3])              # the fold between top and valance
    for k in range(0, w, 6):                                        # scallops
        for dx in range(6):
            depth = [1, 2, 3, 3, 2, 1][dx]
            for dy in range(depth):
                px(img, k + dx, 18 + dy, (A if stripe(k + dx) else CREAM)[2 if dy < depth - 1 else 3])
    # a hanging price board in the middle of the valance
    rect(img, 19, 19, 29, 25, WOOD[3])
    rect(img, 20, 20, 28, 24, (56, 72, 64))
    for x in (21, 23, 26):
        px(img, x, 22, CREAM[0])
    px(img, 24, 21, LEMON[1]); px(img, 25, 22, LEMON[1])
    outline(img)
    return img

# --------------------------------------------------------------------------- lamp
IRON = [(128, 184, 168), (72, 128, 120), (40, 88, 88), (24, 56, 64)]
GLOW = [(255, 255, 224), (255, 240, 152), (248, 208, 88), (216, 152, 56)]

def lamp():
    w, h = 16, 48
    img = canvas(w, h)
    # stepped base
    rect(img, 4, 42, 12, 47, IRON[2]); rect(img, 4, 42, 6, 47, IRON[1])
    rect(img, 5, 39, 11, 42, IRON[2]); rect(img, 5, 39, 6, 42, IRON[1])
    rect(img, 3, 46, 13, 48, IRON[3])
    # fluted post
    rect(img, 7, 15, 9, 39, IRON[2]); rect(img, 7, 15, 8, 39, IRON[1])
    rect(img, 6, 24, 10, 26, IRON[2]); rect(img, 6, 24, 7, 26, IRON[1])     # a collar
    # lantern: cap, glass panes lit, frame
    rect(img, 3, 3, 13, 5, IRON[2]); rect(img, 4, 2, 12, 3, IRON[1])
    rect(img, 7, 0, 9, 2, IRON[1])                                          # finial
    rect(img, 4, 5, 12, 13, IRON[3])
    rect(img, 5, 6, 11, 12, GLOW[1])
    rect(img, 5, 6, 7, 9, GLOW[0])
    rect(img, 9, 9, 11, 12, GLOW[2])
    rect(img, 8, 6, 9, 12, IRON[3])                                         # the frame's mullion
    rect(img, 5, 13, 11, 15, IRON[2]); rect(img, 6, 13, 7, 15, IRON[1])
    outline(img)
    return img

# --------------------------------------------------------------------------- fountain
STONE = [(248, 244, 224), (224, 216, 192), (184, 176, 152), (136, 128, 112)]
WATER = [(224, 248, 255), (136, 216, 248), (80, 168, 232), (48, 112, 200)]

def fountain():
    w, h = 80, 64
    img = canvas(w, h)
    cx = w / 2
    # octagonal basin: rim (top lit), inner wall, water, front face
    def octagon(rx, ry, cy):
        out = []
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                dx, dy = abs(x + 0.5 - cx) / rx, abs(y + 0.5 - cy) / ry
                if dx <= 1 and dy <= 1 and dx + dy <= 1.45:
                    out.append((x, y))
        return out
    for x, y in octagon(39, 15, 44):
        px(img, x, y, STONE[1])
    for x, y in octagon(39, 15, 50):                                         # the basin's front face
        if y > 44:
            px(img, x, y, STONE[2] if y < 59 else STONE[3])
    for x, y in octagon(39, 15, 44):
        px(img, x, y, STONE[1] if y < 44 else STONE[1])
    for x, y in octagon(35, 12, 44):
        px(img, x, y, WATER[2])
    for x, y in octagon(35, 12, 44):
        if y < 37:
            px(img, x, y, WATER[3])                                          # the inner wall's shade on the water
    for (x0, y0, n) in ((14, 46, 6), (52, 49, 5), (22, 52, 4), (58, 42, 4), (30, 40, 3)):
        for k in range(n):
            px(img, x0 + k, y0, WATER[1])
        px(img, x0 + n // 2, y0 - 1, WATER[0])
    # rim highlight along the top edge, blocks on the front face
    for x, y in octagon(39, 15, 44):
        if not any((x, y - 1) == p for p in [(x, y - 1)] if False):
            pass
    top = {}
    for x, y in octagon(39, 15, 44):
        top[x] = min(top.get(x, 99), y)
    for x, y in top.items():
        px(img, x, y, STONE[0])
    for x in range(int(cx - 36), int(cx + 37), 9):
        for y in range(51, 59):
            if img[y, x, 3]:
                px(img, x, y, STONE[3])
    # the pedestal and upper bowl
    rect(img, 35, 22, 45, 44, STONE[2]); rect(img, 35, 22, 38, 44, STONE[1]); rect(img, 44, 22, 45, 44, STONE[3])
    for y in range(18, 24):
        half = 14 - abs(y - 21) * 2 + (2 if y < 21 else 0)
        rect(img, int(cx - half), y, int(cx + half), y + 1, STONE[1] if y < 21 else STONE[2])
    rect(img, int(cx - 13), 17, int(cx + 13), 18, STONE[0])
    rect(img, int(cx - 12), 18, int(cx + 12), 20, WATER[2])
    outline(img)
    # jets and spray
    for x0, peak in ((33, 5), (39, 0), (45, 5)):                           # three jets, lit on the left
        for y in range(peak, 18):
            px(img, x0, y, WATER[0])
            px(img, x0 + 1, y, WATER[1] if y > peak + 1 else WATER[0])
            px(img, x0 + 2, y, WATER[2] if y > peak + 3 else WATER[1])
    for (x, y) in ((28, 10), (30, 6), (32, 3), (48, 3), (50, 6), (52, 10), (26, 16), (54, 16), (24, 24), (56, 24),
                   (22, 30), (58, 30), (20, 36), (60, 36), (37, 2), (43, 2)):
        px(img, x, y, WATER[0]); px(img, x + 1, y + 1, WATER[1])
    for (x, y) in ((21, 38), (59, 38), (19, 40), (61, 40)):                  # splashes where the spray lands
        px(img, x, y, WATER[0]); px(img, x - 1, y, WATER[1]); px(img, x + 1, y, WATER[1])
    return img

# --------------------------------------------------------------------------- marquee
FONT = {  # 5 px tall capitals
    'G': ["01110", "10000", "10011", "10001", "01110"], 'A': ["01110", "10001", "11111", "10001", "10001"],
    'M': ["10001", "11011", "10101", "10001", "10001"], 'E': ["11111", "10000", "11110", "10000", "11111"],
    'C': ["01111", "10000", "10000", "10000", "01111"], 'O': ["01110", "10001", "10001", "10001", "01110"],
    'R': ["11110", "10001", "11110", "10010", "10001"], 'N': ["10001", "11001", "10101", "10011", "10001"],
    ' ': ["000", "000", "000", "000", "000"]}
NEON_PINK = [(255, 208, 240), (248, 104, 200), (192, 48, 152)]
GOLD = [(255, 248, 184), (248, 208, 64), (200, 144, 32), (136, 88, 24)]
BOARD = [(72, 48, 120), (48, 32, 88), (32, 24, 56)]

def text(img, s, x, y, light, dark):
    for ch in s:
        g = FONT[ch]
        for gy, row in enumerate(g):
            for gx, v in enumerate(row):
                if v == '1':
                    px(img, x + gx, y + gy, light)
                    if gy == len(g) - 1 or g[gy + 1][gx] == '0':
                        px(img, x + gx, y + gy + 1, dark)
        x += len(g[0]) + 1
    return x

def marquee(word='GAME CORNER'):
    w, h = 96, 28
    img = canvas(w, h)
    rect(img, 2, 3, w - 2, h - 5, BOARD[1])
    rect(img, 4, 5, w - 4, h - 7, BOARD[2])
    rect(img, 4, 5, w - 4, 6, BOARD[0])
    for x in range(3, w - 3, 3):                                           # the bulb border, every third lit gold
        for y in (3, h - 6):
            px(img, x, y, GOLD[0] if (x // 3) % 2 == 0 else GOLD[1])
    for y in range(6, h - 6, 3):
        for x in (2, w - 3):
            px(img, x, y, GOLD[0] if (y // 3) % 2 == 0 else GOLD[1])
    width = sum(len(FONT[ch][0]) + 1 for ch in word) - 1
    text(img, word, (w - width) // 2, 9, NEON_PINK[0], NEON_PINK[2])
    # a gold coin at each end
    for cx in (9, w - 10):
        disc(img, cx, 11.5, 4.4, [GOLD[0], GOLD[1], GOLD[2], GOLD[3]])
        px(img, cx, 10, GOLD[3]); px(img, cx, 11, GOLD[3]); px(img, cx, 12, GOLD[3]); px(img, cx, 13, GOLD[3])
    # struts down to the roof
    for x in (14, w - 15):
        rect(img, x, h - 5, x + 2, h, GOLD[3])
        rect(img, x, h - 5, x + 1, h, GOLD[2])
    outline(img)
    return img

# --------------------------------------------------------------------------- conservatory
FRAME = [(255, 255, 255), (224, 232, 240), (176, 184, 200), (120, 128, 152)]
GLASS = [(232, 252, 255), (176, 232, 248), (128, 200, 232), (96, 160, 208)]
LEAF = [(176, 232, 120), (112, 192, 80), (64, 144, 64), (40, 96, 56)]
BRICKS = [(232, 176, 144), (200, 128, 104), (152, 88, 80)]

def conservatory():
    """The Arboretum's glasshouse, 96 x 72: a domed centre house between two glazed wings on
    a brick plinth, white iron ribs, the glass lit from the upper left, palms and ferns
    showing through it."""
    w, h = 96, 72
    img = canvas(w, h)
    cx = w // 2
    def glazed(x0, y0, x1, y1, roof_rise):
        for y in range(y0, y1):
            for x in range(x0, x1):
                px(img, x, y, GLASS[2])
        for y in range(y0 - roof_rise, y0):                                    # a pitched glass roof
            k = y0 - y
            for x in range(x0 + k, x1 - k):
                px(img, x, y, GLASS[1] if x < (x0 + x1) // 2 else GLASS[2])
        for x in range(x0, x1, 6):                                             # ribs
            for y in range(y0 - roof_rise + max(0, min(x - x0, x1 - 1 - x) < roof_rise and roof_rise - min(x - x0, x1 - 1 - x) or 0), y1):
                if img[y, x, 3]:
                    px(img, x, y, FRAME[1])
        for y in range(y0, y1, 7):
            for x in range(x0, x1):
                px(img, x, y, FRAME[1])
        for y in range(y0 - roof_rise, y1):
            for x in range(x0, x1):
                if img[y, x, 3] and img[y, x, :3].tolist() == list(GLASS[2]) and (x + y) % 9 == 0:
                    px(img, x, y, GLASS[0])                                     # glints
    # plants inside: palm crowns and ferns, behind the glass (drawn first, glass blended over)
    glazed(4, 34, 36, 62, 10)
    glazed(60, 34, 92, 62, 10)
    # the domed centre house
    for y in range(8, 62):
        for x in range(cx - 18, cx + 18):
            dx = (x + 0.5 - cx) / 18
            top = 30 - (1 - dx * dx) ** 0.5 * 22
            if y >= top:
                px(img, x, y, GLASS[1] if x < cx - 4 else GLASS[2] if x < cx + 8 else GLASS[3])
    for x in range(cx - 18, cx + 18, 6):
        for y in range(8, 62):
            if img[y, x, 3]:
                px(img, x, y, FRAME[1])
    for y in (30, 38, 46, 54):
        for x in range(cx - 18, cx + 18):
            if img[y, x, 3]:
                px(img, x, y, FRAME[1])
    # leaves behind the glass
    for (x0, y0) in ((10, 44), (20, 48), (28, 42), (66, 46), (76, 42), (84, 48), (cx - 10, 36), (cx + 6, 40), (cx - 2, 46)):
        for dy in range(-3, 4):
            for dx in range(-5, 6):
                if abs(dx) + abs(dy) * 1.6 < 5.5 and img[y0 + dy, x0 + dx, 3]:
                    px(img, x0 + dx, y0 + dy, LEAF[1] if dy < 0 and dx < 1 else LEAF[2])
        px(img, x0 - 1, y0 - 2, LEAF[0])
    # finial and a gold weathervane on the dome
    rect(img, cx - 1, 2, cx + 1, 9, FRAME[2]); rect(img, cx - 1, 2, cx, 9, FRAME[0])
    disc(img, cx, 3, 1.6, [GOLD[0], GOLD[1], GOLD[2], GOLD[3]])
    # brick plinth and the door
    rect(img, 2, 62, w - 2, 70, BRICKS[1]); rect(img, 2, 62, w - 2, 63, BRICKS[0])
    for y in (65, 68):
        rect(img, 2, y, w - 2, y + 1, BRICKS[2])
    rect(img, cx - 6, 50, cx + 6, 70, FRAME[2]); rect(img, cx - 5, 51, cx + 5, 70, GLASS[3])
    rect(img, cx - 1, 51, cx + 1, 70, FRAME[2])
    outline(img)
    return img

# --------------------------------------------------------------------------- street furniture
def bench():
    """A park bench, 24 x 16: timber slats on green iron ends."""
    img = canvas(24, 16)
    for x0 in (2, 19):
        rect(img, x0, 6, x0 + 3, 15, IRON[2]); rect(img, x0, 6, x0 + 1, 15, IRON[1])
    rect(img, 1, 2, 23, 5, WOOD[1]); rect(img, 1, 2, 23, 3, WOOD[0])        # back rest
    rect(img, 1, 8, 23, 12, WOOD[2]); rect(img, 1, 8, 23, 9, WOOD[0])       # seat
    rect(img, 1, 10, 23, 11, WOOD[3])
    outline(img)
    return img

def planter(tree):
    """A street tree in a square stone planter: the tree's own art over a 24 x 10 box."""
    img = canvas(32, 52)
    C_ = tree.copy()
    a = C_[..., 3] > 0
    img[:48][a] = C_[a]
    rect(img, 4, 40, 28, 50, STONE[2]); rect(img, 4, 40, 28, 42, STONE[0]); rect(img, 4, 48, 28, 50, STONE[3])
    rect(img, 7, 42, 25, 46, (104, 80, 56))                                  # soil
    rect(img, 13, 34, 19, 44, (148, 115, 74)); rect(img, 17, 34, 19, 44, (123, 99, 74))
    C2 = tree.copy(); C2[40:] = 0
    a = C2[..., 3] > 0
    img[:48][a] = C2[a]
    outline(img)
    return img

def casino_lights(img):
    """The Game Corner made to glow: bulbs along its pale neon bands (every third pixel,
    gold and white by turns), and a hot-pink neon edge traced round its arch."""
    img = img.copy()
    rgb = img[..., :3].astype(int)
    a = img[..., 3] > 0
    pale = a & (rgb.min(-1) > 180) & (rgb[..., 2] > rgb[..., 1] + 10)        # the lavender light bands
    ys, xs = np.nonzero(pale)
    for y, x in zip(ys, xs):
        if (x + 2 * y) % 3 == 0:
            img[y, x, :3] = GOLD[0] if (x // 3) % 2 else (255, 255, 255)
    deep = a & (rgb[..., 2] > 150) & (rgb[..., 0] < 90) & (rgb[..., 1] < 60)  # the arch's deep blue
    pad = np.pad(deep, 1)
    rim = deep & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[rim, :3] = NEON_PINK[1]
    return img
