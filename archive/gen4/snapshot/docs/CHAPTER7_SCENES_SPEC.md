# Chapter 7 — Scene Spec & Full Script (Route 6 · Vermilion · Route 11 · Diglett's Cave · Departure)

This is the **complete line-by-line dialogue** for Chapter 7, the single source of truth
for what every character says. It sits one altitude below
[CHAPTER7_BUILD.md](CHAPTER7_BUILD.md) (staging, flags, files) and pairs with
[KANTO_BATTLES.md](KANTO_BATTLES.md) (rosters) and [KANTO_ITEMS.md](KANTO_ITEMS.md).

**Status:** ⬜ not implemented — writing pass. Engine wiring (`.gmm` banks, `npc_msg`,
`scr_seq` hooks) happens at implementation; no message IDs assigned yet.

**Conventions:**
- `{PLAYER}` = player name token. No `{RIVAL}` this chapter (Kestra's in Goldenrod).
- Battle lines use **[Pre]** / **[Loss]** / **[Post]**. Route 6, Route 11, and the Lodge
  battles map to **real engine trainer slots** (verified from `011_R06.json`,
  `016_R11.json`, `322_T06GYM0101.json`); see [KANTO_BATTLES.md](KANTO_BATTLES.md).
- *Italic parentheticals* are staging cues, not spoken. House style: drive with dialogue,
  minimal narration ([[dialogue-over-narration]]).
- **Silver is warm and opaque.** Nothing he says is provably wrong. The menace is in the
  staging (the dismissed lab coats, the pointed Mel questions), not the words. **He does
  not battle.**
- **The associates are silent.** They never address the player. Half-seen, unexplained.

---

## 7.0 · Route 6 — South to the Coast

*The Saffron south gate — the Chapter 5 blocker — opens on the Requiem badge. Route 6
descends toward the sea; the port is visible on the horizon.*

**Route 6 sign:** "ROUTE 6 — Vermilion City, south. Kanto's gateway to the sea."

### 7.0a · The checkpoint guard (`R06R0201`)

*The badge-conditional gate from Ch5/Ch6. The guard's "closed" branch now falls through.*

**Guard** *(reading the badge case, then stepping aside):*
- "That's a Kanto League badge. Earned one, did you — the Lavender gym? Not many
  travelers manage that stranded. ...That's your credential. Vermilion's straight down the
  hill. Working port, so mind the cargo traffic. Go on through."
- *(if talked to again)* "Ships out of Vermilion go everywhere. If you're headed home —
  that's your best road now. If you're not..." *(shrug)* "...well. You've heard that one
  already, I bet."

### 7.0b · Route 6 sight-trainers (three battles)

*All vanilla `std_trainer` placements in `011_R06.json`. Rosters/levels in
[KANTO_BATTLES.md](KANTO_BATTLES.md).*

**Camper Virgil** — `TRAINER_CAMPER_VIRGIL`
- **[Pre]:** "Down to the coast, huh? Everybody's headed for the boats these days. Me, I
  like the walk down. Battle me before you hit all that noise."
- **[Loss]:** "Yeah, that tracks. You've got sea legs and you haven't even boarded yet."
- **[Post]:** "Vermilion's loud. Cranes, horns, the whole port going all day. You'll get
  used to it or you'll leave. Most people leave."

**Picnicker Selina** — `TRAINER_PICNICKER_SELINA`
- **[Pre]:** "I come down here for the view — you can see the ships from the ridge. Prettier
  from up here than down in all that diesel. One battle, then I'll let you at it."
- **[Loss]:** "Worth the trip up, then. For me, I mean. Not for you."
- **[Post]:** "If you're catching a boat, check the departures board at the port. They
  changed the whole schedule when the network expanded. Nobody can keep it straight."

**Twins Day & Dani** — `TRAINER_TWINS_DAY_AND_DANI` *(double battle)*
- **[Pre]** (Day): "We're allowed to go as far as the ridge!" (Dani): "And NO further, Mom
  said, because of the port traffic." (Day): "So we battle everyone who comes down. It's the
  rule. Our rule."
- **[Loss]** (Dani): "We lost." (Day): "We lost as a *team*, though." (Dani): "...That is
  worse, actually."
- **[Post]:** "Are you getting on a boat? Everybody who comes down here is getting on a
  boat. We're not allowed on boats. We're not allowed on anything."

---

## 7.1 · Vermilion City — The Port Town

*Route 6 opens onto Vermilion: cranes, cargo, warehouses, ships at berth. The sea is a
workplace. Residential streets spread north. Port-worker chatter everywhere.*

**Vermilion sign:** "VERMILION CITY — The Sea Routes Start Here. Gateway to the S.S.
Network: Slateport · Olivine · Driftveil."

### 7.1a · Port-town residents (ambient)

**Customs officer** *(near the pier, buried in paper):*
- "Three ships in this morning, two more before dark, and every one of them is a stack of
  manifests I have to read. You want to move Pokémon across a border now, there's a *form*.
  There's always a form. ...You're not carrying anything undeclared, are you? No — of course
  not. Move along. I've got a form."

**Dock supervisor's spouse** *(a residential street):*
- "My husband supervises the night unloading. Twelve, fourteen hours some days. The port
  tripled its throughput in five years and they hired what, a dozen people? He comes home
  and he can't hear right for an hour, all those horns. But it's steady work. It's the only
  work down here now."

**Retired sailor** *(a bench, looking at the water):*
- "I sailed out of this port when it was a *dock and a half* and one crane that broke every
  winter. Now look at it. Ships from four regions, cargo stacked three stories, kids who've
  never rowed a boat running the whole thing off a screen. ...It's better. I know it's
  better. I just don't recognize it. That's allowed, at my age."

**Shipping clerk** *(near the departures board):*
- "Slateport, Olivine, Driftveil — that's the loop. Passenger berths and cargo on the same
  hulls now, which the old sailors *hate*, but it's cheaper, so. You need a ticket for any
  of them, and tickets are..." *(waves vaguely)* "...complicated. Home-region rules, League
  permits, who you know. Mostly who you know."

**Kid on the waterfront** *(pointing at a ship):*
- "That one came from HOENN. It's got a palm tree painted on it. Someday I'm getting on a
  ship with a palm tree and I'm never coming back. My mom says I have to finish school
  first. School doesn't have palm trees."

### 7.1b · The Fishing Dude House (`361_T06R0101`, kept)

**Fishing enthusiast** *(rods on every wall):*
- "You fish? You should fish. This whole coast, and Route 11 out east, and there's water in
  places you wouldn't think. ...Here — take this, a proper rod. The port kids never use the
  water anymore, they just watch the boats. Somebody ought to."
- *(gives a rod — see [KANTO_ITEMS.md](KANTO_ITEMS.md); if already held)* "Then go *use*
  the one you've got. The Magikarp aren't going to hook themselves. Well. They basically
  are. But still."

---

## 7.2 · The Trainers' Lodge (old Vermilion Gym)

*Surge's Electric gym, converted to a hostel for trainers arriving by ship. Metal bones,
softened with bunks and a common room. A bulletin board of travel tips and open
challenges. Everyone here is coming or going.*

### 7.2a · The bulletin board (read-only)

**Travel-tips board:**
- "SLATEPORT — market's a zoo, museum's worth it, don't buy the 'rare' dolls."
- "OLIVINE — see the lighthouse. Then leave. There is the lighthouse and there is nothing
  else and both are correct."
- "DRIFTVEIL — cold. Bring layers. Ask for Clay if you want dock work, don't if you don't."
- "RE: the old Gym — Lt. Surge relocated to Mauville (Hoenn), 'consulting on the power
  grid.' No, he is not coming back. No, you cannot challenge him here. Yes, people keep
  asking."

### 7.2b · Lodge travelers (three battles + flavor)

*The gym's 3 vanilla trainer slots, re-lined as cosmopolitan travelers. Rosters (Kanto-base
with a level-capped import each) in [KANTO_BATTLES.md](KANTO_BATTLES.md).*

