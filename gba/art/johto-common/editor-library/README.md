# Johto Porymap editing library — October 18, 2026

## Use now

The already-open `apocrypha-src` Route 30 project now uses
`johto-editor-prefabs.json`. Open **Map → Prefabs**, click the picture of the
object, choose **Paint (pencil)** and place it. Undo works normally. Categories
start with buildings, trees, scenery, stairs and ledges. Individual native tiles
follow, with hexadecimal IDs. Existing 71 default prefabs remain intact and the
original `prefabs.json` is untouched.

**The raw Metatiles bank remains ID-ordered.** This is a categorized selection
shelf, not a renumbering of that bank. Changing native IDs would also require
updating shared layouts, borders, scripts, door animations and other references.
Porymap 6.3.1 does not expose an independent categorized display order for it.

The currently open checkout is `aa8ea35eea` with owner edits, not the newest
review branches. Its 16 object selections and 371 individual tile selections
were built from the actual saved files. Do not interpret its old art as the
approved latest art. Damaged old apricorn crops were excluded from object stamps.
No map, tileset, collision, event or script was modified by this task.

## Prepared revision-specific catalogs

| Package | Source | Object selections | Individual tiles |
|---|---|---:|---:|
| active | aa8ea35eea + owner edits | 16 | 371 |
| latest | 1643f58a48: New Bark, Cherrygrove, Violet, Routes 31/36 | 63 | 2154 |
| route29 | ca8781c07c | 11 | 280 |
| route30 | 4f01430776 | 18 | 385 |
| route32 | 6a5fbb19cf | 9 | 701 |
| route33 | origin/codex/route33-hgss, pinned in manifest | 0 | 337 |

The newer packages contain 101 assembled selections in total. Some are scenery
or one-cell objects rather than multi-cell structures. Route 33 currently has
no separate building/tree stamps; its tree-free terrain bank is preserved.
These packages are **prepared, not installed into the old open checkout**.
They must stay separate where revisions share tileset symbols but use different
native IDs or palettes. `install.py` refuses mismatching source hashes.

Included: C06 Center and M01 Mart in their installed city contexts; Violet's
university, lecture hall, tower, residences, teaching court, bridge, islet and
lilies; New Bark laboratory and homes; gates; green/pink/apricorn trees where
installed; signs, mailbox, windmill, flowers, fences, reef, ships and dock
modules; stair flights, joined ledges and selected complete wall modules.
This is not a claim that every conceivable assembly or every uninstalled art
master has a native prefab. Source-only sign/scenery variants, animated Cut and
item objects, and cave/interior objects still need their own compatible native
installation/event setup. Do not substitute static tiles for event sprites.

## Painting limitations

- Prefabs copy native metatiles **and their source collision/elevation**. They
  also copy the terrain in those metatiles. Transparent master art is preserved
  upstream, but this editor feature is not a foreground-only compositing brush.
- Choose the matching terrain context and adjust collision/elevation for a new
  height. Some gate/building selections intentionally include their existing
  surrounding trees, cliff or ground; these are assembled-context selections.
- Door warps, sign scripts, interactions and animations are not created by
  placing a prefab. They remain separate Events / engine data.
- Pink trees remain Cherrygrove-only. Unused/rejected donor metatiles are excluded
  from the categorized individual-tile shelf.
- Terrain grouping uses native behavior and broad visual material hints for
  unlabeled cells; it is an editing aid, not a new authoritative terrain taxonomy.

## Reproduce / install

Tools: `tools/gba/maps/editor_library/` (`build.py`, `snapshot.py`, `verify.py`,
`install.py`). Python needs Pillow and numpy. Build reads native source only;
no older map generator is replayed. `snapshot.py REV OUTPUT MAP...` exports only
needed native source paths from `JOHTO_SOURCE` (the source Git repository).
`build.py PROJECT OUTPUT --maps MAP...` produces a catalog and native prefabs.
`verify.py LIBRARY_ROOT` checks source hashes, every object cell's original ID,
collision/elevation and preview equality; checks all selection bounds/values.
`install.py PACKAGE PROJECT` validates hashes and writes a separate merged
`johto-editor-prefabs.json`, preserving existing default/user prefabs. Configure
that file through Project Settings → Prefabs Path, then reload with no unsaved
map changes. Native tileset-pair filtering also applies inside Porymap.

## Evidence

`validation.json`: native hashes unchanged, object preview/collision matches,
and schema checks for all six packages. The actual Porymap 6.3.1 UI was reloaded
and visually inspected with the Route 30 categorized objects visible. No emulator
or ROM build was needed: no game content changed. The owner map remains the same
saved version and retains its pre-existing dirty files.

Backups of original prefab/config files are in the owner's checkout under
`.porymap-library-backups/20261018-140904/`. The working generated catalog is
reproducible from the tracked `active` package. Full latest-map consolidation and
exhaustive source-art-to-native prefab coverage remain separate work.
