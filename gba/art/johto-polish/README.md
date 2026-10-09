# New Bark and Route 31: rebuild after visual rejection

October 9, 2026. The owner rejected both October 8 previews as below the Cherrygrove standard. This revision starts again from the HGSS references and Claude's preserved route baseline. Earlier previews, owner-edited layouts, production `game/`, and Claude's Route 29/30 cells are retained.

## Review

- [New Bark native map](new_bark-overview.png).
- [Route 31 native map](route31-overview.png).
- Editable, native-scale source silhouettes and palette-indexed modules: `native/`.
- Source: `tools/gba/maps/johto_polish/art.py` and `build.py`; engine changes: `gba/johto-polish.patch`.

## What was rebuilt

Buildings now use measured silhouette masks, not color-keying that erased teal roof pixels. Complete roofs, wall outlines, doors, windows and trim survive. Windmills, mailboxes and laboratory fencing are separate native assets. Windmill highlight colors are protected during palette reduction, and native roof textures are factored into reusable patterns without changing silhouettes, door frames or wall pixels. Every New Bark exterior door has its own return destination, including the previously closed upper-right house.

Forest pixels are retained beneath architecture. Two hardware layers preserve mixed tree/building palette edges rather than recoloring them or cutting rectangular holes out of the forest. The compiler verifies every opaque authored scenery pixel against the decoded native map; there is no additional loss from tile packing. Ground pixels in a mixed-palette quadrant are indexed into the building palette when a third layer would otherwise be required; the original material textures remain elsewhere.

Route 31 has three distinct cliff platforms with exposed vertical faces and corners, a dark cave mouth, the pond-bank cliff, one wooden bridge, the Apricorn tree and the HGSS grass terraces. A separate turquoise freshwater material replaces the inappropriate coastal sea texture in the pond. Shore modules contain no reference NPC pixels. The original shared coastal water animation remains on New Bark's east edge; the pond and windmill blades are currently static.

New Bark retains its HGSS four-building arrangement and eastern water, with a six-cell western approach outside the source town to protect Route 29's connected camera window. Route 31 retains the native 63-cell width and adds one southern row for Route 30. Full Violet City, full Dark Cave, native Johto interiors, trainers/encounters, the expanded institute design and campaign scenes remain outside this exterior revision. Current interiors are explicitly borrowed GBA layouts; Violet's previous arrival court is retained. No new story or persistent flags are added.

## Reference and native files

The source references are the Bulbagarden Archives renders already preserved in `../hgss-connections/references/`:

- https://archives.bulbagarden.net/media/upload/d/dd/New_Bark_Town_HGSS.png
- https://archives.bulbagarden.net/media/upload/d/d8/Johto_Route_31_HGSS.png

Original designs/art: Game Freak / Nintendo / Creatures. Source hashes and measured native capacity are in `build-report.json`. Ground, forest, sea, flowers and signs reuse the existing HGSS-in-2D Cherrygrove assets; Route 30's visible palette banks are retained exactly. Standard Emerald/Porymap map JSON, binary layouts, indexed tiles, metatiles, attributes and JASC palettes are produced. No Porymap GUI save round trip is claimed for this revision; the prior Cherrygrove editor evidence is historical.

## Reproduce

Use a fresh isolated workbench containing the refreshed Claude town/routes patches and tag its baseline `routes-baseline`. The generator refuses to overwrite an existing New Bark map.

```
python3 tools/gba/maps/johto_polish/build.py <workbench>
python3 tools/gba/maps/johto_polish/validate.py <workbench> --output <structure.json>
make -C <workbench> -j1 generated TOOLCHAIN=<ARM-toolchain>
make -C <workbench> -j8 TOOLCHAIN=<ARM-toolchain>
python3 tools/gba/maps/johto_polish/runtime.py <workbench> <checks> --toolchain <ARM-toolchain>
python3 tools/gba/maps/johto_polish/preserve.py <workbench> <checks>
```

`runtime.py` also accepts `--film-only` for native walking captures. `preserve.py` checks previous map layouts, scripts, events, referenced tiles/palettes, encounters, flags and the shared primary before preserving the source patch and review package.

Run the map-source generation step serially before parallel compilation: the upstream multi-output map rule can otherwise race while rewriting `heal_locations.json`. The build uses the untouched baseline healing data; no gameplay healing changes are part of this patch.

## Verified review package

[New Bark in-game](evidence/new-bark-in-game.png), [Route 31 in-game](evidence/route31-in-game.png), [native walking](evidence/new-bark-walk.gif), [ordinary save / Continue](evidence/save-continue.png), [HGSS/New Bark comparison](evidence/compare-new-bark.png), [HGSS/Route 31 comparison](evidence/compare-route31.png).

All four home/institute doors enter and return correctly. Bidirectional route connections, the bridge walk to Violet's gate, cave enter/return, ledge direction, water blocking and signs pass in mGBA. Separate emulator write/read/menu phases prove an ordinary 128KiB flash save, cold reload and title Continue. Native walking footage and the in-game captures were inspected. The packed map reproduces 470,354 authored scenery pixels in the two rebuilt maps with zero mismatches; 210 seam metatiles match between connected tilesets. These checks do not imply owner visual acceptance.

Playable package: `/workspace/library-files/Apocrypha-Johto-polish-preview.zip`. Load the matching ROM/save and choose Continue in New Bark. The source patch applies forward to the baseline, produces the tested source tree, and reverses cleanly. 99 source files match the fresh generator output (palette line endings normalized). Claude's old layouts, events, scripts, encounters, flags, referenced artwork and shared primary remain preserved.
