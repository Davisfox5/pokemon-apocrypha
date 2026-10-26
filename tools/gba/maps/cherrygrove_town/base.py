"""Cherrygrove at the engine's base revision, and the shared helpers of the town tools."""
from __future__ import annotations
import io, json, re, struct, subprocess, sys, tarfile, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / 'route30_catalog')]
import reference as Rf                               # noqa: E402  (Route 30's frame: the band, the wall, the lattice)
from tiles import Tileset                            # noqa: E402

ART = ROOT / 'gba/art/cherrygrove-town'
R30_ART = ROOT / 'gba/art/route30-catalog'
SEAM = R30_ART / 'source/seam'                       # what Route 30's pack reads of the town
BASE_REV = '2722eaf7601ec02dc5a684fa8cdef9206c0dc377'   # the engine's apocrypha base (route30_catalog/pack.py BASE_REV)
W, H = 80, 48
OWN = Rf.CG_WALL_ID0 - 512                           # Cherrygrove's own secondary metatiles (84)
BLOCKED, OPEN = (3, 3), (0, 3)                       # Cherrygrove's collision, elevation
NORMAL, COVERED = 0, 1
MB_NORMAL, WATER_MB = 0x00, 0x15
R29_SEEN = range(W - 8, W)                           # columns Route 29's camera draws with its own tilesets
R30_SEEN = (5, range(27, W))                         # rows and columns Route 30's camera reaches (seams.py)
PRIMARY_LAYOUTS = ('LAYOUT_CHERRYGROVE_CITY', 'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH', 'LAYOUT_NEW_BARK_TOWN',
                   'LAYOUT_VIOLET_CITY_ENTRANCE', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_29', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_30')
COPY_LAYOUTS = ('LAYOUT_CHERRYGROVE_ROUTE30_APPROACH', 'LAYOUT_JOHTO_ROUTE31')   # on copies of CherrygrovePrimary's metatiles

def rgb5(a): return np.asarray(a).astype(np.int32) >> 3
def entry(tile, flip, bank): return tile | ((flip & 1) << 10) | ((flip >> 1) << 11) | (bank << 12)
def words_of(data, w):
    return np.array(struct.unpack('<%dH' % (len(data) // 2), data)).reshape(-1, w)
def jasc(cols):
    return '\r\n'.join(['JASC-PAL', '0100', '16'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols]) + '\r\n'
def read_pal(path):
    return [tuple(map(int, l.split())) for l in path.read_text().splitlines()[3:19]]
def gba(c):
    return tuple((int(v) >> 3) << 3 for v in c)     # a colour as the packs write theirs (5-bit value x 8)
def layouts(engine):
    return {l['id']: l for l in json.loads((engine / 'data/layouts/layouts.json').read_text())['layouts'] if 'id' in l}
def tileset_dir(engine, sym):
    g = (engine / 'src/data/tilesets/graphics.h').read_text()
    m = re.search(r'gTilesetTiles_%s\[\] = INCGFX_U32\("data/tilesets/(\w+/\w+)/tiles\.png"' % sym[9:], g)
    return engine / 'data/tilesets' / m.group(1)
def tiles_of(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    return [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
def metatiles_of(d):
    return [tuple(b) for b in struct.iter_unpack('<8H', (d / 'metatiles.bin').read_bytes())]
def attrs_of(d):
    b = (d / 'metatile_attributes.bin').read_bytes()
    return list(struct.unpack('<%dH' % (len(b) // 2), b))
def map_ids(engine, l, root=None):
    """Metatile ids a layout draws: its map and its border."""
    root = root or engine
    ids = set((words_of((root / l['blockdata_filepath']).read_bytes(), l['width']) & 1023).ravel().tolist())
    if l.get('border_filepath'):
        d = (root / l['border_filepath']).read_bytes()
        ids |= {v & 1023 for v in struct.unpack('<%dH' % (len(d) // 2), d)}
    return ids

def base_checkout(engine):
    """Cherrygrove's map and tilesets, and Route 29's secondary, at BASE_REV, unpacked in the engine's layout
    (every run starts from them)."""
    d = Path(tempfile.mkdtemp(prefix='cherrygrove-base-'))
    tar = subprocess.check_output(['git', '-C', str(engine), 'archive', BASE_REV, 'data/layouts/CherrygroveCity',
                                   'data/tilesets/primary/cherrygrove', 'data/tilesets/secondary/cherrygrove',
                                   'data/tilesets/secondary/claude_route29'])
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(d, filter='data')
    return d

class Town:
    """Base Cherrygrove: words, tileset, render."""
    def __init__(self, engine):
        self.engine = engine
        self.base = base_checkout(engine)
        self.words = words_of((self.base / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), W)
        self.t = Tileset(self.base, 'cherrygrove', 'cherrygrove')
        self.img = np.array(self.t.map_image(self.words.ravel().tolist(), W).convert('RGB'))
    def banks(self, m):
        blk = self.t.blocks[int(m >= 512)][m - 512 if m >= 512 else m]
        return {e >> 12 for e in blk if e}
    def attr(self, m):
        return self.t.attrs[int(m >= 512)][m - 512 if m >= 512 else m]
    def render_id(self, m):
        return np.array(self.t.render(m).convert('RGB'))
