# Shared Pokémon Center and Pokémart art

Owner direction, 2026-10-14: copy and paste approved Pokémon Centers and Pokémarts across maps instead of rebuilding them for each town or route.

Reusable copies are committed in `gba/art/shared-building-art/`: `pokemon-center.png` with its bank-8 palette, and `poke-mart.png` / `poke-mart.indexed.png` with the shared Mart palette and brandmark. Their exact source hashes are in `provenance.json`.

The canonical Pokémon Center is the finished Violet City asset at `gba/art/violet-city/source/materials/center.png`, hub commit `1c8e61c317a870910ef099af7851144549480b12`, engine commit `9037554c61833a5f8f7da175d45420b4797bafde`. Route 32 carries an exact copy and its provenance under `gba/art/route32-hgss-blocks/source/shared-art/`. Reuse its pixels, silhouette, palette, footprint and compatible door animation. Change placement and door destinations for the local map.

Pokémarts follow the same reuse rule: use the established shared Johto Mart asset (`tools/gba/maps/johto_mart/assets.py` and `gba/art/johto-mart/source/` on the Violet source branch), rather than drawing another store. Route 32 has no Pokémart in its HGSS layout.

A later owner-approved revision to either shared building should become the new canonical source. Preserve the source commit and propagate deliberately; do not regenerate owner-edited layouts to update a building.
