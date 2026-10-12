# Pokémon Apocrypha — Johto Item Locations

> **Scope:** Item locations for the **Johto** chapters — gift/key items, hidden items, and notable Mart stock. One of the per-region item docs. Pairs with:
> - [DESIGN.md](../DESIGN.md) — region/map design + high-level story
> - [JOHTO_BATTLES.md](JOHTO_BATTLES.md) — wild encounters + trainer battles
> - per-chapter docs (e.g. [CHAPTER1_BUILD.md](CHAPTER1_BUILD.md)) — interactions + quests
>
> **Engine:** pokeheartgold (HGSS).

---

## Chapter 1 — Cherrygrove · Route 29 · New Bark

Grounded in the real map files: `064_T21.json` (Cherrygrove), `030_R29.json` (Route 29), `057_T20.json` (New Bark). Geography: **Cherrygrove (west) → Route 29 (east) → New Bark (east)**; Route 30 (north of Cherrygrove) leads to Violet.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| Starter Poké Ball | Gold's house, Cherrygrove | Player chooses 1 of Cyndaquil / Totodile / Chikorita (Scene 2) |
| Pokédex | Elm's Lab, New Bark | Elm gives one to the player (and narratively to Kestra) (Scene 3) |
| Running Shoes + Town Map (Map Card) | Gold's house, Cherrygrove — end of starter ceremony (Scene 2) | Reassigned from the deceased Guide-Gent — Gold hands them over grumbling (repurposes vanilla tour msgs 6–7, 10–12). Given in Scene 2 so the player can run on Route 29. |
| Poké Ball ×5 | Cherrygrove, post-catching-tutorial (Scene 4) | Gold, after the catching demo |

### Field & hidden items (already placed on the maps)

| Item | Location (x,z) | Source object / script |
|------|----------------|------------------------|
| Potion (visible ball) | Route 29 (654,386) | `obj_R29_monstarball` → `std_itemball_r29_potion` |
| Nugget (hidden) | Route 29 / Cherrygrove border (572,390) | `std_hiddenitem_r29_r30_t21_nugget` |
| Potion (hidden) | Cherrygrove, west (522,388) | `std_hiddenitem_t21_nugget` → **downgraded to Potion** (was a Nugget; see note) |
| Potion (hidden) | New Bark (682,391) | `std_hiddenitem_t20_potion` |
| Apricorn — Red (param0=5) | Route 29 tree (596,392) | `obj_R29_bonguri` → `std_apricorn_tree` |

