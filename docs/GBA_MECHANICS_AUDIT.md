# GBA mechanics audit

Status: 2026-09-11. Source audit complete for the configuration surfaces below;
**the final rules profile is not approved or fully implemented**. Twenty-five settings
now record approved scope, including the Gen 4–5 per-move physical/special split,
Gen 5 species base stats, abilities, move data and experience yields, and ORAS learnsets. Most generation-dependent rules remain
upstream defaults pending the remaining individual rule choices. No maps, save redesign,
custom type assignments, or campaign gates were implemented in this task.

## Finding and authority

The pinned expansion defines `GEN_LATEST` as `GEN_9`, not `GEN_CHAMPIONS`.
Choosing GBA graphics did not automatically choose Emerald battle rules. The
existing foundation's phrase “classic” does not settle every difference between
Emerald, HGSS and B2W2. Do not globally change `GEN_LATEST`: it also controls
species data, breeding, items, presentation and later-species behavior.

[Foundation decisions](FOUNDATION_DECISIONS.md) own approved scope. This document
owns the audit and proposed choices, not new narrative canon. A setting that is
currently enabled is not automatically approved. The machine-readable
[inventory](../gba/evidence/mechanics-config-inventory.json) records declarations
from every config header except the separately qualified species roster. It is a
lookup/drift record, not proof every conditional is active or every feature works.
Read this document first; do not preload the full inventory into agent context.

## Applied within existing scope

[Mechanics profile](../gba/mechanics-profile.json) records exact old/new values and
reasons; [the patch](../gba/mechanics-profile.patch) preserves changes outside the
submodule. These settings do not settle the broader generation choice.

| Change | Player-facing result | Relevant source |
| --- | --- | --- |
| Experience selectors at `GEN_5`, classic held-item sharing retained | Owner-approved M02 reward scaling, division and bonuses; see package below. | `battle_script_commands.c`, `config/item.h` |
| `B_PHYSICAL_SPECIAL_SPLIT = GEN_5` | Owner-approved per-move categories; Fire Punch is physical and Flamethrower is special. | `battle_util.c:GetBattleMoveCategory` |
| `P_UPDATED_EXP_YIELDS = GEN_5` | Owner-approved M03d yields. About 190 roster species are worth roughly 10% less experience, completing the Gen 5 experience package begun in M02. | `data/pokemon/species_info/*.h` |
| `P_LVL_UP_LEARNSETS = GEN_6` | Owner-approved M03c learnsets. ORAS level-up movesets, chosen over Gen 5 because Gen 5 learnsets leave 22 of 23 Fairy-typed roster species unable to attack with their own type. Mr. Mime is given Dazzling Gleam at 44. | `data/pokemon/level_up_learnsets/gen_6.h` |
| `B_UPDATED_MOVE_DATA = GEN_5` | Owner-approved M03c move data. 133 moves change: the big special attacks and several setup moves return to their higher Gen 5 power and PP, and a few later buffs revert. | `data/moves_info.h` |
| `P_UPDATED_ABILITIES = GEN_5` | Owner-approved M03b ability sets, with eighteen pinned exceptions. Weather setters, Neutralizing Gas and Sharpness are kept; Gengar and the Litwick line keep their present-day abilities rather than the Gen 5 restorations. | `data/pokemon/species_info/*.h` |
| `P_UPDATED_STATS = GEN_5` | Owner-approved M03a base stats; every species in the Gen 1-5 roster uses its Black 2 / White 2 spread. Sylveon and retained Mega forms keep their canonical later stats. | `data/pokemon/species_info/*.h` |
| `B_AFFECTION_MECHANICS = FALSE` | Friendship no longer grants affection-based battle advantages or its extra experience bonus; ordinary friendship/evolution remain. | `battle_util.c`, `battle_script_commands.c` |
| `B_RUN_TRAINER_BATTLE = FALSE` | Cannot flee a trainer battle. | `battle_main.c` |
| `B_CATCH_SWAP_INTO_PARTY = GEN_5` | When the party is full, catches follow the PC route without the newer party-swap prompt. | `battle_script_commands.c` |
| `B_OBEDIENCE_MECHANICS = GEN_5` | Retain classic outsider-based obedience rather than applying modern restrictions to the player's own catches. Twenty-badge thresholds still need design. | `battle_util.c` |
| `B_TRAINERS_KNOCK_OFF_ITEMS = FALSE` | Restore upstream's vanilla restriction on trainer item theft/swapping; this does not disable Knock Off's normal damage effect. | `battle_script_commands.c` |
| `B_EXTRAPOLATED_MOVE_FLAGS = FALSE` | Do not add speculative, unofficial properties to moves. | `data/moves_info.h` |
| `P_UPDATED_TYPES`, `B_UPDATED_MOVE_TYPES`, `B_UPDATED_TYPE_MATCHUPS = GEN_6` | Explicit Fairy-era species/move retyping and standard chart, including Steel's loss of Ghost/Dark resistance. | `data/pokemon/species_info/`, `data/moves_info.h`, `data/types_info.h` |
| `OW_PC_HEAL`, `OW_PC_MOVE_ORDER`, `OW_PC_PRESS_B = GEN_3` | Deposits heal; Emerald PC menu order and held-cursor B-button behavior. | `pokemon_storage_system.c` |

