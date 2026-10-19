# Ecruteak City — HGSS-based native exterior

[Native source PR #19](https://github.com/Davisfox5/pokeemerald-expansion/pull/19).
Engine source `dbf53f6f3975eb20179c26badd6ba48169857ad1`, based on the latest
Azalea source `d822306675`. This is an exterior proposal for owner visual review.
The source PR remains a draft: local validation passed, but no hosted CI run has
started. See [observed hosted status](evidence/hosted-ci.json).

## Visual evidence

- [Whole native map](evidence/native-map.png), [2×](evidence/native-map-2x.png)
- [Registered original/native comparison](evidence/reference-comparison.png)
- [Original grid](evidence/reference-grid.png), [native grid](evidence/native-grid.png)
- [Burned Tower](evidence/Burned-Tower-comparison.png), [temple and pond](evidence/temple-pond-comparison.png)
- [Residential courts](evidence/residential-courts-comparison.png), [civic buildings](evidence/civic-buildings-comparison.png)
- [Gym and torii](evidence/Gym-torii-comparison.png), [grove outcrop](evidence/grove-outcrop-comparison.png)
- [House material correction](evidence/house-material-before-after.png)
- [Actual gameplay gallery](evidence/gameplay-gallery.png), [individual captures](evidence/gameplay/)
- [Cell ledger](evidence/cell-ledger.json), [native checks](evidence/review.json), [visual findings](evidence/visual-review.json)

## Reference and interpretation

Original: [HGSS Ecruteak overview](https://archives.bulbagarden.net/media/upload/7/77/Ecruteak_City_HGSS.png),
1032×785. Source (0,0) registers to native (64,16), without geometric scaling.
The complete exterior occupies 72×52 native 16px squares. Outward padding completes
tree crowns and the clipped side gates. This is an overview reconstruction, **not
extracted DS collision, height data or hidden terrain**.

The northwest Burned Tower and its nested stone courses, south-facing stairs,
northeast temple entrance, angular spring pond, stepped paving boundary, ten
residential/civic courts, Gym, Dance Theater and southern torii follow the original
arrangement. The western grove's small outcrop and the boulder beside the pond
remain stone foregrounds over independent ground. Materials and authored
traversal are recorded separately for all 3,744 native squares.

The approved Center, Mart and G02 gates are reused. Four local house fronts share
a material-aware fifteen-color ramp that protects violet glazing and green
sliding doors instead of allowing roof colors to erase them. The ruined tower,
temple, Theater, Gym and torii retain original architectural silhouettes and
textures. The Gym's central wooden roof spine is opaque, not an accidental hole.
Source masks, native masters and palette covering are editable under `source/`.

All 447 trees use complete shared T01 crowns, with distinct 2×2 root footprints.
Autumn variants change only leaf colors; trunk pixels and silhouettes remain.
Residential planting uses two complete crowns on a 32px pitch, matching the tall
original groups. Source masters and visible approved shared pixels are checked by
hash and native RGB5 comparison. No nearest-tile replacement is used.

## Native adaptation and scope

Two rendering districts preserve room for landmark art: the temple district uses
994 glyphs / 362 metatiles, and the city 925 / 398. Both use thirteen BG banks,
with the final sixteen glyph slots available for later door work. The split is
at global native row 27 (source y416). Travel across the avenue uses a short
ordinary map fade, not a seamless scrolling connection. Landing one square inside
the receiving district prevents immediate retriggering; this is an explicit
traversal adaptation. Paving borders avoid a fabricated forest across the street.

Shared service buildings require adapted receiving courts and approaches. Gates
and boundary trees need outward padding; local residential tree groups snap to
the native grid. The paving retains a compact 16px original texture core; terrain
corners, silhouettes and stair treads take priority over spare texture variants.
The stone stairs, small stone props and fence use adjacent native material ramps.
Foreground artwork and ground underneath stay separate. Fully hidden background
quadrants are compacted without changing any visible pixels.

Building interiors, tower interiors, Bell Tower path, adjoining Routes 37/38/42,
campaign actors, dialogue, encounters, shops and Gym mechanics remain unwired.
Closed entrances are tested as closed approaches. No original-game story triggers
or unapproved narrative changes were imported. The exterior is accessible through
the existing native map-proof entry points until adjoining areas are integrated.

## Validation and preservation

Actual Porymap 6.3.1 project exports match decoded native output pixel for pixel.
The audit checks all native map collision/behavior entries, complete tree bounds,
distinct roots, visible shared pixels, and reachability of the landmark approaches.
Headless libmGBA 0.10.5 tests pass for ordinary walking, the Burned Tower stairs,
forest/fence/pond/post barriers, both district travel directions, and closed doors.
Ordinary flash save, a fresh emulator load and title Continue pass on the same ROM.
Native 1× gameplay captures were inspected. These checks do not establish owner
visual acceptance or compatibility with an unavailable preexisting player save.

Exact identities and checks: [build](evidence/build.json), [runtime](evidence/runtime.json),
[preservation](evidence/preservation.json), [reproduction](evidence/reproduction.json).
Existing map IDs and art are preserved. New maps append at group 80, IDs 51–52.
The PR is stacked on current Azalea work; its body links the Ecruteak-only delta.

First-authoring provenance: `assets.py`, `build.py ENGINE PORYTILES_LEGACY`, then
`register.py ENGINE` under `tools/gba/maps/ecruteak_city/`. Native maps become the
editor after creation; the builder refuses committed layouts. Porytiles 2.0.0
compiles the layers using exact Z3 palette covering, then the result is partitioned
at the engine's stable 512 primary/secondary boundary. Run `review.py` against
actual Porymap exports and `runtime.py` against a newly built ROM for later edits.

Original geography and game artwork: Game Freak / Nintendo / Creatures. Shared
project artwork and revisions are recorded in `source/shared-provenance.json`.
No ROMs, saves, credentials or tool executables are committed.
