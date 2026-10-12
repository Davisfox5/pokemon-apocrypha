# Cohesive Johto correction

This generator revises Claude's Route 29/30, Route 31 and New Bark in a fresh
`routes-baseline` engine worktree. It leaves the accepted Cherrygrove primary,
town cells, flags and encounters intact. Earlier draft generators and artifacts
remain available under johto-connections, hgss-connections and johto-polish.

Run `python3 tools/gba/maps/johto_cohesion/build.py WORKTREE` on the recorded
routes baseline (05566fe9). The corresponding source patch is applied after the
existing production mechanics, Claude Cherrygrove and Claude route patches.

Tall grass uses HGSS archive files/a/0/4/4, member 2, TEX0 `egrass`, decoded by
our existing NARC/TEX0 tools. The committed decoded PNG is a reproduction input
when the optional donor checkout is absent. Provenance lives alongside the art.
Native masks distinguish interior grass from bladed boundaries, avoiding the
previous mirrored quadrant bands. Building pixels derive from accepted
Cherrygrove indexed house/gable assets. New Bark's larger shell repeats cleaned
roof and timber modules and has one central aligned entrance. Four additional
houses share those building assets and connect to two residential streets and a
central north–south path. This extension is a design proposal, not approved canon.

Route 31 retains the measured complete HGSS cliff silhouette and terraces.
Interior opaque cliff tiles are reduced to source representatives to fit GBA
capacity; transparent edges and the cave opening remain measured source pixels.
The native compiler uses two real layers for overlapping scenery palettes.
Route 29/30 keep original map events and encounters; their original closed gate
and houses have not gained invented events or Route 46 access.

Run `runtime.py WORKTREE OUTPUT --toolchain TOOLCHAIN` with the documented
libmGBA flags to verify ordinary input, door returns, seams and cold Continue.
Porymap-compatible layouts and tilesets are authored directly; no cloud GUI
Porymap roundtrip is claimed. Full Violet City, full Dark Cave, bespoke interiors
and windmill animation are outside this exterior correction. Visual review must
consider gameplay frames as well as decoded whole maps and passing tests.
