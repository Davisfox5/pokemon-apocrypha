# Violet City interiors (November 3)

Owner request: rebuild the interiors of the university, Sprout Tower, the lecture hall and the five houses,
"with aesthetics based on their previous iterations but more appropriate for their new roles in the story."

The previous iteration of each room is its HGSS original. Every room starts from HGSS's own data, rendered
from pret/pokeheartgold (revision `9d8b7591f`) by `tools/gba/maps/violet_interiors/hgss_interior.py`. That
script uses the route renderer's projection (`route29_catalog/hgss_render.py`), one HGSS tile per 16 px
cell, and draws each room's terrain and every furniture model separately. Collision comes from HGSS's
permission grid, and warps and exits from HGSS's zone events. Rooms whose role changed are labelled
**proposals**. Their sources are DESIGN.md (Violet as the academic capital: the trainer school grown into a
university, Falkner's gym a lecture hall and practice arena) and the owner's November 3 choice of campus homes.

| Room | HGSS original | What it is now |
| --- | --- | --- |
| `SproutTower1F`-`3F` | Sprout Tower 1F-3F (D15R0101-0103) | HGSS as it is: the floor, walls, lanterns, railings, the swaying pillar, ladders, Bellsprout statues. All three floors are built, linked by HGSS's own ladders. |
| `VioletUniversity` | Pokémon School (T22R0301) | Proposal. HGSS's school is the lecture room as it is: blackboard, the dean's desk, students' desks, bookshelf and cabinet, the tiled aisle. West of it the room runs on nine columns of its own floor and wall as the library: four tall stacks on the back wall (bookshelf behaviour), two free-standing stacks and two reading tables (scenes 2.3b-c). |
| `VioletLectureHall` | Violet Gym (T22GYM0101) | Proposal. HGSS's hall: the drapery and crest, orange pillars, glass floor panels and rails, the wooden stage and its green mat, the statues at the door. The pit and the raised walkways become a stone practice court with white lines. A blackboard stands at the back of the stage and a lectern at its edge. Two rows of desks face the stage on each side (scene 2.5). |
| `VioletHouse1` (11, 26) | Violet house, tatami twin (T20R0301) | Proposal: a retired sage's home, nearest the tower. A home shrine, a low table with cushions, a Bellsprout statue (Sprout Tower's own model), a bonsai. |
| `VioletHouse2` (10, 37) | Violet house (T22R0401) | Proposal: a students' boarding house. Two beds, a study desk, a poster. |
| `VioletHouse3` (26, 55) | Violet house | Proposal: a second boarding house. Two beds, the bookshelf, a study table, a new arrival's boxes. |
| `VioletHouse4` (36, 60) | Violet house | Proposal: a professor's home with a study. Two tall shelves and a globe by the reading table. |
| `VioletHouse5` (56, 63) | Violet house | Proposal: the map-card kid's family home (scene 2.3c), with their gran. HGSS's house as it is, plus a town map on the wall and a TV. |

![every room, HGSS original beside the native map](evidence/VioletUniversity-compare.png)

Each `evidence/<map>-clean.png` shows HGSS's room beside the native map at 3x without grids (`-native-3x.png` the native map alone). Each `evidence/<map>-compare.png` shows HGSS's room (coordinate grid in HGSS cells) beside the native map
(map cells, blocked cells marked red). `-composed.png` is the room as composed, and `-installed.png` is the
installed map decoded from its native tiles.

## How it is built

`tools/gba/maps/violet_interiors/build.py ENGINE` runs these steps:

- **Compose each room.** `rooms.py` holds each room's recipe and `room.py` the tools:
  - Crop or re-lay HGSS's columns (`compose`).
  - Keep, drop, move or add HGSS furniture models (`place`).
  - Copy terrain cells (`paint`).
- **Layers.** A prop's parts that stand over a walkable cell go on the top layer and draw over the
  player. Everything else is the bottom layer. Ladder and exit cells keep their art under the player.
- **Collision.**
  - Rooms kept as HGSS has them use HGSS's own collision.
  - Added furniture blocks the cells it stands on.
  - The lecture hall's court and seating are walkable floor apart from the desks, rails and statues.
- **Packing.** Each building's rooms pack into a private tileset pair of its own (`ipack.py`):
  - Pairs: `violet_university`, `violet_lecture_hall`, `violet_sprout_tower`, `violet_sage_house`,
    `violet_houses`.
  - Every 8 px quadrant draws from one of 13 banks of 15 colours.
  - The packer tries two palette methods and keeps the one that scores better:
    - exact banks after merging near-identical colours, each bank then refit to its quadrants' own colours;
    - k-means over quadrants.
  - A repair pass then gives each quadrant's missing colours a bank.
