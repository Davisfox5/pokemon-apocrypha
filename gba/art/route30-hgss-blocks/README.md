# Route 30: independent HGSS block reconstruction

Engine branch `codex/route30-hgss-blocks`, commit `aa8ea35eea378b5d69c58b5f5c0c2f566689c6ac`, based on production `apocrypha` (`2722eaf`). The previous Route 30 reconstruction remains on `codex/route30-rebuild`; its evidence remains on `codex/route30-review`. This is a new reconstruction proposal, not a declaration of owner visual acceptance.

## Owner correction: complete trees and native Emerald terrain

The owner authorized widening forest strips into open ground while keeping paths clear. This revision removes every cropped woodland-margin filler and places 337 complete Cherrygrove trees, absorbing 189 non-forest cells. The lower western separator moves one column east and the eastern wall narrows by one column, making room for complete pairs. Remaining narrow blocked terrain uses native Emerald rock rather than foliage cutouts. The original HGSS survey remains editable; `forest.py` records these explicit owner-authorized liberties. Existing Cherrygrove connection art remains preserved.

Stairs, walls and ledges now decode original Emerald Expansion `primary/general` metatiles with unchanged colors in the already shared bank 8. IDs and provenance are in `source/emerald-assets.json`; no custom HGSS stairs, CG cliffs or custom ledges are used. Cut uses `OBJ_EVENT_GFX_CUTTABLE_TREE` and `EventScript_CutTree`, with standard temporary reset flag 13 and passable underlying terrain. Its object blocks movement and shows the standard Cut interaction. The empty-party test exercises the cannot-cut response; successful party HM use has not been separately exercised.

[Before/after forest and terrain comparison](evidence/forest-before-after.png)

## Review

- [Whole HGSS/native comparison](evidence/whole-map-comparison.png)
- [Native complete map with Cut-object preview](evidence/native-proposal-with-objects.png)
- [Gameplay gallery at 2x nearest-neighbor scale](evidence/gameplay-gallery.png)
- [Northern connection progression](evidence/north-crossing.gif)
- [Tree footprint overlay](evidence/tree-footprints.png): amber ground footprint; blue upper canopy.
- Seven `evidence/comparison-rows-*.png` boards compare twelve-row sections at native scale. The overview adds the native Cut object sprite at its map position; `native-proposal.png` remains the exact terrain-only Porymap export. Individual 240x160 emulator frames are in `evidence/gameplay/`.

## Source authority and reconstruction

`source/hgss-reference.png` is the existing verified HGSS overview from `gba/art/claude-routes/references/route30-hgss.png`, not Claude's Gen 3 layout. Its digest and measured registration are in `source/reference.json`. `source/blocks.txt` is an independently classified 35-column, 74-row survey; `structures.json` records measured buildings, ponds, stairs, ledges, signs, apricorns and the Cut barrier. `terrain.txt` separates ground from structures. `block-ledger.json` records each source box and inferred native collision.

The overview is 563x1196, registered at (6,4) on a 16px grid. Column 34 has thirteen visible pixels rather than sixteen; missing pixels are marked dark in comparisons. Eight leftover pixels below row 73 are excluded. This is image reconstruction, not recovery of original DS map/collision records. Sprite perspective and native grid rounding require interpretation; stair heights and roofs are native adaptations.

All 2,590 surveyed core blocks are reconstructed independently: zero core cells copy prior Gen 3 blockdata. Rows 74-85 are a separate connection adapter to the established Cherrygrove approach. The partly clipped southern pond is completed through two adapter rows. Immutable baseline libraries are preserved under `source/seam-baseline/`; previous layout data is consulted only for library reservations and the southern compatibility adapter. Old layout generators are not run.

The large trees and both houses reuse accepted Cherrygrove native art. Ordinary ground is selected from existing static Cherrygrove bank-0 glyphs. Main tree ground footprints are exclusive 2x2 rectangles with a 2x3 sprite; only the upper canopy may overlap the rear tree. The narrow HGSS divider has explicitly measured 1x2 physical footprints and a walkable western canopy overhang. Canopies use the foreground layer; ground shadows use the lower layer. No one-cell woodland-margin foliage is emitted in the corrected build.

