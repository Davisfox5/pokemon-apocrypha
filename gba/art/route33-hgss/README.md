# Route33 — terrace joins, fitted cave entrance and approach

Engine `codex/route33-hgss`, `eb15d8923401af86bb12670c6627c2bfba1e3d0a`,
[draft PR10](https://github.com/Davisfox5/pokeemerald-expansion/pull/10).
The owner approved the straight shared rock faces, then requested another pass
on blending, terrace levels, incorrect corners, the entrance and its dirt approach.
This revision changes receiving joins and two front placements; it retains the
approved straight texture rather than extending the previous all-face lock.

**This is intentionally a tree-free terrain review.** All88 large trees and both
Apricorns are absent, including border repetitions. Original forest/fruit collision
remains blocked, so this inspection stage contains reserved invisible barriers.
It is not a claim of a finished playable route or accepted art.

## Current receiving-join refinement, 2026-10-18

- [Whole map](evidence/tree-free-map-2x.png) and [HGSS/native](evidence/tree-free-reference-comparison.png)
- [North: HGSS / previous / current](evidence/receiving-joins/north-corners.png)
- [Southeast levels and turns](evidence/receiving-joins/southeast-levels.png)
- [Cave arch and short bordered approach](evidence/receiving-joins/entrance.png)
- [Summit step](evidence/receiving-joins/summit-step.png) and [west return](evidence/receiving-joins/west-front.png)
- [Labelled interpreted planes](evidence/receiving-joins/levels-labelled.png), [receiving profiles](evidence/receiving-join-profiles.json)
- [Independent native checks](evidence/receiving-joins-review.json), [cell ledger](evidence/receiving-join-cells.json), [reproduction](evidence/join-reproduction.json)

R10 was being reused for southern side-to-front turns despite being a north-facing
stacked elbow. Fourteen receiving corners now use the already existing native
mountain modules with the right turn silhouette and plateau backing, fitted to
existing shared stone/plateau palettes. These24px local joins are outside the16px
R02 registry contract; the canonical17 shared PNGs are untouched. Hidden lower
footing corners reuse matching exposed outer turns, not tree-covered source pixels.

The southeast upper fronts now end at252 and324px instead of248/320, matching the
reference projection more closely. Their straight interiors move four pixels
without stretching or recoloring. Northern levels and stepped summit stay distinct;
low bevel pixels receive a small palette fit instead of a solid shade band.
The arch uses the HGSS opening/rim geometry in the existing native palette, centered
on the unchanged warp. Its black interior and dark stone threshold replace the
long offset black cutout. The dirt approach regains the source taper and grass
border using the existing lawn/path palette. Sign-obscured ground is inferred from
adjacent path; the ground layer is separate from foreground art.

120 cells /7,276 visible pixels change versus f3022508;125 cells have layer edits.
All986 native cells match actual Porymap output; collision/elevation and decoded
attributes remain exact. 11,600 untouched straight-front pixels and the moved
southeast interiors match their preceding texture exactly. Nine private native
files reproduce byte-for-byte in a fresh f3022508 worktree using
`receiving_joins.py ENGINE ORIGINAL_NATIVE_214e38cf --install`; it is guarded edit
provenance, not a layout generator to replay over committed source.
`join_review.py ENGINE BEFORE_F3022508 PORYMAP_EXPORT` checks the final native output.
Arm GNU14.2.1 build and27 headless observations pass, including cave travel both
ways, ledges, barriers and ordinary save/cold reload/Continue. A copied f3022508
ordinary save also loads and Continues; its original is unchanged. Current gameplay
frames are in `evidence/gameplay`; plateau camera placements remain visual probes,
not claims of traversable heights.
Current editable layer snapshots are under `source/receiving-joins`; engine source
remains authoritative. Earlier cap/depth evidence below is historical.

## Earlier cap-only refinement, 2026-10-17 (f3022508)

Existing native HGSS-derived bevel modules now carry the plateau texture into the
wall, replacing the flat dark transition bands. A dedicated formerly unused
palette combines five existing plateau highlights with all ten unchanged shared
stone shades. The source silhouettes, baselines and 24px rises stay intact.
No new rock master was drawn; the canonical completed R02 family is unchanged.

- [Northern joins: HGSS / before / current](evidence/cap-blend/north-joins.png)
- [Southeast joins: HGSS / before / current](evidence/cap-blend/southeast-joins.png)
- [West front comparison](evidence/cap-blend/west-front.png)
- [Exact changed pixels](evidence/cap-blend/changed-pixels.png)
- [Independent cap review](evidence/cap-blend-review.json),
  [four-file reproduction](evidence/cap-reproduction.json),
  [prior ordinary-save compatibility](evidence/cap-save-compatibility.json)

90 cells / 7,587 pixels change, entirely within the local bevel masks.
31,154 visible approved-face pixels remain exact, including compatible side and
corner overlaps. Background pixels, map entries, attributes, palette3 and canonical
masters are unchanged. Only private primary glyph/metatile data and palette04
in the Route33 pair change. Actual Porymap export matches all986 decoded cells;
Arm GNU14.2.1 build,27 headless runtime observations, ordinary save/cold reload/
Continue and a copy of the prior74e91ff save pass. Controlled plateau frames are
camera-only observations, not traversal claims.

`blend_caps.py ENGINE ORIGINAL_NATIVE_214e38cf --install` is a guarded one-time
native edit from74e91ff; it reproduces all four files exactly in a fresh worktree.
It is provenance, not an editor to replay over committed layouts. Text guards
allow LF/CRLF checkout differences; generated mapjson includes are excluded.
`cap_review.py ENGINE APPROVED_74e91ff PORYMAP_EXPORT` independently checks final
native pixels, face locks, unchanged map/attributes and actual Porymap output.
Editable current bevel foreground is `source/cap-blend/foreground.png`; its
background is the unchanged `source/terrain-depth/background.png`.

## Earlier depth-pass visual links (updated whole maps above are current)

- [Tree-free whole native map,2×](evidence/tree-free-map-2x.png)
- [HGSS / tree-free native comparison](evidence/tree-free-reference-comparison.png)
- [Northern three terrace fronts](evidence/terrain-depth/north-terraces.png)
- [Northwest exterior face](evidence/terrain-depth/northwest-front.png)
- [Summit step](evidence/terrain-depth/summit-step.png)
- [Southeast two-level formation](evidence/terrain-depth/southeast-levels.png)
- [Southeast receiving inset](evidence/terrain-depth/southeast-inside.png)
- [Gameplay](evidence/gameplay-gallery.png); [controlled north camera](evidence/gameplay/controlled-terrain-north-levels.png), [controlled southeast camera](evidence/gameplay/controlled-terrain-southeast-levels.png)
- [Profiles and placements](evidence/terrain-depth.json), [independent native checks](evidence/terrain-depth-review.json)

## Correct source family and depth

The current source is hub `codex/violet-city` at
`ddafe9de4b923800bc12fc6f54b821469389ae48`, including the **completed** R02 catalog
introduced by `a20fa293`. It supersedes the separate rim/mask method used in the
previous rejected pass. The full seventeen-master catalog and hash-pinned PNGs
are preserved under `source/complete-rocks`; no canonical master is redrawn,
recolored, height-scaled or assembled from separate grass slivers.

The registry limits this family to compatible16px rises and explicitly leaves
different-height mountain/cave caps local. Route33 therefore uses whole uncapped
R02/R04 front, R10 corner and R11/R12 side masters for the16px wall bodies, with
its existing8px mountain bevel above: **24px total per front rise**. The current cap-only pass uses the existing native bevel texture and a transition
palette; their silhouette remains local. No face is vertically stretched. Flat
plateau textures remain separate from the wall planes.

The northern exterior, middle terrace and summit have distinct front baselines:
188,166 and128px, with the summit's eastern return at116px. The southeast raised
L has short/long front baselines248/320px, above the outer platform. The platform's
southern footing is inferred behind the original foliage at360px, using the same
24px profile. All named source/receiving profiles are in the ledger. These are
visual interpretations of the registered HGSS overview, not decoded DS z-values
or new GBA elevation-bit semantics. Parts hidden by original trees remain declared
interpretations rather than source-confirmed geometry.

Inside joins retain their local receiving geometry where the catalog's R17 turn
faces the wrong direction. An incompatible corner is not inserted into the upper
plane. Complete shared corner/side modules handle exposed turns. The accepted
48px cave arch/shoulders, black opening, warps, paths and ledges remain intact.

## Preceding tree-removal/depth pass (74e91ff; retained provenance)

Tree-removal masks use the locked common master silhouettes and original placements.
Two foliage-rim pixels on each boulder were also removed; all stone RGB is retained,
with the prior boulder sources preserved. Ground is inspected across the entire
old object footprint, not just outside its alpha. Foreground foliage pixels are
zero; border art is plain closed lawn. Boulders, sign and ledges remain separate.

- Actual Porymap6.3.1 export equals decoded native RGB for all986 cells.
- 156 whole-master placements,29,799 unoccluded canonical pixels checked with
  zero RGBA differences. Local bevels and overlapped/prop-covered pixels are
  accounted for separately. Raw shared PNG hashes are exact.
- 630 cells change visually. Collision, elevation and decoded attributes are
  unchanged everywhere. All water stays blocked; tree/fruit barriers remain.
- Background outside the two mountain regions is unchanged. Fully hidden opaque
  wall quadrants use a compact existing plateau backing: no visible texture is
  discarded or replaced by a nearest-match tile. Maximum glyph937 is below
  reserved1008–1023; 414 metatiles allocated.
- Nine native files reproduce exactly from6e4d438b with the guarded
  `terrain_depth.py ENGINE ORIGINAL_NATIVE_BASELINE --install`. The baseline is
  native214e38cf for the original mountain surfaces; no layout generator executes.
- Arm GNU14.2.1 builds the ROM. Headless libmGBA0.10.5 checks27 observations,
  including real cave travel, both ledges, ground/barriers, ordinary save, cold
  reload and title Continue. A copied6e4d438b save also loads and Continues with
  its original untouched. Plateau camera placements are controlled visual views,
  not claims that those blocked heights are walkable.

Read-only verification:
`depth_review.py ENGINE BEFORE_ENGINE PORYMAP_EXPORT`, plus
`review.py ENGINE PORYMAP_EXPORT`. Runtime:
`runtime.py ENGINE NEW_OUTPUT --toolchain ARM_ROOT`.
Current source, ROM and runtime identities are in `evidence/build.json`.

## Scope and preserved history

The preceding depth pass changed only private Route33 native map/border/tileset source;
the cap-only refinement changes four private tileset files.
Cave art, events, warps, map IDs, other maps and owner saves are preserved.
`previous-6e4d438b`, earlier snapshots and Git retain rejected drafts. The depth-stage layers remain in `source/terrain-depth`; the subsequent cap-stage
foreground/target and face/mask locks are in `source/cap-blend`.
Current native source is authoritative. Older authoring/repair tools are historical
and must never be replayed over the current map.

Azalea remains unbuilt; west exit closed. Encounters, sign dialogue, actors,
harvest mechanics and campaign triggers remain outside scope. Eastern sea framing
is static. Local tall-mountain caps/inside joins are not falsely advertised as a
finished universal R02 family. The original reference is the528×463 HGSS overview,
origin0,0 registered to16px squares and8px quadrants. CI and owner visual acceptance
remain separate from local verification; the PR stays draft.
