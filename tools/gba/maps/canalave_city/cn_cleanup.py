"""Native cleanup of the Canalave reference before packing (AGENTS.md, map work: art and cleanup)."""
from __future__ import annotations
import numpy as np
from cn_reference import W, H, MARGIN, PX

BRIDGE_MODELS = (31, 32)
BRIDGE_AXIS = (MARGIN + 15) * PX          # Platinum x = 15.0: between the drawbridge's two halves

def mirror_bridge(t):
    """The drawbridge's west half takes the east half mirrored about the canal's centre line.

    Platinum's two halves are the same structure lit from one side, so no tile of one repeats in the other
    (268 tiles). Mirrored, the towers, deck and rails share their tiles and both towers stand alike."""
    own, B = t.c['fg_owner'], t.c['buildings']
    ids = [i for i, b in enumerate(B) if b['model'] in BRIDGE_MODELS]
    m = np.isin(own, ids)
    ys, xs = np.nonzero(m)
    y0, y1 = ys.min(), ys.max() + 1
    half = max(BRIDGE_AXIS - xs.min(), xs.max() + 1 - BRIDGE_AXIS)
    west = (slice(y0, y1), slice(BRIDGE_AXIS - half, BRIDGE_AXIS))
    east = (slice(y0, y1), slice(BRIDGE_AXIS, BRIDGE_AXIS + half))
    mw, me = m[west], m[east][:, ::-1]
    up_w = t.up[west]
    up_w[mw] = 0                                       # the west half's own pixels go
    src = t.up[east][:, ::-1]
    up_w[me] = src[me]
    t.notes.append(dict(cleanup='mirror_bridge', axis_px=int(BRIDGE_AXIS), rows=[int(y0), int(y1)], half_px=int(half),
                        west_pixels_replaced=int(mw.sum()), east_pixels_copied=int(me.sum())))

# Platinum draws its signs as overworld objects, so the map art has none. Gen 3 signs are map cells: Emerald's
# own wooden sign (General metatile 0x1B) and town sign (0x03) stand on Platinum's sign cells.
SIGNS = {  # Platinum cell: (kind, script label)
    (3, 18): ('wood', 'CanalaveCity_Sign_Library'),
    (4, 28): ('town', 'CanalaveCity_Sign_Gym'),
    (9, 48): ('wood', 'CanalaveCity_Sign_Dock'),
    (22, 50): ('town', 'CanalaveCity_Sign_City'),
    (5, 44): ('wood', 'CanalaveCity_Sign_EldritchHouse'),
    (24, 10): ('wood', 'CanalaveCity_Sign_HarborInn'),
}
SIGN_METATILE = dict(wood=0x1B, town=0x03)

def emerald_metatile(engine, mid):
    """RGBA of a General metatile: its top layer, or the whole cell less its lawn when the art is one layer."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tiles import Tileset
    ts = Tileset(engine, 'petalburg', 'general')
    out = np.zeros((16, 16, 4), np.uint8)
    ent = ts.blocks[0][mid]
    lawn = ts.blocks[0][1]
    top_used = any(e & 1023 for e in ent[4:])
    for layer in ((1,) if top_used else (0,)):
        for q in range(4):
            e = ent[layer * 4 + q]
            if not top_used and e == lawn[q]:
                continue
            tile = ts.tiles[0][e & 1023]; pal = ts.pals[0][e >> 12]
            for y in range(8):
                for x in range(8):
                    v = tile[(7 - y if e & 2048 else y) * 8 + (7 - x if e & 1024 else x)] % 16
                    if v:
                        out[(q // 2) * 8 + y, (q % 2) * 8 + x] = (*pal[v], 255)
    if not top_used:                                   # drop the lawn the sign stands on
        lawn_img = np.array(ts.render(1).convert('RGB'))
        same = (out[..., :3] == lawn_img).all(-1)
        out[same] = 0
    return out

def signs(t, engine):
    for (px, pz), (kind, _) in SIGNS.items():
        x, r = px + MARGIN, pz + MARGIN
        art = emerald_metatile(engine, SIGN_METATILE[kind])
        sl = t.cell(x, r)
        a = art[..., 3] > 0
        t.up[sl][a] = art[a]
        t.coll[r, x] = True
    t.notes.append(dict(cleanup='signs', cells=[[x + MARGIN, z + MARGIN] for x, z in SIGNS]))

TRANSLUCENT_MODELS = (244,)               # the fountain statue: Platinum draws its stone with alpha

def restore_translucent(t):
    """Props Platinum draws with alpha are not in the renderer's opaque foreground, and the bottom layer
    leaves out every blended pixel (the soft cast shadows). Their pixels come back from the full render,
    onto the top layer, inside the prop's own box."""
    full, ter, B = t.c['full'][..., :3], t.c['terrain'][..., :3], t.c['buildings']
    for b in B:
        if b['model'] not in TRANSLUCENT_MODELS:
            continue
        x0, z0, x1, z1 = b['footprint']
        X0, X1 = int(np.floor(x0)) * PX, int(np.ceil(x1)) * PX
        Y0, Y1 = (int(np.floor(z0)) - 3) * PX, int(np.ceil(z1)) * PX
        box = (slice(Y0, Y1), slice(X0, X1))
        m = (full[box] != ter[box]).any(-1) & (t.up[box][..., 3] == 0)
        t.up[box][..., :3][m] = full[box][m]
        t.up[box][..., 3][m] = 255
        t.notes.append(dict(cleanup='restore_translucent', model=b['model'], box_px=[X0, Y0, X1, Y1], pixels=int(m.sum())))

def apply(t, engine):
    mirror_bridge(t)
    restore_translucent(t)
    signs(t, engine)
