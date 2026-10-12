# Independent review of Claude's M04 findings

Reviewed 2026-09-12 against the latest Claude response in session `a04014ef-69f5-4c91-9565-ab517f23e519`, timestamp `2026-09-12T23:28:33.228Z`.

## Verdict

The implementation checkpoint is real, but the findings are not yet thorough enough to establish the intended move economy or a smooth power curve. Preserve the owner's four decisions: origin-matched TMs, exactly 100, split tutor currencies, and signature teaching that trickles in late and opens fully post-game. Correct the analysis before treating the list's balance and the tutor plan as settled.

No gameplay, configuration, save, or existing design document was changed for this review.

## 1. Save evidence has an incorrect measurement and omits compatibility

**Confirmed measurement error:** `python3 tools/gba/measure.py` reports `sizeof(SaveBlock1) = 15,660`, leaving **212** of 15,872 bytes. The report says 15,588 and 284 free. The existing ordinary ROM's ELF independently corroborates the measurement: `gSaveblock1` has symbol size `0x3dac` (15,788), including the 128-byte ASLR reserve defined in `include/load_save.h`.

An ARM compile using the production ABI and changing only the TM/HM bag count from 108 back to 64 gives a 176-byte reduction. Berries, Pokeblocks, flags and variables all move by 176 bytes. PC storage being separate does not establish compatibility for the other persistent data. The reordered TM list also changes the meaning of saved numeric IDs: baseline TM01 meant Focus Punch; it now means Protect.

This is source/layout evidence, **not an observed failed save load**. No prior-save compatibility or migration test was performed by this review, and the 18 mechanics tests do not exercise that contract. This finding concerns the TM changes; it does not reopen the deferred 30-box architecture.

Sources: [measurement tool](../tools/gba/measure.py), [bag and SaveBlock1](../game/include/global.h), [TM IDs](../game/include/constants/items.h), [new TM order](../game/include/constants/tms_hms.h).

## 2. The 85-power filter does not prove the absence of power spikes

`MOVE_ECONOMY.md` says, “Power is capped at 85, so no TM is a power spike.” The battle code contradicts that inference:

| Selected TM | Relevant actual behavior |
| --- | --- |
| Return / Frustration | Up to 102 power; the data-table value 1 is a placeholder |
| Acrobatics | 110 power without a held item |
| Low Kick / Grass Knot | Up to 120 power against heavy targets |
| Facade | 140 effective power with an applicable status condition |
| Bullet Seed | 25 per hit, up to five hits: 125 total nominal power |

The list also includes setup, weather, evasion, hazards and other utility whose impact cannot be ranked by a zero-power field. Conversely, high printed power may come with accuracy, recoil, recharge, or setup costs.

These moves do not automatically need removal. They need explicit balance classifications and acquisition timing. Rate ordinary damage, conditional damage, drawbacks, utility, available abilities/items and representative team combinations; do not use the scalar power field as the balance verdict.

Sources: [base-power and modifier calculations](../game/src/battle_util.c), [move data](../game/src/data/moves_info.h).

## 3. Nine TM power entries do not describe the configured game

The original curation script extracted every number from a power expression and selected the maximum, rather than resolving its generation condition. Independently preprocessing the current source with the project's ARM compiler and production defines exposes these discrepancies:

| Move | Document | Configured value |
| --- | ---: | ---: |
| Thief | 60 | 40 |
| Low Kick | 50 | Variable; table sentinel 1 |
| Rock Tomb | 60 | 50 |
| Knock Off | 65 | 20 |
| Air Cutter | 60 | 55 |
| Incinerate | 60 | 30 |
| Low Sweep | 65 | 60 |
| Hex | 65 | 50 |
| Struggle Bug | 50 | 30 |

These are base-data values; separate effect settings can modify damage, notably Knock Off. The same mistake affects the signature pool: Energy Ball is listed as 90 but is 80 in this configuration. Recompute the entire candidate inventory using resolved settings before relying on its counts or exclusions.

Sources: [published tables](MOVE_ECONOMY.md), [configured move data](../game/src/data/moves_info.h), [independent earlier move-data assertions](../tools/gba/mechanics_test.c).

## 4. TM exclusion is not an acquisition-gate audit

The new test confirms that fourteen named moves are absent from TMs. It does not establish that signature moves are unavailable before late game. Pikachu retains Thunderbolt at level 42 in the approved ORAS learnset. Existing Hoenn tutors still offer moves such as Double-Edge and Explosion. Surf remains a 95-power HM.

