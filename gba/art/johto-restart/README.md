## September 22 collision audit — current

Reviewed all 6,432 exterior cells across Cherrygrove and both approach maps (329 unique metatiles). Corrected 1,349 collision/elevation cells and aligned terrain behaviors: open grass, flowers, beach and deck are walkable; trees, buildings, cliffs, boats, fences and reef hazards are solid; water uses surfing elevation/behavior; seven doors retain native entry behavior. Graphics are unchanged. One visible fence at town (8,6) closes a newly accessible cliff-top strip. Latest owner edits otherwise remain intact; exact pre-audit snapshot is `tools/vendor/gba/johto-before-collision-audit-20260922`.

Current source remains `tools/vendor/gba/johto-restart-game`. New separate preview: `tools/vendor/gba/Cherrygrove-collision-20260922/Cherrygrove.gba`, matching fresh save starts at (48,20); ZIP beside the folder. The previous `Cherrygrove-live-20260922` ROM and owner save were left intact. Use the matching fresh preview save because old saves cache nearby map collision.

Validation: 288/288 representative native movement probes pass, seven building entry/exit pairs, bedroom stairs, both route round trips, pier/island barriers, ordinary save, cold reload and title-screen Continue pass. Static reachability checks cover 906 walkable cells and 1,652 combined walking/surfing cells without uncovered camera edges. The complete cell classification is `evidence/collision-audit.json`; movement proof is `collision-runtime.jsonl`, broader acceptance `collision-acceptance.json`, visuals `collision-in-game.png`; build identity is `evidence/build.json`. Standalone `gba/johto-restart.patch` regenerated and forward/reverse application verified.

Porymap was reloaded cleanly after unlock, with no unsaved marker, and the corrected map was visually verified. mGBA launched the matching `Cherrygrove-collision-20260922/Cherrygrove.gba` revision. Do not replay older map regeneration scripts. The audit script is guarded against unknown map changes and uses the exact pre-audit backup; future owner edits require a fresh snapshot and review.

## September 22 pond repair and live emulator — current

Latest owner edits were successfully saved from Porymap (80x48), backed up at `tools/vendor/gba/johto-owner-pond-20260922`, and retained in full. This resolves the older pending editor reconciliation below. Do not replay earlier regeneration scripts: the owner changed 1154 cells since the prior candidate. `fix_owner_pond_bank.py` repaired only (68..69,3..7), mirroring the left bank with native tile flips. All other 3830 cells and their pixels are verified identical. Porymap was reloaded cleanly with matching tiles and the corrected pond visually inspected.

Current source: `tools/vendor/gba/johto-restart-game`; live ROM/save: `tools/vendor/gba/Cherrygrove-live-20260922/Cherrygrove.gba` and `.sav`, start beside the pond at (67,10). Build, save, cold reload and ordinary Continue pass in `tools/vendor/gba/johto-pond-live-runtime-20260922`. mGBA app is `/opt/homebrew/Cellar/mgba/0.10.5_2/mGBA.app`. Preserve any save the owner makes there. Native screenshot `gba/art/johto-restart/evidence/pond-bank-fixed.png`; current build identity in evidence/build.json. Prior exhaustive boundary/movement results describe earlier map state and should not be asserted for subsequent owner edits without a new check.

## September 22 direct owner-map revision — editor reconciliation pending

The owner authorized bench reversal/north one tile, upper southeast house north one tile, barge east **one** tile, aligned forest/route boundaries, and rocks stopping surfing at the western water edge. Implemented by `tools/gba/maps/edit_owner_cherrygrove.py` directly over the exact turn-start snapshot `tools/vendor/gba/johto-owner-direct-20260922`, not the rejected reconstruction. Current built source is `tools/vendor/gba/johto-restart-game`; candidate package is `tools/vendor/gba/Cherrygrove-owner-direct-20260922.zip`.

