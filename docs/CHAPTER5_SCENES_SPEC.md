# Chapter 5 — Scene Spec & Full Script (Saffron City · Silph lobby · the Dojos · stranded in Kanto)

This is the **complete line-by-line dialogue** for Chapter 5, the single source of
truth for what every character says. It sits one altitude below
[CHAPTER5_BUILD.md](CHAPTER5_BUILD.md) (staging, flags, files) and pairs with
[KANTO_BATTLES.md](KANTO_BATTLES.md) and [KANTO_ITEMS.md](KANTO_ITEMS.md) (Saffron is
the first Kanto location).

**Status:** ⬜ not implemented — this is the writing pass. Engine wiring (`.gmm`
message banks, `npc_msg` beats, `scr_seq` hooks) happens at implementation; no
message IDs are assigned yet.

**Conventions:**
- `{PLAYER}` = player name token. No `{RIVAL}` this chapter — Kestra stayed in
  Goldenrod. Final HG-charset pass (dash, ellipsis, apostrophe) at `.gmm` transcription.
- **No battle lines this chapter** — Saffron has no wild grass, both dojos are
  **closed**, and the dojo clash is a **spectator** scene. There are no `[Pre]/[Loss]/
  [Post]` blocks because there are no player battles.
- *Italic parentheticals* are terse staging cues, not spoken. Per house style
  ([[dialogue-over-narration]]) drive scenes with dialogue; keep narration minimal.
- **Mel's defining beat is an absence:** she never says goodbye. Do not write her a
  farewell line to the player — the missing line *is* the scene.
- **Sabrina & Bruno are introduced, not battled.** They are institutional figures
  here, not gym leaders.

---

## 5.1 · Silph Co. — The Lobby and the Parting

**Intent:** explore the curated lobby and its conspiracy seeds; Mel bulldozes upstairs
and is gone without a goodbye. **End state:** `FLAG_APOC_CH5_SILPH_PARTING_DONE`.

*Mel marches the player in from the street. The lobby is glass, steel, and polish —
display cases, a tour podium, a long front desk. Aggressively, expensively normal.*

**Mel:** *(barely slowing, scanning the room like a headline)* "Okay. THIS is the
face they show the public. Look at it. Spotless. Nobody spotless ever has nothing to
hide — clean is a *choice*, clean costs *money.*" *(already walking)* "Look around,
soak it in, I'll do the talking."

### 5.1a · The lobby (free explore — the seeds)

**Tour podium (interact):** "Welcome to Silph Co., Saffron City — *Engineering
Tomorrow, Today.* Our guided tour showcases six decades of innovation: the modern
Poké Ball, the Silph Scope, regional communication networks, and the Magnet Train
that carried you here. Silph: connecting a connected world."

**Product display case (interact):** "ON DISPLAY: the Silph Scope. The Pokégear comm
module. The next-generation storage transfer node. *'If it moves information, a
Silph engineer touched it first.'*"

**Community Partnerships wall (interact — the seed):** "SILPH CO. COMMUNITY
PARTNERSHIPS — proud to support research and heritage across the regions." *(a long
list of partner sites; a few names sit oddly among the civic ones — a Johto ruin, a
coastal lab, a 'wellness reclamation project.' Nothing is explained. The player has
been to one of these. Read-only; no comment from the game.)*

**Magnet Train display (interact — the seed):** "THE NEW MAGNET TRAIN: re-engineered
end to end by Silph Co. Faster. Smarter. *Aware.* Our integrated systems monitor
every journey for your safety and our continuous improvement." *(the word 'aware'
sits a half-beat too long.)*

**Elevator bank (interact — the wall):** *(a panel glows red)* "UPPER FLOORS —
AUTHORIZED PERSONNEL. Badge verification required." *(It does not open. It is not
going to open.)*

### 5.1b · The parting (Mel leaves)

*Mel reaches the front desk. The receptionist (`SPRITE_GSWOMAN6`) puts on the
practiced smile.*

**Receptionist:** "Welcome to Silph Co.! How can I help you and your... young
companion today?"

**Mel:** *(credentials already out)* "Press. I need your research-division contact,
your executive-affairs desk, and a straight answer about your recent partnerships in
Johto — the field ones. The ones not on the wall over there."

**Receptionist:** *(smile not moving)* "I'd be happy to provide our public
information packet. The upper floors aren't open to—"

