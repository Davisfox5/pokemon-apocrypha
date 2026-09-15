# M1 — State & Save Architecture

> Milestone M1 (foundational), state/save half. Design-level; no build required to author it. Grounded in the checked-out `pokeheartgold @ b843c93` source. This is the load-bearing layer: every region map, script, and save baked afterwards assumes it, so it is settled before content authoring (M3+).
>
> Companion: `../ENGINEERING.md` (roadmap, verified findings). Symbol/file references below are into `disasm/pokeheartgold/`.

## 1. Verified baseline

| System | Fact | Source |
|--------|------|--------|
| Persistent script flags | `NUM_FLAGS = 2912` (bits), stored `u8 flags[NUM_FLAGS/8]` = 364 B | `include/constants/flags.h:2222`, `include/save_vars_flags.h` |
| Named flags in use | ~2246 `FLAG_*`/`SYS_FLAG_*` defines → **~666 free** | `include/constants/flags.h` |
| Flag ID layout | maptemp `0x1`(64), daily `0xAA0`(192), persistent max ≈ `0xB60`; **temp (RAM-only) at `TEMP_FLAG_BASE 0x4000`** | `include/constants/flags.h:14,2026,2225` |
| Persistent vars | `NUM_VARS = 0x170` (368 × u16 = 736 B); ~full | `include/constants/vars.h:384` |
| Var ID layout | `VAR_BASE 0x4000`, temp/objgfx carved from the low range, `SPECIAL_VAR_BASE 0x8000` (14 special) | `include/constants/vars.h:4,386` |
| Flag/var access | `Save_VarsFlags_{Check,Set,Clear}FlagInArray`, `…GetVarAddr`; asserts bound to `NUM_FLAGS`/`NUM_VARS` | `src/save_vars_flags.c` |
| Save slot | `dynamic_region[SAVE_PAGE_MAX * SAVE_SECTOR_SIZE]` = 35 × `0x1000` = **`0x23000`** (143,360 B); double-buffered (`saveSlotSpecs[2]`) | `include/save.h`, `include/constants/save_arrays.h` |
| Save blocks | **42** blocks (`SAVE_BLOCK_NUM`), dynamically packed by `gSaveChunkHeaders[]` via per-block `sizeof()`/`Init()`; per-block header w/ offset+size+CRC | `src/save_arrays.c`, `include/constants/save_arrays.h` |
| Flags/vars block | `SAVE_FLAGS` (id 4) → `SaveVarsFlags` struct | `src/save_vars_flags.c` |
| Dex storage | `Pokedex` struct `0x340`; `caughtSpecies/seenSpecies/seenGenders` sized by `NUM_DEX_FLAG_WORDS = CEILDIV(NATIONAL_DEX_COUNT+8,32)`, `caughtLanguages[ROUND_UP(NATIONAL_DEX_COUNT,4)]` | `include/pokedex.h` |

**Takeaway:** the *byte* cost of expansion is small (a few KB); the *binding* constraint is slack inside the fixed `0x23000` slot, and ultimately flash capacity. Flag/var **ID** space is plentiful (large gaps below `0x4000`); flag/var **storage** and **named-slot availability** are what's scarce.

## 2. Requirements driving the design

The design (see `../DESIGN.md`) needs the save/state layer to hold, durably and without soft-locks:

- **20 badges** across **5 regions** (progression gate state, per-region + global).
- **Inter-region gating** ("gated between regions, flexible within") — route open/close state that changes on story events.
- **Five cross-regional threads**, each hinting in several regions and climaxing in one — i.e. per-thread progress that multiple regions read and write.
- **Silver encounter cadence** and other recurring-NPC state across all regions.
- **Concurrent B2W2 timeline** — the player arrives *after* events resolve ("one step behind"), so Unova needs a timeline cursor decoupled from the player's own progress.
- Headroom for ~5× the per-region NPC/quest flags vanilla spends on Johto+Kanto alone — well beyond the ~666 free flags left.

## 3. Design decisions

### D1 — Grow the general flag/var budget in place
Bump `NUM_FLAGS` and `NUM_VARS` so ordinary scripts keep using stock `FlagSet/FlagGet/VarGet` with a larger pool.
- **Flags:** raise `NUM_FLAGS` from `2912` toward (but below) `TEMP_FLAG_BASE 0x4000`. Even `NUM_FLAGS = 0x3000` (12288) costs `flags[1536]` (+1.2 KB) and yields ~9k free persistent flags, with the temp base untouched. Keep maptemp/daily where they are.
- **Vars:** raise `NUM_VARS` from `0x170` toward the `SPECIAL_VAR_BASE 0x8000` ceiling (relative to `VAR_BASE 0x4000`, room up to `0x4000` entries). A modest `NUM_VARS = 0x400` (1024) costs `vars[1024]` (2 KB) and triples the pool.
- **Cost:** small, additive bytes into `SAVE_FLAGS`. No API changes; asserts in `save_vars_flags.c` follow the constants automatically.
- **Constraint:** counts against the slot budget — see D4.

