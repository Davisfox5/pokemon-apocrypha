# Pokemon Apocrypha - Chapter 7 Build Spec

> Scope: Route 6, **Vermilion City** (the maritime hub), Route 11, **Diglett's Cave**,
> and the **departure by sea** — the Silver encounter at the port and the S.S. Ticket
> that sends the player to Hoenn. **No badge**: a travel/transition chapter. This is the
> implementation-facing expansion of the Chapter 7 outline in `DESIGN.md`. Pairs with
> **[CHAPTER7_SCENES_SPEC.md](CHAPTER7_SCENES_SPEC.md) — the full line-by-line dialogue
> script** — and with [KANTO_BATTLES.md](KANTO_BATTLES.md) (encounters + route/Lodge
> trainers) and [KANTO_ITEMS.md](KANTO_ITEMS.md) (items + marts + the fossil + the
> ticket). The "Sample lines" below are voice references; the full script is in the
> scenes spec.

## Chapter Promise

Chapter 7 is the payoff for stopping being stranded. The player earned a credential
(Eve's badge), the road south opened, and now they walk into **Vermilion** — a working
port city that has become the single busiest crossroads in the region. Where Saffron was
cold and Lavender was busy proving itself, Vermilion is just *working*: cranes, cargo,
customs lines, ships from four regions at berth, and a constant churn of people coming
and going. It's the first place in Kanto that feels like the whole connected world
DESIGN keeps promising — you can stand on the dock and see how small the distance between
regions has become.

The player came here with a vague plan of **going home**. The chapter quietly takes that
plan away and hands them a bigger one. They explore a real city, test themselves on two
new routes and a cave, and then — at the port, deciding which way home — **Silver** finds
them. The Champion. Warm, generous, impossible to read. He congratulates them, asks a few
too-pointed questions about a journalist named Mel, and presses an **S.S. Ticket** into
their hand: not home, but *Hoenn.* The player thinks they've been rewarded. They've been
**directed** — the second time this game an adult with more power has pointed the player
somewhere for reasons the player can't see, and the player has gone willingly.

The chapter ends with the Vermilion skyline receding across open water. New region next.

Core themes:

- **The connected world, made physical.** Everything DESIGN says about rail and the S.S.
  network and collapsing distance is *abstract* until Vermilion. Here the player stands in
  the machine: manifests, throughput, customs, ships to Slateport and Olivine and
  Driftveil. The world is one market now, and the port is where you feel it.
- **Momentum with a borrowed destination.** The player is moving with purpose for the
  first time since the Well — but the destination keeps being *chosen for them.* Mel swept
  them to Kanto (Ch4); Silver ships them to Hoenn (Ch7). They go willingly both times.
  That willingness is the quiet horror the game is building.
- **Silver, the deniable hero.** Every beat of the port scene is a good Champion doing a
  kind thing. He also dismisses three lab-coated associates before he approaches, and his
  interest in Mel is a scalpel. Nothing provable. Everything wrong.
- **A city that finished its work.** Vermilion's running gag — the building under
  construction forever — is *done.* The old man died; his Machamp finished it alone. It's a
  quiet grace note about work outlasting the worker, in a chapter that's otherwise about a
  city that never stops moving.

> **Reviewed & confirmed (design pass).** (1) **Silver does not battle** — the port scene
> stays a pure cutscene; his strength is saved for a later climactic fight and the menace
> stays deniable. (2) **Route 11's two Psychic slots reclass to Sailor/Hiker** (DESIGN's
> archetypes; a build-time sprite/class edit, teams written to fit) — *confirmed*, not a
> fallback. (3) **The Pewter/Route 2 wall stays mundane** — "tunnel maintenance" that's
> overrun its welcome, with a scrawled hint something's off (no overt conspiracy, no second
> credential gate). (4) **The Maritime Museum return-hook stays deferred** — ship the flavor
> + the Machamp now, design the mechanical hook when later-game Vermilion content is built.
> (5) Fossil = **Claw Fossil → Anorith/Armaldo** (Hoenn), the non-native "it migrated" lore.
> Level band **~lv22→25-26** confirmed.

