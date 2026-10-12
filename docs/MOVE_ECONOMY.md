# Move economy: TMs, tutors and regional identity

**Status: owner-approved design, partly implemented.** The 100-TM list and the
11 HMs below are built and in the ROM. The tutor tiers are designed but **not implemented** --
tutors require NPC script data, which waits on world design.

## The intent

Moves are split into three tiers so that travelling between regions means
something mechanically, not just geographically.

1. **TMs are the generic toolkit.** Useful, moderate-power moves a player carries
   across every region to build a team through the game. The intent is no large
   power spikes; the *table* power cap of 85 is a proxy for that, not proof of it.
   See the balance caveat under Tier 1.
2. **Signature moves are tutor-only, and belong to the region that invented
   them.** Thunderbolt, Ice Beam, Flamethrower, the starter ultimates and their
   peers are not TMs. Each is taught in its home region, so Hoenn brings
   something Johto cannot.
3. **Ordinary tutors fill gaps.** Unrestricted teachers of everyday moves, freely
   placed wherever the world design wants them.

Signature moves are bought with items that are hard to get and often come from
**another region** -- a Hoenn teacher wanting Sinnoh-mined material. The regions
have only recently opened to each other, and the move economy should say so.
Signature moves trickle in during the final phase; the full list opens post-game.

This is partly a restoration rather than an invention: the starter ultimates were
already Gen 3 tutor moves in Emerald and FireRed, and Draco Meteor was a Gen 4
tutor in Diamond and Pearl.

## Tier 1: the 100 TMs (implemented)

Regions are listed in story order and stock only moves their own generation
introduced. **Johto, Kanto and Hoenn carry nineteen rather than twenty**, because
the three Fairy TMs close the list at 98-100. Every offensive Fairy move is Gen 6
or later, so under the origin rule no region could stock one and the list had no
Fairy attack at all. Fairy belongs to no region because it is new to the world,
which is the premise rather than an exception to it.

(Charm, Sweet Kiss and Moonlight are Gen 2 moves retyped to Fairy in Gen 6, so
they *are* Johto-eligible under the rule. All three are status moves and none was
ever a TM in any game, so they do not change the offence problem.)

**Power below is the resolved table value under this build's configuration**
(`B_UPDATED_MOVE_DATA = GEN_5`), not the highest number appearing in a
generation-dependent expression. An earlier version of this table was wrong for
nine of these hundred entries for exactly that reason, and for 39 of the 559
Gen 1-5 moves in the wider candidate set it was drawn from. Every error was an
overestimate. Regenerate with `python3 tools/gba/move_inventory.py`, which runs
the real preprocessor; do not read power out of the source by hand.

**The table value is not a balance verdict.** Several entries reach far higher
effective power through conditions, and a zero-power field says nothing about the
impact of setup, weather, hazards or evasion. The Effective column flags the
conditional cases. No TM exceeds 85 *table* power -- that was verified -- but
that fact alone does not establish the absence of power spikes, and the balance
classification called for in the review has not been done.


### Johto — 10 candidates, 8 teachable

| Move | Power | Type | Learners | Excluded because |
| --- | --- | --- | --- | --- |
| Zap Cannon | 120 | Electric | 90 |  |
| Outrage | 120 | Dragon | 88 |  |
| Megahorn | 120 | Bug | 26 |  |
| Iron Tail | 100 | Steel | 241 |  |
| Dynamic Punch | 100 | Fighting | 139 | already taught outside Tier 2, so it is neither origin-locked nor late |
| Future Sight | 100 | Psychic | 78 |  |
| Cross Chop | 100 | Fighting | 21 |  |
| Sacred Fire | 100 | Fire | 2 |  |
| Aeroblast | 100 | Flying | 1 | single-species |
| Sludge Bomb | 90 | Poison | 110 |  |

### Kanto — 25 candidates, 21 teachable

