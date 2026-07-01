# Chapter 4 — Scene Spec & Full Script (Route 34 · Goldenrod · Radio Tower · Magnet Train · Saffron arrival)

This is the **complete line-by-line dialogue** for Chapter 4, the single source of
truth for what every character says. It sits one altitude below
[CHAPTER4_BUILD.md](CHAPTER4_BUILD.md) (staging, flags, files) and pairs with
[JOHTO_BATTLES.md](JOHTO_BATTLES.md) (rosters) and [JOHTO_ITEMS.md](JOHTO_ITEMS.md).

**Status:** ⬜ not implemented — this is the writing pass. Engine wiring (`.gmm`
message banks, `npc_msg` beats, `scr_seq` hooks) happens at implementation; no
message IDs are assigned yet.

**Conventions:**
- `{PLAYER}` = player name token; `{RIVAL}` = Kestra; `{STARTER}` = the player's
  starter species; `{KESTRA_MON}` = Kestra's type-advantage counter-starter (the
  evolved form by this chapter), branched on `VAR_APOC_FRIEND_STARTER`. Final
  HG-charset pass (dash, ellipsis, apostrophe) happens at `.gmm` transcription.
- Battle lines use **[Pre]** (sent-out intro), **[Loss]** (last Pokémon faints,
  in-battle), **[Post]** (overworld, after).
- *Italic parentheticals* are terse staging cues, not spoken. Per house style
  ([[dialogue-over-narration]]) drive scenes with dialogue; keep narration minimal.
- **Mel never battles** (non-combatant by design). She is dialogue and movement only.
- **No new badge this chapter.** The only required battles are the six Route 34
  sight-trainers; the Kestra send-off is the chapter's one "boss."

---

## 4.0 · Route 34 — The Road In

*The Ilex west exit lands the player on Route 34, descending toward the city. On
first entry, the music opens up and the Goldenrod skyline is visible at the bottom
of the screen. One ambient beat — no lockall.*

**Route 34 sign:** "ROUTE 34 — Goldenrod City, just south. Mind the Day-Care."

**Hiker at the ridge (first overlook, optional):** "First time seeing it? Yeah.
Everybody stops here the first time." *(nods at the skyline)* "Biggest city in
Johto. You can hear it from up here if the wind's right."

### 4.0a · The displaced Oddish (ambient, optional — the Ch3 payoff)

*A local near the Day-Care fence, or Picnicker Gina pre-battle. Mundane, not
ominous. Pays off the Ilex→Route 34 displacement seeded in Chapter 3.*

**Local by the fence:** "Funny thing — didn't used to see the little weed-Pokémon
out here. Oddish. They like the deep forest, my dad always said." *(shrugs)* "Now
they're all over the south grass. Whole families of 'em. Forest's changing, I
guess. Things move around."

### 4.0b · The Day-Care (systems beat, talk-to)

**Day-Care Man (at the fence):** "Hey, you. You raise Pokémon? Course you do, look
at you." *(jerks a thumb at the gate)* "Me and the missus run the Day-Care here.
You leave one with us, we'll raise it while you're off doing... whatever it is
you kids do. It'll come back stronger. Might even come back knowing something new."

**Day-Care Man (if player has Pokémon to deposit):** "Just one or two at a time,
mind. We're good, we're not miracle workers. Come back for 'em whenever. We'll
settle up the fee then."

**Day-Care Lady (inside, optional):** "Oh, they're no trouble at all. We've raised
Pokémon from every region you can name, these last years. Had a little blue thing
last spring nobody could place — turned out it was from clear across the sea." *(warmly)*
"World keeps getting smaller, doesn't it."

### 4.0c · Route 34 sight-trainers (six)

*All six are vanilla `std_trainer` placements in `035_R34.json`, re-lined as
Goldenrod-outskirts locals. Rosters/levels in [JOHTO_BATTLES.md](JOHTO_BATTLES.md).*

