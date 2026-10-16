# Rock faces and mountains — comparison inventory

**Start with the [three-way comparison](review/comparison.png), then open the
[category catalog](review.html).** Use the displayed IDs when describing what you
like. This is a review collection; no style has been chosen or installed.

## Collections

| Collection | What it shows |
|---|---|
| [Current Johto](review/current-johto.png) | Six installed rock sections: Cherrygrove, Route 29, Route 30, Route 31 mountain and divider, Route 36 |
| [Existing conversions](review/existing-conversions.png) | Twelve earlier/current source modules, including Cherrygrove B/C and route adaptations; historical examples are labeled |
| [Emerald originals](review/emerald-rocks.png) | Twelve actual map examples: coast, volcano, caves, pale mountain, ice, Navel Rock |
| [FireRed originals](review/firered-rocks.png) | Nine actual map examples: routes, Mt. Moon, Rock Tunnel, Seafoam, Victory Road, Mt. Ember, Cerulean Cave and Sevii |
| [HGSS families](review/hgss-families.png) | Eleven overviews of exterior, cave, snow and ice families |
| [Sinnoh families](review/sinnoh-families.png) | Eight further natural rock, cave and ice overviews from Platinum |
| [HGSS source map context](review/hgss-map-context.png) | Original Cherrygrove, Route 31/Dark Cave and Route 36 map renders |
| Full source pieces, in the catalog | Complete raw faces, caps, corners, cave openings, slopes, snow/ice and related surfaces; searchable by ID or texture name |

The gallery includes full Gen 3 map links and the exact metatile IDs used in each
selected map crop. Gen 4 family overviews preserve whole texture samples; the
individual source cards retain every texel at its original dimensions.

## Coverage and interpretation

- Audited the established seven-map Johto scope. New Bark and Violet do not add a
  separate tall-cliff family; their shorelines and loose rocks remain separate work.
- Read 119 texture members in the local HGSS archive. The original set range is
  0–105; 106–118 are earlier Sinnoh imports (the boundary is recorded in
  `tools/regionport/import_sinnoh.py`). Imported textures have their own collection.
- Surveyed the local Platinum map texture sets as well. There are **291 source
  entries, representing 265 distinct decoded images across both archives**. Exact
  duplicates within an archive are collapsed and all source locations retained.
  Cross-game counterparts remain visible for comparison and retain matching hashes.
- Source selection covers natural cliff/rock walls, caps, cave mouths, slopes,
  climb faces, mountain rock, ice and snow. Related architectural textures sharing
  these source families remain visible; obvious wallpaper is in a separate group.
  This does not inventory every masonry building, dungeon decoration or loose rock.
- Raw DS textures are **not finished GBA tiles**. They can include multiple faces,
  UV layouts, attached terrain or incomplete silhouettes that depend on geometry.
  Their unlit colors also differ from map-render lighting. Do not adopt them by
  cutting arbitrary rectangles or removing every green pixel.
- The current examples expose the actual differences: angular Emerald versus
  rounded HGSS geometry, differing face heights, directional faces and abrupt
  cap/base joins. Native map correctness and visual fidelity are separate checks.

## What to choose next

Choose a preferred **face texture and shape**, then its **top/cap**, **base against
terrain**, **inside/outside corners**, **east/west faces**, and **cave entrance**.
Palette can be chosen separately. We will then produce coherent 16x16 modules with
shared heights and matching joins, test a complete cliff/plateau, and validate
stairs, collision and elevation before map rollout. Nothing is standardized yet.

## Reproduction and provenance

`catalog.json` records IDs, source revisions, crops, source hashes, palettes,
metatile IDs and family membership. `source-data/source-ids.json` preserves stable
review IDs. Gen 4 palettes use actual material bindings from the source map models
where available; exact-name matches are also allowed. `a_9wcliff → a9_criff` is an
explicit naming alias for the otherwise unreferenced source texture. No generic
first-palette fallback is used. The source decoder reports zero unresolved pairs.

```sh
python tools/gba/maps/johto_common/rock_sources.py --donors /path/to/disasm
python tools/gba/maps/johto_common/rock_catalog.py --donors /path/to/disasm --engine /path/to/apocrypha-violet
python tools/gba/maps/johto_common/check_rocks.py --donors /path/to/disasm
```

Uses existing Pillow/NumPy and the project NSBTX/model decoders. Generation only
writes this review directory. It never modifies donors, engine maps or palettes.
Engine snapshot: `6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf`.

Checks cover source hashes, complete unmodified source pixels, source links and
independent Emerald decode comparisons. PNG comparison sheets were visually
inspected. Browser automation rejected local `file:` navigation, so interactive
browser rendering was not verified; the PNG sheets are the verified review views.
No emulator opened. Original artwork: Game Freak / Nintendo / Creatures.