## Progression Spine

| Beat | Maps | Purpose |
|------|------|---------|
| 7.0 Route 6 south | Route 6 (`R06`) | The badge-cleared checkpoint; 4 sight-trainers; the descent to the coast |
| 7.1 Vermilion arrives | Vermilion City (`T06`) | The maritime hub; the port visual; town texture (customs, dockworkers, growth) |
| 7.2 The Trainers' Lodge | Vermilion Gym repurposed (`T06GYM0101`) | Surge's gym → cosmopolitan hostel; 3 traveler battles; the travel-tips board |
| 7.3 The International Exchange + Museum | Fan Club (`T06R0301`), a repurposed house | Fan Club → Pokémon Exchange (the theme, literal); the Maritime History Museum + the Machamp |
| 7.4 Route 11 east | Route 11 (`R11`) | 4 sight-trainers; the lookout point; the fisherman; the Snorlax branch-block |
| 7.5 Diglett's Cave | Diglett's Cave (`D01R0101`) | Items + **the fossil**; the **Pewter (Route 2) soft-wall** |
| 7.6 Silver at the port | S.S. Aqua Vermilion port (`P01R0103/0104`) | The cutscene: lab coats dismissed; the Mel probe; the **S.S. Ticket to Slateport** |
| 7.7 Departure by sea | port → ship | Board; the skyline recedes; hand off to **Chapter 8 (Slateport)** |

Target start state: lead team ~lv 22, **2 badges (Hive + Requiem)**, fresh off Eve's gym.
Target end state: lead team ~lv 25-26, **2 badges (no new badge)**, holding an **S.S.
Ticket to Slateport**, Kanto behind them — Chapter 8 opens in Hoenn.

> **Level note (post +3 curve lift).** Chapter 7 sits **between the badge-2 line (~lv22)
> and the badge-3 line (~lv27)** on the whole-game curve. The player arrives ~lv22 off
> Eve; Route 6 + Route 11 + Diglett's Cave carry them to ~lv25-26 by the departure —
> right-sized for the first Hoenn gym. Vanilla Kanto is endgame-leveled (Route 6 trainers
> lv24, the gym lv40s+); Apocrypha **re-tunes down** to this band, the same discipline as
> Ch5/Ch6. See [KANTO_BATTLES.md](KANTO_BATTLES.md).

## Cast

### The port scene

**Silver — the Champion (the chapter's spine).** Giovanni's son, grown into the most
admired trainer alive and the current Champion. This is his **second speaking
appearance.** He is **warm, gracious, and completely opaque.** He congratulates the player
on a badge earned the hard way, asks — lightly, twice — about the journalist who dragged
them into Kanto, and then solves their problem for them: an S.S. Ticket to Slateport,
"a spare the League keeps for promising kids." Every line is a good Champion being kind.
The staging says otherwise: **he dismisses three lab-coated associates and an executive
before he approaches**, and his interest in Mel is not idle. The player leaves grateful.
That's the point — Silver is the game's thesis that the most dangerous power looks exactly
like generosity. **He does not battle here.**
- *"You look like the week has been long. Two badges, though. In a region that isn't
  yours, without a soul helping you. That's not luck. I know luck; that's not it."*
- *(light, twice)* *"The reporter who brought you over — Mel, was it? Chatty type. She
  still... chasing whatever she was chasing? No reason. She just leaves an impression."*
- *(pressing the ticket over)* *"Go to Hoenn. Really. The gyms will humble you and the
  region's worth the boat. I've got a spare — don't argue, I've got dozens. Consider it a
  Champion betting on you."*

**The associates — lab coats + an executive (silent).** Three figures Silver is speaking
with when the player arrives; he sends them off with a look before he turns to the player.
Silph-coded (the coats read the same as the Slowpoke Well detail and the Saffron HQ). They
**say nothing to the player** and walk off toward the cargo side. The player half-sees
them. It is never explained. A **seed**, not a scene.

### Vermilion — the working port

**The Maritime History Museum Machamp (the caretaker).** The building that was under
construction "forever" (the vanilla Vermilion running gag) is **finished.** The old man
who dreamed it — a retired sailor — has **passed away**; his **Machamp** completed the
construction alone and now keeps the museum: straightening displays, dusting a Sevii
expedition log and an Orange Islands figurehead, greeting visitors with a solemn nod. It
does not battle. It is the chapter's grace note. (Reuse the vanilla **Machop/Machamp
follower object** already placed in `T06`.)
- *(no dialogue — the Machamp only nods; a placard by the door carries the old man's
  name and the dates, and a single line: "He said he'd finish it. He did.")*

