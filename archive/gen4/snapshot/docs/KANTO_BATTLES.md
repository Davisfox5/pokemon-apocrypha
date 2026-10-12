# Pokémon Apocrypha — Kanto Battles & Encounters

The Kanto companion to [JOHTO_BATTLES.md](JOHTO_BATTLES.md): wild encounter tables,
trainer/gym battles, and the level band for the Kanto chapters of the story. Kanto
begins at **Saffron City (Chapter 5)** when the player is stranded off the Magnet
Train, and continues east/west from there (Lavender, Celadon, Vermilion…).

> Detail split (see [[apocrypha-doc-taxonomy]]):
> - this file — Kanto encounters + trainers + battles
> - [KANTO_ITEMS.md](KANTO_ITEMS.md) — Kanto items + marts
> - per-chapter docs (`CHAPTER<N>_BUILD.md` / `CHAPTER<N>_SCENES_SPEC.md`) — staging + dialogue

**Level curve:** Kanto continues the single **whole-game** curve defined at the top of
[JOHTO_BATTLES.md](JOHTO_BATTLES.md) (Full Epic Scale, with the **+3 lift**) — it is
*not* a separate Kanto re-scale. The player arrives in Kanto at **~lv 19–20, 1 badge
(Hive)**, and the Kanto routes pick up the band from there. Where a Kanto location's vanilla levels sit far
above this point (Kanto is endgame in vanilla HGSS), Apocrypha **re-tunes down** to the
story's actual progression — the same discipline used for the Goldenrod Department
Store TM gating (see [JOHTO_ITEMS.md](JOHTO_ITEMS.md)).

---

## Chapter 5 — Saffron City (stranded)

**Player level by end of chapter:** ~19–20 (unchanged — no battles to grow on).
**Badges:** 1 (Hive), **no new badge**. Chapter 5 is a **pure story/atmosphere
chapter with no required trainer battles** — Saffron is a city (no wild grass), both
dojos are **closed for challenges**, and the dojo clash is a **spectator** scene. See
[CHAPTER5_BUILD.md](CHAPTER5_BUILD.md) for staging and
[CHAPTER5_SCENES_SPEC.md](CHAPTER5_SCENES_SPEC.md) for dialogue.

### Required battles

**None.** This is by design — after the Slowpoke Well doubles, the first gym, and the
Kestra send-off, Chapter 5 is the breather where the *world* applies the pressure, not
a trainer. The player's productive options (Silph access, dojo challenges) are all shut
down by circumstance; the chapter is about being stranded and choosing a road out.

### Spectator showcase (flavor — not fought)

The dojo flashpoint stages powerful Pokémon the player **only watches**. They exist to
set the **power scale** ("you are not ready for this") and to introduce Sabrina and
Bruno — none are `trainer_battle` encounters this chapter:

| Shown | Owner | Role in the scene |
|-------|-------|-------------------|
| **Medicham** (Psychic/Fighting) | contested | The flashpoint — claimed by both dojos, belongs to neither; distressed in the plaza |
| Abra / Kadabra | Psychic Dojo students | The brawl tableau (vs. the Fighting side) |
| Machop / Machoke | Fighting Dojo students | The brawl tableau (vs. the Psychic side) |
| **Alakazam** | Psychic Dojo master | The escalation — master-level heavyweight; player can't touch it |
| **Machamp** | Fighting Dojo master | The escalation — master-level heavyweight; player can't touch it |
| (unshown teams) | **Sabrina**, **Bruno** | End the brawl by presence alone; **introduced, not battled** |

> **Sabrina & Bruno are not fought here.** Their trainer slots
> (`TRAINER_LEADER_SABRINA_SABRINA`, `TRAINER_ELITE_FOUR_BRUNO_BRUNO`) and the dojo
> juniors (`MEDIUM_DARCY/REBECCA`, `PSYCHIC_M_JARED/FRANKLIN`, the Fighting Dojo's
> `GSFIGHTER`/`GSLEADER*` crowd) are present as a **scripted tableau** only — no
> `trainer_battle` calls. The two dojos open for **real** challenges in a later
> chapter; spec Sabrina's psychic team and the Fighting master's team there, on the
> whole-game curve, when they're actually battleable.

### Wild encounters

