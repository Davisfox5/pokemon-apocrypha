# Asset Sources — Overworld Sprites & Map Data

> Research findings for *Pokemon Apocrypha*. Companion to `DESIGN.md` and `ENGINEERING.md`.
> Compiled 2026-07-05. Links verified live at time of writing.
>
> **Scope.** This catalogs *where to obtain* overworld sprites and map data for the
> five regions. The *rationale* for how each region is sourced (native / ported /
> extracted) lives in `ENGINEERING.md` §Region Sourcing — this document does not
> relitigate it, it lists the concrete repos, asset banks, and formats.

## Engine premise (corrected)

The engine is **`pret/pokeheartgold` — the Gen-4 Nintendo DS decompilation** (ARM9,
C), **not** a Gen-3 GBA base. This changes everything about assets versus a GBA
project:

- Maps are **NARC-packed** DS data (map matrix, headers, 3D `nsbmd` map models,
  collision/permission `bin`), not GBA `.blk`/metatile tilesets.
- Overworld sprites are **BTX spritesheets inside `a/0/8/1` (`mmodel.narc`)**,
  indexed by a table in Overlay 1 — not GBA object-event PNGs.
- RMXP/Essentials sprite packs and pokeemerald-expansion forks (what a GBA project
  would use) **do not apply** and are excluded here.

Consequently the highest-value sources are the **pret Gen-4 decomps themselves**:
each already contains its region's maps *and* native overworld sprites in exactly
the target format.

---

## Map data