**Sailor (off the Slateport run)** — `TRAINER_GUITARIST_VINCENT`
- **[Pre]:** "Just off the Slateport run. You want weather? Hoenn's got *weather.* Rains
  sideways, then it cooks you, then it rains up out of the ground somehow. I loved it. Give
  me a battle before I ship back."
- **[Loss]:** "Hah! Sea legs and a right hook. You'd do fine over there. They'd eat you
  alive, but you'd do *fine.*"
- **[Post]:** "You headed south? Slateport's the first stop and it does not ease you in. Big,
  loud, hot, everybody selling everybody something. After Vermilion it'll feel like a fever.
  A fun one."

**Backpacker (from Olivine)** — `TRAINER_JUGGLER_HORTON`
- **[Pre]:** "Came in on the Olivine boat. Walked the whole Johto coast before that. My legs
  have opinions now; they'd like a rest, but they'll settle for a battle."
- **[Loss]:** "...Fair. Fair. I've been sitting on ships too long. You've been *walking.* It
  shows."
- **[Post]:** "Olivine's got the lighthouse — Jasmine keeps it, if she's still there. Worth
  the climb. The town's quiet as a held breath, but that lighthouse... it's the kind of thing
  you carry after. Go see it someday."

**Gentleman (well-traveled)** — `TRAINER_GENTLEMAN_GREGORY`
- **[Pre]:** "A young trainer in a Lodge full of sailors, with a Johto look and a Kanto
  badge. You've come an interesting distance. I collect interesting distances. Indulge me."
