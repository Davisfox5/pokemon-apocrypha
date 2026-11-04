"""Route 32 (HGSS textures): compose the native art, bottom and top layers, 16 px per cell.

    python3 tools/gba/maps/route32_hgss/compose.py ENGINE PHG_CHECKOUT

AGENTS.md / docs/GBA_MAP_RECONSTRUCTION.md: original-game textures and accepted shared art.

  * Ground, woods, rock (cap, faces and shading), ledges, tall grass, sea, shore foam, pier, stairs,
    boulders, the Union Cave mouth and the route signs: HGSS Route 32's own textures, from
    hgss_render.py's 1:1 render of its land_data (ground layer without the viaduct's shadow, the
    HGSS gatehouse and the HGSS Center).
  * Ruins of Alph gatehouse: G02, the owner-approved HGSS side gate (Route 31), its stairs on HGSS's
    gate warps. Pokemon Center: C06, the approved Violet Center, its door on HGSS's Center door.
  * Magnet Train viaduct: HGSS's own viaduct textures (`overpass` guard rail and side, `senro_out` track
    bed, a/2/3/3 model 24's texture set) on the footprint of HGSS's viaduct shadow (rows 82.5-87.5).
  * North padding: Violet City's own south edge (pack.py places rows 0-4 by Violet's metatile ids).

Layering (Gen 3): an object's pixels go to the top layer only on cells the player can stand on that
lie north of the object's base (sign heads, the Center roof's top row, the viaduct over walkable or
surfable cells); everything else is drawn into the bottom layer.

Cleanup: render seams where a lifted rock face uncovered the sea's flat texture inside a rock cell
(blue specks on the islets and cliff feet) are filled from the surrounding rock texture. Each pixel
changed is recorded.

Writes gba/art/route32-hgss/source/compose/{bottom.png, top.png, compose.json} and
evidence/compose/{native-art.png, cleanup.png}.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reference as Rf                                 # noqa: E402
from reference import W, H, HW, HH, PX, COL0, ROW0     # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route32-hgss'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'compose', EV / 'compose'
SHARED = SRC / 'shared-art'
SCRATCH_RENDER = HERE / 'render_layout.py'

GATE_ORIGIN = (0, 1 + ROW0)          # G02 is 7x7 cells; its stairs (column 6, rows 4-5) on HGSS's gate warps (6,5)/(6,6)
CENTER_DOOR = (2, 4)                 # C06's door inside its 5x5 cells
VIOLET_LAYOUT = 'VioletCity_Layout'
VIADUCT_PX = (round((Rf.VIADUCT[0] + ROW0) * PX), round((Rf.VIADUCT[1] + ROW0) * PX))
SEA = ('sea_un', 'sea_on')

def rgba(p): return np.array(Image.open(p).convert('RGBA'))

# --------------------------------------------------------------------------- viaduct
def viaduct_textures(phg):
    sys.path[:0] = [str(ROOT / 'tools/hoennconv'), str(ROOT / 'tools/regionport')]
    import hgss_render as R, narc, mdlview
    m = mdlview.Model(narc.load(Path(phg) / 'files/a/2/3/3')[24])
    out = {}
    for t in m.tex.textures:
        if t.name in ('overpass', 'senro_out'):
            p = m.tex.pal_for(t)
            out[t.name] = R.decode(m.tex, t, p.name if p else None)[..., :3]
    return out

def viaduct_art(phg, width):
    """The deck seen from above, track running east-west: guard rail, track bed, guard rail, south side."""
    tx = viaduct_textures(phg)
    over, bed = tx['overpass'], tx['senro_out']
    rail = np.rot90(over[:, 0:16])                     # silver rail stripes, now along x (16 x 32)
    side = np.rot90(over[:, 16:32])                    # grey side with its brackets (16 x 32)
    track = np.rot90(bed)                              # sleepers across the track (32 x 32)
    def band(tex, rows):
        t = tex[rows]
        reps = -(-width // t.shape[1])
        return np.tile(t, (1, reps, 1))[:, :width]
    deck = np.concatenate([
        band(rail, slice(3, 13)),                      # north guard rail, 10 px
        band(track, np.arange(52) % 32),               # track bed, 52 px
        band(rail[::-1], slice(3, 13)),                # south guard rail, 10 px
        band(side, slice(4, 12)),                      # the deck's south side, 8 px
    ])
    assert deck.shape[0] == VIADUCT_PX[1] - VIADUCT_PX[0], deck.shape
    return deck.astype(np.uint8)

# --------------------------------------------------------------------------- violet padding
def violet_render(engine):
    """Violet City's layout decoded from the engine (both layers composited)."""
    tmp = OUT / 'violet-city.png'
    subprocess.run([sys.executable, str(HERE / 'render_layout.py'), str(engine), 'HEAD', VIOLET_LAYOUT, str(tmp)],
                   check=True, capture_output=True)
    return np.array(Image.open(tmp).convert('RGB'))

