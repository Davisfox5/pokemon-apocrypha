# Chapter 8 — Scene Spec & Full Script (Slateport · Route 110 rescue · Oceanic Museum · Route 109 beach)

This is the **complete line-by-line dialogue** for Chapter 8, the single source of truth for
what every character says. It sits one altitude below [CHAPTER8_BUILD.md](CHAPTER8_BUILD.md)
(staging, flags, files) and pairs with [HOENN_BATTLES.md](HOENN_BATTLES.md) (rosters) and
[HOENN_ITEMS.md](HOENN_ITEMS.md).

**Status:** ⬜ not implemented — writing pass. Engine wiring happens at implementation; no
message IDs assigned yet.

**Conventions:**
- `{PLAYER}` = player name token. No `{RIVAL}` this chapter.
- Battle lines use **[Pre]** / **[Loss]** / **[Post]**. Battles map to **pokeemerald source
  trainer slots** (Gabby & Ty, Route 109/110, Seashore House), **rebuilt as HGSS trainers**
  and **re-tuned up** to the curve — see [HOENN_BATTLES.md](HOENN_BATTLES.md).
- *Italic parentheticals* are staging cues, not spoken. House style: drive with dialogue,
  minimal narration ([[dialogue-over-narration]]).
- **Cross-region:** every Hoenn map here is a **new HGSS build ported from pokeemerald** (see
  the BUILD doc's cross-region note). Dialogue is engine-agnostic.
- **The conspiracy is asleep this chapter.** This is a Pokémon adventure — light, warm, fun.
  Team Aqua stays hidden. Stern/Scott/Lisia plant seeds, gently.

---

## 8.0 · Arrival — Slateport Harbor

*The S.S. vessel from Vermilion docks. First steps in Hoenn: heat, noise, salt, an open sky.*

**Deckhand (at the gangway):**
- "Slateport! Everybody off who's getting off — that's you, kid. Mind the step, mind the
  gulls, mind everybody, honestly, it's a lot down there." *(a grin)* "Welcome to Hoenn. It's
  hot, it's loud, and it grows on you like barnacles. Go on."

**Dockworker (on the pier):**
- "Off the Vermilion boat? You've got that gray look about you still. Don't worry — Slateport'll
  cook it right out of you. Sun does most of the work around here. Rest of it's the noise."

*(The player is free in Slateport City.)*

---

## 8.1 · Slateport City — Hoenn's Personality

*Warm palette, low buildings, rooftop solar, an open sky. Ambient NPCs deliver the region's
lived-in environmental identity — never preachy.*

**Slateport City sign:** "SLATEPORT CITY — Where the land ends and the market begins.
Please recycle. (We mean it. We learned.)"

**Fisher (looking at the water):**
- "You're not from here. It's fine, most people aren't anymore. ...You know Pacifidlog? Little
  town, out on the swells. The water took the whole thing. One season. We used to build like
  the sea was a neighbor. Now we build like it's a landlord. You learn." *(a shrug, no drama)*
  "Anyway. Fish are biting. Life goes on. That's the other thing you learn."

**Rooftop-solar installer (on a ladder):**
- "Every roof in this city, eventually. Cheaper than the grid and the sun doesn't send a bill.
  Kanto thinks we're soft for it. Kanto's never watched a tide eat a post office. Hand me the
  bracket?"

**Kid (reciting):**
- "'The ocean gives and the ocean takes and it is our job to take LESS.' It's on the poster at
  school. I didn't wanna learn it but now it's just IN there. Forever. Thanks, poster."

**Market cook (proud):**
- "Whole stall runs off recovered heat from the fry line. Nothing wasted, everything twice-used.
  You want skewers? They taste better when they're smug. And these are VERY smug."

---

## 8.2 · The Market — The Hook

*Open-air stalls along the southern city. Vendors, food, color — and a few empty pitches.*

**Market regular (near the empty stalls):**
- "See those empty spots? Mauville crew. Come down every market day, rain or shine, been doing
  it for years — and today, nothing. No carts, no word. That's not like them. Somebody said
  there's trouble up on Route 110. Hope it's just a wheel off a cart. Hope."

**Berry vendor:**
- "Half my regulars buy from the Mauville stalls, not me, and you don't see ME complaining they
  didn't show. ...Okay, a little. A little complaining. Where ARE they, though? They never miss."

**Energy Guru (the held-item vendor):**
- "You look like a traveler who *invests* in her team. Good. I sell the good stuff — the powders,
  the herbs, the things that separate a trainer from a tourist. Browse. The prices are honest and
  the Pokémon leave happier." *(stock in [HOENN_ITEMS.md](HOENN_ITEMS.md))*

### 8.2a · Gabby & Ty — the interview

*Gabby, mic out, is haranguing a vendor while Ty frames the shot. She spots the player.*

**Gabby:**
- "—no, no, cut that, nobody wants forty seconds on cart axles, Ty, we need a FACE—" *(she
  sees the player)* "—oh. OH. Ty. Ty, look at this. Off the boat, are we? Little dusty, little
  road-worn, GREAT bone structure for TV. You're a trainer. You're a trainer, aren't you?"

**Ty:** *(not looking up from the camera)* "He's a trainer, Gabby."

**Gabby:**
- "He's a trainer! Then you know what I need. One battle. For the segment. Slateport's got a
  story today and I need B-roll of a real trainer doing real trainer things. You in? You're in.
  Ty, roll it."

**Ty:** "Rolling."

---

## 8.3 · The Filmed Battle — Gabby & Ty

*The double battle. `TRAINER_GABBY_AND_TY_1` (rebuilt/re-tuned up; roster in
[HOENN_BATTLES.md](HOENN_BATTLES.md)). Ty battles alongside Gabby but she does all the talking.*

**Gabby & Ty** — `TRAINER_GABBY_AND_TY_1` *(double battle)*
- **[Pre]** (Gabby): "Okay — big energy, big moves, give me something the six o'clock crowd
  will REMEMBER. Ty and I go together, that's the format, that's the brand. GO!" (Ty, quietly):
  "Try not to hit the camera."
- **[Loss]** (Gabby): "—AND HE TAKES IT! Did you get that?? Tell me you got that!" (Ty): "Got
  it." (Gabby): "We got it!!"
- **[Post]** (Gabby): "Okay, THAT'S television. That's a face people trust. Ty, we're keeping
  him. Kid — hang on. Don't wander off. I've got a bigger idea and it's a GREAT one."

### 8.3a · The recruitment

**Gabby:**
- "Here's the thing. That story I'm chasing — the Mauville vendors, no-shows, first time ever?
  I want to go FIND them. Route 110, north, see what the 'trouble' is. And I want a trainer with
  me, in case the trouble's got teeth. You just made yourself very hireable." *(a beat, a grin)*
  "It's good TV and you'd actually be helping people. Those two things almost never line up.
  When they do, you RUN at it. Come on. Ty, grab the kit."

**Ty:** "Kit's grabbed. It's always grabbed." *(to the player, low, as they set off)* "She's
  a lot. She's also usually right. Watch the road, not the camera."

*(The player, Gabby, and Ty head north. Set `FLAG_APOC_CH8_GABBY_TY_MET`.)*

---

## 8.4 · Route 110 — The Vendor Rescue

*The southern segment of Route 110: coastal path, the Seaside Cycling Road elevated overhead,
tall grass with Hoenn wilds. Beach/route trainers; then the cornered vendors.*

**Route 110 sign:** "ROUTE 110 — Mauville, north. Seaside Cycling Road above (bicycles only).
Watch for wild Pokémon in the grass."

### 8.4a · Route 110 sight-trainers (southern subset)

*pokeemerald source placements, rebuilt + re-tuned up; rosters in [HOENN_BATTLES.md](HOENN_BATTLES.md).*

**Youngster Timmy** — `TRAINER_TIMMY`
- **[Pre]:** "You came UP the route? Everyone's going DOWN today, all spooked about the Mauville
  guys. Not me. I'm going up. To battle. Which is you. Hi."
- **[Loss]:** "Aw, man. Okay, going down now. With everybody else. Don't tell 'em why."
- **[Post]:** "The trouble's further up. Big mean pack of somethings, blocking the whole path.
  I turned around. You've got a camera crew, though, so. Good luck with that."

**Triathlete (cyclist)** — `TRAINER_ANTHONY` *(recast Route 110 triathlete)*
- **[Pre]:** "I train on the coast road — well, BESIDE it, they won't let me up on the cycling
  road without the bike pass, bureaucrats. Sharpen me up. Quick one."
- **[Loss]:** "Clean. You've got a traveler's engine on you. Where'd you come in from?"
- **[Post]:** "Johto by boat? That's a real haul. You'll like Hoenn — it's flatter about who
  you are. Nobody here cares where you're from, only whether you can keep up."

**Psychic Edward** — `TRAINER_EDWARD`
- **[Pre]:** "The sea does something to the mind, this close. Openness. You feel it? No? You
  will. Let's see what your team feels."
- **[Loss]:** "Mm. Clear-headed. The road does that too, I suppose. Sharpens the noise into a
  point."
- **[Post]:** "The pack up ahead isn't malicious. It's frightened. Territory is just fear with
  a border. Be firm with it, not cruel. There's a difference and they can tell."

**Fisherman Dale** — `TRAINER_DALE`
- **[Pre]:** "Whole route's jammed up north, so I came down here to fish and mind my business.
  You're not minding your business, are you. Fine. Battle. Then I'm fishing."
- **[Loss]:** "Hah. Patient. You'd make a fisher. Go on, go be a hero, I'll be here catching
  dinner like a sensible person."
- **[Post]:** "Those vendors are good people. Bring 'em home. The market's not the same without
  the Mauville stalls, and I'm not just saying that 'cause they sell better bait than me. ...They
  do, though."

### 8.4b · The cornered vendors + the pack

*Partway up: the Mauville merchants, carts and hauler-Pokémon, backed against the rocks by a
territorial wild pack. `FLAG_APOC_CH8` scripted-wild battles — see [HOENN_BATTLES.md](HOENN_BATTLES.md).*

**Lead vendor (cornered):**
- "Oh thank goodness — a trainer! Don't — careful, they've had us pinned since dawn! Our
  Pokémon haul carts, they don't FIGHT — please, if you can move that pack, we'll — just be
  careful, they're scared and scared is worse than mean!"

**Gabby** *(hanging back, filming, thrilled):*
- "Ty are you GETTING this, this is INCREDIBLE, stranded merchants, a wall of feral fury, one
  lone trainer from a distant land — do NOT stop rolling—"

**Ty:** "Rolling. Maybe help, though?" *(to player)* "She means you. Go."

*(The player fights/scares off the pack — 2-3 scripted wild battles. On clear:)*

**Lead vendor:**
- "They're — they're running! You did it! Oh, we've been up here HOURS, the carts, the stock —
  bless you, bless you, we're getting straight down to Slateport, market day's half gone!
  You'll come by the stalls? You HAVE to come by the stalls. We owe you the whole cart."

**Gabby** *(to camera, breathless recap):*
- "There you have it, Slateport — a lone trainer from JOHTO, three regions from home, charged a
  fortress of wild fury and freed your beloved Mauville merchants SINGLE-HANDED! Ty got every
  second! This is the kid, this is the STORY — I'm Gabby, this is Ty, and THIS—" *(gestures
  grandly at the perfectly ordinary route)* "—is history."

