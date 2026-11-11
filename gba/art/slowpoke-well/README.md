# Slowpoke Well: three floors from HGSS, the cave method

Owner review pending. Engine branch `claude/slowpoke-well` (on `codex/azalea-town`, where Azalea is).
Maps `SlowpokeWell_Entrance` (id 51, 32x32), `SlowpokeWell_B1F` (52, 64x32) and `SlowpokeWell_B2F` (53,
32x32), in HGSS's own coordinates (zones D26R0101-0103, area bank 84), wired to Azalea's well at (48, 14).

## Review

- Whole floors, HGSS beside native: [entrance](evidence/review/entrance-whole.png) · [B1F](evidence/review/b1f-whole.png) ·
  [B2F](evidence/review/b2f-whole.png); without the grid: [entrance](evidence/review/entrance-hgss-beside-native.png) ·
  [B1F](evidence/review/b1f-hgss-beside-native.png) · [B2F](evidence/review/b2f-hgss-beside-native.png)
- At 2x: [entrance](evidence/review/entrance-2x.png) · [B1F](evidence/review/b1f-2x.png) · [B2F](evidence/review/b2f-2x.png)
- [Exits, hole and ladders, HGSS beside native](evidence/review/doors-and-ladders.png) · [stairs](evidence/review/stairs.png)
- [Azalea's well](evidence/review/town-mouth.png) · [gameplay gallery](evidence/review/gameplay-gallery.png) (headless mGBA)

## Art

The cave method as Mt. Mortar has it, with the owner's Mt. Mortar reviews carried over, built by the
shared Johto cave kit (`tools/gba/maps/johto_caves/`, this cave's config `tools/gba/maps/slowpoke_well/cave.py`),
every colour swapped for HGSS's Slowpoke Well colours (texture set 84).

| HGSS | Gen 3 | Art |
|---|---|---|
| Floor 0x08 and open type-0 cells | MB_CAVE | the routes' road in `droad01`'s tones |
| Water 0x15 | MB_POND_WATER; B1F's middle pool solid, as in HGSS | FRLG's rock-edged pond in Dark Cave's cave water |
| Puddle 0x16 (the well's bottom) | MB_PUDDLE | Emerald's own puddle (general, its nine-slice) in cave water |
| The well's round wall (`yadonwall`) | solid | the cave's rock, laid out by HGSS's heights. The round shaft is square-cornered on the Gen 3 grid |
| Stones (`yadoishi`, `d_rock01s`) / rock piles `d_rock01` | solid | FRLG General's boulder in their own tones / a rock formation one tier up. Loose stones on open floor are not drawn |
| Stairs (`dslope`) | MB_CAVE | Seafoam's 644 in the rock's tones, climbing the way HGSS's floor says |
| Up-ladders 0x3D over 0x3C; the entrance's foot 0x3C alone; ladder down 0x3E | MB_LADDER | Seafoam's top over its foot (on the entrance, the top is drawn on the wall above the foot, so the ladder is whole); its ladder into a hole |
| Exit 0x6F (B1F, into the dark) / hole 0x6E (the entrance) | MB_SOUTH_ARROW_WARP / MB_NON_ANIMATED_DOOR | Union Cave's door arch in its darks, set in a levelled wall |

Lossless pack on a tileset pair of its own (`gTileset_SlowpokeWellPrimary`, `gTileset_SlowpokeWell`): 158
tiles, 93 metatiles, exact palette banks ([pack.json](evidence/pack.json)).

## Traversal and events

- Warps are HGSS's own, index for index: Azalea's well to the entrance's ladder, the entrance's hole and
  B1F's exit, B1F's ladder down and both cells of B2F's up-ladder.
- Azalea (another session's map, `codex/azalea-town`): native wiring only. The well's ladder foot at
  (48, 14) has metatile 208, used by no other cell; it becomes MB_NON_ANIMATED_DOOR with its layer kept,
  the cell's collision opens, one warp is appended (Azalea's first).
- HGSS's Strength boulder on B1F (23, 3) is placed. Team Rocket, Kurt, the Slowpoke, items and hidden items
  are recorded in `source/hgss-events/`, not placed.

## Checks

- [audit.json](evidence/audit.json) (`check.py`): each floor's decode equals the packer's image; behaviour,
  collision, elevation and layer per cell equal the ledger; every floor fits Gen 3's map buffer. Reach with
  walking and Surf from the floor's warps equals HGSS's: 39, 360 and 567 cells (on foot 39, 279, 26). Every
  warp pairs back and is a warp behaviour with collision 0. Azalea: 0 pixels changed; map.bin differs only at
  the well's collision, attributes only at 208, map.json only by one appended warp.
- [Headless mGBA](evidence/gameplay/results.json) (`runtime.py`): every map frame rebuilt from VRAM equals
  the native decode. Azalea's well walked in and back out (the ladder stepped off and back on); every warp
  inside walked, the player arriving on its HGSS partner; a puddle walked into; a surfer on B2F's lake;
  ordinary flash save, cold reload and Continue.
- [Porymap 6.3.1](evidence/porymap/results.json) (`porymap.py`, fresh clone): all four maps open and save;
  exports equal the native decodes; no Slowpoke Well or Azalea line changes on save.

## Not verified

- **Strength.** The harness has no party, so the boulder is placed but not pushed.
- **NPCs, items, encounters.** Not placed.
- **Visual review.** Owner review pending.

## Rebuild

```
python3 tools/gba/maps/slowpoke_well/hgss_render.py PHG gba/art/slowpoke-well/source/hgss/entrance entrance   # and b1f, b2f
python3 tools/gba/maps/slowpoke_well/hgss_events.py PHG gba/art/slowpoke-well/source/hgss-events
python3 tools/gba/maps/slowpoke_well/assemble.py PHG ENGINE
python3 tools/gba/maps/slowpoke_well/pack.py ENGINE
python3 tools/gba/maps/slowpoke_well/install.py ENGINE
make -C ENGINE -j8
python3 tools/gba/maps/slowpoke_well/check.py ENGINE
python3 tools/gba/maps/slowpoke_well/runtime.py ENGINE OUT_DIR
python3 tools/gba/maps/slowpoke_well/porymap.py ENGINE PORYMAP_BINARY
python3 tools/gba/maps/slowpoke_well/review.py ENGINE OUT_DIR
```
