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