- **Install.** Layouts, maps and warps go into the engine. `violet_city/doors.py` keeps these interiors'
  layouts and inner warps whenever Violet is reinstalled.

| Pair | Colours in | Method | Tiles | Metatiles |
| --- | --- | --- | --- | --- |
| violet_university | 121 | merged within 2 steps, refit | 241 | 110 |
| violet_lecture_hall | 227 | merged within 2 steps, refit, repaired | 574 | 300 |
| violet_sage_house | 111 | merged within 1 step, refit | 185 | 78 |
| violet_houses | 150 | merged within 2 steps, refit, repaired | 354 | 151 |

The numbers are in `evidence/build.json`; two builds in a row write identical tilesets.
| violet_sprout_tower | 146 | k-means, repaired | 928 | 623 |

Installed against composed: mean channel error 0.4-2.0 per room, and at most 9 pixels per room more than
32 off on a channel (most rooms 0).

## Round 2 (owner, November 4)

- **Lecture hall:** the court and desks now sit up against the stage and blackboard. HGSS's walkway neck
  (rows 9-10) and one entrance row are gone, so the room is 26 rows instead of 30. The desks run along both
  sides of the court, with the students on stools facing it.
- **University:** the free-standing library stacks are the back wall's own tall shelf. The green-book
  shelf drew mangled. An aisle now separates the stacks from the back wall.
- **Sprout Tower 1F-3F:** a Gen 3 conversion (`sprout_native.py`) on HGSS's own floor plan. Every
  walkway, the railing ring, the pillar, the ladders and the statues stand on HGSS's squares, drawn in
  Gen 3 pieces:
  - FireRed's Pokémon Tower purple north wall.
  - The Fighting Dojo's planks, wall shade and hanging scrolls (at HGSS's lanterns).
  - Emerald's Fortree trunk as the swaying pillar.
  - Fortree's exit mat.

  Gen 3 has no wooden railing, indoor ladder or Bellsprout statue, so those three are drawn in Gen 3's
  manner (flat ramps, 1 px outlines) from the trunk's browns. The statue is HGSS's reduced to those browns.
  Packed exactly: 29 colours, 86 tiles.
- **Houses:** each has a floor plan for its role (`houses_native.py`, `evidence/houses-floorplans.png`),
  following the Celadon apartments method. Each room is 11 x 9 with a two-row north wall, furniture
  against it, a one-square way to every piece, and the exit mat at (4, 8). All are built from whole
  FireRed room pieces with their own collision and behaviour:
  - Pallet Town's houses: the kitchen, TV, window, dining set on its rug, beds, PC and desk, bookshelf,
    town map, plants, floor, walls and mat.
  - Lavender's study table and Fuchsia's reading table on its rug.
  - The sage's home on the Fighting Dojo: its green wall with round windows and scrolls, planks, tatami,
    potted plant and mat, plus the tower's Bellsprout statue.

  Packed exactly: 46 colours in the four FireRed houses, 33 in the sage's.
- `evidence/<map>-clean.png`: HGSS's room (or, for the houses, the floor plan) beside the native map at
  3x, without grids.

Checks on the round 2 ROM:
- Interior runtime: 20 of 20 warps, including both cells of Sprout Tower's exit mat.
- Violet doors: 11 of 11.
- Porymap: 0 pixels differ on all ten interiors.

## Round 3 (owner, November 5)

