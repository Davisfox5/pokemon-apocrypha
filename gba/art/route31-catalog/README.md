# Route 31, rebuilt by the Mahogany / Route 43 process

October 25, 2026. Route 31 (engine map `JohtoRoute31`), Route 30 to the Violet gatehouse and Dark Cave,
built the way the owner accepted for Route 29 (PR #34), together with [Route 30](../route30-catalog/README.md).
HGSS only. It replaces the earlier 63x30 cutout build. Engine branch `claude/routes-30-31-catalog`, draft
PR #39 against `apocrypha`. Visual acceptance stays with the owner.

## The method

1. **Reference** (`reference.py`, `hgss_render.py`, `hgss_events.py`): HGSS Route 31 (EVERYWHERE matrix cells
   (16..17, 8), land_data, zone events R31) rendered at 16 px per cell. Native cell = HGSS cell; the map is
   HGSS's 64x32 with no padding. Route 30 joins its south edge with Route 30's column 0 at Route 31's column
   27 (offsets 27 / -27), so Route 31's road meets Route 30's stairs.
2. **Trees**: 243 non-overlapping 2x2 roots on HGSS's woods cells, each the Cherrygrove tree.
3. **Ground** (`assemble.py`): the Cherrygrove/Route 36 painter on HGSS's own flat ground colours, at
   Cherrygrove's texture phase (through Route 30).
4. **Terrain**:
   - Rock: Blackthorn's FRLG terraces for the ridge, the walls beside the pond and Dark Cave's mountain.
   - Pond: Route 43's natural pond.
   - Stairs: HGSS's ridge crossing is an east-west flight over both ridge columns. Each column takes Route 36's
     plank flight (`route30_catalog/stair_pieces.py`: engine 1643f58a48, "04 Stairs | East-west flight 1"),
     its rock cheeks in this ridge's rock ramp.
   - Dark Cave: its dark opening, cut from HGSS's render.
5. **Catalog art**, byte for byte with hashes (`codex/violet-city` de5d8cfb):
   - G02, the owner-approved HGSS side gate, on the gatehouse with its stairs on HGSS's two gate warps.
   - G15 on all 165 tall-grass cells.
   - L11/L12/L13 on the jump-south runs, turned a quarter for the jump-east run, with the corner piece.
   - P14 on the route sign and P13 on the Dark Cave plaque.
   - Flower heads (6 tones) and light lawn (3) lifted from HGSS's ground.
6. **Pack** (`route30_catalog/pair_pack.py`, joint with Route 30): exact, 0 native pixels differ.
   - Primary `cherrygrove_route31`: CherrygrovePrimary with palettes 0, 2 and 3 kept. Route 31 never draws
     Cherrygrove's sea palette, so palettes 1, 4 and 5 hold route art.
   - Secondary `route31_hgss`: 484 tiles and 278 metatiles (53 of them the seam cells shared with Route 30),
     banks 6-12.
7. **Events** on HGSS's cells:
   - Warps:
     - 0 and 2, the gatehouse doorway (6,13)/(6,14), lead to the Violet gate (`MAP_VIOLET_EAST_GATE` warp 2)
       as `MB_WEST_ARROW_WARP`.
     - 1, Dark Cave's opening (53,13), leads to `MAP_DARK_CAVE_ENTRANCE` warp 0 as `MB_NON_ANIMATED_DOOR`.
     - The engine's gate and cave already return to warps 0 and 1.
   - Signs: the route sign ("ROUTE 31 / WEST TO VIOLET CITY") and the Dark Cave plaque.
   - The two cuttable trees.
   - The Poke Ball (33,25) and Potion (45,13) balls (`FLAG_ITEM_APOC_ROUTE31_POKE_BALL` 0x268,
     `FLAG_ITEM_APOC_ROUTE31_POTION` 0x269; JOHTO_ITEMS.md).

## Seams

Route 30 (south): the cells either route can see across the seam sit at secondary metatile ids both
secondaries define, each drawn with its own map's tiles. Clean both ways (`route30_catalog/seams.py`). Crossing
loads the other route's primary and redraws the view (the engine change in PR #39; see Route 30's README).

