#!/usr/bin/env python3
"""Adult Silver battle-sprite concepts.

A: Lance body (class 86 champion f0) — cape recolored to black coat w/ crimson
   lining, navy suit kept, Silver head transplant.
B: Palmer body (class 97 tower tycoon f0) — arms-crossed longcoat recolored to
   charcoal-indigo w/ crimson collar, Silver head transplant.
"""
from PIL import Image
import os, sys

LIB = "artwork-library/heartgold-johto/trainers/battle-front/"
S = os.path.dirname(os.path.abspath(__file__))

# ---------- Silver source head ----------
silver = Image.open(LIB + "a058_c023_rival.png").crop((0, 0, 80, 80))
spal = silver.getpalette()
sc = lambda i: tuple(spal[i*3:i*3+3])
SILVER_HAIR = {1, 2, 3, 4}
SILVER_SKIN = {10, 11, 12, 13}

def silver_head():
    """RGBA head crop: box x26-48, y7-28 inclusive; keep hair/skin/outline/eye."""
    keep = SILVER_HAIR | SILVER_SKIN | {14, 15}
    px = silver.load()
    out = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    o = out.load()
    for y in range(7, 29):
        for x in range(26, 49):
            v = px[x, y]
            if v in keep:
                o[x, y] = sc(v) + (255,)
    return out

# ---------- generic helpers ----------
def to_rgba(imP, bg_idx):
    pal = imP.getpalette()
    px = imP.load()
    out = Image.new("RGBA", imP.size, (0, 0, 0, 0))
    o = out.load()
    for y in range(imP.size[1]):
        for x in range(imP.size[0]):
            v = px[x, y]
            if v != bg_idx:
                o[x, y] = tuple(pal[v*3:v*3+3]) + (255,)
    return out

def erase_zone(rgba, box, colors_rgba=None):
    o = rgba.load()
    x0, y0, x1, y1 = box
    for y in range(y0, y1+1):
        for x in range(x0, x1+1):
            if o[x, y][3] and (colors_rgba is None or o[x, y][:3] in colors_rgba):
                o[x, y] = (0, 0, 0, 0)

def remap(rgba, mapping):
    o = rgba.load()
    for y in range(rgba.size[1]):
        for x in range(rgba.size[0]):
            p = o[x, y]
            if p[3] and p[:3] in mapping:
                o[x, y] = mapping[p[:3]] + (255,)

def remap_zone(rgba, box, mapping):
    o = rgba.load()
    x0, y0, x1, y1 = box
    for y in range(y0, y1+1):
        for x in range(x0, x1+1):
            p = o[x, y]
            if p[3] and p[:3] in mapping:
                o[x, y] = mapping[p[:3]] + (255,)

def paste_head(body, head, dx, dy):
    h = head.load(); b = body.load()
    for y in range(80):
        for x in range(80):
            if h[x, y][3]:
                tx, ty = x + dx, y + dy
                if 0 <= tx < 80 and 0 <= ty < 80:
                    b[tx, ty] = h[x, y]

# Silver identity colors
HAIR = [sc(1), sc(2), sc(3), sc(4)]          # red ramp light->dark
CRIMSON = (140, 24, 49)
CRIMSON_D = (99, 24, 57)
COAT_D = (23, 18, 33)     # near-black indigo coat dark
COAT_M = (41, 33, 57)     # coat mid
COAT_L = (66, 57, 90)     # coat light edge
NAVY_D = (33, 24, 49)
NAVY_M = (49, 49, 90)
PANT_M = (57, 57, 115)
PANT_L = (74, 74, 148)