| Region | Repo / source | Format & nature of work | In repo? |
|---|---|---|---|
| **Johto** | [`pret/pokeheartgold`](https://github.com/pret/pokeheartgold) | Native HGSS NARC map data. No porting. | ✅ submodule |
| **Kanto** | `pret/pokeheartgold` (native HGSS Kanto) + [`pret/pokefirered`](https://github.com/pret/pokefirered) (reference/assets) | Native DS base; FRLG as Gen-3 reference to flesh out. | ✅ both submodules |
| **Sinnoh** | [`pret/pokeplatinum`](https://github.com/pret/pokeplatinum) | Same-gen DS. Reconcile Platinum ↔ HGSS forks into one ROM. **Note:** pokeplatinum is WIP; where extracted map/graphic data is incomplete, [`pret/pokediamond`](https://github.com/pret/pokediamond) (D/P, more mature) is a supplementary bank for the same Sinnoh assets. | ✅ pokeplatinum submodule; pokediamond not vendored |
| **Hoenn** | [`pret/pokeemerald`](https://github.com/pret/pokeemerald) | Cross-gen. Gen-3 GBA block/collision/tileset → DS NARC/`nsbmd`. Conversion, not authoring. | ✅ submodule |
| **Unova** | Retail **B2W2 ROM** (direct extraction) | No decomp exists (see `ENGINEERING.md`). Extract with DS map tools, convert Gen-5 NitroSystem → Gen-4 (HGSS) format. | ❌ no source repo |

The four native/near-native regions (Johto, Kanto, Sinnoh, Hoenn) have their map
data available as source; the real map work concentrates in the **Hoenn Gen-3→4
conversion** and the **Unova extract-and-convert**, per `ENGINEERING.md`.

---

## Overworld sprites

### How they're stored (Gen 4)

- **NARC**: HGSS → `a/0/8/1`; DPPt → `mmodel/mmodel.narc`. Contains the overworld
  character BTX spritesheets (`mmodel` = "map model").
- **Format**: BTX, **≤16 colours, background indexed to palette slot 0**. NPCs are
  typically 32×32 with 16 frames; large sprites (legendaries) 64×64/128×64 with
  fewer frames.
- **Property table**: HGSS → single 12-byte-entry table at **`0x21BA8` in
  (uncompressed) Overlay 1**; Platinum → two tables at **`0x2BC34`** and
  **`0x2CA08` in Overlay 5** (frame count + dimensions). Any sprite whose size
  differs from the one it replaces requires editing this table.

*(Source: [DS Pokémon Hacking — Overworld Sprite Replacement Guide](https://ds-pokemon-hacking.github.io/docs/generation-iv/guides/overworld_sprites/). Reference NARC maps: [NARC_List gist](https://gist.github.com/PlatinumMaster/9a12681f6c001a052444b21a27eb9f11), [HGSS NARC table](https://hirotdk.neocities.org/NARCTableHGSS.txt).)*

### Where to get them

| Source | What it provides | Notes |
|---|---|---|
| **`pret/pokeheartgold`** (`a/0/8/1`) | Every native Johto + Kanto NPC, trainer, and player overworld, already in target BTX format. | The primary, zero-conversion source. Extract with Tinke. |
| **`pret/pokeplatinum`** / **`pret/pokediamond`** (`mmodel.narc`) | Native Sinnoh NPC/trainer overworlds (Galactic, gym leaders, civilians) in DS format. | Same generation → drop-in after per-region property-table entry. |
| [**Spriters Resource — HGSS**](https://www.spriters-resource.com/ds_dsi/pokemonheartgoldsoulsilver/) | Ripped HGSS overworlds/trainers as PNG spritesheets. | For reference or re-import; DS-native proportions already correct. |
| [**Spriters Resource — DPPt**](https://www.spriters-resource.com/ds_dsi/pokemondiamondpearl/) | Sinnoh overworld rips. | Same. |
| [**Spriters Resource — B2W2**](https://www.spriters-resource.com/ds_dsi/pokemonblack2white2/) — [Overworld Entities](https://www.spriters-resource.com/ds_dsi/pokemonblack2white2/asset/48049/) | **Unova NPC/character overworlds** (and [BW](https://www.spriters-resource.com/ds_dsi/pokemonblackwhite/)). | Primary Unova overworld bank. Gen-5 style; re-index to ≤16 colours + convert to BTX for the Gen-4 engine. |
| [**Project Pokémon — HGSS Overworld Sprites**](https://projectpokemon.org/home/docs/gen-4/hgss-overworld-sprites-r33/) & [**HGSS Event Overworlds**](https://projectpokemon.org/home/docs/gen-4/hgss-event-overworlds-r15/) | Character-code–labelled HGSS overworld dumps. | Best for identifying *which* BTX index a specific NPC/trainer is. |

**Practical takeaway:** Johto/Kanto (HGSS) and Sinnoh (Plat/DP) overworlds need
**no restyling** — pull them straight from the decomp NARCs. Only **Unova** needs
sprite conversion (Gen-5 rip → ≤16-colour BTX), matching the map-side Unova work.
Any *new* characters not in canon (e.g. Mel, the Apocrypha-specific NPCs) need
original 32×32/16-frame BTX sheets authored to the same spec.

---

## Tools (DS / Gen-4 pipeline)

| Tool | Use | Link |
|---|---|---|
| **DSPRE** (DS Pokémon ROM Editor) | Maps (3D view, collision, permissions, building placement, DAE/GLB import/export), events, overworld sprite rendering + property editing, scripts, encounters, trainers. Supports D/P/Pt/HG/SS. **AGPL-3.0**, open source. | [DS-Pokemon-Rom-Editor/DSPRE](https://github.com/DS-Pokemon-Rom-Editor/DSPRE) |
| **Pokémon DS Map Studio (PDSMS)** | Author *new* DS maps from scratch (used alongside SDSME). | [ProjectPokemon file](https://projectpokemon.org/home/files/file/4237-pokemon-ds-map-studio/) |
| **SDSME** (Spiky's DS Map Editor) | Map header/matrix/event editing for Gen 4. | [ProjectPokemon file](https://projectpokemon.org/home/files/file/4237-pokemon-ds-map-studio/) |
| **Tinke 0.9.2** | Unpack NARCs; view/extract/replace BTX overworld sheets. | community tool |
| **BTX Editor 2.0** | Import a custom PNG spritesheet into BTX. | community tool |
| **HxD** | Direct hex edits to the Overlay 1 / Overlay 5 overworld property tables. | community tool |

`ENGINEERING.md` also lists **Tinke / SDSME** and the [ds-pokemon-hacking B2W2
toolchain](https://ds-pokemon-hacking.github.io/getting-started/b2w2/) for the
Unova extraction path — same tools, applied to the retail B2W2 ROM.

---

## Per-region coverage summary

| Region | Map data | Overworld sprites | Conversion needed? |
|---|---|---|---|
| **Johto** | pokeheartgold (native) | pokeheartgold `a/0/8/1` (native) | None |
| **Kanto** | pokeheartgold + pokefirered ref | pokeheartgold `a/0/8/1` (native) | None (native HGSS Kanto) |
| **Sinnoh** | pokeplatinum (+ pokediamond fill-in) | pokeplatinum/pokediamond `mmodel.narc` | Fork reconciliation only |
| **Hoenn** | pokeemerald (Gen-3) | pokeemerald OWs (Gen-3) → BTX | **Gen-3 → Gen-4 format conversion** |
| **Unova** | B2W2 ROM extraction | Spriters Resource B2W2 / ROM rip → BTX | **Gen-5 → Gen-4 extract + convert** |

Effort concentrates exactly where `ENGINEERING.md` predicts: **Hoenn** (cross-gen
conversion) and **Unova** (no source repo — extract and convert both maps and
sprites). The other three regions are drop-in from decomp NARCs.

---

## Licensing & attribution

Every source here reuses Nintendo/Game Freak copyrighted assets — the whole
ecosystem (this project included) is legally gray and strictly non-commercial. The
*tools* are the exception and carry real licenses (DSPRE is AGPL-3.0). In practice:

- **pret decomps**: reuse per community norm; credit pret and the specific decomp.
- **Ripped sprite banks** (Spriters Resource, Project Pokémon): credit the ripper
  listed on each asset page.
- Maintain a running `CREDITS.md`; add each source as it's pulled in.

---

## Recommended next actions

1. **Extract the native overworld banks now** (no build needed): pull `a/0/8/1`
   from pokeheartgold and `mmodel.narc` from pokeplatinum/pokediamond with Tinke,
   and inventory which BTX index maps to which named character (use the Project
   Pokémon labelled dumps). This is [source]-tier work that can proceed before M0.
2. **Confirm pokeplatinum's extracted-data completeness** for Sinnoh maps/OWs; if
   thin (WIP), plan to draw the same assets from pokediamond.
3. **Scope the Unova sprite conversion** alongside the map extraction: Spriters
   Resource B2W2 sheets → ≤16-colour re-index → BTX, plus the Overlay property-table
   entries.
4. **Spec the Hoenn OW conversion** (Gen-3 object-event → BTX) as part of the
   broader Gen-3→Gen-4 Hoenn port.
5. **Author original BTX sheets** for Apocrypha-only NPCs (Mel et al.) to the
   32×32 / 16-frame / ≤16-colour spec.
6. Start `CREDITS.md`.
