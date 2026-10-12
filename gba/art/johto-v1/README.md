# Johto environment samples, 2026-09-13

**Latest preview:** the owner preferred the generated house and Center to these
first native imports. [The revised import](../johto-v2/README.md) preserves their
proportions and more detail with an 80×80 grid and shared per-tile palettes. This
folder retains the original generated sources and first-pass evidence.

The owner requested actual Johto references and redesigned assets for Emerald-expansion, rather than recoloring Emerald scenery. This is a **visual proposal**, integrated into a separate playable Cherrygrove preview. It is not an approved complete regional tileset.

## References and design

[HeartGold/SoulSilver Cherrygrove City reference](https://archives.bulbagarden.net/wiki/File:Cherrygrove_City_HGSS.png), retrieved 2026-09-13 from Bulbagarden Archives. [Original image](https://archives.bulbagarden.net/media/upload/b/bb/Cherrygrove_City_HGSS.png) is preserved in `references/cherrygrove-hgss.png`, with three extracted detail crops. Reference artwork belongs to Game Freak / Nintendo / Creatures; Bulbagarden hosts it as game imagery, not as a permissively licensed asset pack. The new samples are adaptations of that recognizable game architecture, not unrelated original IP.

- **House:** asymmetrical clay-red roof, inset skylight, timber/plaster frontage and blue window. The reference silhouette survives the smaller GBA grid.
- **Pokémon Center:** broad orange roof with pale rim, projecting emblem canopy and teal entrance, reproducing the Johto building form.
- **Tree:** taller, tapered, overlapping olive-green canopy tiers, with cool undersides and a visible trunk.

Generation used the **built-in image_gen tool**. Final design prompts are in [prompts.json](prompts.json); transparency correction prompts are in [alpha-prompts.json](alpha-prompts.json). Selected generated sources are `generated/house-final.png`, `generated/center.png`, and `generated/tree-alpha.png`. Earlier house/tree files are intermediate outputs that failed transparency inspection. No DS asset format or engine code was imported.

## Deliverables

- [Reference / native asset comparison](comparison.png). Enlargements use nearest-neighbor scaling; native-size samples are also shown.
- [Actual emulator captures](evidence/runtime.png), [short movement capture](evidence/walk.gif), and [offline full-town render](evidence/town-overview.png).
- `native/`: indexed transparent PNG, JASC palette, RGB555 `.gbapal`, and row-major 8x8 `.4bpp` data for every object.
- [Native dimensions and counts](native/manifest.json), [integration allocation](evidence/integration.json), [build identity](evidence/build.json), [runtime observations](evidence/runtime-results.json), and [structural checks](evidence/structural.json).
- Engine source changes are preserved in `gba/johto-art-v1.patch`, applied after `gba/cherrygrove-town.patch` on the existing map-qualification baseline.
- Ignored playable package: `tools/vendor/gba/Johto-art-preview.zip`. It contains a ROM plus ordinary development save. Continue starts at the pier; walk north to Gold's house and onward to the Center.

| Sample | Native pixels | Opaque colors | Unique 8x8 tiles | Raw 4bpp bytes |
| --- | --- | --- | --- | --- |
| House | 80 x 64 | 15 | 78 | 2,560 |
| Center | 64 x 64 | 14 | 63 | 2,048 |
| Tree | 32 x 48 | 14 | 24 | 768 |

The importer samples generated pixels onto the target grid without dithering, thresholds alpha at 224 for index-zero transparency, and quantizes colors to RGB555. These are inspected, lossy GBA adaptations; the large model output alone is not tile-ready. A binary round-trip checks the 4bpp packing. Palettes occupy secondary banks 8, 10 and 6 respectively.

## Integration and validation

The isolated checkout is `tools/vendor/gba/johto-art-game`, based on town snapshot `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. The existing town source patch was applied to a temporary index at qualification snapshot `b01afeda981936736c0deb49376f8575e88ea533` and reproduced that baseline tree exactly. The new art patch passed both forward and reverse apply checks. Production `game/` and the previous Cherrygrove checkout were not edited.

Four houses, the Center and green town trees use the new art. The Center receives eight transparent pixels on each side in its metatile placement, moving its footprint one tile west so the doorway aligns with the existing warp at (33,8). The unpadded source remains 64 x 64. Existing door behaviors and all destination warps are retained. Door-frame animation art is not supplied in this sample pack; inherited custom-town door transitions still work without bespoke opening frames.

The build passes with **356 / 512 secondary tiles** and **221 / 512 secondary metatiles** used by the combined town tileset (tile sheet storage pads to 368 tiles). Linked ROM use is 19,649,444 bytes, EWRAM 226,736 bytes and IWRAM 28,392 bytes. This establishes capacity for these samples, not a budget for all five regions.

All three mGBA 0.10.5 runtime processes pass: six building entries/returns, player-home stairs, both route connections, pier collision, dialogue/shop interaction, ordinary 128 KiB flash saving, cold reload and normal title-menu Continue. Structural validation covers eleven maps and access to all six entrances. Native 240 x 160 screenshots and movement frames were inspected after integration.

## Reproduce

From the repository root, with the qualified toolchain installed:

```sh
python3 tools/gba/maps/compile_johto_art.py
# Supply a clean, separate checkout of the Cherrygrove town baseline:
python3 tools/gba/maps/install_johto_art.py tools/vendor/gba/johto-art-game
gmake -C tools/vendor/gba/johto-art-game -j8 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
python3 tools/gba/maps/validate_cherrygrove.py tools/vendor/gba/johto-art-game
python3 tools/gba/maps/check_cherrygrove.py tools/vendor/gba/johto-art-game tools/vendor/gba/johto-art-new-run --toolchain tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi
```

The installer refuses dirty checkouts and does not overwrite production or the original Cherrygrove preview. To reproduce already-integrated source, apply `gba/johto-art-v1.patch` to the town baseline instead of rerunning the installer. See `docs/CHERRYGROVE_GBA.md` for the preceding map/roster patch chain. The gallery harness is `tools/gba/maps/johto_art_runtime.c`, compiled against the same installed mGBA library and using the symbols emitted by the town checker.

## Remaining visual work

The Mart, pink blossom trees, terrain, waterfront objects, interiors and route-approach art remain from the earlier preview. House variants, a distinctive Gold-house treatment, roof pixel refinement, flowering Johto-tree variants and matching door animation frames remain proposals for the next art pass. No story, trainers, encounters, tutor distribution or production save architecture changed. Owner visual acceptance remains open.
