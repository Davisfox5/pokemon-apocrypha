# Union Cave — HGSS first-floor reconstruction

This replaces the 14×12 Route 32 entrance test room with the recognizable
**34×60 HGSS first floor**. The original screenshot is the geographic/art reference;
the old Gen 3 room is preserved as comparison evidence, not used as the design.
Exact engine commit and validation results are recorded in `evidence/build.json`.

## Review

- [Whole original/native comparison](evidence/comparison.png)
- Materials and terrain: [north](evidence/material-comparison-1.png),
  [middle](evidence/material-comparison-2.png), [south](evidence/material-comparison-3.png)
- [Native gameplay](evidence/gameplay-gallery.png)
- [Numbered original](evidence/numbered-hgss.png)
- [Previous entrance test room](evidence/previous-entrance-test-room.png)

## Layout and art

The 544×962 HGSS image is registered at 1:1 pixel scale to native 16×16 squares,
with origin (0,0). Two bottom border pixels are omitted. Original floor, rock,
water and outside void remain distinct. The north branch, central narrow pool,
western water-separated pockets, winding eastern corridor, large southern lake,
stalagmites, spiral-stair locations and two exterior doorway locations are retained.
The Route 32 exterior is unchanged, including both entrance cells and warp IDs.

Clean original cave floor/plateau samples form reusable native textures. Native
five-bit palette reduction and reusable 8×8 glyphs fit private primary/secondary
banks; these do not repack shared Cherrygrove or Route 32 art. Critical terrain
boundary glyphs are retained, while rare interior texture variants use the closest
reusable native glyph. This is a native conversion, not a pixel-exact screenshot.
Packing figures are in [packing.json](evidence/packing.json).

Characters/items are removed from terrain artwork. Explicit context repairs retain
wall behind heads and water/shore beneath the southern trainer. No trainer teams,
story roles, dialogue, rewards, encounters or quests are invented by this pass.

Stalagmites have separate art and movement footprints. Connected formations retain
their complete dark centers/silhouettes; only their base rows occupy the rock
footprint. Upper sections use the native foreground layer so the player can pass
behind them where the original passage permits. Rock behind a formation remains
blocked. The editable [footprints](source/stalagmite-footprints.json), material grid,
separate foot mask and overhead pixel mask expose this interpretation.

The existing cave map/layout ID is retained. A Union Cave region-map section is
appended and identified as Johto, preserving all existing named location IDs.
The generated terminal NONE/COUNT sentinels advance with the appended section.

## Validation and interpretation limits

The reference is a **visual interpretation**, not extracted DS terrain or collision.
The 2,040 source cells are checked against actual map collision and water behavior.
Actual decoded RGB is checked separately: mixed shores, shadowed wall edges,
foreground props, spiral stairs and lighted doorway cells can disagree with a
simple dominant-color label. These disagreements remain explicitly listed in
[audit.json](evidence/audit.json); they are not counted as confirmed material matches.
Inspect original/native panels rather than treating a color threshold as authority.

Porymap 6.3.1 project-core export must match the decoded native map with zero pixel
differences. A standalone Porytiles 2.0 legacy round-trip validates 128 representative
material metatiles with exact native RGB/alpha. The headless mGBA tour exercises the
main walking passage and both staircase approaches, blocked water/rock/stalagmite
roots, foreground overlap, both Route 32 entry cells and return, plus fresh ordinary
128 KiB flash save, cold reload and title Continue. Results belong to the exact ROM
hash in evidence. No desktop game is opened and no ROM/save/tool binary is committed.

**Unfinished connections:** B1F/B2F and Route 33 are not built here. Spiral stair and
southern exterior positions are retained but unwired; this is a first-floor review,
not a claim that all Union Cave is complete. Cave water currently has static art and
native Surf behavior; campaign Surf access, encounters, field-move exit state and
original hidden event rules are not qualified by the walking tour. Prior saves are
preserved; old saves inside the replaced small test room are not automatically
relocated or claimed compatible with new geometry.

## Editable source and reproduction

Edit committed engine layouts/assets directly in Porymap. `trace.py` and `build.py`
are reproducible source provenance, not an editor to replay over owner changes.
The manifest guard refuses changed owned files. In an isolated checkout based on
Route 32 commit `7049fd5d8b95b3f357056ff53b8b2b3a3e848d74`:

```sh
python3 tools/gba/maps/union_cave/trace.py
python3 tools/gba/maps/union_cave/build.py /path/to/engine
make -C /path/to/engine -j1 generated
make -C /path/to/engine -j8
python3 tools/gba/maps/union_cave/check_art.py /path/to/engine /path/to/porytiles-legacy
python3 tools/gba/maps/union_cave/runtime.py /path/to/engine /new/runtime-dir --toolchain /path/to/arm-toolchain
```

`review.py` renders actual native art, material panels, ledger and preservation
checks after a real Porymap project export. This session's scratch paths are explicit
in that narrow evidence adapter; authoring source has no dependency on a prior map
render. Original image URL, checksum, credits, dimensions, crop, removed occluders
and scope are in [reference.json](source/reference.json). Nintendo / Game Freak /
Creatures artwork, reference hosted by Bulbagarden Archives.