**Youngster Samuel** — `TRAINER_YOUNGSTER_SAMUEL`
- **[Pre]:** "You came from the forest? Man, I've been waiting out here ALL day for
  someone to come from the forest. Battle me, battle me!"
- **[Loss]:** "Aw, all day for THAT?"
- **[Post]:** "Okay but that was still the best thing that's happened to me today.
  The city's right there, you know. You're almost famous already."

**Picnicker Gina** — `TRAINER_PICNICKER_GINA`
- **[Pre]:** "We drove out from the city for the quiet. Then the Oddish ate half the
  sandwiches." *(sighs)* "Fine. One battle, while my brother re-packs the basket."
- **[Loss]:** "You're better than the sandwiches deserved."
- **[Post]:** "Go on, the city's beautiful at this hour. Get a window seat on the
  monorail if you can. Best view in Johto and nobody ever takes it."

**Youngster Ian** — `TRAINER_YOUNGSTER_IAN`
- **[Pre]:** "Samuel says he's the best trainer on this route. Samuel is a liar.
  Watch."
- **[Loss]:** "...Okay. Don't tell Samuel."
- **[Post]:** "When you get to the Department Store, go to the top floor. The vending
  machines up there have the good stuff. That's a real tip, that's not a trick."

**Policeman Keith** — `TRAINER_POLICEMAN_KEITH` *(gated `FLAG_UNK_1D2`)*
- **[Pre]:** "Hold up. Routine. Big-city outskirts, we keep an eye on who's coming
  in off the forest road these days." *(beat)* "Nothing personal. Let's make it a
  battle instead of a checkpoint, huh?"
- **[Loss]:** "Heh. You're clean. Move along, trainer."
- **[Post]:** "Word of advice, since you seem the type to wander into things — city's
  bigger than it looks and not everybody in it is what they advertise. Keep your
  wits in the Underground."

**Camper Todd** — `TRAINER_CAMPER_TODD`
- **[Pre]:** "Last campsite before the city! After this it's all concrete. Let's do
  this properly — out here, in the grass, the old way."
- **[Loss]:** "Worth it. Now I can tell people I lost to a real one."
- **[Post]:** "Enjoy the city. I give it a day before I'm back out here. Too loud in
  there. Too many people who want something."

**Pokéfan Brandon** — `TRAINER_POKEFAN_M_BRANDON`
- **[Pre]:** "Aren't they wonderful? All of them, every one, from everywhere. I come
  out here just to see what wanders down the forest road." *(grins)* "Show me yours.
  Properly. With a battle."
- **[Loss]:** "Magnificent. Truly. Thank you for that."
- **[Post]:** "You can feel it out here, can't you — the world getting bigger. Ten
  years ago this grass was all Rattata and Drowzee. Now? Now anything could walk
  out of those trees."

### 4.0d · Item balls (no dialogue)

*`std_itemball_r34_nugget` → Nugget. `std_itemball_r34_tm63` → TM63 (Embargo). See
[JOHTO_ITEMS.md](JOHTO_ITEMS.md).*

---

## 4.1 · Goldenrod City — The Big Arrival

**Intent:** the city as a playground and a showcase. Free exploration; nothing here
is mandatory until the player engages the rival beat (4.2). **End state:**
`FLAG_APOC_CH4_GOLDENROD_INTRO_DONE` (arrival framing one-shot).

*Trigger: first step into the city from the Route 34 gate. A brief beat — the
camera finds the skyline, the city's theme comes up, then control returns. No
forced dialogue.*

**City sign (north of the gate):** "GOLDENROD CITY — The Festival of Commerce.
Where everything from everywhere ends up."

### 4.1a · Street ambient (talk-to, optional)

**Excited kid (near the plaza):** "Did you SEE her? The radio lady? She's doing a
LIVE one today. My mom says she's gonna get herself in trouble one day and my dad
says good, somebody should." *(beat)* "I think she's the coolest person alive."

**Tourist with a bag:** "I came for the Department Store and I am NOT leaving until
I've been to every floor. Six floors! Do you understand? Where I'm from we have a
shop. One shop."

