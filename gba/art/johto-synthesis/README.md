# Connected Johto map rebuild

Routes 29, 30, 31 and expanded New Bark reuse the owner-approved October 11
Cherrygrove synthesis. This is an isolated native GBA map revision for visual
review. It does not complete Chapter 1 scenes or furnish the provisional interiors.

## Latest corrections

- Route 31's central divider, southern rim and nearby jump ledges now use
  standard Emerald general 0x075/0x07c/0x076/0x087 in the approved HGSS browns.
  The east-facing wall uses the real directional tile; the southern rim uses
  the native front face. The existing two-course footprint is preserved.
- Both stair crossings use original gray Emerald 0x0af/0x0cf, verified in the
  Mossdeep cliff stairway. North/south stairs retain the original orientation;
  the east/west crossing turns the tread pattern 90 degrees and is now mirrored
  left to right as requested. No rescaling.
  Route 30's adjoining rock strip and stair cells match. Route-specific bank 8 preserves
  the approved five-color rock palette and native gray stairs.
- All collision, behavior and ground-cell arrays match `522b72e` exactly.
  The pond position, complete adjacent trees and walkable crossing remain.
- Moved the pond north one whole tile (16 pixels), including its shoreline,
  water behavior and collision. Its southern bank now has a grass strip between
  the water and dirt path, and its north bank meets the trees.
- Aligned Dark Cave's lowest rock course and its entire exposed base at native
  pixel row 215. Filled donor transparency holes, including the grass notch right
  of the entrance. The HGSS arch is retained over a short warm shadow ramp into
  the approved dirt texture.
- Moved the cave sign down to (51,14) as a freestanding prop and repaired the rock
  behind its previous position. The sign's collision and interaction move with it;
  the cave warp remains (52,13). The later pond/divider correction above is the only other geometry change.
- Three foreground tree crowns retain complete pixels over real rock lower tiles,
  now covering 36 backing quadrants. No lawn-colored crown background remains.
- Replaced the noisy continuous grass material with native Emerald blade
  silhouettes, a four-value Johto green ladder and transparent local ground.
  Distinct clumps supply the edge transition without a rectangular texture mask.
- Replaced jump ledges and their end/corner pieces with actual Emerald tiles,
  recolored to warm Johto rock outside the current Route 31 correction. Grass and path remain visible around their
  curved outlines. All 95 one-way ledge cells retain their previous behavior.
- Reused the HGSS cliff foot texture at Dark Cave. Removed exterior
  donor-ground/tree residue and cool fringe colors from the other rock cuts.
  The small Route 30 bridge has a traced outline that preserves all its planks.
- The preceding revision replaced compressed rock bars and rotated faces with HGSS
  directional cliff faces, wooden steps and the Dark Cave arch. The cave entrance
  retains warp (52,13); its dirt apron now reaches the threshold.
- Route 31 retains the reference's stepped terraces, pond divide, bridge and
  southern rock rim/stairs. The plateau and unfinished eastern continuation are
  inaccessible. The bridge is the only walkable crossing of the rock divide.
- Restored Route 30's long northern divider, its actual small plateau bridge and
  the eastern passage through tall grass. Restored the lower rock band, both stair
  flights and the southern jump ledge. The approved town approach is appended to
  the original core rather than overwriting its last twelve rows (height 86).
- Windmills stand on grass beside the streets, with collision at their pole bases.
  Roofs retain the approved rear/side overhang treatment and explicit wall bounds.
- The closed Route 46 continuation and the lookout cliff remain blocked. Negative
  reachability tests cover unavailable areas and mandatory route crossings.

## Art and native integration

Buildings, complete green/pink trees, ground, shores and animated water come from
`../cherrygrove-synthesis/`. No resized Gen 4 town image is used as the ground map.
The accepted laboratory comes from `../johto-native-refinement/native/institute.png`;
its palette is preserved in `references/native-base/`.

