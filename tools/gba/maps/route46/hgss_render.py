"""Render HGSS Route 46 from the game's own map data, 1:1 at 16 px per tile, with the top
SOUTH_ROWS rows of Route 29's chunk below it (the Route 29 gatehouse and its woods).

Inputs are pret/pokeheartgold's packed archives, read only:

    a/0/6/5  land_data: per 32x32 chunk permissions, building placements, NSBMD terrain
    a/0/4/2  area data: Route 46 (bank 9, as Blackthorn)
    a/0/4/4  map texture sets (NSBTX)
    a/0/4/0  exterior building models (bm_field), textures embedded

Projection: ground (x, z) lands on its own 16 px cell, as the permission grid
does; anything above the town floor rises by its height (screen y = z - (y - floor)),
the way Gen 3 draws building fronts and roofs. One HGSS tile is one native cell.

    python3 tools/gba/maps/route46/hgss_render.py PATH/TO/pokeheartgold OUT_DIR

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import json, struct, sys, hashlib
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / 'tools/hoennconv'), str(ROOT / 'tools/regionport')]
import narc, hgss_map, mdlview          # noqa: E402
from nsbtx import Tex0                  # noqa: E402

AREA_BANK = 9
HEADER_ID = 48                          # MAP_ROUTE_46
# Owner review (2026-10-29): the native map runs on SOUTH_ROWS rows into the chunk below it,
# MAP_ROUTE_29's (area bank 2, its own map textures), so the whole Route 29 gatehouse and the woods
# closing on it are on Route 46 and its south border never comes into view.
SOUTH_HEADER, SOUTH_AREA_BANK, SOUTH_ROWS = 33, 2, 6
PX = 16                                 # pixels per tile
SNAP = True                             # stretch cliff/ledge fronts to whole 8 px rows

# --------------------------------------------------------------------------- textures
def _colors(tex0, pal, n):
    out = np.zeros((max(n, 1), 3), np.uint8)
    for i in range(min(n, pal.pal_ncolors)):
        (v,) = struct.unpack_from('<H', tex0.blob, pal.pal_off + i * 2)
        out[i] = ((v & 31) << 3 | (v & 31) >> 2, ((v >> 5) & 31) << 3 | ((v >> 5) & 31) >> 2,
                  ((v >> 10) & 31) << 3 | ((v >> 10) & 31) >> 2)
    return out

def decode(tex0, entry, palname):
    """RGBA uint8 array (h, w, 4) for one texture under a named palette."""
    w, h, fmt, o, b = entry.width, entry.height, entry.fmt, entry.data_off, tex0.blob
    n = w * h
    raw = np.frombuffer(bytes(b[o:o + {1: n, 2: n // 4, 3: n // 2, 4: n, 6: n, 7: 2 * n}.get(fmt, 0)]), np.uint8)
    pal = next((p for p in tex0.palettes if p.name == palname), None) or tex0.pal_for(entry)
    rgba = np.zeros((n, 4), np.uint8)
    if fmt == 7:
        v = raw.view('<u2').astype(np.uint32)
        for k, s in enumerate((0, 5, 10)):
            c = (v >> s) & 31
            rgba[:, k] = (c << 3) | (c >> 2)
        rgba[:, 3] = np.where(v & 0x8000, 255, 0)
        return rgba.reshape(h, w, 4)
    if fmt == 2:
        idx = np.stack([(raw >> s) & 3 for s in (0, 2, 4, 6)], 1).ravel()
    elif fmt == 3:
        idx = np.stack([raw & 15, raw >> 4], 1).ravel()
    elif fmt in (1, 6, 4):
        idx = raw & {1: 31, 6: 7, 4: 255}[fmt]
    else:
        rgba[:] = (255, 0, 255, 255)
        return rgba.reshape(h, w, 4)
    cols = _colors(tex0, pal, {1: 32, 2: 4, 3: 16, 4: 256, 6: 8}[fmt])
    rgba[:, :3] = cols[np.minimum(idx, len(cols) - 1)]
    rgba[:, 3] = 255
    if fmt == 1:
        a = raw >> 5
        rgba[:, 3] = (a * 36 + (a >> 1)).astype(np.uint8)
    elif fmt == 6:
        a = raw >> 3
        rgba[:, 3] = ((a << 3) | (a >> 2)).astype(np.uint8)
    elif entry.color0:
        rgba[idx == 0, 3] = 0
    return rgba.reshape(h, w, 4)

# --------------------------------------------------------------------------- materials
MATERIAL_NAMES = []

class Material:
    def __init__(self, model, mid, tex0):
        self.tex = None
        name, pal = model.mat_tex.get(mid), model.mat_pal.get(mid)
        if name and tex0 is not None:
            e = next((t for t in tex0.textures if t.name == name), None)
            if e is not None:
                self.tex = decode(tex0, e, pal)
        self.name = name or ''
        if self.name not in MATERIAL_NAMES:
            MATERIAL_NAMES.append(self.name)
        self.uid = MATERIAL_NAMES.index(self.name)
        body = model.mat_body[mid] if mid < len(model.mat_body) else None
        self.repeat = (True, True); self.flip = (False, False); self.alpha = 31; self.scale = (1.0, 1.0)
        if body is not None:
            blob = model.blob
            poly, = struct.unpack_from('<I', blob, body + 0x0C)
            ti, = struct.unpack_from('<I', blob, body + 0x14)
            flag, = struct.unpack_from('<H', blob, body + 0x1E)
            self.alpha = (poly >> 16) & 31
            self.repeat = (bool(ti & 0x10000), bool(ti & 0x20000))
            self.flip = (bool(ti & 0x40000), bool(ti & 0x80000))
            if flag & 1 and not flag & 2:
                sx, sy = struct.unpack_from('<ii', blob, body + 0x2C)
                self.scale = (sx / 4096.0, sy / 4096.0)

    def sample(self, s, t):
        tex = self.tex
        h, w = tex.shape[:2]
        s = s * self.scale[0]; t = t * self.scale[1]
        def wrap(v, n, rep, flip):
            v = np.floor(v).astype(np.int64)
            if not rep:
                return np.clip(v, 0, n - 1)
            if flip:
                p = np.mod(v, 2 * n)
                return np.where(p >= n, 2 * n - 1 - p, p)
            return np.mod(v, n)
        return tex[wrap(t, h, self.repeat[1], self.flip[1]), wrap(s, w, self.repeat[0], self.flip[0])]

# --------------------------------------------------------------------------- raster
class Canvas:
    def __init__(self, w, h):
        self.rgb = np.zeros((h, w, 3), np.float32)
        self.depth = np.full((h, w), -1e9, np.float32)
        self.owner = np.full((h, w), -1, np.int32)
        self.height = np.full((h, w), np.nan, np.float32)
        self.mat = np.full((h, w), -1, np.int16)       # material id of the opaque surface
        self.over = np.full((h, w), -1, np.int16)      # last translucent overlay blended on top
        self.steep = np.zeros((h, w), bool)
        self.w, self.h = w, h

    def tri(self, p, uv, depth, mat, owner, blend=False, hgt=(0, 0, 0), steep=False):
        (x0, y0), (x1, y1), (x2, y2) = p
        minx, maxx = int(max(0, np.floor(min(x0, x1, x2)))), int(min(self.w - 1, np.ceil(max(x0, x1, x2))))
        miny, maxy = int(max(0, np.floor(min(y0, y1, y2)))), int(min(self.h - 1, np.ceil(max(y0, y1, y2))))
        if minx > maxx or miny > maxy:
            return
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-9:
            return
        ys, xs = np.mgrid[miny:maxy + 1, minx:maxx + 1]
        px, py = xs + 0.5, ys + 0.5
        w0 = ((x1 - px) * (y2 - py) - (x2 - px) * (y1 - py)) / area
        w1 = ((x2 - px) * (y0 - py) - (x0 - px) * (y2 - py)) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            return
        d = w0 * depth[0] + w1 * depth[1] + w2 * depth[2]
        yy, xx = ys[inside], xs[inside]
        d = d[inside]
        vis = d >= self.depth[yy, xx] - 1e-4
        if not vis.any():
            return
        yy, xx, d = yy[vis], xx[vis], d[vis]
        a0, a1, a2 = w0[inside][vis], w1[inside][vis], w2[inside][vis]
        if mat.tex is None:
            return
        s = a0 * uv[0][0] + a1 * uv[1][0] + a2 * uv[2][0]
        t = a0 * uv[0][1] + a1 * uv[1][1] + a2 * uv[2][1]
        texel = mat.sample(s, t).astype(np.float32)
        alpha = texel[:, 3] / 255.0 * (mat.alpha / 31.0)
        if blend:
            keep = alpha > 0.02
            yy, xx, alpha, texel = yy[keep], xx[keep], alpha[keep], texel[keep]
            self.rgb[yy, xx] = self.rgb[yy, xx] * (1 - alpha[:, None]) + texel[:, :3] * alpha[:, None]
            self.over[yy, xx] = mat.uid
        else:
            keep = alpha >= 0.5
            yy, xx, d, texel = yy[keep], xx[keep], d[keep], texel[keep]
            self.rgb[yy, xx] = texel[:, :3]
            self.depth[yy, xx] = d
            self.owner[yy, xx] = owner
            self.height[yy, xx] = (a0 * hgt[0] + a1 * hgt[1] + a2 * hgt[2])[keep]
            self.mat[yy, xx] = mat.uid
            self.steep[yy, xx] = steep

def reference_height(world, base_y, flat=False):
    """Per-vertex height that maps onto the vertex's own cell.

    Buildings (base_y given): everything rises from the building's base.
    Terrain (base_y None): walkable, near-horizontal faces register top-down on
    their own cells; steep faces (cliff and ledge fronts) rise from their lowest
    vertex, so they stand on the cells behind their base, as Gen 3 cliffs do.
    """
    if base_y is not None:
        return [base_y] * len(world)
    p = np.array(world, float)
    if flat:
        return list(p[:, 1])
    n = np.cross(p[1] - p[0], p[2] - p[0])
    norm = np.linalg.norm(n)
    if norm < 1e-9 or abs(n[1]) / norm >= 0.5:
        return list(p[:, 1])
    base, lift = p[:, 1].min(), p[:, 1].max() - p[:, 1].min()
    if not SNAP or lift <= 0:
        return [base] * len(world)
    # Gen 3 adaptation: stretch each front so its drawn height is a whole
    # number of 8 px tile rows (HGSS cliff bands are 14.4 px, ledges 5.7 px).
    scale = max(1, round(lift * PX / 8)) * 8 / PX / lift
    return [y - (y - base) * scale for y in p[:, 1]]

def draw_model(canvas, model, tex0, place, owner, base_y, flat=False):
    """place: callable (x, y, z) model-space -> world (X, Y, Z) in tiles."""
    mats = {}
    opaque, clear = [], []
    for mid, verts in model.faces():
        if mid not in mats:
            mats[mid] = Material(model, mid, tex0)
        mat = mats[mid]
        world = [place(*v[0]) for v in verts]
        ref = reference_height(world, base_y, flat)
        steep = base_y is None and not flat and any(r < w[1] - 1e-6 for r, w in zip(ref, world))
        scr = [(X * PX, (Z - (Y - r)) * PX) for (X, Y, Z), r in zip(world, ref)]
        # Top-down surfaces tie on Z alone; the higher one (a bridge over a river) wins.
        dep = [Y if flat else Z + (Y - r) + 0.01 * Y for (X, Y, Z), r in zip(world, ref)]
        uv = [v[1] for v in verts]
        tris = [(0, 1, 2)] if len(verts) == 3 else [(0, 1, 2), (0, 2, 3)]
        translucent = mat.alpha < 31 or (mat.tex is not None and ((mat.tex[:, :, 3] > 0) & (mat.tex[:, :, 3] < 255)).any())
        for a, b, c in tris:
            item = ([scr[a], scr[b], scr[c]], [uv[a], uv[b], uv[c]], [dep[a], dep[b], dep[c]], mat,
                    (world[a][1], world[b][1], world[c][1]), steep)
            (clear if translucent else opaque).append(item)
    for p, uv, d, mat, hgt, steep in opaque:
        canvas.tri(p, uv, d, mat, owner, hgt=hgt, steep=steep)
    return clear

# --------------------------------------------------------------------------- map
def load(phg):
    a = phg / 'files/a'
    land = narc.load(a / '0/6/5')
    area = narc.load(a / '0/4/2')[AREA_BANK]
    bld_set, map_set = struct.unpack_from('<HH', area, 0)
    tex0 = Tex0(narc.load(a / '0/4/4')[map_set])
    south_set = struct.unpack_from('<HH', narc.load(a / '0/4/2')[SOUTH_AREA_BANK], 0)[1]
    south_tex0 = Tex0(narc.load(a / '0/4/4')[south_set])
    models = narc.load(a / '0/4/0')
    d = (phg / 'files/fielddata/mapmatrix/map_matrix/map_matrix_0000_EVERYWHERE.bin').read_bytes()
    w, h, _, has_alt, nl = d[:5]
    p = 5 + nl
    hdr = struct.unpack_from('<%dH' % (w * h), d, p); p += 2 * w * h
    if has_alt: p += w * h
    lid = struct.unpack_from('<%dH' % (w * h), d, p)
    cells = [(x, z) for z in range(h) for x in range(w) if hdr[z * w + x] == HEADER_ID]
    x0, z0 = min(c[0] for c in cells), min(c[1] for c in cells)
    chunks = [dict(cx=x - x0, cz=z - z0, land=lid[z * w + x], tex0=tex0) for x, z in cells]
    z1 = max(c[1] for c in cells) + 1
    for x in sorted({c[0] for c in cells}):
        assert hdr[z1 * w + x] == SOUTH_HEADER, ('the chunk south of Route 46 is not Route 29\'s', x, z1)
        chunks.append(dict(cx=x - x0, cz=z1 - z0, land=lid[z1 * w + x], tex0=south_tex0, south=True))
    rows = (z1 - z0) * 32 + SOUTH_ROWS
    return land, tex0, models, chunks, dict(area_bank=AREA_BANK, map_texture_set=map_set, building_texture_set=bld_set,
                                            matrix_origin=[x0, z0], south=dict(header=SOUTH_HEADER, area_bank=SOUTH_AREA_BANK,
                                            map_texture_set=south_set, rows=SOUTH_ROWS), rows=rows)

# The shared Gen 3 Center and Mart replace these HGSS models (and their door
# panels); everything else is HGSS art.
REPLACED = {'gs_pc_a': 'pokemon_center', 'gs_fs_a': 'poke_mart'}

def _place(X, Y, Z, sx, sy, sz):
    return lambda x, y, z: (X + x * sx, Y + y * sy, Z + z * sz)

def render(phg):
    """Returns the reference composite plus the separate layers a Gen 3 map needs.

    full:   everything, HGSS Center and Mart included (the reference)
    ground: terrain and every non-replaced building's translucent contact shadow
    fg:     opaque pixels of non-replaced buildings and props, RGBA
    """
    land, tex0, models, chunks, meta = load(phg)
    W = (max(c['cx'] for c in chunks) + 1) * 32
    H = (max(c['cz'] for c in chunks) + 1) * 32
    HO = meta['rows']                       # the rows kept: Route 46's own and SOUTH_ROWS of Route 29's
    ground = Canvas(W * PX, H * PX)
    under = Canvas(W * PX, H * PX)        # pure top-down terrain, fills what lifted faces uncover
    fg = Canvas(W * PX, H * PX)
    fg_all = Canvas(W * PX, H * PX)
    types = np.zeros((H, W), np.uint8); coll = np.zeros((H, W), np.uint8)
    terrain_clear, shadow_kept, shadow_all = [], [], []
    buildings = []
    for c in chunks:
        ch = hgss_map.MapChunk.parse(land[c['land']])
        ox, oz = c['cx'] * 32, c['cz'] * 32
        types[oz:oz + 32, ox:ox + 32] = np.array(ch.types, np.uint8).reshape(32, 32)
        coll[oz:oz + 32, ox:ox + 32] = np.array(ch.collisions, np.uint8).reshape(32, 32)
        terrain = mdlview.Model(ch.model)
        place = lambda x, y, z, ox=ox, oz=oz: (x + 16 + ox, y, z + 16 + oz)
        draw_model(under, terrain, c['tex0'], place, -1, None, flat=True)
        terrain_clear += draw_model(ground, terrain, c['tex0'], place, -1, None)
        for i in range(len(ch.buildings) // 48):
            e = ch.buildings[i * 48:i * 48 + 48]
            mid, = struct.unpack_from('<I', e, 0)
            bx, by, bz = [struct.unpack_from('<i', e, 4 + 4 * k)[0] / 65536 for k in range(3)]
            rot = struct.unpack_from('<3I', e, 16)
            sc = [struct.unpack_from('<i', e, 28 + 4 * k)[0] / 4096 for k in range(3)]
            assert rot == (0, 0, 0), rot
            buildings.append(dict(model=mid, chunk=c['land'], pos=[bx + 16 + ox, by, bz + 16 + oz], scale=sc))
    # A door panel belongs to the building whose footprint contains it.
    for b in buildings:
        m = mdlview.Model(models[b['model']])
        b['names'] = sorted(set(m.mat_tex.values()))
        fs = m.faces(); X, Y, Z = b['pos']
        xs = [X + v[0][0] for _, f in fs for v in f]; zs = [Z + v[0][2] for _, f in fs for v in f]
        b['footprint'] = [min(xs), min(zs), max(xs), max(zs)]
        b['replaced_by'] = next((v for k, v in REPLACED.items() if k in b['names']), None)
    for b in buildings:
        if b['replaced_by'] is None and b['names'] == ['pc_door']:
            for o in buildings:
                f = o['footprint']
                if o is not b and o['replaced_by'] in REPLACED.values() and f[0] <= b['pos'][0] <= f[2] and f[1] <= b['pos'][2] <= f[3] + 0.5:
                    b['replaced_by'] = o['replaced_by'] + '_door'
                    break
    for n, b in enumerate(buildings):
        m = mdlview.Model(models[b['model']])
        place = _place(*b['pos'], *b['scale'])
        shadow_all += draw_model(fg_all, m, m.tex, place, n, b['pos'][1])
        if b['replaced_by'] is None:
            shadow_kept += draw_model(fg, m, m.tex, place, n, b['pos'][1])
    from scipy.ndimage import distance_transform_edt
    def finish(canvas, clear):
        for p, uv, d, mat, hgt, steep in sorted(clear, key=lambda it: max(it[2])):
            canvas.tri(p, uv, d, mat, -2, blend=True)
    # Lifted cliff fronts uncover a strip behind their base; show the terrain
    # there as seen from straight above. Anything still empty is a modelling
    # seam: fill from the nearest drawn pixel and record the count.
    uncovered = (ground.depth <= -1e8) & (under.depth > -1e8)
    ground.rgb[uncovered] = under.rgb[uncovered]
    ground.mat[uncovered] = under.mat[uncovered]
    ground.depth[uncovered] = -1e7
    meta['top_down_fill_pixels'] = int(uncovered.sum())
    holes = ground.depth <= -1e8
    if holes.any():
        _, (iy, ix) = distance_transform_edt(holes, return_indices=True)
        ground.rgb[holes] = ground.rgb[iy[holes], ix[holes]]
        ground.mat[holes] = ground.mat[iy[holes], ix[holes]]
    meta['filled_seam_pixels'] = int(holes.sum())
    finish(ground, terrain_clear)
    terrain_only = ground.rgb.copy()
    full = Canvas(W * PX, H * PX); full.rgb = terrain_only.copy(); full.depth = ground.depth.copy()
    finish(ground, shadow_kept)
    finish(full, shadow_all)
    for src, dst in ((fg_all, full), (fg, None)):
        m = src.depth > -1e8
        if dst is not None:
            dst.rgb[m] = src.rgb[m]
    rgba = np.zeros((H * PX, W * PX, 4), np.uint8)
    m = fg.depth > -1e8
    rgba[..., :3] = np.clip(fg.rgb, 0, 255).astype(np.uint8); rgba[m, 3] = 255
    hc = ground.height.reshape(H, PX, W, PX)
    with np.errstate(all='ignore'):
        cell_height = np.nanmedian(hc.transpose(0, 2, 1, 3).reshape(H, W, -1), axis=2)
    img = lambda a: Image.fromarray(np.clip(a[:HO * PX], 0, 255).astype(np.uint8))
    keep = [b for b in buildings if b['footprint'][1] < HO]
    return dict(full=img(full.rgb), ground=img(ground.rgb), terrain=img(terrain_only), fg=Image.fromarray(rgba[:HO * PX], 'RGBA'),
                fg_owner=np.where(m, fg.owner, -1)[:HO * PX], ground_mat=ground.mat[:HO * PX], ground_over=ground.over[:HO * PX],
                ground_steep=ground.steep[:HO * PX], materials=list(MATERIAL_NAMES), types=types[:HO], collision=coll[:HO],
                buildings=keep, meta=meta, cell_height=cell_height[:HO], holes=holes[:HO * PX])

def main(phg, out):
    out.mkdir(parents=True, exist_ok=True)
    global SNAP
    SNAP = False
    render(phg)['full'].save(out / 'hgss-reference-true-heights.png')   # review only: HGSS front heights
    SNAP = True
    r = render(phg)
    r['full'].save(out / 'hgss-render.png')
    r['ground'].save(out / 'hgss-ground.png')
    r['terrain'].save(out / 'hgss-terrain.png')
    r['fg'].save(out / 'hgss-foreground.png')
    np.savez_compressed(out / 'hgss-foreground-owner.npz', owner=r['fg_owner'].astype(np.int16))
    np.save(out / 'hgss-cell-height.npy', r['cell_height'])
    np.savez_compressed(out / 'hgss-ground-materials.npz', material=r['ground_mat'], overlay=r['ground_over'],
                        steep=r['ground_steep'], names=np.array(r['materials']))
    Image.fromarray((r['holes'] * 255).astype(np.uint8)).save(out / 'hgss-seam-fill-mask.png')
    np.savez(out / 'hgss-permissions.npz', types=r['types'], collision=r['collision'])
    a = phg / 'files/a'
    rev = __import__('subprocess').run(['git', '-C', str(phg), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    src = {f'files/a/{n}': hashlib.sha256((a / n).read_bytes()).hexdigest() for n in ('0/6/5', '0/4/2', '0/4/4', '0/4/0')}
    (out / 'hgss-render.json').write_text(json.dumps(dict(
        source=dict(repository='pret/pokeheartgold (Davisfox5 fork)', revision=rev, archives=src),
        meta=r['meta'], size_cells=[r['types'].shape[1], r['types'].shape[0]], px_per_cell=PX,
        projection=('screen x = X*16; screen y = (Z - (Y - ref))*16, depth Z + (Y - ref). ref = own height for '
                    'walkable near-horizontal terrain (top-down, registers on its cell), lowest vertex for steep '
                    'terrain faces, building base for buildings'),
        buildings=r['buildings']), indent=2) + '\n')
    print('rendered', r['full'].size, len(r['buildings']), 'buildings', r['meta'])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