# ---------- Concept A: Lance body ----------
def concept_a():
    lance = Image.open(LIB + "a058_c086_champion.png").crop((0, 0, 80, 80))
    body = to_rgba(lance, 0)
    lp = lance.getpalette()
    lc = lambda i: tuple(lp[i*3:i*3+3])
    # erase Lance head: hair/skin/outline within head zone
    head_colors = {lc(i) for i in (3, 4, 5, 6, 10, 11, 12, 13, 15, 14, 7)}
    erase_zone(body, (18, 0, 52, 13), head_colors)   # full hair spread
    erase_zone(body, (22, 14, 48, 26), head_colors)  # face, avoid hands
    # cape wine ramp -> coat black w/ crimson lining (5=lit outer -> crimson)
    remap(body, {
        lc(3): COAT_D,
        lc(4): COAT_M,
        lc(5): CRIMSON_D,
        lc(6): CRIMSON,
        lc(13): COAT_L,
    })
    # orange trim -> silver-red trim
    remap(body, {lc(2): (173, 49, 57)})
    paste_head(body, silver_head(), -5, -2)
    return body

# ---------- Concept B: Palmer body ----------
def concept_b():
    palmer = Image.open(LIB + "a058_c097_tower_tycoon.png").crop((0, 0, 80, 80))
    body = to_rgba(palmer, 0)
    pp = palmer.getpalette()
    pc = lambda i: tuple(pp[i*3:i*3+3])
    # erase Palmer head: blonde + tan face + outline in head zone
    head_colors = {pc(i) for i in (2, 5, 6, 13, 11, 12, 1, 3)}
    erase_zone(body, (33, 0, 58, 18), head_colors)
    # coat greens -> charcoal-indigo ramp; collar/scarf light green -> crimson
    # collar zone = rows 15-27 (around neck/shoulders); elsewhere light green stays coat light
    remap_zone(body, (30, 14, 62, 28), {pc(9): CRIMSON, pc(8): CRIMSON_D})
    remap(body, {
        pc(7): COAT_D,
        pc(8): COAT_M,
        pc(9): COAT_L,
    })
    # pants brown -> silver navy pants; tan pant-light -> pant mid
    remap(body, {pc(10): PANT_M, pc(2): PANT_L})
    # stray blonde outside head (belt?) -> gold stays; lavender shirt tones keep
    head = silver_head()
    # drop the cowlick rows that would clip at frame top (src y7-9 -> dst y<1)
    hp = head.load()
    for y in range(7, 10):
        for x in range(26, 49):
            hp[x, y] = (0, 0, 0, 0)
    paste_head(body, head, 7, -9)
    return body

def despeck(rgba):
    """Drop opaque pixels with <=1 opaque 8-neighbor."""
    o = rgba.load()
    kill = []
    for y in range(80):
        for x in range(80):
            if o[x, y][3]:
                n = sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                        if (dx or dy) and 0 <= x+dx < 80 and 0 <= y+dy < 80
                        and o[x+dx, y+dy][3])
                if n <= 1:
                    kill.append((x, y))
    for x, y in kill:
        o[x, y] = (0, 0, 0, 0)

# ---------- Production: full 6-frame strip on Palmer body ----------
# per-frame: (erase_box, (head_dx, head_dy), clip_cowlick, collar_box)
FRAME_CFG = {
    0: ((33, 0, 58, 18), (7, -9), True,  (30, 14, 62, 28)),
    1: ((33, 0, 58, 18), (7, -9), True,  (30, 14, 62, 28)),
    2: ((30, 9, 57, 28), (4, -1), False, (28, 24, 58, 38)),
    3: ((30, 9, 57, 28), (4, -1), False, (28, 24, 58, 38)),
    4: ((30, 9, 57, 28), (4, -1), False, (28, 24, 58, 38)),
}

# ---------- Crouch v2: GS ace trainer (c053) ready pose ----------
# One hand to the belt (ball-grab, ball removed), other arm out at the
# ready, staggered feet, knees bent. Recolored to the Silver kit.
GOLD = (214, 181, 123)
GREY_D = (74, 66, 82)
SKIN_L = (255, 214, 189)
SKIN_M = (222, 165, 123)
WHITE = (239, 239, 255)
BLACK = (0, 0, 0)

