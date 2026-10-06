# Chapter 1 dialogue and scene reconciliation (2026-09-29)

The latest isolated GBA scene build is preserved under
`../chapter1-route/source-overlay/`; the current staging ROM SHA-256 is `20b363e2f7c8b5831e80f328a7521e6cf163a871c41762c0a57c5d7bbd687d81`.
The owner's existing playable ROM/save was not replaced.

## Narrative source order

1. Current owner direction and `DESIGN.md` Chapter 1 govern story and tone.
2. The authored HGSS message files provide character voice and wording:
   `disasm/pokeheartgold/files/msgdata/msg/msg_0550_T21.gmm` (Gold, Silver,
   Kestra), `msg_0545_T20R0201.gmm` (Mom), and `msg_0543_T20R0101.gmm` (Elm).
3. `archive/gen4/snapshot/docs/CHAPTER1_BUILD.md` supplies scene direction.
   Its later §10 and §10b replace the earlier grass-block warp and indoor
   starter ceremony with Route 30 rescue, a town tour, and outdoor starters.
   §10c adds onlookers and first-meeting direction; §3B and §4C supply Elm
   and Mom's longer dialogue.
4. `docs/CHAPTER1_SCENES_SPEC.md` records historical intent. DS coordinates,
   script IDs, and old completion marks do not establish GBA completion.

## Implemented direction

Gold/Silver's exchange has visible Pokémon and witnesses. Kestra faces and
names the player within the continuous opening scene. Route 30 has a visible
wild Rattata and an alternate grass-step trigger. Gold's five continuous
walking stops lead to an outdoor starter ceremony after he steps into his
house. Route 29
has a one-time first-grass goad; Kestra joins the New Bark entrance beat.
Elm gives the Pokédex. Gold's return scene starts automatically, uses a
player-controlled practice throw, and awards five real balls once. Mom's
farewell and optional savings follow. Native evidence is in
`../chapter1-staging/evidence/scene-sequence.png`.

## Fidelity limits

The battle is a field cinematic; the tour is now a continuous walk. Kestra's
Route 29 accompaniment is staged at the grass beat and New Bark entry rather
than persistent following
through the whole route. The institute art remains provisional. These are
visible production limitations, not missing dialogue events. Headless runtime
checks and the fresh New Game to ordinary-save to Chapter 1 walkthrough are
recorded in `../chapter1-staging/README.md`.
