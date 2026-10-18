> Superseded by [the HGSS placement audit](../hgss-placement-audit/README.md). Counts, commits and runtime receipts below describe the initial pass; current images and native-review.json reflect the corrections.

# Route 36 rock family: outdoor rollout

2026-10-17. Native source changes are committed on separate review branches;
they have not been merged into one campaign checkout. Owner visual approval
is pending. The larger HGSS terrain/layout audit remains separate.

## Changed maps

| Map | Native commit | Changed cells | Treatment |
| --- | --- | ---: | --- |
| Cherrygrove | `f5a437d6ff` | 114 | Coastal faces and existing grass cap; shore silhouette retained |
| Route 29 | `880403037e` | 264 | Coastal lookout faces; approved coastal adaptation retained |
| Route 30 | `949948be2f` | 302 | Fronts, mirrored sides and complete grass caps; exact stairs retained |
| Route 31 | `f5a437d6ff` | 181 | Divider, southern terrace and mountain exterior; stone tops retained |
| Route 32 | `077f9a3423` | 419 | Exposed fronts and both side directions; plateau, railway and stairs retained |

Source is the approved `../r02-complete-tiles/source/tiles` family. Placement
ledgers and masks are under `source/`; native exports and every changed unique
cell pair/context are under `review/`.

New Bark and Violet have no comparable exposed cliff faces to replace. Route 36
remains at its approved `5b80e625d1` source. Route 33 has newer concurrent source
at `eb15d8923401af86bb12670c6627c2bfba1e3d0a`, already using this family. That
branch deliberately omits trees for terrain review and was not overwritten.
Union Cave's three floors remain at `fc1017fecad147879de460fcb9727ff63862598b`;
no cave interior source was edited.

## Preservation and validation

- All 1,280 changed cells retain their original collision/elevation and behavior.
  Objects, events, warps and connections are unchanged.
- Owner Route 30 edits (34 cells) are preserved in preceding commit
  `9b7bebc27f3ac13ab923315c868309ed085345ab`; the owner's original checkout is untouched.
- Native decode equals target and actual Porymap 6.3.1 output pixel for pixel.
- 221 distinct before/after cell pairs and their receiving contexts were reviewed.
  The stair exclusion mask and light wall shades were corrected during review.
- Four ARM ROM builds passed. Four background libmGBA runs passed their write,
  cold reload and ordinary Continue phases. Relevant movement, barriers, stairs,
  doors and route connections were exercised. No desktop emulator was opened.
- Exact revisions, ROM hashes and runtime receipts: `evidence/builds.json`.
  These checks apply to each isolated source branch, not a combined future merge.
- Cherrygrove and Route 32 needed lossless private graphics repacking. Animated
  glyphs 0–92, door palette indices and unchanged live metatile IDs are preserved.
  Cherrygrove fills all 1,008 slots; Route 32 has four spare slots. Further art
  additions require another capacity review, not silent color approximation.

The first city runtime fixture incorrectly expected a blocked coastal cap to be
walkable. The fixture was corrected against the original grid; collision was
not modified. A rejected recoloring of Route 31's plateau bevel produced a band;
the final version preserves the original plateau and changes its exposed faces.

## Reproduction

Use an engine clone containing the branches in `evidence/builds.json`, Python
with Pillow/NumPy, and the existing project GBA build tools.

1. `python tools/gba/maps/johto_common/regional_rocks_baselines.py ENGINE`
   materializes exact baseline source files under `/tmp/rock-baselines` from
   the immutable revisions in `source/inputs.json`. It never resets a checkout.
2. `python tools/gba/maps/johto_common/regional_rocks.py` regenerates target art.
3. On a fresh disposable checkout of that map's `baseline_commit`, run
   `python tools/gba/maps/johto_common/regional_rocks.py --engine ENGINE --map MAP`.
   This refuses a changed source grid/render. Do not replay it over owner edits.
4. Build with serial `gmake generated`, then `gmake TOOLCHAIN=ARM` using the
   project's pinned toolchain. Run the matching `regional_runtime_*.py` wrapper
   with `ENGINE FRESH_OUTPUT --toolchain ARM_TOOLCHAIN` and libmGBA flags.
5. `regional_rocks_porymap.cpp` exports actual Porymap maps offscreen. The review
   script checks those exports and emits the complete changed-cell sheets.

Full map images: [Cherrygrove](review/CherrygroveCity-native.png),
[Route 29](review/CherrygroveRoute29Approach-native.png),
[Route 30](review/CherrygroveRoute30Approach-native.png),
[Route 31](review/JohtoRoute31-native.png), [Route 32](review/JohtoRoute32-native.png).
