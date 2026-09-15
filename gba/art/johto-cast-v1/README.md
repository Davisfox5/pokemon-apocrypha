# Gold, Silver and Kestra in Cherrygrove

Owner request, 2026-09-13: clean up the custom Gold and Silver sprites and place
them with Kestra and the existing Cherrygrove residents for visual review.

- [Actual in-game walking](evidence/walking.gif),
  [native screenshot](evidence/residents-native.png), and
  [interaction captures](evidence/interactions.png).
- [Playable preview](../../../tools/vendor/gba/Cherrygrove-cast-preview.zip).
  Use its matching ordinary save and choose **Continue** to start beside the
  group at (50,13). Gold is southwest of the boy, Silver is southeast of the
  blossom tree, and Kestra is east of the girl. A shows each character's name.
- [Native cleanup comparison](evidence/cleanup-comparison.png) and
  [all imported directions](evidence/imported-directions.png).

## Artwork

Gold comes from the owner's [recovered Aseprite sheet](../../../assets/src/trainers/recovered-gold/README.md).
Silver and Kestra use the existing custom overworld sheets in
`assets/src/trainers/overworld/`. All originals are preserved. Gold's south cap
crown shading is consolidated, and its two walking poses now share the same
cap shape with the original bob/sway. Silver's lower coat/trousers lose residual
teen-Silver red/purple pixels; his red hair and crimson mantle remain. Kestra's
design is unchanged. These edits cover the overworld walking cells; battle art
and Gold's unused action cells are untouched.

`tools/artwork_library/clean_johto_cast.lua` performs the native Aseprite repairs:
93 indexed-pixel changes for Gold, 130 for Silver, zero for Kestra. It applies a
fixed one-pixel vertical anchor and nearest RGB555 palette conversion. There is
no spatial resizing. Prepared PNGs and editable Aseprite files are in `prepared/`;
engine-indexed PNGs, palettes and 4bpp data are in `native/`.

An imagegen cleanup comparison was generated from the originals and preserved at
`references/generated-cleanup-reference.png`. It is a visual reference only.
The ROM uses the repaired native custom pixels, not a reduction of that image.
Source hashes and cleanup details are in [cleanup.json](evidence/cleanup.json).
These remain owner-customized Pokémon-derived assets, not an original ownership
claim over the underlying Game Freak / Nintendo / Creatures designs.

Gold's twelve imported source cells are `0,1,2,3,4,5,6,7,8,11,12,13`, read across
the recovered six-column grid. Silver/Kestra use their twelve horizontal cells.
All are assembled into the qualified NPC order: north idle 0, west 1–3, east
4–6, north steps 7–8, south 9–11. East frames remain independently drawn.

## Integration and verification

The [manifest](import.json) gives Gold/Silver/Kestra stable graphics IDs
1029–1031 and separate palette tags. Gold and Silver walk small squares; Kestra
walks east/west. The original five NPC imports remain. Placements and name-only
interactions are for this visual review; no campaign scenes or trainer teams
are added. The approved v3 geography and buildings remain unchanged.

Visual review caught a missing engine registration: `SetStepAnim` would update
direction without selecting the corresponding idle image for the custom tables.
Both the regional residents and new cast are now registered in `sStepAnimTables`.
The cast checker compares actual OBJ VRAM pixels with source frame cells, in
addition to observing directions, positions, collisions and palettes. It checks
south-facing idle pixels after normal A-button interactions with all three
characters and the existing boy, then confirms walking resumes. Instrumented
setup warps the player; NPC movement and conversations use ordinary engine logic.
The movement probe allows the preceding pose on the first sample of a direction
change because OBJ upload and direction updates are staggered; it must agree by
the next four-frame sample. Conversation checks allow no such stale pose.

The evidence pack records 1,440 frames with all six outdoor residents visible,
plus the town's doors, stairs, connections, shop, flash save, fresh-process reload
and normal title-menu Continue. Compiled graphics/palettes match the prepared
imports. Native motion and dialogue captures are visually inspected. See
[movement.json](evidence/movement.json),
[runtime-results.json](evidence/runtime-results.json), and
[build.json](evidence/build.json) for the final verification and artifact hashes.
The final build uses 19,703,012 linked ROM bytes (+19,312 over NPC v1); EWRAM and
IWRAM remain 226,736 and 28,392 bytes respectively. Re-importing the cast is
byte-identical for every patched engine file.

## Reproduction

The isolated checkout is `tools/vendor/gba/johto-cast-v1-game`, on town baseline
`f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. Apply these patches in order:
`gba/johto-art-v3.patch`, `gba/johto-npc-v1.patch`, then
[gba/johto-cast-v1.patch](../../johto-cast-v1.patch). Forward/reverse patch checks
pass. Production `game/` and earlier preview builds remain separate.

To regenerate the cast above v3 + NPC v1, run the Aseprite Lua script with
`--script-param root="$PWD"`, then `python3 tools/gba/maps/import_johto_cast.py
tools/vendor/gba/johto-cast-v1-game`. Build with the qualified ARM toolchain and
the existing `compresSmol` dependency, as documented for v3.

Run `tools/gba/maps/check_cherrygrove.py` with
`--runtime-source tools/gba/maps/cherrygrove_npc_runtime.c` and a fresh output
directory. Run `tools/gba/maps/check_johto_cast.py` with the cast checkout,
gallery output path, and the same `--toolchain` argument. ROMs, saves and emulator
binaries remain under the ignored `tools/vendor/gba/` directory.
