# R02 terrain transition refinement

[Original / previous / revised comparison](review/comparison.png) ·
[Actual gameplay](review/gameplay.png) · [Full native route](review/native-full.png)

The owner accepted the wall/stair/raised-landing direction and requested review
of the transitions between materials. This pass cleans the complete tall-grass
patch, the adjoining plateau path and the western rock contacts.

## Changes

- All 39 tall-grass cells use the approved transparent G-series masters selected
  from current north/south/west/east neighbors. Old dirt fragments are gone.
  Destination ground is independent. Root shading stays below the transparent
  blade gaps to preserve the dense grass texture without bright horizontal gaps.
- Path/lawn joins use a compact two-pixel ramp; tight turns round by at most
  three pixels. The cleaned border continues to the eastern stair approach.
- Western rock contacts gain a two-pixel lower lawn shadow and a one-pixel upper
  earth lip. These sit outside the accepted wall, never cutting holes into it or
  painting grass across the stair mouth.

The rock/stair surface and every existing tree pixel remain identical. Collision,
elevation, behavior, events and warps are unchanged. Shared source masters are
reused without alteration. This is a transition pass, not a whole-route redesign.

## Review and verification

220 comparison cells / 880 quadrants inspected, covering columns 12–33, rows 17–26.
127 native cells were recomposed. [Cell ledger](evidence/cell-review.json) and
[visual findings](evidence/visual-review.json) separate inspection from acceptance.
Coordinate-labelled sheets: [1](review/cells-1.png) · [2](review/cells-2.png) · [3](review/cells-3.png) · [4](review/cells-4.png) · [5](review/cells-5.png) · [6](review/cells-6.png) · [7](review/cells-7.png) · [8](review/cells-8.png) · [9](review/cells-9.png) · [10](review/cells-10.png).

Local ROM build passes. Porymap and independent native decode match exactly.
Headless checks pass both western stair lanes, shoulders/barriers, grass entry
and return at both boundaries, plateau path, eastern stair crossing/return,
ordinary flash save, cold reload and title Continue. Final gameplay frames were
inspected at native scale. No desktop game was opened.

[Structure](evidence/structure.json) · [Runtime](evidence/runtime.json) ·
[Porymap](evidence/porymap.png).

Native usage: 811 tiles (123 appended), 51 appended metatiles, one previously
unused palette bank. All 13 available map palette banks are now occupied; future
art additions need palette reuse or deliberate consolidation. No such repacking
was performed here.

Engine base: `833a9c4355be0b191e676963f5f8d39930560fb6`.
Engine candidate: `5b14c523c1a0688f3c291b485998bd91fd05dc86`.
ROM SHA-256: `a46e7d78dcd94a6760f36ba81a13bb54a9c71671ce8c1bdc602c2a10a719831c`.
[Draft PR #12](https://github.com/Davisfox5/pokeemerald-expansion/pull/12), still
dependent on PR #5. Production and the original Violet engine checkout are untouched.

## Reproduce

Use an isolated clean engine checkout at the exact base above:

```sh
python tools/gba/maps/johto_common/r02_transitions.py --engine /path/to/engine --install
python tools/gba/maps/johto_common/r02_review.py gba/art/johto-common/rocks/r02-transitions
# Build with serial generated then parallel gmake using the pinned ARM toolchain.
python tools/gba/maps/johto_common/r02_transitions_runtime.py /path/to/engine /tmp/r02-run --toolchain /path/to/arm-toolchain
# Export through r02_porymap.cpp, commit the engine, then collect:
python tools/gba/maps/johto_common/r02_publish.py /path/to/engine /tmp/r02-run /tmp/r02-porymap --pack gba/art/johto-common/rocks/r02-transitions --shots west-approach grass-landing-edge grass-east-edge plateau-east-approach lower-wall title-continue
```

The installer refuses an unexpected revision or dirty target files. Review must
be repeated after art changes. See the preceding [source record](../r02-refined/source/geometry.json)
for HGSS cliff texture/model provenance and the shared [scenery registry](../../scenery/catalog.json)
for G-series masks. Original game artwork: Game Freak / Nintendo / Creatures.

Other cliff families and the older eastern stair artwork remain unchanged.
HGSS vegetation spacing and grass-field shape still differ from this native map.
Owner visual acceptance of the new transitions is pending.
