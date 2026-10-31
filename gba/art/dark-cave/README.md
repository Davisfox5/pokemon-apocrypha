# Dark Cave: HGSS cave textures, both maps

Owner review pending (second pass: rock on the Gen 3 grid). Engine branch `claude/dark-cave` (stacked on `claude/route-46`), maps
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

Gen 3 sizing (owner review, October 31). HGSS builds its cave walls as 45-degree tiers, one tile
deep and one tile high each, and its camera draws them slanted: side walls came out as diagonal
wedges, faces started 9 px into a cell, and wall pixels lay on 225 walkable cells. As on the routes,
`assemble.py` redraws the rock top-down on the Gen 3 grid, in HGSS's own cave textures. Each rock
cell keeps HGSS's tier height and takes a nine-slice piece from its neighbours:

| Lower neighbour | Piece |
| --- | --- |
| south | the face: `dwall_s`, one cell tall, on the grid (`dwall_sw` / `dwall_es` halves at its corners) |
| north, east, west | the rim: `dallpeak_p`'s lip along that edge, turned to face the lower side |
| none | the top: `dcliff01` where HGSS shows its beige cliff top, its side-wall rock (`dwall_e` / `dwall_w`) where it shows a wall tier, black where it shows the dark above its walls |

Walkable cells keep HGSS's render, with the wall pixels its slant laid on them painted back as floor
(`droad01` at HGSS's own phase) or water. Ledges, boulders, stairs, exits and water keep HGSS's render.
[Before and after, Route 45 side](evidence/assemble/route45-side-before-after.png) ·
[Route 31 side](evidence/assemble/route31-side-before-after.png).

Both maps share one tileset pair of their own, `gTileset_DarkCavePrimary` and `gTileset_DarkCave`.
On the grid the two maps hold 1,291 distinct 8x8 tiles; a Gen 3 pair holds 1,008 in 13 banks of 15
colours. `pack.py` fits them with fitted palette banks and reuse of real tiles (a pixel whose
material class differs costs heavily, so a wall edge is only drawn by a tile with the same edge):
1,008 tiles, 550 metatiles ([pack.json](evidence/pack.json)). Against `assemble.py`'s art, about 98% of
pixels are exact and 99.98% within two RGB555 levels. Every cell is one bottom layer under the player.

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
python3 tools/gba/maps/dark_cave/assemble.py PHG
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
