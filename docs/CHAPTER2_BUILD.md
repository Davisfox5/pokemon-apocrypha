# Pokemon Apocrypha - Chapter 2 Build Spec

> Scope: Routes 30/31, Violet City, Sprout Tower, optional Ruins of Alph,
> Route 32, Union Cave, Route 33. This is the implementation-facing expansion
> of the Chapter 2 outline in `DESIGN.md`. Pairs with
> [JOHTO_BATTLES.md](JOHTO_BATTLES.md) (rosters), [JOHTO_ITEMS.md](JOHTO_ITEMS.md)
> (items), and **[CHAPTER2_SCENES_SPEC.md](CHAPTER2_SCENES_SPEC.md) — the full
> line-by-line dialogue script.** The "Sample lines" in the Cast section below are
> voice references; the complete spoken script lives in the scenes spec.

## Chapter Promise

Chapter 2 is the first time the player feels like a real trainer. Chapter 1 is
home, awe, and permission. Chapter 2 is road dust, classroom rivalry, borrowed
wisdom, and the happy shock of realizing that the world is much larger than the
route north of Cherrygrove.

The spirit stays bright and classic. Nobody is in mortal danger. The conflict is
pranks, pride, bad preparation, and adults gently trying to turn enthusiasm into
discipline. The player learns the region's trainer culture before the story ever
asks them to distrust it.

Core themes:

- Training is social: students, sages, route kids, and visiting instructors all
  teach something different.
- Tradition and institution sit side by side: Sprout Tower and Violet University
  are both places of learning.
- Kestra is a friend first and a rival second. She wants to win, but she also
  wants the player beside her for every ridiculous new thing.
- The first long-game unease is optional and quiet: Silph researchers at the
  Ruins of Alph are polite, competent, and slightly too interested.

## Progression Spine

| Beat | Maps | Purpose |
|------|------|---------|
| 2.1 Road north | Route 30, Route 31 | First trainer battles, held items, Apricorns, route color |
| 2.2 Violet arrival | Violet City, gatehouse | Establish the university city and Earl as dean |
| 2.3 Campus sampler | Violet interiors, old gym | Students, practice court, Roxanne tease |
| 2.4 Sprout incident | Sprout Tower 1F-3F | Mediation quest, support/status lesson |
| 2.5 Roxanne practicum | Violet old gym | Pseudo-gym, first formal test, TM reward |
| 2.6 Kestra battle | Violet City / old gym exit | First rival battle with type-advantage starter |
| 2.7 Optional ruins | Ruins of Alph | Wonder, puzzle flavor, first subtle Silph seed |
| 2.8 Road to Azalea | Route 32, Union Cave, Route 33 | Old Rod, first dungeon, rainy arrival |

Target end state: player lead team around lv 15-17 (post +3 curve lift), no badge
yet, ready for Azalea and the first real gym badge in Chapter 3.

## Cast

### Kestra

Kestra arrives on Route 30 ahead of the player, pretending this was strategy and
not impatience. Her Chapter 2 role is to keep momentum high: she calls out the
first real trainers, points the player toward Violet University, and gets tangled
in Ren's Sprout Tower prank because she cannot resist a dare.

Voice: bright, competitive, funny, emotionally direct.

Sample lines:

- "There you are! I was starting to think Gold's shoes were decorative."
- "Rule one of being trainers: if a sign says Trainer Tips, we pretend we read
  it."
- "If I beat a Sage, I am calling it homework."
- "After Roxanne, you and me. First official battle. No wild Pokemon, no rescue
  panic, no Gold hovering with a lecture face."

### Earl Dervish

Earl is Violet University's dean: theatrical, intense, and genuinely beloved by
students. He still speaks in odd inversions, but he is not a joke. He built a
trainer school into a university because he believes Pokemon training is a craft
that deserves scholarship.

Voice: grand, warm, peculiar syntax, teacherly.

Sample lines:

- "Yes! Earl I am! Dean I am also! Welcome, new road scholars!"
- "Violet teaches many ways. Books for mind, court for body, tower for spirit."
- "A prank is small storm. A lesson is what remains after rain."

### Roxanne

Roxanne is visiting from Hoenn as a guest instructor. She is younger than many
faculty but carries herself like someone used to being underestimated. Her
pseudo-gym is not a badge match; it is a practicum on type pressure, switching,
and item use.

Voice: precise, encouraging, quietly competitive.

Sample lines:

- "A gym battle is not a test of whether you know one answer. It is a test of
  whether you can keep thinking after the first answer fails."
- "Rock Pokemon are honest teachers. They punish carelessness immediately."
- "You adjusted. That matters more than winning quickly."

### Ren

Ren is a Violet student with a good heart and terrible impulse control. He hid
school training tags around Sprout Tower as a dare, startling the monks and
making Kestra laugh until the Sages caught them both.

