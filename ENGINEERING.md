# Pokemon Apocrypha — Engineering Reality

> Companion to `DESIGN.md`. Where DESIGN.md is the source of truth for *what the game is*, this document is the source of truth for *what it takes to build it*. It records engineering scope, build tasks, and technical constraints assessed against the actual toolchain.
>
> **When to consult this document:** any implementation, porting, build-system, engine-modification, asset-pipeline, or feasibility work — anything that touches how the game is made rather than what it contains. For creative and narrative decisions (story, characters, world, gyms, tone), DESIGN.md remains authoritative. When a design decision has engineering cost, note it here; do not relitigate the design there.

---

## Toolchain

- **Base engine**: pokeheartgold decomposition project (Gen-4 Nintendo DS, ARM9, C).
- **Vendored submodules** (`.gitmodules`): pokeheartgold, pokeplatinum, pokeemerald, pokefirered.
- **Not vendored**: any Gen-5 (Black/White, Black 2/White 2) decomp. None suitable exists — see Region Sourcing, Unova.

> **Verification status.** The pokeheartgold submodule is now checked out (pinned `b843c93`) and has been read directly; the other three remain uninitialized. Engine-internal facts confirmed against real source are recorded under **Verified Findings** below. Region sourcing, mechanic approach, and dex breadth are confirmed design decisions. No build has been produced yet — see the build blocker note.

## Verified Findings (pokeheartgold @ b843c93)

Read directly from source, not inferred:

- **Codebase scale**: 312 `.c` files, 513 headers. A substantial but tractable C decomp (MWCC/ARM9).
- **National Dex cap = 493** (`SPECIES_ARCEUS`). `NATIONAL_DEX_COUNT`, `MAX_SPECIES`, and `NUM_SPECIES` (= `SPECIES_ROTOM_MOW`) all top out at the Gen-4 roster. Crucially, Pokedex *storage* is sized off this constant — `caughtLanguages[ROUND_UP(NATIONAL_DEX_COUNT, 4)]` and `NUM_DEX_FLAG_WORDS = CEILDIV(NATIONAL_DEX_COUNT + 8, 32)`. Adding *any* species past 493 (even our bounded Gen 1–5 + picks set needs slots for the picks) means bumping this constant and every save array derived from it. The single-region-dex assumption is real and load-bearing.
- **Story-state budget** (crux of the progression state machine): base HGSS ships **`NUM_FLAGS = 2912`** persistent flags (stored as `u8 flags[NUM_FLAGS / 8]` = 364 bytes), plus 64 temp, 64 map-temp, and 192 daily flags; and **`NUM_VARS = 0x170` = 368** `u16` script vars (`u16 vars[NUM_VARS]` = 736 bytes) plus 32 temp vars and 14 special vars. Vanilla HGSS already spends a large share of these on Johto + Kanto. A five-region, 20-badge, five-thread game with a concurrent B2W2 timeline will almost certainly exhaust this budget — so **expanding `NUM_FLAGS`/`NUM_VARS` and the save block that holds them is a concrete, quantified task**, not a vague worry.
- **Save architecture**: sector-based flash save; the top-level `SaveData` struct is **`0x2330C` bytes (~140 KB)** and is partitioned into many named sub-blocks (`save_vars_flags`, `save_pokegear`, `save_local_field_data`, `save_follow_mon`, `save_trainer_card`, …). The flag/var store lives in `save_vars_flags`. This is exactly the layer any multi-region state expansion has to modify, and its size/CRC/sector layout must be versioned to avoid bricking saves across builds.
- **Field/map system** present (`field_system.c`, `field_*`) for later inspection of the map-matrix and region-map assumptions (not yet audited in depth).

> **Build blocker (step zero).** Per `INSTALL.md`, a *matching* build requires two proprietary components that the project cannot distribute and that are **not obtainable in this environment**: the **Metrowerks MWCC ARM compiler** (`tools/mwccarm/…`, run under wine) and the **Nitro SDK** (`tools/bin/…`), both distributed via the pret Discord, plus `binutils-arm-none-eabi`, `libpng`, and python3. A future GCC path is mentioned in the README but not yet available. **Consequence:** we cannot produce a ROM here until those toolchain artifacts are supplied. Source-level analysis, content/asset planning, and the state/dex/save architecture design can all proceed without a compile; anything requiring a built ROM is blocked on obtaining the compiler + SDK.

