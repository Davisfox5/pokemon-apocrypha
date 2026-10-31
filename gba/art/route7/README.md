# Route 7: Celadon to Saffron

Status: **built in the engine, round 2 after the owner's review (2026-10-31), owner visual review
pending.** Round 2: the Kanto gatehouse (option B, `evidence/gate-options.png`: HGSS's gate in
FireRed's Kanto gatehouse metal and yellow brick); Celadon's lane ends where the paving meets the
dirt road, and the road is HGSS's four rows again; every rock edge takes its edge piece (no rock top
ends in grass on a hard line); the east ledge is FireRed's top, middle and corner pieces. The plot (`evidence/plan.png`) was
approved on 2026-10-30 with one change: the Underground Path is unsealed (its inside, "bars and
shops", comes later), so HGSS's "sealed" notice and locked-door sign are gone and its door stays
solid until the inside is built. Engine branch `claude/route-7` on `claude/celadon-city`.

## What was built

- `KantoRoute7` (Kanto 16, `MAPSEC_ROUTE_7`, 33 x 32), from HGSS's ledger in Gen 3 elements
  (`compose.py`): FireRed's grass, HGSS's road01 at 1:1 with FireRed's path edges and its
  pebbles, Celadon's paving and two-lane cycleway run on from the city to the paving's end, whole-cell
  tall grass (G15), FRLG ledges and FRLG rock in HGSS's cliff ramp (the step down from Celadon, both
  outcrops), Cherrygrove's tree on Celadon's staggered lattice, HGSS's gate (247) in FireRed's Kanto
  gatehouse materials, Underground Path entrance (339) and notice board (31) at 45 degrees. Evidence: `evidence/review.png` (HGSS beside native, coordinate grid),
  `review-seam.png`, `compose-2x.png`.
- Streamed with Celadon as one 97 x 52 world (`world.py`; engine `celadon_view.c`): either map's
  view shows the other's real art across the connection, and the cache and banks carry on when the
  player crosses (`LoadMapFromCameraTransition` skips the tileset reload for a streamed map).
  32 palettes, the worst step 13, all banked; the busiest view 684 of 956 glyph slots.
- `KantoRoute7Gatehouse` (Kanto 17): FireRed's Route 7 gate room, every pixel exact
  (`gate_room.py`); its east arrow lands on Saffron's west gate (8, 27), opened natively (a copy
  of its metatile with FireRed's west arrow behaviour, metatile 263).
- FireRed's Underground Path sign on the board; the wild table from KANTO_BATTLES' R07 row
  (`install7.WILD`: Rattata, Spearow, Growlithe; Raticate 4%, Shinx 4%, Plusle and Minun 1%; FireRed's
  rate 21).

## Adaptations from HGSS

- Celadon's lane runs on over x 0-4 (rows 18-19) and ends with the paving; the road beyond is HGSS's
  four rows (round 1 widened it to carry the lane to the gate; the owner had the lane stop).
- HGSS's x 0-3 row 14 is woods: Celadon's woods at x 60-63 run on there.
- HGSS's gate warps sit on its wall cell (25, 16-17); the Gen 3 sprite fills that cell, so the four
  road cells in front of it, (24, 15-18), are east arrow warps, as FireRed's Route 7 does it.
