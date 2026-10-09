# Routes to New Bark and Violet, campus layout proposal

October 8, 2026. Continues the October 4 Claude Cherrygrove/Route 29/Route 30 maps
from `codex/gba-source-handoff` (`9195267`). The existing town, route geometry,
encounters, signs and hidden Potion are preserved. This is an isolated map/art
preview, not the integrated Chapter 1 campaign.

## Exterior work

- Route 29 now connects east to New Bark, with return travel on the same lane.
- Route 30 now connects north to Route 31. Route 31 is a new layout proposal with
  the Violet gate, Dark Cave junction, pond, tall grass and a south-facing ledge.
  It retains those recognizable landmarks; it is not a cell-for-cell HGSS copy.
- New Bark is a 44 by 34 research campus. Elm's institute keeps its entrance at
  `(27,11)`, matching the preserved Chapter 1 scene coordinates. Teal/off-white
  architecture, paved circulation, two planted courtyard pockets, supply crates,
  a dish, researchers, staff homes and a coastal observation terrace distinguish
  it from Cherrygrove. The annex is closed to visitors.
- Both homes have separate interior maps and return to their own doorways.
- Violet's east entrance is a small arrival court with a visible gate facade.
  The rest of Violet City and its university are not built by this preview.

The campus and Route 31 layouts are proposals for visual review, not newly approved
canon. They follow `DESIGN.md`'s research hub, clean Chapter 1 and cooler campus
accent. No Silph/Apex content, quest flags, rewards or trainer teams were added.
Route 31 has no new encounter table; the owner deferred that design.

## Art and source

`tools/gba/maps/johto_connections/layouts.py` contains the editable exterior plans.
`art.py` contains original native pixel modules for the institute/annex, paving,
equipment and cave entrance. Existing HGSS-derived town houses are recolored for
staff housing; trees, sea, cliffs, flowers, fences, signs and benches reuse the
town kit. The Route 31/Violet gate and tall grass/ledge art reuse the preserved
route kit. There is no image-model art or full-map quantization step.

Original reused designs: Game Freak / Nintendo / Creatures. HGSS render provenance
and hashes remain in `../claude-routes/README.md` and `../claude-cherrygrove/README.md`.
New campus/cave modules are original project pixel work. No new external art was
downloaded. Tiles are 8 by 8, metatiles 16 by 16, with index 0 transparent and
at most 15 visible colors per bank. Generated native sources are preserved in
`../../johto-connections.patch`; overview PNGs decode those packed sources.

The institute reception uses Emerald's lab layout. Housing uses its generic house
layout. The gate uses Emerald's native two-entrance gate layout, without
its original actors or scripts. Dark Cave is a bounded entrance room cut from the
native Rusturf tiles/layout, with its upper route sealed and no donor campaign
events. These are functional interior reuse, not finished Johto interior art.
Elm's scene, Pokédex handoff and prior Chapter 1 scripts are not imported here.

## Connection safety

The shared primary remains at 511 tiles and is unchanged. Each new secondary
copies the neighbor's visible metatiles and graphics at their existing IDs. Any
additional seam entries are appended to the neighbor's secondary; new art away
from the seam can use other secondary slots. Palette banks in crossing windows
must match. `validate.py` compares actual decoded pixels and behavior attributes
with either map's tileset, over both camera visibility and 16-cell crossing windows.
It also checks native tile references and reachable doors/signs.

See `build-report.json` for measured tile/metatile spans and copied entries.
Removing unused end-of-sheet padding does not alter the referenced route art.

## Reproduce

From a fresh isolated workbench, with the host dependencies and Arm compiler
described in `docs/GBA_REMOTE_HANDOFF.md`:

```sh
python3 tools/gba/portable.py --preset workbench --output tools/vendor/gba/connections-preview
git -C tools/vendor/gba/connections-preview apply --binary "$PWD/gba/claude-cherrygrove.patch"
git -C tools/vendor/gba/connections-preview apply --binary "$PWD/gba/claude-routes.patch"
python3 tools/gba/maps/johto_connections/build.py tools/vendor/gba/connections-preview
make -C tools/vendor/gba/connections-preview -j8 TOOLCHAIN=/path/to/arm-toolchain
python3 tools/gba/maps/johto_connections/validate.py tools/vendor/gba/connections-preview --output tools/vendor/gba/connections-structure.json
python3 tools/gba/maps/johto_connections/runtime.py tools/vendor/gba/connections-preview tools/vendor/gba/connections-check --toolchain /path/to/arm-toolchain
```

Alternatively, apply `gba/johto-connections.patch` after the two preserved patches
instead of running the generator. The generator refuses existing New Bark source
so later manual edits cannot be erased. Neither method regenerates Cherrygrove
or requires the historical DS submodules.

This session's pinned vendor compiler download was denied by the cloud proxy.
The build uses Debian's Arm GNU 14.2.1 package and libmGBA 0.10.5, extracted into
an isolated dependency folder. `--toolchain` and `MGBA_FLAGS` select local tools;
no system installation, proxy bypass or production `game/` change is needed.

## Verification and review

Structural evidence is in `evidence/structure.json`. Runtime captures and phase
results are published beside it. All three runtime phases passed. The runtime starts a new
emulator process for each write, cold reload and title-screen Continue phase.
Debug entry points select test starting locations; transitions and doors are then
walked with ordinary directional input. New Game skips naming in this art preview.
Save testing uses ordinary flash saves, never savestates.

Whole-map PNGs are packed-tile previews without actors. Native engine captures
are the visual evidence for final review. The playable package is an art preview;
use Continue to start in New Bark or New Game for the original Cherrygrove start.
Production, owner saves and earlier packages remain untouched.

Review boards: [New Bark](evidence/new-bark-in-game.png),
[the route to Violet](evidence/route31-in-game.png),
[connection crossings](evidence/seams-in-game.png),
[Save/Continue](evidence/save-continue.png), and
[native campus walking](evidence/campus-walk.gif).
The walking GIF captures every fourth engine frame at native resolution;
it is an emulator recording, not an animated overview.

`evidence/preservation.json` checks the old route/town layouts, referenced graphics,
palettes, flags and encounters. `evidence/reproduction.json` records a fresh
generation matching all 95 changed/new map-source files in the tested workbench.
The patch passes forward and reverse application checks.