### D2 — Dedicated, versioned `SAVE_STORY_STATE` block for the quest machine
Do **not** encode the story spine as hundreds of loose booleans. Add one new save block holding a *typed, structured* state machine (section 4), accessed by a small typed API plus new script commands.
- New id `SAVE_STORY_STATE = 42`; `SAVE_BLOCK_NUM` → `43`. Register a `sizeof()`/`Init()` pair in `gSaveChunkHeaders[]` exactly like the existing 42.
- **Why separate:** isolates our data from vanilla flag ranges (no renumbering churn), makes the spine debuggable/inspectable as fields rather than bit-hunting, and lets us version/migrate it independently.
- Loose flags (via D1's expanded pool) still handle one-off, local NPC/quest booleans; the structured block handles anything cross-regional, gate-bearing, or timeline-related.

### D3 — Schema versioning & migration
The engine gives per-block CRC and a chunk `magic` (`0x20060623`) but **no semantic schema version** for our data.
- Prefix `SAVE_STORY_STATE` with `u32 schemaVersion` (and a project-wide `APOCRYPHA_SAVE_VERSION`).
- On load: CRC-valid but version-mismatched → run a migration step (or, pre-1.0, a guarded safe-reset of just that block) rather than silently reinterpreting bytes. This is what prevents new builds from bricking testers' saves — the risk called out in the roadmap.
- Same discipline for any resized vanilla block we own (e.g. the enlarged `SaveVarsFlags`).

### D4 — Slot-budget fit (measure, then choose)
All of D1+D2 consume the fixed `0x23000` slot. Sequence:
1. **Measure** (first thing once M0 builds): sum the packed block sizes + headers to get current slack in `0x23000`. HGSS runs near its save limit, so treat slack as unknown until measured.
2. If slack ≥ our additions (est. **~5–8 KB**: ~1–2 KB flags, ~1–2 KB vars, ~2–4 KB story block, +~0.3 KB dex): land as-is.
3. If not: raise `SAVE_PAGE_MAX` (grow the slot in `0x1000` pages). This touches slot/sector math and is bounded by the cartridge flash capacity and the two-slot + extra-chunk layout — verify against the flash size before committing. Prefer keeping additions lean enough to avoid this.

### D5 — Dex arrays (coordination with the dex-expansion half of M1)
State-side impact only: raising `NATIONAL_DEX_COUNT` (493 → Gen-1–5 `≈649` + picks) auto-resizes `Pokedex` via its macros — est. **~+250 B** (`NUM_DEX_FLAG_WORDS` 16→~21; `caughtLanguages` 496→~660). Requires relocating the sentinels currently at 494–507 (`SPECIES_EGG`=494, `SPECIES_BAD_EGG`=495, Rotom forms → `NUM_SPECIES`=507). Owned by the dex half; noted here because it shares the slot budget in D4.

## 4. The quest-stage model (contents of `SAVE_STORY_STATE`)

Structured, monotonic, and soft-lock-resistant by construction:

```
struct StoryState {
    u32 schemaVersion;

    u32 badges;              // 20-badge bitfield (1 bit/badge)
    u8  chapter;             // linear chapter cursor (DESIGN.md chapter spine)
    u8  region;              // current region id
    u8  regionsUnlocked;     // bitfield of inter-region access

    u8  threadStage[5];      // one monotonic enum per cross-regional thread
                             // (Research, Energy, Stone, Trade, Silver/Apex)
    u8  regionStage[5];      // per-region local progress cursor

    u8  b2w2Cursor;          // concurrent Unova timeline position ("one step behind")
    u8  silverEncounter;     // Silver cadence counter across regions
    // + reserved padding for forward-compat growth
};
```

Principles:
- **Monotonic stage enums, not scattered booleans.** A thread/region advances by incrementing a stage; "is route X open?" and "has event Y happened?" are *derived* from stage comparisons, not stored independently. This makes illegal/contradictory combinations unrepresentable — the core soft-lock defense across a partly player-chosen region order.
- **Gates are functions of state**, evaluated by a central `IsRouteOpen(route)` / `IsRegionUnlocked(r)` helper reading `threadStage`/`regionStage`/`regionsUnlocked` — so gating logic lives in one auditable place, not sprinkled across map scripts.
- **Timeline decoupling:** `b2w2Cursor` advances independently of the player's own progress, modelling "the B2W2 protagonist already resolved this."
- **Invariant checks:** a debug validator asserts monotonicity and cross-field consistency on load and after each advance, to catch soft-lock states in testing.

Access: a typed API (`StoryState_Get`, `StoryState_AdvanceThread`, `StoryState_HasBadge`, `IsRouteOpen`, …) plus thin script-command wrappers so map scripts can read/advance stages without touching raw bytes.

## 5. Risks & open items
- **Slack unknown until M0 builds** (D4 step 1) — the one hard dependency on the owner-supplied toolchain. Everything else here is authorable now.
- **`SAVE_BLOCK_NUM` change** ripples anywhere the count is assumed; audit `gSaveChunkHeaders[]` ordering and any `SAVE_BLOCK_NUM`-sized tables.
- **Save-version migration** must exist before the first tester distribution, or layout changes brick saves.
- **Special vars** (`0x8000`, 14) are engine-reserved; do not repurpose — use the expanded general pool or the story block instead.

## 6. M1 (state/save) task checklist
- [ ] `[build/measure]` Sum packed block sizes → slack in `0x23000` (D4.1).
- [ ] `[source]` Bump `NUM_FLAGS`, `NUM_VARS`; confirm temp/special bases untouched (D1).
- [ ] `[source]` Define `struct StoryState`, `SAVE_STORY_STATE` id, register in `gSaveChunkHeaders[]`, `SAVE_BLOCK_NUM`→43 (D2).
- [ ] `[source]` Typed API + script commands for story state (D2/§4).
- [ ] `[source]` `schemaVersion` + load-time version/migration path (D3).
- [ ] `[source]` Central `IsRouteOpen`/`IsRegionUnlocked` gate evaluator + debug invariant validator (§4).
- [ ] `[coordinate]` Confirm dex-array growth budget with the dex-expansion half (D5).
