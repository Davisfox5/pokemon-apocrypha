# Routes 38 and 39 — native terrain-only review

The owner was broadly satisfied with Ecruteak and requested the Olivine–Ecruteak
connection stripped to its terrain before any further town/route dressing.
This pass adds actual editable native maps `JohtoRoute38` (68×33) and
`JohtoRoute39` (38×56). Open `/workspace/apocrypha-src` directly in Porymap.
The maps are appended as IDs 53 and 54 in group80; existing IDs are unchanged.
The source branch is `codex/route38-39-terrain` on the expansion fork.

All trees, buildings (including Moomoo Farm/windmill/gate), fences, props,
characters, tall grass and jump ledges are absent. Their footprints are ordinary
lawn or the continuing path, with no leftover object collision, wild encounters,
or jump/grass behavior. Rock walls and the two north–south stairways remain.
Both maps share one private tileset and their three-lane junction is a genuine
bidirectional native map connection, offset by two cells. City exits remain
unwired and the preview's outer perimeter is bounded. Ecruteak is unchanged.

## Geography and intentional interpretation

Reference: original HGSS overview images from Bulbagarden Archives:
[Route38](https://archives.bulbagarden.net/media/upload/6/64/Johto_Route_38_HGSS.png)
(1077×513), [Route39](https://archives.bulbagarden.net/media/upload/0/08/Johto_Route_39_HGSS.png)
(599×883). Source images, hashes, explicit path polygons and each rock/stair
module placement are retained under `source/`. Route38 reference origin is
native(0,0); Route39 origin is native(8,8), resolving its half-cell phase and
aligning the east–west path. Marginal padding completes native cells.

This is an overview trace, **not extracted original collision or height data**.
Visible paths, exposed cliff contours and stairs anchor the terrain. Ground
beneath removed foreground and forest-covered continuations of the rock banks
are inferred. Exposed wall placements are registered to native16px modules;
sub-cell projection differences are approximated. The long forest-covered
continuations/caps are a first-pass interpretation for owner height review.
Do not treat those hidden contours as proven HGSS geography.

Relative native planes are farm/main Route38=5, central Route39 valley=3,
south end/outer clefts=1; stair cells0 bridge the corresponding planes. The
small original jump ledges have been flattened as requested. Every remaining
nonzero elevation boundary meets rock collision; no invisible height seams remain.
The farm stair approaches are extended locally across the removed fence gap
so dirt joins the first and last treads cleanly.

## Art and native source

Ordinary lawn/path and intact directional rock modules reuse the accepted
Azalea/Route32 material family. Stair treads are the original Emerald general
0xaf/0xcf family, reduced explicitly to native RGB5 and fitted to local ground.
No generated image is used as the map. Provenance and donor hashes are in
`source/provenance.json`. Porytiles2.0.0 performs exact tile/palette packing.
Both routes use one new primary/secondary pair `route38_39`; unrelated tilesets
and layouts retain their bytes. The initial authoring helper refuses tracked
layouts; committed map.bin/metatiles/palettes are the authoritative editable source.

[Whole native overview](evidence/native-overview.png) ·
[Route38 comparison](evidence/route38-comparison.png) ·
[Route39 comparison](evidence/route39-comparison.png) ·
[Gameplay](evidence/gameplay-contact.png)

Coordinate-labelled source/native grids, conservative per-cell reference-occlusion coverage, a per-cell material/traversal ledger,
relative-level views and focused stair review accompany those sheets.
The gameplay preview contains only the ordinary player avatar, with no designed
story actors or encounters. This is a terrain review, not finished route dressing.

## Verification and reproduction

`evidence/preservation.json` pins the source parent, published source, final ROM,
tool versions, review findings and test results. `native-audit.json` covers all
4372 cells: decoded tiles match the authored RGB5 pixels exactly, no forbidden
behaviors, no adjacent open nonzero height seams. Actual Porymap6.3.1 exports
match the decoded native images. `gameplay-pixels.json` compares native terrain
against actual mGBA frames outside the player avatar; all checked pixels match.

Run initial authoring only on an untracked new map (never over owner edits):
`python3 tools/gba/maps/route38_39/build.py ENGINE PORYTILES_LEGACY`, then
`register.py ENGINE`. Run `review.py ENGINE` independently against current native
source. Build the expansion with `make -j1 generated` after `make tools`, then
`make -j8 TOOLCHAIN=...`. `runtime.py ENGINE NEW_OUTPUT --toolchain ...` exercises
stairs both ways, cleared object footprints, all three connection lanes both
ways, ordinary flash save/cold reload/title Continue. Add `--boundaries` for the
788 open-to-blocked native edge probes. `MGBA_FLAGS` can select libmGBA headers/libs.
The Porymap exporter links a narrow probe against the installed6.3.1 object files;
it uses Porymap's actual Project/Layout renderer, not a replacement editor.

ROMs, saves and tool binaries are excluded from Git. The downloadable ZIP is
outside the repositories and contains a matched ROM/save; choose Continue.
Owner visual acceptance remains pending for these new route terrains.