- **[Loss]:** "Marvelous. You've the manner of someone the road hasn't finished with. Good.
  It's the finished ones who bore me."
- **[Post]:** "A word, since you're clearly *going* somewhere: the people who move easily
  between regions now — ships, rail, permits — they are not all the pleasant sort. The world
  got small. Not everyone who profits from that is kind about it. ...Off you go. Mind the
  cargo."

---

## 7.3 · The Exchange & The Museum

### 7.3a · The International Pokémon Exchange (`362_T06R0301`, old Fan Club)

*The former Pokémon Fan Club, now an inter-regional trade & showcase hall — the connected
world in one room. The Chairman is absent (he's in Celadon — Ch6).*

**Exchange host** *(at the desk):*
- "Welcome to the International Exchange! Used to be the Fan Club — same building, bigger
  idea. Trainers from every region, trading, showing off, comparing. You'd be amazed what
  turns up. A Sinnoh kid traded a Hoenn tourist something neither of them can pronounce
  yesterday. It was beautiful."
- *(if asked about the Chairman)* "Oh, he's off in *Celadon.* Went for the food, he said. Two
  weeks ago. Sends postcards. All about his Rapidash. We miss him. A little. A very
  manageable amount."

**Hoenn trader** *(showing off):*
- "Back home everybody's got one of these — but out here? Exotic! That's the whole game.
  Your common is my treasure, my common is yours. The ships made it possible. Ten years ago
  I'd never have met a Johto trainer in my life, and now — hi. Want to trade?"

**Sinnoh showcase kid:**
- "I'm not trading, I'm just *showing.* There's a difference. Back in Sinnoh nobody's
  impressed by my team. Here everybody's impressed. I take the boat over just to feel
  impressive for a weekend. Don't judge me. You'd do it too."

### 7.3b · The Maritime History Museum (`363_T06R0401`, a repurposed house)

*The building "under construction forever" — finished. The old man who dreamed it has
passed; his Machamp completed it alone and now keeps it.*

**Door placard:**
- "THE VERMILION MARITIME HISTORY MUSEUM. Founded by [name], master seaman, retired. He
  said he'd finish it. He did."

**The Machamp** *(the caretaker):*
- *(no words — it looks up from straightening a display case, gives the player a slow,
  solemn nod, and returns to its work. If the player lingers, it gestures — four hands, one
  motion — toward the collection, as if to say: look, then. That's what it's for.)*

**Museum displays (read-only):**
- "A captain's log, Sevii Islands expedition. Water-stained. The last entry is a grocery
  list. He made it home."
- "Figurehead, Orange Islands trading vessel. Carved as a Lapras. The ship is gone; the
  Lapras kept swimming, in a manner of speaking."
- "Navigation instruments, pre-network era. Before the screens and the permits, men found
  Olivine from Vermilion with *this* and a steady nerve. Mostly the nerve."
- *(a small placard by the door, newer than the rest)* "The founder passed before the
  doors opened. His partner finished the work. It does not require a name to be faithful."

---

## 7.4 · Route 11 — East to the Cave

*East from Vermilion: rocky outcrops, coastal scrub, tall grass. Shore-leave sailors,
drifting gamblers, hikers bound for the cave. A lookout near the cave mouth shows the port
and the open sea.*

**Route 11 sign:** "ROUTE 11 — Diglett's Cave, east. (Route 2 / Pewter beyond — CLOSED,
see notice.)"

### 7.4a · Route 11 sight-trainers (four battles + the fisherman)

*All vanilla `std_trainer` placements in `016_R11.json`. Rosters/levels in
[KANTO_BATTLES.md](KANTO_BATTLES.md).*

**Sailor on shore leave** — `TRAINER_PSYCHIC_M_FIDEL`
- **[Pre]:** "Shore leave. Two days on solid ground and I already miss the roll of the deck.
  You battle to stay sharp on land, or you go soft. Come on, then. Keep me honest."
