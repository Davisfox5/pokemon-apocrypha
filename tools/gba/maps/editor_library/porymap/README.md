# Spatial metatile selector — work in progress

Status 2026-10-20: compiled and headlessly tested; NOT installed in the owner's
Porymap. The Mac was locked. Do not replace/reload the open application before
inspecting and preserving its unsaved edits.

This narrow Porymap patch presents complete objects in a rectangular arrangement,
with category headings, repeated native IDs and disabled separator cells. It
changes display order only. It does not delete metatiles or rewrite map IDs.
Native source SHA-256 checks reject stale catalogs and restore the stock selector.

## Reproduce

Official source: https://github.com/huderlem/porymap
Pinned commit: `26b919d7ff4b54152de010abd5bf344af2ebe116` (6.3.1).
Apply `spatial-selector.patch` with `git apply` to that revision. The patch also
contains the giflib BOOL compatibility fix required by the current macOS SDK.
Build out of tree using Qt 5.15.19 qmake, then `make -j6`.
No downloaded or built application binary is committed.

Generate a catalog with:

```
python tools/gba/maps/editor_library/selector.py CATALOG_PACKAGE OUTPUT_DIRECTORY
```

The generator needs Pillow and NumPy. Its material classification is currently
specific to the Cherrygrove palette family and MUST NOT be accepted as a general
classifier for other map tilesets. The catalog is named `porymap.selector.json`;
only place it in a disposable project for testing at this stage.

## Native test

`selector_check.cpp` links against the Porymap build objects except `main.o`.
Use the build's CXXFLAGS, INCPATH and LIBS. Run with `QT_QPA_PLATFORM=offscreen`:

```
selector-check DISPOSABLE_PROJECT CherrygroveRoute30Approach
```

It edits/restores the disposable catalog to test invalid-source fallback, paints
and undoes map memory, and saves `selector-native.png`. It never saves map files.
Do not point it at the owner's project. The test project must contain the matching
native assets/configuration and catalog.

2026-10-20 result: 203 visible selector positions checked, 80 separator cells in a
rectangular selection disabled, native paint/undo and hidden-ID eyedropper passed,
stale-catalog fallback passed. These tests do not establish desktop UI usability.

## Remaining work before delivery

1. Unlock Mac; inspect active Porymap unsaved state and preserve owner edits.
2. Reconcile active aa8ea35eea Route 30 checkout with approved later revisions.
3. Review per-map terrain categories and all object crops. The active prototype
   still contains context composites; hiding fragments is not asset cleanup.
4. Implement/verify approved foreground placement. Transparent source PNGs alone
   are not native compositing brushes: ordinary painting replaces the whole
   metatile, including its lower layer. Never present these context stamps as
   terrain-independent foregrounds.
5. Activate in a separate persistent app path, retain stock app, and verify native
   selector UI and painting in a disposable map before opening the owner project.

Current active prototype: 16 object groups, 182 unique visible IDs, 189 used
unclassified IDs hidden. Hidden IDs remain intact in engine data. This is not
an all-map cleanup and does not install newer trees or approved art by itself.
