# Pokégear services — September 27

Native implementation in the isolated `opening-house-work` build. The owner-approved
modern shell and mobile handset icon are retained. Desktop emulator/game was not opened.

## Working features

- Five regional atlases adapted from actual HGSS / Emerald / Platinum / B2W2 Town
  Maps. Overview/detail toggle, directional cursor, region browsing, current-town
  marker for the authored regional samples, 100 persistent notes with four symbols.
- Phone registry capacity 75, contact ordering, favorites, sixteen-call scrollable
  history/redial, incoming queue, missed-call state, and requested Mom callbacks
  triggered by ordinary walking. Mom is the only chapter-authored contact today.
- Event-driven gift service: one pending item per contact, inventory-full retention,
  clear-on-success delivery; rematch readiness reads the existing trainer state.
  No gifts/rematches are seeded into the opening. Script adapters use 0x8004 for
  contact and 0x8005 for item/trainer, returning VAR_RESULT.
- Four broadcasts: live active-outbreak reporting, seven-day music rotation,
  rotating tips matching approved mechanics, and a daily password entry with
  persisted completion. SELECT opens broadcast text; B returns to the tuner.
- Existing clock, 12/24-hour choice, four stored frequencies and six accents.

Map Card remains locked in the ordinary opening. `callnative ApocGear_GiveMapCard`
is ready for Gold's later handoff. It is granted **only as an explicit test fixture**
in the atlas screenshots, not by Mom or an invented Gold scene.

## Save and runtime evidence

SaveBlock3 grows from 4 to 940 bytes, within its 1624-byte existing limit. Original
field offsets remain intact; new gear record begins at offset 4, is versioned and
has its own FNV-1a checksum because upstream sector checksums omit these spare chunks.
Previous-build save migration preserves opening stage, Potion, gear and settings.
Damaged known records display a recovery notice; game progress survives, while the
new gear record is reinitialized. No player/owner save was written.

`evidence/runtime.txt`: legacy Continue, app controls, all five atlas views, note,
favorite, history, incoming and missed calls, once-only test gift, all broadcasts,
daily entry, ordinary menu Save, entirely fresh emulator cold Continue, callback
through actual walking, corruption isolation, 100-note limit/reuse and 75-contact
bounds. Normal UI presses are three frames in the service fixture harness.
`evidence/opening-runtime.jsonl`: ordinary full opening regression, mutual facing,
Mom staging, stairs/door round trips, Potion once, four Save/cold Continue cycles,
app switches and persisted existing gear settings; exit 0.
`build-manifest.json`: pinned source, ROM hash, patch hash, measured sizes and scope.

The engine source is preserved in `gba/pokegear-services.patch`, incremental over
`gba/pokegear-modern.patch` (which follows `opening-house-revision.patch`). Forward
and reverse apply checks pass. Production `game/` and the active editor are untouched.
Tools: `tools/gba/maps/build_pokegear_maps.py`, `pokegear_services_runtime.c`, and
`qualify_pokegear_services.py`. Qualification consumes a cloned previous-build
ordinary-save artifact identified by hash in the manifest; it is not an owner save.

## Content and parity still pending

This is a working service layer, not full HGSS campaign content. Later chapters
must supply registered contacts, authored episodes, gift events and rematch trainer
links. No Mom savings economy, Buena prize economy, encounter boosts, Fly/roamer
integration, per-route atlas descriptions, or story-news schedule was introduced.
These require campaign integration or mechanics decisions. Browsing another region
never warps the player or changes exploration, collision or encounter data.
The current-town pin is qualified for Cherrygrove, Sandgem and Floccesy; expanded
campaign maps need location metadata rather than treating the sample pins as universal.

## Provenance

Original game Town Map screenshots: Nintendo / Creatures / Game Freak, archived by
Bulbagarden contributors. Exact file URLs, source hashes and coordinate adaptation
are in `map-provenance.json`. Screenshots use animation frame two, preserve aspect
ratio, and reduce to fourteen map colors plus black/white marker colors for native
GBA rendering. Downloaded overworld-composite references were rejected in favor of
actual Town Maps; they are not used by the build.
