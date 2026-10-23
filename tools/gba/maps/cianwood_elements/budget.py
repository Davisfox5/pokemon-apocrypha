"""Where Cianwood's tile and palette budget goes, per element, before anything is cut.

    python3 tools/gba/maps/cianwood_elements/budget.py ENGINE_CHECKOUT [STYLE]   # STYLE C by default

Reads elements.py's compose-STYLE.npz and counts, for every element (rock, each prop,
ground, the shared Center), the distinct 8x8 tiles that are not already in
CherrygrovePrimary (flips counted once) and the 5-bit colours those tiles need from
the secondary palette banks. A tile shared by two elements is listed under both, so the
per-element counts add up to more than the union printed last.
"""
from __future__ import annotations
import collections, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B                                   # noqa: E402
import pack as P                                    # noqa: E402

def canon(px, mask):
    k = B.rgb5(px).astype(np.int16)
    k[~mask] = -1
    return min(v.tobytes() for v in (k, k[:, ::-1], k[::-1], k[::-1, ::-1]))

def main(engine, style):
    comp = np.load(P.SRC / 'elements' / f'compose-{style}.npz', allow_pickle=True)
    bottom, top, shared, owner = comp['bottom'], comp['top'], comp['shared'], comp['owner']
    cells = json.loads((P.SRC / 'elements/ledger.json').read_text())['detail']
    tiles, pals, _, _ = P.primary(engine)
    opaque, masked = P.primary_index(tiles, pals)
    fixed = {b: {tuple(v >> 3 for v in c) for c in p[1:]} for b, p in pals.items()}
    tiles_by, colours_by = collections.defaultdict(set), collections.defaultdict(set)
    for ty in range(P.H * 2):
        for tx in range(P.W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            lab = cells[ty // 2][tx // 2]['lab']
            sh = shared[sl][..., 3] > 0
            if sh.any():
                if not ((P.key5(shared[sl][..., :3]) in opaque) if sh.all() else (P.key5(shared[sl][..., :3], sh) in masked)):
                    tiles_by['shared Center (C06)'].add(canon(shared[sl][..., :3], sh))
                if sh.all():
                    continue
            layers = [(bottom[sl], np.ones((8, 8), bool), opaque, 'ground' if lab not in 'TESWN' else 'rock (bottom)')]
            t = top[sl][..., 3] > 0
            if t.any():
                who = sorted(set(owner[sl][t].ravel().tolist()) - {''})
                layers.append((top[sl][..., :3], t, masked, ','.join(who) if who else
                               ('rock' if lab in 'TESWN' else 'ledge' if lab == 'L' else 'boulder' if lab == 'O' else 'other top')))
            for px, m, index, name in layers:
                key = P.key5(px, None if m.all() else m)
                if key in index:
                    continue
                tiles_by[name].add(canon(px, m))
                cols = {tuple(int(v) for v in c) for c in B.rgb5(px)[m]}
                if not any(cols <= f for f in fixed.values()):
                    colours_by[name] |= cols
    rows = sorted(tiles_by, key=lambda k: -len(tiles_by[k]))
    for k in rows:
        print(f'{len(tiles_by[k]):4d} tiles  {len(colours_by[k]):3d} learned colours  {k}')
    print(f'{len(set().union(*tiles_by.values())):4d} tiles in all (secondary limit 496)')
    print(f'{len(set().union(*colours_by.values())):4d} town colours in all, besides the Center\'s 21 (7 banks x 15 = 105)')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else 'C')
