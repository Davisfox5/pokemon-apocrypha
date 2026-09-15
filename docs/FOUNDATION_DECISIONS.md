# Approved Apocrypha foundation

**Owner-approved 2026-09-10. Platform review closed.** This is the technical
source of truth; DESIGN.md retains narrative authority. Implementation is tracked
separately in [GBA_BASELINE.md](GBA_BASELINE.md).

## Locked decisions

| ID | Approved decision |
| --- | --- |
| F01 | GBA ROM, Gen 3 2D presentation, pokeemerald-expansion. One production platform. |
| F02 | Otherwise classic Pokemon mechanics with canonical Fairy typing, late-game Mega Evolution, a custom Shadow type limited to Wes's gym, and a custom Terra type restricted to the designated final gym leader. |
| F03 | Living Pokedex support: target 30 PC boxes / 900 slots with familiar PC interaction and ordinary saves. |
| F04 | Agents perform the vast majority of design production, coding, gameplay, tooling, testing, and revisions; the owner directs story/creative identity and reviews. |
| F05 | Newly authored five-region layouts and elements reflecting roughly ten years of change, using familiar geography, landmarks, regional aesthetics, and reusable assets as references. |
| F06 | Retain the DS implementation and references for selective research and an explicitly authorized hard-blocker fallback. No parallel DS development. |

## Battle categories (owner-approved 2026-09-11)

Use the Gen 4–5 per-move physical/special split: Fire Punch is physical and
Flamethrower is special. Pin `B_PHYSICAL_SPECIAL_SPLIT = GEN_5`; this selector
implements the shared Gen 4+ category behavior. The approval does not select
every Gen 5 calculation, experience formula, learnset or convenience. Resolve
those separately in the [mechanics audit](GBA_MECHANICS_AUDIT.md).

## Experience (owner-approved 2026-09-11)

Gen 5 level-based experience scaling; defeated opponents award experience split
among participants, with classic held-item Exp. Share and trainer-battle bonus.
No catch experience, automatic whole-party sharing, or delayed-evolution bonus.
This changes rewards, not enemy levels. No new level caps. Species experience
yields, item distribution and five-region pacing still require separate work.

## Species base stats (owner-approved 2026-09-11)

Use the Gen 5 / Black 2–White 2 base-stat baseline for Gen 1–5 Pokemon, with
canonical later stats for the approved Sylveon and Mega forms. No custom buffs
or nerfs. Approval covers base stats only, not abilities, learnsets, move power,
experience yields or breeding.

Applied and verified 2026-09-11: `P_UPDATED_STATS = GEN_5`. Sylveon carries no
generation selector and was already canonical; Mega Alakazam is the only retained
Mega form the selector reached and is pinned to its canonical 105 Sp. Def. See
[GBA_MECHANICS_AUDIT.md](GBA_MECHANICS_AUDIT.md) for the resolved-selector audit
and [m03a-build.json](../gba/evidence/m03a-build.json) for build and test evidence.

## Species experience yields (owner-approved 2026-09-12)

Use Gen 5 / Black 2-White 2 experience yields. Applied and verified:
`P_UPDATED_EXP_YIELDS = GEN_5`. About 190 roster species are worth roughly 10%
less, uniformly. Together with M02 this makes the whole experience package one
reference: the rules and the yields those rules multiply both come from B2W2.

No exception was required. Sylveon's yield is a literal and every Mega selector
falls back to a genuine Gen 6 or Gen 7 figure. EV yields, base friendship and egg
groups remain inherited and unapproved. See
[m03d-build.json](../gba/evidence/m03d-build.json).

## Species abilities (owner-approved 2026-09-11)

Use the Gen 5 / Black 2-White 2 ability sets for Gen 1-5 Pokemon, with a short
list of owner-chosen exceptions. Approval covers which abilities each species
has, not how the player obtains a Hidden Ability, and not learnsets, move power,
experience yields or breeding.

Applied and verified 2026-09-11: `P_UPDATED_ABILITIES = GEN_5`, with eighteen
exceptions pinned in `game/src/data/pokemon/species_info/`. Kept from present-day:
the four weather setters and their families (Torkoal, Pelipper, Gigalith,
Vanilluxe, plus Wingull, Roggenrola, Boldore, Vanillite, Vanillish, Cubchoo,
Beartic), Koffing/Weezing's Neutralizing Gas and Gallade's Sharpness. Overridden
away from the Gen 5 restoration: Gengar keeps Cursed Body and the Litwick line
keeps Infiltrator. Where Gen 5 restores an ability and the owner did not override
it, the Gen 5 version stands -- Zapdos keeps Lightning Rod, and Raikou, Entei and
Suicune keep their absorbing hidden abilities. See
[GBA_MECHANICS_AUDIT.md](GBA_MECHANICS_AUDIT.md) and
[m03b-build.json](../gba/evidence/m03b-build.json).

