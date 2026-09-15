# Chapter 6 — Scene Spec & Full Script (Route 8 · Celadon · Lavender · Eve's Ghost Gym)

This is the **complete line-by-line dialogue** for Chapter 6, the single source of
truth for what every character says. It sits one altitude below
[CHAPTER6_BUILD.md](CHAPTER6_BUILD.md) (staging, flags, files) and pairs with
[KANTO_BATTLES.md](KANTO_BATTLES.md) (rosters) and [KANTO_ITEMS.md](KANTO_ITEMS.md).

**Status:** ⬜ not implemented — writing pass. Engine wiring (`.gmm` banks, `npc_msg`,
`scr_seq` hooks) happens at implementation; no message IDs assigned yet.

**Conventions:**
- `{PLAYER}` = player name token. No `{RIVAL}` this chapter (Kestra's in Goldenrod).
- Battle lines use **[Pre]** / **[Loss]** / **[Post]**. Route 8 + gym + optional
  battles map to **real engine trainer slots** (verified from `013_R08.json` /
  `352_T07GYM0101.json`); see [KANTO_BATTLES.md](KANTO_BATTLES.md).
- *Italic parentheticals* are staging cues, not spoken. House style: drive with
  dialogue, minimal narration ([[dialogue-over-narration]]).
- **Mary is seen, never named.** **Looker is unnamed.** Both are deliberate.
- **Eve runs Gen-1 Kanto ghosts only** — no imports; that's a character statement.

---

## 6.0 · Route 8 — The Road East (the spine)

*The required path from Saffron to Lavender. Landscape loosening from city grid to open
country. Seven sight-trainers, re-lined as Kanto-corridor locals.*

**Route 8 sign:** "ROUTE 8 — Lavender Town, east. Broadcasting to all of Kanto!"

### 6.0a · Route 8 sight-trainers (seven)

*All vanilla `std_trainer` placements in `013_R08.json`. Rosters/levels in
[KANTO_BATTLES.md](KANTO_BATTLES.md).*

**Biker Dwayne** — `TRAINER_BIKER_DWAYNE`
- **[Pre]:** "You walk this road? Nobody *walks* this road. We ride it. Loud. All day."
- **[Loss]:** "Tch. Walker beat me. Don't tell the crew."
- **[Post]:** "Lavender's dead ahead. Used to give me the creeps. Now it's all antennas
  and coffee. Progress, I guess. I kinda miss the creeps."

**Biker Harris** — `TRAINER_BIKER_HARRIS`
- **[Pre]:** "Dwayne go down already? Useless. Fine — my turn."
- **[Loss]:** "...Okay, you're not nothing."
- **[Post]:** "Go on. Nothing out here but us and the road noise."

**Biker Zeke** — `TRAINER_BIKER_ZEKE`
- **[Pre]:** "Three of us on this stretch. You beat two. Math says you're due to lose."
- **[Loss]:** "Math lied."
- **[Post]:** "Whatever. Ride safe. Walk safe. Whatever it is you do."

**Super Nerd Sam** — `TRAINER_SUPER_NERD_SAM`
- **[Pre]:** "I moved out here for the signal, you know. Best broadcast reception in
  Kanto, right by the tower. My devices have never been happier. Battle me."
- **[Loss]:** "Statistically improbable. I'll be recalculating this for a week."
- **[Post]:** "Did you know the tower rebroadcasts to four regions now? Four! You can
  hear Sinnoh weather in Lavender. What a time."

**Super Nerd Tyrone** — `TRAINER_SUPER_NERD_TYRONE`
- **[Pre]:** "Sam and I have a bet on who loses to fewer trainers this month. He's
  winning. Which means I need to beat you. No pressure. All pressure."
- **[Loss]:** "...He's going to be insufferable."
- **[Post]:** "The gym in Lavender's the real test. Ghost types. They don't play fair.
  Nothing about that town plays fair, honestly."

**Young Couple Moe & Lulu** — `TRAINER_YOUNG_COUPLE_MOE_AND_LULU` *(double battle)*
- **[Pre]** (Moe): "We're on a walking tour of Kanto! Romantic, right?" (Lulu): "It was
  romantic four blisters ago. Battle us, it'll cheer me up."
- **[Loss]** (Lulu): "Okay THAT cheered me up." (Moe): "...We lost, though?" (Lulu):
  "Details."
- **[Post]:** "Lavender's lovely this time of year. Well — 'lovely.' It's got a *vibe.*
  You'll see. Enjoy!"

**Gentleman Milton** — `TRAINER_GENTLEMAN_MILTON`
- **[Pre]:** "A young trainer, on foot, off the Saffron road. You have the look of
  someone the week has *happened* to. Allow me to make it worse. Or better. Let's find
  out."
- **[Loss]:** "Ha! Splendid. The week clearly sharpened you rather than dulled you."
- **[Post]:** "Lavender ahead. Don't let the antennas fool you — the best thing in that
  town is tucked in a dark little building nobody advertises. Ask about the gym."

---

## 6.1 · Celadon City — Optional Detour

**Intent:** an optional reward city — market/services, gardens, hotel, café quest, Game
Corner — bookended by the Cycling Road dead-end. Nothing here gates progression.

**Celadon sign:** "CELADON CITY — The City of Rainbow Dreams. Rebuilt by its people."

### 6.1a · Street ambient (talk-to, optional)

**Proud local:** "Isn't it something? You'd never know this city was *occupied* once.
We tore out what they left and planted gardens over it. Best revenge there is —
getting *nicer.*"

**Market vendor:** "Fresh from the stalls! We're not a mall, hon, we're a *market* —
you haggle, you sample, you make a friend or two. The department store's still here but
it does *services* now. Go get your Pokémon a bath, you monster, look at it."

### 6.1b · Daisy Oak — the salon (services building)

**Daisy Oak:** "Oh, hello! You look like you've been on the road a while — and so does
this little one." *(she means the player's Pokémon)* "I'm Daisy. I run the salon. No
battling, no training — just care. You'd be amazed what a good grooming does for a
Pokémon that's been fighting nonstop."

**Daisy Oak:** "My brother battles. My grandfather practically *invented* battling. And
me? I brush a Growlithe till it falls asleep in my lap and I wouldn't trade it for a
championship." *(warm)* "Bring yours by anytime. Free the first visit — you look like
you needed a kind face more than a fee."

### 6.1c · The Botanical Gardens (Erika · Janine · Aaron)

**Erika:** "Welcome to the gardens. Mind the Bellossom, they're napping in the sun."
*(gracious)* "You're the Johto one, aren't you — the stranded trainer. Word travels,
even to a garden. You had a rough time in Saffron, I hear. Those two dojos..." *(a small
sigh)* "...proud old houses, behaving like children. Silph's shadow makes everyone
smaller. I got out of the gym business before it could make *me* smaller."

