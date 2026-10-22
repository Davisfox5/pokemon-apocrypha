# Blackthorn City: native exterior built from Gen 3 elements

Blackthorn as one native Gen 3 map, laid out cell for cell from HeartGold/SoulSilver's
own map data but drawn with Gen 3 pieces: each HGSS element (rock terraces, ground,
water, ledges, props, buildings) is replaced by a Gen 3 element that does the same job,
styled with Blackthorn's HGSS colours. Editable source is in
[engine PR #26](https://github.com/Davisfox5/pokeemerald-expansion/pull/26) against
`apocrypha`, branch `claude/blackthorn-city`. Owner visual acceptance is pending.

![HGSS render and the installed native map](evidence/elements/original-native.png)

## The map

| | |
| --- | --- |
| Map | `BlackthornCity`, 64x64, `gMapGroup_Cherrygrove` id 43 (Center 44, Center upstairs 45, Mart 46) |
| Primary | `gTileset_CherrygrovePrimary` (accepted Johto primary: ground, animated water, signs, Center) |
| Secondary | `gTileset_BlackthornCity`: 467 of 496 tiles (16 kept for door animation), 377 of 512 metatiles |
| Palettes | banks 0-5 the primary's; 8 Cherrygrove's Center palette; 9 the shared Mart's; 10 the Center/Mart junction; 6, 7, 11, 12 learned |

## Reference: decoded HGSS data

`tools/gba/maps/blackthorn/hgss_render.py` reads pret/pokeheartgold's packed archives
(revision `9d8b7591`, hashes in `source/hgss/hgss-render.json`): land_data chunks
104-107 (terrain model, 32x32 permission grids, building placements), area data bank 9,
the map and building textures, and zone events T30 (`source/hgss-events.json`). Its 1:1
render at true heights (`source/hgss/hgss-reference-true-heights.png`) is the review
reference. Collision, water, ledges and doors are the decoded HGSS permissions, cell for
cell. HGSS behaviour codes match Emerald's: `0x10` pond, `0x15` ocean, `0x3B` jump south,
`0x69` door, `0x6E` deep south warp.

## Element ledger

`elements.py` labels every cell from a flat top-down HGSS height map and the
permissions (`source/elements/ledger.json`, `ledger.png`): rock top or face (with its
downhill direction), ledge, boulder, other blocked, water, open, plus the ground under
it. A rock cell's terrace level is its HGSS peak height minus the town floor, so each
HGSS layer becomes one Gen 3 terrace and each face one metatile.

## Rock: three treatments

HGSS's Blackthorn cliff layers are about 1.5 tiles tall. Three ways of turning them
into one-tile Gen 3 terraces were built and compared (`evidence/elements/styles.png`,
`rock-compare.png`, `rock-detail.png`):

| Style | Rock pieces | Secondary tiles |
| --- | --- | --- |
| A | HGSS's own rock top, face band and side, compressed to one layer per metatile | 581: over the 496 budget, render only |
| B | Emerald's General rock pieces recoloured to Blackthorn's ramp | 448 |
| **C (installed)** | FRLG's General mountain set (the Gen 3 counterpart of HGSS's Kanto/Johto rock) recoloured to Blackthorn's ramp | 467 |

Style C uses FRLG's nine-slice (corners, rims, sides, front face) and its four inner
corners. Each 8x8 quadrant of a rock cell takes the piece its two edges call for, so any
terrace outline gets matching corners. As in FRLG the rock is a top-layer overlay over
plain ground: clear pixels show what lies past the edge (the lower terrace's top, or the
flattest primary block of that ground), and the cast shadow is Cherrygrove's border
grey, so cliff tiles don't multiply with the ground texture. Terrain rising toward the
south faces away from the Gen 3 camera, so those steps show as rims, the way FRLG draws
the far side of a mountain.

## Other elements

- **Ground and water**: Cherrygrove's own tiles, chosen per 8-neighbour configuration and
  texture phase (the accepted Johto vocabulary, animated sea included). Grass-water edges
  use Route 30's accepted pond rim (`source/elements/route30-native.png`, decoded from the
  engine at `apocrypha`). Ledges are Route 31's accepted jump ledge in Blackthorn's ramp.
- **Caves**: FRLG's cave mouth on the Dragon's Den and Ice Path warp cells; Ice Path's arch
  is rimmed with frost and a snow drift spills onto the grass in front.
