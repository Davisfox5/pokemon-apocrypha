# Route 32 — rebuilt from scratch with HGSS tiles (draft for comparison)

Engine branch `claude/route32-hgss-scratch-15` on the expansion fork (see the commit hash in
[compile-log](evidence/compile-log.json) and the build line below), built on the cleanup
commit `48cefd3d` only for the approved Violet Center prefab and the ported collision.

## What this is

The HGSS overview is a perspective shot with 12.5 px rows, so the earlier retiles sliced it on
the wrong grid and every square came out slightly different. Here the overview is rectified to
16 px tiles (vertical scale 1.28, sub-pixel grid origin found by tile-consistency search), which
makes every HGSS material exactly 2×2 periodic in world space. The map is 32×160, the HGSS size
(5 chunks of 32 rows), rebuilt as two Porymap maps joined by a connection: `JohtoRoute32`
(rows 0–77) and `JohtoRoute32South` (rows 78–159), sharing one primary tileset and each with
its own secondary, so the detail fits the GBA budget at a tight glyph tolerance (12/255 mean).
NPC and item sprites are replaced from clean same-phase donors. Palette banks 0–12 are assigned
per material family (lawn, tall grass, path, tree ×2, rock ×2, water ×2, deck, misc); the
Center's banks 2/7/8 are untouched.

- [Whole map: rectified original / native](evidence/whole-map.png)
- 32-row strips at 3x: [0–31](evidence/strip-000.png), [32–63](evidence/strip-032.png), [64–95](evidence/strip-064.png), [96–127](evidence/strip-096.png), [128–159](evidence/strip-128.png)
- [Native gameplay frames](evidence/gameplay/) from the headless tour (266 observations; whole route walked, seam both ways, Center and cave entry/return, flash save, cold reload, title Continue)
- [Rectified original with sprites removed](evidence/original-rectified-32x160.png)

## Validation

ROM built locally, sha256 `8d64eec513650cc71245859e7dd236bd8c2e55386a0874493b53800c9c448705`. Actual
Porymap 6.3.1 project-core export of both maps equals the native decode on every pixel. Headless
mGBA tour passes all three phases.

## Known defects (not yet hand-fixed)

- Lawn/tall-grass strip under the west end of the railway (rows 83–87, x 1–9) is in the bridge's
  shadow in the overview, so its tiles came out dark and flat.
- Railway top edge (row 78) shows a dotted rail where the overview's edge pixels were sampled.
- A few forest-over-lawn canopy squares (rows 100–125, x 2–7) keep resample speckle.
- Sprite-donor seams at (23,24), (15,32) and the dock arm's top edge.
- Water is static (no animation callback yet); shore lips are the HGSS pixels as sampled.
- Collision was ported from the 128-row layout by row mapping and then overridden by material;
  the tour passes, but every ledge and one-way cell needs a square-by-square check before this
  is more than a comparison draft.

Tools: `tools/gba/maps/route32_canon/` (`rip.py`, `compile_split.py`, `preview_split.py`, `runtime.py`).
Source art: Nintendo / Game Freak / Creatures; overview via Bulbagarden Archives.
