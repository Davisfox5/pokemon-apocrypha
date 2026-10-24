# Route 29 rebuilt from the decoded HGSS map (superseded)

> Superseded on October 25 by `gba/art/route29-catalog`, after owner review: placement, trees, paths, grass,
> ledges, borders and walking routes were wrong. Kept as the prior draft; its generator now targets the
> same tileset name, so do not run it over the current branch.

October 24, 2026. Cherrygrove to New Bark, redone from scratch under
[the map reconstruction workflow](../../../docs/GBA_MAP_RECONSTRUCTION.md). The
reference is the decoded DS map itself (terrain types, collision bytes and events
from the HGSS ROM data), not a screenshot trace; the 1:1 HGSS render is used only as
texture for the pieces the Emerald kit does not have. Editable source is the layout,
map and secondary tileset on branch `claude/route29-hgss-decoded` of
`Davisfox5/pokeemerald-expansion` (PR against `apocrypha`); this folder is the
evidence and the provenance. Visual acceptance stays with the owner. The first
attempt (`gba/art/apoc-route29`, PR #3) is kept as a prior draft and is superseded
by this one.

## Review

- [overview.png](evidence/overview.png): the whole HGSS route above the whole native
  layout, with a column ruler.
- `compare-NN-xA-zB.png` (twelve sheets, e.g. [compare-04](evidence/compare-04-x9-z14.png)):
  each 24x14-cell window of the HGSS route beside the same cells of the native
  render, both with cell grids and coordinates; the decoded material letter is
  printed on every HGSS cell (`T` forest, `G` tall grass, `_` ledge, `|`/`!` ledge
  wall, `c` corner, `P` path, `g` gate, `D` door, `A` Apricorn tree, `x` cuttable
  tree, `s` sign). The render sits about one cell off the decoded grid in places
  (its registration is a perspective trace); the letters are the authority.
- [gameplay.png](evidence/gameplay.png): 46 headless mGBA frames from the checks
  below (both town seams, every ledge row, walls, gate, lookout, grass, signs, trees,
  the Potion, the walk along the route, cold reload and Continue).
- [audit.json](evidence/audit.json): every reconstructed cell checked against the
  decoded grids. 2478 agree; 18 differ and each is a declared adaptation (13 lawn
  cells blocked under whole trees, 2 gate door cells kept blocked, 2 cuttable trees
  as object events, 1 forest cell without tree art). No defects.
- [native-map.png](evidence/native-map.png), [tileset-sheet.png](evidence/tileset-sheet.png),
  [build-report.json](evidence/build-report.json), [hashes.json](evidence/hashes.json).

## Source of truth (source/)

| File | Content |
| --- | --- |
| `reference.json` | ROM data identity: EVERYWHERE matrix cells (18..20, 12), land data archive index, world origin (576, 384) |
| `hgss-terrain-types.txt`, `hgss-collision.txt` | the decoded 96x32 terrain-type and collision bytes |
| `material-grid.txt`, `traversal-grid.txt` | the two separate layers derived from them (materials; `X` blocked, `.` open, `v` one-way, `D` door) |
| `hgss-events.json` | the decoded zone events in HGSS cell coordinates (signs, Apricorn tree, cuttable trees, gate warp) |
| `traversal-ledger.csv` | one row per HGSS cell: type byte, collision byte, material, traversal, map cell, in-region flag |
| `adaptations.json` | everything that is not a 1:1 transfer: tree fitting, absorbed cells, overlaps, event moves, pinned seam ids, unwired items |

Map cell = HGSS cell + (1, 3). The reconstructed region is columns 10-87, rows 0-34
of a 98x54 layout. Columns 0-9 and 88-97 are the accepted layout's town-seam windows
and rows 35-53 its sea ridge and lookout, carried verbatim from `apocrypha` commit
`2722eaf` (the ridge moved down six rows to make room for the full HGSS height; the
hidden Potion moved with it to (62, 33)).

## How the native art was assembled

- Ground: the accepted Cherrygrove lawn (2x2 phase) and its dirt kit, learned from
  the town layout, on every `.` and `P` cell. The path runs up to the ledge walls on
  the dirt kit's edge tiles, as in HGSS.
- Trees: the accepted 2x3 tree (crown top, crown middle, trunk), 330 of them with
  complete footprints. HGSS stacks its canopies, so a tree may stand one row below
  the tree behind it; the overlapped row is a composite metatile (crown top over the
  flattened trunk row, palette bank 12). One-column strips and parity-straddling
  blocks get a whole tree overlapping its neighbour by a column. Short forest runs
  absorb a lawn row only when every open region stays connected (13 cells, listed).
  One forest cell (66, 29) has no whole-tree fit and is blocked lawn. Seven
  free-standing trees near Cherrygrove are the town's blossom tree (design bible,
  Chapter 1).
