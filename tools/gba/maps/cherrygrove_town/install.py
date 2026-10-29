"""Encode Cherrygrove's new cells into native metatiles and install them, keeping every other cell, every
other map on CherrygrovePrimary and both seams exactly as they draw.

Tilesets. Cherrygrove moves to its own copy of CherrygrovePrimary (cherrygrove_town, the way Routes 30 and 31
have theirs). The copy keeps every metatile id and every tile the town's camera draws (its own cells, Route
29's window, Route 30's band, the sea's animated tiles 1-87, all it draws of the 92) and frees the other
slots for the town's new art; its sea animation writes those 87 tiles only. CherrygrovePrimary changes only
where Route 29 draws the town. The two regional preview maps draw a frozen copy of Cherrygrove's secondary
at the base revision (cherrygrove_preview), so the town's sheet takes the slots only they used.

Folds. When the slots run out, a new texture tile may take an existing one up to k pixels away (k as small
as fits, FOLD_STEPS). Edge and feature cells (shore, beach edges, paths, boats, pier, flowers, the Center's
and Mart's lawn) fold only a ground texture's inner dither, to another tone of that texture (DITHER_K);
the Center and Mart art, doors, and cells Route 29 or Route 30 also draw never fold.

Ids. Unchanged cells keep theirs. New cells Route 29 can see (its camera draws Cherrygrove's last 8 columns
with CherrygrovePrimary and its own secondary) take primary metatile ids no map draws, defined the same in
CherrygrovePrimary and the copy, from tile slots free in both (or secondary slots free in both Cherrygrove's
sheet and Route 29's, written to both). New cells Route 30 can see take the ids its pack gave them (Route 30's
secondary defines the same ids, source/pack/mirror-ids.json). The rest take Cherrygrove secondary ids after
those.

Layers. Each 8x8 quadrant splits by palette: below, a palette holding the rest (the lawn's bank 0, the tree
palette 3 or the blossom palette 10, both given the lawn's two tones and its rim tone in slots no map draws,
or the sea's own animated tiles under a cliff's foot); above, the rock (bank 5), the trees (3) or the
blossoms (10). A walkable cell under a crown keeps the crown above (layer type normal: the player walks
behind it). Tiles the town already has are reused in any flip; new ones take sheet slots nothing drawn uses.
"""
from __future__ import annotations
import json, re, shutil, struct
from pathlib import Path
import numpy as np
from PIL import Image

import base as B
from base import Rf, W, H, rgb5, entry
import elements as E
import rock as Rk                                    # noqa: E402
from tiles import Tileset                            # noqa: E402

PAL5_RAMP = (2, 3, 4, 6, 7, 11, 12)                  # the rock ramp
PAL5_EXTRA = {13: Rk.BORDER_GRAY, 15: Rk.FRINGE_RIM}   # with the rock, above the lawn (14 is the pier's)
LAWN_EXT = {12: (104, 208, 152), 13: (104, 200, 152), 15: (88, 176, 136)}   # the lawn in palettes 3 and 10
SEA = {(0, 0): 0x03B, (1, 0): 0x03A, (0, 1): 0x04C, (1, 1): 0x04B}
TOWN_SYM, TOWN_DIR = 'CherrygroveTownPrimary', 'cherrygrove_town'
TP_ANIM = 87                                         # the sea tiles the town draws (1-87): its copy animates only these
PREVIEW_SYM, PREVIEW_DIR = 'CherrygrovePreview', 'cherrygrove_preview'   # the two regional previews' secondary, frozen
R29_SHEET = 'data/tilesets/secondary/claude_route29/tiles.png'

# --------------------------------------------------------------------------- what is drawn, what is free
def others_ids(engine):
    """Primary metatile ids every map but Cherrygrove draws (maps on CherrygrovePrimary and on its copies)."""
    ids = set()
    for lid, l in B.layouts(engine).items():
        if lid != 'LAYOUT_CHERRYGROVE_CITY' and l.get('primary_tileset', '').startswith('gTileset_Cherrygrove'):
            ids |= B.map_ids(engine, l)
    return {m for m in ids if m < 512}

def target_words(town, cv):
    w = town.words.copy()
    for x, r in cv.changed:
        if 0 <= r < H:
            w[r, x] = -1
    for (x, r), (m, ce) in cv.kit.items():
        w[r, x] = m | (ce[0] << 10) | (ce[1] << 12)
    return w

def neighbour_ids(engine):
    """Ids the town's camera draws of its neighbours, with its own tilesets: Route 29's window, Route 30's band."""
    L = B.layouts(engine)
    l = L['LAYOUT_CHERRYGROVE_ROUTE29_APPROACH']
    ids = set((B.words_of((engine / l['blockdata_filepath']).read_bytes(), l['width'])[:, :Rf.WINDOW + 1] & 1023).ravel().tolist())
    l = L['LAYOUT_CHERRYGROVE_ROUTE30_APPROACH']
    ids |= set((B.words_of((engine / l['blockdata_filepath']).read_bytes(), l['width'])[Rf.PAD0 - 2:] & 1023).ravel().tolist())
    return ids

def view_ids(engine, town, cv):
    """Ids the town's camera draws: its kept cells, its border and its neighbours' strips."""
    ids = {int(v) & 1023 for v in target_words(town, cv).ravel() if v >= 0}
    ids |= {v & 1023 for v in struct.unpack('<4H', (town.base / 'data/layouts/CherrygroveCity/border.bin').read_bytes())}
    return ids | neighbour_ids(engine)

def free_primary_ids(engine, town, cv):
    kept = others_ids(engine) | view_ids(engine, town, cv) | set(cv.fixed.values())
    return [m for m in range(1, 512) if m not in kept]

def free_cp_tiles(engine, town, cv):
    """CherrygrovePrimary tile slots no drawn metatile uses (any map on it, the town as installed, the sea
    animation's tiles 1-92)."""
    L = B.layouts(engine)
    pb = town.t.blocks[0]
    ref = set(range(0, 93))
    w = target_words(town, cv)
    for lid, l in L.items():
        if lid != 'LAYOUT_CHERRYGROVE_CITY' and l.get('primary_tileset') != 'gTileset_CherrygrovePrimary':
            continue
        if lid == 'LAYOUT_CHERRYGROVE_CITY':
            ids = {int(v) & 1023 for v in w.ravel() if v >= 0}
            sm = town.t.blocks[1]
        else:
            ids = B.map_ids(engine, l)
            sm = B.metatiles_of(B.tileset_dir(engine, l['secondary_tileset']))
        for m in ids:
            blk = pb[m] if m < 512 else (sm[m - 512] if m - 512 < len(sm) else ())
            ref |= {e & 1023 for e in blk if (e & 1023) < 512}
    return [i for i in range(512) if i not in ref]

