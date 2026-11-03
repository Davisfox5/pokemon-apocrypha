# Dark Cave: HGSS cave textures, ten years on, and Dive

**Owner-accepted 2026-11-03** ("Hey, now we're talking! I love it. Let's lock that in."), engine
`0ce719368e`, hub `4ec88e1c`. Treat all four maps as locked: edit their committed native source in
Porymap, never regenerate them from these tools (`install.py` refuses to run over them).

Engine branch `claude/dark-cave` (stacked on
`claude/route-46`), maps `DarkCaveRoute45Side` (id 49) and `DarkCaveRoute31Side` (id 50), 64x64
each in HGSS's own coordinates; `DarkCaveGrotto` (id 51, 40x30) and `DarkCaveUnderwater` (id 52,
64x64, the Route 45 side's coordinates). Owner's style choice: HGSS's own Dark Cave rock, floor and water converted to native
tiles, the way Union Cave was finished. None of Union Cave's art, palettes or generators are used.

## Ten years on (owner direction, November 2-3)

"Make it seem like ten years have passed", with bigger changes than the first mockups, a new section
dug farther into the rock for minerals, existing art from the repo's games wherever it exists, and a
place in the water to Dive to an underwater path and a new cave section built from scratch.

Review: [Route 45 side, sixth pass beside ten years on](evidence/review/route45-side-decade-whole.png) ·
[Route 31 side](evidence/review/route31-side-decade-whole.png) · at 2x:
[the mine](evidence/review/route31-side-decade-mine.png) ·
[west cavern, camp, heaps](evidence/review/route31-side-decade-west-cavern-camp-and-heaps.png) ·
[lake and Dive spot](evidence/review/route45-side-decade-lake-and-dive-spot.png) ·
[rockfall and camp](evidence/review/route45-side-decade-rockfall-and-camp.png) ·
[north hall and camp](evidence/review/route45-side-decade-north-hall-and-camp.png) ·
[the Dive spot over the underwater path, same cells](evidence/review/dive.png) ·
[grotto](evidence/review/grotto-whole.png) · [underwater path](evidence/review/underwater-whole.png) ·
[gameplay gallery](evidence/review/gameplay-gallery-decade.png)

`decade.py` edits the mapped ledger before anything is drawn, so every new wall is drawn by the same
rock pieces as HGSS's own:

| Change | Where | Built from |
| --- | --- | --- |
| The mine: a drift south out of the west cavern, a gallery closed at its east end by a rockfall, an ore stope and a quartz stope joined by a crosscut, a lower gallery, a drift closed by a timber barricade, a loading room | Route 31 side, (14-15, 26) south to row 58 | Floor at the cavern's height; the rock round it steps up a tier a cell (HGSS's rings); the rockfall is HGSS's rock pile as the cave draws it (a formation one tier up) |
| A sign at the mine: "DARK CAVE MINE / No entry without a light." | (13, 26) | The routes' sign (route-46 shared P13); a Gen 3 sign event |
| The lake two cells higher over its lowest shore, never over the worn track, an exit or an HGSS event cell; no one-cell fingers or stubs | Route 45 side | The cave's pond pieces |
| The Dive spot, 3x3 | Route 45 side (37-39, 31-33) | Emerald Cave's dive water (metatile 660), each colour as much darker than the cave water as Emerald's is than its own pool (368) |
| A rockfall across the east shore path (the lake reaches past it) | Route 45 side (48-51, 39-40) | HGSS's rock pile as a formation |
| Debris heaps at a wall's foot | Route 45 side (30-31, 8); Route 31 side (33, 14-15) | FRLG Power Plant's debris (power_plant_frlg 693, top layer) in the cave rock ramp |
| Camps; the mine's crates, log stacks, ore and quartz | Route 45 side (41-46, 37-38), (53-54, 2); Route 31 side (8-10, 5); the mine | Slateport's crates (822, 830, 831), Mauville's log stack (708) in the crates' wood, FRLG's boulder in ore and quartz tones |
| Moss rocks spread over damp floor and along walls, one at a time, each only where nothing reachable is cut off, never in rows | both sides | HGSS's moss rock as the cave already draws it |
| A worn track between the exits and into the mine | both sides | Two of the floor's own four tones lighter, edged with the ground painter's wave |
| The Johto grade (DESIGN.md: shadows toward teal, light toward amber) | every map | `decade.grade` |