- Sliced from the HGSS render on its 16 px grid: tall grass (nine-slice, 16 edge
  variants), ledges and walls (8 px bar, 7 px wall, three corners), the Route 46 gate
  (placed so its left edge is on HGSS column 48, footprint 48-53), the Apricorn tree
  (1x2, crown over the walkable cell above), orange flowers, the light lawn patch
  (snapped to its rectangle), the route sign.
- Cuttable trees are the native cuttable-tree object (`EventScript_CutTree`) on the
  HGSS tree cells (54, 20) and (44, 24); the cells are open under the object.
- Ledges are impassable in the layout with `MB_JUMP_SOUTH`, the vanilla convention
  (Route 101), so the jump works and walking back up is blocked.

Tileset `route29_hgss`: 257 secondary tiles of 512, 279 metatile slots, banks 6-12.
Seam rule: cells near a connection are drawn by the neighbouring town with its own
tileset, so every secondary metatile id used in the seam windows (the accepted
route's own cells, New Bark's first eight columns, Cherrygrove's last eight) keeps
its id and its look in this tileset (`seam_pinned_metatiles` in adaptations.json);
banks 10 and 11 are therefore fixed to the towns' palettes. Tile 0x200 is left blank:
after a connection crossing the engine showed the first secondary tile of the new
tileset as stale VRAM on both sides of the New Bark seam, and leaving it unused
cleared both crossings (frames `seam-new-bark`, `new-bark-into-route`).

## Checks

- ROM built locally with the installed ARM toolchain (`make tools`, `make generated`,
  `make`); hashes in `hashes.json`.
- Headless mGBA (libmgba 0.10.5, `tools/gba/maps/route29_hgss/runtime.py`): new game;
  Cherrygrove -> Route 29 -> Cherrygrove across the connection; the walk along the
  route; Route 29 -> New Bark -> Route 29 and New Bark -> Route 29 by walking; nine
  ledge rows jump down and block from below; five wall probes; the closed gate; the
  lookout railing; six tall-grass steps with an empty party and no battle; both signs
  read; both cuttable trees and the Apricorn tree block; the hidden Potion found once
  and its flag survives the save; ordinary save at the lookout; cold flash reload;
  title screen Continue. All phases exit 0 (`results.json` in the check directory).
- Porymap 6.3.1 was built here from source (qmake6) and run offscreen with this
  checkout as its project and `CherrygroveRoute29Approach` as the recent map: the
  log shows the project opened, 34/34 project files monitored and the map set, with
  no errors; see "Not verified" for what that does not cover.
- JSON validity of map/layout files is covered by the `apocrypha build` workflow.

## Not verified

- No GUI Porymap save round trip (no display here). The files are the standard
  Emerald formats and the engine builds and runs them.
- The upstream `CI/test` job is red on every `apocrypha` PR because of the roster
  and mechanics profile; `apocrypha build` is the relevant check.
- Known visual limits for the owner's call: the dense HGSS-style stacking inside the
  region meets the accepted six-row tree band in the seam columns (87/88 and 9/10)
  with a visible change of rhythm; the lawn speckle phase under many tree cells does
  not match the surrounding lawn (the kit has two phases per tree row, listed as
  `lawn_phase_misses`); the gate interior is not built, so its door stays blocked;
  the accepted sea ridge replaces HGSS rows 29-31 of forest only at the ridge join.

## Reproduce

```
python3 tools/gba/maps/route29_hgss/build.py ENGINE_DIR          # tileset, layout, map.json, headers, source/, evidence basics
python3 tools/gba/maps/route29_hgss/runtime.py ENGINE_DIR OUT    # headless mGBA phases (MGBA_FLAGS for libmgba)
python3 tools/gba/maps/route29_hgss/evidence.py ENGINE_DIR OUT   # comparison sheets, audit, gallery, hashes
```

The generator reads the DS data through the hub's `tools/regionport` and
`tools/mapeditor` decoders and the carried regions from the `apocrypha` commit named
in `BASE_REV`. Do not replay it over owner edits made in Porymap: edit the native
files on the branch instead.