- The gate is HGSS's model in FireRed's Kanto gatehouse materials (owner's choice), not HGSS's teal.
- The notice board a row south, (12, 25): at (12, 24) its top covered the entrance's foot.
- The gate overhangs HGSS's block by three quarters of a cell: the map is 33 columns.
- HGSS's pale lawn in front of the entrance is FireRed's grass, as Celadon's lawns are.

## Checks

- Audit (`check7.py`, `evidence/engine/audit.json`): tables byte for byte; budgets; the walkable
  cells against HGSS's, 0 unexplained of 1,024; traversal on both maps; every route cell reached
  from Celadon's Center door; warps both ways through the gate room; connections; the seam; scope.
- Headless mGBA (`runtime7.py`, `evidence/engine/gameplay/`, `ingame-montage.png`): 48 frames,
  0 map-layer pixels wrong against the decode, across the seam both ways, along the road, in the
  gate room and at Saffron's west gate; walk-behind (a tree, the entrance) and in-front depth; the
  south ledge jumps and neither ledge climbs; the entrance's door holds; the sign reads; ordinary
  save on the route, cold reload, Continue.
- Porymap 6.3.1 round trip (`porymap7.py`): the export equals the stand-in decode (0 pixels
  differ); saving changes no Route 7 or Celadon file.
- Pixels: the route 99.3% exact in 5-bit colour (the trees' shared palettes); Celadon's own decode
  differs from round 6 in 2,583 of 851,968 pixels, from the shared tree palettes being repacked.

## Limits

- Tall grass covers the player's feet with Emerald's own grass sprite (the engine's field effect).
- Not built: the gate guard and his line, trainers, the Mental Herb and the hidden item (flags),
  the cafe's honey, the Underground Path's inside, music beyond FireRed's.
- Night tint and weather on the route are not checked.

## Story brief

- DESIGN.md (Chapter 6, "The Celadon Path"): "Route 7 is short — a handful of trainers, the
  western gate, and Celadon opens up."
- CHAPTER5_SCENES_SPEC 5.5c: Saffron's gate guard sends the player west ("that one's open"; the
  long way round past Celadon is blocked).
- KANTO_BATTLES: Route 7 is trainer-light, lv 17-19; wild R07 lv 16-19: Rattata (Raticate rare),
  Spearow, Growlithe, rare Plusle, Minun, Shinx. Trainers are not designed.
- KANTO_ITEMS: one optional hidden item.
- DESIGN.md's cafe quest names "a rare honey from Route 7" as one option; the scene spec sources
  the ingredient from the market and gardens.
- The approved Celadon plan runs its cycleway "from Route 7 (east, to Saffron)".

## Other agents' work

No Route 7 in either repo's PRs or branches. The Johto route branches (`claude/route-42` to
`claude/route-46`) carry owner rules that apply here: whole-cell tall grass (G15), woods tight
round gates (Route 36's gate surround), no custom rocks, every height step its own wall.

## HGSS source

Map header 15 (`MAP_ROUTE_7`, zone R07), area bank 15 (Celadon's), one 32 x 32 block (land data
169), decoded by `tools/gba/maps/route7/hgss_source.py` from pret/pokeheartgold `9d8b7591f`. Events:
two warps at (25, 16) and (25, 17) into `MAP_ROUTE_7_SAFFRON_GATEHOUSE`; the Celadon Police
notice at (12, 24) ("the Underground Path has been sealed indefinitely"); the locked door at
(13, 23); the Mental Herb ball at (15, 2). The east neighbour is Saffron (header 59).

## Ledger

| HGSS element | Cells | Gen 3 element |
| --- | --- | --- |
| Celadon's level (height 3), its road | x 0-3 | Celadon's paving and cycleway at their own width |
| Terrace step (wall01, slope) | x 4 | one FRLG rock terrace in HGSS's ramp, the road passing through |
| Road (road01) | rows 15-18, x 5-25 | HGSS's road texture at 1:1, widened to row 19 for the lane |
| Woods (tree01) | most of the map | Cherrygrove's standard tree, staggered rows |
| Tall grass (egrass) | x 15-23, rows 3-13 | whole-cell tall grass (G15), wild encounters |
| Ledges (allpeak) | row 13, row 21, x 15 rows 10-13 | FRLG ledges, jumping as HGSS's behaviours say |
| Rock outcrops (cliff01) | NE x 21-27 rows 0-5; SW x 5-11 rows 20-31 | FRLG General mountain set in HGSS's cliff ramp, one terrace |
| Saffron gate (model 247) | x 25.25-32.75, rows 14-20 | HGSS's model at 45 degrees; the map is 33 cells wide for its east wall |
| Underground Path entrance (339) | x 12-16, rows 21-23 | HGSS's model at 45 degrees, door solid until its inside is built |
| Notice board (31) | (12, 24) | HGSS's model at 45 degrees, sign event |
| Lawn (grass01gs) | x 12-20, rows 23-27 | Celadon's lawn with its smooth edge |

Uncertain: HGSS's decoded collision blocks the terrace step x 4 on the road rows, the only way
between Celadon and the route; read as HGSS's walkable slope.

## Change list

1. Celadon's main road comes on at its own width (3 rows of paving, the 2-lane cycleway): the
   approved Celadon plan; AGENTS.md "Fit, don't drop on".
2. HGSS's terrace step at x 4 stays, as Gen 3 rock north and south of the road.
3. HGSS's road runs on to the gate with the cycleway beside it as its own painted lane.
4. The Saffron gate, HGSS's model on its lot, woods tight round it, the road and lane taken in at
   its west door. The door warps into a new gatehouse room (FireRed's Route 7 gate room, as a new
   Emerald map); its east exit lands at Saffron's west gate (8, 27), which opens (Saffron's native
   files: the warp and the door cell).
5. The Underground Path entrance on HGSS's lot. Owner, 2026-10-30: unsealed, its inside to come
   later; HGSS's "sealed" notice and locked-door sign left out, FireRed's Underground Path sign on
   the board, the door solid until the inside exists.
6. Whole-cell tall grass with KANTO_BATTLES' R07 table.
7. Cherrygrove's trees, FRLG ledges, FRLG rock in HGSS's ramp.
8. A map connection to Celadon (Route 7 row = Celadon row - 1). Gen 3 draws a connected map with
   the current map's tiles, and Celadon's map holds stand-in tiles, so Route 7 joins Celadon's
   streamer and each side draws the other's real art across the seam. No connection to Saffron:
   the gate room is the way through, as in FireRed, whose Saffron already draws the gate.

Displaced warps: none. HGSS's two warps go to the gate room; FireRed's `Route7_Frlg` maps are
untouched.

Out of this pass: the gate guard and his line, trainers, the Mental Herb and the hidden item
(flags), the cafe's honey, the Underground Path's inside.