def free_tp_tiles(engine, town, cv):
    """The town's copy: primary tile slots its camera does not draw (kept cells, border, neighbours' strips,
    the sea animation's tiles 1-TP_ANIM, all the town draws of CherrygrovePrimary's 1-92)."""
    pb, sb = town.t.blocks
    ref = set(range(0, TP_ANIM + 1))
    for m in view_ids(engine, town, cv) | set(SEA.values()):
        blk = pb[m] if m < 512 else (sb[m - 512] if m - 512 < B.OWN else ())
        ref |= {e & 1023 for e in blk if (e & 1023) < 512}
    assert not ref & set(range(TP_ANIM + 1, 93)), ('the town draws a sea tile its copy does not animate', sorted(ref & set(range(TP_ANIM + 1, 93))))
    return [i for i in range(512) if i not in ref]

DOOR_SLOTS = range(496, 512)                          # tiles 1008-1023: field_door.c draws the door frames there

def free_secondary_tiles(engine, town, cv):
    """Cherrygrove secondary sheet slots nothing drawn with it uses (the metatiles its camera draws; the
    preview maps draw a frozen copy, register_preview), then the sheet's growth to 496: the last 16 slots are
    the door animations' (DOOR_SLOTS)."""
    used = view_ids(engine, town, cv)
    pb, sb = town.t.blocks
    ref = {0}
    for m in used:
        blk = pb[m] if m < 512 else (sb[m - 512] if m - 512 < B.OWN else ())
        ref |= {(e & 1023) - 512 for e in blk if (e & 1023) >= 512}
    n = len(town.t.tiles[1])
    return [i for i in range(min(n, DOOR_SLOTS.start)) if i not in ref] + list(range(n, DOOR_SLOTS.start))

def free_route29_tiles(engine, town, cv):
    """Route 29's secondary sheet slots its map, its border and its window on the town do not draw."""
    l = B.layouts(engine)['LAYOUT_CHERRYGROVE_ROUTE29_APPROACH']
    d = town.base / 'data/tilesets/secondary/claude_route29'
    ids = B.map_ids(engine, l) | {int(v) & 1023 for v in target_words(town, cv)[:, B.R29_SEEN.start:].ravel() if v >= 0}
    sm, pb = B.metatiles_of(d), town.t.blocks[0]
    ref = {0}
    for m in ids:
        blk = pb[m] if m < 512 else (sm[m - 512] if m - 512 < len(sm) else ())
        ref |= {(e & 1023) - 512 for e in blk if (e & 1023) >= 512}
    return [i for i in range(512) if i not in ref]

# --------------------------------------------------------------------------- palettes
def palettes(engine, town, cv):
    """Write CherrygrovePrimary's palettes 3 and 5, the town's palette 10 and Route 29's (identical to the
    town's) from the base revision with the new slots, and the town's banks its art fills anew (cv.pals,
    secondary), after checking no map draws those slots."""
    pri = engine / 'data/tilesets/primary/cherrygrove'
    bpri = town.base / 'data/tilesets/primary/cherrygrove'
    sec_banks, tp_banks = tuple(b for b in cv.pals if b >= 6), tuple(b for b in cv.pals if b < 6)
    used = drawn_slots(engine, town, cv, (3, 5, 10))
    used.update(drawn_slots(engine, town, cv, sec_banks, secondary='gTileset_Cherrygrove'))
    used.update(view_slots(engine, town, cv, tp_banks))
    for bank, slots in ((5, set(PAL5_RAMP) | set(PAL5_EXTRA)), (3, set(LAWN_EXT)), (10, set(LAWN_EXT))) + tuple(
            (b, set(range(1, len(c) + 1))) for b, c in cv.pals.items()):
        assert not used[bank] & slots, ('palette slots in use', bank, sorted(used[bank] & slots))
    for b in range(16):                              # every run starts from the base town's palettes
        f = f'data/tilesets/secondary/cherrygrove/palettes/{b:02d}.pal'
        shutil.copyfile(town.base / f, engine / f)
    for b in sec_banks:                              # the copy's banks: write_town_primary
        (engine / f'data/tilesets/secondary/cherrygrove/palettes/{b:02d}.pal').write_text(B.jasc(bank_pal(cv.pals[b])))
    p5 = B.read_pal(bpri / 'palettes/05.pal')
    for s, c in list(zip(PAL5_RAMP, Rk.ROCK_RAMP)) + list(PAL5_EXTRA.items()):
        p5[s] = B.gba(c)
    (pri / 'palettes/05.pal').write_text(B.jasc(p5))
    p3 = B.read_pal(bpri / 'palettes/03.pal')
    for s, c in LAWN_EXT.items():
        p3[s] = B.gba(c)
    (pri / 'palettes/03.pal').write_text(B.jasc(p3))
    for d in ('cherrygrove', 'claude_route29'):
        p10 = B.read_pal(town.base / f'data/tilesets/secondary/{d}/palettes/10.pal')
        for s, c in LAWN_EXT.items():
            p10[s] = B.gba(c)
        (engine / f'data/tilesets/secondary/{d}/palettes/10.pal').write_text(B.jasc(p10))
    out = {b: B.read_pal(bpri / f'palettes/{b:02d}.pal') for b in range(6)}
    out.update({b: B.read_pal(town.base / f'data/tilesets/secondary/cherrygrove/palettes/{b:02d}.pal') for b in range(6, 13)})
    out.update({3: p3, 5: p5, 10: B.read_pal(engine / 'data/tilesets/secondary/cherrygrove/palettes/10.pal')})
    out.update({b: bank_pal(c) for b, c in cv.pals.items()})
    return out

def bank_pal(cols):
    assert len(cols) <= 15, ('a bank of more than 15 colours', len(cols))
    return [(0, 0, 0)] + [tuple(c) for c in cols] + [(0, 0, 0)] * (15 - len(cols))

def view_slots(engine, town, cv, banks):
    """Palette slots the town's camera draws in banks of its own copy (its kept cells, its border, its
    neighbours' strips)."""
    pb, sb = town.t.blocks
    out = {b: set() for b in banks}
    for m in view_ids(engine, town, cv):
        blk = pb[m] if m < 512 else (sb[m - 512] if m - 512 < B.OWN else ())
        for e in blk:
            if e and (e >> 12) in out:
                i = e & 1023
                tiles = town.t.tiles[int(i >= 512)]
                j = i - 512 if i >= 512 else i
                if j < len(tiles):
                    out[e >> 12] |= {v % 16 for v in tiles[j]}
    return {b: s - {0} for b, s in out.items()}

def drawn_slots(engine, town, cv, banks, secondary=None):
    """Palette slots any map on CherrygrovePrimary (and on the given secondary) draws in the given banks: every
    metatile of its map and border, its tiles read from the sheet that map draws them from (the town: the
    cells it keeps, at its base revision)."""
    L = B.layouts(engine)
    ptiles = B.tiles_of(town.base / 'data/tilesets/primary/cherrygrove')
    pb = town.t.blocks[0]
    out = {b: set() for b in banks}
    for lid, l in L.items():
        if lid != 'LAYOUT_CHERRYGROVE_CITY' and l.get('primary_tileset') != 'gTileset_CherrygrovePrimary':
            continue
        if secondary and l['secondary_tileset'] != secondary:
            continue
        d = B.tileset_dir(engine, l['secondary_tileset'])
        root = town.base if d.name in ('cherrygrove', 'claude_route29') else engine
        d = root / 'data/tilesets/secondary' / d.name
        stiles, sm = B.tiles_of(d), B.metatiles_of(d)
        if lid == 'LAYOUT_CHERRYGROVE_CITY':
            ids = {int(v) & 1023 for v in target_words(town, cv).ravel() if v >= 0}
            ids |= {v & 1023 for v in struct.unpack('<4H', (town.base / 'data/layouts/CherrygroveCity/border.bin').read_bytes())}
        else:
            ids = B.map_ids(engine, l)
        for m in ids:
            blk = pb[m] if m < 512 else (sm[m - 512] if m - 512 < len(sm) else ())
            for e in blk:
                if e and (e >> 12) in out:
                    i = e & 1023
                    tl = ptiles[i] if i < 512 else (stiles[i - 512] if i - 512 < len(stiles) else None)
                    if tl is not None:
                        out[e >> 12] |= set(np.unique(tl).tolist())
    return {b: s - {0} for b, s in out.items()}