**None in Saffron** — it's a city. Kanto's first wild tables begin in **Chapter 6**
(Routes 5–8 around Saffron, and the Lavender approach). The two **open** exit routes
carry trainers at the player's level — but those routes and their battles belong to
**Chapter 6**; Chapter 5 ends at the gate the player chooses.

### Exit fork (battle-relevant note)

Two of Saffron's four gates are open; both reach Lavender (Celadon dead-ends for now).
The trainers and encounters beyond them are **Chapter 6** content:

- **East → Lavender (Route 8):** open; the main spine. Trainers ~the player's level.
- **West → Celadon (Route 7):** open; dead-end for now (Cycling Road needs a bike).
- **North → Cerulean (Route 5):** closed (dojo-incident spillover).
- **South → Vermilion (Route 6):** League-gated (needs a Kanto badge — re-opens later).

---

## Chapter 6 — Route 7/8 · Celadon (optional) · Lavender · Eve's Ghost Gym

**Player level by end of chapter:** ~21–22. **Badges:** 1 (Hive) → **2** (Eve's Ghost
badge — first Kanto badge). Chapter 6 has the region's **first real gym** (Eve, Ghost)
and a proper trainer road (Route 8). Celadon is **optional** (trainer-light detour).
Vanilla Kanto is endgame-leveled; everything here is **re-tuned down** to the badge-2
band (see the region economy note above). Staging: [CHAPTER6_BUILD.md](CHAPTER6_BUILD.md);
dialogue: [CHAPTER6_SCENES_SPEC.md](CHAPTER6_SCENES_SPEC.md).

### Level anchors

| Subject | Level | Notes |
|---------|-------|-------|
| Route 8 sight-trainers | 19–21 | The spine; a clean climb from the ~lv19–20 Saffron exit toward the gym |
| Route 7 (Celadon path) | 17–19 | Short, trainer-light; optional |
| Aaron (Celadon gardens, casual) | ~20–21 | Sinnoh E4 **holding way back** — a friendly scaled fight, *not* his real team |
| Celadon hotel / Lavender lobby / TV studio | 19–21 | Optional casual battles |
| **Eve — Ghost gym (Requiem badge)** | ace **22** | Gen-1 ghost roster; Marowak anchor; player target ~lv 21. Already on the +3-lifted badge-2 line (~22), so Eve is unchanged; the routes lift up to meet her |

The player should reach Eve ~lv 20–22 via Route 8 + wilds (+ optional Celadon/Lavender
battles), with no grinding. Eve's ace at lv22 is a fair +1–2 over a prepared team.

### Wild encounters

Species faithful to vanilla; **levels re-tuned down** to the badge-2 band (with the +3
lift), and obvious second-stage "commons" softened to their first stage where a low level
would read oddly (e.g. Pidgey/Abra as the common slot rather than Pidgeotto/Kadabra). Per
the Inter-Regional Exchange, the routes' vanilla "insertion" slots (**Plusle/Minun** Hoenn,
**Shinx** Sinnoh) read as naturalized **Electric-ish migrants** — thematically at home in
the **broadcast/antenna corridor** feeding Lavender. Keep them rare.

**Route 8 (`R08`)** — the spine, **lv 17–20**:

| Slot | Day |
|------|-----|
| Common | Pidgey → occasional Pidgeotto (lv 17–20) |
| Common | Growlithe (lv 17–19) |
| Uncommon | Abra (lv 17–18) → occasional Kadabra (lv 20) |
| Rare (migrants) | **Plusle / Minun** (Hoenn) / **Shinx** (Sinnoh) (lv 17–19) |

**Route 7 (`R07`)** — the Celadon side, **lv 16–19** (optional): Rattata (→ Raticate
rare), Spearow, Growlithe, + the same Plusle/Minun/Shinx migrant slots (rare).

> **Re-tune note.** Vanilla Kanto Routes 7/8 sit ~lv 40s (Kanto = endgame in HGSS).
> Apocrypha pulls them to the badge-2 band above. Keep the species *families* faithful;
> just cap the levels and prefer first-stage commons. Growlithe on both routes is a nice
> readable Fire presence pre-gym and pairs with the Lavender "everything runs hot/electric
> now" texture.

### Trainer battles

**Route 8 — seven sight-trainers (the spine).** All vanilla `std_trainer` placements in
`013_R08.json`, re-lined as Kanto-corridor locals. Teams stay **Kanto-base**; the one
import sits with the well-traveled Gentleman, mirroring the routes' migrant slots. 1:1 to
the real engine slots:

