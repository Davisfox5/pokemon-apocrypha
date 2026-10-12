# Floccesy richer native map — September 25

This revision brings the September 24 native Floccesy map closer to the owner's supplied original-game image. It is built in the isolated `tools/vendor/gba/floccesy-rich-work` copy. The active `johto-restart-game` source and its saved editor state remain untouched while Porymap is open on a locked Mac. The incremental `gba/floccesy-v3.patch` is ready to apply over the active v2 source once that state can be checked.

## Visual changes

- Center: 96×96 to 144×144 pixels. Houses: 80×96 to 112×128. Northern lodge and sheds also have larger footprints, with door cells aligned to their facades.
- Grass now uses a native small-tuft pattern rather than the pale, heavily blended v2 texture. Flower clusters are more common around the court, clock garden, Center, and park.
- The right park has a branching dirt path, bench, hedge, bin, and the clock garden has a sign. The court, raised clock square, dark street, brick plazas, northern forest, and six building functions remain.
- The Unova visitor moves from (35,55) to (39,51) because the larger house occupies the former route. The other five residents keep their positions and routes.

The owner's supplied original-game image is `references/owner-floccesy.jpg`. The larger building cutouts reuse the September 24 generated originals in `generated/` and their prompts in `native-prompts.json`. The prior concept `floccesy-art-preview.png` is retained for comparison. New terrain and park props are authored in `tools/gba/maps/build_floccesy_v3.py`; approved Cherrygrove cliff and bench sources are reused as before. The decoded native map is `evidence/town-overview.png`, and actual emulator captures are in `evidence/in-game-tour.png` and the individual `*-in-game.png` files.

## Native limits and validation

The larger scene produced 1,599 candidate 8×8 tiles. A weighted visual reduction selected 1,008 tiles, the full map allocation; 425 metatiles and 13 palettes are used. The decoded map differs from its uncompressed composition at 20.1% of pixels, with mean absolute channel error 5.43/255. Facades, court markings, garden masonry, and core road/cliff patterns are prioritized. These measured limits explain why the native image cannot retain every texture in the reference. `evidence/integration.json` has the exact counts.

The isolated ROM compiled with Arm GNU Toolchain 14.2.Rel1. Static checks passed across all 4,368 cells: all doors and six NPC routes connect, scenery stays below sprites, and the camera boundary remains covered. In mGBA, both directions of travel, six door round trips, Center stairs, ordinary save, cold reload, title Continue, 186 movement probes, and 1,800 NPC samples passed. Source, native captures, and ROM identity are in `evidence/build.json`, `evidence/structure.json`, and `evidence/runtime.json`. Cherrygrove and Sandgem sampled layout, map, and tileset files are byte-identical to the active source; see `evidence/preservation.json`.

## Reproduce and review

Run `build_floccesy_v3.py`, `check_floccesy_v3_structure.py`, and `floccesy_v3_doors.py` from the repository root on the isolated workbench. These scripts are not safe to point at the live owner-edited project without first reconciling any later edits. `preserve_floccesy_v3.py` regenerates the 97 KB incremental patch and checks forward application to v2 and reverse application to the isolated v3 source.

Playable preview: `tools/vendor/gba/Floccesy-rich-preview-20260925.zip`; choose Continue to start in Floccesy. This is a preview ROM and save, not a production release. No ROM, save, or build binary belongs in Git.