## Review

- [Whole map](evidence/review/whole.png): HGSS above, native below.
- [Sheets 1-3](evidence/review/): HGSS left, native right, numbered cells.
- [Gameplay](evidence/review/gameplay.png): 57 headless mGBA frames.
- [Material grid over HGSS](evidence/trace/) and the [ledger](source/trace/material-grid.txt).

## Checks

| Check | Result |
| --- | --- |
| Material audit, every HGSS cell (`material-audit.json`) | 2,042 match, 6 declared (gatehouse base row), 0 mismatch |
| Native decode vs assembled art | 0 pixels differ |
| Walkable area vs HGSS (`evidence/pack/install.json`) | identical: 562 cells, none missing, none added |
| Seams, both directions (`seams.py`) | clean |
| Porymap 6.3.1 export vs native decode (`porymap.json`) | 0 pixels differ |
| ROM build | passes; sha256 in `hashes.json` |
| Headless mGBA (`runtime-summary.json`) | all three phases exit 0 |

The headless run covers:

- Route 30's north end, across the seam and along Route 31 to the gatehouse doorway, every step checked.
- West into the doorway warps to the Violet gate.
- From the doorway on foot to Dark Cave; north into its opening warps into the cave.
- Back across the seam into Route 30.
- A walking tour into every area HGSS reaches.
- Every ledge run (south and east) jumps and refuses the climb back.
- Both cuttable trees, both signs, the pond, the gatehouse wall, the rock and the cave's rock block.
- Six tall-grass steps with an empty party start no battle.
- Both signs read. Both item balls give their item and are gone.
- The flags survive an ordinary save, a cold reload and title Continue.

29 of 52 write-phase frames are identical to the native decode. The rest differ only where something covers
the map: dialogue boxes, the map-name popup, the item balls and the cuttable trees.

## Declared adaptations

- **Gatehouse base**: HGSS's building reaches row 16. G02 is seven rows (9-15, its stairs on HGSS's warps), so
  row 16 under its base is lawn and stays solid as HGSS's footprint.
- **Not placed**: the sleeping man, the youngsters, the bug catcher, the Apricorn tree and the other NPCs
  (objects or campaign work).
- **Encounters**: none added; the map had no wild table before.
- The earlier Route 31 secondary (`gTileset_Route31`) stays in the engine unused by any layout.

## Not verified

- No desktop Porymap save round trip; Porymap's own loader and renderer ran headlessly.
- The Violet gate's own exit back onto Route 31 was not walked (the run warps in, then re-enters Route 31);
  its warp events point at warp 0, the doorway.
- `apocrypha build` CI can't run: GitHub Actions is disabled on the engine repository.
- Owner visual acceptance.

## Reproduce

```sh
python3 tools/gba/maps/route31_catalog/hgss_render.py PHG gba/art/route31-catalog/source/hgss
python3 tools/gba/maps/route31_catalog/hgss_events.py PHG gba/art/route31-catalog/source/hgss-events.json
python3 tools/gba/maps/route31_catalog/reference.py PHG
python3 tools/gba/maps/route31_catalog/assemble.py PHG CATALOG ENGINE      # CATALOG: checkout of codex/violet-city de5d8cfb
python3 tools/gba/maps/route30_catalog/pair_pack.py ENGINE --install       # both routes (Route 30's assembly first)
python3 tools/gba/maps/route30_catalog/seams.py ENGINE
make -C ENGINE -j4
MGBA_FLAGS=... python3 tools/gba/maps/route31_catalog/runtime.py ENGINE OUT
python3 tools/gba/maps/route30_catalog/review.py 31 ENGINE OUT PORYMAP_OUT
```

Treat these tools as provenance. Once the owner edits the map in Porymap, edit the native files.
