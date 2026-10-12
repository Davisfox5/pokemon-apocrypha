# Native clock-garden sample — September 26

The owner approved a small native sample after rejecting the v5 illustration as excessive. This is an actual GBA tile revision in the isolated `tools/vendor/gba/floccesy-clock-sample-work` source. It is not a conversion of the v5 painting. The art changes are confined to map cells x14–31, y42–53: warmer tower masonry, a slate-purple roof palette, low-contrast lawn clusters and contact shadows, shaded plants within existing flower-cell footprints, dressed paving, coping on the existing garden walls, and clearer street curbs. No new objects or exploration features were added. Pattern authoring is in `tools/gba/maps/build_floccesy_clock_sample.py`; original tower/foliage art derives from the v4 assets and their recorded provenance.

## Baseline correction

Runtime inspection found that v4 used background palette banks 13–15 even though this engine loads only 0–12 (`include/fieldmap.h`, `NUM_PALS_TOTAL=13`). This invalidates v4's previous blanket visual-verification claim. Its offline overview could look correct while foliage rendered incorrectly in-game.

The separate `gba/floccesy-clock-palette-fix.patch` corrects those references, reuses the supported tree palette, and maps the northern opening into supported colors. The corrected control build is `tools/vendor/gba/floccesy-clock-baseline-work`. Comparisons use this corrected control, so broken baseline foliage does not exaggerate the sample's improvement. This art-data repair changes no geometry or exploration properties. Unloaded banks are not enabled through engine changes.

## Native properties and capacity

All 4,368 cells retain identical collision, elevation, behavior and layer properties relative to v4. All map event and script files, NPC routes, doors, warps, connections and other layout binaries remain byte-identical. The sampled region's metatile IDs change because their artwork changes; their properties are copied exactly. Outside the sample, decoded pixels match the corrected control exactly.

The compiler reuses lower-layer patterns whose differing pixels are fully hidden behind opaque upper-layer scenery. This is lossless: the final decoded image must equal the authored native pixels exactly, and no nearest-tile reduction is used. The final map references 960 of the 1,008 available tile patterns, leaving 48 slots. It uses 755 metatiles and only supported palette banks 0–12. See `evidence/integration.json` and `preservation.json`.

## In-game evidence

- `evidence/clock-comparison.png` and `street-comparison.png`: real 240×160 mGBA captures, before and after at matching positions.
- `evidence/sample-walk.gif`: ordinary movement from the garden through the existing exit to the street.
- `evidence/sample-npc-dialogue-in-game.png`: existing visitor dialogue with the new art loaded.
- `evidence/runtime.json`: both control and sample passed identical garden traversal, wall blocking, exit/street movement, NPC dialogue/return, save, cold reload and title Continue checks.
- `evidence/town-runtime.json`: separate sample checks passed two-way Cherrygrove travel, all six building round trips, Center stairs and save/reload/Continue.

Both ROMs compiled with Arm GNU Toolchain 14.2.Rel1. Captures were inspected at native size and across movement frames. The result is a restrained material pass; visual acceptance belongs to the owner. No whole-town art expansion was performed.

## Reproduce and use

Run the builder with `--baseline` for the corrected control, and without it for the sample. Build each isolated source using the existing GBA toolchain. Run `tools/gba/maps/check_floccesy_clock_sample.py` for paired emulator evidence. Run `preserve_floccesy_clock_sample.py` to regenerate the two binary source patches and playable package. Patches pass forward and reverse application checks: apply the palette-fix patch over v4, then `gba/floccesy-clock-sample.patch` over that corrected source. They are not patches over active v2.

Playable package: `tools/vendor/gba/Floccesy-clock-sample-20260926.zip`. Load its matching ROM/save and choose Continue to start beside the clock tower. All ROMs, saves and compiled test binaries remain ignored. The active Porymap project was not modified; the sample is isolated, as planned.
