"""Dark Cave: the routes' rock walls, in HGSS's cave rock colours, laid out on HGSS's cave.

    python3 tools/gba/maps/dark_cave/assemble.py PATH/TO/pokeheartgold ENGINE_CHECKOUT

HGSS draws its cave walls with the same kind of rock as its routes, in cave colours. So the cave
uses the rock the owner accepted outdoors: FRLG General's mountain pieces (route46/elements.py
frlg_pieces: the nine-slice, its over-rock variant, the inner corners and the jump ledges), with
the outdoor rock ramp swapped for HGSS's cave rock ramp (CAVE_RAMP, from dwall_s, dcliff01 and
dallpeak_p). They are laid out exactly as on the routes (rock_frlg): each rock cell keeps HGSS's
tier height, and a neighbour lower than it (walkable ground, a lower tier, the void beyond the
cave) puts an edge on that side, per 8x8 quadrant, with FRLG's whole inner-corner piece where
only a diagonal is lower. The clear pixels of a piece show what lies past that edge (HGSS's
floor texture, its water, or the black void), and the cast shadow on the floor is the floor's
darkest tone. HGSS's jump ledges are FRLG's ledge in the same ramp (rounded ends where a run
stops on open floor, turned on its side for the west-facing runs), as on the routes.

Walkable cells keep HGSS's render, with any wall pixels HGSS's slanted tiers laid on them painted
back as floor (droad01 at HGSS's own texture phase) or water. Boulders, stairs, exits and water
keep HGSS's render.

Writes source/assemble/<side>.png (the native art) and <side>-class.npy (the per-pixel material
class pack.py's tile reuse respects), and evidence/assemble/<side>-before-after.png.
"""
from __future__ import annotations
import importlib.util, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hgss_render as R                              # noqa: E402
import pack as P                                     # noqa: E402

_spec = importlib.util.spec_from_file_location('route46_elements', HERE.parent / 'route46/elements.py')
E = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(E)   # the routes' FRLG rock pieces

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/dark-cave'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 64
PALETTE = {'d_rock01': 'd_rock01s_pl', 'droad01_sub': 'droad01_sub2_pl'}
# pack.CLASS numbers: 0 void, 1 floor, 2 wall face, 3 cliff top, 4 rim, 5 boulder, 6 stairs, 7 water, 8 exit
VOID, FLOOR, FACE, TOP, RIM, BOULDER, STAIRS, WATER, EXIT = range(9)
# The outdoor ramp (E.ROCK_RAMP: outline, then light to dark) in HGSS's cave rock colours, each tone
# taken from the cave's own wall textures at the matching place in the ramp: the outline is
# dallpeak_p's darkest, tones 1-3 dcliff01's and dwall_s's light rock, 4-6 dwall_s's dark rock.
CAVE_RAMP = [(66, 57, 41), (173, 165, 148), (156, 148, 132), (140, 132, 115), (115, 107, 90), (99, 90, 74), (82, 74, 57)]
DIRS = E.DIRS
CLEAR, SHADOW = E.CLEAR, E.SHADOW

def textures(phg):
    _, tex0, _, _, _ = R.load(phg)
    return {e.name: R.decode(tex0, e, PALETTE.get(e.name, e.name + '_pl')) for e in tex0.textures}

def tiled(tex, x, y):
    """The 16x16 block of a texture tiled at world pixel phase for cell (x, y)."""
    t = tex[..., :3]
    th, tw = t.shape[:2]
    return t[(np.arange(16) + y * 16) % th][:, (np.arange(16) + x * 16) % tw].copy()

def ramp_class(k):
    """Material class of a ramp tone: the outline and dark tones are face, the light tones top."""
    return FACE if k in (0, 4, 5, 6) else TOP

