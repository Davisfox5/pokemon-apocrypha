# Tutor rosters

**Status: the move data is built and in the ROM. Placement, pricing and
progression are open.**

**150 tutor moves**, every one assigned to a region. That is the whole tutor
economy in data: `gTutorMoves[]` holds exactly these 150 and nothing else.

Three sources feed it:

| Source | Count | What it is |
| --- | --- | --- |
| Historical TM | 89 | Was a TM or HM in a Gen 1-5 mainline game, but is not one of our 111 machines |
| Emerald tutor | 12 | Vanilla Emerald's own tutor moves, which had no region until now |
| Tier 2 | 49 | Signature moves that were never TMs -- the starter ultimates, Draco Meteor, Sacred Fire and their peers |

The historical TM sets come from the per-game `TMMoves` in
`game/tools/learnset_helpers/porymoves_files/` -- real game data, not
recollection, across RBY, Yellow, GS, Crystal, RSE, FRLG, DP, Platinum, HGSS, BW
and B2W2.

## How regions were assigned

Not by introducing generation. That was the first cut and it failed: Gen 1
introduced the moves that stayed TMs for eleven straight games, so it handed
**Kanto 44** and left **Hoenn and Unova with 8 each**, with Kanto only the second
region the player reaches.

Learner distribution was tested as a tiebreaker and is useless here -- Roar's
learners are 21-33% of every region's roster, Hyper Beam's 46-60%. These moves are
broadly learnable everywhere, so the data cannot decide it.

So each move sits where it makes sense: a landmark, a gym leader, a species, or a
region's type character. Moves with a strong tie to a place were left there.

| Region | Moves | Signature | Ordinary | Identity |
| --- | --- | --- | --- | --- |

| Johto | 31 | 10 | 21 | tradition, martial discipline, folklore and the roaming legends |
| Kanto | 28 | 14 | 14 | the origin: its institutions, the Dojo, the Power Plant, Lavender Tower |
| Hoenn | 30 | 20 | 10 | ocean, weather, volcano and the contest circuit |
| Sinnoh | 35 | 21 | 14 | mountains, snow, myth and heavy industry |
| Unova | 26 | 15 | 11 | the modern, urban, industrial region |
| **Total** | **150** | **80** | **70** | |

## Tier

**Signature** is table power 86 or above, above the TM cap. Bought with rare
goods, often from another region, and opening late. **Ordinary** is everything
else: common currency, placeable early, and the tier that should grow as the
player progresses.

The split is mechanical, on table power alone, and has not been reviewed for
conditional damage or utility. Treat it as a starting cut.

## Not every teacher is a move tutor

A roster this size does not mean a hundred and fifty generic tutors. Signature
moves in particular suit **named characters** teaching a single move as an event:
Lance giving Draco Meteor in the Dragon's Den, Steven giving Meteor Mash at Meteor
Falls, Riley giving Aura Sphere on Iron Island. Those are marked in the tables.
An ordinary tutor can also carry two or three moves rather than twenty, and can
gain more as the game goes on.

## What is built and what is not

`extraTutors` in `game/src/data/pokemon/special_movesets.json` carries 138 of the
150; the other 12 come from Emerald's own tutor data. The generator merges both
into `gTutorMoves[]` and the teachable learnsets, so **every one of these moves is
teachable** by the species that can learn it.

The regional assignment is design, not data -- the engine has no concept of a
region. **No tutor exists in the world, none has a price, and none has a
location.** Moving a move between regions here costs nothing until tutors are placed.


## Johto — 31 moves

*Tradition, martial discipline, folklore and the roaming legends.*