**Ty:** *(deadpan)* "It was three Poochyena." *(beat)* "Great shot, though. Really was."

**Gabby** *(to the player):*
- "We're heading further up — more route, more Hoenn, more STORY. You'll see us again, kid, count
  on it. Places to be, faces to film. Go collect your thank-yous. You earned the market."

*(Set `FLAG_APOC_CH8_VENDORS_RESCUED`. Gabby & Ty exit north — rematch seed.)*

---

## 8.5 · The Market, Unlocked

*Back in Slateport: the once-empty stalls are open, Mauville specialty stock laid out.*

**Lead vendor (at the newly-open stall):**
- "There she is — our hero, in the flesh! Everybody, THIS is the one! We're open, we're stocked,
  and your money's no good here — well. It's a LITTLE good here, I've got a business. But you get
  the *friend price*, forever. Take a look. Mauville makes things you won't find anywhere else on
  this coast." *(stock in [HOENN_ITEMS.md](HOENN_ITEMS.md))*

**Grateful vendor 2:**
- "We told everyone. EVERYONE. Half of Slateport knows your face now, and the other half saw you
  on Gabby's segment last night. You're famous for about a week. Enjoy it — it fades right about
  the time you leave town. It always does."

---

## 8.6 · Brawly's Gym — Closed

