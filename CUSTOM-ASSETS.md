# Custom Community Assets — Modernized Overworld & Map Art

> Research findings for *Pokemon Apocrypha*. Companion to `ASSET-SOURCES.md`
> (which covers vanilla/decomp sources) and `ENGINEERING.md`.
> Compiled 2026-07-05. Links verified live at time of writing except where noted.

## Purpose

`ASSET-SOURCES.md` covers the **vanilla** map data and overworld sprites ripped
from the games. This document covers **custom, fan-made assets released by the
community for reuse** — the material that makes the world feel *changed*.

**Design driver:** in-fiction, **~10 years have passed** since the player was last
here. Cities have modernized, infrastructure has grown, and the returning cast has
aged. `DESIGN.md` already bakes this in — Goldenrod as a modern media metropolis,
Vermilion's expanded industrial port, Saffron reshaped by Silph's expansion,
Olivine's shipbuilding boom, Jasmine as a civic icon, Blue as a professor, Brock as
a breeder. Vanilla HGSS/DPPt tiles and sprites can't express that on their own. The
two levers that can:

1. **Custom tilesets** — modern buildings, skyscrapers, industrial ports, updated
   city layouts.
2. **Aged-up / redesigned overworld sprites** — returning characters ten years
   older, plus new NPCs.

## The format reality (read first)

This is a **Gen-4 DS (pokeheartgold)** project. Two hard truths about custom assets:

- **DS-native custom art is narrower than the GBA/decomp scene.** The main channel
  for custom DS *map* art is **Pokémon DS Map Studio** tilesets; for *overworlds*,
  HGSS-format BTX sprite packs.
- **Most "custom Pokémon" art online targets RPG Maker XP / Pokémon Essentials
  (fan games), not DS ROMs.** That art is reusable but is *source material, not
  drop-in*: it must be re-indexed to DS palette limits and rebuilt into the DS
  formats — `nsbmd`/DS Map Studio tilesets for maps, 32×32/16-frame ≤16-colour
  **BTX** sheets for overworlds (per `ASSET-SOURCES.md` §Overworld sprites). Each
  source below is tagged with its native format so the conversion cost is explicit.

**Synthesis worth noting:** the "modern metropolis" look is largely the **BW/BW2
aesthetic** (Castelia skyscrapers, Nimbasa, Driftveil industry). Since the project
is *already* extracting B2W2 for Unova (`ENGINEERING.md` §Region Sourcing), **BW/BW2
tilesets do double duty** — Unova region art *and* the vocabulary for modernizing
Johto/Kanto cities. Prioritize them.

---

## 1. Custom tilesets (map art)