This may be intentional: restricting purchased teaching can coexist with natural species progression. The report needs to distinguish those policies, and analyze level-up, evolution/relearning, eggs, inherited tutors, HMs and scripted rewards against expected progression before claiming that the whole power curve is gated. Do not silently remove approved natural learnsets.

The claim that none of the 100 TMs is obtainable is also false for the current vanilla-world build. For example, the Lilycove department-store script sells Fire Punch, Thunder Punch, Icy Wind and Body Slam, plus defensive TMs. Accurate status: custom Apocrypha distribution is unimplemented; inherited and rethemed rewards remain.

Sources: [Pikachu learnset](../game/src/data/pokemon/level_up_learnsets/gen_6.h), [existing tutors](../game/data/scripts/move_tutors.inc), [Lilycove shop](../game/data/maps/LilycoveCity_DepartmentStore_4F/scripts.inc), [TM tests](../tools/gba/mechanics_test.c).

## 5. Fairy coverage needs an explicit timing and regional policy

Removing Dazzling Gleam from TMs is consistent with the chosen origin rule, but calling for an early *signature* Fairy tutor conflicts with signature teaching being late and origin-locked: Gen 6 has no home region in this game. An ordinary early Fairy tutor or an explicit regional exception would resolve this; it is not yet designed.

The literal assertion that every Fairy species learns a Fairy attack itself is too broad. The compiled roster includes Cleffa, Igglybuff, Mime Jr., Togepi and Azurill with no direct Fairy attack in their selected level-up lists, and Togekiss relies on Togetic's Fairy Wind. Arceus requires separate treatment for Judgment's dynamic typing. These are coverage qualifications, not evidence that M04 newly removed all family-level access.

The existing Fairy regression test samples selected species and checks Togetic; it is not an exhaustive per-species, per-stage availability audit. Resolve evolution, relearning, items and timing when specifying the early teaching route.

Sources: [Fairy policy](MOVE_ECONOMY.md), [selected learnsets](../game/src/data/pokemon/level_up_learnsets/gen_6.h), [regression fixture](../tools/gba/mechanics_test.c).

## 6. Tutor design and its supporting inventories are incomplete

Four of the five signature candidate lists end with ellipses, so the reported counts are not complete reviewable selections. They are filtered primarily by printed power; useful status and variable-power moves need their own review. There is no per-move availability tier, recipient policy, price, goods source, replenishment rule or expected acquisition effort. Claude appropriately acknowledges that implementation is pending, but “designed” overstates the detail available.

`RESERVED_MOVE_POOL.md` and its JSON still describe Focus Blast as restored by the discarded TM expansion, although the revised list removed it again. The document also says gating a starter ultimate behind an endgame trial would be a mistake, which needs reconciliation with the newer owner-approved late signature-tutor economy. Regenerate the snapshot; do not use these old counts as current planning evidence.

The engine's `special_movesets.json` also supports `extraTutors`, which the generator merges with script-discovered tutors. Thus compatibility data can be prepared without a placed NPC, although actual player-facing teaching still needs an interaction. The claim that *all* tutor work is blocked on map scripts is too absolute.

The next useful deliverable is an agent-prepared proposal with complete tutor rosters and progression/currency rules for owner review. Exact NPC coordinates and visual map production can remain deferred.

Sources: [candidate pools and open work](MOVE_ECONOMY.md), [stale reserved pool](RESERVED_MOVE_POOL.md), [snapshot](../gba/evidence/reserved-move-pool.json), [tutor generation](../game/tools/learnset_helpers/make_teachables.py), [extra tutor configuration](../game/src/data/pokemon/special_movesets.json).

## What verified successfully

- The current submodule is at the recorded upstream pin `e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7`.
- Ordinary ROM SHA-256 matches the record: `81b9df9a07105f68874e93e76b85dfdc0514e342527187868d29184bb262fcb7`.
- Every source and log hash in `gba/evidence/m04-build.json` matched.
- The mechanics patch passes reverse-apply checking; the config audit passes.
- The mechanics suite was rerun independently: **18 passed / 18 total**. Review log: `/tmp/apocrypha-claude-review-tests.log`.
- The compiled-data audit resolves 787 species entries. All 100 selected TMs have nonzero teaching coverage; the narrowest selection is Drill Run, with 37 compiled entries. This counts forms separately and is not a campaign encounter or team-coverage metric.

The new TM tests cover counts, sampled item mappings, one item's importance field and fourteen TM exclusions. They do not test the full learning/consumption UI, all 100 item contracts, save migration, economy pacing or complete acquisition gating. No campaign playthrough was performed. The ordinary ROM was hash-verified; the independent fresh build was the mechanics test build.