**Do not reload or overwrite Porymap yet.** It acquired an unsaved marker during work. The user continued interacting with it, so two attempted saves were rejected by the control tool. An asynchronous question asks the owner to pause editing and reply "paused". No save/reload has succeeded. Before attempting that save, the complete candidate map/layouts/events/tilesets, door source/art and patch were backed up to `tools/vendor/gba/johto-direct-before-editor-save-20260922`. After the owner pauses: capture/save the UI changes; diff the editor-saved map against the immutable turn-start snapshot with its original tilesets; preserve and merge those deltas; rebuild/recheck as needed; only then reload the matching map and tilesets together. The previous restoration incident was caused by a cached mismatched tileset. Do not blindly save cached old map IDs against new tiles.

Candidate map is 80x48: eight scenery columns on each side and six rows below. All owner coordinates translate +8 x; no y translation. Exact pixels are preserved for 2478 original cells outside requested placement/border changes. Actual water is now clear collision at surf elevation 1; land remains elevation 3 and rocks are impassable/non-water. The western reef touches only original water edge cells, preserving the cliff and existing rock island. A southern reef closes the bypass without entering the coast/forest. Outer forest crowns align with the existing three-row/odd-column southern pattern; both route approaches have coherent paths and full crowns.

Evidence is bound by `gba/art/johto-restart/evidence/build.json`. All 818 reachable walking tiles checked: 811 stable emulator positions and seven automatic door-step cells separately covered by building round trips. Both routes and saves pass. Combined walking/surf flood-fill has covered camera footprints; 57 physical surfing boundary probes pass. All twelve NPC movement/frame/route checks pass; automated dialogue checks did not complete and must not be reported as passing. The new girl route is (60,20)-(61,20), avoiding the moved house and Silver. Updated native door generation also resolved the restored HarborHouse transition failure.

New validation helpers: `check_johto_direct_boundaries.py`, `johto_direct_runtime.c`, `johto_direct_boundary_runtime.c`, `review_johto_direct_views.py`, `johto_surf_boundary_runtime.c`, `check_johto_direct_npcs.py`, `johto_direct_npc_runtime.c`. Runtime evidence: `tools/vendor/gba/johto-direct-accepted-20260922`, sweep `/tmp/johto-direct-boundary-sweep.jsonl`, surf `/tmp/johto-direct-surf.jsonl`. Candidate board: `gba/art/johto-restart/evidence/direct-in-game.png`.

# Cherrygrove — fresh custom exterior

2026-09-14. Current visual-review build, made after the owner rejected the repurposed HGSS-art reconstruction. The owner preferred the earlier custom buildings on Emerald terrain and explicitly requested a fresh start with the same geography, polish and moving-cast expectations. Visual acceptance of this new version remains the owner's next decision.

This exterior starts from clean Emerald town baseline `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`, upstream `e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7`. It uses a new layout and newly generated tree, cliff, Mart and island art. No v4 assets, layouts or source patch were used. The approved v2 house and Center PNGs are byte-identical; the previously approved character integration is retained. Production `game/`, all earlier previews and original character sources remain separate.

## Restored owner-edited Cherrygrove (2026-09-21)

The owner rejected the boundary-review revision and requested their edited version back. **Current source is `tools/vendor/gba/johto-restart-game`, town 64x42.** Its map is byte-identical to `tools/vendor/gba/johto-concurrent-boundary-save/data/layouts/CherrygroveCity/map.bin` (SHA256 prefix `981d0a9ce5c231f2`), the latest saved owner edits. Matched original tilesets remain intact. The active art overview and standalone patch have been restored to that source. Recovery snapshot: `tools/vendor/gba/johto-owner-restored-20260921`.

**Do not regenerate this map from older snapshots.** The boundary reconstruction lost owner details by rebuilding from an older source and carrying only selected deltas. Future revisions must edit this actual map directly and preserve current Porymap state. `extend_johto_port.py` and the boundary audit scripts describe the rejected separate reconstruction, not the active owner map. Rejected source remains in `johto-boundary-review-game`; rejected art/patch is retained in `johto-rejected-boundary-art`. Older validation claims below do not apply to the restored owner version.

[Restored owner map](evidence/port-overview.png).

## September 21 island access, boat headings and tree layers