Not drawn: wall lamps (no Gen 3 tileset in the repo has a cave lamp, and HGSS's lights are 3D
models) and rails (none exist in any tileset here). Both would be new tile art.

### Dive

| From | Action | To |
| --- | --- | --- |
| Route 45 side, the Dive spot (MB_DEEP_WATER) | Dive (map connection `dive`) | `DarkCaveUnderwater`, same cell |
| `DarkCaveUnderwater`, under the Dive spot (MB_NORMAL; everywhere else MB_NO_SURFACING) | Emerge (connection `emerge`) | Route 45 side, same cell, surfing |
| `DarkCaveUnderwater` water door (28, 33) (MB_WATER_DOOR) | swim in | `DarkCaveGrotto` (19, 21), its deep water, surfing |
| `DarkCaveGrotto` deep water (18-19, 21-22) | Dive (ON_RESUME `setdivewarp`, the Seafloor Cavern pattern) | `DarkCaveUnderwater` (28, 34), in front of the door |

`underwater.py` lays the path out in the Route 45 side's own cells (Gen 3 dives and emerges at the
same cell): a pool under the Dive spot, a trench south, west and north to the door, the rest the
seabed's rock. It uses Emerald's own underwater pieces by rule (plateau 531, faces 653/654/547/644,
corners 637/638/645/646 and 518/519/546, floor 681, seaweed 641, Underwater_Route128's six door
pieces), recoloured to the cave water's hue and dimmed. The grotto (`grotto.py`, a creative
proposal) is a flooded chamber: the pool, a shore, a terrace and an upper chamber of quartz and moss
rock, two stair flights. Gen 3 counts underwater as outdoors, so diving clears Flash; the grotto is
dark until Flash is used again. No items or encounters are placed.

## Review

- Whole maps, HGSS beside native: [Route 45 side](evidence/review/route45-side-whole.png),
  [Route 31 side](evidence/review/route31-side-whole.png)
- Route 45 side at 2x: [north halls](evidence/review/route45-side-north-halls.png) ·
  [west ledges](evidence/review/route45-side-west-ledges.png) · [lake](evidence/review/route45-side-lake.png) ·
  [south and the hole down](evidence/review/route45-side-south-and-hole.png)
- Route 31 side at 2x: [west cavern and pools](evidence/review/route31-side-west-cavern-and-pools.png) ·
  [hole and north](evidence/review/route31-side-hole-and-north.png) · [east halls](evidence/review/route31-side-east-halls.png) ·
  [south and the Route 46 exit](evidence/review/route31-side-south-and-route46-exit.png)
- [The doors on Routes 45 and 46](evidence/review/route-doors.png)
- [Gameplay gallery](evidence/review/gameplay-gallery.png) (headless mGBA)

## Art

Owner direction (October 31): no HGSS render pixels and no blended tiles; the Johto routes' own
tiles, recoloured. `assemble.py` maps the cave out cell by cell from HGSS's data and draws it with
exactly the pieces the routes use:

- **Mapped shapes** ([Route 45 side](source/assemble/route45-side-terrace-grid.txt),
  [Route 31 side](source/assemble/route31-side-terrace-grid.txt)): every floor at its own height,
  every rock cell at its tier top, both read straight down from HGSS's mesh
  (`hgss-cell-peak.npy`), plus stairs, jump ledges, water, boulders and exits. HGSS's black void is
  rock, as a Gen 3 cave's surroundings are.