Generation selectors above express individual behavior thresholds, not an approved
global Gen 5 or Gen 6 battle profile. Production still has fourteen boxes.

## Decisions to resolve in order

Recommendations here are proposals, not applied changes.

| ID | Choice and current behavior | Proposed direction / consequence |
| --- | --- | --- |
| M01 | **Approved 2026-09-11:** Gen 4–5 per-move physical/special split. `B_PHYSICAL_SPECIAL_SPLIT = GEN_5` is applied. | Closed for move categories. Other Gen 4/5 differences remain separate choices; no blanket B2W2 preset approved. |
| M02 | **Approved 2026-09-11:** Gen 5 scaled rewards, participant division, held-item Exp. Share, trainer bonus; no catch EXP or delayed-evolution bonus. | Applied. Species yields and five-region pacing remain separate work. |
| M03a | **Approved and applied 2026-09-11:** Gen 5 base stats for the Gen 1-5 roster; Sylveon and retained Mega forms keep canonical later stats. `P_UPDATED_STATS = GEN_5`. | Closed for base stats. Abilities, learnsets, move data and species experience yields are still inherited. |
| M03b | **Approved and applied 2026-09-11:** Gen 5 ability sets for the Gen 1-5 roster with eighteen owner-chosen exceptions. `P_UPDATED_ABILITIES = GEN_5`. | Closed for which abilities each species has. How the player *obtains* Hidden Abilities is still open. |
| M03c | **Approved and applied 2026-09-11:** ORAS level-up learnsets and Gen 5 move power, accuracy and PP. `P_LVL_UP_LEARNSETS = GEN_6`, `B_UPDATED_MOVE_DATA = GEN_5`. | Closed for learnsets and move data. `B_UPDATED_MOVE_FLAGS`, species experience yields and breeding revisions are still inherited. The vanilla TM/HM list is a separate open gap. |
| M03d | **Approved and applied 2026-09-12:** Gen 5 species experience yields. `P_UPDATED_EXP_YIELDS = GEN_5`. No exception pin was needed. | Closed. The Gen 5 experience package is now complete: rules from M02, yields from M03d. |
| M03e | Species/moves: move flags, EV yields, base friendship, egg groups and breeding revisions remain inherited (base stats, abilities, learnsets, move data and experience yields are settled by M03a-M03d). Roster restrictions do not restrict all moves or abilities. | Use one explicit reference for ordinary species and moves, with a small documented Fairy/Mega supplement. Decide how Hidden Abilities are obtained, and availability of later moves/items; M03c already hit the Fairy-stranding trap once; re-run that check for any move or TM change. |
| M04 | **Approved and applied 2026-09-12, rebalanced 2026-09-13:** 100 TMs, origin-matched and capped at 85 power; 19/19/19/20/20 by region plus a 3-move Fairy block. Signature moves excluded by design. TMs stay **single-use**. **HMs expanded to 11** (2026-09-13): Defog, Rock Climb and Whirlpool added for traversal. | Closed for the TM list. Tutors, trade goods, TM placement and the item economy are open; see MOVE_ECONOMY.md. |
| M04b | Convenience: HM forgetting is restricted. Linking Cord and direct-use trade-evolution alternatives already exist in species tables. | Prefer retaining solo evolution alternatives for a living Dex, but get a decision before distributing those items. TM reuse is settled by M04 (single-use). |
| M05 | Presentation: faster HP/EXP bars, move details, last-ball shortcut, effectiveness hints, indoor running and day/night tint are enabled. DexNav, followers, HGSS Dex and overworld wild spawns are disabled. | Keep useful speed improvements provisionally; review information hints and optional menus as a compact package. Do not treat GBA presentation as a request to disable every convenience. |
| M06 | Mega rule generation, exact eligible Pokemon and unlock event remain unspecified. Terra/Shadow matchups, moves and type-slot assignments are also unspecified. | Keep existing Mega engine/data; author its late-game item distribution/gates later. Owner supplies custom-type creative choices. Never substitute Terastallization. |

The owner approved M01, M02 and M03a-M03c on 2026-09-11 and M03d on 2026-09-12; all six are
applied and tested. The TM/HM list, Hidden Ability access, move flags and breeding are the
remaining open decisions. See the continuation handoff before starting another task.

## Experience package (M02, approved and applied)

`B_EXP_CATCH`, `B_SPLIT_EXP`, `B_SCALED_EXP`, `B_TRAINER_EXP_MULTIPLIER`
and `B_UNEVOLVED_EXP_MULTIPLIER` are pinned to `GEN_5`.
`I_EXP_SHARE_ITEM = GEN_5` and `I_EXP_SHARE_FLAG = 0` are retained and checked
by the profile inventory. Lower-level recipients catch up faster; overleveled
recipients earn less. This scales rewards, not enemy or player levels.
No catch EXP or bonus for delaying evolution; no automatic whole-party EXP.
Species EXP yields, reward item availability and five-region balancing remain
separate decisions. The profile now checks twenty-five settings, including two
unchanged Exp. Share settings; twenty-three differ from upstream.

## Species stats (M03a, approved and applied)

Owner approved on 2026-09-11: Gen 5 / Black 2-White 2 base stats for the Gen 1-5
roster, retaining canonical later stats for Sylveon and Mega forms. No custom
buffs or nerfs. `P_UPDATED_STATS = GEN_5` is applied and tested.

