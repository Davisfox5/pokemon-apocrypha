# Johto shared building review: Centers and Marts

## Simple review

- **C01:** current Cherrygrove Center.
- **C02:** current Violet Center; recommended shared Center, with the softer edge treatment.
- **M01:** the original shared Johto Mart, already approved October 14. Preserve this design.
- **M02:** older HGSS shop still used in Cherrygrove; shown to make the rollout difference clear.

Choose a Center ID or describe changes to it. The Mart does not need approval again. No building is replaced during this comparison step.

[Current Centers](centers-current.png) · [Current Marts](marts-current.png) · [Earlier Centers](c-earlier.png) · [Earlier Marts](m-earlier.png)

The current sheets show source-sized silhouettes at 3x and decoded native map contexts at 2x. The source transparency is preserved; transparent entrance/ground areas are not missing pixels. Older sheets retain the original saved defects and cutout remnants for identification; they are not proposed finished assets. An earlier standalone sign may be separate from its building in the original package.

## Coverage

The agreed map scope is New Bark, Route 29, Cherrygrove, Route 30, Route 31, Violet and Route 36. Only Cherrygrove and Violet have Center/Mart exteriors in those sources. Their current versions are shown above. Houses and area-specific landmarks form a separate building group; this comparison covers the two common service buildings.

The inventory contains 8 Center variants and 11 Mart variants, including four current entries. Identical tight RGBA art is deduplicated; its aliases remain in [catalog.json](catalog.json). Earlier Center and Mart files from Johto v1-v4, the Johto restart, Cherrygrove art study, Claude's Cherrygrove, B/C references and saved Violet Mart revisions are included where available. Concepts from other regions are outside this Johto review.

## Evidence and provenance

Current Center and Cherrygrove Mart pixels were sampled from the native engine map using their existing source alpha. The locked M01 asset hash and every opaque pixel were checked against its recorded approval and current Violet map. The read-only generator verifies that engine Git state does not change. No ROM build or gameplay run is needed for this unchanged-art inventory; it is not a new integration claim.

All item IDs, source paths, source revision, dimensions and RGBA hashes are recorded in the catalog. Original project art and game-derived HGSS material retain their source credits. Reproduce with the porygon Python environment:

```sh
python tools/gba/maps/johto_common_review/service_buildings.py /path/to/engine
```