**Office worker (brisk):** "Excuse me — no — sorry, I'm late. Everyone here is
always late and always going somewhere. You'll get used to it or you'll leave."

**Old woman on a bench:** "I've watched this city my whole life, dear. It used to
end at the river. Now it doesn't end at all. Trains, the radio, that great glass
trading hall — the whole world pours through here now." *(pats the bench)* "I don't
mind it. Loud is just quiet with people in it."

### 4.1b · Department Store (flavor; stock in ITEMS)

**Clerk, 1F:** "Welcome to the Goldenrod Department Store! Medicine and basics this
floor. TMs are on 2F, vitamins on 5F, and if you've never seen a real TM rack
before — sweetheart, go up. Go up right now."

**Shopper, 2F (by the TM rack):** "They sell *moves.* In a *box.* I will never get
over it. Back home a TM is a treasure. Here it's on a shelf next to the others."

**Rooftop vendor (top floor):** "Vending machines, fresh drinks, best view in the
city. You can see the train station from here. See it? That silver line going east?
That's the way to Kanto. Reopened last week. First time in years."

### 4.1c · Game Corner (flavor; prizes in ITEMS)

**Game Corner attendant:** "Coins in, luck out, prizes on the wall. House rules,
house odds, house always wins a little — but the prizes are real and that TM in the
corner case is the real deal. Good luck."

### 4.1d · Underground (flavor)

**Traveling merchant (Underground):** "Pssst. Over here. You look like someone with
taste." *(lowers voice)* "I deal in the *real* stuff. Straight from Hoenn. Sinnoh,
when I can get it. Things you can't buy upstairs at any price." *(winks)* "The world's
open for business, friend, if you know which doors. Come back when your wallet's
heavier."

**Underground passer-by:** "Watch yourself down here. Half the deals are honest and
the other half are *very* friendly about not being. You'll learn to tell."

### 4.1e · Global Terminal (the on-theme room)

**Terminal guide (just inside):** "First time at the Global Terminal? Welcome.
This whole building exists for one reason: to trade across regions. Used to be, you
caught what your region had and that was that. Now?" *(gestures up at the hall)*
"Now a kid in Goldenrod can trade with a kid in Sinnoh before breakfast. We connect
the storage networks. Mostly." *(small laugh)* "Ask Bill about the 'mostly.'"

**Terminal patron:** "I sent a Pokémon to my cousin in Hoenn this morning and got
one of theirs back. Just like that. My grandparents would not have believed me."

### 4.1f · Bill (optional seed — `FLAG_HIDE_GOLDENROD_BILL`, Bill's House)

**Bill:** "Oh — hi, hello, sorry, I'm elbow-deep in it today." *(at a terminal,
surrounded by cable)* "Storage networks. Between regions. They *talk* to each other
now — Johto to Kanto, Kanto to Hoenn, the whole web. When it works it's beautiful."
- **Bill (continued):** "When it *doesn't*... transfers stall. Boxes go quiet for
  an hour and come back like nothing happened. A Pokémon left here, arrived there, but
  the system swears for ninety seconds that it's in *neither* place." *(rubs his eyes)*
  "Probably nothing. Probably load. The system's just busier than anyone built it to
  be." *(beat)* "...Still. I don't love a system that can briefly lose track of a
  living thing. Anyway! Don't mind me. Welcome to Goldenrod."

*(Pure technical flavor. Plants, quietly, that the inter-region infrastructure has
seams — and that something could move through a seam. No follow-up this chapter.)*

### 4.1g · International trainer (optional seed — Pokémon Center)

**Visiting trainer:** "You're a local? Lucky. I'm just passing through — came up on
the boat, taking the train down to Kanto, then home." *(brightens)* "You should see
where I'm from someday. **Mossdeep.** Out on the water, east as east gets. Nothing
like this place. Quieter. The sky's bigger." *(beat)* "Everybody's going somewhere
these days, huh? Wasn't always like that."