**Erika:** "Here — take this. It grows only in these beds." *(gives a **botanical gift**
— berry / nature-themed held item; see [KANTO_ITEMS.md](KANTO_ITEMS.md))* "A little
piece of a place that chose to grow instead of fight. Carry it east."

**Janine:** *(not looking up from a specimen)* "Erika grows the questions. I answer
them. This nightshade, for instance — same alkaloid family as a Weezing's exhaust.
Nature wrote the poison first; the Pokémon just... learned to sing it." *(glances at the
player)* "Koga's daughter. You'll have heard the name if you know Fuchsia. I traded the
gym for a laboratory. Everyone in this garden traded a gym for something quieter. Funny,
that."

**Aaron:** *(net in one hand, sketchbook in the other, already talking)* "— and THAT'S
a Kanto Scyther morph you do NOT get in Sinnoh, look at the mandible curve, it's the
humidity, it HAS to be the humidity —" *(spots the player)* "Oh! Hi! Sorry! I'm Aaron,
I study Bug-types, I'm from Sinnoh, this garden is a MIRACLE, do you battle?"
- **[Pre]:** "Yes! Okay! Nothing serious — just for the joy of it! Show me what a Johto
  team looks like up close! GO!"
- **[Loss]:** "Ahh, beautiful, beautiful — you read the type matchups like you *breathe*
  them. I'm keeping notes on you."
