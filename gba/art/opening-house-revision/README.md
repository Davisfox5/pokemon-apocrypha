# Opening-house corrections — September 27

Source: `tools/vendor/gba/opening-house-work`, isolated from production and the
active editor. Patch: `gba/opening-house-revision.patch` over
`tools/vendor/gba/floccesy-polish-work`. The previous opening patch and recorded
playthrough remain preserved. This revision includes an **unfinished native
Pokégear prototype**, not a complete HGSS replacement.

## Corrected house behavior

- Welcome: player (4,4) faces east; Mom (5,4) faces west before the room fades in.
- Mom walks to (2,7), faces north, and blocks departure while the PC is pending.
- On returning from upstairs, Mom waits at (3,3). Player walks from the stair
  landing (2,2) to (2,3); both face one another for the Pokégear handoff.
- Mom then walks to (3,5), beside the moving box, faces south, and keeps that
  position after saving or revisiting. Stage-based positioning reconciles map
  transitions, rather than relying on a single fixed object position.
- Stair entrances are the red landings on the **right** of each stair graphic:
  1F (2,2), 2F (2,3). They use directional left stair warps. Arrival animates
  toward the right. Walking north onto a landing does not automatically warp.
  The old lower stair cells are blocked as scenery.
- Door exit/return cells are (2,7)/(3,7), one tile above the prior cells. Exterior
  destination remains the existing Cherrygrove house door. Exit guard moved up
  correspondingly; optional boxes and the classic PC remain intact.

## Evidence

`evidence/house-review.png` contains actual background-core frames. Male and
female traces record Mom/player coordinates and facing at the guard, stair
arrival, handoff, unpacking, and re-entry. Ordinary New Game input and menu
Save/cold Continue were used; no test warps or direct save/state writes.

Both appearances pass: welcome facing, guarded exit, sideways stair round trip,
PC Potion once, classic PC menu, Mom handoff, outdoor door round trip, ordinary
save/Continue at stages 1/2/4 and after gear settings, then reopening the gear.
Pokégear input also exercises 12/24 hour display, preset storage/recall,
no-signal tuning, calling/hanging up, all six palette choices, tab navigation,
last-page persistence, and return to the field menu. This does **not** prove the
missing features in the Pokégear status document.

No desktop game or emulator window was opened. Production `game/`, the active
Porymap project, owner saves, and other previews were not installed or replaced.

## Reproduce

1. Apply the tracked patch to the recorded isolated baseline.
2. Build with `gmake -j8 TOOLCHAIN=<absolute GBA toolchain path>` inside that source.
3. Compile `tools/gba/maps/opening_house_revision_runtime.c` against libmgba.
4. Extract the symbol names used by the harness from `pokeemerald.elf`; run with
   ROM, symbol file, output directory, and optional `female` argument.

Save variables 0x40F8–0x40FC were audited for existing use; they were unused
constant definitions only. Gear settings use existing save storage. No save
block size, PC capacity, automatic checkpoints, or gameplay configuration changed.
