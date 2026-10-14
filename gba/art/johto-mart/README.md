# Shared Johto Poké Mart pavilion

Original retail architecture, refined after the owner flagged flat perspective, ambiguous split roof heights, oversized tower signage and unwanted text. The shop now has one continuous sapphire roof with parallel outer verges, shaded hip faces, standing seams, a thick projecting eave and a recessed glazed storefront. A small roof-mounted emblem replaces the tower. There is no lettering anywhere on the building.

Roof depth, overhang and wall presentation were visually compared to the actual Violet house and approved lecture hall sprites. This is a raster perspective match, not a measured recovered camera angle. The shop keeps its native footprint, door and collision.
Installed for review in Violet City only. Other Johto towns can reuse this source with their own ground treatment and placement. Owner visual approval is pending.

## Assets and placement

- `source/building.png`: transparent 112×96 pavilion (7×6 metatiles).
- `source/brandmark.png`: separate transparent 32×32 emblem for future applications.
- `source/*.indexed.png`: identical pixels, transparent palette index zero.
- `source/palette.pal`: 15 visible RGB555 colors plus transparency.
- `source/manifest.json`: dimensions, door/approach offsets and provenance.

Door tile is (2,5); approach is (2,6). Violet origin is (19,35), retaining door (21,40) and approach (21,41). The top row draws above the player; wall rows 1–5 are solid. Its east aisle and front clearance are walkable. There is no separate sign collision. Interiors are still unimplemented; the entrance remains closed.

## Reuse

`make_assets(bank)` returns the building and standalone brandmark canvases sharing the requested palette bank. The building already contains its small roof-mounted emblem; the standalone emblem does not need placement. Preserve transparent ground, set destination collision/overlap explicitly, and compile tile IDs per town. Violet numeric tile IDs are not portable.

```sh
PYTHONPATH=tools/gba/maps python -m johto_mart gba/art/johto-mart/source --bank 9
```

All building/signage pixels are original native artwork in `tools/gba/maps/johto_mart/assets.py`. Windows repeat on the hardware tile grid without losing their shelves, merchandise or reflections. The map packer also shares exact patterns through lossless palette-index permutations. No donor background or town-specific name is embedded.

[Before/after](../violet-city/evidence/mart-depth-comparison.png) · [Native gameplay](../violet-city/evidence/mart-depth-gameplay.png) · [Validation](../violet-city/evidence/mart-depth-validation.json)
