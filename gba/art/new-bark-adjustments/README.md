# New Bark Town: mailbox, lab and housing adjustments

Source: `Davisfox5/pokeemerald-expansion`, branch `codex/new-bark-layout-adjustments`, commit `e20ef274d3bb4e52ce3979818a90dcbdb0e57660`, [PR #7](https://github.com/Davisfox5/pokeemerald-expansion/pull/7) against `apocrypha` (`2722eaf`). The owner approved the overall existing town and requested only these local changes. Visual review is pending.

- [Updated town](evidence/new-bark.png)
- [Before/after](evidence/before-after.png)
- [Native gameplay gallery](evidence/gameplay-gallery.png)

## Requested edits

Remove the two stray mailboxes. Put one native Cherrygrove mailbox beside each of the seven houses, with a clear door approach. These remain decorative props; no new interactions or dialogue are added.

Move the accepted lab from (11,0) to (12,0), exactly one cell east. Preserve its building tiles and door identity; its door moves from (16,6) to (17,6). Add two complete trees immediately west at (10,0) and (10,3), blocking the old side passage. The shift consumes one column of the two trees formerly on the right, so their remaining halves are removed rather than leaving partial trees. The new west pair replaces them. Block access through the roof footprint; there is no walkable backyard strip above it.

Move Residence 1 from (9,26) to (8,24), Residence 2 from (23,26) to (24,25), Residence 3 from (9,35) to (10,32), and Residence 4 from (23,35) to (22,34). Reconnect the paths with continuous native Cherrygrove edges. Residence 1 has a blue roof and Residence 4 a purple roof. Their existing shapes, walls, doors and interiors are retained.

The two other central houses, upper house, windmills, flowers, signs, eastern water, outer woods and other maps are preserved outside the explicitly affected cells. All map, warp and event IDs stay stable. Interior return warp IDs are unchanged.

## Native import and verification

This is a scoped committed-block editor, not a replay of the town generator. Existing building words move directly from the baseline; ground edits are limited to the changed boundaries and vacated/occupied cells. Roof variants append metatiles without changing existing IDs. Existing referenced tile glyphs, metatiles and attributes are preserved; seven new glyphs occupy unreferenced zero padding at slots 982-988. Static graphics never enter the door-animation scratch area at 1008-1023. The library remains 496 secondary tiles and 431 secondary metatiles. Supported palette banks 12 and 9 hold the roof variants. The lab and purple-gable facade animation are refreshed so they keep their correct colors during entry; other door animations are unchanged.

Porymap 6.3.1 project-core export matches the native decoder. No manual desktop UI save is claimed. Pixels outside the requested edit mask are unchanged. Town connection camera and cached glyph checks pass against both production Route 29 and its separately accepted `6f7661e9` reconstruction. Other map exports are unchanged. Native collision verifies eight reachable door approaches and blocks the lab side/roof passage.

The local ROM and [project CI build](https://github.com/Davisfox5/pokeemerald-expansion/actions/runs/38455412022) pass. The broader upstream matrix is still running at verification. Headless libmGBA walks the town with ordinary inputs, enters and returns through all eight doors, checks all seven mailbox bases and the lab-side barrier, crosses the Route 29 connection both ways, saves 128KiB ordinary flash and reloads through cold resume and title Continue. Fixture positioning is used for isolated lab collision probes and final save placement; the door/mailbox tour uses normal walking. Gameplay images are inspected after door animations, not only before them. All seven mailbox heads match the native reference pixels after the tour (5-bit color expansion applied; player hat overlap excluded). The source authoring procedure reproduces committed engine bytes exactly. Passing checks is not owner visual acceptance.

## Source and reproduction

`source/baseline` preserves the committed town and native libraries. `source/edited-cells.npy`, `source/mailbox-source.png` and the authoring scripts preserve scope and art provenance. Previous Route 29 and Route 30 work remains on its own source/evidence branches; this PR does not overwrite it.

Use an isolated checkout of the stated base. These scripts record this owner-authorized correction; do not replay them over later owner edits. The final map is editable directly in Porymap.

```sh
python tools/gba/maps/new_bark_adjustments/edit.py /path/to/apocrypha-src
python tools/gba/maps/new_bark_adjustments/door.py /path/to/apocrypha-src
make -C /path/to/apocrypha-src -j1 generated
make -C /path/to/apocrypha-src -j8
python tools/gba/maps/new_bark_adjustments/runtime.py /path/to/apocrypha-src /new/output --toolchain /path/to/toolchain
python tools/gba/maps/new_bark_adjustments/review.py /path/to/apocrypha-src /porymap/export /baseline/export /runtime/output /accepted/route29/source
```

The source-art palettes and indexed graphics derive from accepted Cherrygrove and New Bark native assets. No ROMs, player saves, credentials or tool binaries are committed. There are no changes to story roles, quests, mechanics or save structure.
