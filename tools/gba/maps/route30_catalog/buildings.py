"""Route 30's houses and Mr. Pokemon's mailbox as Gen 3 sprites, by Blackthorn's method
(tools/gba/maps/blackthorn/sprites.py and hgss_camera.py on hub branch claude/blackthorn-city).

    python3 tools/gba/maps/route30_catalog/buildings.py PATH/TO/pokeheartgold

HGSS's own models and textures (Mr. Pokemon's house 53, the Apricorn house 37, each with its door 50 at
HGSS's own placement offset, and the mailbox 30) are rendered at the owner-locked C06 Center's angle
(orthographic at 38 degrees, 16 px per tile up the screen, squeezed across to fit the footprint), so roof
pitch and doors match the Center, Mart and Blackthorn's houses, then finished as Gen 3 art: each in its own
14 colours (weighted k-means over its 5-bit colours, farthest-first seeds, so a door knob or a window keeps
its colour; the mailbox shares its house's), each roof mirrored on its middle axis so its halves share tiles, C06's outline colour round the
silhouette, and tiles that differ only by a one-pixel edge shift folded together.

Writes gba/art/route30-catalog/source/local-art/buildings/{name}.png and a contact sheet; assemble.py
places them with each door on HGSS's door cell and each sprite's bottom on its base row.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hgss_render as R                     # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route30-catalog'
OUT = ART / 'source/local-art/buildings'

# --------------------------------------------------------------------------- C06 camera (Blackthorn's hgss_camera.view)
C06_PITCH, C06_SCALE = 38.0, 16.0

def view(models, parts, width_px, pitch=C06_PITCH, sy=C06_SCALE, skip=('h_kage',), ground=0.1, retex=None):
    """Gen 3 view of HGSS models at C06's angle: orthographic at `pitch`, `sy` px per tile up the screen,
    squeezed across so the visible model is `width_px` wide. parts lists (model id, (x, y, z) offset in
    tiles). Textures are cutouts (alpha >= 200); the ground shadow quad (h_kage) and every face lying on the
    ground are left out. retex maps a texture name to a function returning a replacement texture (marker
    renders). Returns RGBA and a function mapping model (x, y, z) to sprite pixels."""
    th = math.radians(pitch)
    s, c = math.sin(th), math.cos(th)
    items = []
    for mid, (ox, oy, oz) in parts:
        m = R.mdlview.Model(models[mid])
        mats = {}
        for matid, verts in m.faces():
            if matid not in mats:
                mat = R.Material(m, matid, m.tex)
                if mat.tex is not None:
                    mat.tex = mat.tex.copy()
                    mat.tex[..., 3] = np.where(mat.tex[..., 3] >= 200, 255, 0)
                    if retex and mat.name in retex:
                        mat.tex = retex[mat.name](mat.tex)
                mats[matid] = mat
            mat = mats[matid]
            if mat.name in skip or mat.tex is None or max(v[0][1] + oy for v in verts) < ground:
                continue
            items.append(([(v[0][0] + ox, v[0][1] + oy, v[0][2] + oz) for v in verts], [v[1] for v in verts], mat))
    pts = np.array([p for w, _, _ in items for p in w])
    sx = width_px / (pts[:, 0].max() - pts[:, 0].min())
    x0, y0 = pts[:, 0].min() * sx, min((p[2] * s - p[1] * c) * sy for p in pts)
    to_px = lambda x, y, z: (x * sx - x0, (z * s - y * c) * sy - y0)
    W = int(round(width_px)); H = int(math.ceil(max((p[2] * s - p[1] * c) * sy for p in pts) - y0))
    cv = R.Canvas(W, H)
    for w, uv, mat in items:
        scr = [to_px(*p) for p in w]
        dep = [p[2] * c + p[1] * s for p in w]
        for a, b, d in ([(0, 1, 2)] if len(w) == 3 else [(0, 1, 2), (0, 2, 3)]):
            cv.tri([scr[a], scr[b], scr[d]], [uv[a], uv[b], uv[d]], [dep[a], dep[b], dep[d]], mat, 0)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = np.clip(cv.rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.where(cv.mat >= 0, 255, 0)
    return rgba, to_px

def visible_width(models, parts, skip=('h_kage',), ground=0.1):
    """Width in tiles of what view() draws."""
    xs = []
    for mid, (ox, oy, oz) in parts:
        m = R.mdlview.Model(models[mid])
        for matid, verts in m.faces():
            if m.mat_tex.get(matid) in skip or max(v[0][1] + oy for v in verts) < ground:
                continue
            xs += [v[0][0] + ox for v in verts]
    return max(xs) - min(xs)

# --------------------------------------------------------------------------- Gen 3 finish (Blackthorn's sprites.py)
C06_LINE = (41, 41, 49)                  # the owner-locked C06 Center's outline
CH_W = np.array([3.0, 4.0, 2.0])         # channel weights for colour error (Blackthorn's build.py)

def kmeans_colors(colors, weights, k, iters=40):
    """Weighted k-means over unique RGB5 colours, farthest-first seeds (Blackthorn's build.py)."""
    colors = colors.astype(float)
    if len(colors) <= k:
        return np.array(list(colors) + [colors[0]] * (k - len(colors))).astype(int)
    cent = [colors[int(np.argmax(weights))]]
    for _ in range(k - 1):
        d = np.min([((colors - c) ** 2 * CH_W).sum(1) for c in cent], 0) * weights
        cent.append(colors[int(np.argmax(d))])
    cent = np.array(cent)
    for _ in range(iters):
        lab = (((colors[:, None] - cent[None]) ** 2) * CH_W).sum(-1).argmin(1)
        new = cent.copy()
        for j in range(k):
            m = lab == j
            if m.any():
                new[j] = (colors[m] * weights[m, None]).sum(0) / weights[m].sum()
        if np.allclose(new, cent):
            break
        cent = new
    return np.clip(np.rint(cent), 0, 31).astype(int)

def sprite_palette(rgba, n=14):
    px = rgba[rgba[..., 3] > 0][:, :3] >> 3
    uc, cnt = np.unique(px, axis=0, return_counts=True)
    return [tuple(int(v) << 3 for v in c) for c in kmeans_colors(uc, np.sqrt(cnt).astype(float), n)]

def outline(img, c):
    """One-pixel outline along the inside edge of the opaque area."""
    a = img[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[edge] = tuple(c) + (255,)

def finish(rgba, pal, mirror=None):
    """Mirror the roof's left half onto its right, map to the sprite's palette, outline in C06's colour."""
    img = rgba.copy()
    if mirror:
        rows, axis, cols = mirror
        left = img[:rows, axis - (cols - axis):axis]
        img[:rows, axis:cols] = left[:, ::-1]
    a = img[..., 3] > 0
    p = np.array(pal, int)
    img[..., :3] = p[((img[..., :3][..., None, :].astype(int) - p[None, None]) ** 2).sum(-1).argmin(-1)]
    img[~a] = 0
    outline(img, C06_LINE)
    return img

REUSE = 12
FLIPS = [(False, False), (True, False), (False, True), (True, True)]

def flip(t, f):
    t = t[:, ::-1] if f[0] else t
    return t[::-1] if f[1] else t

def edge_shift(old, new, diff):
    o, n, oa = old[..., :3].astype(int), new[..., :3].astype(int), old[..., 3] > 0
    for y, x in zip(*np.nonzero(diff)):
        if not any(0 <= y + dy < 8 and 0 <= x + dx < 8 and oa[y + dy, x + dx] and (o[y + dy, x + dx] == n[y, x]).all()
                   for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            return False
    return True

def reuse_tiles(img, x_phase=0):
    """A tile that differs from a more common tile of its sprite (any flip) only where an edge sits a pixel
    over (at most REUSE pixels, each taking a colour its own 4-neighbour already had, same silhouette) becomes
    that tile. The 8 px grid runs up from the bottom edge and across from x_phase."""
    pad = (-img.shape[0]) % 8
    lpad, rpad = x_phase % 8, (-(img.shape[1] + x_phase % 8)) % 8
    g = np.zeros((img.shape[0] + pad, img.shape[1] + lpad + rpad, 4), np.uint8)
    g[pad:, lpad:lpad + img.shape[1]] = img
    seen = {}
    for ty in range(g.shape[0] // 8):
        for tx in range(g.shape[1] // 8):
            t = g[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].copy()
            if not t[..., 3].any():
                continue
            t[t[..., 3] == 0] = 0
            f = min(FLIPS, key=lambda f: flip(t, f).tobytes())
            c = flip(t, f)
            seen.setdefault(c.tobytes(), [c, []])[1].append((ty, tx, f))
    kept = []
    for t, where in sorted(seen.values(), key=lambda v: -len(v[1])):
        a, best = t[..., 3] > 0, None
        for r in kept:
            for f in FLIPS:
                fr = flip(r, f)
                if ((fr[..., 3] > 0) != a).any():
                    continue
                diff = (fr[..., :3] != t[..., :3]).any(-1) & a
                d = int(diff.sum())
                if d <= REUSE and (best is None or d < best[0]) and edge_shift(t, fr, diff):
                    best = (d, fr)
        if best is None:
            kept.append(t)
            continue
        for ty, tx, f in where:
            g[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = flip(best[1], f)
    return g[pad:, lpad:lpad + img.shape[1]]

# --------------------------------------------------------------------------- Route 30
def placements():
    """HGSS's own placements (hgss-render.json): each house with its door's offset from it."""
    b = json.loads((ART / 'source/hgss/hgss-render.json').read_text())['buildings']
    pos = {}
    for e in b:
        pos.setdefault(e['model'], []).append(np.array(e['pos']))
    def door_of(p):
        d = min(pos[50], key=lambda q: np.linalg.norm(q - p))
        return tuple(float(v) for v in d - p)
    return dict(mr_pokemon_house=[(53, (0.0, 0.0, 0.0)), (50, door_of(pos[53][0]))],
                apricorn_house=[(37, (0.0, 0.0, 0.0)), (50, door_of(pos[37][0]))],
                mailbox=[(30, (0.0, 0.0, 0.0))])

def door_columns(models, parts, width):
    """Sprite columns showing the door (a marker render of its texture)."""
    paint = lambda t: np.where(t[..., 3:] > 0, np.array([0, 255, 0, 255], np.uint8), t)
    img, _ = view(models, parts, width, retex={'yo_door1': paint})
    g = (img[..., 0] < 60) & (img[..., 1] > 200) & (img[..., 2] < 60)
    xs = np.nonzero(g.any(0))[0]
    return (int(xs.min()), int(xs.max()) + 1) if len(xs) else None

def build(phg):
    _, _, models, _, _ = R.load(phg)
    OUT.mkdir(parents=True, exist_ok=True)
    info = {}
    renders = {}
    for name, parts in placements().items():
        width = int(round(visible_width(models, parts) * 16 / 8)) * 8 if name != 'mailbox' else int(round(visible_width(models, parts) * 16))
        renders[name] = (parts, width, view(models, parts, width)[0])
    # Mr. Pokemon's mailbox stands with his house: the two share one 14-colour palette (one bank).
    joint = np.concatenate([renders['mr_pokemon_house'][2].reshape(-1, 4), renders['mailbox'][2].reshape(-1, 4)])[None]
    pals = dict(mr_pokemon_house=sprite_palette(joint), mailbox=None, apricorn_house=sprite_palette(renders['apricorn_house'][2]))
    pals['mailbox'] = pals['mr_pokemon_house']
    for name, (parts, width, rgba) in renders.items():
        pal = pals[name]
        door = door_columns(models, parts, width) if name != 'mailbox' else None
        img = finish(rgba, pal)
        img = reuse_tiles(img)
        Image.fromarray(img, 'RGBA').save(OUT / f'{name}.png')
        info[name] = dict(models=[m for m, _ in parts], offsets=[list(o) for _, o in parts], size=[img.shape[1], img.shape[0]],
                          door_columns=door, colours=len({tuple(c) for c in img[img[..., 3] > 0][:, :3].tolist()}))
    (OUT / 'buildings.json').write_text(json.dumps(dict(
        note="Blackthorn's method: HGSS models at C06's angle (38 degrees, 16 px per tile up the screen, squeezed to the "
             "footprint), 14 colours each by k-means, C06 outline, one-pixel edge folds.", sprites=info), indent=1) + '\n')
    parts = [np.array(Image.open(OUT / f'{n}.png')) for n in info]
    w = sum(p.shape[1] * 4 + 16 for p in parts); h = max(p.shape[0] for p in parts) * 4 + 16
    sheet = Image.new('RGBA', (w, h), (120, 200, 160, 255)); x = 8
    for p in parts:
        sheet.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 4, p.shape[0] * 4), Image.Resampling.NEAREST), (x, 8)); x += p.shape[1] * 4 + 16
    sheet.save(ART / 'evidence/assemble/buildings.png')
    print(json.dumps(info))

if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve())