- **[Loss]:** "Sharp enough. Good. I'll tell them at the docks a land-legs kid took me. They
  won't believe it. I'll tell them anyway."
- **[Post]:** "That cave ahead — Diglett's — it's a maze and it's dark and it comes out the
  wrong side of the region. Pewter way. Which is shut. So it's a maze that goes nowhere
  right now. Grab what's in it and come back. That's my advice. Free."

**Hiker** — `TRAINER_PSYCHIC_M_HERMAN`
- **[Pre]:** "Heading into the cave. I do the cave every week — good ground-type stock in
  there, and the quiet suits me after all that port noise. Battle first? I insist. Politely."
- **[Loss]:** "Ha — you've got the legs for the cave, then. Watch the drops. The Diglett pop
  up where the floor gives. Startles you every time. Every *single* time."
- **[Post]:** "Far end's blocked, mind. Route 2's shut for works, or that's the notice.
  Been 'works' a while. Pewter doesn't want visitors this season. You didn't hear it from
  me."

**Youngster (gambler kid, drifted from Celadon)** — `TRAINER_YOUNGSTER_OWEN`
- **[Pre]:** "I was up big at the Celadon slots and then I wasn't, so now I'm out here
  'clearing my head,' which is what you say when you're broke. Battle me. Winner feels
  better about themselves."
- **[Loss]:** "Of course. OF COURSE. The slots, and now this. The universe has a *note* out
  on me."
- **[Post]:** "I'm gonna hit the port, work a cargo shift, win it back on the next Celadon
  trip. It's a *system.* ...It's not a system. I know it's not a system. Leave me alone."

**Youngster (kid brother, tagging along)** — `TRAINER_YOUNGSTER_JASON`
- **[Pre]:** "My brother said I could come out here if I stayed where he could see me. He
  can't see me. Battle me before he notices!"
- **[Loss]:** "Aw. Okay. Don't tell him you beat me, he'll say I told you so, he ALWAYS says
  I told you so—"
- **[Post]:** "He lost too, y'know. To you. So we're the same. We're a matched set of guys
  who lost. That's kind of nice actually."

**The fisherman** *(coastal edge — a small placed trainer)* — recast a Route 11 slot / build-added
- **[Pre]:** "Been fishing this stretch since before the port ate the whole coastline.
  Still bites out here, past the noise. You want a battle? I've got time. Fish have got
  nothing but time, and I've been matching them for years."
- **[Loss]:** "Heh. Patient hands. That's a fisher's gift and a battler's, turns out. Same
  gift."
- **[Post]:** "Cave's just up. Dark as a closed eye and it doesn't come out where you'd
  hope — Pewter side, and Pewter's shut. But there's things worth having in the dark, if you
  go slow. Always are. Go slow."

### 7.4b · The lookout point (read-only vista)

**Lookout marker:**
- *(the player faces the sea: Vermilion's cranes to the west, ships small at their berths,
  the S.S. departures churning the water; open ocean to the south, no far shore.)*
- "You can see the whole port from here. And past it, the water — no other side to it, not
  from here. Everything that leaves Vermilion leaves *that* way. Including, soon enough,
  you."

### 7.4c · The Snorlax (branch-block)

*The sleeping Snorlax (`FLAG_HIDE_ROUTE_11_SNORLAX`) blocks the Route 11 branch that would
lead deeper into Kanto by land.*

**Hiker by the Snorlax** *(if talked to):*
- "That thing's been asleep so long the route grew *around* it. There used to be a flute
  on the radio that'd wake one up — some old promotion. They cancelled it. Now it's just...
  furniture. Big, breathing furniture. Road doesn't go past it anymore. Nobody minds. The
  boat's the way now, anyway."

*(Interacting with the Snorlax itself:)*
- "Snorlax is fast asleep. It doesn't stir. Whatever used to wake these — it's long gone
  off the air. The way past is closed by a very large nap."

---

## 7.5 · Diglett's Cave — Items, the Fossil, the Wall

*A deep, dark tunnel of tumbling Ground-types. No trainers — a change of pace. The one real
treasure is here, and so is the westernmost wall of the chapter.*

### 7.5a · Cave ambience

**Cave-mouth NPC (a spelunker, `gsmiddleman1`):**
- "Careful in there. It splits and doubles and the Diglett come up right under your feet.
  Most of it loops back. The one straight path... goes to Pewter. Or it would, if Pewter
  were open. It's not. So the cave's a treasure box with a locked back door. Take the
  treasure. Leave by the front."

