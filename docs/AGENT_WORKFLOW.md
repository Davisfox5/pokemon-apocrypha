# Agent production and validation workflow

Read only when performing the relevant production task. AGENTS.md and
FOUNDATION_DECISIONS.md define ownership and scope.

## Authoring

Keep editable source art, map layouts, collision, events, and metadata separate
from generated binaries. Regeneration must preserve authored overrides. Prefer
native source formats; add a narrow adapter when a recurring operation is awkward.
Do not build a second general-purpose engine/editor before proving a real need.

Track asset origin, credits, reuse conditions, palette, target dimensions,
frame order/timing, and import destination. Record tool versions and commands.
Keep creative references and proposals separate from approved game assets.

## Maps

For each requested location, identify recognizable landmarks, what changed in
ten years, the reason for each change, and the player's activities. Use approved
regional architecture, vegetation, terrain, and palette identity. New layouts can
reuse components. Do not copy old story triggers with a donor map.

Keep art, collision/elevation, doors, warps, encounters, and actors consistent.
Validate connectivity and gated paths. Do not remove barriers, demote artwork,
or insert placeholder props silently to make a check pass. Review a location's
readability at native game scale; a large attractive overview alone is insufficient.

## Characters

Agents produce the complete asset set: design references, pixel cleanup, palette,
all overworld directions/movement frames, battle front/back frames, and any
auxiliary animation cells. Follow actual target definitions, not DS dimensions
or the assumption that every character uses the same sheet layout.

Check identity, outfit, handedness, baseline, frame alignment, transparency,
and motion. Inspect and fix defects before presenting the result. Do not describe
image-model output as plug-and-play until it has been integrated and verified.
Do not generate replacement Pokemon designs; source suitable canonical sprites.

## State and save safety

Trace flags/variables through code, scripts, initialization, and global callbacks
before retiring or reallocating them. Preserve engine systems. Use reviewed
healing/shop/trainer/item templates for the fresh campaign. Temporary state,
persistent state, and ordered stages have different lifetimes; do not mix them.

Use one source of truth for each gate or badge, with adapters for engine checks.
Do not double-store derived state without an explicit synchronization contract.
Optional discoveries need independent flags. Central stage counters alone do not
prove that every progression order is valid.

Measure packed save boundaries and checksums when changing storage, dex, flags,
or layouts. A schema number does not migrate shifted bytes. Do not silently reset
old saves. Before tester releases, support a tested migration or clearly identify
incompatible development builds. Keep backup/recovery behavior intact.

## Validation

Use focused checks for the changed behavior: compile and structural validation,
then new-game initialization, event preconditions, one-time rewards, return travel,
and persistence as appropriate. Validate normal saves by fully closing and
restarting the emulator. Savestates are debugging conveniences, not save tests.
Record base revision, configuration and build identity with test evidence.

Once visual work is requested, inspect at native resolution and in motion.
Use in-game captures for final visual claims. Label mockups, off-line previews,
unimplemented interactions, and placeholders explicitly. The owner reviews
finished proposals; the owner is not the first person to discover obvious defects.

## Handoff

Report changed files, actual checks, results, remaining limitations, and concrete
creative judgments needed. Preserve existing dirty work. Do not repeatedly ask
permission for already authorized implementation or repairs. Record accepted
changes in the appropriate shared document; avoid divergent per-model policies.
