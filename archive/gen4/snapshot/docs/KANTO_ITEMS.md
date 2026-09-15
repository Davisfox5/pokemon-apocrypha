# Pokémon Apocrypha — Kanto Item Locations

The Kanto companion to [JOHTO_ITEMS.md](JOHTO_ITEMS.md): item & hidden-item locations
and Mart stock for the Kanto chapters. Kanto begins at **Saffron City (Chapter 5)**.

> Detail split (see [[apocrypha-doc-taxonomy]]):
> - this file — Kanto items + marts
> - [KANTO_BATTLES.md](KANTO_BATTLES.md) — Kanto encounters + trainers
> - per-chapter docs (`CHAPTER<N>_BUILD.md` / `CHAPTER<N>_SCENES_SPEC.md`) — staging + dialogue

**Economy note:** the player reaches Kanto **money-poor and badge-light** (1 badge),
having just had their Goldenrod shopping trip. Kanto is *endgame* in vanilla HGSS, so
its vanilla Marts are stocked for high-level players; Apocrypha **trims Kanto stock to
the story's actual tier** here, the same discipline as the Goldenrod TM gating (see
[JOHTO_ITEMS.md](JOHTO_ITEMS.md)). Stock grows as the player earns Kanto badges.

---

## Chapter 5 — Saffron City (stranded)

Grounded in the real map files: `056_T11.json` (Saffron City), `359_T11R0701.json`
(Silph Co. lobby), `365_T11FS0101.json` (Saffron Mart), `363_T11PC0101.json` (Pokémon
Center), `361/362_T11R0801/02.json` (Copycat House), `357_T11R0601.json` (Magnet Train
Station). Chapter 5 is a **story/atmosphere chapter** — light on items by design. The
headline "item" is really a **non-item**: the rail pass the player *can't* buy.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| **Magnet Train Pass** | **Unobtainable in Kanto** | The stranding lock. Rail passes are issued **only in the holder's home region** (Johto); the player can't buy one here at any price. `ITEM_PASS` is **never granted** in Kanto. Not a quest — a rule (resolved by later progress, not by shopping) |
| **Copycat's reward** | Copycat House (`T11R0802`) | Bring Copycat the specific item/doll she wants; she rewards a **Nugget**. Thematic (a broke kid stranded in a money city gets a lump to sell) and **curve-safe** — a bounded one-time payout, not a compounding money-doubler. Sells for real cash toward the road ahead |

### Story objects (not bag items)

| Object | Where | Purpose |
|--------|-------|---------|
| **Community Partnerships wall** | Silph lobby | Read-only display listing Silph's "partner sites" — a few of which the player will *later* recognize as compromised (the Ruins of Alph, others). A seed, not an item |
| **Magnet Train display** | Silph lobby | Boasts Silph-engineered "aware" train systems; pairs with the engineer's "over-engineered / extra sensors" grumble. A seed |
| **Badge-locked elevator bank** | Silph lobby | The visibly-gated door to the upper floors the player can't pass. Staging, not an item |

### Field & hidden items

Keep Saffron **light** — it's a transition city, not a loot stop. A few modest hidden
items appropriate to a big corporate city are fine (a stray consumable in the plaza or
near the café; coins/cash in a corner), but no TMs, no held-item gifts beyond Copycat,
no rare balls. The chapter's reward is narrative (and the road out), not loot.

| Item | Location | Notes |
|------|----------|-------|
| Hidden small cash / coins | Saffron streets / plaza | Light flavor; the city is wealthy, the player is not |
| Hidden consumable (Potion / Super Potion) | Near the Center or café | One or two quiet finds; keep modest |

### Marts

**Saffron Mart (`T11FS0101`)** — a big-city Mart kept to the player's **badge-1 tier**
(roughly matching the Goldenrod Department Store basics floor; **not** the vanilla
endgame Kanto stock). Recommended stock: Poké Ball, Great Ball, Potion, Super Potion,
Antidote, Paralyze Heal, Burn Heal, Awakening, Repel, Super Repel, Escape Rope.

> **Trim the vanilla Kanto stock.** Vanilla HGSS Kanto Marts sell Ultra Balls, Hyper
> Potions, Full Restores, Max Repels — endgame-tier, because Kanto *is* the endgame
> there. At Apocrypha's badge-1 arrival that's ahead of curve; keep Ultra Ball / Hyper
> Potion-and-up gated to later Kanto badges (dial). Consumables are money-gated either
> way, so this is about *signaling the tier*, not hard balance.