Of 191 `P_UPDATED_STATS` selectors in the species tables, 76 now resolve to the
B2W2 value; the other 115 are unchanged. The 113 selectors gated on `>= GEN_2`
stay on their post-Gen-1 branch, so `GEN_5` does **not** roll species back to the
Gen 1 combined Special stat: Charizard keeps 109 Sp. Atk and Gengar 75 Sp. Def.
Shared stat macros were traced individually, including `PIKACHU_DEFENSE`,
`ALAKAZAM_SP_DEF`, `WIGGLYTUFF_SP_ATK`, `VICTREEBEL_SP_DEF` and `EEVEE_SP_ATK`.

Exceptions checked rather than assumed. Sylveon has no selector at all; its
95/65/65/60/110/130 spread is already canonical. All 98 Mega entries were
scanned, and **Mega Alakazam is the only retained Mega the selector reached**
(its Sp. Def rose from 95 to 105 in Gen 7), so it is pinned to 105 directly in
`src/data/pokemon/species_info/gen_1_families.h`. The other Gen 6+ entries the
selector touches - Aegislash, Zacian, Zamazenta and the Gigantamax forms - are
compiled out by the roster profile. Cresselia is the reverse case: it was
*lowered* after Gen 5, so it keeps 120 Def / 130 Sp. Def.

This is a resolved-selector audit plus sampled runtime assertions, not an
exhaustive per-species historical database audit. Abilities, learnsets, move
power, Hidden Ability availability and species experience yields remain separate
choices. See [the continuation handoff](AGENT_HANDOFF.md) for exact next steps.

## Species abilities (M03b, approved and applied)

Owner approved on 2026-09-11: Gen 5 / Black 2-White 2 ability sets for the Gen 1-5
roster, with a short list of owner-chosen exceptions. `P_UPDATED_ABILITIES = GEN_5`
is applied and tested.

Of 134 `P_UPDATED_ABILITIES` selectors, 91 are gated on `>= GEN_4` and are
unaffected, so the Gen 4/5-era ability updates are retained. The remaining 43 are
affected: 25 take the B2W2 set and 18 are pinned as exceptions.

**The switch runs in both directions**, which is easy to get wrong. Gen 5 removes
later additions, but it also *restores* abilities that were removed afterwards --
Gengar's Levitate, the Litwick line's hidden Shadow Tag, Zapdos's Lightning Rod,
the legendary beasts' absorbing hidden abilities, the Piplup line's Defiant,
Shiftry's Early Bird and the Venipede line's Quick Feet.

Owner exceptions, pinned directly in `src/data/pokemon/species_info/` with a
comment naming M03b:

| Direction | Species | Result |
| --- | --- | --- |
| Kept present-day | Torkoal, Pelipper, Gigalith, Vanilluxe | The four weather setters keep Drought, Drizzle, Sand Stream and Snow Warning. |
| Kept present-day | Wingull, Roggenrola, Boldore, Vanillite, Vanillish, Cubchoo, Beartic | Same-line members kept modern so no evolution line is half Gen 5 and half present-day. Reversible per species. |
| Kept present-day | Koffing, Weezing | Neutralizing Gas and Stench retained. |
| Kept present-day | Gallade | Sharpness retained. |
| Overridden to present-day | Gengar | Cursed Body, **not** the Gen 5 restoration of Levitate. |
| Overridden to present-day | Litwick, Lampent, Chandelure | Infiltrator, **not** the Gen 5 restoration of hidden Shadow Tag. |

Where Gen 5 restores something and the owner did not override it, the Gen 5
version stands: Zapdos keeps Lightning Rod and Raikou, Entei and Suicune keep
Volt Absorb, Flash Fire and Water Absorb.

No Mega form, no Gigantamax form and not Sylveon carries a `P_UPDATED_ABILITIES`
selector, so M03b needed no form exception. Mega Gengar has its own entry and does
not read the pinned `GENGAR_ABILITIES` macro.

Two consequences to carry forward. The weather setters change battle pacing, and
gym leader and trainer teams have not been designed around them. Several pinned
abilities are Hidden Abilities, and **how the player obtains a Hidden Ability is
still an open question** -- pinning one does not make it reachable in play.

## Species experience yields (M03d, approved and applied)

Owner approved on 2026-09-12: Gen 5 / Black 2-White 2 experience yields.
`P_UPDATED_EXP_YIELDS = GEN_5` is applied and tested.

Of 814 selectors, 514 are gated on `>= GEN_4` or `>= GEN_5` and are unaffected;
300 fall back to the B2W2 value. That reaches about 190 roster species, uniformly:
the median and mean Gen 5 / present-day ratio are both **0.90**. Clefable
242 -> 213, Nidoking 253 -> 223, Alakazam 250 -> 221, Gengar 250 -> 225 (through
the shared `GENGAR_EXP_YIELD` macro), Krookodile 260 -> 229.

**This completes the Gen 5 experience package.** M02 set the rules -- participants
divide the reward, gains scale with the level difference, trainers pay a 1.5x
bonus, catching awards nothing, Exp. Share stays a held item. M03d sets the yields
those rules multiply. Both now come from the same published game.

