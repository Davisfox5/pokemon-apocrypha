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
- **Lake, islet**: its teal top read as a pool of water round the tree. It is grass, in the islet's own
  greens (its palette is shared with the west gatehouse's teal, which stays). Its east half is its west
  half mirrored (it was all but symmetric), so every east tile is a flipped west one: that frees the door
  frames' slots (below).
- Unchanged: Sprout Tower, the university and clock tower, the lecture hall, the practice court, the
  approved C06 Center and M01 Mart, the houses, the west gatehouse, the forests (already the overlapping
  lattice), bridges, lanterns, signs, ducks.

## Tilesets

Violet is the only map on `VioletCityPrimary` and `VioletCity`, so the installer (`tools/gba/maps/violet_city`)
lays both out anew from the town's two decoded layers: each quadrant takes the bank that holds its colours,
identical quadrants share one tile in any flip, identical cells one metatile. The 13 banks are Violet's,
with colours its art no longer draws freed for the new ones.

- 1,008 of 1,008 tiles (512 primary, 496 secondary), 652 metatiles.
- Secondary slots 496-511 (tiles 1008-1023) stay empty: `field_door.c` draws door frames there, so Violet's
  doors can animate. The installer always reserves them.
- Where both of a cell's layers draw below the player, a quadrant one bank can draw takes one tile, not
  two (4,022 quadrants).
- **Folds**: a new texture tile may take an existing one up to 3 px away (742 pixels in 298 cells), each
  moved pixel another tone of its own texture. Lawn, cobble, water and canopy move anywhere within
  themselves; the verge, the bank and the landing's stone only inside, never their lines or edges. Building
  art never moves.

## Checks

| Check | Result |
| --- | --- |
| Every cell draws as composed (`violet.py --install`) | 0 pixels differ outside the folds; every fold is a tone of its own texture |
| Collision, elevation, behaviour and layer type | unchanged on every cell |
| Porymap 6.3.1 export vs native decode | 0 pixels differ (Violet City, Route 36, Cherrygrove) |
| Runtime (`runtime.py`): into the east gate, into the west gate, the north road over both bridges and the landing to the main street (30 steps), the lake blocking on foot | passes; 34 frames, every one at least 99.7% identical to the decode outside the player (`evidence/runtime-summary.json`, `evidence/runtime-walk.png`) |
| Cherrygrove town runtime on the same ROM | passes |

## Limits

- The tile budget is spent: the 16 door-frame slots are free, no others. Where the tiles go (exclusive to
  each part): Sprout Tower 236, C06 Center 94, lecture hall 82, university and clock tower 81, M01 Mart 77,
  lake water, banks and ducks 55, the streets and lawn 35. Houses share almost everything.
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