def build_crouch2():
    don = Image.open(LIB + "a058_c053_ace_trainer_m_gs.png").crop((0, 0, 80, 80))
    dp = don.getpalette()
    dc = lambda i: tuple(dp[i*3:i*3+3])
    px = don.load()
    out = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    o = out.load()
    for y in range(80):
        for x in range(80):
            v = px[x, y]
            if v == 0:
                continue
            if y <= 25 and 24 <= x <= 50 and v != 0:
                continue                      # donor head erased
            if 10 <= x <= 28 and 39 <= y <= 48:
                continue                      # ball + forearm + glove erased
            # zones matching the standing frames' outfit:
            # mantle upper third / white shirt center / coat sleeves+panels /
            # jeans legs / plain dark shoes
            shirt = 32 <= x <= 40 and 30 <= y <= 45
            mantle = y <= 39 and not shirt
            legs = y >= 48
            c = None
            if v in (2, 3, 9):
                if shirt:
                    c = WHITE if v in (2, 3) else (173, 165, 206)
                elif 36 <= y <= 48 and (x <= 28 or x >= 49):
                    c = SKIN_L if v == 2 else (SKIN_M if v == 3 else GREY_D)
                elif mantle:
                    c = CRIMSON if v in (2, 3) else CRIMSON_D
                elif legs:                               # boot cuffs -> jeans
                    c = PANT_L if v in (2, 3) else PANT_M
                else:
                    c = COAT_D
            elif v == 7:
                c = WHITE if shirt else (CRIMSON if mantle else
                                         (PANT_L if legs else COAT_M))
            elif v == 8:
                c = (173, 165, 206) if shirt else (CRIMSON_D if mantle else
                                                   (PANT_M if legs else COAT_D))
            elif v == 1:
                c = CRIMSON
            elif v in (4, 5):
                c = GREY_D
            elif v == 6:
                c = (23, 18, 33)
            elif v == 10:
                c = SKIN_L
            elif v in (11, 12):
                c = SKIN_M
            elif v == 13:
                c = CRIMSON_D
            elif v == 14:
                c = WHITE
            elif v == 15:
                c = BLACK
            if c:
                o[x, y] = c + (255,)
    # left torso edge outline where the arm was cut away
    for y in range(39, 49):
        edge = next((x for x in range(24, 40) if o[x, y][3]), None)
        if edge is not None and o[edge, y][:3] != BLACK:
            o[edge-1, y] = BLACK + (255,)
    # bent forearm hugging the torso: elbow tip x26, hand to the belt
    ARM = [
        (27,36,COAT_M),(28,36,COAT_M),
        (27,37,COAT_M),(28,37,COAT_D),
        (26,38,COAT_M),(27,38,COAT_D),
        (26,39,COAT_M),(27,39,COAT_D),
        (26,40,COAT_M),(27,40,COAT_M),
        (27,41,COAT_M),(28,41,COAT_M),
        (28,42,COAT_M),(29,42,COAT_M),
        (29,43,SKIN_L),(30,43,SKIN_L),
        (30,44,SKIN_L),(31,44,SKIN_M),
        (31,45,SKIN_M),
    ]
    # white shirt sliver + gold buckle glint (match the standing frames)
    for x, y in ((36,28),(37,28),(36,29),(37,29),(37,30)):
        if o[x, y][3]:
            o[x, y] = WHITE + (255,)
    for x, y in ((35,46),(36,46)):
        if o[x, y][3]:
            o[x, y] = GOLD + (255,)
    for x, y, c in ARM:
        if y <= 39 and c == COAT_M:
            c = CRIMSON            # mantle drapes over the upper arm
        elif y <= 39 and c == COAT_D:
            c = CRIMSON_D
        o[x, y] = c + (255,)
    # fill the mantle drape: transparent wedge between the belt-arm and the
    # torso (rows 26-42) becomes solid cloth over the shoulder
    for y in range(26, 43):
        arm = max((x for x in range(18, 31) if o[x, y][3]), default=None)
        torso = min((x for x in range(28, 38) if o[x, y][3]), default=None)
        if arm is None or torso is None or torso - arm < 2:
            continue
        for x in range(arm+1, torso):
            o[x, y] = (CRIMSON if y <= 32 else CRIMSON_D) + (255,)
    # rounded shoulder mass left of the torso (transparent pixels only)
    SHOULDER_W = {27: 2, 28: 3, 29: 4, 30: 5, 31: 5, 32: 5, 33: 5,
                  34: 5, 35: 5, 36: 4, 37: 3, 38: 3}
    for y, w in SHOULDER_W.items():
        torso = min((x for x in range(30, 39) if o[x, y][3]), default=None)
        if torso is None:
            continue
        for x in range(torso - w, torso):
            if not o[x, y][3]:
                o[x, y] = (CRIMSON if y <= 32 else CRIMSON_D) + (255,)
    # contour the new cloth: black outline where it meets background
    for y in range(26, 45):
        for x in range(16, 36):
            if not o[x, y][3]:
                continue
            if o[x, y][:3] in (CRIMSON, CRIMSON_D):
                for dx, dy in ((-1, 0), (0, -1)):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < 80 and 0 <= ny < 80 and not o[nx, ny][3]:
                        o[nx, ny] = BLACK + (255,)
    # pokeball in the ready hand: fingers grip from above
    RED, BAND, W = (173, 49, 57), BLACK, WHITE
    BALL = [
        (53,39,BAND),(54,39,BAND),(55,39,BAND),(56,39,BAND),
        (52,40,BAND),(53,40,RED),(54,40,CRIMSON),(55,40,RED),(56,40,RED),(57,40,BAND),
        (52,41,BAND),(53,41,CRIMSON),(54,41,RED),(55,41,RED),(56,41,RED),(57,41,BAND),
        (52,42,BAND),(53,42,BAND),(54,42,BAND),(55,42,BAND),(56,42,BAND),(57,42,BAND),
        (52,43,BAND),(53,43,W),(54,43,W),(55,43,W),(56,43,W),(57,43,BAND),
        (53,44,BAND),(54,44,W),(55,44,W),(56,44,BAND),
        (54,45,BAND),(55,45,BAND),
    ]
    for x, y, c in BALL:
        o[x, y] = c + (255,)
    # open-coat skirt: flaps hanging outside the legs, rows 47-60
    for y in range(47, 63):
        w = 3 if 49 <= y <= 59 else 2
        xs = [x for x in range(80) if o[x, y][3]]
        if not xs:
            continue
        lx, rx = min(xs), max(xs)
        for i in range(1, w+1):
            if not o[lx-i, y][3]:
                o[lx-i, y] = (COAT_D if i == 1 else COAT_M) + (255,)
        if not o[lx-w-1, y][3]:
            o[lx-w-1, y] = BLACK + (255,)
        for i in range(1, w+1):
            if not o[rx+i, y][3]:
                o[rx+i, y] = (COAT_D if i == 1 else COAT_M) + (255,)
        if not o[rx+w+1, y][3]:
            o[rx+w+1, y] = BLACK + (255,)
    # outline the new arm's left edge
    for y in range(36, 46):
        edge = next((x for x in range(20, 40) if o[x, y][3]), None)
        if edge is not None and o[edge, y][:3] != BLACK:
            o[edge-1, y] = BLACK + (255,)
    paste_head(out, silver_head(), 0, -3)
    despeck(out)
    return out

