"""Violet's interiors as rooms of native 16 px cells, built from HGSS's own rooms.

An HGSS room comes apart into its terrain (floor and walls, as hgss_render.py projects them) and its props
(furniture models, each drawn on its own with its height above the floor), so a room can keep, drop, move
or add props. Each cell then gets its lower layer (terrain, flat props, props on blocked cells) and its
upper layer (the parts of tall props that stand over a walkable cell, drawn over the player), its
collision and its behaviour.

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import struct, sys
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'route29_catalog'), str(HERE)]
import hgss_render as R                 # noqa: E402
import hgss_interior as HI              # noqa: E402

PX = 16
PHG = Path('/home/user/pokeheartgold')
LIFT = 0.25                             # tiles above the floor: a prop part this high stands over the player

_cache = {}

def models(kind):
    """0: room models (bm_room), 1: field models (Sprout Tower's objects)."""
    if kind not in _cache:
        _cache[kind] = R.narc.load(PHG / ('files/a/1/4/8' if kind == 0 else 'files/a/0/4/0'))
    return _cache[kind]

@dataclass
class Prop:
    model: int
    pos: tuple                          # (X, Y, Z) in tiles, as HGSS places it
    scale: tuple = (1.0, 1.0, 1.0)
    kind: int = 0
    rgba: np.ndarray = None             # drawn, full room canvas
    lift: np.ndarray = None             # tiles above the prop's base, per pixel
    shadow: list = field(default_factory=list)

    def draw(self, w, h):
        m = R.mdlview.Model(models(self.kind)[self.model])
        c = R.Canvas(w, h)
        place = R._place(*self.pos, *self.scale)
        self.shadow = R.draw_model(c, m, m.tex, place, 0, self.pos[1])
        a = np.zeros((h, w, 4), np.uint8)
        on = c.depth > -1e8
        a[..., :3] = np.clip(c.rgb, 0, 255).astype(np.uint8); a[on, 3] = 255
        self.rgba = a
        self.lift = np.where(on, c.height - self.pos[1], np.nan)
        self.depth = c.depth
        self.names = sorted(set(n for n in m.mat_tex.values() if n))
        return self

def hgss_room(name):
    """HGSS's room: terrain RGB (32x32 cells), its props, collision and types."""
    hdr, bank, matrix = HI.ROOMS[name]
    area = R.narc.load(PHG / 'files/a/0/4/2')[bank]
    kind = area[6]
    R.load = HI.loader(bank, matrix, {0: models(0), 1: models(1)})
    R.SNAP = True
    r = R.render(PHG)
    terrain = np.array(r['terrain'].convert('RGB'))
    h, w = terrain.shape[:2]
    props = [Prop(b['model'], tuple(b['pos']), tuple(b['scale']), kind).draw(w, h) for b in r['buildings']]
    return dict(terrain=terrain, props=props, collision=r['collision'], types=r['types'], kind=kind, size=(w // PX, h // PX))

class Room:
    """A room of W x H cells: a lower RGB layer, the props over it, collision and behaviour per cell."""
    def __init__(self, terrain, origin, size, kind):
        x0, y0 = origin
        W, H = size
        self.W, self.H, self.kind = W, H, kind
        self.origin = origin
        self.lower = terrain[y0 * PX:(y0 + H) * PX, x0 * PX:(x0 + W) * PX].copy()
        self.props = []                  # (rgba, lift, depth) cropped
        self.blocked = np.zeros((H, W), bool)
        self.behaviors = {}              # (x, y): 'exit', 'ladder', ... (build.MB)
        self.rect = (0, 0, W, H)         # the room's own cells; outside it the map is black
        self.notes = []

    def inside(self, x, y):
        x0, y0, x1, y1 = self.rect
        return x0 <= x < x1 and y0 <= y < y1

    def crop(self, a):
        x0, y0 = self.origin
        return a[y0 * PX:(y0 + self.H) * PX, x0 * PX:(x0 + self.W) * PX]

    def add(self, prop, dx=0, dz=0):
        """A prop drawn at its HGSS place, moved by whole cells (dx, dz)."""
        rgba, lift, depth = self.crop(prop.rgba), self.crop(prop.lift), self.crop(prop.depth)
        if dx or dz:
            rgba, lift, depth = (np.roll(np.roll(a, dz * PX, 0), dx * PX, 1) for a in (rgba, lift, depth))
        self.props.append((rgba, lift, depth))
        # its contact shadow: the translucent faces, blended into the floor
        if prop.shadow:
            c = R.Canvas(*self.full_size())
            c.rgb[:] = self.full_lower()
            for p, uv, d, mat, hgt, steep in sorted(prop.shadow, key=lambda it: max(it[2])):
                c.tri(p, uv, d, mat, -2, blend=True)
            sh = self.crop(np.clip(c.rgb, 0, 255).astype(np.uint8))
            if dx or dz:
                sh = np.roll(np.roll(sh, dz * PX, 0), dx * PX, 1)
            changed = (sh != self.lower).any(-1)
            self.lower[changed] = sh[changed]

    def full_size(self):
        return self._full.shape[1], self._full.shape[0]

    def full_lower(self):
        f = self._full.copy()
        x0, y0 = self.origin
        f[y0 * PX:(y0 + self.H) * PX, x0 * PX:(x0 + self.W) * PX] = self.lower
        return f

    def layers(self):
        """(lower RGB, upper RGBA): props on the lower layer, except tall parts over a walkable cell."""
        low = self.lower.copy()
        up = np.zeros(low.shape[:2] + (4,), np.uint8)
        depth = np.full(low.shape[:2], -1e9, np.float32)
        stand = ~self.blocked
        for (x, y), b in self.behaviors.items():
            if b in ('ladder', 'exit'):          # the player stands on these: their art stays under the player
                stand[y, x] = False
        walk = np.repeat(np.repeat(stand, PX, 0), PX, 1)
        for rgba, lift, d in self.props:
            on = (rgba[..., 3] > 0) & (d >= depth)
            depth[on] = d[on]
            high = on & walk & (np.nan_to_num(lift, nan=0) > LIFT)
            low[on & ~high] = rgba[..., :3][on & ~high]
            up[high] = rgba[high]
            up[on & ~high, 3] = 0
        return low, up

    def image(self):
        low, up = self.layers()
        a = up[..., 3] > 0
        low[a] = up[..., :3][a]
        return low

def from_hgss(name, origin, size):
    h = hgss_room(name)
    r = Room(h['terrain'], origin, size, h['kind'])
    r._full = h['terrain']
    r.hgss = h
    x0, y0 = origin
    c = h['collision'][y0:y0 + size[1], x0:x0 + size[0]]
    r.blocked = c == 128
    r.types = h['types'][y0:y0 + size[1], x0:x0 + size[0]]
    return r

# --------------------------------------------------------------------------- composing new rooms
FOOT_LIFT = 0.75                         # a prop's pixels this low stand on their own cells: those cells block

def footprint(rgba, lift, W, H):
    on = (rgba[..., 3] > 0) & (np.nan_to_num(lift, nan=9) < FOOT_LIFT)
    return on.reshape(H, PX, W, PX).any((1, 3))

def compose(name, cols, rows, keep=None):
    """A room from HGSS's room `name`, its cells re-laid: column i of the new room is HGSS column cols[i],
    row j is HGSS row rows[j]. HGSS's props come along where their base cell lands (the last time its
    source column is used: the room's original run), unless keep(index, prop) says no; their collision comes with them."""
    h = hgss_room(name)
    T = h['terrain']
    W, H = len(cols), len(rows)
    new = np.zeros((H * PX, W * PX, 3), np.uint8)
    for j, sy in enumerate(rows):
        for i, sx in enumerate(cols):
            new[j * PX:(j + 1) * PX, i * PX:(i + 1) * PX] = T[sy * PX:(sy + 1) * PX, sx * PX:(sx + 1) * PX]
    r = Room(new, (0, 0), (W, H), h['kind'])
    r._full = new
    r.hgss = h
    r.blocked = np.array([[h['collision'][sy, sx] == 128 for sx in cols] for sy in rows])
    first = {sx: i for i, sx in enumerate(cols)}          # a prop goes where its column appears last (the original run)
    rowof = {sy: j for j, sy in enumerate(rows)}
    r.kept = []
    for k, p in enumerate(h['props']):
        X, Y, Z = p.pos
        cx, cz = int(np.floor(X)), int(np.floor(Z))
        if cx not in first or cz not in rowof or (keep and not keep(k, p)):
            if keep and not keep(k, p) and cx in first and cz in rowof:
                # its own collision goes with it (not the room's walls)
                q = Prop(p.model, p.pos, p.scale, p.kind).draw(*T.shape[1::-1])
                fp = footprint(q.rgba, q.lift, T.shape[1] // PX, T.shape[0] // PX)
                for j, sy in enumerate(rows):
                    for i, sx in enumerate(cols):
                        if fp[sy, sx] and r.inside(i, j):
                            r.blocked[j, i] = False
            continue
        r.kept.append((k, p.model, (X - cx + first[cx], Y, Z - cz + rowof[cz])))
    return r

def place(r, model, x, z, kind=0, y=0.0, block=True, scale=(1.0, 1.0, 1.0)):
    """A prop at room cell coordinates (x, z: its base, as HGSS's positions), drawn and, unless block is
    False (rugs, mats), blocking the cells it stands on."""
    W, H = r.full_size()
    p = Prop(model, (x, y, z), scale, kind).draw(W, H)
    r.add(p)
    if block:
        r.blocked |= footprint(r.crop(p.rgba), r.crop(p.lift), r.W, r.H)
    return p

def finish(r, extra=()):
    """Draw the props compose() kept at their new places, then any extra (model, x, z, kwargs)."""
    for k, model, (x, y, z) in r.kept:
        place(r, model, x, z, kind=r.kind, y=y, block=False)
    for model, x, z, kw in extra:
        place(r, model, x, z, **kw)
    return r

def paint(r, dst, src):
    """Copy terrain cells: dst and src are lists of (x, y) room cells (before props are drawn)."""
    base = r.lower.copy()
    for (dx, dy), (sx, sy) in zip(dst, src):
        r.lower[dy * PX:(dy + 1) * PX, dx * PX:(dx + 1) * PX] = base[sy * PX:(sy + 1) * PX, sx * PX:(sx + 1) * PX]
    r._full = r.lower.copy() if r.origin == (0, 0) and r._full.shape == r.lower.shape else r._full
