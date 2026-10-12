# Cherrygrove: first playable GBA town proposal

**Latest preview:** [Johto revision 3](../gba/art/johto-v3/README.md) preserves the
owner-approved buildings, corrects the tree and scenery transparency, and revises
the geography around the HGSS western bay. Its layout is 64 × 40, with moved
entrances and matching runtime checks. This page retains the original town
milestone and patch-chain provenance; use the v3 page for current coordinates,
art and playable package.

Built 2026-09-13 in an independent checkout. This is the first explorable town
and an owner-reviewable layout/art proposal. Chapter 1's scripted opening is not
implemented by this milestone. Production `game/` was not modified by the town work.

## Play and review

Local preview folder: `tools/vendor/gba/cherrygrove-preview/`.
Open `Cherrygrove.gba` in mGBA with the matching `Cherrygrove.sav` beside it, then
choose **CONTINUE**. The provided ordinary save starts on the pier. Walk north
into town. The title-screen Continue path was checked using button input after a
cold emulator reset, separately from the instrumented save/load tests.

This isolated development save has no starter. It is for walking, entering rooms,
interacting with residents and inspecting the town. Keep it separate from campaign
saves. The ROM, save and emulator binaries remain ignored local artifacts.

- [Runtime captures](../gba/evidence/cherrygrove/runtime-contact-sheet.png)
- [Full layout preview, rendered from source](../gba/evidence/cherrygrove/town-overview.png)
- [Build, provenance and runtime evidence](../gba/evidence/cherrygrove/build.json)
- [Structural checks](../gba/evidence/cherrygrove/structural.json)

## Town and canon

The map is 44 × 40 metatiles (704 × 640 pixels), with six enterable buildings:
player home, Gold's home, southeast neighbor, a transplant's home, Mart and Pokémon
Center. The player home includes an upstairs bedroom. A small blossom park sits
northwest of the shops; the south and west open to the sea. The southern beach
has a wooden pier, two non-boardable boats, drying-net scenery and a lookout.
Gold's house has a weathered amber roof, blossom trees and a bare practice yard.
Two moving boxes dress the player home. Gold has no monument or shrine.

Route 29 leaves **east** toward New Bark. Route 30 leaves **north** toward Violet.
Both have short connected technical approaches; complete routes, encounters and
chapter gates are not part of this build. The approach boundaries are preview
limits, not newly invented story barriers.

Sources of narrative authority: `DESIGN.md`, Chapter 1 World & Map Design and
Cherrygrove's ten-years-on description. The specifically referenced historical
Chapter 1 sections 8.0, 8.2 and 8.5 supplied the corrected exit directions,
waterfront/commuter flavor and scenery requirements. Their DS coordinates, IDs,
models and obsolete owner-labor instructions were not carried into GBA work.

The exact new layout, component assembly, shortened resident lines, provisional
Mart stock (Potion, Antidote, Paralyze Heal) and ambient music are proposals for
review. They do not settle campaign economy, encounters or level progression.

## Assets and editing

The town uses a uniform **Emerald** layout format: 512 primary / 512 secondary
tile split and 16-bit metatile attributes. This avoids the earlier native-FRLG
editor complication. Porymap 6.3.1 opened and rendered Cherrygrove's custom tileset.
Saving through its UI preserved the map blocks, map IDs, Johto region metadata,
`build_target`, doors and connections. Parsed JSON was semantically identical;
the editor-saved rebuild produced an identical ROM. JSON formatting was then
normalized back to the project's existing style.

Native asset provenance is the pinned pokeemerald-expansion source:

| Component | Source and treatment |
| --- | --- |
| Terrain, buildings, foliage | Existing `primary/general` pixel indices and metatiles, with map-local palette data and selected metatile palette remapping |
| Secondary framework | Existing `secondary/petalburg`, extended with a small remapped subset of Slateport tiles |
| Boats, seating, nets | Selected `secondary/slateport` components; boats have solid collision and no warp |
| Palette | Warm highlights, muted greens, teal water, an independent pink blossom bank, and amber roof accents |
| Interiors | Existing Emerald house, Mart and Pokémon Center layouts, with newly authored map events and reciprocal warps |
| People/boxes | Existing GBA generic residents, Mom and moving-box object graphics |