### 7.5b · The fossil (the promissory reward)

*A single fossil embedded deep in the rock — the **Claw Fossil** (Anorith → Armaldo, a
Hoenn revive). See [KANTO_ITEMS.md](KANTO_ITEMS.md). One-shot, `FLAG_APOC_CH7_FOSSIL_TAKEN`.*

- *(on inspecting the deep rock face)* "There's something *in* the stone here — not a rock.
  Older than a rock. Claws, or something like them, pressed flat into the stone. You work it
  loose."
- *"{PLAYER} obtained the Claw Fossil!"*
- *(examining it in the bag)* "Whatever it was, it swam. These weren't made for walking —
  they were made for *water.* And this deep in the rock, this far from the shore... the sea
  was *here*, once. A long time ago. Before it went where it went."
- *(the spelunker, if shown the fossil)* "Ohh, that's an old one. Older than Kanto, my
  cousin the digger would say — she works the Hoenn coast, finds the grown-up version of
  *that* in the sea cliffs out there. Same critter, basically. Lived here, ended up there.
  Everything migrates eventually. Even the dead things. *Especially* the dead things."
- *(examining it again / a placard by the dig site)* "You'd need a lab to bring it back —
  the kind they keep at the **Pewter Museum.** ...Which is exactly the way you can't go
  right now. So: a promise, in your pocket. For later. Funny — the thing in your bag already
  made the trip you're about to make. Kanto to Hoenn. It just took a few million years."

### 7.5c · The Pewter (Route 2) soft-wall

*The far exit toward Route 2 / Pewter is blocked. Framing: a League/works notice + a
worker.*

**Route 2-side worker (at the blocked exit):**
- "Sorry — no through traffic to Route 2. Pewter's got the whole approach closed. 'Tunnel
  maintenance,' the notice says." *(lowers voice)* "Been 'maintenance' a good while, if you
  ask me, which you didn't. Point is you're not getting to Pewter this way, or any way, this
  season. Head on back to Vermilion. The sea's the road that's open."

**Posted notice (read-only):**
- "ROUTE 2 / PEWTER APPROACH — CLOSED FOR TUNNEL MAINTENANCE. No through traffic. By order
  of the Kanto League Works Authority. We apologize for the inconvenience." *(Someone has
  written under it in pen: "since WHEN. it's been months.")*

---

## 7.6 · Silver at the Port — The Ticket

*The player returns to Vermilion and goes to the S.S. Aqua port to weigh their options.
The departures board lists Slateport, Olivine, Driftveil. Silver is there — the Champion —
finishing a low conversation with three lab-coated figures and an executive.*

### 7.6a · The associates (silent)

*As the player enters, Silver glances up, sees them, and — without a word to the player —
makes a small gesture. The three lab coats and the executive turn and walk off toward the
cargo side. They do not look at the player. They do not speak. Set
`FLAG_APOC_CH7_LAB_COATS_GONE`.*

- *(no dialogue. A dockworker nearby, if talked to afterward:)* "Those the Champion's
  people? Suits and lab coats, down here? Huh. Figured he traveled alone. ...Guess even
  Champions have a staff. Fancy staff. Didn't say a word, any of 'em."

### 7.6b · Silver

*He turns to the player. Warm. Easy. Genuinely pleased. Nothing about him reads as
threat — that's the point.* **He does not battle.**

**Silver:**
- "There you are. I was hoping the timing would work out." *(a real smile)* "You don't
  remember me being this friendly, do you? People change. Some of us for the better."
- "Look at you. Two badges. In a region that isn't yours, off the train with nothing, not a
  soul in your corner — and you went and *earned* your way through. Lavender, no less. Eve
  doesn't hand those out." *(a beat)* "That's not luck. I know luck intimately. That's
  not it."

*(He lets the compliment land. Then, lighter — too light:)*

- "The reporter. The one who brought you over on the Magnet Train — Mel, isn't it?" *(easy,
  offhand)* "Chatty. Persistent. She's got a program out of Goldenrod, chases the kind of
  story that gets a person in trouble." *(a small pause)* "She still after whatever she was
  after? Did she... say much to you, before she ran off and left you here?"

*(However the player is prompted to respond — the game gives them nothing real to answer
with; the beat is that Silver is asking, not that the player knows.)*