**The Lodge travelers (Trainers' Lodge — old gym).** Surge relocated to Mauville
(DESIGN); his Electric gym is now a **hostel for trainers arriving by ship.** Bunks, a
common room, a bulletin board of travel tips and open challenges. The travelers are the
chapter's cosmopolitan texture and its **import battles** (justified: they came off boats
from everywhere). A **Slateport sailor** talks about Hoenn's weather; an **Olivine
backpacker** describes the lighthouse; a couple of them battle. (Re-line the gym's 3
vanilla trainer slots — see State And Files.)
- *(sailor)* *"Just off the Slateport run. You want weather? Hoenn's got weather. Rains
  sideways, then the sun'll cook you, then it rains up. I loved it. Going back."*

**Port-town residents (Vermilion streets + houses).** The town's identity has shifted from
quaint seaside village to working-class port. NPCs talk shipping schedules, cargo
manifests, overtime. A **customs officer** buried in paperwork; a **dock supervisor's
spouse** worried about the hours; a **retired sailor** who misses the old Vermilion; one
resident notes the port has **tripled its throughput** in five years since the S.S.
network expanded. Growth isn't always comfortable.

**The International Pokémon Exchange (Fan Club, repurposed).** The old Pokémon Fan Club is
now an **inter-regional trade & showcase hall** — the Inter-Regional Exchange rule made
literal: trainers from different regions meet here to trade and show off. (The Fan Club
**Chairman himself is away** — he's in *Celadon*, boring a café owner about his Rapidash,
per Ch6; a nice cross-chapter consistency.) A place to see the connected world in one
room. Optional NPC-trade / showcase content; **no battle required.**

**The Route 11 fisherman.** On the coastal route east, a fisherman offers a **battle** and
**tips about Diglett's Cave** ahead ("dark, deep, and it doesn't come out where you'd
hope"). Ties to Vermilion's fishing waterfront and the **Fishing Dude House** (`T06R0101`,
kept as a fishing enthusiast — rod tips / a rod upgrade).

## Scene Details

### 7.0 Route 6 — South to the Coast (the checkpoint pays off)

The Saffron south gate (`R06R0201`, the Chapter 5 blocker) now **accepts the Requiem
Badge** on its existing badge-conditional check — no new flag, just the check passing. The
guard waves the player through, and Route 6 descends from the Saffron plateau toward the
sea. First glimpse of the port on the horizon.

Staging direction:

- **Confirm the badge-gate opens automatically.** The guard's Ch5/Ch6 "closed" branch
  falls through once `give_badge` (Requiem) has run; write the **open** branch (a line
  acknowledging the credential) and let the player pass. See Ch6 §6.6.
- **Four sight-trainers, already placed** in `011_R06.json` via `std_trainer`: **Camper
  Virgil**, **Picnicker Selina**, and the **Twins Day & Dani** (a built-in **double
  battle**). Re-line them as Saffron-corridor day-trippers / coastal locals; rosters and
  the re-tune-down in [KANTO_BATTLES.md](KANTO_BATTLES.md). This plus Route 11 is the
  chapter's level engine.
