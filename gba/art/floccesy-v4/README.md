# Floccesy detailed native revision — September 25

The owner asked for a more interesting, detailed version of the previously enlarged Floccesy map. This v4 revision keeps the six buildings, town functions, resident routes and Cherrygrove connection from v3. It enlarges the trees from 32×40 to 48×56 pixels, staggers northern canopy rows, uses shaded and sunlit forest palettes, adds a dark northern woodland opening, and adds more flowers, tufts, court benches and ground variation. The supplied original-game image is `references/owner-floccesy.jpg`.

The native decoded overview is `evidence/town-overview.png`. Actual mGBA captures are `evidence/in-game-tour.png` and the individual `*-in-game.png` files. The visual work is authored by `tools/gba/maps/build_floccesy_v4.py` and lives in the isolated `tools/vendor/gba/floccesy-detailed-work` source. Original generated cutouts and their prompts are retained in `generated/` and `native-prompts.json`.

## Verification

The isolated GBA ROM compiled using Arm GNU Toolchain 14.2.Rel1. The native package uses 1,008 8×8 tiles (full allocation), 640 metatiles and 16 palettes. Its measured mean absolute channel error from the uncompressed composition is 2.39/255, and 10.27% of pixels changed through tile reduction; see `evidence/integration.json`. Static checks covered 4,368 map cells, all doors and NPC routes, camera edges, and sprite layering. mGBA core checks passed two-way Cherrygrove travel, six door round trips, Center stairs, ordinary save, cold reload, title Continue, 264 ordinary movement probes, and 1,800 NPC samples. Source and runtime evidence are in `evidence/build.json`, `structure.json`, and `runtime.json`.

`gba/floccesy-v4.patch` is an incremental patch over the currently installed v2 source. Forward and reverse `git apply --check` pass. The active `johto-restart-game` remains v2: Porymap is running on a locked Mac, so its unsaved editor state cannot be checked. Do not install this patch or point the builder at that source until the editor state is inspected. Playable isolated package: `tools/vendor/gba/Floccesy-detailed-preview-20260925.zip`; load its ROM with its matching save and choose Continue. ROMs and saves do not belong in Git.

Reproduce in the isolated source by running `build_floccesy_v4.py`, `check_floccesy_v4_structure.py`, `floccesy_v4_doors.py`, and `preserve_floccesy_v4.py` from the repository root. The builder checks the previous authored map hash and refuses unknown later edits.
