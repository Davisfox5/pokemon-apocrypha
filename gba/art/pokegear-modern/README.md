# Modern Pokégear — distinct from C-Gear

The owner requested B/W-era polish, then clarified that the device should retain
its Pokégear identity and be distinctly different from the C-Gear.

## Implemented visual direction

- Physical charcoal/slate casing, recessed glass display, small orange index
  notch and pale bevels.
- Persistent clock and POKéGEAR branding above the app display.
- Five recognizable clock/radio/map/phone/settings tabs with an orange position
  marker and colored underline. No connectivity-module layout.
- Restrained cyan/green status typography, fine dividers and strong text contrast.
- Pokégear-style circular globe tuner and round radio preset controls.
- Phone contact/call panels and six subdued accent palettes.

Original B/W's default C-Gear is a reference for contrast, typography and finish,
not this device's navigation structure or function set. The honeycomb draft is
retained only as a comparison in `../pokegear-bw`; it was superseded before any
owner-facing runtime delivery. Original B/W reference screenshot:
https://miro.medium.com/v2/resize:fit:2000/1*FSKtf54-xxqbUOylNFsgdA.png

## Native implementation

Source remains isolated `tools/vendor/gba/opening-house-work`.
`gba/pokegear-modern.patch` is incremental over `gba/opening-house-revision.patch`.
It changes the application presentation and its three graphics files, plus
queues button press edges during redraws so quick presses are retained.
The current asset adapter is `tools/gba/maps/build_pokegear_modern_assets.py`.
Screens are 240x160, one 16-color palette, with native text and controls.

Actual background mGBA captures are in `evidence/`. The reference and offline
shell PNGs are not the runtime proof. No desktop emulator window was opened.
Production `game/` and the active editor were not installed or replaced.

## Scope and remaining functionality

This visual revision does not complete the whole device. Regional map rendering,
incoming calls/contact/rematch services and full radio broadcasts remain pending;
see `../pokegear/README.md`. The clock, current Mom call, tuner/presets, menu
return, current Map Card progression and existing saved setting IDs still work.

Validation uses `tools/gba/maps/pokegear_modern_runtime.c`: ordinary New Game,
corrected house sequence, tab navigation, 12/24-hour display, Mom call/hang-up,
radio tuning/store/recall, all accent palettes, menu Save, fresh emulator core,
Continue and reopening the last page with the stored palette. The final check uses one-frame button taps to verify the redraw input fix.

## Phone icon correction

The owner accepted the visual direction except for the phone icon. Replaced the
ambiguous curved silhouette with a crisp mobile handset: chamfered body, screen,
speaker and home key. Build and patch checks pass. A background core loaded the
previous ordinary save, opened the gear, switched to Phone, called/hung up and
returned to the field. Latest actual capture: `evidence/phone-icon-revised.png`.
Earlier montage captures preserve the previous icon for comparison.
