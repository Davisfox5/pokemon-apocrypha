## Current visual direction — September 27 owner clarification

The owner now wants a distinctly Pokégear device with B/W-era polish. Read
`../pokegear-modern/README.md` for the current native casing, tabs, typography and
runtime evidence. The older HGSS shell below is historical. Full maps, phone
services and broadcast integration are still incomplete. The visual target is
now the modern Pokégear adaptation, rather than exact copies of HGSS backgrounds.

# Pokégear rebuild — native prototype, incomplete

The owner requested the actual HGSS look and functionality, with possible
Gen 5-level additions. The prior field-dialogue phone/clock is insufficient.
The current isolated revision replaces it with a full-screen GBA application;
**that application is still a prototype, not the requested completed device**.

## Verified now

- Clock reads the engine RTC; weekday and 12/24-hour switching.
- L/R page navigation and B return to the existing field menu.
- Phone lists the actually registered contact, Mom, with call/hang-up screens.
- Radio has the HGSS globe/tuner artwork, four presets, manual tuning, preset
  storage/recall and music playback/restoration. One music station uses existing
  GBA music provisionally. Other program slots say OFF AIR; this is a disclosed
  missing service, not finished radio content.
- Location name comes from the current map; the Map Card's later Gold handoff
  remains unchanged. No map is currently rendered.
- Six palette choices, saved last page, time format, tuning and presets. The
  authentic six decorative HGSS backgrounds are not all reproduced.
- Ordinary menu Save, new emulator core, Continue and gear reopening preserve
  settings. Existing unused variables 0x40F8–0x40FC are named and reserved.

`evidence/gear-review.png` shows actual runtime frames, including the incomplete
map and radio. This is stronger than a visual mockup, but not full functionality.

## Remaining implementation and acceptance

| Feature | Required work |
|---|---|
| Complete HGSS visual identity | Native versions of all six backgrounds, correct tab selection, icon proportions, clock band, contact and broadcast layouts; compare at 240x160 against source screens |
| Maps | Actual regional map assets/data, current-position marker, cursor, zoom, place details, markings/notes and roaming/event markers; respect Map Card and story gates |
| Phone | Extensible registered-contact storage, ordering/favorites, incoming calls and missed-call state, contextual dialogue, rematch/gift event APIs and tests; add contacts only as campaign scripts establish them |
| Radio | Authored scheduled programs, scrolling broadcast text, real reception restrictions, regional station/card gates, outbreak reports, manual special frequencies and supported music/encounter effects; no fabricated world events |
| Persistence | Allocate and qualify full contact/note/event storage with ordinary save/Continue and independent event IDs; do not fold this into the deferred 30-box work |
| Gen 5-level additions | Owner preference pending; default is finish faithful HGSS first. Five-region navigation is required by this game's world. Dowsing, networking or encounter changes are not silently added |

Do not mark this complete based on a screen montage or on the current settings
persistence tests. A complete release requires functional tests for every row,
card progression, phone registration/events and runtime map positions.

## Primary reference implementation

Preserved `disasm/pokeheartgold`, inspected narrowly without modifying it:
- `include/save_pokegear.h`: cards, styles, last page, map notes, contact list,
  Mom savings/gifts and trainer rematch state.
- `include/application/pokegear/pokegear_internal.h`: page/application switching.
- `src/application/pokegear/phone/` and `asm/pokegear_app_{map,radio,configure}.s`:
  actual application implementations, not DS production targets for this game.

Source screen references:
- https://blog-imgs-49.fc2.com/m/e/r/merupoke/1_20140216233052afd.png
  (HGSS blue radio, both screens; actual globe, presets and tab icons retiled).
- https://static.guidestrats.com/images/02/12686/03-dj-ben-plays-sinnoh-sound-on-thursdays-pokemon-hgss.jpg
  (HGSS League style upper radio screen).

Local files retain these references under `references/`. The adapter is
`tools/gba/maps/build_pokegear_assets.py`; UI source is tracked in the revision
patch. Donor copyrights remain with their original owners, as with existing
regional reference assets. No generated Pokémon or inferred campaign lore.