**No exception pin was needed, the first M03 decision where that is true.**
Sylveon's yield is a flat literal. All 35 Mega entries carrying a selector fall
back to a genuine Gen 6 or Gen 7 figure rather than a pre-Mega placeholder --
Mega Venusaur 313 -> 281, Mega Alakazam 300 -> 266. Mega Alakazam takes its Gen 6
number because its Gen 7 yield rise came with the Sp. Def change that M03a pinned
for base stats only; the two are separate fields and need not match. No species
resolves to an `expYield` of 0.

Pacing is not settled by this. The level curve authored for trainers and wild
encounters affects progression far more, and none of it is written yet.

## Learnsets and move data (M03c, approved and applied)

Owner approved on 2026-09-11: ORAS level-up learnsets and Gen 5 move power,
accuracy and PP. `P_LVL_UP_LEARNSETS = GEN_6` and `B_UPDATED_MOVE_DATA = GEN_5`
are applied and tested.

**Why learnsets are not `GEN_5`.** Level-up learnsets are a whole-file swap in
`src/pokemon.c`, not a per-species selector. The roster has 23 Fairy-typed
species. Resolved against each candidate file:

| Setting | Fairy species that learn no Fairy attacking move |
| --- | --- |
| `GEN_5` (B2W2) | 22 of 23 -- only Sylveon, which post-dates B2W2 and falls back to Gen 6 data |
| `GEN_6` (ORAS) | 7 of 23, reduced to 6 by the owner exception below |
| `GEN_7` (USUM) | 7 of 23 |
| `GEN_9` (SV) | 2 of 23 |

TMs cannot compensate. `include/constants/tms_hms.h` still holds the vanilla
Emerald 50 TMs and 8 HMs, which contain no Fairy move -- and no Gen 4 or Gen 5
move either. **That TM gap is pre-existing and still open**; it is not something
M03c fixed or created.

The six species left at `GEN_6` are Azurill, Cleffa, Igglybuff, Mime Jr., Togepi
and Togekiss. The first five are babies that evolve into a species that has a
Fairy move; Togekiss has none of its own but carries Fairy Wind up from Togetic,
which learns it at 14. Mr. Mime was the only final-stage species genuinely
stranded, and the owner approved giving it **Dazzling Gleam at level 44** --
the level it learns that move in the present-day games -- pinned in
`src/data/pokemon/level_up_learnsets/gen_6.h`.

**Move data.** 133 moves change across 169 selectors, mostly power (81), PP (37)
and accuracy (19). Gen 6 toned down the staple special attacks and Gen 5 restores
them: Flamethrower, Surf, Ice Beam and Thunderbolt return to 95 power; Hydro
Pump, Blizzard, Thunder and Fire Blast to 120. Swords Dance returns to 30 PP,
Growth to 40, and Thunder Wave to 100% accuracy. It is not a one-way power
increase -- later buffs revert too, so Vine Whip drops to 35, Pin Missile to 14
and Skull Bash to 100.

Two checks before applying it. No selector's Gen 5 branch resolves to zero power,
accuracy or PP, so no move is left broken. And no Fairy move carries a move-data
selector that `GEN_5` reaches -- Moonblast, Dazzling Gleam, Play Rough, Disarming
Voice, Draining Kiss and Fairy Wind are plain literals.

`B_UPDATED_MOVE_FLAGS` is **deliberately left at `GEN_LATEST`** and is a separate
open choice. Setting it to `GEN_5` would, among other things, stop sound moves
bypassing Substitute.

## Egg moves and breeding (reviewed; breeding still OPEN)

**Egg moves are preserved and were never a choice.** `src/data/pokemon/egg_moves.h`
is a single file included unconditionally; the expansion offers no per-generation
egg-move file set the way it does for level-up learnsets. So the egg-move pool is
the present-day (Gen 9-era) data, one step more modern than the rest of the
species data, and no M03 decision touched it. The only generation references
inside the file are `P_GEN_n_CROSS_EVOS` guards, which gate which baby Pokemon
exist, not which moveset generation is used.

**Safety review, 2026-09-11** ([evidence](../gba/evidence/egg-move-audit.json)).
The owner accepts a move being obtainable only by breeding, in the spirit of Volt
Tackle; the concern was whether a modern egg move could unbalance the game once
obtained. It cannot, on this roster:

- 34 post-Gen-5 moves appear in the egg pool for compiled-in species. 15 of those
  are obtainable no other way. **All 15 are Gen 6 or Gen 7 -- nothing from Gen 8
  or Gen 9 is egg-exclusive here.**
- The strongest is Burn Up at 130 power, which removes the user's own Fire type
  after use and so is self-limiting. Everything else tops out at an ordinary
  95-power attack. First Impression is +2 priority but only on the user's first
  turn out. Power Trip is the only scaling-damage effect and needs setup turns.
- Strength Sap, on the Oddish, Bellsprout and Hoppip lines, is the most impactful
  non-damaging one: it lowers the target's Attack and heals the user by that
  amount. Strong, but a fair Gen 7 move.
- Every Gen 8/9 problem move was screened for. Population Bomb, Rage Fist,
  Surging Strikes, Wicked Blow, Shed Tail, Salt Curse and the rest are absent from
  the file entirely. **Last Respects** -- the one genuinely game-warping egg move
  present -- sits behind `#if P_HISUIAN_FORMS` on Basculin White-Striped, which
  the roster profile compiles out, so neither species nor move can be reached.