---

## 4.2 · The Rival Resurfaces

**Intent:** Kestra reconnects and pulls the player to the Radio Tower — the natural
route to Mel. **Trigger:** one-time approach scene near the Department Store front /
plaza, after `FLAG_APOC_CH4_GOLDENROD_INTRO_DONE`. *lockall.*

**{RIVAL}:** *(spotting the player, loud enough to turn heads)* "There you ARE!"

**{RIVAL}:** "Do you know how big this city is? I've been here four days and I STILL
get lost in the Underground. I've been to the top of the Department Store twice. I
beat the slots once and lost it all back in like a minute. It's incredible. I love
it here."

**{RIVAL}:** *(grabbing the player's arm)* "Okay, no, listen, you have to come with
me, RIGHT now — the Radio Tower. There's a live show today. The radio lady? **Mel?**
She's famous, she's kind of a big deal, my landlady says she's a menace which means
she's definitely cool —"

**{RIVAL}:** "— and TODAY she's doing the **Azalea thing.** The Slowpoke Well. The
thing that actually happened." *(beat, not connecting it to the player at all)*
"It's all anybody's talking about. Come on. Live. We can't miss it."

*(She doesn't know — or doesn't think about — the fact that the player was *there*.
To her this is just a cool broadcast. She heads off toward the Radio Tower; the
player is free to follow or dawdle. Set the rival-resurfaces one-shot; reveal Kestra
at the Radio Tower via `FLAG_HIDE_RADIO_TOWER_RIVAL`.)*

**{RIVAL} (if spoken to again before the tower):** "Radio Tower! Big one! You can't
miss it! Hurry, we're gonna miss the good part!"

---

## 4.3 · The Radio Tower — Enter the Journalist

**Intent:** Mel's live broadcast; Kestra's brag; the interrogation; the Silph-coat
lever; the Saffron snap decision. **Trigger:** player enters Radio Tower 1F with the
rival scene done. **End state:** `FLAG_APOC_CH4_MEL_MET`.

*Inside: a small live studio. Mel at the broadcast desk (repurposed leader slot),
a scatter of studio-audience NPCs, Kestra near the front, starstruck. A broadcast is
already in progress — the player walks in mid-segment. Stage Mel's lines as
"on-air," fast and performed.*

### 4.3a · The broadcast (Mel, on air)

**Mel (on air):** "— and that's the thing, that's the THING, that's what nobody
wants to say out loud: it's not one incident. Azalea was not one incident."

**Mel (on air):** "A well full of Slowpoke in a town that's loved those Slowpoke for
a hundred years, and somebody was down there doing something to them. Fine. Terrible,
but fine, file it, move on — except." *(a beat, leaning in)* "Except I've got a
missing-Pokémon report out of the Ruins of Alph. Equipment nobody can identify on a
route near Violet. 'Researchers' at three sites that didn't ask for any researchers."

**Mel (on air):** "Now I'm not saying it's connected. I would NEVER say a thing I
can't prove on air, my producer is making a face at me right now." *(she is clearly
saying it's connected)* "I'm just saying — when you've been doing this as long as I
have, you learn the shape of a thing before you can name it. And this has a shape.
This has a very particular shape."

**Mel (on air):** "Somebody is running a quiet little operation across this whole
region, polite and professional and gone before anyone gets a good look. And one day
somebody is going to get a good look. And when they do —" *(snaps her fingers)* "—
they should call ME first. We're back after this."

*(The "on-air" light clicks off. The studio relaxes. Kestra is vibrating.)*

### 4.3b · The brag (Kestra)

**{RIVAL}:** *(barreling up to the desk before anyone can stop her)* "That was SO
good. That was incredible. Okay, okay — Ms. Mel, hi, I'm a huge fan, but you don't
have to take my word about Azalea being real because—" *(grabbing the player and
shoving them forward, beaming, proud)* "—because THIS one was THERE."

