# Pokemon Apocrypha - Chapter 5 Build Spec

> Scope: Saffron City — Silph Co. lobby, the two Dojos, the city streets and exit
> gates. **No new badge, no gym, no required trainer battles.** This is the
> stranded-in-Kanto atmosphere chapter. Implementation-facing expansion of the
> Chapter 5 outline in `DESIGN.md`. Pairs with **[CHAPTER5_SCENES_SPEC.md](CHAPTER5_SCENES_SPEC.md)
> — the full line-by-line dialogue script** — and with the new region docs
> [KANTO_BATTLES.md](KANTO_BATTLES.md) and [KANTO_ITEMS.md](KANTO_ITEMS.md) (Saffron
> is the first Kanto location, so Kanto's battle/item tracking begins here). The
> "Sample lines" below are voice references; the complete script is in the scenes spec.

## Chapter Promise

Chapter 4 ended on momentum — the player swept into Saffron on a reporter's pass,
the door not yet closed behind them. Chapter 5 is where the door closes. **Mel
abandons the player** — not cruelly, just at velocity, bulldozing through Silph
security without ever noticing she left someone on the wrong side of it. The
Magnet Train won't take the player back (rail passes are home-region only; the
player's home region is Johto). So the player is **stranded in a foreign corporate
city, alone, with no plan and no way home.**

It isn't a crisis — the player is a capable trainer. It's a *disruption*. The plan
was Johto's gym circuit; now they're somewhere bigger and faster and colder, and
they have to figure out what a stranded trainer does. What they find is a city with
its own problems: two ancient dojos at each other's throats over a contested
Medicham, a brawl that escalates **far above a one-badge trainer's level**, and two
quiet titans — **Sabrina** and **Bruno** — who end it without raising their voices.
The player watches, learns where they stand in the world's power scale, gets
apologized to, and is gently told to move on. Every productive thing they try in
Saffron gets shut down by circumstance. So they pick a road out.

Core themes:

- **Abandonment by momentum.** Mel's exit is the payoff of everything Chapter 4
  planted: she is a force of nature, and forces of nature don't check on the people
  in their wake. No villainy, no betrayal — just being forgotten by someone moving
  too fast. The player learns who Mel is the hard way.
- **You are not ready for this.** Alakazam vs. Machamp, commanded by masters, is a
  wall the player can only watch. After being the hero of Slowpoke Well, this
  re-sets the scale: there are powers here the player can't touch yet.
- **Stranded, not helpless.** The tone is stuck-and-annoyed, not scared. The player
  has Pokémon and competence; what they lack is a *plan*. The chapter is about
  improvising one.
- **The corporate city quietly seeds the conspiracy.** Silph is aggressively normal
  on the surface — and every "normal" detail (a partnerships wall, an over-engineered
  train, a tired employee's "special projects") is a seed the later game harvests.
  Nothing is confronted; everything is noted.

## Progression Spine

| Beat | Maps | Purpose |
|------|------|---------|
| 5.1 The lobby and the parting | Silph Co. HQ lobby (`T11R0701`) | Explore the curated lobby; Mel bulldozes upstairs and is *gone*; the seeds (partnerships wall, train display, badge-locked elevators) |
| 5.2 Stranded | Magnet Train Station (`T11R0601`) | The rail-pass rule; no ride home; the stranding lands |
| 5.3 The dojo flashpoint | Saffron streets / plaza (`T11`), Fighting Dojo (`T11R0101`), "Psychic Dojo" = Saffron Gym (`T11GYM0101`) | Request a battle → the Medicham dispute erupts → the brawl → Alakazam vs. Machamp → **Sabrina & Bruno** end it |
| 5.4 City texture | Saffron streets, Copycat House (`T11R0801/02`), Center, café | Optional encounters: Copycat, the train engineer, a Hoenn trainer, a Silph worker, street performers |
| 5.5 Moving on | The four exit gatehouses (`R05/R06/R07/R08` Saffron-side) | The fork: N Cerulean **closed**, S Vermilion **League-gated**, W Celadon **open** (dead-end), E Lavender **open** |

Target start state: lead team ~lv 19-20, **1 badge (Hive)**, just off the Magnet
Train. Target end state: lead team ~lv 19-20 (no battles to grow on — this is a
pure story/atmosphere chapter), **still 1 badge**, no rail pass, choosing a road
out of Saffron toward Lavender (Chapter 6).

> **No combat this chapter.** Saffron is a city (no wild grass), both dojos are
> **closed for challenges** this visit, and the dojo clash is a **spectator** scene
> the player only watches. The exit routes (5–8) carry trainers, but those battles
> belong to **Chapter 6** — Chapter 5 ends at the gate the player chooses. See
> [KANTO_BATTLES.md](KANTO_BATTLES.md) §Chapter 5.

## Cast

### Mel (exit — the abandonment)

The Mel of Chapter 4, paid off. She marches the player to Silph, is polite at the
front desk for about three seconds, then her velocity takes over: questions the
receptionist can't field, credentials already out, through the security barrier and
into the elevator corridor before the guard is fully standing. **She doesn't say
goodbye. She doesn't realize there's a goodbye to say.** She's swallowed by the
building, chasing the story, operating on a frequency that doesn't include "check on
the kid." This is not a betrayal beat — it's a *character* beat. The player liked
her; now they understand her.

Voice: same rapid overlap as Chapter 4, but here it's pointed away from the player —
the camera, narratively, watches her recede.

Sample lines:

- "Research divisions. Executive access. Recent Johto partnerships — specifically
  the ones you don't list on the wall downstairs. I'll wait. No I won't —"
- *(over her shoulder, not to the player, to no one)* "Don't wait on me, I move
  fast —" *(she is already gone; the line wasn't even for them)*
- *(never delivered to the player at all — that's the point)*

### Silph receptionist & security (lobby)

Aggressively, professionally normal. The receptionist is trained to deflect without
ever seeming to; security is polite and immovable. Their job in the scene is to be
the *wall* — the calm institutional surface that closes seamlessly behind Mel and
leaves the player on the outside with an apology and nothing else.

Sample lines:

- **Receptionist:** "I'm so sorry — the upper floors aren't open to visitors.
  Your... colleague isn't either, technically, but she's already—" *(a tight,
  practiced smile)* "Can I get you a brochure?"
- **Security:** "Lobby's open till six. Everything above the lobby needs a badge.
  No exceptions, not even for press. *Especially* not for press."

### The two Dojo masters (the flashpoint)

Both unnamed institutional heads — proud, stretched thin, and quicker to anger than
they used to be (Saffron's been squeezed). The **Fighting Dojo master** (the Karate
King, `SPRITE_GSFIGHTER` in `T11R0101`) is gruff and physical; the **Psychic Dojo
master** (a senior psychic in the Saffron Gym, `T11GYM0101`) is cold and certain.
Each believes the contested **Medicham** is rightfully theirs. When the dispute
boils over they bring out **Machamp** and **Alakazam** — the "you are not ready for
this" beat — and are stopped only by their respective higher authorities.

Sample lines:

- **Fighting master:** "That Medicham trained its *body* in this dojo. Psychic tricks
  don't make a fighter — discipline does. It's ours."
- **Psychic master:** "Its mind woke up under our teaching. You taught it to punch.
  We taught it to *think*. Step back."

### Sabrina (introduction — perceptive, reserved)

The most powerful psychic in Kanto's history, here as an **institutional figure**,
not a gym leader (the gym/dojo is closed this chapter). She ends the brawl without a
word raised — her disappointment is quiet and devastating. She observes too much:
she may note something about the player — their Pokémon, their composure, something
a psychic catches that a normal person wouldn't. Not a plot beat — a *character*
moment that plants her for later. **She is not battled here.**

Voice: still, precise, a half-second too knowing. Says less than she sees.

Sample lines:

- "Enough." *(one word; the plaza goes quiet)*
- "You've come a long way to stand in the middle of someone else's argument."
  *(to the player, even, unreadable)* "...And you're carrying something heavier than
  your level. I won't ask. But I noticed."
- "Come back when this city remembers what these dojos were *for*."

### Bruno (introduction — warm, direct)

Of the Elite Four, here as the Fighting Dojo's institutional elder. A wall — massive,
composed, his sheer physicality enough to make students stand down. Where Sabrina is
ice, Bruno is a steady hand on the shoulder. He apologizes plainly, respects trainers
who travel, and can tell the player has already been through something. **Not battled
here.**

Voice: blunt, paternal, kind under the bulk.

Sample lines:

- "That's *enough.* You're black belts. Act like it." *(the Fighting side folds)*
- "Sorry you caught us at our worst, kid. The dojos have squabbled for generations,
  but this..." *(shakes his head)* "...this is new. The whole city's wound too tight
  lately."
- "You've got the look of someone a long way from home. Get some rest. Come back when
  it's quieter — I'll give you a real match."

### Saffron city texture (optional)

Each pulls double duty — flavor now, payoff later:

- **Copycat** (`T11R0802`): the famous mimic, still collecting dolls and imitating
  everyone. Asks for a specific item/Pokémon to imitate; rewards a TM or held item.
  Pure nostalgia and charm. (Reward specifics in [KANTO_ITEMS.md](KANTO_ITEMS.md).)
- **Off-duty Magnet Train engineer** (café near the station): grumbles that Silph's
  renovation "over-engineered" the train — more data collection than a train needs.
  Not suspicious, just annoyed. **Silph seed.**
- **Silph employee on break** (bench outside HQ): tired, the upper floors have been
  busy, lots of "special project" activity above their clearance. Not a whistleblower
  — a person with mundane complaints. **"Special projects" echoes later.**
- **Visiting Hoenn trainer** (Pokémon Center): passing through to Vermilion to catch a
  boat south; "everything in Kanto is so... *structured.*" Regional-identity flavor +
  a future-travel hint.
- **Street performers** (central square): a battle *exhibition* — flashy, theatrical,
  crowd reactions. Entertainment, not combat. Makes the city feel culturally alive.

### Gate guards (the fork)

- **Route 5 (north → Cerulean) guard:** apologetic — the route was closed after dojo
  students took their fight north of the city; not cleared yet. The player's *own
  experience* explains the block.
- **Route 6 (south → Vermilion) League checkpoint:** polite but firm — inbound port
  traffic needs Kanto trainer registration or a League travel permit; a Johto trainer
  has neither. A **Kanto gym badge** would serve as proof and open this later.

## Scene Details

### 5.1 Silph Co. — The Lobby and the Parting

Mel marches the player straight into Silph HQ (`359_T11R0701.json`). The lobby is
public-facing and curated: product display cases (Poké Balls, Silph Scopes, comm
devices), a guided-tour spiel, a polished receptionist (`SPRITE_GSWOMAN6` slot) and
security (`SPRITE_POLICEMAN` slot). Aggressively normal.

Staging direction:

- **Free explore the lobby first.** Three details reward attention and are the
  chapter's quiet conspiracy seeds:
  1. a **"community partnerships" donations wall** listing Silph's partner sites —
     several of which the player will *later* recognize as compromised (the Ruins of
     Alph, others). Read-only flavor object now.
  2. a **Magnet Train display** boasting Silph-engineered systems (pairs with the
     engineer's "over-engineered" grumble in 5.4).
  3. a **badge-locked elevator bank** to the upper floors — visibly gated, the door
     the player can't pass.
- **The parting:** Mel approaches the desk, is polite for a beat, then accelerates —
  questions, credentials, past the barrier, into the elevator corridor, *gone*,
  before security finishes reacting. No farewell, no "wait here." She doesn't notice
  she's left the player. Drive with `apply_movement` (Mel walks briskly off-map /
  into the locked corridor) + the receptionist's apology; **do not** give her an exit
  line directed at the player — the absence is the point.
- The player is left on the wrong side of the barrier. Security closes ranks; the
  receptionist apologizes; there's no confrontation to have. Set
  `FLAG_APOC_CH5_SILPH_PARTING_DONE`.
- The vanilla lobby ships a `SPRITE_DAIGO` (Steven) slot gated
  `FLAG_HIDE_SAFFRON_CITY_STEVEN` — **leave it hidden/unused** this chapter (no Steven
  cameo here; keep the lobby's cast to receptionist + security for focus).

### 5.2 Stranded — The Rail Pass Rule

The player returns to the Magnet Train Station (`357_T11R0601.json`; attendant =
`SPRITE_POLICEMAN`). The attendant is polite but absolute.

Staging direction:

- The rule: the Magnet Train requires a **rail pass**, and passes are sold **only in
  the holder's home region**. The player's home is **Johto**; they're in **Kanto**.
  No workaround, no exception, no "but a reporter brought me." **No pass, no ride.**
- Keep it un-dramatic — this is a *rule*, not a quest. The attendant isn't a villain;
  he's just doing his job. Set `FLAG_APOC_CH5_STRANDED`.
- This is the clean mechanical lock that keeps the player in Kanto. (The vanilla
  `ITEM_PASS` is never granted — consistent with Chapter 4 withholding it. Do not
  introduce a way to buy one in Kanto.)
- Tone: stuck and slightly annoyed, not afraid. A short internal beat / line sells
  "okay. New plan. What now."

### 5.3 The Competing Dojos — Spectator Flashpoint

With Silph closed and no ride home, the player explores and wanders into one of the
two dojos to ask for a battle. The dojos are the **Fighting Dojo** (`T11R0101`) and
the **"Psychic Dojo"** (Apocrypha's framing of the **Saffron Gym**, `T11GYM0101`).

Staging direction:

- The player approaches a dojo master to request a battle (either dojo — the scene is
  symmetric). Just as it's about to begin, a junior bursts in: **the other dojo is
  trying to take the Medicham.** The master drops everything and rushes to the plaza;
  the player follows.
- **The Medicham** (`SPECIES_MEDICHAM`, Psychic/Fighting) is the contested object —
  it belongs to both disciplines and neither. Stage it in the plaza center, distressed.
- **The brawl:** students squaring off — Abra/Kadabra vs. Machop/Machoke — messy and
  heated, a scrum of punches and psychic flashes. Use the dojo crowd sprites (the
  Fighting Dojo's ~16 `GSLEADER*`/`GSFIGHTER` slots; the gym's psychic-trainer slots)
  relocated/placed in the plaza as a one-time scripted tableau. **No player battles.**
- **The escalation:** the two masters arrive and bring out **Machamp** (Fighting
  master) and **Alakazam** (Psychic master). The plaza clears — everyone realizes this
  is about to get serious. The player can only watch: this is **well above a one-badge
  trainer.** Establish the power scale; let the player feel small.
- **Sabrina & Bruno end it.** They walk up together and stop it without violence —
  Sabrina's quiet "Enough," Bruno's blunt "That's *enough.*" Students disperse, the
  Medicham is retrieved, the masters recall their heavyweights, chastened. Sabrina's
  slot can reuse `FLAG_HIDE_SAFFRON_GYM_SABRINA` (relocated to the plaza for the
  scene); Bruno needs a sprite placed for the beat.
- **The introductions:** they notice the player — a young trainer caught in someone
  else's fight. They explain: the dojos have always been rivals (mind vs. body), but
  the tension's gotten worse because **Saffron's resources are tighter — Silph's
  expansion has eaten the city's public infrastructure**, and both dojos feel
  squeezed. The Medicham was a flashpoint, not the cause. Sabrina observes the player
  (the "carrying something heavier than your level" beat); Bruno apologizes warmly and
  tells them to come back when it's calmer.
- **Both dojos are closed for the day.** No battles, no challenges — the player's
  attempt to be productive is shut down again. Set `FLAG_APOC_CH5_DOJO_INCIDENT_DONE`
  (covers Sabrina + Bruno introductions; they should not re-trigger).
- **Note (Sabrina/Bruno not battled):** their trainer slots
  (`TRAINER_LEADER_SABRINA_SABRINA`, `TRAINER_ELITE_FOUR_BRUNO_BRUNO`) and the dojo
  juniors exist but are **spectator-only** here. No `trainer_battle` calls this
  chapter. See [KANTO_BATTLES.md](KANTO_BATTLES.md).

### 5.4 City Texture and Small Events (optional)

With Silph inaccessible and the dojos closed, the player explores at their own pace.
All optional; all double-duty (flavor + later payoff). Full lines in the scenes spec;
cast summarized above. Place these as ordinary talk-to NPCs using Saffron's
`FLAG_NOTHING` flavor slots (`056_T11.json` ships ~10) plus the Copycat house
(`T11R0801/02`) and the Pokémon Center interior.

- Copycat (reward beat — TM/held item; see [KANTO_ITEMS.md](KANTO_ITEMS.md)).
- Magnet Train engineer (Silph seed). Silph employee on break (special-projects seed).
- Hoenn trainer (regional identity + future-travel hint). Street performers (city life).

### 5.5 Moving On — The Exit Fork

Four gates, two open. The player chooses; both open paths converge on Lavender
(Celadon is a dead-end for now). This is the game's **first meaningful directional
fork**, even though the paths reconverge.

Staging direction:

- **North → Cerulean (Route 5 gatehouse, `R05R0301`):** **Closed.** Guard: students
  took their fight north and the route isn't cleared. Block with a guard-NPC + a
  re-pointed/withheld warp; gate on a new `FLAG_APOC_CH5_ROUTE5_CLOSED`-style flag (or
  reuse a vanilla Saffron route-block flag if one is free). The player's own
  experience (5.3) explains it.
- **South → Vermilion (Route 6 gatehouse, `R06R0201`):** **League checkpoint.** Guard:
  inbound port traffic needs Kanto registration / a League travel permit; a Johto
  trainer has neither. **A Kanto gym badge opens this later.** Polite, firm, logical.
- **West → Celadon (Route 7 gatehouse, `R07R0101`):** **Open.** Short walk west;
  Celadon is a **dead-end for now** (Cycling Road blocks the through-route) — Chapter 6
  treats Celadon as optional.
- **East → Lavender (Route 8 gatehouse, `R08R0201`):** **Open.** East toward Lavender
  through a route with trainers at the player's level — **Chapter 6** content.
- Set `FLAG_APOC_CH5_DONE` when the player passes either open gate, handing off to
  Chapter 6. Behind them, Silph's tower catches the afternoon light — Mel is in there
  somewhere, getting the story of a lifetime or getting arrested; the player may never
  find out which.

## State And Files

Confirmed map/script targets (from `disasm/pokeheartgold`,
`include/constants/maps.h` and `files/fielddata/...`):

| Area | Map JSON | Script | Map constant |
|------|----------|--------|--------------|
| Saffron City | `056_T11.json` | `scr_seq_0827_T11.s` | `MAP_SAFFRON` (59) |
| Silph Co. HQ (lobby) | `359_T11R0701.json` | `scr_seq_0837_T11R0701.s` | `MAP_SAFFRON_SILPH_CO_HQ` (402) |
| Magnet Train Station 1F | `357_T11R0601.json` | `scr_seq_0834_T11R0601.s` | `MAP_SAFFRON_MAGNET_TRAIN_STATION_1F` (400) |
| Fighting Dojo | `355_T11R0101.json` | `scr_seq_0832_T11R0101.s` | `MAP_SAFFRON_FIGHTING_DOJO` (398) |
| "Psychic Dojo" (= Saffron Gym) | `366_T11GYM0101.json` | `scr_seq_0829_T11GYM0101.s` | `MAP_SAFFRON_GYM` (410) |
| Copycat House 1F / 2F | `361_T11R0801.json` / `362_T11R0802.json` | `scr_seq_0840` / `scr_seq_0841` | `MAP_SAFFRON_COPYCAT_HOUSE_1F/2F` (404/405) |
| Mr. Psychic's House | `356_T11R0501.json` | — | `MAP_SAFFRON_MR_PSYCHIC_HOUSE` (399) |
| Saffron Pokémon Center 1F | `363_T11PC0101.json` | `scr_seq_0830_T11PC0101.s` | `MAP_SAFFRON_POKECENTER_1F` (407) |
| Saffron Mart | `365_T11FS0101.json` | `scr_seq_0828_T11FS0101.s` | `MAP_SAFFRON_POKEMART` (409) |
| Route 5 Gatehouse (N→Cerulean, **closed**) | `R05R0301` | `scr_seq_0182_R05R0301.s` | `MAP_ROUTE_5_SAFFRON_GATEHOUSE` (391) |
| Route 6 Gatehouse (S→Vermilion, **League-gated**) | `R06R0201` | `scr_seq_0185_R06R0201.s` | `MAP_ROUTE_6_SAFFRON_GATEHOUSE` (389) |
| Route 7 Gatehouse (W→Celadon, **open**) | `R07R0101` | `scr_seq_0187_R07R0101.s` | `MAP_ROUTE_7_SAFFRON_GATEHOUSE` (493) |
| Route 8 Gatehouse (E→Lavender, **open**) | `R08R0201` | `scr_seq_0189_R08R0201.s` | `MAP_ROUTE_8_SAFFRON_GATEHOUSE` (390) |

### Flags & vars

**Reuse (vanilla, already wired):**

- `FLAG_HIDE_SAFFRON_GYM_SABRINA` (`0x2F1`) — Sabrina's sprite; relocate to the plaza
  for the 5.3 break-up scene, then hide.
- `FLAG_HIDE_SAFFRON_CITY_STEVEN` (`0x2FA`) — the lobby `SPRITE_DAIGO` slot; **leave
  hidden** (no Steven this chapter).
- `FLAG_HIDE_SAFFRON_CITY_COPYCAT_HOUSE_CLEFAIRY_DOLL` (`0x2FB`) — keep the Copycat
  doll-collection flavor intact.
- Saffron flavor NPC slots (`056_T11.json`, all `FLAG_NOTHING`) — dress the city /
  city-texture beats.
- Fighting Dojo crowd slots (`GSFIGHTER` + ~16 `GSLEADER*` in `T11R0101`) and the
  Saffron Gym psychic-trainer slots (`MEDIUM_DARCY/REBECCA`, `PSYCHIC_M_JARED/FRANKLIN`)
  — repurpose as the brawl tableau; **do not** wire them as `trainer_battle` (closed).
- `ITEM_PASS` (`480`) — **never granted in Kanto** (the stranding lock).

**New custom flags to allocate** (5 one-shots — assign to genuinely-free bits at build
time; see the allocation note below — **do not** trust `FLAG_UNK_*` names as "free"):

- `FLAG_APOC_CH5_SILPH_PARTING_DONE` — lobby explore + Mel's exit one-shot.
- `FLAG_APOC_CH5_STRANDED` — rail-pass denial / stranding realization.
- `FLAG_APOC_CH5_DOJO_INCIDENT_DONE` — the brawl + Sabrina/Bruno intro one-shot (covers
  both introductions).
- `FLAG_APOC_CH5_ROUTE5_CLOSED` — north-gate (Cerulean) closure state; clear it whenever
  Route 5 is later opened.
- `FLAG_APOC_CH5_DONE` — chapter-complete one-shot (player passes an open gate); hands
  off to Chapter 6.

> **Flag-allocation note (applies to all APOC chapters).** `FLAG_UNK_*` in `flags.h`
> means *un-named*, **not** *unused* — most are live vanilla flags referenced by maps
> (e.g. `FLAG_UNK_258` is used by a Lavender Radio object). Assign new APOC flags only
> to bits that are **0-reference across `files/fielddata/` and `src/`**. The natural
> pool is the **vacated Team Rocket arc** — Apocrypha removes the Radio-Tower takeover
> and the Mahogany hideout, freeing that whole flag block (e.g. the
> `FLAG_HIDE_ROCKET_HIDEOUT_*_MURKROW` set at `0x24A–0x24D`, verified 0-reference) —
> plus any `FLAG_UNK_*` confirmed 0-reference (e.g. `0x25E`). Audit at build time; the
> specific hex isn't pinned here on purpose.

> The south gate (Vermilion / Route 6) does **not** need a new "closed" flag — it's a
> **conditional** check (player has no Kanto badge), so gate it on badge state, not a
> one-shot. It re-opens automatically once a Kanto badge is earned.

**New custom var:** none required — Chapter 5 is linear and the five flags above
cover its ordering. (If the optional city events ever need sequencing, a free `0x40xx`
var can be added, but it isn't needed for the spine.)

## Implementation Order

1. **Silph lobby** — dress the curated lobby (display cases, tour spiel,
   receptionist + security); place the three seed objects (partnerships wall, train
   display, badge-locked elevators); script **Mel's bulldoze-and-vanish** (no farewell
   line); the receptionist's apology; set `FLAG_APOC_CH5_SILPH_PARTING_DONE`.
   (`scr_seq_0837_T11R0701.s`)
2. **Stranding** — the Magnet Train attendant's rail-pass rule; set
   `FLAG_APOC_CH5_STRANDED`. (`scr_seq_0834_T11R0601.s`)
3. **Dojo flashpoint** — the request-a-battle interruption; the plaza brawl tableau;
   Machamp/Alakazam escalation; **Sabrina & Bruno** break it up and introduce
   themselves; both dojos close; set `FLAG_APOC_CH5_DOJO_INCIDENT_DONE`. Spectator
   only — no `trainer_battle`. (`scr_seq_0827_T11.s`, `scr_seq_0832_T11R0101.s`,
   `scr_seq_0829_T11GYM0101.s`)
4. **City texture** — Copycat reward beat; the engineer / employee / Hoenn-trainer /
   street-performer flavor NPCs. (`scr_seq_0841_T11R0802.s` + Saffron/Center scripts)
5. **Exit fork** — Route 5 closed (guard + block, `FLAG_APOC_CH5_ROUTE5_CLOSED`);
   Route 6 League checkpoint (badge-conditional); Routes 7/8 open; set
   `FLAG_APOC_CH5_DONE` on exit. (`scr_seq_0182/0185/0187/0189_R0x...`)
6. **Items pass** — see [KANTO_ITEMS.md](KANTO_ITEMS.md): Saffron Mart stock, the
   Copycat reward, lobby flavor items / hidden items, and the **rail-pass-unbuyable**
   note.
7. **Battles pass** — see [KANTO_BATTLES.md](KANTO_BATTLES.md): confirm **no required
   battles**; record the spectator showcase (Alakazam/Machamp, Sabrina/Bruno) as
   flavor; note the exit-route trainers are Chapter 6.