Beware a false shortcut here: filtering species by name suffix is not enough.
Sirfetch'd, Ursaluna and Basculin White-Striped carry no form suffix but are all
compiled out by config. Resolve `species_enabled.h` and walk the `#if` guards.

**Breeding and inheritance rules are OPEN and fully inherited at Gen 9.** None of
these has been chosen, and they are not implied by any M03 decision:

| Setting | Currently | What it governs |
| --- | --- | --- |
| `P_MOVE_INHERITANCE` | `GEN_LATEST` | The order in which an Egg inherits level-up, Egg and TM moves from its parents. |
| `P_EGG_MOVE_TRANSFER` | `GEN_LATEST` | Gen 8 same-species Egg-move transfer in the Day Care, plus the Gen 9 Mirror Herb. |
| `P_ABILITY_INHERITANCE` | `GEN_LATEST` | Chance of passing down a regular or Hidden Ability. Interacts with the still-open Hidden Ability question. |
| `P_NATURE_INHERITANCE` | `GEN_LATEST` | Everstone behaviour and whether Nature passes at 100%. |
| `P_BALL_INHERITANCE` | `GEN_LATEST` | Whether an Egg inherits the mother's or either parent's Poke Ball. |
| `P_EGG_HATCH_LEVEL` | `GEN_LATEST` | Whether Eggs hatch at level 1 or level 5. |
| `P_INCENSE_BREEDING` | `GEN_LATEST` | Whether baby Pokemon still require a parent to hold an Incense. |

`P_INCENSE_BREEDING` is the one with world-facing consequences: at the Gen 9
default, Incense items are no longer needed to breed baby Pokemon, which changes
what those items are for. Take this as its own decision when convenient; it does
not block species experience yields or the TM/HM list.

**Reserved move pool (owner idea, 2026-09-12).** Rather than discard the powerful
moves the review screened for, the owner may build a deliberately difficult
late-game path that grants a few as a reward. Exclusivity is fine -- the model is
Volt Tackle -- the requirement is that a granted move must not unbalance the game.
This is expected to be designed **together with** the breeding rules above, and the
engine agrees: `game/src/daycare.c` already holds `sBreedingSpecialMoveItemTable`,
a one-row table mapping offspring plus held item to a granted move, which is
exactly the hook to extend. The catalogue is in
[RESERVED_MOVE_POOL.md](RESERVED_MOVE_POOL.md); note especially that 83 of the 255
unreachable moves are a **TM gap rather than reward material** and belong to the
open TM/HM decision instead.

## TM and HM list (M04, approved and applied)

Owner direction of 2026-09-12 replaced the first attempt. TMs are the **generic
toolkit**; signature moves belong to **regional tutors**. The full design is in
[MOVE_ECONOMY.md](MOVE_ECONOMY.md); this section records only what is built.

**100 TMs, origin-matched, rebalanced 2026-09-13.** Each region stocks only moves
its own generation introduced, capped at 85 power, ordered Johto, Kanto, Hoenn,
Sinnoh, Unova. Johto, Kanto and Hoenn carry nineteen rather than twenty: three
Fairy TMs close the list at 98-100, because every offensive Fairy move is Gen 6 or
later and the origin rule left the list with no Fairy attack at all. Charm, Sweet
Kiss and Moonlight are Gen 2 moves retyped to Fairy and are Johto-eligible, but
all three are status and none was ever a TM. TMs remain **single-use**; `I_REUSABLE_TMS` is `FALSE`. All 100 were validated for
origin, power cap, HM collision and duplication. The HM list has since grown to
eleven; see the HM expansion section below.

Thunderbolt, Ice Beam, Flamethrower, Fire Blast, Blizzard, Thunder, Earthquake,
Hyper Beam, Giga Impact, Overheat, Draco Meteor and the starter ultimates are
**deliberately not TMs**. A regression test asserts each returns `ITEM_NONE` from
`GetTMHMItemIdFromMoveId`.

**The 2026-09-13 rebalance.** Measured coverage ran from Normal at ten attacking
TMs to Dragon at one and Fairy at zero, with eight of the Normal entries above
three hundred learners doing nearly the same job. Four swaps and the Fairy block
fixed it: Johto traded Frustration (Return mirrored) and Safeguard for Dragon
Breath; Kanto traded Swift and Double Team for Psybeam; Hoenn traded Secret Power
(a functional duplicate of Facade) and Torment for Dragon Claw; Sinnoh traded
Grass Knot, whose weight-variable power reaches 120, for a flat-80 Energy Ball.
Result: Normal 10 -> 7, Dragon 1 -> 3, Psychic 2 -> 3, Fairy 0 -> 3, and 41/27/32
physical/special/status -> 40/31/29. No TM exceeds 85 table power.

Two gaps were left open on purpose. **Poison stays at two** -- the only qualifying
addition is Acid Spray at 40. **Fighting reads as six attacking TMs and plays as
three**, since Seismic Toss and Counter are fixed damage and Low Kick scales on
weight; no special Fighting move at or below 85 exists in these generations except
Vacuum Wave at 40. Both would be made worse by padding.

