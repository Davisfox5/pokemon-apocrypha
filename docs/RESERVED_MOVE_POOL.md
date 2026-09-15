# Reserved move pool (design intent; nothing implemented)

**Status: an idea the owner asked to keep, not approved canon and not built.**
No move has been granted, gated or redistributed. This page exists so the option
survives the decisions around it. Machine-readable lists, including the full 254
entries, are in [reserved-move-pool.json](../gba/evidence/reserved-move-pool.json).

## Owner intent, 2026-09-12

Some powerful moves are currently unreachable. Rather than delete or distribute
them, the owner may build a deliberately difficult late-game path that grants a
few as a reward for players who invest real time. Exclusivity is explicitly fine
— the stated model is Volt Tackle — the requirement is that a granted move must
not wreck the game once obtained.

**Design this alongside the deferred breeding and inheritance rules.** The owner
expects the two to integrate, and the engine already points the same way.

## The hook already exists

`game/src/daycare.c` holds `sBreedingSpecialMoveItemTable`, which today has
exactly one row:

| Offspring | Required held item | Granted move |
| --- | --- | --- |
| Pichu | Light Ball | Volt Tackle |

Offspring species, a required held item, a granted move. Adding rows is trivial;
the real work is designing what the gate should be. This is why Volt Tackle does
**not** appear in the lists below — it is already reachable through this rule.

## Do not confuse the two lists

**These counts are stale and must be regenerated before use.** They describe the
discarded first M04 build, which appended B2W2's TM list wholesale. The curated
per-region list that replaced it removed Focus Blast again, so the one move that
build restored is unreachable once more. Treat every number below as historical.

At the time of writing, 254 ordinary moves could not be reached by any of the 787
compiled-in species. They split into two groups that must be treated completely differently.

**82 are a TM gap, not reward material.** A roster species legitimately learns
these in the source games; they are unreachable only because the **move tutor** set is still
Emerald's 30. Blast Burn, Hydro Cannon, Frenzy Plant, Draco Meteor, Superpower
and V-create are all here -- all tutor moves in Gen 5, which is why M04's TM
expansion did not reach them. **These belong to the open tutor decision.** Note also that
this framing now partly conflicts with the owner-approved move economy: under
[MOVE_ECONOMY.md](MOVE_ECONOMY.md), signature moves including the starter
ultimates are *deliberately* gated behind late, item-purchased regional tutors.
The warning below against gating a starter ultimate behind an endgame trial
predates that decision and no longer reflects owner direction. Gating a
starter's signature ultimate move behind an endgame trial would be a mistake.

**172 are genuine vault material.** No species on this roster ever learns them,
in any game. Most are signature moves of Gen 6–9 Pokemon the roster excludes.
Granting one is a pure addition, not a restoration.

## Tier 1: the high-risk moves

These came out of the egg-move safety review. They are the ones that would
actually warp battles, which is exactly why they are worth gating rather than
simply handing out.

| Move | Power | Why it is dangerous | List |
| --- | --- | --- | --- |
| Last Respects | 50 base | Grows with every fainted party member. The one genuinely warping move already sitting in `egg_moves.h`, behind `#if P_HISUIAN_FORMS` on Basculin White-Striped, which is compiled out. | Vault |
| Population Bomb | 20 x 10 hits | Up to 200 before items; a Wide Lens papers over its accuracy. | Vault |
| Surging Strikes | 25 x 3 hits | `alwaysCriticalHit`, so it ignores the target's defensive boosts. | Vault |
| Wicked Blow | 80 | `alwaysCriticalHit`. | Vault |
| Fishious Rend | 85 | Doubles to 170 when the user moves first. | Vault |
| Bolt Beak | 85 | Doubles to 170 when the user moves first. | Vault |
| Glaive Rush | 120 | Dragon physical, with a drawback turn. | Vault |
| Make It Rain | 120 | Steel special. | Vault |
| Salt Cure | 40 | Chip damage that is far worse against Steel and Water. | Vault |
| Rage Fist | 50 base | Grows each time the user is hit. **Tutor gap, not vault** — a roster species learns it. | Tutor gap |
| Shed Tail | — | Substitute plus a free switch. **Tutor gap, not vault.** | Tutor gap |
| Triple Axel, Scale Shot | 20/25 multi-hit | **Tutor gap, not vault.** | Tutor gap |

Shell Smash was screened too and needs no gate: roster species already learn it
by level-up, as they do in the source games.

## Tier 2: vault highlights

Strongest entries of the 172. The full list is in the JSON.

| Move | Power | Type | Gen |
| --- | --- | --- | --- |
| Gigaton Hammer | 160 | Steel | 9 |
| Eternabeam | 160 | Dragon | 8 |
| Prismatic Laser | 160 | Psychic | 7 |
| Meteor Assault | 150 | Fighting | 8 |
| Dragon Energy | 150 | Dragon | 8 |
| Mind Blown | 150 | Fire | 7 |
| Light of Ruin | 140 | Fairy | 6 |
| Blood Moon | 140 | Normal | 9 |
| Fleur Cannon | 130 | Fairy | 7 |
| Glacial Lance | 130 | Ice | 8 |
| Astral Barrage | 120 | Ghost | 8 |
| Armor Cannon | 120 | Fire | 9 |
| Pyro Ball | 120 | Fire | 8 |

Note the two Fairy entries. Light of Ruin and Fleur Cannon are the only
high-power Fairy moves in the build that nothing on the roster can learn, which
makes them interesting against the thin Fairy offence found in the M03c review.

## Before using any of this

These lists are a snapshot against the current configuration. **Changing the
tutor set, learnsets, the TM list or the roster profile changes both lists.**
Regenerate rather than trusting this page. The method is recorded in the JSON:
resolve `species_enabled.h`, walk the `#if` guards for compiled-in species, then
subtract level-up, teachable and egg moves. Filtering species by name suffix is
not sufficient — Sirfetch'd, Ursaluna and Basculin White-Striped carry no form
suffix and are all compiled out by config.

Related: [GBA_MECHANICS_AUDIT.md](GBA_MECHANICS_AUDIT.md) for the egg-move review
and the deferred breeding rules, and
[egg-move-audit.json](../gba/evidence/egg-move-audit.json).