- *(a warm, forgiving wave, dropping it)* "No — forget I asked. She just leaves an
  impression, that one. Occupational, I suppose. For both of us." *(and it is gone, folded
  away like it never happened.)*

*(Now the generosity. He reaches into his coat.)*

- "Here's what I actually came down to say. You're clearly not going home — not really, not
  yet. You've got the look of someone the road isn't done with. I had it. I still have it,
  most days." *(he produces a ticket)*
- "Go to **Hoenn.** I mean it. The gyms there will humble you and put you back together
  meaner. The region's worth the crossing all on its own. And the ship out of here goes
  straight to **Slateport** — first stop, and it does not ease you in." *(he presses the
  ticket into the player's hand before they can refuse)*
- "Don't argue. It's a spare — the League keeps a few boarding passes for promising kids,
  and you're the most promising thing I've seen come through this port in a year. Consider
  it a Champion betting on you. I don't lose those bets." *(the smile again)* "I really
  don't."

*"{PLAYER} received the S.S. Ticket!"*

*(He steps past the player, toward the dock, then half-turns — as if remembering something
small.)*

- "Oh — and {PLAYER}? Whatever you think you saw at that Well." *(a beat; perfectly kind)*
  "It's being handled. It always is. Go see Hoenn. Let the grown-ups clean up the boring
  parts." *(and he's gone, easy as weather, leaving the player holding a ticket to a place
  they never planned to go.)*

### 7.6c · The departures board (post-Silver, read-only)

**S.S. Departures:**
- "SLATEPORT (Hoenn) — boarding. ✔ ticketed"
- "OLIVINE (Johto) — boarding. [requires: home-region pass / permit]"
- "DRIFTVEIL (Unova) — scheduled. [freight priority — passenger berths limited]"
- *(a smaller line at the bottom)* "Magnet Rail transfers: see Saffron. Home-region
  passholders only." *(— the one road the player still can't take. `ITEM_PASS` never
  comes.)*

---

## 7.7 · Departure by Sea

*The player boards. The sequence is brief and cinematic — Vermilion is workmanlike, so the
departure is too; save the spectacle for Slateport.*

**Deckhand (at the gangway):**
- "Ticket? ...Slateport. Right this way. We're a cargo hull with passenger berths, so mind
  the crates and don't feed the Wingull — they follow us the whole crossing and they *never
  learn.* Welcome aboard. Cast off in five."

*(Boarding warp → departure cutscene. Set `FLAG_APOC_CH7_DONE`.)*

**Departure cutscene** *(minimal text; let the image carry it):*
- *(the gangway pulls up; the horn sounds; the water churns white)*
- *(Vermilion's cranes and containers slide backward and shrink — the port that ate a
  coastline, small now, then smaller)*
- *(open water. No far shore. The ship points south.)*
- *(a single line, if any:)* "Kanto slips away behind the wake. Somewhere back on the dock,
  three figures in lab coats are already at work on whatever it was you almost saw. Ahead:
  Hoenn. Because the Champion said so. And it sounded like a great idea."

*(Fade. → **Chapter 8 — Slateport City.** The ship pulls into Slateport Harbor: heat,
noise, a market roaring to life. New region. New rules.)*

---

## Continuity & callbacks (build-check)

- **`ITEM_PASS` is still never granted.** The home-region Magnet Train pass remains
  unobtainable (Ch5 stranding). Silver gives `ITEM_S_S__TICKET` — a ship *away*, not a road
  home. The departures board reinforces it (rail = home-region passholders only). The
  one-way logic that stranded the player now *carries* them — same rule, new direction.
- **The Mel probe pays off later.** Silver's two-touch questioning about Mel is a planted
  seed (the corporate/conspiracy thread; DESIGN's Silph arc). Keep his lines *deniable* —
  he never accuses, never threatens; he asks and forgives. The unease is the player's, not
  the text's.
- **The lab coats = the Well/Silph coats.** Same visual as the Slowpoke Well detail (Ch3)
  and the Saffron HQ (Ch5). The player half-sees them dismissed. Never explained here.
- **Surge → Mauville** (DESIGN): the Lodge board + a line make it canon so a later Hoenn
  cameo (Mauville, with Wattson) can land.
- **The fossil → Pewter later.** The un-revivable fossil is a promissory hook: it needs the
  Pewter Museum lab, which is exactly this chapter's soft-wall. A concrete reason to bring
  the player back to Kanto's northwest in a later chapter.
- **Kestra:** not present (she's in Goldenrod, Ch4). No `{RIVAL}` lines this chapter.
