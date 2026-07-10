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

## Region Port Status (M2/M3 — updated 2026-07-09, v5)

**Sinnoh and Hoenn overworlds are in the ROM and traversable, with Sinnoh
buildings and full-scale seamless Hoenn rendering.** Tooling lives in
`tools/regionport/` (all generators idempotent; run `import_sinnoh.py` then
`import_hoenn.py`, `rm files/fielddata/mapmatrix/map_matrix.narc`, rebuild).

- **Sinnoh** (same-gen lift): all 176 Platinum overworld chunks converted to the
  HGSS land-data container, 13 Platinum tilesets, 30x30 matrix, 66 headers
  (`MAP_APOC_SINNOH_*`, ids 540-605). **v2 adds building props**: the 140
  Platinum building models the ported areas need are appended to
  `bm_field.narc`/`a/0/4/0` (global ids 340-479; HGSS caps the model-file array
  at 550), with matshp locator records, per-area build lists + prop texture
  sets, and `a/1/0/7` no-anim members (HGSS reads that NARC per model id with
  NO bounds guard — missing members hang the engine). Towns render real
  Platinum architecture. `MAP_MATRIX_MAX_SIZE` 799→900; RomSize 1G→2G.
  Causeway carver opens gate/cave seams; ~80% of the on-foot overworld is
  reachable from the arrival pier.
