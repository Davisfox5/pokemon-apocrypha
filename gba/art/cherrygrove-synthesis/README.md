# Cherrygrove B / C / E synthesis

Native GBA review proposal for the owner's October 10 selection. This resolves the
previous question about which Cherrygrove reference to use. The accepted New Bark
laboratory remains unchanged in `johto-native-refinement`.

## Review

- [Latest Center, dock and collision screenshots](evidence/door-dock-collision-review.png)
- [Centered Center door animation](evidence/center-door.gif)
- [Native whole map](evidence/CherrygroveCity.png)
- [Actual in-game views](evidence/in-game-review.png)
- [Shore, pond, trees and house close-ups](evidence/detail-review.png)
- [Tree contour before/after](evidence/tree-contour-review.png)
- [HGSS source versus native terrain tiles](evidence/terrain-source-check.png)
- [Animated harbor](evidence/harbor-water.gif)
- [Player house entrance](evidence/player-door.gif)

This is an isolated Cherrygrove preview. The original owner workbench, existing
ROM/save, main checkout, production `game/`, and accepted laboratory are preserved.
It retains E's existing interiors and preview residents/travel links. It does not
claim new campaign integration, sailing, or a functioning shipyard business.

## The synthesis

| Reference | Incorporated elements |
| --- | --- |
| B — `207615f` | Saved indexed HGSS houses, gable roofs, red/teal roof variants, Center, Mart and separate sign, whole green/pink trees; water texture and pale shoreline treatment. |
| C — `dc32b88` | Bright grass/path palette and two-course rock face, fitted to E's cliff height with a clean toe and landward taper. |
| E — latest owner workbench | 80×48 layout, all seven active door cells, event/warp IDs, route corridors, coast shape, pond, docks, island, three vessels and neighborhood arrangement. |

The player's house uses a mirrored B facade to retain an existing NPC's walking
lane. The Center's transparent padding is shifted to align its glass entrance to
the original warp cell and leave the pond visible. The neighboring home's new
footprint replaces a conflicting fence section. Collision edits are confined to
building/sign footprints and the explicitly recorded new tree footprints. Door
anchors, harbor access, route corridors and previously clear NPC movement cells
are preserved.

Both approach maps use the same trees and terrain. Pink trees are scattered beside the
shops, player home, southern homes and forest edges. Trees now use a complete crop from the HGSS map, including its actual short
trunk and shadow, fitted to the existing 32×48 asset. Pink foliage retains B's
colour treatment; its trunk and shadow use the same colours as the green tree.
The southeast grove uses a consistent 32px lattice to close the missing section.
No new raster generation was used for this synthesis.

## October 10 detail revision

`refine.py` traces complete building silhouettes against the original HGSS render,
recovering side walls and eaves removed by the earlier rectangular background
cuts. `refined/` contains the resulting indexed assets. House, Center and Mart
entrances retain their existing map anchors; door animation frames are regenerated
from the revised facades. The original B/C/E reference bundles remain immutable.

## Correction after rejection of invented trunks and textures

The owner rejected the procedural trunks and ground motifs in `9cc4857`.
Those implementations are removed. `references/HGSS-direct/` preserves the actual
source crops plus reference hash, exact crop rectangles and conversion details:

- Tree: HGSS Cherrygrove render rectangle `(624,46)-(664,94)`, including the
  rendered model's short trunk and shadow. The DS canopy texture alone lacks that
  geometry. Alpha is outlined around the foreground tree; nearest-neighbour
  horizontal fitting makes it 32px wide without extending its trunk.
- Grass: `(472,116)-(504,148)`, repeated as the original 32×32 lawn patch.
- Dirt path: `(568,52)-(600,84)`, repeated as the original 32×32 path patch.
- Sand: `(408,148)-(424,164)`, repeated as the original 16×16 beach patch.

Ground pixels are assigned to the existing C GBA palette. There are no generated
blade, dot or ripple patterns. Existing shoreline geometry, pond bank, water
animation, buildings, cliff, events and collision remain unchanged by this
correction. Ground hidden beneath scenery shares complete texture tiles to fit
native limits without flattening the visible textures.

`detail-preservation.json` records source hashes, changed paths and the exact
previous revision used for scope comparison.

## October 11 canopy and terrain borders