Latest package: `tools/vendor/gba/Cherrygrove-island-20260921.zip`. [Updated map](evidence/port-overview.png) and [in-game review](evidence/island-in-game.png).

The pier moved north three tiles; its southern branch joins the small sandy island, whose eight central tiles can be walked around. The lower fishing launch is beside the island. The other fishing boat and the cargo vessel now face north, on the right and left of the pier respectively. New north-facing art preserves the overhead cabin perspective; [exact generation prompts and files](island-provenance.json).

A bench and path sit beside the northeast pond, and northern trees close the edge. Complete trees replace the northern forest and Route 30's former repeated two-row fragments. Six inaccessible southern scenery rows move the engine's repeating border outside the reachable camera; town size is now 64 by 42, with all existing buildings and events at their original coordinates. Route 30's preview approach is 18 rows deep, with a straight path and whole trees.

The grass-over-player defect came from normal-layer tree metatiles whose palette-packed upper tiles included grass. The town and both approach routes now use covered background layers for opaque scenery. All trees remain impassable; flowers still sit beneath trees in the composed art. [Layer audit](evidence/tree-layer-audit.json) checks every used metatile for opaque pixels on the above-character background. This is a guarantee for these three maps, not an audit of the entire ROM.

Porymap contained 29 unsaved tile changes when refreshed. They were saved into `tools/vendor/gba/johto-owner-unsaved-preserved-20260921/` before restoring the new work. Their beach corrections and removal of the flat southern bank are incorporated; the delta is retained under `owner-20260921/recovered-unsaved-delta.json`. The earlier port source/art also remains backed up in `tools/vendor/gba/johto-port-before-island-20260921/`.

Validation includes actual movement onto, across and off the island; pond northern collision; all seven building round trips; route returns; save/cold reload/Continue; twelve NPCs; native water animation; bench/island connectivity; and inspection of native in-game captures. Porymap was reloaded from disk after preserving its unsaved state.

## September 21 port and southern neighborhood

Current preview: `tools/vendor/gba/Cherrygrove-port-20260921.zip`. Extract the matching ROM/save together and choose Continue. [Updated town](evidence/port-overview.png), [actual in-game views](evidence/port-in-game.png).

The owner's saved Porymap state is preserved in `owner-20260921/`, with a larger local backup at `tools/vendor/gba/johto-owner-before-port-20260921/`. The saved terrain had a five-row northward wrap while doors/NPCs stayed in place. This revision reverses that overall shift, retains the other authored tiles, and changes only the southern forest, neighborhood and harbor area. The owner was asked about the shift; absent a reply, it was treated as accidental. The exact original remains recoverable.

The southern forest now uses complete, regularly spaced crowns around the existing coastal outline. A walkable timber pier serves two fishing launches and a medium cargo vessel. Two additional houses connect to the town paths; each has its own quiet preview interior, animated door and working return warp. The southern tree belt is continuous and impassable. No sailing or commercial gameplay is implemented.

All seven building round trips, both routes, pier edge, southern barrier, save/cold reload/Continue, twelve walking NPCs and animated water passed. The new scene passed an exact pixel roundtrip; unchanged cells retain their original visuals. See [port integration](evidence/port-integration.json), [build identity](evidence/build.json), and [generated asset provenance](port-provenance.json). New boats use the built-in image generator, reduced to native scale and the existing palette; originals remain in `generated/`.

Use `tools/gba/maps/extend_johto_port.py --undo-shift` for this snapshot, followed by the door builder. It refuses to overwrite subsequent unincorporated map edits. The original fresh-layout builder now refuses to run over an owner-authored snapshot. Do not bypass either guard to discard new Porymap work. The standalone patch includes the entire current playable result.

The sections below describe the earlier foundation and September 21 feedback pass; their older package and five-building counts are historical.

## September 21 owner-feedback revision

Corrected all five reported scenery issues: removed solid forest-floor backplates so tree transparency reveals grass; tapered and shaded the northwest cliff return; capped the southern face and brought the forest against it with a blocked intervening strip; removed the isolated rocks beside Route 30; enclosed the northeast pond with a rounded grassy bank and kept trees off water; and composited trees after flowers/fences so foliage wins overlapping pixels. Route stubs now extend only their actual exit corridors, preventing pond fragments from repeating outside the town.

