> Historical depth revision. The owner liked the improved depth but rejected the remaining tree-shaped terrain gaps. Use the [counted groves and completed receiving surfaces](../forest-refinement/README.md) for current review.

# Olivine — fresh terrain after both rejected attempts

The owner rejected `601d1b07` and requested a fresh start. This version discards
that wall-strip assembly and builds new native terrain from the HGSS contours:
connected faces, small intermediate shelves, rounded returns, complete stair
openings, and the southwest outcrop omitted from the earlier versions.

**Source:** [`116ea8011c958d10bf5d61daf2d879cca9e8a184`](https://github.com/Davisfox5/pokeemerald-expansion/commit/116ea8011c958d10bf5d61daf2d879cca9e8a184),
[existing draft PR #21](https://github.com/Davisfox5/pokeemerald-expansion/pull/21).
[Terrain-only change from the rejected version](https://github.com/Davisfox5/pokeemerald-expansion/compare/601d1b073e4e4723066a3dc88c679c21d317991b...116ea8011c958d10bf5d61daf2d879cca9e8a184).
**Visual acceptance is pending.** The earlier versions remain preserved as rejected evidence.

## Review

The comparisons show **HGSS / rejected 601d1b07 / fresh native assembly**, at the
same registration and scale. The gameplay images come from the built ROM.

- [Whole-map comparison](whole-map-before-after.png) · [native map](native-map.png) · [2× native map](native-map-2x.png)
- [Lighthouse courses and returns](lighthouse-courses-before-after.png) · [three-course guide](course-guide.png)
- [Northern branches and residential shelves](northern-branches-before-after.png)
- [Western retaining wall](western-wall-before-after.png) · [restored southwest rock spur](western-rock-spur-before-after.png)
- [Eastern shore and recessed terraces](eastern-shore-before-after.png)
- [Upper stair opening](upper-stair-before-after.png) · [lighthouse timber ramp](timber-ramp-before-after.png)
- [Actual gameplay gallery](gameplay-gallery.png) · [individual captures](gameplay/)
- [Numbered original grid](reference-grid.png) · [numbered native grid](native-grid.png) · [actual Porymap exports](porymap/)

## What changed

The old independent strips were replaced by a fresh trace of the original visible
landforms. The narrow western faces now connect to the three southern lighthouse
courses; the east shore follows its individual recessed steps. Rounded source
ends and shoulders are retained. The exposed upper residential shelf receives a
complete return where the smaller native tree no longer hides the original end.
The western beach has its original raised rock outcrop again.

The two timber openings include their full treads, rails, abutments and receiving
ground. Purple and neutral rock shadows are retained in the material mask; they
no longer become false green cracks. Detached original tree-root/prop fragments
are removed from the rock layer, while the complete native foreground remains.

Long straight stretches use explicitly selected, same-facing original texture
cores. Native conversion retains seven rock shades and compact ground textures.
Compatible edge templates move a contour at most one pixel while preserving its
corner occupancy, connected components and edge contacts. Texture representatives
are restricted to the same front/east/west/top plane. The editable adaptation
records disclose these choices; this is not a claim of pixel-identical DS rendering.

## Verification

- Actual Porymap 6.3.1 exports and decoded native pixels agree exactly.
- All **4,032** cells pass the independent collision/behavior audit. Building
  approaches remain reachable; **235** complete trees retain distinct roots.
- Shared foreground pixel checks pass. **136,805** visible pixels change, with
  **zero** changes outside the terrain/stair receiving scope.
- City uses **924**, Quay **997**, and unchanged Harbor **312** scenery glyphs,
  within the 1,008 available slots per district. City/Quay use 13 BG banks.
- The local Arm GNU 14.2.1 build passes. mGBA 0.10.5 passes **37** observations,
  covering both stair directions, wall/outcrop barriers, ordinary district travel,
  closed service entrances, flash save, cold reload and title-screen Continue.
- Native changes are confined to **55 City/Quay layout and private tileset files**.
  Map/layout/event/warp IDs, registries, Harbor source and other maps are unchanged.
- No hosted workflow run was returned for this commit; the PR remains draft.
  [Hosted status](hosted-ci.json).

ROM SHA-256: `b084c5c1e79367f811cb57ae6ebdeafc0daf85a015d5dd0d108557a8d9d881e0`.
No ROM or save is committed.

[Build identity](build.json) · [runtime results](runtime.json) · [native audit](review.json)
· [source/preservation manifest](preservation.json) · [visual review record](visual-review.json)
· [per-cell ledger](cell-ledger.json) · [editable terrain source](../../source/terrain-reset/README.md).

The elevation/course interpretation comes from the visible HGSS overview, not
extracted DS heights or collision. Existing native architecture/tree footprints,
static water, three ordinary-fade districts, closed interiors and unwired
Routes 39/40/shipping remain exterior-proposal limitations.
