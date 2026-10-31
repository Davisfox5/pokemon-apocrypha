"""Dark Cave: HGSS's cave rock redrawn on the Gen 3 grid, in HGSS's own cave textures.

    python3 tools/gba/maps/dark_cave/assemble.py PATH/TO/pokeheartgold

HGSS builds its cave walls as 45-degree tiers, one tile deep and one tile high each, and its
camera draws them at a slant: side walls come out as diagonal wedges, faces start part way down
a cell (dwall_s sits 9 px below the cell grid), and 225 walkable cells carry wall pixels. Gen 3
draws rock top-down, one cell at a time. So, as on the routes (route46/elements.py rock_frlg),
each rock cell keeps HGSS's tier height and takes a nine-slice piece from its neighbours: a
neighbour lower than it (walkable ground, a lower tier, or the void beyond the cave) puts an
edge on that side.

    south lower       the face: dwall_s, one cell tall, on the grid (dwall_sw / dwall_es halves
                      where the face turns a corner west / east)
    north, east, west the rim: dallpeak_p's lip along that edge, turned to face the lower side
    no lower side     the rock top: dcliff01 where HGSS shows its beige cliff top on the cell,
                      HGSS's side-wall rock (dwall_e / dwall_w) where it shows a wall tier, black
                      where it shows d_ro (the dark above its walls)

Walkable cells keep HGSS's render, with any wall pixels HGSS's slant laid on them painted back
as floor (droad01 at HGSS's own texture phase) or water. Ledges, boulders, stairs, exits and
water keep HGSS's render as drawn.

Writes source/assemble/<side>.png (the native art) and <side>-class.npy (the per-pixel material
class pack.py's tile reuse respects), and evidence/assemble/<side>-before-after.png.
"""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hgss_render as R                              # noqa: E402
import pack as P                                     # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/dark-cave'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 64
PALETTE = {'d_rock01': 'd_rock01s_pl', 'droad01_sub': 'droad01_sub2_pl'}
# pack.CLASS numbers: 0 void, 1 floor, 2 wall face, 3 cliff top, 4 rim, 5 boulder, 6 stairs, 7 water, 8 exit
VOID, FLOOR, FACE, TOP, RIM, BOULDER, STAIRS, WATER, EXIT = range(9)

def textures(phg):
    _, tex0, _, _, _ = R.load(phg)
    return {e.name: R.decode(tex0, e, PALETTE.get(e.name, e.name + '_pl')) for e in tex0.textures}

def tiled(tex, x, y, flip_h=False):
    """The 16x16 block of a texture tiled at world pixel phase for cell (x, y)."""
    t = tex[..., :3]
    if flip_h:
        t = t[:, ::-1]
    th, tw = t.shape[:2]
    ys = (np.arange(16) + y * 16) % th
    xs = (np.arange(16) + x * 16) % tw
    return t[ys][:, xs].copy()

def over(dst, cls, src, k, mask=None):
    a = src[..., 3] > 0 if mask is None else mask
    dst[a] = src[..., :3][a]
    cls[a] = k

def main(phg):
    out_dir = SRC / 'assemble'; out_dir.mkdir(parents=True, exist_ok=True)
    (EV / 'assemble').mkdir(parents=True, exist_ok=True)
    T = textures(phg)
    lip = T['dallpeak_p']                                     # lip along the cell's south edge as stored
    lips = dict(n=lip[::-1], s=lip, e=np.rot90(lip, 1)[:, ::-1].copy(), w=np.rot90(lip, 1).copy())
    lips['e'] = np.rot90(lip, -1).copy()                      # lip's south side turned east
    lips['w'] = np.rot90(lip, 1).copy()                       # ... turned west
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
        height = np.load(hg / 'hgss-cell-height.npy')
        cells = hcls.reshape(H, 16, W, 16).transpose(0, 2, 1, 3).reshape(H, W, 256)
        major = np.array([[Counter(cells[y, x].tolist()).most_common(1)[0][0] for x in range(W)] for y in range(H)])
        void = (types == 0) & (coll == 0)
        blocked = (coll & 0x80) > 0
        ledge = np.isin(types, (0x3B, 0x39))
        rock = blocked & ~ledge & np.isin(major, (FACE, TOP, RIM))   # rebuilt; the rest keep HGSS's cell
        level = np.where(rock, np.round(np.nan_to_num(height)).astype(int), -1)
        level[void] = -2

        def lower(x, y, nx, ny):
            if not (0 <= nx < W and 0 <= ny < H):
                return False
            return not rock[ny, nx] or level[ny, nx] < level[y, x]

        img = ref.copy()
        cls = hcls.copy()
        img_c = img.reshape(H, 16, W, 16, 3)
        painted = 0
        for y in range(H):
            for x in range(W):
                sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                if void[y, x] and not rock[y, x]:
                    img[sl] = 0; cls[sl] = VOID
                    continue
                if not rock[y, x]:
                    if blocked[y, x]:
                        continue                                       # ledges, boulders, exits, water rocks: HGSS's cell
                    wall = np.isin(cls[sl], (FACE, TOP, RIM))
                    if wall.any():
                        painted += 1
                        fill, k = (tiled(T['driver'], x, y), WATER) if types[y, x] == 0x15 else (tiled(T['droad01'], x, y), FLOOR)
                        img[sl][wall] = fill[wall]
                        cls[sl][wall] = k
                    continue
                lo = {k: lower(x, y, x + dx, y + dy) for k, (dx, dy) in dict(n=(0, -1), s=(0, 1), e=(1, 0), w=(-1, 0)).items()}
                cell, ck = np.zeros((16, 16, 3), np.uint8), np.zeros((16, 16), np.int16)
                if major[y, x] == TOP:
                    cell[:] = tiled(T['dcliff01'], x, y); ck[:] = TOP
                elif major[y, x] == FACE:                              # a tier HGSS shows as wall: its side-wall rock
                    cell[:] = tiled(T['dwall_e' if lo['e'] or not lo['w'] else 'dwall_w'], x, y); ck[:] = FACE
                else:
                    ck[:] = VOID                                       # HGSS's dark above its walls
                if lo['s']:
                    cell[:] = tiled(T['dwall_s'], x, y, flip_h=True); ck[:] = FACE
                    if lo['w']:
                        cell[:, :8] = T['dwall_sw'][:, :8, :3]
                    if lo['e']:
                        cell[:, 8:] = T['dwall_es'][:, 8:, :3]
                else:
                    for k in ('n', 'e', 'w'):
                        if lo[k]:
                            over(cell, ck, lips[k], RIM)
                img[sl] = cell; cls[sl] = ck
        Image.fromarray(img).save(out_dir / f'{side}.png')
        np.save(out_dir / f'{side}-class.npy', cls.astype(np.int8))
        both = Image.new('RGB', (W * 32 + 12, H * 16), (24, 26, 30))
        both.paste(Image.fromarray(ref), (0, 0)); both.paste(Image.fromarray(img), (W * 16 + 12, 0))
        both.save(EV / f'assemble/{side}-before-after.png')
        report[side] = dict(rock_cells_redrawn=int(rock.sum()), walkable_cells_repainted=painted)
        print(side, report[side])
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