- **Houses:**
  - Two beds share a room the way FireRed's S.S. Tidal cabins do it: headboards on the north
    wall, in its corners (`VioletHouse2`) or side by side (`VioletHouse3`).
  - Every house has a kitchen (Pallet's counter, stove and fridge) on a grey stone corner, the kind HGSS
    puts under its house kitchens.
  - The FireRed pieces keep their shapes and are retoned to the HGSS Violet house: its warm wood floor,
    cream wall and grey stone (`houses_native.retone`). Packed exactly: 47 colours, 38 in the sage's.
- **Lecture hall:** the gym's glass floor panels and the rails under them are gone; their squares are the
  court's stone.
- `evidence/hgss-sprout-tower-{1F,2F,3F}.png`: HGSS's own Sprout Tower floors, unconverted.

Checks on the round 3 ROM: interior runtime 20 of 20 warps, Violet doors 11 of 11, Porymap 0 pixels differ
on the lecture hall and all five houses.

## Round 4 (owner, November 5): Sprout Tower as a custom tileset

The owner approved every room but Sprout Tower and asked for a custom Gen 3 tileset converted from HGSS's,
with the pillar at Gen 3's pitch, and Gen 3's own ladders.

- `sprout_gen3.py` reads each square of HGSS's floor plan: the texture that covers it, its collision and its
  props. It gives each square the Gen 3 tile for that element (`evidence/sprout-tileset.png`).
- Each element is HGSS's own texture, decoded from the DS data (Sprout Tower's map texture set and its field
  models). HGSS draws these at 16 texels a tile, which is Gen 3's density. The conversion keeps their pixels
  and hues, widens their value range 1.3 times to Gen 3's ramps, and adds one-pixel outlines. Solid things
  are redrawn at Gen 3's pitch.
  - **Floor:** `d15_yuka01` planks. The row under the north wall is in the wall's shadow.
  - **North wall:** four rows. A trim and frieze, then HGSS's niches (`d15_wall01`) every three squares, at
    HGSS's own places. The lit ones are `d15_light_b` with `d15_light_a`'s flame, where HGSS hangs its lamps.
    On 3F, HGSS's windows (`d15_win`) take their places.
  - **Side walls:** the wall's purple top.
  - **Railings:** `d15_wall02` balusters under `d15_wall02a`'s red rail and posts.
    - An east-west run is the railing's face on its first row and its kerb (HGSS's dark band) on the second.
    - A north-south run is the rail seen from above, with the kerb's shade to its east.
  - **Lattice:** `d15_yuka03` over the drops, with its inner face on the north side.
  - **Plinth:** `d15_yuka02`'s tan slab and its three-band front.
  - **Statues:** `d15_obj02`'s Bellsprout on `d15_obj01`'s pedestal.
  - **Exit:** `d15_genkan`'s stone.
- **Ladders:** FireRed's own. The ladder up is from Mt. Moon B1F (3, 2-3). The hole with the ladder down is
  from Mt. Moon 1F (5, 6), its rim recoloured in the floor's wood.
- **Pillar** (`evidence/sprout-pillar-pitch.png`):
  - HGSS's model is a 2 x 2 post 12 tiles high, capped by a black face (`d15_pillar03`) that the DS camera
    never shows. Projected flat, it runs to the north wall and ends in that black square.
  - Gen 3 draws a floor-to-ceiling column as tall as the room's north wall, with a lit top. FireRed's Hall of
    Fame columns and Lorelei's ice columns both do this.
  - The pillar is now a post two squares wide and four rows tall (the wall's height) on its plinth. HGSS's two
    iron bands (`d15_pillar02`) sit a quarter and three quarters up. The top where the ceiling cuts it shows
    the post's own end grain.
- **Map size:** the floors are one row taller (23 x 26) for the four-row wall. Warps moved with the floor
  plan, and the Violet door's exit cells are now (11, 24) and (12, 24).
- **Packing:** colours merged within one 5-bit step. Mean channel error 0.2-0.24 against the composed floors,
  0 pixels more than 32 off. 280 tiles, 209 metatiles.
- `sprout_native.py` (round 2) stays as provenance; `rooms.py` no longer uses it.

Checks on the round 4 ROM:
- Interior runtime: 20 of 20 warps.
- Violet doors: 11 of 11.
- Porymap: 0 pixels differ on Sprout Tower 1F-3F.

## Round 4 accepted (owner, November 6)

The owner accepted Sprout Tower with two fixes:
- **Statues on the last floor row:** these now stand on their own square's foot. Their pedestals no longer
  reach into the black row below the map.
- **3F, east of the pillar:** the two statues and the railing stand one square east (map column 15 for the
  statues, 16 for the rail), mirroring the west side. The strip they left is walkway (`OWNER_MOVES` in
  `sprout_gen3.py`).

Packing: k-means into 13 banks; mean channel error 0.29-0.33, 0 pixels more than 32 off. Checks: interior
runtime 20 of 20 warps, Violet doors 11 of 11, Porymap 0 pixels differ on Sprout Tower 1F-3F.

## Pokémon Centers and Marts (owner, November 8)

The owner asked for HGSS's Center for Johto (Sinnoh's and Unova's from their own games), and for HGSS's Mart sized
to the M01 building's front, with two counters. The owner's choices:
- **Center:** HGSS's 1F with its B1F.
- **Mart's second counter:** varies by town.
- **Unova:** later, from files the owner supplies.

Every Johto town shares the Johto rooms; each town keeps its own map, NPCs and scripts.

| Room | Source | Used by | Notes |
| --- | --- | --- | --- |
| `JohtoPokemonCenter1F` | HGSS T21PC0101 as it is | Cherrygrove, Violet | nurse (8, 11) across her counter, PC (4, 8), the raised back with three counters, escalator down at (14, 17), exit (8, 19) |
| `JohtoPokemonCenterB1F` | HGSS T27PC0105 as it is | the towns' upstairs maps | three counters, the lounge, escalator up at (14, 10) |
| `JohtoMart` | HGSS T21FS0101, 18 wide | Cherrygrove, Violet | proposal; see below |
| `SinnohPokemonCenter1F` | Platinum PokemonCenter_1F | Sandgem | nurse (8, 4), PC (12, 3), escalator up at (2, 10), exit (8, 12); the basement escalator is closed (Platinum shuts it with an attendant) |
| `SinnohPokemonCenter2F` | Platinum PokemonCenter_2F | Sandgem's upstairs map | three counters, escalator down at (2, 10); the Union Room door is closed |

**The Mart (proposal).** HGSS's Mart is 14 squares wide. Four more columns of its own floor and cooler wall make it
18 wide for M01's 7-square front (HGSS's own Mart front is about half that). The standard counter stays on the
west wall, as HGSS has it. A second counter is HGSS's mirrored onto the east wall. HGSS's shelves, cafe table,
fridge and plants stand between them, with the exit at (4, 11). Each town's second counter:
- **Cherrygrove: a Discount Corner.** Poké Ball, Potion, Antidote, Paralyze Heal, at three quarters of the price
  (the money-poor first town, docs/JOHTO_ITEMS.md).