- **[Post]:** "If you ever make it to Sinnoh — and you should, everyone should — the Bug
  routes there will change your life. Tell them Aaron sent you. They'll know. They'll
  sigh, but they'll know."

### 6.1d · The Pokémon Hotel (Looker upstairs)

**Hotel collector (lobby):** "Every one of these is from a different region. Took me
fifteen years. People say 'why not just trade for them fast, the networks are open now'
— because the *point* is the fifteen years, that's why!"

**Arguing couple (hallway):** (A) "Hoenn food is the best food, this is not a debate—"
(B) "You said that in Unova about Unova food. You have no loyalty, only appetite."

**The bored cop (Looker — upstairs room, unnamed):** *(files everywhere, cold coffee)*
"Hm? Oh — sorry, come in, don't mind the mess. Occupational habit; I bring the case
files even when there's no case." *(rubs his eyes)* "International police. I go where the
crime is. Problem is..." *(gestures at the empty desk)* "...there isn't any. Not here.
Not in the whole Johto-Kanto corridor. Cleanest it's been in my entire career."

**The bored cop:** "You want to know the funny part?" *(a rueful laugh)* "It's *him.*
The Champion. Silver. Ever since he took the seat, organized crime just — evaporated.
The trafficking rings, the black labs, the old Rocket remnants. Gone. Handled." *(shakes
his head, admiring)* "Who would've thought — the son of the man who *ran* the greatest
evil organization in history, and he grows up to be the best thing that ever happened to
law and order? Life's a strange story."

**The bored cop:** "Anyway. I'll move on soon. Nothing to solve in a safe world.
Pleasure meeting you, traveler. If crime ever *does* find you..." *(he doesn't finish;
he's already back to a file he doesn't need to read.)*

*(The player meets a cop with nothing to do and moves on. His admiration for Silver is
genuine. His name is never given.)*

### 6.1e · The Café — the Fan Club Chairman quest

**Café owner:** *(harried)* "Oh thank goodness, a customer who isn't— " *(lowers voice)*
"—him. That gentleman's been at that table for THREE HOURS talking about his horse
Pokémon and I'm too polite to shoo him and now I'm behind on the event prep and I'm
missing an ingredient and everything is ON FIRE. Metaphorically. The kitchen is fine."

**Pokémon Fan Club Chairman:** *(guiltily)* "...She's talking about me, isn't she. I do
that. I get to talking about my Rapidash and I lose the *thread* of the room." *(stands)*
"Let me make it right — I can't cook, but you look capable. She needs one ingredient.
I know exactly where it grows. Would you? I'd be in your debt, and the Fan Club's, which
is more of a thing than it sounds."

*(Short NPC-chain fetch — the ingredient sourced from Celadon's market/gardens; see
[KANTO_ITEMS.md](KANTO_ITEMS.md) for the chain.)*

**Café owner (on delivery):** "You're a LIFESAVER. The event's saved. Here — this is a
little something a regular taught the cook. It's about... taking food off someone's
plate mid-bite, honestly, but it's a *very* good move." *(gives **TM88 Pluck**)*

**Pokémon Fan Club Chairman (already reseated):** "Wonderful work! Now — have I told
you about my Rapidash? Her mane, when she gallops, it's like a *sunset learning to
run*—" *(the café owner mouths 'GO, SAVE YOURSELF' at the player.)*

### 6.1f · The Cycling Road dead-end (Route 16 gate)