**{RIVAL}:** "Down in the Well. While it was happening. My friend went IN. Saw the
whole thing. Tell her! Tell her about the —"

*(Kestra has no idea what she's just done. She thinks she's bragging about her cool
friend. She is.)*

### 4.3c · The interrogation (Mel)

*Mel's attention snaps to the player like a spotlight. Everything speeds up.*

**Mel:** *(no longer performing — this is the real her, and it's somehow faster)*
"In the Well. You were in the Well." *(not a question)* "Okay. Okay okay okay. Don't
move, don't leave, you are the most interesting person who has walked through that
door in a YEAR. What did you see. Start anywhere. Start at the worst part."

**Mel:** "How many of them? — no, don't count, ballpark. What did they wear? Were
they loud, were they scared, did they run? People who run are amateurs. Did they
run?"

*(Beat for player reaction — the build can branch flavor here, but the script funnels
to the one detail that matters.)*

**Mel:** "Equipment. There's always equipment. Cases, tablets, something with a logo
on it — people never stamp the *important* stuff but they ALWAYS stamp the
*expensive* stuff. Was there a name on anything. Anything at all. Think."

*(The player surfaces the detail — staged as a player-driven beat, then Mel seizes
on it.)*

**Mel:** "A lab coat." *(very still, for the first time)* "On the gear. A coat with
a stamp on it. What did the stamp say."

**Mel:** *(the air changes)* "...Silph. You said **Silph.** Silph Co." *(quiet, almost
to herself)* "Say it once more and don't think about it, the first answer's the true
one — what was on the coat."

*(Confirmation beat. Then Mel exhales like she's been holding her breath for a year.)*

**Mel:** "Silph. *Silph.*" *(a laugh, disbelieving, delighted, a little frightening)*
"I have been pulling that thread for a year and a half and every time I get close it
goes soft in my hands. Lawyers. 'No comment.' Doors that lock from the inside. And
you — a KID off the forest road — you just walked in and handed me the one thing I
could never get: a witness who saw the name in the dirt."

### 4.3d · The snap decision (Mel)

**Mel:** *(already gathering her things, talking faster)* "Right. Okay. Here's what's
happening. The Magnet Train reopened last week — last WEEK, do you understand what
the odds of that are, the universe does not hand a reporter a reopened train and a
live witness in the same month unless it WANTS something printed —"

**Mel:** "Silph Co. headquarters is in Saffron. That's Kanto. That's two hours on the
fast rail and I have a pass and you have a face that saw the coat." *(turning to the
player, intense, certain)* "You're coming with me. Right now. I need you in that city.
I need someone who can say *I saw it* and mean it. Grab your bag, we are going to go
look the dragon in the lobby."

**Mel:** *(already at the door)* "Don't overthink it. Overthinking is just fear
wearing a smart coat. Let's GO."

---

## 4.4 · The Send-Off — Kestra's Last Battle and the Goodbye

**Intent:** Kestra registers the insanity, refuses to follow, and says goodbye the
only way she knows how — a battle. **End state:** `FLAG_APOC_CH4_RIVAL_SENDOFF_DONE`;
Kestra stays in Goldenrod.

### 4.4a · The argument (short)

**{RIVAL}:** *(catching up, the excitement curdling into alarm)* "Wait. Wait wait
wait — Kanto? You're going to KANTO? With— with HER? On a TRAIN? Right now??"

**{RIVAL}:** *(to Mel, fast)* "You can't just— that's my— you can't just TAKE people!"

**Mel:** *(not unkind, just already three steps gone)* "I'm not taking anyone, kid.
Your friend's got legs and a story in their pocket. They can say no." *(a glance back
at the player, a small grin)* "They're not going to say no. Nobody interesting ever
says no." *(she heads for the station; she will not wait long)*

**{RIVAL}:** *(to the player, quieter, the bravado cracking)* "...You're actually
gonna go. Of course you're gonna go. Look at you." *(beat)* "Kanto. With a stranger.
On a train. That is the single most reckless, most *Champion* thing I have ever heard
and I HATE that it's not me doing it."

