# Chapter 3 — Scene Spec & Full Script (Azalea · Slowpoke Well · First Gym)

This is the **complete line-by-line dialogue** for Chapter 3, the single source of
truth for what every character says. It sits one altitude below
[CHAPTER3_BUILD.md](CHAPTER3_BUILD.md) (staging, flags, files) and pairs with
[JOHTO_BATTLES.md](JOHTO_BATTLES.md) (rosters) and [JOHTO_ITEMS.md](JOHTO_ITEMS.md).

**Status:** ⬜ not implemented — this is the writing pass. Engine wiring (`.gmm`
message banks, `npc_msg` beats, `scr_seq` hooks) happens at implementation; no
message IDs are assigned yet.

**Conventions:**
- `{PLAYER}` = player name token; `{RIVAL}` = Kestra. Final HG-charset pass (dash,
  ellipsis, apostrophe) happens when text is transcribed to `.gmm`.
- Battle lines use **[Pre]** (sent-out intro), **[Loss]** (last Pokémon faints,
  in-battle), **[Post]** (overworld, after).
- *Italic parentheticals* are terse staging cues, not spoken. Per house style
  ([[dialogue-over-narration]]) drive scenes with dialogue; keep narration minimal.
- The Field Team are **never** "Team Rocket," never named, never theatrical. The
  Lead Operative's name (Proton slot) is stripped entirely.

---

## 3.0 · Arrival — Route 33 into Azalea

*Trigger: player crosses the R33/Azalea border after the rain. One ambient line as
the music shifts; no lockall.*

**Azalea gate sign:** "AZALEA TOWN — Where People and Slowpoke Live as One."

**Townswoman (just inside):** "Oh — a traveler. You picked a strange few days to
visit, hon. Mind the well path. Folks are jumpy."

---

## 3.1 · Something Is Off

**Intent:** establish the Slowpoke-as-family town, the quiet wrongness, and recruit
Turk for the descent. **End state:** `FLAG_APOC_CH3_AZALEA_INTRO_DONE`; well path
open; Turk staged at the well mouth.

### 3.1a · Entry coordinate scene (one-shot)

*Fires once on first approach to the town center. A townsman is counting Slowpoke
at the well rim and coming up short.*

**Townsman (counting):** "...nine. Nine. There's supposed to be fourteen by the
rim this time of morning." *(turns to player)* "You haven't seen any wandered off
toward the gate, have you? No. Course not."

**Townsman:** "Five gone in three days. And the ones still here..." *(glances at a
Slowpoke pressed flat against the stones, unmoving)* "...look at him. He won't even
yawn. A Slowpoke that won't yawn isn't a Slowpoke. Something's wrong down that
well."

### 3.1b · Ambient townsfolk (talk-to, optional)

**Little girl:** "I can't find Bubbles. She always waits by our step for breakfast.
She didn't come. Mister, if you see a Slowpoke with a chip in her tail, that's
Bubbles, okay? Tell her I'm waiting."

**Old man on bench:** "Sixty years the well's made the same sound. Drip, and the
slow ones breathing. Three nights ago it started up — clicking. Humming. Like the
inside of a clock. I don't sleep much now."

**Charcoal Kiln man (in doorway, distracted):** "Can't keep my mind on the fire
today. Keep listening for that hum." *(beat)* "...You need charcoal? Here. Take
it, take it. I can't think straight to haggle."  *(gives Charcoal —
`FLAG_GOT_CHARCOAL_FROM_AZALEA_TOWN_MAN`)*

**Apricorn note pinned to Kurt's door:** "OUT. Don't knock — go around the side."

### 3.1c · The well-path blocker (repurposed harassment beat)

*A Field Team member stands on the well steps, polite and immovable. Reuses
`FLAG_AZALEA_ROCKET_HARASSING_CIVILIAN` framing — no shouting.*

**Field Tech (blocking):** "Apologies. The well's under private survey this week.
Structural assessment. It isn't safe for the public right now."

**Townsman (to the tech, helpless):** "It's never needed a 'survey' in sixty
years. Those are our Slowpoke down there."

**Field Tech:** "Then you'll want the structure sound, won't you. We'll be done
soon." *(does not move)*

### 3.1d · Kurt

*In his house (side door) or at the well mouth. Drives the recruit.*

**Kurt:** "You're not from here. Good. Means you can see it plain — everyone born
in this town's gone half deaf to that well, and now it's screaming and they're
arguing about *permits*."