- Wilds (Route 6 grass + the coastal water tables) in [KANTO_BATTLES.md](KANTO_BATTLES.md);
  apply the whole-game **re-tune-down** (vanilla Route 6 grass is fine at ~lv12-15, but the
  band should sit at the badge-2+ tier here — lift the *route* to meet the player, the
  inverse of Ch6's problem). The coastal water introduces the **naturalized port migrant**
  (a Hoenn **Wingull** — "the gulls came in on the boats"), kept rare.

### 7.1 Vermilion City — The Port Town

Route 6 opens onto Vermilion. The docks dominate the southern waterfront: cranes, cargo
containers, warehouses, ships from multiple regions at berth. Residential neighborhoods
have expanded north and inland — port workers, customs officials, shipping employees. The
sea here isn't scenic; it's a **workplace.**

Staging direction:

- Dress `051_T06.json` toward **industrial port**: cranes and containers on the south
  waterfront, a widened dock, a customs checkpoint near the pier, warehouses. Retheme the
  vanilla NPC chatter (generic townsfolk → port workers: schedules, manifests, overtime).
- The vanilla **Suicune / Eusine / Steven** events in `T06` are flag-hidden and **not part
  of Apocrypha's story** — leave them hidden/unused (don't trip their flags).
- Keep the town's geography readable: **Pokémon Center** (`T06PC0101`) and **Mart**
  (`T06FS0101`) kept; the **Trainers' Lodge** (7.2), the **Exchange** and **Museum** (7.3),
  and the warp to the **port** (7.6) are the landmarks. The player will end the chapter at
  the port, so signpost it early (a dockside sign, the S.S. departures board).

### 7.2 The Trainers' Lodge (old Vermilion Gym)

Surge's Electric gym is now a **hostel for trainers arriving by ship** — the building
keeps Surge's industrial bones (metal walls, the old feel) softened with bunks, a common
room, and a bulletin board of travel tips and challenges. Transient, cosmopolitan energy:
everyone is coming or going.

Staging direction:

- Repurpose `322_T06GYM0101.json`: strip the gym puzzle (the trash-can switch obstacles are
  flag-hidden dummies — leave them off), reframe as the Lodge interior. Add a **travel-tips
  bulletin board** (read-only flavor; hints at Slateport/Olivine/Driftveil and the
  departures ahead).
- **Re-line the gym's 3 trainer slots** as Lodge travelers (battleable, the cosmopolitan
  import battles): `TRAINER_GUITARIST_VINCENT`, `TRAINER_JUGGLER_HORTON`,
  `TRAINER_GENTLEMAN_GREGORY` — recast as a Slateport sailor, an Olivine backpacker, and a
  well-traveled gentleman; rosters (Kanto-base with a level-capped import each) in
  [KANTO_BATTLES.md](KANTO_BATTLES.md). **Lt. Surge is not here** — a note on the board or
  an NPC line explains he's in Mauville "on the grid" (DESIGN).

### 7.3 The International Exchange + The Maritime History Museum

Two Vermilion interiors carry the chapter's texture.

Staging direction:

