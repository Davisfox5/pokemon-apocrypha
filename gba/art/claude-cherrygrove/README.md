# Cherrygrove City, Claude's independent build

2026-09-15. An original Cherrygrove exterior for the GBA pokeemerald-expansion
project, built from the portable **workbench** preset in a remote Linux session.
Nothing here continues another agent's reconstruction: the layout, every
scenery tile, the door animations and the resident placements were authored for
this build. The workbench's character graphics (custom Gold, Silver and Kestra,
five Johto residents, five regional samples) are used as registered, with no
pixel changes. Production `game/` and every earlier preview are untouched.

## Review

- Playable package: `tools/vendor/gba/Cherrygrove-claude-preview.zip` (ROM and
  matching ordinary save, ignored by git). Load both together and choose
  **CONTINUE**. The player starts outside the front door at (50,18). A fresh
  **NEW GAME** starts at the same spot.
- [Walking tour captured in-game](evidence/walking-tour.gif) and the
  [four-view board](evidence/in-game-tour.png).
- [Twelve conversations](evidence/dialogue.png), [places around town](evidence/places.png),
  [door animations](evidence/doors-in-game.png), [title screen, Continue, cold reload and Mart](evidence/save-continue.png).
- [Whole exterior](town-overview.png), rendered from the packed engine tiles
  (no residents), plus the [Route 30](route30-stub.png) and [Route 29](route29-stub.png) stubs.

## The interpretation

Geography follows HGSS Cherrygrove: open sea to the west under a sandstone
cliff, a concave beach down the west side, Route 30 leaving north beside the
shops and Route 29 leaving east past the homes. On top of that, the design
bible's ten-years-on additions: a petal-strewn blossom park with benches and
lanterns, a weathered fishing pier with two idle boats and drying nets, a small
timber lookout under the cliff, and one newer slate-roofed home for a transplant
family by the waterfront. No statue or shrine to Gold; a plain nameplate on his
door and a worn sand yard beside the house where he and Silver have just
finished a battle.

The art is drawn to Emerald's own tile grammar so it sits beside the native
grass, sand paths and animated water without looking imported: one navy
outline for built things, three or four tones per material, light from the top
left, hatched roof courses, a pale bevelled cornice between roof and wall, blue
glass in white frames, red pixel lettering on the Mart sign. Shapes and colours
are Johto: rose hip roofs with a front gable and attic window, cream boards with
dark timber posts, the orange rounded Pokemon Center with its Poke Ball emblem,
the blue Mart, round broccoli-crown trees in scalloped tiers, white picket
gardens of red, yellow and pink tulips.

Town is 60x34 metatiles. Six buildings: player's home (classic rose roof by the
Route 29 lane), Gold's house with the yard, the old guide's house near the
beach now a neighbour's, the slate-roof transplant home by the pier, the Mart
and the Pokemon Center along the north lane.

## Residents

Twelve walkers, all ordinary engine movement with collision: Gold wanders his
yard, Silver paces a square beside him, Kestra walks the lane outside the
player's home, a woman keeps the pier, a man stands by the shops, a boy plays
in the park, a girl walks the beach; the Hoenn visitor is on the sand, Kanto by
the Route 29 sign, Johto outside the Center, Sinnoh at the lookout and Unova in
the park. Dialogue is ambient and lore-checked against `DESIGN.md`: Silver is
seen, not spoken to (pressing A gives narration), Gold is content about losing
the friendly battle, Kestra is starstruck, visitors make no travel-route claims.
No flags or variables are used.

## Source

- `tools/gba/maps/claude_cherrygrove/art.py`: every scenery asset as indexed
  pixel art (palette-constrained, 15 colours per bank). `pixel.py` is the tiny
  authoring kit. `layout.py` is the town plan. `cast.py` is residents and text.
- `build.py`: composes the object canvas over a primary-ground grid, dedupes
  8x8 tiles (with flips) into the `cherrygrove` secondary tileset, writes
  metatiles, attributes, palettes, the town and stub layouts, warps, signs,
  object events, scripts, the new-game spawn and the six door animations.
- `runtime.py`: generated libmGBA harness (write, read, menu, walk phases).
  `evidence.py`: structure BFS, movement analysis, boards and GIF. `preserve.py`:
  source patch and package. `export.py`: editable source art.
- Editable sources: `source/*.png` (RGBA) and `source/*.idx.png` (4-bit indexed
  with the exact palette), `source/palettes/*.pal` (JASC), `source/manifest.json`.
- Standalone engine patch: `gba/claude-cherrygrove.patch`, applied on top of the
  workbench preset (`python3 tools/gba/portable.py --preset workbench ...`).

Palette budget: the engine loads seven secondary banks (6 to 12). Trees, blossom
trees, cliff and rocks, two house palettes, the shared shop palette and the wood
props take those. Flowers sit in ten free slots of the primary grass bank and the
beach in ten free slots of the primary path bank, so the Emerald ground tiles
keep their own colours. Water tones in the shore tiles copy the graded primary
water so foam sits on live animated water.

## Verified

Built with ARM GNU 14.2.rel1 (Linux x86_64) and tested with libmGBA from the
Ubuntu package in a fresh emulator process per phase. Hashes binding the tested
ROM, the packaged save and the patch are in [build.json](evidence/build.json);
tile/metatile counts in [build-report.json](build-report.json).

- [Runtime](evidence/runtime.json): new game spawn, all six doors in and out
  with their animations, bedroom stairs both ways, Route 29 and Route 30
  connections and returns, shoreline collision, Mart shop menu, ordinary flash
  save, cold-process reload, title-screen Continue at the saved spot.
- [Structure](evidence/structure.json): every door approach, both exits, every
  resident's start, the pier end and the lookout are reachable on foot from the
  spawn; the sea is impassable except the pier and lookout decks.
- [Movement](evidence/movement.json): seven camera views, 360 samples each at
  four-frame intervals; every visible resident's displayed OBJ VRAM frame matches
  the correct source cell for its facing, no horizontal mirroring, distinct
  palettes, never on a blocked cell; twelve conversations stop the NPC facing the
  player with the right idle frame and release afterwards.

## Reproduce

From the repository root, with the workbench built as in
`docs/GBA_REMOTE_HANDOFF.md`:

```sh
python3 tools/gba/maps/claude_cherrygrove/build.py tools/vendor/gba/claude-cherrygrove
make -C tools/vendor/gba/claude-cherrygrove -j4 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi"
python3 tools/gba/maps/claude_cherrygrove/runtime.py tools/vendor/gba/claude-cherrygrove tools/vendor/gba/claude-check-NN
python3 tools/gba/maps/claude_cherrygrove/evidence.py tools/vendor/gba/claude-cherrygrove tools/vendor/gba/claude-check-NN
python3 tools/gba/maps/claude_cherrygrove/preserve.py tools/vendor/gba/claude-cherrygrove tools/vendor/gba/claude-check-NN
```

Or apply `gba/claude-cherrygrove.patch` to a fresh workbench checkout with
`git apply --binary` and build.

## Limitations

- Interiors are the workbench's donor rooms (Littleroot and Petalburg
  layouts); only the exterior was built here.
- The route stubs are short tree-lined approaches, not Routes 29 and 30.
- Surf is not qualified; the sea is collision-blocked. Eight tiles where the
  pier and lookout decks cross the shoreline were palette-remapped to the wood
  bank (deck post gaps show wood-toned sand there).
- The lamp posts in the park draw their upper half above the player using the
  NORMAL layer type; everything else is below sprites.
- Owner visual acceptance is pending; nothing here is merged into production.