| Source | Native format | What it offers for a "10-years-later" look | Terms |
|---|---|---|---|
| **Pokémon DS Map Studio** — [`Trifindo/Pokemon-DS-Map-Studio`](https://github.com/Trifindo/Pokemon-DS-Map-Studio) + [`AdAstra-LD` fork](https://github.com/AdAstra-LD/Pokemon-DS-Map-Studio) | **DS-native** (`nsbmd`) | The primary DS custom-map channel. Bundles community tilesets — HGSS, **BW & BW2** — with **BW2 tilesets credited to Brom & AdAstra**, others to **Jiboule, Nextworld, Jay**. Also imports arbitrary custom tiles. BW2 sets = ready-made modern-city vocabulary. | Credit the named tileset authors + Trifindo/AdAstra for the tool. Verify per-tileset terms in the PDSMS thread. |
| **PDSMS community thread** — [PokéCommunity](https://www.pokecommunity.com/threads/pokemon-ds-map-studio-create-pokemon-ds-maps-in-5-min-2-1-version.429563/) | DS-native | Where new community tilesets land between releases. Best place to watch for fresh modern/urban DS tilesets. | Per-post credit. *(Thread not directly fetchable — login-gated; sourced from search.)* |
| **"Gen IV & V Style Tilesets" guide** — [Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2436216636) | **RMXP** (needs conversion) | Curated index of 10 custom tileset artists incl. **Shiney570 (Black & White buildings)**, **Magiscarf**, KingLotus, Akirazu, WilsonScarloxy (indoor/outdoor), SailorVicious (Hoenn Project). Strong for modern building/interior art *as source*. | "Work of their creators" — credit each; confirm terms with each artist. RMXP→DS conversion required. |
| **ROM Hacking Sprites Pack (updated 2026)** — [PokéCommunity](https://www.pokecommunity.com/threads/rom-hacking-sprites-pack-overworlds-trainer-sprites-tilesets-and-more.527581/) | ⚠️ unverified (likely GBA-leaning) | Large shared pack: battle backgrounds, overworlds, trainer sprites, tilesets. | Credit per pack. **Verify it contains DS/Gen-4 content before relying on it — could be GBA-only.** *(Not fetchable — login-gated.)* |

**Recommendation:** build the modern-city language on **BW/BW2 DS tilesets via
PDSMS** (Brom/AdAstra), supplemented by the individual artists in the Gen IV/V guide
where a specific modern building/interior is needed (converted from RMXP). Re-dress
Goldenrod, Vermilion, Saffron, and Olivine with these rather than vanilla HGSS tiles.

---

## 2. Custom overworld sprites (aging up the cast + new NPCs)

| Source | Native format | Use for the redesign | Terms |
|---|---|---|---|
| **OW Gen 4 Trainer Sprite Creator** — [PokéCommunity](https://www.pokecommunity.com/threads/ow-gen-4-trainer-sprite-creator.416464/) | Gen-4 OW template | **Has explicit *aged* and *child* templates** — the direct tool for making "10 years older" overworlds of returning characters (Silver, Blue, Jasmine, Brock, Clair…). | Credit the creator. |
| **Playable Character Community Project** — [PokéCommunity](https://www.pokecommunity.com/threads/playable-character-community-project.414973/) | Gen-3/DS-style OW | Custom OWs for playable characters and NPCs across the series; useful base bodies to reskin/age. | Credit contributors. |
| **UD's Custom Sprite Resources** — [PokéCommunity](https://www.pokecommunity.com/threads/uds-custom-sprite-resources.397580/) | Custom sprites | Individual custom sprite sets (overworld + battle) released for reuse. | Credit UberDude. |
| **"Pokemon Overworld (HGSS Style)" showcase** — [PokéCommunity](https://www.pokecommunity.com/threads/pokemon-overworld-hgss-style.435782/) | HGSS-style OW | Community-made HGSS-proportioned custom overworlds — matches the engine's native look, minimal restyling. | Per-post credit. |
| **Eevee Expo — "ALL Official Gen 4 Overworld Sprites"** — [eeveeexpo.com/resources/404](https://eeveeexpo.com/resources/404/) | **RMXP** | Includes **custom OWs for trainers whose battle sprite didn't match** — i.e., original work beyond vanilla. Source material; convert to BTX. | Credit; RMXP→DS conversion required. |
| **DeviantArt** custom overworld collections (e.g. [SnakeMasterz favourites](https://www.deviantart.com/snakemasterz/favourites/72325550/custom-pokemon-sprites-and-overworlds)) | mixed | Scattered individual custom overworlds; case-by-case. | Per-artist terms — check each before use. |

**Recommendation:** for returning characters, generate **aged overworlds** with the
OW Gen 4 Trainer Sprite Creator (aged templates) over HGSS-style base bodies, then
convert to BTX. For wholly new NPCs (Mel, Apocrypha-specific cast), author original
BTX sheets to the same 32×32 / 16-frame / ≤16-colour spec.

---

## 3. Custom trainer / battle sprites (VS + battle screen)

| Source | Native format | Notes | Terms |
|---|---|---|---|
| **DS-Styled 64×64 Organized Trainer Sprite Resource** — [PokéCommunity](https://www.pokecommunity.com/threads/ds-styled-64x64-quality-organized-trainer-sprite-resource.285758/) | DS 64×64 16-bit | Trainers/leaders/E4 across **DP/Pt/HGSS/BW/B2W2**, organized. Good base for aged/redesigned versions of returning leaders. | **Free to use with credit.** |
| **Gen 4 & 5 Trainer sprites + PBS** — [Eevee Expo](https://eeveeexpo.com/threads/2562/) | RMXP-oriented | Companion trainer-sprite set frequently paired with the OW packs. | Credit. |

*(Battle sprites are DS-format-adjacent; the 64×64 organized resource is the closest
to drop-in for redesigning gym leaders' VS art.)*

---

## Mapping to the redesign (DESIGN.md)

| Location / character | Redesign need | Custom source to lean on |
|---|---|---|
| Goldenrod — modern media metropolis | Skyscraper/urban tileset | BW2 tilesets (Brom/AdAstra) via PDSMS |
| Vermilion — expanded industrial port | Cranes, cargo, port tiles | BW Driftveil-style / custom port tiles (Gen IV/V guide) |
| Saffron — Silph expansion | Corporate/urban tileset | BW Castelia-style tiles |
| Olivine — shipbuilding boom | Industrial/maritime tiles | BW/BW2 industrial + custom |
| Silver (Champion), Blue (prof.), Jasmine (civic), Brock (breeder), Clair | Aged-up overworlds + VS sprites | OW Gen 4 Trainer Sprite Creator (aged) + DS-Styled 64×64 resource |
| Mel & new cast | Original overworlds | Author new BTX to spec |

---

## Honest gaps & risks

- **Format tax is real.** The richest custom libraries (Eevee Expo, the Gen IV/V
  tileset guide, most DeviantArt art) are **RMXP/Essentials**, not DS. Budget for
  re-indexing + rebuilding into `nsbmd`/BTX. Genuinely DS-native custom assets are
  limited to PDSMS tilesets and HGSS-format OW packs.
- **Login-gated sources unverified.** Several PokéCommunity threads returned 403 to
  automated fetch; details above are from search snippets. **Confirm format
  (DS vs RMXP vs GBA), contents, and current terms by opening each thread manually**
  before committing to it — especially the "ROM Hacking Sprites Pack."
- **Per-asset licensing.** Unlike the tools (PDSMS is open source), custom art terms
  vary by author and are often "credit required, no redistribution." Log every asset
  and its author in `CREDITS.md` as it's pulled in.
- **The aging aesthetic is authorship, not just sourcing.** No pack ships "Johto, ten
  years later." These sources supply the *vocabulary* (modern tiles, aged templates,
  base bodies); making the world read as changed is original mapping/spriting work on
  top of them.

## Recommended next actions

1. **Pull PDSMS (Trifindo + AdAstra fork) and inventory its bundled BW/BW2 tilesets**
   — the fastest, DS-native path to a modern-city look. Confirm per-tileset credit.
2. **Trial one modernized city** (e.g. Goldenrod) with BW2 tiles to validate the
   aesthetic and the PDSMS→SDSME→ROM pipeline before scaling.
3. **Prototype aged overworlds** for 2–3 returning characters via the OW Gen 4
   Trainer Sprite Creator, convert to BTX, and confirm they read as "older."
4. **Manually vet the login-gated packs** (ROM Hacking Sprites Pack, Eevee Expo) for
   DS-usable content and terms.
5. **Start `CREDITS.md`** and add every custom asset + author on first use.
