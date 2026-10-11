# Connected Johto map rebuild

Routes 29, 30, 31 and expanded New Bark reuse the owner-approved October 11
Cherrygrove synthesis. This is an isolated native GBA map revision for visual
review. It does not complete Chapter 1 scenes or furnish the provisional interiors.

## Latest corrections

- Replaced compressed rock bars and rotated faces with real HGSS low ledges,
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

Ledges, stairs, Route 30 cliff modules and the plateau bridge are cropped at native
scale from `../claude-routes/references/route29-hgss.png` and `route30-hgss.png`.
Dark Cave and the vertical rock divide use `../hgss-connections/references/route31-hgss.png`.
The measured cliff outline/tiers are retained; repeated plateau and straight-face
materials keep the graphic within the GBA tile budget. Its colors follow the
Cherrygrove warm rock palette, with black/gray reserved for the cave entrance.
Tall grass uses the recovered HGSS egrass material through `johto_cohesion.art`.
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

Final verification: 1,665 independent boundary/surf cases, all travel/door/stair
assertions, 1,200 ordinary grass steps, save/cold reload/Continue, and 512 frames
of animated water all pass on ROM `00aa8eae76902bbcd028ba8b96db48b2f351ace1b2aac3bd3f0e223420d57bb2`.

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
```

Compile the ROM, then run `verify.py ENGINE OUTPUT --toolchain TOOLCHAIN` and
`verify_extra.py ENGINE OUTPUT TOOLCHAIN`; each output directory must be new.
`preserve.py` writes the standalone patch from the named isolated engine.
`reproduce.py FRESH_DESTINATION` applies it and compares all changed source files.
The scripts do not launch a desktop emulator or overwrite an owner save.

Next: owner review of the updated native art and route geometry. Campaign events,
NPC placement, furnished interiors and full Violet City remain separately scoped.
