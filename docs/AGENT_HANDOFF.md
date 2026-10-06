## October 4 Route 29 and Route 30 (Claude build): isolated, qualified

Owner asked Claude for the routes north and east of Cherrygrove. Read `gba/art/claude-routes/README.md`.
Both routes follow the HGSS renders, extend Claude's Cherrygrove (`gba/art/claude-cherrygrove/`) and replace
its stubs; workbench `tools/vendor/gba/claude-routes`, package `tools/vendor/gba/Routes-claude-preview.zip`.
Connections to the town are seam-safe on both sides (`tools/gba/maps/claude_routes/seams.py`); the shared
primary is at 511 of 512 tiles. New state: one hidden-item flag aliased on `FLAG_UNUSED_0x264` (no overlap
with the Chapter 1 overlay's 0x020-0x02F). Engine: random wild battles skip an empty party. Not built: the
gate and house interiors, Route 30 trainers, New Bark and Route 31 maps. `gba/claude-cherrygrove.patch` was
refreshed from the current town generator; the old copy predated its last revision. Not merged into Codex's
campaign workbench.

## September 30 Cherrygrove native detail test — isolated

Owner rejected the whole-town artwork study visually, then asked to try one small section before abandoning the approach. Read `gba/art/cherrygrove-detail-sample-v1/README.md`: closer reference house/tree/grass/path conversion, native palette clustering, actual engine captures and focused walking/house-blocking proof. Source `tools/vendor/gba/cherrygrove-detail-sample-work`; package `tools/vendor/gba/Cherrygrove-detail-sample-20260930.zip`. **769 patterns for this section alone: visual test, not a scalable full-town tileset.** Await visual feedback, then modularize assets if accepted. Neither prior full map was replaced. The first whole-town art study below is owner-rejected visually despite functional checks.

## September 30 Chapter 1 scene refinement — isolated

The latest Chapter 1 review ROM is
`tools/vendor/gba/Chapter1-refinement-review-20260930/Apocrypha-Chapter1-refined.gba`.
Read `gba/art/chapter1-refinement/README.md` for the real Route 30 return from
Kestra's rescue, Gold/Silver camera pan, Kestra's exit paths, safe outdoor
fades, five-stop blocking proof, build identity, and remaining art/battle limits.
Its independent workbench is `tools/vendor/gba/chapter1-scene-refinement-work`;
the prior campaign workbench and owner ROM/save remain untouched. Three changed
scripts are preserved as an overlay on the September 29 chapter overlay.
Fresh New Game/save/Continue and all three starter branches reached the
northbound departure in headless mGBA. No desktop emulator was opened for this
refinement.

## September 30 reviewed Cherrygrove artwork conversion — isolated

Owner requested one of the five reviewed artworks as a playable map. Cherrygrove revision 3 was converted in `tools/vendor/gba/cherrygrove-art-study-work`; read `gba/art/cherrygrove-art-study-v1/README.md`. Separate package `tools/vendor/gba/Cherrygrove-art-study-20260930.zip`. Seven door pairs, two native route round trips, island, 224 movement probes, twelve walkers, ordinary Save/cold reload/Continue pass in headless mGBA. Actual capture gallery and reference comparison in evidence. Native budget 990/1008 tiles, 342 metatiles, 13 palettes. Incremental patch `gba/cherrygrove-art-study.patch` and source overlay preserve edits. This is an art review candidate; active editor, campaign source/build and owner saves were not replaced. Avoid replaying generators over later edits. Water is static; surfing/full service dialogue not requalified.

## September 29 Chapter 1 scene blocking correction — isolated

The latest review ROM is
`tools/vendor/gba/Chapter1-staging-review-20260929/Apocrypha-Chapter1-staging.gba`.
Read `gba/art/chapter1-staging/README.md` for the full five-stop walking tour,
actor facing/placement changes, native captures, background recording, current
ROM hash, and the focused mGBA checks. The modified engine source is in
`tools/vendor/gba/opening-house-work` and preserved in
`gba/art/chapter1-route/source-overlay/`; the route generator is
`tools/gba/maps/build_chapter1_tour.py`. The owner's active playable ROM/save,
production `game/`, and Porymap state were not changed. The remaining Route 29,
New Bark and institute art work is separate from this scene staging revision.

## September 27 Pokégear service layer — isolated and qualified

Owner authorized maps, phone services and broadcasts after approving the modern
shell/phone icon. Read `gba/art/pokegear-services/README.md`. Current isolated build
has five original-game atlases, zoom/cursor/100 saved notes, a 75-slot phone registry,
favorites/order/history/redial, queued and missed calls, ordinary-walking callbacks,
event gift/rematch adapters and four working radio broadcasts. Map Card stays locked
until Gold's later event; atlas/gift/registry captures use explicit service fixtures.
Only Mom has authored phone content in this opening. Broader HGSS campaign parity
and chapter event wiring remain open, as listed in that README.

New versioned/checksummed gear state appends to SaveBlock3: 940/1624 bytes total,
previous upstream offsets preserved. Old-save migration, new-state ordinary Save /
cold Continue, callback walking, capacity limits, corruption isolation and the full
opening regression pass. Damaged known gear records show a visible notice rather
than silently clearing them. No desktop game or active-editor install occurred.
Patch `gba/pokegear-services.patch` follows `gba/pokegear-modern.patch`; apply checks
pass. Latest gallery: `gba/art/pokegear-services/evidence/services-review.png`.

## September 27 modern Pokégear visual direction

Owner requested the B/W equivalent's polish, then explicitly kept Pokégear
identity and asked for a distinct design. Current isolated application has a
slate bezel, recessed dark screen, orange hardware index, persistent clock/name,
recognizable field-device tabs, circular radio dial and restrained accents.
Owner subsequently accepted the direction except for the phone icon; that
icon is now a crisp mobile handset. Latest capture is
`gba/art/pokegear-modern/evidence/phone-icon-revised.png`.
Read `gba/art/pokegear-modern/README.md`; patch `gba/pokegear-modern.patch` applies
over the opening-house revision patch. The C-Gear honeycomb draft is superseded.
This is a native visual revision; full maps, incoming calls/contact/rematch
services and radio broadcasts remain pending. No networking scope was added.
ROM compilation, patch forward/reverse checks, ordinary opening/app input and
menu Save/cold Continue pass. Short button edges are queued across redraws;
one-frame input checks now retain all theme/tuner selections and saved settings.
Background captures only; no desktop game window or active-editor installation.

## September 27 owner review corrections — house qualified, gear incomplete

Owner identified incorrect facing/Mom staging, bottom-side stair warps and an
incomplete Pokégear. Read `gba/art/opening-house-revision/README.md` and
`gba/art/pokegear/README.md`. Isolated `opening-house-work` now has scripted
mutual facing, Mom's doorway/stairs/box positions, directional stair entrances
on the right-side red landings and the door exit/return one tile higher.
Both appearances passed ordinary button playthrough, actor facing/position
assertions, PC Potion once, stair/door round trips and four menu Save/cold
Continue cycles each. No desktop game window or active-editor install occurred.

`gba/opening-house-revision.patch` supersedes the previous opening patch when
applied over `floccesy-polish-work`; forward/reverse checks pass. The old patch,
ROM package and screen recording remain preserved. Current native Pokégear
supports RTC, Mom call, tuner/presets, palette choices and saved settings, but
**is still a prototype**. Regional maps, complete HGSS backgrounds, incoming
calls/contact/rematch services and actual radio programs are not complete.
Do not describe it as full HGSS functionality or use its screens as proof of
those services. Full Pokégear reconstruction is the owner's highest priority
before advancing the chapter. Gen 5 additions remain a preference question;
default is faithful HGSS first. Preserve Gold's later Map Card handoff.

## September 27 opening house milestone — isolated, qualified

Owner authorized the opening-house slice and corrected the interior method to
use the existing Johto templates. Read `gba/art/opening-house/README.md`.
Source `tools/vendor/gba/opening-house-work` now has HGSS-derived rooms, moving
boxes, appearance-only New Game, cold opening, PC/Potion, Mom handoff and exit.
Both appearances passed button-driven playthrough and menu Save/cold Continue
at stages 1, 2 and 4. Desktop emulator/game stayed closed as requested.
The tracked source patch passed forward/reverse checks; current approved mechanics
were carried into the isolated source. Production/active editor remain untouched.
Next scoped scene is Gold/Silver's friendly battle and Kestra's later naming beat;
full Chapter 1 is still pending. Phone/clock are basic; radio/map/contact expansion
is not finished. Screenshots: `gba/art/opening-house/evidence/playthrough.png`.

## September 27 opening chapter direction — scope recorded, implementation pending

The owner agreed to visual cleanup/standards with a caveat: towns must retain
independent visual identity, especially Unova and potentially Diamond/Pearl
Sinnoh. This clarification is recorded in FOUNDATION_DECISIONS.md. The owner also
supports opening chapter(s) as the next coherent-game test. Read
`docs/GBA_OPENING_CHAPTER_PLAN.md` for the bounded Chapter 1 milestone and actual
assembly requirements. Current player-home scripts are exploratory dialogue;
Chapter 1 is not implemented by the map previews. No campaign source or active
editor was modified by this planning pass.

## September 26 roofs, fences, park and woodland opening — latest playable revision

The owner rejected sloppy roofs/tree overlap, fencing, park and the cave-like northern opening. Read `gba/art/floccesy-polish/README.md`. Revised roof planes/ridges/canopy ordering, fence modules, park ground/props and woodland opening are in `tools/vendor/gba/floccesy-polish-work`. In-game captures are in its evidence folder. Active Porymap is untouched. Package: `tools/vendor/gba/Floccesy-polish-20260926.zip`.

Final ROM passed paired exploration/dialogue/save/Continue, town travel, six doors, Center stairs, 199 collision probes and 1,800 recorded NPC samples. All 4,368 cell exploration properties, event/scripts, NPC routes, warps and other layouts match the prior cleanup revision. Exact layer factoring and metatile repacking preserve authored pixels and border IDs; 999/1,008 referenced patterns including border, 640 metatiles. Door art references regenerated, implementation unchanged. Patch `gba/floccesy-polish.patch` applies over cleanup with forward/reverse checks. The woodland opening is still decorative/blocked; no new functional exit. Preserve subsequent owner edits before rebuilding/installing.

## September 26 surface cleanup and training court — previous playable revision

The owner requested removing plants from streets/walls/steps/doors, cleaning building edges/shadows and improving the arena. Read `gba/art/floccesy-cleanup/README.md`. Isolated source: `tools/vendor/gba/floccesy-cleanup-work`; playable package: `tools/vendor/gba/Floccesy-cleanup-20260926.zip`. Explicit surface cleanup, native silhouette repairs and the clay court/markings/fencing are implemented. Actual in-game captures are in its evidence folder. The active editor remains untouched.

All 4,368 exploration cell properties, events/scripts, NPC routes, doors/warps and other layouts are preserved. The final ROM passed paired traversal/dialogue/save/Continue, town travel, six door round trips, Center stairs, 193 collision probes and 1,800 recorded NPC samples. Compiler is lossless, uses legal palette banks and 930 metatiles. `gba/floccesy-cleanup.patch` applies over the prior materials revision, with forward/reverse checks. See `evidence/qualification.json` and `preservation.json` for final ROM/source hashes. Preserve later owner edits before rebuilding or installing.

## September 26 corrected walls and town materials — previous playable revision

The owner approved the native sample textures, rejected the tower-square walls and authorized extending the treatment to the town after fixing them. Read `gba/art/floccesy-materials/README.md`. Corrected directional coping/corners/stair jambs and town-wide lawn, paving, paths, curbs, flower textures and foliage palette are in `tools/vendor/gba/floccesy-materials-work`. Actual before/after wall captures, town views, walking GIF and door frames are in its evidence folder. No v5 painting import or active-editor installation occurred. All 4,368 cell collision/elevation/behavior/layer properties, events, NPC routes, warps and other layouts are preserved. Door art references were regenerated; engine door logic is unchanged. The native compiler remains lossless and uses supported palette banks only.

ROM build, static checks, paired exploration/dialogue/save/Continue, six door round trips, Center stairs and travel passed. Movement sweep: 190 probes, zero failures; 1,800 NPC samples recorded. `gba/floccesy-materials.patch` applies over the previous clock sample, with forward/reverse checks. Playable package: `tools/vendor/gba/Floccesy-materials-20260926.zip`. The map uses 997 tile patterns plus protected border patterns within the 1,008-slot budget, and 919 metatiles. Preserve later owner edits before rebuilding or installing.

## September 26 native clock-garden sample — owner review

The owner rejected the v5 painting as excessive and approved a small native sample with exploration fixed. Read `gba/art/floccesy-clock-sample/README.md`. Actual in-game comparisons and movement GIF are in its evidence folder. Isolated sample source: `tools/vendor/gba/floccesy-clock-sample-work`; playable ZIP: `tools/vendor/gba/Floccesy-clock-sample-20260926.zip`. All cell collision/elevation/behavior/layer properties, event scripts, NPC routes, doors and warps are preserved. The sample uses 960/1,008 referenced tile patterns with lossless lower-layer reuse, 755 metatiles and supported palettes 0–12. Paired baseline/sample traversal, walls, dialogue, save/cold reload/Continue and sample town travel/interiors passed. No active-editor installation or whole-town art expansion occurred.

**Correction to v4 evidence:** v4 referenced palettes 13–15, but this engine loads only 0–12. Some foliage could therefore render incorrectly despite the offline map. The separate `gba/floccesy-clock-palette-fix.patch` repairs that art data over v4. `gba/floccesy-clock-sample.patch` applies after it. Both pass forward/reverse checks. Before/after captures compare against the corrected baseline (`floccesy-clock-baseline-work`), not the faulty v4 display. The older claim that v4 was visually verified is too broad. Do not use the v5 painting as the native target or change exploration geometry to match it.

## September 26 Floccesy 2026 art direction — artwork proposal

The owner requested another pass with less primitive graphics: Gen 3-style design made for a 2026 audience, with visual progress reflecting the ten-year setting. `gba/art/floccesy-v5/floccesy-2026-art.png` is a built-in imagegen revision using the original-game reference and v4 native overview. See its README and exact prompt. It proposes coherent lighting, richer roofs/masonry, overlapping mature foliage, landscaped clock/park gardens, path lights and bicycle parking. This is artwork only; generated spacing is not validated against native collisions or doors. No game/editor source changed. v4 below remains the latest playable revision. Translate the new art direction into reusable native modules and inspect in-game before making native visual claims; do not import the entire painting or present it as gameplay proof.

## September 25 detailed Floccesy map — latest isolated playable revision

The owner's follow-up was that v3 still looked boring. `gba/art/floccesy-v4/README.md` describes the native v4 pass: trees grew to 48×56 px, outer forest rows were staggered, shaded/sunlit foliage palettes and a northern woodland opening were added, and court/ground/flower detail increased. Isolated source: `tools/vendor/gba/floccesy-detailed-work`; patch over active v2: `gba/floccesy-v4.patch`; playable package: `tools/vendor/gba/Floccesy-detailed-preview-20260925.zip`. The ROM compiled, forward/reverse patch checks pass, and mGBA core checks passed two-way travel, six interiors, Center stairs, save/cold reload/Continue, 264 ordinary movement probes and 1,800 NPC samples. Native map and actual in-game captures are in `gba/art/floccesy-v4/evidence/`. The active `johto-restart-game` is still v2 because Porymap is running on a locked Mac; inspect unsaved editor state before installing v4. Do not confuse the isolated preview with an active-editor installation.

## September 25 richer Floccesy map — previous isolated playable revision

The owner asked for larger buildings and more of the original map's detail. `gba/art/floccesy-v3/README.md` describes a revised native map with larger Center/houses/northern buildings, brighter textured grass, court and garden detail, and a more developed right park. It is built in `tools/vendor/gba/floccesy-rich-work`; the active `johto-restart-game` remains v2 because Porymap is running while the Mac is locked, preventing an unsaved-editor-state check. Do not overwrite the active project until that state is checked. The 97 KB incremental `gba/floccesy-v3.patch` applies over v2 and passes forward/reverse checks. Playable package: `tools/vendor/gba/Floccesy-rich-preview-20260925.zip`.

The isolated ROM compiled. Six building round trips, Cherrygrove travel, Center stairs, normal save/cold reload/Continue, 186 native collision probes and 1,800 NPC movement samples passed. Decoded native map and in-game captures are in `gba/art/floccesy-v3/evidence/`. This verifies the isolated preview, not an installation into the active editor project. The Unova visitor moved to (39,51) to clear the larger house; other residents and non-Floccesy source remain unchanged.

## September 24 Floccesy native tiles — active editor baseline

The owner requested in-game tiles from the richer v2 artwork. Converted separate generated assets to native tiles and integrated them into `tools/vendor/gba/johto-restart-game`. Read `gba/art/floccesy-v2/README.md`. Actual decoded map: `evidence/town-overview.png`; source patch `gba/floccesy-v2.patch` passes forward/reverse checks. 1,000/1,008 tiles, 263 metatiles, 13 palettes. Static reachability/layer checks and ROM compilation pass. Porymap reloaded and visually inspected. **No emulator or runtime tests run**, per owner restriction; v1 runtime evidence does not prove v2 gameplay. All event data and non-Floccesy maps/tilesets preserved. Backup `tools/vendor/gba/johto-before-floccesy-v2-20260924`. Do not overwrite later owner edits with generators.

## September 24 Floccesy artwork revision — visual review

The owner rejected the September 23 Floccesy art as too primitive and supplied the original map again. New built-in image_gen artwork preview is `gba/art/floccesy-v2/floccesy-art-preview.png`, with the exact prompt, owner reference and limitations in that folder. This restores richer foliage/architecture/terrain and closer proportions. It is **artwork only**, not native game integration, and has not been approved yet. No emulator was opened or run at the owner’s explicit instruction. Existing game source, maps and saves were unchanged. The v1 technical checks below remain historical evidence, not visual acceptance or proof of the v2 image in-game.

## September 23 Floccesy Town — current Unova preview

Built a custom 2D adaptation of the original B2W2 spring Floccesy map, connected both ways to Cherrygrove's eastern approach. Read `gba/art/floccesy-v1/README.md` before editing. Source remains `tools/vendor/gba/johto-restart-game`; Floccesy is group 80 map 20, 56x78, start (30,62); six interiors/upstairs are maps 21–27. New separate preview: `tools/vendor/gba/Floccesy-preview-20260923/Floccesy.gba` and matching `.sav`, ZIP beside folder. Existing owner saves untouched. Porymap is open on FloccesyTown; mGBA launched the preview.

Six generated custom assets, native paving/court, and an approved reused bench establish the town. Six regional walkers, six door pairs, Center stairs, both-way Cherrygrove travel, save/cold reload/Continue, and 126 native collision probes pass. Every new exterior tile draws below characters; visual inspection caught and fixed early paving occlusion. NPC frames/paths pass over 1,440 samples. 1,439 reachable tiles have scenery-covered camera footprints. Existing Cherrygrove and Sandgem regression checks also pass. Interiors use existing Emerald room art, and the eastern onward path is fenced.

All existing layout binaries remain identical except two directional cells on CherrygroveRoute29Approach; prior Johto metatiles are preserved with two appended clones. Exact backup `tools/vendor/gba/johto-before-floccesy-20260923`. Standalone source patch `gba/floccesy.patch` includes all three towns; forward/reverse checks pass. Do not rerun builders/installers over new owner changes. Evidence and prompts are in `gba/art/floccesy-v1`.

## September 22 Sandgem owner-reference revision — current

The owner rejected the invented Sandgem coastline/buildings and supplied an original-game screenshot. Current Sandgem follows that image: turquoise asymmetric northwest lab, orange Center, compact northeast Mart, two blue-gabled houses, saturated mint grass, dense round trees, southeast dry sand, **no water**. Read `gba/art/sandgem-v1/README.md` before editing. Rejected draft is preserved separately at `tools/vendor/gba/sandgem-rejected-20260922`.

Current source remains `tools/vendor/gba/johto-restart-game`; Sandgem is group 80 map 13, size 48x40. Its southern path connects both ways to Cherrygrove's northern approach via native directional warps. Cherrygrove town layout remains byte-identical. New playable ROM/save is `tools/vendor/gba/Sandgem-reference-20260922/Sandgem.gba` and `.sav`, start (29,29). Older live saves are untouched. Porymap is refreshed on SandgemTown and mGBA launched this new revision. Current standalone source patch is `gba/sandgem.patch`, including both towns. Do not regenerate over newer owner edits.

All five Sandgem door pairs, upstairs, both-way town travel, save/cold reload/Continue pass, as does the previous seven-door Cherrygrove regression. 55 native collision probes pass; 420 reachable exterior cells have covered camera footprints. Interiors are existing Emerald rooms, not custom Sinnoh interiors. Build identity and machine evidence are under `gba/art/sandgem-v1/evidence`.

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

## Restored owner-edited Cherrygrove (2026-09-21)

The owner rejected the boundary-review revision and requested their edited version back. **Current source is `tools/vendor/gba/johto-restart-game`, town 64x42.** Its map is byte-identical to `tools/vendor/gba/johto-concurrent-boundary-save/data/layouts/CherrygroveCity/map.bin` (SHA256 prefix `981d0a9ce5c231f2`), the latest saved owner edits. Matched original tilesets remain intact. The active art overview and standalone patch have been restored to that source. Recovery snapshot: `tools/vendor/gba/johto-owner-restored-20260921`. Restored package: `tools/vendor/gba/Cherrygrove-owner-restored-20260921.zip`. Cold reload and Continue pass. HarborHouse entrance did not transition in the exact restored map; do not claim all seven doors pass. No repair was applied during restoration.

**Do not regenerate this map from older snapshots.** The boundary reconstruction lost owner details by rebuilding from an older source and carrying only selected deltas. Future revisions must edit this actual map directly and preserve current Porymap state. `extend_johto_port.py` and the boundary audit scripts describe the rejected separate reconstruction, not the active owner map. Rejected source remains in `johto-boundary-review-game`; rejected art/patch is retained in `johto-rejected-boundary-art`. Older validation claims below do not apply to the restored owner version.

## Current Cherrygrove boundary review (2026-09-21)

Current source: `tools/vendor/gba/johto-boundary-review-game`. The owner is editing
`johto-restart-game` live; do not overwrite it or reload its unsaved view. A second
concurrent save was preserved separately before this revision was isolated. Read
the new top revision section in `gba/art/johto-restart/README.md` for backups,
placement changes, preserved path edits and exhaustive boundary validation.
Barge shifted east two tiles, bench reversed/north one tile, NeighborHouse north
one tile, southeast tree fragments removed. Town now 72x42; Route 29 24x42;
Route 30 72x18, with inaccessible scenery buffers around reachable camera views.
Latest package: `tools/vendor/gba/Cherrygrove-boundary-review-20260921.zip`.
All 834 reachable exterior cells have covered camera footprints; 827 stable
positions and seven door entries/exits were checked in-game. No exposed black
map edge remains. Package identity and validation paths are in evidence/build.json.
Older entries below are historical. The guarded extension/door/check/patch scripts
now default to the separate boundary review checkout.

## Current Cherrygrove island revision (2026-09-21)

Porymap showed another unsaved-change marker after the final refresh. Those newer
in-memory edits were left untouched; preserve them before any future reload. The
ZIP and standalone patch preserve the verified revision independently.

The latest preview is `tools/vendor/gba/Cherrygrove-island-20260921.zip` in
`johto-restart-game`. Read the first section of `gba/art/johto-restart/README.md`.
Dock joins the walkable island; north-facing cargo/fishing boats flank it; bench
and trees enclose the pond. Town is now 64x42 with inaccessible southern padding.
Tree grass no longer uses the above-character layer. Route 30 has complete crowns.
Recovered 29 previously unsaved owner shoreline tiles before refreshing Porymap;
backup/delta locations are documented. Preserve future Porymap edits before rerunning
the guarded extension builder. The fresh-layout builder must not be used here.

## Current Cherrygrove port revision (2026-09-21)

Owner edits backed up before the extension. Current source remains
`tools/vendor/gba/johto-restart-game`; current playable package is
`tools/vendor/gba/Cherrygrove-port-20260921.zip`. Read the new top section of
`gba/art/johto-restart/README.md` for the shift correction, preserved snapshot,
port/boats, two additional houses, southern forest and validation evidence.
Seven building round trips, route returns, boundaries, twelve walkers, water and
ordinary saves pass. Porymap refresh was blocked by the Mac locking; source files
are updated, but do not save an old cached editor view over them. Reopen the project.

## Owner editing in Porymap (2026-09-21)

The owner is manually tidying `CherrygroveCity` in
`tools/vendor/gba/johto-restart-game`. Treat that checkout as authored work.
Before any regeneration, capture its current map/tileset/event diffs and incorporate
the owner edits; do not run `build_johto_restart.py` over them. The September 21
feedback ZIP and standalone patch preserve the pre-manual-edit baseline.

# Continue Apocrypha here

Updated 2026-09-11 at the owner's request before usage runs out. Read root
AGENTS.md and CONTEXT_INDEX.md, then this page. Load other documents only for the
specific task. Claude/Gemini root files already point to the same AGENTS.md.

## Remote source access (2026-09-15)

The owner requested independent Cherrygrove builds from Claude and Grok. The GBA
source, art and handoffs are now prepared on `codex/gba-source-handoff` in
`Davisfox5/pokemon-apocrypha`. Start with [the remote setup guide](GBA_REMOTE_HANDOFF.md).
Use its portable workbench preset for an independent exterior; no access to the
owner's Mac or old DS build is required. Existing preview documentation describes
historical local paths; the remote guide is authoritative for fresh-clone setup.
The owner found the fresh custom exterior mostly good and requested comparisons.
Preserve each agent's separate work; this is not authorization to replace another
agent's preview or merge experimental maps into production.

## Immediate next task

**Claude's independent Cherrygrove (2026-09-15):** built on the portable workbench
preset (Linux container, then the owner's Mac). Second revision after the owner
asked for the Gen 4 HGSS Johto look in 2D: scenery is now derived read-only from
HGSS itself (buildings, cliff, rocks, flowers, fences and props lifted at native
scale from the 1:1 HGSS Cherrygrove render, the tree from the DS texture, ground
painted in the render's sampled colours with its rim profiles); the pier, boats,
nets, benches and lanterns stay original art. Own primary and secondary tilesets.
Gold (sprite rebuilt from the HGSS hero), Silver, Kestra, four Johto residents
and five regional visitors walk and talk; the sea animates. Revision 3 answers the
owner's nineteen pinned review notes. Doors, stairs, both route stubs, ordinary
save, cold reload, title-menu Continue and a Porymap save round-trip pass. See [the README](../gba/art/claude-cherrygrove/README.md);
source patch `gba/claude-cherrygrove.patch` applies on top of the workbench preset.
Production `game/` and every earlier preview are untouched.

**Custom Cherrygrove feedback fixes (2026-09-21):** continuing the owner's preferred
custom restart. Tree backplates removed; cliff ends finished and southern gap blocked;
Route 30 rock strip removed; northeast pond bank enclosed and trees kept on land;
tree foliage now covers overlapping flowers. Route-stub pond repetition corrected.
Latest preview: `tools/vendor/gba/Cherrygrove-custom-feedback-20260921.zip`.
See `gba/art/johto-restart/README.md` and focused in-game evidence. The September 14
package remains intact. This is an isolated visual revision, not a production merge.

**Fresh custom Cherrygrove (2026-09-14):** the owner rejected the repurposed HGSS
art direction and requested a fresh start, returning to the custom buildings on
Emerald terrain. [The current preview](../gba/art/johto-restart/README.md) starts
from clean town baseline f09ec1de, with an independent layout and newly generated
Mart/tree/cliff/island art. Approved house/Center pixels and the prior character
integration are retained. No rejected v4 art, layout or source patch was used.
The fresh town has three houses, Mart/Center, a curved western beach, gardens and
north/east exits. Twelve residents include Gold/Silver/Kestra and all five region
samples. Five doors, route transitions, save/cold reload/ordinary Continue,
7,200 frames of NPC routes and eight conversations pass; native water animation
leaves static tiles intact. Actual native screenshots and movement were inspected.
Review `tools/vendor/gba/Cherrygrove-custom-restart-preview.zip` next; Continue
starts at (40,20). The README links a walking tour, provenance and measured limits.
`gba/johto-restart.patch` is standalone on f09ec1de, not an incremental v4 patch.
Patch regeneration is byte-identical; the regenerated ROM matches the tested ROM.
Existing interiors and route stubs remain preview content. Owner visual acceptance
is pending. Keep production `game/` and all earlier sources/previews intact.

**Rejected visual direction — HGSS reconstruction (2026-09-14):** v4 passed
technical checks but the owner disliked the repurposed art and preferred the
custom buildings. Preserve `gba/art/johto-v4/` and its patch as historical evidence;
do not resume it or use it as the foundation for the current exterior. The current
fresh build above supersedes it for visual review.

**Five-region scale preview (2026-09-13):** the owner authorized reducing the
large custom cast toward Emerald scale and adding characters from all five
regions. [The new preview](../gba/art/regional-scale-v1/README.md) places walking
Hoenn, Kanto, Johto, Sinnoh and Unova samples near the shops beside smaller
Gold/Silver/Kestra. Hoenn player/buildings/geography retain their scale. Regional
samples have A-button region labels; this is visual-review staging. The isolated
build, all eight actor movement/dialogue checks and ordinary save/Continue pass.
Actual OBJ VRAM frames are checked. Latest package:
`tools/vendor/gba/Cherrygrove-regional-scale-preview.zip`. Continue beside the group.
Review the shared-scale proposal next; no global art replacement is assumed.
Source is preserved in `gba/regional-scale-v1.patch` after art v3, NPC v1 and
cast v1. Original assets/previews and production `game/` remain separate.


**Custom cast preview (2026-09-13):** Gold and Silver's native overworld walk cells
are cleaned up, and both now join Kestra and the three roaming citizens near the
shops. See [the cast handoff](../gba/art/johto-cast-v1/README.md). Original art is
preserved. This preview also fixes missing step/idle table registration affecting
the earlier NPC pilot; the checker now compares displayed VRAM pixels with source
frames during movement and interaction. The latest package is
`tools/vendor/gba/Cherrygrove-cast-preview.zip`, with Continue beside the group.
Review appearance and movement next. Name labels and placements are for visual
review; no new campaign scene or battle art was added. Source is preserved in
`gba/johto-cast-v1.patch`, applied after v3 art and NPC v1. Production `game/`
remains separate.

**Custom Gold recovered (2026-09-13):** the owner confirmed a custom Gold sprite
existed. It was found in Aseprite recovery data for temporary `adultgold_grid.png`,
not the normal trainer asset directory. The latest recovered 24-cell overworld
grid and editable Aseprite copy now live at `assets/src/trainers/overworld/gold_adult_ow_grid.*`.
See [recovery evidence](../assets/src/trainers/recovered-gold/README.md). Pixels,
palette and transparent index are preserved, and original recovery records are
copied into the repo. This is Gold, distinct from the existing custom adult Silver.
Gold has not yet been placed in the GBA preview; classify the 24-cell action layout
before adapting the NPC importer. Do not replace this custom source with stock Ethan.

**Johto NPC pilot (2026-09-13):** the owner liked the v3 map and authorized getting
Johto residents onto it and walking. [The NPC preview](../gba/art/johto-npc-v1/README.md)
imports five existing HGSS human strips with exact colors/pixels and explicit
direction mapping. Three residents walk near the shops; the waterfront woman
and functioning clerk also use Johto sprites. Runtime observation verifies
movement, simultaneous palettes and conversation stop/face/resume. All town
entry/connection/shop/save/Continue phases pass. Latest package:
`tools/vendor/gba/Johto-NPC-preview.zip`; Continue starts beside the residents.
The manifest/importer and `gba/johto-npc-v1.patch` preserve the work. Apply this
NPC patch after the v3 art patch on the town baseline. Review the NPC appearance
and movement next; broader roster imports and story characters remain separate.
Production `game/` was not modified.

**Cherrygrove revision 3 (2026-09-13):** the owner loves the building designs;
preserve the v2 house and Center pixels. Their requested corrections are now in
[revision 3](../gba/art/johto-v3/README.md): one continuous tree crown, scenery
composition that preserves backgrounds and animated water, and a broad western
bay/curved beach/northern cliff based on the HGSS map. The existing park, fourth
home and fishing waterfront remain Apocrypha additions. The layout source is
`gba/maps/cherrygrove/town-v3.json`; the older town.json reproduces v1/v2 only.
The isolated ROM builds, all three runtime/save phases pass, native/movement/water
captures were inspected, and the patch passes forward/reverse checks. Latest
package: `tools/vendor/gba/Johto-art-v3-preview.zip`. Review the corrected trees,
scenery and geography next; no unrequested building variants were introduced.
Source and patch are preserved outside production `game/`.

**Johto art revision (2026-09-13):** the owner preferred the generated house and
Center to their first map imports. [Revision 2](../gba/art/johto-v2/README.md)
uses the same generated designs with preserved proportions, 80×80 native pixels
and two shared per-tile building palettes. Its isolated ROM builds and all three
town runtime/save phases pass; captures and movement frames were inspected.
`tools/vendor/gba/Johto-art-v2-preview.zip` is the latest art preview. Old art,
evidence and ROM package remain intact. Review this version before expanding art.

**Johto aesthetic samples (2026-09-13):** the owner clarified that Cherrygrove must
reproduce Johto's visual identity, not simply recolor Emerald scenery. Three HGSS
reference-based house/Center/tree samples now have native GBA assets and a tested
isolated ROM. See [the art sample pack](../gba/art/johto-v1/README.md) for reference
comparisons, in-game captures, prompts, source patch and capacity. These are
proposals awaiting visual review; remaining town art is still the prior prototype.
Production `game/` and Claude's mechanics work were not modified.

**Cherrygrove town follow-up (2026-09-13):** the owner authorized the first town.
An isolated explorable GBA proposal now exists with six enterable buildings,
blossom park, waterfront, player-home stairs and connected route approaches.
See [CHERRYGROVE_GBA.md](CHERRYGROVE_GBA.md) for the preview, source patch,
runtime evidence and exact scope. Porymap's uniform Emerald-format town workflow
now passes open/render/save/rebuild; native FRLG mixed-format editing remains a
separate question. Review/revise this town before expanding map production.
Opening cutscenes, Gold/Kestra/Silver art and starter events are not integrated.

**2026-09-13 owner priority:** qualify maps beyond Hoenn before advancing campaign
design. See [GBA_MAP_QUALIFICATION.md](GBA_MAP_QUALIFICATION.md). An isolated ROM
now runs five appended region fixtures, native Kanto art, collision, NPC warping,
map connections and cold location reloads (ten runtime processes pass). The
editor round-trip, regional town-map/Fly support and full asset budget remain
unqualified. This proof has not been applied to production `game/`.
The owner has story bones through about eight or nine chapters and a gym leader
list; Pokémon placement, trainer teams and level curve remain undesigned.
The mechanics/tutor continuation below describes the separate ongoing work;
it does not override this map-first priority for campaign development.

**M03a-M03d and M04 are implemented and verified.** The ordinary ROM rebuilt
(exit 0) and all eighteen mechanics tests pass. Evidence in `gba/evidence/`:
`m03a-build.json` through `m03d-build.json`, plus `m04-build.json`.

Settled: Gen 5 base stats, abilities, move data and experience yields; ORAS
level-up learnsets; and a tiered move economy whose TM half is built.

**Read [MOVE_ECONOMY.md](MOVE_ECONOMY.md) before touching TMs, tutors or move
distribution.** The owner's design tiers moves deliberately: TMs are the generic
toolkit (100, twenty per region, origin-matched, capped at 85 power, single-use),
while signature moves like Thunderbolt, Ice Beam and the starter ultimates are
**tutor-only and locked to the region that invented them**, bought with trade
goods from a *different* region, trickling in late with the full list post-game.
An earlier same-day build imported B2W2's TM list wholesale; the owner rejected
that. Do not re-import a stock list.

**The next task is the tutor tiers**, which are designed but not implemented.
This is the first piece that genuinely couples to world design, so it cannot be
finished as a data edit. What it needs:

1. Choose which signature moves each region teaches from the candidate pools in
   MOVE_ECONOMY.md. Johto has 10 candidates, Kanto 25, Hoenn 19, Sinnoh 30,
   Unova 19.
2. Design the trade goods: what each region produces, names, how the player gets
   them, and rates. Only the *shape* is approved (common currency for ordinary
   tutors, cross-region goods for signature ones).
3. Implement. `all_tutors.json` is generated by scanning `data/**/*.inc`, so a
   tutor exists only if an NPC script offers it. This is map and script work.

**Place a Fairy tutor early.** Dazzling Gleam is no longer a TM under this design.
Nothing regressed in reachability -- every Fairy-typed species still learns a
Fairy attack by level-up after M03c -- but the breadth is gone until a tutor
exists.

Also open after that: Hidden Ability access, `B_UPDATED_MOVE_FLAGS`, and breeding
together with the reserved move pool.

**TM capacity is full.** The item enum reserves exactly `ITEM_TM01`-`ITEM_TM100`
and the list fills all 100. Adding a TM means removing one or renumbering every
item id after `ITEM_HM01`. `SaveBlock1` has 284 bytes free of 15,872.

**Vanilla TM rewards were rethemed, not designed.** 18 TMs that vanilla content
referenced are no longer TMs, so 28 files in `game/data`, `game/src` and
`game/test` were retargeted to type-matched survivors to keep the build green.
Those are placeholder rewards; re-specify them when the regions are built.

Three open threads to raise at the right moment, not bundled into one question:

- **Move tutors are still Emerald's 30**, and TM placement in the world has not
  started. M04 settled the TM list but none of the 50 new TMs is obtainable in
  play yet.
- **How the player obtains a Hidden Ability.** Still undecided. M03b pinned
  several hidden abilities, which does not make them reachable in play.
- **Gym leader and trainer teams.** Weather setters now exist (M03b) and the big
  special attacks hit harder (M03c). No team has been designed around either.
- **Breeding and inheritance rules.** `P_MOVE_INHERITANCE`, `P_EGG_MOVE_TRANSFER`,
  `P_ABILITY_INHERITANCE`, `P_NATURE_INHERITANCE`, `P_BALL_INHERITANCE`,
  `P_EGG_HATCH_LEVEL` and `P_INCENSE_BREEDING` are all still at inherited Gen 9
  defaults. The owner asked on 2026-09-11 that this be recorded and returned to at
  a time of the agent's choosing; it does not block the experience-yield or TM
  decisions. `P_INCENSE_BREEDING` is the one with world-facing consequences.
  **Egg-move data itself is settled and needs no decision:** it is a single file
  with no per-generation option, and a safety review confirmed nothing
  egg-exclusive on this roster is unbalanced. See
  `gba/evidence/egg-move-audit.json`.
- **Reserved move pool**, recorded 2026-09-12 and expected to integrate with the
  breeding decision above. The owner may grant some currently unreachable powerful
  moves through a deliberately difficult late-game path. Catalogue:
  [RESERVED_MOVE_POOL.md](RESERVED_MOVE_POOL.md) and
  `gba/evidence/reserved-move-pool.json`. The hook already exists --
  `sBreedingSpecialMoveItemTable` in `game/src/daycare.c`, currently one row
  (Pichu + Light Ball -> Volt Tackle). **Read the vault/TM-gap split before using
  the list:** 83 of the 255 unreachable moves are only unreachable because the
  TM/HM list is vanilla, and belong to the TM decision, not behind a reward gate.

**Resolve `species_enabled.h` before judging what is reachable.** Filtering species
by name suffix is not enough: Sirfetch'd, Ursaluna and Basculin White-Striped carry
no form suffix but are compiled out by `P_GALARIAN_FORMS`, `P_GEN_8_CROSS_EVOS` and
`P_HISUIAN_FORMS`. The egg-move review first under-counted egg-exclusive moves for
exactly this reason. Walk the `#if` guards; 787 species entries are compiled in.

**Re-run the Fairy-coverage check for any change to moves, TMs or learnsets.**
M03c nearly shipped a setting that would have left 22 of the 23 Fairy-typed
roster species unable to attack with their own type. The check is: resolve the
Fairy-typed roster from `species_info/` (note the type macros `CLEFAIRY_FAMILY_TYPES`,
`JIGGLYPUFF_FAMILY_TYPES`, `TOGEPI_FAMILY_TYPE1`, `RALTS_FAMILY_TYPE2`,
`COTTONEE_FAMILY_TYPE2`, which a naive `TYPE_FAIRY` grep misses), then intersect
each species' level-up and teachable movesets with the Fairy attacking moves.

Commands from repository root (toolchain is already installed on this machine):

```sh
python3 tools/gba/audit_config.py > gba/evidence/mechanics-config-inventory.json
python3 tools/gba/build.py
python3 tools/gba/build.py --mechanics
```

These checks do not qualify the deferred 30-box system. Do not run concurrent
builds/tests in `game/`. The test wrapper removes its temporary injected source.

How M03a-M03c were implemented, as the pattern to follow:

1. Scan every selector for the setting and resolve it against the proposed value.
   Trace shared macros separately from inline selectors, and check both
   directions: a generation switch can restore something as well as remove it.
   M03b nearly shipped a wrong summary because only the removals were counted.
2. Check what the setting reaches that is outside the Gen 1-5 roster's own data --
   retained Mega forms, Sylveon, the approved Fairy typing. Confirm each is
   actually compiled in under `include/config/species_enabled.h` before treating
   it as an exception, and pin real exceptions in the data file with a comment
   naming the decision.
3. Update `gba/mechanics-profile.json`, regenerate `gba/mechanics-profile.patch`
   from the submodule diff, and confirm `python3 tools/gba/audit_config.py` passes.
4. Add targeted assertions to `tools/gba/mechanics_test.c`, rebuild, run the
   tests, and write a new `gba/evidence/` record. Do not edit older evidence.

## Settled requirements: do not reopen

- GBA ROM, Gen 3 2D graphics, `rh-hideout/pokeemerald-expansion`; DS is archived
  fallback only. Five regions: Johto, Kanto, Hoenn, Sinnoh, Unova; 20 sanctioned
  badges; story/world roughly ten years later. No new maps/art in this phase.
- Owner handles story, creative direction and review. Agents perform routine
  production, coding, tooling, tests, asset cleanup and revisions.
- Gen 1–5 roster plus explicit Sylveon; existing Pokemon visuals. Canonical Fairy,
  late-game Mega, custom Terra confined to the final gym leader and Shadow to
  Wes's gym. Terra/Shadow are fixed additional type identities, not transformations;
  no invented matchups, third type slots, or unapproved new systems.
- Familiar party/PC interactions, target 30 boxes / 900 slots, ordinary persistent
  saves. Production currently has **14 boxes**, not 30.
- M01: Gen 4–5 per-move physical/special split, pinned `GEN_5`.
- M02: Gen 5 EXP scaling/division, held-item Exp. Share, trainer bonus, no catch
  EXP, no delayed-evolution bonus or whole-party automatic sharing. Applied.
- M03a: Gen 5 species base stats with Sylveon/Mega exceptions. Applied and verified.
  Mega Alakazam is pinned to its canonical 105 Sp. Def; Sylveon needed no change.
- M03b: Gen 5 species abilities with eighteen owner-chosen exceptions. Applied and
  verified. Kept present-day: the four weather setters and their families,
  Koffing/Weezing Neutralizing Gas, Gallade Sharpness. Overridden away from the
  Gen 5 restoration: Gengar Cursed Body, Litwick line Infiltrator. Gen 5 stands
  where it restores and the owner did not override: Zapdos Lightning Rod and the
  legendary beasts' absorbing hidden abilities.
- M03c: ORAS level-up learnsets and Gen 5 move power/accuracy/PP. Applied and
  verified. Learnsets are deliberately **not** Gen 5: that would strand 22 of 23
  Fairy-typed species with no Fairy attacking move. Mr. Mime is given Dazzling
  Gleam at 44. `B_UPDATED_MOVE_FLAGS` is deliberately still inherited.
- M03d: Gen 5 species experience yields. Applied and verified. ~190 roster species
  worth ~10% less; no exception pin was needed.
- M04: tiered move economy. 100 single-use TMs, twenty per region, origin-matched
  and capped at 85 power; signature moves excluded and reserved for origin-locked
  regional tutors gated behind cross-region trade goods. TM half built; tutor
  tiers designed only. See MOVE_ECONOMY.md.

Authoritative decisions: [FOUNDATION_DECISIONS.md](FOUNDATION_DECISIONS.md).
Detailed applied settings and remaining options: [GBA_MECHANICS_AUDIT.md](GBA_MECHANICS_AUDIT.md).

## Completed work and exact evidence

| Work | Result / where to look |
| --- | --- |
| DS deprecation | Original 45 documents preserved with checksums in `archive/gen4/snapshot-manifest.json`; archive index explains selective recovery. `.rgignore` avoids routine context loading. Donor trees retained. Do not preload archive. |
| Toolchain | Pinned expansion `expansion/1.17.0`, commit `e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7`; ARM GCC 14.2.1 toolchain and mGBA installed. Reproduction/limits in GBA_BASELINE.md and `tools/gba/toolchain.json`. |
| Roster profile | Later families/unapproved forms disabled; Gen 1–5, Sylveon and retained Mega forms preserved. `gba/roster-profile.patch`. Roster-only benchmark linked ROM ~18.65 MiB, ~13.35 MiB headroom; historical measurement, not a five-region fit guarantee. |
| Ordinary save qualification | All 420 current PC slots, party/story and a fresh-process flash reload passed. This proves current 14-box baseline only. Historical evidence in `gba/evidence/roster-*.json`. |
| Storage prototype | Isolated 900-record page store passed native/GBA tests, 1,408 simulated interruptions plus two controls, ~4,236-byte ARM workspace. Seven changed pages max per atomic transaction; roughly 2-second unoptimized three-page commit. Not integrated. See GBA_STORAGE_PROTOTYPE.md only when this topic returns. |
| Mechanics audit | All config headers except separately qualified species roster inventoried. Initial 12 corrections restore approved scope, including PC healing, trainer-battle restrictions, Fairy chart and no affection bonuses. Human summary in GBA_MECHANICS_AUDIT.md; don't preload the large inventory JSON. |
| M01 category split | Explicitly pinned; ordinary build passed. `gba/evidence/m01-build.json`. |
| M03a base stats | `P_UPDATED_STATS = GEN_5`; ordinary ROM builds and **all ten mechanics tests pass**. `gba/evidence/m03a-build.json` records ROM/source/log hashes and the full selector audit: 76 of 191 selectors moved to the B2W2 value, the 113 `>= GEN_2` selectors kept their post-Gen-1 branch, shared stat macros were traced individually, and all 98 Mega entries were scanned. Mega Alakazam was the only retained Mega the selector reached and is pinned to 105 Sp. Def; Sylveon has no selector. This is a resolved-selector audit plus sampled runtime assertions, not an exhaustive per-species historical database audit. |
| M04 move economy | 100 TMs, twenty per region, origin-matched, single-use; ordinary ROM builds and **all eighteen mechanics tests pass**. `gba/evidence/m04-build.json` and `docs/MOVE_ECONOMY.md`. Records the engine limits found (the `ITEM_TM01`-`ITEM_TM100` ceiling, and the truncating block comment inside `FOREACH_TM`), the measured save cost (SaveBlock1 15,412 -> 15,588 of 15,872), and the retheme of 18 dangling vanilla TM references. |
| M03d experience yields | `P_UPDATED_EXP_YIELDS = GEN_5`; ordinary ROM builds and **all sixteen mechanics tests pass**. `gba/evidence/m03d-build.json`. 514 of 814 selectors unaffected, 300 fall to the B2W2 value, reaching ~190 roster species at a uniform 0.90 ratio. First M03 decision needing no exception pin. |
| M03c learnsets and move data | `P_LVL_UP_LEARNSETS = GEN_6`, `B_UPDATED_MOVE_DATA = GEN_5`; ordinary ROM builds and **all fifteen mechanics tests pass**. `gba/evidence/m03c-build.json` records the Fairy-coverage resolution per candidate learnset file (Gen 5: 22 of 23 stranded; ORAS: 6, all babies or covered by a pre-evolution) and the move-data audit (133 moves, 169 selectors, no move left with zero power/accuracy/PP, no Fairy move touched). |
| M03b abilities | `P_UPDATED_ABILITIES = GEN_5` with eighteen pinned exceptions; ordinary ROM builds and **all twelve mechanics tests pass**. `gba/evidence/m03b-build.json` records the selector audit: 91 of 134 selectors are `>= GEN_4` and unaffected, 25 take the B2W2 set, 18 are owner exceptions. No Mega, Gigantamax or Sylveon entry carries an ability selector. |
| M02 experience | Ordinary ROM built; **all seven mechanics tests pass**, including five experience tests. `gba/evidence/m02-build.json` has ROM/source/log hashes. Tests check catch rewards, level scaling, held-item sharing/nonsharing, exact participant division, trainer bonus without delayed-evolution bonus, plus Fairy and trainer item-theft regressions. |

Current profile checks 25 settings (23 differ from upstream; two retained
Exp. Share settings are checked unchanged). The mechanics patch also carries
non-config engine edits: the M03a/M03b species pins, the M03c Mr. Mime learnset
pin, and the M04 TM list, bag capacity and item entries. `tools/gba/mechanics_test.c` is the
tracked runtime fixture. Initial fixture mistakes were corrected: ordinary
trainer theft must use AI trainer battles, not recorded-link singles; when a
fixture sets Speed explicitly, every Pokemon requires an explicit Speed.
The existing linker RWX warning is recorded; do not claim warning-free or release
certification. No full gameplay/menu playthrough has been performed.

Historical build evidence contains hashes of the sources **at that stage**.
Do not overwrite it to make hashes match later changes. The config inventory is
a current reproducible snapshot, not a substitute for runtime tests.

## Deferred and unresolved work

- **Save/autosave research is explicitly deferred by owner.** The page-store
  prototype's limits are not proven universal GBA limits. No automatic checkpoints,
  custom emulator requirement, or save-behavior change is approved. If revisited,
  desired autosaves rotate separately, preserve the last manual save until manual
  replacement, and complete in under a second. Retention/device details unresolved.
  Do not reopen it merely because another agent starts a session.
- Abilities/Hidden Ability availability; learnsets/move power and later Fairy move
  availability; species EXP yields; exact breeding/item rules and convenience UI.
  Gen 5 graphics/categories/EXP/stats do not approve all of these by implication.
- Exact damage/status/weather generation settings still mostly inherit Gen 9.
  Do not globally redefine `GEN_LATEST`.
- Mega eligibility and story unlock; Terra/Shadow matchups, moves and assignments.
  Disabling form assets does not globally disable Z-Move/Dynamax/Tera activation
  code. A future production eligibility/content audit is still required.
- Solo trade evolution alternatives exist in upstream tables (e.g. Linking Cord),
  but their availability is unapproved. Reusable TMs remain a separate choice.
- Once mechanics choices are settled, plan stable campaign flags/variables,
  20 badges and five-region travel identifiers. Preserve engine flags and optional
  event independence. Save-dependent integration awaits storage qualification.
- Validate map/tool constraints before any visual pilot. Porymap/Poryscript/
  Porytiles/Aseprite-compatible workflows are chosen direction, not proof every
  dependency is installed or every import path is qualified.

## Preserve this workspace

There is substantial uncommitted work from this conversation and preexisting
work. No commit or push was made during this handoff. Inspect status first;
never reset/clean the tree or blanket-stage unrelated paths.

`game/` is a pinned submodule with roster/mechanics edits. The parent patches are
its reproducible source of changes. `roster-profile.patch` covers
`include/config/species_enabled.h` only. `mechanics-profile.patch` covers the
three config headers plus the M03a Mega Alakazam stat pin in
`src/data/pokemon/species_info/` (the M03a Mega Alakazam stat pin and the M03b
ability exceptions, currently in the gen 1, 3 and 5 family files) and
`src/data/pokemon/level_up_learnsets/` (the M03c Mr. Mime pin); regenerate it with
a plain `git -C game diff` over exactly those paths after any mechanics change. On a
fresh clean pin, use:

```sh
python3 tools/gba/profile.py apply
python3 tools/gba/profile.py apply --profile mechanics
```

Do not apply again in this already-patched checkout. Use `git apply --reverse
--check` to verify a patch is present without removing it. Preserve unrelated
dirty `disasm/pokeheartgold`, `tools/omni/`, `tools/omni-editor` and other existing
work. The staged submodule/gitmodules additions predate this handoff. Avoid
committing ROMs, saves, binaries or ignored toolchain/log directories.