*A queue of frustrated trainers outside the Fighting gym. The door's locked. An aide works the
line.*

**Gym sign:** "SLATEPORT FIGHTING GYM — Leader: BRAWLY. Hours: when he's here. (He commutes.
We're sorry.)"

**The aide (at the front of the line):**
- "I know. I KNOW. He's not in. He commutes from Dewford — across the water — and if the surf's
  running, sometimes the Leader chooses the surf. It's a whole thing. When he DOES turn up, he
  batters through the entire line in one afternoon, boom, boom, boom, so nobody loses their
  challenge. Just... not today. Check back. Or don't. I'm not the boss of your day."
- *(if asked about the gym)* "Fighting-type. Physical, aggressive, gets right in your face and
  stays there. Brawly doesn't out-think you, he out-*wills* you. Bring something that can take a
  hit and hit back. And bring patience, because — gestures at everything — commute."

**Frustrated challenger (in line):**
- "Third day. THIRD. I could've ferried to Dewford and back twice by now. But the moment I leave,
  that's the moment he shows, and I lose my spot, and — no. No, I'm staying. I'm committed to my
  own misery now."

*(No badge. The player notes the gym and moves on.)*

---

## 8.7 · The Oceanic Museum — Captain Stern

*Slateport's cultural centerpiece. Marine biology, naval history, the weather crisis handled
with restraint, a small Pacifidlog memorial. Stern is on the floor, vibrating with enthusiasm.*

