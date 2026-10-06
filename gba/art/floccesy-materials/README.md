# Floccesy walls and town materials — September 26

The owner approved the native sample's textures, rejected the tower-square walls, and requested correcting those walls before extending the treatment through town. This revision is implemented in `tools/vendor/gba/floccesy-materials-work`. It preserves the exploration map and is an isolated playable revision, not an active Porymap installation.

## Art changes

The garden's side walls now have continuous longitudinal coping rather than repeated front-facing masonry. The north/south runs, joined corners, shaded front face and two stair jambs have separate directional treatment. The existing wall cells, height/elevation properties, opening and stairs remain unchanged. The reference is the original Floccesy image retained at `../floccesy-v4/references/owner-floccesy.jpg`.

The approved material treatment is extended to the rest of the town's lawn, public paving, asphalt curbs, dirt routes and training court. Existing flower-cell footprints receive reusable shaded plants; foliage has a more restrained green palette. Court markings remain in their original pixel positions. The small clock palette and grounding shadow are retained. All buildings, trees, props, routes and interactions keep their footprints and placements. No artwork from the excessive v5 painting was imported.

`build_floccesy_materials.py` authors these native textures and compiles them without lossy tile reduction. Hidden lower-layer pixels are reused losslessly; decoded map pixels must match the authored composition exactly. The map references 997 tile patterns; the existing border accounts for the remaining reserved patterns within the 1,008-slot allocation. There are 919 metatiles, using only engine-supported palette banks 0–12. The earlier v4 palette correction remains included.

## Evidence

- `evidence/clock-comparison.png`: real in-game captures of the previous sample and corrected wall treatment.
- `evidence/town-in-game.png`: real captures of the garden, street, court, northern buildings, park, houses, Center and NPC dialogue.
- `evidence/town-overview.png`: decoded native map, not a concept image.
- `evidence/sample-walk.gif`: movement through the same garden exit and onto the street.
- `evidence/door-animation-contact.png`: native animated door frames across all six buildings.

The ROM compiled with Arm GNU Toolchain 14.2.Rel1. All 4,368 map cells retain identical collision, elevation, metatile behavior and layer properties. All event/map-script files, NPC routes, warps, connections and other layout binaries remain byte-identical. Six animated door art records were regenerated to match new metatile IDs and surrounding ground; the door implementation is identical after removing those art references.

Static checks verify all doors/NPC routes, camera coverage and connections. Paired prior-sample/new-town runtime checks passed garden movement, wall blocking, stair exit, street traversal, NPC dialogue/return, save, cold reload and title Continue. Separate town checks passed Cherrygrove travel, all six building round trips and Center stairs. The runtime collision sweep passed 190 probes with zero failures; 1,800 NPC movement samples were recorded. Captures and animation/movement frames were inspected. See `integration.json`, `structure.json`, `runtime.json`, `town-runtime.json`, `movement.json`, and `preservation.json` under `evidence/`.

## Reproduce and play

The builder reads the preserved v4 source and writes only to its isolated workbench. Run `tools/gba/maps/build_floccesy_materials.py`, then `floccesy_materials_doors.py` and `check_floccesy_materials_structure.py`. Compile the isolated ROM using the existing GBA toolchain. `check_floccesy_materials_runtime.py` compares actual movement and captures with the prior clock sample. `preserve_floccesy_materials.py` validates unchanged exploration/event data and packages the result.

`gba/floccesy-materials.patch` applies over the prior native clock sample, not active v2. Forward and reverse checks pass. Playable package: `tools/vendor/gba/Floccesy-materials-20260926.zip`; load the matching ROM/save and choose Continue beside the clock tower. ROMs, saves and test binaries stay ignored. The active editor and owner saves are untouched.
