# Trees round a gatehouse

Owner rule, 2026-11-25. Applies to every Johto gatehouse on every map.

Every Johto gatehouse gets its trees laid out the way the finished Route 31 gate has them, plus one
row of trees directly under the gate. This is the accepted result at both Violet City gates
(`tools/gba/maps/violet_gates/trees.py`). Do it this way first time, on every map:

- Behind the gate: rows on the forest's normal 32 px spacing, the last row with its crown top 32 px
  above the gate art's top-left pixel. Its trunks tuck 8 px behind the roof and show only at the roof corners.
- Under the gate: one row with its crown top 96 px below that same pixel, tips 10 px over the ledge,
  then the rest of the forest on the normal spacing.
- Never change the spacing between rows, never leave a lawn strip or a doubled row where the gate's
  rows meet the forest. If the forest beside the gate is off those rows, move that whole strip of
  forest (its columns, map edge to map edge) by half a tree so its rows land on the gate's rows.
  A stagger against the neighbouring forest is fine.
- No tree over walkable paving. The column beside the stairs steps down half a tree if the paving's
  corner is walkable there.
- Whole tree cut-outs drawn in order (ground, trees behind, gate, trees in front). No clipped or doubled
  trees and no background inside a tree tile.
- Anything that frees tileset tiles counts the layout's border block as in use.

## Gatehouse interiors and links

Both Violet gates use the shared Johto gate room (`LAYOUT_VIOLET_EAST_GATE` / `LAYOUT_VIOLET_WEST_GATE`
on `data/layouts/JohtoGate`, tilesets `johto_gate`): HGSS's east-west gate, a mat on each side wall, an
officer behind the counter. Each mat is an arrow warp. Every stair cell outside warps to the mat on its
side, and each mat leads back out to the first stair cell on that side. `tools/gba/maps/violet_city/runtime.py`
walks Violet, gate, route and back through both gates.
