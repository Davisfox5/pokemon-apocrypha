# Route 32 — HGSS cell-grid correction

Engine branch `codex/route32-hgss-blocks`, commit `5627255b0ace34e80dc76e54c2caf06ce0d53d81`, [draft PR #8](https://github.com/Davisfox5/pokeemerald-expansion/pull/8). The exact validated engine commit is recorded in [build.json](evidence/build.json). This revises the accepted rock pass `fe8df8b`; visual acceptance remains with the owner.

## Review

- [Whole original HGSS/native map](evidence/comparison.png)
- [Source/native foot-grid comparison](evidence/source-grid-comparison.png), with [north](evidence/grid-comparison-1.png), [terraces and EW stairs](evidence/grid-comparison-2.png), [docks and fishing woods](evidence/grid-comparison-3.png), [Center/cave](evidence/grid-comparison-4.png)
- [Before/after](evidence/grid-revision-overview.png), [element details](evidence/detail-comparison.png), [native gameplay](evidence/grid-gameplay-gallery.png)
- Numbered original reference: [rows 0–24](evidence/hgss-numbered-grid-1.png), [25–49](evidence/hgss-numbered-grid-2.png), [50–74](evidence/hgss-numbered-grid-3.png), [75–99](evidence/hgss-numbered-grid-4.png), [100–124](evidence/hgss-numbered-grid-5.png)

## Corrections

The previous polygon/color-score pass left incorrect gaps and blocked parts of the original clearings. The placement authority is now a checked-in, reviewed **30×125 source-cell grid**, registered at native offset **+1,+1**. All 3,750 source squares are compared with collision decoded from the committed GBA layout/metatile attributes. This is an interpretation of the original HGSS overview and rooted terrain, **not extracted DS collision data**. It does not prove invisible original event gates or Surf rules.

`source/hgss-cell-grid.txt`, `hgss-tree-footprints.json`, `hgss-reference-blocked.npy` and `source-native-walkability.csv` expose the trace. Forests use explicit full-tree anchors with exclusive 2×2 roots, rather than greedy color-based packing. The western fishing stand, isolated trees and woods behind the Center now close the unintended passages. The boulder beside the cave has its own footprint and an open square below it; no tree root shares its square. Signs, the clipped gate base, dock arms, western rock edge and cave doorway are registered against the numbered source. Both cave warp cells move with the doorway to `(14,117)` and `(15,117)`.

The only declared foot-grid differences are **14 additional occupied squares belonging to the owner-selected wider Violet Center prefab**. Every square is listed in [grid-audit.json](evidence/grid-audit.json); there are no unexplained differences against the reviewed trace. One-way ledges remain distinct from ordinary blocked floor and are tested directionally.

The dock uses a clean, unoccupied HGSS wood-core sample, reduced to native colors with continuous panel joins. Grain changes direction on the transverse fishing arm/bend. Framing, perimeter shading and corrected deck courses replace the old repeated horizontal bands. Padding continues the marine terrain instead of adding a lawn strip at the right edge.

The EW placeholder uses **Emerald General tread pixels**, assembled along the original staggered flight, rather than rotating the complete rectangular NS staircase. Two adjacent rock corners are blocked. `source/stair-placements.json` lists both named assemblies, their landings and blocked corners for later replacement. The accepted NS asset is byte-for-byte unchanged from `fe8df8b`. Custom HGSS stair art remains deferred.

Accepted Cherrygrove ground, tree and rock colors/textures are preserved. A **Route 32-only primary tileset** retains all referenced Cherrygrove glyphs and animation slots, using unreferenced static slots for the extra local corner/panel pieces. Its unused catalogue entries are blanked. Shared Cherrygrove source, other maps' tiles/metatiles, map IDs and owner saves are unchanged. Secondary static glyphs end below the door-animation scratch area. The original `7bae845` and `fe8df8b` drafts remain in history and explicit evidence snapshots.

## Validation

Local ROM build passes. Actual Porymap 6.3.1 project-core export matches the decoded map with zero pixel differences. Foreground native RGB/mask checks pass. Standalone Porytiles compilation validates 128 local art metatiles with zero native RGB/alpha errors.

The headless mGBA tour checks both walking branches and railway underpasses, both directions of each stair flight, fixed reference-based forest/stair/boulder barriers, the restored floor below the boulder, grass, a one-way ledge, Center entry/return and both cave warp cells. Fresh 128 KiB ordinary flash, cold reload and normal title Continue pass. A **copy** of the preceding `fe8df8b` proof save also reloads/continues; that source save is untouched. These checks cover the isolated Route 32 proof saves, not unspecified campaign saves. Evidence records the source commit and ROM digest; ROMs, saves and tool executables are not committed. No desktop game was opened.

## Editing and reproduction

Edit the committed engine checkout directly in Porymap. Generators are provenance, not an editor to replay over owner changes. The manifest guard protects editable source (including Poryscript), ignores regenerated map headers/events/connections and refuses changed map/tileset files. The current refinement reads the source grid, not any prior native layout or marine plan.

For an isolated reconstruction from production base `2722eaf7601ec02dc5a684fa8cdef9206c0dc377`:

```sh
python3 tools/gba/maps/route32_hgss_blocks/build.py /path/to/engine
python3 tools/gba/maps/route32_hgss_blocks/register.py /path/to/engine
python3 tools/gba/maps/route32_hgss_blocks/trace_grid.py
python3 tools/gba/maps/route32_hgss_blocks/register_primary.py /path/to/engine
python3 tools/gba/maps/route32_hgss_blocks/refine.py /path/to/engine
make -C /path/to/engine -j1 generated
make -C /path/to/engine -j8
python3 tools/gba/maps/route32_hgss_blocks/review_grid.py /path/to/engine
python3 tools/gba/maps/route32_hgss_blocks/compile_assets.py /path/to/engine /path/to/porytiles-legacy
python3 tools/gba/maps/route32_hgss_blocks/runtime.py /path/to/engine /new/runtime-evidence --toolchain /path/to/arm-toolchain
python3 tools/gba/maps/route32_hgss_blocks/publish_review.py /path/to/engine /new/runtime-evidence /porymap-export-directory
```

The headless Porymap probe source is alongside those scripts. Source art: Nintendo, Game Freak, Creatures; HGSS overview hosted by Bulbagarden Archives. Existing reference/shared-asset hashes and original art remain preserved.

## Remaining scope

Violet City and an Alph destination still need external wiring. The native cave room is an entrance test room, not full Union Cave. Original trainers, encounters, items and story/event gates remain separate campaign work. The screenshot trace can be tightened further against decoded original DS collision if that data becomes available; the visible grid and explicit adaptations make that review possible.
