"""Violet City cleaned up to AGENTS.md's native visual rules, as native edits of the newest Violet.

    python3 tools/gba/maps/violet_city/violet.py ENGINE --preview   # draw the town (evidence/preview.png)
    python3 tools/gba/maps/violet_city/violet.py ENGINE --install   # repack Violet's two tilesets, write the map

Every run starts from Violet at the engine's port commit (base.BASE_REV). Violet is the only map on
VioletCityPrimary and VioletCity, so the install lays both out anew (pack.py); every cell keeps its
collision, elevation, behaviour and layer type. Read gba/art/violet-city-review/README.md.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import base as B                                     # noqa: E402
import elements as E                                 # noqa: E402
import pack as P                                     # noqa: E402

def compose(engine):
    v = B.Violet(engine)
    cv = E.Canvas(v)
    E.paths(cv)
    E.lake_bank(cv)
    E.landing(cv)
    E.islet(cv)
    E.flatten(cv)
    return v, cv

def decode(engine):
    """The installed map as the engine's tilesets draw it."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tiles import Tileset
    t = Tileset(engine, 'violet_city', 'violet_city')
    b = (engine / B.LAYOUT / 'map.bin').read_bytes()
    w = [int(x) for x in np.frombuffer(b, '<u2')]
    return np.array(t.map_image(w, B.W).convert('RGB')), t, np.array(w, np.int64).reshape(B.H, B.W)

def families(v):
    """The textures a fold may move a pixel within (pack.py), and which of them have no edge of their own."""
    lawn = E.keyset(E.G.textures()[E.G.GRASS])
    img = v.image()
    canopy = E.keyset(img[0:12 * 16, 0:16 * 16]) - lawn   # the north-west forest: crowns over the lawn
    earth = E.keyset(np.array(Image.open(E.BANK_TEX).convert('RGB'))) | {E.DEEP}
    stone = set(E.LANDING_SNAP.values())
    cobble = E.keyset(E.cobble_texture(img))
    sand = E.keyset(E.G.textures()[E.G.PATH]) | set(E.VERGE_PROFILE) | {E.LAWN_FLAT}
    water = {(48, 176, 224), (64, 184, 224), (72, 200, 224)}
    fams = [canopy, earth, stone, lawn, cobble, sand, water]
    return fams, [0, 3, 4, 6]

MB_ANIMATED_DOOR = 0x69

def animated_doors(engine, v):
    """Whether a door animation can play in Violet (field_door.c draws its frames in tiles 1008-1023): a cell
    with the animated-door behaviour, or a door table entry for Violet's tilesets. Violet's two warps are a
    plain doorway and an arrow warp, so its sheet may use those 16 slots until a door is added."""
    cells = any(v.attr(int(w) & 1023) & 0xFF == MB_ANIMATED_DOOR for w in v.words.ravel())
    src = (engine / 'src/field_door.c').read_text()
    return cells or 'gTileset_VioletCity' in src

FOLD_STEPS = range(0, 9)                             # pixels a texture tile may move to reuse another, as few as fit

def install(engine, v, cv):
    cells = cv.cells()
    border = []
    for w in v.border:
        m = w & 1023; low, up = v.layers(m)
        border.append((low, up, v.attr(m), w & 0xFC00, [[e >> 12] for e in v.block(m)]))
    fams, free = families(v)
    P.S_TILES = 512 if not animated_doors(engine, v) else 496
    for k in FOLD_STEPS:
        try:
            words, bwords, pk = P.pack(v, cells, [list(b) for b in v.banks], border, k, fams, free)
            break
        except AssertionError as e:
            if 'more tiles' not in str(e) or k == FOLD_STEPS[-1]:
                raise
    P.write(engine, v, words, bwords, pk)
    got, t, w = decode(engine)
    want = cv.image()
    diff = (P.rgb5(got) != P.rgb5(want)).any(-1)
    fam_of = {tuple(int(x) >> 3 for x in c): i for i, f in enumerate(fams) for c in f}
    for y, x in zip(*np.nonzero(diff)):
        a, b = tuple(int(c) for c in P.rgb5(want[y, x])), tuple(int(c) for c in P.rgb5(got[y, x]))
        assert fam_of.get(a, -1) >= 0 and fam_of.get(a) == fam_of.get(b, -2), ('a pixel moved outside its texture', x // 16, y // 16)
    per = diff.reshape(B.H, 16, B.W, 16).sum((1, 3))
    attrs = lambda m: t.attrs[int(m >= 512)][m - 512 if m >= 512 else m]
    moved = [[x, r] for r in range(B.H) for x in range(B.W)
             if (int(w[r, x]) & 0xFC00) != (int(v.words[r, x]) & 0xFC00) or attrs(int(w[r, x]) & 1023) != v.attr(int(v.words[r, x]) & 1023)]
    assert not moved, ('traversal changed', moved[:20])
    report = dict(tiles=dict(primary=min(len(pk.tiles), P.P_TILES), secondary=max(0, len(pk.tiles) - P.P_TILES),
                             left=P.P_TILES + P.S_TILES - len(pk.tiles), door_slots_used=P.S_TILES == 512),
                  metatiles=len(pk.metas), cells_redrawn=len(cv.changed), traversal_changed=0,
                  fold=dict(max_pixels_per_tile=k, pixels_moved=int(diff.sum()), cells=int((per > 0).sum()),
                            note='every moved pixel is another tone of its own texture'),
                  notes=cv.notes)
    out = B.ART / 'evidence'; out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(got).save(out / 'installed.png')
    (out / 'install.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report))

def main(engine, mode):
    v, cv = compose(engine)
    out = B.ART / 'evidence'; out.mkdir(parents=True, exist_ok=True)
    if mode == '--preview':
        img = cv.image()
        Image.fromarray(img).save(out / 'preview.png')
        before = v.image()
        Image.fromarray(np.concatenate([before, np.full((before.shape[0], 16, 3), 255, np.uint8), img], 1)).save(out / 'before-after.png')
        print(len(cv.changed), 'cells redrawn;', *cv.notes, sep='\n  ')
        return
    install(engine, v, cv)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2])
