# HGSS rock placement audit — 2026-10-17

Supersedes the first regional rock-family rollout. The earlier pass checked changed tiles but missed placements, including Route 29 inland walls and stair shoulders. This pass compares registered HGSS imagery, the preceding native render and corrected native output on a 16px grid.

## Results

| Map | Additional changed cells | Correction |
| --- | ---: | --- |
| Route 29 | 69 | Four omitted inland wall runs and low ledge palette |
| Cherrygrove | 0 | Approved coastal adaptation retained |
| Route 30 | 158 | East wall direction, stair shoulders, removal of forest rock filler |
| Route 31 | 126 | Missed mountain courses and stair shoulders |
| Route 32 | 776 | Explicit front/side placement; shared native stone-top core |

The CSV files enumerate 2,075 scoped cells. `review/` contains 25 registered comparison pages. Source coordinates, offsets and reference hashes are in `coverage.json`; Route 32 continuous plane rectangles are in `source/route32-planes.json`. Occluded source terrain and approved adaptations are not asserted to be pixel-identical. Source snapshots are image-derived; they do not claim decoded DS collision data.

All five native exports equal the actual Porymap output. Collision/elevation, behavior, objects, warps and connections are unchanged. The remaining original colored Emerald rock pixels are zero on Routes 29–31; original gray stair pixels are preserved. Four ROM builds and four headless write/cold-reload/ordinary-Continue runs pass. Exact commits, hashes and receipts are under `evidence/`. No desktop emulator was opened.

Route 32 retains its original rock-top outline but repeats an existing 32px top texture to reserve room for complete faces. It has 27 spare graphics. Its 16px shared face modules can repeat within taller HGSS courses; this is a native adaptation, not an exact source-art copy.

## Preserved differences and limits

The ten-year town compositions, expanded Cherrygrove harbor, Route 29 coast/lookout, Route 30 owner's 34 local cells and southern adapter, and Route 31 approved pond/cave/sign alignment remain. Existing tree/terrain widths were not globally rebuilt. Full-map HGSS fidelity beyond rock placement remains a separate review. Route 33 concurrent review and Route 36 approved terrain are untouched; cave interiors remain excluded. Separate source branches are pushed but not merged; owner visual acceptance remains pending.

## Reproduce

Materialize baselines with `regional_rocks_baselines.py`, generate/install with `regional_rocks.py` in a disposable matching source checkout, export with the existing Porymap wrapper, run `regional_rocks_review.py`, then `rock_hgss_audit.py`. The latter reads native output and never changes engine files. Native install refuses a changed baseline. See the preceding rollout README for toolchain commands; use the updated commit manifest in this directory.
