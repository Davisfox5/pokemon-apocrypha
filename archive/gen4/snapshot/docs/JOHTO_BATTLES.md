# Pokémon Apocrypha — Johto Battles & Encounters

> **Scope:** Wild encounter tables and trainer/gym battles for the **Johto** chapters. One of the per-region battle docs (so no single file bloats). Pairs with:
> - [DESIGN.md](../DESIGN.md) — region/map design + high-level story (canon spine)
> - [JOHTO_ITEMS.md](JOHTO_ITEMS.md) — item & hidden-item locations
> - per-chapter docs (e.g. [CHAPTER1_BUILD.md](CHAPTER1_BUILD.md)) — interactions + chapter quests
>
> **Engine:** pokeheartgold (HGSS). **Latitude:** free redesign, but early Johto stays nostalgically faithful (the classic GSC opening makes the later tonal break land harder).

---

## Level Curve — whole-game reference (Full Epic Scale)

A continuous climb across 20 badges and five regions. Badges interleave regions (the player bounces Johto→Kanto→Hoenn→… per the chapter order), so the curve is **monotonic by badge, not by region**. Trainer and wild levels are tuned to keep the player's lead team roughly **+1 to +3 over the local gym ace** with no grinding, less if they skip optional battles.

**Curve revision — uniform +3 lift (2026-07):** the whole climb was raised ~**+3** to keep the mid-run from feeling slack (the earlier band read slightly low, especially across the no-badge travel chapters). The badge anchors below are the lifted values. The lift **ramps in** from the fixed **lv 5 starter** — Chapter 1 and the earliest Route 30/31 battles stay low; the full +3 is reached by **badge 1** and held from there.

| Badge | Gym ace ~level | Notes |
|-------|----------------|-------|
| Start | 5 (starter) | Cherrygrove (fixed floor; lift ramps in above this) |
| 1 | ~17 | Azalea (Bug) |
| 2 | ~22 | Lavender (Ghost, Eve) — first Kanto badge |
| 5 | ~36 | |
| 10 | ~53 | |
| 15 | ~69 | |
| 20 | ~85 | Final gym (Viridian, Tera) |
| Elite Four / Silver | high-80s (~87–90) | Endgame climax |
| Postgame (Red) | ~90–100 | Mt. Silver |

Wild Pokémon trail the local trainer band by ~3–6 levels. Each chapter section below restates its own anchors (all lifted to match).

---

## Chapter 1 — Cherrygrove · Route 29 · New Bark

