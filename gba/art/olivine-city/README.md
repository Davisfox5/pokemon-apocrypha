# Current revision: counted groves and complete receiving surfaces

**[Review the native map, before/after comparisons, row counts and trees-hidden terrain](evidence/forest-refinement/README.md).**
Native source `8eb23f6774fd937f3018d413f1fab5b6dc8d05c8` is on existing
[draft PR #21](https://github.com/Davisfox5/pokeemerald-expansion/pull/21).
The owner liked the groves and improved depth; the remaining tree-shaped gaps
prompted reconstruction of the receiving surfaces and eastern planted shelf.
Acceptance of this completed revision remains pending. Earlier images below
are historical.

---

# Olivine City — HGSS-based native exterior

[Native source PR #21](https://github.com/Davisfox5/pokeemerald-expansion/pull/21),
engine source `c26b9b21d095ca6e0f8a7e5a46a091bc82701e52`, stacked on Ecruteak `dbf53f6f3975eb20179c26badd6ba48169857ad1`.
The source PR remains draft: no hosted CI run was returned; local validation passed.
See [hosted status](evidence/hosted-ci.json). Exterior proposal for owner visual review. Geography follows the HGSS original;
this does not implement Olivine's interiors, campaign events or shipping services.

## Review

- [Native whole map](evidence/native-map.png), [2×](evidence/native-map-2x.png)
- [HGSS/native comparison](evidence/reference-comparison.png)
- [Original grid](evidence/reference-grid.png), [native grid](evidence/native-grid.png)
- [Lighthouse and cliff joins](evidence/lighthouse-comparison.png)
- [Residential streets](evidence/residences-comparison.png)
- [Quay and moorings](evidence/quay-comparison.png), [terminal](evidence/terminal-comparison.png)
- [Civic hall](evidence/civic-hall-comparison.png), [service buildings](evidence/service-buildings-comparison.png)
- [Gameplay gallery](evidence/gameplay-gallery.png), [individual frames](evidence/gameplay/)
- [Before local join cleanup](evidence/before-join-cleanup.png)
- [Cell ledger](evidence/cell-ledger.json), [native audit](evidence/review.json)
- [Visual findings and adaptations](evidence/visual-review.json)
- [Source and ROM identities](evidence/preservation.json), [runtime checks](evidence/runtime.json)

## Reference and native interpretation

Original: [HGSS Olivine overview](https://archives.bulbagarden.net/media/upload/f/f6/Olivine_City_HGSS.png),
1035×858 pixels, preserved under `source/hgss-reference.png`. Source (0,0) maps to
native (+64,+16), without geometric scaling. The native exterior is 72×56
16px squares. Outward padding completes the original clipped perimeter crowns.
This is a reviewed overview reconstruction, **not extracted DS collision,
height data, event data, or hidden ground**.

The city retains the north road, western beach opening, original civic building
footprint, three residences, café, Center/Mart lots, east stair lane, lighthouse
headland and ramp, broad quay, three parasols/benches, two sailboats, breakwater
chain, central ferry pier and terminal. Lawn, cobbles, sand, rock planes, water,
wooden decking, foreground features and traversal are authored separately.
Every native square is recorded in the ledger; occluded source ground remains
an explicit interpretation, rather than a claimed original collision match.

The accepted shared Center, Mart, tree and grass masters are reused without
redrawing their pixels. Local architectural silhouettes and texture patterns are
masked from the original. Foreground geometry is never replaced by an unrelated
nearest-color tile. A shared ground palette keeps neighboring cliff, sand and
paving planes coherent; local rock retains seven shades and cobbles four. Sand
grain is preserved explicitly rather than collapsing to a uniform nearest shade.
Sails, fabric and pennants share a compact maritime ramp. Every crown has complete
source bounds and distinct roots; the lighthouse occludes its grove naturally.

Apocrypha canon says Olivine has **no active Gym** (`DESIGN.md`, Johto overview).
The original Gym shell remains in its original lot, with the Gym emblem removed
and a small maritime crest proposed. This is an exterior civic-building treatment,
not new dialogue, lore, a named service, or a functional Gym. The larger future
shipbuilding district described in canon is not invented in this reference pass.

## Adaptations and limits

The approved shared service buildings need local footprint/approach adaptation.
Tree spacing, projected cliff corners, curbs, shore contacts and rock footprints
are registered to the native grid. Hidden terrain and original collision are not
recoverable from the overview. The diagonal lighthouse ramp traverses east/west
in native squares; its complete visible timber slope remains in place.

Three rendering districts preserve the art budget: city rows 0–25, quay rows
26–43, harbor rows 44–55. Travel uses short ordinary map fades at the district
boundaries. This is **not seamless scrolling**; landing one tile inside the next
district prevents immediate return triggers. Borders use local paving/decking
instead of unrelated terrain. The northern district boundary is below the central
house's approach. The city/quay split also divides the distant lighthouse art;
each native map retains its own correct portion, not a seamless shared tileset.

Routes 39/40, building/lighthouse/terminal interiors, transport, NPCs, encounters,
shops, dialogue and campaign progression remain unwired. Unwired approaches stay
closed. Water is a static original texture in this exterior pass. Native proof
entry points provide isolated access while adjoining areas are developed.

## Validation and reproduction

Actual Porymap 6.3.1 offscreen project exports are compared pixel for pixel against
decoded native metatiles/palettes. The audit checks all 4,032 cells, collision,
behaviors, distinct roots, complete crown bounds, visible shared pixels, budget
limits and reachability of each architectural approach. Native gameplay captures
are inspected at 1× and nearest-neighbor enlargement. Headless movement tests cover
stairs, ramp travel in both directions, both district boundaries in both directions,
closed building approaches, benches, railing, cliff, pier/water and unwired edges.
Ordinary flash save, a fresh emulator instance, and title Continue are exercised.
These checks do not establish owner visual acceptance or compatibility with an
unavailable preexisting player save. No desktop emulator is opened on the owner's
machine and no interactive Porymap UI save is claimed.

First-authoring provenance: `tools/gba/maps/olivine_city/assets.py`, then
`build.py ENGINE PORYTILES_LEGACY`, then `register.py ENGINE`. The builder refuses
committed Olivine layouts: Porymap/native source becomes authoritative after first
creation. Porytiles legacy 2.0.0 compiles the exact RGB5 layers with Z3 palette
covering, then partitions them at the stable 512-tile primary/secondary boundary.

For later native changes, run `review.py ENGINE ACTUAL_PORYMAP_EXPORT_DIRECTORY`
and `runtime.py ENGINE NEW_OUTPUT_DIRECTORY --toolchain ARM_PREFIX`. Native map
IDs append at group 80, indices 53–55; earlier IDs and map art are preserved.

Original geography and game artwork: Game Freak / Nintendo / Creatures.
Shared project art provenance is in `source/shared-provenance.json`; local source
masks, palette decisions and texture donors are in `source/local-asset-provenance.json`.
No ROMs, saves, credentials, downloaded dependencies or tool binaries are committed.
