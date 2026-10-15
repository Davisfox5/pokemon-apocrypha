# Route 33 — HGSS grid reconstruction

Source: `Davisfox5/pokeemerald-expansion`, `codex/route33-hgss`,
`224ee13c392888780bdcaeb7053487f42a9ab731`, [engine PR10](https://github.com/Davisfox5/pokeemerald-expansion/pull/10).
Depends on the owner-reviewed Union Cave `fc1017f` / PR9, and Route32 PR8.
The owner accepted the current cave for now and requested the next route with a
detailed first pass under all AGENTS.md map rules. This is Route33, south of the cave.

## Readable visuals

- [Whole native map](evidence/native-map.png)
- [HGSS / native comparison](evidence/comparison.png)
- [Close-up terrain and transition review](evidence/detail-review.png)
- [Native gameplay and cave travel](evidence/gameplay-gallery.png)
- [Original numbered grid](evidence/reference-grid.png) / [native grid](evidence/native-grid.png)

## Reference and design

[Original HGSS overview](https://archives.bulbagarden.net/media/upload/8/8b/Johto_Route_33_HGSS.png),
528×463px, Nintendo / Game Freak / Creatures. Register at (0,0), 16px native
squares and 8px hardware quadrants. Final 34×29 map includes 16px eastern framing
and a single southern padding pixel. This is an overview reconstruction;
traversal is interpreted from visible original geography, not decoded DS collision.

Preserves the original tiered cliff silhouettes, nested upper terrace, cave arch,
L-shaped one-way ledge, western dirt approach, southern grass block, forest bounds,
two boulders and two apricorn silhouettes. Complete accepted Cherrygrove trees
occupy distinct two-by-two root footprints with supported canopy overlap.
Interstitial gaps behind the upper ridge remain blocked. Ledges reuse Emerald's
west/south family, with a fitted lower corner. Shared Cherrygrove grass/dirt and
Route32's coherent HGSS-native grass family retain their palettes. Original cliff
pixels receive local native palette conversion; geometry is not replaced by
nearest-color blocks. The mouth retains its original threshold and fitted dirt
apron. Native rain matches Route33. No houses or campaign content are invented.

Separate editable material grid, detailed cell ledger, collision/behavior arrays,
foreground/background art and source registration are in `source/`. The 946
native glyphs use exact flip deduplication with 1008–1023 reserved. There are 331
metatiles. The two private tilesets preserve unrelated palettes/metatile IDs.
The south cave doorway gains appended warp3 and its unique threshold's exit
behavior; cave artwork, layout/collision and existing warp IDs are unchanged.

## Validation and reproduction

Actual Porymap 6.3.1 export equals decoded native RGB across all 986 cells;
behavior/collision agree with their separate ledger. Review sheets cover the arch,
cliff shoulder and concave corner, ledge head/return, forest feet, boulders and
path/grass/canopy junction. Porytiles validates 128 representative layered native
metatiles with zero RGB/alpha errors. Its standalone validation combines the
engine's two banks under a 13-palette capacity; it does not repack engine art.

The local 32MiB ROM builds with Arm GNU14.2. Headless libmGBA checks cover travel
through the real cave mouth both ways, ordinary walking around the ledge, both
jump directions and blocked returns, forest/cliff/fruit footprints, tall grass,
closed Azalea endpoint and an ordinary 128KiB save/cold reload/title Continue.
A copied prior cave save also loads and Continues; the original is unchanged.
Exact source/ROM hash, observations and scope are in `evidence/build.json`,
`runtime.json`, `prior-cave-save.json` and `preservation.json`.
All 52 owned source files reproduce byte-identically, normalizing palette EOLs.

The scripts in `tools/gba/maps/route33_hgss/` are provenance, not an editor.
`build.py` then `register.py` reproduce the initial authoring ONLY in an isolated
checkout of exact `fc1017f`; never replay them over committed/owner native layouts.
Use the current engine native source and installed Porymap for subsequent edits.
`review.py ENGINE PORYMAP_EXPORT_DIR`, `check_art.py ENGINE PORYTILES_BINARY`,
`runtime.py ENGINE NEW_OUTPUT --toolchain ARM_ROOT` and
`publish.py ENGINE RUNTIME_OUTPUT` perform the documented checks. See the source
native lock and reproduction report. Preserve earlier working material and saves.

## Concrete limits

Azalea is not built, so the visible western approach is closed at its boundary.
Apricorn art has no harvest scripts. Actors, encounters, sign dialogue and campaign
triggers are outside this map-art pass. Small flower decoration is simplified.
Some tree shapes and ledge profiles deliberately use the accepted Gen3 vocabulary.
Water in the inaccessible eastern framing is static. CI is separate from local
checks; the PR stays draft. Functional checks do not establish owner visual acceptance.
