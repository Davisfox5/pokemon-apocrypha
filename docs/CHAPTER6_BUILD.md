# Pokemon Apocrypha - Chapter 6 Build Spec

> Scope: Route 7 + **Celadon City (optional)**, Route 8, **Lavender Town** and
> **Eve's Ghost gym (2nd badge — first Kanto badge)**, unlocking Vermilion. This is
> the implementation-facing expansion of the Chapter 6 outline in `DESIGN.md`. Pairs
> with **[CHAPTER6_SCENES_SPEC.md](CHAPTER6_SCENES_SPEC.md) — the full line-by-line
> dialogue script** — and with [KANTO_BATTLES.md](KANTO_BATTLES.md) (encounters +
> trainers + the gym) and [KANTO_ITEMS.md](KANTO_ITEMS.md) (items + marts + services).
> The "Sample lines" below are voice references; the full script is in the scenes spec.

## Chapter Promise

After the cold of Saffron, Chapter 6 lets the player breathe *and* gives them their
footing back. Two Kanto cities that have both **moved on from what they used to be**:
**Celadon**, a green, walkable, livable place that rebuilt itself into an open-air
market and gardens; and **Lavender**, the old ghost-town, now a **broadcast hub**
humming with antennas and ambition, aggressively determined to prove it's past its
haunted history. The player, freshly stranded and improvising, starts to do the same
thing these cities did — move on, make the best of it, find a way forward.

The forward is a **badge.** In a converted annex that leans into everything the rest
of Lavender is trying to forget, **Eve** — Agatha's granddaughter, a dry, sharp Ghost
specialist — runs the one gym in town. Beating her earns the player's **second badge,
their first in Kanto**, which is exactly the credential the Route 6 checkpoint wanted:
the road south to **Vermilion and its ships** opens. The player isn't stranded
anymore. They *chose* a way out.

Core themes:

- **Cities that moved on.** Celadon rebuilt after Rocket; Lavender rebranded away from
  death. Both wear their reinvention as identity. The player, mid-reinvention
  themselves, is walking through the answer to their own situation.
- **The world is full of specialists with lives.** Celadon's gardens are a crossroads
  for Erika (plants), Janine (poisons), and Aaron (bugs); the hotel holds a bored
  international cop; the café has a guilty Fan Club Chairman. None are plot — all are
  *people*, and several are quiet seeds.
- **The past isn't as buried as the town wants.** Eve's gym is a deliberate pocket of
  old Lavender inside new Lavender; the peripheral cemetery still holds Mr. Fuji,
  Agatha, and a grieving Alder. The town paved over its ghosts; Eve, and the graves,
  are what it couldn't quite pave.
- **Earning your way out.** The badge is a credential, not a trophy — it literally
  unlocks the checkpoint. The player stops being *stuck* and starts *traveling*.

## Progression Spine

| Beat | Maps | Purpose |
|------|------|---------|
| 6.0 Route 8 east | Route 8 (`R08`) | The spine road to Lavender; 7 sight-trainers; wilds; the level climb toward the gym |
| 6.1 Celadon (optional) | Route 7 (`R07`), Celadon (`T07`) + interiors | Market/services, gardens (Erika/Janine/Aaron), hotel (Looker), café quest, Game Corner; **Cycling Road dead-end** |
| 6.2 Lavender arrives | Lavender Town (`T05`) | The reinvented broadcast town; texture; the tower |
| 6.3 The broadcast tower | Lavender Radio Station (`T05R0701`) | Mary (seen, unnamed); lobby battles; Fantina; the TV exhibition side quest |
| 6.4 Eve — the Ghost gym | host building in Lavender (`T05R0201`/`0601`) | The 2nd badge; Gen-1 ghost roster; the Marowak anchor |
| 6.5 The cemetery | House of Memories (`T05R0601`) / north edge | Mr. Fuji & Agatha memorials; **Alder** and his grief; the Unova seed |
| 6.6 Moving on | Route 6 checkpoint (`R06R0201`) | The Kanto badge opens Vermilion; the road south to the ships |

