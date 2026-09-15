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
