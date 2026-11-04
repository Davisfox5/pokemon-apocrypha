# Route 32, built by the Route 29/30 catalog process

November 4, 2026. A fresh Route 32 (engine map `JohtoRoute32`), Violet City to the Union Cave forecourt. The owner
reviewed every earlier Route 32 (Codex's #8 and #17, Claude's native cleanup and its variant branches) and kept
none. This one is built the way the owner accepted for Route 29 and Routes 30/31: HGSS's own map data rendered
1:1, a square-by-square trace, catalog art, the Cherrygrove painter, an exact pack, seam checks and a headless
mGBA run. HGSS only. Engine branch `claude/route-32`, stacked on `claude/routes-30-31-catalog` (PR #39), which
holds Violet City. Visual acceptance stays with the owner.

It follows [the map reconstruction workflow](../../../docs/GBA_MAP_RECONSTRUCTION.md).

## The method

1. **Reference** (`reference.py`, `hgss_render.py`, `hgss_events.py`): HGSS Route 32 (EVERYWHERE matrix cells
   (14, 9..13), land_data, zone events R32) rendered at 16 px per cell. Native cell = HGSS cell + (0, 6); the map
   is 32 x 166. Violet City is north (matrix (14, 8)), Route 33 south (matrix (14, 14)), the open sea east.
   - Six rows north continue Violet's south edge: the lawn below its last tree row and its cobble road (Violet row
     71). Rows 0-4 are Violet's own metatiles, placed by id; row 5 is the same lawn drawn as route art, under the
     crowns of HGSS's first tree row. Violet column x is Route 32 column x - 4, so Violet's road comes down onto
     columns 18-20, inside HGSS's open north edge (columns 14-25).
2. **Trees**: an integer program places 325 non-overlapping 2x2 roots on HGSS's woods cells; each is the
   Cherrygrove tree (T01 with the town's contact shadow, Route 30's cut), crown one row north of its root.
3. **Ground**: the approved Cherrygrove/Route 36 painter on an 8 px lawn/road grid read from HGSS's flat ground
   colours, with Cherrygrove's own road block (at the engine's base revision).
