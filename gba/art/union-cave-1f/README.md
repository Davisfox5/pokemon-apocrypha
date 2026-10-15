# Union Cave — stone stairs, smooth rock shading and fitted thresholds

Native source **`ab04d9792ea5c36233a3ef2ff0c410b46b6658b6`**, branch `codex/union-cave-1f`,
[draft engine PR #9](https://github.com/Davisfox5/pokeemerald-expansion/pull/9).
This corrects the preceding `de6922a` pass across 1F, B1F and B2F.
[B1F review](../union-cave-b1f/README.md) · [B2F review](../union-cave-b2f/README.md).

## Visual review

- [Southern entrance: previous / replaced / actual gameplay](evidence/south-entrance-before-after.png)
- [Entrances, stairs and rocks: HGSS / de6922a / corrected native](evidence/entrances-rocks-before-after.png)
- [Whole original / native 1F](evidence/comparison.png), [native gameplay](evidence/gameplay-gallery.png)
- Source/native panels: [north](evidence/material-comparison-1.png), [middle](evidence/material-comparison-2.png), [south](evidence/material-comparison-3.png)
- [Every wall cell, source / native, with coordinates](evidence/wall-cell-review.png)
- [Original HGSS stone-step texture and native up/down assets](evidence/stone-stairs-reference.png)
- Preserved passes: [de6922a](evidence/previous-de6922a/comparison.png), [6abf7e84](evidence/previous-6abf7e84/comparison.png)

## Corrections and material checks

Rock and wall shading receives bounded cleanup within the same material. This
removes isolated resampling noise without blurring floor into wall, cutting rock
silhouettes or changing their base footprints. Beige formations remain boulders.
Complete teal rock heads retain their separate native foreground layer.

The previous independent RGB tile substitution could replace part of a wall with
an incompatible piece. Native packing now requires the **same exact 8×8 material
mask** for every substitution: floor, wall, water and void outlines cannot be
exchanged. Spare glyphs cover the largest remaining shading/border errors. Shared
wall palette ramps prevent palette changes across ground/water banks. Compact
floor, water and plateau texture families are reserved instead of flattening them.
Interior shading still uses a finite 1,008-tile dictionary; this is not a claim of
pixel-exact source RGB or extracted original DS collision.

The approved northern light/threshold treatment remains pixel-identical in its
48×32 protected region. A literal copy to the southern warp row was rejected:
the southern rock rim has a different baseline, and the northern west corner
turns downward. The replacement fits the approved light **four pixels higher**
than that literal translation, replaces the full rim and straight shoulders,
and omits that corner. Local open floor stays open; there is one continuous rim
rather than a stacked border or hanging pillar. The southern exterior is still
unwired and remains blocked beyond its threshold.

All eight stair markers now use native stone treads derived from **the actual
HGSS Union Cave `d_level01.png` texture**, with ascending/descending variants.
No Emerald wooden ladder artwork remains in the current assets. The existing
native warp behavior 97 remains appropriate for instant cave floor transitions.
[Texture provenance and checksums](source/hgss-textures/provenance.json) credit
Nintendo / Game Freak / Creatures and the Kuramapika1 texture rip hosted by The
Models Resource. The overview references remain hosted by Bulbagarden Archives;
original event records come from pret/pokeheartgold.

| Native stair pair | Return destination |
| --- | --- |
| 1F north `(5,5)` | B1F main `(31,35)` |
| 1F water-separated south `(7,57)` | B1F lower west `(4,48)` |
| B1F lower east `(29,46)` | B2F northwest `(4,5)` |

The two other B1F markers still reference unpictured Alph rooms. Route32's two
external entry cells, return warp and IDs remain unchanged. The accepted 34×60
first floor, 36×52 B1F and 40×47 B2F registrations remain; these projected overview
images are not decoded DS collision. [Original registration](source/warp-registration.json)
and [event records](source/hgss-events.json) preserve the distinction.

## Verification

- Local ROM build passed. Actual Porymap 6.3.1 exports match native decoding on
  all three floors with zero pixel differences; no desktop game was opened.
- All 5,792 collision/elevation entries are byte-identical to `de6922a`.
  [Preservation](evidence/physics-preservation.json) and [native audit](evidence/all-floors-audit.json).
- Every actual background quadrant is checked against its tile bytes and material
  silhouette; wall cells have coordinate-labelled source/native review sheets.
  [Wall review](evidence/wall-review.json).
- Layered Porytiles imports round-trip 128 representative metatiles per floor
  with zero RGB/alpha errors. Foreground RGB, opaque backgrounds and tile budget pass.
- Native walking, Route32 entry/return, all three stair pairs in both directions,
  controlled existing-engine Surf/disembark, the southern threshold/barrier, and
  separate ordinary 128KiB saves/cold reload/title Continue on all floors pass.
  [Exact source, ROM hash and phase results](evidence/all-floors-build.json).
- Copies of three preceding proof saves reload/Continue; originals are untouched.
  [Compatibility scope](evidence/previous-save-compatibility.json). These are
  development proof saves, not arbitrary campaign-save qualification.
- Repeated authorized packing is byte-identical across 117 native asset/layout
  files. [Reproducibility](evidence/reproducibility.json). Shared art, Route32,
  existing map IDs and warp definitions remain unchanged. CI status is separate
  from the local build and owner visual acceptance.

## Concrete remaining scope

The pictured floor sections and their three internal stair pairs are built.
Original warp records also name upper Alph transit rooms **outside these overview
images**; those rooms and their destinations are not invented here. Two B1F stair
markers remain unwired for that work. Route33 exterior is also pending. The fixed
Strength boulder preserves its barrier; pushing is not implemented/qualified here.
Water art is static. Campaign actors, items, encounters, Lapras and Surf badge/party
activation remain separate work. Surf proof setup initializes the existing engine
state on water; it does not grant a campaign HM or change progression gates.

## Editable source and isolated reproduction

Edit committed layouts/assets directly in Porymap. Do not replay provenance tools
over owner edits. Current fingerprints or an exact preserved baseline are required;
never bypass a guard refusal. Previous source and evidence are preserved under
`previous-de6922a/`; the earlier `previous-6abf7e84/` remains intact.

For this correction, start with an **isolated, unchanged `de6922a` engine checkout**
and this hub branch, then run from the hub:

```sh
python3 tools/gba/maps/union_cave/polish.py
python3 tools/gba/maps/union_cave/refine.py /path/to/engine 1f
python3 tools/gba/maps/union_cave/refine.py /path/to/engine b1f
python3 tools/gba/maps/union_cave/refine.py /path/to/engine b2f
make -C /path/to/engine -j8
python3 tools/gba/maps/union_cave/runtime_all.py /path/to/engine /new/runtime-output --toolchain /path/to/arm-toolchain
# Separate saves: --save-floor 1f or --save-floor b1f, with new output directories.
```

`trace.py` / `trace_basements.py` and `register_floors.py` document the preceding
floor reconstruction; do not run them after this cleanup or replay the old 1F
`build.py`. `refine.py ENGINE FLOOR --check-only` verifies ownership without writes.
The canonical dictionary preserves geometry and deterministic tile ordering.
`compile_porymap_probe.py` links the actual Porymap exporter; `review_all.py`
takes engine/export paths; `check_art.py` takes engine/Porytiles/floor paths.
`publish_all.py` records the committed source hash. No ROMs, player saves or tool
binaries are committed. Visual acceptance remains with the owner.
