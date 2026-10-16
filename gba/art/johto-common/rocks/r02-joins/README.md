# R02 — complete wall, matching stair rise, raised landing

[Original / rebuilt / native comparison](review/comparison.png) ·
[Gameplay](review/gameplay.png) · [Numbered grid](review/grid.png)

This corrects the owner's three findings on the previous sample. It remains an
isolated candidate awaiting visual approval; production is not changed.

## Corrections

1. **Complete lower wall.** The unobscured second rock band of the original HGSS
   `wall01_d` texture supplies a continuous side plane. The previous color-keyed
   silhouette had terrain-shaped gaps. The new 16x128 foreground has no holes,
   grass or tree fragments. All existing tree pixels are preserved over it.
2. **One consistent rise.** The wall and stairs share a 16-pixel rise. Original
   `slope` geometry is projected directly into a 32-pixel-wide opening; the final
   projection is no longer squashed vertically. Shoulders remain part of the model.
3. **Raised path.** The east landing moves one row north, matching the top tread.
   The grass border moves north locally. A two-cell bend joins the existing route.
   Existing native side-stair behaviors make the player ascend and descend with
   this geometry; no new engine code or warp is introduced.

The new wall is a planar adaptation of original HGSS texture. It deliberately
replaces the irregular, incomplete silhouette; it is not an exact DS model render.
The original model/texture hashes are retained in [the preceding source record](../r02-refined/source/geometry.json).
Original artwork: Game Freak / Nintendo / Creatures.

## Tile and gameplay review

[Cell ledger](evidence/cell-review.json) records all 96 comparison cells and 384
quadrants. [Visual findings](evidence/visual-review.json) describe each correction
and pin the reviewed images. Enlarged sheets: [1](review/cells-1.png),
[2](review/cells-2.png), [3](review/cells-3.png), [4](review/cells-4.png).

Native build and exact Porymap/render equality pass. Headless checks cover both
stair lanes in both directions, the upper/lower shoulders, wall barriers, raised
landing/path bend, ordinary flash save, cold reload and title Continue.
[Runtime evidence](evidence/runtime.json) · [Path bend](evidence/gameplay/path-bend.png).
No desktop game was opened. GitHub has not reported CI checks.

The new upper stair cell at (14,21) is walkable; three stair behavior cells and
five former tall-grass cells are updated to match the art. All elevation bits,
existing IDs, events and warps remain unchanged. No pixels change outside the
28 affected cells. See [native structure](evidence/structure.json).

Engine base: `285b577993906c76c8d96ed38eedb5e2c955b714`.
Candidate: `833a9c4355be0b191e676963f5f8d39930560fb6`.
ROM SHA-256: `c694ba71002d757fb3099298ce3cc683a38ffffdf7cf14e01ee661ce59f6e4d6`.
[Draft PR #12](https://github.com/Davisfox5/pokeemerald-expansion/pull/12), dependent
on parent PR #5. The original Violet engine checkout is untouched.

## Reproduce

On an isolated, clean checkout of the exact base above:

```sh
python tools/gba/maps/johto_common/r02_joins.py --engine /path/to/engine --install
python tools/gba/maps/johto_common/r02_review.py gba/art/johto-common/rocks/r02-joins
# Build the engine with serial generated and the pinned ARM toolchain.
python tools/gba/maps/johto_common/r02_joins_runtime.py /path/to/engine /tmp/r02-run --toolchain /path/to/arm-toolchain
# Export using the existing r02_porymap.cpp offscreen probe, then commit the engine.
python tools/gba/maps/johto_common/r02_publish.py /path/to/engine /tmp/r02-run /tmp/r02-porymap --pack gba/art/johto-common/rocks/r02-joins
```

The installer appends tiles/metatiles and uses a previously unused palette bank.
It refuses a different base or dirty target files. Do not replay it on owner edits.
Manual visual review must be repeated after art regeneration.

## Remaining scope

Existing tree spacing and tall-grass density differ from HGSS. Other cliff areas,
plateau corners and cave entrances remain untouched. This completes the requested
correction candidate, not a whole-route or region-wide art rollout.