**{RIVAL}:** "I'm not coming. Don't— don't make that face, I'm NOT. This is your
crazy thing, not mine. I've got a city to figure out and a team to build and somebody
in this dumb friendship has to stay the sensible one for ONE day." *(small, real)*
"Guess it's my turn."

### 4.4b · The send-off battle (the chapter's one boss)

*Kestra's team is the evolved counter-starter + grown Johto catches, branched on
`VAR_APOC_FRIEND_STARTER`. Full rosters in [JOHTO_BATTLES.md](JOHTO_BATTLES.md). Drive
from the `SPRITE_GSRIVEL` slot.*

**{RIVAL}:** *(squaring up, scrubbing her eyes once)* "One battle. Right now. If
you're gonna go do something this stupid, I am NOT letting you walk onto that train
soft. Show me you're ready. Show me I don't have to worry." *(she does have to worry)*
"Send it out!"

- **[Pre]:** "{KESTRA_MON}, GO! Come on — like we're home, like it's Route 29, last
  time for a while — give them everything!"
- **[Loss]** *(her last Pokémon faints)*: "...Yeah. Yeah, okay. You're ready. I knew
  it. I hate it, but I knew it."

### 4.4c · The goodbye

*Win or lose, the goodbye is warm and worried. Mel is audibly impatient off-screen —
characterization, not cruelty.*