- **Hoenn** (cross-gen rebuild): 190 chunks *generated* from pokeemerald data —
  real per-tile collision, flat BDHC, NSBMD models by template surgery on an
  **outdoor** Platinum chunk (`map_data_147`; posScale 64 — v1 templated an
  indoor chunk whose posScale 32 drew every chunk at HALF scale around its
  center, the root cause of all "black chunk" sightings). **One shared
  area/texture set for the whole region** (the engine binds chunk textures
  against the current map's area, so per-map areas break cross-map rendering):
  a global pool of 189 repeating tile textures + one 512x256 atlas
  (2x2 supertiles incl. pool-pattern blocks, 2x1/1x2 pair-tiles, 8px tail with
  nearest-content remap), per-chunk material name patching, and real NNS
  patricia dictionary trees (dicts with 16+ entries are tree-walked by the
  engine; builder verified against all 148 Platinum tileset dicts). Every 2x2
  chunk window is budgeted under 5400 vertices (DS renders ~6144/frame).
  45 headers (`MAP_APOC_HOENN_*`, ids 606-650), all `areaDataBank = 119`.
  Emerald pixels render as flat "diorama" ground with correct collision.
- **v3 — Sinnoh interactivity** (`sinnoh_life.py`, run after `import_sinnoh.py`;
  persists per-map banks to `build/sinnoh_overrides.json` so importer re-runs
  keep them): 384 always-visible Platinum NPCs imported with coordinates 1:1
  (the Sinnoh matrix preserves Platinum's 30x30 layout), sprites remapped to
  HGSS equivalents, movement remapped, generic Apocrypha dialogue from a new
  msg bank (`msg_0830_APOCSIN`) + script bank (`scr_seq_0967_APOCSIN`; script 0
  is the Canalave→Cherrygrove return ferry). PC/Mart doors in 15 cities warp to
  30 cloned interiors (headers 670+ reusing Cherrygrove PC/Mart map+scripts —
  nurse healing and the shop work verbatim; exit warps return to the right
  city). 49 wild-encounter tables generated from Platinum's encounter JSONs
  into `g_/s_enc_data.csv` (land levels/species incl. time-of-day slots 2/3,
  surf/rod slots, dual-slot species → Hoenn/Sinnoh Sound radio). Verified
  in-emu: Canalave loads with wandering NPCs, PC door → cloned interior
  (nurse/PC/escalator alive) at the door tile.
- **v3 — Hoenn 3D buildings** (`hoenn_buildings.py`, driven by
  `import_hoenn.py`): enterable buildings extracted per map by rectangle
  growth from each warp door (body = impassable at **elevation 0** — fences
  and cliffs sit at elevation 3; up to 3 roof-art rows above), art cropped
  from the rendered map, masked, and deduped perceptually (type+size+per-tile
  mean color — exact bytes differ across towns via baked background corners).
  Each distinct art becomes a fold-billboard NSBMD prop (front wall vertical,
  roof tilted back, solid-color sides from an 8x8 patch baked into the
  texture padding) textured with its own GBA art as pltt16 (color 0
  transparent), registered through the Sinnoh prop pipeline (models 480+,
  matshp, anim stubs, one build list + prop texset for shared area 119).
  Footprints are flattened in the ground to the door-approach tile before
  texture planning. Verified in-emu: Slateport's Pokémon Center and Mart
  stand as real 3D buildings on clean ground.
- **v3 — lighting fix**: generated Hoenn chunks were unlit vertex-color
  materials (v2's template normalization used the *indoor* recipe), which the
  arealight day/night system cannot tint — they rendered ~half-bright at noon
  and never darkened. Chunk materials now use the vanilla outdoor recipe
  (light0 enable + fog + white ambient + vertex-color diffuse, both faces);
  Slateport midday brightness now matches vanilla Johto (140 vs 145 mean).
  `files/data/area00light.txt` is parsed at runtime and is CRLF-sensitive —
  LF-only or missing final `EOF` hangs every outdoor map load.
- **Access (temporary scaffolding)**: two sailors on Cherrygrove beach warp to
  Canalave City (38,743) and Slateport City plaza (216,272); return sailors at
  both piers. Scripts 019-022 in `scr_seq_0850_T21.s` (Canalave's return
  sailor now uses `scr_seq_0967_APOCSIN` script 0).
- **Hard limits mapped**: HGSS renders props by the matshp locator's
  mat/shp pairs — a locator count of 0 draws NOTHING (Platinum's C falls back
  to a full-model draw); every generated prop carries one (mat0,shp0) pair.
  Field **texture VRAM holds ~192KB total** (empirical: ground 175KB + props
  16KB works; +69KB corrupts the ground; +99KB corrupts the props), so the
  building texel budget is 16KB = the 6 most-instanced arts (PCs, marts,
  common houses; 18 placements). Raising it requires shrinking the ground
  atlas (512x256 fixed) — a retune of the supertile/merge/vertex system.
- **v4 — HM field moves from bag items**: overworld Cut/Surf/Strength/Rock
  Smash/Waterfall/Whirlpool/Rock Climb are usable whenever the matching HM
  item (ITEM_HM01..08) is in the bag — no badge, no party mon that knows the
  move. Most gates live in the std field-move script `scr_seq_0146.s` (each
  handler's `get_party_slot_with_move`+`check_badge` pair → `hasitem
  ITEM_HMxx`; the mon that plays the field animation falls back to the party
  lead). **Surf is special**: its tile-interaction is gated in still-ASM
  overlay code (`asm/overlay_01_021E6880.s`, `GetInteractedMetatileScript`) —
  the badge(FOG)+`GetIdxOfFirstPartyMonWithMove(SURF)` pre-checks there bail
  before the script runs, so those two conditionals were removed and the
  bag-item gate added to the surf script instead. Party-menu badge gates
  disabled in `field_move.c` (8 `PlayerProfile_TestBadgeFlag` blocks). An HM
  porter NPC on the Canalave pier hands out HM01-08 once (keyed on owning
  HM01). Verified in-emu: the surf prompt fires with an empty/no-Surf party
  (mounting still needs *a* Pokémon to ride). ASM overlay `.s` files ARE
  assembled by the build (COMPARE=0), so editing them is a supported patch
  path — mind the assembler uses `;` for comments, not `@`.
- **v4 — Sinnoh fully populated**: every city building is enterable (181
  interior clones — PC/Mart + generic house rooms cloned from Cherrygrove,
  headers 670+); town/route **signposts** carry name+slogan text; **location
  names** show in the entry popup (new `MAPSEC_APOC_*` values 235+, appended
  `msg_0279` rows indexed by mapsec — the popup indexes that gmm directly, so
  gmm rows must track new mapsec constants 1:1; town-map position is
  per-header `worldMapX/Y`, not mapsec-indexed, so it's safe); **music** set
  per map type (SEQ_GS town/city/port/snow/route themes; day==night per
  vanilla convention).
- **v4 — Sinnoh building lights**: Platinum window-light animations ported
  for the imported building models. `bm_anime` files (NSBTA/NSBTP, byte-
  identical between games) copied into HGSS `a/1/0/6`; per-model 24-byte list
  entries rebuilt in `a/1/0/7` from Platinum's 20-byte `bm_anime_list`
  members (re-based file ids; day/night pairs preserved as header `flags
  0x03 / kind 2 / 2 ids`). The lit-window textures already live in the
  imported prop texture sets, so no extra texture import was needed.
- **v4 — Hoenn art**: the roof-with-ground-baked-in artifact is fixed —
  roof-overdraw rows (passable rows above a building's collision body) are
  re-rendered from the metatiles' **top layer only** (color 0 transparent),
  so no ground bleeds behind the roof. All Emerald-derived ground + building
  textures get a +12% brightness lift (`HOENN_GAIN`) to match DS-native map
  brightness (Slateport plaza mean ~150 vs vanilla Johto ~145).
- **v5 — Hoenn ground cleanup** (the "fuzzy, wrong pixels" pass): three
  compounding texture-quality bugs fixed in `import_hoenn.py`/`nsbmd.py`:
  1. **Dither speckle**: every ground texture went through PIL `quantize()`
     whose *default* is Floyd-Steinberg dithering — deliberate noise scattered
     over every tile, shimmering where tiles repeat. All quantize calls now
     pass `dither=NONE` (atlas additionally uses MAXCOVERAGE, which keeps
     dominant exact colors — better for flat-color pixel art).
  2. **Pool tiles now pixel-exact 4bpp**: the 191 repeating pool textures
     (the majority of on-screen area) were 8bpp indices into one shared
     256-color palette. They're now format-3 (4bpp) with **first-fit grouped
     16-color palettes** (29 groups, BGR555-exact for tiles with ≤16 colors —
     nearly all of them): truer color than the shared palette at HALF the
     texels (63KB→24KB). Vanilla area texsets are almost entirely fmt 2/3
     (only THREE 8bpp textures in all 119) — this is the vanilla pattern.
     `build_btx_named` grew a 6th tuple element: fmt-3 *without* the
     color-0-transparent bit (ground must be opaque; buildings keep it).
  3. **TEMPLATE PALETTE-DICT TRAP (the v5 regression)**: per-material palette
     names only bind correctly if the template's palette dict has one entry
     per material. `map_data_147`'s dict has SEVEN entries — materials 3+4
     share one — so patching 8 distinct names positionally shifted every
     binding after slot 3 and silently dropped the 8th (`glb_pl`): washed-out
     pale Hoenn, atlas drawn with a 16-color pool palette. Template is now
     `map_data_415` (outdoor beach, 8 mats/shapes/textures/palettes, one
     material per dict entry), and `build_model` patches names through the
     dict-slot→material permutation (`tex_slot_of`/`pal_slot_of`), not by
     position. Diagnosed by decoding a generated chunk's dicts offline —
     cheaper than emulator round-trips.
  Also: 16px-tier promotion in the atlas is now score-greedy across
  supers/pairs/singles (equal extra-bytes per tile-occurrence ⇒ one merged
  occurrence ranking); LANCZOS→BOX for 8px downscale (no ringing);
  prop texel budget 16K→40K from the pool savings (13 building arts now 3D,
  27 placements — shipyard/museum-class landmarks still splat); RTC-noon
  verification trick: py-desmume `movie.record(rtc_date=…)` forces daytime
  regardless of host clock (arealight tint otherwise makes night captures
  unjudgeable).
- **v5 reality check on capacity**: the detail layer wants 2438 distinct
  16x16 tiles ≈ 610KB at 8bpp — VRAM holds ~200KB total, so the single
  512x256 atlas keeps everything at 8px (1030 kept, 1408 rare singles
  remapped to nearest). Fixing *that* needs the multi-material vanilla-style
  architecture (more pool slots per chunk + several 4bpp group atlases), a
  future round.
- **v4 gaps**: Sinnoh interiors are all Cherrygrove clones (no bespoke gym/
  house layouts); Mart clones sell Cherrygrove stock; NPC dialogue is a
  16-line generic pool; encounter tables still unverified in battle; Hoenn
  ground is still flat (no 3D relief) and rarer buildings beyond the 16KB
  prop-texel budget stay 2D-baked; surf-only areas + Hoenn east islands
  unreached; long-range `emu_ram.teleport` corrupts chunk-streaming (black
  screen on next warp) — short in-map hops are safe. Building window lights
  are ported but only verified as **non-crashing** (Canalave loads and is
  playable); the day/night frame-select call site is HGSS field ASM, so
  whether windows actually toggle at night is unconfirmed.

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
- **Dex expansion**: raise `NATIONAL_DEX_COUNT` / `MAX_SPECIES` from 493 to cover the Gen 1–5 roster (national #1–649) plus the specific cross-region picks (Sylveon, etc.). Relocate the internal sentinels currently occupying 494–507 (`SPECIES_EGG`, `SPECIES_BAD_EGG`, Rotom forms). Resize the derived save/dex arrays (`caughtLanguages`, `NUM_DEX_FLAG_WORDS`). Add species data, learnsets, evolutions, sprites, and cries for the added set. **Designed in detail: [`engineering/m1-dex-expansion.md`](engineering/m1-dex-expansion.md)** (~157 new species; assets sourced from the same B2W2 extraction as Unova).
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