**Mel:** "—visitors, right, of course, totally understand—" *(she is no longer
listening; she's reading the badge-reader by the elevators, measuring it)* "—is that
a standard mag-lock or a Silph proprietary? Because if it's standard—"

*(Mel moves. Fast. Past the desk, past a security guard (`SPRITE_POLICEMAN`) who is
only beginning to stand, through the barrier as someone else badges in, into the
elevator corridor. It happens in the time it takes to describe it.)*

**Mel:** *(over her shoulder, to the room, to the chase, to no one — NOT to the
player)* "Don't wait on me, I move fa—"

*(The corridor swallows her. The barrier settles closed. She is gone. She never
looked back. She did not say the player's name.)*

**Security guard:** *(now fully up, to the player, flat)* "...That one's going to get
herself escorted out. You with her?"

**Receptionist:** *(to the player, gentler, the apology that is the whole point)*
"I'm sorry, sweetheart. The upper floors really aren't open to visitors — and I'm
afraid that includes you. Your friend is..." *(a small, helpless gesture at the
closed corridor)* "...she's not really a 'wait for you' sort, is she."

**Receptionist:** "Is there someone I can call? ...No? Okay. Well." *(back to the
script, because the script is all she has)* "Can I get you a brochure?"

*(The player is alone in a lobby in a foreign city. Set
`FLAG_APOC_CH5_SILPH_PARTING_DONE`. Mel does not return this chapter.)*

---

## 5.2 · Stranded — The Rail Pass Rule

**Intent:** the player tries to go home and learns they can't. **End state:**
`FLAG_APOC_CH5_STRANDED`.

*Back at the Magnet Train Station. The attendant (`SPRITE_POLICEMAN`) is polite and
immovable.*

**Player (option to interact with the platform gate).**

**Station attendant:** "Magnet Train to Goldenrod? Of course. Rail pass, please."

*(The player has none.)*

**Station attendant:** "...No pass. I see." *(not unkind, just final)* "I'm sorry,
but the Magnet Train's pass-only, and passes are issued in the rider's **home
region**. Yours would be Johto, by the sound of you. You'd buy it *there.*"

**Station attendant:** "I can't sell you one here. It's not a money thing — it's a
*registration* thing. Home region only. No exceptions." *(beat)* "How'd you get over
without one? ...Ah. Someone walked you through on theirs, did they." *(he's seen it
before)* "And now they're not here. Yeah."

**Station attendant:** "Look — you're not stuck *forever.* You're a trainer; you've
got options a tourist doesn't. But the easy way home? That door's shut till you sort
out credentials. Sorry, kid."

*(No quest prompt, no workaround offered — it's a rule, not a riddle. Set
`FLAG_APOC_CH5_STRANDED`. The tone is stuck-and-annoyed, not afraid.)*

**Player internal beat (single line, on leaving the station):** "...Okay. New plan.
Whatever a 'new plan' is, in a city I've never been to, in a region that isn't mine."

---

## 5.3 · The Competing Dojos — Spectator Flashpoint

**Intent:** the player wanders in to battle, the Medicham dispute erupts, the brawl
escalates above their level, and **Sabrina & Bruno** end it and introduce themselves.
**End state:** `FLAG_APOC_CH5_DOJO_INCIDENT_DONE`. No player battles.

### 5.3a · Asking for a battle (either dojo)

*Symmetric — the player can enter the Fighting Dojo or the Psychic Dojo. Sample shown
for the Fighting Dojo; mirror the lines for the Psychic side.*

**Fighting Dojo master:** *(sizing the player up)* "A challenger? From off-region, by
the gear. Hah — good. We don't get enough fresh fists in here. Step up, then. Let's
see what your—"

*(A junior bursts in, breathless.)*

**Dojo junior:** "MASTER! It's — it's the Medicham — they're trying to TAKE it, the
psychics are out in the plaza, they say it's *theirs*—"

**Fighting Dojo master:** *(already moving, the player forgotten)* "Over my *body*
they will. STAY HERE, kid—"