The original September 14 art/evidence and patch are preserved locally under `tools/vendor/gba/johto-restart-before-feedback-20260921/`; its original preview ZIP is unchanged. Current reviewed evidence and source patch refer to this revision. [Focused in-game corrections](evidence/feedback-20260921.png).

## Review

- Playable package: `tools/vendor/gba/Cherrygrove-custom-feedback-20260921.zip` from repository root. Extract the matching ROM/save together and choose **Continue**. Starts at `(40,20)`.
- [Actual in-game walking tour](evidence/walking-tour.gif), [four-view board](evidence/in-game-tour.png), [opening doors](evidence/doors-in-game.png), [animated water](evidence/water-in-game.gif).
- [Whole exterior](evidence/town-overview.png) is a decoded map render; unlike the walking tour it does not include live residents.

Three asymmetrical red-roof homes and the approved orange-roof Center set the architectural style. A new blue-roof Mart complements them. Newly generated trees have one continuous canopy and a short trunk. New warm sandstone cliffs and rocky outcrops border a curved western beach; sage grass, pale dirt and blue water retain Emerald's native tile patterns and animation. The compositor preserves the actual background behind transparent objects, including live water. Each building has a matching three-stage door animation.

Geography follows the [HGSS Cherrygrove map reference](https://archives.bulbagarden.net/wiki/File:Cherrygrove_City_HGSS.png): western ocean and beach, northern cliff, offshore rocks, three houses, Mart/Center, gardens, north Route 30 and east Route 29. This is a 64×36 adaptation for the larger custom building footprints, not a pixel-for-pixel HGSS copy. The earlier invented docks, boats and park are absent from this fresh layout. Local reference: `gba/art/johto-v1/references/cherrygrove-hgss.png`.

Twelve residents walk: four Johto citizens, custom Gold/Silver/Kestra, and Hoenn, Kanto, Johto, Sinnoh and Unova samples. The regional samples and custom cast retain the earlier scale-comparison treatment. Four imported citizens retain their original size. Movement is ordinary engine NPC movement with collision; talking stops the eight named/sample actors, faces the player and resumes their routes. Cast name labels and visitor dialogue are preview staging, not new campaign scenes.

## Source and artwork

- [Foundation record](foundation.json), [layout](layout.json), [resident routes](residents.json).
- Standalone source patch: `gba/johto-restart.patch`. Apply directly to the clean town baseline above; **do not apply the old art patches first**. It includes the required character integration and all new exterior/door edits.
- `generated/`: original transparent bitmap outputs from the built-in `image_gen` tool. Full prompts and references: [prompts.json](prompts.json), [island-prompt.json](island-prompt.json).
- `native/`: palette-constrained PNGs, JASC palettes and collision source; `prepared/`: editable Aseprite documents for all six scenery assets. [Provenance and hashes](provenance.json).
- `tools/gba/maps/build_johto_restart.py`: fresh layout, native terrain palette changes, alpha composition, tile packing, collision, connections and resident placement. It reads the clean baseline, approved v2 art and pre-v4 character scripts. Earlier exact-composition helpers informed the implementation; no rejected reconstruction input is used.
- `tools/gba/maps/johto_restart_doors.py`: building-specific native door frames and engine registration.
- `tools/artwork_library/preserve_johto_restart.lua`: editable Aseprite preservation.
- `tools/gba/maps/preserve_johto_restart.py`: complete binary source patch, with forward/reverse application checks using a private Git index. Raw door graphics are included even though the engine normally ignores them.

Scenery was generated specifically for this task. Pokémon architecture and native Emerald assets are by Game Freak/Nintendo/Creatures. Existing character provenance remains in `johto-npc-v1`, `johto-cast-v1` and `regional-scale-v1`; custom Gold is the recovered owner-created source, not stock Ethan. See the linked provenance record for exact generated asset hashes.

## Verified result

Built with ARM GNU 14.2.rel1; tested using mGBA 0.10.5. [Build/package hashes](evidence/build.json) bind the tested ROM to the packaged ROM and 128 KiB ordinary save. The standalone source patch passes forward and reverse application checks. The September 21 ROM was rebuilt from the revised isolated source; the package contains that tested ROM and matching ordinary save.

- [Town runtime](evidence/runtime.json): all five building entry/exit pairs, bedroom stairs both directions, both route connections and returns, blocked shoreline, ordinary save, cold reload and title-screen Continue passed. Door animation screenshots were visually inspected.
- [Walking verification](evidence/movement.json): 7,200 engine frames / 1,800 observations across five camera positions, all twelve complete routes, eight conversations. Displayed OBJ VRAM pixels match the correct source frames; no horizontal mirroring, palette conflicts or blocked-cell occupation.
- [Water](evidence/water.json): 512 frames, eight animation states, no static-terrain overwrites.
- [Connectivity](evidence/structure.json): all five door approaches, both exits and every resident route are reachable. Legacy warp 3 remains reserved in blocked forest.
- [Tile integration](evidence/integration.json): exact pixel roundtrip through installed tiles/metatiles, approved buildings unchanged, animation slots excluded from static art. The current tile counts are recorded in `evidence/integration.json`; art uses secondary slots and unused primary slots; 16 door-animation slots remain reserved. Current metatile usage is recorded in the same integration report. These are scene-specific allocations, not a guarantee of spare capacity for arbitrary future maps sharing this tileset.
- Linked use: EWRAM 226,736 bytes; IWRAM 28,392 bytes; ROM 19,748,932 bytes, padded to 32 MiB. No wider mechanics qualification is claimed by these visual checks.

Native captures and movement sequences were visually inspected. Corrections made during inspection included cliff proportions, shoreline joins, terrain colors, tree collision and the clipped northern forest continuation.

## Reproduce

Commands below run from repository root. The existing isolated clone is `tools/vendor/gba/johto-restart-game`. For an independent reproduction, create a clean clone at the pinned town baseline and apply `gba/johto-restart.patch` with `git apply --binary`. That patch is sufficient for engine source/art; no image generation is needed to rebuild. The toolchain and `compresSmol` dependency must be installed as recorded by the GBA baseline workflow.

To regenerate the preserved art/layout in the existing isolated preview, then build and test:

```sh
python3 tools/gba/maps/extend_johto_port.py --undo-shift
python3 tools/gba/maps/johto_restart_doors.py
gmake -C tools/vendor/gba/johto-restart-game -j8 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
python3 tools/gba/maps/check_cherrygrove.py tools/vendor/gba/johto-restart-game tools/vendor/gba/johto-restart-review-run --toolchain tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi --runtime-source tools/gba/maps/johto_port_runtime.c
python3 tools/gba/maps/check_johto_restart.py
cc -I/opt/homebrew/opt/mgba/include tools/gba/maps/johto_restart_water_runtime.c -L/opt/homebrew/opt/mgba/lib -lmgba -o tools/vendor/gba/johto-restart-water/runtime
tools/vendor/gba/johto-restart-water/runtime tools/vendor/gba/johto-restart-game/pokeemerald.gba tools/vendor/gba/johto-restart-movement/symbols.txt tools/vendor/gba/johto-restart-water
python3 tools/gba/maps/preserve_johto_restart.py
```

The regeneration script expects the clean `johto-art-v3-baseline` directory and retained prior approved asset sources. `check_cherrygrove.py` requires a new output-directory name each run. The movement checker refreshes the ELF symbols consumed by the water check. Runtime proof entrypoints position the camera/player to exercise each view; all observed NPC movement and animation uses the normal game engine. Fixed noon RTC is used only in test harnesses for consistent screenshots.

## Preview boundaries

The new exterior connects to existing preview interiors and short Route 29/30 stubs. Those rooms and the wider regional campaign have not been rebuilt in this art pass. Surf access and offshore gameplay are not qualified here. The fourth old interior ID remains preserved but inaccessible. Prior preview saves belong with their original ROMs because this version changes map coordinates. A successful build and runtime checks do not substitute for the owner's visual acceptance.