### Reward pacing notes

- **The big "item" beat is a withheld one** — the rail pass the player can't buy. Lean
  into the anticlimax: the player walks up expecting to solve it with money and learns
  it's a *rule*. That's the chapter's defining mechanical moment.
- **Copycat is the one real reward** — keep it charming and curve-safe (a **Nugget**;
  the broke-in-a-money-city irony does double duty as flavor, and a one-time payout
  won't compound like a prize-money multiplier would).
- **Saffron is loot-light on purpose.** It's a place the player is *passing through* and
  stuck in, not a treasure city. Save Kanto's real item economy for the chapters where
  the player is actually progressing (Lavender / Celadon, Chapter 6+).

---

## Chapter 6 — Route 7/8 · Celadon (optional) · Lavender

Grounded in the real map files: `012_R07.json` / `013_R08.json` (routes), `052_T07.json`
(Celadon) + interiors (Dept Store `T07R0101…`, Condominiums `T07R0201…`, Restaurant
`T07R0701`, Game Corner `T07SP0101`), `050_T05.json` (Lavender) + Radio Station
`T05R0701`, Mart `T05FS0101`. Chapter 6 is where **Kanto's item economy actually opens
up** — but Celadon's headline is **services**, not stock, and Lavender stays modest. The
badge chapter's headline reward is a TM (Shadow Ball), as in Johto.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| **Requiem Badge** (2nd badge, 1st Kanto) | Eve's Ghost Gym (Lavender) | Defeat **Eve**. Engine `give_badge <BADGE_*>` — badge-order pass assigns the constant. Opens the Route 6 (Vermilion) checkpoint |
| **TM30 Shadow Ball** | Eve's Ghost Gym | Badge reward — the vanilla Ghost-gym precedent (Morty). Earned, not bought. Real Ghost STAB/coverage, appropriate as an *earned* badge-2 prize |
| **Erika's botanical gift** | Celadon Botanical Gardens | Erika gives a nature-themed reward — recommend a **held berry** (e.g. a status-cure or a pinch-berry like Sitrus/Lum). Curve-safe, thematic, "a piece of a place that chose to grow." Dial: a Miracle Seed (Grass-boost held item) if a type item is preferred |
| **TM88 Pluck** | Celadon Café (side quest) | Reward for the Fan Club Chairman's ingredient fetch. Food-themed (steals the target's held berry). Explicitly **not Leftovers** — too strong now |
| **TV exhibition reward** | Lavender Broadcast Tower | Prize money + a useful item (recommend a stack of consumables or an X-item bundle — showy, not powerful) for stepping into the canceled segment |

### Celadon services (the "not a mall, a market" step-up)

Celadon's repurposed Dept Store / market is about **services**, not shelves — the economic
novelty of the chapter is *paying for care and training*, not buying power:

| Service | Where | Effect |
|---------|-------|--------|
| **Daisy Oak's salon** | Market services building | Grooming → **friendship / condition** boost. First visit free (flavor). No power, pure care |
| **Move Tutor** | Market services building | Re-teach / tutor moves for a fee (or a currency like heart scales if wired). Utility, not power creep — keep the tutor list stage-appropriate |
| **EV-training facility** | Market services building | Pay for structured stat-training sessions. A *time/money* investment path, not a free power spike — price it so it's a choice, not a default |

### Marts

**Celadon Market** — services-forward (above); as a *shop*, keep item vendors light and
badge-2-tier (Poké/Great Ball, Super Potion, status heals, Repels, a few X-items in the
market stalls). **Not** the vanilla endgame Celadon Dept Store stock.

**Lavender Mart (`T05FS0101`)** — modest, badge-2-tier: Poké Ball, Great Ball, Super
Potion, Antidote, Paralyze Heal, Awakening, Repel, Super Repel, Escape Rope. (Trim the
vanilla endgame Kanto stock as with Saffron.)

### Field & hidden items

