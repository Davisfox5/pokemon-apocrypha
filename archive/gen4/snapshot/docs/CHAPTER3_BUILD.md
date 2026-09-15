# Pokemon Apocrypha - Chapter 3 Build Spec

> Scope: Azalea Town, Slowpoke Well, Azalea Gym, Ilex Forest (passage only).
> This is the implementation-facing expansion of the Chapter 3 outline in
> `DESIGN.md`. Pairs with [JOHTO_BATTLES.md](JOHTO_BATTLES.md) (encounter/trainer
> tables), [JOHTO_ITEMS.md](JOHTO_ITEMS.md) (item placement), and
> **[CHAPTER3_SCENES_SPEC.md](CHAPTER3_SCENES_SPEC.md) — the full line-by-line
> dialogue script.** The "Sample lines" in the Cast section below are voice
> references; the complete spoken script lives in the scenes spec.

## Chapter Promise

Chapter 3 is the tonal break. Chapters 1-2 were home, awe, road dust, and
classroom rivalry — a deliberately bright, classic Pokemon opening. Chapter 3 is
where the player walks into their first gym town expecting a badge and finds a
crime scene instead.

Nothing here is loud or melodramatic. The horror is quiet and procedural: a
beloved town has something wrong with it that nobody can name, the people who
caused it are calm professionals rather than cackling villains, and the only
authority who can fix it is the hero the player already worships. The chapter
ends with the player holding their first badge **and** their first unanswered
question. They don't yet know the two are connected.

Core themes:

- **Wrongness without a villain.** The Slowpoke Well operatives never monologue,
  never threaten, and never identify themselves. They are interrupted, they
  protect their data, and they leave. The dread comes from competence, not menace.
- **Earned alliance before rivalry.** The player fights *beside* Turk (Kurt's
  grandson) in the Well before fighting *against* him for the badge. The badge
  match is a friendly test between two kids who already trust each other, not a
  gate guarded by a stranger.
- **The hero arrives.** Silver's first spoken scene is everything the player
  hoped for — warm, attentive, presidential — with one half-second flicker of
  surprise that the player is unlikely to consciously register. The first crack.
- **A planted detail, not a clue.** A Silph Co. logo on a discarded lab coat.
  It means nothing now. It is the lever Chapter 4's journalist will pull.

## Progression Spine

| Beat | Maps | Purpose |
|------|------|---------|
| 3.1 Town under a cloud | Azalea Town (`T23`), Kurt's house | Establish the Slowpoke-as-culture town, the wrongness, recruit Turk |
| 3.2 Into the Well | Slowpoke Well 1F/B1F/B2F (`D26`) | First **double battles**, the operatives, the Silph lab coat, the freeing |
| 3.3 Silver arrives | Azalea Town (Well mouth) | Silver's first speaking scene; the flicker; validation |
| 3.4 The Hive Badge | Azalea Gym (`T23GYM`) | First real gym; player vs. Turk with Bugsy officiating; badge + TM |
| 3.5 Out through Ilex | Ilex Forest (`D36`), gatehouse | Atmospheric passage west; inert Celebi shrine; flavor foreshadowing |

Target start state: lead team ~lv 15-17, 0 badges (carried from Chapter 2).
Target end state: lead team ~lv 17-19, **1 badge (Hive)**, TM89 U-turn, exiting
Ilex Forest toward Goldenrod (Chapter 4).

## Cast

### Turk — Kurt's grandson (Azalea Gym Leader, Bug)

Turk ("Kurt" backward — a family-craft echo, like a ball passed down) is young,
earnest, and a little overwhelmed. He trains under Bugsy and is being groomed as
the gym's successor, but he has never run a real battle that mattered. He loves
the Slowpoke the way every Azalean does — they are family, not wildlife — and the
sight of them hurt is what hardens him over the course of the chapter. He fights
to protect, never to prove. By the gym match he has found a quiet spine he didn't
have that morning.

Voice: gentle, nervous, increasingly resolved. Apologizes when he shouldn't,
stops apologizing by the end.