**{RIVAL}:** "Okay. Okay. You're really doing this." *(deep breath, then the old
spark, forced up for the player's sake)* "Go look your dragon in the lobby, or
whatever she said. Be the one who saw it. That's — that's actually really cool, I'm
not gonna pretend it's not."

**{RIVAL}:** *(grabbing the player by both shoulders)* "But you CALL me. The second
it gets weird. And it's gonna get weird, {PLAYER}, you're going to a city built
around the people you saw in that Well — of COURSE it's gonna get weird. So you call
me. Pokégear. Day or night. Promise."

**Mel (off-screen, calling):** "TRAIN'S NOT GONNA WAIT, WITNESS!"

**{RIVAL}:** *(rolling her eyes, wet-eyed, grinning)* "Ugh. GO. Before I change my
mind and tackle you onto a different train." *(stepping back, hand up)* "...Smell ya
later, {PLAYER}."

*(The line lands soft — Silver's catchphrase, the one she's said with swagger since
Chapter 1, here turned into something gentle and a little scared. She stays in
Goldenrod. The Magnet Train Station is the objective.)*

---

## 4.5 · The Magnet Train

**Intent:** boarding on Mel's pass; the ride; Mel's Silph-threads monologue; the
cross-region passenger gallery. **Trigger:** player reaches the Goldenrod Magnet Train
Station with the send-off done.

### 4.5a · Boarding (Goldenrod Station)

**Station attendant:** "Magnet Train to Saffron, departing shortly. Passes, please."

**Mel:** *(flashing a pass and a press credential in one fluid motion, not slowing
down)* "Two. Press. They're with me — witness on the Azalea story, fully cleared,
we're on a deadline." *(to the player, low, already past the gate)* "Don't say
anything. You don't have a pass, I have a pass, the difference is a sentence I'm very
good at saying. Keep walking. Window seat."

*(Establish, lightly, that the player rides on Mel's pass — they have none of their
own. This is the one-way gate. Don't belabor it; one line is enough.)*

**Station attendant (as they pass, half to himself):** "...Press. Sure. Everybody's
press this week."

### 4.5b · The ride (Mel's monologue + passengers)

*A short on-rails transitional sequence — window views blurring between regions. Mel
talks at the player the whole way. Tone stays light despite the subject.*

**Mel:** *(settling in, finally a little slower — this is as calm as she gets)* "Okay.
Window's yours. People always think they won't want the window and then they spend the
whole ride looking out it. Look — there, see how the country changes? You can almost
see where Johto stops being Johto."

**Mel:** "So here's what I've actually got, and it's not much, I want to be honest
with you because you're the realest source I've had in a year and I don't lie to good
sources." *(ticking on her fingers)* "Silph's research partnerships have been
expanding. Quietly. Into places research doesn't usually go. The Ruins of Alph.
Your well. A couple of sites up north I've only got rumors on."

**Mel:** "I don't have a theory. I want to be SO clear about that — I'm not one of
those people with a string-and-corkboard wall, I don't think there's a lizard running
the world. I have *threads.* Just threads. Things that shouldn't be near each other
that keep turning up holding hands." *(she shrugs, grinning)* "And I cannot leave a
thread alone. It's a medical condition. Ask anyone who's ever worked with me. Ask
anyone who's ever DATED me."

**Mel:** "But that coat. The Silph coat. That's not a thread, that's a *knot.* That's
the first hard thing I've ever had. And it came out of a kid's memory, off a forest
road, which means it's clean — nobody coached you, nobody lawyered you, you just SAW
it." *(she looks at the player, and for a second it's almost warm)* "You have no idea
how rare that is. A person who just saw the thing and says the thing. Don't ever lose
that. The job ruins it eventually. Hang onto it as long as you can."

*Passenger gallery (talk-to, optional):*

**Businessman:** "Saffron. Contract work. Silph Co., three months, can't say what."
*(checks his watch)* "Good company to have on a résumé. They're everywhere now, you
know. Every region. Can't move for Silph these days." *(he says it like a good thing)*

**Woman with luggage:** "Visiting my daughter in Vermilion. Haven't seen the sea in
two years. This train — two hours! It used to be two DAYS and a boat." *(beaming)*
"What a time to be alive."

**Young trainer:** "Kanto gym challenge, here I come. Eight badges, the proper
circuit. You doing the challenge too?" *(if anything)* "...Huh. 'Following a reporter
to a corporate headquarters.' That's a new one. Good luck with that, I guess?"

**Kid at the window:** "MOM. MOM. We're going so FAST. The trees are LINES." *(no one
answers; the kid is delighted anyway)*

---

## 4.6 · Saffron City — Arrival (chapter close)

**Intent:** first steps in Kanto; corporate atmosphere; Silph skyline; Mel drives
toward the lobby; chapter ends on momentum. **End state:**
`FLAG_APOC_CH4_SAFFRON_ARRIVED`. *Chapter 5 picks up immediately.*

*The train decelerates. Saffron Station — clean, fast, institutional. The player
steps off into Kanto for the first time.*

**Station announcement (PA):** "Now arriving: Saffron City. Welcome to Kanto. Please
mind the gap, and mind the time — Saffron waits for no one."

**Saffron commuter (brisk, barely stopping):** "First time? Tower's that way, you
can't miss it, nobody misses it." *(he's already gone)*

**Saffron employee (Silph badge on the lapel):** "Visiting the company? Lobby's open
to the public till six. Be nice. They watch the lobby." *(a thin professional smile)*
"Everyone's very friendly here. Famously friendly."

*(The atmosphere does the work — bigger than Goldenrod, colder, Silph's tower over
everything. Keep arrival NPC lines short and clipped. A closed-dojo notice can be
visible for Chapter 5 setup; don't engage it here.)*

### 4.6a · The close (Mel)

**Mel:** *(stepping out ahead of the player, throwing her arms wide at the city like
she owns it)* "KANTO. Smell that? That's industry. That's a thousand people who all
think they're the most important person in the building." *(she points up, at the
Silph tower)* "And THAT is where they keep the answers."

**Mel:** "Okay. Stick with me. We're not going to do anything crazy — not yet, not
today. Today we just walk into the lobby like two perfectly ordinary people and we
LOOK. You see what a thing looks like when it's pretending to have nothing to hide,
and then later you know exactly where it's lying." *(she grins back at the player)*
"Come on, witness. Let's go see the public face."

*(She heads toward the tower. The player follows. The chapter ends here — the two of
them walking into Saffron together, momentum intact, the door not yet closed behind
them. Chapter 5 opens on the consequences.)*

**[Chapter 4 ends — set `FLAG_APOC_CH4_SAFFRON_ARRIVED`; hand off to Chapter 5.]**

---

## Coverage Checklist (for the implementation pass)

Trainer/NPC slots that need lines wired, verified against the disasm zone JSON:

- [ ] **4.0 Route 34** — six sight-trainers (`YOUNGSTER_SAMUEL`, `PICNICKER_GINA`,
  `YOUNGSTER_IAN`, `POLICEMAN_KEITH`, `CAMPER_TODD`, `POKEFAN_M_BRANDON`), each
  Pre/Loss/Post; Day-Care man + lady; displaced-Oddish ambient line; skyline-reveal
  hiker; two item balls (Nugget, TM63 Embargo).
- [ ] **4.1 Goldenrod** — arrival framing one-shot (`FLAG_APOC_CH4_GOLDENROD_INTRO_DONE`);
  street ambient (kid, tourist, office worker, old woman); Dept Store clerk + shopper
  + rooftop vendor; Game Corner attendant; Underground merchant + passer-by; Global
  Terminal guide + patron; Bill (`FLAG_HIDE_GOLDENROD_BILL`); international trainer
  (Center).
- [ ] **4.2 Rival resurfaces** — Kestra pull-to-Radio-Tower one-shot; reveal at tower
  (`FLAG_HIDE_RADIO_TOWER_RIVAL`).
- [ ] **4.3 Radio Tower** — Mel broadcast (4 on-air beats); Kestra brag; Mel
  interrogation funnel to the Silph-coat detail; Saffron snap decision; set
  `FLAG_APOC_CH4_MEL_MET`. Mel placed via leader slot; studio-audience flavor NPCs.
- [ ] **4.4 Send-off** — argument; **Kestra rival battle** (starter-conditional Pre,
  Loss/Post, `VAR_APOC_FRIEND_STARTER`); goodbye; set
  `FLAG_APOC_CH4_RIVAL_SENDOFF_DONE`; Kestra stays.
- [ ] **4.5 Magnet Train** — boarding-on-Mel's-pass beat (Goldenrod station attendant);
  Mel ride monologue; passenger gallery (businessman, woman, trainer, kid).
- [ ] **4.6 Saffron** — PA announcement; commuter + Silph employee; Mel's close; set
  `FLAG_APOC_CH4_SAFFRON_ARRIVED`; **no return path registered.**

## Retheme / cut stubs (engine-facing notes)

- **Goldenrod Rocket-takeover slots** (`SPRITE_ROCKETM`, `FLAG_HIDE_ROCKET_TAKEOVER_*`
  in `073_T25.json`): the takeover event doesn't exist in Apocrypha — leave hidden.
  Dress the city through interior/shop NPCs instead.
- **Radio Tower rival slot** (`SPRITE_GSRIVEL`, `FLAG_HIDE_RADIO_TOWER_RIVAL`): was the
  vanilla Silver radio encounter → now **Kestra** (brag + send-off battle).
- **Radio Tower leader slot** (`SPRITE_GSLEADER3`, `FLAG_UNK_318`): repurpose as **Mel**
  at the broadcast desk, or place a fresh NPC if a better sprite is available.
- **Magnet Train Pass** (`ITEM_PASS`): **withheld** from the player this chapter — they
  ride on Mel's. The missing pass is the one-way gate (resolved Ch5). Do not gift it.
- **Goldenrod Gym** (`T25GYM0101`, Whitney): **closed / leader away** this chapter — no
  badge. Re-opens on the player's later return to Johto. See
  [JOHTO_BATTLES.md](JOHTO_BATTLES.md) deferral note.
- **Saffron content** (Fighting Dojo `T11R0101`, gym `T11GYM0101`, deeper Silph
  `T11R0701`): closed/gated this visit — Chapter 5+ surface. Only the station + a
  street tease + the Silph lobby exterior are live for the arrival.
