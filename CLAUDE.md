# CLAUDE.md

Pokemon Apocrypha: a Gen-4 DS romhack built on HGSS. Five regions, 20 badges,
a concurrent B2W2 timeline. `DESIGN.md` is the world bible and `ENGINEERING.md`
is the engine reality check.

## Hard rules

- **Never edit `DESIGN.md`.** It is the authority on the world and it is
  read-only for agents. A proposal that contradicts it is refused, not merged
  into it. Changing the bible is Davis's call, in its own conversation.
- Chapter specs under `docs/CHAPTER*_SCENES_SPEC.md` are downstream of
  `DESIGN.md` and can themselves be wrong. Check the bible, not the spec.
- Story state is a fixed budget, not an implementation detail. Run
  `/apoc-budget-check` before committing to a scene that needs new flags or vars.

## Repo skills

| Skill | Use it for |
|---|---|
| `/apoc-lore-check` | Does this scene, NPC, or location contradict `DESIGN.md`? Refuses rather than compromises. |
| `/apoc-budget-check` | Flag and var usage against `NUM_FLAGS` 2912, `NUM_VARS` 368, dex cap 493. Reports what is left. |
| `/df-writing` | NPC dialogue. Carries the Apocrypha voice row: Gen 4 in-game register, one thought per message box, no modern idiom. |

## The rig

`tools/` drives the ROM under py-desmume with a RAM oracle, so a scene is
verified against ground truth (scene var, map id, player tile) rather than
guessed from pixels.

```bash
source .emu-venv/bin/activate
python tools/cockpit.py                              # play + monitor + annotate
python tools/cockpit.py --record paths/ch1_s2.json   # also record what you press
python tools/path_replay.py paths/ch1_s2.json --state cur_cherrygrove.dsv
```

Recording exists so choreography can be walked by hand once instead of
hand-coded as `press()` calls. A path records real hold and gap frames, because
the idle time between presses is usually a script or a transition playing and
dropping it desyncs the replay. Paths are seeded from a savestate;
`path_replay.seed_state()` reports which one and replaying from a cold boot will
not work.

`docs/CH1_PLAYTHROUGH_LOG.md` is the record of the chapter's real state,
including deliberate breakage and engine limitations. It is a diff target, not a
list of assertions that should all be green. See
`docs/proposals/nightly-rebuild-and-play.md`.

## Runtime model routing

Nothing here calls an LLM at runtime. It is a romhack. The skills and the rig
are build-time tooling.
