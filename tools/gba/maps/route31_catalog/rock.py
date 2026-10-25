"""Route 30's rock: Blackthorn's FRLG terraces, the method the owner accepted for Mahogany and used on
Route 43 (Route 43's elements.frlg_pieces / rock_frlg and assemble.terraces, carried here unchanged in
behaviour for Route 30's frame).

Every HGSS height layer is one Gen 3 terrace. A rock cell (ledger label R: HGSS's wall01 walls,
decoded flat) stands at its rock peak above the floor; every other cell at its ground height. FRLG
General's mountain nine-slice, its over-rock version where an edge drops to a lower terrace, and its
four inner corners, recoloured to the Johto rock ramp, one face per metatile, as a top-layer overlay;
under its clear pixels the bottom carries the plainest 8x8 block of the ground beyond the edge, and its
cast shadow is Cherrygrove's border grey.
"""
from __future__ import annotations
import numpy as np
from PIL import Image

DIRS = dict(n=(0, -1), ne=(1, -1), e=(1, 0), se=(1, 1), s=(0, 1), sw=(-1, 1), w=(-1, 0), nw=(-1, -1))
# The HGSS rock ramp, outline then light to dark (Blackthorn's cliff01gs, decoded).
ROCK_RAMP = [(82, 58, 52), (239, 189, 140), (222, 173, 123), (198, 148, 115), (165, 115, 99), (132, 90, 74), (99, 70, 66)]
BORDER_GRAY = (128, 136, 120)
FRLG_RAMP = {9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6}
FRLG_NINE = {('N', 'W'): 0x68, ('N', 'M'): 0x69, ('N', 'E'): 0x6A, ('M', 'W'): 0x70, ('M', 'M'): 0x71,
             ('M', 'E'): 0x72, ('S', 'W'): 0x78, ('S', 'M'): 0x79, ('S', 'E'): 0x7A}
FRLG_NINE_OVER_ROCK = {('N', 'W'): 0x6B, ('N', 'M'): 0x6C, ('N', 'E'): 0x6D, ('M', 'W'): 0x73, ('M', 'M'): 0x71,
                       ('M', 'E'): 0x75, ('S', 'W'): 0x7B, ('S', 'M'): 0x7C, ('S', 'E'): 0x7D}
FRLG_INNER = dict(se=0xB2, sw=0xB3, ne=0xBA, nw=0xBB)
FRLG_LEDGE = dict(mid=0x87, left=0xB0, right=0xB1)
FRLG_JOIN = dict(w=0x1F1, e=0x1F2)
CLEAR, SHADOW = -1, -2
PLAIN = dict(sand=(8, 8), grass=(16, 0))   # flattest 8x8 block of each Cherrygrove texture

