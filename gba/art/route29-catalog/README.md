# Route 29, rebuilt by the Mahogany / Route 43 process

October 24-25, 2026. Third Route 29 rebuild. It answers the owner's review of the previous attempt
(`gba/art/route29-hgss`): wrong placement, overlapping trees, wrong paths, missing tall grass,
ledges that didn't connect, bad borders between tile types and wrong walking routes.

It follows [the map reconstruction workflow](../../../docs/GBA_MAP_RECONSTRUCTION.md) and the process
the owner accepted for Mahogany Town (PR #28) and reviewed on Route 43 (PR #33). Engine branch
`claude/route29-hgss-decoded`, draft PR #34 against `apocrypha`. Visual acceptance stays with the owner.

## What was wrong before, and why

- **The reference was misregistered.** The old screenshot reference (`claude-routes/references/route29-hgss.png`)
  is a tilted-camera capture at about 12 px per row, not 16: tall grass repeats every 12 px down and
  16 px across. Everything sliced or placed from it on a 16x16 grid was off by up to two rows.
- **Paths came from the wrong data.** The previous build drew roads from a permission flag that marks
  footstep sound, not the road texture, so the roads were wide blocks.
- **The vertical "walls" were ledges.** HGSS types 0x38 and 0x39 are jump-east and jump-west ledges.
  They were built as solid walls, so the walking routes were wrong.
- **Trees overlapped**, and grass and ledge pieces were cut from the squashed render.

## The method this time

1. **Reference** (`reference.py`, `hgss_render.py`, `hgss_events.py`): HGSS Route 29 is rendered from its
   own DS map data (EVERYWHERE matrix cells 18-20/12, land_data, area bank 2, zone events R29) at
   exactly 16 px per cell, the way Route 43 was. Native cell = HGSS cell + (4, 3).
   - Row offset 3 keeps both connections on their roads (Cherrygrove offset 0, New Bark offset 6).
   - Column offset 4 keeps the HGSS signs and tall grass out of the 8-column seam windows. It also
     lines HGSS's two-column tree pairs up with the windows.
   - Two padding columns on the east keep HGSS's east grass out of the east window.
2. **Trees**: an integer program places the largest set of non-overlapping 2x2 roots on HGSS's woods cells
   (Route 43's method), interior cells first. Each tree is the Cherrygrove tree, which is T01 pixel for pixel
   plus the town's contact shadow, with its crown one row north of its root. They are painted north to
   south, so each crown covers the trunk behind it, as Cherrygrove's own dense forest does. Nothing
   overlaps. 440 trees, no leftover woods cells.
3. **Ground** (`assemble.py`): the approved Cherrygrove/Route 36 painter on an 8 px lawn/road grid read
   from HGSS's own flat ground colours, so the road follows HGSS's shape and rims. The road texture is
   Cherrygrove's own, so it runs into the town unchanged.
4. **Catalog art**, copied byte for byte with hashes from the Johto catalog (`codex/violet-city` de5d8cfb):
   - G15 on every HGSS tall-grass cell (409 cells).
   - L11/L12/L13 on the jump-south runs, with rounded free ends.
   - The same pieces turned a quarter for the jump-east and jump-west runs, with corners joining both.
   - G01a on HGSS's Route 46 gatehouse, its doorway on HGSS's gate warps.
   - P14 on both HGSS signs.
   - Flowers and the light lawn patches are lifted from HGSS's own ground textures: every pixel that is
     not plain HGSS lawn.
5. **Seams** (`pack.py`, `seams.py`): Gen 3 draws a connected map's 7 nearest columns with the current map's
   tilesets. So Route 29 keeps CherrygrovePrimary unchanged, and its 8-column windows hold only
   metatiles both towns draw identically.
   - The windows use the towns' own road kits on their road rows.
   - New Bark's edge metatiles and the accepted coast's metatiles are carried with their own
     definitions, palettes included.
6. **Pack**: exact. Every native pixel keeps its assembled colour. Tiles already in CherrygrovePrimary
   are reused. 410 secondary tiles, 264 metatiles, banks 6-11.

## Review

- [Whole map](evidence/review/whole.png): HGSS above, native below, same cells.
- [Sheet 1](evidence/review/sheet-1-x0-25.png), [2](evidence/review/sheet-2-x25-50.png),
  [3](evidence/review/sheet-3-x50-76.png), [4](evidence/review/sheet-4-x76-101.png): HGSS left, native right,
  numbered cells.
- [Gameplay](evidence/review/gameplay.png): 52 headless mGBA frames.
- [Material grid over HGSS](evidence/trace/grid-over-hgss-1.png) (sheets 1-4) and the [ledger](source/trace/material-grid.txt).

## Checks

| Check | Result |
| --- | --- |
| Material audit, every HGSS cell above the coast (`material-audit.json`) | 2,784 match, 0 mismatch |
| Native decode vs assembled art | 0 pixels differ outside the windows; 112 lawn-speckle pixels inside them (primary tree joins) |
| Walkable area vs HGSS (`pack.json`) | every cell HGSS reaches is reachable; the only additions are 54 overhang cells under crowns |
| Seams, both directions, every cell a player can see (`seams.py`) | clean |
| Porymap 6.3.1 export vs native decode (`porymap.json`) | 0 pixels differ, Route 29, Cherrygrove and New Bark |
| ROM build | passes; sha256 in `hashes.json` |
| Headless mGBA (`runtime-summary.json`) | all three phases exit 0 |

The headless run covers:

- Cherrygrove to Route 29 to New Bark and back, walked with every step checked against the predicted route.
- A walking tour into every area: upper lawn, north grass, gatehouse front, north-east grass, east sign,
  east grass, south-east pocket, centre, south lawn and the lookout.
- All 13 ledge runs jump and refuse the climb back.
- The gatehouse door, both cuttable trees and both signs block.
- Six tall-grass steps with an empty party start no battle.
- Both signs read, and the hidden Potion is found once on foot.
- Ordinary save, cold reload and title Continue.

Each frame is compared with the native decode at the camera position, both towns included. 36 of 49
frames are identical. The rest differ only where something covers the map: dialogue boxes, the map-name
popup, cuttable-tree sprites and the Continue menu.

## Declared adaptations

- **Coast.** Rows 32-50 are the accepted Cherrygrove coast from `apocrypha` 2722eaf, carried as metatile
  ids. They replace HGSS rows 29-31, which are solid forest border, so nothing walkable changes.
  - The coast moves four columns east and three rows south with the new frame.
  - The hidden Potion moves with it, to (66,30): two rows above the railing, as before.
- **Overhang.** 54 HGSS woods cells under a crown have no 2x2 root that fits, because of HGSS's offset
  crowns. They are open, and the player walks behind the crown, as on Route 43. None joins two areas
  HGSS separates.
- **Seam windows.** The windows' tree joins use the primary's own join tiles (0x1A3/0x1A4), which differ
  from the assembled pixels only in lawn speckle.
- **Window crowns.** In the windows, a crown over a woods cell is solid, as on both towns' forest edges.
- **Hidden coast ids.** Three carried coast ids in the east window (0x277, 0x287, 0x288) would draw
  differently in New Bark's tileset. New Bark never shows those columns, so they are kept.
- **Gatehouse.** The doorway stays shut: no Route 46 gatehouse interior exists.
- **Cuttable trees.** HGSS's cuttable trees are native cuttable-tree objects (`EventScript_CutTree`).
- **West sign.** It reuses the route's existing sign script; its text names Cherrygrove.
- **Not placed:** the Apricorn tree, NPCs and the item ball. They are objects or campaign work.
- **Trees.** The Cherrygrove tree stands one row taller than HGSS's squat tree, as on Route 43.

## Not verified

- No desktop Porymap save round trip. Porymap's own loader and renderer were run headlessly
  (`porymap_probe.cpp`).
- `apocrypha build` CI cannot run: GitHub Actions is disabled on the engine repository.
- Owner visual acceptance.

## Reproduce

```sh
python3 tools/gba/maps/route29_catalog/hgss_render.py PHG out=gba/art/route29-catalog/source/hgss
python3 tools/gba/maps/route29_catalog/hgss_events.py PHG gba/art/route29-catalog/source/hgss-events.json
python3 tools/gba/maps/route29_catalog/reference.py PHG
python3 tools/gba/maps/route29_catalog/assemble.py PHG CATALOG ENGINE      # CATALOG: checkout of codex/violet-city de5d8cfb
python3 tools/gba/maps/route29_catalog/pack.py ENGINE --install
python3 tools/gba/maps/route29_catalog/seams.py ENGINE
make -C ENGINE -j4
MGBA_FLAGS=... python3 tools/gba/maps/route29_catalog/runtime.py ENGINE OUT
python3 tools/gba/maps/route29_catalog/review.py ENGINE OUT PORYMAP_OUT
```

Here PHG is a pokeheartgold checkout with its archives. These tools are provenance: once the owner edits
the map in Porymap, edit the native files and do not replay the generator over them.
