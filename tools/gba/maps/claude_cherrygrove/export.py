#!/usr/bin/env python3
"""Export editable source art for the Claude Cherrygrove build.

gba/art/claude-cherrygrove/source/<asset>.png       RGBA at native size, one file per scenery piece
gba/art/claude-cherrygrove/source/<asset>.idx.png   indexed (P-mode, 4-bit) with the asset's bank palette
gba/art/claude-cherrygrove/source/palettes/*.pal    JASC palettes per bank (0-5 primary, 6-11 secondary)
gba/art/claude-cherrygrove/source/ground.png        the painted ground layer of the town at 1x
gba/art/claude-cherrygrove/source/sheet.png         every asset on grass at 1x, for a quick look
gba/art/claude-cherrygrove/source/manifest.json     sizes, banks, footprints, provenance
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from claude_cherrygrove import layout as L, build, ground  # noqa: E402

OUT = HERE.parents[3] / 'gba/art/claude-cherrygrove/source'
BANK_NAMES = {0: 'ground', 1: 'sea', 2: 'cliff', 3: 'tree', 4: 'flowers', 5: 'rocks', 6: 'house', 7: 'house-teal', 8: 'center', 9: 'mart', 10: 'blossom', 11: 'wood'}

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True); (OUT / 'palettes').mkdir()
    assets, palettes = build.build_assets()
    manifest = dict(assets={}, palettes={}, layout=dict(width=L.W, height=L.H, spawn=L.SPAWN, buildings=L.BUILDINGS))
    for name, c in assets.items():
        rgba = c.to_rgba(); Image.fromarray(rgba).save(OUT / f'{name}.png')
        im = Image.fromarray(c.px.astype(np.uint8)).convert('P') if False else Image.fromarray(c.px.astype(np.uint8), 'P'); flat = []
        for r, g, b in c.pal.gba(): flat += [r, g, b]
        im.putpalette(flat + [0] * (768 - len(flat))); im.save(OUT / f'{name}.idx.png', bits=4)
        manifest['assets'][name] = dict(width=c.w, height=c.h, bank=c.pal.bank, pool=getattr(c, 'pool', 'secondary'), metatiles=[c.w // 16, c.h // 16])
    for bank, pal in sorted(palettes.items()):
        (OUT / 'palettes' / f'bank{bank:02}-{BANK_NAMES.get(bank, "spare")}.pal').write_text('JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in pal.gba()) + '\n')
        manifest['palettes'][BANK_NAMES.get(bank, str(bank))] = dict(bank=bank, colors=pal.gba())
    town = build.compose_town(assets); gimg, _ = ground.paint(town['cells']); Image.fromarray(gimg).save(OUT / 'ground.png')
    manifest['provenance'] = (
        'Scenery is derived read-only from HeartGold/SoulSilver: buildings, cliff, rocks, flowers, fences, signpost, mailbox and the '
        'beach ripple are lifted at native 16 px scale from the top-down HGSS Cherrygrove render (gba/art/johto-v1/references/cherrygrove-hgss.png), '
        'cleaned of neighbours and shadows and door-aligned to movement cells (tools/gba/maps/claude_cherrygrove/hgss.py); the tree is the '
        'HGSS tree01 texture from disasm/pokeheartgold/files/a/0/4/4 at its rendered size in the render\'s tones. Grass, paths, sand and sea '
        'are painted in the render\'s sampled colours with its rim profiles (ground.py). The teal house and blossom trees are palette recolours '
        'of the HGSS house and tree. Pier, boats, nets, benches and lamps are original pixel art (art.py). Original designs: Game Freak / '
        'Nintendo / Creatures. Characters come from the workbench preset; no character pixels were changed.')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    from claude_cherrygrove.sheet import render
    render(str(OUT / 'sheet.png'), assets, scale=1)
    print('exported', len(assets), 'assets to', OUT)

if __name__ == '__main__':
    main()
