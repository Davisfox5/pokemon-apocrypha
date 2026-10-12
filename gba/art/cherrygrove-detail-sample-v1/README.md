# Cherrygrove native detail sample — September 30

Owner rejected the first whole-town artwork conversion's visual quality, then authorized a small section test before deciding whether to continue the approach. This is that test: one house, trees, grass and path edges from the reviewed revision-3 image. Both earlier full-town versions and all owner/editor/campaign work remain untouched. Only `tools/vendor/gba/cherrygrove-detail-sample-work` is edited.

## What changed

The first converter classified terrain in 8-pixel chunks and replaced it with a few repeated, muted textures; building/tree extraction also changed silhouettes. This test preserves all reference contours and uses color-distribution clustering to allocate thirteen shared GBA palette banks, with fifteen opaque colors per bank. It uses no dithering or antialiasing after native palette assignment. Input rectangle `(768,448)-(1280,832)` is reduced to 256x192 with box filtering and hardware RGB5 precision, then encoded as actual 4bpp 8x8 patterns and 16x16 metatiles. No new image generation was used. Reference artwork and architectural designs retain the previous five-town provenance.

`evidence/comparison.png` shows reference at native scale, prior rejected conversion, and revised decoded native tiles. `evidence/in-game-review.png` contains two real headless-mGBA captures at exact 2x scale. These are engine output, not the concept image pasted over a screenshot. Exact tile encode/decode equality passes for the palette-reduced native result.

## Constraint exposed

769 tile patterns, 193 metatiles, 13 palette banks. Almost every small pattern is unique: this section alone occupies roughly 76% of the 1008-pattern scenery budget. This establishes a closer visual target under native display rules, **not a scalable full-town tileset**. The next production step, if this quality is accepted, is reusable leafy tree assets, turf patches, grass/path edge modules and building materials that preserve this appearance. Do not stamp unique image rectangles throughout a full town or treat this sample as a finished town conversion.

## Engine validation and limits

Compilation passes. Runtime enters the 32x24 isolated test room, captures the house and grass/trees, confirms walking on the path and house collision, and writes an ordinary 131072-byte fresh save. Cold save reload/title Continue were not separately tested. No desktop emulator was opened. The test room has no NPCs, working entrance or regional connection: those systems in the earlier whole-town work were preserved rather than rebuilt here. Collision is only coarse sample staging and is not a finished per-tile audit.

Package: `tools/vendor/gba/Cherrygrove-detail-sample-20260930.zip`. Changed source overlay and base/sample SHA256 hashes are preserved here. ROM/save remain ignored under tools/vendor. Production `game/`, the owner-edited `johto-restart-game`, the prior `cherrygrove-art-study-work` and campaign workbenches were not modified.

Reproduction: copy the prior isolated study into a new `cherrygrove-detail-sample-work`, run `python3 tools/gba/maps/build_cherrygrove_detail_sample.py`, then use its ordinary gmake ARM-toolchain build. The compiler deliberately targets only this sample workbench. `tools/gba/maps/cherrygrove_detail_sample_runtime.c` records focused runtime proof using libmGBA. Do not rerun over subsequent authored changes without preserving them first.