| Engine slot | Trainer (recast) | Team (origin) | Level | Notes |
|-------------|------------------|---------------|-------|-------|
| `TRAINER_BIKER_DWAYNE` | Biker Dwayne | Koffing, Grimer | 20, 20 | Gritty Kanto poison; road-gang flavor |
| `TRAINER_BIKER_HARRIS` | Biker Harris | Koffing, Voltorb | 19, 20 | Poison + a Self-Destruct scare |
| `TRAINER_BIKER_ZEKE` | Biker Zeke | Grimer, Koffing | 19, 20 | "math says you lose" — all-local |
| `TRAINER_SUPER_NERD_SAM` | Super Nerd Sam | Magnemite, Voltorb | 20, 20 | Electric, near the tower's signal |
| `TRAINER_SUPER_NERD_TYRONE` | Super Nerd Tyrone | Magnemite, Grimer, Ditto | 19, 20, 20 | Three mons; the Ditto is a fun coin-flip |
| `TRAINER_YOUNG_COUPLE_MOE_AND_LULU` | Young Couple Moe & Lulu | Nidoran♂ + Nidoran♀ | 20, 20 | **Double battle**; the classic paired Nidoran |
| `TRAINER_GENTLEMAN_MILTON` | Gentleman Milton | Meowth, **Glameow** (Sinnoh) | 20, 21 | Route high mark; his import is a "gentleman's cat" from Sinnoh — the one Exchange nod on R8 |