4. **Terrain**:
   - Rock: Blackthorn's FRLG terraces in the Johto rock ramp (`rock.py`, Route 30's), one terrace per HGSS height
     layer, the soft grass fringe where a rock top meets grass at its height. The sea is one level, below every
     rock face beside it.
   - The three small rock islands in the sea take one terrace each: HGSS's mixed heights broke the FRLG faces into
     fragments, and HGSS's own islet art costs about 120 tiles the map does not have.
   - Stairs, in HGSS's own direction (its decoded height slope across each flight): the flight through the wall
     at (9-10, 74-76) falls from west to east (height 2.9 to 1.2) and takes Route 36's plank flight, its cheeks in
     the Johto rock ramp (Route 30's east-west flight); the flight at (6-8, 111-112) falls from north to south (2.9
     to 1.2) and takes Route 30's grey treads.
   - Ledges: L11/L12/L13 on the jump-south runs, turned a quarter for the jump-east run, corners joined (Route 29's).
5. **Sea and pier** (`assemble.py` `sea_and_pier`): HGSS's own pixels from the flat decode. Every sea cell takes the
   HGSS sea cell with the same water/land neighbours (open water: and the same 32 px texture phase); every pier cell
   the HGSS pier cell with the same pier neighbours. Land pixels at a shore cell's edge take the open sea's texture,
   so no land is copied into the water; HGSS's shore rim and foam (`pond_line`) stay in the water cells. Where the
   rim reaches into the land cells beside the sea it is left out: drawing it there joined the sea's and the land's
   palettes and the route no longer fit 13 palettes. One exemplar per configuration keeps the tile count small.
6. **Boulders**: HGSS's sea boulders and land boulders as sprites at HGSS's own positions (16 px grid), from HGSS's
   own render, one exemplar each. The land boulders stand on HGSS's own sand. One cell HGSS blocks beside a sea boulder,
   (28, 99), shows open water: the boulder's sprite stands in the next cell.
7. **Union Cave mouth**: HGSS's cavehole texture from its own render, over the rock face.
8. **Catalog art**, byte for byte with hashes (`codex/violet-city` de5d8cfb): G15 on all 417 tall-grass cells,
   P14 on the three route signs, G02 (the owner-approved HGSS side gate, Route 31's) on the Ruins of Alph gatehouse
   with its stairs on HGSS's gate warps, C06 (the owner-approved Center) with its door on HGSS's Center door.
9. **Magnet Train viaduct**: Route 32's land_data carries only the viaduct's shadow (a translucent band across HGSS
   rows 82.5-87.5); the viaduct model is not in the map data. The deck is drawn on that footprint above the player in
   HGSS's own Magnet Train track textures (`a/2/3/3` model 0: `senro_base`, `senro_line`), in Violet palette 11's
   greys, with a guard rail along each edge. Its look is a proposal; its place is HGSS's.
10. **Local art from HGSS** (`source/local-art/`): flowers and light lawn patches, cell by cell from one exemplar per
    texture and 32 px phase. Tone reductions are in `reductions.json`.
11. **Pack** (`pack.py`): exact, 0 native pixels differ from the assembled art.
    - Route 32 has a primary of its own (`route32`) and a secondary (`route32_hgss`): Violet is on its own primary,
      and PR #39 reloads a primary and redraws the view on a crossing.
    - Violet's metatiles in the padding, and every one a player on the padding's road can see in Violet (its rows
      66-71), sit at Violet's own ids with Violet's tiles, in banks that take Violet's palettes 0, 1, 3 and 11.
    - The 21-colour masters (G02, C06) are drawn across both layers where the player never walks in front of them:
      their six least common colours in the lower tile, the rest in the upper, so each master's upper tiles fit one
      palette. The picture is the same pixel for pixel.
    - Palettes from the exact bank program (HiGHS), cached in `source/pack/banks-cache.json`.
12. **Events**: the three signs with HGSS's text; the Center door leads into `Route32PokemonCenter` (Violet's Center
    interior, retargeted, with its upstairs); item balls for HGSS's Repel, Great Ball and Shell Bell; hidden Heart
    Scale, Great Ball and Super Potion; the cuttable tree; the breakable rock. Flags 0x26A-0x26F
    (`FLAG_ITEM_APOC_ROUTE32_*`, `FLAG_HIDDEN_ITEM_APOC_ROUTE32_*`).

## Seams

- **Violet City (north, offset -4)**: Violet draws the padding as itself; Route 32 draws Violet's visible cells with
  Violet's tiles at Violet's ids. `seams.py` checks every cell either side can see: clean both ways.
- Violet City's map now has the matching `down` connection (offset 4).

## Review

- [Whole map](evidence/review/whole.png): HGSS left, native right.
- [Sheets](evidence/review/): HGSS left, native right, numbered cells.
- [Gameplay](evidence/review/gameplay.png): headless mGBA frames.
- [Material grid over HGSS](evidence/trace/) and the [ledger](source/trace/material-grid.txt).

## Checks

| Check | Result |
| --- | --- |
| Material audit, every HGSS cell (`evidence/review/material-audit.json`) | 5,113 match, 6 declared (gatehouse base row), 1 flagged: (28, 99), a cell HGSS blocks beside a boulder whose sprite stands in the next cell |
| Native decode vs assembled art (`evidence/pack/pack.json`) | 0 pixels differ |
| Walkable area vs HGSS (`source/pack/traversal.json`) | HGSS's 1,544 cells; native adds only the Center door cell |
| Budget | 985 of 1,024 tiles; 480 primary and 172 secondary metatiles; 13 palettes; 24 Violet metatiles pinned |
| Rock faces (`evidence/review/rock-face-audit.json`): every HGSS rock cell with a face against the native terrace in that direction | 717 drop as HGSS's do, 66 face another rock cell, 31 at the map edge, 2 do not: (9, 71) and (10, 72), the corner above the east-west stairs, where HGSS's mesh has no material and the cells are solid rock |
| Stair direction from HGSS's decoded slope | (9-10, 74-76) east-west (slope -0.056 in x), (6-8, 111-112) north-south (-0.061 in y): both placed that way |
| Seams, both directions, every cell a player can see (`seams.py`) | clean: Violet City |
| ROM build | passes; sha256 in `evidence/review/hashes.json` |
| Headless mGBA (`evidence/review/runtime-summary.json`) | all three phases exit 0 |

The headless run covers:

- Violet City to Route 32 to the Union Cave forecourt and back to Violet on foot, every step checked against the
  predicted route (415 steps).
- A walking tour into every area the route reaches on foot (693 steps), under the viaduct included.
- The Center door into Route 32's Center and back out.
- All four ledge runs jump and refuse the climb back.
- The gatehouse doorway, the cave mouth, the cuttable tree, the breakable rock, the signs and the sea block.
- Six tall-grass steps with an empty party start no battle.
- The signs read. The three item balls give their items, set their flags and are gone. Two hidden items are found
  once. The flags survive an ordinary save, a cold reload and title Continue.

Each frame is compared with the native decode at the camera position, Violet included. 60 of 76 frames are identical;
the rest differ only where something covers the map (dialogue boxes, the map-name popup, the Continue menu).

## Declared adaptations

- **North padding.** Six rows of Violet's lawn and road between Violet and HGSS row 0, for the seam.
- **Gatehouse base row.** HGSS's gatehouse footprint reaches HGSS row 8; G02 is seven rows, so row 8 under its base is
  lawn and stays solid as HGSS's footprint (Route 31's adaptation).
