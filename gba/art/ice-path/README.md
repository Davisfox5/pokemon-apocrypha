# Ice Path: four floors from HGSS, Dark Cave's method

Owner review pending. Engine branch `claude/ice-path` (the Mahogany stack, `claude/route-42`, and the
Blackthorn stack, `claude/dark-cave`, joined by one merge so Ice Path can open onto both Route 44
and Blackthorn). Maps `IcePath_1F` (id 62, 64x64), `IcePath_B1F` (63, 32x64), `IcePath_B2F` (64,
64x32), `IcePath_B3F` (65, 32x32), in HGSS's own coordinates (zones D39R0101-0104, area bank 76).

## Review

- Whole floors, HGSS beside native: [1F](evidence/review/1f-whole.png) · [B1F](evidence/review/b1f-whole.png) ·
  [B2F](evidence/review/b2f-whole.png) · [B3F](evidence/review/b3f-whole.png)
- At 2x: [1F west ice and halls](evidence/review/1f-west-ice-and-halls.png) · [1F east ladders](evidence/review/1f-east-ladders.png) ·
  [1F Route 44 door and ice](evidence/review/1f-route44-door-and-ice.png) ·
  [B1F crystal field and holes](evidence/review/b1f-crystal-field-and-holes.png) · [B1F lower room](evidence/review/b1f-lower-room.png) ·
  [B2F west ice](evidence/review/b2f-west-ice-and-fallen-boulders.png) · [B2F east](evidence/review/b2f-east.png) ·
  [B3F](evidence/review/b3f-whole-2x.png)
- [Every stair flight, HGSS beside native](evidence/review/stairs.png)
- [The doors on Route 44 and Blackthorn](evidence/review/doors.png)
- [Raised floors' north edges, HGSS, before and now](evidence/review/north-edges.png)
- [Gameplay gallery](evidence/review/gameplay-gallery.png) (headless mGBA)

## Art

Dark Cave's method (owner-accepted 2026-11-03), its layout code used as a library
(`dark_cave/assemble.py`): each floor mapped cell by cell from HGSS's data (heights from its mesh,
ice, ladders, exits, rock objects), drawn with the Johto routes' own pieces (FRLG rock by the routes'
`rock_frlg`, the routes' road), then every colour swapped for HGSS's Ice Path colours (texture set
76: the rock ramp from `dwall_s`, `dcliff01`, `dallpeak_p`; the floor from `droad01`).

Ice Path's own features are FRLG Icefall Cave's pieces (`seafoam_islands_frlg`), recoloured colour
for colour by brightness, never redrawn:

| HGSS | Native | Icefall piece |
| --- | --- | --- |
| Slide ice (`ice_fe01b`, permission 0x20) | MB_ICE: the player slides | 843, in the ice's own rendered tones (its texture is one flat colour) |
| 2x2 ice clusters (`d_rock01`) | blocked | the ice pillar, Icefall B1F (8-9, 4-6), its top and foot rows fitted to 2x2 |
| Single crystals (`d_rock01s`) | blocked | the crystal 679 or the ice rock 643, cut from their snow |
| B1F's four drop holes (script triggers in HGSS) | MB_MT_PYRE_HOLE | 646 |
| Ladders down / up | MB_LADDER | 645 (ladder into a hole) / 662, in HGSS's ladder wood |
| Stairs: nine two-cell flights in a one-row ice wall (floor 0x08 with the slope bit 0x06) | MB_CAVE, a flight through the wall | FRLG Seafoam Islands' ice stairs 644, set two wide as Seafoam sets them, in Ice Path's wall tones |

A crystal standing in the ice has ice under it. HGSS's exit glows are its own art over the floor.
Owner review (November 4): the stairs were left out (walkable, but drawn as wall); every flight is
now drawn. Owner review (November 5): a raised floor's north edge was drawn as a cliff face looking
south onto the raised floor; it is now a drop with the rock's light top, the pale lip HGSS shows there
(49 cells: 1F rows 13, 14 and 25, B2F and B3F row 7; [HGSS, before, now](evidence/review/north-edges.png)).
Lossless pack on a tileset pair of its own (`gTileset_IcePathPrimary`, `gTileset_IcePath`): 205
tiles, 67 metatiles ([pack.json](evidence/pack.json)).