**Kurt:** "I'd go down myself. These knees say otherwise. These lungs say
otherwise, loud as that machine-hum." *(grips a workbench)* "I made balls for this
town for sixty years so its Pokemon could come home safe. And I can't walk down my
own well to bring them home."

**Kurt:** "Turk's at the gym steps. My grandson. He's got the heart for it and
none of the nerve — he won't go down alone, and he's right not to." *(looks at
player)* "But two of you? Go on. Find out what they're doing to my Slowpoke."

### 3.1e · Turk — the recruit

*At the well mouth. This is the double-battle setup: he wants a partner, not
backup.*

**Turk:** "You're the one Gramps sent? Okay. Okay, good." *(too fast)* "I'm Turk. I
train under Bugsy at the gym, I'm — that's not important. The Slowpoke are
important."

**Turk:** "There are people down there. Not townsfolk. They've got cases and
screens and they keep the Slowpoke in *rings*, and nobody'll let me past to look
because I'm 'just a kid.'" *(steadies)* "I'm done being just a kid about it."

**Turk:** "I'm not asking you to fight my fight for me. I'm asking you to fight it
*with* me. Two of us, side by side, the whole way down. You in?"

*(Yes →)*

**Turk:** "Then send yours out the second I send mine. We don't get separated.
Whatever's down there, we meet it together."

*(No / talk again →)*

**Turk:** "...I'll wait. I'm not going down there alone, and I'm not going home.
So. Whenever you're ready."

---

## 3.2 · Slowpoke Well — The First Encounter

**Intent:** the game's first **double battles**, fought beside Turk; the cold
professional operation; the Silph-coat detail; the freeing. **End state:**
`FLAG_BEAT_AZALEA_ROCKETS` + `FLAG_APOC_CH3_WELL_CLEARED`; Slowpoke restored
(`FLAG_HIDE_AZALEA_SLOWPOKES` cleared); modified King's Rock evidence placed.

### 3.2a · First contact (Entrance / B1F)

*The first Field Tech notices them and sighs. No alarm, no theatrics.*

**Field Tech (Site Technician):** "How did — the steps were *blocked*." *(into a
collar mic)* "We've got two kids on B1F. No, I'll handle it. It's children."

**Field Tech:** "Listen. Turn around. There is nothing down here a child needs to
see, and I'd rather not make it a battle."

**Turk:** "Then let the Slowpoke go and we'll leave together."

**Field Tech:** "...Of course you'd say that." *(resigned)* "Fine. Quickly, then."

> **[Battle 1 — double]** Field Tech (Magnemite, Voltorb) + Turk (Spinarak) vs. {PLAYER}.

**Field Tech [Loss]:** "Down to nothing. They train them out in the grass, these
two. Hm."

**Field Tech [Post]:** "Go ahead. Look. It won't mean anything to you anyway." *(steps
aside; does not flee — just stops mattering to him)*

**Turk:** "He's not even angry. Why isn't he angry? You break into someone's home,
you should at least have the decency to be *angry*."

### 3.2b · The monitoring stations (read-only flavor objects)

*Scattered down B1F/B2F. The horror is in the data, not a speech.*

**Slowpoke ring (examine):** "Six Slowpoke sit inside a chalk-and-cable ring.
Small devices are clipped where their tails meet the floor. None of them look up."

**Terminal 1 (examine):** "SUBJECT 04 — induced-evolution trial 11. King's Rock
variant, modified. Result: incomplete. Note: stress response higher than modeled.
Continue."

**Terminal 2 (examine):** "'Higher than modeled' — flagged three trials ago. Why
are we still continuing? — appended, unsigned."

**Equipment case (examine):** *A lab coat is folded over the lid. The only mark on
any of it: a small printed logo on the breast pocket.* "Silph Co."

**Turk (at the coat):** "Silph. That's — that's a real company. They make the
Pokegear my mom uses. Why would..." *(trails off)* "No. Keep moving. Tell someone
who knows what it means. We free the Slowpoke first."

### 3.2c · Deeper (B1F → B2F)

> **[Battle 2 — double]** Field Researcher (Koffing, Baltoy) + Turk (Spinarak/Ledyba) vs. {PLAYER}.

**Field Researcher [Pre]:** "I'm not paid to fight children. I'm also not paid to
let you near the main terminal. So."

**Field Researcher [Loss]:** "Enough. Take it — I'm not bleeding for a data set."

**Field Researcher [Post]:** "That clay one isn't even local, in case you're
wondering. We bring what works. We bring it from a long way off." *(more than she
meant to say; she shuts up)*