- **International Pokémon Exchange** (repurpose the **Fan Club** `362_T06R0301.json`): an
  inter-regional trade & showcase hall — trainers from different regions meet to trade and
  show off rare Pokémon. The Inter-Regional Exchange rule, made a *place.* The **Fan Club
  Chairman is absent** (he's in Celadon — Ch6). Optional NPC-trade / showcase content; a
  couple of cross-region NPCs; **no battle required.** A clean spot to nod at the connected
  world without plot weight.
- **Maritime History Museum** (repurpose a Vermilion house — recommend the **Central House**
  `363_T06R0401.json`, or the vanilla "endless construction" building): the finished
  building, the **Machamp caretaker**, and a small, specific collection — a Sevii Islands
  captain's log, an Orange Islands figurehead, old manifests and navigation instruments,
  some pieces pointing at places the player hasn't been. **Return-hook: deferred
  (confirmed).** The museum needs a mechanical reason to revisit (an activity/quest/reward),
  but that's **intentionally not designed this pass** — ship the flavor + the Machamp now,
  and design the hook when later-game Vermilion content exists. Candidates to weigh then: a
  **region-collection quest** (bring back artifacts found in later regions), a **conspiracy
  archive** (the old shipping manifests become evidence for the port-trafficking arc), or a
  **heritage move tutor.** Leave a build note; don't stub the mechanic yet.

### 7.4 Route 11 — East to the Cave (the lookout)

Route 11 runs east from Vermilion toward Diglett's Cave. It has more substance than early
Johto paths: rocky outcroppings, coastal scrub, tall grass. Trainers are sailors on shore
leave, gamblers drifting from the Celadon direction, hikers headed for the cave. A
**lookout point** near the cave entrance shows the sea and Vermilion's port — you can see
ships at dock from here.

Staging direction:

- **Four sight-trainers, already placed** in `016_R11.json` via `std_trainer`: **Psychic
  Fidel**, **Psychic Herman**, **Youngster Owen**, **Youngster Jason** — re-line as shore-
  leave sailors / hikers / a gambler; rosters + re-tune in
  [KANTO_BATTLES.md](KANTO_BATTLES.md). Add the **fisherman** (battle + cave tips) as a
  small placed trainer or reuse the coastal edge.
- **The lookout point:** a read-only vista object near the cave mouth (the port and the sea;
  a quiet "look how far you've come / how far there is to go" beat). Optional bench NPC.
- **The Snorlax branch-block:** `016_R11.json` carries a **sleeping Snorlax**
  (`FLAG_HIDE_ROUTE_11_SNORLAX`, `0x261`). Keep it asleep — the player has no Poké Flute
  and the radio-flute quest is cut — and use it to **block the Route 11 branch that would
  lead deeper into Kanto by land.** The only through-path east is **into Diglett's Cave**,
  and the cave's far exit is the Pewter soft-wall (7.5). Both blockers funnel the player
  back to the port: *Kanto has no land road onward — the only way forward is by sea.* (An
  NPC lampshades the sleeping Snorlax: "Been out for years. Whole route reorganized around
  its nap.")
- Wilds (Route 11 grass) in [KANTO_BATTLES.md](KANTO_BATTLES.md); Kanto-native
  (Drowzee/Rattata/Magnemite, Hypno rare), re-tuned to the band.

### 7.5 Diglett's Cave — Items, the Fossil, and the Pewter Wall

Diglett's Cave is a deep, dark tunnel of tumbling ground-types. **No trainers** — it's an
exploration-and-loot beat, and it holds the chapter's one real treasure and its
westernmost wall.

Staging direction:

- **No trainer objects** (vanilla `103_D01R0101.json` has none — keep it that way; the cave
  is a wild/loot space, a change of pace from two trainer routes).
- **Wilds:** Diglett (common) / Dugtrio (rare) only — faithful to vanilla; levels re-tuned
  to the band (Dugtrio the rare high mark). A pure-Ground pocket is a nice team-testing
  wrinkle after two mixed routes.
- **Items** (details + re-tune in [KANTO_ITEMS.md](KANTO_ITEMS.md)): the vanilla finds
  (Max Revive, Calcium, PP Max, Rock Incense) are **endgame-tier — trim them** to the
  badge-2 band (Revive / Calcium / PP Up / a Hard Stone). **Add the fossil** (DESIGN):
  a single fossil embedded deep in the rock — the **Claw Fossil** (`ITEM_CLAW_FOSSIL`,
  100 → **Anorith → Armaldo**, a **Hoenn** fossil). The lore is the point (user call): it's
  a *non-Kanto-native* revive, framed as **"this ancient Pokémon lived in Kanto's
  primordial seas and its lineage migrated to other regions"** — an ancient sea-arthropod
  whose descendants ended up in Hoenn's waters, which is *exactly where the player is about
  to sail.* It deepens the Inter-Regional Exchange into deep time (the world was always
  connected). It is a **promissory reward**: revivable only at the **Pewter Museum lab —
  which is exactly the blocked destination** (below). The player finds a treasure they can't
  use yet, and a concrete reason to return to Pewter later.
  - *Dials:* **Root Fossil** (`ITEM_ROOT_FOSSIL`, 99 → Lileep → Cradily) is the equally-good
    maritime alternative (a sea-lily anchored in the ancient shallows); the **Sinnoh** pair
    (**Skull Fossil**→Cranidos / **Armor Fossil**→Shieldon) if the migration should point at
    Sinnoh instead of Hoenn. All exist in the decomp; Pewter's revive script gets an entry
    for whichever is chosen.
- **The Pewter (Route 2) soft-wall:** Diglett's Cave's far exit warps toward **Route 2 /
  Pewter.** Block it — a guard or a rockfall or a posted notice — so the player can't leave
  Kanto by land through the northwest. Recommended framing: a **League/works notice**
  ("Route 2 closed for tunnel maintenance" / a Pewter-side checkpoint), consistent with the
  chapter's "the only way onward is the sea" logic and with Pewter being reserved for later.
  The player turns around and heads back to Vermilion — and the port.

### 7.6 Silver at the Port — The Ticket

The player returns to Vermilion and goes to the port to weigh their options: the S.S.
departures board lists Slateport, Olivine, Driftveil. And **Silver is there** — the
Champion, in person, wrapping up a quiet conversation with three lab-coated associates and
an executive.

Staging direction:

- Stage the scene at the **S.S. Aqua Vermilion port** — interior `386_T04R0301.json`
  (`P01R0103`, the reception/dock hall) and/or exterior `387_T04R0401.json` (`P01R0104`,
  the open dock: cranes, cargo, the maritime-hub visual). **Retarget the port interior's
  warp** (vanilla points back to Cerulean — a placeholder) so it serves the Vermilion
  departure, not the old Olivine ferry.
- **The associates dismissed:** 2-3 lab-coat NPC objects + an executive walk **off toward
  the cargo side** at Silver's gesture as the player enters — silent, unexplained, half-
  seen. Set them behind a one-shot so they're gone after (a `FLAG_APOC_CH7_*` hide).
- **Silver's beats** (full script in [CHAPTER7_SCENES_SPEC.md](CHAPTER7_SCENES_SPEC.md)):
  (1) congratulates the player — genuine, warm, notes the badges earned alone in a foreign
  region; (2) **probes about Mel** — light, twice, deniable, and *pointed*; (3) redirects
  them to **Hoenn** and presses over an **S.S. Ticket to Slateport** — effortless
  generosity from a man who can afford it. **No battle.** He leaves first; the player is
  left holding the ticket.
- **Grant `ITEM_S_S__TICKET`** (456) — reuse the vanilla S.S. Ticket key item, **retargeted
  as the Slateport boarding pass** (the S.S. "network" is the broader international loop, not
  just the Olivine ferry). Parallel to Ch5: the player still has **no `ITEM_PASS`** (the
  home-region Magnet Train pass) — Silver hands them a ship *away*, not a road home. The
  one-way logic holds. Set `FLAG_APOC_CH7_SILVER_DONE`.

### 7.7 Departure by Sea — Hand-off to Chapter 8

With the ticket, the player boards. The departure sequence is brief and cinematic: the
Vermilion skyline recedes, open water ahead.

Staging direction:

- Boarding warp from the port (the S.S. Aqua dock) → a short **departure cutscene** (skyline
  recedes; optional deck moment) → **Slateport arrival** (Chapter 8). The vessel is a
  working passenger/cargo ship on the international route (not a set-piece cruise — Vermilion
  is workmanlike; save the spectacle contrast for Slateport's chaos).
- Set `FLAG_APOC_CH7_DONE` on boarding for clean chapter tracking; hand control to **Chapter
  8 (Slateport City)**.
- Closing image: the port shrinking astern; somewhere behind the player, Silver making sure
  the people in lab coats clean up whatever the player almost saw.

## State And Files

Confirmed map/script targets (from `disasm/pokeheartgold`,
`include/constants/maps.h` and `files/fielddata/...`):

| Area | Map JSON | Map constant |
|------|----------|--------------|
| Route 6 (Saffron↔Vermilion, **spine**) | `011_R06.json` | `MAP_ROUTE_6` (14) |
| Route 6 checkpoint (Saffron south gate) | `R06R0201` | `MAP_ROUTE_6_SAFFRON_GATEHOUSE` (389) |
| Vermilion City | `051_T06.json` | `MAP_VERMILION` (54) |
| Vermilion Pokémon Center | `T06PC0101` | `MAP_VERMILION_POKECENTER_1F` (358) |
| Vermilion Mart | `T06FS0101` | `MAP_VERMILION_POKEMART` (360) |
| Trainers' Lodge (old Gym) | `322_T06GYM0101.json` | `MAP_VERMILION_GYM` (365) |
| International Exchange (old Fan Club) | `362_T06R0301.json` | `MAP_VERMILION_POKEMON_FAN_CLUB` (362) |
| Maritime History Museum (a house) | `363_T06R0401.json` | `MAP_VERMILION_CENTRAL_HOUSE` (363) |
| Fishing Dude House (kept) | `361_T06R0101.json` | `MAP_VERMILION_FISHING_DUDE_HOUSE` (361) |
| Route 11 (east to the cave) | `016_R11.json` | `MAP_ROUTE_11` (19) |
| Diglett's Cave | `103_D01R0101.json` | `MAP_DIGLETT_CAVE` (106) |
| S.S. Aqua Vermilion port (interior/dock hall) | `386_T04R0301.json` | `MAP_SS_AQUA_VERMILION_PORT_INTERIOR` (386) |
| S.S. Aqua Vermilion port (exterior/docks) | `387_T04R0401.json` | `MAP_SS_AQUA_VERMILION_PORT_EXTERIOR` (387) |

### Trainers & battles

**Reuse (vanilla `std_trainer` placements — re-line + re-team per
[KANTO_BATTLES.md](KANTO_BATTLES.md); keep placements):**

- **Route 6** (`011_R06.json`, 4 objects): `TRAINER_CAMPER_VIRGIL`,
  `TRAINER_PICNICKER_SELINA`, `TRAINER_TWINS_DAY_AND_DANI` (×2 objects = the **double
  battle**).
- **Route 11** (`016_R11.json`, 4 objects): `TRAINER_PSYCHIC_M_FIDEL`,
  `TRAINER_PSYCHIC_M_HERMAN`, `TRAINER_YOUNGSTER_OWEN`, `TRAINER_YOUNGSTER_JASON` — plus the
  **fisherman** (add a small placed trainer or reuse the coastal edge).
- **Trainers' Lodge** (`322_T06GYM0101.json`, 3 gym-trainer slots re-lined as travelers):
  `TRAINER_GUITARIST_VINCENT`, `TRAINER_JUGGLER_HORTON`, `TRAINER_GENTLEMAN_GREGORY`.
- **`TRAINER_LEADER_LT_SURGE_LT__SURGE`** (255) — **not used** this chapter (Surge relocated
  to Mauville; his Electric roster is available for a later Hoenn/Mauville cameo if wanted).
- **Diglett's Cave** — **no trainers** (keep vanilla's zero-trainer layout).

### Flags & vars

**Reuse (vanilla, already wired):**

- `give_badge <BADGE_*>` badge-check on the **Route 6 gate** (`R06R0201`) — Ch6's Requiem
  badge opens it automatically; write the **open** branch. No new unlock flag.
- `FLAG_HIDE_ROUTE_11_SNORLAX` (`0x261`) — keep the Snorlax **shown/asleep** as the Route 11
  branch-block (do *not* trip its wake flag; the flute quest is cut).
- Vanilla `T06` **Machop/Machamp follower** object — repurpose as the Museum's Machamp
  caretaker.
- Vanilla `T06` **Suicune / Eusine / Steven** events — leave **flag-hidden/unused** (not
  Apocrypha story).

**Item grants:**

- `ITEM_S_S__TICKET` (456) — Silver's gift at the port, **retargeted to Slateport**. The
  boarding key item for 7.7.
- `ITEM_PASS` (480) — **still never granted** (the Ch5 stranding rule persists; the player
  leaves by ship, not train).
- Diglett's Cave: the **fossil** (Helix/Dome/Old Amber — one), plus the re-tuned field items
  (see [KANTO_ITEMS.md](KANTO_ITEMS.md)).

**New custom flags to allocate** (assign to genuinely-free bits at build time — see the
allocation note; do **not** trust `FLAG_UNK_*` names as free):

- `FLAG_APOC_CH7_LAB_COATS_GONE` — the port associates dismissed (one-shot hide).
- `FLAG_APOC_CH7_SILVER_DONE` — the Silver port cutscene played + S.S. Ticket granted.
- `FLAG_APOC_CH7_FOSSIL_TAKEN` — the Diglett's Cave fossil one-shot.
- `FLAG_APOC_CH7_DONE` — chapter-complete (boarded the ship; hand-off to Ch8).

> **Flag-allocation note (repeat, important).** `FLAG_UNK_*` in `flags.h` means *un-named*,
> **not** *unused* — most are live vanilla flags referenced by maps/`src` (an audit found
> e.g. `FLAG_UNK_258` used by a Lavender Radio object; `FLAG_HIDE_ROUTE_11_SNORLAX` is a
> named, live flag). Assign new APOC flags only to bits verified **0-reference across
> `files/fielddata/` and `src/`**. The natural pool is the **vacated Team Rocket arc**
> (Radio-Tower takeover / Mahogany hideout — Apocrypha removes it; e.g.
> `FLAG_HIDE_ROCKET_HIDEOUT_*_MURKROW` at `0x24A–0x24D`, verified 0-reference) plus any
> `FLAG_UNK_*` confirmed 0-reference. See [[apocrypha-flag-allocation]]. The reused vanilla
> flags above are verified correct; new-flag hex is left to the build-time audit.

## Implementation Order

1. **Route 6 checkpoint + spine** — confirm the Requiem-badge check opens the `R06R0201`
   gate (write the open branch); re-line/re-team the 4 sight-trainers; Route 6 grass +
   coastal water table (the Wingull migrant); the descent to Vermilion. (`R06R0201`,
   `011_R06.json`)
2. **Vermilion city dress** — port-industrial retheme of `051_T06.json` (cranes, cargo,
   customs, warehouses); port-worker NPC chatter; keep Center/Mart; signpost the port;
   leave Suicune/Eusine/Steven hidden. (`scr_seq` for `T06`)
3. **Trainers' Lodge** — repurpose `322_T06GYM0101.json` (strip the puzzle, add bunks +
   travel-tips board); re-line the 3 trainer slots as travelers (import battles); the
   "Surge's in Mauville" note. (`T06GYM0101` script)
4. **Exchange + Museum** — Fan Club → International Exchange (`362_T06R0301.json`, trade/
   showcase NPCs, Chairman absent); a house → Maritime History Museum (`363_T06R0401.json`,
   the Machamp caretaker + the collection; leave the return-hook TODO).
5. **Route 11 + Diglett's Cave** — re-line/re-team the 4 R11 trainers + the fisherman; the
   lookout vista; the Snorlax branch-block; the cave wilds; the re-tuned items + **the
   fossil**; the **Pewter (Route 2) soft-wall.** (`016_R11.json`, `103_D01R0101.json`)
6. **Silver at the port** — stage `386_T04R0301.json` / `387_T04R0401.json`; retarget the
   port warp; the lab-coat walk-off (`FLAG_APOC_CH7_LAB_COATS_GONE`); Silver's three beats
   (congrats → Mel probe → ticket); grant `ITEM_S_S__TICKET`; set
   `FLAG_APOC_CH7_SILVER_DONE`. (port scripts)
7. **Departure** — boarding warp → departure cutscene (skyline recedes) → Slateport arrival;
   set `FLAG_APOC_CH7_DONE`; hand off to **Chapter 8.**
8. **Items pass** — see [KANTO_ITEMS.md](KANTO_ITEMS.md): the fossil, the re-tuned cave
   items, the S.S. Ticket, Vermilion Mart, Route 6/11 field items, the Fishing Dude rod.
9. **Battles pass** — see [KANTO_BATTLES.md](KANTO_BATTLES.md): Route 6/11 wilds + trainers
   (re-tuned up-then-capped to the band), the coastal Wingull migrant, the Lodge import
   battles, Diglett's Cave wilds.
