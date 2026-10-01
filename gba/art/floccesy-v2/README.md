# Floccesy native tiles — September 24

Created native GBA assets from the revised art direction and installed them in `tools/vendor/gba/johto-restart-game`. Porymap was reloaded and visually inspected. The full-town `floccesy-art-preview.png` remains a concept image; `evidence/town-overview.png` is decoded from the actual native tiles and map.

The town uses 1,000 native 8x8 tiles out of 1,008 available (16 reserved for doors), 263 unique metatiles, and 13 palette banks with 15 opaque colors each. Fourteen complex tile junctions were reduced to two palette banks. Separate generated architecture, tree and grass originals are in `generated/`; exact prompts and source paths are in `native-prompts.json`. Native cutouts and terrain are in `native/`. Reference designs belong to Game Freak/Nintendo/Creatures. The bench and cliff texture reuse the approved Cherrygrove assets.

Compilation passed. Native encode/decode matches the quantized assembled image. Static checks cover all 4,368 exterior cells, 1,409 reachable walking cells, six door approaches, NPC routes, layer ordering and camera boundary coverage. The 167 generated movement probes were NOT run. No emulator was opened or run; door transitions, NPC movement and gameplay require runtime revalidation. Earlier v1 runtime results do not verify this revision.

All map event data and all non-Floccesy layouts and tilesets match the pre-conversion snapshot. Cherrygrove, Sandgem, existing travel links and owner saves were preserved. The isolated ROM compiled to `tools/vendor/gba/johto-restart-game/pokeemerald.gba`; build identity is in `evidence/build.json`.

Reproduction: `tools/gba/maps/build_floccesy_v2.py`, `floccesy_v2_doors.py`, `check_floccesy_v2_structure.py`, and `preserve_floccesy_v2.py`. Do not rerun generators over subsequent owner edits. Snapshot: `tools/vendor/gba/johto-before-floccesy-v2-20260924`. Standalone source patch: `gba/floccesy-v2.patch`, forward and reverse checks passed; the v1 patch remains intact.

`floccesy-native-tiles.zip` contains native art, palettes, map/layout binaries, door frames and validation records. It is a source package, not a ROM or a universal drag-and-drop tileset for unrelated projects.
