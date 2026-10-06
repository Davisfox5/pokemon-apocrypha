#!/usr/bin/env python3
"""Gold's overworld sprite from the HGSS hero (Ethan) walking frames, in the workbench's 12-frame Johto cast layout.

Layout (sAnimTable_JohtoCast): N idle, W idle, W1, W2, E idle, E1, E2, N1, N2, S idle, S1, S2.
HGSS strip (artwork-library/heartgold-johto/overworld-sprites/0069_hero.png, 24 frames of 32x32):
0 N idle, 1 W idle, 2-3 W walk, 4-5 E walk, 6 E idle, 8/10 N walk, 11 S idle, 12-13 S walk (14-23 are running frames).
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
ORDER = [0, 1, 2, 3, 6, 4, 5, 8, 10, 11, 12, 13]

def main(game):
    hero = np.asarray(Image.open(ROOT / 'artwork-library/heartgold-johto/overworld-sprites/0069_hero.png').convert('RGBA'))
    frames = [hero[i * 32:(i + 1) * 32] for i in ORDER]
    sheet = np.concatenate(frames, axis=0)
    colors = [tuple(int(v) for v in c) for c in np.unique(sheet[sheet[..., 3] > 0][:, :3], axis=0)]
    assert len(colors) <= 15, len(colors)
    pal = [(0, 0, 0)] + colors + [(0, 0, 0)] * (15 - len(colors))
    idx = np.zeros(sheet.shape[:2], np.uint8); m = sheet[..., 3] > 0
    arr = np.array(colors, np.int32); flat = sheet[m][:, :3].astype(np.int32)
    idx[m] = ((flat[:, None, :] - arr[None]) ** 2).sum(-1).argmin(1) + 1
    im = Image.fromarray(idx, 'P'); f = []
    for c in pal: f += list(c)
    im.putpalette(f + [0] * (768 - len(f)))
    out = Path(game) / 'graphics/object_events/pics/people/johto/gold.png'; im.save(out, bits=4)
    (Path(game) / 'graphics/object_events/palettes/johto_gold.pal').write_text('JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in pal) + '\n')
    return len(colors)

if __name__ == '__main__':
    import sys; print('gold sprite written with', main(sys.argv[1]), 'colours')