- **Props and buildings**, redrawn as Gen 3 sprites (`sprites.py`, `source/elements/sprites.png`):
  the Gym (plank barrel roof with a dark spine, beams that rise above it and splay to the
  hall's foot, banded drum hall, red emblem panel, glass doors), the three thatched houses,
  the two dead-trunk gate posts (16 px wide, inside their own cell column), the standing
  stone. HGSS's boulder is kept as a 2x2 prop. The bridge and stairs are element pieces.
- **Walk-behind**: props and rock sit on the top layer. The packer gives every walkable
  cell with top-layer art the normal layer type (drawn above the player) and every blocked
  cell the covered type, so the player walks behind a gate post, a house's roof, the stone
  and the Gym's roof (by Surf) and stays visible around them.
- **Shared buildings**: the approved Violet Center and Johto Mart, on the HGSS warps (34,48)
  and (27,48). All 13,958 shared pixels keep their exact colours.

## Deliberate adaptations

- **Unbuilt destinations are solid**: the Gym door, three house doors, Ice Path (57,16) and
  Dragon's Den (32,4). The bridge reaches the south edge with no connection.
- The shared Mart is wider than HGSS's and closes the one-cell passage between the two
  buildings (x 30-31, y 44-48); the town stays connected around them.
- Rock-labelled slivers beside the bridge deck are its railing posts; the Gym's island is
  water under the roof and grass under the hall's foot.
- **Signs**: city, Gym and Dragon's Den signs read their HGSS text, minus Clair's name on the
  Gym sign. The tutor-house and trainer-tips signs are unscripted props.
- **Colour**: the native map holds 98.7% of the composed element art's pixels exactly in
  5-bit colour and 99.6% within one level (`evidence/elements/pack-C.json`).

## Verification

- **Native audit** (`check_elements.py`, `evidence/elements/native-audit.json`): the installed
  files decode identically to the packer; all 4,096 cells match the traversal ledger's
  behaviour, collision, elevation and layer type; all 876 open cells are reachable (868 on
  foot, 8 by Surf: the Dragon's Den ledge, as in HGSS); every walkable cell with top-layer
  art draws above the player and no blocked cell does; Center bank 8 and Mart bank 9
  palettes identical to the shared sources; existing map ids unchanged; changed files
  within scope. Coordinate grid: `evidence/elements/native-grid.png`.
- **Headless mGBA 0.10.2** (`runtime_elements.py`, `evidence/elements/gameplay/results.json`):
  views across the town; standing behind both gate posts, the west house and the stone;
  two ledges jumped and not climbed; Mart body, cliffs, pond edge and both cave mouths
  block; three signs read; Center in, upstairs, back and out; Mart in and out; Cherrygrove
  and back; ordinary flash save, cold reload in a new process, title Continue.
- **Rendering parity**: for all 33 captures the map layers BG1-BG3 rebuilt from dumped VRAM,
  palettes and BG registers match the decoded native image pixel for pixel, apart from
  CherrygrovePrimary's animated sea tiles. In the walk-behind captures BG1 covers the
  player's own cell (81 px at each gate post, 201 at the house roof, 23 at the stone).
- **Porymap 6.3.1** (`porymap.py`, `evidence/porymap/results.json`), built from source and run
  under Xvfb on a fresh clone: the city and its three interiors open with no errors;
  Porymap's export of the city matches the native decode pixel for pixel; saving the maps
  and the city's tilesets rewrote 21 Blackthorn files, all byte-identical. The only lines a
  save changes predate Blackthorn: key order in a Route 110 layout entry and three `é`
  escapes in Kanto MAPSEC names.

Engine commit `b166fa1d8689ae53918b5dd52fe5194757e273cc`, local ROM SHA-256
`5d5c163c60c7e07fcd2f8c797c07cee04d2d2f9581c27811ea594bd5550988b8` (Ubuntu Arm GNU 13.2.1).
No ROM, save, toolchain or emulator binary is committed.

![Headless capture: the player behind the west gate post](evidence/elements/gameplay/behind-gate-post.png)

Region pairs for close review: `evidence/elements/review/`.

## Not verified or not built

- No interiors for the Gym or houses; no Ice Path, Dragon's Den or Route 45 connection.
- Center nurse and Mart shop scripts are Cherrygrove's copies, not exercised. The Mart stock
  is Cherrygrove's placeholder list. Music is a placeholder (`MUS_FALLARBOR`).
- No NPCs, trainers, encounters or story events.

## Editing and reproduction

Edit `BlackthornCity` natively in Porymap; it is an ordinary single map. First-authoring
provenance (never replay over owner edits; `install_elements.py` refuses if the maps exist):

```sh
python3 tools/gba/maps/blackthorn/hgss_render.py /path/to/pokeheartgold gba/art/blackthorn-city/source/hgss
python3 tools/gba/maps/blackthorn/sprites.py
python3 tools/gba/maps/blackthorn/elements.py /path/to/engine /path/to/pokeheartgold
python3 tools/gba/maps/blackthorn/pack.py /path/to/engine C
python3 tools/gba/maps/blackthorn/install_elements.py /path/to/engine C
# after make:
python3 tools/gba/maps/blackthorn/check_elements.py /path/to/engine C
python3 tools/gba/maps/blackthorn/runtime_elements.py /path/to/engine /tmp/blackthorn-run C
python3 tools/gba/maps/blackthorn/review_elements.py C
python3 tools/gba/maps/blackthorn/porymap.py /path/to/engine /path/to/porymap C
```

`MGBA_FLAGS` and `ARM_NM` select a non-system libmgba or toolchain.

## Prior draft

The first build rendered HGSS 1:1 and needed about 1,900 tiles, so it split the city into
three connected sections and streamed their tiles with an engine city view. It is
superseded by this one and kept for reference: its tools (`build.py`, `install.py`,
`stream.py`, `check.py`, `runtime.py`, `review.py`) and evidence (`evidence/sections-draft/`),
and its engine commits on the branch before `b166fa1d`.

Original map geography, models and textures: Game Freak / Nintendo / Creatures
(HeartGold/SoulSilver); FRLG mountain pieces from the engine's `general_frlg` tileset.
Read-only derivation under the repository's existing asset practice.
