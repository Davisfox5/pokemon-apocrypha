# HGSS New Bark and Route 31 recreation

October 8, 2026. Replaces the invented exterior geometry of the separate `johto-connections` campus preview with a native-scale HGSS-based recreation. Claude's Route 29 and Route 30 are retained, not regenerated. This isolated workbench does not overwrite an owner's Porymap project.

## Maps for review

- [Claude's Route 29](../claude-routes/route29-overview.png), [Claude's Route 30](../claude-routes/route30-overview.png).
- [New Bark](new_bark-overview.png): HGSS four-building arrangement, original model silhouettes, central paths, south homes, eastern water edge. A six-cell western approach keeps buildings outside the already-full shared primary tileset's connection window.
- [Route 31](route31-overview.png): HGSS pond, west gate, two grass terraces, eastern corridor, wood bridge and Dark Cave frontage. One extra southern row connects to the preserved Route 30 stairs.

These are decoded native tiles and map cells, not concept images. This first recreation still simplifies Route 31's cliff terraces, omits wind turbines/mailboxes, keeps the upper-right New Bark house closed, and uses the previous Violet entrance court and provisional interiors. Full Violet City and full Dark Cave are not included. HGSS is the reference baseline; the expanded Apocrypha research campus remains in the separate earlier proposal for later adaptation.

## Existing Porymap work examined

- `../claude-cherrygrove/`: accepted HGSS-in-2D native-scale cutouts, door alignment, material profiles, palette banks and the recorded Porymap 6.3.1 save round trip.
- `../johto-restart/`: preserves the owner's saved layout and artwork; small local edits replace destructive regeneration. Existing saved cells are not replaced here.
- `../floccesy-polish/`: retained architecture, reusable native modules, hidden-layer factoring and decoded-map verification.
- `../cherrygrove-detail-sample-v1/`: documents the rejected generic-texture conversion. This revision uses source silhouettes rather than that approximation.

## Source and strategy

`tools/gba/maps/hgss_connections/build.py` uses the same `claude_cherrygrove` palette/canvas compiler and `claude_routes` cell plans, cutout routines, tile reuse and connected-camera analysis. HGSS render geometry is recreated on a 16px movement grid; building crops stay at native scale and doors align to their cells. Palette banks hold at most 15 opaque colors, with no dithering. Route 31's grass is indexed into Route 30's existing palette; seam metatiles keep identical IDs, pixels and behavior in both maps. Existing tiles, route scripts, encounters, flags and Cherrygrove cells are preserved.

Output is standard Emerald `map.json`, layout/border `map.bin`, indexed `tiles.png`, metatiles/attributes and JASC palettes, in `gba/hgss-connections.patch`. A new Porymap GUI save round trip has **not** been performed here; the earlier Cherrygrove round trip is historical evidence only.

## References and reproduction

References downloaded from Bulbagarden Archives, native renders of Game Freak / Nintendo / Creatures artwork:

- https://archives.bulbagarden.net/media/upload/d/dd/New_Bark_Town_HGSS.png
- https://archives.bulbagarden.net/media/upload/d/d8/Johto_Route_31_HGSS.png

SHA-256 hashes and measured tile budgets are in `build-report.json`. Apply the existing Claude town/routes patches to the portable GBA workbench, then run the new generator against that fresh baseline; it refuses to overwrite existing New Bark maps. Build with the established GBA toolchain. `validate.py` checks reachability and connected camera windows; `runtime.py` exercises actual mGBA input, doors, barriers, ordinary flash save, cold load and title Continue; `preserve.py` asserts old-map preservation and records the source patch and review package.

## Verified review build

Structure checks pass: three New Bark doors and both Route 31 doors reachable; 48 New Bark / 126 Route 31 seam metatiles identical in pixels and behavior across both connected tilesets. Native mGBA write/read/menu phases pass: bidirectional route crossings, institute and both homes, bridge to Violet gate, cave enter/return, one-way ledge, water barrier, signs, ordinary flash save, cold reload and title Continue. Old Claude town/routes layouts, events, encounters, flags and referenced artwork remain unchanged. Source patch reverses cleanly, and 97 source files match a fresh generator run. See `evidence/` for recorded checks and native captures.

Playable package: `/workspace/library-files/Apocrypha-HGSS-connections-preview.zip`. Matching ROM/save; select Continue in New Bark. ARM GCC 14.2.1 and libmGBA 0.10.5. No new Porymap GUI round trip was run.
