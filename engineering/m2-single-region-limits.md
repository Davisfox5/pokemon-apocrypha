# M2 — Single-Region Limits Audit

> Milestone M2. Resolves the hypotheses in `../ENGINEERING.md` problem #3 against the checked-out `pokeheartgold @ b843c93` source. Each single-region assumption is now confirmed, refuted, or flagged for build-time measurement, with a severity and a generalization path. Mostly `[source]` findings; one item (`[build/measure]`) needs M0.

## 1. Findings summary

| # | Assumption / limit | Status | Severity | Evidence |
|---|--------------------|--------|----------|----------|
| A | Region identity is a boolean (`isKanto`) | **Confirmed** | Medium (small logic footprint, large data footprint) | `include/map_header.h:31`, `src/map_header.c:128` |
| B | `mapsec` region-map location namespace is 8-bit and nearly full | **Confirmed — hard limit** | **High** | `include/map_header.h:26`; 235/256 used (`include/constants/map_sections.h`) |
| C | Town/region map is a single 64×64 grid | **Confirmed** | Medium | `worldMapX/Y : 6` (`include/map_header.h:17-18`) |
| D | Fly/region-map UI assumes one region | **Confirmed** (coupled to B/C) | Medium | pokegear map + `worldMapX/Y` + `mapsec` |
| E | Map-header **count** is a hard cap | **Refuted** | None — good news | `sMapHeaders[]` bounded only by `NELEMS`; 540 entries; `mapId` is `u32` |
| F | Map matrix size is a global limit | **Refuted** | None | `MAP_MATRIX_MAX_SIZE = 799` is **per-matrix**, not global (`include/map_matrix.h:7`) |
| G | ARM9 overlay / 4 MB RAM working set | **Needs M0 measurement** | Unknown | 357 overlay refs; paging mechanism confirmed |

**Headline:** the engine is not "one region" so much as **exactly two** (Johto/Kanto), expressed as a 1-bit flag over a **shared, nearly-exhausted** `mapsec` namespace and a **single** town-map grid. The blocker is not map capacity (E/F refuted — the map *table* extends freely) but the **region-identity model (A)** and the **8-bit `mapsec` ceiling (B)**.

## 2. Region identity — the `isKanto` bit (A)

```c
// include/map_header.h
u32 isKanto : 1;              // per-map region flag
// src/map_header.c:128
BOOL MapHeader_IsInKanto(u32 mapId) { return sMapHeaders[mapId].isKanto; }
```

- **Behavioral footprint is small:** only a couple of logic sites actually read it (e.g. `src/scrcmd_battle.c:195` for encounter music). Generalizing the *logic* is cheap.
- **Data footprint is large but mechanical:** `.isKanto` is set on all **540** map-header entries (`src/data/map_headers.h`). A region field must be populated per map.
- **Plan:** replace `isKanto : 1` with `region : 3` (≥5 values: Johto/Kanto/Hoenn/Sinnoh/Unova), keep a `MapHeader_GetRegion(mapId)` accessor, and provide `MapHeader_IsInKanto` as a compatibility shim (`region == REGION_KANTO`) so existing call sites keep working. Region-dependent behavior (music, town map, dex scoping, story gates via M1's `StoryState.region`) switches on the new field.

## 3. The `mapsec` ceiling — the hard limit (B)

```c
u16 mapsec : 8;   // include/map_header.h:26  → 0..255
```
- `map_sections.h` defines **235** sections (`MAPSEC_MYSTERY_ZONE`=0 … `MAPSEC_CLIFF_EDGE_GATE`=234), leaving only **~21 free** in the 8-bit field.
- **Bonus finding:** because HGSS is built on the DP engine, the namespace **already contains Sinnoh sections** (Twinleaf … Snowpoint, routes 201-230) *plus* Johto + Kanto. So three of five regions' region-map sections already exist — a real head start for the Sinnoh/Platinum port.
- **But** Hoenn (~30) + Unova (~30) sections won't fit in ~21 slots. `mapsec` **must be widened past 8 bits.**
- **Plan:** widen `mapsec` to `u16 mapsec : 9` (or 10) within `MapHeader` (there is spare room in the surrounding bitfields — audit the struct packing), update every `mapsec`-typed variable/accessor (`MapHeader_GetMapSec`, region-map lookups, `MAPSEC_*` tables), then append Hoenn/Unova sections. This is the highest-severity structural change M2 surfaces because `mapsec` threads through the region-map, fly, and area-name systems.

## 4. Town/region map & fly (C, D)

- `worldMapX : 6`, `worldMapY : 6` place each map on a **single 64×64** region-map grid — one image, shared by Johto+Kanto today (the HGSS Pokégear map card).
- **Plan:** move to **per-region town-map images with a region selector**, interpreting `worldMapX/Y` relative to the map's `region` (from A). Fly destinations (start-menu/pokegear map + `field_move.c`) become a per-region table keyed on `region` + `mapsec`. This work rides on A (region field) and B (mapsec space), so sequence it after them.

## 5. What is *not* a blocker (E, F)

- **Map count:** `sMapHeaders[]` is bounded only by `NELEMS(sMapHeaders)`; `mapId` is passed as `u32`. Five regions (~5 × 540 ≈ 2,700 maps) extend the table with no engine cap to raise. (Verify only that no *other* struct narrows `mapId`/`matrixId` — `matrixId` is `u16`, giving 65 k matrices, ample.)
- **Map matrix:** `MAP_MATRIX_MAX_SIZE = 799` is a per-area cell limit, not a global one. Not a scaling blocker.

These refutations matter: they mean the multi-region problem is about **identity and namespaces**, not **capacity** — a smaller, more surgical scope than problem #3 assumed.

## 6. Overlays / RAM (G) — measure at M0

357 overlay references confirm the ARM9 overlay paging mechanism is pervasive (field, apps, battle all page into limited main RAM). Whether five regions' scripts/features strain the working set can only be measured against a built ROM (per-overlay sizes + peak residency). **Deferred to M0**; not blocking design.

## 7. Recommended M2 sequencing
1. **A — region field** (`isKanto : 1` → `region : 3` + accessor/shim). Foundational; M1's `StoryState.region` pairs with it.
2. **B — widen `mapsec`**, append Hoenn/Unova sections (Sinnoh already present).
3. **C/D — per-region town map + fly table**, keyed on the region field.
4. **G — measure overlay/RAM residency** once M0 builds.

## 8. Task checklist
- [ ] `[source]` `MapHeader.region` field + `MapHeader_GetRegion` + `IsInKanto` shim; migrate the 540 header entries (A).
- [ ] `[source]` Widen `mapsec` bitfield; audit all `mapsec`/`MAPSEC_*` consumers; append Hoenn + Unova sections (B).
- [ ] `[source]` Per-region town-map images + region selector; region-scoped fly table (C/D).
- [ ] `[verify]` Confirm no struct narrows `mapId` below the ~2,700-map need (E).
- [ ] `[build/measure]` Overlay count + peak main-RAM residency with five regions (G).