Other stairs, Route 30 cliff modules and the plateau bridge are cropped at native
scale from `../claude-routes/references/route29-hgss.png` and `route30-hgss.png`.
Dark Cave uses `../hgss-connections/references/route31-hgss.png`. The central
divider and southern rim use standard Emerald directional rock; the crossing/seam
stairs use Emerald general 0x0af/0x0cf. Rock uses the approved HGSS colors; stairs keep the original gray. Route 114 bridge decking was inspected and rejected
as the stair donor; the final source is the verified Mossdeep cliff stairway.
The measured cliff outline/tiers are retained; repeated plateau and straight-face
materials keep the graphic within the GBA tile budget. Its colors follow the
Cherrygrove warm rock palette, with black/gray reserved for the cave entrance.
Tall grass and low ledges now use Emerald's `primary/general` metatiles via
`johto_synthesis/terrain.py`; see `terrain-provenance.json` for donor IDs/hashes.
Native blade silhouettes retain their source geometry with added blade-face/tip
highlights. Emerald lawn pixels are transparent, revealing the approved Johto
ground. Only ledge graphics changed; jump direction and collision did not.
Source references and their existing provenance are retained in those directories;
Pokemon map graphics originate with Nintendo/Game Freak, with render credits in
those packages. This revision does not change their reuse rights.

Graphics are packed as native 4bpp tiles, palettes and metatiles. Doors use separate
16-tile animation space (1008..1023). Shared animated tiles occupy 1..92. The shared
primary is repacked, while every pixel and metatile ID in approved Cherrygrove is
checked for exact equality. Connected camera windows resolve identical tiles,
palettes and behavior from both maps. Other regional towns retain their independent
primary tilesets and earlier artwork.

Existing map IDs 0..27 remain stable. New Bark and the route/interior additions
occupy 28..40. Old regional preview stubs are retained as 41/42 so Sandgem/Floccesy
return warps remain valid without putting preview portals on the real Johto roads.
All warp destination IDs are checked. Existing encounter tables and the optional
Route 29 Potion flag are preserved. Current source still uses the established
empty-party encounter guard; this map build is not a new battle progression test.

## Evidence

`evidence/` contains:

- `route29.png`, `route30.png`, `route31.png`, `new_bark.png`: native decoded maps.
- `runtime-review.png`: captures from the background libmGBA instance.
- `terrain-review.png`: previous/current background captures at identical cameras.
- `cave-review.png`, `route31-crowns-runtime.png`: latest Dark Cave revision,
  captured in the background game, including the rock/tree junctions.
- `divider-review.png`: before/after native crossing and southern junction captures.
- `emerald-rock-baseline.json`: full-map geometry hashes from `522b72e`.
- `emerald-rock-pixels.json`: 22 packed-tile samples match donor rock/stair pixels
  after applying the approved palette, excluding donor lawn replaced by local ground.
  The complete Route 31 render matches the approved preview plus stair flip.
- `town-rock-baseline.json`: historical geometry hashes before the previous pass.
- `divider-baseline.json`, `divider-structure.json`: scoped geometry and pixel
  preservation against `5d50fbb`, pond position, cliff/crossing collision and 13
  complete adjacent trees; current checks additionally enforce full geometry
  equality against `522b72e` and allow only the adjoining northern rock/stair strip in Route 30.
- `cave-structure.json`: 36 rock-backed crown quadrants, complete tree pixels,
  aligned base, shaded dirt threshold, moved sign and unchanged other maps.
- `route31-cave-sign-runtime.png`: the relocated sign displaying its original text.
- `terrain-geometry.json`: matching solid, behavior and ground-cell hashes against
  the earlier accepted-layout revision `1016f4a6`, retained as historical evidence.
  Current geometry changes are recorded by the divider checks above.
- `integration.json`: tile/metatile use, complete-tree placement and connected windows.
- `structure.json`: paths, doors, forbidden areas, mandatory crossings and jump behavior.
- `runtime.json`: ordinary travel/door/stair checks, sustained grass walking,
  ordinary save, cold reload and title-menu Continue.