Route 8 tuning: 13 of 14 mons Kanto-native; the single import (Milton's Glameow) is the
character-justified one, level-capped. Keep movepools route-tier (Tackle, Smog, Sludge,
Spark, Sonic Boom, Bite, Fury Swipes); Voltorb's Self-Destruct is the only "gotcha."

**Route 7 (Celadon path).** Short and trainer-light in vanilla (`012_R07.json` has ~no
`std_trainer` placements) — leave it a quick optional connector. If a battle or two is
wanted, add small Kanto-local placements at build (Bug Catcher / Youngster tier, lv 17–18).

**Aaron — Celadon Botanical Gardens (casual, optional).** The Sinnoh Elite Four Bug
specialist, **holding way back** for a friendly garden battle. Reuse one repurposed
Celadon-gym slot for him. A light Bug team scaled to the player, **not** his real E4 roster:

| Recast slot | Team (origin) | Level | Notes |
|-------------|---------------|-------|-------|
| (repurposed garden slot) → **Aaron** | Dustox (Hoenn), Kricketune (Sinnoh) | 20, 21 | Explicitly scaled-down; flavor, not a wall. His true team (Yanmega/Scizor/Vespiquen/Heracross/Drapion, lv50s+) is reserved for a real Sinnoh encounter |

**Optional casual battles** (Celadon hotel, Lavender tower lobby, TV exhibition studio) —
placed at build, ~lv 19–21, Kanto-base with light cross-region flavor appropriate to a
cosmopolitan hotel / a media hub. Representative, tune at build:

- **Celadon hotel:** a Hoenn tourist (Zigzagoon/Wingull, lv 20), a rare-mon collector
  (shows off, may battle with a single prized Kanto mon lv 21).
- **Lavender lobby:** media intern (Voltorb/Magnemite, lv 20), off-duty tech (Gastly, lv 20
  — leaning into the "ghost-story podcast" bit).
- **TV exhibition:** 2–3 studio trainers, lv 20–21, showy movesets for the commentator to
  oversell. Reward is prize money + item (see [KANTO_ITEMS.md](KANTO_ITEMS.md)).

**Eve — the Ghost Gym (2nd badge, first Kanto badge).** Lavender has **no vanilla gym**;
host Eve's gym in a repurposed building (recommend Volunteer Pokémon House `T05R0201`) and
add her leader slot. **Deliberately Gen-1 Kanto ghosts only — no imports** (her character:
the traditionalist keeping old Lavender; the "small Gen-1 ghost pool" *is* the design). The
fight tests non-straightforward battling (Ghost immunities, status, indirect pressure):

| Order | Pokémon | Level | Role / moves (intent) |
|-------|---------|-------|-----------------------|
| 1 | Haunter | 19 | Opener — Hypnosis, Confuse Ray, Night Shade (indirect chip, not brute force) |
| 2 | Marowak | 20 | **The emotional anchor** (the Lavender Tower mother; Eve never explains it). Bone Club / Bonemerang, Focus Energy — a physical curveball on a Ghost team |
| 3 | Haunter | 21 | Curse, Mean Look, Shadow-tier chip — punishes a switch-happy player |
| 4 (ace) | **Gengar** | 22 | Shadow Ball, Hypnosis, Dream Eater, Sucker Punch — the real threat; patient and punishing |

Eve / gym tuning:

- **The lesson is "hit what you can't see."** Normal/Fighting moves whiff on the ghosts;
  the player needs real answers (Dark/Ghost, or status of their own). A player who spams
  their strongest STAB and watches it phase through is *meant* to lose a Pokémon and learn.
  Marowak in the middle punishes anyone who over-commits to a Ghost-only counter-plan.
- **Keep it honest for badge 2:** low-power, high-annoyance movesets (status, Night Shade,
  Curse) rather than big damage. The ace Gengar is the only one that hits genuinely hard.
- **All-Gen-1-Kanto by design** — no Misdreavus/Duskull/Shuppet/etc. imports. This is the
  deliberate *anti*-Inter-Regional-Exchange statement: the institutional/League and younger
  trainers salt in imports; Eve, the keeper of the old town, refuses to. Contrast is the point.
- **Reward:** the **Requiem Badge** (confirmed name; engine
  `give_badge <BADGE_*>`, constant deferred to the whole-game **badge-order pass** — the
  Saffron/**Marsh** bit is a candidate, freed by Saffron's gym being the closed Psychic
  Dojo) + **TM30 Shadow Ball** (the vanilla Ghost-gym precedent — Morty gives it; earned as
  a badge prize, not bought). Set `FLAG_APOC_CH6_BADGE_DONE`.
- **Optional gym juniors:** the host building has no gym-trainer slots; if juniors are
  wanted, add 1–2 small ghost trainers (Gastly/Haunter, lv 19–20) at build. Not required —
  a lean, Eve-only gym fits the "small pocket of old Lavender" framing.

> **Eve level dial.** If the lv22 Gengar ace reads hot for a ~lv21 player, drop the ace to
> lv21 and the roster to 3 (Haunter 19 / Marowak 20 / Gengar 21). If it reads soft, add a
> Curse/Destiny-Bond wrinkle rather than raising levels — the gym's difficulty should live
> in *unfairness*, not stats.

### Vermilion unlock (no battle)

Eve's badge opens the **Route 6 checkpoint** (the Ch5 south gate) on its existing
badge-conditional check — no new trainer, no new flag. The road south to Vermilion and the
S.S. network opens (Chapter 7).

---

## Chapter 7 — Route 6 · Vermilion City · Route 11 · Diglett's Cave (departure)

**Player level by end of chapter:** ~25–26. **Badges:** 2 (Hive + Requiem), **no new
badge** — a travel/transition chapter. Chapter 7 sits **between the badge-2 line (~lv22)
and the badge-3 line (~lv27)** on the whole-game curve. Route 6 + Route 11 + Diglett's
Cave carry a ~lv22 arrival to ~lv25–26 for the crossing to Hoenn. Staging:
[CHAPTER7_BUILD.md](CHAPTER7_BUILD.md); dialogue:
[CHAPTER7_SCENES_SPEC.md](CHAPTER7_SCENES_SPEC.md).

> **Re-tune direction flips here.** Ch6 pulled Kanto's *endgame* Route 7/8 levels **down**.
> Vermilion's approach is different: vanilla **Route 6 grass (~lv12–15)** and **Route 11
> grass (~lv14–16)** sit *below* the player now — so those wilds get **lifted up** to the
> band, the inverse move. Vanilla *trainers* (Route 6 ~lv24, the Vermilion Gym ~lv40s+) are
> still **capped down**. Net: everything converges on the ~lv22–26 Ch7 band. Species stay
> Kanto-faithful; imports stay in the **Trainers' Lodge** (the cosmopolitan port), keeping
> Route 6/11 **native-base** per the Inter-Regional Exchange rule.

### Level anchors

| Subject | Level | Notes |
|---------|-------|-------|
| Route 6 sight-trainers | 22–23 | The descent to the coast; a clean climb off the ~lv22 Saffron exit |
| Route 11 sight-trainers | 23–24 | Slightly above Route 6; the eastern trainer road |
| Fisherman (Route 11) | 23–24 | Build-added; a Magikarp gag lead + two real mons |
| Trainers' Lodge travelers | 24–25 | The cosmopolitan port battles; **one level-capped import each** |
| Diglett's Cave wilds | 22–26 | Diglett common; **Dugtrio** the rare high mark |
| Route 6 / Route 11 wilds | 20–24 | Lifted **up** from vanilla to the band |

No new gym, no boss. The chapter's "climb" is pure route/cave XP toward the first Hoenn
gym; no grinding needed to leave ~lv25–26.

### Wild encounters

Species faithful to vanilla; **levels normalized to the band** (lifted up on the routes,
Diglett's Cave kept in range). Second-stage "commons" softened where a low level reads
oddly (Pidgey over Pidgeotto as the common slot). Per the Inter-Regional Exchange, the
**coastal water** near Vermilion carries one naturalized migrant — a Hoenn **Wingull** —
read as "the port's gulls came in on the boats." Keep it rare.

**Route 6 (`R06`)** — the Saffron→Vermilion descent, grass **lv 20–23**:

| Slot | Species (levels) |
|------|------------------|
| Common | Pidgey → occasional Pidgeotto (lv 20–23) |
| Common | Bellsprout / Oddish (day/night split, lv 20–22) |
| Uncommon | Magnemite (lv 21–22) |
| Uncommon | Abra (lv 20–21) → occasional Kadabra (lv 23) |

**Route 6 coastal water** (surf/rod, the port approach):

| Method | Species (levels) |
|--------|------------------|
| Surf | Psyduck (lv 20–22), occasional Golduck (lv 23) |
| Old/Good Rod | Magikarp (lv 12–20), Poliwag (lv 20–22) |
| Super Rod | Poliwag → Poliwhirl (lv 23–25) |
| **Rare (migrant)** | **Wingull** (Hoenn) (lv 20–22) — the port gull; keep rare |

**Route 11 (`R11`)** — the eastern trainer road, grass **lv 21–24**:

| Slot | Species (levels) |
|------|------------------|
| Common | Rattata → occasional Raticate (lv 21–23) |
| Common | Drowzee (lv 21–23) |
| Uncommon | Magnemite (lv 22–23) |
| Rare | Hypno (lv 24) — the rare high mark |

**Diglett's Cave (`D01R0101`)** — a pure-Ground pocket, **lv 22–26**:

| Slot | Species (levels) |
|------|------------------|
| Common | Diglett (lv 22–24) |
| Rare | Dugtrio (lv 25–26) — the rare high mark |

> **Re-tune note.** Vanilla Diglett's Cave runs Diglett/Dugtrio lv15–29 — already close to
> the band; just seat the common Diglett in the low-20s and let Dugtrio be the rare
> mid-20s spike. A Ground-only cave right before a sea departure is a nice team-check (bring
> a Water/Grass/Ice answer or grind it out).

### Trainer battles

Teams stay **Kanto-base** on the routes; the **Lodge** holds the chapter's imports (one
each, level-capped — justified by a port full of arrivals). Movepools stay route-tier
(Tackle, Gust, Quick Attack, Confusion, Rock Throw, Water Gun, Bite); nothing exotic.

**Route 6 — three battles (four slots, one is a double).** All vanilla `std_trainer`
placements in `011_R06.json`, re-lined as Saffron-corridor day-trippers / coastal locals.
1:1 to the real engine slots:

| Engine slot | Trainer (recast) | Team (origin) | Level | Notes |
|-------------|------------------|---------------|-------|-------|
| `TRAINER_CAMPER_VIRGIL` | Camper Virgil | Sandshrew, **Bulbasaur** | 22, 23 | Kanto-native; the Bulbasaur reads as "a kid's first partner," not a gift |
| `TRAINER_PICNICKER_SELINA` | Picnicker Selina | Bellsprout, Pidgeotto | 22, 23 | Grass + bird, the classic picnicker identity |
| `TRAINER_TWINS_DAY_AND_DANI` (×2) | Twins Day & Dani | **Double:** Day → Meowth 22 + Oddish 22; Dani → Meowth 22 + Oddish 22 | 22 | The matched-pair double; two Meowth, two Oddish across the two twins |

**Route 11 — four battles + the fisherman.** All vanilla `std_trainer` placements in
`016_R11.json`. **DESIGN wants sailors / hikers / a gambler here**, so the two **Psychic**
slots are **reclassed at build (sprite + class swap)** to **Sailor** and **Hiker** with
teams to match; the two **Youngster** slots already fit the gambler-kid + kid-brother and
keep their class. The **fisherman** is a small **build-added** placement (Fisherman class):

| Engine slot | Trainer (recast) | Team (origin) | Level | Notes |
|-------------|------------------|---------------|-------|-------|
| `TRAINER_PSYCHIC_M_FIDEL` | **Sailor** Fidel (reclass) | Machop, Tentacool | 23, 24 | Shore-leave sailor; Kanto-base sea/tough mons |
| `TRAINER_PSYCHIC_M_HERMAN` | **Hiker** Herman (reclass) | Geodude, Onix | 23, 24 | Cave-bound hiker; Kanto Rock/Ground |
| `TRAINER_YOUNGSTER_OWEN` | Youngster Owen (gambler kid) | Spearow, Raticate | 23, 24 | Drifted from the Celadon slots, broke |
| `TRAINER_YOUNGSTER_JASON` | Youngster Jason (kid brother) | Pidgey, Rattata | 22, 23 | The weakest fight; tag-along little brother |
| (build-added Fisherman) | Fisherman | Magikarp, Goldeen, Poliwhirl | 12, 23, 24 | Magikarp is the **gag lead** (lv12 Splash); the real fight is behind it |

> **Reclass note (confirmed).** The Sailor/Hiker reclass is the **chosen** design (matches
> DESIGN's Route 11 archetypes). It's a trainer-data edit (class → sprite + battle label +
> team) — trivial in a romhack. **Emergency-only fallback** (if a sprite swap can't ship):
> keep them Psychics — port-town fortune-tellers/tide-readers with Drowzee/Kadabra/Mr. Mime
> (lv 23–24), which still fits a superstitious sailors' coast. Levels/curve unchanged either
> way.

**Trainers' Lodge — three battles (old Vermilion Gym).** Surge relocated to Mauville; his
3 gym-trainer slots in `322_T06GYM0101.json` are re-lined as **cosmopolitan travelers** —
the chapter's **import battles** (one level-capped import each, justified by a port full of
arrivals; this is the "handful of imports" the Exchange rule allows):

| Engine slot | Trainer (recast) | Team (origin) | Level | Notes |
|-------------|------------------|---------------|-------|-------|
| `TRAINER_GUITARIST_VINCENT` | Sailor (off the Slateport run) | Machop, Tentacool, **Wingull** (Hoenn) | 24, 24, 24 | The Wingull is his character-justified import — "came over on the boat" |
| `TRAINER_JUGGLER_HORTON` | Backpacker (from Olivine) | Geodude, **Mareep** (Johto) | 24, 25 | Walked the Johto coast; the Mareep is a shepherd-country neighbor mon |
| `TRAINER_GENTLEMAN_GREGORY` | Gentleman (well-traveled) | Growlithe, **Skitty** (Hoenn), Persian | 24, 24, 25 | Route high mark; the Skitty is "a gift from a Slateport lady," level-capped |

Lodge tuning: 6 of 9 mons Kanto-native; the 3 imports (Wingull, Mareep, Skitty) are the
character-justified ones, level-capped and concentrated in the cosmopolitan Lodge — Route
6/11 stay 100% Kanto-base. `TRAINER_LEADER_LT_SURGE_LT__SURGE` (255) is **unused** this
chapter (Surge's Electric roster is held for a possible later Mauville cameo).

### Silver — the port cutscene (no battle)

**Silver does not battle in Chapter 7.** The port encounter is a **scripted cutscene**
(congratulations → the Mel probe → the S.S. Ticket) — no `trainer_battle` call. His
appearance is character and plot, not a fight. If/when Silver is battled (a later
Champion-tier encounter), spec his team then, on the whole-game curve, far above this band.
See [CHAPTER7_SCENES_SPEC.md](CHAPTER7_SCENES_SPEC.md) §7.6.

### Departure (no battle)

Boarding the S.S. vessel to Slateport is a cutscene + region hand-off — no encounter. Kanto
battle/encounter tracking ends here; **Chapter 8 opens in Hoenn (Slateport)** and its
battles belong to a Hoenn region doc (`HOENN_BATTLES.md`, created with Chapter 8).
