# Pokégear world atlas — user artwork trial

The source is the image supplied in the September 27 conversation. Its original
JPEG is retained byte for byte in `reference/world-map.jpg` (SHA-256
`9007f4c6f0e8052d26d4e05db8c15ed4e35e3bead20a4fab6743f3704f288b2c`).
`tools/gba/maps/build_pokegear_world_atlas.py` makes a 416 × 256 world canvas and
five 208 × 128 crops, all from that single image with one fixed 16-color palette.
The GBA viewer shows the whole world, zooms and pans over it, and cycles the
five approved playable-region details. Other labels in the supplied artwork
are visual geography; they do not grant travel or chapter content.

This is device cartography. It does not edit overworld map tiles, collision,
warps, encounters, or region availability. The viewer deliberately does not
claim a precise player marker on this composite artwork until field coordinates
are calibrated to it; the bottom line gives the game's current map name.

The source was built in the isolated `tools/vendor/gba/opening-house-work`
checkout with the pinned 14.2 ARM toolchain. A headless libmGBA run passed the
Pokégear service qualification, including Map Card navigation, five regional
views, notes, radio/phone services, and a cold Continue. Native 240 × 160 captures
are in `gba/art/pokegear-services/evidence/map-world-overview.png`,
`map-world-detail.png`, and `map-region-1.png` through `map-region-5.png`.
The Map Card was granted explicitly by that qualification fixture; the
chapter's real Gold handoff is not verified by this test.

An exact source snapshot of the isolated changes is in `source-overlay/`, with
SHA-256 hashes in `source-overlay/SHA256.json`, so no new engine change exists
only in the dirty workbench. This overlay also captures the **unfinished**
Chapter 1 draft currently in that workbench; it is not a ready-to-apply final
campaign patch. Production `game/` was not modified.