**Player level by end of chapter:** ~5–6. **Badges:** 0. **Trainer battles:** none (by design — the first human battles are Chapter 2's Routes 30/31). Chapter 1 teaches battling through wild encounters and a coached catching demo only.

### Level anchors

| Subject | Level | Source |
|---------|-------|--------|
| Player's starter | 5 | Gold's house (Cyndaquil / Totodile / Chikorita) |
| Kestra's starter | 5 | Always the type-advantage counter to the player's pick |
| Catching-tutorial Marill | 5 | Engine demo (temporary, sandbox) |
| Catching-tutorial Rattata | 2 | Engine demo target |

### Wild encounters

**Cherrygrove City** — no catchable land encounters. Surf/fishing water is present but **locked** (no rod until Chapter 2's Route 32; no Surf until much later). The idle boats and southern beach are scenery only this chapter.

**Route 29** — iconic Johto, **lv 2–4**, day/night split. Short and safe.

| Slot | Morning / Day | Night |
|------|---------------|-------|
| Common | Pidgey (lv 2–4) | Hoothoot (lv 2–4) |
| Common | Sentret (lv 2–4) | Sentret (lv 2–4) |
| Uncommon | Rattata (lv 2–4) | Rattata (lv 2–4) |

> Confirmed **no** rare/signature slot — Route 29 stays purely iconic. (Revisit if a signature early catch is wanted later.)

**New Bark Town** — no catchable land encounters. New Bark is a **Pokémon research hub** (see DESIGN.md); the player passes through for the Pokédex. Eastern water is fishing-locked. The deeper research facility is gated for a later return visit.

### Trainer battles

None. The only "battle" content is Gold's **coached catching tutorial** in Cherrygrove (Scene 4): the engine's player-controlled demo (temporary lv5 Marill vs. wild lv2 Rattata, sandbox balls), framed by Gold narrating each step. No XP, party, or bag changes carry out of the demo; the player's real first catch happens on the road.

---

## Chapter 2 — Routes 30/31 · Violet University · Sprout Tower · Union Cave

**Player level by end of chapter:** ~15–17. **Badges:** 0. Chapter 2 is the training chapter: first trainer battles, first rival battle, first pseudo-gym practicum, first dungeon, and the Old Rod. *(Levels reflect the +3 curve lift — ramping in across the chapter from the lv5 start toward badge 1's ~lv17.)*

### Level anchors

| Subject | Level | Notes |
|---------|-------|-------|
| Route 30 trainers | 5–8 | First human battles; Youngsters/Bug Catchers stay gentle (near the lv5 floor) |
| Route 31 trainers | 7–9 | Slight step up; optional Dark Cave mouth nearby |
| Sprout Tower Sages | 9–12 | Status/support lesson, mostly Bellsprout line flavor |
| Roxanne practicum | ace 12 | Not a badge; a deliberately gentle first formal battle test (kept below the Kestra rival spike right after) |
| Kestra rival battle | starter 15 | Type-advantage starter plus route catches |
| Union Cave trainers | 13–15 | First dungeon resource check |

### Wild encounters

**Route 30** — classic early Johto, **lv 3–6**. Keeps Route 29's familiarity but adds Bug/Grass options and a slightly more serious route feel.

| Slot | Morning / Day | Night |
|------|---------------|-------|
| Common | Pidgey (lv 3–5) | Hoothoot (lv 3–5) |
| Common | Rattata (lv 3–5) | Rattata (lv 3–5) |
| Uncommon | Caterpie / Weedle (lv 4–6) | Spinarak (lv 4–6) |
| Rare | Bellsprout (lv 5–6) | Bellsprout (lv 5–6) |

**Route 31** — threshold route into Violet, **lv 5–7**.

| Slot | Morning / Day | Night |
|------|---------------|-------|
| Common | Bellsprout (lv 5–7) | Bellsprout (lv 5–7) |
| Common | Pidgey (lv 5–7) | Hoothoot (lv 5–7) |
| Uncommon | Rattata (lv 5–7) | Rattata (lv 5–7) |
| Rare | Caterpie / Weedle (lv 6–7) | Gastly near Dark Cave edge (lv 6–7) |

**Dark Cave, Route 31 side** — optional sampler only, **lv 5–8**. No Flash yet, so the deep cave remains a promise.

| Slot | All times |
|------|-----------|
| Common | Zubat (lv 5–8) |
| Common | Geodude (lv 5–8) |
| Rare | Dunsparce (lv 6–8) |

**Sprout Tower** — serene training dungeon, **lv 9–12**.

| Slot | All times |
|------|-----------|
| Common | Gastly (lv 9–12) |
| Uncommon | Rattata (lv 9–11) |

**Route 32** — first long road, **lv 10–13**; fishing begins here.

| Slot | Morning / Day | Night |
|------|---------------|-------|
| Common | Mareep (lv 10–12) | Mareep (lv 10–12) |
| Common | Hoppip (lv 10–12) | Wooper (lv 11–13) |
| Uncommon | Ekans (lv 11–13) | Rattata (lv 11–13) |
| Rare | Wooper near water (lv 11–13) | Gastly near ruins/gate edge (lv 11–13) |

**Old Rod, Route 32/Violet ponds** — **lv 5–10**: Magikarp common, Poliwag uncommon where water is calm. *(Old Rod stays flat — fishing pools aren't on the land curve.)*

**Union Cave** — first real dungeon, **lv 11–14**.

| Slot | All times |
|------|-----------|
| Common | Zubat (lv 11–14) |
| Common | Geodude (lv 11–14) |
| Uncommon | Onix (lv 12–14) |
| Uncommon | Sandshrew (lv 12–14) |

**Route 33** — rainy approach to Azalea, **lv 12–15**.

| Slot | Rain / all times |
|------|------------------|
| Common | Hoppip (lv 12–14) |
| Common | Rattata (lv 12–14) |
| Uncommon | Ekans (lv 13–15) |
| Rare | Wooper (lv 13–15) |

### Trainer battles

**Route 30/31 route kids** stay nostalgic and readable: Youngsters with Rattata/Sentret, Bug Catchers with Caterpie/Weedle, one student trainer with Bellsprout to foreshadow Violet. Levels 5–9, one or two Pokemon each (near the lv5 floor — the +3 lift ramps in later in the chapter).

**Sprout Tower Sages** are the first intentional lesson trainers. Teams emphasize Bellsprout, Hoothoot, and Gastly, with status/support moves like Growth, Sleep Powder, Hypnosis, and Reflect appearing as teaching moments rather than hard walls. Levels 9–12.

**Roxanne practicum** (Violet old gym / practice hall):

| Trainer | Team | Level target | Purpose |
|---------|------|--------------|---------|
| Student A | Geodude, Bellsprout | 10–11 | Type pressure + Grass answer |
| Student B | Hoothoot, Mareep | 10–11 | Accuracy/status and Electric coverage |
| Roxanne | Geodude, Nosepass | 11, 12 | First formal test; Rock Tomb reward |

Roxanne is allowed one Hoenn signature Pokemon because she is explicitly a visiting instructor. Keep Nosepass slow and sturdy, not over-tuned; the battle should ask for adaptation, not grinding.

**Kestra rival battle** after Roxanne:

| Player starter | Kestra starter | Suggested team |
|----------------|----------------|----------------|
| Chikorita | Cyndaquil lv 15 | Cyndaquil, Pidgey lv 13, Bellsprout lv 12 |
| Cyndaquil | Totodile lv 15 | Totodile, Sentret lv 13, Hoothoot lv 12 |
| Totodile | Chikorita lv 15 | Chikorita, Pidgey lv 13, Rattata lv 12 |

Her team should feel caught, not curated: ordinary route Pokemon, useful moves, big enthusiasm. She can use one Potion.

**Union Cave trainers** are Hikers, Firebreathers, and fieldwork students at levels 13–15. Teams should include Geodude, Onix, Zubat, Koffing, Vulpix, and one student with Wooper/Mareep to reward Route 32 catches.

---

## Chapter 3 — Azalea · Slowpoke Well · First Gym

**Player level by end of chapter:** ~17–19. **Badges:** 0 → **1 (Hive)**. Chapter 3 is the tonal break: the game's **first double battles** (the Slowpoke Well, fought side-by-side with Turk), the first real gym, and the first badge. The combat should stay readable — this is still early-game tuning — but the *framing* turns cold. See [CHAPTER3_BUILD.md](CHAPTER3_BUILD.md) for staging. *(Levels reflect the +3 curve lift — badge 1's ace is now ~lv17.)*

### Level anchors

| Subject | Level | Notes |
|---------|-------|-------|
| Well operatives (field team) | 12–15 | Re-skinned Rocket-grunt slots; fought as **doubles** with Turk as partner |
| Lead operative (B2F terminal) | 15 | Last double before the data-wipe retreat; no full team, buys time |
| Turk — Well partner (AI) | 13–15 | Spinarak/Ledyba; the player's *first look* at his roster |
| Turk — gym leader (Hive) | ace **17** | Same early Bug line seen in the Well, now 1v1, plus an ace |
| Bugsy | — | **Does not battle.** Officiates Turk's match (see build spec) |
| Optional gym juniors | 14–16 | Keep one or two vanilla Bug-catcher gym trainers before Turk if desired |

Wild Well/Forest encounters trail the trainer band by a few levels per the whole-game curve. The player should reach Turk around lv 17–19 on the lead with no grinding.

### Wild encounters

**Slowpoke Well (`D26`)** — the crime-scene dungeon, **lv 9–15**. Slowpoke are the cultural signature of the place (and the reason the operatives chose it). Kept faithful to the vanilla Well pool — **deliberately all-native, no naturalized imports**. The only foreign presence in the Well is the *human* operation; the *ecology* should still read as untouched home so the violation lands as something done *to* the place, not part of it.

| Slot | All times |
|------|-----------|
| Common | Slowpoke (lv 9–13) |
| Common | Zubat (lv 9–13) |
| Uncommon | Geodude (lv 11–14) |
| Rare | Slowpoke (lv 14–15, deeper floors) |

> The freed-but-harmed Slowpoke shown in the overworld after the Well are **scripted objects**, not encounters — their "wrongness" is staging, not a stat line. Wild Slowpoke remain ordinary.

**Ilex Forest (`D36`)** — atmospheric passage west, **lv 12–17**. Dense, old, day/night split. Headbutt trees stay optional flavor. This is the chapter's showcase of **ecological drift** (DESIGN.md *Inter-Regional Exchange*): one naturalized out-of-region species has settled in, and a native has thinned in response.

| Slot | Morning / Day | Night |
|------|---------------|-------|
| Common | Caterpie / Weedle (lv 12–14) | Hoothoot (lv 12–14) |
| Common | Paras (lv 13–16) | Spinarak / Ledyba (lv 13–16) |
| Uncommon | **Seedot** (Hoenn, naturalized) (lv 12–15) | **Seedot** (Hoenn, naturalized) (lv 12–15) |
| Uncommon | Oddish (lv 12–15, now scarcer) | Oddish (lv 12–15, now scarcer) |
| Rare | Metapod / Kakuna (lv 15–17) | Noctowl (lv 15–17) |
| Water (Old Rod) | Psyduck / Poliwag (lv 13–15) | Psyduck / Poliwag (lv 13–15) |

> **The Ilex displacement story.** Hoenn's **Seedot** — acorn-mimics that hang in broadleaf canopy — drifted in over the last decade and found the old forest's understory wide open. They've crowded the native **Oddish**, which used to be a *common* Ilex grass slot and is now only *uncommon* here; the displaced Oddish population has resettled on the brighter, more open grass of **Route 34** toward Goldenrod (honor this when Ch4's tables are built — Oddish should read as newly-common there). Keep Seedot a single naturalized slot, not a takeover: the point is *believable* ten-year drift, not a Hoenn forest. An old-woodsman NPC line about the woods "feeling different lately" (see [CHAPTER3_BUILD.md](CHAPTER3_BUILD.md) §3.5) now has a concrete, mundane cause.

### Trainer battles

**Slowpoke Well — operative double battles.** The Well ships **exactly four opposing trainers, all placed on B1F** (`170_D26R0102.json`): three sight-trainer grunt slots and Proton as the scripted boss. Re-skin each as a field technician/researcher and rewrite every line — no "Rocket," no R-logos, no names, no villain banter (see build spec). Every fight is a **2v2** with Turk fighting beside the player.

These rosters carry the chapter's two motifs (per DESIGN.md *Inter-Regional Exchange*). The operatives are a **cross-regional corporate crew**, but their teams stay **Johto-based** — mostly Gen 1–2 instrument-like Pokémon (sensors, alarms, gas, sludge) chosen like **equipment, not companions** — with only a **handful of imports** salted in. The two imports' *origins escalate as the player descends* (Hoenn mid-crew, a Sinnoh artifact on the lead): a quiet tell that this is bigger than Azalea, without turning the Well into a foreign zoo. All are low-evolution and level-capped — cross-region access widens the species pool, never the power curve. The table maps 1:1 to the real engine slots:

| Order | Engine slot (re-skin → class) | Operative team (origin) | Level | Turk's partner | Motif read |
|-------|-------------------------------|-------------------------|-------|----------------|------------|
| 1 | `TRAINER_TEAM_ROCKET_GRUNT` → Site Technician | Magnemite (Johto), Voltorb (Johto) | 13, 13 | Spinarak 13 | All-local instruments: a magnet-sensor and an alarm/Self-Destruct "data security" unit. Pokémon as equipment, no import yet |
| 2 | `TRAINER_TEAM_ROCKET_GRUNT_2` → Field Researcher | Koffing (Johto), **Baltoy** (Hoenn) | 13, 14 | Spinarak 13 / Ledyba 14 | Containment gas + the first import: an imported clay artifact that "isn't from around here" |
| 3 | `TRAINER_TEAM_ROCKET_F_GRUNT` → Field Researcher | Grimer (Johto), Magnemite (Johto) | 14, 14 | Ledyba 14 | Back to all-local — waste-containment and a second sensor. Keeps the crew grounded |
| 4 (boss) | `TRAINER_EXECUTIVE_PROTON_PROTON` → **Lead Researcher** (unnamed) | Voltorb (Johto), **Bronzor** (Sinnoh) | 15, 16 | Ledyba 15 | The reach goes farthest on the boss — a **Sinnoh** artifact beside the local hardware. Strip Proton's name/identity entirely |

That's **6 Johto + 2 imports** across the crew (Hoenn → Sinnoh). Tuning notes:

- **The two imports are the foreshadow** — the first shows up mid-descent (Hoenn), the deepest sits with the lead (Sinnoh). The player won't consciously clock it, but the team sheets say "this organization has reach" before the plot does. Keep it subtle; no NPC remarks on it.
- **Instrument-like species sell "Pokémon as equipment"** (Magnemite, Voltorb, Koffing, Grimer read as machines/industrial; Baltoy and Bronzor as artifacts). Keep movepools mundane and utilitarian — Tackle, Sonic Boom, Spark, Smog, Confusion, Harden, Self-Destruct (held in reserve, not led with).
- **Texture by typing:** Electric/Poison/Steel/Psychic gives these fights a distinct feel from the routes' Bug/Normal and the gym's Bug — reinforcing the tonal break (these aren't route kids). Watch coverage: a badge-0/1 player may lack answers to Steel (Bronzor), so keep it slow and low-damage — a puzzle, not a wall. Turk's partner helps here.
- Turk's partners are the local Bug line (Spinarak/Ledyba) he'll bring to the gym — the recognition payoff. Don't surprise-swap his species between the Well and the gym.
- **Placement reality:** vanilla puts all four fights on B1F; the entrance (`D26R0101`) and B2F (`D26R0103`) have **no** trainer battles. **Default (low map surgery):** keep all four fights on B1F and let B2F be the terminal / evidence / data-wipe / retreat scene (no combat). **Optional:** redistribute slots 3–4 to B2F for "descending pressure" pacing — only if a map-object move is worth it.
- Because this is the double-battle tutorial-by-narrative, the player needs ≥2 healthy Pokémon. By Chapter 3 they reliably do; no soft-lock guard needed beyond standard whiteout handling.

**Azalea Gym — the Hive Badge (vs. Turk, Bugsy officiating).** The gym ships **four junior slots + the leader slot**, all already placed in `173_T23GYM0102.json`. Re-line the juniors as **Azalea kids / Turk's trainees** — children who just lived through the Slowpoke scare, not generic Bug Catchers. The **Twins are a built-in double battle**, neatly reinforcing the mechanic the Well just taught. Turk takes the leader slot (`TRAINER_LEADER_BUGSY_BUGSY` re-skinned).

Turk's gym identity is **protection and endurance**, not power — he "fights to protect, not to prove." His team is an endurance core (Shuckle + screen support) with **one** honest hitter, and every member is locally catchable for a kid his level and location (see notes). The juniors are **Johto-based Bug with a couple of imports** among the kids — the *friendly* mirror of the operatives' foreign hardware. Note the contrast: **Turk himself runs an all-Johto team** (the local steward, rooted in Azalea's own ecology), while his younger trainees are the ones casually fielding foreign catches — the shrinking world shows up in the kids first. The table maps 1:1 to the real engine slots:

| Engine slot | Trainer (recast) | Team (origin) | Level | Notes |
|-------------|------------------|---------------|-------|-------|
| `TRAINER_BUG_CATCHER_AL` | Azalea kid Al | Caterpie, Weedle | 14, 14 | Pure local warm-up; unevolved chip |
| `TRAINER_BUG_CATCHER_BENNY` | Azalea kid Benny | Spinarak | 15 | Local; status flavor (String Shot / Poison Sting) |
| `TRAINER_BUG_CATCHER_JOSH` | Azalea kid Josh | Ledyba, **Wurmple** (Hoenn) | 15, 14 | Local Ledyba + a small Hoenn import — "everyone's trading bugs now" |
| `TRAINER_TWINS_AMY_AND_MIMI` | Twins Amy & Mimi | Spinarak + **Nincada** (Hoenn) | 15, 15 | **Double battle.** One local, one "our cousin in Hoenn sent it" import — the benign side of inter-regional exchange |
| `TRAINER_LEADER_BUGSY_BUGSY` → Turk | **Turk (Leader)** | Ledyba, Spinarak, **Shuckle**, **Heracross** | 15, 15, **16**, **17** | **All-Johto** by design. Endurance core + one honest hitter, every member locally catchable (see below) |

Turk / gym tuning:

- **Shuckle (lv16)** is the endurance signature the chapter's protector motif is built on — Withdraw, Encore, Bide, Rock Throw; offensively near-harmless. It teaches patience: the player has to commit and *out-last* it. This deliberately foreshadows the Cianwood Rock-gym leader, whose whole identity is "endurance over aggression." (Shuckle isn't a local catch — normally a Cianwood gift / higher-level water mon — so frame it as Turk's **family/signature** Pokémon, fitting Kurt's lineage, rather than a route grab.)
- **Heracross (lv17)** is the ace and the one real threat — and it is **research-confirmed local**: Heracross is a Headbutt-tree encounter on **Azalea Town (`T23`) and Route 33 (`R33`)** at tree-level lv 3–6 (it's absent from all grass/surf/fishing tables — Headbutt-only, which is why it feels rare). So Turk catching and raising one is authentic to his exact location. **Tune it honest for a first badge:** high Attack but a shallow kit (Leer, Horn Attack, Fury Attack, Endure), no coverage — a prepared player with a Flying / Fire / Psychic answer wins cleanly. This is *not* Heracross's late-game powerhouse self.
- Ledyba/Spinarak run light support (Light Screen, Reflect, String Shot, Supersonic) so the gym's lesson is "protect and outlast," echoing Sprout Tower's status lesson — then the U-turn reward flips that into momentum.
- Juniors stay unevolved and Johto-based, with two small Hoenn imports among them (**Wurmple** on Josh, **Nincada** on the Twins) — the gentle counterpart to the operatives' imports: same world-shrinking principle, benign. Turk's own all-Johto team is the deliberate contrast.
- **Reward:** Hive Badge (engine badge byte via `give_badge`) + **TM89 U-turn** (see [JOHTO_ITEMS.md](JOHTO_ITEMS.md)).
- Bugsy does **not** field a team. If a Bugsy battle is ever wanted later (rematch / post-game), spec it separately; in Chapter 3 he only officiates.

> **Heracross dial:** confirmed local and stage-appropriate, but it *is* a strong species. If it reads too hot for badge 1 in playtest, the lightest swap is **Pinsir** (the other Azalea-area Headbutt/Bug-Contest Bug at lv 16–17) or capping Turk's ace at Shuckle. Both keep the team local and on-motif. Turk's eventual roster (Heracross, Forretress, Scizor, Ariados, Ledian, Shuckle — DESIGN.md) is reserved for a much later rematch, *not* badge 1.

---

## Chapter 4 — Route 34 · Goldenrod · Radio Tower · Magnet Train · Saffron (arrival)

**Player level by end of chapter:** ~19–20 (20 is the ceiling). **Badges:** 1 (Hive) → **1 (no new badge)**. Chapter 4 is the travel/transition chapter — the badge grind pauses and the world widens, so the level gain over Chapter 3 (~17–19) is modest. The **only required battles are the six Route 34 sight-trainers**; the **Kestra send-off** in Goldenrod is the chapter's one "boss." Goldenrod City has no standing overworld trainers (its vanilla object slots are the unused Rocket-takeover set), and **Goldenrod Gym / Whitney is deferred** (see note below). See [CHAPTER4_BUILD.md](CHAPTER4_BUILD.md) for staging and [CHAPTER4_SCENES_SPEC.md](CHAPTER4_SCENES_SPEC.md) for dialogue.

### Level anchors

| Subject | Level | Notes |
|---------|-------|-------|
| Route 34 sight-trainers | 16–19 | Re-lined Goldenrod-outskirts locals; a comfortable warm-up band into the city |
| Kestra — send-off (rival) | ace **21** | Evolved counter-starter + grown Johto catches; the chapter's one real fight, pitched just above the player's ~20 mark |
| Goldenrod Gym (Whitney) | — | **Deferred.** Not fought this chapter; gym closed / leader away until the later Johto return |

The player should reach Goldenrod ~lv 18–19 on the lead with no grinding, and clear Kestra's send-off ~lv 19–20. The Day-Care (Route 34) is introduced here as the chapter's one new *system* — useful for the curve from here on, but not required.

### Wild encounters

**Route 34 (`R34`)** — the open, managed grass on Goldenrod's doorstep, **lv 13–16** (trailing the trainer band per the whole-game curve). This is the **payoff of Chapter 3's Ilex displacement**: the native **Oddish** that Seedot crowded out of Ilex Forest has resettled here, and now reads **newly-common** on the south grass. Being the threshold of Johto's most connected city, Route 34 is also where the game's **Inter-Regional Exchange** is most visible in the wild — a couple of naturalized migrants from far-off regions turn up at the margins (kept rare/swarm, never dominant).

| Slot | Morning / Day | Night |
|------|---------------|-------|
| Common | Rattata (lv 13–15) | Rattata (lv 13–16) |
| Common | **Oddish** (lv 13–15, **newly resettled from Ilex**) | **Oddish** (lv 13–15) |
| Uncommon | Drowzee (lv 13–15) | Drowzee (lv 13–16) |
| Uncommon | Abra (lv 13) | — |
| Rare | Ditto (lv 16) | Ditto (lv 16) |
| Rare (naturalized migrants) | **Whismur** (Hoenn) / **Bidoof** (Sinnoh) (lv 13–15) | **Whismur** (Hoenn) (lv 13–15) |
| Swarm (radio/exchange) | Ralts (lv 15) when active | Ralts (lv 15) |
| Water (Surf) | Tentacool (lv 15–25) | Tentacool (lv 15–25) |
| Water (Old/Good Rod) | Magikarp / Krabby (lv 10–20) | Magikarp / Krabby (lv 10–20) |

> **The Route 34 Oddish payoff.** Honor the Chapter 3 promise (see the Ilex displacement note above): Oddish should read as *abundant* here — whole families on the south grass — where in vanilla it's absent from R34. This is the same ecological-drift principle as Ilex, seen from the *receiving* end: a native pushed out of one place lands, visibly, in another. An NPC names it plainly (see [CHAPTER4_SCENES_SPEC.md](CHAPTER4_SCENES_SPEC.md) §4.0a) — mundane, not ominous. Keep the foreign migrants (**Whismur**/**Bidoof**, both already vanilla R34 "GBA-insertion" slots) **rare**: the point is that Goldenrod's doorstep is *where the world shows up first*, not that the route stopped being Johto.

### Trainer battles

**Route 34 — six sight-trainers.** All six are vanilla `std_trainer` placements in `035_R34.json`, re-lined as Goldenrod-outskirts locals (commuters, a beat cop, a picnicking family, a collector). Teams stay **Johto-base**, with imports appearing only where the *character* justifies it — the rustic trainers (Picnicker, Camper) are all-local; the urban/collector trainers carry the route's naturalized migrants, exactly mirroring the wild table. The two ecological notes pay off **in the trainer teams too**: Picnicker Gina fields the displaced **Oddish**, and collector Pokéfan Brandon fields the route's foreign migrants (**Whismur**/**Bidoof**). The table maps 1:1 to the real engine slots:

| Engine slot | Trainer (recast) | Team (origin) | Level | Notes |
|-------------|------------------|---------------|-------|-------|
| `TRAINER_YOUNGSTER_SAMUEL` | Outskirts kid Samuel | Rattata, Sentret | 16, 16 | Pure-local warm-up; the first fight off the forest road |
| `TRAINER_PICNICKER_GINA` | Picnicker Gina | **Oddish**, Hoppip | 17, 16 | All-Johto; her Oddish is the **displacement payoff** in team form |
| `TRAINER_YOUNGSTER_IAN` | Outskirts kid Ian | Spearow, Rattata | 17, 17 | Local; "I'm better than Samuel" chip |
| `TRAINER_POLICEMAN_KEITH` | Beat cop Keith | **Growlithe** (K-9), Machop | 19, 17 | Growlithe as a police-dog signature; ace of the route. *(Gated `FLAG_UNK_1D2`.)* |
| `TRAINER_CAMPER_TODD` | Camper Todd | Geodude, Poliwag | 18, 17 | All-Johto rustic; "last campsite before the concrete" |
| `TRAINER_POKEFAN_M_BRANDON` | Collector Brandon | **Whismur** (Hoenn), **Bidoof** (Sinnoh) | 18, 18 | The collector who fields the route's **naturalized migrants** — his "anything could walk out of those trees" line in team form |

Route 34 tuning:

- **6 of 8 mons are Johto-native;** the two imports sit with the one trainer whose whole character is collecting from everywhere (Brandon), and they're the *same species the route's wild slots represent*. The imports widen the species pool, never the power curve — all are unevolved/low and level-capped to the route band.
- **Growlithe (Keith, lv19)** is the route's high mark and a deliberate readable threat (Fire-type police dog) — a prepared player handles it, an underleveled one respects it. Keith is gated behind `FLAG_UNK_1D2` in vanilla; honor whatever gate the build keeps, or open him by default.
- Keep movepools route-appropriate (Tackle, Quick Attack, Ember/Bite, Absorb, Rock Throw) — this is a warm-up band, not a wall. The chapter's difficulty lives in the Kestra send-off, not here.

**Goldenrod — Kestra send-off (the chapter's one boss).** Kestra challenges the player before they board the Magnet Train, from the `SPRITE_GSRIVEL` slot in Radio Tower 1F (`109_D23R0101.json`). Her team is the **type-advantage counter-starter** (persisted in `VAR_APOC_FRIEND_STARTER` since Chapter 1, now **evolved**) plus **grown Johto-native catches** — a direct continuation of the Chapter 2 rival roster, leveled up. She is **all-Johto by design**: the homegrown-Johto counterweight to a player about to leave for Kanto. Branch on the player's starter exactly as the Chapter 2 fight did:

| Player starter | Kestra's counter (ace) | Suggested team | Levels |
|----------------|------------------------|----------------|--------|
| **Chikorita** | **Quilava** | Pidgeotto, Bellsprout, Drowzee, Quilava | 19, 18, 18, **21** |
| **Cyndaquil** | **Croconaw** | Furret, Hoothoot, Drowzee, Croconaw | 19, 18, 18, **21** |
| **Totodile** | **Bayleef** | Pidgeotto, Rattata, Drowzee, Bayleef | 19, 18, 18, **21** |

Kestra / send-off tuning:

- **Continuity:** the secondary mons grow forward from her Chapter 2 team (Pidgey→Pidgeotto, Sentret→Furret, the same Bellsprout/Hoothoot/Rattata she had), so a returning player recognizes the same trainer, leveled and evolved. The shared **Drowzee (lv18)** is a small character beat — the Route 34 catch she's weirdly proud of (she walked the same road the player just did).
- **The ace evolved** (Quilava/Croconaw/Bayleef at lv21) keeps the rival type-advantage pressure honest: her starter still answers the player's. A player at ~lv19–20 with a developed team wins, but it's a real fight — she's been training in the city for days, so she sits just above the player's mark.
- **All-Johto on purpose.** The institutional trainers (Slowpoke Well operatives) carried foreign imports to signal organizational *reach*; Kestra carries none, to signal *rootedness*. She is what the player is leaving behind. Don't salt imports into her team.
- **Dial:** this fight exists to give the battle-light chapter a real boss and to hold the per-chapter rival cadence. If a quieter, battle-free goodbye is ever preferred, it can be cut without touching anything else (the roster is self-contained). Default is **keep it.**

> **Goldenrod Gym deferral.** Whitney and the Plain Badge are **not** part of Chapter 4 — `DESIGN.md` sets this chapter at **no new badge**. Keep the gym (`T25GYM0101`) closed or "leader away" until the player's later return to Johto (post-Kanto). When the gym is eventually opened, spec Whitney's team there; the Apocrypha-era roster should follow the same **Johto-base + a handful of level-capped imports** rule the rest of the institutional/League trainers use. Nothing in Chapter 4 should hint the badge is available now.