## Learnsets and move data (owner-approved 2026-09-11)

Use ORAS level-up learnsets and Gen 5 move power, accuracy and PP. Approval
covers what Pokemon learn and how hard moves hit; it does not cover move flags,
species experience yields, breeding, or the TM/HM list.

Applied and verified 2026-09-11: `P_LVL_UP_LEARNSETS = GEN_6` and
`B_UPDATED_MOVE_DATA = GEN_5`.

Learnsets deliberately do **not** match the Gen 5 baseline used for stats and
abilities. Level-up learnsets are a whole-file swap, and at Gen 5 twenty-two of
the twenty-three Fairy-typed roster species learn no Fairy attacking move at all,
with no Fairy TM available to compensate. ORAS is the earliest set that keeps the
approved Fairy typing playable. Mr. Mime, the one final-stage species still
stranded, is given Dazzling Gleam at level 44.

`B_UPDATED_MOVE_FLAGS` is deliberately left inherited and is a separate choice.
See [GBA_MECHANICS_AUDIT.md](GBA_MECHANICS_AUDIT.md) and
[m03c-build.json](../gba/evidence/m03c-build.json).

## Move economy: TMs and tutors (owner-approved 2026-09-12)

Moves are tiered so that travelling between regions means something mechanically.

- **TMs are the generic toolkit.** 100 of them, twenty per region, each a move
  that region's own generation introduced, capped at 85 power. Single-use.
  Applied and verified.
- **Signature moves are tutor-only and origin-locked.** Thunderbolt, Ice Beam,
  Flamethrower, the starter ultimates and their peers are not TMs. Each is taught
  in its home region. Designed, not implemented.
- **Ordinary tutors** teach everyday moves and are freely placed.

Signature moves are paid for with trade goods produced by **another** region, so
the move economy expresses a world that has only recently opened up. Ordinary
tutors take a common currency. Signature moves trickle in during the final phase;
the full list opens post-game.

100 TMs fills the engine's item-id ceiling exactly. Adding one means removing one
or renumbering the item enum.

Full design, the complete TM list and the per-region signature pools:
[MOVE_ECONOMY.md](MOVE_ECONOMY.md). Build evidence:
[m04-build.json](../gba/evidence/m04-build.json).

## Egg moves and breeding (reviewed 2026-09-11; breeding DEFERRED)

Egg moves are preserved unchanged. They are a single present-day dataset with no
per-generation option in the engine, so there was no choice to make. A safety
review confirmed nothing egg-exclusive on this roster can unbalance the game:
all fifteen egg-exclusive post-Gen-5 moves are Gen 6 or Gen 7, the strongest is
self-limiting, and the one genuinely warping move in the file (Last Respects) is
compiled out with its species. Owner position: a move being obtainable only by
breeding is acceptable in the spirit of Volt Tackle; being unbalanced is not.

**Reserved move pool: an owner idea recorded 2026-09-12, not approved.** The
powerful moves no roster species can reach may later be granted through a
deliberately difficult late-game path, as a reward for deep play. Exclusivity is
acceptable to the owner in the spirit of Volt Tackle; imbalance is not. To be
designed with the breeding rules, extending `sBreedingSpecialMoveItemTable` in
`game/src/daycare.c`. Catalogue and the vault/TM-gap distinction:
[RESERVED_MOVE_POOL.md](RESERVED_MOVE_POOL.md).

**Breeding and inheritance rules are explicitly deferred, not approved.**
`P_MOVE_INHERITANCE`, `P_EGG_MOVE_TRANSFER`, `P_ABILITY_INHERITANCE`,
`P_NATURE_INHERITANCE`, `P_BALL_INHERITANCE`, `P_EGG_HATCH_LEVEL` and
`P_INCENSE_BREEDING` all remain at inherited Gen 9 defaults. The owner asked that
this be recorded as work to return to, at a time of the agent's choosing. Nothing
in M01-M03 approves them by implication. See
[GBA_MECHANICS_AUDIT.md](GBA_MECHANICS_AUDIT.md) and
[egg-move-audit.json](../gba/evidence/egg-move-audit.json).

## Battle exceptions: scope, not a global redesign

- **Fairy:** apply canonical Fairy typing to affected existing species and the
  approved added Fairy species. Use the corresponding standard type interactions.
- **Mega Evolution:** retain the existing late-game requirement. Eligibility and
  unlock timing follow the approved design; do not unlock it globally at new game.
- **Shadow:** an additional custom type alongside Fire, Water, Electric, and the
  other types, confined to Wes's gym. Preserve the purification narrative; do not
  introduce a player-wide acquisition, progression, or purification subsystem.
