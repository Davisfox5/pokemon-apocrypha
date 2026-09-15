# Cherrygrove City, Claude's independent build

2026-09-15. An independent Cherrygrove exterior for the GBA pokeemerald-expansion
project, built from the portable **workbench** preset. Nothing here continues
another agent's reconstruction: the layout, the tilesets, the door animations and
the resident placements were made for this build. The workbench's character
graphics (custom Gold, Silver and Kestra, five Johto residents, five regional
samples) are used as registered, with no pixel changes. Production `game/` and
every earlier preview are untouched.

Owner direction on 2026-09-15: the town must look almost exactly like the Gen 4
HGSS Johto games, in 2D rather than 3D. This revision replaces the earlier
Gen 3 style pixel art with scenery derived from HGSS itself (see Art below).
Revision 3 (same day) answers the owner's nineteen pinned review notes: 16 px
doors, the whole gable roof, trunks under every tree and the dense HGSS forest
lattice, the cliff turning south at the town's edge as in HGSS, clean rocks,
HGSS-style tulip beds and fences, a plank pier and readable rowboats, a clean
Mart sign, Gold's sprite rebuilt from the HGSS hero, and an animated sea.

## Review

- Playable package: `tools/vendor/gba/Cherrygrove-claude-preview.zip` (ROM and
  matching ordinary save, ignored by git). Load both together and choose
  **CONTINUE**. The player starts outside the front door at (49,14). A fresh
  **NEW GAME** starts at the same spot.
- [Walking tour captured in-game](evidence/walking-tour.gif) and the
  [four-view board](evidence/in-game-tour.png).
- [Twelve conversations](evidence/dialogue.png), [places around town](evidence/places.png),
  [door animations](evidence/doors-in-game.png), [title screen, Continue, cold reload and Mart](evidence/save-continue.png).
- [Whole exterior](town-overview.png), rendered from the packed engine tiles
  (no residents), the [painted ground layer](evidence/ground-layer.png), plus
  the [Route 30](route30-stub.png) and [Route 29](route29-stub.png) stubs.
- Side by side with the source: [HGSS Cherrygrove render](../johto-v1/references/cherrygrove-hgss.png).

## Art: HGSS in 2D

The reference is the 1:1 top-down render of HGSS Cherrygrove that already lives
in the repository. It is native scale (one 16 px cell per movement tile: the
flowers, fence pickets and tree rows land exactly on a 16 px grid), so scenery
can be lifted at exact pixel size and the DS renderer's own lighting comes with
it (the rendered grass is (104,208,152), darker than the raw grass texture).

- **Buildings** are the HGSS models as they appear from above: the skylight
  house, Gold's gable house, the orange Pokemon Center with its portico and Poke
  Ball, the blue Mart with its flag sign. Each is cut from the render, cleaned of
  neighbours and its ground shadow, and nudged three or four pixels so the door
  sits inside one movement cell (HGSS models do not sit on the tile grid). The
  Mart's sign is a separate prop that stands on the lane as in HGSS. Homes are
  five cells by five, the Center six by six, the Mart five by four; each is
  reduced to a 15-colour bank with the window glass and doors protected.
- **Ground** is painted at pixel level in the render's sampled colours: flat
  mint grass with sparse specks, the tan sand path with its speckles and the
  mossy shadow rim measured on the render, the pale rippled beach (the render's
  own 32 px ripple), and the 32 px sea texture. Every material boundary gets the
  measured rim profile (grass-path shadow, beach-grass pale rim, sand-sea foam and
  shallow-blue gradient, cliff-foot foam) along a gently wobbling edge.
- **Trees** are the HGSS `tree01` texture from the DS data at its rendered size,
  in the render's tones, over a ground shadow, planted in the HGSS lattice
  (32 px rows and columns, alternate rows offset one cell). Blossom trees are a
  palette recolour of the same tiles.
- **Cliff, rocks, tulip beds, picket fences, daisies, rose hedge, planters,
  mailbox, signpost** are lifted from the render at native scale.
- **Apocrypha additions**: the fishing pier is built from the HGSS bridge plank
  texture with log posts, the two rowboats, benches and lanterns are original
  pixel art, and the teal-roofed transplant home is a palette recolour of the
  HGSS house.
- **Sea animation**: the primary tileset's callback cycles eight frames over the
  68 sea tiles (the HGSS base water with its sparkle layer drifting east), so the
  bay moves as it does on the DS ([sea-animation.json](evidence/sea-animation.json)).
- **Gold's sprite** is the HGSS hero's twelve walking frames (north, west, east,
  south idles and steps) in the workbench's Johto cast frame layout
  (`gold_sprite.py`); his palette is the HGSS one.

Palettes: primary banks 0-5 hold the terrain (ground, sea, cliff, trees, flowers
and fences, rocks) and are shared by the route stubs; secondary banks 6-11 hold
the houses, the teal recolour, Center, Mart, blossom recolour and wood props.
Tile use is in [build-report.json](build-report.json); the primary tileset is
our own, with its own animation callback for the sea.

Provenance: original designs and art are Game Freak / Nintendo / Creatures;
this is a read-only derivation for the Apocrypha reconstruction. Sources and
hashes are in [provenance.json](provenance.json).

## The interpretation

Geography follows HGSS Cherrygrove: open sea to the west under the brown cliff,
a concave beach down the west side, Route 30 leaving north beside the shops and
Route 29 leaving east past the homes. On top of that, the design bible's
ten-years-on additions: a blossom park with benches and lanterns, a weathered
fishing pier with two idle boats and drying nets, a small timber lookout under
the cliff, and one newer teal-roofed home for a transplant family by the
waterfront. No statue or shrine to Gold; a plain nameplate on his door and a
worn sand yard beside the house where he and Silver have just finished a battle.