| Move | Power | Type | Learners | Excluded because |
| --- | --- | --- | --- | --- |
| Explosion | 250 | Normal | 71 | already taught outside Tier 2, so it is neither origin-locked nor late |
| Self-Destruct | 200 | Normal | 67 |  |
| Hyper Beam | 150 | Normal | 340 |  |
| Sky Attack | 140 | Flying | 43 |  |
| High Jump Kick | 130 | Fighting | 11 |  |
| Double-Edge | 120 | Normal | 479 | already taught outside Tier 2, so it is neither origin-locked nor late |
| Solar Beam | 120 | Grass | 214 |  |
| Blizzard | 120 | Ice | 196 |  |
| Thunder | 120 | Electric | 167 |  |
| Mega Kick | 120 | Normal | 165 | already taught outside Tier 2, so it is neither origin-locked nor late |
| Fire Blast | 120 | Fire | 131 |  |
| Hydro Pump | 120 | Water | 118 |  |
| Thrash | 120 | Normal | 74 |  |
| Petal Dance | 120 | Grass | 15 |  |
| Earthquake | 100 | Ground | 200 |  |
| Dream Eater | 100 | Psychic | 157 | already taught outside Tier 2, so it is neither origin-locked nor late |
| Skull Bash | 100 | Normal | 113 |  |
| Jump Kick | 100 | Fighting | 8 |  |
| Egg Bomb | 100 | Normal | 5 |  |
| Ice Beam | 95 | Ice | 220 |  |
| Thunderbolt | 95 | Electric | 184 |  |
| Flamethrower | 95 | Fire | 142 |  |
| Take Down | 90 | Normal | 454 |  |
| Psychic | 90 | Psychic | 164 |  |
| Crabhammer | 90 | Water | 6 |  |

### Hoenn — 17 candidates, 15 teachable

| Move | Power | Type | Learners | Excluded because |
| --- | --- | --- | --- | --- |
| Focus Punch | 150 | Fighting | 184 |  |
| Water Spout | 150 | Water | 10 |  |
| Eruption | 150 | Fire | 7 |  |
| Blast Burn | 150 | Fire | 6 |  |
| Hydro Cannon | 150 | Water | 6 |  |
| Frenzy Plant | 150 | Grass | 6 |  |
| Overheat | 140 | Fire | 60 |  |
| Psycho Boost | 140 | Psychic | 4 |  |
| Doom Desire | 140 | Steel | 1 | single-species |
| Superpower | 120 | Fighting | 115 |  |
| Volt Tackle | 120 | Electric | 3 | already taught outside Tier 2, so it is neither origin-locked nor late |
| Heat Wave | 100 | Fire | 97 |  |
| Meteor Mash | 100 | Steel | 7 |  |
| Muddy Water | 95 | Water | 70 |  |
| Uproar | 90 | Normal | 243 |  |
| Hyper Voice | 90 | Normal | 123 |  |
| Leaf Blade | 90 | Grass | 22 |  |

### Sinnoh — 28 candidates, 23 teachable

| Move | Power | Type | Learners | Excluded because |
| --- | --- | --- | --- | --- |
| Giga Impact | 150 | Normal | 352 |  |
| Head Smash | 150 | Rock | 28 |  |
| Rock Wrecker | 150 | Rock | 3 |  |
| Roar of Time | 150 | Dragon | 1 | single-species |
| Last Resort | 140 | Normal | 88 |  |
| Leaf Storm | 140 | Grass | 59 |  |
| Draco Meteor | 140 | Dragon | 31 |  |
| Focus Blast | 120 | Fighting | 156 |  |
| Gunk Shot | 120 | Poison | 73 |  |
| Close Combat | 120 | Fighting | 65 |  |
| Flare Blitz | 120 | Fire | 48 |  |
| Brave Bird | 120 | Flying | 38 |  |
| Wring Out | 120 | Normal | 28 |  |
| Power Whip | 120 | Grass | 20 |  |
| Wood Hammer | 120 | Grass | 6 |  |
| Seed Flare | 120 | Grass | 2 |  |
| Crush Grip | 120 | Normal | 1 | single-species |
| Magma Storm | 120 | Fire | 1 | single-species |
| Stone Edge | 100 | Rock | 142 |  |
| Hammer Arm | 100 | Fighting | 40 |  |
| Dragon Rush | 100 | Dragon | 28 |  |
| Spacial Rend | 100 | Dragon | 1 | single-species |
| Earth Power | 90 | Ground | 139 |  |
| Aqua Tail | 90 | Water | 110 |  |
| Dragon Pulse | 90 | Dragon | 72 |  |
| Bug Buzz | 90 | Bug | 47 |  |
| Aura Sphere | 90 | Fighting | 29 |  |
| Attack Order | 90 | Bug | 1 | single-species |