# final shared 16-color palette (0 = transparent)
FOLD = {
    (206, 82, 99): (173, 49, 57),    # hair light -> trim red
    (255, 231, 132): (214, 181, 123),  # gold light -> gold
    (189, 123, 99): (222, 165, 123),   # skin dark -> skin mid
    (123, 66, 66): (99, 24, 57),       # hair-darkest skin edge -> crimson dark
    (99, 99, 90): (74, 66, 82),        # grey -> grey dark
    (148, 132, 132): (173, 165, 206),  # buckle grey -> lavender
}
PALETTE = [(255, 0, 255), (0, 0, 0), (23, 18, 33), (41, 33, 57), (66, 57, 90),
           (74, 66, 82), (140, 24, 49), (99, 24, 57), (173, 49, 57),
           (57, 57, 115), (74, 74, 148), (222, 165, 123), (255, 214, 189),
           (214, 181, 123), (173, 165, 206), (239, 239, 255)]

def build_frame(n):
    palmer = Image.open(LIB + "a058_c097_tower_tycoon.png").crop((n*80, 0, n*80+80, 80))
    body = to_rgba(palmer, 0)
    if n == 5:
        return body  # blank frame stays blank
    pp = palmer.getpalette()
    pc = lambda i: tuple(pp[i*3:i*3+3])
    ebox, (dx, dy), clip, cbox = FRAME_CFG[n]
    head_colors = {pc(i) for i in (2, 5, 6, 13, 11, 12, 1, 3)}
    erase_zone(body, ebox, head_colors)
    remap_zone(body, cbox, {pc(9): CRIMSON, pc(8): CRIMSON_D})
    remap(body, {pc(7): COAT_D, pc(8): COAT_M, pc(9): COAT_L,
                 pc(10): PANT_M, pc(2): PANT_L})
    head = silver_head()
    if clip:
        hp = head.load()
        for y in range(7, 10):
            for x in range(26, 49):
                hp[x, y] = (0, 0, 0, 0)
    paste_head(body, head, dx, dy)
    despeck(body)
    return body

