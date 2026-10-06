# Opening chapter production scope — September 27

The owner supports building the opening chapter(s) to test whether the native
maps can form a coherent game. Regional visual standards must permit distinct
town architecture, palettes and atmosphere, especially for Unova and possibly
Diamond/Pearl Sinnoh. Technical consistency does not require visual uniformity.

## First milestone

Build Chapter 1 as a connected GBA experience from New Game through the farewell
and the northbound departure toward Chapter 2. Chapter 2 follows after this
sequence demonstrates ordinary exploration, scripted events and persistence.

Use DESIGN.md, Chapter Sequencing / Chapter 1, as narrative authority;
CHAPTER1_BUILD.md for the committed scene detail; CHAPTER1_SCENES_SPEC.md for
acceptance intent. DS IDs, commands, coordinates and historical implementation
claims are not GBA implementations. Current GBA scenes must be marked independently.

1. Appearance selection, black-screen cold open, player home, upstairs PC/Potion,
   return downstairs and Mom's handoff. Preserve the later Kestra naming beat.
2. Witness Gold and Silver's friendly battle and Silver's departure; meet Kestra,
   enter the player name, and retain Gold as an interactable mentor.
3. Kestra rescue, witnessed catch, Gold's tour and starter choice. Use the approved
   Johto starter trio; preserve Kestra's type-advantage selection and grants.
4. Route 29, New Bark's introductory institute visit and Elm's Pokédex handoff.
5. Return farewell, catching instruction, five Poké Balls, Mom's farewell and
   northbound departure. Optional state remains independent of main progression.

The current documents contain historical catch/staging differences. Resolve these
against DESIGN.md and the committed build dialogue before implementing scripts;
raise any remaining narrative ambiguity specifically rather than inventing canon.
Encounter tables and broader battle pacing are proposals until owner-approved.

## Location identity

- Cherrygrove: warm, quiet seaside refuge, matured blossom grove and weathered
  waterfront, understated affection for Gold.
- Route 29: recognizable Johto woodland and sea ridge; transition from coastal
  blossoms toward the New Bark surroundings.
- New Bark: cooler, cleaner research-campus accents and a shallow first visit;
  deeper institute access remains gated for later story.

The opening does not require standardizing every town in all five regions.
Other-region map samples remain independent visual references and technical proof.

## Current evidence and assembly requirements

The latest isolated Floccesy source contains Cherrygrove map group 80, its player
home/bedroom, Gold's house, shops and route-approach maps. Its player-home scripts
contain exploratory dialogue only; they do not implement the opening sequence.
The route approaches are not proof of completed Route 29 or New Bark.

Before assembly, choose and record accepted source revisions for Cherrygrove and
its cast, resolve the active-editor/isolated-source divergence, and create a fresh
isolated campaign workbench. Carry approved mechanics deliberately from production;
a map preview alone is not evidence of the latest mechanics integration. Preserve
all current previews and owner work. Record each source and patch in a build manifest.

Author named persistent event IDs with an allocation audit. Preserve engine flags,
ordinary saves, classic party/battle/PC interaction and independent optional events.
The deferred 30-box work remains deferred. Preview debug entry points must not be
required to complete the New Game campaign sequence.

## Acceptance

- Play from New Game to the Chapter 1 departure with ordinary button input.
- All three starter branches and the later player naming return cleanly to field.
- Town/interior/route transitions and story gates are physically consistent.
- Rewards are granted once; mandatory events do not repeat after revisiting.
- Save, fully restart, and Continue at representative chapter stages, including
  before/after starter selection and the Pokédex handoff.
- Optional exploration remains available without corrupting story progress.
- Inspect actual native-resolution captures and movement before owner review.

This document records scope and assembly requirements. It is not a claim that
Chapter 1 is built, tested or installed.
