# Olivine City — rebuilt from independent assets

The owner rejected the earlier full-overview palette conversion with prefabs.
This pass replaces that approach: HGSS supplies geography and design references;
the actual map is assembled from independent architecture, terrain and props.
See [the complete rebuild record](evidence/rebuild/README.md) and the
[city playbook correction](../../../docs/GBA_CITY_BUILDING_PLAYBOOK.md#owner-correction-after-the-first-olivine-pass--2026-10-20).

![Actual native rebuilt city](evidence/native-map.png)

## What is reconstructed

New transparent Gym, reusable residence (three placements), café, lighthouse,
ferry terminal and sailboat masters. Independent native modules provide fan-cut
stone paving, cliff caps/faces, lawn, sand, water, wood decks, curbs, pickets,
lamps, flags, signs, parasol tables, shore rocks, stairs and the lighthouse ramp.
The accepted Center, Mart and tree masters remain protected. All original
screenshot foliage is gone; there are 144 complete shared trees with distinct
roots. No original overview raster is read by the rebuild assembler.

Terrain, transparent buildings, roof coverage and collision remain separate.
Receiving joins include the Mart/lamp clearance, lighthouse/sign spacing,
forest/roof palette overlap, upper stairs and actual festival gate. The old
trace's visible cliff/fence bypasses are corrected and recorded by coordinate.
Partial native path and quay edges are completed to whole cells, including the
8px east edge adaptation at x640 and the central pier at x448.

## Source and evidence

Engine branch: `codex/olivine-goldenrod-playbook-20261019`,
[draft PR23](https://github.com/Davisfox5/pokeemerald-expansion/pull/23).
Thirteen Porymap sections retain IDs63–75 and their dimensions. Previous cities
and their native source remain untouched. `source/rebuilt/` holds generated
original architecture, converted native masters, independently drawn modules,
placement contours and provenance. The assembly is native tile art, not a
runtime screenshot. Its derived atlas uses 1,270 glyphs; the largest buffered
16×16 view needs376 of1,008 slots, with a10,670-byte cache.

`evidence/rebuild/` retains the rejected before image, isolated native asset sheet,
reference/before/after building and terrain contexts, native edit/collision
records, reproduction checks and latest source/build identities. The main evidence
folder contains numbered grids, a cell ledger, actual Porymap exports, gameplay,
walking clips and ordinary-save tests. Native/functional success does not imply
owner visual acceptance.

A pre-existing remote `codex/olivine-city` branch (`506860f6`) with other
Ecruteak/Olivine work remains unchanged. This separate pass must be reconciled
with it before merging; it does not supersede that work.

## Scope

Exterior art/traversal review only. No interiors, Lighthouse floors, Gym mechanics,
healing/shop services, NPCs, encounters, operational ferry or route/destination
connections. Doors and route mouths remain closed. Water, flags and boats are
static. HGSS overview projection and hidden ground are interpreted, not extracted
DS collision/elevation. Cliff contours and partial squares are adapted to the
native grid and documented. Hosted Actions remains disabled; verification is local.

## Editing and reproduction

Current native source is authoritative. Never replay the rejected `author.py`
or first registration over committed maps. `rebuild.py` is a guarded reconstruction
patch from engine `c996146b` and hub `8fb82f73`, meant for an isolated baseline
worktree only. It uses the retained new component library, not the original
map raster. Current ordinary edits must preserve the newer native work.

After native edits:

```sh
python3 tools/gba/maps/olivine_city/stream.py ENGINE
python3 tools/gba/maps/olivine_city/review.py ENGINE ACTUAL_PORYMAP_EXPORTS
make -C ENGINE -j8 TOOLCHAIN=TOOLCHAIN
python3 tools/gba/maps/olivine_city/runtime.py ENGINE NEW_OUTPUT --toolchain TOOLCHAIN
python3 tools/gba/maps/olivine_city/verify_frames.py NEW_OUTPUT
python3 tools/gba/maps/olivine_city/film.py ENGINE NEW_FILM_OUTPUT TOOLCHAIN
```

Use the established ARM14.2.1/newlib, Porymap6.3.1 and mGBA0.10.5 setup.
No ROM, save, toolchain or emulator binary is committed. Historical
`source/reference-ground.png` belongs to the rejected first pass and is not an
input to current reconstruction or native rendering.
