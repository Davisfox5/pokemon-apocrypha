# Violet City, cleaned up to AGENTS.md's native visual rules

2026-10-29, engine branch `claude/routes-30-31-catalog` (PR #39). Starting point: the newest Violet City,
ported unchanged from `codex/johto-editor-consolidation` 8eb43845f6 (engine 42cd9d1a53, with Route 36 and the
west gate; both decode pixel for pixel as that branch's own renders). Checked against HGSS Violet rendered
from pokeheartgold's own data. Every cell keeps its collision, elevation, behaviour and layer type.

![before and after](evidence/review-fixes.png)

## What changed

- **Streets**: the cobble ran square into the lawn behind a 1 px tan line. HGSS runs a dirt verge between
  cobble and lawn and rounds its corners. The cobble now stops 8 px short of the lawn and the Johto port's
  own dirt tones run between (the lawn's shade line, the painter's sand, a dark line on the cobble), the
  corners rounded (3 px). Against buildings, bridges, signs and lanterns the cobble runs right up to them.
  The street's shape is read by cells, so a building's outline doesn't cut it up.
- **Lake, north bank**: HGSS drops from the lawn to the water by an earth bank on the lake's north sides.
  Violet had a 1 px line. It takes HGSS's own bank (`source/hgss/lake-bank.png`): the light face on the
  lawn's last pixels, the dark foot over the water's first, a deeper blue below.
- **Lake, landing**: Violet's landing is HGSS's own size and place (x31-42, rows 23-28). The flat slab with a
  1 px outline takes HGSS's 12 px stone-block border round its dotted floor (`source/hgss/landing.png`, the
  ground layer, so no bridge or lantern), in Violet's own grey ramp, and the deeper ring HGSS draws in the
  water round it. The walkways stay open where the bridges land; the lanterns stay.
- **Sprout Tower** (owner requests, October 31): the port drew it near-black, dim purple tiers over a flat
  black wall with dull gold shapes. HGSS's tower is a bright blue-violet roof over a carved wooden front in
  a pale stone frame. The roof keeps every pixel's shape and takes a lighter ramp with more step between
  tones; the black eave lines stay for a crisp edge and lone speckle pixels take their neighbours' tone. The
  front is HGSS's own (`source/hgss/tower-front.png`): the stone frame, the carved beam, barred windows over
  tan sills and oval panels, the door with its gold panels, fitted to the tower's 24 px wall by leaving out
  repeated rows of plain wood and mirrored about the door (a figure standing at the door in HGSS's render
  is left out). The hall below is cut from the tower, so the two match.
- **University** (owner request, October 30): the port's western hall (slate roof, cream walls, clock
  tower, 20 x 9 cells at x47-66) did not match Violet's Johto style. It is now a Johto hall in Sprout
  Tower's own materials, 15 x 8 cells at x50-64 on the same base line: the tower's two lower roof tiers
  stretched by repeating their middle columns, its top tier as a raised centre roof, the tower's front with
  three window bays each side of its door. The pieces move by whole
  cells (or 8 px columns inside them) with both layers, so they draw with the tower's own tiles. The street
  runs up to the door. The cells it gave back are walkable lawn; the hall's cells are blocked. The sign
  at (53, 43) stays.
- Unchanged: the islet (as the port has it, owner's choice), the lecture hall, the practice court, the
  approved C06 Center and M01 Mart, the houses, the west gatehouse, the forests (already the overlapping
  lattice), bridges, lanterns, signs, ducks.

## Tilesets

Violet is the only map on `VioletCityPrimary` and `VioletCity`, so the installer (`tools/gba/maps/violet_city`)
lays both out anew from the town's two decoded layers: each quadrant takes the bank that holds its colours,
identical quadrants share one tile in any flip, identical cells one metatile. The 13 banks are Violet's,
with colours its art no longer draws freed for the new ones.

- 989 of 1,008 tiles (512 primary, 477 secondary), 657 metatiles. The hall saves 39 tiles over the port's
  university (1,048 against 1,009 before folds).
- Secondary slots 496-511 (tiles 1008-1023) stay empty: `field_door.c` draws door frames there, so Violet's
  doors can animate. The installer always reserves them.
- Where both of a cell's layers draw below the player, a quadrant one bank can draw takes one tile, not
  two (4,022 quadrants).
- **Folds**: none at the current budget. When tiles run short the installer lets a new texture tile take an
  existing one a few px away, each moved pixel another tone of its own texture. Lawn, cobble, water and
  canopy move anywhere within themselves; the verge, the bank and the landing's stone only inside, never
  their lines or edges. Building art never moves.

## Checks

| Check | Result |
| --- | --- |
| Every cell draws as composed (`violet.py --install`) | 0 pixels differ outside the folds; every fold is a tone of its own texture |
| Collision, elevation, behaviour and layer type | unchanged on every cell outside the university's old and new footprint (154 cells: the hall blocked, the rest walkable lawn) |
| Porymap 6.3.1 export vs native decode | 0 pixels differ (Violet City, Route 36, Cherrygrove) |
| Runtime (`runtime.py`): into the east gate, into the west gate, the north road over both bridges and the landing to the main street (30 steps), the lake blocking on foot, the hall blocking at its door, the old west wing's lawn walkable | passes; 36 frames, every one at least 99.7% identical to the decode outside the player (`evidence/runtime-summary.json`, `evidence/runtime-walk.png`, `evidence/runtime-hall.png`) |
| Cherrygrove town runtime on the same ROM | passes |

## Limits

- 19 tiles free beyond the 16 door-frame slots. The largest users before the hall (exclusive tiles): Sprout
  Tower 236, C06 Center 94, lecture hall 82, the port university 81, M01 Mart 77, lake water, banks and
  ducks 55, islet 55.
- Interiors and onward routes are as the source branch left them.
- Owner visual acceptance.

## Reproduce

```sh
python3 tools/gba/maps/violet_city/hgss_sources.py PATH/TO/pokeheartgold   # source/hgss/
python3 tools/gba/maps/violet_city/violet.py ENGINE --preview              # evidence/preview.png, before-after.png
python3 tools/gba/maps/violet_city/violet.py ENGINE --install              # both tilesets and the map
```

Every run starts from Violet at the engine's port commit (`base.py` BASE_REV). Treat the tools as
provenance: once the owner edits Violet in Porymap, edit the native files and don't replay the generator.
