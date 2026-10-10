# October 10 Cherrygrove asset reuse correction

The owner rejected the earlier generic native houses and trees. This correction
uses the actual approved Cherrygrove assets from `claude_cherrygrove.build_assets`.
It supersedes the initial local redraw committed as `f732965`.

## Artwork

- Houses, gable homes, tree crowns and blossom variants are unchanged source
  pixels, at their original size and palette. The generator asserts exact equality
  for seven exported asset families; see `evidence/cherrygrove-reuse.json`.
- The enlarged 208×80 institute assembles existing house wings around the original
  central gable. Wings reuse the existing window wall in place of extra entrances.
  Four southern residences reuse the same two house assets without scaling.
- Routes 29 and 30 reuse those buildings and the original 32×24 woodland lattice.
  Route 31's gate uses the same gable, with its door aligned to the existing warp.
- Ground, paths, trees, daisies, signs and rock texture reuse Cherrygrove artwork.
  Route 31 retains the measured landform outline with the town's grassy tops and
  rock face. The local New Bark windmills derive from its HGSS reference.
- Encounter grass remains the new native 16px blade module; Cherrygrove's lawn
  and established coastal animation remain intact.

## Validation

ARM GNU 14.2.rel1 compilation passed. Fresh libmGBA processes passed route seams,
walking in encounter grass, one-way ledges, eight town door entries/returns,
Violet gate travel, Dark Cave entry/return and ordinary save/cold Continue.
See `evidence/native-gameplay.png` for actual gameplay frames and
`evidence/campus-walk.gif` for a fresh 30-frame walking capture.
Original artwork credits: Game Freak / Nintendo / Creatures; source provenance
is recorded in `../claude-cherrygrove/provenance.json`.
The generated source matched a second clean baseline worktree byte for byte.
Cherrygrove map/scripts/primary tiles, flags, encounters and route scripts are
preserved; see `evidence/preservation.json`.

| Map | Secondary tiles / 512 | Secondary metatiles / 512 |
|---|---:|---:|
| Route 29 | 290 | 320 |
| Route 30 | 472 | 495 |
| New Bark | 292 | 388 |
| Route 31 | 485 | 506 |
| Violet approach | 147 | 110 |

Route 31 has six metatile slots left, so further additions require module reuse
or repacking. Visual acceptance remains the owner's decision.

## Porymap status

Porymap 6.3.1 has the isolated project open, but its inaccessible file-watcher
warning still disables project controls and Quit. Current attempts to dismiss
it and select NewBarkTown did not change the editor state. **Editor inspection
and save roundtrip are pending.** The Mac lock from the earlier run is no longer
the observed blocker. No Porymap painting or roundtrip is claimed.

Project:
`/Users/davisfox/.codex/worktrees/johto-native-refinement/the-omni-hack/tools/vendor/gba/johto-native-work`.

## Reproduction

Prepare `tools/gba/portable.py --preset workbench` into a fresh directory. Apply
`gba/claude-cherrygrove.patch` then `gba/claude-routes.patch` with binary patch
support and `core.autocrlf=false`. This is the routes baseline. Apply
`gba/johto-native-refinement.patch` instead of the cloud cohesion patch.
Alternatively run the native generator on the clean routes baseline:

```sh
python3 tools/gba/maps/johto_native_refinement/build.py ENGINE
python3 tools/gba/maps/johto_native_refinement/check.py ENGINE
```

Compile host tools, generate maps serially, then compile the ROM:

```sh
gmake -C ENGINE -j8 tools
gmake -C ENGINE -j1 TOOLCHAIN=TOOLCHAIN generated
gmake -C ENGINE -j8 TOOLCHAIN=TOOLCHAIN
MGBA_FLAGS='-I/opt/homebrew/include -L/opt/homebrew/lib -lmgba' \
  python3 tools/gba/maps/johto_native_refinement/runtime.py ENGINE OUTPUT \
  --toolchain TOOLCHAIN
```

This remains exterior art work. Interiors are the borrowed GBA rooms already in
the cloud proposal. Windmills and freshwater pond are static; coastal sea retains
its animation. Route 29's gate and the Route 30 houses retain their existing
closed behavior. Full Violet, full Dark Cave, campaign actors and dialogue are
not completed by this patch. Production `game/` and owner ROM/save files are untouched.