> **[Battle 3 — double]** Field Researcher ♀ (Grimer, Magnemite) + Turk (Ledyba) vs. {PLAYER}.

**Field Researcher ♀ [Pre]:** "You're persistent. Persistent isn't the same as
welcome."

**Field Researcher ♀ [Loss]:** "Fine. *Fine.* The terminal's that way — and it
won't matter by the time you reach it."

**Turk (after):** "What did she mean, 'won't matter'? {PLAYER} — the screens. They're
wiping the screens. Go, *go!*"

### 3.2d · The Lead Operative (B2F terminal)

*The Lead is calm at the main terminal, already deleting.*

**Lead Researcher:** "Children. Of course it's children." *(not looking up)* "Do
you know what you're standing in? No. You think you walked into a kidnapping. You
walked into a *measurement*."

**Turk:** "They're not numbers. They have names. That one's Bubbles — a little girl
up top is waiting on her step right now."

**Lead Researcher:** "...How sentimental." *(a pause — the only crack)* "Hold them
off. I need ninety seconds."

> **[Battle 4 — double, boss]** Lead Researcher (Voltorb, Bronzor) + Turk (Ledyba) vs. {PLAYER}.

**Lead Researcher [Loss]:** "Time. That's all I needed. Time."

*(Post-battle: the terminal is wiped; the Lead pockets the modified King's Rock —
no, leaves a broken one — grabs the Silph coat, and steps into the back tunnel.)*

**Lead Researcher [Post]:** "The readings were inconclusive. Remember that, if
anyone asks. *Inconclusive.*" *(to the freed Slowpoke, flat)* "Leave the husks.
They're no use to anyone now."

**Turk:** "Stop — you can't just — !"

*(The Lead is gone through the back exit. The rings power down. Slowpoke begin to
stir.)*

**Turk (quiet):** "...He didn't even run. He just *left*. Like we were weather."
*(turns to the Slowpoke)* "Hey. Hey, it's okay. You're okay now. Come on. Let's get
you home."

**Modified King's Rock (examine, left behind):** "A King's Rock, fitted with
circuitry you've never seen — fine wire, a dead indicator light. Someone built
this on purpose. You pocket it; someone should see it."  *(quest object; not a
usable item)*

---

## 3.3 · Silver Arrives

**Intent:** Silver's first spoken scene — warm, presidential, with one half-second
flicker. **End state:** `FLAG_APOC_CH3_SILVER_MET`; Silver leaves; player
validated.

*The player and Turk surface. Kurt and a small crowd wait. Silver is already
there — too soon for anyone to question it.*

**Kurt:** "There — there they are! The Slowpoke, are they—?"

**Turk:** "They're coming up, Gramps. They're hurt, some of them. But they're
coming up."

*(Silver steps forward. The player faces him for the first time. A beat — his
expression flickers, surprise or calculation, gone before anyone clocks it.)*

**Silver:** "...You." *(then the smile, perfect)* "You're the one Gold mentioned.
Cherrygrove. He said there was a trainer worth watching." *(warm)* "I should have
guessed it would be you down that well."

**Silver:** "Tell me what you saw. All of it. Slowly." *(he listens — actually
listens, eyes never leaving the player. It feels like being *seen*.)*

*(Player offers the modified King's Rock.)*

**Silver:** "May I?" *(turns it in the light; the concern reads as genuine)* "...This
isn't improvised. This is *engineered*." *(the faintest flicker again — recognition?
— buried instantly)* "Whoever did this is not a vandal. They're a professional. I'll
treat them like one."

**Silver:** "Here is what happens now. The League takes this. We trace the
equipment, we track the people, we put protection on this town's Slowpoke until
every last one is accounted for. You have my word — and my word, these days, moves
quickly."

**Silver:** "You did more today than most trainers do in a year, {PLAYER}. Rest.
Earn your badge. Leave the rest to me." *(to Turk)* "And you. You didn't leave them.
Remember that the rest of your life." *(he goes — clean walk-off or lift-off;
he never explains how he arrived first.)*

**Kurt (watching him leave):** "...Champion himself. Here, fast as that." *(a flicker
of his own — old, wary, dismissed as soon as it forms)* "Well. The boy's right.
You're not just a kid anymore either, are you. Go on. Turk's been wanting his
turn at you since you came up those steps."