def padding(engine):
    v = violet_render(engine)
    rows = np.zeros((ROW0 * PX, W * PX, 3), np.uint8)
    src = v[Rf.VIOLET_ROW * PX:(Rf.VIOLET_ROW + 1) * PX, Rf.VIOLET_SHIFT * PX:(Rf.VIOLET_SHIFT + W) * PX]
    for y in range(ROW0):
        rows[y * PX:(y + 1) * PX] = src
    return rows, v

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 + 1 / 32
CAP = [(0x80, 0x88, 0x78), (0xd8, 0xb8, 0x80), (0xe0, 0xc8, 0x80), (0xb8, 0xa8, 0x80)]   # Violet's verge, outside in

def seam_row(bottom):
    """Padding row 5 (route art): Violet's lawn turns into HGSS's lawn by an ordered dither, and Violet's
    cobble road ends in a rounded cap of its own verge colours before HGSS's lawn."""
    y0 = (ROW0 - 1) * PX
    cell = bottom[y0:y0 + PX].astype(int)
    vl = np.array((104, 208, 152)); hl = bottom[ROW0 * PX:ROW0 * PX + 48].reshape(-1, 3)
    vals, cnt = np.unique(hl, axis=0, return_counts=True)
    hgss_lawn = vals[cnt.argmax()]
    lawn = (np.abs(cell - vl).sum(-1) < 24)
    road_cols = np.nonzero(~lawn[0])[0]
    L, R = int(road_cols.min()), int(road_cols.max()) + 1
    out = cell.copy()
    for y in range(PX):
        t = (y + 0.5) / PX
        for x in range(W * PX):
            if lawn[y, x]:
                out[y, x] = hgss_lawn if t > BAYER[y % 4, x % 4] else cell[y, x]
    # road cap: rounded rectangle, open at the top, bottom edge at y = 11
    bot, rad = 11, 4
    for y in range(PX):
        for x in range(L, R):
            cxp = min(max(x + 0.5, L + rad), R - rad); cyp = min(y + 0.5, bot + 1 - rad)
            inside = np.hypot(x + 0.5 - cxp, y + 0.5 - cyp) if y + 0.5 > bot + 1 - rad else None
            dist = min(x + 0.5 - L, R - (x + 0.5)) if inside is None else rad - inside
            if dist < 0:
                out[y, x] = hgss_lawn if (y + 0.5) / PX > BAYER[y % 4, x % 4] else vl
            elif dist < len(CAP) and (inside is not None or y >= 0):
                if inside is not None or dist < 1:
                    out[y, x] = CAP[min(int(dist), len(CAP) - 1)] if inside is not None else cell[y, x]
    bottom[y0:y0 + PX] = out.astype(np.uint8)
    return dict(road_px=[L, R], hgss_lawn=[int(v) for v in hgss_lawn], violet_lawn=vl.tolist())

# --------------------------------------------------------------------------- compose
CLIFF = ('wall01_d', 'wall01_g', 'cliff01gs')

def rock_near(rock, r):
    return ndimage.binary_dilation(rock, np.ones((3, 3)), iterations=r)

