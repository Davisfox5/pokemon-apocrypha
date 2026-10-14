# Shared Johto Poké Mart exterior

Reusable proposal after the owner rejected the Violet tiled roof and imported sign. The shop uses a smooth blue enamel roof with rounded corners, a steel-and-glass storefront and a new blue-and-white shopping-bag / MART sign. HGSS shop color and service-building identity inform the design; every pixel is authored natively in `tools/gba/maps/johto_mart/assets.py`.

Installed for review in Violet City only. The approved university, lecture hall and other cities are preserved. This is ready for reuse across Johto; owner visual approval of this revision is pending.

## Contents

- `source/building.png` and `sign.png`: transparent RGBA source/review cutouts.
- `source/*.indexed.png`: identical artwork with transparent palette index zero.
- `source/palette.pal`: one native 15-color RGB555 palette plus transparency.
- `source/manifest.json`: dimensions, placement offsets and entrance/sign anchors.

The building is 80x64 pixels (5x4 metatiles). Door tile is (1,3), approach (1,4); existing Violet interiors remain unimplemented. In this placement the top building row overlaps the player and rows 1–3 are solid. Sign is 32x64, normally offset (4,1) from the building origin; its pole/body occupy sign cells (0,1), (0,2), (0,3), with the upper row above the player. Review collision/layer placement for each destination town.

## Reuse

`make_assets(bank)` returns independent building/sign canvases sharing a selected scenery palette. Use the returned palette when packing each town. Keep terrain beneath the transparent artwork and compile tile IDs per destination; Violet's numeric tile IDs are not portable.

```sh
PYTHONPATH=tools/gba/maps python -m johto_mart gba/art/johto-mart/source --bank 9
```

Violet's generator imports this module directly. Its native decoded exports match this pack pixel-for-pixel. [Comparison](../violet-city/evidence/johto-mart-comparison.png), [native game captures](../violet-city/evidence/johto-mart-gameplay.png) and [validation](../violet-city/evidence/johto-mart-validation.json) document the installed example. No town-specific name, surrounding terrain or donor background is baked into either component.
