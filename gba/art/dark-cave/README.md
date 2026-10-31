# Dark Cave: HGSS cave textures, both maps

Owner review pending. Engine branch `claude/dark-cave` (stacked on `claude/route-46`), maps
`DarkCaveRoute45Side` (id 49) and `DarkCaveRoute31Side` (id 50), 64x64 each, in HGSS's own
coordinates. Owner's style choice: HGSS's own Dark Cave rock, floor and water converted to native
tiles, the way Union Cave was finished. None of Union Cave's art, palettes or generators are used.

## Review

- Whole maps, HGSS beside native: [Route 45 side](evidence/review/route45-side-whole.png),
  [Route 31 side](evidence/review/route31-side-whole.png)
- Route 45 side at 2x: [north halls](evidence/review/route45-side-north-halls.png) ·
  [west ledges](evidence/review/route45-side-west-ledges.png) · [lake](evidence/review/route45-side-lake.png) ·
  [south and the hole down](evidence/review/route45-side-south-and-hole.png)
- Route 31 side at 2x: [west cavern and pools](evidence/review/route31-side-west-cavern-and-pools.png) ·
  [hole and north](evidence/review/route31-side-hole-and-north.png) · [east halls](evidence/review/route31-side-east-halls.png) ·
  [south and the Route 46 exit](evidence/review/route31-side-south-and-route46-exit.png)
- [The doors on Routes 45 and 46](evidence/review/route-doors.png)
- [Gameplay gallery](evidence/review/gameplay-gallery.png) (headless mGBA)

## Art

The native art is HGSS's own render of both maps (`tools/gba/maps/dark_cave/hgss_render.py`, decoded
land_data, area bank 87): its rock walls, cliff tops, floor and moss, pools, stairs, boulders and
exit light, one HGSS tile per native cell. Both maps share one tileset pair of their own,
`gTileset_DarkCavePrimary` and `gTileset_DarkCave`.

HGSS's two maps hold 2,413 distinct 8x8 tiles and 80 colours; a Gen 3 tileset pair holds 1,008 tiles
in 13 banks of 15 colours. `pack.py` fits it in two lossy steps:

1. **Palette banks.** Each distinct tile goes to one of 13 banks, each bank's 15 colours fitted to its
   tiles.
2. **Tile reuse.** Representatives are always real HGSS tiles. The one whose loss costs least is
   dropped, and its users take their nearest remaining representative under any flip, until 1,008
   patterns remain. A pixel whose HGSS material class differs (floor, wall face, cliff top, rim,
   boulder, stairs, water, exit) costs heavily, so a wall edge is only drawn by a tile with the same
   edge.

Result ([pack.json](evidence/pack.json)): 1,008 tiles (512 + 496), 809 metatiles (512 + 297). Against
HGSS's render, in RGB555, about 96% of cave pixels are exact, 99.1% within one level and 99.8% within
two. The largest moves are in the exit-light glows, which band slightly. Every cell is one bottom
layer under the player.

## Traversal

From HGSS's permission grid, cell for cell ([traversal](source/pack/)):

| HGSS | Native |
| --- | --- |
| floor (0x08) | MB_CAVE, elevation 3 |
| water (0x15) | MB_POND_WATER, elevation 1 (Surf) |
| ledges (0x3B, 0x39) | MB_JUMP_SOUTH, MB_JUMP_WEST, one way |
| exit cell (0x6F) with arrow (0x65) south of it | MB_SOUTH_ARROW_WARP on the exit cell |
| hole into the Route 45 side (0x6E) | MB_NON_ANIMATED_DOOR: walked into northward, the player steps out south |
| wall, rim, void | solid |

The border block is the black void metatile, so past the map edge is black, as in HGSS. Both maps
are MAP_TYPE_UNDERGROUND and need Flash, under the existing MAPSEC_DARK_CAVE, music MUS_CAVE_OF_ORIGIN
(DarkCaveEntrance's).

## Doors

| From | To |
| --- | --- |
| Route 45 (10, 6) mouth | Route 45 side (60, 4) exit |
| Route 45 side (6, 57) exit | Route 31 side (26, 4) hole |
| Route 31 side (55, 56) exit | Route 46 (20, 9) mouth |

Routes 45 and 46 are owner-accepted and locked, so their changes are native wiring edits only: the
mouth metatile (Route 45's 523, Route 46's 538, each used by that one cell) becomes
MB_NON_ANIMATED_DOOR with its layer kept, the cell's collision opens, and one warp is added. No pixel
changes ([audit](evidence/audit.json)).

HGSS's ledges on the Route 45 side run one way. From the hole up from the Route 31 side there is no
way back up to Route 45, in HGSS or here; the audit checks each exit reaches the others exactly as
HGSS's do.

## Not built or not placed

- **Route 31 exit** (5, 26) stays solid. Route 31 and `DarkCaveEntrance` are another agent's maps.
- Placed: the Route 31 side's four Rock Smash rocks and the Strength boulder, at HGSS's cells, as
  Gen 3 field objects. They hold back 377 cells on foot, as in HGSS.
- Not placed: the sunglasses NPC, item balls (TM54, Revive, Potion, Hyper Potion, Full Heal, Dire Hit,
  Black Flute), hidden items and wild encounters. All are recorded in
  [source/hgss-events](source/hgss-events/).

## Evidence

- **Audit** ([audit.json](evidence/audit.json)): both maps decode to the packer's image on every
  pixel; behaviour, collision, elevation and layer match the ledger on every cell. Gen 3 movement
  reaches exactly HGSS's cells from the exits: 1,259 on the Route 45 side, 758 on the Route 31
  side, on foot and with Surf, obstacles in place or cleared. Every warp pairs back. Routes 45 and 46
  change no pixel, and the changed-file list is checked.
- **Headless mGBA** ([results](evidence/gameplay/results.json)): 31 captures, each rebuilt from VRAM
  and equal to the decoded map. Caves are dark without Flash and lit with it; all three doors are
  walked both ways; a ledge jumps one way; Surf starts on both pools. The Rock Smash rock and the
  boulder block the player, and so does Route 31's exit. Flash save, cold reload and title
  Continue all pass.
- **Porymap 6.3.1** ([results](evidence/porymap/results.json)): opens, exports and saves all four maps
  on a fresh clone. Exports equal the native decodes on every pixel, no Dark Cave or route file is
  rewritten, and the log has no errors.

## Reproduce

```sh
python3 tools/gba/maps/dark_cave/hgss_render.py PHG OUT route45-side   # and route31-side
python3 tools/gba/maps/dark_cave/hgss_events.py PHG gba/art/dark-cave/source/hgss-events
python3 tools/gba/maps/dark_cave/pack.py ENGINE
python3 tools/gba/maps/dark_cave/install.py ENGINE      # refuses over commits that are not its own
make -C ENGINE -j8
python3 tools/gba/maps/dark_cave/check.py ENGINE
python3 tools/gba/maps/dark_cave/runtime.py ENGINE OUT_DIR
python3 tools/gba/maps/dark_cave/porymap.py ENGINE PORYMAP_BINARY   # needs the engine change committed
python3 tools/gba/maps/dark_cave/review.py ENGINE OUT_DIR
```

Source artwork: Nintendo / Game Freak / Creatures, decoded read-only from pret/pokeheartgold's
archives. No ROMs, saves or tool binaries committed.
