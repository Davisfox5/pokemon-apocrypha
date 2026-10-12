# Floccesy surface cleanup and training court — September 26

Native GBA revision in `tools/vendor/gba/floccesy-cleanup-work`, following the owner's request to remove misplaced vegetation, clean building edges/shadows, and improve the basic arena. This is an isolated playable preview. The active Porymap project is untouched.

## Changes

- Explicit surface ownership removes old grass/flower pixels from streets, paving, stone walls, stairs, entrance cells and dirt paths. Existing flowers remain on lawns. The authoring pass replaced 4,849 plant pixels on these surfaces, including the former grass-fringed dirt margins.
- Preserved native building alpha repairs 420 edge/stray pixels. This closes vegetation holes and removes protruding silhouette fragments while retaining canopy overlaps and the clock's short contact shadow.
- The court has its own warm clay palette, compacted perimeter apron, crisp cream boundaries, a central Poké Ball and two trainer starting boxes. Side fences run longitudinally. Both original bench silhouettes and their blocked cells are retained. Painted markings do not introduce triggers or obstacles.
- Palette ordering now puts lawn beneath plants/buildings, allowing shared backgrounds under opaque pixels. Compilation is lossless: decoded native pixels equal the authored composition exactly. 925 referenced map tile patterns, 930 metatiles, supported palettes 0–12, within the 1,008-tile allocation.

## Verified

ROM build succeeded with Arm GNU Toolchain 14.2.Rel1. All 4,368 cells retain the same collision, elevation, metatile behavior and layer properties as the previous materials revision. Event/map-script files, NPC routes, warps and all other layouts are byte-identical. Six door animations were regenerated for the revised surrounding artwork; door implementation remains unchanged apart from art references.

Real mGBA checks passed town travel, six door round trips, Center stairs, wall blocking, garden exit, street movement, NPC dialogue and return, save, cold reload and ordinary title Continue. The final build passed 193 ordinary collision probes with zero failures. 1,800 NPC movement samples were recorded. Paired exploration/dialogue/save observations match the prior materials ROM. Final ROM hash and validation summary are in `evidence/qualification.json`.

- `evidence/arena-in-game.png`: enlarged actual court capture.
- `evidence/town-in-game.png`: actual court, clock garden, Center, homes, northern buildings and park captures.
- `evidence/town-overview.png`: decoded native map.
- `evidence/sample-walk.gif`: actual traversal.
- `evidence/door-*.png`: native door animation art frames; runtime door captures remain in `tools/vendor/gba/cleanup-town-proof`.

## Reproduce / preserve

The builder reads preserved v4 source and writes only the isolated cleanup workbench. Run `tools/gba/maps/build_floccesy_cleanup.py`, `floccesy_cleanup_doors.py`, and `check_floccesy_cleanup_structure.py`; compile the isolated ROM with the existing GBA toolchain. `check_floccesy_cleanup_runtime.py` compares the final ROM with the materials ROM. `floccesy_cleanup_runtime.c` covers travel, doors and town screenshots. Established collision and NPC harnesses were run against final symbols. `preserve_floccesy_cleanup.py` verifies properties and saves the patch/package.

`gba/floccesy-cleanup.patch` applies over `floccesy-materials-work`, with forward and reverse checks. Playable package: `tools/vendor/gba/Floccesy-cleanup-20260926.zip`. Load the matching ROM/save and choose Continue beside the clock tower; the court is north of the tower. ROMs, saves and test binaries remain ignored. Preserve any subsequent work before rebuilding or installing.