These are adaptations of existing project assets, not newly generated Pokémon
or a claim of new ownership/reuse rights over the original game artwork. Native
source paths and compilation remain in the patch. The palette/compiler code and
layout specification are editable sources.

Current seating uses small deck-chair components as a visible provisional choice.
Bespoke park benches, richer weathering, final Gold/Kestra/Silver assets, expanded
interior dressing and the exact regional art finish remain owner-review work.
Gold's house is enterable, but Gold, Typhlosion and the starter ceremony are not
placed yet. No substitute character was silently cast as Gold.

## What passed

- ROM compilation, native graphics and script linking.
- Eleven map definitions; all warp targets, connection targets and event labels resolve.
- Collision-grid connectivity from spawn to every building entrance, both route
  exits, the pier and the lookout. The town's padded grid uses 3,186 / 10,240 cells.
- Directional-input entry and exit for all six buildings.
- Player-home stairs in both directions.
- East Route 29 connection and return; north Route 30 connection and return.
- Pier end collision, resident dialogue rendering and the Mart menu.
- Ordinary 128 KiB flash save at the pier, separate-process reload with exact
  map/region/coordinates, and a separate ordinary title-screen Continue test.
- Native-resolution field captures, editor rendering and visual corrections to
  the coast, boat backgrounds, blossom colors and sea border.

The host harness uses engine entry points for controlled setup and relocations;
movement, door/stair entry, connections, menu input and the final Continue test
use normal button input. A harness-only error from warping while dialogue was
still open was fixed by waiting for field controls to unlock. Initial title test
input stopped at the title screen; the final test advances through the actual
Continue menu and passes. These failures and passing runs remain in ignored local
run folders; the evidence file points to the final passing results.

The standard nurse routine is wired without the donor's campaign callbacks.
HP recovery, fainting/respawn behavior, upstairs Center services, full save-menu
interaction, old-save migration and hardware execution were not separately
qualified. The deferred 30-box architecture is unchanged. No battles, rewards,
Hidden Ability access, tutor economy or level curve was designed in this task.

## Source and reproduction

The town patch is [gba/cherrygrove-town.patch](../gba/cherrygrove-town.patch).
It applies after the qualified map-pipeline snapshot, whose independent commit
is `b01afeda981936736c0deb49376f8575e88ea533`, based on upstream
`e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7` and the mechanics snapshot identified
in the evidence JSON. It is **not** a patch against a clean upstream checkout.
Current production mechanics continued to change independently; integrate the
accepted town against that current source in a later scoped step.

Do not apply the whole preview patch blindly to production: it includes isolated
starting-location and harness changes. All engine modifications and native map/
asset source are preserved outside the dirty submodule; no ROM or save is tracked.

To reconstruct from the local baseline into a new path:

```sh
 git clone --shared tools/vendor/gba/cherrygrove-game tools/vendor/gba/cherrygrove-fresh
 git -C tools/vendor/gba/cherrygrove-fresh apply "$PWD/gba/cherrygrove-town.patch"
 gmake -C tools/vendor/gba/cherrygrove-fresh -j8 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
 python3 tools/gba/maps/validate_cherrygrove.py tools/vendor/gba/cherrygrove-fresh
 python3 tools/gba/maps/check_cherrygrove.py tools/vendor/gba/cherrygrove-fresh tools/vendor/gba/cherrygrove-fresh-results --toolchain "$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
```

For a new generated layout, use `tools/gba/maps/cherrygrove.py` instead of applying
the town patch. It reads `gba/maps/cherrygrove/town.json` and compiles native
palette, tile, map and event data. It refuses to overwrite an existing town unless
explicitly invoked with `--refresh-generated`; preserve any native editor work in
the source patch first. The generator is a narrow town compiler, not a new editor.
`tools/gba/maps/tiles.py` renders native source for inspection.

Tests use installed mGBA 0.10.5 and a fixed emulator RTC for consistent review
captures, using its [documented source implementation](https://github.com/mgba-emu/mgba/blob/0.10.5/src/core/interface.c).
The real ROM still uses the engine's time-of-day behavior. Source hashes, tool
versions, ROM identity and measured size belong to the evidence JSON.

Next: owner review of this town's layout and GBA visual direction; then revise
that proposal and implement the opening/home/Gold sequence against approved
Chapter 1 dialogue. This build does not imply approval of its exact art or layout.