**Gate guard (Cycling Road):** "South? Down Cycling Road? Ahh — sorry. It's probably an
outdated rule at this point, but it's always been policy that you must have a bike on
Cycling Road. No bike, no road. You'll have to come back with a bicycle."

**Gate guard (Cycling Road):** "Where do you get a bike? ...Honestly? Not sure anymore.
Shop's been 'reopening soon' for a year. Like I said. Outdated rule. But a rule's a
rule." *(Dead end. The player backtracks through Saffron to Route 8.)*

---

## 6.2 · Lavender Town — The Town That Moved On

**Intent:** establish the reinvented broadcast town. Ambient texture; the tower as
landmark. *Trigger: first entry from Route 8. One ambient beat; no lockall.*

**Lavender sign:** "LAVENDER TOWN — Broadcasting Kanto's Future. (Historic District: 1
block north.)"

**Sound tech (hurrying, coffee in hand):** "You lost? Everyone thinks Lavender's still
the spooky graveyard town. It's not! It's the *broadcast* town now. Ghosts don't pay
rent; antennas do." *(gone before the player can answer.)*

**Producer on a call:** "—no, push the Sinnoh segment to four, run the weather twice,
nobody's awake enough to notice— I'll call you back, I'm walking." *(doesn't look up.)*

**Older resident (quieter, near the north path):** "They've done wonders with the place,
everyone says. Antennas and studios and coffee at all hours." *(pause)* "I remember when
it was quiet for a different reason. Up the hill's still quiet, if you want it. Some of
us still climb it." *(nods north, toward the cemetery.)*

---

## 6.3 · The Broadcast Tower

**Intent:** the public floors — Mary (seen, unnamed), lobby battles, Fantina, and the TV
exhibition side quest. *The old Pokémon Tower, fully converted.*

### 6.3a · Lobby (Mary through the glass)

**Visitor-center display (interact):** "THE LAVENDER BROADCAST TOWER — once a place of
rest, now a place of *reach.* From this spot, Kanto speaks to the world. (Please do not
ask about the building's former purpose. Please enjoy the gift shop.)"

**Tour guide:** "Through the glass there — that's our production floor, and that's our
director running it. Twenty years in broadcast, came down from Goldenrod radio, built
*this* from a pile of old stone. Don't wave, she won't see you. She hasn't seen anything
that isn't a run-sheet since 1998." *(Behind the glass, a woman with headphones and a
clipboard directs six people at once with brisk, delighted authority. She is **Mary**.
The game never says so.)*

### 6.3b · Lobby battles (media staff, optional)

*A couple of interns / off-duty techs battle for fun between shifts. Rosters in
[KANTO_BATTLES.md](KANTO_BATTLES.md).*

**Media intern:** "Segment's not for an hour. You wanna go? I've been staring at
waveforms all day, I need to hit something that hits back."

**Off-duty tech:** "I mix ghost-story podcasts all day — real ones, allegedly, from the
old tower records. Doesn't scare me. YOU don't scare me. Prove me wrong."

### 6.3c · Fantina (visiting Eve)

**Fantina:** *(sweeping, purple, luminous)* "Ahh! A traveler, yes? With the dust of the
road still ON you — magnifique, I adore an arrival." *(she takes the player in like a
portrait)* "I am Fantina. Sinnoh. Ghosts and Contests — the two most misunderstood arts,
and I practice BOTH, imagine my suffering."

**Fantina:** "You are here for our Eve, yes? Of COURSE you are. Everyone should be." *(a
theatrical hand to the heart)* "She is a *poem*, that girl. Such restraint! Such
*dread*! She battles like a held breath and she refuses — REFUSES — to know how good she
is. It drives me to despair. I came all the way from Sinnoh simply to tell her so, and
she said—" *(dry, imitating)* "—'okay.' ONE word. 'Okay.' I could WEEP."

**Fantina:** "Go. Challenge her. And when she destroys you — she will, do not be
insulted — come tell me, and we shall despair together over how magnificent she is.
*Bonne chance,* little traveler." *(the Sinnoh seed, planted without force.)*

