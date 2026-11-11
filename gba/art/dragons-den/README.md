# Dragon's Den: two floors from HGSS, the cave method

Owner review pending. Engine branch `claude/dragons-den` (stacked on `claude/mt-mortar`). Maps
`DragonsDen_Entrance` (id 70, 32x32) and `DragonsDen` (71, 64x64), in HGSS's own coordinates (zones
D44R0101-0102, area bank 86), wired to Blackthorn at (32, 4).

## Review

- Whole floors, HGSS beside native: [entrance](evidence/review/entrance-whole.png) · [den](evidence/review/den-whole.png);
  without the grid: [entrance](evidence/review/entrance-hgss-beside-native.png) · [den](evidence/review/den-hgss-beside-native.png)
- At 2x: [entrance](evidence/review/entrance-2x.png) · den [north-west](evidence/review/den-2x-row1-col1.png),
  [north-east](evidence/review/den-2x-row1-col2.png), [south-west](evidence/review/den-2x-row2-col1.png),
  [south-east](evidence/review/den-2x-row2-col2.png)
- [Exit and ladders, HGSS beside native](evidence/review/doors-and-ladders.png) · [stairs](evidence/review/stairs.png)
- [Blackthorn's mouth](evidence/review/town-mouth.png) · [gameplay gallery](evidence/review/gameplay-gallery.png) (headless mGBA)

## Art

The cave method as Mt. Mortar has it, with the owner's Mt. Mortar reviews carried over, built by the
shared Johto cave kit (`tools/gba/maps/johto_caves/`, this cave's config `tools/gba/maps/dragons_den/cave.py`):
Dark Cave's layout code as a library, the Johto routes' pieces (FRLG rock by `rock_frlg`, the routes'
road, FRLG General's rock-edged pond, Seafoam's stairs and ladders), every colour then swapped for HGSS's
Dragon's Den colours (texture set 86: the rock ramp from `dwall_s`, `dcliff01`, `dallpeak_p`; the floor
from `droad01`; the moss from `d17_rdr1`).

| HGSS | Gen 3 | Art |
|---|---|---|
| Floor 0x08 and the den's open type-0 cells | MB_CAVE | the routes' road in `droad01`'s tones; the moss terraces (`d17_rd*`) in the moss's own green |
| Water 0x15 | MB_POND_WATER | FRLG's rock-edged pond in Dark Cave's cave water (the caves' water, owner review on Mt. Mortar) |
| Whirlpool 0x11 | solid | HGSS's own whirlpool over cave water. Gen 3 has no Whirlpool, so it blocks, and the reach model counts it solid on both sides |
| The shrine, its deck and sign; the north pier and the wreck | the deck walkable (MB_CAVE), the rest solid | HGSS's own pixels (as Route 45's cascades and Mt. Mortar's climbing holds), each group in 15 colours of its own; the cells under them are water at the lake's level |
| Shrine door 0x69 | solid, no warp | the shrine's inside (D44R0103) is an interior and is not built, as the towns keep doors whose interiors do not exist yet |
| Rocks in the lake (`sea_rock`, `sea_rock_m`) | solid | FRLG General's boulder in those rocks' own grey tones, on water |
| Small rocks `d_rock01s` / rock piles `d_rock01` | solid | FRLG General's boulder in their own tones / a rock formation one tier up |
| Stairs (`dslope`) | MB_CAVE | Seafoam's 644 in the rock's tones, climbing the way HGSS's floor says |
| Up-ladder 0x3D over 0x3C; ladder down 0x3E | MB_LADDER | Seafoam's top over its foot; its ladder into a hole |
| Exit 0x6F (arrow 0x65 south) | MB_SOUTH_ARROW_WARP | Union Cave's door (owner direction on Mt. Mortar): its arch light on a straight rim |

Lossless pack on a tileset pair of its own (`gTileset_DragonsDenPrimary`, `gTileset_DragonsDen`): 738 tiles,
315 metatiles, exact palette banks ([pack.json](evidence/pack.json)).

## Traversal and events

- Warps are HGSS's own, index for index: Blackthorn's mouth to the entrance's exit, the ladder down and
  both cells of the den's up-ladder. The shrine door's warp (HGSS's last) is left out.
- Blackthorn (another session's map): native wiring only. Its den mouth at (32, 4) has metatile 521, used
  by no other cell; it becomes MB_NON_ANIMATED_DOOR with its layer kept, the cell's collision opens, one
  warp is appended.
- NPCs (Clair, Lance, the rival, the trainers), items and hidden items are recorded in `source/hgss-events/`, not placed.

## Checks

- [audit.json](evidence/audit.json) (`check.py`): each floor's decode equals the packer's image; behaviour,
  collision, elevation and layer per cell equal the ledger; both floors fit Gen 3's map buffer. Reach with
  walking and Surf from the floor's warps equals HGSS's under the same moves: 42 and 883 cells (on foot 42
  and 144). Every warp pairs back and is a warp behaviour with collision 0. Blackthorn: 0 pixels changed;
  map.bin differs only at the mouth's collision, attributes only at 521, map.json only by one appended warp.
- [Headless mGBA](evidence/gameplay/results.json) (`runtime.py`): every map frame rebuilt from VRAM equals
  the native decode. Blackthorn's mouth walked in and back out; every warp inside walked, the player
  arriving on its HGSS partner; a surfer on the lake; ordinary flash save, cold reload and Continue.
- [Porymap 6.3.1](evidence/porymap/results.json) (`porymap.py`, fresh clone): all three maps open and save;
  exports equal the native decodes; no Dragon's Den or Blackthorn line changes on save.

## Not verified

- **Whirlpool.** Gen 3 has no Whirlpool field move; the whirlpool is solid.
- **NPCs, items, encounters.** Not placed. The shrine's inside is not built.
- **Visual review.** Owner review pending.

## Rebuild

```
python3 tools/gba/maps/dragons_den/hgss_render.py PHG gba/art/dragons-den/source/hgss/entrance entrance   # and den
python3 tools/gba/maps/dragons_den/hgss_events.py PHG gba/art/dragons-den/source/hgss-events
python3 tools/gba/maps/dragons_den/assemble.py PHG ENGINE
python3 tools/gba/maps/dragons_den/pack.py ENGINE
python3 tools/gba/maps/dragons_den/install.py ENGINE
make -C ENGINE -j8
python3 tools/gba/maps/dragons_den/check.py ENGINE
python3 tools/gba/maps/dragons_den/runtime.py ENGINE OUT_DIR
python3 tools/gba/maps/dragons_den/porymap.py ENGINE PORYMAP_BINARY
python3 tools/gba/maps/dragons_den/review.py ENGINE OUT_DIR
```
