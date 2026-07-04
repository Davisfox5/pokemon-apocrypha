# Asset Sources — Overworld Sprites & Map Data

> Research findings for *Pokemon Apocrypha*. Companion to `DESIGN.md`.
> Compiled 2026-07-04. All links verified live at time of writing.

The design mandate is: **solo dev, all assets reuse existing community resources**
(`DESIGN.md` §Technical Foundation). The engine is **pokeemerald** (Gen 3 GBA
decomp), and the world spans **Johto, Kanto, Hoenn, Sinnoh, Unova**. Of those,
only Hoenn (native) and Kanto (via pokefirered) exist as clean Gen 3 decomp map
data. Johto, Sinnoh, and Unova must be sourced from community ports or built from
ripped assets. This document catalogs where to get both the **map data**
(tilesets + metatiles + `.blk` layouts + map JSON) and the **overworld sprites**
(player, NPC, and follower object events).

## Reuse strategy — two paths

1. **Fork whole regions.** Several community projects have already ported entire
   regions into the Gen 3 decomp format (map JSON, `.blk` layouts, tilesets, and
   matching overworlds). These are the highest-leverage sources: the map data is
   already in the exact format porymap and pokeemerald consume. Pull the
   `data/maps/`, `data/layouts/`, and `data/tilesets/` trees plus the relevant
   `graphics/object_events/` sprites.
2. **Assemble from asset banks.** For anything not already ported (notably
   **Unova**), pull raw sprites/tiles from the ripping communities and convert to
   the GBA indexed-PNG format the decomp expects.

---

## Tier 1 — Full region ports (drop-in map data + tilesets + overworlds)

These are open-source Gen 3 decomp projects whose map trees can be adapted
directly. This is the fastest route to Johto and Sinnoh.

