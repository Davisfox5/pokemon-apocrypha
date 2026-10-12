# Pokémon Apocrypha — Hoenn Item Locations

The Hoenn companion to [JOHTO_ITEMS.md](JOHTO_ITEMS.md) / [KANTO_ITEMS.md](KANTO_ITEMS.md):
item & hidden-item locations and Mart stock for the Hoenn chapters. Hoenn begins at
**Slateport City (Chapter 8)**.

> Detail split (see [[apocrypha-doc-taxonomy]]):
> - this file — Hoenn items + marts
> - [HOENN_BATTLES.md](HOENN_BATTLES.md) — Hoenn encounters + trainers
> - per-chapter docs (`CHAPTER<N>_BUILD.md` / `CHAPTER<N>_SCENES_SPEC.md`) — staging + dialogue

> **⚑ Cross-region source.** Hoenn maps/marts don't exist in the HGSS engine — everything here
> is **referenced from pokeemerald** (`disasm/pokeemerald/`) and **rebuilt as native HGSS
> data.** Item *constants* are HGSS-side; where an item is Hoenn-flavored (berries, specialty
> balls) confirm the HGSS item table has it (HGSS carries the full item list). New custom key
> items (the collection-quest artifacts) get new HGSS item constants. See [[apocrypha-cross-region-maps]].

**Economy note:** the player reaches Hoenn **three regions deep, 2 badges**, off a Champion's
boat. Slateport is the **biggest, most varied market yet** — the original that Celadon's
market (Ch6) was modeled after — but Apocrypha keeps *purchasable power* on the whole-game
leash: variety and services grow, but nukes/endgame stock stay gated by badge count (the same
discipline as the Goldenrod Department Store and the Kanto marts). Vanilla Hoenn Slateport is
*early-game*, so its stock is modest — Apocrypha **lifts the variety a little** to match the
player's tier (the inverse of trimming Kanto's endgame marts), without handing out power.

---

## Chapter 8 — Slateport City · Route 110 (south) · Route 109 (beach)

Grounded in the pokeemerald reference maps (rebuilt in HGSS): `SlateportCity` + interiors
(`_OceanicMuseum_1F/2F`, `_Mart`, `_PokemonCenter`, `_Harbor`, market stall objects),
`Route110`, `Route109` + `Route109_SeashoreHouse`. Chapter 8's item story is **a market that
opens up** (the Mauville rescue unlock) and **a quest that never closes** (Stern's five-region
collection). Loot is otherwise light — the chapter's payload is a new region and three seeds.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| **Mauville specialty stalls** (permanent stock) | Slateport Market | Reward for the **Route 110 vendor rescue** (`FLAG_APOC_CH8_VENDORS_RESCUED`). The empty stalls open for good with Mauville goods not sold elsewhere on the coast. Permanent inventory unlock, not a one-shot item (details below) |
| **Collection-quest artifacts** (×5 key items) | **Not obtainable in Ch8** | Captain Stern's five-region quest (`FLAG_APOC_CH8_STERN_QUEST`). Custom key items, one per region's great maritime/subterranean site; all require later-game access (Surf/Dive/reaching those regions). Design + rewards below |
| **Scott's card** | Slateport (Scott cameo) | Flavor/seed, **not a bag item** (or a valueless "Frontier Card" key item if a tangible token is wanted). Plants the Battle Frontier for the late/post-game; explains nothing |

### The Slateport Market (regulars)

Vendor **objects on the `SlateportCity` map** (not a separate interior), re-lined from the
vanilla stalls. Keep purchasable power badge-2/3-tier:

| Stall | Vanilla source | Stock (Apocrypha) |
|-------|----------------|-------------------|
| **Energy Guru** (held/vitamin vendor) | `EnergyGuru` | The bitter cheap-heal line (Energy Powder, Energy Root, Heal Powder, Revival Herb) + **vitamins** (Protein/Iron/Calcium/…) at real prices. Vitamins are money-gated — fine as a *sink*, not a spike |
| **TM stall** (utility/light-coverage only) | `PowerTMClerk` | A small rotating TM counter — **utility & light coverage ONLY** (e.g., Return, Rock Tomb, Bullet Seed, Fury Cutter-tier), **NOT** the nukes. Same rule as the Goldenrod badge-1 rack: coverage/big-BP TMs stay gated by badge count |
| **Berry stall** | (market berries) | Assorted berries — held pinch/status berries (Sitrus, Lum, Oran, Pecha…) and cooking/Pokéblock stock if that system is in. Curve-safe held-item economy |
| **Decor / Doll stalls** | `DecorClerk` / `DollClerk` | Flavor (Secret Base decor / dolls). Keep as cosmetic/optional; no power. Cut if Secret Bases aren't in Apocrypha |

### The Mauville unlock (permanent, post-rescue)

The rescued vendors' stalls open with **Mauville specialty stock** — the mechanical reward for
Route 110. "Specialty, not power": variety the player can't get on the coast, all curve-safe:

| Category | Recommended stock | Notes |
|----------|-------------------|-------|
| Specialty ball | **Nest Ball** (or Timer Ball) | Utility ball unavailable at the regular Mart; catching flavor, not power |
| Rare berries | A couple of **held pinch/status berries** (Sitrus/Lum/Persim) | Curve-safe held-item access |
| Held item | One modest **type-boost or utility held item** (e.g., Magnet / Cell Battery / an X-item bundle) | Modest; foreshadows Mauville's Electric identity without a spike |
| Mauville TM | One **Electric-flavored utility TM** (e.g., **Shock Wave** — never-miss, low-BP, or Charge Beam) | A taste of the Mauville/power-corridor region; utility-tier, gated below the nukes |

