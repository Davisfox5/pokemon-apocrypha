# Mt. Mortar: four floors from HGSS, the cave method

Owner review pending. Engine branch `claude/mt-mortar` (stacked on `claude/ice-path`). Maps
`MtMortar_1F_Entrance` (id 66, 96x64), `MtMortar_1F_Back` (67, 75x88), `MtMortar_2F` (68, 64x64),
`MtMortar_B1F` (69, 64x96), in HGSS's own coordinates (zones D38R0101-0104, area bank 79). 1F back
is HGSS's 96x96 matrix with its void margin cropped: Gen 3 loads a map only while
(width + 15) * (height + 14) <= 10240 (`MAX_MAP_DATA_SIZE`, fieldmap.h), and 96x96 is 12210. Its
native cell (x, y) is HGSS's (x + 16, y + 5); nothing walkable or drawn is lost.

## Review

- Whole floors, HGSS beside native: [1F entrance](evidence/review/1f-entrance-whole.png) ·
  [1F back](evidence/review/1f-back-whole.png) · [2F](evidence/review/2f-whole.png) · [B1F](evidence/review/b1f-whole.png)
- At 2x: [falls and upper pool](evidence/review/1f-entrance-falls-and-upper-pool.png) ·
  [1F west halls](evidence/review/1f-entrance-west-halls-and-mouths.png) ·
  [1F east halls and Rock Climb](evidence/review/1f-entrance-east-halls-and-rock-climb.png) ·
  [1F back north maze](evidence/review/1f-back-north-maze.png) · [1F back brown hall](evidence/review/1f-back-brown-hall.png) ·
  [1F back east](evidence/review/1f-back-east-rock-climb-and-ledges.png) · [1F back exits](evidence/review/1f-back-south-exits.png) ·
  [2F west](evidence/review/2f-west.png) · [2F east](evidence/review/2f-east.png) ·
  [B1F terraces](evidence/review/b1f-north-terraces.png) · [B1F lake](evidence/review/b1f-lake-and-ladders.png)
