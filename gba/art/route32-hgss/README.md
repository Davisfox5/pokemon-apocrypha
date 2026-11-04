# Route 32, rebuilt from HGSS's own textures

November 4, 2026. A from-scratch Route 32 (Violet City to the Union Cave forecourt) under
[AGENTS.md](../../../AGENTS.md) and [the map reconstruction workflow](../../../docs/GBA_MAP_RECONSTRUCTION.md).
It replaces the catalog build (`gba/art/route32-catalog`, engine PR #51 / hub PR #46), which the owner rejected.
Engine branch `claude/route-32-hgss`, stacked on `claude/routes-30-31-catalog` (PR #39, which holds Violet City).
Visual acceptance stays with the owner.

## What changed from the rejected build

The catalog build drew Route 32 with stand-in art: FRLG rock terraces, Route 36's plank stairs, the Cherrygrove
tree on an integer-program lattice, a painted lawn and road, one-terrace islets, an invented viaduct deck. This
build uses HGSS's own textures for the route itself, as AGENTS.md asks ("original-game textures"; "preserve the
original wall/cap texture and shading"), the approved shared buildings, and HGSS's own viaduct textures:

| Element | Source |
| --- | --- |
| Lawn, flowers, light lawn, dirt road, tall grass, woods, rock caps and faces, ledges, stairs, sea, shore foam, pier, sea and land boulders, islets, Union Cave mouth, route signs | HGSS Route 32's land_data rendered 1:1 at 16 px a cell (`hgss_render.py`), each cell's own pixels |
| Ruins of Alph gatehouse | G02, the owner-approved HGSS side gate (Route 31's), its stairs on HGSS's gate warps (6,5)/(6,6) |
| Pokemon Center | C06, the approved Violet Center, its door on HGSS's Center door (20,130) |
| Magnet Train viaduct | HGSS's `overpass` (guard rail, side) and `senro_out` (track bed) textures (`a/2/3/3` model 24) on the footprint of HGSS's viaduct shadow (HGSS rows 82.5-87.5); the deck runs east-west, above the player |
| North padding (6 rows) | Violet City's own south edge: rows 0-4 are Violet's metatiles by id, row 5 ends Violet's cobble road in its own verge and dithers Violet's lawn into HGSS's |

Trees keep HGSS's footprints (the woods cells are HGSS's blocked 0x06 cells, crowns where HGSS draws them), so
paths, clearings and barriers are HGSS's own. Stairs, ledges and rock faces face the way HGSS's mesh does,
because they are HGSS's pixels for those cells.

## Two maps

HGSS's textures for the whole route need about 1,960 distinct 8x8 tiles; one Gen 3 map holds 1,024. AGENTS.md:
adapt the technique to each map's hardware budget. The route is split at the viaduct:

- `JohtoRoute32`: native rows 0-88 (Violet City to the viaduct), its own `route32_north` primary and secondary.
- `JohtoRoute32South`: native rows 89-165 (the viaduct to the cave), `route32_south` primary and secondary. Its
  row r is native row 89 + r. The Center (`Route32PokemonCenter`, Violet's interior retargeted) is entered from here.

The seam sits in the middle of the deck. A Gen 3 map draws a connected map's rows with its own tilesets, so the 7
rows either side of the seam have the same metatile ids, tiles and colours in both maps (palette banks 2 and 4-10
are identical in both; seam tiles use only those). `seams.py` checks every cell either side can see: clean.
The map name pops up again when crossing (`OW_HIDE_REPEAT_MAP_POPUP` is FALSE in the engine config; not changed).

## Palettes and tiles

- One bank per material family (`pack.py` `BANK_PLAN`): sea, rock, trees, pier, deck, lawn and flowers, road,
  tall grass shared by both maps; buildings per map; north keeps Violet's banks 0, 1, 3 and 11 for the pinned
  Violet cells; south has second rock, sea, tree and lawn banks. Each bank holds its family's most-used HGSS
  colours exactly (up to 14), the rest fitted to the joins. One material stays in one bank, so a road or a cliff
  cap doesn't change tone from square to square.
- Feature colours no bank held (stair planks, the cave mouth's black, the Center's glass, building trims) get
  locked slots.
- Where a square needs two banks (buildings carry 21 colours; the shore foam sits on rock-brown dots), the missing
  colours go in its upper tile, both layers below the player (`METATILE_LAYER_TYPE_COVERED`: 232 cells north, 74
  south). Never on cells with art above the player or in the seam rows.
- Tiles: exact dedupe with flips (north 1,277 patterns, south 1,389), then logged near-duplicate merges to fit
  1,024 (325 and 366 merges; median 1.6 / 1.9 Lab, 90th percentile 3.8 / 4.6, never above 7.3 mean or 30 on a
  pixel), only within one material class and layer. Stairs, ledges, doors, signs, buildings, the cave mouth,
  top-layer art and the seam are never merged away. Every merge: `source/pack/merges.json`.
- Against the HGSS art, per pixel: palette mean 0.86 Lab (95th percentile 4.3); installed native mean 0.93 Lab.

## Cleanup

- Render seams: 2,660 pixels in 72 rock cells where a lifted face or an islet top let the flat sea show through
  (blue specks on the islets and cliff feet), filled from the rock's own texture 8 px above or below
  (`compose.py`; before/after in `evidence/compose/cleanup.png`).
- The HGSS gatehouse and Center models are left out of the ground render (G02 and C06 stand there); the
  viaduct's translucent shadow is left out of the ground (the deck covers those rows).

## Review

- [Whole route](evidence/review/whole.png): HGSS left, native right.
- [Sheets](evidence/review/): HGSS left, native right, numbered cells; [the seam](evidence/review/seam.png).
- [Gameplay](evidence/review/gameplay.png): headless mGBA frames.
- [Material grid over HGSS](evidence/trace/) and the [ledger](source/trace/material-grid.txt).

## Checks

| Check | Result |
| --- | --- |
| Traversal audit, every HGSS cell (`evidence/review/material-audit.json`) | 5,117 match, 3 declared (gatehouse doorway, cave mouth), 0 mismatches |
| Native pixels vs the HGSS-texture art, per cell | mean Lab per cell: 3,281 under 1, 1,458 at 1-3, 367 at 3-6, 14 at 6 or more (listed) |
| Walkable area vs HGSS (`evidence/pack/pack.json`) | HGSS's 1,544 cells; native adds only the Center door cell |
| Stairs (`evidence/review/rock-stair-audit.json`) | (9-10, 74-76) east-west and (6-8, 111-112) north-south, per HGSS's decoded slope; walkable; 2.1-3.4 Lab from HGSS's pixels |
| Seams, both directions, every visible cell (`seams.py`) | clean: Violet / north, north / south |
| Porymap 6.3.1 export vs native decode (`evidence/review/porymap.json`) | 0 differing pixels on both maps |
| ROM build | passes; sha256 in `evidence/review/hashes.json` |
| Headless mGBA (`evidence/review/runtime-summary.json`) | write, read, menu phases exit 0; 1,262 observations; 61 of 79 frames identical to the decode, the rest only where a dialogue box, the map-name popup or the Continue menu covers the map |

The headless run covers Violet City to the cave forecourt and back on foot across both seams (every step checked
against the predicted route), a walking tour into every area the route reaches, all ledge runs (jump and refuse
the climb back), the gatehouse doorway and cave mouth (shut), the cuttable tree, the breakable rock, the signs
and the sea edge, tall grass with an empty party, the Center door in and out, the item balls and hidden items,
and an ordinary save, cold reload and title Continue. Frames are compared with the native decode at the camera
position; the frames that differ are the ones with a dialogue box, the map-name popup or the Continue menu.

## Declared adaptations

- **Two maps** at the viaduct (budget, above). The name popup shows again on crossing.
- **North padding**: six rows of Violet's lawn and road between Violet and HGSS row 0, for the seam.
- **Gatehouse base row**: HGSS's gatehouse footprint reaches HGSS row 8; G02 is seven rows, so row 8 under its base
  shows lawn and stays solid as HGSS's footprint (Route 31's adaptation).
- **Doors**: the Ruins of Alph gatehouse doorway and the Union Cave mouth stay shut (no interiors on this branch).
  The Center door is a non-animated door (no door animation is registered for these tilesets).
- **Viaduct**: above the player on its rows (4 cells hidden under it); it ends at the map edges, since a Gen 3
  border is one 2x2 block.
- **Route 33**: no south connection (no Route 33 on this branch).
- **Tile merges and palette reduction** (above): logged, material-constrained; the rock caps' diamond highlights
  are slightly softer than HGSS's where merges landed.
- Trainers, NPCs and the TM09 ball are campaign work and not placed.

## Reproduce

```sh
python3 tools/gba/maps/route32_hgss/hgss_render.py PATH/TO/pokeheartgold gba/art/route32-hgss/source/hgss
python3 tools/gba/maps/route32_hgss/hgss_events.py PATH/TO/pokeheartgold
python3 tools/gba/maps/route32_hgss/reference.py PATH/TO/pokeheartgold
python3 tools/gba/maps/route32_hgss/compose.py ENGINE PATH/TO/pokeheartgold
python3 tools/gba/maps/route32_hgss/pack.py ENGINE --install
make -C ENGINE -j8
python3 tools/gba/maps/route32_hgss/seams.py ENGINE
MGBA_FLAGS='-lmgba' python3 tools/gba/maps/route32_hgss/runtime.py ENGINE RUNTIME_OUT
porymap_probe ENGINE PORYMAP_OUT JohtoRoute32 JohtoRoute32South   # tools/gba/maps/route29_catalog/porymap_probe.cpp
python3 tools/gba/maps/route32_hgss/review.py ENGINE RUNTIME_OUT PORYMAP_OUT
```

Generators are provenance; edit the committed engine maps in Porymap rather than replaying them over owner edits.
Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation from pret/pokeheartgold).
