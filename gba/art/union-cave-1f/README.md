# Union Cave — refined first floor and connected basements

Current source: `de6922a964721aceb11147bcac6acadc477d4538` on
`codex/union-cave-1f`, [draft engine PR #9](https://github.com/Davisfox5/pokeemerald-expansion/pull/9).
This refines the owner-liked first pass and adds the pictured HGSS B1F and B2F
sections. [B1F review](../union-cave-b1f/README.md) · [B2F review](../union-cave-b2f/README.md).
Exact source/ROM identity and checks are in [all-floors-build.json](evidence/all-floors-build.json).

## Review

- [Entrances and rocks: HGSS / previous / refined close-ups](evidence/entrances-rocks-before-after.png)
- [Whole HGSS / native first floor](evidence/comparison.png)
- [First-floor gameplay](evidence/gameplay-gallery.png)
- Original/native terrain panels: [north](evidence/material-comparison-1.png),
  [middle](evidence/material-comparison-2.png), [south](evidence/material-comparison-3.png)
- [Numbered original reference](evidence/numbered-hgss.png)
- [Preserved preceding pass](evidence/previous-6abf7e84/comparison.png)

## Corrections

Small teal rock formations now retain their complete silhouettes, dark centers,
shadows and native foreground layers. Beige boulder shapes and both lighted cave
thresholds retain their source detail instead of using approximate texture glyphs.
Foreground, ladder, boulder, shoreline and outside-boundary glyphs receive priority;
only spare interior background texture variants are approximated. Six private
native palettes and route-local glyph banks leave Cherrygrove/Route32 art unchanged.
The [packing audit](evidence/packing.json) records zero foreground RGB errors and
zero transparent background quadrants. Representative Porytiles imports use the
actual background/foreground layers rather than flattening incompatible palettes.

**The beige formations at `(6,16)` and `(29,38)` are boulders, not stairs.**
Original HGSS event data places the northern 1F stairs at the northern branch end
and the southern stairs in the water-separated western pocket. The native
registrations are `(5,5)` and `(7,57)`. Clean Emerald Cave ladder art (`0x205`) is
used for the native stair markers, with a matching floor/lip. The original overview
omits those dynamic stair markers; they are registered using its landmarks and the
actual original warp destinations, not guessed from the beige rock drawings.

The three visible stair pairs work in both directions:

| 1F / B1F source | Destination |
| --- | --- |
| 1F north `(5,5)` | B1F main section `(31,35)` |
| 1F southern pocket `(7,57)` | B1F lower western bank `(4,48)` |
| B1F lower eastern bank `(29,46)` | B2F northwestern entrance `(4,5)` |

Route32 warp IDs and both exterior entry cells are preserved. They land at the
interior threshold `(28,19)` and walk normally onto `(28,18)`; returning uses the
native south-arrow warp. The southern lighted threshold is aligned to `(28,58)`;
its Route33 destination remains unwired rather than substituted with another room.

## Reference and native interpretation

The accepted 34×60 first-floor proportions remain. The 544×962 overview is mapped
to 16×16 native squares, omitting two bottom border pixels. These images are
foreshortened/cropped DS scenes, not raw DS collision grids. Actual DS world X/Z
coordinates therefore cannot be pasted into the screenshot grid: stair locations
are registered against original actor/item landmarks and the pictured branch ends.

[Original event records](source/hgss-events.json) and
[registration/provenance](source/warp-registration.json) preserve the exact DS
warp graph and source revision. Original image URLs, checksum and credits are in
[reference.json](source/reference.json). Terrain, foreground silhouettes, base
footprints, low shores and native water planes are editable separate source data.
Original characters/items are removed from terrain artwork with explicit wall,
shore and floor repairs; no campaign content is invented or baked into the map.

## Validation

- Local ROM build; actual Porymap 6.3.1 project export matches every native pixel
  on all three floors. No desktop game is opened.
- 5,792 native cells checked against the reviewed material/foot model, actual
  behavior, collision, elevation, palette and tile entries. This is **not a claim
  of extracted original DS collision or exact color-majority matches**.
- Native water uses collision `0`, elevation `1`, and `MB_POND_WATER`; ordinary
  land is elevation `3`. Walking is blocked by elevation while Surf works.
  Two B2F low shoreline lips remain walkable banks, not raised rock walls.
- Porytiles round-trips 128 representative layered material metatiles per floor
  with zero native RGB/alpha errors.
- 398 native observations cover original walking barriers, complete rock layers,
  exact Route32 landings/return, all three stair pairs both ways, existing-engine
  Surf movement and disembark at the pictured banks, plus ordinary 128 KiB flash
  saves/cold reload/title Continue separately on every floor.
- Copies of preceding first-floor and Route32 proof saves also reload/Continue;
  their originals are untouched. These are proof saves, not a promise about every
  campaign save. Existing map/layout/named-location IDs remain stable; two maps
  and layouts append. Shared art and Route32 files are byte-identical.

## Concrete remaining scope

The pictured floor sections and their three internal stair pairs are built.
Original warp records also name upper Alph transit rooms **outside these overview
images**; those rooms and their destinations are not invented here. Two B1F stair
markers remain unwired for that work. Route33 exterior is also pending. The fixed
Strength boulder preserves its barrier; pushing is not implemented/qualified here.
Water art is static. Campaign actors, items, encounters, Lapras and Surf badge/party
activation remain separate work. Surf proof setup initializes the existing engine
state on water; it does not grant a campaign HM or change progression gates.

## Editable source and reproduction

Edit committed native layouts/assets directly in Porymap. Authoring scripts are
provenance; do not replay them over owner edits. Owned-file fingerprints refuse
changed maps/assets. The older `build.py`/`runtime.py`/`review.py` describe the initial
first-floor proof; use the refined all-floor tools for this revision.

From an isolated copy of the preceding `6abf7e84` engine source:

```sh
python3 tools/gba/maps/union_cave/trace.py
python3 tools/gba/maps/union_cave/trace_basements.py
python3 tools/gba/maps/union_cave/refine.py /path/to/engine 1f
python3 tools/gba/maps/union_cave/refine.py /path/to/engine b1f
python3 tools/gba/maps/union_cave/refine.py /path/to/engine b2f
python3 tools/gba/maps/union_cave/register_floors.py /path/to/engine
make -C /path/to/engine -j1 generated
make -C /path/to/engine -j8
python3 tools/gba/maps/union_cave/runtime_all.py /path/to/engine /new/runtime-output --toolchain /path/to/arm-toolchain
# Separate save proofs: append --save-floor 1f or --save-floor b1f, with new outputs.
```

The guard recognizes the exact preserved `6abf7e84` baseline through its Git
revision and `source/previous-6abf7e84/` fingerprints; the current fingerprint
describes the committed refined result. `refine.py ENGINE FLOOR --check-only`
checks owned source without authoring.
Do not bypass a guard refusal over later owner changes. `compile_porymap_probe.py`
links the provided exporter against an already-built Porymap tree. `review_all.py`
takes the engine and export directories; `check_art.py` takes engine, Porytiles
binary and floor key. `publish_all.py` ties the final runtime runs to the engine
commit, preserving earlier evidence. No ROMs, player saves or tool binaries are
committed. Source artwork: Nintendo / Game Freak / Creatures; reference hosted by
Bulbagarden Archives; event metadata from pret/pokeheartgold.