**Signature — rare goods, late: 10**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Draco Meteor | 140 | Dragon | Spec | 31 | Tier 2 | Blackthorn's dragon masters -- Lance's move to give |
| Zap Cannon | 120 | Electric | Spec | 90 | historical TM | a Gen 2 original |
| Outrage | 120 | Dragon | Phys | 88 | Tier 2 | the Dragon's Den clan |
| Megahorn | 120 | Bug | Phys | 26 | Tier 2 | Heracross in the National Park |
| Superpower | 120 | Fighting | Phys | 115 | Tier 2 | Mt. Mortar's martial discipline |
| Dynamic Punch | 100 | Fighting | Phys | 139 | historical TM | Mt. Mortar's Karate King |
| Iron Tail | 100 | Steel | Phys | 241 | historical TM | Steel was introduced here; Steelix |
| Future Sight | 100 | Psychic | Spec | 78 | Tier 2 | the Ruins of Alph |
| Cross Chop | 100 | Fighting | Phys | 21 | Tier 2 | Mt. Mortar's Karate King |
| Sacred Fire | 100 | Fire | Phys | 2 | Tier 2 | Ho-Oh and the Tin Tower |

**Ordinary — common currency: 21**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Headbutt | 70 | Normal | Phys | 426 | historical TM | the Headbutt tree -- Johto's own field mechanic |
| Secret Power | 70 | Normal | Phys | 629 | historical TM | Secret Bases are cut, so it is simply a plain universal attack -- first-region fare |
| Icy Wind | 55 | Ice | Spec | 233 | Emerald tutor | Pryce's gym at Mahogany |
| Snore | 40 | Normal | Spec | 633 | historical TM | a Gen 2 original |
| Rollout | 30 | Rock | Phys | 158 | historical TM | Whitney's Miltank |
| Fury Cutter | 20 | Bug | Phys | 148 | historical TM | Bugsy in Azalea |
| Mud-Slap | 20 | Ground | Spec | 397 | historical TM | a Gen 2 original |
| Frustration | 1 | Normal | Phys | 629 | historical TM | the mirror of Return, which is a Johto TM |
| Seismic Toss | 1 | Fighting | Phys | 131 | Emerald tutor | Mt. Mortar's martial discipline |
| Roar | — | Normal | Stat | 164 | historical TM | the roaming legendary beasts |
| Whirlwind | — | Normal | Stat | 59 | historical TM | the other half of the phazing pair |
| Curse | — | Ghost | Stat | 359 | historical TM | Ecruteak and the Burned Tower |
| Nightmare | — | Ghost | Stat | 57 | historical TM | Ecruteak |
| Detect | — | Fighting | Stat | 146 | historical TM | martial discipline |
| Swagger | — | Normal | Stat | 629 | historical TM | a Gen 2 original |
| Psych Up | — | Normal | Stat | 233 | historical TM | a Gen 2 original |
| Safeguard | — | Normal | Stat | 186 | historical TM | a Gen 2 original |
| Sweet Scent | — | Normal | Stat | 61 | historical TM | the National Park |
| Sleep Talk | — | Normal | Stat | 630 | Emerald tutor | a Gen 2 original |
| Endure | — | Normal | Stat | 629 | Emerald tutor | a Gen 2 original |
| Swords Dance | — | Normal | Stat | 178 | Emerald tutor | Mt. Mortar's martial discipline |


## Kanto — 28 moves

*The origin: its institutions, the Dojo, the Power Plant, Lavender Tower.*

**Signature — rare goods, late: 14**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Explosion | 250 | Normal | Phys | 71 | historical TM | Voltorb and Electrode at the Power Plant |
| Self-Destruct | 200 | Normal | Phys | 67 | historical TM | the same |
| Hyper Beam | 150 | Normal | Spec | 340 | historical TM | the Celadon Game Corner prize, the ultimate Gen 1 TM |
| High Jump Kick | 130 | Fighting | Phys | 11 | Tier 2 | Hitmonlee at the Fighting Dojo |
| Mega Kick | 120 | Normal | Phys | 165 | historical TM | the Saffron Fighting Dojo |
| Thunder | 120 | Electric | Spec | 167 | historical TM | the Power Plant |
| Thrash | 120 | Normal | Phys | 74 | Tier 2 | a Gen 1 rampage |
| Petal Dance | 120 | Grass | Spec | 15 | Tier 2 | Erika at Celadon |
| Dream Eater | 100 | Psychic | Spec | 157 | historical TM | Hypno and Lavender Town |
| Earthquake | 100 | Ground | Phys | 200 | historical TM | Giovanni's ground |
| Jump Kick | 100 | Fighting | Phys | 8 | Tier 2 | Hitmonlee at the Fighting Dojo |
| Thunderbolt | 95 | Electric | Spec | 184 | historical TM | Lt. Surge and the Power Plant |
| Psychic | 90 | Psychic | Spec | 164 | historical TM | Saffron and Sabrina |
| Crabhammer | 90 | Water | Phys | 6 | Tier 2 | Kingler in the Cerulean waters |

