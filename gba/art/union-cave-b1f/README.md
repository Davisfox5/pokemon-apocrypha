# Union Cave B1F — original HGSS reconstruction

Native source `ab04d9792ea5c36233a3ef2ff0c410b46b6658b6`, branch
`codex/union-cave-1f`. [Shared cave review, checks and reproduction](../union-cave-1f/README.md).

- [Whole original / native map](evidence/comparison.png)
- [Actual native gameplay](evidence/gameplay-gallery.png)
- Original/native detail panels: [north](evidence/material-comparison-1.png),
  [middle](evidence/material-comparison-2.png), [south](evidence/material-comparison-3.png)
- [Numbered HGSS reference](evidence/numbered-hgss.png)
- [Native audit](evidence/audit.json), [packing](evidence/packing.json),
  [build identity](evidence/build.json)

Grid: 36×52, 16×16 native squares registered to the pictured HGSS scene.
Original reference, event records and registration are preserved under `source/`.
This is visual material interpretation plus the actual original warp topology,
not extracted DS collision. Native rock silhouettes, background/foreground layers,
base footprints and low shores remain separate editable data. Sprite/item pixels
are removed with local terrain repairs; campaign actors are not baked into art.

B1F retains both pictured disconnected sections. The main entrance `(31,35)`
returns to northern 1F `(5,5)`. The lower western bank `(4,48)` returns to the
water-separated 1F pocket `(7,57)`; Surf across that chamber reaches the lower
eastern stair `(29,46)`, connected to B2F `(4,5)`. The two upper-left stair markers
reference Alph transit rooms omitted by the overview; their destinations remain
unwired. The original fixed Strength rock remains a barrier; pushing is pending.

Porymap export matches native decoding with zero pixel differences. Layered
Porytiles RGB/alpha checks pass. Native stair travel, walking barriers, controlled
existing-engine Surf movement/disembark and ordinary save/cold reload/Continue are
verified. Campaign Surf activation/Strength rules and animated water are not
qualified by these map tests. No ROM/save/tool binaries are committed.

Current correction: bounded rock/wall cleanup, geometry-constrained tile reuse,
shared wall ramps, and actual HGSS Union Cave stone-step artwork. Collision and
elevation remain identical to de6922a. [Every wall cell](evidence/wall-cell-review.png)
and [decoded tile/material audit](evidence/wall-review.json) document the pass.
Previous source/renders remain under `previous-de6922a/`.