Voice: fast, embarrassed, defensive until someone gives him a way to help.

Sample lines:

- "It was not vandalism! It was... unauthorized field placement."
- "Kestra said the tower needed more excitement. I may have supplied too much
  excitement."
- "If I apologize in alphabetical order, will they know I mean it?"

### Elder Li

The senior Sage of Sprout Tower. Calm, dry, difficult to ruffle. He turns the
prank into a lesson on patience, status moves, and respect for places older than
the university.

Voice: spare, amused, quietly sharp.

Sample lines:

- "The tower bends. It does not panic."
- "A trainer who cannot wait will eventually be taught by paralysis."
- "Return what was misplaced. Then battle us with steadier hands."

### Mr. Pokemon

Mr. Pokemon becomes the held-item introduction. He is delighted by new trainers
and gives a Quick Claw because an early journey should teach that preparation
can matter before power does.

Voice: delighted collector, fond of odd practical wisdom.

Sample lines:

- "A held item is a little promise. Your Pokemon carries it, and it may answer
  at just the right moment."
- "This Quick Claw is not a shortcut. It is a surprise. Surprises are sometimes
  enough."

### Silph Field Team

Two polite researchers at Ruins of Alph. They never threaten anyone and do not
mention Apex. They ask about Unown, survey plates, and radio interference. The
seed is their corporate presence, not a villain speech.

Voice: professional, clipped, friendly at the surface.

Sample lines:

- "Silph sponsors preservation equipment here. The ruins are delicate."
- "Unown react strongly to pattern, sound, and expectation. That third one is
  not in our report, naturally."
- "If your Pokedex records anything unusual, the university would appreciate a
  copy."

## Scene Details

### 2.1 Route 30 - The Road Becomes Real

Kestra waits near the southern bend of Route 30, just far enough from
Cherrygrove that the music and grass make the journey feel official. She calls
the player out for taking too long, then reframes Route 30 as their first test:
wild Pokemon, eye-contact trainers, Apricorns, and Mr. Pokemon up north.

Scenery direction:

- Keep the HGSS route shape, but make it feel lived in: berry pots, small school
  notices nailed near Trainer Tips signs, and students practicing beside the
  fence.
- The Apricorn man's house stays warm and eccentric. He is the route's "local
  craft" voice.
- Mr. Pokemon's house should feel like an overstuffed collector's cottage: boxes,
  labeled jars, old field maps, and one clear tabletop where he explains held
  items.

Implementation notes:

- Add a one-time Kestra coordinate scene at the southern approach.
- Keep the vanilla Apricorn Box event unless it later conflicts with pacing.
- Retheme existing route NPC lines toward first-journey training advice.
- Mr. Pokemon gift: Quick Claw, gated by a Chapter 2 flag.

### 2.2 Route 31 and the Violet Gate

Route 31 is the transition from friendly route to wider region. Dark Cave sits
nearby as a visible dare, but without Flash the player can only sample its mouth.
The gate attendant mentions Violet's university traffic and warns that half the
students think catching a Bellsprout counts as spiritual preparation.

Scenery direction:

- Dark Cave exterior should feel cool and damp against Route 31's warm daylight.
- Gatehouse posters advertise guest lectures, practical battles, and Sprout
  Tower visitation rules.

### 2.3 Violet City - University City

Violet is no longer just a gym town. The old school expanded into a compact
university district, while the traditional city still wraps around Sprout Tower.
The old gym building is now a League practice hall used for visiting instructor
sessions and pre-badge assessments.

Key spaces:

- Pokemon School: lecture room and lobby chatter. Students discuss natures,
  status moves, and rumors about Roxanne's practicum.
- Old Gym / Practice Hall: Falkner's old arena repurposed with court markings,
  student benches, and a visiting-instructor station.
- Library / northwest house: compact lore hub for Sprout Tower, Ruins of Alph,
  and old Johto League history.
- Mart and Center: trainer-student economy, with early support items emphasized.

Earl arrival scene:

Earl intercepts the player and Kestra near the gate or school approach. His tour
is short and energetic, unlike the vanilla city tour. He identifies them as new
"road scholars," points out the Center/Mart, and invites them to visit the
practice hall after seeing the tower.

### 2.4 Sprout Tower - Ren's Prank

Ren hid university practice tags around the tower as a dare. The tags are paper
talismans marked with move categories, type symbols, and silly student notes.
The Sages are not furious; they are disappointed in a very calm way. Earl asks
the player, Kestra, and Ren to help retrieve the tags and apologize properly.

Quest loop:

1. Enter tower; Sage explains the disturbance.
2. Find Ren and Kestra on 1F or 2F.
3. Retrieve three tags from tower floors through simple object interactions.
4. Battle Sages who teach status/support ideas.
5. Elder Li accepts the apology and gives the player Flash or a support reward.