The upper-right canopy mask was too narrow. The missing shoulder now uses matching
pixels reflected from the intact left shoulder of the same HGSS tree. This adds
42 native opaque pixels; every previous opaque pixel and all trunk/lower-canopy
pixels are unchanged. Both foliage colours share the repaired silhouette.

Grass/path, grass/sand and water/sand joins now use actual HGSS transition strips
(their rectangles and sampling are recorded in `references/HGSS-direct/provenance.json`).
Path coverage follows native 16px cells, with rounded joins; shore edges follow
the preserved water boundary. Native 8px edge modules reuse matching material
silhouettes, permitting at most one-pixel contour corrections. The source grain
inside grass, dirt and sand blocks is preserved.

`check_terrain_sources.py` recovers the grass/path/sand pixels from the installed
GBA atlas and verifies exact agreement with the HGSS crops after palette conversion.
The side-by-side source review is linked above. The native decoder also verifies
every final map pixel, including the authored edge-module reuse and palette seams.
Scipy 1.13.1 supplies distance transforms for border placement; Pillow and NumPy
remain the existing image/array dependencies.

Collision data, event/warp coordinates and the accepted New Bark lab remain
unchanged. Ground tiles hidden by foreground objects now reuse matching complete
atlas tiles; this preserves visible pixels while keeping the richer borders within
native capacity. Six scenery tile slots remain free; 16 separate slots are reserved
for door animation.

## Center, dock and building-footprint revision (latest)

The Center's original glass doorway and its animation rectangle were offset.
The complete HGSS facade is now translated six pixels within a 112x96 native
canvas; the glass leaf is fitted to 16 pixels, centered at x56 in the unchanged
entrance cell. The door animation covers that glass rectangle only, including
its actual ten-pixel height. The sign, closed glass, player and opening align.
The exterior warp remains `(61,9)` with the same ID and destination.

The two-cell strip at `(38..39,18..19)` now uses the same literal HGSS dirt as
the path, continuing directly to the wooden dock. This material override does
not change coast geometry, water flags, dock collision or the adjacent beach.

Building collisions now use explicit wall rectangles in `integration.json`,
independent of the projected roof silhouettes. One rear row and narrow side
eaves can be walked beneath; their scenery is on the native top background
layer so roofs correctly cover the lower part of a sprite. Walls and doors
retain their physical blocking/warp roles. A deeper first version hid the whole
player and was corrected before this review. Tree barriers remain solid.
This implements the stated classic-overlap interpretation of the owner's request.

`building-collision-runtime.json` records 21 actual approaches from behind,
beside and in front of the seven buildings. See `building-collision-review.png`
for every captured position and `door-dock-collision-review.png` for the focused
review. The fresh build passes 3,256 position-specific collision checks, 49 exact travel
cases, 481 focused land/surf probes, ordinary save/Continue and water-animation
protection. The map has 926 connected walking cells; door anchors, all event records,
other town content and the accepted New Bark lab are unchanged in this revision.

## October 11 access and collision audit

The owner accepted the current artwork and requested a mechanics audit. Three
corrections preserve that artwork and the visible door anchors:

- Reapply final tree collision after clearing old building footprints. This fixes
  three walkable tree cells at `(45,14)`, `(45,15)`, `(45,16)` beside the player's house.
- Move the Unova preview resident from `(62,29)` to `(61,29)`, keeping its entire
  three-cell stroll in the lane rather than against the garden house wall.
- Redirect both exits of the unused transplant interior to the harbor-house
  landing. Its old return point was inside the forest. The dormant outdoor warp
  slot 3 remains blocked and has no door behavior; retaining it preserves all
  existing warp IDs. The unused interior and its contents are preserved.

`events.py` applies only these reviewed event changes to the immutable E snapshot.
The supplemental transplant-room snapshot matches the pinned engine baseline.
`check_access.py` checks every reachable outdoor cell, all visible door behavior,
NPC walking ranges, reciprocal active links and clear destinations. Every visible
entrance remains reachable even with all NPC movement ranges treated as occupied.
It checks that no reachable cell contains a substantial tree silhouette.

See [collision overlay](evidence/collision-overlay.png): red is solid, blue is
water, green is reachable land, and yellow outlines the seven doors. The map has
875 connected walking cells across the town and its two approach maps. The three
removed cells were the erroneous tree penetration; no path or door was relocated.