**Museum sign:** "THE OCEANIC MUSEUM — Hoenn and the Sea: A Long Conversation. Admission free.
Curiosity mandatory."

### 8.7a · Exhibit placards (read-only)

- "MARINE BIOLOGY WING — The Hoenn coast holds more life per fathom than any water on record.
  We are still naming it. Some of it is naming us back."
- "THE WEATHER CRISIS — Two forces, drought and deluge, pushed to the edge and past it. People
  suffered. The region adapted. We do not dramatize it here. We remember it, and we build lower
  to the water, and we take less. That is the whole exhibit. That is the whole lesson."
- "THE TWO TEAMS (historical) — Once, two movements believed the sea and the land could be
  argued into taking sides. They were wrong, and being wrong nearly drowned all of us. When the
  waters settled, so did they — disbanded, scattered, absorbed back into the ordinary business
  of living somewhere that finally *listened* to its weather. We keep this case small on purpose.
  They are history. We would like to keep them that way."
- "IN MEMORY OF PACIFIDLOG — The tides took the town. They did not take the people who choose,
  every year, to say its name aloud. Say it. Pacifidlog. There. Now you carry a little of it too."
- "NAVAL HISTORY — Before the ferries and the freight loops, Hoenn found its neighbors by star
  and nerve. The instruments in this case still work. The nerve is left as an exercise to the
  visitor."

### 8.7b · Captain Stern — the tour + the quest

**Captain Stern:**
- "A visitor! A YOUNG visitor! Who came in and is — you're actually reading the placards. You're
  READING them. Do you know how rare that is? Come here, come here, forget the placards, I'll
  give you the real tour, the DIRECTOR'S tour, and it is SO much better."
- *(sweeping the player along)* "Marine trenches, naval charts, the sediment core over there that
  is — I know, it's a tube of mud, but it's a tube of mud that remembers the last four thousand
  years and it does not lie, which is more than I can say for most of my board of directors—"
- *(deflating a little, at a set of half-empty cases)* "And then. There's this. My collection. My
  *incomplete* collection. Look at these gaps. It's an embarrassment and it's a heartbreak and
  it's the same thing, at a museum."

*(The quest.)*

**Captain Stern:**
- "Here's the dream, and I'm going to say it out loud to a stranger because that's the kind of
  day it's been. Every region — EVERY one — built something near the water, or under it. Temples.
  Ruins. Caverns nobody should've reached and did anyway. And every one of those places left
  something behind. A relic. A piece of the long conversation between people and the sea."
- "I want one from each. Just ONE, from the greatest maritime or subterranean site in every
  region. The Whirl Islands, out your way in Johto. The frozen caves at Seafoam, in Kanto. The
  deep trenches here in Hoenn. Iron Island, in Sinnoh — they mined the bones of the earth there.
  And the sunken ruins in Unova, older than writing, with writing on them anyway."
- "I can't go. I can't leave the museum long enough to do the fieldwork — I've tried, the place
  falls apart, I come back and someone's mislabeled a WHALE. But you — you're a traveler. You go
  to places like that. So." *(he looks at the player, suddenly shy about it)* "If you ever —
  EVER — find yourself in one of those places, and you see something that looks like it belongs
  in a museum... would you think of me? Bring it here? I'll make it worth your while, each one,
  I swear it. And if you brought them all..." *(he trails off, almost afraid to want it)*
  "...well. That would be the whole conversation, wouldn't it. In one room. Finally."