### 6.3d · The TV exhibition side quest

**Stressed producer:** "You. You have Pokémon and a pulse. That's the entire job
description right now." *(frantic)* "My battle segment CANCELED. The trainer bailed. The
slot is LOCKED, it airs live in twelve minutes, and if I run dead air my director will
feed me to the antenna. Please. Step in. Two, three battles, our studio trainers, all in
good fun. I'll pay. I'll pay *well.*"

*(If the player agrees — a small studio set; a commentator NPC calls it live. Studio
trainer rosters in [KANTO_BATTLES.md](KANTO_BATTLES.md).)*

**Commentator (live, oversells everything):** "AND WE'RE LIVE! Our MYSTERY CHALLENGER
steps into the arena — a stranger from a FARAWAY LAND — and OH, the tension is
UNBEARABLE!" *(there is no tension; there is one cameraman)*
- (mid-battle) "AN ABSOLUTELY DEVASTATING TACKLE! THE CROWD IS ON THEIR FEET!" *(there
  is no crowd)*
- (finish) "IT'S OVER! WHAT A COMPETITOR! REMEMBER THE NAME, KANTO — actually we didn't
  get the name, no matter, WHAT A MATCH!"

**Stressed producer (after):** "You SAVED me. Here—" *(prize money + a useful item)*
"—and it airs tonight, region-wide. You're gonna be a little famous for about six hours.
Enjoy it. That's the whole industry, honestly: famous for about six hours." *(NPCs in
later towns may reference "that kid from Johto on TV.")*

---

## 6.4 · Eve — The Ghost Gym (2nd badge, first Kanto badge)

**Intent:** the gym challenge; the badge; the reinvention theme made literal. **End
state:** `FLAG_APOC_CH6_BADGE_DONE`; Vermilion road opens (6.6).

*A dark, quiet, deliberately eerie building — a pocket of old Lavender inside the media
town. Ghost-types drift the corridors. The bustle outside doesn't reach in here.*

### 6.4a · Meeting Eve

**Eve:** *(unhurried, dry, not looking up at first)* "You made it past the front door.
Most people from the tower crowd don't — too many antennas out there, not enough signal
in here. I like it that way." *(she turns; sharp, young, unbothered)* "You're the Johto
kid. Stranded. Word gets around a town this size in about an hour."

**Eve:** "Here's what I know about you: a reporter dragged you to Kanto and left you.
You could've sat in the Pokémon Center feeling sorry for yourself. Instead you walked
across two routes and found the one gym in a town that's trying real hard to pretend it
doesn't have one." *(a small, real nod)* "I respect that. Genuinely. Let's see if the
respect survives the next ten minutes."

**Eve:** "Everybody wants Lavender to be about towers and coffee now. Fine. Somebody's
got to keep the lights off in one building, keep the old thing *remembered.* That's the
job. Ghosts aren't scary, {PLAYER}. Forgetting is scary." *(she reaches for a Poké
Ball)* "Come on. I'll show you the difference between a fight and a *haunting.*"

### 6.4b · The gym battle

*Gen-1 Kanto ghost roster — no imports (a character statement). Marowak is the emotional
anchor. Full roster/tuning in [KANTO_BATTLES.md](KANTO_BATTLES.md).*

- **[Pre]:** "Haunter. Start us slow." *(later)* "...Marowak. Be gentle with them —
  they've earned it." *(the Marowak line is quiet; she does not explain it)*
- **[Ace / Gengar]:** "Gengar. Okay. No more warm-up. Show them why this town used to
  whisper."
- **[Loss]** (her last faints): "...Huh. The respect survived." *(a genuine, surprised
  half-smile)* "Good. It doesn't, usually."

### 6.4c · The badge

**Eve:** "That was clean. You read the ghosts instead of panicking at them — most
challengers just spam their strongest move and wonder why it phases through. You
*thought.* That's the whole gym, really. That's the whole point of a haunting: it makes
you think about what you can't hit."

