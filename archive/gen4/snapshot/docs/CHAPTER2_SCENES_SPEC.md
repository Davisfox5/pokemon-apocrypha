# Chapter 2 — Scene Spec & Full Script (Routes 30/31 · Violet University · Sprout Tower · Union Cave)

This is the **complete line-by-line dialogue** for Chapter 2, the single source of
truth for what every character says. It sits one altitude below
[CHAPTER2_BUILD.md](CHAPTER2_BUILD.md) (staging, flags, files) and pairs with
[JOHTO_BATTLES.md](JOHTO_BATTLES.md) (rosters/levels) and
[JOHTO_ITEMS.md](JOHTO_ITEMS.md). Same format as
[CHAPTER3_SCENES_SPEC.md](CHAPTER3_SCENES_SPEC.md).

**Status:** ⬜ not implemented — this is the writing pass. Engine wiring (`.gmm`
banks, `npc_msg` beats, `scr_seq` hooks) happens at implementation; no message IDs
assigned yet.

**Conventions:**
- `{PLAYER}` = player name token; `{RIVAL}` = Kestra; `{STARTER}` / `{KESTRA_MON}`
  = the player's starter and Kestra's type-advantage counter
  (`VAR_APOC_FRIEND_STARTER`: Chikorita→Cyndaquil, Cyndaquil→Totodile,
  Totodile→Chikorita). Final HG-charset pass happens at transcription.
- Battle lines: **[Pre]** (intro), **[Loss]** (last Pokémon faints, in-battle),
  **[Post]** (overworld, after). Trainer names are the **real engine slots**.
- *Italic parentheticals* are staging cues, not spoken. Drive scenes with dialogue
  ([[dialogue-over-narration]]); keep narration minimal.
- **Tone reminder:** Chapter 2 is the bright, classic training chapter. Nobody is
  in danger. The only shadow is the *optional* Silph seed at the Ruins of Alph —
  polite, never ominous. The restraint here is what makes Chapter 3 land.

---

## 2.1 · Route 30 — The Road Becomes Real

**Intent:** Kestra reframes the road as the player's first real test; first human
battles; the held-item lesson. **End state:** `FLAG_APOC_CH2_ROUTE30_INTRO_DONE`;
Quick Claw obtained.

### 2.1a · Kestra opener (one-shot, southern bend)

*Kestra is waiting just far enough up Route 30 that the music and grass make it
feel official. Fires once.*

**Kestra:** "There you are! I was starting to think Gold's shoes were
decorative." *(falls in beside the player)* "Okay. Real talk. Cherrygrove was the
tutorial. *This* is the game. Wild Pokemon that don't care about us, trainers who
absolutely do, and an Apricorn guy who'll talk your ear off if you let him."

**Kestra:** "Rule one of being trainers: if a sign says Trainer Tips, we pretend
we read it. Rule two: Mr. Pokemon's place is up north and he gives stuff away.
We are definitely visiting Mr. Pokemon." *(grins)* "Race you to the first
trainer. Loser carries the conversation."

### 2.1b · Route 30 trainers

**Youngster Joey [Pre]:** "Hey! You and me! My Rattata is in the top
percentage of Rattata — you're gonna want to remember that name."
**Youngster Joey [Loss]:** "Top percentage and everything..."
**Youngster Joey [Post]:** "I'm registering you in my Pokegear. When my Rattata's
huge, I'm calling for a rematch. Constantly. Fair warning."

**Youngster Mikey [Pre]:** "I haven't decided if I'm a Flying guy or a Normal guy
yet. Help me find out!"
**Youngster Mikey [Post]:** "Okay. Neither. I'm an 'I lost' guy. For now."

**Bug Catcher Don [Pre]:** "Bugs are underrated. Watch them carry me!"
**Bug Catcher Don [Post]:** "They did not carry me. But they tried so hard."

### 2.1c · Apricorn man's house

**Apricorn man:** "Apricorns! Pick 'em, dry 'em, and old Kurt down in Azalea turns
'em into balls you can't buy in any shop. Here — take a Box to carry them." *(gives
Apricorn Box)* "When you reach Azalea, tell Kurt that Wesley still sends his best.
He'll know."  *(plants the Kurt/Azalea thread — pays off in Chapter 3.)*