def _tiles(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    return [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]

def frlg_pieces(engine):
    """FRLG General's mountain pieces as index maps into the rock ramp (bank 1 only)."""
    d = engine / 'data/tilesets/primary/general_frlg'
    tiles = _tiles(d)
    blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    def piece(m):
        out = np.full((16, 16), CLEAR, int)
        for li in range(8):
            e = int(blocks[m][li])
            if e >> 12 != 1:
                continue
            t = tiles[e & 1023]
            if e & 0x400: t = t[:, ::-1]
            if e & 0x800: t = t[::-1]
            q = li % 4
            sub = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            for (yy, xx), v in np.ndenumerate(t):
                if v:
                    sub[yy, xx] = FRLG_RAMP.get(int(v), SHADOW)
        return out
    return dict(nine={k: piece(v) for k, v in FRLG_NINE.items()}, rock={k: piece(v) for k, v in FRLG_NINE_OVER_ROCK.items()},
                inner={k: piece(v) for k, v in FRLG_INNER.items()}, ledge={k: piece(v) for k, v in FRLG_LEDGE.items()},
                join={k: piece(v) for k, v in FRLG_JOIN.items()})

def terraces(cells, floor):
    """Terrace level per native cell: a rock cell at its rock peak above the floor (at least 1), every other
    cell at its ground height (the ponds sit below the floor and count as 0)."""
    H, W = len(cells), len(cells[0])
    rock = np.array([[c['lab'] == 'R' for c in row] for row in cells])
    d = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d[y, x] = max(1, round(c['peak']) - floor) if rock[y, x] else max(0, round(c['ground']) - floor)
    return d, rock

def rock_frlg(cells, d, isrock, base, pieces, tex):
    """Blob autotiling from FRLG's set (Blackthorn's rock_frlg). A cell whose only lower neighbours are
    diagonal takes FRLG's whole inner-corner piece (two of them split down the middle when both lower
    diagonals are on one side). Every other cell is composed per 8x8 quadrant from the nine-slice piece
    its two edges call for, using the over-rock pieces where the quadrant faces a lower rock terrace and
    the over-ground pieces where it faces ground. Returns (bottom, top overlay RGBA, piece names)."""
    H, W = d.shape
    out = base.copy()
    over = np.zeros(base.shape[:2] + (4,), np.uint8)
    nine, nine_rock, inner, join = pieces['nine'], pieces['rock'], pieces['inner'], pieces['join']
    ledge_mid = pieces['ledge']['mid']
    is_ledge = lambda x, y: 0 <= x < W and cells[y][x]['lab'] in 'LJ'
    clamp = lambda x, y: (min(max(x, 0), W - 1), min(max(y, 0), H - 1))
    lvl = lambda x, y: d[clamp(x, y)[1], clamp(x, y)[0]]
    fill = np.array([ROCK_RAMP[i] for i in nine[('M', 'M')].ravel()], np.uint8).reshape(16, 16, 3)
    plain = {k: np.tile(tex[k][oy:oy + 8, ox:ox + 8], (2, 2, 1)) for k, (oy, ox) in PLAIN.items()}
    def beyond(x, y):
        cx, cy = clamp(x, y)
        if isrock[cy, cx]:
            return fill, 'rock'
        k = cells[cy][cx]['floor']
        return plain[k], k
    cast = dict(grass=BORDER_GRAY, sand=BORDER_GRAY, rock=None)
    piece = np.full((H, W), '', object)
    for y in range(H):
        for x in range(W):
            if not isrock[y, x]:
                continue
            me = d[y, x]
            lo = {k: lvl(x + dx, y + dy) < me for k, (dx, dy) in DIRS.items()}
            X0, Y0 = x * 16, y * 16
            cell, ov = out[Y0:Y0 + 16, X0:X0 + 16], over[Y0:Y0 + 16, X0:X0 + 16]
            diag = [k for k in ('ne', 'se', 'sw', 'nw') if lo[k]]
            whole = None
            if not any(lo[k] for k in 'nesw') and diag:
                if len(diag) == 1:
                    whole = inner[diag[0]]
                elif sorted(diag) in (['se', 'sw'], ['ne', 'nw']):
                    r, l = ('se', 'sw') if 'se' in diag else ('ne', 'nw')
                    whole = np.concatenate([inner[l][:, :8], inner[r][:, 8:]], 1)
            for qy in (0, 1):
                v = ('N', 'S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M'
                for qx in (0, 1):
                    h = ('W', 'E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M'
                    sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
                    vk, hk = 'ns'[qy], 'we'[qx]
                    toward = next((DIRS[k] for k in (vk, hk, vk + hk) if lo[k]), None)
                    bg, kind = beyond(x + toward[0], y + toward[1]) if toward else (fill, 'rock')
                    if whole is not None:
                        ix = whole[sl]
                    elif lo[vk + hk] and not lo[vk] and not lo[hk]:
                        ix = inner[vk + hk][sl]
                    else:
                        ix = (nine_rock if kind == 'rock' else nine)[(v, h)][sl]
                    if qy == 1 and is_ledge(x + (1 if qx else -1), y):
                        if (v, h) == ('M', 'W' if qx == 0 else 'E'):
                            ix = join['w' if qx == 0 else 'e'][sl]
                        else:
                            ix = np.where((ix < 0) & (ledge_mid[sl] >= 0), ledge_mid[sl], ix)
                    cell[sl] = bg[sl]
                    q = ov[sl]
                    for (yy, xx), k in np.ndenumerate(ix):
                        if k >= 0:
                            q[yy, xx] = ROCK_RAMP[k] + (255,)
                        elif k == SHADOW and cast[kind]:
                            q[yy, xx] = cast[kind] + (255,)
                    if (q[..., 3] > 0).all():
                        cell[sl] = fill[sl]
            piece[y, x] = ''.join(k for k in DIRS if lo[k])
    return out, over, piece
