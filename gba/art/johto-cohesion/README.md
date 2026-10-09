# Connected Johto exterior correction — October 9, 2026

This proposal corrects Claude's Route 29/30 artwork as well as Route 31 and
New Bark. It supersedes the rejected johto-polish proposal; earlier source,
reference art, map patches and workbenches remain preserved. Accepted Cherrygrove
terrain, trees, palettes, town cells, original flags and encounters remain intact.

Route 30's houses and both route gates reuse Cherrygrove architectural pixels.
HGSS `egrass` is decoded directly from the recovered texture archive, converted
to the measured six-color native shadow ladder, and given coherent blade edges.
Two real hardware layers retain scenery colors where palette banks overlap.
Route 30 stair positions remain fixed; path landings continue to their approach.
Route 31 uses the measured complete HGSS cliff silhouette and terraces rather
than repeated multi-terrace crops. Interior texture representatives fit GBA limits.

New Bark retains the HGSS core arrangement and eastern water. The institute is
208×80 pixels with a continuous Cherrygrove roof, timber facade, window bays and
one aligned central entrance. The town expands from 36×24 to 36×44 cells with
four homes on two connected southern streets. Each door has a clear approach
and an independent interior return. This exact extension is a design proposal;
no new roles, dialogue, quests or mechanics are introduced.

## Visual review

Previous Claude routes / rejected town proposals appear on the left of each
whole-map comparison; the correction appears on the right. Images retain native
map pixels and can be opened at full size.

- [Route 29 comparison](comparisons/route29.png)
- [Route 30 comparison](comparisons/route30.png)
- [Route 31 comparison](comparisons/route31.png)
- [New Bark comparison](comparisons/new_bark.png)
- [Violet approach comparison](comparisons/violet_entrance.png)
- [Native route frames](evidence/routes-native.png)
- [Institute and southern housing frames](evidence/new-bark-native.png)
- [Native connection frames](evidence/connections-native.png)
- [Housing walk](evidence/housing-walk.gif)

## Evidence and limits

The cloud ROM compiles with arm-none-eabi GCC 14.2.1. Headless libmGBA 0.10.5
checks cover both directions of Cherrygrove/29, 29/New Bark, Cherrygrove/30 and
30/31; all eight New Bark doors; the Violet gate and cave; grass walking;
residential streets; water collision; ledges; ordinary 128-KiB save and fresh
cold Continue. Results and the tested ROM hash are in `evidence/runtime.json`.
The engine was never opened on the owner's desktop.

The decoded native map checks match authored opaque scenery pixels exactly.
That checks packing fidelity, not owner visual approval. There was no cloud
Porymap GUI save roundtrip. Route 29's existing gate and Route 30 houses remain
closed. Interior rooms are provisional GBA reuse. Windmills and freshwater pond
are static; coastal sea remains animated. Full Violet City and full Dark Cave
are not supplied by this exterior correction.

## Source and reproduction

See [the generator instructions](../../../tools/gba/maps/johto_cohesion/README.md).
Use a clean routes baseline after the existing Claude Cherrygrove and routes
patches; apply `gba/johto-cohesion.patch`, or run the generator. The patch contains
engine source and native map/tileset assets, not ROM/save binaries. A separate
fresh generation is compared with the built source in `evidence/source-manifest.json`.
`evidence/preservation.json` records preserved files and patch checks. The decoded
HGSS input PNG and archive revision/hash are in `references/` and `provenance.json`.
Original source art: Game Freak / Nintendo / Creatures; conversion and modules
reuse the project's accepted Cherrygrove work.