## Traversal and events

- HGSS's permissions: floor MB_CAVE, ice MB_ICE, exits (0x6F, arrow south) MB_SOUTH_ARROW_WARP,
  ladders MB_LADDER, walls and void solid. HGSS's warps are kept index for index, including the
  second cell HGSS gives most ladders.
- **Holes and boulders.** B1F's holes drop the player to HGSS's B2F cells (12,12), (10,21), (20,10),
  (21,23). Strength boulders work as FRLG Seafoam's: a B1F boulder pushed onto a hole falls, its
  flag hides it and the flag in its `trainer_type` shows its copy on B2F, an ice stopper ("It has
  sunk in and cannot be moved."). `IcePath_1F` hides the B2F copies once. Flags 0x4E7-0x4EF,
  unused in this tree, are named for it (`FLAG_HIDE_ICE_PATH_BOULDER_n_INIT`, `_FALLEN`,
  `FLAG_ICE_PATH_FALLEN_BOULDERS_HIDDEN`). Gen 3 lets Strength push any boulder, so the B2F copies
  can be pushed (as FRLG's are); HGSS fixes them.
- Placed: five B1F boulders, four B2F copies, the B3F Rock Smash rock. Recorded, not placed: NPCs,
  items (HM07, TM72, Never-Melt Ice and the rest), hidden items, encounters
  ([source/hgss-events](source/hgss-events/)).
- `MAPSEC_ICE_PATH` (Johto). Underground, no Flash needed, as in HGSS; music MUS_CAVE_OF_ORIGIN.

## Doors

| From | To |
| --- | --- |
| Route 44 (89,9) mouth | 1F (11,58) exit |
| Blackthorn (57,16) mouth | 1F (55,40) exit |

Native wiring edits only, as on Routes 45 and 46 for Dark Cave: each mouth metatile (Route 44's 641,
Blackthorn's 551, each used by that one cell) becomes MB_NON_ANIMATED_DOOR with its layer kept, the
cell's collision opens, one warp is appended. No pixel changes ([audit](evidence/audit.json)).
Blackthorn was built in another session; this is its only change besides the Route 45 connection.

## Evidence

- **Audit** ([audit.json](evidence/audit.json)): every floor decodes to the packer's image on every
  pixel; behaviour, collision, elevation and layer match the ledger on every cell; Gen 3 reach equals
  the ledger's and HGSS's from every warp (888, 342, 696 and 162 cells); warps pair back; B1F's
  boulder flags match B2F's; Route 44 and Blackthorn change no pixel; the changed-file list is checked.
- **Headless mGBA** ([results](evidence/gameplay/results.json)): 35 captures rebuilt from VRAM equal to
  the decoded floors. Both doors walked both ways; every ladder pair; every stair flight up and back down; a B1F hole drops to its B2F cell;
  slides on 1F and B2F stop where the cells say; a B1F boulder pushed into a hole by 26 planned moves,
  its own flag set and its B2F copy's cleared; the Rock Smash rock blocks; flash save, cold reload and
  Continue.
- **Porymap 6.3.1** ([results](evidence/porymap/results.json)): all six maps open, export and save on a
  fresh clone; exports equal the native decodes; no Ice Path, Route 44 or Blackthorn line changes.

## Reproduce

```sh
python3 tools/gba/maps/ice_path/hgss_render.py PHG OUT/1f 1f      # and b1f, b2f, b3f
python3 tools/gba/maps/ice_path/hgss_events.py PHG gba/art/ice-path/source/hgss-events
python3 tools/gba/maps/ice_path/assemble.py PHG ENGINE
python3 tools/gba/maps/ice_path/pack.py ENGINE
python3 tools/gba/maps/ice_path/install.py ENGINE
make -C ENGINE -j8
python3 tools/gba/maps/ice_path/check.py ENGINE
python3 tools/gba/maps/ice_path/runtime.py ENGINE OUT_DIR
python3 tools/gba/maps/ice_path/porymap.py ENGINE PORYMAP_BINARY
python3 tools/gba/maps/ice_path/review.py ENGINE OUT_DIR
```

Source artwork: Nintendo / Game Freak / Creatures, decoded read-only from pret/pokeheartgold's
archives and pokeemerald-expansion's FRLG tilesets. No ROMs, saves or tool binaries committed.