| Item | Location | Notes |
|------|----------|-------|
| Route 8 items | Route 8 | A couple of modest field/hidden items on the spine (a Super Potion, an Antidote/coins). Keep light |
| Route 7 items | Route 7 | One optional hidden item on the short Celadon connector |
| Celadon hidden | Celadon plaza / gardens | Light flavor (a berry near the gardens, coins in the market) |
| Lavender hidden | Lavender / near the cemetery | One quiet find near the memorial hill (a Cleanse Tag or Spell Tag — thematic, curve-safe) |

### Game Corner (`T07SP0101`)

Celadon's surviving Game Corner — slots + prize counter, entirely optional. Same
discipline as Goldenrod's: keep prizes flavor/utility (a coin-exclusive utility TM, a
held item, a coin-exclusive rare mon), nothing curve-breaking, and never gate anything on
it.

### Reward pacing notes

- **The chapter's "economy" is services, not stock.** Daisy Oak (care), the move tutor
  (utility), and EV training (investment) are the novelty — Celadon lets the player *invest
  in* their team rather than *buy power for* it. Keep purchasable items badge-2-tier.
- **Shadow Ball is an earned badge prize**, consistent with Johto's badge TMs (U-turn,
  Rock Tomb). It's real coverage, but it's *earned*, not sold — distinct from the strict
  utility-only rule on the Goldenrod **store** rack.
- **Pluck, not Leftovers.** The café reward is deliberately a fun, low-power food move; the
  strong food item (Leftovers) is held back for later.
- **Celadon is optional and loot-light on purpose** — its value is charm, services, and
  characters, not treasure. The required progression (and the badge) lives in Lavender.

---

## Chapter 7 — Route 6 · Vermilion City · Route 11 · Diglett's Cave (departure)

Grounded in the real map files: `011_R06.json` (Route 6), `051_T06.json` (Vermilion) +
interiors (Gym→Lodge `322_T06GYM0101`, Fan Club→Exchange `362_T06R0301`, houses
`361/363/364_T06R0101/0401/0601`, Mart `360_T06FS0101`), `016_R11.json` (Route 11),
`103_D01R0101.json` (Diglett's Cave), `386/387_T04R0301/0401.json` (S.S. Aqua Vermilion
port). Chapter 7's headline "item" is a **key item that isn't a reward** — the **S.S.
Ticket** Silver uses to point the player at Hoenn — plus a **promissory fossil** the player
can't cash in yet. Loot-light by design; the payload is narrative and a destination.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| **S.S. Ticket** (`ITEM_S_S__TICKET`, 456) | Vermilion port (Silver cutscene) | Silver presses it over — a "spare the League keeps." **Reuse the vanilla S.S. Ticket key item, retargeted to Slateport** (the S.S. "network" is the broader international loop, not just the Olivine ferry). The boarding pass for the Ch7→Ch8 crossing. Not earned — *given*, to direct the player (see pacing notes) |
| **Claw Fossil** (`ITEM_CLAW_FOSSIL`, 100 → **Anorith → Armaldo**) | **Diglett's Cave** (deep rock) | An **Apocrypha add** (vanilla Diglett's Cave has no fossil), and a deliberately **non-Kanto-native** revive (user call). Lore: *"this ancient sea-Pokémon lived in Kanto's primordial shallows and its lineage migrated to other regions"* — Armaldo is a **Hoenn** mon, so the fossil the player digs up already made the Kanto→Hoenn crossing they're about to make. Deepens the Inter-Regional Exchange into **deep time.** A **promissory reward**: revivable only at the **Pewter Museum lab — this chapter's blocked destination** → a concrete reason to return to Kanto's northwest later. One-shot (`FLAG_APOC_CH7_FOSSIL_TAKEN`). *Dials:* Root Fossil (Lileep→Cradily, Hoenn, sea-lily) is the equal maritime alt; the Sinnoh pair (Skull→Cranidos / Armor→Shieldon) if the migration should point at Sinnoh |
| **A rod** (Good Rod, dial) | Vermilion **Fishing Dude House** (`T06R0101`) | The kept fishing NPC gives/upgrades a rod — feeds the Route 6 coastal water table (Wingull migrant, Poliwag) and Vermilion's fishing-waterfront theme. Utility, curve-safe |
| **Magnet Train Pass** (`ITEM_PASS`, 480) | **Still never granted** | The Ch5 stranding rule persists — the player leaves by **ship, not train.** The departures board reinforces it (rail = home-region passholders only). Silver's ticket is a ship *away*, not a road home |