Nine vanilla files were retargeted from the seven dropped TMs to type- and
role-matched survivors.

**Engine limits, both still binding:**

- `include/constants/items.h` reserves exactly `ITEM_TM01`-`ITEM_TM100`. The list
  fills it exactly, so adding a TM means removing one or renumbering the item
  enum. The HM expansion did exactly that renumbering, for HMs rather than TMs:
  items from 690 up shifted by three. Item ids should now be treated as frozen.
- New enum members must be declared **before** the `ENUM_TM`/`ENUM_HM` zip that
  consumes them. Appending them after the charm block compiles to
  "`ITEM_HM09` undeclared".
- A block comment placed *inside* the backslash-continued `FOREACH_TM` macro
  silently truncates it and produces errors in unrelated files.

**Save cost.** `BAG_TMHM_COUNT` 64 -> 111, which grows `SaveBlock1` by 188 bytes
(47 further `ItemSlot`s at 4 bytes each). `tools/gba/measure.py` reports
**15,672 of 15,872, leaving 200 bytes**. The three added HMs cost 12 bytes of the
212 free before them. An earlier figure of 15,588/284 in this document was
wrong: it came from a compile probe using the default ABI instead of the production
`-mabi=apcs-gnu`, which changes struct padding. **Measure with `measure.py`, not an
ad-hoc probe.**

The 176 bytes shift every later field in `SaveBlock1` -- berries, Pokeblocks, flags
and variables -- and reordering the TM list changes what saved item ids mean
(baseline TM01 was Focus Punch; it is now Protect). **Prior-save compatibility is
untested.** No real save exists yet, so the practical risk now is near zero, but
this is the moment to treat TM ids as frozen: changing them later would break
saves for real. PC boxes are in sectors 5-13 and are unaffected.

**Collateral work.** 18 TMs that vanilla content referenced are no longer TMs, so
every reference was retargeted to a type-matched survivor -- Thunderbolt to Shock
Wave, Earthquake to Bulldoze, Ice Beam to Avalanche -- across 28 files in
`game/data`, `game/src` and `game/test`. These are placeholder rewards in vanilla
Hoenn content that the region rebuild will re-specify; they are ledger material,
not final design.

**Fairy consequence.** Dazzling Gleam is no longer a TM: it is Gen 6, so it fits
no region's origin set, and Fairy attacks route through tutors under this design.
Reachability is unchanged -- every Fairy-typed roster species still learns a Fairy
attacking move by level-up after M03c -- but the breadth the first M04 build gave
is gone until a Fairy tutor exists. **A Fairy tutor should be among the first
placed.**

**Not done.** *Apocrypha* TM distribution is unimplemented, but the earlier claim
that none of the 100 is obtainable was false: inherited and rethemed vanilla
content still distributes them. The Lilycove department store alone sells Fire
Punch, Thunder Punch, Icy Wind, Body Slam, Protect, Safeguard, Reflect and Light
Screen. Tutors remain Emerald's 30, and Tier 2 is a candidate pool, not a design.

**TM exclusion is not an acquisition gate.** The regression test proves fourteen
signature moves are absent from TMs. It does not prove they are unavailable early:
Pikachu still learns Thunderbolt at level 42 in the approved ORAS learnset, the
inherited Hoenn tutors still offer Double-Edge and Explosion, and Surf remains a
95-power HM. Restricting *purchased* teaching while leaving natural learnsets
intact is a coherent policy -- it is the policy -- but the power curve is not
gated, and approved learnsets must not be quietly trimmed to make it look gated.

## HM expansion (owner-approved, applied and verified)

Eleven HMs, not eight. Each region as originally built demands its own field moves,
and the union across five regions is eleven: Cut, Fly, Surf, Strength, Flash,
Rock Smash, Waterfall, Dive, Whirlpool, Rock Climb, Defog. Sinnoh alone brings
Rock Climb and Defog; Johto brings Whirlpool.

The owner's decision is that traversal moves ship as HMs, so they cost no region
a TM slot. Defog is HM09 and Rock Climb is HM10; both were already implemented
upstream behind `OW_DEFOG_FIELD_MOVE` and `OW_ROCK_CLIMB_FIELD_MOVE`, which are
now TRUE. Whirlpool is HM11 and had to be built outright.

The eight-slot limit was an item-id reservation, not a structural one. Field
moves key on the move through `gFieldMoveInfo`, never on the HM item, and
`NUM_HIDDEN_MACHINES`, `GetItemTMHMIndex` and `gTMHMItemMoveIds` all derive from
`FOREACH_HM`. Two new ids and two list entries were the whole of it, plus:

- **Items from 690 up renumbered, by two for HM09/HM10 and again by one for
  HM11.** Appending the new ids after the charms fails to compile: enum members
  must be declared before the `ENUM_HM` zip consumes them. No player save exists,
  so no saved id was invalidated -- and this is the point at which item ids should
  be frozen.
- **A latent upstream bug.** `src/item_menu.c` formatted the HM number at a fixed
  one-digit width, so HM10 displayed as `HM0`. No game has shipped ten HMs before,
  so the case had never arisen upstream.