### 2.1d · Mr. Pokemon's house — the held-item lesson

*Overstuffed collector's cottage: boxes, labeled jars, old field maps, one cleared
tabletop.*

**Mr. Pokemon:** "Visitors! And young ones, with that first-week-on-the-road shine.
Sit, sit. I collect curiosities — and I've learned that the smallest curiosity
often matters most." *(sets a small stone on the table)*

**Mr. Pokemon:** "A held item is a little promise. Your Pokemon carries it, and it
may answer at just the right moment — not because you were strong, but because you
*prepared*." *(slides it over — Quick Claw)* "This Quick Claw is not a shortcut.
It is a surprise. And surprises, in a tight spot, are sometimes enough."

**Mr. Pokemon:** "Go on. Clip it to one of yours. Preparation before power — that's
the whole lesson, and most trainers learn it far too late."  *(gives Quick Claw,
`FLAG`-gated.)*

**Kestra (if present):** "A free held item for sitting through a speech? Best trade
of my life. Thank you, Mr. Pokemon!"

---

## 2.2 · Route 31 & the Violet Gate

**Intent:** transition to the wider region; the Dark Cave "not yet" tease; arrival
at Violet. **End state:** player at Violet City gate.

**Bug Catcher Wade [Pre]:** "Six of these little guys and counting! One of them's
gotta beat you. Statistically!"
**Bug Catcher Wade [Loss]:** "Statistics lied to me."
**Bug Catcher Wade [Post]:** "If you ever want a Bellsprout or three, I'm your guy.
I've got... so many. Too many, honestly."

**Kid by Dark Cave mouth:** "You can go in, but you can't go *far* — it's pitch
black past the first room. You'd need Flash. They say the sages at Sprout Tower
teach it, if you're respectful enough to be taught anything." *(the Flash → Dark
Cave loop is set up here; Flash is the Sprout Tower reward.)*

**Dark Cave sign:** "DARK CAVE — Bring your own light. We mean it."

**Violet gatehouse attendant:** "Headed into Violet? Mind the foot traffic — half
of Johto's students are here now. The other half are *trying* to catch a Bellsprout
because someone told them it counts as spiritual preparation. It does not. Welcome
to a university town."

---

## 2.3 · Violet City — University City

**Intent:** establish Violet as Johto's academic capital; Earl as dean; plant the
quiet seeds. **End state:** campus open; Earl points the player at the tower.

### 2.3a · Earl's arrival tour (one-shot)

*Earl intercepts the player (and Kestra) near the gate/school approach. Energetic,
short — not the vanilla city tour.*

**Earl Dervish:** "Hah! New faces, road-dust still on them! Yes! Earl I am! Dean I
am also! Welcome, welcome, new road scholars!"

**Earl Dervish:** "Once a little school this was. Now? A *university*. For training
is a craft, and a craft deserves scholarship!" *(sweeps an arm across the campus)*
"Violet teaches many ways. Books for the mind. The court for the body. The tower,
for the spirit. Center and Mart, that way — heal, restock, then go and *learn*."

**Earl Dervish:** "See the tower first, I think. Old Sprout Tower, where the sages
train as they have for centuries. Then come find me at the practice hall. A
visitor we have — a real gym leader — and she does not stay forever." *(bustles
off)*

**Kestra:** "Did he just say a *real gym leader* is here? Okay, change of plans, we
are doing everything he said in that exact order. Tower, then gym lady. Move!"

### 2.3b · Campus ambient (Pokémon School / Practice Court)

**Lecture instructor:** "Type matchups aren't trivia — they're the difference
between a clean win and a fainted partner. Grass fears Fire. Water quenches it.
Round and round. Learn the circle until it's reflex."

**Status-move instructor:** "A sleeping Pokemon can't bite you. A poisoned one is
on a timer. Damage is loud; status is *patient*. The sages upstairs the hill will
show you patience the hard way, if you let them."

**Practice-court student [optional battle, Pre]:** "Court rules — clean match, no
hard feelings. Ready?"
**Practice-court student [Post]:** "Good switches. You actually *think* between
turns. Half the people here just mash."

### 2.3c · The library (planted seeds — keep casual)