### Diglett's Cave field items (re-tuned)

Vanilla Diglett's Cave carries **endgame-tier** finds — **trim them** to the badge-2 band,
the same discipline as Saffron/Celadon marts:

| Vanilla item | Apocrypha (re-tuned) | Notes |
|--------------|----------------------|-------|
| Max Revive (hidden) | **Revive** | Max Revive is ahead of curve at ~lv25; a plain Revive fits |
| PP Max (ball) | **PP Up** | PP Max is an endgame one-of-a-kind; PP Up is the badge-2-tier version |
| Calcium (hidden) | **Calcium** (keep) | One free vitamin is fine — vitamins are money-gated everywhere else |
| Rock Incense (ball) | **Hard Stone** (or keep) | Rock Incense is a niche breeding item; a Hard Stone is more useful this tier (dial) |
| — | **the Claw Fossil** (added) | The real prize (above); embedded deep, one-shot; the deep-time migration lore |

### Marts

**Vermilion Mart (`T06FS0101`)** — a port-city Mart kept to the **badge-2 tier** (matching
Saffron/Lavender; **not** the vanilla endgame Kanto stock). Recommended: Poké Ball, Great
Ball, Super Potion, Antidote, Paralyze Heal, Burn Heal, Awakening, Repel, Super Repel,
Escape Rope. A small **maritime flavor** touch is fine (an extra stack of Repels "for the
cave," a discounted Escape Rope) but no Ultra Balls / Hyper Potions yet.

> **Trim the vanilla Kanto stock** (repeat of the Ch5/Ch6 discipline): Kanto is endgame in
> vanilla HGSS, so its Marts sell Ultra Balls / Full Restores / Max Repels. At Apocrypha's
> 2-badge tier that's ahead of curve; keep the good stuff gated to later regions/badges.

### The port economy (flavor, not a shop)

Vermilion is a **working port**, and its "economy" is texture, not stock — the cargo/customs
world the player walks through (manifests, throughput, permits). The one *venue* is the
**International Pokémon Exchange** (Fan Club, repurposed): a **trade & showcase hall**, not
a store — optional NPC-trade / showcase content, the Inter-Regional Exchange rule made a
place. No power for sale; the value is meeting the connected world in one room.

### Field & hidden items

| Item | Location | Notes |
|------|----------|-------|
| Route 6 items | Route 6 | A couple of modest field/hidden items on the descent (a Super Potion, coins). Keep light |
| Vermilion hidden | Docks / plaza | Light flavor (coins on the pier, a stray consumable near the warehouses). A wealthy working port; modest finds |
| Route 11 items | Route 11 | One or two on the eastern road (an Antidote/coins; a hidden item near the lookout) |
| Diglett's Cave | see above | The re-tuned finds + **the fossil** — the chapter's one real loot beat |

### Reward pacing notes

- **The headline "reward" is a redirection, not a prize.** The S.S. Ticket *feels* like a
  gift and *functions* like an order — Silver chooses the player's next destination and the
  player thanks him for it. Keep the framing generous and the subtext directive; that
  tension is the chapter's defining beat (it mirrors Mel sweeping the player onto the train
  in Ch4). Mechanically it's just a boarding key item; narratively it's the hook.
- **The fossil is a promise, not a payoff.** Un-revivable now (Pewter lab = the blocked
  destination). Lean into it: the player finds something precious and immediately learns
  they can't use it yet. It plants a *return* and rewards exploration without giving power.
  It also carries **lore, not just loot** — a non-native (Hoenn) ancient sea-Pokémon found
  deep under Kanto, framed as "it lived here, then migrated," which quietly makes the
  Inter-Regional Exchange *ancient* rather than modern, and foreshadows Hoenn one beat before
  the player sails there.
- **`ITEM_PASS` stays withheld.** The player still can't buy/earn the home-region rail pass —
  they leave Kanto the only way open to them: a ship pointed *away* from home. The one-way
  logic that stranded them (Ch5) now carries them onward (Ch7). Same rule, opposite effect.
- **Loot-light, like Saffron.** Vermilion is a place the player passes *through* on the way
  to a bigger region. Save Kanto's deeper item economy (and Pewter's fossil lab) for later
  returns; Chapter 7's job is momentum and a destination, not treasure.