*(He doesn't stay to see if the player obeys. The player follows him out.)*

### 5.3b · The brawl (the plaza)

*The plaza between the dojos. Students from both sides squared off — Abra and Kadabra
against Machop and Machoke — a messy scrum of punches and psychic flashes. The
contested Medicham is in the middle, distressed. No player control beyond watching.*

**Psychic student:** "Its *mind* woke up under our teaching! You can't own a thing
that *thinks!*"

**Fighting student:** "We taught it to STAND, to STRIKE, to never quit — that's not
nothing! Let it GO!"

**Fighting Dojo master:** *(arriving, roaring)* "HANDS OFF. That Medicham trained its
body in MY dojo. Psychic parlor tricks don't make a fighter — *discipline* does. It
is OURS."

**Psychic Dojo master:** *(cold, certain, arriving from the other side)* "You taught
it to punch. We taught it to *think.* A body without a mind is a tool. Step back
before you embarrass your students further."

### 5.3c · The escalation (you are not ready for this)

*The two masters reach for their belts. The plaza goes still.*

**Fighting Dojo master:** "MACHAMP."

**Psychic Dojo master:** "Alakazam."

*(Two fully-evolved heavyweights materialize, facing off, commanded by masters. The
students fall back. Bystanders clear. The air pressure changes. This is no longer a
scuffle — and it is leagues beyond a one-badge trainer. The player can only watch,
small at the edge of it.)*

**Bystander (low, to the player):** "...You'll want to step back, kid. When those two
go, the *cobblestones* go."

### 5.3d · Sabrina & Bruno end it

*Before the heavyweights clash — two figures walk up together, unhurried.*

**Sabrina:** "Enough."

*(One word. It is not loud. The plaza hears it anyway. Alakazam's eyes flick to her
and it goes still.)*

**Bruno:** *(stepping between the students, a wall)* "That's *enough.* You're black
belts and psychics of the Saffron dojos. Look at yourselves. Brawling in the street
over a Pokémon that's frightened of *all* of you." *(quiet thunder)* "Recall them.
Now."

*(The masters hesitate — then, chastened, recall Machamp and Alakazam. Students
disperse, eyes down. A junior gently retrieves the trembling Medicham.)*

**Psychic Dojo master:** "...Sabrina. We didn't—"

**Sabrina:** "You did. In the street. Where the whole city could watch the two oldest
schools in Saffron behave like the thing they were built to rise above." *(she does
not raise her voice once)* "We'll speak later. Not here."

**Bruno:** *(to the Fighting master, blunt but not cruel)* "Go cool off. Drink some
water. We'll sort the Medicham properly — *talking*, like adults, like we should've
the first time." *(the master nods, deflated, and goes.)*

### 5.3e · The introductions (Sabrina & Bruno notice the player)

*The plaza emptying. The two titans notice the young off-region trainer standing where
a brawl just happened.*

**Bruno:** "...And who's this. You're not one of ours." *(not suspicious — kind)* "You
were standing awful close to that. You alright?"

**Player (beat).**

**Bruno:** "Sorry you caught us at our worst, kid. Truly. These two dojos have
squabbled for *generations* — mind against body, the old argument, it's practically a
sport." *(his face hardens)* "But this? Heavyweights in the street? That's new. The
whole city's wound too tight lately."

**Sabrina:** *(studying the player, even and unreadable)* "Saffron is being squeezed.
Silph grows; the city's older bones get less. Water, space, money, *attention* — all
of it flows to the tower now. The dojos feel it like everyone feels it, and old
rivalries fray fastest when everyone's afraid." *(beat)* "The Medicham was a spark.
The dry grass was already here."

**Sabrina:** *(a half-second too knowing — the character beat)* "You've come a long
way to stand in the middle of someone else's argument." *(her eyes settle on the
player, then on their Pokémon)* "...And you're carrying something heavier than your
level. I won't ask what. But I noticed. I notice most things." *(she lets it sit, then
lets it go.)*

**Bruno:** *(warmer, breaking the moment)* "Don't mind her, she does that to
everyone. Makes grown champions check their pockets." *(a real smile)* "Listen —
both dojos are closed for the day, and after *that* spectacle I wouldn't blame the
whole street for shutting early. No battles today. But you travel, I can tell. Come
back when it's quieter and I'll give you a proper match. That's a promise from
Bruno, and Bruno keeps them."

**Sabrina:** "Come back when this city remembers what these dojos were *for.*" *(she's
already turning to go)* "...And mind the gates, traveler. Not every road out is open
today. You'll find that out for yourself soon enough."

*(They leave together. Set `FLAG_APOC_CH5_DOJO_INCIDENT_DONE`. Sabrina's last line
soft-foreshadows the exit fork in 5.5. Neither is battled.)*

---

## 5.4 · City Texture and Small Events (optional)

**Intent:** the city feels lived-in; each beat is flavor now and a seed later. All
optional talk-to NPCs. No flags required (pure flavor), except the Copycat reward,
which sets its own item flag.

### 5.4a · Copycat (`T11R0802`) — the reward beat

**Copycat:** "Hiiii! Are you new? You LOOK new. Do this—" *(strikes a pose; the player
does nothing; she copies the nothing perfectly)* "—see? I'm the best at copying. The
BEST. I copy everybody. The mailman, the mayor, the lady who yells at the train. Wanna
see my dolls?"

