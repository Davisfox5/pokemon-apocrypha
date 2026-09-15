# Johto NPCs in Cherrygrove

Latest follow-up: [custom cast preview](../johto-cast-v1/README.md) adds Gold,
Silver and Kestra and fixes step/idle animation registration for these residents
as well. Its verification checks displayed sprite pixels, not only direction
state. The v1 evidence below is retained as the original pilot record.

Owner request, 2026-09-13: get Johto-specific NPC sprites onto the map and walking
around. This pilot imports existing HGSS artwork into the isolated revision 3
town. The buildings, scenery and geography retain their accepted v3 source.

- [Watch the residents walking](evidence/walking.gif): actual mGBA frames, 3×
  nearest-neighbor display scale. The player stays still while the engine moves
  the residents. No frame interpolation or synthetic character movement.
- [Native screenshot](evidence/residents-native.png),
  [imported directions](evidence/imported-directions.png), and
  [dialogue/shop captures](evidence/interactions.png).
- [Playable preview](../../../tools/vendor/gba/Johto-NPC-preview.zip): open the
  included ROM with its matching ordinary `.sav`, then choose **Continue**.
  You start beside the residents at (50,13), south of the Mart and Center.

## Installed characters

| Character | Placement and behavior | Source texture | Graphics ID |
|---|---|---|---|
| Boy | Walks east/west along the shopping lane | `0115_gsboy2.png` | 1024 |
| Girl | Walks north/south near the Center | `0117_gsgirl1.png` | 1025 |
| Man | Walks a small square beside the blossom tree | `0120_gsman1.png` | 1026 |
| Woman | Existing waterfront resident, existing dialogue | `0123_gswoman1.png` | 1027 |
| Clerk | Existing functioning Mart shopkeeper | `0132_shopm1_2.png` | 1028 |

The boy and girl have short proposed ambient lines. Existing scripts, local IDs
and flags for the other three actors are retained. This introduces no trainer
teams, story scenes or new roles for Gold, Silver or Kestra.

## Importer and provenance

`tools/gba/maps/import_johto_npcs.py` reads [import.json](import.json), converts the
five reviewed source strips, registers graphics/palettes/animation tables and
updates explicit map events. It is a bounded importer for the reviewed twelve
frame HGSS human profile, not an assumption that every sprite sheet shares that
layout. Each source has twelve 32×32 frames and at most fifteen opaque colors.
The original colors and visible pixels survive exactly. Palette index zero is
transparent; all frames receive the same +1px vertical anchor adjustment.
There is no resizing, per-frame recentering or generated replacement art.

Frame mapping: south 9/10/11, north 0/7/8, west 1/2/3, east 4/5/6. The shared
animation table retains the independently drawn east frames instead of applying
Emerald's mirrored west frames. Idle and all four standard walking speeds are
registered. The runtime pilot exercises ordinary walking and conversation idle.

Sources are existing Pokémon HeartGold/SoulSilver overworld textures in
`artwork-library/heartgold-johto/overworld-sprites`, by Game Freak / Nintendo /
Creatures. Extraction provenance is in `artwork-library/README.md` and
`tools/artwork_library/extract_hg_owsprites.py`. This is not an original ownership
claim. [Import evidence](evidence/import.json) records exact source hashes,
palette counts, frame bounds and conversion checks. The earlier
[feasibility study](../johto-npc-study/README.md) preserves the source inspection.

Johto graphics use a separate fixed range, 1024–1028, with dedicated palette tags
0x1180–0x1184. The existing graphics enum and dynamic-variable IDs are unchanged.
Compile-time assertions prevent overlap with dynamic/follower graphics. The
engine's normal object palette allocator handles simultaneous NPC colors.

## Reproduction

The dedicated checkout is `tools/vendor/gba/johto-npc-v1-game`, based on town
commit `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. Apply
[johto-art-v3.patch](../../johto-art-v3.patch) first, then
[johto-npc-v1.patch](../../johto-npc-v1.patch). The NPC patch contains only this
increment above v3, including the five graphics and palettes. Both forward and
reverse patch checks pass. Production `game/` remains separate.

To regenerate instead of applying the NPC patch, apply v3 to the dedicated
checkout and run the importer. Fresh clones also need the qualified ignored
`tools/compresSmol` dependency described in the [v3 handoff](../johto-v3/README.md).

```sh
python3 tools/gba/maps/import_johto_npcs.py tools/vendor/gba/johto-npc-v1-game
gmake -C tools/vendor/gba/johto-npc-v1-game -j8 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
python3 tools/gba/maps/validate_cherrygrove.py tools/vendor/gba/johto-npc-v1-game gba/maps/cherrygrove/town-v3.json
python3 tools/gba/maps/check_cherrygrove.py tools/vendor/gba/johto-npc-v1-game tools/vendor/gba/johto-npc-v1-run --toolchain tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi --runtime-source tools/gba/maps/cherrygrove_npc_runtime.c
python3 tools/gba/maps/check_johto_npcs.py tools/vendor/gba/johto-npc-v1-game tools/vendor/gba/johto-npc-v1-gallery --toolchain tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi
```

The town check requires a fresh output directory; the NPC evidence renderer uses
the qualified `johto-npc-v1-run` captures for its interaction contact sheet.
ROMs, emulator binaries and ordinary saves stay in the ignored vendor directory.

## Verified result

The ROM builds with 19,683,700 linked ROM bytes, an increase of 34,264 bytes over
v3. EWRAM remains 226,736 bytes and IWRAM 28,392 bytes. The existing tool-build
deprecation and linker RWX warnings remain; there were no build errors.

The three town acceptance phases pass: all six doors and returns, stairs, route
connections, pier collision, resident dialogue, shop interaction, 128 KiB flash
save, fresh-process load and ordinary title-menu Continue. See
[runtime-results.json](evidence/runtime-results.json).

The NPC recorder observes 1,440 engine frames without moving the player. All
three residents change positions on clear ground with distinct palettes. The
man uses all four directions; the other two use their assigned two directions.
All four animation commands occur across each route; a short one-tile leg may
turn before completing the entire cycle. An ordinary A-button interaction
stops the boy, turns him toward the player and resumes movement after dismissal.
See [movement.json](evidence/movement.json) and its raw trace. The probe reads
object/sprite state; it does not move NPCs or select their animation frames.

Native images and sampled movement frames were visually inspected for direction,
scale, transparent edges and anchor consistency. Compiled 4bpp and palette bytes
match all five lossless imports exactly. Structural checks still pass for all
eleven town maps. [build.json](evidence/build.json) records the ROM, patch and
package hashes; the packaged ROM and save were verified after compression.

More reviewed twelve-frame townspeople can use the same workflow. Additional
sheet formats, including the thirteen-frame Center staff strip, need their frame
layout classified before registration. This pilot does not qualify every NPC,
movement speed or special field effect in the source library.
