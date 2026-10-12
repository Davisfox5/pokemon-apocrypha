# Shared-source Pory tools verification

October 12, 2026. The cloud checkout uses the current accepted source at
`Davisfox5/pokeemerald-expansion@2722eaf7601ec02dc5a684fa8cdef9206c0dc377`.
No generators were replayed and no committed layout was redesigned.

[Porymap configuration PR](https://github.com/Davisfox5/pokeemerald-expansion/pull/1)
adds `porymap.project.cfg` and narrows the ignore rule to `porymap.user.cfg`.
This chooses the correct Emerald base for checkouts named `apocrypha-src` and
shares portable project settings. Existing handwritten `.inc` script mode is
retained; the build already compiles new `.pory` files automatically.

Actual Porymap 6.3.1 loader, renderer and save code were exercised with the
cloud-only offscreen adapter in `tools/gba/maps/shared_source/porymap_probe.cpp`.
These are terrain/layout exports from Porymap, not emulator gameplay captures:

- [Cherrygrove](evidence/CherrygroveCity.png)
- [Route 29](evidence/CherrygroveRoute29Approach.png)
- [Route 30](evidence/CherrygroveRoute30Approach.png)
- [New Bark and accepted laboratory](evidence/NewBarkTown.png)
- [Route 31](evidence/JohtoRoute31.png)
- [Violet entrance](evidence/VioletCityEntrance.png)

New Bark's Porymap save preserved all map values, including custom `region` and
`build_target` fields, warps and connections. It reordered JSON keys; that
formatting-only change was discarded. All layouts and tilesets stayed
byte-identical, and all source map files are unchanged in the proposed PR.
The adapter exercises editor code without claiming a manual GUI roundtrip.

Poryscript 3.6.1 compiled an isolated fixture. Host tools, serial generated data,
and parallel ROM compilation pass locally with GCC 14.2.1. The tested ROM hash
is in `evidence/build.json`. No emulator or game was launched on the owner's
computer; ROMs, saves and tool binaries are not committed.

Porytiles 2.0.0 runs here and is available for new PNG tilesets. Existing accepted
tilesets were not imported or repacked. The optional porygon MCP server exposes
29 callable tools, reads the maps/connections and validates scripts. Its current
validator falsely reports `ITEM_POTION` undefined because that item is a C enum,
not a define; the source assigns it 28 and builds successfully. MapScripts
unused-label warnings also overlook map-header references. Preserve the actual
item IDs; see `evidence/porygon-limitations.json`.

Evidence records the expansion config commit and its accepted map-source parent.
Use `docs/GBA_SHARED_SOURCE.md` for future work; the old patch stacks are history.