**Whirlpool is HM11, built from nothing.** It had no metatile behavior, no
`FieldMove` entry and no field effect. It was built rather than designed around
because the alternative -- re-cutting Johto's whirlpools as dive sites -- means new
underwater maps: Dive is a warp to a paired `MAP_TYPE_UNDERWATER` map, of which
vanilla ships twenty-six, each with its own layout, collision, tileset, events and
scripts. That is deferred map production; the field move is bounded engine work.

Waterfall is the model, since both are used from the surfing state and test the
tile ahead. Whirlpool has no fixed direction, so the ride follows the player's
facing rather than `DIR_NORTH`. It reuses `FLDEFF_FIELD_MOVE_SHOW_MON` and ordinary
walk movement, so it needs no new art.

Verified: builds clean, 20 of 20 mechanics tests pass, and the regenerated
mechanics patch round-trips exactly against the roster baseline -- reverse-apply
lands on `f31b4400a5200d01355cb346306a09d94fcfe12c`, re-apply restores the working
tree. ROM `8a80af001a883b9cc5e1ce2fcb30d2d7f4ce4c469c69bb304add0cd905ec34d4`.

**Two things are built but not finished.** No tileset assigns `MB_WHIRLPOOL`, so
no whirlpool exists in any map; and all three new HMs inherit vanilla badge gates
written against an eight-badge game. Apocrypha has twenty badges and no settled
badge order, so those gates are placeholders to revisit with the HM timing policy,
not considered choices.

## Detailed coverage and integration findings

- **Damage and statuses:** `config/battle.h` controls critical-hit odds/multiplier,
  paralysis speed, confusion chance, burn damage, binding, sleep, screens/spread
  damage and turn order. Most remain Gen 9. For example the current selectors
  choose 1.5x critical damage, halved Speed under paralysis and 1/16 burn damage.
  Rules-era selection must include these; flipping the split alone is insufficient.
- **Abilities and weather:** Sturdy, Intimidate, redirection, weather duration and
  ability updates have separate switches. Ability weather currently expires;
  Snow Warning/overworld snow select snow rather than old hail. Mega-specific
  Parental Bond, -ate boosts and speed timing must be separately pinned after M01.
- **Type chart:** Fairy is already present independently of a global generation
  switch. `types_info.h` changes Steel's Ghost/Dark resistance at Gen 6. Keeping
  Fairy while selecting a pre-Gen-6 chart without an exception would create a
  hybrid chart. Terra and Shadow identities/chart/UI are still absent.
- **Items/catching:** healing amounts, held-item power, prices/resale, ball rates,
  critical catches and badge-based catch penalties have independent selectors.
  Do not carry the current eight-badge catch/obedience assumptions into twenty
  badges. The comment for `I_SITRUS_BERRY_HEAL` is reversed: the actual item table
  selects **25% at Gen 4+**, otherwise a flat 30 HP. Trust code over that comment.
- **Evolution/breeding:** species tables contain methods beyond config switches:
  Alakazam/Machamp/Golem/Gengar have Linking Cord alternatives; Porygon2/Porygon-Z
  include direct-use item alternatives. Eevee's Sylveon method requires friendship
  plus a Fairy move. The current friendship threshold, Egg level, inheritance,
  incubation speed and incense rules are modern. No all-species obtainability or
  evolution-path qualification is claimed.
- **Party/PC:** classic six-member party remains. The changed full-party catch
  path and PC healing restore intended behavior, but 900-slot integration is still
  deferred. NPC selection from both PC and party remains enabled and needs M05
  review; do not broaden the PC rewrite to accommodate it prematurely.
- **AI/difficulty:** `config/ai.h` has many modern switching/prediction tuning
  knobs; trainer-specific flags in authored teams determine use. Difficulty var,
  no-bag restriction, mandatory sleep clause, level/EV caps and smart-wild flag
  are inactive by default. Do not equate this with a completed difficulty balance
  or assert that every trainer uses original Emerald AI. No global level scaling
  was introduced; final authored trainers/encounters remain future work.
- **Gimmicks:** disabling species forms is not a universal mechanic switch.
  `data/gimmicks.h` still registers Mega, Z-Move, Ultra Burst, Dynamax and Tera
  activation callbacks. Z-Moves have a separate ring/item gate; Dynamax/Tera have
  their own checks. No unapproved gimmick should receive items, trainer settings
  or script access. A production eligibility guard/content audit is still needed;
  this config patch does **not** claim to remove those engines. Mega's player
  check requires a Mega Ring outside test builds; opponents need a separate
  content audit. Existing engine support is not proof of late-game story gating.
- **Overworld and release:** normal random encounters remain; double-wild chance
  is zero. Poison damage, weather, day/night and field-move access need their own
  rules decisions. Debug/quickstart are development facilities with release
  conditions; do not distribute a development build as a qualified player release.
- **Art:** existing species sprite style switches currently select updated assets.
  They have not been changed or visually reviewed. This is not new map/art work;
  a later asset pass must verify cohesive Gen 3 presentation and retained species
  coverage before promising plug-and-play graphics.

## Reproduce and validate

On the pinned checkout, apply the roster patch first, then the mechanics patch:

```sh
python3 tools/gba/profile.py apply
python3 tools/gba/profile.py apply --profile mechanics
python3 tools/gba/audit_config.py > gba/evidence/mechanics-config-inventory.json
python3 tools/gba/build.py
python3 tools/gba/build.py --qualification
python3 tools/gba/build.py --mechanics
python3 tools/gba/smoke.py
python3 tools/gba/move_inventory.py --check
```

