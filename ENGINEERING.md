# Pokemon Apocrypha — Engineering Reality

> Companion to `DESIGN.md`. Where DESIGN.md is the source of truth for *what the game is*, this document is the source of truth for *what it takes to build it*. It records engineering scope, build tasks, and technical constraints assessed against the actual toolchain.
>
> **When to consult this document:** any implementation, porting, build-system, engine-modification, asset-pipeline, or feasibility work — anything that touches how the game is made rather than what it contains. For creative and narrative decisions (story, characters, world, gyms, tone), DESIGN.md remains authoritative. When a design decision has engineering cost, note it here; do not relitigate the design there.

---

## Toolchain

- **Base engine**: pokeheartgold decomposition project (Gen-4 Nintendo DS, ARM9, C).
- **Vendored submodules** (`.gitmodules`): pokeheartgold, pokeplatinum, pokeemerald, pokefirered.
- **Not vendored**: any Gen-5 (Black/White, Black 2/White 2) decomp. None suitable exists — see Region Sourcing, Unova.

> **Verification status.** The submodules are declared in `.gitmodules` but **not yet checked out**, and there is no build scaffold. Claims in this document about engine internals (memory budgets, hardcoded caps, save layout, table sizes) are drawn from general knowledge of these games, not from inspecting the vendored source. Treat them as hypotheses to confirm once the HGSS submodule is initialized and building. Region sourcing, mechanic approach, and dex breadth below are confirmed design decisions.

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

3. **Raising the engine's single-region hardcoded limits.** The Gen-4 engine assumes one region. The National Dex cap (~493), the fly/town-map/region-map system, the map-matrix and header tables, the Pokegear map UI, and the ARM9 overlay budget against 4 MB main RAM are all expected to encode that assumption. A five-region world would break these limits and require low-level engine work distinct from content authoring. *(To verify: these specifics are drawn from general Gen-4 engine knowledge, not from this repo — the pokeheartgold submodule is not yet checked out. Confirm each limit against the actual source before planning around it.)*

4. **A nonlinear, cross-regional progression state machine.** "Gated between regions, flexible within them," routes that open and close on story events, five cross-regional threads that hint in multiple regions but climax in one, Silver appearing everywhere, and the B2W2 timeline retconned to run concurrently (the player always arrives after events resolved — "one step behind"). This demands a purpose-built quest-stage architecture over the engine's script system, kept soft-lock-proof across a partly player-chosen region order.

5. **Level curve, balance, and the solo-dev content and testing pipeline.** A meaningful difficulty ramp across twenty badges and five regions, constrained by the region-native roster rule and region-locked early dex, tuned so no region trivializes a later one across a branching order (DESIGN.md Open Question 13). Wrapped around it: heavier DS asset authoring (maps, animated sprites, NARC-packed scripts) and a combinatorial testing surface (every region-entry order x within-region gym order) that will need automated battle simulation rather than manual playtesting.
