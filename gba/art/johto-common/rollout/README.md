# Johto shared-family rollout

Seven-map integration of the families already reviewed. Engine **698db52a18**,
[draft PR13](https://github.com/Davisfox5/pokeemerald-expansion/pull/13),
branch `codex/johto-common-rollout`, based on approved Route 36 tree repair
**5b80e625d1**. No desktop emulator opened. Changes are pushed for review, not merged.

## Coverage

| Family | Installed / verified |
|---|---|
| Large trees T01/T02 | New Bark, Route 29, Cherrygrove, Route 30, Route 31, Violet, Route 36. Full destination-ground repair, including clipped edge fragments. Pink foliage exclusive to Cherrygrove. |
| Apricorn T03/T04 | Existing Route 29, Route 30 and Route 31 placements restored using the complete shared masters, with native foliage palettes. |
| Cut tree, item ball, Strength/Smash objects | Transparent native animation masters verified; engine object graphics and mechanics unchanged. No new item placements. |
| Center C06 / Mart M01 | Existing Cherrygrove and Violet installations retained and checked; Cherrygrove doors, entry/return and native animation frames tested. Violet services remain closed as before. |
| Gates G01a/G02 | Existing Route 36 gates retained; G01a replaces the old house-shaped gates on Routes 29 and 31. Route 29 stays closed. Route 31's existing warp destination and coordinates remain intact. Violet exception below. |
| Tall grass G00–G15 | All 724 existing tall-grass cells across Routes 29, 30, 31 and 36 use their actual north/south/west/east neighbors. Encounter behavior unchanged. |
| Low jump ledges | Existing Emerald silhouettes retained; Route 29 donor-ground fringe removed. Route 29/30/31 jumps and blocked uphill travel tested. |
| Small scenery | Existing signs, fence, flowers, windmills and water props installed or verified against the clean library; red New Bark mailboxes restored and Violet rail fringes repaired. Unplaced sign variants remain reusable library art. |
| R02 walls/stairs | All 102 approved complete rock/grass placements remain pixel-exact. The 17-piece family and mirrored references are canonical for compatible geometry; Route 36 stair direction and barriers tested. Different-height cliffs/cave caps are not silently substituted. |

Use the [regional registry](../approved-tilesets.json), linked category catalogs
and locked master hashes. Reuse transparent foregrounds over destination terrain;
R02 structural terrain deliberately includes its own approved grass cap.

## Open exception: Violet gates

The map currently uses 982 live graphics. The smallest tested lossless G02 gate
candidate needs **1,175**, exceeding the **1,008** limit. Palette reallocation and
index deduplication were attempted; a later candidate required 1,226. These results
are measurements of these candidates, not proof that every possible packing fails.
Existing Violet gates are preserved. No failed candidate was written to native
files. Further lossless packing or an explicitly reviewed map-specific art budget
is needed. Do not call the gate rollout complete.

Water/shoreline terrain, regular ground/path transition families, and other
mountain/cave geometries still need their separate category review.

## Review

- Whole-map overviews: [New Bark /29](review/overview-1.png), [Cherrygrove /30](review/overview-2.png), [31 /Violet](review/overview-3.png), [36](review/overview-4.png).
- Background gameplay: [trees, mailbox, grass and gate](review/gameplay-1.png), [ledges and services](review/gameplay-2.png), [fence, pink trees and Violet](review/gameplay-3.png).
- [Clipped-tree ground cleanup](review/edge-shadow-audit.png).
- Full-resolution map PNGs and nine coordinate-labelled before/after cell sheets in `review/`; all coordinate groups in `evidence/cell-review.json`.

Native review covered **9,561 cells /416 unique before-after pairs**. Source master
checks pass (5 trees, 56 scenery pieces; retired alternatives remain absent).
There are zero obsolete tree-shadow-color pixels in all seven decoded maps.
All seven actual Porymap exports equal the native decoder. Three additional maps
sharing the primary tileset remain pixel- and behavior-identical. Shared animation
graphics 0–92 remain unchanged. No event/script/object-graphics files changed.
Only the two replaced gate footprints change collision or behavior; exact cells
are listed in `evidence/native-audit.json`. Other map behavior/elevation is unchanged.

The ROM builds. Background mGBA runs pass real Center/Mart entry and return,
Route 31 gate entry and return, Route 29 closed gate, three routes' ledge jumps and
uphill blocking, Route 36 stairs/barriers/routes, and ordinary save/cold reload/title
Continue. Door frames and seven-map gameplay captures were visually inspected.
Native pixel review and runtime correctness are separate from owner visual approval.
ROM identity and measured results are in `evidence/summary.json`; no ROM or save
is committed. The first test used an outdated Route 31 map ID; final tests use the
current group table and pass. Gate behavior is explicitly nonanimated walk-through.

## Reproduction / source

The staged engine checkpoints are `f19232f453` (trees), `dbed35ebca` (scenery),
`391b44ffc5` (small objects and corrected Route 36 grass palette), and `698db52a18`
(gates and clipped-tree ground). Use a disposable checkout when replaying one-time
installers against their corresponding pre-stage state; never replay an old map
generator over later authored work.

Scripts in `tools/gba/maps/johto_common/`: `rollout.py`, `rollout_scenery.py`,
`rollout_small_objects.py`, `rollout_gates.py`, `rollout_shadow_edges.py` install
bounded edits. They retain native terrain outside their documented masks.
`rollout_review.py BASE ENGINE` audits native deltas; `rollout_verify.py BASE ENGINE
PORYMAP_EXPORT` checks exports and shared-primary isolation. `rollout_porymap.cpp`
is the offscreen Porymap 6.3.1 exporter. Use the existing project Qt build.
`rollout_runtime.py ENGINE OUTPUT --toolchain ARM_TOOLCHAIN` and
`r02_markup2_runtime.py` perform background mGBA checks. `rollout_publish.py ENGINE
RUNTIME_OUTPUT ROUTE36_OUTPUT` gathers evidence without binaries or saves.

`violet_gate_experiment.py`, `rollout_private.py` and `palette_fit.py` are explicitly
uninstalled packing experiments. The solver requires z3-solver in an isolated
Python environment (`JOHTO_PALETTE_PYTHON`); do not use them as production installers.
Original artwork credits remain in the linked category registries.
