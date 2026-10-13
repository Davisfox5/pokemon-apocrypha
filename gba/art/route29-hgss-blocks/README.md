# Route 29: HGSS survey, complete trees and Emerald terrain

Source: `Davisfox5/pokeemerald-expansion`, branch `codex/route29-hgss-blocks`, commit `fd1d4bf872b8365e3fe737fdd6e293c6c4f13631`, draft [PR #6](https://github.com/Davisfox5/pokeemerald-expansion/pull/6) against `apocrypha` (`2722eaf`). This is the owner's requested Route 29 reconstruction using the corrected Route 30 method. Visual acceptance is pending.

## Review

- [Whole HGSS/native interior comparison](evidence/whole-map-comparison.png)
- [Complete native map with the retained coast](evidence/native-proposal.png)
- [West](evidence/comparison-west.png), [central](evidence/comparison-central.png), [east](evidence/comparison-east.png) sections at matching block coordinates
- [Claude's prior proposal versus the reconstruction](evidence/claude-before-after.png)
- [Native gameplay gallery](evidence/gameplay-gallery.png), [New Bark crossing progression](evidence/new-bark-crossing.gif)
- [Whole-tree footprint overlay](evidence/tree-footprints.png): amber exclusive ground footprint, blue upper canopy

## Layout authority and explicit adaptations

The existing verified HGSS overview `gba/art/claude-routes/references/route29-hgss.png` is the layout authority. `source/reference.json` records its digest and grid registration at (4,5), 16px cells, 98 columns and 34 complete rows. `trace.py` independently surveys all 3,332 cells by source color and measured structures. No earlier Gen 3 plan array or `R29_OPS` supplies the reconstructed interior. The nine extra pixels at the image's right and bottom are outside this full-cell survey.

The editable `blocks.txt`, `structures.json` and per-cell ledger preserve the survey. Native source rows 0-26 sit at map rows 2-28. The accepted sea ridge, coast and lookout override the reference's lower forest from native row 29 south, and the lookout pocket at columns 54-63 / rows 25-28 is retained. Ten-column western/eastern town adapters preserve the existing connections; these are explicitly retained native integration areas, not independently recovered HGSS data.

There are 317 complete Cherrygrove trees, exclusive 2x2 ground rectangles, and 2x3 native sprite canvases. No cropped one-cell crown fillers are emitted. Woods can absorb spare lawn/grass under the owner's approved liberty. Measured main, gate and eastern grass passages are reserved before tree placement, including ground behind upper canopies; they are preserved as explicit walk cells in the assembly report. Remaining narrow blocked terrain uses complete native rock cells. Original DS collision/elevation records were not recovered: this is image-inferred ground plus deliberate native footprint adaptations, not a claim of byte-exact HGSS collision.

Ordinary ground reuses opaque static Cherrygrove bank-0 tiles. Trees, the Apricorn silhouette conversion, flowers and signs use the established native palette vocabulary. Tall grass reuses the accepted real HGSS TEX0 `egrass`, `egrass_u` and `egrass_v` family: sixteen edge variants, compiled separately with Porytiles legacy 2.0.0 and verified for exact RGB/alpha equality before import. The compiled family is preserved with its editable source layers. The new terrain uses 137 secondary tile slots and 240 metatiles; primary and untouched-map IDs remain unchanged.

The Route 46 gate replaces the mismatched HGSS cutout with an 80x112 native gate made from accepted Cherrygrove gable/roof/wall/window pixels. Its two extra wall courses are an authored native adaptation; no story role is added. Gray entrance steps use original Emerald general 0x0af/0x0cf. Interior walls and ledges use original Emerald general directional rock and end/middle ledge pieces with original colors in bank 8; exact source IDs are in `source/emerald-assets.json`. The coast retains its accepted Cherrygrove art. There are no original Cut-tree barriers on this reference, so none are invented.

The original western sign falls inside the retained Cherrygrove adapter. Its native placement is (12,17), outside the camera buffer with a clear door-size approach, using the existing route-sign text. The eastern sign and existing hidden Potion event/flag stay unchanged and retain their event indices. No dialogue, quests, mechanics or NPC roles are invented.

## Verification

Porygon MCP applies the map byte-for-byte and appends the shifted sign. Porymap 6.3.1 project-core export matches the decoded native terrain exactly. This does not claim a manual desktop UI edit/save. Both directions of both town connections have zero visible palette/pixel mismatches and zero cached 16x16-window glyph mismatches, including an offscreen New Bark flower glyph reserved at its existing ID. Protected adapters and coast match the original map words exactly. Cherrygrove, New Bark, Route 30, Route 31 and Violet remain unchanged relative to the engine base; Route 30's separately accepted work remains on its own PR #4.

The local ROM builds. Headless libmGBA 0.10.5 traverses the entire route with ordinary directional inputs, visits gate/grass/Apricorn/lookout landmarks, crosses both towns in both directions, tests eight barriers, two one-way ledges, grass walking and both signs, and reloads an ordinary 128KiB save through cold resume and title Continue. Fixture positioning is used only for isolated probes; the main traversal uses normal movement. The current source's New Bark map ID is 28, Route 29 is 9; the harness uses the current IDs. No desktop game is opened. Functional checks are implementation evidence, not owner visual acceptance.

Concrete limits: Route 46's gate is closed; its interior and onward route are not implemented. The Apricorn is decorative, without a harvesting script. Original NPC/story gates are not introduced. The hidden Potion's event/flag and reachable location are preserved, but this pass does not independently exercise item collection. Town adapters, the coast and native canopy/collision interpretations are explicit deviations from literal full-image reconstruction. All previous Claude and Route 30 drafts remain preserved on their original branches/commits.

## Provenance and reproduction

Reusable packing/ground/forest utility code derives from the accepted Route 30 reconstruction (engine `aa8ea35e`, hub `42cccb2`). Native Cherrygrove art is under `gba/art/cherrygrove-synthesis`; decoded texture references are under `gba/art/johto-cohesion/references`. Immutable original libraries and the prior layout are preserved in `source/baseline` solely for native ID reservation and the named adapters/coast. Claude's inspected prior engine branch is `claude/route29-hgss-slices`, commit `4e20e557`; its overview and provenance remain in `gba/art/apoc-route29`.

Use an isolated checkout of the stated engine base. These tools are provenance for the authorized reconstruction, not a reason to replay generation over later owner edits. Native committed layouts stay editable in Porymap.

```sh
python tools/gba/maps/route29_hgss_blocks/trace.py
python tools/gba/maps/route29_hgss_blocks/assemble.py /path/to/apocrypha-src
/path/to/porygon/.venv/bin/python tools/gba/maps/route29_hgss_blocks/apply.py /path/to/apocrypha-src
make -C /path/to/apocrypha-src -j1 generated
make -C /path/to/apocrypha-src -j8
python tools/gba/maps/route29_hgss_blocks/runtime.py /path/to/apocrypha-src /new/output --toolchain /path/to/arm-toolchain
python tools/gba/maps/route29_hgss_blocks/review.py /path/to/apocrypha-src /porymap/export /baseline/export /runtime/output
```

Source is committed directly to the expansion fork. ROMs, saves, binaries and tool executables are excluded. Editable PNGs, palette/metatile assets, source grids, native screenshots, verification records and reproducible authoring code are preserved in this hub branch.
