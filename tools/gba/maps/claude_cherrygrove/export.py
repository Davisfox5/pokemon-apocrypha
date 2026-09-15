#!/usr/bin/env python3
"""Export editable source art for the Claude Cherrygrove build.

gba/art/claude-cherrygrove/source/<asset>.png       RGBA at native size, one file per painted object
gba/art/claude-cherrygrove/source/<asset>.idx.png   indexed (P-mode, 4-bit) with the asset's palette
gba/art/claude-cherrygrove/source/palettes/*.pal    JASC palettes per bank
gba/art/claude-cherrygrove/source/sheet.png         every asset on grass at 1x, for a quick look
gba/art/claude-cherrygrove/source/manifest.json     sizes, banks, footprints, provenance
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from claude_cherrygrove import art, layout as L  # noqa: E402

OUT = HERE.parents[3] / 'gba/art/claude-cherrygrove/source'

def main():
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'palettes').mkdir(exist_ok=True)
    assets = art.build_all(); manifest = dict(assets={}, palettes={}, layout=dict(width=L.W, height=L.H, spawn=L.SPAWN, buildings=L.BUILDINGS))
    for name, c in assets.items():
        rgba = c.to_rgba(); Image.fromarray(rgba, 'RGBA').save(OUT / f'{name}.png')
        im = Image.fromarray(c.px.astype(np.uint8), 'P'); flat = []
        for r, g, b in c.pal.gba(): flat += [r, g, b]
        im.putpalette(flat + [0] * (768 - len(flat))); im.save(OUT / f'{name}.idx.png', bits=4)
        manifest['assets'][name] = dict(width=c.w, height=c.h, bank=c.pal.bank, metatiles=[c.w // 16, c.h // 16])
    for key, pal in art.PALETTES.items():
        (OUT / 'palettes' / f'{key.lower()}-bank{pal.bank:02}.pal').write_text('JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in pal.gba()) + '\n')
        manifest['palettes'][key] = dict(bank=pal.bank, slots={n: i for n, i in pal.index.items()}, colors=pal.gba())
    manifest['provenance'] = ('All scenery is original pixel art authored in tools/gba/maps/claude_cherrygrove/art.py for this build, following '
                              'Gen 3 tile conventions with HGSS Cherrygrove shapes and colours. Ground grass, sand paths and animated water are '
                              'Emerald primary tiles with regraded palettes. Characters come from the workbench preset (existing Gold/Silver/Kestra, '
                              'Johto residents and regional samples); no character pixels were changed.')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    from claude_cherrygrove.sheet import render
    render(str(OUT / 'sheet.png'), scale=1)
    print('exported', len(assets), 'assets to', OUT)

if __name__ == '__main__':
    main()