> **Keep it "specialty, not power."** The unlock's value is *variety and a permanent reason to
> return to Slateport's market*, mirroring Ch8's rescued-vendors payoff. Price it as a choice,
> not a default; nothing here should outclass a badge-3 team's earned kit.

### The Oceanic Museum — Captain Stern's collection quest (whole-game)

The chapter's headline is a **quest that spans the entire game.** Stern wants **one relic from
each region's greatest maritime/subterranean site.** All five are **custom key items** (new HGSS
constants), tracked by **`VAR_APOC_STERN_ARTIFACTS`** (a 5-bit mask). **None are obtainable in
Chapter 8** — each site needs later-game access. Item flavor: *"An ancient relic recovered from
[site]. Looks like it belongs in a museum."*

| Artifact (working name) | Region | Site (access gate) | Return reward (individual) |
|-------------------------|--------|--------------------|-----------------------------|
| **Whirl Relic** | Johto | Whirl Islands (Surf/Whirlpool) | A rare held item or a Water/ocean-themed TM (dial) |
| **Seafoam Relic** | Kanto | Seafoam Islands (Surf/Strength) | A rare held item or an Ice-themed TM (dial) |
| **Trench Relic** | Hoenn | Undersea Cave / underwater routes (Dive) | A rare held item or a unique deep-sea item (dial) |
| **Iron Relic** | Sinnoh | Iron Island (region access) | A rare held item or an evolution/mineral item (dial) |
| **Abyssal Relic** | Unova | Abyssal Ruins / Relic Temple (region + Dive) | A rare held item or a unique inscription item (dial) |

- **Payoff shape = hybrid: small per-turn-in + a big capstone** (user call). Each relic pays out
  *and* the full set pays out; the individual rewards stay **modest**, the capstone is **major**.
- **Each artifact returns to Stern individually** for a **modest, curve-safe** reward (a rare held
  item, a single TM, or a unique flavor item — never a power spike) — pick per-region at build,
  tuned for *when* the player can actually reach that site.
- **Full set = a capstone that is BOTH mechanical AND narrative:**
  - *Mechanical:* a genuine one-of-a-kind reward — lead candidate a **relic-tied rare-Pokémon
    gift** (a deep-time / fossil-adjacent species fitting Stern's oceanography), with a **signature
    held item**, an **exclusive move tutor**, or a **one-off TM** as alternates. This is a *committed
    capstone slot* (no longer "TBD"); only the exact item is tunable at build.
  - *Narrative:* assembling the five relics **charts the deep-time migration routes** — the same
    ancient Inter-Regional Exchange the Ch7 Claw Fossil hinted at (see [KANTO_ITEMS.md](KANTO_ITEMS.md)
    §Ch7). Stern realizes the relic sites **overlap the undersea legendary-research sites** the
    Silph/Rocket coalition is quietly surveying (DESIGN, "Undersea Legendary Research") — so the
    player's innocent archaeology has been charting exactly what Apex/Rocket want. The wholesome
    collection quest **turns into a live thread of the conspiracy** in the endgame. That reframe is
    the payoff that justifies a whole-game hunt.
- **Ch8's job is only to PLANT it.** The player leaves Slateport knowing Stern wants relics, and
  every maritime cave / sunken ruin for the rest of the game now carries a Stern-shaped itch. Do
  not place any artifact in Ch8.

### Marts

**Slateport Mart (`SlateportCity_Mart`)** — a big-market Mart kept **badge-2/3-tier**:
Poké Ball, Great Ball, Super Potion, Antidote, Paralyze Heal, Burn Heal, Awakening, Full Heal,
Repel, Super Repel, Escape Rope, a few X-items. A **notch more variety** than the Kanto marts
(the player's further along and Slateport is a big market) but **still no Ultra Balls / Hyper
Potions / Full Restores** — those stay gated to later Hoenn badges.

**Seashore House (`Route109_SeashoreHouse`)** — the beach **soda shop**: Fresh Water (₽200),
Soda Pop (₽300), Lemonade (₽350) — cheap on-the-beach HP heals, exactly as vanilla. Charming,
optional, curve-neutral.

### Field & hidden items

| Item | Location | Notes |
|------|----------|-------|
| Route 110 items | Route 110 (south) | A couple of modest field/hidden items on the rescue segment (a Super Potion, coins, maybe a berry). Keep light; north-half items are Ch9 |
| Route 109 / beach | Route 109 | Beach finds — a hidden Heart Scale in the sand, a berry, coins. Light, thematic |
| Slateport hidden | City / docks / market | A stray consumable or coins; a Nugget-tier find is fine (big port), kept sparse |

### Reward pacing notes

- **The market unlock is the mechanical reward, and it's a *place*, not a payout.** Like
  Celadon's services (Ch6), Ch8's economy novelty is **permanent access** (the Mauville stalls),
  not a power item. It rewards the rescue and gives Slateport lasting return value. Keep the
  stock specialty/curve-safe.
- **Stern's quest is the long game.** It hands the player *nothing* now — its entire Ch8 value is
  narrative (a reason to care about every future underwater/ancient site). Resist front-loading
  it; the payoff is the whole rest of the game.
- **Loot-light, like a good tourist stop.** Slateport is dense with *life*, not treasure. The
  chapter's real gifts are a new region, a market that opens, and three quiet seeds (Stern, Scott,
  Lisia). Save Hoenn's deeper item economy for the badge chapters (the first Hoenn gym — Rustboro/Wes — onward).
- **No power for arriving.** The player crossed an ocean on a Champion's ticket — the game does
  **not** reward that with a strength spike. Hoenn's power is *earned on Hoenn's terms* (badges,
  from the first Hoenn gym on). Ch8 keeps the purchasable/gift tier honest.