*(Set `FLAG_APOC_CH8_STERN_QUEST` + init `VAR_APOC_STERN_ARTIFACTS`. Nothing collectible yet.)*

**Captain Stern** *(brightening, back to normal):*
- "Anyway! No pressure! You probably think I'm a lot! I AM a lot! Enjoy the sediment core, it's
  genuinely the best thing here, and mind the wet-floor sign, we take the ocean seriously in this
  building, sometimes it comes inside."

---

## 8.8 · The Beach (Route 109) + The Cameos

*The beach south of Slateport: casual sand battles, swimmers guarding the water, sunbathers, a
soda shack. Optional, light, fun.*

**Route 109 sign:** "ROUTE 109 — Slateport Beach. Swim at your own risk. Battle at everyone's."

### 8.8a · Beach trainers (optional)

*pokeemerald Route 109 + Seashore House placements, rebuilt + re-tuned up; rosters in
[HOENN_BATTLES.md](HOENN_BATTLES.md). Rename any vanilla "Mel".*

**Tuber (with a float)** — `TRAINER_LOLA_1`
- **[Pre]:** "I'm not even all the way in the water and I'll STILL battle you! That's beach
  rules! Everybody near the water is fair game!"
- **[Loss]:** "Nooo, my float's gonna float away while I sulk about this—"
- **[Post]:** "You're pretty good for someone who's clearly never been to a beach before. You've
  got the boat-pale thing going. It's okay. Hoenn'll fix it. Hoenn fixes everybody."

**Swimmer (treading water)** — *(recast Route 109 swimmer)*
- **[Pre]:** "You want past me you go THROUGH me, that's how the water works! Come on in, the
  battling's fine!"
- **[Loss]:** "Blублlub — okay — blub — good one—"
- **[Post]:** "Careful past the drop-off, the Wailmer come up under you like a hiccup. Big
  friendly hiccup. Terrifying. Adorable. Both."

**Sailor (Seashore House)** — `TRAINER_DEWFORD_HOUSE` *(recast Seashore House sailor, Dwayne)*
- **[Pre]:** "Landlocked-looking fella like you, in MY soda shack? You'll battle for the stool,
  friend. House rules. My house. My rules. My stool."
- **[Loss]:** "Hah! Take the stool. Take the soda too, you earned it. First one's on me."
- **[Post]:** "You headed to Dewford eventually? Ferry runs from down the coast now — commercial,
  daily, none of the old ask-a-sailor-nicely business. Brawly's over there when he's not over
  HERE, which is a coin toss on a good day."

### 8.8b · The Seashore House (soda shop)

**Seashore House owner:**
- "Fresh Water, Soda Pop, Lemonade — all cheap, all cold, all better on a hot beach than
  anything a Mart'll sell you. Sit. Drink. Watch somebody lose to a Tuber. It's the Slateport
  experience. Well — it's A Slateport experience. There's a lot of them." *(stock in [HOENN_ITEMS.md](HOENN_ITEMS.md))*

### 8.8c · Scott (the Frontier seed)

*Scott finds the player — beach, market, or outside the gym. Thirty seconds.*

**Scott:**
- "Mind if I—? No, don't get up. Name's Scott. I travel. Regions, mostly — I go where the
  interesting trainers are, and lately that's a lot of airports." *(a easy, weighing look)*
  "I watch a lot of battles. Most of them, I finish my drink and move on. Yours, I put the drink
  down."
- "I'm not going to explain myself — where's the fun — but I'll be building something, out here,
  eventually. For trainers who've got that thing you've got. Take this." *(a card changes hands)*
  "You'll understand it when you need to. And you'll need to. See you around, kid. And you will
  see me around. That's kind of the whole bit."