- **Rock:** FRLG General's mountain nine-slice, over-rock pieces and inner corners, laid out as on the
  routes (`route46/elements.py` `rock_frlg` with the routes' `terraces`, `topped` and `south_faces`):
  every HGSS height is a terrace, ground included, and a wall has a face only toward ground that is
  really lower. A thin wall between two floors is the upper floor's edge, not a free ridge.
- **Ground:** the routes' road (Cherrygrove's sand quarter), edge to edge.
- **Water:** FRLG General's rock-edged pond (metatiles 419-431, inner corners 435-436, as in Icefall
  Cave), the lip in the rock ramp. The lip runs only where water meets ground (floor, a ledge, stairs, a
  rock object), the same brown lip on every side (FRLG's north row turned over for the south edge,
  since its own south row is a pale strip that met the side lips badly); where a wall meets the water
  the wall goes straight in, as in HGSS (owner review: consistent water borders).
- **HGSS's rock objects** (owner review: some stones were rock formations; recolour the rocks): its
  2x2 rock pile (`d_rock01`) is a small rock formation in the route rock, one tier above its floor; its
  moss rock (`d_rock01s`) is FRLG General's boulder in HGSS's moss tones (MOSS_RAMP, from its rendered
  texture), on the floor or water under it. A blocked cell HGSS paints with a floor or pool decal and
  no rock object is a pillar top, so it is rock.