**Copycat:** "Okay okay, I'll trade you. I want a thing to copy that I don't have yet.
Bring me—" *(she names a specific item / shows a Pokémon she wants to mimic)* "—and
I'll give you something good. Promise! Copies don't lie. Well. Copies ONLY lie. But
I don't!"

**Copycat (on fulfillment — reward):** "EEE! Perfect! Watch—" *(she nails the
imitation)* "—ta-DAA. Okay, deal's a deal. Here, this is for you." *(she digs a
gleaming lump out of a drawer full of shiny junk)* "It's shiny! I LOVE shiny. But
you've got that stuck-far-from-home look, and shiny things sell for a LOT — you need
it more than I need another one." *(presses a **Nugget** into the player's hands —
see [KANTO_ITEMS.md](KANTO_ITEMS.md))* "Come back anytime! I'll be you next time!
Byeee!"

### 5.4b · The Magnet Train engineer (café — Silph seed)

**Off-duty engineer:** "Don't get me started on the train. No — too late, you made eye
contact, you're getting started." *(sips coffee)* "Silph did the renovation. Beautiful
work, I'll give 'em that. But *overbuilt.* You don't need that many sensors to move a
train from A to B. Half that hardware isn't measuring the *rails.*"

**Off-duty engineer:** "What's it measuring, then? Beats me. Above my pay grade. I just
fix what they tell me to fix and don't ask what the extra boxes are for." *(shrugs)*
"Probably nothing. It's always probably nothing." *(he doesn't believe that, quite,
but he's tired.)*

### 5.4c · The Silph employee on break (bench — special-projects seed)

**Silph employee:** "Lunch. Twenty whole minutes of not being in that building." *(eyes
closed, face to the sun)* "It's been *nonstop* up there. Special projects, special
projects, everybody's on a special project except me — I don't have the clearance, I
just keep the lights on for the people who do."

**Silph employee:** "Don't even know what they're working on. Up past the badge floors,
where the likes of me don't go. Long hours, weird shipments, people I've never seen
badging in at 3 a.m." *(opens one eye)* "Pays the rent, though. You learn not to ask.
Asking's not in the benefits package." *(closes the eye again.)*

### 5.4d · Visiting Hoenn trainer (Pokémon Center — regional identity)

**Hoenn trainer:** "Oh, you're off-region too? Thank GOSH, I thought it was just me
feeling like a fish out of water." *(grins)* "I'm Hoenn. Just passing through — down to
Vermilion to catch a boat south, back toward the sea where things make sense."

**Hoenn trainer:** "Kanto's so... *structured*, you know? Everything in a grid.
Everything on a schedule. Back home a route is a jungle or a coastline and you just
*deal* with it." *(friendly)* "You'll figure this place out. Or you won't and you'll
leave, like me. Either's fine. Safe travels."

### 5.4e · Street performers (central square — city life)

**Performer (announcer voice):** "—and the CHALLENGER pivots, ladies and gentlemen,
look at that footwork! This is EXHIBITION battling, Saffron-style — all the drama, none
of the badges! Throw a coin in the hat if your heart rate went up!"

**Spectator (in the crowd):** "They do this every afternoon. Same two trainers, same
flashy finish. It's rigged as a card game and I love it anyway. Sit, watch. The city's
not all glass and hurry."

---

## 5.5 · Moving On — The Exit Fork

**Intent:** four gates, two open; the player chooses a road out. Both open paths reach
Lavender (Celadon dead-ends for now). **End state:** `FLAG_APOC_CH5_DONE` on passing an
open gate. Hands off to Chapter 6.

### 5.5a · North → Cerulean (Route 5 gatehouse — **closed**)

**Gate guard (Route 5):** "Sorry, friend — Route 5's closed off right now. Had a pack
of dojo students take their little disagreement *north* this afternoon, before the
masters got hold of it. Bit of a mess up there. Pokémon everywhere, nothing cleared."

**Gate guard (Route 5):** "Give it a day, maybe two. You were *at* that circus in the
plaza? Then you know exactly why I can't let you through. Cerulean'll keep." *(The
player's own experience explains the block.)*

### 5.5b · South → Vermilion (Route 6 gatehouse — **League checkpoint**)

**League officer (Route 6):** "Hold up. Heading south to Vermilion? Vermilion's a
working port — League security screens everyone inbound these days. I'll need your
**Kanto trainer registration** or a **League travel permit.**"

*(The player has neither.)*

**League officer (Route 6):** "...Johto credentials. Right. Those don't carry here,
I'm afraid — different region, different paperwork." *(not unkind)* "Tell you what
*does* count: a **Kanto Gym Badge.** Earn one and that's all the proof I need that
you're legitimate training stock, not someone slipping toward the docks. Come back
with a badge and I'll wave you straight through. Until then — sorry. Can't."

### 5.5c · West → Celadon (Route 7 gatehouse — **open**, dead-end)

**Gate guard (Route 7):** "West to Celadon? Go right ahead — that one's open. Lovely
city, big department store, the Game Corner if that's your vice." *(beat)* "Heads-up,
though: the through-road past Celadon — Cycling Road — needs a bike, and the long way
round's blocked just now. So it's a there-and-back from Celadon for the moment. Still
worth the trip."

### 5.5d · East → Lavender (Route 8 gatehouse — **open**)

**Gate guard (Route 8):** "East? Route 8's clear, heads toward Lavender Town. Fair few
trainers along the way at about your level — good road to shake off a bad day on, if
you ask me." *(nods)* "Mind yourself near Lavender. It's a... quiet sort of place.
Folks there keep to the tower and their own business. You'll see."

### 5.5e · The close

*Whichever open gate the player takes, a final beat as they leave the city.*

*(Behind the player, Silph Co.'s tower catches the afternoon light. Somewhere inside
it, Mel is getting the story of a lifetime or getting arrested. The player may never
find out which. They square their shoulders and walk — east toward Lavender, or west
to Celadon and back. Either way the road bends, eventually, to the same quiet town.)*

**[Chapter 5 ends — set `FLAG_APOC_CH5_DONE`; hand off to Chapter 6.]**

---

## Coverage Checklist (for the implementation pass)

- [ ] **5.1 Silph lobby** — tour podium, product case, **partnerships wall** (seed),
  **train display** (seed), badge-locked elevator; Mel's bulldoze-and-vanish (NO
  farewell line); receptionist apology + security; set
  `FLAG_APOC_CH5_SILPH_PARTING_DONE`. Leave the Steven slot hidden.
