"""Route 7's gatehouse room: FireRed's own (Route7_EastEntrance_Frlg, layout
SaffronCity_EastWestEntrance), repacked on Emerald's gTileset_Building the Celadon way
(AGENTS.md: an interior Kanto needs is FireRed's room, packed into its own secondary;
celadon_elements/interiors.py does the drawing and the exact pack).

    python3 tools/gba/maps/route7/gate_room.py ENGINE_CHECKOUT

The room's two arrow cells keep their FireRed behaviours: the west one leads out onto Route 7
(the arrow cells in front of the gate's west face), the east one onto Saffron's west gate
(8, 27); FireRed's second row of warps, on plain floor, is left out. Every other cell is MB_NORMAL. FireRed's guard and his scene triggers stay out of this
pass (the gate guard and his line are for the NPC pass).

Writes gba/art/route7/source/interiors/gate.npz and evidence/interiors/gate.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
import interiors as I          # noqa: E402
import build as B              # noqa: E402

ROOT = HERE.parents[3]
OUT, EV = ROOT / 'gba/art/route7/source/interiors', ROOT / 'gba/art/route7/evidence/interiors'
FRLG_MAP, FRLG_LAYOUT, FRLG_SECONDARY = 'Route7_EastEntrance_Frlg', 'SaffronCity_EastWestEntrance_Frlg', 'generic_building_2_frlg'
WARPS = {(1, 5): 'route', (11, 5): 'saffron'}          # FireRed's arrow cells (its second row of warps has none)
KEEP = I.KEEP + ('MB_EAST_ARROW_WARP', 'MB_WEST_ARROW_WARP')

def main(engine):
    MB = B.behaviors(engine)
    keep_mb = {MB[k] for k in KEEP}
    pair = I.frlg.Pair(engine, 'building_frlg', FRLG_SECONDARY)
    grid, _ = I.frlg.layout(engine, FRLG_LAYOUT)
    bot, top, info = I.draw(pair, grid)
    keep = {xy for xy in WARPS if info[xy[1]][xy[0]]['frlg_behavior'] in keep_mb}
    assert keep == set(WARPS), ('a warp lost its arrow', set(WARPS) - keep)
    p = I.pack(bot, top, info, MB, keep)
    got = I.decode(p)
    d5 = np.abs(B.rgb5(got) - B.rgb5(I.frlg.flat(bot, top))).max(-1)
    assert d5.max() == 0, ('packed room differs from its picture', int((d5 > 0).sum()))
    OUT.mkdir(parents=True, exist_ok=True); EV.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / 'gate.npz', **p)
    Image.fromarray(got).resize((got.shape[1] * 2, got.shape[0] * 2), Image.Resampling.NEAREST).save(EV / 'gate.png')
    h, w = p['grid'].shape
    rep = dict(source=FRLG_MAP, size=[w, h], tiles=len(p['tiles']), metatiles=len(p['meta']), pixels_exact=True,
               warps=[dict(x=x, y=y, to=to, behaviour=int(info[y][x]['frlg_behavior'])) for (x, y), to in WARPS.items()])
    (OUT / 'gate.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(rep)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