Sample lines:

- "Gramps can't go down there anymore. His knees, his lungs... but I can. I just
  — I didn't want to go alone. Will you come with me?"
- "They're not even looking at the Slowpoke like they're alive. Like they're
  *equipment.*"  (in the Well, voice cracking)
- "Two of us, two of them. Send yours out — we do this together."  (double-battle prompt)
- "After down there, a gym battle feels... almost simple. Almost." (post-badge)

### Kurt

Elderly now, the master ball craftsman of Azalea. Too frail to climb into the
Well himself, which eats at him — he has lived his whole life within earshot of
that water and knows exactly what it should sound like. The wrongness is
unbearable to him precisely because he can't act on it. He trusts Turk and,
grudgingly, the player. His craft (Apricorn balls) is the warm domestic anchor
the chapter keeps returning to between the cold of the Well.

Voice: gruff, proud, frightened underneath. Talks about the Well the way a
sailor talks about weather.

Sample lines:

- "Sixty years I've slept to the sound of that well. Three nights now it's been
  wrong. *Machine*-wrong."
- "I can't make these old knees do what's needed. So I'll ask a child to do it,
  and I'll hate myself for it the whole time you're down there. Go."
- "You brought them back. Some of them... aren't right. But you brought them back."

### Bugsy

The official Azalea Gym Leader, now mostly a mentor. He is sharper and more
watchful than his cheerful exterior suggests — he clocks the Well situation as
genuinely dangerous and keeps the gym (and Turk's training) as a stabilizing
routine through it. At the badge match he officiates rather than battles: he
wants Turk to fight his own first real battle, and he wants to see what the
player is made of.

Voice: bright, observant, teacherly without condescension.

Sample lines:

- "I could battle you myself. I've decided not to. Turk needs this more than I
  need to win it."
- "Bug Pokemon get underestimated. So do the people who raise them. Watch."
- "You both walked out of that well changed. Let's see what changed *into.*"

### The Field Team (Slowpoke Well operatives)

Not Team Rocket — not in name, not in dress, not in behavior. They wear field
gear and lab coats, carry equipment cases and data tablets, and treat the player
and Turk as an *interruption to a job*, not as enemies. They fight only to buy
time to secure their data, then withdraw through an exit the player can't follow.
The only identifiable branding in the entire operation is a **Silph Co. logo** on
a lab coat draped over a case — and that coat is gone when the dust settles.

Their *Pokémon* are the second tell, if the player is paying attention: a
**Johto base** of instrument-like Pokémon (Magnemite, Voltorb, Koffing, Grimer —
sensors, alarms, containment) salted with a **handful of imports** whose origins
**escalate as the player descends** — a Hoenn **Baltoy** mid-crew, a Sinnoh
**Bronzor** with the lead. Not a foreign zoo; a local-looking crew with two
artifacts that "aren't from around here." This is the chapter quietly showing the
operation's reach before the plot names it — see DESIGN.md *Inter-Regional
Exchange* and the roster table in [JOHTO_BATTLES.md](JOHTO_BATTLES.md). Nobody on
screen remarks on it; it's a team-sheet detail, not a line of dialogue.

Voice: clipped, professional, faintly annoyed. No threats, no ideology, no
gloating.

Sample lines:

- "This site is under private survey. You shouldn't be down here. Neither should
  they, frankly." (gestures at the Slowpoke without warmth)
- "Secure the terminal. Bag the portable units. We were never here."
- "Tell whoever sent you the readings were inconclusive." (a lie, calm, on the way out)

### Lead Operative

Slightly older, in charge, the one who triggers the data wipe. Never named, never
unmasked. The most chilling thing about them is how unbothered they are.

Sample lines:

- "Children. Of course it's children." (the only line with any feeling in it — and
  it's tiredness, not anger)
- "Wipe it. All of it. Leave the husks; they're no use to anyone now."
- (no farewell — just gone)

### Silver (first speaking appearance)

The Champion arrives at the Well mouth almost too fast. For the build, the entire
weight of the scene rides on **one frame of expression** — a flicker of surprise
or calculation as he registers *this* trainer — immediately buried under a warm,
attentive, presidential persona. Everything he says is correct. He listens, he
examines the modified King's Rock with real concern, he may mention that *Gold
spoke of a promising trainer from Cherrygrove*, and he promises League resources.
The player leaves validated by their hero. The dissonance is planted, never stated.

Voice: calm, magnetic, precise. Says exactly the right thing every time — which
is, in retrospect, the tell.

Sample lines:

- "...You." (half a beat too long, then the smile) "You're the one Gold mentioned.
  Cherrygrove. I should have guessed."
- "May I?" (taking the modified King's Rock) "...This is not improvised. Someone
  built this." (a flicker of something — recognition? — gone instantly)
- "You did more today than most trainers do in a year. Leave the rest to the
  League. To me."

### Azalea townsfolk (ambient)

Uneasy, not panicked. Their Slowpoke are family and several are missing or
"acting wrong." Retheme the vanilla Azalea NPC chatter toward quiet dread:
someone counting Slowpoke at the well and coming up short, a kid who can't find
their Slowpoke, the Charcoal Kiln man too distracted to work. After the Well is
cleared, their lines soften to relief shaded with unease — the Slowpoke are back,
but some aren't *right*.

## Scene Details

### 3.1 Azalea Town — Something Is Off

The player enters from Route 33 (south) into a town that should be sleepy and
warm and instead is holding its breath. Slowpoke — normally everywhere — are
scarce. The ones present look lethargic and flinch from contact.

Scenery / staging direction:

- Use the vanilla `FLAG_HIDE_AZALEA_SLOWPOKES` to thin out the wandering Slowpoke
  during the crisis; restore them (cleared flag) after the Well, but leave one or
  two placed "wrong" (static, facing a wall) as the lasting-harm detail.
- The vanilla town already ships a Rocket-harassment beat
  (`FLAG_AZALEA_ROCKET_HARASSING_CIVILIAN` / `FLAG_AZALEA_HARASSED_CIVILIAN` in
  `scr_seq_0866_T23.s`). **Repurpose, don't delete:** reframe the harasser as one
  of the field team blocking the well path "for safety," polite and immovable,
  rather than a shouting grunt.
- Kurt's house (`T23R0501`) is the warm anchor — ball craft, Apricorns, the
  domestic counterweight to the Well's cold. Kurt is too frail to descend.
- The friend-rival (Kestra) is **not** here — per DESIGN.md she went ahead to the
  gym and hasn't noticed the Well. Keep her off the Azalea overworld this chapter
  until the gym epilogue if desired (a single "where were you?" line works).

Beat flow:

1. On entry, a one-time coordinate scene establishes the unease (townsperson
   counting Slowpoke, coming up short). Gate behind a new
   `FLAG_APOC_CH3_AZALEA_INTRO_DONE`.
2. Talking to Kurt (in the house or at the well mouth) explains the machine-wrong
   sounds and points the player at Turk.
3. Turk, near the gym or the well, asks the player to descend *with* him. His ask
   is the double-battle setup — he explicitly wants a partner, not backup.
4. Kurt gives grudging blessing; the well entrance opens.

### 3.2 Slowpoke Well — The First Rocket Encounter

The Well is the chapter's centerpiece and the game's **double-battle tutorial by
narrative** — every operative fight is a 2v2 with Turk as the AI partner. Descend
across the three vanilla sub-maps (Entrance `D26R0101` → B1F `D26R0102` → B2F
`D26R0103`).

Down the floors, the player and Turk find monitoring stations around captive
Slowpoke: King's Rock devices and other evolutionary items applied under
controlled, forced, accelerated-evolution conditions. Data logs record
transformation rates, stress responses, energy output. It reads as a lab, not a
hideout. The single identifiable detail: a lab coat over an equipment case with a
**Silph Co. logo** on the breast pocket.

Combat structure:

- The Well ships **exactly four opposing trainers, all on B1F** (`170_D26R0102.json`):
  three sight-trainers — `TRAINER_TEAM_ROCKET_GRUNT`, `TRAINER_TEAM_ROCKET_GRUNT_2`,
  `TRAINER_TEAM_ROCKET_F_GRUNT` — and the scripted boss `TRAINER_EXECUTIVE_PROTON_PROTON`
  (in `scr_seq_0060_D26R0102.s`). Re-skin all four as field techs/researchers; the
  Proton slot becomes the unnamed **Lead Operative** (strip the name entirely). The
  entrance (`D26R0101`) and B2F (`D26R0103`) have **no** trainer battles in vanilla.
- Every fight is a 2v2 with Turk (Spinarak/Ledyba) as partner. The operatives field
  a **Johto base of instrument-like Pokémon** with a **handful of imports** whose
  origins escalate as you descend (a Hoenn Baltoy mid-crew, a Sinnoh Bronzor on the
  lead) — the quiet "this is bigger than Azalea" tell. Full 1:1 slot→roster mapping
  is in [JOHTO_BATTLES.md](JOHTO_BATTLES.md).
- **Default (low surgery):** keep all four fights on B1F; make B2F the terminal /
  evidence / data-wipe / retreat scene where the **Lead Operative** triggers the
  wipe, grabs portable equipment (and the Silph coat), and exits through a back way
  the player can't follow. Redistributing fights down to B2F is optional pacing,
  not required.
- The Slowpoke are freed (clear `FLAG_HIDE_AZALEA_SLOWPOKES` on exit) but some
  show lasting effects. Leave fragments behind: a few un-wiped data logs (read-only
  flavor objects), a single **modified King's Rock** with unfamiliar circuitry
  (the object Silver examines later). The Silph coat is *gone* — the player saw it,
  but it isn't recoverable.

Implementation notes:

- Reuse the **four trainer slots vanilla already places in the Well**
  (`TRAINER_TEAM_ROCKET_GRUNT`, `_GRUNT_2`, `_F_GRUNT`, and `TRAINER_EXECUTIVE_PROTON_PROTON`)
  but re-skin sprites to field-tech/researcher and rewrite every line — no "Team
  Rocket," no R logos, no Proton name, no villain music. The encounter should feel
  like catching contractors mid-job.
- Drive the partner battles with a Well-progress var (`VAR_APOC_CH3_WELL_PROGRESS`)
  rather than many one-shot flags.
- The vanilla `FLAG_GOT_KINGS_ROCK_FROM_SLOWPOKE_WELL_MAN` King's Rock gift is
  *narratively occupied* by the modified-King's-Rock evidence beat — repurpose the
  reward (see ITEMS) so a King's Rock isn't handed out as loot mid-crime-scene.

### 3.3 Silver Arrives

The player and Turk surface into daylight; Kurt and a small crowd wait. Silver is
already there.

Staging direction:

- He arrives "too fast" — don't explain it, just have him already present when the
  warp-out completes.
- **The flicker:** a single brief alternate-expression frame or a half-second
  pause before his first line as he registers the player specifically. This is the
  whole point of the scene; it must be subtle enough to miss on a first read.
- He examines the modified King's Rock (the evidence object from the Well), shows
  real concern, validates the player (the Gold-from-Cherrygrove line), and
  promises League follow-up. Warm, never dismissive, never alarmist.
- Gate the scene behind well-cleared state; set `FLAG_APOC_CH3_SILVER_MET` on
  completion so it never replays. Silver should then leave the overworld (reuse a
  fly-off or a clean walk-off depending on available sprites).
- Turk's post-scene line lands the character shift: relieved, shaken, hardened.

### 3.4 The Azalea Gym — First Badge

The badge challenge. Bugsy officiates; the player's opponent is **Turk**.

Staging direction:

- Keep the vanilla Azalea Gym layout and its spinarak-web ride/switch puzzle
  (engine routines `BeginAzaleaGymSpinarakRide`, `FlipAzaleaGymSwitch`; macros
  `azalea_gym_init`, `azalea_gym_spinarak`, `azalea_gym_switch`). It's a good,
  thematic first-gym traversal.
- Bugsy is present (control via `FLAG_HIDE_AZALEA_GYM_BUGSY`) but does **not**
  battle — he introduces the match, then officiates.
- Keep all **four vanilla gym juniors** placed in `173_T23GYM0102.json` — Bug
  Catchers `AL`, `BENNY`, `JOSH`, and the `TWINS_AMY_AND_MIMI` (a built-in **double
  battle**, which reinforces the Well's lesson). Re-line them as Turk's students /
  Azalea kids. Turk takes the leader slot (`TRAINER_LEADER_BUGSY_BUGSY` re-skinned).
  Full rosters in [JOHTO_BATTLES.md](JOHTO_BATTLES.md).
- Turk's gym team reads as **protection and endurance**, not power: the local Bug
  line the player saw in the Well (Spinarak/Ledyba, support-leaning) anchored by a
  **Shuckle** wall, with a single honest hitter — a **Heracross** ace — as the one
  real threat. Both signatures are stage-appropriate and location-authentic
  (Heracross is a confirmed Headbutt-tree catch on Azalea Town and Route 33;
  Shuckle is framed as his family/Kurt-lineage Pokémon). Full rosters, tuning, and
  the Heracross-vs-Pinsir dial are in [JOHTO_BATTLES.md](JOHTO_BATTLES.md). The
  player having *seen* his support Bugs in the Well is the intended payoff.
- On win: award the **Hive Badge** (give_badge) and **TM89 U-turn**. U-turn is
  thematically perfect (hit-and-switch momentum, the gym's first real strategic
  lesson) and matches the vanilla Azalea reward.
- Bugsy congratulates both; Turk concedes gracefully (no rivalry — that's
  Kestra's role). Set `FLAG_APOC_CH3_BADGE_DONE`. Register the Azalea fly point
  (`FLAG_SYS_FLYPOINT_AZALEA`) here if not already set on town entry.

### 3.5 Ilex Forest — Passage Only

West out of Azalea through the gatehouse (`T23R0101`) into Ilex Forest (`D36`),
toward Goldenrod and Chapter 4.

Staging direction:

- The forest is **just a forest** this chapter. The Celebi shrine is visible and
  inert: no temporal event, no equipment, no researchers.
- Atmosphere over plot: keep it dense, old, and quiet. Retheme a woodsman / a
  couple of NPCs toward "the woods feel different lately," "the air around the
  shrine feels heavier" — flavor, not hooks. No required content beyond passage.
- **Ecological-drift flavor (mundane, not ominous):** the "woods feel different"
  line has a concrete, benign cause — Hoenn's **Seedot** has naturalized in Ilex
  over the last decade and thinned the native Oddish (see the Ilex wild table +
  displacement note in [JOHTO_BATTLES.md](JOHTO_BATTLES.md)). Let the woodsman name
  it plainly: strange little acorn-Pokémon in the trees that weren't here when he
  was young, and the radish-Pokémon gone quiet. This is *world-is-changing* texture,
  deliberately **separate** from the shrine's "something is watching" unease — two
  different kinds of "different," one ecological and ordinary, one supernatural and
  saved for later. Don't let the NPC conflate them.
- Preserve the vanilla Ilex traversal (Headbutt trees, the Farfetch'd cut-tree
  guidance beat if kept) as optional flavor; none of it is gated story.
- The west exit hands off to Goldenrod (Chapter 4). No badge, item gate, or HM
  requirement is introduced here.

## State And Files

Confirmed map/script targets (from `disasm/pokeheartgold`,
`include/constants/maps.h` and `files/fielddata/...`):

| Area | Map JSON | Script | Map constant |
|------|----------|--------|--------------|
| Azalea Town | `071_T23.json` | `scr_seq_0866_T23.s` | `MAP_AZALEA` (74) |
| Azalea ↔ Ilex Gatehouse | `097_T23R0101.json` | `scr_seq_0872_T23R0101.s` | `MAP_AZALEA_ILEX_FOREST_GATEHOUSE` (100) |
| Charcoal Kiln | `157_T23R0201.json` | `scr_seq_0873_T23R0201.s` | `MAP_AZALEA_CHARCOAL_KILN` (163) |
| Kurt's House | `158_T23R0501.json` | `scr_seq_0874_T23R0501.s` | `MAP_AZALEA_KURT_HOUSE` (164) |
| Azalea Mart | `159_T23FS0101.json` | — | `MAP_AZALEA_POKEMART` (165) |
| Azalea Pokémon Center 1F | `160_T23PC0101.json` | — | `MAP_AZALEA_POKECENTER_1F` (166) |
| Azalea Gym (entrance) | `132_T23GYM0101.json` | `scr_seq_0868_T23GYM0101.s` | `MAP_AZALEA_GYM_ENTRANCE` (136) |
| Azalea Gym (arena) | `173_T23GYM0102.json` | `scr_seq_0869_T23GYM0102.s` | `MAP_AZALEA_GYM` (180) |
| Slowpoke Well — Entrance | `111_D26R0101.json` | `scr_seq_0059_D26R0101.s` | `MAP_SLOWPOKE_WELL_ENTRANCE` (114) |
| Slowpoke Well — B1F | `170_D26R0102.json` | `scr_seq_0060_D26R0102.s` | `MAP_SLOWPOKE_WELL_B1F` (177) |
| Slowpoke Well — B2F | `174_D26R0103.json` | `scr_seq_0061_D26R0103.s` | `MAP_SLOWPOKE_WELL_B2F` (181) |
| Ilex Forest | `114_D36R0101.json` | `scr_seq_0092_D36R0101.s` | `MAP_ILEX_FOREST` (117) |

### Flags & vars

**Reuse (vanilla, already wired):**

- `FLAG_BEAT_AZALEA_ROCKETS` (`0x7B`) — set once the Well operatives are cleared.
- `FLAG_HIDE_AZALEA_SLOWPOKES` (`0x1AB`) — thins Slowpoke during the crisis;
  clear after the Well to restore them (leave 1-2 placed "wrong").
- `FLAG_AZALEA_ROCKET_HARASSING_CIVILIAN` (`0x271`),
  `FLAG_AZALEA_HARASSED_CIVILIAN` (`0x272`) — repurpose the existing town-tension
  beat as the polite "well is closed for survey" blocker.
- `FLAG_HIDE_AZALEA_GYM_BUGSY` (`0x2EA`) — Bugsy presence in the gym (present but
  officiating, not battling).
- `FLAG_SYS_FLYPOINT_AZALEA` (`0x9BE`) — fly-point registration.
- `FLAG_GOT_CHARCOAL_FROM_AZALEA_TOWN_MAN` (`0x81`) / `FLAG_DAILY_KURT_MAKING_BALLS`
  (`0xAA2`) — leave Kurt's Apricorn-ball and the Charcoal Kiln loops intact as
  warm flavor.
- Well trainer slots (all on B1F): `TRAINER_TEAM_ROCKET_GRUNT` (12), `_GRUNT_2`,
  `_F_GRUNT`, and boss `TRAINER_EXECUTIVE_PROTON_PROTON` — re-skin + re-line as the
  field team / unnamed Lead Operative; do not surface "Rocket" or "Proton" in
  dialogue.
- Gym trainer slots: `TRAINER_BUG_CATCHER_AL`, `_BENNY`, `_JOSH`,
  `TRAINER_TWINS_AMY_AND_MIMI` (double), and `TRAINER_LEADER_BUGSY_BUGSY` (→ Turk).
  All already placed in `173_T23GYM0102.json`; re-line and re-team per BATTLES.
- `FLAG_GOT_KINGS_ROCK_FROM_SLOWPOKE_WELL_MAN` (`0x7A`) — **do not** use as a loot
  gift here (a King's Rock handout clashes with the crime-scene tone). The King's
  Rock concept appears instead as the *modified-King's-Rock evidence object*.

**New custom flags to allocate** (free `FLAG_UNK_*` slots adjacent to the existing
APOC block at `0x22E-0x233`; confirm still free at implementation time):

- `FLAG_APOC_CH3_AZALEA_INTRO_DONE` (`0x234`) — town-unease intro + Turk recruit
  one-shot.
- `FLAG_APOC_CH3_WELL_CLEARED` (`0x239`) — narrative completion of the Well (pair
  with vanilla `FLAG_BEAT_AZALEA_ROCKETS` for object hides).
- `FLAG_APOC_CH3_SILVER_MET` (`0x23A`) — Silver's first-speaking scene one-shot.
- `FLAG_APOC_CH3_BADGE_DONE` (`0x23B`) — gym/Turk battle complete (badge
  possession itself is the engine badge byte via `give_badge`, not a flag).

**New custom var:**

- `VAR_APOC_CH3_WELL_PROGRESS` (free `0x403x`, e.g. `0x4032`) — drives the
  double-battle wave sequencing through the three Well sub-maps.

> Allocation discipline matches Chapters 1-2: prefer free `FLAG_UNK_*` in the
> hide/APOC range and a free `0x40xx` var, and re-skin vanilla trainer/event
> slots rather than adding new ones. Verify each slot is still unused at build
> time (several nearby `UNK_23x` flags are claimed by later Johto maps).

## Implementation Order

1. **Azalea town pass** — entry unease coordinate scene, retheme NPC chatter,
   repurpose the harassment beat as the polite well-blocker, place Turk + wire the
   recruit dialogue. (`scr_seq_0866_T23.s`, `071_T23.json`)
2. **Kurt scene** — house/well-mouth dialogue, grudging blessing, open the well.
   (`scr_seq_0874_T23R0501.s`)
3. **Slowpoke Well doubles** — re-skin + re-line the grunt slots as the field
   team; build the partner double battles across `D26R0101/02/03`; place the
   monitoring stations, Silph-coat detail, un-wiped logs, modified King's Rock,
   and the lead operative's data-wipe/retreat. (`scr_seq_0059/0060/0061_D26R...`)
4. **Silver arrival** — Well-mouth scene with the flicker, King's-Rock exam,
   validation, promise, walk/fly-off. (`scr_seq_0866_T23.s`)
5. **Azalea Gym** — keep the spinarak-web puzzle; Bugsy officiates; Turk badge
   match; Hive Badge + TM89 U-turn. (`scr_seq_0868/0869_T23GYM...`)
6. **Ilex Forest** — atmospheric flavor pass, inert shrine, "woods feel
   different" lines, clean handoff west to Goldenrod. (`scr_seq_0092_D36R0101.s`)
7. **Items/economy pass** — see [JOHTO_ITEMS.md](JOHTO_ITEMS.md): Azalea Mart
   restock, Well field items, the modified-King's-Rock evidence object, Charcoal
   Kiln reward, badge TM wiring.
8. **Encounter/level pass** — see [JOHTO_BATTLES.md](JOHTO_BATTLES.md): Well wild
   table, Ilex Forest wild table, operative double-battle teams, Turk's gym team.
</content>
</invoke>

---

## Implementation status (2026-07-01)

**Status: ✅ implemented** (all five beats), builds clean (`MAKE EXIT=0`). Not yet
play-tested; staging coordinates need an emulator pass.

### What shipped

- **Data pass:** Well field team all TRAINERCLASS_SCIENTIST (no Rocket
  uniforms), split into paired 1-mon entries for the `multi_battle` 2v2 grid
  (b-sides on vacated hideout slots GRUNT_20/21/25/26); Proton slot = unnamed
  "Lead"; Turk tag partner on `TRAINER_PARTNER_RIVAL_1` (Ethan backpic);
  Turk badge team on the Bugsy slot (BUG_CATCHER class: Ledyba/Spinarak
  screens+web, Shuckle wall, Heracross 17); juniors incl. Hoenn imports
  (Nincada, Surskit twin); Well + Ilex (Seedot/Oddish drift) wild tables.
- **3.0/3.1:** entry counting-townsman one-shot (gsman1 rehomed to the rim,
  pre/post states); polite survey blocker on the vanilla harassment
  machinery; bench/kiln/wrong-Slowpoke ambience; Kurt recruits (no well
  jump), post-clear thanks = King's Rock (re-sited per JOHTO_ITEMS) then the
  untouched vanilla Apricorn crafting loop; Bubbles girl pre/post.
- **3.2:** Turk recruit (yes/no) warps both down; descending un-recruited
  bounces you out; three tech fights + Lead, all 2v2 beside Turk, trainer-flag
  gated, any order (Lead beatable on arrival — the techs are pressure, not
  gates); ring/terminal examines on the captive-Slowpoke objects; Silph coat
  case (CARDBOARDBOX sprite) vanishes in the wipe; Lead walk-off; clear
  restores Slowpoke and keeps vanilla downstream (Farfetch'd/kiln beats).
- **3.3:** Silver at the well mouth behind a surfacing fade; flicker = 45-frame
  pause before "...You."; King's Rock exam; League promise; Kurt + Turk
  buttons; reveals gym Turk.
- **3.4:** Bugsy officiates (object kept, rematch logic retired); gym Turk
  badge match -> Hive Badge + TM89 + the enduring/leaving lesson; Kestra
  west-exit epilogue on the vanilla ambush trigger (`VAR_UNK_4075` 1→2).
- **3.5:** gatehouse warning; headbutt tutor doubles as the ecological
  woodsman (Seedot/Oddish, kept mundane); shrine plaque + heavier-air girl
  (kept supernatural-separate). Vanilla Celebi/Pichu event machinery left
  in place (inert without event items).

### Flags/vars

`0x417-0x41F`: HIDE_TURK_TOWN, SILVER_MET, BADGE_DONE, HIDE_SILVER_T23,
HIDE_KURT_T23, HIDE_KESTRA_T23, HIDE_WELL_CASE, KINGSROCK_TAKEN,
HIDE_TURK_GYM. `0x409` re-purposed as FLAG_APOC_ALWAYS_HIDDEN (retires the
fallen-Kurt objects). Vars: `VAR_APOC_CH3_WELL_PROGRESS` (0x4034; 1=recruited,
5=cleared), `VAR_APOC_CH3_AZALEA_SCENE` (0x4038; 0 intro→1→2 Silver
pending→3 done). `_std_init` seeds the town-actor hides.

### Known deviations / notes for polish

- Turk is not visually present during the Well descent (engine: NPCs can't
  follow across maps). He IS in every battle (backpic + party) and speaks in
  every beat; a per-floor placed Turk could be added in a polish pass.
- Each operative displays as two same-named SCIENTIST trainers in battle
  (multi_battle needs two opponent entries).
- The two-tile trigger bands at the east entry (x438/x442) and the well-mouth
  (433-434,455), plus the Silver-scene actor spots, are map-data guesses —
  playtest items 1-5 below.

### Playtest checklist

1. East-entry intro trigger fires (bands at x438/x442, z460-470).
2. Recruit warp lands at (17,8) in the well entrance; bounce gate at (16-18,9)
   catches an un-recruited entry.
3. B1F battles: multi_battle partner backpic renders (Ethan), operative pairs
   correct; loss white-out re-entry state sane.
4. Lead post-battle staging, case/ring hides, Slowpoke restoration on T23.
5. Silver scene at (433-434,455): fade staging, walk-offs, gym Turk reveal.
6. Gym: web puzzle intact, Turk battle, badge/TM89, Kestra epilogue at the
   west exit; her run-off.
7. Kurt crafting loop still works after the King's Rock thanks.