**Ordinary — common currency: 14**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Body Slam | 85 | Normal | Phys | 399 | Emerald tutor | Snorlax asleep on the road |
| Mega Punch | 80 | Normal | Phys | 170 | historical TM | the Saffron Fighting Dojo |
| Submission | 80 | Fighting | Phys | 61 | historical TM | the Saffron Fighting Dojo |
| Thunder Punch | 75 | Electric | Phys | 157 | Emerald tutor | Lt. Surge and the Power Plant |
| Pay Day | 40 | Normal | Phys | 36 | historical TM | Meowth and the Game Corner |
| Horn Drill | 1 | Normal | Phys | 21 | historical TM | the Gen 1 one-hit KO, Rhydon and Nidoking |
| Fissure | 1 | Ground | Phys | 58 | historical TM | the Gen 1 one-hit KO, Giovanni's ground |
| Counter | 1 | Fighting | Phys | 196 | Emerald tutor | the Saffron Fighting Dojo |
| Substitute | — | Normal | Stat | 629 | historical TM | the defining Gen 1 utility TM |
| Metronome | — | Normal | Stat | 98 | historical TM | Clefairy in Mt. Moon |
| Mimic | — | Normal | Stat | 380 | historical TM | a Gen 1 staple |
| Soft-Boiled | — | Normal | Stat | 9 | historical TM | Chansey |
| Teleport | — | Psychic | Stat | 44 | historical TM | Abra and Saffron |
| Double Team | — | Normal | Stat | 629 | historical TM | a Celadon Game Corner prize in Red and Blue |


## Hoenn — 30 moves

*Ocean, weather, volcano and the contest circuit.*

**Signature — rare goods, late: 20**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Focus Punch | 150 | Fighting | Phys | 184 | historical TM | Hoenn's own |
| Water Spout | 150 | Water | Spec | 10 | Tier 2 | Kyogre |
| Eruption | 150 | Fire | Spec | 7 | Tier 2 | Groudon and Mt. Chimney |
| Blast Burn | 150 | Fire | Spec | 6 | Tier 2 | the master of the three starters |
| Hydro Cannon | 150 | Water | Spec | 6 | Tier 2 | the master of the three starters |
| Frenzy Plant | 150 | Grass | Spec | 6 | Tier 2 | the master of the three starters |
| Overheat | 140 | Fire | Spec | 60 | historical TM | Mt. Chimney and Team Magma |
| Sky Attack | 140 | Flying | Phys | 43 | historical TM | Winona and Fortree |
| Psycho Boost | 140 | Psychic | Spec | 4 | Tier 2 | Deoxys and the Mossdeep Space Center |
| Fire Blast | 120 | Fire | Spec | 131 | historical TM | volcanic Hoenn |
| Solar Beam | 120 | Grass | Spec | 214 | historical TM | Groudon's harsh sunlight |
| Double-Edge | 120 | Normal | Phys | 479 | historical TM | a contest staple |
| Hydro Pump | 120 | Water | Spec | 118 | Tier 2 | Sootopolis |
| Heat Wave | 100 | Fire | Spec | 97 | Tier 2 | Mt. Chimney |
| Meteor Mash | 100 | Steel | Phys | 7 | Tier 2 | Meteor Falls and Metagross -- Steven's move to give |
| Flamethrower | 95 | Fire | Spec | 142 | historical TM | volcanic Hoenn |
| Muddy Water | 95 | Water | Spec | 70 | Tier 2 | the Hoenn sea |
| Take Down | 90 | Normal | Phys | 454 | historical TM | a contest staple |
| Uproar | 90 | Normal | Spec | 243 | Tier 2 | Loudred and the contest circuit |
| Leaf Blade | 90 | Grass | Phys | 22 | Tier 2 | Sceptile |

