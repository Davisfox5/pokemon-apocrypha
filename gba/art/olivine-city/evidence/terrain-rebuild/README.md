# Olivine rock courses and stair rebuild

The first terrain pass was rejected. This revision removes its complete rock
paint layer, including fragments in mixed 8px squares, and replaces it with
traced wall courses and the established native Johto wall vocabulary.

**Native source:** [PR #21](https://github.com/Davisfox5/pokeemerald-expansion/pull/21),
commit `601d1b073e4e4723066a3dc88c679c21d317991b`.
[Terrain-only source diff](https://github.com/Davisfox5/pokeemerald-expansion/compare/c26b9b21d095ca6e0f8a7e5a46a091bc82701e52...601d1b073e4e4723066a3dc88c679c21d317991b).
Owner visual acceptance remains pending.

## Review the actual change

Each comparison uses **HGSS reference / rejected first pass / rebuilt native**
in that order, with identical registration and crop scale.

- [Whole map comparison](whole-map-before-after.png), [rebuilt native map](native-map.png)
- [Lighthouse courses and complete returns](lighthouse-courses-before-after.png)
- [Three-course guide](course-guide.png)
- [Upper stairs and retaining shoulders](upper-stair-before-after.png)
- [Timber ramp and continuous wall backing](timber-ramp-before-after.png)
- [Northern branches and terrace ends](northern-branches-before-after.png)
- [Western wall and beach return](western-wall-before-after.png)
- [Eastern shore courses](eastern-shore-before-after.png)
- [Actual gameplay gallery](gameplay-gallery.png), [individual native captures](gameplay/)
- [Numbered HGSS grid](reference-grid.png), [native grid](native-grid.png)

## Wall structure and materials

The northwest forest has a single retaining course that continues down the west
city edge and turns into the beach boundary. The northern retaining face,
residential terrace, forest course and short Route 39 spur have separate traced
runs and their own caps, elbows and endings. The upper terrace's inward corner
uses the opposite handedness from the eastern shore; this was inspected and fixed
at the join into the lighthouse's west-facing wall.

The lighthouse headland has **three visible courses**, with cap lines near source
rows 576, 600 and 624 and the shore contact near 648. Each course has its own
front, side return and toe. The stepped eastern outline continues through the
shoulders instead of stopping at a rectangle. Bare rocky shoulders use a top-plane
texture, rather than a repeated vertical wall. The eastern shoreline likewise
uses three separate stepped courses, following the original reference bends.

Route 36's native cap/face/toe and corner family is the donor from engine
`698db52a184083687d354452f3bd1c8f2791d23b`, on the Violet–Goldenrod/Ecruteak
approach. The plateau-grain donor comes from Route 31 on
`1643f58a48f0d98c1179d68a6223994f69db7ae0`. Original donor masters and exact
coordinates are preserved in [native-donors.json](../../source/terrain-rebuild/native-donors.json).
Native 8px caps and complete 16px face/toe portions assemble the observed 24px
course pitch without rescaling. Five face shades and two separate top-plane
shades preserve texture and silhouette while fitting the BG bank budget.

The upper stair opening is a complete opaque 48×24 native seat. The central
unscaled treads retain their direction; the cheeks meet the retaining walls and
paving begins outside the foot, rather than appearing through it. The timber
ramp retains its direction and silhouette over continuous retaining stone. Its
previous grey rectangular backing is removed.

These are local course/face interpretations of the HGSS overview. Hidden terrain
and absolute DS z values are not extracted or asserted. Whole crowns, native
service buildings, architecture, props and the existing layout registration are
preserved. No town-placement generator was replayed.

## Actual checks and scope

Porymap 6.3.1 project exports match decoded native output pixel for pixel. The
cell audit checks all 4,032 collision/behavior entries, complete roots/crowns,
visible shared artwork and connected architectural approaches. The native maps
use 769 glyphs in the city, 910 in the quay and the unchanged 312 in the harbor;
all remain below the reserved 1,008-glyph ceiling.

Headless mGBA checks pass the upper stairs in both directions, timber ramp in
both directions, closed approaches, north/west retaining walls, upper headland
face, eastern shoulder, curved beach return, quayside barriers, both district
crossings and ordinary flash save, a fresh-process reload and title Continue.
The source and ROM identities are in [preservation.json](preservation.json),
[build.json](build.json) and [runtime.json](runtime.json).

The pixel audit finds **zero visible changes outside the wall/stair scope**.
Only the private city/quay tilesets and their layouts change in this source
commit. Native Harbor files, all other maps, map/layout/warp/event IDs and
integration registries remain unchanged. Earlier evidence and saves are retained.
The first terrain pass is historical evidence, not an accepted design.

The existing three district fades, static ocean, closed interiors and unwired
Routes 39/40, actors, shops and shipping services remain as before. Hosted CI
status is [recorded separately](hosted-ci.json); local checks do not establish owner visual approval.

The narrow native patch and checks live in `tools/gba/maps/olivine_city/`:
`rebuild_terrain.py`, `terrain_palettes.py`, `review.py`, `runtime.py`, and
`publish_terrain.py`. The terrain patch takes only immutable rejected source
`c26b9b21`; it refuses later committed layouts. The current committed native
source remains the editor after this revision. Editable course/role records,
material/traversal arrays, native-derived planes, donor masters and target ramp
are retained under `source/terrain-rebuild/`. Exact bank covering never substitutes
an unrelated tile or removes a silhouette to fit capacity.