### Unova — 16 candidates, 8 teachable

| Move | Power | Type | Learners | Excluded because |
| --- | --- | --- | --- | --- |
| V-create | 180 | Fire | 1 | single-species |
| Freeze Shock | 140 | Ice | 1 | single-species |
| Ice Burn | 140 | Ice | 1 | single-species |
| Bolt Strike | 130 | Electric | 1 | single-species |
| Blue Flare | 130 | Fire | 1 | single-species |
| Hurricane | 120 | Flying | 47 |  |
| Head Charge | 120 | Normal | 1 | single-species |
| Inferno | 100 | Fire | 20 |  |
| Fusion Flare | 100 | Fire | 2 |  |
| Fusion Bolt | 100 | Electric | 2 |  |
| Psystrike | 100 | Psychic | 1 | single-species |
| Searing Shot | 100 | Fire | 1 | single-species |
| Foul Play | 95 | Dark | 94 |  |
| Sludge Wave | 95 | Poison | 50 |  |
| Wild Charge | 90 | Electric | 75 |  |
| Sacred Sword | 90 | Fighting | 7 |  |

**75 teachable candidates across five regions**, from pools of 96. Rock Climb left the Sinnoh pool when it became HM10.

The regional balance is uneven in a way the raw counts hid. **Johto is the
thinnest at eight**, but they are among the most iconic moves in the series --
Zap Cannon, Outrage, Megahorn, Cross Chop. That reads as scarcity, not poverty,
and suits the region the player passes through first.

**Unova is the problem: sixteen candidates, but only eight teachable.** Ten of
its high-power Gen 5 moves belong to single legendaries -- V-create, Freeze
Shock, Ice Burn, Blue Flare, Bolt Strike, Fusion Bolt, Fusion Flare, Psystrike,
Searing Shot, Head Charge. What is left is Hurricane, Inferno, Foul Play, Sludge
Wave, Wild Charge, Sacred Sword and two more. For the last region of the game,
that is a weak closing offer, and the power filter alone will not fix it --
Gen 5's depth is in its utility and mid-power moves, not its high-power ones.

Sinnoh is the richest at twenty-three, which fits a late region; Kanto at
twenty-one is unsurprising, since the most recognisable attacks in the series
are Gen 1's.

## Tier 3: ordinary tutors (open)

Unrestricted teachers of everyday moves, paid in the common currency. There is a
large pool to draw from and no need to decide it as a single list; load them out
per settlement as the world design calls for.

## Currency design (approved in shape, not in detail)

| Tier | Paid with |
| --- | --- |
| Ordinary tutors | A common currency earned anywhere |
| Signature tutors | Trade goods that only another region produces |

The split keeps routine move-teaching frictionless while making a signature move
a genuine expedition. Still to design: what each region produces, what each good
is called, how the player acquires it, and the exchange rates.

## Unlock timing

A handful of signature tutors become reachable in the final phase, once the
player has the cross-region access to afford them. The complete list opens after
the credits.

## Fairy offence: solved by the Fairy TM block

This was the sharpest gap in the list and is now closed. Under Gen 6 learnsets
23 species are Fairy-typed, and the TM list had no Fairy attack at all -- the
origin rule forbade one, because every offensive Fairy move is Gen 6 or later.

**Three Fairy TMs now close the list at TM98-100**: Dazzling Gleam (80, special,
98 learners), Disarming Voice (40, special, never misses, 62 learners) and
Draining Kiss (50, special, heals, 46 learners). Johto, Kanto and Hoenn each gave
up a slot to pay for them.

Six of the 23 Fairy species still reach a Fairy attack only through evolution or a
pre-evolution -- Cleffa, Igglybuff, Azurill, Mime Jr., Togepi and Togekiss -- which
is ordinary for baby forms and not a coverage failure.

The earlier plan here routed Fairy through an "early signature tutor", which was
self-contradictory: signature teaching is late and origin-locked, and a Gen 6 move
has no home region to be locked to. The TM block is the coherent answer.

## Tier 4: HMs — keep the power, control the timing (owner-approved)

**Eleven HMs, built and verified.** The eight vanilla HMs plus **Defog (HM09)**
and **Rock Climb (HM10)** for Sinnoh, and **Whirlpool (HM11)** for Johto. They are
HMs rather than TMs by owner decision, so they cost no region a slot out of its
twenty. This covers every field move the five regions need as originally built.