Tone:

The tower remains serene. Humor comes from Ren and Kestra being very bad at
looking innocent next to monks who miss nothing.

### 2.5 Roxanne Practicum

After Sprout Tower, Earl opens the practice hall. Roxanne runs a pseudo-gym:
student trainers first, then Roxanne. It is formal enough to feel important but
explicitly not a badge challenge.

Lesson goals:

- Rock types punish careless Normal/Flying reliance.
- Status and support from Sprout Tower are useful.
- Held items and healing items are legitimate preparation.
- Switching is part of battling, not an emergency button.

Reward:

- TM39 Rock Tomb.
- Earl/Roxanne endorsement that the player is ready for the Azalea badge circuit.

### 2.6 First Kestra Rival Battle

Kestra challenges the player after Roxanne. She uses the starter that has type
advantage over the player's starter plus Route 30/31 catches. This battle should
feel friendly, fair, and important: she wants to mark the exact moment they stop
being kids with borrowed Pokemon and become peers.

Post-battle:

Kestra heads toward Azalea first, claiming she is doing "advance research" and
absolutely not racing. She can mention Route 32, Union Cave, and the old fishing
guru.

### 2.7 Optional Ruins of Alph

The Ruins are optional but should feel tempting. A student or researcher points
the player south/west. The immediate content can be small: exterior NPCs, a
partial puzzle room, Unown lore, a hidden item, and Silph field researchers.

The Silph seed must stay quiet. No villain music. No blocked doors with ominous
guards. Just a polished corporate research presence in a sacred old place.

### 2.8 Route 32, Union Cave, Route 33

Route 32 is the first long departure from a hub. It grants the Old Rod and shows
the player that optional catches can change a team. Union Cave is the first real
dungeon, teaching resource management and navigation without becoming punishing.
Route 33's rain gives the arrival to Azalea a memorable sensory shift.

Scenery direction:

- Route 32: ponds, fishermen, university students going home, first sense of the
  road stretching.
- Union Cave: damp amber stone, small pools, hikers, students on fieldwork.
- Route 33: rain, darker greens, wet path into Azalea.

## State And Files

Known map/script targets:

| Area | Map JSON | Script |
|------|----------|--------|
| Route 30 | `031_R30.json` | `scr_seq_0227_R30.s` |
| Route 30 Apricorn House | `124_R30R0101.json` | `scr_seq_0228_R30R0101.s` |
| Mr. Pokemon's House | `139_R30R0201.json` | `scr_seq_0229_R30R0201.s` |
| Route 31 | `032_R31.json` | `scr_seq_0230_R31.s` |
| Route 31/Violet Gate | `094_R31R0101.json` | `scr_seq_0231_R31R0101.s` |
| Violet City | `070_T22.json` | `scr_seq_0857_T22.s` |
| Violet Mart | `152_T22FS0101.json` | `scr_seq_0858_T22FS0101.s` |
| Violet Old Gym | `131_T22GYM0101.json` | `scr_seq_0859_T22GYM0101.s` |
| Violet Pokemon Center | `153_T22PC0101.json` | `scr_seq_0860_T22PC0101.s` |
| Violet Pokemon School | `154_T22R0301.json` | `scr_seq_0862_T22R0301.s` |
| Sprout Tower | `107_D15R0101.json` etc. | `scr_seq_0016_D15R0101.s` etc. |
| Ruins of Alph | `110_D24R0101.json` | `scr_seq_0037_D24R0101.s` |
| Union Cave | `096_D25R0101.json` etc. | `scr_seq_0056_D25R0101.s` etc. |

Initial state additions:

- `FLAG_APOC_CH2_ROUTE30_INTRO_DONE` (`0x233`): hides the Route 30 Kestra
  object and prevents replaying the first Chapter 2 road scene.

Future likely state:

- Mr. Pokemon held-item gift flag.
- Violet arrival/Earl intro flag.
- Sprout prank progress variable.
- Roxanne practicum clear flag.
- Kestra rival battle clear flag.

Use only confirmed-free flags/vars as they are added; several nearby `UNK_23x`
flags are already used by later Johto maps.

## Implementation Order

1. Route 30 opener: Kestra object, one-time coordinate scene, dialogue.
2. Route 30/31 NPC retheme and Mr. Pokemon held-item gift.
3. Violet arrival: Earl short tour, university signage/NPC lines.
4. Sprout Tower prank quest and Sage dialogue pass.
5. Roxanne practicum trainer and reward wiring.
6. Kestra rival battle with starter-dependent team.
7. Ruins of Alph optional Silph seed.
8. Route 32/Union/Route 33 item and trainer pass.

