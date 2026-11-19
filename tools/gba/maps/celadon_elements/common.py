"""Paths, sizes and HGSS access shared by Celadon's element build.

Celadon is HGSS's Celadon (pokeheartgold map header 55, MAP_CELADON, area data bank 15,
zone T07) drawn as Gen 3 elements by the Olivine method (AGENTS.md, "Converting a Gen 4
map"): HGSS's layout cell for cell, its ground textures at 1:1 on the Gen 3 grid, its
buildings rendered from their own models at C06's angle. The native map is the 60x50 cut
of HGSS's 64x64 block that holds the town (columns 60-63 and rows 50-63 are forest).

HGSS readers (hgss_render, hgss_camera) and the palette helpers (build) are Olivine's,
imported from tools/gba/maps/olivine_elements; Celadon's own modules have other names, so
nothing of Olivine's shadows them.
"""
from __future__ import annotations
import functools, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/celadon-elements'
SRC, EV = ART / 'source', ART / 'evidence'
OLIVINE = HERE.parent / 'olivine_elements'
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(OLIVINE) not in sys.path:
    sys.path.append(str(OLIVINE))

W, H = 60, 50                       # native map, cells
HW, HH = 64, 64                     # HGSS block, cells
HEADER_ID, AREA_BANK = 55, 15

def R():
    import hgss_render
    hgss_render.HEADER_ID, hgss_render.AREA_BANK = HEADER_ID, AREA_BANK
    return hgss_render

@functools.lru_cache(maxsize=None)
def load(phg):
    return R().load(Path(phg))

# HGSS's ground and prop textures in Celadon's map texture set (15), each with its own
# palette (the NSBTX palette names differ from the texture names).
TEXTURES = dict(tama_yuka='tama_yuka_pl', tama_yuka2='tama_yuka2_pl', tama_fuch='tama_fuch_pl', tama_br='tama_br_pl',
                tama_f='tama_f_pl', grass01gs='grass01', grass01_a='grass01_a', pond_un='pond_un', pond_line='pond_line',
                pond_edge='pond_edge', pond_on='pond_on', flower01='flower01', flower02='flower02', flower03='flower03',
                allpeakgs='apeak', allpeak_pgs='apeak', tree01gs='tree01', tree01_re='tree01_re', tree01_un='tree01_un')

def textures(phg=None):
    """name -> RGBA texture. Decoded once from pokeheartgold into source/hgss/textures.npz,
    so later steps run without the HGSS checkout."""
    cache = SRC / 'hgss/textures.npz'
    if phg is not None:
        r = R()
        _, tex0, _, _, _ = load(str(phg))
        out = {}
        for name, pal in TEXTURES.items():
            e = next(t for t in tex0.textures if t.name == name)
            out[name] = r.decode(tex0, e, pal)
        np.savez_compressed(cache, **out)
        return out
    z = np.load(cache)
    return {k: z[k] for k in z.files}

def art(rows, pal):
    """An RGBA image from rows of palette characters ('.' clear)."""
    out = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal:
                out[y, x, :3] = pal[ch]
                out[y, x, 3] = 255
    return out

def put(dst, img, X, Y):
    """Draw img's opaque pixels into dst (RGB or RGBA) at (X, Y), clipped."""
    h, w = img.shape[:2]
    y0, x0 = max(Y, 0), max(X, 0)
    y1, x1 = min(Y + h, dst.shape[0]), min(X + w, dst.shape[1])
    if y1 <= y0 or x1 <= x0:
        return
    part = img[y0 - Y:y1 - Y, x0 - X:x1 - X]
    m = part[..., 3] > 0
    sl = dst[y0:y1, x0:x1]
    sl[..., :3][m] = part[..., :3][m]
    if dst.shape[-1] == 4:
        sl[..., 3][m] = 255
