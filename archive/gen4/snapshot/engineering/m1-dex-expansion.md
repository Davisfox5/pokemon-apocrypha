# M1 — Dex Expansion

> Milestone M1 (foundational), dex half. Design-level; authorable now (most work is `[source]`/`[asset]`, only fit-measurement needs a build). Grounded in the checked-out `pokeheartgold @ b843c93` source. Companion to [`m1-state-save-architecture.md`](m1-state-save-architecture.md) and `../ENGINEERING.md`.

## 1. Scope — what's actually being added

Per the confirmed dex-breadth decision (`../DESIGN.md`, Pokedex section): obtainable roster ≈ **Gen 1–5 + select cross-region picks**, *not* a full National Dex.

- **Vanilla HGSS already covers Gen 1–4** (national #1–493). Most design "picks" are already in range: Roserade (#407), Azumarill, Granbull, Clefable, Gardevoir, Mawile, Togekiss, Whimsicott — all ≤493, **already present**.
- **New real species to add:**
  - **Gen 5** — national #494–649 = **156 species**.
  - **Post-Gen-5 picks** — currently just **Sylveon** (Valerie's ace). Small, growable set.
- **Forms** (not dex numbers): Gen-5 alternate forms (Therian, Kyurem fusions, etc.) and later the **Mega forms** (M4) occupy internal "form" slots above the last real species — same mechanism as the existing 496–507 form block.

Net: raise the real-species cap by **~157** and add a forms/sentinel region above it.

## 2. Verified baseline

| Aspect | Fact | Source |
|--------|------|--------|
| Enum top | #493 = `SPECIES_ARCEUS`; `MAX_SPECIES` = `NATIONAL_DEX_COUNT` = 493 | `include/constants/species.h:506-509` |
| Sentinels/forms in the way | `SPECIES_EGG`=494, `SPECIES_BAD_EGG`=495, Deoxys/Wormadam/Giratina/Shaymin/Rotom forms 496–507; `NUM_SPECIES`=507 | `include/constants/species.h:511-526` |
| Data pipeline | Human-editable **JSON/CSV compiled to NARC** via `.mk` rules; `personal.json` has 508 keyed entries | `files/poketool/personal/` (`personal.json`, `evo.json`, `growtbl.csv`, `*.mk`) |
| Per-species tables | base stats/types/abilities (`personal`), evolutions (`evo`), growth (`growtbl`), level-up moves (`wotbl.narc`), `pms.narc`, moves+tutor (`waza/`) | `files/poketool/…` |
| Move-tutor sizing | table sized `(NUM_SPECIES - 2) * sizeof(MoveTutorLearnset)` — **follows the cap** | `src/scrcmd_move_tutor.c:238` |
| Graphics | battle sprites `pokegra/pokegra` (2-frame animated, front/back, gender, normal+shiny palettes), forms `pokegra/otherpoke`, icons `icongra/poke_icon` | `files/poketool/…` |
| Cries | SDAT sound data | `files/data/sound` |
| **National dex order** | **identity** — `Pokedex_CountNationalDexOwned` iterates `1..NATIONAL_DEX_COUNT`; no species→dexnum remap | `src/pokedex.c:534-624` |
| Johto regional dex | separate ordering, `J_NUM_SPECIES = 256`, `johtozukan.narc` | `include/constants/johto_dex.h:6` |
| Dex data/text | `files/application/zukanlist/zukan_data/*` (+ `zukan_enc_gold/silver`), species names in msgdata | `src/message_format.c`, `files/application/zukanlist/` |
| **Follower system (HGSS-specific)** | `FollowMon_GetSpriteID` bounded by `NATIONAL_DEX_COUNT`, **falls back to Bulbasaur sprite when out of range** | `src/follow_mon.c:1645` |
| Dex save storage | `Pokedex` arrays sized off `NATIONAL_DEX_COUNT` (auto-resize, ~+250 B — see state doc D5) | `include/pokedex.h` |

## 3. Design decisions

### D1 — Numbering scheme: contiguous internal IDs, relocate sentinels
Because national dex order is identity and we are explicitly **not** a full National Dex, number the additions **contiguously** rather than by canonical national number:

```
1   – 493   Gen 1–4            (unchanged)
494 – 649   Gen 5              (156, canonical national numbers)
650 – 65x   post-Gen-5 picks   (Sylveon, …; MAX_SPECIES / NATIONAL_DEX_COUNT = last pick)
65x+..      forms              (existing Deoxys/Rotom/… + new Gen-5 forms + Mega forms, relocated)
…top        SPECIES_EGG, SPECIES_BAD_EGG (relocated sentinels) ; NUM_SPECIES = top
```

- **Trade-off:** the handful of post-Gen-5 picks get a game-local dex number (e.g. Sylveon ≈ #650), not its canonical #700. Acceptable for a non-national-dex hack and avoids ~50 empty placeholder slots (#650–699) that canonical numbering would force. Gen 5 keeps its canonical #494–649.
- **Relocation:** move `SPECIES_EGG`/`SPECIES_BAD_EGG` and the 496–507 forms above the new real-species max; update `MAX_SPECIES`, `NATIONAL_DEX_COUNT`, `NUM_SPECIES`, and the `SPECIES_MANAPHY_EGG = SPECIES_BAD_EGG` alias. Grep-audit every `494`/`495`/form-id literal and every `NUM_SPECIES - 2`-style expression.

### D2 — Extend every per-species data table
All are cap-indexed; each needs entries for the new species (JSON where available, NARC otherwise):
- `personal.json` — base stats, types, abilities, catch rate, EV yields, egg groups, growth, color.
- `evo.json` — evolutions (incl. Eevee→Sylveon; Gen-5 evo methods).
- `growtbl.csv` — growth-rate assignments.
- `wotbl.narc` — level-up learnsets.
- `waza/` — move-tutor learnsets (mind the `NUM_SPECIES-2` sizing) and any move additions Gen 5 needs.
- **Audit during implementation:** egg-move table and TM/HM compatibility (in the personal/waza archives) — confirm exact files and extend.

### D3 — Graphics & audio (the real asset burden) — source from B2W2
~157 species × {animated front+back battle sprite, gender variants where they exist, normal+shiny palette, party icon, footprint, cry}. This is the largest data-layer task.
- **Synergy:** these assets (Gen-5 sprites, cries, dex text/height/weight) come from the **same B2W2 ROM we're already extracting Unova maps from** (M3/Unova). Extract species assets and Unova maps in one pass.
- **Followers deferrable:** `FollowMon_GetSpriteID` already placeholder-falls-back out of range, so new species can ship with a placeholder follower and get real overworld models later without blocking.

### D4 — Pokédex UI & regional dex
- **National dex:** identity ordering means raising `NATIONAL_DEX_COUNT` extends it for free; verify UI paging/scroll handles the larger count.
- **Regional dexes:** HGSS ships a Johto dex (`J_NUM_SPECIES=256`). Decision: keep Johto's regional dex as-is (a Johto-native subset) and rely on the **national dex** for everything else, rather than authoring five new regional dex orderings up front. Revisit if the design wants per-region dex UIs.
- `zukan_data` (+ gold/silver encounter/area variants) and species-name/category/flavor msgdata need entries for the new species.

### D5 — Forms & Mega coordination (ties to M4)
The relocated form region is where **Mega Evolution** forms will live (M4 adapts a community Mega implementation). Reserve the forms block with growth headroom so M4 slots Megas in without renumbering. Gen-5 multi-form species (Deoxys-style seen/caught form-history, note `pokedex.h`'s 4-bits-per-form scheme) may need form-history handling extended.

### D6 — Save/budget coordination
Dex array growth (~+250 B) counts against the `0x23000` slot measured in the state half (D4 there). No independent save work; just include it in the one budget measurement.

## 4. Risks & open items
- **Asset volume** is the schedule risk, not the code — 157× sprite/cry/text sets. Mitigated by B2W2 bulk extraction (D3) but still the largest data task.
- **Sentinel/form-literal audit** must be exhaustive; a missed `494`/`507`/`NUM_SPECIES-2` assumption corrupts data indexing silently.
- **Pick list may grow** — if the design adds more post-Gen-5 picks (e.g. other Eeveelutions/Fairies), they append at #651+; keep the block open.
- **National-number divergence** for picks (D1) — confirm this is acceptable to the design owner (it follows directly from the already-approved "not a full National Dex" decision, but the visible dex number changes).

## 5. Dex-expansion task checklist
- [ ] `[source]` Species enum: add Gen-5 (#494–649) + picks; relocate EGG/BAD_EGG/forms; update `MAX_SPECIES`/`NATIONAL_DEX_COUNT`/`NUM_SPECIES` (D1).
- [ ] `[source]` Grep-audit all sentinel/form-id/`NUM_SPECIES`-arithmetic sites (D1).
- [ ] `[source/asset]` Extend `personal.json`, `evo.json`, `growtbl.csv`, `wotbl.narc`, tutor/egg/TM tables (D2).
- [ ] `[asset]` Extract & install Gen-5 battle sprites, icons, palettes, footprints, cries from B2W2 (D3).
- [ ] `[source]` Add species names + `zukan_data` dex text/height/weight/category (gold/silver variants) (D4).
- [ ] `[source]` Reserve/grow the forms block for Gen-5 forms + future Megas (D5).
- [ ] `[build/measure]` Include dex-array growth in the single `0x23000` slot-fit measurement (D6, shared with state half).
- [ ] `[decide]` Confirm game-local dex numbering for post-Gen-5 picks with the design owner (D1/§4).