HMs are not covered by the TM power cap or the tutor gating, and three of them
exceed the cap outright: **Surf at 95, Fly at 90 and Rock Climb at 90**, with
Strength, Waterfall and Dive at 80. They are traversal tools the player effectively must
carry, so they deliver mid-power coverage on a schedule world design sets rather
than this economy.

**Approved policy: Surf and Fly keep their canon power, and the schedule does the
balancing.** They are series-defining moves at those values and reducing them
would read as wrong. Instead, an HM that outclasses the TM toolkit is placed late
enough in the badge order that the level curve can absorb it.

| Band | HMs | Power |
| --- | --- | --- |
| Early | Cut, Rock Smash, Flash, Defog | 50, 40, —, — |
| Mid | Strength, Waterfall, Whirlpool | 80, 80, 35 |
| Late | Surf, Fly, Rock Climb, Dive | 95, 90, 90, 80 |

The bands above are the shape the policy implies, not a placement decision.
**This makes the move economy depend on the badge and route order**, which is not
designed yet. Surf in particular is the hard case: it is traversal-critical in
every region with water, so holding it late constrains routing, and routing may
well push back. Settle the region routing, then fix the HM order against it, then
re-check this table. Until then no HM placement is decided.

## Field moves and traversal across five regions

Each region as originally built demands its own set of field moves, and the sets
are not the same. The union is **eleven moves**, against eight HM slots
(`ITEM_HM01`-`ITEM_HM08`, items 682-689, which the TM block fills up to 681).

| Region | Field moves as originally built |
| --- | --- |
| Johto (GSC) | Cut, Fly, Surf, Strength, Flash, **Whirlpool**, Waterfall |
| Kanto (RBY/FRLG) | Cut, Fly, Surf, Strength, Flash, Rock Smash, Waterfall |
| Hoenn (RSE) | Cut, Fly, Surf, Strength, Flash, Rock Smash, Waterfall, **Dive** |
| Sinnoh (DPPt) | Cut, Fly, Surf, Strength, Rock Smash, Waterfall, **Rock Climb**, **Defog** |
| Unova (BW/B2W2) | Cut, Fly, Surf, Strength, Waterfall, Dive |

Johto also uses Rock Smash, which is a TM in GSC and an HM in HGSS; HGSS adds
Rock Climb. Flash is an HM in Gen 1-3 and a TM from Gen 4, so Sinnoh and Unova
expect it without a slot.

### The eight-slot ceiling is not a traversal ceiling

Field moves key on the **move**, not on the HM item. `gFieldMoveInfo` in
`game/src/field_move.c` is indexed by a `FieldMove` enum and carries a `moveID`;
`field_control_avatar.c` and the party menu ask whether a party member knows that
move and whether it is unlocked. Nothing asks whether the player owns an HM.

So a traversal move can be delivered as a TM or a tutor move and still work in the
field. Eight HMs do not cap traversal at eight moves.

### What the engine already has

| Move | Status in this build |
| --- | --- |
| Cut, Fly, Surf, Strength, Flash, Rock Smash, Waterfall, Dive | HM01-HM08, vanilla |
| **Defog** | **HM09 — built.** `OW_DEFOG_FIELD_MOVE` now TRUE |
| **Rock Climb** | **HM10 — built.** `OW_ROCK_CLIMB_FIELD_MOVE` now TRUE |
| **Whirlpool** | **HM11 — built.** `MB_WHIRLPOOL`, `FLDEFF_USE_WHIRLPOOL` and the hooks are ours; `OW_WHIRLPOOL_FIELD_MOVE` TRUE |

All eleven are now in the build.

### What adding HM09 and HM10 took

The engine reserved exactly eight HM ids, `ITEM_HM01`-`ITEM_HM08` at 682-689,
butted directly against `ITEM_OVAL_CHARM` at 690. Everything above that is
generic: `NUM_HIDDEN_MACHINES` derives from `FOREACH_HM`, `GetItemTMHMIndex` is a
switch generated from the same macro, and `gTMHMItemMoveIds` is indexed by
`enum TMHMIndex`. Nothing range-checks an HM item id.

