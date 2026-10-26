"""Cherrygrove cleaned up to AGENTS.md's Gen 4 conversion rules, as native edits of the owner-approved town.

    python3 tools/gba/maps/cherrygrove_town/town.py ENGINE --preview   # draw the town, write evidence/preview.png
    python3 tools/gba/maps/cherrygrove_town/town.py ENGINE --render    # before Route 30's pack: the cells it must see
    python3 tools/gba/maps/cherrygrove_town/town.py ENGINE --primary   # before Route 30's pack: Route 29's columns
    python3 tools/gba/maps/cherrygrove_town/town.py ENGINE --install   # after Route 30's pack

Every run starts from Cherrygrove at the engine's base revision (base.BASE_REV). Unchanged cells keep their
metatile ids; the town's new cells take ids and tile slots nothing else draws (install.py). Read
gba/art/cherrygrove-town/README.md.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import base as B                                     # noqa: E402
import elements as E                                 # noqa: E402

def compose(engine):
    town = B.Town(engine)
    cv = E.Canvas(town)
    E.north_edge(cv, engine)
    E.islands(cv, engine)
    E.pond(cv)
    E.beach_edges(cv)
    E.houses(cv)
    E.forests(cv)
    E.draw_trees(cv, E.tree_sprites(town))
    return town, cv

def picture(town, cv):
    """The town as drawn (kit cells by their metatiles, the sea under the cliff's foot as its first frame)."""
    img = town.img.copy()
    g = cv.ground[(0 - E.R0) * 16:]
    t = cv.top[(0 - E.R0) * 16:]
    for x, r in cv.changed:
        sl = np.s_[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
        px = g[sl].copy(); a = t[sl][..., 3] > 0; px[a] = t[sl][a][:, :3]
        wet = (px == E.SENTINEL).all(-1)
        if wet.any():
            sea = town.render_id({(0, 0): 0x03B, (1, 0): 0x03A, (0, 1): 0x04C, (1, 1): 0x04B}[(x % 2, r % 2)])
            px[wet] = sea[wet]
        img[sl] = px
    for (x, r), (m, _) in cv.kit.items():
        img[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] = town.render_id(m)
    return img

def main(engine, mode):
    town, cv = compose(engine)
    out = B.ART / 'evidence'; out.mkdir(parents=True, exist_ok=True)
    img = picture(town, cv)
    if mode == '--preview':
        Image.fromarray(img).save(out / 'preview.png')
        Image.fromarray(np.concatenate([town.img, np.full((8, img.shape[1], 3), 255, np.uint8), img], 0)).save(out / 'before-after.png')
        print(len(cv.changed), 'cells drawn anew,', len(cv.kit), 'placed by id;', *cv.notes, sep='\n  ')
        return
    import install as I
    getattr(I, mode[2:])(engine, town, cv, img)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2])