**Turk (quietly, alone with the player a moment):** "I keep thinking about how
calm he was. The man at the terminal. 'No use to anyone now.'" *(looks at his own
Pokemon)* "I'm going to run that gym someday. And nobody's Pokemon is ever going to
be a *measurement* in my town. Come on. Let me show you why I earned the right to
ask you down there."

---

## 3.4 · The Azalea Gym — The Hive Badge

**Intent:** first real gym; player vs. Turk, Bugsy officiating; endurance lesson;
badge + TM89 U-turn. **End state:** Hive Badge + TM89; `FLAG_APOC_CH3_BADGE_DONE`;
Azalea fly point set.

### 3.4a · Bugsy (intro / officiating)

**Bugsy:** "So you're the one who went down the well with my student. Half the
town's talking about it." *(grins)* "I could battle you myself. I've decided not
to. Turk needs this more than I need a win — and after this morning, so does this
town. A clean, honest gym match. Something that makes *sense*."

**Bugsy:** "Bug Pokemon get underestimated. So do the people who raise them. Beat
my juniors, then beat Turk, and you'll have earned the underestimating *out* of
you. Web's that way. Mind your footing."

**Gym guide:** "Azalea's gym runs on spinarak silk — step on the web platforms to
cross. Bug types lean on status: poison, sleep, screens. Bring something that hits
hard before they bog you down. Or bring patience. You'll need one or the other."

### 3.4b · Gym juniors

**Azalea kid Al [Pre]:** "Turk says we don't catch Pokemon, we *look after* them.
Mine'll look after me just fine — watch!"
**Al [Loss]:** "Aw. Looked after me right into the dirt."
**Al [Post]:** "You're good. Turk's better than me, though. Way better. He went
down the *well*, you know."

**Azalea kid Benny [Pre]:** "One Pokemon. That's all I need to slow you down for
Turk. We play the long game in this gym."
**Benny [Loss]:** "Slowed you... not enough."
**Benny [Post]:** "Tch. Go on. He's waiting at the back. Don't say I didn't tangle
you up first."

**Azalea kid Josh [Pre]:** "Check it — my cousin in Hoenn shipped me this little
guy. Bugs from across the sea! The world's getting *small*, huh?"
**Josh [Loss]:** "Okay, the import didn't save me. Worth it for the flex."
**Josh [Post]:** "Everybody's trading now. Trains, boats, the radio. My gran says
when she was a kid you only ever saw what crawled out of *your* forest. Wild."

**Twins Amy & Mimi [Pre]:**
— Amy: "Two of us!"
— Mimi: "Two of you, you mean — better find a partner fast!"
— Amy: "Just like the well! Turk told us everything!"
*(double battle)*
**Twins [Loss]:**
— Mimi: "Both down..."
— Amy: "...at the same time. That's almost cooler than winning."
**Twins [Post]:**
— Amy: "Mine's from here. Mimi's is from Hoenn. We trade so we always match!"
— Mimi: "Go on, hero. Turk's been practicing his serious face all morning."

### 3.4c · Turk — the badge match

**Turk [Pre]:** "Different now, isn't it? Down there we were on the same side.
Up here I want to win." *(settles, the nerves finally gone)* "I'm not going to go
easy because we bled together. That'd be an insult to both of us."

**Turk [Pre, cont.]:** "My team doesn't hit the hardest. It *lasts*. Screens,
webs, a wall you'll get sick of looking at — and then the one that bites. Get
through all of it. Show me you deserve the first badge."

*(Roster: Ledyba, Spinarak, Shuckle, Heracross — endurance core + one hitter. See
[JOHTO_BATTLES.md](JOHTO_BATTLES.md).)*

**Turk [sending Shuckle]:** "Here's the wall. Hope you packed lunch."
**Turk [sending Heracross]:** "And here's the one that bites. Last one. Make it
count — I will."
**Turk [Loss]:** "...All of it. You got through all of it." *(not bitter — lit up)*

### 3.4d · Badge + reward

**Bugsy:** "*That's* a gym battle. Both of you — that's exactly what one should
look like." *(to player)* "You out-lasted the wall and out-thought the bite. The
Hive Badge is yours, and you earned every minute of it."

*(Receives Hive Badge. Azalea fly point registers.)*

**Bugsy:** "And take this. TM89 — U-turn. Strike, then come home before they can
answer. Momentum. Turk's whole gym is about *enduring*; this is the other half of
the lesson — knowing when to leave. Carry both."

*(Receives TM89 U-turn.)*

**Turk:** "After down there, a gym battle should've felt simple. It didn't. You
made me work for every inch of it." *(offers a hand)* "Thank you. For coming down
with me when you didn't have to. Wherever you're headed — Goldenrod, through the
forest — I hope it's quieter than our morning was."

