# Cherrygrove B / C / E synthesis

Native GBA review proposal for the owner's October 10 selection. This resolves the
previous question about which Cherrygrove reference to use. The accepted New Bark
laboratory remains unchanged in `johto-native-refinement`.

## Review

- [Native whole map](evidence/CherrygroveCity.png)
- [Actual in-game views](evidence/in-game-review.png)
- [Shore, pond, trees and house close-ups](evidence/detail-review.png)
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

## Evidence

`evidence/build.json` binds the final ROM hash to fresh libmGBA tests. All seven
building entry/return pairs, bedroom stairs, both route round trips, pier/island
walking, water/forest barriers, ordinary 128 KiB save, cold reload and title-menu
Continue pass. `collision-runtime.jsonl` records all 372 passing focused movement probes.
Warp cells are excluded from obstacle probes because their existing travel
scripts execute before an attempted step; travel is checked separately.

`collision-changes.json` verifies that previously clear NPC movement cells remain
clear and that terrain collision changes stay inside the new architecture and authored tree footprints.
`boundary-structure.json` and `surf-structure.json` verify connected routes and
covered camera edges on foot and while surfing.

`integration.json` records 850/1008 scenery tiles (16 additional slots reserved
for doors), 464 metatiles, local palette seam corrections and an
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
```

Build with the documented ARM GNU 14.2 toolchain and `gmake`, then run
`verify.py OUTPUT_DIRECTORY TOOLCHAIN_DIRECTORY` with a fresh output directory.
The verification script needs local libmGBA headers/library. It also captures
the four targeted views through `review_details.py` and `detail_views.c`.
After preserving the patch, `check_source.py` compares all 284 source files with
the reproduced private engine and checks changes against the preceding committed
source manifest. The private playable
package is `tools/vendor/gba/Cherrygrove-synthesis-preview/Cherrygrove.gba` plus its
matching `.sav`; choose Continue. ROMs and saves are excluded from Git.

Pokémon/HGSS source art belongs to Game Freak/Nintendo/Creatures. The E harbor
uses the previously generated boats, island and native scenery with provenance
in `gba/art/johto-restart/`. No new character or story canon was authored here.