def specks(ground, mat, names, grid):
    """Sea-texture pixels the rock surrounds: render seams where a lifted face or an islet's top left the
    flat sea showing through. (1) sea components that no water cell's sea connects to; (2) sea pixels
    inside the closed outline of a rock mass (islet tops); (3) slivers mostly enclosed by rock."""
    nm = np.array(list(names) + ['none'])
    mn = nm[np.where(mat >= 0, mat, len(names))]
    sea = np.isin(mn, SEA)
    lab, n = ndimage.label(sea, structure=np.ones((3, 3)))
    water_cells = np.zeros((HH, HW), bool)
    for hz in range(HH):
        for hx in range(HW):
            water_cells[hz, hx] = grid[hz + ROW0][hx + COL0] in '~BO'
    wpx = np.kron(water_cells, np.ones((PX, PX), bool))
    keep = np.unique(lab[wpx & sea])
    bad = sea & ~np.isin(lab, keep)
    rock = np.isin(mn, CLIFF)
    closed = ndimage.binary_closing(rock, structure=np.ones((3, 3)), iterations=3)
    inside = ndimage.binary_fill_holes(closed)
    bad |= sea & inside & rock_near(rock, 3)
    # (3) slivers: sea pixels mostly surrounded by cliff (7x7 window)
    for _ in range(3):
        solid = (rock | bad).astype(float)
        bad |= sea & (ndimage.uniform_filter(solid, 7) > 0.62)
    return bad

def fill_from_texture(img, bad):
    """Fill each bad pixel from the nearest good pixel straight above or below it at a multiple of 8 px,
    so the rock texture's own grain continues; anything left takes its nearest good pixel."""
    out = img.copy()
    left = bad.copy()
    g = img.astype(int)
    water = (g[..., 2] > 150) & (g[..., 2] - g[..., 0] > 70)     # never copy water into rock
    bad = bad | water
    for k in range(1, 9):
        for d in (k * 8, -k * 8):
            src = np.roll(img, d, axis=0); sb = np.roll(bad, d, axis=0)
            take = left & ~sb
            if d > 0: take[:d] = False
            else: take[d:] = False
            out[take] = src[take]; left &= ~take
    if left.any():
        _, (iy, ix) = ndimage.distance_transform_edt(bad, return_indices=True)
        out[left] = out[iy[left], ix[left]]
    return out

