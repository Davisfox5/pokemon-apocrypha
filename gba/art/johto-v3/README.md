# Cherrygrove trees, compositing and geography — revision 3

Owner direction, 2026-09-13: keep the preferred buildings, replace the stacked
tree crowns with one tree, correct scenery backgrounds, and align Cherrygrove's
geography with a reference map. This revision remains an isolated town preview.

## Art and map

- [Tree comparison](evidence/tree-comparison.png): the new generated source has
  one continuous crown and one trunk. Its aspect-preserving native import has
  29 × 40 pixels of content inside a 32 × 48 metatile-aligned canvas.
- [Full town overview](evidence/town-overview.png), rendered offline from the
  installed source. This is not an emulator screenshot.
- [Actual in-game captures](evidence/runtime.png), [walking](evidence/walk.gif),
  and [water animation around the boats](evidence/water.gif).
- [Playable revision 3](../../../tools/vendor/gba/Johto-art-v3-preview.zip).
  Use the included matching ordinary save; Continue starts at the southern pier.
- The house and Center use the exact revision 2 native pixels and palettes.
  All four houses still use the owner's preferred red-roof design.
- The Mart and blossom trees retain their previous native artwork. Their grass
  backgrounds are removed during native composition, as are the backgrounds of
  flowers, seating and waterfront props.

The new tree was edited using the built-in `image_gen` tool. The selected output
is [generated/tree.png](generated/tree.png), and the complete prompt and edit
target are in [prompts.json](prompts.json). It derives from the earlier Johto
tree source; original reference provenance remains in [v1](../johto-v1/README.md).
Native quantization uses twelve tree colors plus three exact grass colors in
bank 6, so foliage and ground can share a layer behind the unchanged buildings.

## Background correction

The old importer inserted a grass base behind every 16 × 16 object cell. When a
building overlapped a tree, that rectangular base erased the tree even where
the building artwork was transparent. Tree replacement by metatile ID also lost
the context of overlapping individual tree instances.

The new compiler composes terrain and each object in placement order. Transparent
pixels preserve the existing scenery. It packs the final visible pixels into
two legal palette-selected 4bpp layers per quadrant, reusing native tiles where
possible. It refuses unrepresentable color combinations or tile overflows.
No approximation or quantization is applied to the approved buildings.

Static compositions exclude the primary tileset's animated VRAM slots. The first
runtime inspection caught sand pixels aliasing an animated shoreline slot despite
a correct static image; that reuse is now explicitly rejected. Unchanged terrain
retains its original native references, including intentional water animation.
Where a single foreground palette suffices, original terrain also remains as the
live lower layer beneath the object. This preserves 48 animated water quadrants
under the boat edges instead of baking static water into their backgrounds.

The compiler checks every transparent and opaque house/Center source pixel, then
decodes every installed map tile and verifies an exact full-scene pixel round
trip. This covers the native import, not just the high-resolution source PNG.

## Geography reference

The [HGSS Cherrygrove map on Bulbagarden Archives](https://archives.bulbagarden.net/wiki/File:Cherrygrove_City_HGSS.png)
was checked again on 2026-09-13; its preserved image is
[the original reference](../johto-v1/references/cherrygrove-hgss.png).
This is game imagery by Game Freak / Nintendo / Creatures, used as a visual
reference, not an imported DS map or an original asset ownership claim.

The new 64 × 40 layout restores the reference's broad **western bay**, northern
coastal cliff, curved west-facing beach, offshore rocky island and sandbar.
The settled area is east of the bay, the Mart is west of the Center, Route 30
leaves north and Route 29 leaves east. The former full-width southern ocean
strip is replaced by a southern forest and a beach at the bay's southern lip.

The fourth home, blossom park, practice yard and fishing waterfront are the
established Apocrypha additions. This is an adaptation of HGSS geography to those
requirements and the approved buildings, not an exact tile-for-tile map copy.
No new story interaction, reward or field-move access was added to the island.

## Source and reproduction

- Layout: [town-v3.json](../../maps/cherrygrove/town-v3.json). Previous layout
  sources are retained for reproducibility.
- Compiler: `tools/gba/maps/install_johto_art_v3.py`.
- Dedicated checkout: `tools/vendor/gba/johto-art-v3-game`.
- Clean source clone: `tools/vendor/gba/johto-art-v3-baseline`.
- Both clones start at town commit `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`.
  The compiler always reads the clean baseline, never a previously generated
  tileset. It does not modify production `game/` or the older art previews.
- Native assets and composition checks: [integration.json](evidence/integration.json).
- Preserved engine changes: [johto-art-v3.patch](../../johto-art-v3.patch), applied
  directly to the clean town baseline, not on top of the v1 or v2 art patches.

```sh
python3 tools/gba/maps/install_johto_art_v3.py tools/vendor/gba/johto-art-v3-game
gmake -C tools/vendor/gba/johto-art-v3-game -j8 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
python3 tools/gba/maps/validate_cherrygrove.py tools/vendor/gba/johto-art-v3-game gba/maps/cherrygrove/town-v3.json
python3 tools/gba/maps/check_cherrygrove.py tools/vendor/gba/johto-art-v3-game tools/vendor/gba/johto-art-v3-new-run --toolchain tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi --runtime-source tools/gba/maps/cherrygrove_v3_runtime.c
```

Fresh clones need the qualified ignored `tools/compresSmol` dependency copied
from the existing v2 checkout, as documented for the previous preview.

## Validation status

The final ROM builds successfully: 19,649,436 linked ROM bytes, 226,736 EWRAM bytes,
28,392 IWRAM bytes. The town uses **293/512 secondary tiles** and **141/512 secondary
metatiles**. Native composition and structural checks pass: eleven maps, six
exterior doors, resolved event scripts/warps/connections, reachable entrances and
landmarks, and 4,266 padded map cells within the 10,240-cell limit.

All three final mGBA runtime phases pass: all six entries and returns, player-home
stairs, both route connections and returns, pier collision, resident dialogue,
shop interaction, ordinary 128 KiB flash save, fresh-process reload and normal
title-menu Continue. Native 240 × 160 screenshots, walking frames and eight water
animation frames were inspected. Evidence is in [build.json](evidence/build.json),
[runtime-results.json](evidence/runtime-results.json) and
[structural.json](evidence/structural.json). The known linker RWX warning remains.
The source patch passes forward and reverse checks against the preserved town
baseline. The package's ROM hash and save size were verified after compression.

Chapter scenes, bespoke door animation frames, Gold/Kestra/Silver art, starter
events and the deferred production save architecture remain outside this revision.