**Student A (radio seed):** "There's this interviewer on the Goldenrod station —
she asks the questions nobody else will. I think she's onto something."
**Student B (dismissive):** "She's a conspiracy nut, is what she is. 'Patterns,'
'connections.' It's radio drama. Go back to studying."  *(first Mel seed.)*

**Professor (corporate seed):** "We've had more visiting scholars this year than I
can remember — quite a few from corporate labs, actually. Silph, others. A sign of
the university's growing prestige, I should think." *(says it warmly, thinks
nothing of it.)*  *(first Silph/corporate seed — pays off across the game.)*

**Student C (next-destination seed):** "Once I'm done here I'm going straight for
the Azalea gym. A real badge! Bug types, they say. I just have to survive the
forest after." *(sets up Chapter 3.)*

**Map-card kid:** "The world's gotten *small*, my gran says. Trains, ships, the
radio — Pokemon nobody round here had ever seen, now you spot one every other
week. She says it's wonderful. She also says it's a lot." *(light inter-region
flavor — see DESIGN.md *Inter-Regional Exchange*.)*

**Violet Mart clerk:** "Student prices — Potions, Antidotes, status heals, the
basics. Cram bag before the tower; those sages love a good Sleep Powder."

**Violet Nurse:** "Long day on the road? Let's get your team rested. ...You're
challenging Sprout Tower? Be respectful up there. The sages forgive a loss. They do
not forgive rudeness."

---

## 2.4 · Sprout Tower — Ren's Prank

**Intent:** the chapter's centerpiece — mediation quest, the status/support battle
lesson, and Ren. **End state:** tower reopened; **TM70 Flash** from Elder Li;
**Oran Berry ×3** from Ren.

### 2.4a · The commotion (campus)

*A disturbance breaks out; Earl is exasperated; Ren has been caught spooking the
Bellsprout that form the tower's living support columns.*

**Flustered sage (at the tower doors):** "The whole tower *swayed*! Decades of
discipline and a *child* set our Bellsprout panicking for a laugh! The doors are
shut to university students until this is made right!"

**Earl Dervish:** "Ren. *Ren.* Again it is Ren. Talent he has, sense he has *not*."
*(to the player and Kestra)* "Go with me on this. Mediate. The boy will come — I
insist, and I am, occasionally, insistent."

**Ren (defensive):** "It was not vandalism! It was... *unauthorized field
placement*. Of some tags. Around a tower. That, in hindsight, sways."

**Kestra (caught, not sorry):** "...Okay, in fairness, I *did* dare him. But I
thought he'd chicken out! That's the whole point of a dare!"

**Ren:** "She said the tower needed more excitement. I may have supplied too much
excitement. Look — I'll fix it. I just don't know how to fix it *politely*. That's
not my event."

### 2.4b · The sage battles (status/support lesson)

*Six sages across the floors. Bellsprout/Hoothoot/Gastly, leaning on Growth, Sleep
Powder, Hypnosis, Reflect — teaching moments, not walls. Shared voice with light
variation; map to the real slots.*

**Sage Chow [Pre]:** "Strength is loud. Sit with patience a while. My Bellsprout
will teach the lesson gently."
**Sage Chow [Loss]:** "...Patiently undone. The lesson turns on the teacher."
**Sage Chow [Post]:** "You waited out the powder instead of panicking. Good. Most
do not."

**Sage Nico [Pre]:** "A trainer who only knows how to attack knows only half of
battle."
**Sage Nico [Loss]:** "Out-thought. Cleanly. Hm."
**Sage Nico [Post]:** "You felt the other half just now. Carry it up the stairs."

**Sage Edmond [Pre]:** "Reflect, Screen, a little sleep. The tower bends, young one.
Can you?"
**Sage Edmond [Loss]:** "I bent too far this time. You did not."
**Sage Edmond [Post]:** "You bent. You did not break. That is the whole art."

**Sage Jin [Pre]:** "Hypnosis first. Everything else, after. Show me you can fight
through the quiet."
**Sage Jin [Loss]:** "Through the quiet, and through me. Well done."
**Sage Jin [Post]:** "Awake again, and wiser. Onward."

**Sage Neal [Pre]:** "Talent without discipline is Ren. Discipline without talent
is dull. Show me both."
**Sage Neal [Loss]:** "...So it is both. I was hoping it wouldn't be."
**Sage Neal [Post]:** "Both. Hm. The Elder will want to see you."