> The confirmed "reward curiosity on Route 29" goal is **already satisfied** by the existing visible Potion ball + hidden Nugget — no new item needed. **Decision (applied, reversible):** keep the Route 29/border Nugget but **downgrade the Cherrygrove (522,388) Nugget to a Potion**, so the player stays money-poor through the opening (revisit once the broader economy is designed). The cut Cherrygrove beach hidden-item beat stays cut. The Apricorn tree is harmless flavor (Kurt's ball-craft pays off in Ch.3, Azalea).

### Marts

**Cherrygrove Mart** — early/basic stock: Poké Balls, Potions, Antidote, Paralyze Heal, escape items. The player has little money this chapter; the Mart is mostly for Poké Balls and a Potion or two before heading out.

---

## Chapter 2 — Routes 30/31 · Violet University · Sprout Tower · Union Cave

Grounded in the Chapter 2 route: Route 30 → Route 31 → Violet City / Sprout Tower → optional Ruins of Alph → Route 32 → Union Cave → Route 33. The economy should still feel small: useful medicine, a few Poke Balls, one held item lesson, one pseudo-gym TM.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| Apricorn Box | Route 30, Apricorn man's house | Keep the vanilla one-time Apricorn tutorial unless pacing changes later |
| Quick Claw | Mr. Pokemon's house, Route 30 | Held-item introduction; Mr. Pokemon explains preparation and surprise |
| Oran Berry x3 | Sprout Tower / Ren apology reward | Ren gives practical supplies after the prank is resolved |
| TM70 Flash | Sprout Tower Elder | Tower lesson reward; opens deeper Dark Cave utility later |
| TM39 Rock Tomb | Violet old gym / practice hall | Roxanne pseudo-gym practicum reward, not a badge |
| Old Rod | Route 32 fisherman | First fishing unlock on the road to Azalea |

### Field & hidden items

| Item | Location | Notes |
|------|----------|-------|
| Antidote | Route 30 visible ball | Existing ball near the main route; supports Weedle/poison pacing |
| Potion | Route 30 visible ball | Existing southern ball; early sustain |
| Potion | Route 30 hidden | Existing hidden item near Trainer Tips |
| Nugget | Route 30 / Cherrygrove border hidden | Existing curiosity reward; revisit if early money becomes too high |
| Poke Ball | Route 31 visible ball | Existing early capture support |
| Potion | Route 31 visible ball | Existing route sustain |
| Apricorns | Route 30/31 trees | White/Blk/Pnk style values can stay until Apricorn economy is tuned |
| Escape Rope | Sprout Tower 2F/3F | Teaches dungeon exit item before Union Cave |
| Paralyze Heal | Sprout Tower | Supports Bellsprout/status lesson |
| X Defend or X Accuracy | Violet city item ball | Prefer a battle-item teaching reward over early Rare Candy value |
| Ether | Ruins of Alph optional | Quiet exploration reward; useful but not economy-breaking |
| Super Potion | Union Cave | First dungeon sustain |
| Great Ball | Union Cave | First stronger capture item, optional branch |
| Awakening | Union Cave / Route 33 | Covers cave/status friction |

### Marts

**Violet Mart** — basic trainer-student stock: Poke Ball, Potion, Antidote, Paralyze Heal, Awakening, Escape Rope, Repel. Add Super Potion only if the curve proves too tight after Roxanne and Union Cave testing.

### Reward pacing notes

- The Quick Claw should be the first true held item. Do not bury its explanation in narration; Mr. Pokemon should talk directly about the Pokemon carrying it.
- Roxanne's TM39 is the chapter's headline mechanical reward. It should feel earned, but the dialogue must be clear that it is not a badge.
- Keep Rare Candy out of the visible Violet early loop for now. If the vanilla item ball remains Rare Candy during implementation, downgrade it before chapter polish.

---

## Chapter 3 — Azalea · Slowpoke Well · First Gym

Grounded in the real map files: `071_T23.json` (Azalea Town), `158_T23R0501.json` (Kurt's House), `157_T23R0201.json` (Charcoal Kiln), `111/170/174_D26R010x.json` (Slowpoke Well 1F/B1F/B2F), `132/173_T23GYM010x.json` (Azalea Gym), `114_D36R0101.json` (Ilex Forest). Geography: **Route 33 (south) → Azalea Town → Slowpoke Well (in town) → Azalea Gym → Ilex Forest (west) → Goldenrod**. This is the first-badge chapter; the headline reward is a TM, and the economy stays small but starts including Super Potions.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| **Hive Badge** | Azalea Gym | Defeat **Turk** (Kurt's grandson; Bugsy officiates). Engine badge byte via `give_badge` |
| **TM89 U-turn** | Azalea Gym | Badge reward. The gym's strategic thesis (momentum / switching). Matches the vanilla Azalea TM |
| Charcoal | Charcoal Kiln (`T23R0201`) | Keep the vanilla kiln-man gift (`FLAG_GOT_CHARCOAL_FROM_AZALEA_TOWN_MAN`, `0x81`) as warm flavor / first Fire-boost held item |
| King's Rock | Kurt's House, **post-Well** | **Relocated** from the vanilla in-Well handout. Kurt gives a *clean* King's Rock as thanks after the rescue (reuses `FLAG_GOT_KINGS_ROCK_FROM_SLOWPOKE_WELL_MAN`, `0x7A`, re-sited). Keeps a King's Rock out of the crime scene as loot |
| Apricorn balls (Lure Ball etc.) | Kurt's House | Leave Kurt's vanilla Apricorn ball-craft loop (`FLAG_DAILY_KURT_MAKING_BALLS`, `0xAA2`) intact — domestic anchor flavor |

### Story objects (not bag items)

| Object | Where | Purpose |
|--------|-------|---------|
| **Modified King's Rock** | Slowpoke Well B2F, near the terminal | The *evidence* beat — a King's Rock fitted with unfamiliar circuitry. Read-only quest object Silver examines in Scene 3.3; never enters the bag |
| Un-wiped data logs | Slowpoke Well B1F/B2F | A few terminals the lead operative didn't reach in time. Flavor text only (transformation rates, stress/energy readings). No item |
| Silph Co. lab coat | Slowpoke Well B2F | The single branded detail — draped over an equipment case, then **gone** in the operatives' retreat. Seen, not recoverable. The Chapter 4 lever |

> Keep the Well loot-light on purpose. It's a crime scene, not a treasure dungeon — a couple of recovered consumables (below) read as "left behind in a hurry," not as a reward run.

### Field & hidden items

| Item | Location | Notes |
|------|----------|-------|
| Super Potion | Slowpoke Well B1F | Modest "left behind" consumable; first dungeon sustain at this tier |
| Antidote ×1–2 | Slowpoke Well | Covers Zubat/Koffing/Ekans poison friction during the doubles |
| X Attack or X Defend | Slowpoke Well B2F | Battle-item teaching reward; supports the double-battle lesson |
| Revive | Slowpoke Well (hidden) | One quiet hidden Revive — appropriate after the first dungeon with real fights |
| Potion / Antidote (town hidden) | Azalea Town | Light hidden-item flavor; keep money low |
| Super Potion | Ilex Forest | Passage-chapter sustain |
| Ether | Ilex Forest, near the Celebi shrine | Quiet exploration reward by the inert shrine; thematic, not economy-breaking |
| Full Heal or Awakening | Ilex Forest (hidden) | Covers status from the forest's Bug/Grass pool |
| Repel | Ilex Forest | Optional QoL for the headbutt-tree explorers |

### Marts

**Azalea Mart (`T23FS0101`)** — first post-Union-Cave restock. Stock: Poké Ball, Great Ball, Potion, Super Potion, Antidote, Paralyze Heal, Awakening, Repel, Escape Rope. Super Potion enters the standard stock here (the curve has earned it after Roxanne and Union Cave). Keep prices honest; the player is still money-poor pre-Goldenrod.

### Reward pacing notes

- **TM89 U-turn is the chapter's headline mechanical reward.** It must read clearly as the *badge* prize, distinct from Roxanne's non-badge TM39 in Chapter 2. The dialogue should connect it to the gym's lesson (momentum/switching), not hand it over as a generic trophy.
- **Move the King's Rock off the crime scene.** The vanilla Slowpoke-Well King's Rock handout undercuts the Well's tone; re-site it to Kurt as post-rescue thanks. The only King's Rock *inside* the Well is the modified evidence object, which is non-collectible.
- **Keep the Well loot-light.** A few consumables and one hidden Revive — no TMs, no held-item gifts, no rare balls inside the Well itself. The reward for the Well is narrative (and the badge that follows), not loot.
- The Charcoal and Apricorn-ball loops are deliberately preserved as Azalea's warm domestic texture — the counterweight the chapter keeps cutting back to between the cold of the Well.

---

## Chapter 4 — Route 34 · Goldenrod · Magnet Train · Saffron (arrival)

Grounded in the real map files: `035_R34.json` (Route 34), `073_T25.json` (Goldenrod City), `184–189_T25R1001–1006.json` (Department Store 1F–6F, elevator `396_T25R1007`), `488_T25SP0101.json` (Game Corner), `D37R0101` etc. (Underground), `200_T25R1201.json` (Global Terminal), `190_T25R0501.json` (Goldenrod Magnet Train Station), `357_T11R0601.json` (Saffron Station). Geography: **Ilex Forest (west) → Route 34 → Goldenrod City → Magnet Train → Saffron**. This is the **economic step-up** chapter: the Department Store is the first proper multi-floor shopping in the game, TMs become *purchasable*, and Route 34's Nugget gives the player their first real spending money. No badge, so no badge TM — the headline here is *commerce*, not a single gift.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| (none required) | — | Chapter 4 gives no story key item — it's a *buy* chapter. The Day-Care (Route 34) is introduced as a **system**, not an item gift |
| **Magnet Train Pass** | **Withheld** | The player rides to Saffron on **Mel's** pass and receives **no pass of their own** (`ITEM_PASS`, 480). This is the deliberate **one-way gate** that strands the player in Kanto until Chapter 5 resolves it. Do **not** gift it this chapter |

### Field & hidden items (Route 34 + Goldenrod)

| Item | Location | Notes |
|------|----------|-------|
| **Nugget** | Route 34 (`std_itemball_r34_nugget`, `FLAG_HIDE_ITEMBALL_R34_NUGGET`, `0x43F`) | Keep the vanilla ball. Sells for real money — the player's **first proper Department Store funding**. Intentional timing |
| **TM63 Embargo** | Route 34 (`std_itemball_r34_tm63`, `FLAG_HIDE_ITEMBALL_R34_TM63`, `0x4FA`) | Keep the vanilla ball. Niche utility TM; fine as flavor loot. (If a more useful early TM is ever wanted here, this is a low-stakes swap, but Embargo is the vanilla content and costs nothing to keep) |
| Hidden coins / small cash | Goldenrod City + Underground | Light hidden-item flavor appropriate to a big commercial city; keep modest |
| Hidden item(s) | Goldenrod Underground | Keep the vanilla Underground hidden items as curiosity rewards |

### Marts — the Department Store (the headline)

**Goldenrod Department Store (`T25R1001`–`R1006`)** — the first multi-floor store in the game and the moment the economy *opens up*. Exact per-floor assignment is a build-time detail; the design intent is a clear escalation from the single-counter Marts of Chapters 1–3:

The non-TM floors stay close to the **real vanilla Goldenrod arrays** (in `src/scrcmd_mart.c`), which are already stage-reasonable once gated by the player's thin wallet:

| Floor (intent) | Stock (grounded in vanilla arrays) |
|----------------|------------------------------------|
| Basics / medicine (`_020FBBEA`) | Potion, Super Potion, Hyper Potion, Antidote, Paralyze Heal, Burn Heal, Ice Heal, Awakening, Full Heal *(trim Max Potion to the later return if Hyper-tier feels too generous at badge 1 — it's money-gated either way)* |
| Balls / general (`_020FBC1A`) | Poké Ball, Great Ball, Ultra Ball, Escape Rope, Poké Doll, Repel, Super Repel, Max Repel |
| Battle items (`_020FBBB4`) | X Speed, X Attack, X Defense, X Accuracy, X Special, X Sp. Def, Dire Hit, Guard Spec. — supports the double-battle habits Chapter 3 taught |
| Vitamins (`_020FBAFA`) | Protein, Iron, Calcium, Zinc, Carbos, HP Up — pricey on purpose; the Nugget won't cover everything, so the player chooses |
| Rooftop / vending (`_020FBB16`) | Fresh Water, Soda Pop, Lemonade, Poké Doll, Repel — cheap bulk healing, the classic Goldenrod value play |
| **TM counter (the new thing)** | **Pinned below** — the first time TMs are *bought*; **utility/support only** at badge 1, the rest gated by badge count |

#### TM counter — pinned (the curve fix)

Vanilla Goldenrod sells two TM lists (`_020FBC34`, `_020FBC68`) totaling 24 distinct TMs. Sold *as-is* they'd hand a **first-badge** team (lead ~lv 14–17, 17 the ceiling) Blizzard / Fire Blast / Thunder / Hyper Beam / Solar Beam — curve-breaking this early (vanilla Goldenrod is a *mid-game* stop; Apocrypha arrives at the **first** badge). So the real vanilla pool is **tiered by badge count**: a **utility/support-only** rack sells now, and everything with attacking power — even moderate coverage — unlocks as the player earns more badges.

**Decision (confirmed):** at badge 1 the rack is **utility, support, catching, and field only — no attacking coverage TMs at all** (not even moderate ones like Dig/Avalanche/Brine — those read as too strong for the first badge). Power is gated strictly behind badge count.

**Tier 0 — sold now (≥1 badge, the badge-1 rack):**

| TM | Move | Role |
|----|------|------|
| TM17 | Protect | Universal utility |
| TM16 | Light Screen | Support — echoes the Hive-gym "protect/outlast" lesson |
| TM33 | Reflect | Support pair with Light Screen |
| TM20 | Safeguard | Status defense |
| TM12 | Taunt | Disruption utility |
| TM70 | Flash | Field utility + accuracy drop |
| TM54 | False Swipe | Catching utility — on-theme for the "world is bigger, catch more" chapter |
| TM27 | Return | The single offensive option, and only because it's **friendship-scaled** (weak until raised), not a fixed nuke. The "light" in "light coverage" |

*That's it for badge 1 — eight TMs, all utility/support/catching with one friendship-scaled normal attack. No type coverage is purchasable yet.* (Optional vanilla siblings if ever wanted as flavor: TM21 Frustration, TM83 Natural Gift — both marginal; left out of the core to keep the rack deliberate.)

**Later tiers — unlocked by badge count** (the rest of the real vanilla pool; exact thresholds are tunable to the final 20-badge order, but the *bands* are the point):

| Unlocks at | TMs | Rationale |
|------------|-----|-----------|
| **≥ ~4 badges** (moderate coverage) | TM28 Dig, TM72 Avalanche, TM55 Brine, TM79 Dark Pulse, TM76 Stealth Rock, TM83 Natural Gift | Real type coverage + the hazard, once the player's level and the gym ladder have caught up to it |
| **≥ ~8 badges** (the specials/nukes) | TM15 Hyper Beam, TM14 Blizzard, TM25 Thunder, TM38 Fire Blast, TM22 Solar Beam, TM52 Focus Blast | Full firepower for the back half; this is the vanilla Goldenrod offering, just timed correctly |
| anytime (flavor/niche) | TM21 Frustration, TM87 Swagger, TM78 Captivate, TM41 Torment | Low-impact gimmicks; fine to shelve with Tier 0 or the moderate tier — they don't move the curve |

Implementation note: a single clerk script can stock-gate by reading the badge count (or a small `VAR_APOC_GOLDENROD_TM_TIER` bumped as badges are earned) and appending the unlocked tiers to the offered list. No return-trip flag needed — the rack simply grows as the player does.

> **The Department Store is the chapter's real "reward."** After three deliberately money-poor chapters, the step-up is the payoff for reaching the big city — but it's *access*, gated by a thin wallet (one Route 34 Nugget) and a strictly utility rack, **not** a power spike. The TM counter then keeps paying off across the whole game: every few badges, Goldenrod has something new on the shelf.

### Game Corner (`T25SP0101`)

Optional, self-contained. Coins are won at the minigames and spent at the prize counter. Keep prizes on the generous-but-flavor side:

| Prize tier | Representative (tune at build) |
|------------|--------------------------------|
| Cheap | TMs not sold upstairs (a coin-exclusive utility TM or two) |
| Mid | A held item or evolution-adjacent item |
| Premium | A coin-exclusive **rare Pokémon** (the classic Game Corner mon) — a fun optional team-widener, kept level-capped |

> Game Corner content is **entirely optional** and must not gate anything. If the coin economy is more trouble than it's worth at build time, it can be reduced to flavor without affecting the chapter.

### Underground vendor (flavor shop)

The **traveling merchant** in the Underground (see [CHAPTER4_SCENES_SPEC.md](CHAPTER4_SCENES_SPEC.md) §4.1d) can be a tiny **flavor shop** selling one or two "imported" oddities (a held item or evolution stone framed as Hoenn/Sinnoh stock), or pure dialogue if a shop backend isn't wanted. Either way it sells the **Inter-Regional Exchange** as commerce. Keep it minor — the Department Store is where real buying happens.

### Reward pacing notes

- **This is the economy chapter.** The reward isn't a gift item — it's *access*: the Department Store, the TM counter, the Game Corner, the Underground vendor. The Nugget on Route 34 is the funding that makes the access matter. Let the player feel the jump from "money-poor traveler" to "kid loose in the big city with cash."
- **TMs become purchasable here** for the first time — a real systems milestone. The buy list is **pinned above**: **utility/support/catching only** at badge 1 (no attacking coverage), with moderate coverage and the vanilla nukes **gated by badge count**. The first city is a systems milestone, not a power spike, and the rack keeps growing as the player earns badges.
- **Withhold the Magnet Train Pass.** Riding on Mel's pass is the one-way trick; the player's lack of a pass is what keeps them in Kanto. Resolved in Chapter 5 — do not hand one out now.
- **No Saffron shopping this chapter.** The arrival is the chapter close; Saffron's Mart, Game Corner, and Silph content are Chapter 5+ surface. Keep Chapter 4's economy entirely Goldenrod-side.
