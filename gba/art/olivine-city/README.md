# Olivine City — HGSS-based native exterior

First native exterior pass, following the owner-accepted
[Goldenrod playbook](../../../docs/GBA_CITY_BUILDING_PLAYBOOK.md).
Reference: [HGSS overview](https://archives.bulbagarden.net/media/upload/f/f6/Olivine_City_HGSS.png),
1035×858 pixels, registered at (0,0), 1:1 onto 65×54 native metatiles
(1040×864). Five right and six bottom pixels are explicit edge padding.
The final eight-pixel edge strips extend the last three source columns and two
source rows; the small overlap is recorded explicitly in registration evidence.
This is interpreted overview geography, not extracted DS collision/elevation.

![Actual decoded native city](evidence/native-map.png)

The Gym, café, three residences, lighthouse terrace/ramp, original promenade,
umbrella tables, sailboats, central pier and ferry terminal retain their HGSS
arrangement. Approved transparent Violet Center and shared Mart replace their
local service buildings without attached pavement. Broad forest interiors use
complete canonical trees with distinct root footprints. Tightly framed isolated
HGSS trees remain beside cliff pockets and use a compatible foliage palette.
There is no unapproved carnival or other large ten-year redesign in this pass.

## Native source and hardware

Source is in `Davisfox5/pokeemerald-expansion`, branch `codex/olivine-goldenrod-playbook-20261019`,
stacked on Goldenrod `eb63c24cb7e28c7de1eddd7db0b693a6510b29d4`.
Thirteen ordinary connected Porymap maps, `OlivineCity01`–`13`, append group80 IDs
63–75. Previous map/layout IDs and previous native city art remain unchanged.
Each section owns private native tiles/palettes/metatiles/map blocks. The Olivine
viewport adapter derives exclusively from those files; Porymap remains editable.

Thirteen global palette banks retain coherent water, paving, cliff/sand, lawn,
Gym wood/glass, residential architecture, harbor blue/cream stone, dock wood,
canonical foliage, two canonical Center banks, shared Mart, and café red/wood.
UI banks13–15 remain reserved. A small set of ordinary lawn/paving interiors use
clean same-material texture cores to fit the buffered viewport budget; curbs,
architecture, signs and silhouettes remain independently retained. No image
rescaling, nearest-metatile substitution or runtime screenshot is used.

The derived atlas has 8,108 glyphs, a 24,346-byte volatile cache, and a worst
16×16 ring of 1,000/1,008 slots. Source hashes guard against stale atlas builds.
The adapter is independently owned, reusing the bounded proven Goldenrod method;
other maps retain their original renderer. Heap reset forgets both city pointers,
and map entry releases the inactive city's cache.

Continuous walking revealed an important private-tileset transition issue:
`MoveMapViewToBackup` can copy a previous section's foreign tile IDs and diagonal
void cells over the new collision grid. Olivine has no mutable exterior tiles,
so only its camera transitions retain `InitMap`'s freshly loaded native grid and
skip that stale-view overlay. Other maps, including Goldenrod, keep their prior
behavior. The test walks across a T junction before the formerly blocked seam.

## Visual and traversal review

`source/` keeps the reference, independent material/collision/upper-layer arrays,
shared master hashes, tree roots, building footprints/approaches and native-fit
art. `evidence/building-contexts/` compares all nine individual buildings with
their HGSS neighborhoods at 2× nearest-neighbor zoom. `cell-ledger.csv` records
every square. Reference/native numbered grids and collision overlays support
terrain-boundary inspection. `review.json` records independent decoded native
and actual Porymap comparison, exact visible canonical art, and reachable doors.
Overlapping crowns are checked on visible pixels; distinct tree roots are kept.

Refinements before qualification: protected cyan Gym entrance colors; separate
café red roof family; coherent lighthouse/terminal cream-and-blue ramp; foliage
kept outside forced stone architecture palettes; original Mart flag remnant
removed with a verified same-row paving donor. The Center and Mart have genuine
alpha and separately restored receiving terrain. Lighthouse door and adjacent
sign are separate occupied spaces. The real ramp and terminal-side walkway join
the continuous city route without opening cliff or water barriers.

See `evidence/build.json`, `runtime.json`, `gameplay-background-parity.json`,
`walking-film.json` and `preservation.json` for exact verification identities.
Actual gameplay PNGs and four continuous walking GIFs are retained in evidence.
Functional success does not imply owner visual acceptance of this new city.

## Scope and remaining limits

Exterior art/traversal only. Building doors remain closed; no Lighthouse floors,
Gym mechanics, healing, shop inventory, ferry service, NPCs, encounters or campaign
flags are implemented. Route39 north, Route40 west and south ferry destination
are explicitly closed pending their separately scoped maps. Water, flags, boats
and umbrellas are static. Hidden ground and projected heights are interpreted;
the lighthouse ramp is continuous foot traversal without a new height system.

## Reproduce / edit

Production native maps are authoritative. **Do not replay `author.py` or
`register.py` over committed maps.** These are retained first-authoring provenance,
not an editor. Use ordinary guarded native edits, then regenerate the adapter:

```sh
python3 tools/gba/maps/olivine_city/stream.py ENGINE
python3 tools/gba/maps/olivine_city/review.py ENGINE PORYMAP_EXPORT_DIR
make -C ENGINE -j1 generated TOOLCHAIN=TOOLCHAIN
make -C ENGINE -j8 TOOLCHAIN=TOOLCHAIN
python3 tools/gba/maps/olivine_city/runtime.py ENGINE NEW_RUNTIME_DIR --toolchain TOOLCHAIN
python3 tools/gba/maps/olivine_city/verify_frames.py NEW_RUNTIME_DIR
python3 tools/gba/maps/olivine_city/film.py ENGINE NEW_FILM_DIR TOOLCHAIN
```

Use the established local ARM14.2.1/newlib, Porymap6.3.1 and mGBA0.10.5 setup
recorded in build evidence. `compile_porymap_probe.py` links a city exporter to
actual Porymap; it does not emulate its renderer. No ROM, saves or binaries are
committed. Hosted GitHub Actions is disabled (previous dispatch rejection recorded
in Goldenrod evidence); this pass relies on explicitly recorded local checks.

## Publication and preserved parallel work

[Engine draft PR #23](https://github.com/Davisfox5/pokeemerald-expansion/pull/23)
is stacked on the Goldenrod branch. Source commit is
`c996146b286add8b16f434346a4eed376e6c2b6e`. At publication, a pre-existing remote
`codex/olivine-city` branch at `506860f6` was discovered, containing additional
Ecruteak/Olivine work. It was not overwritten or merged. This separate review pass
requires reconciliation with that branch before any merge. No approval or
supersession of that existing work is implied.
