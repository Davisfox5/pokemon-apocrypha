---
name: apoc-lore-check
description: Check a scene spec, dialogue draft, or design proposal for Pokemon Apocrypha against DESIGN.md, and refuse anything that contradicts it. Use before writing a scene, when adding an NPC or a location, when a chapter spec changes, or when the user says "lore check" or asks whether something fits the world. Reads DESIGN.md; never edits it.
allowed-tools: Read Grep Glob
---

# Apocrypha lore check

`DESIGN.md` is the world bible. It is the authority on governance, regional
character, the transport network, the Pokedex model, the antagonist framework,
and every named character. This skill reads it and rules on whether a proposal
fits.

**`DESIGN.md` is read-only. Never edit, rewrite, reformat, or "tidy" it.** If a
proposal is good but contradicts the bible, that is a decision for Davis, and
the output is a refusal plus what would have to change in the bible. Not an edit.

## Procedure

1. Read `DESIGN.md` in full. It is the only source of truth for world facts.
   Chapter specs under `docs/CHAPTER*_SCENES_SPEC.md` are downstream of it and
   can themselves be wrong.
2. Read the proposal: the scene spec, dialogue, NPC, location, or item.
3. Extract every world claim the proposal makes. A claim is anything that
   asserts a fact about the world rather than describing an action. Named
   characters, regions, organizations, technology, travel, time, and money are
   all claims.
4. Check each claim against `DESIGN.md`. Quote the line you checked against.
5. Rule.

## Ruling

Three outcomes, and only three:

**PASS** with nothing to say. Every claim is consistent, or is new detail that
`DESIGN.md` does not constrain.

**PASS WITH NOTE** when a claim is unconstrained but sits close to something the
bible does constrain. Name the nearby constraint so the author knows the edge is
there. New detail is allowed and expected; the bible does not enumerate
everything.

**REFUSE** when a claim contradicts `DESIGN.md`. Do not soften it, do not offer a
compromise version in the same breath, and do not proceed to write the scene.
Output:

- The contradicting claim, quoted from the proposal.
- The line in `DESIGN.md` it violates, quoted.
- What the proposal would need to say instead to pass.
- If the proposal is better than the bible, say so in one sentence and stop.
  Changing the bible is Davis's call and happens in a separate conversation.

## Checks that catch the most

- **Characters.** `DESIGN.md` has a Characters section with specific people:
  Champion Silver, the Johto friend-rival, Mel, Looker, N, Ghetsis, Clair,
  Steven Stone, Colress, Red, Gold. Their roles, allegiances, and whereabouts
  are fixed. A scene that puts one of them somewhere the bible does not, or has
  them act against their stated role, is a refusal.
- **Regional character.** Each region has a thesis: Johto cultural and spiritual,
  Kanto institutional and scientific, Hoenn energy and consequence, Sinnoh
  economic divide and sacred geography, Unova autonomy and political identity. A
  scene set in a region has to serve that region's thesis or at minimum not
  contradict it.
- **Governance and the transport network.** How regions relate and how a player
  moves between them are structural. A scene that invents a travel route or a
  jurisdiction is a refusal, not a detail.
- **The antagonist framework.** Team Rocket (reformed), Project Apex, and the
  reveal structure are sequenced. A scene that reveals something ahead of its
  place in that sequence breaks the story, even if every fact in it is correct.
- **Timeline.** The B2W2 concurrent timeline constrains what has and has not
  happened. Check any reference to a past event against it.

## What this skill does not do

- It does not check flag or var budget. That is `apoc-budget-check`.
- It does not check NPC voice or message-box length. That is `df-writing`, which
  carries the Apocrypha NPC row.
- It does not check whether a scene is implementable. That is a build question.
