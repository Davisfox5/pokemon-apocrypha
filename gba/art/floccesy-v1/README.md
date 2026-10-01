# Floccesy Town — Unova exterior preview

Built September 23, 2026 at the owner's request for a Unova town connected east of Cherrygrove, using the accepted custom-art method. Layout reference is the [original Black 2/White 2 spring map](https://archives.bulbagarden.net/wiki/File:Floccesy_Town_Spring_B2W2.png), retained in `references/floccesy-spring.png`. This is a native 2D adaptation, not a pixel-exact DS reconstruction: the clock garden, paved crossroads, southwest Center, paired southeast townhouses, northern lodge/training court and two sheds preserve the reference's composition. Scaling fits the existing preview's characters. Forest scenery buffers cover the camera. The eastern continuation is visibly fenced until another map is built.

Six assets were generated individually using the built-in image_gen tool: house, Center, clock tower, lodge, shed and tree. Exact prompts and original output paths are in `prompts.json`; copied originals are in `generated/`; editable native palette-constrained PNGs and palettes are in `native/`. The bench reuses accepted custom Cherrygrove art. Grass, fence and path patterns use the existing Emerald-based native terrain, recolored for this town. Roads, brick paving and court markings are native palette-indexed tile construction. Pokemon/reference designs belong to Game Freak/Nintendo/Creatures; existing NPCs retain prior importer provenance. No new Pokemon sprite designs were generated.

## Play

Open `tools/vendor/gba/Floccesy-preview-20260923/Floccesy.gba` with its matching `.sav`, choose Continue, and start on the main street at (30,62). Follow the lower street west to Cherrygrove. Cherrygrove's eastern exit returns here. Its northern connection to Sandgem remains intact. The ZIP is beside the preview folder. Old owner ROMs and saves were not overwritten.

Source remains `tools/vendor/gba/johto-restart-game`, group 80 map 20, size 56x78. Six interiors and Center upstairs are maps 21–27. Interiors reuse existing Emerald rooms; these are not custom Unova interiors. Six regional residents walk normally. Generic dialogue is preview staging. No encounters, story progression, or permanent cross-region narrative geography were added. The west connection is a native directional warp with a fade so distinct region tiles and palettes load correctly.

## Verification

Build identity is in `evidence/build.json`. Native mGBA checks in `runtime.json` pass: walking east from Cherrygrove into Floccesy and back, all six door entry/exit pairs, Center stairs, normal save, cold reload and title-screen Continue. The existing Cherrygrove seven-door/route checks and Sandgem five-door/travel checks pass (`cherrygrove-regression.json`, `sandgem-regression.json`). Those regressions preceded the final Floccesy-only layer/door refinements; existing town data was unchanged by those refinements.

Structural checks classify all 4,368 cells, with 1,439 reachable walking cells, connected entrances and NPC routes, and no exposed camera edge. All 126 representative native movement probes pass. All six NPCs were checked over 1,440 samples/5,760 frames for both route cells, collision and actual sprite image frames. Every exterior metatile uses the covered layer type, placing its ground and artwork beneath characters, fixing the initially observed paving occlusion. Tree/building footprints are solid. Visuals were inspected at native resolution, including animated doors and player visibility on paved surfaces.

`evidence/town-overview.png` is decoded native map art; `evidence/in-game.png` and `evidence/walking-tour.gif` are native engine captures. Porymap was opened on FloccesyTown with the correct tilesets and no unsaved marker; mGBA launched the new preview.

## Preserve owner edits

The exact pre-task source snapshot is `tools/vendor/gba/johto-before-floccesy-20260923`. All prior layout binaries remain byte-identical except two directional exit cells in CherrygroveRoute29Approach. Existing Johto metatile records are unchanged; two clones were appended. `evidence/preservation.json` records the check. Cherrygrove town and Sandgem were not regenerated.

Standalone `gba/floccesy.patch` includes all three towns above baseline `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. Forward and reverse checks pass; identity is in `evidence/patch.json`. Earlier patches remain intact. Never commit ROMs or saves.

Helpers in `tools/gba/maps/`: `build_floccesy.py`, `install_floccesy.py`, `floccesy_doors.py`, `check_floccesy_structure.py`, `floccesy_runtime.c`, `floccesy_npc_runtime.c`, `preserve_floccesy.py`. Builders describe this snapshot and must not be replayed over newer owner edits. In particular, the installer and door helper read the pre-task backup: preserve and reconcile future edits before rerunning them.