- [Every stair flight, HGSS beside native](evidence/review/stairs.png)
- [Doors and east-west stairs, HGSS beside native](evidence/review/doors-and-side-stairs.png) (owner review, Nov 8)
- [Route 42's four mouths](evidence/review/route42-mouths.png)
- [Gameplay gallery](evidence/review/gameplay-gallery.png) (headless mGBA)

## Art

The cave method (Dark Cave, owner-accepted 2026-11-03; Ice Path), Dark Cave's layout code used as
a library (`dark_cave/assemble.py`): each floor mapped cell by cell from HGSS's data, drawn with the
Johto routes' own pieces (FRLG rock by the routes' `rock_frlg`, the routes' road, FRLG General's
rock-edged pond, the catalog stairs S01-S05), then every colour swapped for HGSS's Mt. Mortar
colours (texture set 79: the rock ramp from `dwall_s`, `dcliff01`, `dallpeak_p`; the floor from
`droad01`). The owner's Ice Path reviews carry over: a raised floor's north edge is a drop with the
rock's light top, and an up-ladder is Seafoam's top over its foot. A wall HGSS shows facing north (its
`dwall_s`, a floor's south wall, unseen from above) never takes a south face: where the terraces would give
it one, its top comes down to the level south of it (19 cells; owner review, Nov 6).

| HGSS | Gen 3 | Art |
|---|---|---|
| Floor 0x08 | MB_CAVE | the routes' road in `droad01`'s tones; 1F back's brown hall (`droad02`) in `droad02`'s tones |
| Water 0x15 | MB_POND_WATER | FRLG's rock-edged pond in Dark Cave's cave water (owner review, Nov 6: the caves' water) |
| The falls (1F entrance, x 38-52) | MB_WATERFALL rows 19-22, the splash (row 23) water | Emerald's own animated waterfall (general's metatiles 179 crest, 185 body, 193 splash, stacked as Meteor Falls stacks them) in cave water; `InitTilesetAnim_MtMortar` copies its four frames into tiles 506-511 as Emerald animates its own. HGSS has one waterfall row (22) with real surfable water behind it; its 10-unit face, drawn top-down, lay over that pool. Now the pool stays water to row 18 and the falls climb to it (owner review, Nov 6) |
| Rock Climb walls 0x4B (north-south) / 0x4C (east-west) | MB_ROCK_CLIMB, solid | the normal wall with HGSS's climbing holds (`dr_climb`) pasted on (AGENTS.md) |
| Ledges 0x3B / 0x39 / 0x38 | MB_JUMP_SOUTH / WEST / EAST | FRLG's ledge; east-facing is the routes' west ledge unmirrored |
| Up-ladders 0x3D over 0x3C; ladders down 0x3E | MB_LADDER | FRLG Seafoam's ladder top 654 over its foot 662; its ladder into a hole 645; in HGSS's ladder wood |
| Exits 0x6F (arrow 0x65 south) / holes 0x6E | MB_SOUTH_ARROW_WARP / MB_NON_ANIMATED_DOOR | doors as Union Cave fits them (owner review, Nov 8): a lit exit is HGSS's light alone (its lit pixels, on the exit cell and the two above) before a straight wall rim, the three cells under it levelled with the rim, no hole or rubble under the light; a hole into the wall keeps HGSS's dark arch |
| Rock piles `d_rock01` / small rocks `d_rock01s` | solid | a rock formation one tier up / FRLG General's boulder in the small rocks' own rendered tones |
| Stairs (`dslope`) | MB_CAVE | each flight climbs the way HGSS's floor at its ends says. North-south flights: FRLG Seafoam's 644, Ice Path's stair, in the rock's tones (owner review, Nov 6). East-west flights cross a run of north-south wall tiers, a step down each tier's face: each column is the routes' side stair (S04 descending west, S05 east) as Dark Cave draws its east-west flights, so the steps follow the walls' angle (owner review, Nov 8) |

Lossless pack on a tileset pair of its own (`gTileset_MtMortarPrimary`, `gTileset_MtMortar`): 512
tiles (the waterfall's six animated ones in slots 506-511, all its colours in one palette bank), 211
metatiles ([pack.json](evidence/pack.json)).

## Traversal and events

- Warps are HGSS's own, index for index: four mouths to Route 42, holes and exits between 1F
  entrance and 1F back, ladders to 2F and B1F (both cells of an up-ladder kept).
- HGSS's two Strength boulders are placed (`OBJ_EVENT_GFX_PUSHABLE_BOULDER`). NPCs (Kiyo, the Mortar
  trainers), items and hidden items are recorded in `source/hgss-events/`, not placed.
- Route 42 (this tool set's own, owner review pending): native wiring only. Its three south mouths
  share metatile 619 and the north mouth has 526, each used by no other cell; they become
  MB_NON_ANIMATED_DOOR with their layer kept, the four cells' collision opens, four warps are
  appended. Route 42's own Rock Climb wall (54-56, 5) stays solid: its far side is not walkable
  natively, so a ride there would end inside rock.

## Checks

- [audit.json](evidence/audit.json) (`check.py`): every floor's decode equals the packer's image;
  behaviour, collision, elevation and layer per cell equal the ledger; every floor fits Gen 3's map
  buffer. Reach with every field move (walking, one-way ledges, Surf, Waterfall up and the falls'
  current down, Rock Climb rides) from the floor's warps equals HGSS's under the same moves: 1,665,
  2,331, 1,349 and 1,194 cells (on foot alone: 767, 2,029, 917, 371). The waterfall's animation is
  wired (frames, callback) and its cells are waterfall rows over a splash on the pool. Every warp pairs back and is a
  warp behaviour with collision 0. Route 42: 0 pixels changed; map.bin differs only at the four
  mouths' collision, attributes only at 619 and 526, map.json only by four appended warps.
- [Headless mGBA](evidence/gameplay/results.json) (`runtime.py`): 42 captures, every map frame
  rebuilt from VRAM equal to the native decode (the animated waterfall's pixels skipped; two captures
  16 frames apart differ inside it and nowhere else, so it animates). All four Route 42 mouths walked in and back out;
  every warp inside walked, the player arriving on its HGSS partner; surfing off the crest the
  current carries the player off the upper pool to the foot, and A at the foot shows Gen 3's Waterfall text; A at a
  Rock Climb wall on 1F entrance and on 1F back runs the game's Rock Climb script; an east and a west
  ledge jumped; ordinary flash save, cold reload and Continue.
- [Porymap 6.3.1](evidence/porymap/results.json) (`porymap.py`, fresh clone): all five maps open and
  save; exports equal the native decodes; no Mt. Mortar or Route 42 line changes on save.

## Not verified

- **Waterfall and Rock Climb rides.** The harness starts a new game with no party or badges, so it
  shows the game's own prompt at the falls and the wall, not the ride itself. The audit models both.
- **NPCs, items, encounters.** Not placed (Kiyo and the Tyrogue gift, the trainers, TM40, the items).
- **Visual review.** Owner review pending.

## Rebuild

```
python3 tools/gba/maps/mt_mortar/hgss_render.py PHG OUT/1f-entrance 1f-entrance    # and 1f-back, 2f, b1f
python3 tools/gba/maps/mt_mortar/hgss_events.py PHG gba/art/mt-mortar/source/hgss-events
python3 tools/gba/maps/mt_mortar/assemble.py PHG ENGINE
python3 tools/gba/maps/mt_mortar/pack.py ENGINE
python3 tools/gba/maps/mt_mortar/install.py ENGINE
make -C ENGINE -j8
python3 tools/gba/maps/mt_mortar/check.py ENGINE
python3 tools/gba/maps/mt_mortar/runtime.py ENGINE OUT_DIR
python3 tools/gba/maps/mt_mortar/porymap.py ENGINE PORYMAP_BINARY
python3 tools/gba/maps/mt_mortar/review.py ENGINE OUT_DIR
```