- `FOREACH_HM` gained `F(DEFOG)` and `F(ROCK_CLIMB)`.
- `ITEM_HM09`/`ITEM_HM10` took 690/691, and **every item from 690 up shifted by
  two**. Enum members must be declared before the `ENUM_HM` zip consumes them, so
  appending them after the charms did not compile. Renumbering keeps the HM block
  contiguous, and no player save exists yet to invalidate.
- `BAG_TMHM_COUNT` 108 -> 111 across both changes; three entries added to
  `src/data/items.h`. Measured save cost: `SaveBlock1` 15,660 -> 15,672 bytes,
  leaving 200 of 15,872 free.
- Both field-move configs flipped to TRUE.
- **A latent bug fixed.** `src/item_menu.c` formatted the HM number with a fixed
  width of one digit, so HM10 rendered as `HM0`. TMs already scaled their width;
  HMs never needed to before. Now `NUM_HIDDEN_MACHINES >= 10 ? 2 : 1`.

### Where the three would sit

Each is from its own region's generation, so the origin rule holds without an
exception:

| Move | Gen | Region | Power | Learners | Note |
| --- | --- | --- | --- | --- | --- |
| Whirlpool | 2 | Johto | 35 spec | 131 | Fits the TM cap; needs engine support built |
| Defog | 4 | Sinnoh | status | 113 | Fits cleanly; config flip only |
| Rock Climb | 4 | Sinnoh | 90 phys | 112 | **Exceeds the 85 TM cap**, and Normal is already the overweight type |

Rock Climb at 90 is the same problem as Surf and Fly, and takes the same answer:
it is a traversal move whose power is a consequence, not a balance choice, so it
belongs under the Tier 4 policy rather than inside the TM cap.

### Whirlpool, built

Whirlpool had no engine support: no metatile behavior, no `FieldMove` entry, no
field effect. It was built rather than designed around, because the alternative --
re-cutting Johto's whirlpools as dive sites -- means producing new underwater maps,
and that is deferred map production. Building the field move is bounded engine work.

**Waterfall is the model.** Both are used from the surfing state and test the tile
ahead, and both ride onto it slowly. Whirlpool differs in having no fixed
direction, so the ride uses the player's current facing instead of `DIR_NORTH`,
and it continues through consecutive whirlpool tiles the same way Waterfall
continues up a fall.

**No new art.** It reuses `FLDEFF_FIELD_MOVE_SHOW_MON` and ordinary walk movement,
so nothing in it is blocked on asset production.

What was added: `MB_WHIRLPOOL` (surfable) and `MetatileBehavior_IsWhirlpool`;
`FLDEFF_USE_WHIRLPOOL` with a five-state task; `FIELD_MOVE_WHIRLPOOL` and its
`gFieldMoveInfo` entry behind `OW_WHIRLPOOL_FIELD_MOVE`; `SetUpFieldMove_Whirlpool`
and an overworld trigger, both gated on the player surfing; the event scripts and
their text; and `ITEM_HM11`, which shifted items 692-875 up by one again.

**Two caveats, neither cosmetic.**

1. **No map uses it.** No tileset assigns `MB_WHIRLPOOL`, so no whirlpool exists in
   the world yet. The move works; nothing calls on it.
2. **The badge gate is a placeholder.** The field move unlocks on
   `FLAG_BADGE08_GET`, copied from the vanilla eight-badge assumption. Apocrypha
   has twenty badges and no settled badge order. This must be revisited together
   with the Tier 4 HM timing policy; it is not a considered choice.

## What is not decided

- Which signature moves each region actually teaches, from the candidate pools.
- The trade goods: names, sources, acquisition, rates.
- Where tutors stand, and their dialogue. Note that tutor *data* is not blocked on
  this: `special_movesets.json` has an `extraTutors` list that the generator merges
  with script-discovered tutors, so teachable sets can be prepared before any NPC
  exists. Only the player-facing interaction needs map work. The earlier claim that
  all tutor work is blocked on map scripts was too absolute.
- Ordinary tutor rosters per settlement.
- **Unova's signature roster below the power floor.** Approved direction: the 86
  power filter is not the right instrument for Gen 5, whose depth is in utility and
  mid-power moves, so Unova's pool is to be widened by merit rather than by table
  power. Eight teachable candidates is too thin for the final region. The wider
  pool has not been selected yet.
- Where the 100 TMs are placed in the world. **None is obtainable in play yet.**

