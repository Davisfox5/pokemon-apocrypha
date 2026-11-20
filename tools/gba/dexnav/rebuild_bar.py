# Rebuild the Pokegear tab bar for six apps (adds the DexNav app between Phone and Style).
import sys, gearimg
DEXNAV = [  # 15x15, '2' = pale icon ink, matches the existing line icons
"....22222......",
"...2.....2.....",
"..2.......2....",
".2.........2...",
".2.22...22.2...",
".2..22.22..2...",
".2....2....2...",
".2....2....2...",
"..2...2...2....",
"...2.....22....",
"....22222.22...",
"...........22..",
"............22.",
".............22",
"..............2",
]
OLD_CENTERS = [28, 74, 120, 166, 212]
NEW_CENTERS = [28, 65, 101, 138, 175, 211]   # slots of the 220px bar (x 10..229)
SEPARATORS = [47, 83, 120, 157, 193]
TOP, BOT = 134, 151                          # icon rows

def rebuild(path_in, path_out):
    px = gearimg.decode(open(path_in, 'rb').read())
    icons = []
    for c in OLD_CENTERS:
        icons.append([row[c-9:c+10] for row in px[TOP:BOT]])   # 19 wide window
    for y in range(TOP, BOT):
        for x in range(10, 230):
            if px[y][x] in (2, 7):
                px[y][x] = 1
    for x in SEPARATORS:
        for y in range(135, 150):
            px[y][x] = 7
    order = [icons[0], icons[1], icons[2], icons[3], None, icons[4]]
    for slot, icon in enumerate(order):
        c = NEW_CENTERS[slot]
        if icon is None:
            for dy, row in enumerate(DEXNAV):
                for dx, ch in enumerate(row):
                    if ch == '2':
                        px[135+dy][c-7+dx] = 2
            continue
        for dy, row in enumerate(icon):
            for dx, v in enumerate(row):
                if v == 2:
                    px[TOP+dy][c-9+dx] = 2
    open(path_out, 'wb').write(gearimg.encode(px))

if __name__ == '__main__':
    rebuild(sys.argv[1], sys.argv[2])
