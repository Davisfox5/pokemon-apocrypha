# Sandgem Town — owner-reference revision

The owner's original-game screenshot in `references/owner-sandgem.png` is the visual authority. The rejected earlier interpretation with water, grey-blue lab and sparse pine trees is preserved at `tools/vendor/gba/sandgem-rejected-20260922`. Do not resume it.

Current exterior is 48x40 including forest buffers. The asymmetric turquoise-roofed lab is northwest, orange Center beside it, blue compact Mart northeast, two differently sized blue-gabled houses south, mint grass and pale paths, dense yellow-green forest, and dry sand southeast. No water. Native engine limitations mean this is a custom 2D adaptation, not a pixel-exact screenshot reproduction. The north and west onward routes are visibly fenced until those locations are built.

Custom bitmap assets were generated with the built-in image_gen tool, using the owner image for every asset. Full exact prompts and generation paths are in `prompts.json`. `generated/*-reference.png` are retained originals, `native/` contains palette-constrained editable PNGs and palettes. Pokémon and reference designs belong to Game Freak/Nintendo/Creatures. Existing character sources retain their regional-scale/Johto-import provenance.

## Play and connection

Source: `tools/vendor/gba/johto-restart-game`. Open `tools/vendor/gba/Sandgem-reference-20260922/Sandgem.gba` with its matching `.sav` and choose Continue. Start is (29,29), near the southern sand path. Walk south into Cherrygrove's northern approach; walk north from Cherrygrove to return. This owner-requested cross-region preview connection is implemented as normal directional path warps with a screen transition so each region loads its own tiles and palette. It does not declare permanent story geography.

Cherrygrove map.bin is byte-identical to the accepted collision-audit revision. Only three copied metatiles and warp events were added to its northern approach. Original live ROM/save folders were not overwritten. Use the new matching preview save; the rejected Sandgem draft had different coordinates.

## Validation and limits

See `evidence/build.json` for tested ROM hash and preview path. `runtime.json` proves normal travel in both directions, all five building entry/exit pairs, Center stairs, save, cold reload and ordinary Continue. `cherrygrove-regression.json` reruns its seven doors, stairs, both routes, island and save checks. All 55 representative native collision probes pass; all 1,920 exterior cells are classified, all door approaches and resident paths connect, and 420 reachable cells have covered camera footprints. No water behavior remains. Exact decoded pixel roundtrip and tile animation exclusion checks pass.

Interiors currently use existing Emerald lab, house, Mart and Center room artwork with fresh preview maps and no donor story triggers. They are not custom Sinnoh interiors. Six regional residents use normal engine walking; generic dialogue is preview staging. No wider campaign, encounter or progression design was introduced.

Visual evidence: `evidence/town-overview.png` is a decoded exterior; `evidence/in-game.png` and `evidence/walking-tour.gif` are actual native engine captures. Porymap has the current SandgemTown open; mGBA launched the matching revision.

## Preservation and reproduction

`gba/sandgem.patch` is standalone above baseline `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. It includes accepted Cherrygrove plus Sandgem; do not apply old art patches first. Forward and reverse checks are recorded in `evidence/patch.json`. Never commit ROMs or saves.

Helpers: `build_sandgem.py`, `install_sandgem.py`, `sandgem_doors.py`, `check_sandgem_structure.py`, `sandgem_runtime.c`, `sandgem_npc_runtime.c`, `preserve_sandgem.py` under `tools/gba/maps/`. These builders describe this snapshot: do not rerun them over subsequent owner edits. The installer reads the pre-Sandgem snapshot for three approach tiles; preserve/reconcile later owner changes first.