*(He's gone. One-shot `FLAG_APOC_CH8_SCOTT_MET`. No item beyond the card/flavor.)*

### 8.8d · Lisia (the Contest / Wallace seed — design add)

*Lisia, mid-photoshoot near the market or beach, a small delighted crowd.*

**Lisia:**
- "—okay okay ONE more photo — oh! OH. You! Yes, you, the one who looks like they walked out of
  a completely different game — where are you FROM? ...Johto?! That's so far, that's like a whole
  BOAT away, I'm obsessed, come here, be in the photo, you're EXOTIC."
- "I'm doing a showcase up in Lilycove — you have to come, it's going to be dazzling, it's going
  to be ME, mostly, but ALSO—" *(a stage whisper, thrilled)* "—my uncle's got this big thing
  coming in Sootopolis. Huge. Hush-hush. I'm not supposed to say and I'm DYING. You didn't hear
  it from me. Okay! Say something cute for the camera! ...You said nothing. That's SO cute. Ty
  would've loved that. Do you know Ty? Everyone knows Ty."

*(Bright, brief. One-shot `FLAG_APOC_CH8_LISIA_MET`. Wallace-retirement seed planted; the player
can't parse it yet.)*

### 8.8e · The Dewford ferry (future-access signpost)

**Ferry barker (at the dock):**
- "Dewford ferry! Daily service, dead cheap, none of the old 'know a guy with a boat' nonsense —
  we replaced all that with a schedule and a snack bar. Not running your way today, but keep us in
  mind. Half of Hoenn's out on those islands and the other half's trying to get back." *(future
  access — not usable this chapter)*

---

## 8.9 · Moving On — North to Mauville

**Pokémon Center nurse / market elder:**
- "Heading on? Smart. Road runs north — Route 110 up to **Mauville**, big bright city, runs on
  electricity and confidence in about equal measure. Past that it climbs toward **Lavaridge** —
  hot springs, and the finest breeding facility in the world, people come from every region for
  it. Long road. Good road. Go while the light's high."

*(Set `FLAG_APOC_CH8_DONE`. Hand off to **Chapter 9 — Mauville**.)*

**Closing image:** *Slateport at the player's back, still roaring — the market reopened, the
story filed, the museum a little less empty in the player's memory than in its cases. A city
that helped them, got a segment out of them, and went right on without them. The player turns
north, into the heat.*

---

## Continuity & callbacks (build-check)

- **This is the first non-HGSS chapter.** Every map is a **new HGSS build ported from
  pokeemerald** (see the BUILD cross-region note + [[apocrypha-cross-region-maps]]). Dialogue is
  engine-agnostic; the battle slots reference pokeemerald source trainers, rebuilt + re-tuned up.
- **The conspiracy is deliberately asleep.** No Silph, no Silver, no lab coats. **Aqua/Magma are
  defunct/historical (confirmed canon)** — a small museum case, not a threat; disbanded after the
  weather crisis. The Hoenn conspiracy thread (port trafficking) runs through Silph/Rocket-Silver,
  not the weather teams. Grunt objects stay hidden permanently.
  Chapter 8 is the palate-cleanser — a real Pokémon adventure. The three seeds (Stern's quest,
  Scott's card, Lisia's Wallace hint) are *quiet* and pay off much later. Resist the urge to
  foreshadow the main plot here; the *absence* of it is the point.
- **Stern's quest spans the whole game.** `VAR_APOC_STERN_ARTIFACTS` tracks 5 relics (Whirl
  Islands/Seafoam/Undersea/Iron Island/Abyssal Ruins). Each site is later-game (Surf/Dive/region
  access). Every maritime cave or sunken ruin the player later enters should offer its artifact.
  See [HOENN_ITEMS.md](HOENN_ITEMS.md) for the item design + rewards.
- **Gabby & Ty return.** Tier 1 is fought here; tiers 2-6 are the Hoenn rematch ladder on later
  routes. Their levels are already built to climb — coordinate rematch placements with the curve.
- **Brawly is closed, not beaten.** No badge this chapter. His Dewford access (the ferry from the
  beach) is planted but not wired; the reopening + his re-tuned roster are a later-chapter job.
- **"Mel" name collision:** rename the vanilla Route 109 trainer "Mel" — Apocrypha's Mel is the
  Goldenrod journalist (Ch4-5), not a Hoenn beachgoer.
- **Lisia is a design add** (ORAS, absent from Emerald) — **kept (confirmed).** Her Wallace hint
  ("something big in Sootopolis") seeds Wallace's arc; keep it a hint the player can't yet decode.
- **No Hoenn badge here — and the first Hoenn badge is not Brawly.** The Hoenn circuit leads with
  **Wes's Shadow gym at Rustboro** (DESIGN gym list); **Brawly's Fighting badge** — at **Dewford**,
  via the Petalburg→Dewford ferry — is a *later* Hoenn badge, not the next, and **not Mauville**
  (which has no gym; Surge only consults there). The curve keeps climbing on routes; Ch8 tops out
  ~lv27-28, heading toward the Hoenn gym circuit.
