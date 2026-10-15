# Johto trees: transparent master review

This is the next shared-asset category after the accepted service buildings.
**Source artwork only; no map/ROM rollout is claimed.**

Open [the comparison sheet](review/trees-over-terrain.png). Left to right:
cleaned transparency, then the same cleaned object over actual
HGSS grass, dirt and rock texture samples. The textures are isolated inspection
swatches, not a proposed map layout. Pink foliage remains Cherrygrove-only.

| ID | Tree | Cleanup |
|---|---|---|
| T01 | Shared large green tree | Removed 197 ground-shadow pixels; full canopy/trunk unchanged |
| T02 | Shared pink tree | Same mask as T01; Cherrygrove only |
| T03 | HGSS green-fruit apricorn | Removed ground shadow; extended original extraction to recover the complete trunk |
| T04 | HGSS pink-fruit apricorn | Recovered original foliage/fruit colors; removed ground shadow |
| T05 | Emerald Cut tree | Already transparent; all four frames preserved |

T03 and T04 use measured source crops from the Route 29/30 HGSS renders. The
previous Route 30/36 small-tree import forced foliage through the large-tree
palette and lost its green detail. The replacement keeps the original RGB values
and needs its own appropriate native palette allocation. Harvest behavior is
outside this artwork change; no new interactions are implied.

## Files and reuse

- `source/T*.png`: transparent RGBA masters, empty pixels fully zeroed.
- `source/T*.idx.png`: exact indexed equivalent, palette index 0 transparent.
- `catalog.json`: provenance hashes, native sizes, anchors and Cut frame layout.
- `review/*-removed-mask.png`: white pixels mark only the removed ground.
- `source-inventory.json`: matching aliases and retirement status.
- `retired-assets.json`: 44 deleted obsolete asset files; the checker forbids restoration.
- `locked-designs.json`: fixed hashes for the owner-selected large and Cut trees.
- `source/T05-intact.png`: the single intact native Cut frame shown in the catalog.
  `T05.png` remains its complete four-frame native animation sheet, not four designs.

The shared large-tree import is identical across Cherrygrove, Route 30, Route 36
and Violet source assets. The Johto synthesis authoring path also imports it for
New Bark and the earlier routes. Duplicate snapshots are inventoried, not offered
as separate designs. At the owner's direction, superseded canopy/trunk studies,
old apricorn cutouts and unused catalog alternatives were deleted. No obsolete
standalone tree assets are kept as selectable historical references. Full reference
map renders and unrelated regional artwork are outside this cleanup. Five current
large-tree source copies now match the cleaned Cherrygrove master exactly. The old
HGSS helper and blossom builder also load the selected masters rather than making
an alternate crop or recolor. The old terrain extractor no longer emits tree variants.
The existing native Cut source is indexed without relying on PNG alpha metadata:
index zero, rather than its displayed RGB, determines transparency.

The general object rule is in AGENTS.md. Terrain belongs on the destination's
lower layer. At integration, do not bake a grass oval into the tree or replace
rock behind a crown with lawn. Preserve route barriers, overlap priority and
native sprite anchors. These review anchors describe the new master canvases;
old placement origins require conversion, especially the 16x32 apricorn imports.
Do not overwrite approved maps using their historical generators.

## Reproduction and checks

```sh
python tools/gba/maps/johto_common/trees.py --engine /path/to/apocrypha-violet
python tools/gba/maps/johto_common/check_trees.py
```

Dependencies: Pillow and NumPy. Source engine revision is in `catalog.json`.
The tool only writes this review pack. It asserts that cleanup preserves every
retained source RGB pixel and that every indexed export decodes exactly back to
the RGBA master. All five families fit a single 4bpp palette each: 7–12 opaque
colors plus transparent index zero. This is per-asset compatibility, not a claim
that destination maps have sufficient free palette/tile slots.

Reviewed the generated sheet at native-pixel magnification: trunks and foliage
remain intact, the green terrain ovals are gone, and Cut animation particles are
preserved. Native map compilation and gameplay checks belong to installation;
no emulator was launched for this source-only change.

Original artwork: Game Freak / Nintendo / Creatures. Reference source hashes and
crop coordinates are recorded rather than treating the assets as original art.