**Ordinary — common currency: 10**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Fire Punch | 75 | Fire | Phys | 135 | Emerald tutor | Mt. Chimney |
| Bubble Beam | 65 | Water | Spec | 96 | historical TM | the sea region |
| Brine | 65 | Water | Spec | 83 | historical TM | the sea region |
| Silver Wind | 60 | Bug | Spec | 46 | historical TM | Beautifly and the contest circuit |
| Water Gun | 40 | Water | Spec | 128 | historical TM | the sea region |
| Dragon Rage | 1 | Dragon | Spec | 33 | historical TM | Meteor Falls and the Bagon line |
| Skill Swap | — | Psychic | Stat | 103 | historical TM | Mossdeep, Tate and Liza |
| Torment | — | Dark | Stat | 142 | historical TM | Hoenn's own |
| Snatch | — | Dark | Stat | 116 | historical TM | Hoenn's own |
| Recycle | — | Normal | Stat | 86 | historical TM | Hoenn's own |


## Sinnoh — 35 moves

*Mountains, snow, myth and heavy industry.*

**Signature — rare goods, late: 21**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Giga Impact | 150 | Normal | Phys | 352 | historical TM | Sinnoh's own |
| Head Smash | 150 | Rock | Phys | 28 | Tier 2 | Rampardos from Oreburgh's mine |
| Rock Wrecker | 150 | Rock | Phys | 3 | Tier 2 | Rhyperior and Iron Island |
| Last Resort | 140 | Normal | Phys | 88 | Tier 2 | Sinnoh's own |
| Leaf Storm | 140 | Grass | Spec | 59 | Tier 2 | Eterna Forest |
| Blizzard | 120 | Ice | Spec | 196 | historical TM | Snowpoint and Route 217 |
| Focus Blast | 120 | Fighting | Spec | 156 | historical TM | Sinnoh's own |
| Close Combat | 120 | Fighting | Phys | 65 | Tier 2 | Maylene at Veilstone |
| Flare Blitz | 120 | Fire | Phys | 48 | Tier 2 | Infernape |
| Brave Bird | 120 | Flying | Phys | 38 | Tier 2 | Staraptor |
| Wring Out | 120 | Normal | Spec | 28 | Tier 2 | Sinnoh's own |
| Wood Hammer | 120 | Grass | Phys | 6 | Tier 2 | Torterra |
| Seed Flare | 120 | Grass | Spec | 2 | Tier 2 | Shaymin at Flower Paradise |
| Stone Edge | 100 | Rock | Phys | 142 | historical TM | Mt. Coronet |
| Skull Bash | 100 | Normal | Phys | 113 | historical TM | mountain country |
| Hammer Arm | 100 | Fighting | Phys | 40 | Tier 2 | Veilstone |
| Dragon Rush | 100 | Dragon | Phys | 28 | Tier 2 | Garchomp and Cynthia's shadow |
| Ice Beam | 95 | Ice | Spec | 220 | historical TM | Snowpoint |
| Aqua Tail | 90 | Water | Phys | 110 | Tier 2 | the Pastoria marsh |
| Bug Buzz | 90 | Bug | Spec | 47 | Tier 2 | Eterna Forest |
| Aura Sphere | 90 | Fighting | Spec | 29 | Tier 2 | Riley and Iron Island -- Riley's move to give |

