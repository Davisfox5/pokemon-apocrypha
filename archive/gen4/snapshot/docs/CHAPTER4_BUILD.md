# Pokemon Apocrypha - Chapter 4 Build Spec

> Scope: Route 34, Goldenrod City (hub), Goldenrod Radio Tower, the Magnet Train,
> Saffron City (arrival only). **No new badge** — this is the travel/transition
> chapter. This is the implementation-facing expansion of the Chapter 4 outline in
> `DESIGN.md`. Pairs with [JOHTO_BATTLES.md](JOHTO_BATTLES.md) (encounter/trainer
> tables), [JOHTO_ITEMS.md](JOHTO_ITEMS.md) (item & mart placement), and
> **[CHAPTER4_SCENES_SPEC.md](CHAPTER4_SCENES_SPEC.md) — the full line-by-line
> dialogue script.** The "Sample lines" in the Cast section below are voice
> references; the complete spoken script lives in the scenes spec.

## Chapter Promise

Chapter 3 closed cold. Chapter 4 deliberately exhales. The player walks out of
Ilex Forest into the **biggest place they have ever seen** — Goldenrod, loud and
bright and full of distractions — and for a while the game just lets them be a kid
in a big city. Shopping. The Game Corner. The Underground. The badge grind pauses;
the world *widens* instead of deepening.

Then a stranger with too much energy and too little impulse control drags the
player somewhere they weren't ready to go. **Mel** — a fast-talking investigative
broadcaster — pulls the single thread the player carried out of the Slowpoke Well
(a **Silph Co.** logo on a lab coat) and, on pure instinct, sweeps them onto the
just-reopened **Magnet Train** to Saffron City. The chapter ends with the player
taking their first steps in **Kanto**, alone except for a reporter who treats them
like a source, with no way back.

Core themes:

- **The world is bigger than the badge.** After two chapters of Johto roads, the
  city's scale, commerce, and cross-region traffic do the worldbuilding. Goldenrod
  is the **showcase of the Inter-Regional Exchange** (see DESIGN.md): foreign goods,
  foreign trainers, foreign Pokemon, a global trade terminal — the connectedness
  the game has only hinted at, made literal and ambient.
- **The friend stays; the player goes.** Kestra reconnects, drags the player to the
  Radio Tower, then — sensibly — refuses to chase a reporter into Kanto. The two of
  them are *both right*. Her one last battle is how she says goodbye. Keeping the
  Johto rival in Johto means the player faces Kanto **alone**.
- **The planted detail becomes a lever.** The Silph coat meant nothing in Chapter 3.
  Mel makes it mean something. This is the first time the player's Well experience
  stops being a memory and starts being **plot**.
- **A force of nature, not a mentor.** Mel never guides, never reassures, never asks
  permission. She is fun, exhausting, and faintly dangerous — the kind of adult who
  forgets other people have plans. The reader should *like* her and *worry* about
  her in the same breath.

## Progression Spine

| Beat | Maps | Purpose |
|------|------|---------|
| 4.0 The road in | Route 34 (`R34`) | Skyline reveal; 6 sight-trainers; the displaced Oddish payoff; Day-Care intro |
| 4.1 The big arrival | Goldenrod City (`T25`) + interiors | Hub exploration: Dept Store, Game Corner, Underground/Global Terminal; optional seeds (Bill, merchant, international trainer) |
| 4.2 The rival resurfaces | Goldenrod City (square / Dept Store front) | Kestra finds the player, buzzing; pulls them to the Radio Tower for the live show |
| 4.3 Enter the journalist | Radio Tower 1F (`D23R0101`) | Mel's live broadcast; Kestra brags; Mel's interrogation; the Silph-coat lever; the snap decision |
| 4.4 The send-off | Radio Tower 1F → station approach | **Kestra rival battle** (last fight before Kanto); the "stay sensible" goodbye |
| 4.5 The Magnet Train | Goldenrod Station (`T25R0501`) → ride | Boarding on Mel's pass; the ride; Mel's Silph theories; cross-region NPC chatter |
| 4.6 Kanto | Saffron Station (`T11R0601`) → Saffron City (`T11`) | First steps in Kanto; Silph skyline; chapter ends stepping into Saffron with Mel |

Target start state: lead team ~lv 17-19, **1 badge (Hive)**, exiting Ilex Forest.
Target end state: lead team ~lv 19-20 (20 the ceiling), **still 1 badge** (no gym
this chapter), Magnet Train Pass *not* held (the one-way problem), standing in
Saffron City with Mel — Chapter 5 picks up immediately.

