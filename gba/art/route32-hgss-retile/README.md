# Route 32 — HGSS retile comparison drafts (not validated)

Three ways of making Route 32 look like the HGSS original, compiled from the HGSS overview
pixels by `tools/gba/maps/route32_hgss_retile/compile.py` on top of the cleanup commit
`48cefd3d`. Each variant is on its own engine branch (`claude/route32-hgss-A/B/C`) for comparison
only: no ROM was built, no Porymap export or headless tour was run, and the square/glyph
vector quantisation still leaves local mis-merged squares. The approved Violet Center is kept in all three.

| Variant | What comes from HGSS | Sheets |
| --- | --- | --- |
| A | every square (trees, lawn, paths, grass, cliffs, water, docks, railway, gate, signs) | [whole map](variant-A/whole-map.png), [north](variant-A/detail-north-gate-terraces.png), [cliffs](variant-A/detail-cliffs-and-stairs.png), [railway and docks](variant-A/detail-railway-docks-pylon.png), [pier and Center](variant-A/detail-lower-pier-center.png), [cave](variant-A/detail-cave.png) |
| B | terrain and structures; the accepted Cherrygrove tree squares stay | [whole map](variant-B/whole-map.png), [north](variant-B/detail-north-gate-terraces.png), [cliffs](variant-B/detail-cliffs-and-stairs.png), [railway and docks](variant-B/detail-railway-docks-pylon.png), [pier and Center](variant-B/detail-lower-pier-center.png), [cave](variant-B/detail-cave.png) |
| C | rock faces/tops, water, shores and boulders only; everything else as the cleanup | [whole map](variant-C/whole-map.png), [north](variant-C/detail-north-gate-terraces.png), [cliffs](variant-C/detail-cliffs-and-stairs.png), [railway and docks](variant-C/detail-railway-docks-pylon.png), [pier and Center](variant-C/detail-lower-pier-center.png), [cave](variant-C/detail-cave.png) |

Each sheet is original HGSS / current cleanup / variant, coordinate-labelled. Logs with budgets
and the sprite squares replaced are in `variant-*/log.json`.