Town is 60x34 metatiles. Six buildings: player's home by the Route 29 lane,
Gold's gable house with the yard, the old guide's house near the beach now a
neighbour's, the transplant home by the pier, the Mart and the Pokemon Center
along the north lane.

## Residents

Twelve walkers, all ordinary engine movement with collision: Gold wanders his
yard, Silver paces a square beside him, Kestra walks the lane outside the
player's home, a woman keeps the pier, a man stands by the shops, a boy plays
in the park, a girl walks the beach; the Hoenn visitor is on the sand, Kanto on
the Route 29 lane, Johto outside the Center, Sinnoh at the lookout and Unova in
the park. Dialogue is ambient and lore-checked against `DESIGN.md`: Silver is
seen, not spoken to (pressing A gives narration), Gold is content about losing
the friendly battle, Kestra is starstruck, visitors make no travel-route claims.
No flags or variables are used.

## Source

- `tools/gba/maps/claude_cherrygrove/hgss.py`: every HGSS-derived piece (crop
  boxes, cleaning, door alignment, the tree from the DS texture). `ground.py`:
  the pixel ground painter and rim profiles. `banks.py`: 15-colour bank
  reduction and recolours. `art.py`: the original wood props. `layout.py` is the
  town plan, `cast.py` residents and text, `pixel.py` the indexed canvas.
- `build.py`: paints ground and objects, dedupes 8x8 tiles (with flips) into the
  `cherrygrove` primary and secondary tilesets, writes metatiles, attributes,
  palettes, the town and stub layouts, warps, signs, object events, scripts, the
  new-game spawn, the six door animations, the sea animation frames and engine
  callback, and Gold's sprite.
- `runtime.py`: generated libmGBA harness (write, read, menu, walk phases).
  `evidence.py`: structure BFS, movement analysis, boards and GIF. `preserve.py`:
  source patch and package. `export.py`: editable source art.
- Editable sources: `source/*.png` (RGBA) and `source/*.idx.png` (4-bit indexed
  with the exact bank palette), `source/palettes/*.pal` (JASC), `source/ground.png`,
  `source/manifest.json`.
- Standalone engine patch: `gba/claude-cherrygrove.patch`, applied on top of the
  workbench preset (`python3 tools/gba/portable.py --preset workbench ...`).

## Porymap

The town is a uniform Emerald-format project, so Porymap 6.3.1 opens the
workbench directly (`porymap.project.cfg` and `porymap.user.cfg` in the
checkout) and renders both custom tilesets, the metatile picker, collision and
events: [map view](evidence/porymap-map.png), [collision view](evidence/porymap-collision.png).
`tools/gba/maps/claude_cherrygrove/porymap/verify.js` is a Porymap custom
script that reads the map back through Porymap's parser and logs a summary:
60x34, 699 passable cells, all six door cells passable at elevation 3, the spawn
passable, and 532 of 542 sea cells blocked (the ten open ones are the pier and
lookout decks), which matches the build's structure evidence. The editor
round-trip is proven on these exact files: File > Save was triggered in Porymap
through System Events menu scripting (Accessibility permission for the app
hosting the shell; no keystrokes, no focus change), Porymap rewrote `map.json`,
`layouts.json`, `map_groups.json`, `map.bin` and `border.bin` byte-identical to
the generator's output, and the rebuilt ROM hashed the same as before
([porymap-roundtrip.json](evidence/porymap-roundtrip.json)). The window
captures were taken by window id, so they work while Porymap is behind other
windows. Porymap has no headless mode and its script API has no save call, so
the build pipeline stays scripted and Porymap is used for editing and inspection.

## Verified

Built with ARM GNU 14.2.rel1 and tested with libmGBA in a fresh emulator process
per phase. Hashes binding the tested ROM, the packaged save and the patch are in
[build.json](evidence/build.json); tile/metatile counts in
[build-report.json](build-report.json).

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

## Limitations

- Buildings are 15-colour reductions of the render's gradients; the Center's
  roof shading is slightly flattened.
- The offshore rock islands and the northeast pond of HGSS are not built; the
  bay has grey boulders instead.
- The lookout deck and drying nets from the first revision were removed at the
  owner's request; the pier and boats remain as the design bible's waterfront.

## Reproduce

From the repository root, with the workbench built as in
`docs/GBA_REMOTE_HANDOFF.md` (use the darwin-arm64 toolchain folder on a Mac):

```sh
python3 tools/gba/maps/claude_cherrygrove/build.py tools/vendor/gba/claude-cherrygrove
make -C tools/vendor/gba/claude-cherrygrove -j4 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi"
python3 tools/gba/maps/claude_cherrygrove/runtime.py tools/vendor/gba/claude-cherrygrove tools/vendor/gba/claude-check-NN
python3 tools/gba/maps/claude_cherrygrove/evidence.py tools/vendor/gba/claude-cherrygrove tools/vendor/gba/claude-check-NN
python3 tools/gba/maps/claude_cherrygrove/export.py
python3 tools/gba/maps/claude_cherrygrove/preserve.py tools/vendor/gba/claude-cherrygrove tools/vendor/gba/claude-check-NN
```

Or apply `gba/claude-cherrygrove.patch` to a fresh workbench checkout with
`git apply --binary` and build.
