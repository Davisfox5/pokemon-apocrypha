# Pokemon Apocrypha - Chapter 8 Build Spec

> Scope: arrival by sea at **Slateport City** (the player's first steps in **Hoenn**),
> the **Slateport Market**, **Gabby & Ty** + the **Route 110 vendor rescue**, the closed
> **Fighting gym**, the **Oceanic Museum** + **Captain Stern's region-spanning collection
> quest**, and the **beach (Route 109)** with its Scott/Lisia cameos. **No badge**: a
> new-region exploration chapter. This is the implementation-facing expansion of the
> Chapter 8 outline in `DESIGN.md`. Pairs with **[CHAPTER8_SCENES_SPEC.md](CHAPTER8_SCENES_SPEC.md)
> — the full line-by-line dialogue script** — and with the **new region docs**
> [HOENN_BATTLES.md](HOENN_BATTLES.md) (encounters + route/duo battles) and
> [HOENN_ITEMS.md](HOENN_ITEMS.md) (market/museum/beach items). The "Sample lines" below are
> voice references; the full script is in the scenes spec.

> **⚑ Cross-region note — this is the first non-HGSS chapter. READ THIS.** Hoenn does not
> exist in the HGSS engine (`pokeheartgold`). Every map, trainer, and encounter table below
> is **referenced from the pokeemerald decomp** (`disasm/pokeemerald/`) and must be **rebuilt
> as a native HGSS map** — new `MAP_*` constants, new zone_event/object data, new trainer +
> encounter entries. The pokeemerald data is the **layout / roster source of truth**;
> Apocrypha re-lines the NPCs, re-teams the trainers, and **re-tunes levels to the whole-game
> curve** (Hoenn's vanilla early routes sit far *below* the player and lift *up* hard — the
> inverse of Kanto's endgame routes). Sister decomps: **pokeemerald = Hoenn**,
> **pokeplatinum = Sinnoh**, **pokefirered = Kanto extras**, **pokeheartgold = the build
> engine (Johto/Kanto)**. The build *method* (hand-port vs. an automated converter) is an
> **open technical decision**; these docs specify the *design*, not the port pipeline. See
> [[apocrypha-cross-region-maps]].

## Chapter Promise

Chapter 8 is the reward for everything the last three chapters put the player through.
They got stranded, earned their way loose, and let a Champion put them on a boat — and the
boat pays off with **a whole new region.** Hoenn hits different: hotter, louder, lower to
the sky, colored warm where Kanto was corporate gray. **Slateport** is the antithesis of
everything the player has walked through since Goldenrod — not a checkpoint, not a canyon
of glass, not a broadcast town selling its own reinvention, but a **chaotic, alive,
salt-and-grilled-food port** that does not slow down for anyone, least of all a Johto kid
fresh off the ship. After the cold institutional grind of Kanto, Slateport is a lungful of
warm air.

And it's **fun.** DESIGN says it outright: *the conspiracy threads are sleeping; this is a
Pokémon adventure.* The player explores a dense, rewarding city; gets pulled into a **local
news story** by a fast-talking reporter and her long-suffering cameraman; **rescues a pack
of stranded merchants** on a coastal route and gets it all filmed; tours a museum run by a
gloriously over-caffeinated ocean nerd who hands them **a quest that will follow them across
the entire rest of the game**; and soaks up a region that paid for its environmental
lessons the hard way and *learned.* No badge — Brawly's not even in town. Just a city, a
region, and the feeling of being a **real traveler** at last, three regions deep, arriving
somewhere that has its own life and barely notices them.

Core themes:

- **A new region as a genuine reset.** Hoenn should feel *foreign* in the best way — new
  species, new weather-conscious culture, new pace. The player has earned the right to be a
  tourist for a chapter. Lean into wonder over plot.
- **The world lives without you.** Slateport has a news cycle, a market economy, a missing-
  vendors problem, a celebrity doing a photoshoot, and a talent scout working the crowd —
  none of it about the player. They step *into* an ongoing place, help with one problem, and
  leave it still running. That's the opposite of being the chosen one.
- **Hoenn learned.** The environmental identity (Pacifidlog, the weather crisis, rooftop
  solar, absorbed conservation habits) is **lived-in, never preachy.** The region is ahead
  of Kanto/Johto on sustainability *because it paid the price.* Texture, not sermon.
- **Seeds for the long game.** Stern's five-region artifact quest, Scott's Frontier card,
  Lisia's Wallace hint — three quiet hooks that pay off chapters or a whole game later. Plant
  them light; let the player forget them until they matter.

## Progression Spine

| Beat | Maps (pokeemerald ref → new HGSS build) | Purpose |
|------|-----------------------------------------|---------|
| 8.0 Arrival by sea | Slateport Harbor (`SlateportCity_Harbor`) | The S.S. from Vermilion docks; first Hoenn impression — heat, noise, salt |
| 8.1 Slateport city | Slateport City (`SlateportCity`) | Melting-pot texture; Hoenn's environmental identity; free exploration |
| 8.2 The Market | Slateport City (south stalls) | The open-air market; vendors; the **empty Mauville stalls** (the hook) |
| 8.3 Gabby & Ty | Slateport City (market) | The **filmed battle**; the recruitment; heading north together |
| 8.4 Route 110 vendor rescue | Route 110 south (`Route110`) | Route trainers + the **cornered Mauville vendors** + aggressive territorial wilds |
| 8.5 Market unlocked | Slateport City (south stalls) | Vendors return; **Mauville specialty inventory opens — permanent** |
| 8.6 Brawly's gym (closed) | new/repurposed Slateport building | Queue of frustrated trainers + the aide; note it; move on (no badge) |
| 8.7 Oceanic Museum + Stern | Oceanic Museum (`SlateportCity_OceanicMuseum_1F/2F`) | The tour; the **five-region artifact collection quest — planted** |
| 8.8 The beach + cameos | Route 109 (`Route109`) + Seashore House | Optional battles/training; **Scott** (Frontier seed); **Lisia** (Contest/Wallace seed); the Dewford ferry dock |
| 8.9 Moving on | north exit → Route 110 north | Toward **Mauville** and **Lavaridge** (Chapter 9) |

Target start state: lead team ~lv 25-26, **2 badges (Hive + Requiem)**, just off the ship.
Target end state: lead team ~lv 27-28, **2 badges (no new badge)**, Slateport fully
explored, the vendor market unlocked, Stern's quest planted — Chapter 9 heads north to
Mauville.

> **Level note (whole-game curve).** Chapter 8 sits **just past the badge-2 line (~lv22)**,
> climbing toward the **badge-3 line (~lv27)**. The player lands ~lv25-26 off the Ch7 routes;
> Route 109/110 trainers + the vendor-rescue wilds carry them to ~lv27-28. **Brawly is
> closed**, so no gym spike this chapter — and no Hoenn badge at all yet. The Hoenn circuit leads
> with **Wes's Shadow gym at Rustboro** (DESIGN gym list); **Brawly's Fighting badge**, fought
> later at **Dewford** (Petalburg→Dewford ferry), is a *later* Hoenn badge, **not** the first.
> (Mauville, the next city north, has **no gym** — Surge only *consults* on its power grid.)
> **Re-tune direction = lift UP, hard:** vanilla Slateport-area routes are early-Emerald
> (~lv12-14); Apocrypha lifts them ~+13 to meet the player. Keep species Hoenn-native. See
> [HOENN_BATTLES.md](HOENN_BATTLES.md).

## Cast

**Gabby & Ty — the reporter and the cameraman (the chapter's engine).** The RSE media duo,
imported wholesale (they exist in pokeemerald as `TRAINER_GABBY_AND_TY_1..6`, a 6-tier
rematch pair). **Gabby** talks fast, chases every lead, and oversells everything to camera;
**Ty** is quiet, perpetually adjusting his shot, and clearly the only reason any of it airs.
They're covering the missing-Mauville-vendors story, clock the player as a good human-
interest angle (a kid who's crossed three regions solo), get a **filmed battle**, and
recruit the player for the Route 110 rescue. They **reappear across the Hoenn arc** offering
rematches — the level ladder is already built into their six tiers. First-tier roster,
re-tuned up, in [HOENN_BATTLES.md](HOENN_BATTLES.md).
- *(Gabby, to camera)* *"—and here he is, folks, a trainer from JOHTO, no less, who's
  crossed THREE regions on his own two feet, standing between Slateport and disaster! Ty,
  tell me you're getting this."* *(Ty, not looking up)* *"I'm getting it."* *(Gabby)*
  *"He's getting it."*

**Captain Stern — the Oceanic Museum director (the long-game quest).** Energetic, scattered,
and *thrilled* that a young trainer wants a tour. He runs the museum and loves the ocean the
way other people love their own children. He gives the player an informal tour, laments the
gaps in the collection, and plants **the five-region artifact quest** — one relic from each
region's great maritime/subterranean site (Whirl Islands · Seafoam · Undersea · Iron Island ·
Relic/Abyssal Ruins), returnable individually for rewards, full set for a big prize. None
collectible yet; it just becomes a thing the player carries. See §8.7 + [HOENN_ITEMS.md](HOENN_ITEMS.md).
- *"You came in for the AIR CONDITIONING, didn't you. It's fine. Everyone does. But you're
  going to LEAVE caring about deep-sea trench sediment, and that is a PROMISE. Come on —
  start here, this is my favorite thing in the building and nobody EVER looks at it."*

**The Mauville vendors — the rescue (permanent market unlock).** A small group of merchants
who come down to Slateport for market day and *never miss it* — until now. Found on Route
110, cornered with their carts and utility Pokémon by an aggressive pack of wild Pokémon that
have claimed the path. Their own mons are pack-animals and haulers, not battlers. The player
clears the way; they head to Slateport grateful, and their stalls **open permanently** with
Mauville specialty stock. See §8.4-8.5 + [HOENN_ITEMS.md](HOENN_ITEMS.md).

**The Brawly gym aide (closed gym).** Managing a queue of frustrated trainers outside the
Fighting gym. Brawly commutes from Dewford and just… didn't come in today (maybe the waves
were good). The aide apologizes down the line, explains Brawly batches all challenges when he
turns up, and — if asked — describes the gym's Fighting-type, physical, aggressive style. No
badge to be had; the player notes the gym and moves on.
- *"He'll be in. Probably. He commutes, see — Dewford's across the water, and if the surf's
  up… look, when he gets here he does everybody at once, boom boom boom, whole line in an
  afternoon. So don't lose your spot. Or do. I'm not your dad."*

**Scott — the talent scout (Frontier seed).** Heavyset, Hawaiian shirt, casual intensity.
Finds the player somewhere in the city, says he travels the regions looking for exceptional
trainers and the player caught his eye, doesn't explain why, gives a card and a promise, and
is gone in thirty seconds. Plants a **Battle Frontier** seed for the late/post-game **without
ever explaining what that is.** (Ties to the vanilla `SlateportCity_BattleTent*` maps, which
can host optional Frontier-seed content later.)
- *"I watch trainers. It's the whole job, more or less. Most of 'em, I keep walking. You, I
  stopped." (a card changes hands) "You'll know what this is when you need to. See you around,
  kid. And you will."*

**Lisia — the Contest star (Wallace/Contest seed; a design add).** *Not in Emerald* (she's
ORAS) — a **pure design addition.** Wallace's niece, a genuine Hoenn celebrity: flashy,
warm, lives for the spotlight. Doing a public appearance near the market/beach promoting an
upcoming **Lilycove contest**, taking fan photos. Delighted to meet a Johto trainer; mentions
her uncle is "doing something big in Sootopolis soon" — a **Wallace-retirement** hint the
player can't parse yet. Bright, brief, gives the world a pop-culture layer beyond battles.
- *"Ohh, a traveler! From JOHTO? That's so far! You have to come to my showcase in Lilycove,
  it's going to be — okay, between us, it's going to be a LITTLE bit about my uncle, he's got
  this big Sootopolis thing coming, but MOSTLY it's about me. Say cheese!"*

**Ambient Hoenn NPCs (the environmental identity).** Weather-conscious, ocean-shaped,
practical about sustainability *because Hoenn paid for the lesson*: a fisher who references
the Pacifidlog tides plainly ("The water took the whole town. We learned."); rooftop-solar
installers; a kid reciting a conservation poster nobody made her read; a market cook proud
that the stall runs on recovered heat. **Never preachy** — lived-in.

## Scene Details

### 8.0-8.1 Arrival + The City

The S.S. vessel from Vermilion pulls into **Slateport Harbor** (`SlateportCity_Harbor`).
First Hoenn impression: heat and noise, docks crowded with fishing boats and ferries,
vendors shouting, the sky suddenly *open* after Saffron's corporate canyons.

Staging direction:

- **Arrival warp:** the departure cutscene from Ch7 (§7.7) lands here — the ship docks at the
  Harbor; a short arrival beat (deckhand, first-steps-in-Hoenn framing) → the player is free
  in Slateport City. Set `FLAG_APOC_CH8_ARRIVED`.
- Dress `SlateportCity` toward **warm, dense, lively** — lower buildings, warm palette, open
  sky, rooftop solar, recovered-materials construction. Retheme vanilla NPC chatter to the
  Hoenn environmental identity (Pacifidlog, weather crisis, practical sustainability). Keep
  the **Team Aqua grunt objects hidden — permanently.** **Canon (confirmed): Aqua & Magma are
  DEFUNCT/historical** — they existed, the weather crisis happened, and both teams **disbanded**
  in its aftermath; their legacy is Hoenn's environmental scars, not an active threat. The
  vanilla `FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` stays set forever (no reveal path). Apocrypha's
  Hoenn conspiracy thread (the port **trafficking** arc — Lavaridge→Slateport→Olivine→Driftveil)
  runs through the **Silph/Rocket-Silver network, not the weather teams.**
- Landmarks to signpost: the **Market** (south), the **Oceanic Museum**, the closed **Fighting
  gym**, the **beach** (Route 109 south), and the **north exit** to Route 110. Slateport is
  dense and rewarding — let the player wander.

### 8.2-8.3 The Market + Gabby & Ty

The **Slateport Market** — open-air stalls along the southern city (vendors are objects on
the `SlateportCity` map, not a separate interior): battle items, berries, held items,
decorations, food. The original that Celadon's market (Ch6) was modeled after — bigger,
louder, more varied.

Staging direction:

- Reframe the vanilla market vendors (**Energy Guru**, the **Power TM salesman**, the ribbon
  woman, decor/doll clerks) as the Slateport regulars; stock/roles in [HOENN_ITEMS.md](HOENN_ITEMS.md).
- **The empty stalls (the hook):** a few pitches stand vacant. An NPC notes the **Mauville**
  vendors are late — *unusual*, they never miss market day; another heard there's **trouble on
  Route 110.** Plant the rescue.
- **Gabby & Ty** are at the market covering exactly that story. They clock the player, Gabby
  wants a battle for the segment → the **filmed battle** (`TRAINER_GABBY_AND_TY_1`, re-tuned
  up; double battle; roster in [HOENN_BATTLES.md](HOENN_BATTLES.md)). After, Gabby smells the
  bigger story (three-regions-solo kid) and **recruits the player** to come north to Route 110
  and find the vendors — good TV, and a hand in case the "trouble" is wild Pokémon. Set
  `FLAG_APOC_CH8_GABBY_TY_MET`. The player, Gabby, and Ty head north.

### 8.4-8.5 Route 110 — The Vendor Rescue (and the payoff)

**Route 110** runs north from Slateport toward Mauville — coastal path, the elevated Seaside
Cycling Road overhead (bike-gated, inaccessible), tall grass with Hoenn-native wilds. Ch8
uses the **southern segment only**; the Cycling Road, the Trick House, and the northern half
belong to **Chapter 9 (Mauville approach).**

Staging direction:

- **Route trainers (southern segment):** re-line a subset of the vanilla Route 110 placements
  (swimmers/triathletes/youngster/psychic/fisher — the full 14-trainer route is split with
  Ch9) as Hoenn-corridor locals; rosters + the lift-up re-tune in [HOENN_BATTLES.md](HOENN_BATTLES.md).
- **The cornered vendors:** partway up, the **Mauville merchants** are stuck — carts, utility
  Pokémon, an aggressive **territorial wild pack** blocking the path (not unusual species; a
  group that claimed the route). Stage **2-3 scripted wild battles** (a Mightyena/Poochyena
  pack — "the pack that claimed the path") to clear/scare them off; levels in
  [HOENN_BATTLES.md](HOENN_BATTLES.md). Gabby films; Ty gets the hero shot; Gabby does a
  breathless recap that makes it sound like the player stormed a fortress.
- **The payoff (permanent):** the vendors head south; back at the market their stalls **open
  for good** with **Mauville specialty stock** (specialty balls, rare berries, a held item or
  two, a Mauville-region TM — curve-safe; [HOENN_ITEMS.md](HOENN_ITEMS.md)). Set
  `FLAG_APOC_CH8_VENDORS_RESCUED` (gates the stall inventory). Gabby & Ty thank the player,
  mention they'll be around Hoenn (**rematch seed**), and head further north.

### 8.6 Brawly's Gym — Closed

Slateport's **Fighting gym** (an Apocrypha relocation — canon Brawly is in Dewford; there's
**no vanilla Slateport gym map**, so this is a **new/repurposed building**, same pattern as
Eve's Lavender gym). A queue of frustrated trainers waits outside; **Brawly is out of town.**

Staging direction:

- Build/repurpose a **gym exterior** on the `SlateportCity` map: a door, a **queue** of 2-3
  frustrated trainer NPCs, and the **aide** at the front. **No interior needed this chapter** —
  the door is locked; the interior gets built when Brawly is actually battleable (a later
  chapter). Keep it a *closed, not blocked* beat: the player learns the gym exists and its
  style, and is never told they're "too weak."
- The aide explains Brawly's Dewford commute, the batch-challenge format, and (if asked) his
  Fighting-type, physical, aggressive style. **Future access** (Petalburg → Dewford ferry, the
  former Mr. Briney route now commercial) is a **later-chapter design detail** — don't wire it
  here; just plant that a Dewford ferry exists (the beach dock, §8.8).

### 8.7 The Oceanic Museum — Stern + The Collection Quest

The **Oceanic Museum** (`SlateportCity_OceanicMuseum_1F/2F`) — Slateport's cultural
centerpiece: marine biology, underwater exploration, Hoenn's naval history, and the
environmental changes that reshaped the region. A **weather-crisis** display, factual and
undramatic; a small **Pacifidlog memorial.**

Staging direction:

- Stage **Captain Stern** on the museum floor (reuse his vanilla object; the vanilla
  `FLAG_HIDE_SLATEPORT_CITY_CAPTAIN_STERN` guards his post-event hide — re-purpose the flag
  logic for Apocrypha's version). He gives the informal tour, then plants **the five-region
  artifact collection quest** (§Cast; full item design in [HOENN_ITEMS.md](HOENN_ITEMS.md)):
  one relic each from **Whirl Islands** (Johto) · **Seafoam Islands** (Kanto) · **Undersea
  Cave** (Hoenn) · **Iron Island** (Sinnoh) · **Relic Temple / Abyssal Ruins** (Unova). Each
  is a *"looks like it belongs in a museum"* key item, found in any order across the whole
  game, returnable individually (each = a reward), full set = a **big prize (TBD).** Set
  `FLAG_APOC_CH8_STERN_QUEST` (quest active/known).
- **Nothing is collectible yet** — all five sites need later-game access (Surf/Dive/reaching
  those regions). The quest is *planted*, not started: every maritime cave or sunken ruin for
  the rest of the game now carries a little Stern-shaped itch.
- The museum's exhibits double as **worldbuilding delivery** (Hoenn's ocean relationship, the
  weather crisis handled with restraint, Pacifidlog remembered). Read-only; no ghosts, no
  event — remembrance and wonder.

### 8.8 The Beach (Route 109) + The Cameos

**Route 109** — the beach south of Slateport: Hoenn beach culture in miniature. Casual sand
battles, swimmers challenging anyone near the water, sunbathers, sandcastles, a fishing-spot
argument. Light, fun, **entirely optional** — a place to train and soak up the region.

Staging direction:

- Re-line the vanilla Route 109 + **Seashore House** trainers (swimmers/tubers/sailors + the
  Seashore House's soda-shop-plus-three-battlers) as beach locals; rosters + the lift-up
  re-tune in [HOENN_BATTLES.md](HOENN_BATTLES.md). Keep the **Seashore House** a **soda shop**
  (cheap Fresh Water/Lemonade/Soda Pop heals; [HOENN_ITEMS.md](HOENN_ITEMS.md)) + optional
  battles. **Rename the vanilla Route 109 trainer "Mel"** (a coincidental name) to avoid
  collision with Apocrypha's journalist Mel.
- **Scott** finds the player somewhere in the city or beach (market / outside the gym / the
  sand): the 30-second Frontier-scout cameo → a card + a promise. One-shot `FLAG_APOC_CH8_SCOTT_MET`.
- **Lisia** (design add) does a public appearance near the market or beach: the Contest-star
  cameo, the Lilycove-showcase pitch, the "my uncle's doing something big in Sootopolis" seed
  (Wallace). One-shot `FLAG_APOC_CH8_LISIA_MET`.
- **The Dewford ferry dock:** stage a small **commercial ferry** presence at the beach/harbor
  (the "former Mr. Briney route, now a daily tourist service" from DESIGN) — a **future-access
  signpost** for Brawly's Dewford, not usable this chapter. A dock sign / a barker is enough.

### 8.9 Moving On — North to Mauville

With Slateport explored, the vendors rescued, the museum toured, and Hoenn absorbed, the path
runs **north** — Route 110 continues toward **Mauville**, and beyond it the road to
**Lavaridge** and its famous breeding facility.

Staging direction:

- An NPC at the Center/market points north: Mauville, then up through Route 111/112 toward Mt.
  Chimney and Lavaridge (hot springs; the world's best breeding facility). Set
  `FLAG_APOC_CH8_DONE`; hand off to **Chapter 9 (Mauville).**
- Closing image: Slateport at the player's back, still roaring — a city that helped them, got
  a story out of them, and went right on without them. The player heads into the heat.

## State And Files

**pokeemerald reference maps** (to be **rebuilt as HGSS maps** — new `MAP_*` constants; the
`MAP_*` names below are the **pokeemerald** source IDs, not final HGSS constants):

| Area | pokeemerald map | pokeemerald `MAP_*` |
|------|-----------------|---------------------|
| Slateport City | `data/maps/SlateportCity/` | `MAP_SLATEPORT_CITY` |
| Slateport Harbor (arrival) | `data/maps/SlateportCity_Harbor/` | `MAP_SLATEPORT_CITY_HARBOR` |
| Oceanic Museum 1F/2F | `data/maps/SlateportCity_OceanicMuseum_1F/2F/` | `MAP_SLATEPORT_CITY_OCEANIC_MUSEUM_1F/2F` |
| Stern's Shipyard 1F/2F | `data/maps/SlateportCity_SternsShipyard_1F/2F/` | `MAP_SLATEPORT_CITY_STERNS_SHIPYARD_1F/2F` |
| Battle Tent (Scott/Frontier seed) | `data/maps/SlateportCity_BattleTent{Lobby,Corridor,BattleRoom}/` | `MAP_SLATEPORT_CITY_BATTLE_TENT_*` |
| Pokémon Center / Mart | `data/maps/SlateportCity_PokemonCenter_1F/2F`, `_Mart/` | `MAP_SLATEPORT_CITY_POKEMON_CENTER_*`, `_MART` |
| Fan Club / Name Rater / House | `data/maps/SlateportCity_{PokemonFanClub,NameRatersHouse,House}/` | `MAP_SLATEPORT_CITY_*` |
| Route 110 (south segment) | `data/maps/Route110/` | `MAP_ROUTE110` |
| Route 109 (beach) | `data/maps/Route109/` | `MAP_ROUTE109` |
| Route 109 Seashore House | `data/maps/Route109_SeashoreHouse/` | `MAP_ROUTE109_SEASHORE_HOUSE` |
| Brawly's gym (**reference only**; Ch8 builds a *closed Slateport* façade) | `data/maps/DewfordTown_Gym/` | `MAP_DEWFORD_TOWN_GYM` |

> **Deferred to Ch9+ (do not build in Ch8):** Route 110 **north** half, the **Seaside Cycling
> Road** (`Route110_SeasideCyclingRoad*Entrance` — bike-gated) and the **Trick House**
> (`Route110_TrickHouse*`, 8 puzzle rooms — an optional side-dungeon better introduced with
> Mauville). Ch8 is Slateport + the beach + the southern rescue segment only.

### Trainers & battles (pokeemerald source → rebuilt HGSS trainers)

**Reference placements (re-line + re-team + lift-up per [HOENN_BATTLES.md](HOENN_BATTLES.md)):**

- **Gabby & Ty:** `TRAINER_GABBY_AND_TY_1` (the filmed Slateport/Route 110 battle; double;
  tier 1 of 6 — the rematch ladder `_2.._6` seeds later Hoenn chapters). Vanilla tier 1 =
  Magnemite@17 + Whismur@17 → lift up to the band.
- **Route 110 (south subset):** a handful of the vanilla Route 110 placements
  (`TRAINER_TIMMY` youngster, a Triathlete e.g. `TRAINER_ANTHONY`/`_JASMINE`,
  `TRAINER_EDWARD` psychic, `TRAINER_DALE` fisher, a Pokéfan e.g. `TRAINER_ISABEL_1`) —
  the rest reserved for Ch9's northern half.
- **Route 109 + Seashore House:** the beach placements (Tubers `TRAINER_LOLA_1`/`_AUSTINA`/
  `_GWEN`, Swimmers, Sailors, the Seashore House's Dwayne/Simon/Johanna). Re-line as beach
  locals; **rename any vanilla "Mel".**
- **Vendor-rescue wilds:** 2-3 **scripted wild** battles (a Mightyena/Poochyena pack), not
  trainers.
- **Brawly** (`TRAINER_BRAWLY_1`; Machop@16/Meditite@16/Makuhita@19 in vanilla) — **not
  battled this chapter** (gym closed); his roster is reference for the later Dewford/Slateport
  reopening, re-tuned to the curve then.

### Flags & vars (new APOC flags — 0-reference audit at build; do **not** trust `FLAG_UNK_*`)

- `FLAG_APOC_CH8_ARRIVED` — docked at Slateport / Hoenn intro played.
- `FLAG_APOC_CH8_GABBY_TY_MET` — the filmed battle + recruitment done.
- `FLAG_APOC_CH8_VENDORS_RESCUED` — Route 110 cleared; **gates the Mauville market stalls** (permanent).
- `FLAG_APOC_CH8_STERN_QUEST` — the five-region artifact collection quest is known/active.
- `FLAG_APOC_CH8_SCOTT_MET` / `FLAG_APOC_CH8_LISIA_MET` — the two cameo one-shots (optional).
- `FLAG_APOC_CH8_DONE` — chapter-complete (Slateport done; north exit to Ch9).
- **Keep set / hidden (permanently):** `FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` — Aqua/Magma are
  **defunct/historical** (confirmed canon; no reveal path this or any chapter).
- **Collection-quest vars:** a `VAR_APOC_STERN_ARTIFACTS` bitmask (which of the 5 relics
  turned in) — a whole-game var, allocate a free `0x40xx`. See [HOENN_ITEMS.md](HOENN_ITEMS.md).

> **Flag-allocation note.** Same discipline as the Kanto chapters — `FLAG_UNK_*` = un-named,
> not unused; assign new APOC flags only to bits verified 0-reference across the build. Note
> that **flag/var namespaces differ between engines** — the pokeemerald `FLAG_*`/`VAR_*` above
> are *source references*; the rebuilt HGSS maps get **HGSS-side** flags/vars. See
> [[apocrypha-flag-allocation]] and [[apocrypha-cross-region-maps]].

## Implementation Order

1. **Port scaffolding** — stand up the Slateport City map + Harbor arrival warp in HGSS
   (from the pokeemerald reference); wire the Ch7→Ch8 departure→arrival hand-off; Hoenn
   environmental dress; keep Team Aqua hidden. (`SlateportCity`, `SlateportCity_Harbor`)
2. **Market + Gabby & Ty** — vendor stalls (regulars + the empty Mauville pitches); the
   "vendors are late / trouble on 110" hook; the Gabby & Ty filmed battle + recruitment.
3. **Route 110 south + rescue** — the southern-segment trainers (lift-up re-tune); the cornered
   vendors + the scripted territorial-wild pack; the clear; Gabby's recap. (`Route110`)
4. **Market payoff** — vendors return; the **Mauville specialty stalls open permanently**
   (`FLAG_APOC_CH8_VENDORS_RESCUED`); Gabby & Ty rematch seed.
5. **Closed gym** — build the Slateport Fighting-gym **exterior** (queue + aide, locked door);
   the closed-not-blocked beat; plant the Dewford-ferry future-access signpost.
6. **Oceanic Museum + Stern** — the museum floor + exhibits (Hoenn ocean identity, weather
   crisis, Pacifidlog memorial); Stern's tour + the **five-region collection quest** planted
   (`FLAG_APOC_CH8_STERN_QUEST`, `VAR_APOC_STERN_ARTIFACTS`). (`SlateportCity_OceanicMuseum_1F/2F`)
7. **Beach + cameos** — Route 109 + Seashore House (soda shop + optional battles); **Scott**
   (Frontier seed) + **Lisia** (Contest/Wallace seed) one-shots; the Dewford ferry dock. (`Route109`, `_SeashoreHouse`)
8. **Moving on** — the north signpost (Mauville/Lavaridge); `FLAG_APOC_CH8_DONE`; hand off to Ch9.
9. **Items pass** — see [HOENN_ITEMS.md](HOENN_ITEMS.md): market regulars + Mauville unlock
   stock, Seashore sodas, the collection-quest artifact items, beach/city hidden items.
10. **Battles pass** — see [HOENN_BATTLES.md](HOENN_BATTLES.md): Route 109/110 wilds + trainers
    (lift-up re-tune), Gabby & Ty tier 1, the vendor-rescue pack, and the Brawly reference roster.