**Sage Troy [Pre]:** "The last sage before the Elder. Steady hands, now."
**Sage Troy [Loss]:** "Steady to the very last. Yours, not mine."
**Sage Troy [Post]:** "Steady indeed. He is waiting at the top. So is your friend's
accomplice."

### 2.4c · Ren & Kestra mid-tower (failing to look innocent)

*Found on 1F/2F "casually" standing near misplaced tags.*

**Kestra:** "We are *helping*. We found three of the tags Ren hid. Totally helping.
Why is that sage looking at us like that."
**Ren:** "Because that sage has watched generations of children pretend to help.
We are not the first. We are merely the loudest." *(hands over the tags)* "Here.
Put these back where the symbols match. If I apologize in alphabetical order, do
you think they'll know I mean it? ...No. Yeah. Bad idea. Forget I said it."

### 2.4d · Elder Li (top floor)

**Elder Li:** "Ah. The one battling their way up while the other two rearrange my
tower like it is a dollhouse." *(dry)* "The tower bends. It does not panic. Today it
panicked — and I find I am less angry at the boy than at how *easily* it was done."

**Elder Li:** "I will not reopen these doors for an apology. Apologies are cheap and
the boy's would be counterfeit anyway." *(looks at the player)* "I reopen them
because of *how you climbed*. You fought my sages with patience. You respected what
this place teaches. That is the apology that counts."

**Elder Li (to Ren):** "A trainer who cannot wait will eventually be taught by
paralysis. Talent buys you time, boy. It does not buy you a single thing worth
keeping." *(Ren opens his mouth, closes it.)*

**Elder Li:** "Take this. The tower's old light, for the dark places the young
insist on entering." *(gives TM70 Flash)* "Now go. Return what was misplaced, and
the next time you climb my tower, do it with steadier hands."

### 2.4e · Ren's thanks (campus)

**Ren:** "So. You smoothed it over. With *monks*. I didn't think that was a thing a
person could do." *(deflecting, then genuine)* "Here — practical stuff, for the
road. Berries. They'll patch a status when you're out of fancier options." *(gives
Oran Berry ×3)*

**Ren:** "You're not boring. That's rare around here, you have no idea." *(half a
grin)* "Go win your gym. I'll be off finding the next thing I shouldn't do. Maybe
I'll even do it *quietly* this time. ...No. Probably not."

---

## 2.5 · Roxanne Practicum — The Pseudo-Gym

**Intent:** a gym in miniature; the lesson is adaptability, not type-mastery; not a
badge. **End state:** **TM39 Rock Tomb**; Roxanne's endorsement that the player is
ready for a real gym.

*Held in the old gym building (Falkner's former arena, now the practice hall). Earl
opens it after the tower.*

**Roxanne [intro]:** "I'm Roxanne. I led a gym in Hoenn once; now I teach, which
was always the part I loved. This is a practicum, not a badge match — but I'd like
you to treat it as though everything were on the line. That's how you learn what
'on the line' even feels like."

**Roxanne [intro, cont.]:** "Two of my students first, then me. A gym battle is not
a test of whether you know one answer. It is a test of whether you can keep
*thinking* after your first answer fails. Let's find out if you can."

*(Practicum students — repurposed Bird Keeper slots in `T22GYM0101`.)*

**Student A (`TRAINER_BIRD_KEEPER_GS_ABE`) [Pre]:** "Rock and a little Grass to
cover it. Bring more than one idea."
**Student A [Loss]:** "Down already? Those reflexes..."
**Student A [Post]:** "You switched the *moment* my Geodude came in. That's the
reflex she's trying to drill into us."

**Student B (`TRAINER_BIRD_KEEPER_GS_ROD`) [Pre]:** "I run status and a sturdy
back line. Patience beats power more than you'd think."
**Student B [Loss]:** "Out-waited at my own game. Ugh."
**Student B [Post]:** "You out-patienced me. Roxanne's going to *love* that. Go on
up."

**Roxanne (`TRAINER_LEADER_FALKNER_FALKNER` slot) [Pre]:** "Now me. Rock Pokemon
are honest teachers — they punish carelessness immediately and forgive nothing.
Lead well. Switch when you must. Show me the thinking, not just the winning."

**Roxanne [mid-battle, on a good switch]:** "There. *That's* the answer changing
when the question did."
**Roxanne [Loss]:** "...And you kept thinking right to the end."

**Roxanne [Post]:** "You adjusted. That matters more than winning quickly — winning
quickly is mostly luck wearing a confident face." *(offers TM39)* "Rock Tomb.
Damage *and* control — it slows them so your plan has time to work. Fitting, I
think." *(gives TM39 Rock Tomb)*

**Roxanne [Post, cont.]:** "I came up through Hoenn gyms, so take this from someone
who's stood on the leader's side of the field: you're ready for a real one. Azalea
gives the first badge. Go and earn it." *(her Hoenn line is the quiet seed for when
the player reaches that region.)*