| Project | Repo | Covers | Base | Notes |
|---|---|---|---|---|
| **Pokémon Heart & Soul** | [`PokemonHnS-Development/pokemonHnS`](https://github.com/PokemonHnS-Development/pokemonHnS) | **Johto** + Kanto postgame | Modern Emerald (pokeemerald fork) | Completed, playtested GSC/HGSS demake. Explicitly open-source and pitched as "a base for a new generation of Johto rom hacks." Includes full Johto map data, `johto`/`johto_modern` tilesets, and matching overworlds. **The single best Johto source.** A pokeemerald-expansion port ("HnS 2.0") is in progress. |
| **pokeemerald-platinum** | [`sinnoh-remakes/pokeemerald-platinum`](https://github.com/sinnoh-remakes/pokeemerald-platinum) | **Sinnoh** | pokeemerald-expansion | Active Platinum demake (last updated 2026-07-04). Full Sinnoh maps + tilesets in Platinum's graphic style, already in expansion format — matches our likely base closely. **Best Sinnoh source.** |
| **Sinnoh-pokeemerald-expansion** | [`LiderMorti00/Sinnoh-pokeemerald-expansion`](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion) | **Sinnoh** | pokeemerald-expansion | Alternate Sinnoh map base built on expansion, intended explicitly as a reusable base for Sinnoh games. Cross-check against pokeemerald-platinum and take the cleaner tileset set. |
| **Pokémon Crossroads** | [`eonlynx/pokecrossroads`](https://github.com/eonlynx/pokecrossroads) | Kanto, **Johto** (WIP), Hoenn, Sevii | pokeemerald-expansion | Multi-region hack demonstrating Kanto+Johto+Hoenn stitched into one expansion ROM — a working reference for exactly the multi-region seam-stitching this project needs, even if we don't lift its maps wholesale. |

### Foundation decomps (already vendored as submodules)

Already present under `disasm/` — these are the canonical, cleanest map/overworld
sources for their native regions:

- [`pret/pokeemerald`](https://github.com/pret/pokeemerald) — **Hoenn** maps,
  tilesets, and the full overworld object-event system (our engine base).
- [`pret/pokefirered`](https://github.com/pret/pokefirered) — **Kanto** + Sevii
  map data and Gen-3 Kanto tilesets; portable into pokeemerald with tileset
  remapping.
- [`pret/pokeheartgold`](https://github.com/pret/pokeheartgold) — **Johto/Kanto**
  reference (Gen 4 DS format; not drop-in, but authoritative for map layout,
  connections, and warp data when adapting).
- [`pret/pokeplatinum`](https://github.com/pret/pokeplatinum) — **Sinnoh**
  reference (Gen 4 DS; layout/data reference, not drop-in).

The two DS decomps are structural references (room layouts, event scripts, warp
tables), not GBA-format assets — pair them with the Tier 1 GBA ports above when
adapting.

---

## Tier 2 — Overworld sprite libraries (Gen-3 / GBA ready)

For the large NPC cast (gym leaders, Elite Four, Rockets, Silph staff, Mel, etc.)
plus the player, these give object-event sprites in or near the decomp's expected
16-color indexed format.

| Source | Where | What it gives |
|---|---|---|
| **rh-hideout/pokeemerald-expansion** | [`rh-hideout/pokeemerald-expansion`](https://github.com/rh-hideout/pokeemerald-expansion) | The overworld *system*, not just art: follower-Pokémon overworlds for all species, gender-difference OW support, substitute OW fallback, and large-OW (48×48/64×64) rendering under bridges. Strongly consider building the whole hack on this base. Credit line: "RHH (Rom Hacking Hideout)". |
| **Dynamic Overworld Palettes (DOWP)** | [`cornixsenex/rhh-dowp`](https://github.com/cornixsenex/rhh-dowp) | Dynamic OW palette allocation merged into expansion — lets many distinctly-colored NPC overworlds coexist past the vanilla palette-slot limit. Essential for a five-region cast. |
| **The DS Style Project** (CompuMax) | [Whack-a-Hack thread](https://whackahack.com/foro/threads/gba-the-ds-style-project-update-08-01-19-ow-pokemon-hg-ss.46299/) | HGSS/DPPt overworlds **already extracted and indexed for GBA insertion** (normal + shiny). The most decomp-ready DS-style OW set. Credit: CompuMax (requested, not required). |
| **Playable Character Community Project** | [PokéCommunity thread](https://www.pokecommunity.com/threads/playable-character-community-project.414973/) | Native **Gen 3-style** overworlds for playable characters and NPCs across the series — no restyling needed to match Emerald. |
| **HGSS Overworlds in FR/Emerald style** | [PokéCommunity thread](https://www.pokecommunity.com/threads/hgss-overworld-sprite-in-fr-style.408123/) | Community effort restyling HGSS OWs to GBA (FR/Emerald) palettes and proportions. |

---

## Tier 3 — Raw sprite / tile banks (need conversion)

Comprehensive but in DS-native or RMXP/Essentials format — must be re-indexed,
re-palettized, and re-framed for the GBA object-event format. Use these to fill
gaps the Tier 2 sets miss (specific gym leaders, Unova NPCs, region tiles).

| Source | Where | Notes |
|---|---|---|
| **The Spriters Resource — HGSS** | [spriters-resource.com](https://www.spriters-resource.com/ds_dsi/pokemonheartgoldsoulsilver/) | Canonical rips of HGSS trainers, NPCs, and overworlds (also has DPPt and B/W sections for Sinnoh/Unova). Raw PNGs. |
| **Project Pokémon — HGSS Overworld Sprites** | [projectpokemon.org](https://projectpokemon.org/home/docs/gen-4/hgss-overworld-sprites-r33/) | Character-code-labeled HGSS overworld dump; useful for identifying specific NPC/trainer sprites. |
| **Eevee Expo — "ALL Official Gen 4 Overworld Sprites"** | [eeveeexpo.com/resources/404](https://eeveeexpo.com/resources/404/) | Every trainer + non-trainer NPC OW from HGSS **and DPPt** (covers Sinnoh characters). RMXP-aligned — needs GBA conversion. |
| **Eevee Expo — "ULTIMATE Gen 4 Overworlds Pack"** | [eeveeexpo.com/resources/609](https://eeveeexpo.com/resources/609/) | 200+ DPPt/HGSS human OWs, full protagonist animations, tiles, autotiles, effects. RMXP format; do-not-redistribute (credit PurpleZaffre). |
| **Pokencyclopedia — Overworlds** | [pokencyclopedia.info](https://www.pokencyclopedia.info/en/index.php?id=sprites/overworlds) | Cross-gen overworld reference/index for locating specific sprites. |

For **B/W (Unova)** sprites and tiles specifically, the Spriters Resource B/W
sections are the primary bank — see Gap Analysis below.

---

## Tools (asset pipeline)

- [`huderlem/porymap`](https://github.com/huderlem/porymap) — map + tileset +
  region-map editor for pokeemerald/firered/ruby. Primary map-editing tool.
- [`grunt-lucas/porytiles`](https://github.com/grunt-lucas/porytiles) — compiles
  RGBA/indexed tile art into `metatiles.bin`, `metatile_attributes.bin`, indexed
  `tiles.png`, palettes, and anim folders. Key for importing new region tilesets.
- [`Rangi42/tilemap-studio`](https://github.com/Rangi42/tilemap-studio) — GB/GBC/
  GBA/DS tilemap + town-map editor; good for region-map/town-map art.

---

## Region-by-region coverage

| Region | Map data source | Overworld sprites | Status |
|---|---|---|---|
| **Johto** | Heart & Soul (`pokemonHnS`) — full port | Heart & Soul OWs + DS Style Project | ✅ Strong — fork Heart & Soul's map tree |
| **Kanto** | `pret/pokefirered` (native Gen 3) + Heart & Soul postgame | FR/LG OWs (native) + DS Style Project | ✅ Strong — native decomp assets |
| **Hoenn** | `pret/pokeemerald` (native) | Native Emerald OWs | ✅ Native to engine |
| **Sinnoh** | `sinnoh-remakes/pokeemerald-platinum` + `LiderMorti00` port | pokeemerald-platinum OWs + Eevee Expo DPPt / DS Style | ✅ Strong — two ports to compare |
| **Unova** | ⚠️ No known GBA/decomp port | Spriters Resource B/W + Eevee Expo (needs conversion) | ⚠️ **Gap** — see below |

### Gap analysis — Unova

No public project ports **Unova (Black/White)** map data into a Gen 3 decomp; the
searches returned only tools, not a B/W map port. Unova will require the most
original work:

- **Tilesets**: rip B/W tiles from The Spriters Resource and compile with
  porytiles, or commission/adapt community B/W GBA tilesets.
- **Map layouts**: rebuild in porymap using `pret/pokeblack`/B2W2 decomp or in-game
  maps as layout reference (DESIGN.md already trims Unova to a 4-recognized-gym
  structure, reducing scope).
- **Overworlds**: Spriters Resource B/W + Eevee Expo Gen 5 packs, converted to GBA.

Recommend confirming a Unova asset plan early, since it is the only region without
a ready-made map source. (Worth a follow-up search: a `pret/pokeblack` or
`pokeblack2` decomp and any newer 2025–2026 Unova-in-Emerald WIP, which move fast.)

---

## Licensing & attribution reality

None of these carry a permissive OSS license in the legal sense — every one
reuses Nintendo/Game Freak copyrighted assets, so the entire ecosystem (including
this romhack) is legally gray and non-commercial by necessity. In practice the
community operates on **credit norms**, not licenses:

- **pokeemerald-expansion / expansion-based ports**: credit "RHH (Rom Hacking
  Hideout)" plus the project's `CREDITS.md` contributors, ideally with a version
  number.
- **Heart & Soul**: open-source, fork-encouraged; credit the project and its
  listed contributors.
- **Sprite packs**: honor each pack's stated terms — e.g. DS Style Project (credit
  CompuMax, optional), Eevee Expo ULTIMATE pack (credit PurpleZaffre, **do not
  redistribute** the pack itself).

Maintain a running `CREDITS.md` from day one; every asset pulled in should add its
source there.

---

## Recommended next actions

1. **Decide the base**: adopt `rh-hideout/pokeemerald-expansion` (aligns with the
   Sinnoh ports and DOWP; gets follower/gender OW systems for free).
2. **Johto**: fork the Heart & Soul map + tileset + OW trees.
3. **Sinnoh**: pull from `pokeemerald-platinum`; keep `LiderMorti00`'s as a
   fallback/comparison.
4. **Kanto**: port `pokefirered` maps/tilesets into the expansion base.
5. **Overworld cast**: layer DS Style Project + Playable Character Community
   Project over the expansion's OW system; use DOWP to survive the palette budget.
6. **Unova**: scope a from-scratch tileset + porymap layout plan; search again for a
   fresh Unova-in-Emerald WIP before committing to full manual work.
7. Start `CREDITS.md` now.
