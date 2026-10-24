"""Saffron City ten years on: FireRed's own Saffron, edited for Apocrypha's story.

    python3 tools/gba/maps/saffron/compose.py ENGINE_CHECKOUT

FireRed's map (SaffronCity_Frlg: 66x55 on General_Frlg + SaffronCity) is the base, cell for
cell. Each change answers a line of DESIGN.md (Kanto; Chapter 5):

    station      The Magnet Train station, the player's way into Kanto (Chapter 4's end)
                 and the place the rail-pass rule strands them (Chapter 5), stands where
                 HGSS puts it, the north-west block, in place of three houses. HGSS's own
                 model at C06's angle (sprites.py); its door is solid until the station's
                 interior exists.
    silph        Silph Co. "dominates the skyline": its tower rises two floors (its roof
                 now stands on the street north of it, which Silph's growth has taken),
                 and the two apartment blocks beside it are Silph's annex wings, built
                 from the tower's own metatiles.
    dojos        Saffron has no gym: Sabrina's building is the Psychic Dojo, beside the
                 Fighting Dojo, its "GYM" plate painted out and both red Gym signposts
                 plain signposts.
    league       The Trainer Fan Club is the Kanto League office (its sign).
    copycat      The Copycat's house, whose lot the station takes, moves to the house at
                 (18, 17), which gains FireRed's own door front.
    grade        Kanto's grade, "cooler institutional steel and glass" (frlg.GRADE): the
                 town's walls concrete, its house roofs slate.

FireRed's Team Rocket occupation is ten years gone, so none of its people or scripts come
across (install.py writes fresh events). Every unchanged cell keeps its FireRed metatile.
Writes source/compose.npz (edited grid, art cells) and evidence/terrain.png, compare.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import frlg                                     # noqa: E402

ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
PRIMARY, SECONDARY, LAYOUT = 'general_frlg', 'saffron_city_frlg', 'SaffronCity_Frlg'
W, H = 66, 55
PAVING = 0x2E9                                  # FireRed's plain Saffron paving
SIGNPOST = 0x002                                # its plain signpost (General)
OLIVE = 0x2EC                                   # the darker paving round its buildings
OPEN, BLOCKED = (0, 3), (1, 0)                  # (collision, elevation) as FireRed's grid has them

# the station: sprite left edge (px), its foot on row 14 (the houses' door row)
STATION_X, STATION_BASE_ROW = 288, 14
STATION_DOOR = (25, 14)
NW_BLOCK = (17, 10, 28, 14)                     # the three houses the station replaces
TOWER = (29, 37)                                # Silph's columns
TOWER_ROWS = dict(top=16, roof=(16, 21), floor=22, base=30)
RISE = 2                                        # floors added
WINGS = [(24, 25), (38, 25)]                    # top-left cells of the two inner apartment blocks (5 x 6)
# A wing from the tower's own cells: its columns are the tower's (left frame, two panes,
# the right panes, right frame); its rows the roof's top edge (walk-behind, as the
# apartment block's was), the roof panel's lower edge, the ledge under the roof, a floor,
# the lower floor and the base.
WING_COLS = [29, 30, 31, 36, 37]
WING_ROWS = [16, 20, 21, 22, 29, 30]
GYM_SIGNS = [(42, 13), (50, 13)]                # red Gym signposts (top cell; the post is the row below)
GYM_PLATE = [(44, 11), (45, 11), (44, 12), (45, 12)]   # the cells of the plate beside the Psychic Dojo's door
PLATE_BOX = (707, 189, 723, 194)                # its white panel, "GYM" on it (px: x0, y0, x1, y1)
COPYCAT_HOUSE = (18, 20)                        # its front's top-left: two rows take the door front
CITY_SIGN = (30, 12)                            # moved from (29, 14), which Silph's roof now covers

def edit_grid(pair, grid):
    g = grid.copy()
    cell = lambda mid, cv: np.uint16(mid | (cv[0] << 10) | (cv[1] << 12))
    notes = {}
    # the station's lot
    x0, y0, x1, y1 = NW_BLOCK
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y, x] = cell(PAVING, OPEN)
    # Silph rises: its roof two rows up, two more floors under it
    c0, c1 = TOWER
    src_rows = list(range(TOWER_ROWS['roof'][0], TOWER_ROWS['roof'][1] + 1)) + [TOWER_ROWS['floor']] * RISE
    for i, sy in enumerate(src_rows):
        for x in range(c0, c1 + 1):
            g[TOWER_ROWS['top'] - RISE + i, x] = grid[sy, x]
    # the fence west of the dojos loses its west post under the roof: its next post is the end
    g[14, c1 + 1] = (g[14, c1 + 1] & 0xFC00) | 0x31D
    # Silph's wings
    for wx, wy in WINGS:
        for j, sy in enumerate(WING_ROWS):
            for i, sx in enumerate(WING_COLS):
                g[wy + j, wx + i] = grid[sy, sx]
    # the dojos' red Gym signposts become plain signposts
    for x, y in GYM_SIGNS:
        g[y, x] = cell(OLIVE, OPEN)
        g[y + 1, x] = cell(SIGNPOST, BLOCKED)
    # the city sign moves north of Silph's roof
    g[CITY_SIGN[1], CITY_SIGN[0]] = cell(SIGNPOST, BLOCKED)
    # the Copycat's house front: FireRed's door front (the house at (21, 13) had it)
    hx, hy = COPYCAT_HOUSE
    for j in range(2):
        for i in range(3):
            g[hy + j, hx + i] = (g[hy + j, hx + i] & 0xFC00) | (grid[13 + j, 21 + i] & 0x3FF)
    notes['copycat_door'] = (hx + 1, hy + 1)
    return g, notes

def station_sprite():
    img = np.array(Image.open(SRC / 'sprites/station.png').convert('RGBA'))
    X = STATION_X
    Y = (STATION_BASE_ROW + 1) * 16 - img.shape[0]
    return img, X, Y

def plate_without_letters(bot, top):
    """The Psychic Dojo's plate: FireRed's Gym plate with its red "GYM" letters painted in
    the plate's own white. Only inside the plate's panel: the door's red trim beside it stays."""
    x0, y0, x1, y1 = PLATE_BOX
    for layer in (bot, top):
        box = layer[y0:y1, x0:x1]
        rgb = box[..., :3].astype(int)
        red = (rgb[..., 0] > 150) & (rgb[..., 1] < 110) & (rgb[..., 2] < 110)
        if layer.shape[-1] == 4:
            red &= box[..., 3] > 0
        if not red.any():
            continue
        plate = (rgb.min(-1) > 200) & ~red
        white = tuple(int(v) for v in np.median(rgb[plate], 0)) if plate.any() else (248, 248, 248)
        box[..., :3][red] = white
    return bot, top

