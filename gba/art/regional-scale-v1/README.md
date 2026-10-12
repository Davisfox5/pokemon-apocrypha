# Five-region character scale comparison

Owner request, 2026-09-13: reduce the large custom Johto characters toward the
Emerald player scale and add Hoenn, Sinnoh, Kanto, Johto and Unova characters.
This is an isolated visual-review proposal, not new campaign staging.

- [Playable ROM and matching ordinary save](../../../tools/vendor/gba/Cherrygrove-regional-scale-preview.zip).
  Extract both files together and choose **Continue** to start at (50,13).
- [Actual in-game movement](evidence/walking.gif),
  [labelled screenshot](evidence/overview.png), and
  [native 240×160 screenshot](evidence/residents-native.png).
- [Original versus proposed scale](evidence/scale-comparison.png), showing
  assembled source pixels above and the smaller versions below.

The walking row near the shops runs west to east: **Hoenn, Kanto, Johto, Sinnoh,
Unova**. A displays each region's name. Smaller custom Gold, Silver and Kestra
remain nearby. Earlier full-size Johto citizens remain around the area as
additional context. Buildings, map geography and the Hoenn player are unchanged.

## Artwork and scale

The five samples use Emerald Man 1, FireRed Youngster, HeartGold boy 2, Platinum
model 4, and the first walking trainer on Barubary's Black/White sheet. The
[provenance record](provenance.json) has source paths, hashes, donor revision,
frame mappings and extraction details. The Unova sheet was obtained from
[The Spriters Resource](https://www.spriters-resource.com/ds_dsi/pokemonblackwhite/asset/34109/).
Its embedded credit remains intact. These are Pokémon-derived assets, with
underlying designs belonging to Game Freak / Nintendo / Creatures; extraction
credit does not transfer those rights.

Gold/Silver/Kestra start from the approved cleaned custom sheets in cast v1.
`tools/artwork_library/prepare_regional_scale.lua` performs native Aseprite
assembly and selected row/column removal, with separate recipes for each asset.
The recipes preserve the face's eye pixels, coat/mantle colors and existing
silhouettes. Gold's south idle receives a two-pixel anchor correction. Original
files and the old playable preview remain intact. Prepared PNGs and editable
Aseprite copies live in `prepared/`; `sourceframes/` is canonical assembly before
reduction, and `native/` holds exact engine-indexed graphics and palettes.

| Sample | Original visible height | Proposed visible height |
| --- | --- | --- |
| Hoenn | 20 px | 20 px |
| Kanto | 18–19 px | 18–19 px |
| Johto | 23–26 px | 20–23 px |
| Sinnoh | 23–25 px | 20–22 px |
| Unova | 29–31 px | 22–24 px |
| Custom Gold | 21–24 px | 19–22 px |
| Custom Silver | 25–28 px | 20–23 px |
| Kestra | 26–28 px | 21–23 px |

These ranges cover all twelve walking cells. Brendan's walking artwork is
21 pixels tall. Hair, hats and walk poses retain modest differences. Hoenn and
Kanto keep their original visible pixels. DS samples have individual reductions;
this is not a runtime zoom or a blanket resize of all assets.

All imported cells are 32×32, transparent, with at most fifteen visible RGB555
colors. Frame order is the existing canonical twelve-frame profile. Gen 3 east
poses bake the source game's mirrored west poses into explicit cells; the DS and
custom assets retain independently drawn east poses. The existing registered
JohtoCast animation table handles movement and stop/turn behavior.

## Integration and evidence

Graphics IDs 1029–1031 retain the custom cast; five new IDs 1032–1036 append the
regional samples. Original enums, dynamic graphics and follower ranges are
unchanged. Each sample walks a small square. Regional labels are temporary review
text. The three older roaming citizens move outside the comparison row.

The build passed, using 19,734,420 linked ROM bytes, 226,736 EWRAM bytes and
28,392 IWRAM bytes. The file is padded to 32 MiB as before. See
[build.json](evidence/build.json) for ROM/package/patch hashes. Known inherited
PNG metadata and RWX linker warnings remain in the full build log; there were
no compile errors.

[Runtime evidence](evidence/movement.json) records 1,440 engine frames / 360
samples: all eight comparison actors move, use distinct palettes, stay on clear
collision tiles and display the source frames appropriate to their direction.
All five regional NPCs and Gold/Silver cover four directions; Kestra follows her
existing east/west route. Compiled graphics and palettes match all eight imports.
Ordinary A-button conversations with all eight verify stop, face-player south
idle pixels, and resumed walking. The observer compares actual OBJ VRAM, allowing
a preceding pose only on the first four-frame sample of a direction transition.
Native screenshots, movement captures and dialogue were visually inspected.

[Town acceptance](evidence/runtime-results.json) passes write, fresh-process read
and ordinary title-menu Continue, plus doors, stairs, routes and shop behavior.
The packaged 128 KiB save and ROM are verified byte-for-byte against the tested
artifacts. Importer reruns are byte-identical. Patch forward/reverse checks pass.
Production `game/` and earlier preview checkouts remain separate.

## Reproduce

Use town baseline `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e` in the isolated
`tools/vendor/gba/regional-scale-v1-game` checkout. Apply these patches in order:
`gba/johto-art-v3.patch`, `gba/johto-npc-v1.patch`, `gba/johto-cast-v1.patch`, then
[gba/regional-scale-v1.patch](../../regional-scale-v1.patch).

To regenerate above cast v1, run the Aseprite Lua script with
`--script-param root="$PWD"`, then `python3 tools/gba/maps/import_regional_scale.py
tools/vendor/gba/regional-scale-v1-game`. The source PNGs are preserved, so donor
extraction/download is not needed for regeneration. Build with the qualified
ARM 14.2 toolchain and compresSmol dependency from the previous preview.

Run `tools/gba/maps/check_regional_scale.py` with the isolated checkout, a gallery
output directory and `--toolchain`. Run `tools/gba/maps/check_cherrygrove.py` with
`--runtime-source tools/gba/maps/cherrygrove_npc_runtime.c` and a fresh output
directory. ROMs, saves and emulator binaries stay in ignored `tools/vendor/gba/`.
