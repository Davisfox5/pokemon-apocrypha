# Opening house milestone — September 27

Isolated source: `tools/vendor/gba/opening-house-work`. Production `game/`, the
active Porymap project, prior map previews and owner saves are untouched.
The exterior remains the accepted Cherrygrove from `floccesy-polish-work`;
its Cherrygrove map files also matched the active editor source when checked.

## Interior and provenance

The initial scratch-drawn room was rejected and replaced. Both floors now derive
from the actual HGSS player-house templates, using the same native-scale map-render
adaptation method as the city. Separate layouts preserve the shared Emerald rooms.
Source actors were removed; matching floor repeats, the curved rug edge and chairs
were reconstructed from unoccupied reference fragments. Two interactive cardboard
moving boxes use a dedicated original 16x16 sprite. No vegetation is baked into
floor, wall, stair or door tiles.

- [HGSS first-floor source](https://archives.bulbagarden.net/wiki/File:Player_House_1F_HGSS.png)
- [HGSS bedroom source](https://archives.bulbagarden.net/wiki/File:Player_Bedroom_HGSS.png)
- Original game imagery: Nintendo / Game Freak / The Pokemon Company;
  downloaded reference files and adapted native assets are retained here/in the patch.
- [Actual playthrough screenshots](evidence/playthrough.png), individual native
  PNGs and [qualification](evidence/qualification.json) are in `evidence/`.

## Implemented

Appearance selection, black-screen cold opening and Mom's welcome; upstairs
PC interaction grants exactly one Potion and then opens the familiar bedroom PC.
Returning downstairs triggers Mom's Pokégear/menu handoff and unlocks the exit.
Pokégear has a scripted Mom call and the engine's clock viewer. Map Card, radio
programming and the wider contact system remain later work; this is not a finished
Pokégear implementation. Save is available during free exploration. Naming and
Trainer Card access remain reserved for Kestra's later scene.

Persistent allocation: home stage `0x40F7` (0 welcome, 1 PC pending, 2 Mom handoff
pending, 4 free exploration); Pokégear flag `0x020`; Potion flag `0x021`.
These were unused engine slots, audited before assignment. Dedicated moving-box
graphics ID 1037 and palette tag `0x118D` follow the existing regional registrations.
The latest approved production mechanics files were copied and compared, including
the eleven-HM/item-ID update; earlier preview saves are not this milestone's saves.

## Evidence and reproduction

Native build passed. Both appearance branches passed ordinary New Game button input,
exit guard, stairs, one-time Potion and standard PC, Mom handoff, leaving/re-entering
the home and walking inside, box interaction, phone/clock, and ordinary menu Save
followed by a new emulator core and title-menu Continue at stages 1, 2 and 4.
The harness reads state for assertions; it does not teleport or invoke debug boot.
No desktop game/emulator window was opened. Screenshots were visually inspected.

597 referenced tile patterns and 210 metatiles, with seven secondary palette banks;
indoor camera padding is a blocked black void. [Build manifest](build-manifest.json)
records the engine revision, ROM hash and affected source paths.
`gba/opening-house.patch` applies over `floccesy-polish-work` and passed forward
and reverse application checks. New engine edits and native assets are in that patch.
`tools/gba/maps/build_opening_house.py` reproduces the native reference adaptation;
`tools/gba/maps/opening_house_runtime.c` reproduces the button-driven checks using mGBA core.

Build inside the isolated source with `gmake -j8 TOOLCHAIN=<local ARM toolchain>`.
The ignored ROM package is `tools/vendor/gba/Opening-house-20260927.zip`.
Chapter 1's Gold/Silver battle, Kestra naming/rescue, starter, Route 29/New Bark and
farewell scenes remain unimplemented; outside the house, preview NPC scripts remain.

## Background screen recording

`tools/vendor/gba/opening-recording/Apocrypha-progress-playthrough.mp4` is an
8:58 H.264/AAC recording with chapter markers and emulator audio. It shows the
ordinary opening, house/PC, Mom, Save/restart/Continue, phone and clock, followed
by the current Cherrygrove, Sandgem and Floccesy map previews. Preview camera
repositioning is explicitly labeled. The isolated emulator clock was set to
daytime for artwork visibility; no ROM or owner save was changed. No desktop
emulator/game window was opened. Capture source: `tools/gba/maps/record_opening_progress.c`.