- `extra-runtime.json`, `collision-runtime.jsonl`: independent boundary/surf cases
  and animated-water/static-VRAM verification, tied to the ROM hash.
- `patch.json`, `reproduction.json`: patch identity and fresh source reproduction.

Earlier debug-harness attempts with hundreds of forced warps in one session could
hit an engine allocation assertion. Collision cases now start independent new games;
ordinary walking is separately exercised for 1,200 grass steps in one session.
No desktop emulator was launched. Porymap interaction was blocked by the locked
Mac session, so a fresh Porymap UI reload/save is not claimed.

Latest verification: all 267 Route 31 boundary/surf cases (25 surf), all ordinary
travel/door/stair assertions, 1,200 grass steps, save/cold reload/Continue and
512 animated-water frames pass on ROM
`8121b58445162bfb3467567ce9ed97dbdfcc1f438202bb57c27837a233b3bca6`.
The boundary rerun is scoped to Route 31 (`verify_extra.py ... --map 29`);
Dark Cave and other maps remain pixel-identical except Route 30’s matching
northern rock and stairs. All geometry matches `522b72e`. Both crossing directions, cliff blocking and
the shifted water edge were also walked in the ordinary suite. The previous
all-map boundary run remains preserved in `74b13f5`. Route 31 uses 911/1008
scenery slots; the 16 door-animation slots are separately reserved.

The first runs exposed a harness fault: injecting position-reading engine calls
during a warp corrupted the lab return. The ordinary suite now polls the same
position fields directly from emulator memory. All travel assertions pass on the
final ROM, including lab return and cave entry/return. Cave sign dialogue is
explicitly opened and closed. Door animations remain byte-identical to `6ce0635`;
the cave palette and Route 31 rock bank are excluded from unrelated door palette selection.

## Source and reproduction

Worktree branch: `codex/johto-native-refinement`.
Engine: `tools/vendor/gba/johto-synthesis-work` (ignored; main `game/` unchanged).
Portable source patch: `gba/johto-synthesis.patch`, standalone against
`f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`.
It includes the preserved Cherrygrove/other preview work; do not stack it on top
of the Cherrygrove patch. No ROM, save, toolchain or emulator binary is tracked.

Apply to a clean engine checkout at that base, then use the established GBA
compiler commands in `docs/GBA_BASELINE.md`. The root `make build` is not this build.
Local verification used Arm GNU 14.2.rel1, Python/numpy/Pillow and Homebrew libmGBA.

To regenerate art, restore the approved Cherrygrove patch at
`tools/vendor/gba/cherrygrove-synthesis-work` first. From the repository root:

```sh
python3 tools/gba/maps/johto_synthesis/build.py ENGINE_DIRECTORY
python3 tools/gba/maps/johto_synthesis/install.py ENGINE_DIRECTORY
python3 tools/gba/maps/johto_synthesis/preview_returns.py ENGINE_DIRECTORY
python3 tools/gba/maps/johto_synthesis/doors.py ENGINE_DIRECTORY
python3 tools/gba/maps/johto_synthesis/check.py ENGINE_DIRECTORY
python3 tools/gba/maps/johto_synthesis/check_divider.py ENGINE_DIRECTORY
python3 tools/gba/maps/johto_synthesis/check_emerald_rock.py ENGINE_DIRECTORY
```

Compile the ROM, then run `verify.py ENGINE OUTPUT --toolchain TOOLCHAIN` and
`verify_extra.py ENGINE OUTPUT TOOLCHAIN`; each output directory must be new.
`preserve.py` writes the standalone patch from the named isolated engine.
`reproduce.py FRESH_DESTINATION` applies it and compares all changed source files.
The scripts do not launch a desktop emulator or overwrite an owner save.

Next: owner review of the updated native art and route geometry. Campaign events,
NPC placement, furnished interiors and full Violet City remain separately scoped.