- **Terra:** an additional custom type, confined to the designated final gym
  leader. Use the spelling **Terra**. It is not the canonical Terastallization
  mechanic and does not change a Pokemon's type during battle.
- Both custom types are assigned before battle, not activated as transformations.
  Add explicit type identities and type-chart support; Shadow is not merely a
  status condition. This adds two types to the 18 standard types, including Fairy.
  It does not imply adding a third simultaneous type slot to every Pokemon.
- Exact offensive/defensive matchups, moves, and which existing type slots the
  gym Pokemon use remain to be specified. Do not invent these creative decisions
  or assume canonical Terastallization or Colosseum rules apply.
- Reuse compatible engine facilities where available. Both custom-type integrations
  require qualification; existing Mega/Terastallization code does not implement them.

Owner clarification: Terra and Shadow are additional types, not battle-time
transformations. This supersedes the earlier interpretation preserved in history.

## Production defaults

- Use Porymap-compatible editable data, Poryscript, suitable Porytiles compilation,
  Aseprite-compatible editable art/exports, and mGBA. Choose compatible pinned tool
  versions during baseline setup. Narrow scripted adapters are preferred to editor clones.
- Agents create new assets, complete frame sheets, handle palettes and imports,
  and inspect results. Image models are tools, not a reason to hand cleanup to the owner.
- Canonical species roster: Gen 1-5 plus explicit picks, currently Sylveon; no
  fakemon or blanket later-generation inclusion. Use existing target-format assets.
  Gen 3 adaptations need not retain original DS pixels or animation formats.
- Keep the expansion's supported internal species IDs distinct from displayed
  dex numbers. Avoid needless custom renumbering; freeze save-relevant identifiers.
- Replace the original campaign events and hooks, retaining functional engine
  systems and reviewed templates. Never blanket-wipe flags or reuse them without tracing references.
- Use named persistent IDs, ordered stages, independent optional-event flags,
  and shared gate predicates. Measure save layout and headroom; no silent resets.
- Preserve classic party/PC/menu interaction. Adapt only what five-region travel,
  twenty badges, the accepted species roster, and 30 boxes require.
- Story gates region travel; authored tiers support local flexibility. No automatic
  party-based level scaling or player-level resets. Record battle-rule settings
  explicitly instead of inheriting every modern expansion default.
- Preserve regional art direction and established narrative. Unresolved story
  identities, late chapter sequencing, and dialogue remain owner-directed.

## Baseline pin and verification

Initial upstream pin: release `expansion/1.17.0`, commit
`e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7` (release checked 2026-09-10).
Do not track moving master/upcoming branches. A documented compatible release
change within this base family is not a platform reversal.

Target ordinary 32 MiB GBA ROM addressing. Verify actual ROM, active RAM, save
layout, map/event identifiers, roster, forms, and 30-box capacity on the build.
A sample sprite estimate is not a full game budget. Owner acceptance establishes
requirements, not proof of implementation or fit. Baseline checks must precede
new map production; see the task document for evidence and unresolved measurements.

## Deferred save architecture

On 2026-09-10 the owner deferred the save/autosave investigation to allow independent
work to proceed. Thirty boxes remain required and unqualified in production.
Prototype tradeoffs are not universal platform limits. Automatic checkpoints and
an emulator dependency are not approved. If autosaves are introduced, the requested
behavior is separate rotating autosaves, preservation of the last manual save until
explicitly replaced, and sub-second autosaves; feasibility remains to be tested.
See [the deferred questions and prototype evidence](GBA_STORAGE_PROTOTYPE.md).
The [mechanics audit](GBA_MECHANICS_AUDIT.md) records applied scope corrections
and unresolved rules-era choices. GBA graphics alone do not select exact battle
calculations; no global Gen 3 or Gen 5 rules preset has been newly approved.

## DS fallback rule

Only reconsider DS for a demonstrated hard requirement that cannot reasonably
be met in GBA after investigating remedies. Document the requirement, reproducible
failure, attempted solutions, and cost, then obtain an explicit owner decision.
Do not switch automatically for tool inconvenience, an art revision, or a bug.
The [archive index](../archive/gen4/README.md) provides recovery pointers; do not
load it during ordinary GBA work.

## Sources

- [Pinned expansion release](https://github.com/rh-hideout/pokeemerald-expansion/releases/tag/expansion/1.17.0)
- [Porymap source formats](https://huderlem.github.io/porymap/manual/project-files.html)
- [Porytiles](https://github.com/grunt-lucas/porytiles)
- [Poryscript](https://github.com/huderlem/poryscript)
- [Aseprite automation](https://www.aseprite.org/docs/cli/)
