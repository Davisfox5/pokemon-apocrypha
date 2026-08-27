# Proposal: nightly rebuild-and-play regression job

**Status: proposed, not built.** Written so the shape can be argued with before
any of it exists.

## What it would do

Once a night, on a machine with the ROM and the toolchain:

1. `make build` from a clean tree.
2. Boot the built ROM under the py-desmume rig and drive Chapter 1 end to end,
   the same way `tools/rig.py` already does by hand.
3. Assert on RAM ground truth at each beat, not on pixels: scene var, map id,
   player tile, party contents.
4. Write a result table in the exact shape of `docs/CH1_PLAYTHROUGH_LOG.md`.
5. Diff that table against the committed log.
6. Report only the diff. A night where nothing changed produces one line.

## Why a diff and not a pass/fail

`CH1_PLAYTHROUGH_LOG.md` is not a list of assertions that should all be green.
It is a record of the chapter's real state, including things that are
deliberately broken (`⬜ deferred-by-design`), things that need a human
(`🟨 needs human spot-check`), and engine limitations that will never be fixed
(the catching demo renders a generic hero, not Gold).

A pass/fail job would be red every night and get ignored inside a week. A diff
job says "row 9 changed from OK to blocker" and that is the whole signal.

## What it would catch

The failures this chapter actually had are all diff-shaped:

- A script seam that leaves the player on a black screen (row 11). The rig
  reaches a beat and then the scene var stops advancing.
- A scene that stops being reachable because a warp or a coord trigger moved.
- An NPC that becomes visible during a fade it should be hidden through, if the
  assertion is on the object table rather than the screen.
- A flag or var that stops being set, breaking a downstream chapter's entry
  condition.

## What it would not catch

Worth stating plainly, because a green nightly is otherwise read as "the game is
fine":

- Anything visual. Sprite corruption, palette errors, and text overflow are
  invisible to a RAM oracle.
- Text quality. Whether an NPC line reads like Gen 4 is a `df-writing` question.
- Anything past where the rig can drive. Interior stairs warps do not fire from
  the rig today (row 3), so any beat behind a staircase is unverifiable.
- Timing and feel. Row 8 ("~15 message boxes before the player can move, feels
  long") is a real finding no assertion produces.

## The piece that makes it cheap

The recorded-path work is the enabler. `tools/cockpit.py --record` writes what a
human actually pressed while walking a scene, and `tools/path_replay.py` plays it
back through the same `Emu` the rig uses. That means the nightly does not need
hand-coded choreography for every beat: walk the chapter once, commit the path,
and the job replays it.

Recorded paths are seeded from a savestate. `path_replay.seed_state()` reports
which one, and the nightly has to honor it or every replay desyncs.

## Open questions before building

1. **Where does it run?** The rig needs the ROM, which is not in the repo. A
   self-hosted runner on the Mac is the obvious answer and also the one that
   rots silently when the Mac sleeps.
2. **How stable are recorded paths across a rebuild?** A path is frames and
   button presses. If a script's message count changes by one box, every
   subsequent press lands a frame off and the replay desyncs. The rig's
   `advance_until_var` is robust to this because it mashes until a var moves;
   a recorded path is not. Likely answer: record paths for movement and
   choreography, use `advance_until_var` for dialogue, and interleave.
   **This is the question that decides whether the whole job is viable.**
3. **What is the checkpoint strategy?** Replaying from a cold boot every night
   is slow and maximizes desync risk. Checkpoints make it fast but go stale when
   the build changes the state they encode.
4. **Who reads the diff?** If it goes nowhere, do not build it.

## Recommendation

Do not build this until question 2 is answered. The cheap experiment: record one
path today, change a single message box in that scene, and see whether the
replay still lands. That answer is worth more than the rest of this document.