**Eve:** "Here." *(hands over the badge — matter-of-fact, like directions, not a
ceremony)* "The Requiem Badge. First Kanto badge. Wear it or don't; what it *does* is
more useful than what it looks like." *(gives **TM30 Shadow Ball**)* "And this — a real
Ghost move, so you stop borrowing mine. Point it at something that thinks it's safe."

**Eve:** "That badge gets you through the Vermilion checkpoint — the League reads it as
'legitimate trainer,' which, congratulations, you now officially are in Kanto." *(beat)*
"Ships leave Vermilion for everywhere. Slateport. Olivine. Further. If you're trying to
get *home* — that's your road; catch a boat, work your way back to Johto." *(a small
shrug, not unkind)* "And if you're *not* trying to get home... well. There's a lot of
world out there, and you've already seen it doesn't wait for you to be ready. Go find
out which one you are."

*(Set `FLAG_APOC_CH6_BADGE_DONE`. No rivalry — Eve is a peer who respects the player.
The Vermilion road [6.6] is now the objective.)*

---

## 6.5 · The Cemetery — Memorials and Alder

**Intent:** the quiet counterweight to the busy town; Mr. Fuji & Agatha memorials;
Alder's grief and the Unova seed. *Staged in the House of Memories / north-edge cemetery.
No ghosts, no event triggers — just remembrance.*

### 6.5a · The memorials (read-only)

**Mr. Fuji's stone (interact):** "In memory of a true lover of people and Pokémon. He
kept this place gentle when it had every reason not to be." *(the flowers are fresh —
someone still climbs the hill.)*

**Agatha's marker (interact):** "AGATHA. Of the Elite Four. Master of ghosts." *(simple;
no epitaph beyond the name and the title. It is a grave, not a shrine. Her granddaughter
carries the rest.)*

**Old trainer's stone (interact, optional):** "For a partner of forty years. 'You went
first so I wouldn't have to be brave alone.'"

### 6.5b · Alder

**Alder:** *(standing among the graves, unhurried, weathered)* "...Oh. Didn't hear you
come up. People don't, mostly. They go to the tower, not the hill." *(a small, tired
smile)* "Don't mind me. I'm not visiting anyone in particular. I just... visit these
places. All of them. Every region has a hill like this."

**Alder:** "I lost a partner. Long time ago now — my first. The one that makes you a
trainer instead of a kid with a Pokémon. I thought I'd have made my peace by now." *(he
looks out over the stones)* "I thought if I visited enough of these quiet places, I'd
eventually stop feeling it. Hasn't worked yet. But the walking helps. The walking always
helps."

**Alder:** "I've been away from home a long while. Left things in good hands — good young
hands, better than mine some days. They don't really need an old champion underfoot right
now, and I..." *(he trails, then gathers)* "...I had walking to do. There's more happening
back that way than a grave-hill hermit ought to admit he's avoiding. But that's Unova's
business, and today I'm just a man at a graveside." *(the Unova seed — quiet, unforced.)*

**Alder:** *(as the player goes)* "You've got the look too, you know. The young version
of it. Something took a piece out of your week." *(kindly)* "Keep walking, kid. It
doesn't fix it. But it helps. It really does help."

*(Optional one-shot `FLAG_APOC_CH6_ALDER_MET`, or leave him re-talkable ambient.)*

---

## 6.6 · Moving On — Vermilion Unlocked

**Intent:** the badge opens the Route 6 checkpoint; the road south to the ships. **End
state:** `FLAG_APOC_CH6_DONE`. Hands off to Chapter 7 (Vermilion).

*The player returns through Saffron to the Route 6 south gate — the one that turned them
away in Chapter 5. This time they have a Kanto badge.*