---

## Region Sourcing

Five regions, one target engine (HGSS). Mapping confirmed with the design owner (2026-07):

| Region | Source | Nature of the work |
|--------|--------|--------------------|
| Johto | pokeheartgold | Native. Home turf — no porting. |
| Kanto | pokeheartgold (base) + pokefirered (reference/assets) | Native HGSS post-game Kanto is the base; pokefirered is the vendored source for Kanto assets/reference to flesh it out. |
| Sinnoh | pokeplatinum | Same-generation DS port. Platinum and HGSS share a large amount of engine code; reconcile two close forks into one ROM. |
| Hoenn | pokeemerald | Cross-generation port. Gen-3 GBA map/block/collision/tileset formats converted to the DS engine's NARC-based formats. Full source data exists; the effort is conversion, not authoring. |
| Unova | B2W2 ROM (direct extraction) | No decomp exists anywhere. Extract map data from the retail B2W2 ROM with DS map tools, then convert Gen-5 NitroSystem formats to the Gen-4 HGSS format. The only region with no in-repo source. |

**Unova sourcing note.** No Black 2/White 2 decompilation exists: pret has no Gen-5 project ([pret/pokefirered#99](https://github.com/pret/pokefirered/issues/99) was never taken up), and the only live Gen-5 effort — [pokemodding/pokeblack](https://github.com/pokemodding/pokeblack) — targets BW1, not B2W2, and is early-stage disassembly (~97% asm). Everything else for B2W2 is script-only tooling ([b2w2-scripts](https://github.com/PhoenixBound/b2w2-scripts), [CheapScript](https://github.com/CodenamePU/CheapScript), the [ds-pokemon-hacking B2W2 resources](https://ds-pokemon-hacking.github.io/getting-started/b2w2/)). Direct ROM extraction is therefore the path; it is a mature, well-supported workflow (Tinke, SDSME, the ds-pokemon-hacking toolchain), with the real work being Gen-5→Gen-4 format conversion, not authoring.

---

## The Five Hardest Problems

1. **Merging engine forks and porting the two non-native regions.** HGSS and Platinum are separate Gen-4 decomp forks that must be reconciled into a single ROM; Hoenn is a Gen-3→Gen-4 format conversion; Unova is a Gen-5→Gen-4 extract-and-convert. Four of five regions have source in hand, so the burden concentrates in the Hoenn conversion and the Unova sourcing gap rather than spreading across all five.

2. **Battle mechanics that postdate the engine.** Gen 4 already has the physical/special split, but the gym roster requires Fairy type (Gen 6), Mega Evolution (Gen 6), Terastallization (Gen 9), and Shadow Pokemon (the Gen-3 Colosseum/XD subsystem). The approach (confirmed with the design owner) is to **adapt existing community implementations** where they exist rather than building each from scratch — matching the DESIGN.md Mega Evolution note. Integration is still substantial: Fairy in particular means retrofitting an 18th type into the type chart, the type enum, damage calc, and every species'/move's type data, and each community patch must be ported to the HGSS base and made to coexist with the others. Compounded by the "harder AI" mandate. The obtainable dex is roughly Gen 1–5 plus select cross-region picks (e.g. Sylveon) — **not** a full National Dex and no Gen 7–9 species — so the added-species asset burden (DS-format animated sprites, cries, dex entries) is bounded to those specific picks rather than hundreds of species.

3. **Raising the engine's single-region hardcoded limits.** The Gen-4 engine assumes one region. Some of this is now confirmed against source (see Verified Findings): the **National Dex cap of 493** with save arrays sized off it, and the **2912-flag / 368-var story-state budget**. Still to audit: the fly/town-map/region-map system, the map-matrix and header tables, the Pokegear map UI, and the ARM9 overlay budget against 4 MB main RAM. A five-region world breaks these limits and requires low-level engine work distinct from content authoring.

4. **A nonlinear, cross-regional progression state machine.** "Gated between regions, flexible within them," routes that open and close on story events, five cross-regional threads that hint in multiple regions but climax in one, Silver appearing everywhere, and the B2W2 timeline retconned to run concurrently (the player always arrives after events resolved — "one step behind"). This demands a purpose-built quest-stage architecture over the engine's script system, kept soft-lock-proof across a partly player-chosen region order.

5. **Level curve, balance, and the solo-dev content and testing pipeline.** A meaningful difficulty ramp across twenty badges and five regions, constrained by the region-native roster rule and region-locked early dex, tuned so no region trivializes a later one across a branching order (DESIGN.md Open Question 13). Wrapped around it: heavier DS asset authoring (maps, animated sprites, NARC-packed scripts) and a combinatorial testing surface (every region-entry order x within-region gym order) that will need automated battle simulation rather than manual playtesting.

---

## Build-Out Roadmap

Ordered milestones. Sequencing is driven by cost-of-delay: foundational decisions that are cheap now and expensive to retrofit come first, content that depends on them comes after, and additive/deferrable systems slot in where convenient.

**Toolchain ownership:** the design owner supplies and runs the build locally (proprietary MWCC + Nitro SDK — see build blocker). Milestones are tagged **[build]** if they require a compiled ROM to validate, or **[source]** if they can be fully designed/authored at the source level without compiling. [source] work can proceed in this environment now; [build] work is gated on the owner's local toolchain.

### M0 — Buildable baseline  [build, owner]
Goal: an unmodified, byte-matching HGSS ROM building locally, plus a place for modifications to live.
- Install MWCC + Nitro SDK; init all four submodules; produce matching `pokeheartgold.us.nds`.
- Stand up reproducible build (document exact steps; optional CI once the toolchain can be provisioned).
- Establish the modification layer / branch structure so engine edits are tracked cleanly against the pinned decomp.
- **Gate for everything [build] below.** Until M0 exists, downstream work is design-only.

### M1 — Foundational architecture  [source] design, [build] to land
The load-bearing layer. Must be settled before authoring region content, because every map/script/save bakes in these assumptions.
- **Dex expansion**: raise `NATIONAL_DEX_COUNT` / `MAX_SPECIES` from 493 to cover the Gen 1–5 roster (national #1–649) plus the specific cross-region picks (Sylveon, etc.). Relocate the internal sentinels currently occupying 494–507 (`SPECIES_EGG`, `SPECIES_BAD_EGG`, Rotom forms). Resize the derived save/dex arrays (`caughtLanguages`, `NUM_DEX_FLAG_WORDS`). Add species data, learnsets, evolutions, sprites, and cries for the added set.
- **State/save architecture**: expand `NUM_FLAGS` (2912) and `NUM_VARS` (368) to a five-region budget; add a versioned `SAVE_STORY_STATE` block for a structured quest-stage machine; version the save so builds don't brick testers. **Designed in detail: [`engineering/m1-state-save-architecture.md`](engineering/m1-state-save-architecture.md).**

### M2 — Multi-region infrastructure  [source] audit, [build] to land
- Finish auditing the single-region assumptions flagged in problem #3 (map-matrix, region-map/fly, Pokegear map, ARM9 overlay budget).
- Design and implement multi-region map headers/matrix, region-switching, and a fly/town-map that spans five regions.

### M3 — Region content porting  [build to validate; [source] planning now]
Per the confirmed sourcing table. Each region: maps, tilesets, encounter tables, scripts, gym.
- Johto (native — re-dress existing HGSS maps to the new story).
- Kanto (HGSS base + pokefirered assets/reference).
- Sinnoh (pokeplatinum same-gen port).
- Hoenn (pokeemerald Gen-3 -> Gen-4 format conversion).
- Unova (B2W2 ROM extraction -> Gen-4 conversion).

### M4 — Battle mechanics  [build] — additive, can parallelize with M3
Adapt community implementations (confirmed approach), port each to the HGSS base, and make them coexist.
- Fairy type (18th-type retrofit), Mega Evolution, Shadow Pokemon, Terastallization.
- "Harder AI" pass.

### M5 — Narrative & systems content  [build]
- Chapter scripting (the DESIGN.md spine), Silver encounter points, the five cross-regional threads, route gating, and wiring it all onto the M1 quest-stage system — kept soft-lock-proof across the branching region order.

### M6 — Balance & test tooling  [source] tooling, [build] to run
- Level curve across the 20-badge arc (DESIGN.md Open Question 13); encounter tables and trainer teams.
- Automated battle-simulation harness to cover the combinatorial region/gym-order surface rather than manual playtesting.

**Critical path:** M0 → M1 → (M2, M3) → M4/M5 → M6. M1 is the highest-leverage design work available right now and needs no build, so it is the recommended immediate focus while the owner stands up M0.