---

## 2.6 · First Kestra Rival Battle

**Intent:** the first rival fight — warm, competitive, a milestone. **End state:**
rival battle clear; Kestra heads south toward Azalea.

*Outside the university, after the practicum.*

**Kestra:** "I did Roxanne's thing while you were busy being a tower diplomat.
Passed, obviously." *(plants her feet)* "Which means it's time. You and me. First
official battle. No wild Pokemon, no rescue panic, no Gold hovering with a lecture
face. Just us."

**Kestra [Pre]:** "I grabbed {KESTRA_MON} back in Cherrygrove *specifically*
because it beats {STARTER}. I've been waiting this whole route to prove that was
smart. Don't you *dare* go easy."

**Kestra [Loss]:** "Type advantage and *everything*..." *(grinning even as she
says it)*

**Kestra [Post]:** "Okay. OKAY. You're better than me today. *Today.*" *(laughs)*
"That's the most fun I've had since we met, and I've been a trainer for like a
week. How is this our *life* now?"

**Kestra:** "I'm going ahead to Azalea — advance research, very serious, absolutely
not a head start." *(already backing away)* "Route 32 south, then Union Cave —
bring a light and some Potions, it's a real one. There's an old fishing guru on the
route who'll set you up. See you at the gym, hero. Don't keep me waiting!"

---

## 2.7 · Ruins of Alph (Optional)

**Intent:** wonder, a puzzle, and the **first Silph seed** — polite, competent,
slightly too interested. Entirely skippable. **End state:** Ether; the seed planted
for players who explore.

**Researcher at the entrance:** "The Ruins of Alph. Older than Johto, older than
anything that kept records. The Unown here aren't quite Pokemon and aren't quite
*writing* — they're both, somehow. We've barely scratched it."

**Psychic Nathan (`TRAINER_PSYCHIC_M_NATHAN`) [Pre]:** "I study the Unown's
resonance — and resonance is a kind of strength. Mind against mind, then. Begin."
**Psychic Nathan [Post]:** "Hm. Steady focus. The Unown like you; they've gone
quiet and watchful. They do that around people worth watching."

### 2.7a · The Silph field team (non-battle — the seed)

*Two researchers in clean field gear, perfectly polite. They never threaten, never
mention anything ominous. Silph branding on their equipment cases.*

**Silph researcher 1:** "Silph sponsors the preservation equipment here. The ruins
are delicate, and the right instruments keep them that way. We're guests, same as
you — just better funded." *(smiles)*

**Silph researcher 2:** "Unown react strongly to pattern, to sound, to
expectation. That third one isn't in our official report, naturally — too hard to
quantify a *feeling*." *(makes a note)* "Fascinating place. We keep finding reasons
to extend the survey."

**Silph researcher 1:** "If your Pokedex happens to record anything unusual down
here, the university would appreciate a copy. So would we. No obligation, of
course." *(entirely reasonable; the player has no reason to think twice — that's
the point.)*

**Unown wall (examine):** "The carvings shift at the edge of sight. Stare too long
and you start reading meaning into them. Ether sits in a cracked alcove, forgotten
by everyone but the dust." *(gives Ether)*

---

## 2.8 · Route 32 · Union Cave · Route 33

**Intent:** the first long road away from a hub; the Old Rod; the first real
dungeon; a rainy arrival. **End state:** player reaches the Azalea outskirts (hands
to [CHAPTER3_SCENES_SPEC.md](CHAPTER3_SCENES_SPEC.md)).

