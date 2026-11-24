# Violet gatehouse exteriors, installed without repacking Violet

These scripts put the approved Johto gate exteriors (as drawn at fork commit 68ef781f) into
Violet City while leaving every other pixel alone. They were run from a scratch folder and
keep its paths (`S=`); set those before re-running.

Order: `analyze.py` (which cells change, which layer tiles are new), `hidden2.py` (lower tiles
that can share a tile because the difference is hidden under opaque upper pixels), `banks.py`,
`recolor.py`, `recolor2.py` (the lake island moves off palette bank 2, which the gate takes),
`build.py` (gate cells, the tree row under each gate moved up 8 px, trees behind Sprout
Tower's spire, island tiles merged until everything fits), `write.py`. `run.sh` does the last two
from a clean checkout of Violet's tilesets and layout.

Inputs the scripts expect: `old/` (an export of Violet's tilesets, layout and map at 68ef781f) and
`violet-base.png` / `violet-old.png` (renders of the base and of 68ef781f).

Check after a run: render the map and diff it against the base. Changes belong only to the two gate
areas, rows 0-2 behind Sprout Tower, rows 70-71 and the island (see
`gba/art/violet-gates/4-every-changed-pixel.png`).

## Round 3 (2026-11-24): tree rows by the gates, the house, behind Sprout Tower

`trees.py ENGINE OUT.pkl`, then `write.py ENGINE OUT.pkl` (fix the palette files' line endings after:
only the files whose colours changed should show in `git status`). It runs on the installed map, not
on the base, and rebuilds only the cells whose picture changes.

What it does, and the rules it follows (AGENTS.md on branch `claude/celadon-city`, "Converting a
Gen 4 map" and the depth rule):

- **Trees by the gates.** Distances are measured on the finished Route 31 and Route 36 gates: the row
  behind the gate has its crown top 32 px above the gate art's origin (trunk feet 8 px behind the roof's
  top edge, trunks showing at the roof corners), and the row in front has its crown top 96 px below the
  origin (tips 10 px over the ledge). Violet's forest lattice is on even rows, 16 px off both, so the two
  rows between each of those and the untouched forest sit 40 px apart instead of 32. The column beside the
  stairs keeps the lattice because the paving's corner is walkable there.
- **Painter's order from whole cut-outs.** Ground, trees behind, gate, trees in front. The tree cut-out is
  read from the lone tree's own tiles (never keyed by colour); the gate is `gate15.png`. Each 8x8 tile is
  then split by palette family: lawn below and tree on top; where the gate is in front of a tree, the gate
  on top and lawn plus tree below in the tree bank; where a tree is in front of the ledge, lawn plus ledge
  below and the tree on top. Hidden pixels are free, which is what keeps it inside the tile budget.
- **The house.** The house at (9..13, 33..38) copied tile for tile to (69..73, 38..43), standing on the
  north edge of the road so the paving meets its door step. Ground quarters take the new spot's ground.
  The door is solid: there is no interior for it.
- **Behind Sprout Tower.** Rows 3 and 4 under the top roof (columns 36-42) are open ground with layer
  type normal, so the roof draws over the player. Same tiles: the roof was already all on the top layer.
- **Border.** `border.bin` is the forest's own four metatiles (12, 13, 4, 5). The old border metatiles
  (684-687) lost their tiles in the earlier gate install, because that install only counted tiles the
  map's cells use. Anything that frees tiles has to count the border block as well.

Budget after the run: 1 tile slot free, no palette slot free in the lawn banks. Two lawn pixels at
(74, 59) differ by one shade from the plain lawn tile there (a mirrored baked tile is reused).

Check: `tools/gba/maps/violet_city/runtime.py` (both gates, the tree rows blocking, the house door,
behind Sprout Tower, every door).