Target start state: lead team ~lv 19-20, **1 badge (Hive)**, just out of Saffron.
Target end state: lead team ~lv 21-22, **2 badges (Hive + Eve's Ghost badge)**,
Route 6 (Vermilion) checkpoint **open** — Chapter 7 heads to the port.

> **Level note (post +3 curve lift).** The player leaves Saffron ~lv19-20 (Ch5 had no
> battles). Route 8's trainers + wilds and the optional Celadon content carry them to
> ~lv20-22 for Eve, whose ace sits at **lv22** — a fair +1-2 over a prepared team.
> Eve was authored already on the lifted **badge 2 ≈ lv22** line, so she's unchanged;
> the routes lift up to meet her. See [KANTO_BATTLES.md](KANTO_BATTLES.md).

## Cast

### Celadon (optional)

**Daisy Oak — the salon (market services building).** Blue's older sister; warm,
gentle, uninterested in the trainer life that consumed her brother and grandfather.
She grooms and pampers Pokémon (friendship/condition boost). Recognizes a Johto kid
and is kind about it. FRLG players get a nostalgia hit; everyone else just meets a
lovely person who loves Pokémon a *different* way than battlers do.
- *"You battle them, that's fine, that's lovely — but have you ever just... brushed
  one? Sat with it? Here. Sit. I'll show you what it does to a tired little heart."*

**Erika — the Botanical Gardens (old gym site).** Not running a gym anymore — tending
something she cares about more. Gracious, genuinely interested in a young traveler.
May comment on the Saffron dojo mess (local knowledge, grounding the player's recent
week). Gives a **botanical gift** (a rare berry / nature-themed held item).
- *"I traded a gym for a garden and I have never once regretted it. Things grow here.
  That's more than most badges ever gave me."*

**Janine — in the gardens (poison/plant research).** Koga's daughter, former Fuchsia
leader; studying poisonous plants and Poison-type biology with Erika's specimens.
Quiet, precise, ninja-trained. Her collegial exchange with Erika shows the player two
former leaders as *colleagues*, not rivals.
- *"Poison isn't cruelty. It's chemistry that hasn't been understood yet. Erika grows
  the questions; I answer them."*

**Aaron — in the gardens (Sinnoh Elite Four, Bug specialist).** Visiting Kanto to
study Bug-types in a different biome. Young, enthusiastic, talks about bugs the way
some people talk about music — infectious, slightly overwhelming. **May challenge the
player to a casual battle** (team scaled to the player's level; roster in BATTLES).
- *"You have GOT to see the Bug diversity these gardens pull in — species I can't find
  in ALL of Sinnoh! Oh — do you battle? Quick one? Please? I'll go easy. I won't. But
  I'll say I will!"*

**The bored cop (Looker — unnamed) — Pokémon Hotel, upstairs room.** An international
police officer, files everywhere, cold coffee. Frustrated: since Silver took over as
Champion, organized crime in the Johto-Kanto corridor has *vanished*. He laughs
ruefully — *"Who'd have thought the son of the leader of the greatest evil
organization in history would grow up to be the hero of the Pokémon world?"* — with
**genuine admiration, not suspicion.** Bored, not paranoid. The player meets him and
forgets him. (Until much later.) **Name never given.**

**Pokémon Fan Club Chairman — the café (quest catalyst).** Traveled from Vermilion for
the food; has been holding a corner table hostage talking about his Rapidash while the
too-polite owner falls behind on prep for a special event. Feels guilty; sends the
player to source the missing ingredient (a short NPC-chain fetch). Reward: a
**food-themed TM/held item** (recommend **TM88 Pluck** — a move about taking someone
else's food, learned at a café; **not** Leftovers, too strong now). Then he goes right
back to talking about Rapidash.

### Lavender

**Mary — the broadcast director (seen, never named).** Behind the production-floor
glass: headphones around her neck, clipboard, brisk cheerful authority keeping a live
broadcast running. Too busy to notice the player. GSC players recognize the former
Goldenrod Radio personality instantly; the game **never says her name.** It doesn't
need to.

**Fantina — the tower lobby (Sinnoh Ghost specialist / Contest star).** Flamboyant,
theatrical, purple everything, an accent that makes everything a performance. Visiting
Lavender to see **Eve** (the Ghost-specialist community is small; she takes a personal
interest in Agatha's granddaughter). She and Eve are a study in contrasts — Fantina
all spectacle, Eve all understatement. Fantina gushes about Eve's talent (which Eve
would find mortifying) and plants a **Sinnoh seed** without forcing anything.
- *"Ahh, a traveler! You must — you MUST — see our Eve battle. Such *restraint*. Such
  *dread*. She is a POEM and she refuses to know it. It drives me to despair!"*

**Eve — Agatha's granddaughter, the Ghost Gym leader (the badge).** Young — older than
the player, not by much. Sharp, dry, confident in the way of someone who grew up in a
famous person's shadow and decided she's fine with it. Not grim or morbid — she finds
it *funny* that she's a Ghost specialist in a town rebranding away from ghosts. She's
the living reminder that Lavender's past isn't as buried as the council would like. She
heard about the stranded Johto kid (small town) and respects that they're *making the
best of it* rather than sulking in the Center.
- *"Everybody wants Lavender to be about antennas now. Fine. Somebody's got to keep the
  lights off in one building."*
- *"You got stranded and you went and found the one gym in town instead of crying about
  it. I respect that. Let's see if the respect survives the battle."*
- (post-badge, matter-of-fact) *"That badge'll get you through the Vermilion checkpoint.
  Ships from there go everywhere. If you're trying to get home — that's your road. If
  you're not..." (a shrug) "...there's a lot of world out there."*

**Alder — the cemetery (former Unova Champion).** Older, weathered, thoughtful. Stands
quietly among the graves — not at any marker, just present. Traveling between regions
visiting places where Pokémon are laid to rest, trying to outwalk grief for his first
partner. Says it plainly, no self-pity. His being here quietly **explains his absence
from Unova** during concurrent events and gives the player an early signal that
*something is happening in Unova too.*
- *"I thought if I visited enough of these places, I'd stop feeling it. Hasn't worked
  yet. But the walking helps. ...You've got that look too. Younger version of it."*

**Memorials (no battles, no ghosts).** Mr. Fuji's stone (*a true lover of people and
Pokémon*; fresh flowers — someone still tends it). **Agatha's** marker nearby (her
granddaughter carries the legacy her own way; the grave is a grave, not a shrine). A
few other old trainers and beloved Pokémon. A place where the dead are remembered by
anyone who bothers to walk up the hill.

**TV producer — the tower lobby (exhibition side quest).** Stressed: a battle segment
fell through, the slot's locked, they need a replacement *now*. If the player agrees,
they fight 2-3 studio battles while a **commentator oversells everything** ("AN
ABSOLUTELY DEVASTATING TACKLE! THE CROWD IS ON THEIR FEET!" — there is no crowd, there
is one cameraman). Reward: prize money + a useful item; the segment airs later (NPCs
elsewhere may reference "that kid from Johto" on TV).

## Scene Details

### 6.0 Route 8 — The Road East (the spine)

Route 8 runs east from Saffron to Lavender — the required path (Celadon is the
optional western detour). More trainers and slightly higher levels than the Celadon
side; landscape loosening from urban sprawl toward open country.

Staging direction:

- **Seven sight-trainers, already placed** in `013_R08.json` via `std_trainer`:
  Bikers `DWAYNE`, `HARRIS`, `ZEKE` (`SPRITE_GANG`), Super Nerds `SAM`, `TYRONE`, the
  **Young Couple `MOE_AND_LULU`** (a built-in **double battle**), and Gentleman
  `MILTON`. Re-line them as Kanto-corridor locals; rosters/levels in
  [KANTO_BATTLES.md](KANTO_BATTLES.md). This is the chapter's level engine.
- Keep it a clean climb: ~lv 17-19 trainers pulling a ~lv17 arrival up toward the gym.
- Wild table (Route 8) + any item balls in [KANTO_BATTLES.md](KANTO_BATTLES.md) /
  [KANTO_ITEMS.md](KANTO_ITEMS.md). Apply the whole-game **re-tune-down** discipline —
  vanilla Kanto Route 8 is endgame-leveled; Apocrypha pulls it to the badge-2 band.

### 6.1 Celadon City — Optional Detour

Route 7 (west from Saffron) is short and trainer-light; Celadon opens beyond it.
**Everything here is optional** — a reward for curiosity, not progression. Celadon is
everything Saffron isn't: pedestrian plazas, tree-lined streets, visible civic pride
(it rebuilt after Rocket's original occupation and wears the recovery as identity).

Staging direction:

- **The Market** (repurpose the vanilla Dept Store `T07R0101…` + the plaza): reframe as
  an **open-air market + services building** — fewer item vendors, more **services**:
  **Daisy Oak's salon** (friendship/condition), a **move tutor**, and an **EV-training
  facility** (pay-to-train stat sessions). Bazaar, not mall. Details/stock in
  [KANTO_ITEMS.md](KANTO_ITEMS.md).
- **The Pokémon Hotel** (repurpose the **Condominiums** `T07R0201-0205`): two explorable
  stories — furnished suites, a lobby lounge, cross-region travelers. Optional battlable
  trainers, a rare-Pokémon collector, a couple arguing about regional food, and — upstairs
  — the **bored cop (Looker)**. (Place trainers using the condo slots; the Looker beat is
  a talk-to script.)
- **The Botanical Gardens** (repurpose the vanilla **Celadon Gym** `T07GYM0101`, the old
  Erika gym): now a public garden, **not a gym challenge**. **Erika** tends it (reuse the
  `FLAG_HIDE_CELADON_GYM_ERIKA` leader slot); **Janine** and **Aaron** are here too.
  Re-line the vanilla gym's placed trainers (`TWINS_JO_AND_ZOE` [double], `LASS_MICHELLE`,
  `PICNICKER_TANYA`, `BEAUTY_JULIA`) as garden visitors — most non-battle, but **Aaron's
  casual battle** can reuse one of these slots (roster in BATTLES). Erika's botanical
  **gift**; the Erika/Janine collegial exchange.
- **The Café** (repurpose the **Restaurant** `T07R0701`): the **Fan Club Chairman** quest
  catalyst → short ingredient fetch → **TM88 Pluck** reward. Self-contained.
- **The Game Corner** (`T07SP0101`): still operational — slots + prizes; optional fun.
- **The Cycling Road dead-end:** heading south, the gate guard (Route 16 gatehouse,
  `R16R0201`) delivers the deliberately-casual line — *"It's probably an outdated rule at
  this point, but it's always been policy that you must have a bike on Cycling Road.
  You'll have to come back with a bicycle."* Dead end; the player backtracks through
  Saffron to Route 8. (No bike this chapter.)
- Celadon is a **reward, not a requirement** — the skipping player misses charm, not
  progression. No flag gating beyond the individual quest/gift one-shots.

### 6.2–6.3 Lavender Town + The Broadcast Tower

East of Route 8, Lavender opens — and it's **busy.** Not the somber village of twenty
years ago: the old Pokémon Tower is **fully converted into a broadcast center** (radio,
podcast, TV for all Kanto), bristling with antennas and dishes, production vans outside.
The town runs on **media and work** — engineers, producers, sound techs, on-air talent
grabbing coffee. Forward-looking and a little too determined to prove it's moved on.

Staging direction:

- Dress `050_T05.json` toward industry/media (retheme the vanilla mournful NPC chatter
  to techs/producers). The graveyard is pushed to a small peripheral cemetery (6.5).
- **The Broadcast Tower** = **Lavender Radio Station** (`394_T05R0701.json`): public
  lower floors — visitor center/lobby, media-history displays, live-feed screens, a gift
  shop; upper floors restricted. **Mary** is visible through the production glass, too
  busy to talk (reuse the `FLAG_HIDE_LAVENDER_RADIO_TOWER_DIRECTOR` slot; **never named**).
- **Lobby battles:** a few media interns / off-duty techs who battle for fun between
  shifts. (The radio station's vanilla objects are scripted NPCs, not `std_trainer` —
  place a couple of small trainer objects here at build, or reuse Route-8 archetypes;
  rosters in BATTLES.)
- **Fantina** in the lobby — visiting Eve; the flamboyant-vs-understated contrast; the
  Sinnoh seed.
- **The TV exhibition side quest** — the stressed producer; 2-3 studio battles with an
  overselling commentator; prize money + item; the "seen on TV" callback. Roster in
  BATTLES.

### 6.4 Eve — The Ghost Gym (2nd badge, first Kanto badge)

Lavender has **no vanilla gym map** — Eve's gym is hosted in a **repurposed Lavender
building**, a "converted annex of the old tower" that leans into the town's original
identity. Inside, the atmosphere flips: dark, quiet, deliberately eerie, Ghost-types
drifting the corridors — a pocket of *old* Lavender inside the new media town.

Staging direction:

- **Host map (build decision):** recommend the **Volunteer Pokémon House**
  (`390_T05R0201.json`) reframed as the gym annex, with the **House of Memories**
  (`393_T05R0601.json`) reserved for the cemetery/memorial beats (6.5). Add a gym warp +
  Eve's leader object to the chosen host; there is no vanilla `MAP_LAVENDER_GYM` to reuse.
- **Eve's roster — deliberately Gen-1 Kanto ghosts only:** Haunter, Marowak, a second
  Haunter, **Gengar** (ace). The small roster is the *point* — Gen 1 barely had Ghost
  types and the gym leans into that limitation; it also marks Eve as a **traditionalist**
  (no cross-region imports — the anti-Inter-Regional-Exchange statement, in character).
  **Marowak** is the emotional anchor (the Lavender Tower mother; Eve never explains the
  reference — she doesn't need to). Full roster/tuning in [KANTO_BATTLES.md](KANTO_BATTLES.md).
- **The fight tests non-straightforward battling** — immunities (Normal/Fighting vs
  Ghost), status, curses, indirect pressure. Eve is patient and punishing: she lets the
  player make mistakes and capitalizes. Beating her should feel *earned*.
- **On win:** award the **2nd badge (first Kanto badge)** — the **Requiem Badge**
  (confirmed name; DESIGN calls it "the Ghost badge"). Engine `give_badge <BADGE_*>`;
  the exact `BADGE_*` constant is deferred to the whole-game **badge-order pass** (the
  Saffron/**Marsh** bit is a natural candidate, freed by Saffron's gym being reframed as
  the closed Psychic Dojo). Reward TM: **TM30 Shadow Ball** (the vanilla Ghost-gym
  precedent — Morty gives it; earned, not bought). Set `FLAG_APOC_CH6_BADGE_DONE`.
- Eve's post-badge line points the player at the Route 6 checkpoint + the Vermilion ships
  (6.6). No rivalry — she's a peer who respects them.

### 6.5 The Cemetery — Memorials and Alder

The old graveyard, pushed north and peripheral but still tended. Stage the memorial
beats in the **House of Memories** (`393_T05R0601.json`) — the vanilla memorial building —
and/or a small north-edge cemetery in `T05`.

Staging direction:

- **Mr. Fuji's memorial stone** (fresh flowers — someone still tends it) and **Agatha's**
  marker nearby. Read-only; **no event, no ghosts** — just remembrance.
- **Alder** stands among the graves. Talk-to reveals his grief-journey and, quietly, his
  absence from Unova (the **Unova seed** — something is happening there too). Kind, not
  self-pitying. Set an `FLAG_APOC_CH6_ALDER_MET`-style one-shot if his lines shouldn't
  repeat, or leave him as re-talkable ambient.
- Keep the whole area understated — the town moved on; the cemetery is a footnote it
  couldn't quite erase. The contrast with the busy media town is the point.

### 6.6 Moving On — Vermilion Unlocked

With the badge, the **Route 6 checkpoint** (`R06R0201`, the Saffron south gate from
Chapter 5) now **accepts a Kanto Gym Badge** as proof of legitimate trainer activity —
it opens. Vermilion's port connects to the S.S. network (Slateport, Olivine, Driftveil).

Staging direction:

- Re-visit the Route 6 gate logic from Ch5: it was **badge-conditional**, so earning
  Eve's badge opens it automatically (no new "unlock" flag — just the badge check passing).
  The guard waves the player through with a line acknowledging the credential.
- The player backtracks through Saffron to Route 6 (or via Route 10/Rock Tunnel south if
  that path is opened later — not required here). Hand off to **Chapter 7 (Vermilion)**.
- Set `FLAG_APOC_CH6_DONE` on the badge + checkpoint-open state for clean chapter tracking.
- Closing image: Lavender's broadcast tower blinking red against the evening sky,
  transmitting to a region that has no idea what's coming.

## State And Files

Confirmed map/script targets (from `disasm/pokeheartgold`,
`include/constants/maps.h` and `files/fielddata/...`):

| Area | Map JSON | Script | Map constant |
|------|----------|--------|--------------|
| Route 7 (Saffron↔Celadon) | `012_R07.json` | `scr_seq_0186_R07.s` | `MAP_ROUTE_7` (15) |
| Route 8 (Saffron↔Lavender, **spine**) | `013_R08.json` | `scr_seq_0188_R08.s` | `MAP_ROUTE_8` (16) |
| Celadon City | `052_T07.json` | `scr_seq_0785_T07.s` | `MAP_CELADON` (55) |
| Celadon Market/Services (Dept Store) | `327_T07R0101.json`… | — | `MAP_CELADON_DEPARTMENT_STORE_1F` (370) |
| Celadon Hotel (Condominiums) | `333_T07R0201.json` | `scr_seq_0796_T07R0201.s` | `MAP_CELADON_CONDOMINIUMS_1F` (376) |
| Celadon Botanical Gardens (old Gym) | `352_T07GYM0101.json` | `scr_seq_0786_T07GYM0101.s` | `MAP_CELADON_GYM` (395) |
| Celadon Café (Restaurant) | `340_T07R0701.json` | `scr_seq_0805_T07R0701.s` | `MAP_CELADON_RESTAURANT` (383) |
| Celadon Game Corner | `489_T07SP0101.json` | — | `MAP_CELADON_GAME_CORNER` (537) |
| Cycling Road gate (dead-end) | `R16R0201` | — | `MAP_ROUTE_16_GATEHOUSE` (421) |
| Lavender Town | `050_T05.json` | `scr_seq_0767_T05.s` | `MAP_LAVENDER` (53) |
| Lavender Broadcast Tower (Radio Station) | `394_T05R0701.json` | `scr_seq_0775_T05R0701.s` | `MAP_LAVENDER_RADIO_STATION` (439) |
| Eve's Ghost Gym (host: Volunteer P. House) | `390_T05R0201.json` | `scr_seq_0771_T05R0201.s` | `MAP_LAVENDER_VOLUNTEER_POKEMON_HOUSE` (435) |
| Memorial hall (House of Memories) | `393_T05R0601.json` | `scr_seq_0774_T05R0601.s` | `MAP_LAVENDER_HOUSE_OF_MEMORIES` (438) |
| Vermilion checkpoint (Route 6 gate) | `R06R0201` | `scr_seq_0185_R06R0201.s` | `MAP_ROUTE_6_SAFFRON_GATEHOUSE` (389) |

### Flags & vars

**Reuse (vanilla, already wired):**

- Route 8 sight-trainers: `TRAINER_BIKER_DWAYNE`, `_HARRIS`, `_ZEKE`,
  `TRAINER_SUPER_NERD_SAM`, `_TYRONE`, `TRAINER_YOUNG_COUPLE_MOE_AND_LULU` (double),
  `TRAINER_GENTLEMAN_MILTON` — re-line + re-team per BATTLES; keep placements.
- Celadon Gardens (old gym) slots: `TRAINER_TWINS_JO_AND_ZOE` (double), `LASS_MICHELLE`,
  `PICNICKER_TANYA`, `BEAUTY_JULIA`, and `FLAG_HIDE_CELADON_GYM_ERIKA` (→ Erika) — re-line
  as garden visitors; one can host **Aaron's** casual battle.
- `FLAG_HIDE_LAVENDER_RADIO_TOWER_DIRECTOR` — **Mary** at the production glass (seen,
  unnamed).
- Vanilla Lavender interiors (Volunteer House, House of Memories, Name Rater) — repurpose
  for the gym host + memorial hall + kept services.
- `give_badge <BADGE_*>` — the engine badge grant; **constant deferred to the badge-order
  pass** (Marsh bit a candidate).

**New custom flags to allocate** (assign to genuinely-free bits at build time — see the
allocation note; do **not** trust `FLAG_UNK_*` names as free):

- `FLAG_APOC_CH6_CELADON_*` — one-shots for the café quest completion, Erika's gift, and
  the Looker beat (as many as the optional content needs; all independent).
- `FLAG_APOC_CH6_EXHIBITION_DONE` — the Lavender TV exhibition side quest one-shot.
- `FLAG_APOC_CH6_BADGE_DONE` — Eve's gym cleared / badge awarded.
- `FLAG_APOC_CH6_ALDER_MET` — Alder cemetery scene one-shot (optional; or leave ambient).
- `FLAG_APOC_CH6_DONE` — chapter-complete (badge earned + Vermilion checkpoint open).

> **Flag-allocation note (repeat, important).** `FLAG_UNK_*` in `flags.h` means
> *un-named*, **not** *unused* — most are live vanilla flags referenced by maps/`src`
> (an audit found e.g. `FLAG_UNK_258` used by a Lavender Radio object). Assign new APOC
> flags only to bits verified **0-reference across `files/fielddata/` and `src/`**. The
> natural pool is the **vacated Team Rocket arc** (Radio-Tower takeover / Mahogany
> hideout — Apocrypha removes it; e.g. `FLAG_HIDE_ROCKET_HIDEOUT_*_MURKROW` at
> `0x24A–0x24D`, verified 0-reference) plus any `FLAG_UNK_*` confirmed 0-reference
> (e.g. `0x25E`). The reused vanilla flags above are verified correct; new-flag hex is
> intentionally left to the build-time audit.

**New custom var (optional):** `VAR_APOC_CH6_CELADON_QUEST` (a free `0x40xx`) if the café
ingredient-chain needs step tracking; not required if each step is its own flag.

## Implementation Order

1. **Route 8 spine** — re-line/re-team the 7 sight-trainers; wild table + item balls;
   the level climb to the gym. (`scr_seq_0188_R08.s`, `013_R08.json`)
2. **Celadon (optional)** — market/services retheme (Daisy Oak salon, move tutor,
   EV facility); Hotel (condo trainers + Looker); Gardens (Erika/Janine/Aaron, gift,
   Aaron battle); Café quest (Chairman → fetch → TM88 Pluck); Game Corner; Cycling Road
   dead-end. (`scr_seq_0785_T07.s`, `_0786_T07GYM0101.s`, `_0805_T07R0701.s`,
   `_0796_T07R0201.s`, `R16R0201`)
3. **Lavender town + tower** — media retheme; broadcast tower lobby (Mary seen, lobby
   battles, Fantina); the TV exhibition side quest. (`scr_seq_0767_T05.s`,
   `_0775_T05R0701.s`)
4. **Eve's Ghost gym** — stand up the host building (`T05R0201`), add gym warp + Eve;
   Gen-1 ghost roster; the badge + TM30 Shadow Ball; set `FLAG_APOC_CH6_BADGE_DONE`.
   (`scr_seq_0771_T05R0201.s`)
5. **Cemetery** — memorial hall (Mr. Fuji, Agatha) + Alder (Unova seed). (`scr_seq_0774_T05R0601.s`)
6. **Vermilion unlock** — confirm the Route 6 checkpoint's badge-conditional check now
   passes; guard waves the player through; set `FLAG_APOC_CH6_DONE`; hand off to Ch7.
   (`scr_seq_0185_R06R0201.s`)
7. **Items pass** — see [KANTO_ITEMS.md](KANTO_ITEMS.md): Celadon services (salon/tutor/
   EV), café TM, Erika gift, Game Corner, Lavender Mart, Route 7/8 field items.
8. **Battles pass** — see [KANTO_BATTLES.md](KANTO_BATTLES.md): Route 7/8 wilds + trainers,
   Aaron, hotel/lobby/exhibition trainers, and **Eve's gym roster** (the badge-2 tuning).