> **Goldenrod Gym is deferred.** Whitney / the Plain Badge are **not** earned this
> chapter. The gym (`T25GYM0101`) stays closed or "leader away" until the player
> returns to Johto later in the game; see the deferral note in
> [JOHTO_BATTLES.md](JOHTO_BATTLES.md). Chapter 4's only required battles are the
> six Route 34 trainers; the Kestra send-off is the chapter's one "boss."

## Cast

### Mel — the journalist (NEW, the chapter's engine)

Mel hosts a live program out of the Goldenrod Radio Tower that is part
investigative journalism, part talk show. She is sharp, fast, and **intense** — the
kind of broadcaster people tune in for because she's entertaining and certain
people dread because she doesn't know when to stop pushing. Or she knows and
doesn't care. She gets scoops nobody else gets because she'll chase a lead off a
cliff and treat the fall as research.

Her interest in the player is, at first, **purely instrumental** — they're a
witness, a source, a name she can put next to "Slowpoke Well." But her personality
makes every interaction feel personal, because she treats the player like an *equal*,
not a kid. She is **not a mentor and not a guide.** She is a force of nature who
pulls people into her orbit whether they want it or not, and — the chapter plants
this early — she is the kind of person who will eventually abandon someone the
moment a better story appears. (That abandonment is Chapter 5's; Chapter 4 only
loads the gun.)

**Mechanically she never battles.** No team, no trainer slot — she is dialogue and
movement only. (Confirmed design decision: Mel is a non-combatant throughout.)

Voice: rapid, overlapping, allergic to silence. Talks in headlines and follow-up
questions. Generous with enthusiasm, stingy with patience. Charismatic enough that
"this is a terrible idea" never quite lands in time.

Sample lines:

- "You were *in* the Well. Down in it. While it was happening." *(not a question —
  she's already three sentences ahead)* "Okay. Okay okay okay. What did they wear?"
- "Silph. You said *Silph.* On the coat. You're sure — no, don't second-guess it,
  first answer's the true one. Silph Co." *(the air changes)* "I have been pulling
  that thread for a year and a half."
- "The train just reopened. That's not luck, that's *timing*, and timing is the
  universe telling a reporter to get on the train. You're coming. Grab your bag."
- "Sit anywhere. No — by the window, you'll want the window. People always think
  they won't want the window." *(already talking about something else)*

### Kestra (returning — the friend-rival)

Kestra ran ahead after Violet and has been **in Goldenrod for a while**, training
and absorbing the city like she absorbs everything — loudly and all at once. She is
the loudest, most uncritical Silver-worshipper in the game (set in Chapter 1), and
that's exactly why her instinct here matters: when the impulsive believer is the
one saying *"this is a bad idea, don't go,"* it lands.

Her arc beat this chapter is small but load-bearing. She is the one who connects
the player to Mel (she dragged them to the show because she's a *fan*), and then she
is the one who **won't follow them into Kanto.** Not out of fear — out of sense.
She's got her own journey, Kanto isn't part of it, and somebody in this friendship
has to be the sensible one for once. The fact that it's *her* is the joke and the
heart of it. Her last beat is the **send-off battle** — the way Kestra says
"be careful" is by making the player prove they're ready.

Her team is the **type-advantage counter-starter** (persisted in
`VAR_APOC_FRIEND_STARTER` since Chapter 1), now evolved, plus grown route catches —
**all Johto-native** on purpose. She is the homegrown-Johto counterweight to a
player about to leave for a foreign region; her team should read *rooted*, not
worldly. Full rosters in [JOHTO_BATTLES.md](JOHTO_BATTLES.md).

Voice: breathless, competitive, warmer than she lets on. Covers worry with bravado.

Sample lines:

- "There you ARE. Do you know how big this city is? I've been here four days and I
  still get lost in the Underground. Come ON, you have to see this — there's a live
  show, the radio lady, she's covering the *Azalea thing.*"
- "Kanto. You're going to *Kanto.* With a stranger. On a train." *(beat)* "...That
  is the single most Champion thing I have ever heard and I hate that it's not me."
- "One battle. Right now. If you're gonna go do something this stupid, I'm not
  letting you go soft first. Send it out."  *(send-off battle prompt)*
- "Smell ya later, {PLAYER}. Call me the second it gets weird. It's gonna get
  weird." *(the goodbye — Silver's catchphrase, turned soft)*

### Goldenrod ambient cast (retheme, not rebuild)

Goldenrod's overworld object slots are vanilla **Rocket-takeover** placements
(`SPRITE_ROCKETM`, all gated by `FLAG_HIDE_ROCKET_TAKEOVER_*`) — that late-game
event **does not exist** in Apocrypha. Leave those slots hidden/unused and dress
the city through its **interior NPCs and shop staff**, which the chapter needs
anyway. The street read should be *commerce and motion*: shoppers, tourists,
out-of-towners, a kid who won't stop talking about the radio. Three optional
encounters do real worldbuilding work:

- **Bill** (vanilla `FLAG_HIDE_GOLDENROD_BILL` slot, in `T25R0401` Bill's House):
  Goldenrod is his family's city. Re-line him toward **storage-network connectivity
  between regions** — the PC boxes don't talk to Kanto's cleanly, there's lag, some
  transfers stall. Technical flavor that quietly says *the regions are wired
  together now, but imperfectly.* A seed, not a quest.
- **Traveling merchant** (Underground): hawks "the real stuff, straight from Hoenn
  and Sinnoh." Names goods and places the player hasn't been. The Inter-Regional
  Exchange as a sales pitch.
- **International trainer** (Pokemon Center): visiting from another region, drops a
  city name the player will eventually reach. A friendly face who makes the map feel
  bigger than the part the player can see.

### Magnet Train passengers (ambient, the ride)

A short gallery of people *in motion*, each a one-liner that widens the world: a
businessman headed to Silph Co. on contract, a woman visiting family in Vermilion,
a trainer going for the Kanto gym challenge, a kid pressed to the window. None are
battles. They exist so the train doesn't feel empty and so Kanto feels *populated*
before the player arrives. See the scenes spec.

### Saffron arrival cast (ambient, the close)

Saffron reads **corporate** where Goldenrod read **commercial** — institutional,
efficient, Silph's tower over everything. The arrival NPCs are clipped and busy:
badge-wearing employees, a closed-dojo notice, someone giving directions in the
brisk way big-city people do. The atmosphere does the work; keep lines short. The
chapter ends before any of this becomes a problem (that's Chapter 5).

## Scene Details

### 4.0 Route 34 — The Road In

The Ilex west exit lands the player on Route 34, descending toward the city. The
**Goldenrod skyline is visible before the city limits** — the first proper
metropolitan reveal in the game. Stage the route as a downhill approach: woodland
at the Ilex end giving way to open, bright, managed grass near the city.

Staging direction:

- **Six sight-trainers, already placed** in `035_R34.json` via `std_trainer`:
  `TRAINER_YOUNGSTER_SAMUEL`, `TRAINER_PICNICKER_GINA`, `TRAINER_YOUNGSTER_IAN`,
  `TRAINER_POLICEMAN_KEITH` (gated by `FLAG_UNK_1D2`), `TRAINER_CAMPER_TODD`,
  `TRAINER_POKEFAN_M_BRANDON`. Re-line them as suburban-Goldenrod-outskirts
  trainers (commuters, a beat cop, a picnicking family). Rosters/levels in
  [JOHTO_BATTLES.md](JOHTO_BATTLES.md); the dialogue is in the scenes spec.
- **The Day-Care** (`std_daycare_man` + the Day-Care couple) stays exactly as
  vanilla — a warm, useful systems beat that fits the "settle in, you're near the
  big city now" tone. Introduce it plainly; it's the chapter's one new *mechanic*.
- **The displaced-Oddish payoff.** Chapter 3 established (see the Ilex displacement
  note in [JOHTO_BATTLES.md](JOHTO_BATTLES.md)) that Seedot crowded the native
  Oddish out of Ilex Forest and the Oddish **resettled on Route 34's open grass.**
  Honor it: Oddish reads **newly-common** in the R34 table, and an NPC (a
  Day-Care-adjacent local or Picnicker Gina) can name it offhandedly — "didn't used
  to see the little weed-Pokemon out here, now they're all over the south grass."
  Mundane ecological texture, *not* ominous — the ordinary face of a changing world.
- **Item balls, already placed:** a **Nugget** (`std_itemball_r34_nugget`,
  `FLAG_HIDE_ITEMBALL_R34_NUGGET`) and **TM63 Embargo** (`std_itemball_r34_tm63`,
  `FLAG_HIDE_ITEMBALL_R34_TM63`). Keep both. See [JOHTO_ITEMS.md](JOHTO_ITEMS.md).
- Keep the vanilla rare-**Marill** flavor object (`FLAG_UNK_22D`) as optional color;
  it costs nothing and reads as "trainers showing off catches near the city."

### 4.1 Goldenrod City — The Big Arrival

The city opens up. Free exploration; **nothing here is mandatory** until the player
chooses to engage with the rival beat. Goldenrod is a playground and a showcase.

Staging direction:

- **Hide all the Rocket-takeover slots** (they belong to a removed event). The
  street is dressed with ambient flavor and shop traffic; no standing sight-trainers.
- **Department Store** (`T25R1001`–`R1006`, elevator `T25R1007`): the first proper
  multi-floor shopping in the game — medicine, balls, vitamins, **TMs for sale**,
  held items. Full stock list in [JOHTO_ITEMS.md](JOHTO_ITEMS.md). This is the
  economic step-up the level curve assumes from here on.
- **Game Corner** (`T25SP0101`): accessible for minigames/coins → prizes. Keep it
  optional and self-contained; prize list in ITEMS.
- **Underground** (`D37R0101` / `B1F` etc.): vendors (incl. the traveling merchant
  seed), haircut brothers (friendship flavor), passage. Optional, rewards curiosity.
- **Global Terminal** (`T25R1201`): lean into it as the **literal Inter-Regional
  Exchange** — a building whose entire premise is trading across regions. Even as
  flavor-only (no live trade backend needed), an NPC explaining what it's *for*
  does enormous worldbuilding. This is the most on-theme room in the chapter.
- **Bill seed** (`T25R0401`, `FLAG_HIDE_GOLDENROD_BILL`): the storage-connectivity
  line (see Cast). Optional.
- Gate the one-time "you have arrived" framing (camera/skyline moment, if any) behind
  `FLAG_APOC_CH4_GOLDENROD_INTRO_DONE` so it never replays.

### 4.2 The Rival Resurfaces

Kestra finds the player — stage near the **Department Store front or the central
plaza** — buzzing with city energy and four days of pent-up things to say. Her pull
is specific: she wants the player at the **Radio Tower** *right now*, because the
"radio lady" is doing a live segment on the **Azalea thing** (the Slowpoke Well),
and Kestra is a fan. This is how the player reaches Mel **naturally** — through a
friend's enthusiasm, not a plot errand.

Staging direction:

- Fire as a one-time coordinate/approach scene once the player is loose in the city;
  gate behind `FLAG_APOC_CH4_GOLDENROD_INTRO_DONE` set (arrival done) and the rival
  scene's own one-shot flag unset.
- Keep it light and fast. Kestra does most of the talking. She doesn't know the
  player is about to become the story — she just thinks the show is cool.
- On completion she heads for the Radio Tower; the player can still dawdle. The Radio
  Tower door becomes the soft objective. (Optionally set the rival's Radio Tower
  presence flag here — see Flags.)

### 4.3 The Radio Tower — Enter the Journalist

Inside, a live broadcast is in progress. **Mel** is the host. The player and Kestra
walk in mid-segment.

Staging direction:

- **Mel's slot:** repurpose the existing leader-type object in `109_D23R0101.json`
  (`SPRITE_GSLEADER3`, gated `FLAG_UNK_318`) as Mel at the broadcast desk, or place a
  fresh NPC if a better sprite exists at build time. The 1F also ships listener/staff
  flavor slots (`SPRITE_GSWOMAN6` ×3, `SPRITE_GSMAN1`, `SPRITE_GSGIRL2`) — dress the
  studio audience with them.
- **Kestra's slot:** the vanilla `SPRITE_GSRIVEL` object already in the Radio Tower
  (gated `FLAG_HIDE_RADIO_TOWER_RIVAL`) **is** Kestra here. Reveal her at/after the
  broadcast for the brag beat and the send-off battle. (In vanilla this slot was the
  Silver/rival radio encounter — clean reuse.)
- **The broadcast (the content):** Mel is connecting dots nobody else has bothered
  to — the Slowpoke Well incident plus a *pattern* of small-time organized activity
  across Johto: missing Pokemon, unusual equipment sightings, researchers where they
  shouldn't be. Energetic, almost giddy. Compelling broadcasting that also makes
  clear she's the type to chase a lead off a cliff. (She is **right**, which the
  player alone knows — dramatic irony the scene runs on.)
- **The brag:** after the segment, Kestra approaches Mel — starstruck — and, *proud
  of her friend and not thinking about consequences*, tells Mel the player was
  actually **in** Slowpoke Well and saw it firsthand.
- **The interrogation:** Mel's attention snaps to the player. Rapid-fire: what did
  you see, who was down there, what were they doing, what equipment. The player's
  key detail — surfaced through the dialogue — is the **Silph Co. lab coat** (a
  manufacturer stamp on the gear, specific enough to stick, ambiguous enough to not
  be proof). Mel latches on. Her energy shifts from entertained to **locked-in**:
  Silph is a thread she's already been pulling.
- **The snap decision:** right there, with impulsive certainty, Mel decides the
  player is coming with her to **Saffron City** — *now* — because the Magnet Train
  just reopened and Silph HQ is in Saffron and she needs a witness who can identify
  what they saw. She's already moving toward the door.
- Set `FLAG_APOC_CH4_MEL_MET` on completion (broadcast + interrogation + decision
  done). Keep Mel's "let's go" energy as the through-line into 4.4/4.5.

### 4.4 The Send-Off — Kestra's Last Battle and the Goodbye

Kestra thinks this is insane. **She's not wrong.** But she also won't *stop* the
player — she'll just refuse to come. The beat resolves with the two friends being
both right, and Kestra saying goodbye the only way she knows how: a battle.

Staging direction:

- **The argument (short):** Kestra calls it the most reckless, most *Champion* thing
  she's ever heard — and means both halves. She's not going. Kanto isn't her road;
  somebody has to be sensible; she's got training to do here. The worry is real and
  she covers it with bravado.
- **The send-off battle (the chapter's one boss):** Kestra challenges the player —
  "if you're gonna go do something this stupid, I'm not letting you go soft first."
  Her team is the **evolved counter-starter + grown Johto catches** (rosters in
  [JOHTO_BATTLES.md](JOHTO_BATTLES.md), conditioned on `VAR_APOC_FRIEND_STARTER` like
  the Chapter 2 rival fight). Drive it from the `SPRITE_GSRIVEL` slot.
  - **Dial:** this battle is the answer to the "battle-light chapter" problem and the
    per-chapter rival cadence. If a quieter goodbye is ever preferred, the battle can
    be cut to an emotional-only scene without touching the rest of the chapter — it's
    deliberately self-contained.
- **The goodbye:** win or lose, Kestra sees the player off warm and worried — "call
  me the second it gets weird; it's gonna get weird." She stays in Goldenrod (set her
  hide flag / leave her in the city). **Mel does not wait politely** — her impatience
  during the goodbye is characterization, not rudeness.
- Set `FLAG_APOC_CH4_RIVAL_SENDOFF_DONE`. The Magnet Train Station becomes the
  objective.

### 4.5 The Magnet Train

Mel has a rail pass and talks the player aboard — flashes credentials, whatever it
takes (the player has **no pass of their own**, which is the whole one-way trick;
see Flags/Items). The ride is a brief transitional sequence.

Staging direction:

- **Boarding:** at the Goldenrod Magnet Train Station (`190_T25R0501.json`; the
  station has a single attendant slot, `SPRITE_POLICEMAN`). Mel handles the gate.
  Establish, lightly, that the player is riding on *Mel's* pass — the mechanical
  seed for being stranded in Chapter 5.
- **The ride:** a short on-rails sequence (reuse the vanilla Magnet Train ride event
  if practical, or a simple fade/scroll). Window views blur between regions. Mel
  talks *at* the player about her Silph theories — **not paranoid, not
  conspiratorial**, a reporter who's noticed patterns: expanding research
  partnerships, Silph presence at unusual sites (the Ruins of Alph, Slowpoke Well,
  others she's heard about). She has **threads, not a theory**, and pulls them
  compulsively. She treats the player as an equal.
- **Passenger chatter:** the cross-region NPC gallery (see Cast) — Silph contractor,
  Vermilion family visit, Kanto gym challenger, kid at the window. The world is full
  of people in motion. Tone stays **light** despite the subject matter.
- Optionally set `FLAG_APOC_CH4_TRAIN_RIDE_DONE` at the far end if the ride needs a
  one-shot guard; otherwise the arrival flag covers it.

### 4.6 Saffron City — Arrival (chapter close)

The train arrives at Saffron Station (`357_T11R0601.json`). The player's **first
steps in Kanto.**

Staging direction:

- Saffron reads larger and more **corporate** than Goldenrod — institutional,
  efficient, **Silph Co.'s HQ dominating the skyline** (`T11R0701` is the building
  interior; for Chapter 4 it's only seen from outside / the lobby tease). A different
  atmosphere from Johto: industry over tradition.
- **Mel is energized** and driving. She tells the player to stick with her — she
  wants to see Silph's **public-facing lobby** before she starts digging. The chapter
  **ends** with the player and Mel stepping out of the station into Saffron together.
- Set `FLAG_APOC_CH4_SAFFRON_ARRIVED` (chapter-complete one-shot). **Chapter 5 picks
  up immediately** — do not resolve or soften the momentum here; the abandonment and
  the stranding are Chapter 5's, not this chapter's.
- **Do not** register a return path (no Saffron→Goldenrod fly/train for the player):
  the lack of a pass is the gate that keeps the player in Kanto until Chapter 5
  resolves it. Saffron's other content (Fighting Dojo, gym, deeper Silph) stays
  closed/gated this visit — that's Chapter 5+ surface.

## State And Files

Confirmed map/script targets (from `disasm/pokeheartgold`,
`include/constants/maps.h` and `files/fielddata/...`):

| Area | Map JSON | Script | Map constant |
|------|----------|--------|--------------|
| Route 34 | `035_R34.json` | `scr_seq_0237_R34.s` | `MAP_ROUTE_34` (38) |
| Goldenrod City | `073_T25.json` | `scr_seq_0885_T25.s` | `MAP_GOLDENROD` (76) |
| Goldenrod Radio Tower 1F | `109_D23R0101.json` | `scr_seq_0029_D23R0101.s` | `MAP_GOLDENROD_RADIO_TOWER_1F` (112) |
| Goldenrod Dept. Store 1F | `184_T25R1001.json` | `scr_seq_0899_T25R1001.s` | `MAP_GOLDENROD_DEPARTMENT_STORE_1F` (191) |
| Goldenrod Underground 1F | `—` (`D37R0101`) | `scr_seq_0093_D37R0101.s` | `MAP_GOLDENROD_TUNNEL_1F` (118) |
| Goldenrod Game Corner | `488_T25SP0101.json` | — | `MAP_GOLDENROD_GAME_CORNER` (536) |
| Goldenrod Global Terminal 1F | `200_T25R1201.json` | — | `MAP_GOLDENROD_GLOBAL_TERMINAL_1F` (207) |
| Bill's House (Goldenrod) | `196_T25R0401.json` | — | `MAP_GOLDENROD_BILLS_HOUSE` (203) |
| Goldenrod Magnet Train Stn 1F | `190_T25R0501.json` | `scr_seq_0893_T25R0501.s` | `MAP_GOLDENROD_MAGNET_TRAIN_STATION_1F` (197) |
| Saffron Magnet Train Stn 1F | `357_T11R0601.json` | `scr_seq_0834_T11R0601.s` | `MAP_SAFFRON_MAGNET_TRAIN_STATION_1F` (400) |
| Saffron City | `056_T11.json` | `scr_seq_0827_T11.s` | `MAP_SAFFRON` (59) |
| Saffron Silph Co. HQ | `359_T11R0701.json` | `scr_seq_0837_T11R0701.s` | `MAP_SAFFRON_SILPH_CO_HQ` (402) |

### Flags & vars

**Reuse (vanilla, already wired):**

- Route 34 sight-trainers: `TRAINER_YOUNGSTER_SAMUEL`, `TRAINER_PICNICKER_GINA`,
  `TRAINER_YOUNGSTER_IAN`, `TRAINER_POLICEMAN_KEITH` (gated `FLAG_UNK_1D2`),
  `TRAINER_CAMPER_TODD`, `TRAINER_POKEFAN_M_BRANDON` — re-line + re-team per BATTLES;
  do not move the placements.
- Route 34 items: `FLAG_HIDE_ITEMBALL_R34_NUGGET` (`0x43F`),
  `FLAG_HIDE_ITEMBALL_R34_TM63` (`0x4FA`) — keep both balls.
- `FLAG_HIDE_RADIO_TOWER_RIVAL` — the `SPRITE_GSRIVEL` slot in Radio Tower 1F = Kestra
  (broadcast brag + send-off battle).
- `FLAG_UNK_318` — the `SPRITE_GSLEADER3` slot in Radio Tower 1F → repurpose as Mel
  at the broadcast desk (or place a fresh NPC if a better sprite exists).
- `FLAG_HIDE_GOLDENROD_BILL` (`0x23E`) — the optional Bill encounter (storage-network
  connectivity seed) in Bill's House.
- `FLAG_HIDE_ROCKET_TAKEOVER_*` (Goldenrod overworld `SPRITE_ROCKETM` slots) — **leave
  hidden/unused**; the Rocket takeover event does not exist in Apocrypha.
- `ITEM_PASS` (`480`) = the Magnet Train Pass. The player **does not** receive one
  this chapter (rides on Mel's). Withholding it is the one-way gate resolved in Ch5.
- `FLAG_UNK_22D` (Route 34 static Marill flavor) — optional, leave as color.
- Day-Care: `std_daycare_man` and the Day-Care couple — keep intact as the chapter's
  systems beat.

**New custom flags to allocate** (4 one-shots + 1 optional — assign to genuinely-free
bits at build time; see the allocation note below. **Do not** trust `FLAG_UNK_*` names
as "free": nearly all `FLAG_UNK_*` in the `0x23x–0x25x` range are live vanilla flags
referenced by maps/`src`):

- `FLAG_APOC_CH4_GOLDENROD_INTRO_DONE` — big-arrival framing one-shot; also the
  precondition that lets the rival-resurfaces scene fire.
- `FLAG_APOC_CH4_MEL_MET` — broadcast + interrogation + Saffron decision complete (the
  Silph-coat lever pulled).
- `FLAG_APOC_CH4_RIVAL_SENDOFF_DONE` — Kestra send-off battle + goodbye complete;
  Kestra stays in Goldenrod.
- `FLAG_APOC_CH4_SAFFRON_ARRIVED` — chapter-complete one-shot (first steps in Kanto);
  hands off to Chapter 5.
- *(optional)* `FLAG_APOC_CH4_TRAIN_RIDE_DONE` — only if the ride needs its own guard
  separate from arrival.

> **Flag-allocation note (applies to all APOC chapters).** `FLAG_UNK_*` means
> *un-named*, **not** *unused* — an audit shows most `FLAG_UNK_*` in this range are
> referenced by real maps (e.g. `FLAG_UNK_258` is used by a Lavender Radio object).
> Assign new APOC flags only to bits that are **0-reference across `files/fielddata/`
> and `src/`**. The natural pool is the **vacated Team Rocket arc** — Apocrypha removes
> the Radio-Tower takeover / Mahogany hideout, freeing that flag block (e.g.
> `FLAG_HIDE_ROCKET_HIDEOUT_*_MURKROW` at `0x24A–0x24D`, verified 0-reference) — plus
> any `FLAG_UNK_*` confirmed 0-reference. The verified reused vanilla flags above
> (`FLAG_HIDE_GOLDENROD_BILL`, `FLAG_HIDE_RADIO_TOWER_RIVAL`, `FLAG_UNK_318`) are
> correct; the new-flag hex is intentionally left to the build-time audit.

**New custom var:**

- `VAR_APOC_CH4_PROGRESS` (free `0x403x`, e.g. `0x4033`, next after Ch3's `0x4032`) —
  optional linear-progress driver if the radio→station beats need ordering beyond the
  four flags above.

**Carried from Chapter 1:**

- `VAR_APOC_FRIEND_STARTER` — Kestra's counter-starter species; **drives the
  send-off battle roster branch** exactly as it drove the Chapter 2 rival fight.

> Allocation discipline matches Chapters 1-3: prefer free `FLAG_UNK_*` in the hide/APOC
> range and a free `0x40xx` var, and **re-skin vanilla trainer/event slots** rather
> than adding new ones (the Route 34 six, the Radio Tower rival + leader slots, the
> Bill slot, the station attendants are all already placed). Verify each slot is still
> unused at build time.

## Implementation Order

1. **Route 34 pass** — re-line/re-team the six sight-trainers; honor the displaced
   Oddish (table + an NPC line); introduce the Day-Care; keep both item balls and the
   skyline-reveal staging. (`scr_seq_0237_R34.s`, `035_R34.json`)
2. **Goldenrod hub pass** — hide the Rocket-takeover slots; dress the streets with
   ambient flavor; wire the Department Store stock, Game Corner, Underground, and
   Global Terminal flavor; place the Bill / merchant / international-trainer seeds.
   Set the arrival one-shot. (`scr_seq_0885_T25.s`, `073_T25.json`, store/terminal maps)
3. **Rival resurfaces** — Kestra finds the player near the Dept Store, pulls them to
   the Radio Tower. One-shot coord scene. (`scr_seq_0885_T25.s`)
4. **Radio Tower / Mel** — broadcast segment, Kestra's brag, Mel's interrogation, the
   Silph-coat lever, the Saffron snap decision. Place Mel (leader slot) + reveal Kestra
   (rival slot). Set `FLAG_APOC_CH4_MEL_MET`. (`scr_seq_0029_D23R0101.s`)
5. **Send-off battle + goodbye** — `VAR_APOC_FRIEND_STARTER`-conditioned Kestra fight
   from the rival slot; warm/worried goodbye; Kestra stays. Set
   `FLAG_APOC_CH4_RIVAL_SENDOFF_DONE`. (`scr_seq_0029_D23R0101.s`)
6. **Magnet Train** — boarding on Mel's pass at the Goldenrod station; the ride
   sequence with Mel's Silph-threads monologue and the passenger gallery.
   (`scr_seq_0893_T25R0501.s`)
7. **Saffron arrival** — first steps in Kanto; corporate atmosphere; Silph skyline;
   Mel drives toward the lobby; set `FLAG_APOC_CH4_SAFFRON_ARRIVED`; hand off to Ch5
   with momentum intact. **No return path registered.** (`scr_seq_0834_T11R0601.s`,
   `scr_seq_0827_T11.s`)
8. **Items/economy pass** — see [JOHTO_ITEMS.md](JOHTO_ITEMS.md): Department Store
   stock (the economic step-up), Game Corner prizes, Underground vendor stock, Route
   34 balls, Magnet Train Pass *withheld*.
9. **Encounter/level pass** — see [JOHTO_BATTLES.md](JOHTO_BATTLES.md): Route 34 wild
   table (with the newly-common Oddish), the six Route 34 trainer teams, the Kestra
   send-off rosters, and the Goldenrod-gym deferral note.

---

## Implementation status (2026-07-01)

**Status: ✅ story spine implemented** (4.0 data → 4.6 arrival), builds clean
(`MAKE EXIT=0`). Ambient-interior flavor pass still open; not yet play-tested.

### What shipped

- **Data pass:** the six Route 34 sight-trainers re-lined/re-teamed (Gina's
  displaced Oddish, Keith's Growlithe ace, Brandon's Whismur/Bidoof); Kestra
  send-off on rival slots 4-6 (LYRA class, evolved counter-starter ace 21,
  all-Johto, Super Potion); R34 wild table with newly-common Oddish, rare
  Ditto/Whismur.
- **4.1/4.2:** Rocket-takeover slots permanently hidden (init +
  deterministic `T25_018`); big-arrival silent one-shot on the R34 gate band
  (`VAR_APOC_CH4_SCENE` 0→1); plaza Kestra pull at the Dept Store front
  (val 1→2, reveals the tower slot); four street ambients rethemed.
- **4.3/4.4:** Mel on the vanilla tower leader slot — on-air brush-off,
  then the full broadcast/brag/interrogation/snap-decision chain
  (`MEL_MET`, val 3); Kestra argument + starter-branched send-off battle +
  goodbye on the vanilla radio-rival slot (`SENDOFF_DONE`, val 4); Mel exits
  mid-goodbye.
- **4.5/4.6:** boarding on Mel's pass (attendant + press routine), ride as a
  four-box monologue over black, warp to Saffron; PA + Mel's KANTO close +
  walk-off (`SAFFRON_ARRIVED`); platform passenger gallery; the vanilla
  ITEM_PASS check still guards the return ride — the one-way gate holds.

### Flags/vars

`0x51F-0x526`: GOLDENROD_INTRO_DONE, MEL_MET, RIVAL_SENDOFF_DONE,
SAFFRON_ARRIVED, HIDE_KESTRA_PLAZA, HIDE_MEL_TOWER, (525 reserved),
HIDE_MEL_SAFFRON. Var `VAR_APOC_CH4_SCENE` (0x4039): 0 fresh → 1 arrived →
2 pulled → 3 Mel met → 4 sendoff done.

### Open items (flavor pass)

- R34: skyline hiker, Day-Care couple re-lines, fence local's Oddish line
  (the wild table + Gina already carry the payoff).
- Goldenrod interiors: Dept Store clerk/shopper/rooftop, Game Corner
  attendant, Underground merchant + passer-by, Global Terminal guide +
  patron, Bill seed, PC international trainer (Mossdeep).
- Saffron street tease NPCs (T11) + kid-at-window line wiring.
- Dept Store stock / Game Corner prizes per JOHTO_ITEMS (vanilla stock in
  place meanwhile).

### Playtest checklist

1. Arrival band on the R34 gate edge fires once, silently.
2. Plaza scene at (364-366, 370): Kestra placement via move_person_facing,
   run-off west.
3. Tower: brush-off pre-plaza; full chain after; Kestra reveal position by
   the desk (26,25 home → scene staging); send-off battle branches; loss
   re-entry (argument replays — acceptable?).
4. Boarding → ride text over black → Saffron landing on (14,7) triggers the
   arrival scene exactly once; Mel walk-off; return ride correctly blocked
   (no pass).
