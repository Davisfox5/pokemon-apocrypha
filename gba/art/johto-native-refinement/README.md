# October 10 original laboratory and Cherrygrove source recovery

## Owner direction and status

The owner explicitly accepted the new laboratory: “The lab look way better. Use that.”
The lab is integrated, compiled and verified. **Trees and water remain provisional:**
the owner remembers an intermediate Cherrygrove using Codex's owner-edited designs
with Claude's colors. The source chat, cloud chat and historical Git revisions were
reviewed; no exact hybrid has yet been verified. `evidence/reference-recovery/`
compares actual recovered versions. Do not describe the current Claude foliage as
owner-approved or invent a recovered hybrid. The reference question is pending.

## Changes

- Original 176x112 lab: ivory masonry, metal hip roof, skylights, ventilation,
  glazed research rooms and central glass entry. Built-in imagegen original and
  exact prompt are in `generated/`; native palette conversion is reproducible in
  `art.py`. Existing entrance remains (16,6). Source is preserved separately.
- Current foliage copies `../claude-cherrygrove/source/tree.idx.png` and its saved
  bank03 palette exactly into secondary bank12. Zero RGBA differences, no resize
  or recolor. A later `hgss.tree()` generator had diverged into a clipped screenshot
  crop; the saved source has a complete crown and trunk.
- Full 32x48 tree footprints do not overlap or spill onto paths/buildings. New Bark
  includes southern scenery padding (36x50) so the housing street's camera avoids
  the old repeating border. Protected Cherrygrove connection windows remain intact.
- Route31 pond now uses Cherrygrove's existing primary water tiles and animation,
  replacing the separately cropped freshwater tiles. The primary source is unchanged.
- Low ledges and rock modules have cleaner ends; cave uses the actual HGSS opening
  with stairs. Windmills have clean complete blades. Existing houses remain reused.
- Packing fills unused tile slots instead of counting PNG row padding as allocation.

## Verification

ARM GNU 14.2.rel1 compilation passed. Fresh libmGBA processes passed route crossings,
eight New Bark building entries/returns, encounter-grass walking, one-way ledges,
Violet gate travel, cave entry/return, ordinary save, cold reload and title Continue.
Fresh walking and pond GIFs are bound to the ROM hash. No desktop game was opened.
Native scenery encode/decode checks pass with zero mismatches; a second clean engine
reproduces all 118 changed source files. Patch reverse application passes.

The first runtime attempt exposed a test-harness bug: fixed scratch SP 0x03007c00
could overwrite live stack-resident decompressor instructions. The harness now uses
scratch space below the suspended SP. The same ROM then passed, followed by fresh
checks of the final padded map. No engine gameplay workaround was introduced.

| Map | Secondary tile slots / 512 | Secondary metatile slots / 512 |
|---|---:|---:|
| Route 29 | 290 | 229 |
| Route 30 | 442 | 393 |
| New Bark | 493 | 396 |
| Route 31 | 444 | 399 |
| Violet approach | 160 | 100 |

New Bark's remaining tile capacity is limited; preserve the accepted lab geometry.
The tree/cave/house source credits remain Game Freak / Nintendo / Creatures;
see `../claude-cherrygrove/provenance.json` and the HGSS references.

## Porymap

The private project is open in Porymap 6.3.1. UI interactions still fail to select
NewBarkTown from PetalburgCity; earlier file-watcher modal behavior remains unresolved.
No editor save roundtrip or Porymap painting is claimed. Native decoded and emulator
inspection succeeded independently. Production `game/`, owner workbench and saves
remain untouched.

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


This remains exterior art work. Interiors are provisional borrowed rooms. Route29's
gate and Route30's houses retain their existing closed behavior. Windmills are static;
pond and coastal water use the existing animation. Full Violet/Dark Cave, narrative
scenes and actors are outside this patch. The broader art revision is not complete
until the owner's Cherrygrove reference is resolved.