Tall grass is derived from the existing decoded real HGSS `egrass`, `egrass_u`, `egrass_v` texture files under `gba/art/johto-cohesion/references`. Six ranked blade shades and sixteen adjacency variants are preserved. Porytiles compiles this isolated family and its decoded output is checked for exact RGB and alpha equality before import into native bank 12. Shared Cherrygrove tilesets are not compiler input. Materials and intermediate source PNGs remain editable.

Two-layer hardware packing sometimes requires an opaque terrain background under a foreground canopy or roof. Palette 7 is reserved for these native composites; four Cherrygrove ground anchors and the ground-shadow shade are pinned. Across 46 background glyphs, 0 pixels undergo native terrain colour cleanup, with maximum channel delta 0. Foreground scenery pixels are unchanged. The cleaned backgrounds are preserved in `source/overhang-backgrounds/`.

Route 31 receives only appended shared seam metatiles, unused zero tile-padding storage and its unused palette 7. Existing nonzero graphics, metatile IDs, layout and scripts stay unchanged; decoded Route 31 itself is pixel-identical. Door slots 1008-1023 are reserved. Cherrygrove tilesets/layout, Route 29, New Bark and Violet remain untouched and their Porymap exports are pixel-identical.

## Verification and limits

`evidence/block-validation.json` checks the authored survey against native collision and grass/water/ledge behavior, exact Porymap render equality, neighboring-map equality and both connection camera windows. Cached 16x16 crossing-window tile glyphs are identical with either secondary tileset. Three northern offscreen blocks use different bank-12 colours; they are outside the conservatively enlarged visible camera at the switch, and palettes reload before they enter view. Actual crossing progression is included for review.

The ROM builds successfully. The corrected source also passes the [production CI build and Poryscript freshness check](https://github.com/Davisfox5/pokeemerald-expansion/actions/runs/38334728321/job/115092148759). Headless libmGBA 0.10.5 walks the entire route with ordinary directional inputs, crosses both connections in both directions, checks ten woodland/cliff barriers, the ledge bypass, directional ledge jumps, Cut barrier, pond collision, grass movement and all three signs. Doors remain closed. The native Cut object blocks movement and responds to interaction. An ordinary 128KiB save reloads through both cold resume and title-screen Continue. Fixtures only position the player for isolated probes; the main traversal uses normal movement. No desktop game is opened. Tests demonstrate implementation consistency, not a pixel-exact original DS collision match or aesthetic approval.

Remaining limits: existing house interiors are not implemented; original NPC/story gates are not reconstructed. The added northern sign reuses the existing route-sign script, not recovered HGSS text. Pond artwork is static. The southern connection adapter and shoreline completion are explicit integration adaptations. No new story roles, quests, mechanics or dialogue were introduced.

## Reproduction

Python dependencies: numpy, Pillow; porygon MCP environment for applying. Work in an isolated checkout from the stated engine base. These are provenance tools for this reconstruction, not instructions to overwrite the production layout routinely. Edit committed native layouts with Porymap after review.

```sh
python tools/gba/maps/route30_hgss_blocks/trace.py
python tools/gba/maps/route30_hgss_blocks/assemble.py /path/to/apocrypha-src
/path/to/porygon/.venv/bin/python tools/gba/maps/route30_hgss_blocks/apply.py /path/to/apocrypha-src
make -C /path/to/apocrypha-src -j1 generated
make -C /path/to/apocrypha-src -j8
python tools/gba/maps/route30_hgss_blocks/runtime.py /path/to/apocrypha-src /new/output --toolchain /path/to/arm-toolchain
python tools/gba/maps/route30_hgss_blocks/review.py /path/to/apocrypha-src /porymap/export /baseline/export /runtime/output
```

Porytiles native output and source layers are checked in to preserve reproducibility without repacking unrelated native banks. Engine source is committed directly, not stored as patch stacks. ROMs, saves, tools and binaries are excluded.
