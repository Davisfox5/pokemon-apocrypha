# Chapter 1 scene blocking correction — 2026-09-29

This is the latest isolated GBA scene build. Review ROM:
`tools/vendor/gba/Chapter1-staging-review-20260929/Apocrypha-Chapter1-staging.gba`
(SHA-256 `20b363e2f7c8b5831e80f328a7521e6cf163a871c41762c0a57c5d7bbd687d81`). It contains no save and starts a New Game. The
previous `Chapter1-scenes-review-20260929` ROM and the owner's active
`Chapter1-play-20260929` ROM/save remain intact. No desktop emulator was opened.

## Corrected staging

- The Gold/Silver confrontation is spread across the walkable square. Gold and
  Silver stand behind Typhlosion and Alakazam; witnesses no longer occupy the
  battle line. The player approaches before the first dialogue so both trainers
  remain in the camera frame. Kestra and the player end the meeting facing one
  another.
- Gold's Cherrygrove tour is a continuous 101-step, three-person walk. It
  visits the Mart, Center, Route 29 mouth, shore and Gold's house in one map
  script, without landmark warps or fades. Each character has a collision
  checked path and an explicit facing at every stop. The background recording
  `evidence/tour-continuous.mp4` and five stop captures show this route.
- Gold now walks into his doorway, pauses, walks back out and remains on screen
  for the outdoor starter choice. Kestra runs off screen after her line.
- Route 30 aligns the player directly below Kestra from any of its three
  trigger tiles. Route 29 aligns both actors for the grass exchange before
  Kestra runs off screen. Kestra remains visible near Elm's institute in New
  Bark; Elm, Kestra and the player meet in a readable triangle inside.
- On the return, Gold and Kestra stand close to the player. Gold remains beside
  the player through his final advice and is repositioned home only after the
  conversation. Mom steps away from the boxes and faces the player from the
  adjacent tile for her goodbye. Gold and Typhlosion face one another indoors.

## Native verification

The ROM compiled from isolated engine base
`f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. A headless mGBA New Game
reached Mom's handoff, saved normally and cold continued. Starting from that
fresh save, ordinary button input and walking completed Chapter 1 to the Route
30 northbound marker; no fixture warps were used in that run. Runtime assertions
checked Gold/Silver/Kestra presence, coordinates and facing at the battle,
rescue return, all five tour stops, Route 29, Elm's institute, Gold's return,
and Mom's goodbye. All three starter choices and Kestra counterpicks passed.
A separate run confirmed Gold stayed visible during his advice, the practice
throw left the real party and Bag unchanged, the five-ball gift was granted
once, and savings survived cold Continue and withdrawal.

`evidence/scene-sequence.png` contains fifteen native 240×160 captures. The
recording is a 480×320 nearest-neighbor enlargement of headless native frames;
it runs at the capture cadence and has no audio. Test sources are
`tools/gba/maps/chapter_continuous_runtime.c`,
`tools/gba/maps/gold_route_runtime.c`,
`tools/gba/maps/chapter_newbark_runtime.c`, and
`tools/gba/maps/opening_house_revision_runtime.c`.
The collision checked tour generator is
`tools/gba/maps/build_chapter1_tour.py`. Exact modified/new engine source is
preserved in `gba/art/chapter1-route/source-overlay/` with its SHA-256 manifest.
No ROM or save is in the source overlay.

## Remaining scope

The Gold/Silver battle is still a scripted field performance, not a turn-based
battle. Route 29 and New Bark art and Elm's institute layout are provisional.
Route 29's wild encounter table and Chapter 2 content remain outside this
staging correction. The deferred 30-box save requirement is unchanged.