# --------------------------------------------------------------------------- encoding
class Encoder:
    """Tiles and metatiles for new cells. Modes: None, the town's copy and its secondary; 'primary', slots
    free in CherrygrovePrimary and the copy; 'shared', those or secondary slots free in Cherrygrove's sheet
    and Route 29's."""
    def __init__(self, engine, town, cv, pals):
        self.town, self.pals = town, pals
        self.index = {b: self._index(p) for b, p in pals.items()}
        self.ramp5 = {tuple(int(v) >> 3 for v in c) for c in Rk.ROCK_RAMP}
        self.extra5 = {tuple(int(v) >> 3 for v in c) for c in PAL5_EXTRA.values()}
        self.sentinel = tuple(v >> 3 for v in E.SENTINEL)
        self.family = {tuple(int(v) >> 3 for v in c): f for f, t in E.G.textures().items()   # the ground's dither tones
                       if f in (E.G.GRASS, E.G.PATH, E.G.SAND) for c in np.unique(t.reshape(-1, 3), axis=0)}
        t = town.t
        have = [np.array(x, np.uint8).reshape(8, 8) & 15 for x in t.tiles[0]] + [np.array(x, np.uint8).reshape(8, 8) & 15 for x in t.tiles[1]]
        self.have_ix = list(range(len(t.tiles[0]))) + [512 + i for i in range(len(t.tiles[1]))]
        self.sfree = free_secondary_tiles(engine, town, cv)
        tp = free_tp_tiles(engine, town, cv)
        self.cpfree = [i for i in free_cp_tiles(engine, town, cv) if i in set(tp)]
        self.tpfree = [i for i in tp if i not in set(self.cpfree)] + self.cpfree   # the copy's own slots first
        self.r29free = set(free_route29_tiles(engine, town, cv))
        # a slot about to be written is not reused, nor one the sea animation rewrites (tiles 1-92, every one
        # of them changing between frames)
        writable = set(tp) | {512 + i for i in self.sfree} | set(range(1, 93))
        keep = [k for k, i in enumerate(self.have_ix) if i not in writable]
        have = np.array(have)[keep]; self.have_ix = [self.have_ix[k] for k in keep]
        self.flipped = np.stack([have, have[:, :, ::-1], have[:, ::-1, :], have[:, ::-1, ::-1]], 1)
        self.placed, self.lookup = {}, {}
        self.cp_used, self.shared = set(), set()     # written to CherrygrovePrimary too / to Route 29's sheet too
        self.budget = dict(copy=len(self.tpfree), both_primaries=len(self.cpfree), secondary=len(self.sfree))
        self.fold_k, self.foldable, self.folded = 0, False, 0   # see near()
    @staticmethod
    def _index(pal):
        out = {}
        for i, c in enumerate(pal[1:], 1):
            out.setdefault(tuple(int(v) >> 3 for v in c), i)
        return out
    def reuse(self, px5, care, bank, opaque, only):
        pal = np.array([tuple(int(v) >> 3 for v in c) for c in self.pals[bank]])
        col = pal[self.flipped]
        ok = ((col == px5[None, None]).all(-1) & (self.flipped > 0) | ~care[None, None]).all((2, 3))
        if not opaque:
            ok &= ((self.flipped == 0) | care[None, None]).all((2, 3))
        for k, f in np.argwhere(ok):
            if not only or self.have_ix[k] < 512:
                return self.have_ix[k], int(f)
        return None
    def near(self, px5, care, bank, opaque):
        """A tile in this bank (the town's or one placed for it) within fold_k pixels of these, with the same
        silhouette: the texture-family fold (docs/GBA_MAP_RECONSTRUCTION.md, native visual cleanup 2-3). In
        an edge or feature cell (foldable == 'texture') only a dither pixel inside one ground texture moves,
        to another tone of that texture: rims, foam, outlines and art stay exact."""
        pal = np.array([tuple(int(v) >> 3 for v in c) for c in self.pals[bank]])
        if self.foldable == 'texture':
            fam = np.array([[self.family.get(tuple(int(v) for v in px5[y, x]), -1) for x in range(8)] for y in range(8)])
            p = np.pad(fam, 1, mode='edge')             # (the tile's own edge stands in for its neighbour's)
            inner = (fam >= 0) & (p[:-2, 1:-1] == fam) & (p[2:, 1:-1] == fam) & (p[1:-1, :-2] == fam) & (p[1:-1, 2:] == fam)
            pal_fam = np.array([self.family.get(tuple(int(v) for v in c), -1) for c in pal])
        stacks = [(self.flipped, self.have_ix)]
        if self.placed:
            ids = list(self.placed)
            p = np.array([self.placed[i] for i in ids])
            stacks.append((np.stack([p, p[:, :, ::-1], p[:, ::-1, :], p[:, ::-1, ::-1]], 1), ids))
        best = None
        for arr, ids in stacks:
            op = arr > 0
            if opaque:
                shape_ok = (op | ~care[None, None]).all((2, 3))
            else:
                shape_ok = (op == care[None, None]).all((2, 3))
            moved = (pal[arr] != px5[None, None]).any(-1) & care[None, None]
            diff = moved.sum((2, 3))
            if self.foldable == 'texture':
                shape_ok &= ~(moved & ~(inner[None, None] & (pal_fam[arr] == fam[None, None]))).any((2, 3))
            diff = np.where(shape_ok, diff, 99)
            k, f = np.unravel_index(int(np.argmin(diff)), diff.shape)
            limit = DITHER_K if self.foldable == 'texture' else self.fold_k
            if diff[k, f] <= limit and (best is None or diff[k, f] < best[0]):
                best = (int(diff[k, f]), ids[k], int(f))
        return best
    def put(self, ix, only):
        for f in range(4):
            v = ix[:, ::-1] if f & 1 else ix
            v = v[::-1] if f & 2 else v
            hit = self.lookup.get(v.tobytes())
            if hit is not None and (not only or hit in self.cp_used or (only == 'shared' and hit in self.shared)):
                return hit, f
        dual = next((s for s in self.sfree if s in self.r29free), None) if only == 'shared' else None
        if dual is not None:
            self.sfree.remove(dual); i = 512 + dual; self.shared.add(i)
        elif only:
            assert self.cpfree, 'no tile slots free in both primaries'
            i = self.cpfree.pop(0); self.tpfree.remove(i); self.cp_used.add(i)
        elif self.sfree:
            i = 512 + self.sfree.pop(0)
        else:
            assert self.tpfree, 'no free tile slots in the town\'s tilesets'
            i = self.tpfree.pop(0)
            if i in self.cpfree:
                self.cpfree.remove(i)
        self.placed[i] = ix.copy(); self.lookup[ix.tobytes()] = i
        return i, 0
    def tile(self, px5, care, bank, opaque, only):
        hit = self.reuse(px5, care, bank, opaque, only)
        if hit:
            return entry(hit[0], hit[1], bank)
        # the same pixels may already exist as a tile in another bank that holds these colours
        need = {tuple(int(v) for v in px5[y, x]) for y, x in zip(*np.nonzero(care))}
        for b in self.index:
            if b != bank and need <= set(self.index[b]) and not (only and b >= 6 and b != 10):
                hit = self.reuse(px5, care, b, opaque, only)
                if hit:
                    return entry(hit[0], hit[1], b)
        if self.fold_k and self.foldable and not only:
            hit = self.near(px5, care, bank, opaque)
            if hit:
                self.folded += hit[0]
                return entry(hit[1], hit[2], bank)
        ix = np.zeros((8, 8), np.uint8) + (1 if opaque else 0)
        idx = self.index[bank]
        for yy, xx in zip(*np.nonzero(care)):
            ix[yy, xx] = idx[tuple(int(v) for v in px5[yy, xx])]
        t, f = self.put(ix, only)
        return entry(t, f, bank)
    def quadrant(self, px5, objmask, sea_id, walk_behind, only):
        """(bottom entry, top entry) for one 8x8 quadrant."""
        keys = [[tuple(int(v) for v in px5[yy, xx]) for xx in range(8)] for yy in range(8)]
        wet = np.array([[k == self.sentinel for k in row] for row in keys])
        rocky = any(k in self.ramp5 for row in keys for k in row)
        if wet.any():
            up = ~wet
            need = {keys[y][x] for y, x in zip(*np.nonzero(up))}
            over_sea = (5,) + (() if only else (4, 1, 0, 3, 2, 6, 7, 8, 9, 10, 11, 12))   # the rock; the shore's foam and sand
            bank = next((b for b in over_sea if need <= set(self.index[b])), None)
            if bank is not None:
                top = self.tile(px5, up, bank, False, only) if up.any() else 0
                return self.town.t.blocks[0][sea_id][self.q], top
            assert not only, ('art over the sea outside any bank', need)
            # art over the sea in two banks: the sea there stays as its first frame, drawn below like the rest
            q = self.q
            still = rgb5(self.town.render_id(sea_id))[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            px5 = px5.copy(); px5[wet] = still[wet]
            keys = [[tuple(int(v) for v in px5[yy, xx]) for xx in range(8)] for yy in range(8)]
            rocky = any(k in self.ramp5 for row in keys for k in row)
        # one bank holds the whole quadrant: one tile, nothing above (but a crown the player walks behind)
        lows_one = (0, 3, 10, 1, 2, 4) + (() if only else (5, 6, 7, 8, 9, 11, 12))
        if not walk_behind:
            allk = {k for row in keys for k in row}
            one = next((b for b in lows_one if allk <= set(self.index[b]) and not (only and b == 5)), None)
            if one is not None:
                return self.tile(px5, np.ones((8, 8), bool), one, True, only), 0
        # the lawn's banks first, then any other the ground may keep from the base town (Route 29's columns:
        # the primary's banks and 10, which Route 29 shares)
        lows = (0, 3, 10, 1, 2, 4) + (() if only else (6, 7, 8, 9, 11, 12))
        orders = [(low, objmask) for low in lows] if walk_behind else []   # the crown above the player
        for low in lows:
            inlow = np.array([[k in self.index[low] and not (rocky and low == 0 and k in self.extra5) for k in row] for row in keys])
            orders.append((low, ~inlow))
        for low, up in orders:
            lowpix = ~up
            if not all(keys[y][x] in self.index[low] for y, x in zip(*np.nonzero(lowpix))):
                continue
            need = {keys[y][x] for y, x in zip(*np.nonzero(up))}
            tops = (3, 10, 5) + (() if only else (1, 2, 4, 6, 7, 8, 9, 11, 12))   # any other: the art the cell keeps
            bank = next((b for b in tops if need <= set(self.index[b])), None) if need else None
            if need and bank is None:
                continue
            if only and bank == 5:
                continue
            bottom = self.tile(px5, lowpix, low, True, only)
            top = self.tile(px5, up, bank, False, only) if need else 0
            return bottom, top
        raise AssertionError(('no palette split for a quadrant', walk_behind))
    def metatile(self, comp, objmask, sea_id, walk_behind, only, mb=B.MB_NORMAL):
        px5 = rgb5(comp)
        ent = [0] * 8
        for q in range(4):
            self.q = q
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ent[q], ent[4 + q] = self.quadrant(px5[sl], objmask[sl], sea_id, walk_behind, only)
        layer = B.NORMAL if walk_behind else B.COVERED
        return tuple(ent), mb | (layer << 12)

def composite(g, tp):
    px = g.copy(); a = tp[..., 3] > 0; px[a] = tp[a, :3]
    return px

def cell_info(town, cv, x, r):
    g, tp = cv.layers(x, r)
    comp = composite(g, tp)
    wet = (comp == E.SENTINEL).all(-1).any()
    walkable = (cell_bits(cv, x, r) >> 10) & 3 == 0
    walk_behind = walkable and (tp[..., 3] > 0).any()
    return comp, tp[..., 3] > 0, SEA[(x % 2, r % 2)] if wet else None, walk_behind

def base_mb(town, x, r):
    """A cell's behaviour in the base town (the pond stays ocean water, as the owner's town has it)."""
    return town.attr(int(town.words[r, x]) & 1023) & 0xFF if 0 <= r < H else B.MB_NORMAL

def cell_mb(cv, x, r):
    """The behaviour a cell installs with: the base town's, unless an element changes it (cv.traverse)."""
    t = cv.traverse.get((x, r))
    return t[2] if t else base_mb(cv.town, x, r)

def cell_bits(cv, x, r):
    """The collision and elevation bits a cell installs with (map word bits 10-15)."""
    t = cv.traverse.get((x, r))
    return (t[0] << 10) | (t[1] << 12) if t else int(cv.town.words[r, x]) & 0xFC00

# --------------------------------------------------------------------------- writing
def primary_cells(cv):
    return sorted((c for c in cv.changed if c[0] in B.R29_SEEN and 0 <= c[1] < H), key=lambda c: (c[1], c[0]))

def encode_primary(engine, town, cv, enc):
    """Route 29's columns: primary metatiles at ids no map draws. Cells Route 30 also sees draw primary
    tiles only (its pack copies them by id into its own primary); the rest may also take secondary slots
    free in both Cherrygrove's sheet and Route 29's."""
    free = free_primary_ids(engine, town, cv)
    seen = lambda c: c[1] < B.R30_SEEN[0] and c[0] in B.R30_SEEN[1]
    cells = sorted(primary_cells(cv), key=lambda c: (not seen(c), c[1], c[0]))
    ids, defs = {}, {}
    for x, r in cells:
        comp, obj, sea, wb = cell_info(town, cv, x, r)
        key = enc.metatile(comp, obj, sea, wb, 'primary' if seen((x, r)) else 'shared', cell_mb(cv, x, r))
        if key not in defs:
            assert len(defs) < len(free), 'no free primary metatile ids'
            defs[key] = free[len(defs)]
        ids[(x, r)] = defs[key]
    return ids, {m: k for k, m in defs.items()}

def write_sheet(path, base_path, placed):
    """A tile sheet from its base revision with the placed tiles (slot: 8x8 indices), grown as needed."""
    im = Image.open(base_path); sheet = np.array(im)
    if placed and max(placed) >= sheet.shape[0] // 8 * 16:
        sheet = np.concatenate([sheet, np.zeros(((max(placed) // 16 + 1) * 8 - sheet.shape[0], 128), sheet.dtype)], 0)
    for i, tl in placed.items():
        sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = tl
    path.parent.mkdir(parents=True, exist_ok=True)
    o = Image.fromarray(sheet.astype(np.uint8), 'P'); o.putpalette(im.getpalette()); o.save(path, bits=4)

def write_metatiles(d, blocks, attrs):
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in blocks))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(attrs), *attrs))

def primary_blocks(town, pdefs):
    blocks, attrs = list(town.t.blocks[0]), list(town.t.attrs[0])
    for m, (ent, a) in pdefs.items():
        blocks[m], attrs[m] = ent, a
    return blocks, attrs

def write_primary(engine, town, enc, pdefs):
    """CherrygrovePrimary: the new metatiles of Route 29's columns and their tiles; Route 29's sheet: the
    tiles they share."""
    pri, bpri = engine / 'data/tilesets/primary/cherrygrove', town.base / 'data/tilesets/primary/cherrygrove'
    write_metatiles(pri, *primary_blocks(town, pdefs))
    write_sheet(pri / 'tiles.png', bpri / 'tiles.png', {i: enc.placed[i] for i in enc.cp_used})
    write_sheet(engine / R29_SHEET, town.base / R29_SHEET, {i - 512: enc.placed[i] for i in enc.shared})

def write_town_primary(engine, town, enc, pdefs, cv, tp_defs):
    """The town's copy: CherrygrovePrimary's metatiles and palettes, its sheet with every new primary tile,
    the door metatiles it redraws at their own ids (tp_defs) and the banks only the town draws (cv.pals)."""
    d, bpri = engine / 'data/tilesets/primary' / TOWN_DIR, town.base / 'data/tilesets/primary/cherrygrove'
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    blocks, attrs = primary_blocks(town, pdefs)
    for m, (ent, a) in tp_defs.items():
        blocks[m], attrs[m] = ent, a
    write_metatiles(d, blocks, attrs)
    write_sheet(d / 'tiles.png', bpri / 'tiles.png', {i: tl for i, tl in enc.placed.items() if i < 512})
    for p in sorted((engine / 'data/tilesets/primary/cherrygrove/palettes').glob('*.pal')):
        shutil.copyfile(p, d / 'palettes' / p.name)
    for b, cols in cv.pals.items():
        if b < 6:
            (d / 'palettes' / f'{b:02d}.pal').write_text(B.jasc(bank_pal(cols)))

TOWN_ANIM = '''static void TilesetAnim_CherrygroveTownPrimary(u16 timer);
void InitTilesetAnim_CherrygroveTownPrimary(void)
{
    sPrimaryTilesetAnimCounter = 0;
    sPrimaryTilesetAnimCounterMax = 256;
    sPrimaryTilesetAnimCallback = TilesetAnim_CherrygroveTownPrimary;
}
static void TilesetAnim_CherrygroveTownPrimary(u16 timer)
{
    if (timer % 16 == 1)
        AppendTilesetAnimToBuffer(gTilesetAnims_Cherrygrove_Sea[(timer / 16) % 8], (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(1)), TP_ANIM * TILE_SIZE_4BPP);
}
'''.replace('TP_ANIM', str(TP_ANIM))

def register_town(engine):
    """The copy's tileset (CherrygrovePrimary's sea animation over the tiles the town draws, TP_ANIM) and the
    town's layout on it."""
    sym, name = TOWN_SYM, TOWN_DIR
    h = engine / 'src/data/tilesets/headers.h'; s = h.read_text()
    if f'gTileset_{sym} =' not in s:
        line = next(l for l in s.splitlines(True) if l.startswith('const struct Tileset gTileset_CherrygrovePrimary ='))
        s = s.replace(line, line + line.replace('CherrygrovePrimary =', f'{sym} =').replace('_CherrygrovePrimary,', f'_{sym},'), 1)
    s = re.sub(r'(const struct Tileset gTileset_%s = .*?\.callback = )\w+' % sym, r'\1InitTilesetAnim_%s' % sym, s, count=1)
    h.write_text(s)
    a = engine / 'src/tileset_anims.c'; s = a.read_text()
    s = re.sub(r'static void TilesetAnim_CherrygroveTownPrimary\(u16 timer\);.*?\n}\n.*?\n}\n', '', s, count=1, flags=re.S)
    s = s.replace('// End Claude Cherrygrove sea', TOWN_ANIM + '// End Claude Cherrygrove sea', 1)
    a.write_text(s)
    d = engine / 'include/tileset_anims.h'; s = d.read_text()
    if f'InitTilesetAnim_{sym}(void);' not in s:
        s = s.replace('void InitTilesetAnim_CherrygrovePrimary(void);\n', f'void InitTilesetAnim_CherrygrovePrimary(void);\nvoid InitTilesetAnim_{sym}(void);\n', 1)
        d.write_text(s)
    g = engine / 'src/data/tilesets/graphics.h'; s = g.read_text()
    if f'gTilesetTiles_{sym}[]' not in s:
        s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/primary/{name}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/primary/{name}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
        g.write_text(s)
    m = engine / 'src/data/tilesets/metatiles.h'; s = m.read_text()
    if f'gMetatiles_{sym}[]' not in s:
        s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/primary/{name}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/primary/{name}/metatile_attributes.bin");\n'
        m.write_text(s)
    lj = engine / 'data/layouts/layouts.json'; s = lj.read_text()
    s2 = re.sub(r'("id": "LAYOUT_CHERRYGROVE_CITY",(?:[^{}]*?)"primary_tileset": )"gTileset_CherrygrovePrimary"', r'\1"gTileset_%s"' % sym, s, count=1)
    if s2 != s:
        lj.write_text(s2)
    assert B.layouts(engine)['LAYOUT_CHERRYGROVE_CITY']['primary_tileset'] == f'gTileset_{sym}'

def register_preview(engine, town):
    """The two regional preview maps (dev warps from Sandgem and Floccesy) draw Cherrygrove's secondary as
    it was at the base revision, from a frozen copy, so the town's sheet can take the slots only they used."""
    sym, d = PREVIEW_SYM, engine / 'data/tilesets/secondary' / PREVIEW_DIR
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(town.base / 'data/tilesets/secondary/cherrygrove', d)
    h = engine / 'src/data/tilesets/headers.h'; s = h.read_text()
    if f'gTileset_{sym} =' not in s:
        line = next(l for l in s.splitlines(True) if l.startswith('const struct Tileset gTileset_Cherrygrove ='))
        s = s.replace(line, line + line.replace('Cherrygrove =', f'{sym} =').replace('_Cherrygrove,', f'_{sym},'), 1)
        h.write_text(s)
    g = engine / 'src/data/tilesets/graphics.h'; s = g.read_text()
    if f'gTilesetTiles_{sym}[]' not in s:
        s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/secondary/{PREVIEW_DIR}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/secondary/{PREVIEW_DIR}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
        g.write_text(s)
    m = engine / 'src/data/tilesets/metatiles.h'; s = m.read_text()
    if f'gMetatiles_{sym}[]' not in s:
        s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/secondary/{PREVIEW_DIR}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/secondary/{PREVIEW_DIR}/metatile_attributes.bin");\n'
        m.write_text(s)
    lj = engine / 'data/layouts/layouts.json'; s = lj.read_text()
    for lid in ('LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_29', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_30'):
        s = re.sub(r'("id": "%s",(?:[^{}]*?)"secondary_tileset": )"gTileset_Cherrygrove"' % lid, r'\1"gTileset_%s"' % sym, s, count=1)
    lj.write_text(s)
    L = B.layouts(engine)
    assert all(L[l]['secondary_tileset'] == f'gTileset_{sym}' for l in ('LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_29', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_30'))

def render(engine, town, cv, img):
    """Before Route 30's pack: the new cells it can see (ground and object layers), and the cells placed by
    primary id (source/seam/)."""
    B.SEAM.mkdir(parents=True, exist_ok=True)
    prim = set(primary_cells(cv))
    cells = sorted((c for c in cv.changed if 0 <= c[1] < H and c not in prim), key=lambda c: (c[1], c[0]))
    lay = [cv.layers(x, r) for x, r in cells]
    seen = lambda x, r: r < B.R30_SEEN[0] and x in B.R30_SEEN[1]
    np.savez_compressed(B.SEAM / 'cherrygrove-cells.npz', cells=np.array(cells), ground=np.array([g for g, _ in lay]),
                        top=np.array([t for _, t in lay]), visible=np.array([seen(x, r) for x, r in cells]))
    kit_json(cv, {})
    (B.SEAM / 'README.md').write_text('Written by tools/gba/maps/cherrygrove_town/town.py: Cherrygrove\'s new cells '
                                      '(ground and object layers, `cherrygrove-cells.npz`), which of them Route 30 can see '
                                      '(`visible`), and the metatiles placed by primary id (`cherrygrove-kit.json`).\n')
    print('rendered', len(cells), 'cells,', sum(seen(x, r) for x, r in cells), 'visible from Route 30;', len(prim), 'in Route 29\'s columns')

def kit_json(cv, pids):
    cells = [[int(x), int(r), int(m), ce[0], ce[1]] for (x, r), (m, ce) in sorted(cv.kit.items())]
    cells += [[int(x), int(r), int(m), int(cv.town.words[r, x] >> 10) & 3, int(cv.town.words[r, x] >> 12)] for (x, r), m in sorted(pids.items())]
    (B.SEAM / 'cherrygrove-kit.json').write_text(json.dumps(dict(
        note='Primary metatiles placed by id: x, row, metatile, collision, elevation.', cells=cells)) + '\n')

# --------------------------------------------------------------------------- checks
def spliced(engine, town, sec, base_sec):
    """A tileset of the engine's secondary sec on CherrygrovePrimary at its base revision (base_sec: the
    secondary at its base revision too)."""
    t = Tileset(town.base if base_sec else engine, sec, 'cherrygrove')
    for k in ('tiles', 'pals', 'blocks', 'attrs'):
        getattr(t, k)[0] = getattr(town.t, k)[0]
    return t

def other_maps_unchanged(engine, town):
    """Every other map on CherrygrovePrimary draws exactly as it did at the base revision."""
    out = {}
    for lid, l in B.layouts(engine).items():
        if lid == 'LAYOUT_CHERRYGROVE_CITY' or l.get('primary_tileset') != 'gTileset_CherrygrovePrimary':
            continue
        sec = B.tileset_dir(engine, l['secondary_tileset']).name
        words = B.words_of((engine / l['blockdata_filepath']).read_bytes(), l['width']).ravel().tolist()
        was = 'cherrygrove' if sec == PREVIEW_DIR else sec       # the previews drew the town's secondary at the base revision
        before = np.array(spliced(engine, town, was, was in ('cherrygrove', 'claude_route29')).map_image(words, l['width']).convert('RGB'))
        after = np.array(Tileset(engine, sec, 'cherrygrove').map_image(words, l['width']).convert('RGB'))
        out[lid] = int((rgb5(before) != rgb5(after)).any(-1).sum())
    assert not any(out.values()), ('another map draws differently', out)
    return out

# --------------------------------------------------------------------------- the doors
DOOR_ANIMS = dict(mart='Mart', center='PokemonCenter', player='PlayerHouse', gold='GoldHouse', neighbor='NeighborHouse', harbor='HarborHouse', garden='GardenHouse')
DOOR_DIR = 'graphics/door_anims/johto_restart'

def door_frames(engine, cv, img, pals):
    """Each house door's open animation, cut from the town as installed: the door's 2x2 block (its cell, the
    cell beside it on the door's side, the row above) in three frames, the panel going dark from its far edge
    (as the town's doors open), every tile in the house's bank (field_door.c draws one layer, one bank per
    tile, each tile the bank of the door's banks that draws it best). field_door.c takes the block's side and
    the banks."""
    src = (engine / 'src/field_door.c').read_text()
    out = {}
    for d in cv.doors:
        x, y = d['cell']; banks = d['banks']
        x0 = (x if d['size'] == 'LEFT' else x - 1) * 16; y0 = (y - 1) * 16
        block = img[y0:y0 + 32, x0:x0 + 32].astype(int)
        px0, py0, px1, py1 = d['panel']
        first = np.array(pals[banks[0]][1:16], int)
        dark = first[int(np.argmin(first.sum(1)))]
        frames = []
        for k in range(3):
            f = block.copy()
            cut = px1 - int(round((px1 - px0) * (k + 1) / 3))
            f[py0 - y0:py1 - y0, cut - x0:px1 - x0] = dark
            frames.append(f)
        data, tile_banks = bytearray(), []
        order = [(cx, cy, q) for cx, cy in ((0, 0), (0, 1), (1, 0), (1, 1)) for q in range(4)]   # top left, bottom left, top right, bottom right
        for k, f in enumerate(frames):
            for i, (cx, cy, q) in enumerate(order):
                t = f[cy * 16 + (q // 2) * 8:cy * 16 + (q // 2) * 8 + 8, cx * 16 + (q % 2) * 8:cx * 16 + (q % 2) * 8 + 8]
                if k == 0:                           # the bank drawing this tile best over all three frames
                    def err(b):
                        pal = np.array(pals[b][1:16], int)
                        return sum(int(((g[cy * 16 + (q // 2) * 8:cy * 16 + (q // 2) * 8 + 8, cx * 16 + (q % 2) * 8:cx * 16 + (q % 2) * 8 + 8][..., None, :] - pal[None, None]) ** 2).sum(-1).min(-1).sum()) for g in frames)
                    tile_banks.append(min(banks, key=err))
                pal = np.array(pals[tile_banks[i]][1:16], int)
                idx = 1 + ((t[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)
                for row in idx:
                    data += bytes(int(row[j]) | (int(row[j + 1]) << 4) for j in range(0, 8, 2))
        name = DOOR_ANIMS[d['name']]
        (engine / DOOR_DIR / f'{name}.4bpp').write_bytes(bytes(data))
        arr = '{' + ','.join([str(b) for b in tile_banks] + ['0'] * 4) + '}'
        src, n = re.subn(r'(static const u8 sRestartDoorPal_%s\[20\] = )\{[^}]*\}' % name, r'\g<1>' + arr, src)
        assert n == 1, ('no palette line for the door', name)
        src, n = re.subn(r'(\.metatileNum=%d, \.tileset=&gTileset_Cherrygrove, \.sound=DOOR_SOUND_NORMAL, \.size=)DOOR_SIZE_2x2_\w+(, \.tiles=sRestartDoor_%s,)'
                         % (cv.fixed[(x, y)], name), r'\g<1>DOOR_SIZE_2x2_%s\g<2>' % d['size'], src)
        assert n == 1, ('no door table entry', name)
        out[name] = dict(cell=[x, y], size=d['size'], banks=tile_banks, metatile=cv.fixed[(x, y)])
    (engine / 'src/field_door.c').write_text(src)
    return out

# --------------------------------------------------------------------------- the steps
def primary(engine, town, cv, img):
    """Before Route 30's pack: Route 29's columns as primary metatiles, the new palettes."""
    register_preview(engine, town)
    pals = palettes(engine, town, cv)
    enc = Encoder(engine, town, cv, pals)
    pids, pdefs = encode_primary(engine, town, cv, enc)
    write_primary(engine, town, enc, pdefs)
    render(engine, town, cv, img)
    kit_json(cv, pids)
    print('primary:', len(pids), 'cells,', len(pdefs), 'metatiles,', len(enc.cp_used), 'tiles in both primaries,',
          len(enc.shared), 'shared with Route 29')

FOLD_STEPS = tuple(range(9))                         # pixels a texture tile may move to reuse another (near())
DITHER_K = 8                                         # in edge cells, where only a ground texture's inner dither moves

def no_fold(cv):
    """(cells whose tiles never fold, edge cells where only ground dither folds). Never: the shared Center
    and Mart, the doors, the cells Route 30 sees (Route 30's pack encodes them too), Route 29's columns
    (both primaries draw them). Dither only: the edges and features (cv.exact: shore, beach edges, paths,
    boats, pier, flowers, the lawn the Center and Mart redrew)."""
    out = set(cv.fixed)
    out |= {(x, r) for r in range(B.R30_SEEN[0]) for x in B.R30_SEEN[1]}
    out |= {(x, r) for r in range(H) for x in B.R29_SEEN}
    boxes = set()
    for (x0, y0), (w, h) in ((E.CENTER_AT, (5, 5)), (E.MART_AT, (7, 6))):
        boxes |= {(x, r) for x in range(x0, x0 + w) for r in range(y0, y0 + h + 1)}
    return out, (cv.exact | boxes) - out

def encode_all(engine, town, cv, fold_k):
    pals = palettes(engine, town, cv)
    enc = Encoder(engine, town, cv, pals)
    report = dict(budget=dict(enc.budget))
    pids, pdefs = encode_primary(engine, town, cv, enc)
    kit = {(x, r): m for x, r, m, _, _ in json.loads((B.SEAM / 'cherrygrove-kit.json').read_text())['cells'] if (x, r) not in cv.kit}
    assert kit == pids, 'Route 29\'s columns encode differently from the --primary step Route 30\'s pack read'
    report['primary_ids'] = sorted(pdefs)
    # the mirror block: Route 30's band cells and the Cherrygrove cells Route 30 sees
    mid = json.loads((B.R30_ART / 'source/pack/mirror-ids.json').read_text())
    z = np.load(B.R30_ART / 'source/assemble/layers.npz', allow_pickle=True)
    want = z['ground'].copy()
    for k in ('flat', 'objects'):
        a = z[k][..., 3] > 0; want[a] = z[k][a, :3]
    defs = {}
    def define(m, comp, obj, sea, wb, mb=B.MB_NORMAL):
        if m in defs:
            assert defs[m][3] == sea and defs[m][4] == mb and (rgb5(defs[m][0]) == rgb5(comp)).all(), ('one id, two looks', m)
        defs[m] = (comp, obj, wb, sea, mb)
    for k, m in mid['band'].items():
        x, y = map(int, k.split(','))
        px = want[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16]
        define(m, px, (px != px).any(-1), None, False)
    for k, m in mid['other'].items():
        x, r = map(int, k.split(','))
        comp, obj, sea, wb = cell_info(town, cv, x, r)
        define(m, comp, obj, sea, wb, cell_mb(cv, x, r))
    mirror = sorted(defs)
    assert mirror == list(range(Rf.CG_WALL_ID0, Rf.CG_WALL_ID0 + len(mirror))), ('the mirror block is not contiguous', mirror)
    # the door cells keep their ids (the door table's): the copy's primary ones, the secondary's own
    tp_defs, own_defs = {}, {}
    for (x, r), m in sorted(cv.fixed.items()):
        comp, obj, sea, wb = cell_info(town, cv, x, r)
        key = enc.metatile(comp, obj, sea, wb, None, cell_mb(cv, x, r))
        into = tp_defs if m < 512 else own_defs
        k = m if m < 512 else m - 512
        assert m < 512 or k < B.OWN, ('a door id outside the town\'s own metatiles', m)
        assert into.get(k, key) == key, ('one door id, two looks', m)
        into[k] = key
    cell_id = {c: m for c, m in cv.fixed.items()}
    prim = set(pids) | set(cv.fixed)
    for x, r in sorted((c for c in cv.changed if 0 <= c[1] < H and c not in prim), key=lambda c: (c[1], c[0])):
        comp, obj, sea, wb = cell_info(town, cv, x, r)
        mb = cell_mb(cv, x, r)
        m = mid['other'].get(f'{x},{r}')
        if m is None:
            m = next((m for m, d in defs.items() if d[3] == sea and d[2] == wb and d[4] == mb and (rgb5(d[0]) == rgb5(comp)).all()), None)
        if m is None:
            assert not (r < B.R30_SEEN[0] and x in B.R30_SEEN[1]), ('a cell Route 30 can see has no id in its secondary', x, r)
            m = Rf.CG_WALL_ID0 + len(defs); defs[m] = (comp, obj, wb, sea, mb)
        cell_id[(x, r)] = m
    exact, dither = no_fold(cv)
    cells_of = {}
    for c, m in cell_id.items():
        cells_of.setdefault(m, []).append(c)
    enc.fold_k = fold_k
    rows, folded_ids = [], set()
    for m in sorted(defs):
        cs = cells_of.get(m, [])
        enc.foldable = bool(cs) and m not in set(mirror) and all(c not in exact for c in cs) and (
            'texture' if any(c in dither for c in cs) else True)
        before = enc.folded
        rows.append(enc.metatile(defs[m][0], defs[m][1], defs[m][3], defs[m][2], None, defs[m][4]))
        if enc.folded > before:
            folded_ids.add(m)
    enc.foldable = False
    sea = {e for m in SEA.values() for e in town.t.blocks[0][m]}
    for ent, _ in rows + list(pdefs.values()) + list(tp_defs.values()) + list(own_defs.values()):
        assert all(e in sea for e in ent if 1 <= (e & 1023) <= 92 and (e & 1023) not in enc.placed), 'a new metatile draws an animated sea tile outside the sea'
    return dict(pals=pals, enc=enc, report=report, pids=pids, pdefs=pdefs, defs=defs, mirror=mirror, tp_defs=tp_defs,
                own_defs=own_defs, cell_id=cell_id, rows=rows, folded_ids=folded_ids, fold_k=fold_k)

def install(engine, town, cv, img):
    """After Route 30's pack: everything. Texture tiles fold only as far as the tile budget needs."""
    register_preview(engine, town)
    for k in FOLD_STEPS:
        try:
            st = encode_all(engine, town, cv, k)
            break
        except AssertionError as e:
            if 'free tile slots' not in str(e) or k == FOLD_STEPS[-1]:
                raise
    pals, enc, report, pids, pdefs, defs, mirror, tp_defs, own_defs, cell_id, rows = (st[n] for n in (
        'pals', 'enc', 'report', 'pids', 'pdefs', 'defs', 'mirror', 'tp_defs', 'own_defs', 'cell_id', 'rows'))
    report['fold'] = dict(max_pixels_per_tile=st['fold_k'], pixels=enc.folded, metatiles=len(st['folded_ids']))
    report['mirror_ids'] = [mirror[0], mirror[-1]]
    report['secondary_ids'] = [Rf.CG_WALL_ID0, Rf.CG_WALL_ID0 + len(rows) - 1]
    # the tilesets
    write_primary(engine, town, enc, pdefs)
    write_town_primary(engine, town, enc, pdefs, cv, tp_defs)
    sec, bsec = engine / 'data/tilesets/secondary/cherrygrove', town.base / 'data/tilesets/secondary/cherrygrove'
    write_sheet(sec / 'tiles.png', bsec / 'tiles.png', {i - 512: tl for i, tl in enc.placed.items() if i >= 512})
    own_b, own_a = list(town.t.blocks[1])[:B.OWN], list(town.t.attrs[1])[:B.OWN]
    for k, (ent, a) in own_defs.items():
        own_b[k], own_a[k] = ent, a
    write_metatiles(sec, own_b + [r[0] for r in rows], own_a + [r[1] for r in rows])
    register_town(engine)
    report['tiles'] = dict(secondary=len([i for i in enc.placed if i >= 512]) - len(enc.shared), shared_with_route29=len(enc.shared),
                           both_primaries=len(enc.cp_used), copy_only=len([i for i in enc.placed if i < 512]) - len(enc.cp_used))
    report['left'] = dict(copy=len(enc.tpfree), secondary=len(enc.sfree))
    # the map
    w = target_words(town, cv)
    for (x, r), m in list(cell_id.items()) + list(pids.items()):
        w[r, x] = m | cell_bits(cv, x, r)                # the base cell's collision and elevation, or the element's
    assert (w >= 0).all()
    (engine / 'data/layouts/CherrygroveCity/map.bin').write_bytes(struct.pack('<%dH' % w.size, *w.ravel().tolist()))
    report['cells_changed'] = int((w != town.words).sum())
    # checks: every cell of the town draws as composed, every mirror id draws the other map's pixels, Route
    # 29's window on the town draws the same with CherrygrovePrimary, every other map draws as before
    t = Tileset(engine, 'cherrygrove', TOWN_DIR)
    mb = lambda m: t.attrs[int(m >= 512)][m - 512 if m >= 512 else m] & 0xFF
    moved = [[x, r] for r in range(H) for x in range(W) if (x, r) not in cv.kit and (
             (int(w[r, x]) & 0xFC00) != cell_bits(cv, x, r) or mb(int(w[r, x]) & 1023) != cell_mb(cv, x, r))]
    report['traversal_changed'] = sorted([list(c) + list(v) for c, v in cv.traverse.items()])
    assert not moved, ('a cell\'s collision, elevation or behaviour moved', moved[:10], len(moved))
    got = np.array(t.map_image(w.ravel().tolist(), W).convert('RGB'))
    per = (rgb5(got) != rgb5(img)).any(-1).reshape(H, 16, W, 16).sum((1, 3))
    folded = {c for c, m in cell_id.items() if m in st['folded_ids']}
    exact, dither = no_fold(cv)
    bad = [[int(x), int(r)] for r, x in zip(*np.nonzero(per)) if (int(x), int(r)) not in folded or (int(x), int(r)) in exact
           or per[r, x] > 8 * (DITHER_K if (int(x), int(r)) in dither else st['fold_k'])]
    assert not bad, ('cells draw wrongly', bad[:20], len(bad))
    # in the edge cells a fold only moves a ground texture's inner dither to another tone of that texture
    want5, got5 = rgb5(img), rgb5(got)
    fam = lambda c: enc.family.get(tuple(int(v) for v in c), -1)
    for x, r in dither:
        sl = np.s_[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
        for y, xx in zip(*np.nonzero((want5[sl] != got5[sl]).any(-1))):
            a, b = want5[sl][y, xx], got5[sl][y, xx]
            assert fam(a) >= 0 and fam(a) == fam(b), ('an edge cell\'s fold moved more than dither', x, r)
    report['fold']['edge_cells_dither_only'] = len([c for c in dither if per[c[1], c[0]]])
    report['fold']['cells'] = len([1 for r, x in zip(*np.nonzero(per))])
    for m in mirror:
        assert (rgb5(np.array(t.render(m).convert('RGB'))) == rgb5(defs[m][0])).all(), ('mirror id draws wrongly', m)
    t29 = Tileset(engine, 'claude_route29', 'cherrygrove')
    win = w[:, B.R29_SEEN.start:]
    got29 = np.array(t29.map_image(win.ravel().tolist(), win.shape[1]).convert('RGB'))
    assert (rgb5(got29) == rgb5(got.reshape(H * 16, W * 16, 3)[:, B.R29_SEEN.start * 16:])).all(), 'Route 29 draws the town\'s columns differently'
    report['other_maps_differing'] = other_maps_unchanged(engine, town)
    report['doors'] = door_frames(engine, cv, got, pals)
    report['cells_differing_outside_folds'] = 0
    out = B.ART / 'evidence'; out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(got).save(out / 'installed.png')
    (out / 'install.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report))
