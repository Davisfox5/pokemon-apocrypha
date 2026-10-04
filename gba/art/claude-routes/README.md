# Route 29 and Route 30, Claude's build

2026-10-04. The two routes out of Claude's Cherrygrove (`gba/art/claude-cherrygrove/`), replacing that build's
short stubs. Route 29 runs east toward New Bark; Route 30 runs north toward Route 31. Both follow the HGSS maps
cell for cell where the engine allows, in the same HGSS-in-2D art as the town, and both join the town across
real map connections with no seam. Production `game/`, Codex's campaign workbenches and every earlier preview
are untouched.

## Review

- Playable package: `tools/vendor/gba/Routes-claude-preview.zip` (ROM and an ordinary save, ignored by git).
  Load both and choose **CONTINUE**: you start at the Route 29 sea lookout. **NEW GAME** starts outside the
  player's house in Cherrygrove; walk east for Route 29, north for Route 30.
- Side by side with HGSS: [Route 29](evidence/compare-route29.png), [Route 30](evidence/compare-route30.png)
  (top/left the Bulbagarden render, bottom/right this build's packed engine tiles).
- In-game captures: [Route 29](evidence/route29-in-game.png), [Route 30](evidence/route30-in-game.png),
  [both connections, step by step, both directions](evidence/seams.png),
  [signs, the hidden Potion, collision, Continue](evidence/interactions.png).
- Whole maps: [route29-overview.png](route29-overview.png), [route30-overview.png](route30-overview.png).

## What is on the routes

**Route 29** (98 x 34): the HGSS layout of ledges, tall grass blocks, tree clumps, the upper lawn with the
Apricorn tree, the Route 46 gate and the two signs. From the design bible (Chapter 1 world design): blossom
trees at the west end where Cherrygrove's grove spills onto the route; a sea-view lookout on the south side
(lawn, white railing, two benches) with the coast cliff and open sea running under the whole route; one hidden
Potion at the lookout, the route's single reward for curiosity.

**Route 30** (35 x 74): the HGSS layout from Cherrygrove up to the Route 31 steps: the path and its one-way
ledges, the two rock bands with their wooden steps, the berry house, the pond, the junction, the north corridor,
and Mr. Pokemon's house on the plateau with its mailbox, log fence and berry tree. The pond in the south-east
corner is the same water as Cherrygrove's north-east pond.

**Behaviour.** Ledges are one way (jump south, blocked from below and from the sides). Tall grass has encounter
tables from `docs/JOHTO_BATTLES.md`, Morning/Day column (this engine runs one table per map):

| Route | Species and levels |
|---|---|
| 29 | Pidgey 2-4 (44%), Sentret 2-4 (39%), Rattata 2-4 (17%) |
| 30 | Pidgey 3-5 (34%), Rattata 3-5 (34%), Caterpie 4-6 (15%), Weedle 4-6 (15%), Bellsprout 5-6 (2%) |

Random wild battles are skipped while the party is empty (`ShouldDisableRandomEncounters`): Chapter 1's
Route 30 rescue walks the player through tall grass before they own a Pokemon. Scripted battles are unaffected.

**New state.** One flag: `FLAG_HIDDEN_ITEM_APOC_ROUTE29_POTION`, aliased onto `FLAG_UNUSED_0x264` inside the
hidden-item range. Codex's Chapter 1 overlay uses `FLAG_UNUSED_0x020`-`0x02F`; there is no overlap. Two map
sections, `MAPSEC_JOHTO_ROUTE_29` and `MAPSEC_JOHTO_ROUTE_30` ("ROUTE 29", "ROUTE 30"), so the location popup
names each route.

**Not built yet.** The Route 46 gate, Mr. Pokemon's house and the berry house have closed doors (no interiors).
Route 30 has no trainers or NPCs (they are Chapter 2 content). New Bark has no map in this workbench, so
Route 29's east path stops at the map edge; Route 30's top steps stop at the edge where Route 31 will join.
Encounters compile and load, but no wild battle was fought in the checks (the test save has no party).

## Seams

A GBA map keeps only its own tilesets in VRAM, so cells drawn across a connection are rendered with the
current map's tilesets, and crossing a connection swaps the secondary tileset without redrawing the 16x16-cell
window around the player (`field_camera.c`, `LoadMapFromCameraTransition`). `tools/gba/maps/claude_routes/seams.py`
measures every cell that can be on screen across each connection and every cell inside that window at any
crossing. The build then:

- packs those route cells into the shared Cherrygrove primary tileset, using only palettes every map here
  shares (0-5, and 10/11, the blossom and wood banks kept identical in all three secondaries);
- copies the town cells a route can show (the Mart and the north signpost for Route 30, the player's house edge
  and the east signpost for Route 29) into that route's secondary at their own metatile and tile ids, with the
  town's palette bank for them.

Three HGSS details moved to keep only shared terrain inside those windows: Route 29's south-west tall grass
starts at column 9 instead of 7; Route 30's last ledge sits one row higher and its bottom tall grass is two
rows instead of six, with woods where HGSS has the rest. The Route 29 path is three rows wide for its first
three cells so it meets the town's lane cleanly. The shared primary now holds 511 of 512 tiles, so further
changes inside the seam windows need a tile freed first.

## Tile budget

| | Tiles (incl. copied town tiles) | Metatiles | Palette banks (secondary) |
|---|---|---|---|
| Route 29 secondary | 230 | 234 | tall grass 7, ledges 8, gate 9, flowers/Apricorn 12; town's house 6, blossom 10, wood 11 |
| Route 30 secondary | 448 | 368 | tall grass and flowers 6, ledges/rock/steps 7, Mr. Pokemon's house 8, berry house 12; town's Mart 9, wood 11 |
| Shared primary (appended for seams) | 27 (511 total) | 62 (409 total) | |

Details in [build-report.json](build-report.json).

## Art

Everything route-specific is cut from the 1:1 HGSS renders in `references/` (Bulbagarden Archives,
`File:Johto Route 29 HGSS.png` and `File:Johto Route 30 HGSS.png`, sha1 checked on download; hashes in
`evidence/build.json`). Grid origins were measured on tall-grass and ledge edges (Route 29 at (4, 5),
Route 30 at (6, 4)). Tall grass repeats exactly every cell in HGSS, so blocks are assembled per 8x8 quadrant
from a six-cell nine-slice; ledges, ledge walls and corners are single cells; the gate, both houses, the rock
walls and the three flights of steps are cut out whole. Ground, trees, the coast cliff, sea, daisies, signposts,
benches and the railing are the town's own assets, so both maps share them tile for tile. Trees use the town's
HGSS lattice with the phase that continues the town's woods across each seam; a forest cell the lattice misses
gets a tree one column off it, and a leftover margin cell is solid where it touches a ledge, wall, rock or water.
Original designs and art: Game Freak / Nintendo / Creatures (read-only derivation).

## Verified

Built with ARM GNU 14.2.rel1 on Linux and tested with libmGBA, a fresh emulator process per phase. The
previously committed Cherrygrove patch, rebuilt here, matched the Mac ROM hash recorded in `claude-cherrygrove` byte for byte.

- [Runtime](evidence/runtime.json): walking from Cherrygrove into each route across the real connection and
  back; Route 29 end to end to its east edge; ledges jump down and block from below on both routes; ledge walls,
  rock walls, the east cliff, the pond, the railing and the gate door block; all three flights of steps climb;
  four signs read; the hidden Potion is found once, sets its flag and survives a save; twelve steps of tall
  grass with an empty party start no battle; ordinary save at the lookout, cold reload, and title-screen Continue.
- [Structure](evidence/structure.json): passable, tall grass, ledge and water cell counts per route.

## Source

- `tools/gba/maps/claude_routes/layouts.py`: both cell plans, as rectangles read off the renders.
- `art.py`: every cut from the renders. `build.py`: composition, packing against the town's primary, the seam
  rules, tilesets, layouts, maps, encounters, flag, map sections and the empty-party guard. `seams.py`: the seam
  analysis. `runtime.py`: the libmGBA checks. `preserve.py`: patches, package and these boards.
- `gba/claude-routes.patch`: the routes on top of the town. `gba/claude-cherrygrove.patch` was refreshed from the
  current town generator (the committed copy predated its last revision).

## Reproduce

From the repository root, with `disasm/pokeheartgold/files/a/0/4/4` present (the HGSS map textures the town's
art reads; a sparse fetch of the submodule is enough):

```sh
python3 tools/gba/portable.py --preset workbench --output tools/vendor/gba/claude-routes --build
git -C tools/vendor/gba/claude-routes apply --binary "$PWD/gba/claude-cherrygrove.patch"
git -C tools/vendor/gba/claude-routes apply --binary "$PWD/gba/claude-routes.patch"
make -C tools/vendor/gba/claude-routes -j8 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi"
```

To regenerate instead of applying the routes patch, run `python3 tools/gba/maps/claude_routes/build.py
tools/vendor/gba/claude-routes` (it runs the town build first), build, then `runtime.py` and `preserve.py` as in
their docstrings. `preserve.py` expects the workbench tags `preset` and `town` described there.
