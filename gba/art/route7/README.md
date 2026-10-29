# Route 7: Celadon to Saffron

Status: **plan for the owner's call** (AGENTS.md, "Planning a new town: the change plot"). Nothing
is built yet. The plot is `evidence/plan.png`; HGSS's own models at 45 degrees are
`evidence/art-samples.png`.

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
| Underground Path entrance (339) | x 12-16, rows 21-23 | HGSS's model at 45 degrees, door solid |
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
5. The Underground Path entrance, sealed as HGSS has it, with HGSS's notice and locked-door sign
   (CHAPTER5 5.5c: the long way round is blocked).
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