### 2.8a · Route 32 — the road stretches

*Eight placed trainers (`033_R32.json`) — the longest trainer gauntlet yet, fitting
the "the road actually stretches now" beat. All scripted 1:1.*

**Fishing guru:** "You've got the look of someone who's never felt a bite. Here —
an Old Rod. Cast it anywhere there's calm water." *(gives Old Rod)* "Won't pull up
monsters. Pulls up *possibility*. A team's not finished till the water's had its
say."

**Youngster Albert (`TRAINER_YOUNGSTER_ALBERT`) [Pre]:** "First trainer past
Violet! That makes me the gatekeeper. Unofficially. Self-appointed."
**Youngster Albert [Loss]:** "Worst gatekeeper ever."
**Youngster Albert [Post]:** "Fine, you may pass. Like you needed my permission."

**Youngster Gordon (`TRAINER_YOUNGSTER_GORDON`) [Pre]:** "I caught everything on my
team right here on Route 32. Home-field advantage!"
**Youngster Gordon [Loss]:** "Home field didn't help."
**Youngster Gordon [Post]:** "Guess knowing the route isn't the same as being good
on it. Noted."

**Camper Roland (`TRAINER_CAMPER_ROLAND`) [Pre]:** "Been camped on this route three
days. You learn a route's rhythm if you sit still long enough. Let's see if you
learned yours."
**Camper Roland [Loss]:** "Out-rhythmed. Hmph."
**Camper Roland [Post]:** "Tip from the tent: there's calm water south for the rod,
and the cave past that bites harder than I do. Rest before Union."

**Picnicker Liz (`TRAINER_PICNICKER_LIZ`) [Pre]:** "I packed lunch *and* a winning
team. One of those is going great so far!"
**Picnicker Liz [Loss]:** "...It was the lunch. The lunch was the good one."
**Picnicker Liz [Post]:** "Take a berry for the road. You earned it, and I have far
too many."

**Bird Keeper Peter (`TRAINER_BIRD_KEEPER_GS_PETER`) [Pre]:** "My birds rule the sky
over this route. The ground's all yours — for now. Look up!"
**Bird Keeper Peter [Loss]:** "Grounded. All of them. Ugh."
**Bird Keeper Peter [Post]:** "Falkner trained near here once, you know — before he
left for Fortree. Big shoes. Half of us are still trying to fill them."  *(quiet
nod to the Falkner-moved-on continuity.)*

**Fisherman Ralph (`TRAINER_FISHERMAN_RALPH`) [Pre]:** "Patience is the angler's
whole art. I'll out-wait you. Watch."
**Fisherman Ralph [Loss]:** "Out-waited. By a kid. The shame."
**Fisherman Ralph [Post]:** "There's better waiting than this. The water's full off
the south bank. Go feel a bite for yourself."

**Fisherman Justin (`TRAINER_FISHERMAN_JUSTIN`) [Pre]:** "Hooked a Magikarp this
big this morning. Threw it back. Then it evolved for someone else. Don't be like
me — battle!"
**Fisherman Justin [Loss]:** "Threw the match back too, apparently."
**Fisherman Justin [Post]:** "Ah, you've got the touch. Some people just do."

**Fisherman Henry (`TRAINER_FISHERMAN_HENRY`) [Pre]:** "Last line on the route. Wade
through me if you can, then the cave's all that's left between you and Azalea."
**Fisherman Henry [Loss]:** "Reeled in and tossed out. Go on, then."
**Fisherman Henry [Post]:** "Union Cave next. Dark, damp, and longer than it looks.
Top off your Potions in Violet if you didn't. Safe travels, trainer."

### 2.8b · Union Cave — the first dungeon

*Damp amber stone, small pools. The first real resource-management dungeon. All
**12** placed trainers (`D25` floors) scripted 1:1 — Hikers, Firebreathers, Poké
Maniacs, and the tougher Ace Trainers deeper down.*

**Hiker Daniel (`TRAINER_HIKER_DANIEL`) [Pre]:** "Down here it's just you, your
team, and how many Potions you packed. Hope you packed enough."
**Hiker Daniel [Loss]:** "Out-packed and out-fought. Fair."
**Hiker Daniel [Post]:** "Ha! Prepared *and* tough. You'll do fine deeper in."

