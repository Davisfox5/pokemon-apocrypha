# Fresh Olivine terrain source

Input: decoded native `116ea801`'s parent, rejected
`601d1b073e4e4723066a3dc88c679c21d317991b`. The native baseline planes are retained
in `../terrain-rebuild/`; the new terrain does not reuse its strip assembly.

Geographic authority: [HGSS Olivine overview](https://archives.bulbagarden.net/media/upload/f/f6/Olivine_City_HGSS.png),
retained at `../hgss-reference.png`, 1035×858. Registration remains native
**(+64,+16), no scaling**, on the 72×56 Gen 3 metatile grid. Region corners are
read at pixel/8px quadrant resolution. Route36/Route31 wall evidence was inspected
for plane direction and depth; this reset uses Olivine's own visible contours and
texture cores instead of shortening and repeating the rejected Route36 modules.

- `contours.json`: individual source landform outlines and local course counts.
- `repeated-runs.json`: same-facing donor/target rectangles; turns and endpoints
  are excluded from long-run repetition.
- `background.png`, `foreground.png`: editable native planes; original shared
  foreground is preserved apart from the explicitly rebuilt stairs/ramp.
- `rock-layer.png`, `wall-mask.png`, `scope-mask.png`: stone geometry and local
  receiving-ground footprint, separate from traversal.
- `material-grid.npy`, `ground-material-grid.npy`: independent material labels.
- `solid.npy`, `behaviors.npy`, `above.npy`: native traversal/layer ledgers.
- `local-course-count.npy`: local maximum-course annotation, not DS z data.
- `native-tile-adaptation.json`: exact native contour/texture packing limits.
- `removed-occlusion-fragments.json`: removal of detached source-original
  root/prop remnants; complete native foreground roots remain separate.
- `hidden-background-reuse.json`: invisible background reuse, zero visible changes.
- `olivine_city/`, `olivine_quay/`: Porytiles layer sheets and palette constraints.

`tools/gba/maps/olivine_city/reset_terrain.py` is this revision's narrow authoring
record. It refuses a different native HEAD and unrecognized local changes.
It must not be replayed over the newly committed layout or later owner edits.
`reset_tiles.py` constrains native edge reuse by topology and a maximum 1px
contour displacement, and restricts texture representatives to the same face
orientation. These are documented GBA adaptations, not extracted DS tiles.
No original town placement generator was replayed.

Validation and reproduction entry points (read-only against the committed source):

```sh
QT_QPA_PLATFORM=offscreen olivine-export ENGINE_CHECKOUT EXPORT_DIRECTORY
python3 tools/gba/maps/olivine_city/review.py ENGINE_CHECKOUT EXPORT_DIRECTORY terrain-reset
python3 tools/gba/maps/olivine_city/runtime.py ENGINE_CHECKOUT NEW_RUNTIME_DIRECTORY --toolchain ARM_ROOT
python3 tools/gba/maps/olivine_city/publish_reset.py ENGINE_CHECKOUT RUNTIME_DIRECTORY EXPORT_DIRECTORY
```

The runtime harness requires libmgba flags as documented in the shared workflow.
The exporter is the existing Porymap 6.3.1 native project exporter. Source, ROM
identities and actual results are in [the evidence](../../evidence/terrain-reset/README.md).