**Turk:** "And if Silver keeps his word about our Slowpoke... then maybe heroes are
real after all. He came so *fast*, didn't he." *(small, unresolved)* "...Anyway.
Go. The forest's just west. Watch the trees — they've gotten strange."

### 3.4e · Kestra (optional epilogue beat)

*If used: Kestra catches up outside the gym, having gone ahead and missed
everything. Keeps her present without crowding the Well.*

**Kestra:** "There you are! I get to Azalea first, I'm all ready to gloat about
beating the gym before you — and the whole town's saying you went down a *well* and
met the *Champion*?!" *(half outrage, half awe)* "I leave you alone for one route!"

**Kestra:** "...You're okay, though? Really?" *(beat, then bright again)* "Okay.
Okay good. Then I want the badge too, and I want the whole story, in that order.
Race you to the forest — last one to Goldenrod buys lunch!"

---

## 3.5 · Ilex Forest — Passage West

**Intent:** atmospheric passage; inert Celebi shrine; the *ecological* drift flavor
kept separate from the *supernatural* unease. **End state:** player exits west
toward Goldenrod (Chapter 4). No badge/HM gate.

**Gatehouse attendant:** "Heading into Ilex? Stick to the path. It's an easy walk
if you don't wander — and lately folks wander, then swear the trees moved on them."

**Old woodsman (ecological — mundane):** "Forest's changed, and I'll tell you
plain how: them little acorn-things in the branches. Seedot. Weren't here when I
was a boy — blew in from somewhere south over the years, and now they're thick as
thieves." *(nods at the underbrush)* "Pushed the radish-ones right out. Oddish
used to carpet this floor. Gone quiet now. Drifted off toward the Goldenrod side, I
hear. Nothing sinister. Just... the world rearranging itself while you're not
looking."

**Old woodsman (cont.):** "Ten years is a long time for a forest. Things come,
things go. You learn to let it."

**Shrine plaque (supernatural — kept separate):** "A small shrine, older than the
town, older than the road. Moss has nearly swallowed the carving. It is utterly
still — and the stillness has a weight to it, like a held breath."

**Girl near the shrine:** "My grandma won't come this deep anymore. She says the
air by the shrine feels *heavier* than it used to. Not bad. Just... like something's
in the room with you." *(shrugs)* "I don't feel anything. But I don't argue with
Grandma about the woods."

**Exit sign (west):** "← GOLDENROD CITY · ILEX FOREST"

---

## Coverage checklist (for the implementation pass)

- [ ] 3.1 town: entry one-shot, ≥3 ambient townsfolk, kiln Charcoal, well-blocker,
  Kurt recruit, Turk recruit (yes/no branches).
- [ ] 3.2 well: 4 operative battles (Pre/Loss/Post each) + Turk partner banter, ≥3
  station/terminal flavor objects, Silph-coat beat, Lead wipe/retreat, modified
  King's Rock object.
- [ ] 3.3 Silver: flicker staging, King's-Rock exam, validation, departure, Kurt +
  Turk buttons.
- [ ] 3.4 gym: Bugsy intro + guide, 4 juniors (Pre/Loss/Post; Twins as double),
  Turk match (Pre/sends/Loss), badge + TM89 text, optional Kestra epilogue.
- [ ] 3.5 Ilex: gatehouse, woodsman (ecological), shrine + girl (supernatural),
  exit.
- [ ] Retheme pass: Azalea Mart clerk, Pokemon Center nurse, post-clear townsfolk
  (Slowpoke restored, some still "wrong"), Bubbles returned to the little girl.

### Stubs to fill in the retheme pass

**Azalea Mart clerk:** "Restocked the Super Potions — figured folks'd want them,
after. You headed down that well too? ...You were one of the *kids*? On the house,
then. The Super Potion. Don't argue."

**Nurse (Pokemon Center):** "Your Pokemon look like they've had a morning. There —
good as new. ...We've had three Slowpoke through here today. I do what I can for
them. Some things don't heal on a counter."

**Little girl (post-clear, Bubbles returned):** "You found her! You found Bubbles!"
*(the Slowpoke yawns enormously)* "See? She's yawning again. That means she's
really okay. Thank you, thank you, *thank you!*"

**Townsman (post-clear):** "Fourteen by the rim again. I counted twice." *(quiet)*
"Three of them still won't go near the water. But fourteen. They came home."
</content>