def compose(engine):
    pair = frlg.Pair(engine, PRIMARY, SECONDARY)
    grid, border = frlg.layout(engine, LAYOUT)
    pals = frlg.graded(pair.pals)
    g, notes = edit_grid(pair, grid)
    bottom, top = frlg.render(pair, g, pals)
    art = np.zeros((H, W), bool)                 # cells packed from pixels, not kept as metatiles
    # the Psychic Dojo's plate
    plate_without_letters(bottom, top)
    for x, y in GYM_PLATE:
        art[y, x] = True
    # the station stands in front of everything behind it: the trees and fence of the
    # forest edge, the lot's paving. Its tiles go on the top layer; the bottom layer there is
    # whatever stands behind it, both FireRed layers flattened.
    img, X, Y = station_sprite()
    a = img[..., 3] > 0
    full = frlg.flat(bottom, top)
    station = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    station[Y:Y + img.shape[0], X:X + img.shape[1]][a] = img[a]
    hit = station[..., 3] > 0
    cells_hit = hit.reshape(H, 16, W, 16).any(axis=(1, 3))
    for y, x in zip(*np.nonzero(cells_hit)):
        sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        bottom[sl] = full[sl]
        top[sl] = station[sl]
        art[y, x] = True
    owner = np.full((H, W), '', '<U12')
    owner[cells_hit] = 'station'
    return dict(pair=pair, grid=grid, border=border, pals=pals, edited=g, bottom=bottom, top=top, art=art, owner=owner,
                station_cells=cells_hit, notes=notes)

def main(engine):
    r = compose(engine)
    SRC.mkdir(parents=True, exist_ok=True); EV.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SRC / 'compose.npz', grid=r['grid'], border=r['border'], edited=r['edited'], bottom=r['bottom'],
                        top=r['top'], art=r['art'], owner=r['owner'], station_cells=r['station_cells'],
                        pals=np.array([r['pals'][b] for b in range(13)], np.uint8))
    after = frlg.flat(r['bottom'], r['top'])
    Image.fromarray(after).save(EV / 'terrain.png')
    before = frlg.flat(*frlg.render(r['pair'], r['grid']))
    sheet = Image.new('RGB', (W * 16 * 2 + 12, H * 16 + 24), (28, 32, 38)); d = ImageDraw.Draw(sheet)
    for i, (im, t) in enumerate(((before, 'FireRed (SaffronCity_Frlg)'), (after, 'Ten years on'))):
        sheet.paste(Image.fromarray(im), (i * (W * 16 + 12), 24)); d.text((i * (W * 16 + 12) + 4, 6), t, fill='white')
    sheet.save(EV / 'compare.png')
    print('art cells', int(r['art'].sum()), 'station cells', int(r['station_cells'].sum()), r['notes'])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
