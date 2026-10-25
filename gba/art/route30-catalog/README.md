# Route 30, rebuilt by the Mahogany / Route 43 process

October 25, 2026. Route 30 (engine map `CherrygroveRoute30Approach`), Cherrygrove City to Route 31, built
the way the owner accepted for Route 29 (PR #34): HGSS's own map data rendered 1:1, a square-by-square
trace, catalog art, the Cherrygrove painter, an exact pack, seam checks and a headless mGBA run. HGSS only.
Built together with [Route 31](../route31-catalog/README.md), which shares its north seam. Engine branch
`claude/routes-30-31-catalog`, draft PR #39 against `apocrypha`. Visual acceptance stays with the owner.

## The method

1. **Reference** (`reference.py`, `hgss_render.py`, `hgss_events.py`): HGSS Route 30 (EVERYWHERE matrix cells
   (17, 9..11), land_data, zone events R30) rendered at 16 px per cell. Native cell = HGSS cell + (5, 2);
   the map is 37x104.
   - Five columns west are woods beyond HGSS's west wall, standing at the wall's top. They put HGSS's
     south road on Cherrygrove's road (connection offset 35, unchanged), and HGSS's woods east of the road
     on the column pairs of Cherrygrove's forest band below, so the trees stand in the band's columns. The
     padding's own trees take the band's even columns.
   - Six rows south are Cherrygrove's own north forest band (its rows 0-2, twice, as Cherrygrove's primary
     metatiles), so Cherrygrove's camera sees its own cells across the seam. The band's two blossom trees take
     the green tree beside them.
   - Two rows north repeat HGSS row 0 with its stairs as road (see Seams).
   - The west wall runs on through the band into Cherrygrove, where the town's east-west cliff turns north
     to meet it (see Cherrygrove's wall, below).
2. **Trees**: an integer program places 360 non-overlapping 2x2 roots on HGSS's woods cells; each is the
   Cherrygrove tree (T01 plus the town's contact shadow), crown one row north of its root.
3. **Ground** (`assemble.py`): the approved Cherrygrove/Route 36 painter on an 8 px lawn/road grid read from
   HGSS's flat ground colours, at Cherrygrove's texture phase.
   - HGSS's road keeps the painter's wavy edge, as on the rest of the route, all the way to the band.
   - Its straight south section sits one quadrant east, on Cherrygrove's road columns, so it runs into the
     town's road without a step.
   - Only the last cell before the band takes the town kit's straight edge, which the band continues.
4. **Terrain**, drawn into the bottom layer:
   - Rock: Blackthorn's FRLG rock terraces (`rock.py`), one terrace per HGSS height layer. The woods
     padding west of HGSS's west wall stands at the wall's top, so the wall keeps only its east face, as
     at HGSS's map edge, and the north rock runs to the edge without turning a corner.
   - Ponds: Route 43's natural pond (HGSS freshwater texture, rough banks) on both.
   - Stairs: the Johto stair pieces already built from HGSS's templates (`stair_pieces.py`), on HGSS's
     stair cells:
     - North-south flights take the earlier Route 30's grey treads, as Route 32 and the earlier Route 31 draw
       them: engine 4f01430776, the editor library's "04 Stairs | middle" prefab.
     - The east-west flight through the column-17 wall takes Route 36's plank flight: engine 1643f58a48,
       "04 Stairs | East-west flight 1". Its rock cheeks take this wall's rock ramp.
     - For two cells above and below each north-south flight, the road stands on the flight's own columns
       with a straight edge, so both dirt paths meet the treads end to end.
5. **Catalog art**, byte for byte with hashes (`codex/violet-city` de5d8cfb): G15 on all 338 tall-grass cells,
   L11/L12/L13 on the 32 jump-south ledge cells, P14 on the route sign, P16 on the Trainer Tips board.
6. **Houses** (`buildings.py`, Blackthorn's method, `tools/gba/maps/blackthorn/sprites.py` on
   `claude/blackthorn-city`):
   - HGSS's own models and textures: Mr. Pokemon's house (model 53) and the Apricorn house (37), each with
     its door (50) at HGSS's own offset, plus Mr. Pokemon's mailbox (30).
   - They're rendered at the owner-locked C06 Center's angle (orthographic at 38 degrees, 16 px per tile up
     the screen, squeezed to the footprint), so roofs and doors read like the Center, the Mart and
     Blackthorn's houses.
   - Then finished as Gen 3 art: each house in 14 colours of its own plus C06's outline colour (the mailbox
     shares its house's), and tiles that differ by a one-pixel edge folded together.
   - Each door sits on HGSS's door cell, its sprite's bottom on the base row. HGSS's contact shadow stays in
     the ground from the door row down.
   - Contact sheet: `evidence/assemble/buildings.png`.
7. **Local art** cut from HGSS's render: the fences, 4 tones; flower heads, 6; light lawn patches, 3
   (`source/local-art/reductions.json`).
8. **Pack** (`pair_pack.py`, joint with Route 31): exact, 0 native pixels differ from the assembled art.
   - Primary `cherrygrove_route30`: CherrygrovePrimary with palettes 0 and 3 and every tile Cherrygrove's
     visible cells and the band use kept (those cells draw from nothing else but bank 10); palettes 1, 2, 4
     and 5 and 180 of its 435 free tile slots hold route art.
   - Secondary `route30_hgss`: 512 tiles, 435 metatiles (596-597 are the wall cells Cherrygrove also
     defines), banks 6-11. Bank 10 is Cherrygrove's own blossom palette, which Cherrygrove's visible trees
     need.
9. **Events**: the four signs on HGSS's cells with HGSS's text; the Antidote and Potion balls
   (`FLAG_ITEM_APOC_ROUTE30_ANTIDOTE` 0x265, `FLAG_ITEM_APOC_ROUTE30_POTION` 0x266); the hidden Potion near the
   Trainer Tips board (`FLAG_HIDDEN_ITEM_APOC_ROUTE30_POTION` 0x267); the cuttable tree.

## Cherrygrove's cliff and wall

Johto's rock is the owner-locked Mahogany Town's: Blackthorn's FRLG terraces in the HGSS rock ramp
(Blackthorn's `cliff01gs`), the same seven colours on Route 30, Route 43 and Blackthorn. Cherrygrove's sea
cliff was the older warm set, so it didn't match the route's wall in colour or shape. `cherrygrove_wall.py`
(run after the pack) redraws it in Johto's rock and turns it north into the route's wall, as HGSS has it
(HGSS Cherrygrove, matrix (16, 12), rendered from its own data: its sea cliff turns north at its columns
32-33 and runs up into Route 30).

- **Levels, from HGSS's heights**: the plateau north of the cliff stands two terraces above the floor. The
  cliff (Cherrygrove rows 7-9) is the upper terrace for two rows and the lower for one, stepping down to the
  sea. The wall (columns 40-41) is the route's two terraces, and the terraces turn the corner together, so
  the corner is FRLG's own outer-corner piece on each step.
- **Foot**: where the cliff stands in the sea, the sea's own animated tiles sit under the rock (no cast
  shadow on water); on the beach and lawn the cast shadow is the route's border grey.
- **Beside the wall**: column 39 (rows 0-5) is Cherrygrove's lawn, blocked, the plateau beside the wall as on
  the route; column 42 is the road's left rim, open. The band's columns 4 and 7 carry the same metatiles.
- **Ids**: Route 30's band wall cells take secondary ids from 596 (after Cherrygrove's own 84), and
  Cherrygrove's secondary defines the same ids with its own tiles: the rock in bank 5 above, the lawn and
  shadow in bank 0 below. The cliff's other cells follow. CherrygrovePrimary's palette 5 takes the rock ramp
  in the seven slots no layout on CherrygrovePrimary draws (the tool checks every metatile of the primary
  and of those layouts' secondaries). No Cherrygrove cell draws the old warm ramp (palette 2) any more.
- **What gave way**: a green tree and the blossom tree at Cherrygrove (39-42, 0-5), and the band's tree pair
  in the same columns. The cliff-top lawn west of the wall (Cherrygrove row 6) no longer connects to the
  road; nothing stood there.
- Evidence: `evidence/cherrygrove-wall/`: before and after, the installed render, and Route 30 joined above it.

## Seams

A Gen 3 map draws a connected map's nearest rows with its own tilesets, and on a crossing it keeps the cells
already on screen as they were drawn.

- **Cherrygrove (south)**: the band is Cherrygrove's own metatiles, and every other Cherrygrove cell visible
  from Route 30 is a primary metatile whose tiles and palettes Route 30's primary keeps. The wall's cells on
  both sides sit at the ids both secondaries define. Clean both ways.
- **Route 31 (north, offset -27)**: each route's palettes are full, so the cells either route can see across
  the seam (Route 30: 160, Route 31: 96) get 55 secondary metatile ids defined in both secondaries. Each map
  draws the other's cells pixel for pixel with its own tiles. Clean both ways.
  - Without the two north rows, Route 31's camera would see Mr. Pokemon's roof. Route 31's banks can't
    hold its colours beside Route 31's own art (the integer program proves it infeasible), so the pad moves
    the house out of that view.
- **Engine change** (PR #39):
  - A crossing into a map on another primary now loads that primary's tiles, palettes 0-5 (with weather)
    and animation. Before, only the secondary and palettes 6-12 were reloaded.
  - When it does, the camera redraws the whole view once it has moved. Without the redraw, the cells on
    screen keep the old tilesets' tile numbers, which the first build showed as scrambled tiles.

## Review

- [Whole map](evidence/review/whole.png): HGSS left, native right.
- [Sheets 1-4](evidence/review/): HGSS left, native right, numbered cells.
- [Gameplay](evidence/review/gameplay.png): 65 headless mGBA frames.
- [Material grid over HGSS](evidence/trace/) and the [ledger](source/trace/material-grid.txt).

## Checks

| Check | Result |
| --- | --- |
| Material audit, every HGSS cell (`material-audit.json`) | 3,072 match, 0 mismatch |
| Native decode vs assembled art | 0 pixels differ |
| Walkable area vs HGSS (`source/pack/traversal.json`, `evidence/pack/install.json`) | HGSS's 1,329 cells, plus the 6 road cells of the north padding |
| Seams, both directions, every cell a player can see (`seams.py`) | clean: Cherrygrove and Route 31 |
| Porymap 6.3.1 export vs native decode (`porymap.json`) | 0 pixels differ: Route 30, Route 31, Cherrygrove |
| ROM build | passes; sha256 in `hashes.json` |
| Headless mGBA (`runtime-summary.json`) | all three phases exit 0 |

The headless run covers:

- Cherrygrove to Route 30's north end and back, walked with every step checked.
- A walking tour into every area HGSS reaches, both house fronts included.
- Every ledge run jumps and refuses the climb back.
- Both house doors, the cuttable tree, the four signs and both ponds block.
- Six tall-grass steps with an empty party start no battle.
- The four signs read. Both item balls give their item and are gone. The hidden Potion is found once.
- The flags survive an ordinary save, a cold reload and title Continue.

47 of 62 write-phase frames are identical to the native decode. The rest differ only where something covers
the map: dialogue boxes, the map-name popup, the item balls and the cuttable tree.

## Declared adaptations

- **Padding**: five woods columns west, Cherrygrove's band south (the west wall running on through it), two rows
  north (HGSS row 0, its stairs as road at the plateau's height: six walkable road cells HGSS doesn't have).
- **Cherrygrove**: its cliff turns north into the route's wall (Cherrygrove's wall, above).
- **Houses**: both doors stay shut; no interiors exist yet.
- **Mailbox**: HGSS model 30 is Mr. Pokemon's mailbox. It's a sprite of its own beside his house, and its sign reads his house.
- **Woods**: cells under a crown stay solid, as HGSS has them.
- **Not placed**: the Apricorn tree, NPCs and trainers (objects or campaign work), and HGSS's Nugget, which
  sits on the Route 29/30/Cherrygrove border, outside this map.
- **Encounters**: the route's existing land table is kept; no surf table was added for the ponds.

## Not verified

- No desktop Porymap save round trip; Porymap's own loader and renderer ran headlessly.
- `apocrypha build` CI can't run: GitHub Actions is disabled on the engine repository.
- Owner visual acceptance.

## Reproduce

```sh
python3 tools/gba/maps/route30_catalog/hgss_render.py PHG gba/art/route30-catalog/source/hgss
python3 tools/gba/maps/route30_catalog/hgss_events.py PHG gba/art/route30-catalog/source/hgss-events.json
python3 tools/gba/maps/route30_catalog/reference.py PHG
python3 tools/gba/maps/route30_catalog/assemble.py PHG CATALOG ENGINE      # CATALOG: checkout of codex/violet-city de5d8cfb
# then Route 31's trace and assembly (its README)
python3 tools/gba/maps/route30_catalog/pair_pack.py ENGINE --install       # both routes
python3 tools/gba/maps/route30_catalog/cherrygrove_wall.py ENGINE          # Cherrygrove's half of the wall
python3 tools/gba/maps/route30_catalog/seams.py ENGINE
make -C ENGINE -j4
MGBA_FLAGS=... python3 tools/gba/maps/route30_catalog/runtime.py ENGINE OUT
python3 tools/gba/maps/route30_catalog/review.py 30 ENGINE OUT PORYMAP_OUT
```

PHG is a pokeheartgold checkout with its archives. Treat these tools as provenance. Once the owner edits the
map in Porymap, edit the native files and don't replay the generator over them.