All 3,056 position-specific movement checks and 49 exact travel cases pass.
Expanded background-emulator evidence is in `access-runtime.json`,
`access-collision.jsonl`, and `access-travel.jsonl`. The directed collision sweep
covers every non-NPC, non-warp walking edge in that connected area; dynamic NPC
ranges are checked structurally and excluded from deterministic obstacle probes.
Water/surf variants remain covered by the separate focused probe suite. Travel
checks assert exact destinations and clear landings, both exit tiles in each
interior, expected door facing, bedroom/Center stairs, all three lanes across
each town connection in both directions, and all five onward preview links.
These are isolated map checks, not Chapter 1 scene or campaign qualification.

## Evidence

`evidence/build.json` binds the final ROM hash to fresh libmGBA tests. All seven
building entry/return pairs, bedroom stairs, both route round trips, pier/island
walking, water/forest barriers, ordinary 128 KiB save, cold reload and title-menu
Continue pass. `collision-runtime.jsonl` records all 481 passing focused movement probes.
Warp cells are excluded from obstacle probes because their existing travel
scripts execute before an attempted step; travel is checked separately.

`collision-changes.json` verifies that previously clear NPC movement cells remain
clear and that terrain collision changes stay inside the new architecture and authored tree footprints.
`boundary-structure.json` and `surf-structure.json` verify connected routes and
covered camera edges on foot and while surfing.

`integration.json` records 998/1008 scenery tiles (16 additional slots reserved
for doors), 596 metatiles, local palette seam corrections and an
exact decoded pixel roundtrip. Water is packed beneath opaque scenery so boat
silhouettes share animated background tiles. `water.json` verifies eight distinct
animation states over 512 frames and no overwrite of static terrain.

Porymap 6.3.1 opened and displayed the synthesis, and Save preserved the map and
event hashes. The final detail revision could not be
visually reloaded: the app exposed disabled File commands and returned no
screenshot. That editor refresh remains unverified; the final revised map
was decoded, inspected and tested in the background emulator. See `porymap.json`.
No desktop emulator was launched.

## Sources and reproduction

- `references/B`, `references/C`: pinned saved source bundles from the above Git revisions.
- `references/E`: immutable owner layout, palettes, metatiles and event snapshot.
- `references/HGSS-direct`: literal map crops and measured provenance for the replacement trees and terrain.
- `tools/gba/maps/cherrygrove_synthesis/`: compositor, facade door animations,
  structural checks, native acceptance and portable patch preservation.
- `gba/cherrygrove-synthesis.patch`: standalone engine source patch above
  `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. It also carries the owner's pre-existing
  isolated workbench content, including Sandgem/Floccesy, without changing it.
- `source-manifest.json`, `reproduction.json`, `preservation.json`, `patch.json`:
  source hashes, fresh checkout/generator comparison, scope preservation, and
  forward/reverse patch checks.

Apply the patch to a clean checkout at the pinned baseline. The local workbench is
`tools/vendor/gba/cherrygrove-synthesis-work`. The compositor and door script also
accept a different isolated engine directory as their first argument.

```sh
python3 tools/gba/maps/cherrygrove_synthesis/build.py
python3 tools/gba/maps/cherrygrove_synthesis/doors.py
python3 tools/gba/maps/cherrygrove_synthesis/check_structure.py
python3 tools/gba/maps/cherrygrove_synthesis/check_boundaries.py
python3 tools/gba/maps/cherrygrove_synthesis/check_access.py
```

Build with the documented ARM GNU 14.2 toolchain and `gmake`, then run
`verify.py OUTPUT_DIRECTORY TOOLCHAIN_DIRECTORY` with a fresh output directory.
Also run `verify_access.py OUTPUT_DIRECTORY TOOLCHAIN_DIRECTORY` for the expanded
position and travel audit. Run `verify_geometry.py OUTPUT_DIRECTORY TOOLCHAIN_DIRECTORY`
for the three wall approaches per building. These scripts need local libmGBA headers/library. It also captures
the four targeted views through `review_details.py` and `detail_views.c`.
After preserving the patch, `check_source.py` compares all 285 source files with
the reproduced private engine and checks changes against the preceding committed
source manifest. The private playable
package is `tools/vendor/gba/Cherrygrove-synthesis-preview/Cherrygrove.gba` plus its
matching `.sav`; choose Continue. ROMs and saves are excluded from Git.

Pokémon/HGSS source art belongs to Game Freak/Nintendo/Creatures. The E harbor
uses the previously generated boats, island and native scenery with provenance
in `gba/art/johto-restart/`. No new character or story canon was authored here.
