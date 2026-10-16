# R02 revised cliff and stair sample

[Original / rebuilt / Route 36 comparison](review/comparison.png) ·
[Actual gameplay](review/gameplay.png) · [Numbered grid](review/grid.png)

This replaces the rejected screenshot-based pilot. It is an isolated playable
review sample; owner visual acceptance is pending. Production is not changed.

## What was corrected

The cliff and stairs now come from complete HGSS Route 36 model geometry with its
original texture/palette bindings. This recovers the faces hidden by trees without
smearing visible screenshot rows. The whole stair shoulder and original olive
tread colors are retained. A four-row wall continuation fixes the lower join.
Ground uses independent accepted texture cores, a compact transition ramp and the
existing route palette; the scalloped border and perimeter color seam are fixed.
Rock/stair source masters have transparent backgrounds.

The source projection uses 16 pixels per horizontal model unit and 12 pixels per
height unit. The original 86-pixel stair/shoulder segment is fitted to 16x64 with
nearest-neighbor sampling to preserve the existing gameplay grid. This adaptation
is explicit, rather than a claim that DS geometry transfers unchanged to GBA.

## Tile review and limits

All 96 cells in columns 10–21 / rows 18–25 have a material, source box,
collision/elevation and 8x8 quadrant record in [cell-review.json](evidence/cell-review.json).
[Visual findings](evidence/visual-review.json) pin the reviewed image hashes.
The four enlarged cell sheets compare original, rejected pilot and corrected:
[1](review/cells-1.png), [2](review/cells-2.png),
[3](review/cells-3.png), [4](review/cells-4.png).
Regenerating the art invalidates previous manual visual approval.

Existing tree footprints and tall grass remain different from HGSS. Older cliff
art outside this rectangle remains, including the transition visible in the wider
north-wall gameplay frame. Plateau corners, other directions and cave entrances
are not built by this sample. The full route is not claimed complete.

## Native and gameplay evidence

- 81 appended tiles, 33 appended metatiles; 609 total tile slots.
- Two previously unused palette banks; old IDs and attributes preserved.
- Zero changed collision/elevation bits or pixels outside the review rectangle.
- Native compilation and actual Porymap 6.3.1 rendering match with zero pixel errors.
- ROM build passes. Both stair lanes work in both directions; adjacent wall
  barriers pass. Ordinary flash save, cold reload and title Continue pass.
- No desktop emulator was opened. The original engine checkout remains untouched.

[Structure](evidence/structure.json) · [Runtime](evidence/runtime.json) ·
[Porymap render](evidence/porymap.png) · [Full native route](review/native-full.png)

Engine base: `6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf`.
Engine candidate: `285b577993906c76c8d96ed38eedb5e2c955b714` on
`codex/r02-cliff-review`, [draft PR #12](https://github.com/Davisfox5/pokeemerald-expansion/pull/12).
This branch depends on the existing Violet/Route 36 PR #5.
ROM SHA-256: `187cb16c51e251d27823e2788cff2c253a6a82321cec7f89c36d0d1c9ba6c966`.

## Source and reproduction

HGSS donor revision `d2f8c958924aa007080dc90227c663553b3eeb30`.
Model NARC `files/a/0/6/5`, member 47; texture NARC `files/a/0/4/4`, member 6.
47 selected wall/stair faces, their UVs, texture palette bindings and hashes are in
[source/geometry.json](source/geometry.json). Textures: `wall01_d`, `wall01_g`, `slope`.
Original game artwork: Game Freak / Nintendo / Creatures.

Use a clean isolated engine checkout at the base above. The installer refuses an
unexpected revision or dirty target files. It appends native data and must not be
replayed on an owner-edited map. Python requires the existing Pillow/NumPy environment.

```sh
python tools/gba/maps/johto_common/r02_refine.py --engine /path/to/review-engine --donor /path/to/pokeheartgold --install
python tools/gba/maps/johto_common/r02_review.py
# In the engine: gmake -j1 generated, then gmake -j8 TOOLCHAIN=/path/to/arm-toolchain
python tools/gba/maps/johto_common/r02_runtime.py /path/to/review-engine /tmp/r02-runtime --toolchain /path/to/arm-toolchain
```

`r02_porymap.cpp` is the focused offscreen Porymap renderer, linked against the
existing Porymap 6.3.1 build objects. After rendering and committing the engine:

```sh
python tools/gba/maps/johto_common/r02_publish.py /path/to/review-engine /tmp/r02-runtime /tmp/r02-porymap
```

Publishing asserts matching ROM hashes and exact Porymap/native output, then
collects gameplay evidence. It does not grant visual approval; inspect the cells,
seams and gameplay and update the manual findings after each art regeneration.