- **Violet: HGSS's own specialty clerk.** Heal Ball and Net Ball (HGSS's Violet list; its Tunnel Mail is not in
  the engine).

How it is built:
- `johto_shops.py` and `sinnoh_shops.py` hold the rooms and install them into each town's maps.
- `plat_interior.py` reads pret/pokeplatinum's `res/field` (`PLAT=` its checkout). Platinum's land data is HGSS's
  without the background-sound block, so the HGSS renderer draws it unchanged.
- Each room has its own tileset pair.
- **Mart palette:** HGSS's cooler wall carries up to 24 colours an 8 px square, more than Gen 3 allows. Those
  squares keep their 14 most representative colours, and the whole room takes one 68-colour palette, with the
  exit mat's reds kept.
- **Packing:** the Centers pack exactly or within one step (mean channel error 0.01-0.8); the Mart at 3.0. No
  pixel is more than 32 off on a channel.

Engine changes:
- **`src/shop.c`:** `ShopItemPrice()` charges three quarters while `FLAG_SHOP_DISCOUNT` (a temporary flag, alias of
  `FLAG_TEMP_1F`) is set. The Discount Corner clerk sets it around `pokemart` and clears it after.
- **`src/field_effect.c`:** an escalator whose east side is solid lets the player off to the west, as HGSS's
  Centers need (`sEscalatorWestward`). Emerald's own escalators have their east side open and are unchanged.
- **`src/apocrypha_map_proof.c`:** the test harness can enter Violet's Mart, Center and upstairs.

Checks:
- Interior runtime: 31 of 31 warps, including both escalators each way in both towns and Sandgem's.
- Town doors: Cherrygrove's seven doors and Sandgem's five lead in; Violet's doors pass 11 of 11.
- `shops_runtime.py`: the nurse answers in all three towns; both counters open their shop in both Marts. The
  Discount Corner sells the 200 Potion at 150 (`evidence/shops-in-game.png`).
- Porymap: 0 pixels differ on all eight maps.

Not done:
- The B1F and 2F attendants (Union Room, Wi-Fi, trainer card) have no NPCs or links.
- Unova's Center waits on the owner's files.
- Violet's standard Mart list sells Escape Rope at ₽0, the engine's price for it.

## Checks

| Check | Result |
| --- | --- |
| `make` | builds |
| Porymap 6.3.1 (its own loader and renderer, headless) | all ten interiors and Violet City export with 0 pixels differing from the native decode |
| Interior runtime (`violet_interiors/runtime.py`): every warp in every interior, from the cell next to it (or standing on the exit mat), lands on its destination | 19 of 19: Sprout Tower's exit and all ten ladder cells across three floors, each other room's exit |
| Violet runtime (`violet_city/runtime.py`): every door in and back out | 11 of 11; 48 frames outside the door openings at least 99.7% identical to the decode |
| Cherrygrove town runtime on the same ROM | passes |

## Not done

- No NPCs or scenes yet: sages, Elder Li, the instructors, the library seeds, the practicum trainers,
  the house residents (CHAPTER2_SCENES_SPEC.md is the implementation pass). The rooms leave space for them.
- Sprout Tower 3F's top floor is as HGSS has it; the swaying pillar does not sway.
- Bookshelf behaviour is on the university's back-wall stacks only.
- Owner visual acceptance.

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation from the game's data).