**League officer (Route 6, now):** "Back again? And — is that a Kanto Gym Badge?" *(he
actually smiles this time)* "The Requiem Badge, Lavender. That'll do it. That's exactly
the proof I needed — you're legitimate training stock, not someone drifting toward the
docks for the wrong reasons." *(steps aside)* "Vermilion's straight south. Working port,
watch your footing, mind the sailors. Ships out of there go everywhere there's water.
Safe travels, trainer. You earned the road."

*(Behind the player, Lavender's broadcast tower blinks red against the evening sky,
transmitting to a region that has no idea what's coming. The player isn't stranded
anymore. They chose the way out.)*

**[Chapter 6 ends — set `FLAG_APOC_CH6_DONE`; hand off to Chapter 7 (Vermilion).]**

---

## Coverage Checklist (for the implementation pass)

- [ ] **6.0 Route 8** — seven sight-trainers (Bikers Dwayne/Harris/Zeke, Super Nerds
  Sam/Tyrone, Young Couple Moe & Lulu [double], Gentleman Milton), each Pre/Loss/Post;
  wild table + field items.
- [ ] **6.1 Celadon (optional)** — street ambient; Daisy Oak salon; Gardens (Erika +
  gift, Janine, **Aaron battle**); Hotel (collector, couple, **Looker** unnamed); Café
  quest (owner + Chairman → fetch → **TM88 Pluck**); Game Corner; **Cycling Road dead-end**.
- [ ] **6.2 Lavender town** — media-retheme ambient; the "historic district north" sign.
- [ ] **6.3 Broadcast tower** — Mary through the glass (seen, unnamed); lobby battles;
  **Fantina** (Sinnoh seed); **TV exhibition** side quest (commentator + reward + TV callback).
- [ ] **6.4 Eve's gym** — meeting Eve; Gen-1 ghost battle (Pre/ace/Loss); the **Requiem
  Badge** + **TM30 Shadow Ball**; set `FLAG_APOC_CH6_BADGE_DONE`.
- [ ] **6.5 Cemetery** — Mr. Fuji & Agatha memorials; **Alder** (grief + Unova seed).
- [ ] **6.6 Vermilion unlock** — Route 6 checkpoint passes on the badge; set
  `FLAG_APOC_CH6_DONE`; hand off to Ch7.

## Retheme / cut stubs (engine-facing notes)

- **Celadon Gym → Botanical Gardens** (`T07GYM0101`): reframed as a public garden, **not**
  a gym challenge. Erika (`FLAG_HIDE_CELADON_GYM_ERIKA`) tends it; re-line the placed gym
  trainers (`TWINS_JO_AND_ZOE`, `LASS_MICHELLE`, `PICNICKER_TANYA`, `BEAUTY_JULIA`) as
  garden visitors — most non-battle; one hosts **Aaron's** casual battle.
- **Celadon Dept Store → Market/Services**; **Condominiums → Pokémon Hotel**;
  **Restaurant → Café**; **Game Corner** kept. Repurpose interiors, don't rebuild.
- **Lavender has no vanilla gym** — host **Eve's gym** in the **Volunteer Pokémon House**
  (`T05R0201`) (recommended); reserve the **House of Memories** (`T05R0601`) for the
  memorial/cemetery beats. Add a gym warp + Eve's leader slot to the host.
- **Mary** = `FLAG_HIDE_LAVENDER_RADIO_TOWER_DIRECTOR` slot, **seen not named**. **Looker**
  in the Celadon hotel, **name never given**.
- **The Requiem Badge** is the **confirmed name** for DESIGN's "Ghost badge." The
  engine `give_badge <BADGE_*>` constant is deferred to the whole-game **badge-order pass**
  (Saffron/**Marsh** bit a candidate, freed by Saffron's gym being the closed Psychic Dojo).
- **Eve's roster is Gen-1 Kanto ghosts only** — no imports, on purpose (she's the
  traditionalist keeping old Lavender). Do not salt cross-region ghosts into her team.
- **Route 6 south gate** re-opens on the **badge check** (no new unlock flag) — the same
  conditional the Ch5 gate used.