def build_strip():
    strip = Image.new("RGBA", (480, 80), (0, 0, 0, 0))
    for n in (0, 1, 5):
        strip.paste(build_frame(n), (n*80, 0))
    # frames 2-4: crouch v2, shifted right to match each bank's screen
    # anchor (origins -43/-45/-44 vs -40 for the standing frames)
    c2 = build_crouch2()
    for n, dx in ((2, 3), (3, 5), (4, 4)):
        shifted = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
        shifted.paste(c2, (dx, 0), c2)
        strip.paste(shifted, (n*80, 0))
    # fold colors, then map onto the fixed 16-entry palette
    o = strip.load()
    lut = {c: i for i, c in enumerate(PALETTE)}
    out = Image.new("P", (480, 80))
    pal = []
    for c in PALETTE:
        pal += list(c)
    out.putpalette(pal + [0]*(768-len(pal)))
    op = out.load()
    unknown = set()
    for y in range(80):
        for x in range(480):
            p = o[x, y]
            if not p[3]:
                op[x, y] = 0
                continue
            c = FOLD.get(p[:3], p[:3])
            if c not in lut:
                unknown.add(c)
                c = min(PALETTE[1:], key=lambda q: sum((a-b)**2 for a, b in zip(q, c)))
            op[x, y] = lut[c]
    if unknown:
        print("WARN colors snapped to nearest:", unknown)
    return out

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "strip":
        strip = build_strip()
        strip.save(S + "/silver_adult_strip.png")
        prev = strip.convert("RGBA")
        bg = Image.new("RGBA", prev.size, (52, 52, 60, 255))
        px, qx = prev.load(), strip.load()
        for y in range(80):
            for x in range(480):
                if qx[x, y] == 0:
                    px[x, y] = (0, 0, 0, 0)
        bg.paste(prev, (0, 0), prev)
        bg.resize((480*2, 160), Image.NEAREST).save(S + "/silver_adult_strip_prev.png")
        print("strip ok,", len(strip.getcolors()), "palette entries used")
        sys.exit()
    a = concept_a(); b = concept_b()
    despeck(a); despeck(b)
    a.save(S + "/silver_adult_A.png"); b.save(S + "/silver_adult_B.png")
    sheet = Image.new("RGBA", (170, 90), (52, 52, 60, 255))
    sheet.paste(a, (2, 5), a); sheet.paste(b, (88, 5), b)
    sheet.resize((170*4, 90*4), Image.NEAREST).save(S + "/silver_adult_concepts.png")
    print("ok")