- [ ] **5.2 Stranding** — Magnet Train attendant rail-pass rule; player internal beat;
  set `FLAG_APOC_CH5_STRANDED`.
- [ ] **5.3 Dojo flashpoint** — request-a-battle interrupt (both dojos, symmetric);
  plaza brawl tableau (dojo crowd sprites, **no player battle**); Machamp/Alakazam
  escalation; **Sabrina & Bruno** break-up + introductions (the "heavier than your
  level" beat; the squeezed-city explanation); both dojos close; set
  `FLAG_APOC_CH5_DOJO_INCIDENT_DONE`.
- [ ] **5.4 City texture** — Copycat (reward), train engineer (seed), Silph employee
  (seed), Hoenn trainer (identity), street performers (life).
- [ ] **5.5 Exit fork** — R5 closed (`FLAG_APOC_CH5_ROUTE5_CLOSED`), R6 League-gated
  (badge-conditional), R7 open/dead-end, R8 open; set `FLAG_APOC_CH5_DONE` on exit.

## Retheme / cut stubs (engine-facing notes)

- **Silph lobby Steven slot** (`SPRITE_DAIGO`, `FLAG_HIDE_SAFFRON_CITY_STEVEN`): leave
  hidden — no Steven cameo this chapter. Lobby cast = receptionist + security only.
- **"Psychic Dojo" = Saffron Gym** (`T11GYM0101`): reframed as the psychic dojo. Its
  placed psychic trainers (`MEDIUM_DARCY/REBECCA`, `PSYCHIC_M_JARED/FRANKLIN`) and the
  Fighting Dojo's `GSFIGHTER`/`GSLEADER*` crowd are **spectator/brawl tableau** here —
  do **not** wire `trainer_battle`. The gym/dojo opens for real challenges in a later
  chapter (spec Sabrina's and the Fighting master's teams there).
- **Sabrina / Bruno** (`TRAINER_LEADER_SABRINA_SABRINA`, `TRAINER_ELITE_FOUR_BRUNO_BRUNO`):
  introduced as institutional figures, **not battled**. Reuse
  `FLAG_HIDE_SAFFRON_GYM_SABRINA` for Sabrina's plaza appearance; place a Bruno sprite
  for the beat.
- **Rail pass** (`ITEM_PASS`): never granted in Kanto — the stranding lock. Do not add
  a Kanto purchase path.
- **Route 6 south gate**: gate on **Kanto-badge state**, not a one-shot flag — it
  re-opens automatically once a Kanto badge is earned.
- **Celadon** (Route 7 west): open but a **dead-end for now** (Cycling Road needs a
  bike). Chapter 6 treats Celadon as optional; the spine goes east to Lavender.