- **Clean-up** (`regularise`, listed per cell in the assemble report; traversal is untouched):
  floor cells one level off the floor round them (HGSS height noise) are levelled; outer rock more
  than three cells from any floor is the rock top (HGSS shows at most three tiers before its dark);
  free-standing formations are one block; narrow rock (open ground on two opposite sides within two
  cells: the lake's diagonal outcrop, thin walls) is one tier per run, except where it meets the wider
  rock it grows from; one-cell spines and small raised bumps on a rock top are flattened; a rock nub
  with three sides lower takes the height of the rock it sticks out of, so it draws as that rock's
  rounded end.
- **Colours:** every colour is then swapped one for one: the Johto rock ramp for HGSS's cave rock
  tones (from `dwall_s`, `dcliff01`, `dallpeak_p`), the road tones for the cave floor tones
  (`droad01`) and the pond water for the cave water (`driver`) by brightness rank, the stairs' grey stone for
  the cave rock ramp, the cast shadow for the floor's darkest. The exit glows and the hole are HGSS's
  own exit art over the floor.

Earlier passes (HGSS's slanted render; HGSS's textures on the grid; the route rock over HGSS's floor)
were turned down in review.

All four maps share one tileset pair of their own (`gTileset_DarkCavePrimary`, `gTileset_DarkCave`). The
pack is lossless: 330 tiles and 176 metatiles, exact palette banks, every pixel as assembled
([pack.json](evidence/pack.json)). Every cell is one bottom layer under the player.
[Before and after, Route 45 side](evidence/assemble/route45-side-before-after.png) ·
[Route 31 side](evidence/assemble/route31-side-before-after.png).

## Traversal

From HGSS's permission grid, cell for cell ([traversal](source/pack/)):

| HGSS | Native |
| --- | --- |
| floor (0x08) | MB_CAVE, elevation 3 |
| water (0x15) | MB_POND_WATER, elevation 1 (Surf) |
| ledges (0x3B, 0x39) | MB_JUMP_SOUTH, MB_JUMP_WEST, one way |
| exit cell (0x6F) with arrow (0x65) south of it | MB_SOUTH_ARROW_WARP on the exit cell |
| hole into the Route 45 side (0x6E) | MB_NON_ANIMATED_DOOR: walked into northward, the player steps out south |
| wall, rim, void | solid |

The border block is the rock-fill metatile HGSS's void cells carry, so past the map edge is rock. Both maps
are MAP_TYPE_UNDERGROUND and need Flash, under the existing MAPSEC_DARK_CAVE, music MUS_CAVE_OF_ORIGIN
(DarkCaveEntrance's).

## Doors

| From | To |
| --- | --- |
| Route 45 (10, 6) mouth | Route 45 side (60, 4) exit |
| Route 45 side (6, 57) exit | Route 31 side (26, 4) hole |
| Route 31 side (55, 56) exit | Route 46 (20, 9) mouth |

Routes 45 and 46 are owner-accepted and locked, so their changes are native wiring edits only: the
mouth metatile (Route 45's 523, Route 46's 538, each used by that one cell) becomes
MB_NON_ANIMATED_DOOR with its layer kept, the cell's collision opens, and one warp is added. No pixel
changes ([audit](evidence/audit.json)).

HGSS's ledges on the Route 45 side run one way. From the hole up from the Route 31 side there is no
way back up to Route 45, in HGSS or here; the audit checks each exit reaches the others exactly as
HGSS's do.

## Not built or not placed

- **Route 31 exit** (5, 26) stays solid. Route 31 and `DarkCaveEntrance` are another agent's maps.
- Placed: the Route 31 side's four Rock Smash rocks and the Strength boulder, at HGSS's cells, as
  Gen 3 field objects. They hold back 374 cells, as in HGSS (the mine is not behind them).
- Not decided (owner's call, as native edits on the locked maps): whether the mine is gated (it is open from the west cavern now), what
  the grotto holds, and whether the rockfalls should open later in the campaign.
- Not placed: the sunglasses NPC, item balls (TM54, Revive, Potion, Hyper Potion, Full Heal, Dire Hit,
  Black Flute), hidden items and wild encounters. All are recorded in
  [source/hgss-events](source/hgss-events/).

## Evidence

- **Audit** ([audit.json](evidence/audit.json)): all four maps decode to the packer's image on every
  pixel; behaviour, collision, elevation and layer match the ledger on every cell. Gen 3 movement
  reaches exactly the ledger's cells. Against HGSS: the only cells added are the mine's (385 on the
  Route 31 side), the only cells lost are the decade's blocked ones (33 and 14); each exit reaches
  the others exactly as in HGSS, on foot and with Surf; every HGSS item, NPC and hidden-item cell is
  still reached. The Dive spot is exactly the underwater path's emerge cells; the connections go
  both ways; the grotto dives to an open no-surfacing cell. Every warp pairs back. Routes 45 and 46
  change no pixel, and the changed-file list is checked.
- **Headless mGBA** ([results](evidence/gameplay/results.json)): 54 captures, each rebuilt from VRAM
  and equal to the decoded map. Caves are dark without Flash and lit with it; all three doors are
  walked both ways; a ledge jumps one way; Surf starts on both pools. The Rock Smash rock, the
  boulder and the rockfall block the player, and so does Route 31's exit. The mine is walked into
  and its sign read. Dive runs Gen 3's own field logic (TrySetDiveWarp, DoDiveWarp; only the party
  HM check is skipped): it dives on the Dive spot and not beside it, emerges only under the spot and
  not in the trench, the water door lands in the grotto's pool surfing, the grotto's stairs climb
  both ways and its deep water dives back to the door. Flash save, cold reload and title Continue
  all pass.
- **Porymap 6.3.1** ([results](evidence/porymap/results.json)): opens, exports and saves all six maps
  on a fresh clone. Exports equal the native decodes on every pixel, no Dark Cave or route line
  changes on save, and the log has no errors.

## Reproduce

```sh
python3 tools/gba/maps/dark_cave/hgss_render.py PHG OUT route45-side   # and route31-side
python3 tools/gba/maps/dark_cave/hgss_events.py PHG gba/art/dark-cave/source/hgss-events
python3 tools/gba/maps/dark_cave/assemble.py PHG ENGINE      # with decade.py, grotto.py and underwater.py
python3 tools/gba/maps/dark_cave/pack.py ENGINE
python3 tools/gba/maps/dark_cave/install.py ENGINE      # refuses over commits that are not its own
make -C ENGINE -j8
python3 tools/gba/maps/dark_cave/check.py ENGINE
python3 tools/gba/maps/dark_cave/runtime.py ENGINE OUT_DIR
python3 tools/gba/maps/dark_cave/porymap.py ENGINE PORYMAP_BINARY   # needs the engine change committed
python3 tools/gba/maps/dark_cave/review.py ENGINE OUT_DIR
```

Source artwork: Nintendo / Game Freak / Creatures, decoded read-only from pret/pokeheartgold's
archives. No ROMs, saves or tool binaries committed.