def main(engine, phg):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    hg = SRC / 'hgss'
    ground = np.array(Image.open(hg / 'hgss-ground.png').convert('RGB'))
    fg = rgba(hg / 'hgss-foreground.png')
    mats = np.load(hg / 'hgss-ground-materials.npz')
    perm = np.load(hg / 'hgss-permissions.npz')
    events = json.loads((SRC / 'hgss-events.json').read_text())
    grid = [l[6:] for l in (SRC / 'trace/material-grid.txt').read_text().splitlines() if not l.startswith('#')]
    log = {}

    # cleanup: render seams
    bad = specks(ground, mats['material'], mats['names'], grid)
    before = ground.copy()
    if bad.any():
        ground = fill_from_texture(ground, bad)
    # (4) blue pixels (any material) enclosed by rock colours: texture-edge water bleeding into cliffs
    g = ground.astype(int)
    blue = (g[..., 2] > 150) & (g[..., 0] < 130) & (g[..., 2] - g[..., 0] > 70)
    brown = (g[..., 0] > g[..., 2] + 20) & (g[..., 0] > 90)
    bad2 = blue & (ndimage.uniform_filter(brown.astype(float), 5) > 0.5)
    for _ in range(2):
        bad2 |= blue & (ndimage.uniform_filter((brown | bad2).astype(float), 5) > 0.6)
    ground = fill_from_texture(ground, bad2)
    bad |= bad2
    log['seam_specks_filled_px'] = int(bad.sum())
    ys, xs = np.nonzero(bad)
    log['seam_speck_cells'] = sorted({(int(x) // PX + COL0, int(y) // PX + ROW0) for y, x in zip(ys, xs)})

    bottom = np.zeros((H * PX, W * PX, 3), np.uint8)
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    pad, violet = padding(engine)
    bottom[:ROW0 * PX] = pad
    bottom[ROW0 * PX:, COL0 * PX:(COL0 + HW) * PX] = ground
    log['seam_row'] = seam_row(bottom)

    # walkable / surfable cells (HGSS permissions); padding is open lawn/road
    stand = np.ones((H, W), bool)
    for hz in range(HH):
        for hx in range(HW):
            t, k = int(perm['types'][hz, hx]), int(perm['collision'][hz, hx])
            stand[hz + ROW0, hx + COL0] = not (k & 0x80) or t in (0x15, 0x10)

    def place(art, x0, y0, base_row, name):
        """Composite an RGBA object; pixels on standable cells north of its base row go to the top layer."""
        h, w = art.shape[:2]
        a = art[..., 3] > 127
        n_top = n_bot = 0
        for yy in range(h):
            y = y0 + yy
            if not 0 <= y < H * PX:
                continue
            for xx in np.nonzero(a[yy])[0]:
                x = x0 + xx
                if not 0 <= x < W * PX:
                    continue
                cy, cx = y // PX, x // PX
                if stand[cy, cx] and cy < base_row:
                    top[y, x] = art[yy, xx]; n_top += 1
                else:
                    bottom[y, x] = art[yy, xx, :3]; n_bot += 1
        log.setdefault('objects', []).append(dict(name=name, xy=[int(x0), int(y0)], base_row=int(base_row),
                                                   top_px=n_top, bottom_px=n_bot))

    # G02 and C06
    g02 = rgba(SHARED / 'G02.png'); c06 = rgba(SHARED / 'C06.png')
    gx, gy = GATE_ORIGIN
    place(g02, gx * PX, gy * PX, gy + g02.shape[0] // PX - 1, 'gate_alph (G02)')
    door = next(Rf.to_map(*w['cell']) for w in events['warps'] if tuple(w['cell']) == (20, 130))
    cx, cy = door[0] - CENTER_DOOR[0], door[1] - CENTER_DOOR[1]
    place(c06, cx * PX, cy * PX, cy + c06.shape[0] // PX - 1, 'pokemon_center (C06)')

    # HGSS signs (foreground render), each based on its own sign cell
    owner = np.load(hg / 'hgss-foreground-owner.npz')['owner']
    rinfo = json.loads((hg / 'hgss-render.json').read_text())
    for i, b in enumerate(rinfo['buildings']):
        if 'board_cd' not in b['names']:
            continue
        m = owner == i
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        art = fg[y0:y1, x0:x1].copy(); art[~m[y0:y1, x0:x1], 3] = 0
        base = int(np.floor(b['pos'][2])) + ROW0
        place(art, x0 + COL0 * PX, y0 + ROW0 * PX, base, f'sign_{int(b["pos"][0])}_{int(b["pos"][2])} (HGSS board_cd)')

    # viaduct: over everything on its rows
    deck = viaduct_art(phg, W * PX)
    d = np.concatenate([deck, np.full(deck.shape[:2] + (1,), 255, np.uint8)], -1)
    v0 = VIADUCT_PX[0]
    for yy in range(deck.shape[0]):
        y = v0 + yy
        cy = y // PX
        for cx in range(W):
            sl = slice(cx * PX, (cx + 1) * PX)
            if stand[cy, cx]:
                top[y, sl] = d[yy, sl]
            else:
                bottom[y, sl] = deck[yy, sl]
                top[y, sl] = 0
    log['viaduct'] = dict(rows_px=list(VIADUCT_PX), textures='a/2/3/3 model 24: overpass, senro_out')

    Image.fromarray(bottom).save(OUT / 'bottom.png')
    Image.fromarray(top, 'RGBA').save(OUT / 'top.png')
    comp = bottom.copy(); a = top[..., 3] > 0; comp[a] = top[a][:, :3]
    Image.fromarray(comp).save(OEV / 'native-art.png')
    ys, xs = np.nonzero(bad)
    if len(ys):
        sh = []
        for (cx, cy) in log['seam_speck_cells'][:24]:
            y, x = (cy - ROW0) * PX, (cx - COL0) * PX
            sl = (slice(max(0, y - 16), y + 32), slice(max(0, x - 16), x + 32))
            p = np.zeros((48, 48 * 2 + 4, 3), np.uint8)
            b_, a_ = before[sl], ground[sl]
            p[:b_.shape[0], :b_.shape[1]] = b_; p[:a_.shape[0], 52:52 + a_.shape[1]] = a_
            sh.append(p)
        Image.fromarray(np.concatenate(sh, 0)).resize((100 * 4, 48 * len(sh) * 4), Image.NEAREST).save(OEV / 'cleanup.png')
    log['sources'] = {k: hashlib.sha256((SHARED / k).read_bytes()).hexdigest() for k in ('G02.png', 'C06.png')}
    log['engine'] = subprocess.run(['git', '-C', str(engine), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    (OUT / 'compose.json').write_text(json.dumps(log, indent=1) + '\n')
    print('composed', {k: v for k, v in log.items() if k not in ('objects', 'seam_speck_cells')}, len(log['seam_speck_cells']), 'speck cells')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
