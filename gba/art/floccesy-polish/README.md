# Floccesy roofs, fences, park and woodland opening — September 26

This isolated native GBA revision addresses the owner's rejection of sloppy roofs, tree-over-roof pixels, fencing, park artwork and the northern entrance. Source: `tools/vendor/gba/floccesy-polish-work`. It is a playable preview, not an installation into active Porymap.

## Art changes and reference

The original map reference is `../floccesy-v4/references/owner-floccesy.jpg`. Existing native architecture and foliage are retained as source/provenance. `tools/gba/maps/floccesy_polish_art.py` authors the new reusable patterns; editable derived modules are saved in `native/`.

- Coherent fired-clay courses, shaded roof planes, shed ridge caps, lodge ridge/dormer, controlled Center enamel panels and clock roof planes replace fragmented old roof pixels. The Center glass band also uses consistent repeated panes. Full roof silhouettes render above intersecting canopy pixels. Tiny mixed-palette lawn gaps at roof/canopy junctions use a consistent foliage shade.
- Two-rail front modules, capped posts, narrow side runs and the same treatment on the eastern fence replace the previous single-bar fence graphics. Existing blocked cells and openings are unchanged.
- The park has a connected rounded gravel walk, clear bench apron, slatted bench, trimmed hedge blocks, ribbed bin and grouped flowers. The bench, hedges and bin keep their exact collision footprints; flowers remain decorative and walkable.
- The northern woodland opening is framed with the forest's native foliage and deep canopy shade, replacing the corrupted green cave-like shape. It remains the existing blocked decorative opening; this revision adds no usable exit or new interaction.

## Native limits and verification

The native compiler checks pixel-for-pixel equality between authored composition and decoded map. It reuses hidden lower layers, factors exact shared detail patterns across layers and repacks metatiles while reserving border IDs. There is no lossy tile reduction. Final map references 988 tile patterns; map plus border references 999 of 1,008 allocated patterns. Metatiles: 640. Palette banks: 0–12 only.

All 4,368 cells retain the prior cleanup revision's collision, elevation, behavior and layer properties. All event/map-script files, NPC routes, warps and other layout binaries are byte-identical. Door art references were regenerated after metatile repacking; door implementation is unchanged apart from art references.

The final ROM compiled with Arm GNU Toolchain 14.2.Rel1. Real mGBA checks passed paired traversal, wall blocking, garden exit, street movement, NPC dialogue/return, save, cold reload and ordinary title Continue; town travel, all six door round trips and Center stairs also passed. The final build passed 199 ordinary collision probes with zero failures; 1,800 NPC movement samples were recorded. Screenshot positions were checked as walkable. Runtime captures and the native map were visually inspected, including the final lodge dormer cleanup.

## Evidence and reproduction

- `evidence/revision-review.png`: actual in-game roof, lodge, park and forest-opening captures.
- `evidence/town-in-game.png`: eight actual in-game views, including fencing and other roofs.
- `evidence/town-overview.png`: decoded native map, not a concept image.
- `evidence/qualification.json`, `runtime.json`, `preservation.json`: final ROM identity, paired observations and preservation checks.
- Runtime door animation captures remain in `tools/vendor/gba/polish-town-proof`.

Run `build_floccesy_polish.py`, `floccesy_polish_doors.py`, and `check_floccesy_polish_structure.py` under `tools/gba/maps/`; compile the isolated ROM with the existing toolchain; run `qualify_floccesy_polish.py`, then `preserve_floccesy_polish.py`. The builder reads preserved v4 source and writes only its isolated workbench, carrying forward cleanup and arena treatments before applying this revision.

`gba/floccesy-polish.patch` applies over the prior cleanup workbench, with forward/reverse checks. Playable ZIP: `tools/vendor/gba/Floccesy-polish-20260926.zip`. Load matching ROM/save and choose Continue by the clock; walk north for the court, lodge and woodland opening. ROMs, saves and test binaries remain ignored. Preserve later owner edits before rebuilding or installing.