**Ordinary — common currency: 14**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Razor Wind | 80 | Normal | Spec | 51 | historical TM | Mt. Coronet's winds |
| Rock Slide | 75 | Rock | Phys | 253 | Emerald tutor | Mt. Coronet's rockfalls |
| Ice Punch | 75 | Ice | Phys | 150 | Emerald tutor | Snowpoint |
| Pluck | 60 | Flying | Phys | 56 | historical TM | Sinnoh's own |
| Swift | 60 | Normal | Spec | 360 | historical TM | Sinnoh's myth of the heavens |
| Frost Breath | 40 | Ice | Spec | 24 | historical TM | the snow country |
| Gyro Ball | 1 | Steel | Phys | 68 | historical TM | Iron Island |
| Fling | 1 | Dark | Phys | 267 | historical TM | Sinnoh's own |
| Grass Knot | 1 | Grass | Spec | 217 | historical TM | Sinnoh's own |
| Natural Gift | 1 | Normal | Phys | 494 | historical TM | the berry culture |
| Rock Polish | — | Rock | Stat | 78 | historical TM | Mt. Coronet |
| Embargo | — | Dark | Stat | 67 | historical TM | Sinnoh's own |
| Defense Curl | — | Normal | Stat | 162 | historical TM | mountain country |
| Captivate | — | Normal | Stat | 440 | historical TM | Sinnoh's own |


## Unova — 26 moves

*The modern, urban, industrial region.*

**Signature — rare goods, late: 15**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Hurricane | 120 | Flying | Spec | 47 | Tier 2 | Tornadus over the plains |
| Gunk Shot | 120 | Poison | Phys | 73 | Tier 2 | Garbodor and Virbank's industry |
| Power Whip | 120 | Grass | Phys | 20 | Tier 2 | Ferrothorn in Chargestone Cave |
| Egg Bomb | 100 | Normal | Phys | 5 | historical TM | the Day Care culture |
| Inferno | 100 | Fire | Spec | 20 | Tier 2 | Unova's own |
| Fusion Flare | 100 | Fire | Spec | 2 | Tier 2 | Reshiram |
| Fusion Bolt | 100 | Electric | Phys | 2 | Tier 2 | Zekrom |
| Sludge Wave | 95 | Poison | Spec | 50 | historical TM | Virbank's industry |
| Foul Play | 95 | Dark | Phys | 94 | Tier 2 | Team Plasma's methods |
| Wild Charge | 90 | Electric | Phys | 75 | historical TM | Chargestone Cave and Nimbasa |
| Sludge Bomb | 90 | Poison | Spec | 110 | historical TM | Virbank's industry |
| Dragon Pulse | 90 | Dragon | Spec | 72 | historical TM | Opelucid, Drayden and Iris |
| Sacred Sword | 90 | Fighting | Phys | 7 | Tier 2 | the Swords of Justice |
| Hyper Voice | 90 | Normal | Spec | 123 | Tier 2 | Meloetta and Nimbasa's musicals |
| Earth Power | 90 | Ground | Spec | 139 | Tier 2 | the Desert Resort |

**Ordinary — common currency: 11**

| Move | Power | Type | Cat | Learners | Source | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| Tri Attack | 80 | Normal | Spec | 44 | historical TM | Klink and Genesect, Unova's machine Pokemon |
| Sky Drop | 60 | Flying | Phys | 14 | historical TM | Unova's own |
| Echoed Voice | 40 | Normal | Spec | 157 | historical TM | Unova's own |
| Mega Drain | 40 | Grass | Spec | 71 | historical TM | Pinwheel Forest |
| Rage | 20 | Normal | Phys | 172 | historical TM | a plain move for a plain teacher |
| Bide | 1 | Normal | Phys | 193 | historical TM | a plain move for a plain teacher |
| Psywave | 1 | Psychic | Spec | 52 | historical TM | a plain move for a plain teacher |
| Ally Switch | — | Psychic | Stat | 123 | historical TM | Unova's own |
| Telekinesis | — | Psychic | Stat | 121 | historical TM | Unova's own |
| Quash | — | Dark | Stat | 18 | historical TM | Unova's own |
| Thunder Wave | — | Electric | Stat | 196 | Emerald tutor | Elesa at Nimbasa |

## Still to design

- Where each tutor stands, how many moves it carries, and which are named-character
  events rather than tutors.
- The progression schedule: which moves open when. This is how the roster is paced,
  not geography.
- Prices, and which trade goods buy the signature tier.
- Whether the signature tier's rare goods are region-specific, which is the stated
  intent: a Hoenn teacher wanting Sinnoh-mined material.

