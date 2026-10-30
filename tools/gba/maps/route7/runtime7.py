"""Headless mGBA checks for Route 7 and the Celadon seam (celadon_view.c, one streamed world).

    python3 tools/gba/maps/route7/runtime7.py ENGINE_CHECKOUT OUT_DIR [--check-only]

Celadon's harness (celadon_elements/runtime6.py) with Route 7's steps. One fresh emulator process
per phase:
    write  stand at Celadon's east edge and walk east across the map connection onto Route 7 and
           along its road to the gate, a capture every few steps; views of the gate, the tall
           grass, both outcrops, the ledges, the Underground Path and the woods; stand behind a
           tree and under the gate's roof; jump the south ledge and try both ledges from below
           (they hold); try the Underground Path's door (it stays shut); read the notice board;
           go through the gate room to Saffron's west gate and back; walk west back across the
           seam into Celadon; Celadon's main road and its doors as a regression; ordinary flash
           save on the route
    read   cold flash reload of that save
    menu   title screen -> Continue
Every capture's map layers (BG1-BG3, rebuilt from the VRAM dump) must match world.py's decode
pixel for pixel in 5-bit colour, read from the current map's world origin, on both maps and
across the seam (the fountains' animated glyph slots set aside); the gate room against
gate_room.py's decode; Saffron against its accepted native image.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
sys.path.insert(0, str(HERE))
import common as C             # noqa: E402
import runtime6 as R6          # noqa: E402
import interiors as IN         # noqa: E402
import compose as R            # noqa: E402
import world as WD             # noqa: E402

RE = R6.RE
CITY, SAFFRON = R6.CITY, R6.SAFFRON
ROUTE, GATE = R6.KANTO0 + 16, R6.KANTO0 + 17
REPORT = json.loads((WD.OUT / 'stream.json').read_text())
INSTALL = json.loads((WD.OUT / 'install.json').read_text())
SAVE = (ROUTE, 10, 16)
SAFFRON_GATE = tuple(INSTALL['saffron']['cell'])

def route_behind():
    out = {}
    for k, (x, y) in REPORT['walk_behind'].items():
        if k.startswith('r7_') and x >= WD.CW:
            out.setdefault('tree' if 'tree' in k else k[3:], (ROUTE, x - WD.CW, y - R.OY))
    return out

BEHIND = {f'behind-{k}': v for k, v in route_behind().items()}

def walk(m, x, y, moves, tag):
    out = [('go', m, x, y), ('shot', f'{tag}-0')]
    for i, (d, n) in enumerate(moves):
        out.append((d, n, f'{tag}-{i + 1}'))
    return out

def steps():
    out = [('view', CITY, 63, 18, 'celadon-east-edge'), ('view', ROUTE, 0, 17, 'route-west-edge'),
           ('view', ROUTE, 22, 17, 'gate-front'), ('view', ROUTE, 19, 9, 'tall-grass'), ('view', ROUTE, 20, 4, 'north-meadow'),
           ('view', ROUTE, 13, 24, 'underground-front'), ('view', ROUTE, 10, 12, 'ledges'), ('view', ROUTE, 13, 22, 'south-lawn'),
           ('view', ROUTE, 6, 14, 'step-north'), ('view', ROUTE, 20, 25, 'south-woods')]
    # east across the seam and along the road to the gate
    out += walk(CITY, 56, 17, [('east', 4)] * 3, 'walk-seam-east')
    out += [('at', ROUTE, 4, 16)]
    out += [x for x in walk(ROUTE, 4, 18, [('east', 4)] * 4 + [('east', 3)], 'walk-lane')]
    out += [('at', ROUTE, 23, 18)]
    for tag, (m, x, y) in BEHIND.items():
        out += [('go', m, x, y), ('shot', tag)]
    # ledges: jump the south one, and neither lets the player climb back
    out += [('go', ROUTE, 10, 12), ('south', 1, None), ('wait', 60), ('at', ROUTE, 10, 14), ('shot', 'ledge-jumped'),
            ('north', 1, None), ('wait', 30), ('at', ROUTE, 10, 14),
            ('go', ROUTE, 16, 11), ('west', 1, None), ('wait', 30), ('at', ROUTE, 16, 11)]
    # the Underground Path's door stays shut until its inside is built
    dx, dy = R.UNDERGROUND_DOOR
    out += [('go', ROUTE, dx, dy + 1), ('north', 1, None), ('wait', 60), ('at', ROUTE, dx, dy + 1)]
    out.append(('sign', ROUTE, R.NOTICE[0], R.NOTICE[1], 'sign-underground-path'))
    # through the gate room to Saffron and back
    sx, sy = SAFFRON_GATE
    out += [('go', ROUTE, 23, 17), ('east', 1, None), ('at', ROUTE, 24, 17), ('east', 1, None), ('wait', 400),
            ('map', GATE, 'gate-room-entry'), ('at', GATE, 1, 5), ('shot', 'room-gate'),
            ('go', GATE, 10, 5), ('east', 1, None), ('at', GATE, 11, 5), ('east', 1, None), ('wait', 400),
            ('at', SAFFRON, sx, sy), ('shot', 'saffron-west-gate'),
            ('west', 1, None), ('wait', 400), ('at', GATE, 11, 5), ('shot', 'room-gate-back'),
            ('go', GATE, 2, 5), ('west', 1, None), ('at', GATE, 1, 5), ('west', 1, None), ('wait', 400),
            ('at', ROUTE, 24, 17), ('shot', 'gate-exit')]
    # west back across the seam into Celadon
    out += walk(ROUTE, 20, 16, [('west', 4)] * 6, 'walk-seam-west')
    out += [('at', CITY, 60, 17)]
    # Celadon as before
    out += R6.walk(60, 17, [('west', 6)] * 3, 'walk-road')
    cx, cy = R6.DOORS['center']
    out += [('view', CITY, cx, cy + 1, 'center-front'), ('view', CITY, 12, 27, 'market'), ('view', CITY, 22, 41, 'footbridge')]
    out += [('view', CITY, 41, 45, 'blossom-plaza'), ('view', SAFFRON, 24, 40, 'regression-saffron'),
            ('view', ROUTE, SAVE[1], SAVE[2], 'save-spot')]
    return out

def world_ref():
    img = np.array(Image.open(WD.OUT / 'native.png').convert('RGB')).astype(np.int32) >> 3
    H, W = img.shape[0] // 16, img.shape[1] // 16
    P = R6.PAD
    out = np.zeros(((H + 2 * P) * 16, (W + 2 * P) * 16, 3), np.int32)
    for py in range(H + 2 * P):
        for px in range(W + 2 * P):
            sx, sy = WD.outside(px - P, py - P)
            out[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = img[sy * 16:sy * 16 + 16, sx * 16:sx * 16 + 16]
    return out, P * 16

def gate_ref():
    p = dict(np.load(R.SRC / 'interiors/gate.npz'))
    img = IN.decode(p).astype(np.int32) >> 3
    h = img.shape[0] // 16
    black = img[(h - 1) * 16:h * 16, 0:16]
    return R6.padded(img, np.tile(black, (2, 2, 1)))

def check_frames(out, game, phases):
    positions = {o['step'][5:]: o for p in phases for o in p['observations'] if o.get('step', '').startswith('shot:')}
    world, pad = world_ref()
    gate = gate_ref()
    saffron = R6.padded(np.array(Image.open(C.ROOT / 'gba/art/saffron-kanto/evidence/native.png').convert('RGB')).astype(np.int32) >> 3,
                        R6.saffron_border(game))
    results = []
    for p in sorted(out.glob('vram-*.bin')):
        tag = p.stem[5:]
        o = positions[tag]
        m = R6.KANTO0 + o['map'] if o['group'] == R6.KANTO_GROUP else None
        if m == GATE:
            (ref, rpad), (ox, oy) = gate, (0, 0)
        elif m == SAFFRON:
            (ref, rpad), (ox, oy) = saffron, (0, 0)
        else:
            ref, rpad = world, pad
            ox, oy = (WD.CW, R.OY) if m == ROUTE else (0, 0)
        shot = RE.map_layers(p)
        Image.fromarray((shot << 3 | shot >> 2).astype(np.uint8)).save(out / f'bg-{tag}.png')
        x0, y0 = (ox + o['x']) * 16 - 112 + rpad, (oy + o['y']) * 16 - 72 + rpad
        d = (ref[y0:y0 + 160, x0:x0 + 240] != shot).any(-1)
        anim = R6.pinned(p) if ref is world else np.zeros((160, 240), bool)
        r = dict(frame=tag, map=m, mismatched_map_layer_pixels=int((d & ~anim).sum()), pixels_on_animated=int(anim.sum()),
                 camera_origin_px=[int(x0 - rpad), int(y0 - rpad)])
        if tag in BEHIND:
            r['bg1_pixels_over_player_cell'] = int(RE.bg1(p)[72:88, 112:128].sum())
        if tag in R6.IN_FRONT:
            r['bg1_pixels_over_player'] = int(RE.bg1(p)[56:88, 112:128].sum())
        results.append(r)
    return results

def setup():
    R6.STEPS = steps()
    R6.SAVE = SAVE
    R6.WALK_BEHIND = BEHIND
    R6.IN_FRONT = ('center-front', 'gate-exit')
    R6.check_frames = check_frames

def main(game, out, check_only=False):
    setup()
    R6.main(game, out, check_only)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), '--check-only' in sys.argv)
