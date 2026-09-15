# Johto NPC import feasibility

**Implemented follow-up:** [Johto NPC pilot](../johto-npc-v1/README.md) now imports
five of these sources, with three residents walking in the qualified town ROM.
This page retains the earlier read-only feasibility findings.

Source inspection on 2026-09-13, following the owner's request to automate
Johto-specific sprite imports. No NPC importer or new NPC ROM integration was
implemented by this study.

[Existing source lineup](source-lineup.png) · [One complete frame strip](man-frame-order.png) ·
[Measured sample inventory](source-inventory.json)

The repository already contains extracted HGSS overworld textures under
`artwork-library/heartgold-johto/overworld-sprites`. Eight ordinary Johto NPC
samples were inspected: boy, girl, man, woman, older man, older woman, shop clerk,
and Center staff. Seven strips have twelve 32 × 32 frames; Center staff has
thirteen. Each inspected strip uses at most fifteen opaque colors, plus alpha.
The supplied pixels therefore fit a 4bpp palette without color reduction.
These are existing game assets, not generated art; provenance/extraction is
described in `artwork-library/README.md` and `tools/artwork_library/extract_hg_owsprites.py`.

The pinned Emerald-expansion source supports 32 × 32 object-event graphics and
custom frame/animation tables. Typical ordinary Emerald people use 16 × 32
frames, so a visual scale/anchor check is still required. Cropping or shrinking
every source into a 16-pixel width is not a justified default.

The inspected `0120_gsman1` strip has north idle frame 0, west 1–3, east 4–6,
north steps 7–8, and south 9–11. Emerald's standard table uses a different frame
layout and mirrors west for east. The importer must map directions explicitly
and retain independently drawn east frames. Frame count alone is not proof that
every donor sprite shares the same layout; the thirteen-frame nurse needs its
extra frame classified before automatic registration.

## Proposed bounded pilot

Use ordinary Cherrygrove residents and the shop clerk first. Build a manifest
containing each source/hash, frame dimensions and mapping, anchor, palette,
stable appended graphics ID, destination path, and explicit map-event mapping.
Generate indexed PNGs/4bpp data, palette registrations, frame/animation tables,
graphics info and event references. Preserve the current v3 map/buildings and
the existing actors' scripts, local IDs and flags.

Validate all four facing directions and walking cycles in the isolated town,
along with transparent edges, player-relative scale, baseline jitter, simultaneous
NPC palettes, interaction facing and door transitions. Only then expand the
manifest to a larger regional roster. Importing art does not decide NPC placement,
roles, dialogue, schedules or trainer teams. Gold/Silver/Kestra visual direction
remains separate from ordinary regional townspeople.