**Hiker Russel (`TRAINER_HIKER_RUSSEL`) [Pre]:** "Rock and Ground all the way down.
Heavy and patient. That's cave life."
**Hiker Russel [Loss]:** "Heavy's no good if it's slow, I guess."
**Hiker Russel [Post]:** "You didn't waste a single turn. That's how you survive a
cave."

**Hiker Leonard (`TRAINER_HIKER_LEONARD`) [Pre]:** "My Onix has been through this
cave a hundred times. It knows every echo. Do you?"
**Hiker Leonard [Loss]:** "A hundred times and *today's* the loss. Typical."
**Hiker Leonard [Post]:** "Mind the fork ahead — left's a dead end, right's the way
through. Saved you a headache. Go on."

**Hiker Phillip (`TRAINER_HIKER_PHILLIP`) [Pre]:** "I haul rocks up mountains for
fun. You think a battle's going to tire me out?"
**Hiker Phillip [Loss]:** "...Okay. That tired me out."
**Hiker Phillip [Post]:** "Strong team. Light on your feet, too. Rare combo down
here in the dark."

**Firebreather Bill (`TRAINER_FIREBREATHER_BILL`) [Pre]:** "It gets cold down here.
Let me warm it up for you!"
**Firebreather Bill [Loss]:** "Snuffed out. Brr."
**Firebreather Bill [Post]:** "Phew. Put me right out. Get some rest before you push
on."

**Firebreather Ray (`TRAINER_FIREBREATHER_RAY`) [Pre]:** "No sunlight, so I bring my
own heat. Mind the sparks!"
**Firebreather Ray [Loss]:** "Out of fuel. Out of luck."
**Firebreather Ray [Post]:** "The exit's still a ways yet. Don't burn through your
items the way I burned through mine."

**Poké Maniac Larry (`TRAINER_POKE_MANIAC_LARRY`) [Pre]:** "I came down here for the
rare ones and I'm not leaving till I battle everyone I meet. You're up!"
**Poké Maniac Larry [Loss]:** "Aw, beaten by a tourist!"
**Poké Maniac Larry [Post]:** "Worth it! Tell folks topside Larry's still down here
living the dream."

**Poké Maniac Andrew (`TRAINER_POKE_MANIAC_ANDREW`) [Pre]:** "Do you have any idea
how rare an Onix is when you *love* Onix? I have three. THREE."
**Poké Maniac Andrew [Loss]:** "All three! Beaten! The audacity!"
**Poké Maniac Andrew [Post]:** "You don't even collect, do you. You just *win*. Must
be nice."

**Poké Maniac Calvin (`TRAINER_POKE_MANIAC_CALVIN`) [Pre]:** "Everyone underrates
cave Pokemon. I'm going to change your mind right now."
**Poké Maniac Calvin [Loss]:** "Mind unchanged. Dang."
**Poké Maniac Calvin [Post]:** "Okay, you respect them at least. That's something.
That's most of it, actually."

**Ace Trainer Gwen (`TRAINER_ACE_TRAINER_F_GWEN`) [Pre]:** "Most people rush Union
Cave. I linger — it's the best training in the region if you respect it. Show me
respect."
**Ace Trainer Gwen [Loss]:** "...Respect earned. Both ways."
**Ace Trainer Gwen [Post]:** "Sharp. You read the cave instead of fighting it. Few
do. There's a lower chamber sealed off down there — come back when you're stronger.
It's worth the wait."  *(deeper-floor "return later" tease.)*

**Ace Trainer Emma (`TRAINER_ACE_TRAINER_F_EMMA`) [Pre]:** "I train where it's hard,
so the easy days feel like a gift. Today won't be a gift for you. Come on."
**Ace Trainer Emma [Loss]:** "...Or maybe today's *my* hard day. Good."
**Ace Trainer Emma [Post]:** "You don't flinch in the dark. That'll carry you a long
way past this cave. Hold onto it."

