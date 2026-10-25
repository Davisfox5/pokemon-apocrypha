"""Existing FRLG mountain modules, as reused by accepted Mahogany/Blackthorn.
No rescaling or screenshot synthesis. Original Game Freak/Nintendo art.
"""
from pathlib import Path
import numpy as np
from PIL import Image
def _tiles(d):
 a=np.array(Image.open(d/'tiles.png'))&15
 return [a[y:y+8,x:x+8] for y in range(0,a.shape[0],8) for x in range(0,a.shape[1],8)]
FRLG_RAMP = {9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6}
FRLG_NINE = {('N', 'W'): 0x68, ('N', 'M'): 0x69, ('N', 'E'): 0x6A, ('M', 'W'): 0x70, ('M', 'M'): 0x71,
             ('M', 'E'): 0x72, ('S', 'W'): 0x78, ('S', 'M'): 0x79, ('S', 'E'): 0x7A}
FRLG_NINE_OVER_ROCK = {('N', 'W'): 0x6B, ('N', 'M'): 0x6C, ('N', 'E'): 0x6D, ('M', 'W'): 0x73, ('M', 'M'): 0x71,
                       ('M', 'E'): 0x75, ('S', 'W'): 0x7B, ('S', 'M'): 0x7C, ('S', 'E'): 0x7D}   # an edge onto lower rock
FRLG_INNER = dict(se=0xB2, sw=0xB3, ne=0xBA, nw=0xBB)          # whole-cell inner corners
FRLG_LEDGE = dict(mid=0x87, left=0xB0, right=0xB1)             # jump ledge and its rounded ends
FRLG_JOIN = dict(w=0x1F1, e=0x1F2)       # a mountain side with a ledge running into its foot from the west / east
CLEAR, SHADOW = -1, -2

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