`move_inventory.py` regenerates `gba/evidence/move-inventory.json`: resolved move
power, type, category, introducing generation and species breadth, plus the Tier 2
candidate pools. It preprocesses the move table with the Makefile's own CPPFLAGS,
so generation-dependent fields are evaluated rather than guessed. Reading power
out of the source by hand was wrong for 39 of the 559 Gen 1-5 moves, always high.
Use the tool. This is the same rule as `measure.py` for save capacity: the tracked
tool is the answer, an ad-hoc probe is not.

Skip an apply step when that patch is already applied; the helper refuses a
conflicting/double apply. `remove --profile mechanics` reverses only its own
patch after a check. Preserve other local work. Builds/tests must not run in
parallel against this checkout. Historical roster evidence predates this patch;
use mechanics evidence for the resulting build. These are development qualification
checks, not playthrough or release certification.

## Verification results

The following runtime checks were performed on the twelve-setting audit build,
before the explicit M01 pin. M01 selects the same Gen 4+ category branch already
used by that build; its separate build evidence is linked below.

- Ordinary development ROM build passed.
- Both baseline qualification tests passed, including saving/reloading all 420
  currently available PC slots with party/story state and roster/Fairy assertions.
- Both mechanics tests passed: actual Fairy chart/species/move data and ordinary
  trainer Thief/Covet attacks dealing damage without taking the player's item.
  The latter contains two move cases. Its initial fixture used recorded-link
  singles (where item exchange is permitted); the corrected ordinary-trainer
  fixture passed. No production engine workaround was introduced for that fixture.
- The ordinary ROM booted for 600 emulator frames. A normal save written in one
  emulator process loaded in a fresh process with story state intact; only the
  128 KiB save file crossed between processes. These checks bypass the menus.
- Profile source checks and patch reverse-applicability passed. Python syntax and
  whitespace checks passed. Temporary test source was removed after each run.

Evidence: [build and test results](../gba/evidence/mechanics-build.json),
[current capacity](../gba/evidence/mechanics-capacity.json),
[cold-save/boot result](../gba/evidence/mechanics-smoke.json).
The checks do not establish PC menu behavior by playtesting, every battle rule,
or final release compatibility. The existing linker warning remains recorded.

M01 follow-up: [build evidence](../gba/evidence/m01-build.json). The ordinary ROM
rebuilt successfully after explicitly pinning the approved split; remaining
experience settings were not changed.

M02 follow-up: [build and runtime evidence](../gba/evidence/m02-build.json).
Ordinary ROM build and all seven mechanics tests passed, including five new
experience tests: no catch rewards, recipient-level scaling, held-item sharing
with no reward for other inactive Pokemon, exact trainer bonus without delayed
evolution bonus, and exact division between two participants. Two initial test
fixtures lacked explicit Speed values for every Pokemon; fixed test setup passed.
No save-format or storage integration changes were made.

M03a follow-up: [build and runtime evidence](../gba/evidence/m03a-build.json).
The ordinary ROM rebuilt (exit 0) and all ten mechanics tests passed, including
three new base-stat tests: sampled Gen 1-5 species on their B2W2 spreads,
`>= GEN_2` special-stat selectors unchanged, and the Sylveon/Mega exceptions
intact. The linker RWX warning is unchanged. Historical M01/M02 evidence was not
rewritten; hashes there still describe the sources at those stages.

M03b follow-up: [build and runtime evidence](../gba/evidence/m03b-build.json).
The ordinary ROM rebuilt (exit 0) and all twelve mechanics tests passed, including
two new ability tests: sampled species on their B2W2 ability sets with the Gen 4-era
updates retained, and every owner exception in both directions. The linker RWX
warning is unchanged. Earlier evidence records were not rewritten.

M03c follow-up: [build and runtime evidence](../gba/evidence/m03c-build.json).
The ordinary ROM rebuilt (exit 0) and all fifteen mechanics tests passed after a
corrected assertion, including three new tests: ORAS-specific learnset levels,
Fairy species able to attack with their own type, and Gen 5 move power/PP/accuracy
with Fairy moves untouched. One assertion initially failed because the test helper
returns the first level a move is learned and Gardevoir learns Moonblast twice, at
1 and at 62; the assertion was changed to a unique level and no production data
was altered. The linker RWX warning is unchanged.

M03d follow-up: [build and runtime evidence](../gba/evidence/m03d-build.json).
The ordinary ROM rebuilt (exit 0) and all sixteen mechanics tests passed,
including one new yield test covering inline selectors, the shared Gengar macro,
unaffected literals and the Mega fallbacks. One assertion was first written as 270
for Mega Alakazam and corrected to 266 after reading its three-branch selector; no
production data changed.

M04 follow-up: [build and runtime evidence](../gba/evidence/m04-build.json).
The ordinary ROM rebuilt (exit 0) and all eighteen mechanics tests passed,
including two covering the machine count and per-region representatives, and a
second asserting that fourteen named signature moves are unobtainable from any
TM. The first M04 attempt that imported B2W2's list wholesale was superseded the
same day and its evidence file rewritten rather than kept, since it described a
build that no longer exists.