**Ace Trainer Nick (`TRAINER_ACE_TRAINER_M_NICK`) [Pre]:** "Last real fight before
the far exit. If you're going to fold before Azalea, fold now and save us both the
trip."
**Ace Trainer Nick [Loss]:** "Didn't fold. Not even a crease. Go."
**Ace Trainer Nick [Post]:** "Azalea's through the far mouth and down Route 33. Bring
your best to that gym — and to whatever else you find. Cave's quiet, but the world
isn't, lately."  *(faint forward-lean toward Chapter 3's tonal break.)*

### 2.8c · Route 33 — rain into Azalea

*One placed trainer (`034_R33.json`) — the rainy threshold before town.*

**Hiker Anthony (`TRAINER_HIKER_ANTHONY`) [Pre]:** "Last battle before Azalea, kid.
Rain and all. Let's see if a soggy road slows you down."
**Hiker Anthony [Loss]:** "Rain didn't slow you. Nothing does, looks like."
**Hiker Anthony [Post]:** "Town's just down the slope. ...It's been off down there
lately — Slowpoke acting strange, folks on edge. Probably nothing. Probably." *(the
last words before Chapter 3's tonal shift.)*

**Traveler under the gatehouse eave:** "Rain always starts right about here, like
the sky's marking the border. Azalea's just through the trees. Quiet town. Good
town." *(beat)* "...Been a strange few days down there, though, from what I hear.
You're headed in anyway? Mind yourself."

*(The path opens west into Azalea Town — Chapter 3 begins. See
[CHAPTER3_SCENES_SPEC.md](CHAPTER3_SCENES_SPEC.md) §3.0.)*

---

## Coverage checklist (for the implementation pass)

- [ ] 2.1 Route 30: Kestra opener one-shot, 3 named route kids (Joey/Mikey/Don),
  Apricorn man (+ Kurt/Wesley thread), Mr. Pokemon Quick Claw.
- [ ] 2.2 Route 31: Bug Catcher Wade, Dark Cave/Flash tease, gate attendant.
- [ ] 2.3 Violet: Earl tour one-shot, campus instructors, **3 library seeds**
  (Mel / corporate-scholars / Azalea) + inter-region flavor, Mart + Center.
- [ ] 2.4 Sprout Tower: commotion, Ren intro, 6 sages (Pre/Post), Ren+Kestra
  mid-tower, Elder Li + TM70 Flash, Ren thanks + Oran Berry ×3.
- [ ] 2.5 Practicum: Roxanne intro, 2 students, Roxanne (Pre/mid/Loss/Post),
  TM39 Rock Tomb + endorsement + Hoenn seed.
- [ ] 2.6 Kestra rival: challenge, starter-conditional Pre, Loss/Post, Azalea
  hand-off.
- [ ] 2.7 Ruins (optional): entrance researcher, Psychic Nathan, **Silph field
  team (non-battle seed)**, Unown lore + Ether.
- [ ] 2.8 Route 32 (8 trainers, all named), Old Rod guru; Union Cave (**all 12**
  trainers, Pre/Loss/Post) + deeper-floor tease; Route 33 (Hiker Anthony) + rainy
  Azalea hand-off.

> **Trainer coverage (verified against `disasm` zone JSON):** every placed Chapter 2
> trainer is now scripted 1:1 — R30 (Joey, Mikey, Don), R31 (Wade), Sprout Tower (6
> sages + Elder Li), Violet practicum (Abe→Student A, Rod→Student B, Falkner→Roxanne),
> Ruins (Nathan), R32 (Albert, Gordon, Roland, Liz, Peter, Ralph, Justin, Henry),
> Union Cave (Daniel, Russel, Leonard, Phillip, Bill, Ray, Larry, Andrew, Calvin,
> Gwen, Emma, Nick), R33 (Anthony). No "fill in later" placeholders remain.

### Continuity hooks planted here, paid off later
- **Mel (Goldenrod interviewer)** — library radio seed → Chapter 4.
- **Silph / corporate scholars** — Violet professor + Ruins of Alph field team →
  the multi-region pattern Looker eventually connects.
- **Kurt / Apricorns** — Apricorn man's "tell Kurt Wesley sends his best" → Chapter
  3 (Azalea).
- **Roxanne's Hoenn past** — pays off when the player reaches Hoenn (Rustboro / Wes).
- **Union Cave lower chamber** — Ace Trainer's "come back stronger" → later return.
</content>
