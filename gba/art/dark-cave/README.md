# Dark Cave: HGSS cave textures, both maps

Owner review pending (sixth pass: HGSS's rock objects, uniform pond lips, formations). Engine branch `claude/dark-cave` (stacked on `claude/route-46`), maps
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

Owner direction (October 31): no HGSS render pixels and no blended tiles; the Johto routes' own
tiles, recoloured. `assemble.py` maps the cave out cell by cell from HGSS's data and draws it with
exactly the pieces the routes use:

- **Mapped shapes** ([Route 45 side](source/assemble/route45-side-terrace-grid.txt),
  [Route 31 side](source/assemble/route31-side-terrace-grid.txt)): every floor at its own height,
  every rock cell at its tier top, both read straight down from HGSS's mesh
  (`hgss-cell-peak.npy`), plus stairs, jump ledges, water, boulders and exits. HGSS's black void is
  rock, as a Gen 3 cave's surroundings are.
- **Rock:** FRLG General's mountain nine-slice, over-rock pieces and inner corners, laid out as on the
  routes (`route46/elements.py` `rock_frlg` with the routes' `terraces`, `topped` and `south_faces`):
  every HGSS height is a terrace, ground included, and a wall has a face only toward ground that is
  really lower. A thin wall between two floors is the upper floor's edge, not a free ridge.
- **Ground:** the routes' road (Cherrygrove's sand quarter), edge to edge.
- **Water:** FRLG General's rock-edged pond (metatiles 419-431, inner corners 435-436, as in Icefall
  Cave), the lip in the rock ramp. The lip runs only where water meets ground (floor, a ledge, stairs, a
  rock object), the same brown lip on every side (FRLG's north row turned over for the south edge,
  since its own south row is a pale strip that met the side lips badly); where a wall meets the water
  the wall goes straight in, as in HGSS (owner review: consistent water borders).
- **HGSS's rock objects** (owner review: some stones were rock formations; recolour the rocks): its
  2x2 rock pile (`d_rock01`) is a small rock formation in the route rock, one tier above its floor; its
  moss rock (`d_rock01s`) is FRLG General's boulder in HGSS's moss tones (MOSS_RAMP, from its rendered
  texture), on the floor or water under it. A blocked cell HGSS paints with a floor or pool decal and
  no rock object is a pillar top, so it is rock.
- **Clean-up** (`regularise`, listed per cell in the assemble report; traversal is untouched):
  floor cells one level off the floor round them (HGSS height noise) are levelled; outer rock more
  than three cells from any floor is the rock top (HGSS shows at most three tiers before its dark);
  free-standing formations are one block; narrow rock (open ground on two opposite sides within two
  cells: the lake's diagonal outcrop, thin walls) is one tier per run, except where it meets the wider
  rock it grows from; one-cell spines and small raised bumps on a rock top are flattened; a rock nub
  with three sides lower takes the height of the rock it sticks out of, so it draws as that rock's
  rounded end.
- **Colours:** every colour is then swapped one for one: the Johto rock ramp for HGSS's cave rock
  tones (from `dwall_s`, `dcliff01`, `dallpeak_p`), the road tones for the cave floor tones
  (`droad01`) and the pond water for the cave water (`driver`) by brightness rank, the stairs' grey stone for
  the cave rock ramp, the cast shadow for the floor's darkest. The exit glows and the hole are HGSS's
  own exit art over the floor.

Earlier passes (HGSS's slanted render; HGSS's textures on the grid; the route rock over HGSS's floor)
were turned down in review.

Both maps share one tileset pair of their own (`gTileset_DarkCavePrimary`, `gTileset_DarkCave`). The
pack is lossless: 225 tiles and 119 metatiles, exact palette banks, every pixel as assembled
([pack.json](evidence/pack.json)). Every cell is one bottom layer under the player.
[Before and after, Route 45 side](evidence/assemble/route45-side-before-after.png) ·
[Route 31 side](evidence/assemble/route31-side-before-after.png).

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

The border block is the rock-fill metatile HGSS's void cells carry, so past the map edge is rock. Both maps
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
python3 tools/gba/maps/dark_cave/assemble.py PHG ENGINE
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
