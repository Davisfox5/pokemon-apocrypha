# Johto generated-source import revision

The owner preferred the generated house and Pokémon Center to their first map
imports (2026-09-13). Those same generated designs are now imported with their
original aspect ratios, a larger native grid and two shared building palettes.
No new building designs were generated for this revision.

- House source: [house-final.png](../johto-v1/generated/house-final.png), the
  transparency-corrected version of the generated house.
- Center source: [center.png](../johto-v1/generated/center.png).
- Provenance, reference images and generation prompts remain in the
  [original sample pack](../johto-v1/README.md).
- [Before/after native comparison](comparison.png).
- [Actual in-game captures](evidence/runtime.png) and [movement](evidence/walk.gif).
- [Playable revised preview](../../../tools/vendor/gba/Johto-art-v2-preview.zip).
- [Full-town render](evidence/town-overview.png) is an offline source render.

Both buildings occupy 80×80 native pixels. The house previously occupied 80×64,
which compressed its almost-square source vertically. The Center previously
occupied 64×64; its enlarged grid now retains the roof squares and window detail.
The converter preserves aspect ratio, centers horizontally and aligns the bottom.
The original high-resolution images still undergo GBA palette and pixel reduction.

Each 8×8 building tile selects palette bank 8 or 10, with 15 opaque RGB555 colors
per bank. A deterministic iterative palette assignment separates the roof and
facade color groups, preserving blue glass and other small details that lost out
to the roof's area in the old single-palette import. These banks are shared by
both buildings, so no other town palette is displaced. The existing tree import
remains unchanged in bank 6. Native building PNGs are RGBA inspection previews;
the `.4bpp`, bank map in `native/manifest.json`, and `.pal` files are the actual
engine inputs. A multi-bank sprite cannot be represented by one 16-color PNG.

Roofs extend one metatile north. The Center's left edge stays at the previous
art preview's x=31. All six exterior door coordinates, scripts and destination
warps remain unchanged. The town uses 402/512 secondary tiles and 231/512
secondary metatiles. Other scenery remains from the first town preview.

## Verified result

The ROM builds successfully (19,650,436 linked ROM bytes; 226,736 EWRAM bytes;
28,392 IWRAM bytes). All three mGBA runtime phases pass: six building entries and
returns, player-home stairs, route connections, pier collision, dialogue/shop
interaction, ordinary flash save, cold reload and title-menu Continue. Eleven
maps pass structural checks. The enlarged roof footprints leave all entrances
and tested landmarks reachable. Static native pixels match installed tile and
palette data exactly, including a 4bpp round trip. The patch passes forward and
reverse application checks against the preserved town baseline.

Native 240×160 captures and movement frames were inspected. The gallery harness
is `tools/gba/maps/johto_art_v2_runtime.c`. Build identity, import checks,
allocation and runtime observations are recorded under `evidence/`. The known
linker RWX-segment warning remains; this is an art preview, not a release build.

`tools/vendor/gba/Johto-art-v2-preview.zip` contains the new ROM, a matching
ordinary development save and instructions. Continue starts at the pier. The
old `Johto-art-preview.zip` remains available for comparison. Production
mechanics and deferred save architecture were not changed.

## Reproduce

The isolated checkout is `tools/vendor/gba/johto-art-v2-game`, based on town
snapshot `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. Preserve the old v1 checkout
and patch. This revision's patch is `gba/johto-art-v2.patch`, applied directly to
the same town baseline; do not stack it on the v1 art patch.

```sh
python3 tools/gba/maps/compile_johto_art_v2.py
# On a clean, isolated town-baseline checkout with the qualified tools present:
python3 tools/gba/maps/install_johto_art_v2.py tools/vendor/gba/johto-art-v2-game
gmake -C tools/vendor/gba/johto-art-v2-game -j8 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
python3 tools/gba/maps/validate_cherrygrove.py tools/vendor/gba/johto-art-v2-game
python3 tools/gba/maps/check_cherrygrove.py tools/vendor/gba/johto-art-v2-game tools/vendor/gba/johto-art-v2-new-run --toolchain tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi
```

The compiler uses Python, Pillow and NumPy. A fresh local snapshot clone omits
the ignored `tools/compresSmol` dependency; use the already qualified copy from
`tools/vendor/gba/johto-art-game/tools/compresSmol` before building. Production
`game/` is not the destination for this isolated preview patch.