def main(phg, engine):
    out_dir = SRC / 'assemble'; out_dir.mkdir(parents=True, exist_ok=True)
    (EV / 'assemble').mkdir(parents=True, exist_ok=True)
    T = textures(phg)
    pieces = E.frlg_pieces(engine)
    nine, nine_rock, inner, ledge_p = pieces['nine'], pieces['rock'], pieces['inner'], pieces['ledge']
    floor_tex = T['droad01'][..., :3].reshape(-1, 3)
    shadow = tuple(int(v) for v in floor_tex[np.argmin(floor_tex.astype(int).sum(1))])
    fill_ix = nine[('M', 'M')]
    report = {}
    for side in P.SIDES:
        hg = SRC / f'hgss/{side}'
        ref = np.array(Image.open(hg / 'hgss-render.png').convert('RGB'))
        m = np.load(hg / 'hgss-ground-materials.npz')
        names = [str(v) for v in m['names']]
        lut = np.array([P.CLASS[n] for n in names] + [VOID], np.int16)
        hcls = lut[m['material']]
        perm = np.load(hg / 'hgss-permissions.npz')
        types, coll = perm['types'], perm['collision']
        height = np.nan_to_num(np.load(hg / 'hgss-cell-height.npy'))
        cells = hcls.reshape(H, 16, W, 16).transpose(0, 2, 1, 3).reshape(H, W, 256)
        major = np.array([[Counter(cells[y, x].tolist()).most_common(1)[0][0] for x in range(W)] for y in range(H)])
        void = (types == 0) & (coll == 0)
        blocked = (coll & 0x80) > 0
        ledge = np.isin(types, (0x3B, 0x39))
        rock = blocked & ~ledge & np.isin(major, (FACE, TOP, RIM))   # the rest keep HGSS's cell
        level = np.where(rock, np.round(height).astype(int), -1)
        inside = lambda x, y: 0 <= x < W and 0 <= y < H

        def lower(x, y, nx, ny):
            if not inside(nx, ny):
                return False
            return not rock[ny, nx] or level[ny, nx] < level[y, x]

        img, cls = ref.copy(), hcls.copy()

        def beyond(x, y, nx, ny):
            """(pixels, class, shadow colour) past an edge of cell (x, y) toward (nx, ny), at (x, y)'s phase."""
            if not inside(nx, ny) or void[ny, nx] and not rock[ny, nx]:
                return np.zeros((16, 16, 3), np.uint8), VOID, None
            if rock[ny, nx]:
                return np.array([CAVE_RAMP[k] for k in fill_ix.ravel()], np.uint8).reshape(16, 16, 3), TOP, None
            if types[ny, nx] == 0x15:
                return tiled(T['driver'], x, y), WATER, None
            return tiled(T['droad01'], x, y), FLOOR, shadow

        def paint(sl, ix, bg, bgk, cast):
            cell, ck = bg.copy(), np.full((16, 16), bgk, np.int16)
            for (yy, xx), k in np.ndenumerate(ix):
                if k >= 0:
                    cell[yy, xx] = CAVE_RAMP[k]; ck[yy, xx] = ramp_class(k)
                elif k == SHADOW and cast:
                    cell[yy, xx] = cast
            img[sl], cls[sl] = cell, ck

        painted = 0
        for y in range(H):
            for x in range(W):
                sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                if void[y, x] and not rock[y, x]:
                    img[sl] = 0; cls[sl] = VOID
                elif not rock[y, x] and not blocked[y, x]:
                    wall = np.isin(cls[sl], (FACE, TOP, RIM))
                    if wall.any():
                        painted += 1
                        fill, k = (tiled(T['driver'], x, y), WATER) if types[y, x] == 0x15 else (tiled(T['droad01'], x, y), FLOOR)
                        img[sl][wall] = fill[wall]; cls[sl][wall] = k
        # Rock: FRLG's nine-slice per quadrant, as route46/elements.py rock_frlg composes it.
        for y in range(H):
            for x in range(W):
                if not rock[y, x]:
                    continue
                lo = {k: lower(x, y, x + dx, y + dy) for k, (dx, dy) in DIRS.items()}
                diag = [k for k in ('ne', 'se', 'sw', 'nw') if lo[k]]
                whole = None
                if not any(lo[k] for k in 'nesw') and diag:
                    if len(diag) == 1:
                        whole = inner[diag[0]]
                    elif sorted(diag) in (['se', 'sw'], ['ne', 'nw']):
                        r, l = ('se', 'sw') if 'se' in diag else ('ne', 'nw')
                        whole = np.concatenate([inner[l][:, :8], inner[r][:, 8:]], 1)
                cell = np.zeros((16, 16, 3), np.uint8); ck = np.zeros((16, 16), np.int16)
                for qy in (0, 1):
                    v = ('N', 'S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M'
                    for qx in (0, 1):
                        h = ('W', 'E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M'
                        q = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
                        vk, hk = 'ns'[qy], 'we'[qx]
                        toward = next((DIRS[k] for k in (vk, hk, vk + hk) if lo[k]), None)
                        if toward:
                            bg, bgk, cast = beyond(x, y, x + toward[0], y + toward[1])
                        else:
                            bg, bgk, cast = beyond(x, y, x, y)               # own rock top
                        if whole is not None:
                            ix = whole[q]
                        elif lo[vk + hk] and not lo[vk] and not lo[hk]:
                            ix = inner[vk + hk][q]
                        else:
                            ix = (nine_rock if bgk == TOP else nine)[(v, h)][q]
                        cell[q], ck[q] = bg[q], bgk
                        for (yy, xx), k in np.ndenumerate(ix):
                            if k >= 0:
                                cell[q][yy, xx] = CAVE_RAMP[k]; ck[q][yy, xx] = ramp_class(k)
                            elif k == SHADOW and cast:
                                cell[q][yy, xx] = cast
                img[y * 16:y * 16 + 16, x * 16:x * 16 + 16], cls[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = cell, ck
        # Jump ledges: FRLG's ledge strip, rounded where a run stops on open floor; west runs on their side.
        for y in range(H):
            for x in range(W):
                if not ledge[y, x]:
                    continue
                sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                bg, bgk, cast = beyond(x, y, x, y + 1 if types[y, x] == 0x3B else y)
                if types[y, x] == 0x39:
                    bg, bgk, cast = beyond(x, y, x - 1, y)
                free = lambda nx, ny: inside(nx, ny) and not rock[ny, nx] and not ledge[ny, nx] and not void[ny, nx]
                if types[y, x] == 0x3B:
                    ix = ledge_p['mid'].copy()
                    if free(x - 1, y): ix[:, :8] = ledge_p['left'][:, :8]
                    if free(x + 1, y): ix[:, 8:] = ledge_p['right'][:, 8:]
                else:
                    side_ = lambda p: p.T[:, ::-1]                      # face looking west
                    ix = side_(ledge_p['mid']).copy()
                    if free(x, y - 1): ix[:8, :] = side_(ledge_p['left'])[:8, :]
                    if free(x, y + 1): ix[8:, :] = side_(ledge_p['right'])[8:, :]
                paint(sl, ix, bg, bgk, cast)
        Image.fromarray(img).save(out_dir / f'{side}.png')
        np.save(out_dir / f'{side}-class.npy', cls.astype(np.int8))
        both = Image.new('RGB', (W * 32 + 12, H * 16), (24, 26, 30))
        both.paste(Image.fromarray(ref), (0, 0)); both.paste(Image.fromarray(img), (W * 16 + 12, 0))
        both.save(EV / f'assemble/{side}-before-after.png')
        report[side] = dict(rock_cells=int(rock.sum()), ledge_cells=int(ledge.sum()), walkable_cells_repainted=painted)
        print(side, report[side])
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
