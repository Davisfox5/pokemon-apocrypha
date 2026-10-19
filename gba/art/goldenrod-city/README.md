# Goldenrod City — HGSS-based native exterior

Goldenrod’s streets, waterfront and landmarks are built in editable Gen 3 native
source on engine `codex/goldenrod-city`, commit
`fdaf387b1ef1b0704e4f6a2f4ac0c24444d900a7`.
[Engine draft PR #20](https://github.com/Davisfox5/pokeemerald-expansion/pull/20).
This area starts from pending Azalea source `d822306675e15abe67c85235d9faf8d6e676d449`;
previous maps, artwork, map/layout ID prefixes and persistent data are preserved.
Owner accepted the first pass and building/tree refinement. The requested Radio Tower and Center placement fixes are now ready for review.

[**Latest: Radio equipment and Center before/after**](evidence/center-radio/README.md).

[**Building-by-building refinement and southeast before/after**](evidence/refinement/README.md).

## Look at the map

- [Whole native map](evidence/native-map.png), [2×](evidence/native-map-2x.png)
- [Registered HGSS/native comparison](evidence/reference-comparison.png)
- [Actual gameplay gallery](evidence/gameplay-gallery.png)
- Walking clips: [avenue seam](evidence/avenue-seam-walk.gif), [railway underpass](evidence/railway-underpass-walk.gif), [southern arch](evidence/southern-arch-walk.gif)
- [Radio Tower waterfront](evidence/Radio-plaza-comparison.png)
- [Magnet station and railway underpass](evidence/station-and-underpass-comparison.png)
- [Gym square and northern buildings](evidence/Gym-square-comparison.png)
- [Center and Game Corner](evidence/Center-and-Game-Corner-comparison.png)
- [Department Store and Bike Shop](evidence/department-and-bike-comparison.png)
- [Southern blocks](evidence/southern-blocks-comparison.png)
- [Numbered reference](evidence/reference-grid.png), [native grid](evidence/native-grid.png)
- [Material/traversal ledger](evidence/cell-ledger.csv), [collision view](evidence/collision-review.png)

## Geography, materials and native adaptation

The original reference is
[Goldenrod City HGSS](https://archives.bulbagarden.net/media/upload/6/65/Goldenrod_City_HGSS.png),
1330×885 pixels. Source `(0,0)` registers to native `(0,0)`, without shrinking the
city. Fourteen pixels of right padding and eleven of bottom padding finish the
84×56 native metatile grid. Original image/hash, foreground/background planes,
structure bounds, editable collision/material/layer arrays and canonical masters
are retained under `source/`.

The Radio Tower peninsula and fountains, waterfront avenue, station annex and
curved station canopy, elevated railway and street beneath it, northern plaza,
Gym, Flower Shop, Name Rater building, Game Corner, Department Store, Bike Shop,
Underground entrances, residential blocks and southern arch follow the original
arrangement. The northern picket fence, closed gate footprint, seawalls, exposed
cliff and arch pillars retain their barrier roles. Gameplay exercises the long
avenues and the viaduct/arch in both directions.

Materials remain distinct: water/shore, lawn, stone roadway, gold paving, wood,
stone facades, violet glazing, gold roof texture, orange paint/red trim, foliage,
and foreground architecture. Native 8×8 quadrants preserve the original texture
patterns with curated 15-color RGB5 families. Repeated highrises and residences
use coherent ramps instead of independent palette choices that produced vent
and window seams. No nearest-metatile substitution discards a silhouette.

The approved 80×80 Violet Center and complete 32×48 shared trees are reused.
The Center’s pad is restored and its native origin is `(792,576)`, fitted between the restored western building and lamp.
Its doorway approach remains `(52,41)`; the building silhouette and local ground are
independent, with no rectangular pavement patch attached. Forty-nine shared trees
have complete masters and distinct 2×2 root footprints. Their original forest
zones are adapted to these full footprints; clipped overview foliage, residual
trunks/shadows and the roof spire touching the cleanup were reviewed separately.
See [the cleanup comparison](evidence/north-cleanup-before-after.png) and
[the final forest/roof join](evidence/northern-forest-joins-comparison.png).

The city is twelve connected ordinary Porymap sections, listed in
[evidence/sections.json](evidence/sections.json). A Goldenrod-only glyph cache
keeps their camera views continuous while preserving detailed native artwork.
It reads an atlas generated **from the actual native source**, not an alternate
screenshot layout. Thirteen coherent BG palette banks, a maximum of 926 glyphs
in any 16×16 buffered view, and 1,008 available slots fit the hardware budget.
The top sixteen slots remain reserved. The roughly 25 KB allocation is volatile;
it is released outside Goldenrod and invalidated on heap reset.

Directional camera margins reuse native ocean, complete conifers/lawn, cliff,
street and paving cores. These are decorative extensions beyond the cropped
reference, not new traversable routes or recovered original terrain. Capacity
and captured-background checks include these margins. The southern stone cap is
on the upper layer, with transparent road beneath it and solid visible pillars:
[before/after gameplay](evidence/arch-before-after.png).

This is an overview-based reconstruction. Hidden ground and projected building
heights are interpreted; no extracted DS collision or z data is claimed. Every
native cell’s actual art/layer/collision is checked, but there is no invented
exact original-game categorical match score. Approved prefab footprints, forest
completion, padding and camera margins are explicit adaptations.

## Checks and reproducible source

- Arm GNU 14.2.1 native ROM build passes. [Build identity](evidence/build.json).
- Actual Porymap 6.3.1 exports equal all 4,704 decoded native cells.
- Native collision/layer arrays, complete root footprints, shared Center pixels
  and connected landmark approaches pass. [Review](evidence/review.json).
- Movement, closed entrances, seawalls, cliff, original pickets, northern gate,
  arch pillars, internal crossings and return travel pass in headless mGBA.
- Ordinary flash save, fresh-process reload and title Continue pass.
  [Runtime phases](evidence/runtime.json).
- All 78 audited BG views match the decoded native source and directional
  margins across 2,995,200 pixels, with zero RGB errors and cache overflows.
  [Actual VRAM/palette/scroll comparison](evidence/gameplay-background-parity.json).
- Native atlas regeneration is byte-exact; the direct arch and boundary edits
  reproduce from their named immutable baselines. A fresh checkout verifies all
  525 source files, including the repository’s CRLF palette rule. Stale native
  edits are rejected at build time. See the reproduction, fresh-checkout,
  source-manifest and preservation JSON files in `evidence/`.

GitHub Actions is disabled in the engine repository. A workflow dispatch was
rejected with HTTP 422; this is recorded in [hosted-ci.json](evidence/hosted-ci.json).
Local checks pass; the PR remains draft rather than claiming green hosted CI.

Open the engine branch directly in Porymap. Build with the shared-source
instructions (`make tools`, serial `make -j1 generated`, then `make -j8`).
After future native edits, regenerate only the adapter:

```
python3 tools/gba/maps/goldenrod_city/stream.py /path/to/engine
```

That tool never writes a native layout or tileset. Build-time source hashes
prevent a Porymap edit from silently leaving the runtime atlas stale. Preserve
coherent palette banks across sections.

`author.py` and `register.py` record first authoring; **do not replay them over
committed maps**. The newest `finish.py` correction expects `bb54d528` and is recorded in `evidence/center-radio/`. The one-shot `refine.py` building/tree cleanup expects `f439df15` and reads immutable first-pass metadata; never replay it over later edits. Its native/atlas reproduction is recorded in `evidence/refinement/`. The direct `arch.py` repair expects `200ffd16`; `borders.py`
expects `fed2667c`. Their guards preserve later native edits. The runtime renderer
is hand-authored engine C. `review.py`, the actual Porymap exporter, `runtime.py`,
`verify_frames.py` and `publish.py` retain the inspection/qualification workflow.
Tool versions and exact source/ROM hashes are recorded. No ROM, save or tool
executable is committed.

## Remaining scope

This is the exterior for visual review. Building interiors, train travel,
Game Corner activities, shop services, adjacent routes and campaign actors are
not wired. Entrances and outside connections remain closed. Water and fountains
are static; current water is a closed shoreline barrier, not a tested Surf area.
Stock city music is reused. No original player save was supplied or modified;
current-build ordinary persistence is verified, without a prior-save claim.

Original geography and game artwork: Game Freak / Nintendo / Creatures.
Canonical shared asset origins, immutable source URLs and hashes are in
[source/shared-provenance.json](source/shared-provenance.json).