- **Doors.** The Ruins of Alph gatehouse doorway and the Union Cave mouth stay shut: neither interior is on this
  branch (Union Cave is on Codex's branches, against the previous Route 32). The Center door is a non-animated door:
  no door animation is registered for Route 32's tilesets.
- **Route 33.** HGSS's south edge opens onto Route 33; no Route 33 is on this branch, so there is no south connection.
- **Viaduct.** Drawn from HGSS's track textures on HGSS's shadow footprint (above).
- **North-south stairs.** HGSS draws the flight at (6-8, 111-112) in tan wood; it takes the grey treads Routes 30 and 31
  established for north-south flights.
- **Shore rim on land.** HGSS's rim reaches a few pixels into the land cells beside the sea; it is drawn only in the
  water cells (palette budget, above).
- **Islets.** One terrace each (above).
- **Items.** HGSS's item balls and hidden items are placed with HGSS's items; JOHTO_ITEMS.md does not list Route 32's
  field items yet, so they are a proposal for the owner. HGSS's TM09 ball is left out (the TM list is the project's own).
- **Not placed:** trainers, the fisherman and other NPCs (campaign work).
- **Woods.** Woods cells under a crown stay solid, as HGSS has them.

## Not verified

- No Porymap round trip: Porymap is not installed in this environment.
- `apocrypha build` CI cannot run: GitHub Actions is disabled on the engine repository.
- The Heart Scale's rock is reachable only by Surf, which the headless run does not use.
- Owner visual acceptance.

## Reproduce

```sh
python3 tools/gba/maps/route32_catalog/hgss_render.py PHG gba/art/route32-catalog/source/hgss
python3 tools/gba/maps/route32_catalog/hgss_events.py PHG gba/art/route32-catalog/source/hgss-events.json
python3 tools/gba/maps/route32_catalog/reference.py PHG
python3 tools/gba/maps/route32_catalog/assemble.py PHG CATALOG ENGINE      # CATALOG: checkout of codex/violet-city de5d8cfb
python3 tools/gba/maps/route32_catalog/pack.py ENGINE --install            # --count: tile count only
python3 tools/gba/maps/route32_catalog/seams.py ENGINE
make -C ENGINE -j8
MGBA_FLAGS=... python3 tools/gba/maps/route32_catalog/runtime.py ENGINE OUT
python3 tools/gba/maps/route32_catalog/review.py 32 ENGINE OUT
```

PHG is a pokeheartgold checkout with its archives; ENGINE is `claude/route-32`. These tools are provenance: once
the owner edits the map in Porymap, edit the native files and do not replay the generator over them.
