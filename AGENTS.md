# Apocrypha — shared agent rules

## Start here; keep context small

- Production target: **GBA, Gen 3 2D presentation, pokeemerald-expansion**.
  The owner approved this on 2026-09-10. Do not reopen the platform choice.
- Resuming this work: read `docs/AGENT_HANDOFF.md` after the context index.
  It identifies the last verified build and next task; do not repeat settled choices.
- Read `docs/CONTEXT_INDEX.md`, then ONLY the document/section relevant to the task.
  Read `docs/FOUNDATION_DECISIONS.md` when changing foundation behavior; it is the
  authoritative technical decision record. Current user instructions take priority.
- Do not bulk-read DESIGN.md, archive/, disasm/, old chapter builds, or tool trees.
  Find headings/symbols with scoped `rg`, then read bounded ranges. Expand only
  when a specific dependency requires it. Do not initialize reference submodules
  or load sprite libraries merely to understand the project.
- `DESIGN.md` owns narrative canon. Read relevant sections, not the whole file.
  Legacy engine IDs and implementation notes inside it are historical only.
- DS documentation and source access are indexed in `archive/gen4/README.md`.
  Do not read that archive during ordinary GBA work. Old build pages are redirects.
- `.rgignore` excludes archived snapshots and donor source trees from default
  searches, not from Git. For an intentional lookup use `rg --no-ignore` against
  a specific historical file or donor directory, never the whole repository.
- Claude and Gemini follow this file through their root pointer files. Keep one
  shared rule set; do not maintain different policies per model.

## Required workflow for every map-building task

- All models and instances, including Codex, Claude, Grok and Gemini, must read
  and apply [the map reconstruction workflow](docs/GBA_MAP_RECONSTRUCTION.md)
  before building, rebuilding, extending or refining a map.
- Compare the original-game reference square by square with native Gen 3 tiles.
  Match **specific terrain materials and structure as well as traversal**;
  collision agreement alone does not establish a faithful map.
- This requirement supplements existing Grok rules and other applicable shared
  instructions. Preserve those rules; do not replace them with a per-model policy.
- Inspect actual native renders and headless gameplay, fix visual defects, and
  publish readable source/native comparisons. Functional tests do not establish
  owner visual acceptance.

## Required native visual cleanup — all maps and floors

Owner-established after the Union Cave refinement, 2026-10-15. Apply this to
outdoors and interiors, in addition to the reconstruction and existing Grok/tool
rules above. Use the [detailed cleanup method](docs/GBA_MAP_RECONSTRUCTION.md#native-visual-cleanup-and-final-review).

- Review each map/floor at the same standard. Inspect original/native grids,
  every wall/terrain boundary and corner, then actual headless gameplay frames.
  Keep coordinate-labelled review sheets and specific findings; traversal checks
  alone do not establish visual quality.
- During tile reuse or compression, match the material/structure silhouette and
  orientation. Preserve complete outlines, corners, roots and narrow barriers.
  Give edges, foreground features, doors and stairs priority over spare texture
  variants; retain compact ground/water/plateau texture families.
- Keep one wall/cap treatment across the map and inspect the cap, front/side faces
  and corners as one continuous surface. On a Gen 4 conversion that treatment is a
  Gen 3 rock set restyled with the original's colour ramp (see the conversion section
  below), not the original's own texture. Repair joins locally. Retain texture detail
  during palette reduction.
- Put stair/door warps on their actual visible entrances. Remove superseded
  marker squares and restore their ground; inspect the first/last steps and
  the whole stair-to-wall join.
- Clean isolated pixel noise within the same material and shading plane. Keep
  deliberate creases and crisp silhouettes. Maintain consistent palette ramps
  across neighboring banks; inspect light/dark bands and seams after native
  palette reduction. Keep foreground art, ground beneath it and collision separate.
- On a map built from a render or trace, confirm sprite/item-removal donors are
  unobscured across their full bounds.
  Inspect repaired corners for leftover clothing, skin, outlines and corrupted
  palette pixels; reconstruct the missing local terrain from clean context.
- Fit reused art to the receiving location: width, height, baseline, wall depth,
  shoulders, approach and adjacent corners. Rebuild the complete join when needed.
  An approved entrance or building still needs local seam/footprint inspection.
- Build from accepted shared art and Gen 3 pieces, with the original game as the
  reference for layout, shape and colour (see the conversion section below).
  Preserve tree footprints and complete canopies, coherent grass borders, cliff
  tops/faces, stair axis, shore lips and dock grain. Reuse the approved Violet
  Center and shared Pokémart.
- Validate actual decoded native tiles/palettes/layers and Porymap output, plus
  relevant headless movement, gates, connections, water, doors/stairs and ordinary
  saves. Review all affected floors/maps and both sides of transitions. Record
  exact source/ROM identities, before/after evidence and concrete remaining limits.
- Keep owner-approved topology and traversal unless a change is authorized.
  Preserve owner work, IDs, prior drafts and saves. Once the owner has edited or
  accepted a map, edit its native sources directly; until then a converted map is
  regenerated from its tools each round (see the conversion section below).
  Adapt the technique to each map's own tilesets and hardware budget. Cave-specific
  art, palettes and generators stay local to Union Cave. Visual acceptance remains
  with the owner.

## Converting a Gen 4 map: convert elements, not pixels

Owner-praised method, Blackthorn City, 2026-10-22: it reached near-acceptance in a few
rounds of small notes. Use it for every HGSS-to-Gen 3 map. Where an older rule in this
file or the linked docs reads differently for a Gen 4 conversion, this section wins.
Details, pitfalls and budgets are in
[the element conversion playbook](docs/GBA_MAP_RECONSTRUCTION.md#element-conversion-playbook);
the worked example is `gba/art/blackthorn-city/README.md` with tools in
`tools/gba/maps/blackthorn/` (read the script you need, not the tree).

- Do not paste a 1:1 HGSS render onto a Gen 3 grid. Keep HGSS's **layout** (decoded
  heights, permissions, events, cell by cell), but replace each **element** with the
  Gen 3 piece that does the same job: rock terraces, ground, water, ledges, props.
- Build a per-cell element ledger first: material, structure (rock top/face direction,
  ledge, shore), terrace level from HGSS heights, traversal from HGSS permissions.
- Rock: take a Gen 3 piece set with the same role (FRLG's General mountain set for
  Johto/Kanto rock) and restyle it with the HGSS colour ramp. One HGSS layer becomes one
  one-tile terrace. Autotile per 8x8 quadrant, place inner corners as whole pieces, use
  the over-rock variants on stacked terraces, join ledges into cliffs with FRLG's join
  pieces. When unsure, build two treatments side by side and measure both budgets.
- Props and buildings other than the shared Center and Mart: redraw from scratch as
  top-layer sprites, inside their own cell columns. Take shape and proportion from the
  game's own model drawn through the map's own field camera (`hgss_camera.py`) when no
  screenshot is available. Walkable cells with top-layer art get the normal layer type
  (walk-behind); blocked cells get covered.
- Reuse accepted vocabulary (Cherrygrove ground and water, Route 30 pond rim, the
  approved Violet Center and shared Mart) and colours the loaded palettes already hold
  (the primary's banks, the Center's bank 8), so tiles and palettes stay inside one
  tileset pair. Keep each other colour family to 15 colours and check every element's
  decoded colours after packing. Measure per-element tile and colour cost (`budget.py`)
  before cutting anything.
- A borrowed edge piece brings its source map's texture with it. Repaint its water or
  ground with the receiving map's own texture at that map's phase, mirror pieces for
  sides the source never shows, and run a shoreline on under a cliff's clear pixels so
  it meets the rock instead of stopping short.
- Every round: compose, pack, install, build, audit (decode, traversal, reachability,
  walk-behind, palettes, budgets, ids, file scope), headless mGBA with VRAM parity,
  Porymap round trip, then look at the images yourself and show the owner
  before/after crops inline. Answer review notes with targeted fixes, not rebuilds.
- Regenerating the map from its tools each round is the method while the map is still
  the agent's draft. Check `git log` on its layout and tileset first: once any commit is
  an owner edit, or the owner has accepted the map, stop regenerating and edit the
  native files. Keep generators deterministic (no hash-order tie-breaks), so a rerun
  reproduces the installed map exactly.

## Ownership and autonomy

- Owner: story, creative direction, visual review, playtesting, approval/revisions.
- Agents: map/asset design and production, coding, gameplay within approved canon,
  tooling, integration, testing, visual inspection, and all revision labor.
- Do not hand routine drawing, pixel cleanup, palette editing, frame assembly,
  collision painting, map placement, import/export, or editor operation to the owner.
  Automate or perform it. Make routine reversible technical choices independently.
- Use existing tools, source formats, scripts, and narrow adapters first. Build a
  new editor only when a demonstrated recurring problem justifies it.
- Do not invent canon or silently change character roles. Label creative proposals.
- Follow `docs/AGENT_WORKFLOW.md` for the relevant production/validation work.

## Non-negotiable scope

- Five playable regions: Johto, Kanto, Hoenn, Sinnoh, Unova; twenty sanctioned
  badges; original regional identity with substantial changes roughly a decade on.
- Classic Pokemon party, battle flow, menus, and PC interaction. Explicit exceptions:
  canonical Fairy typing throughout; late-game Mega Evolution; Shadow in Wes's
  gym; Terra confined to the designated final gym leader.
- Terra and Shadow are additional custom types alongside the standard types.
  They are assigned before battle, not activated through mid-battle transformations.
  Terra is not Terastallization; Shadow is not merely a status condition. Do not
  expand their gym-specific scope or invent matchups/typing assignments.
- Canonical species: Gen 1-5 plus documented picks, currently Sylveon. Use existing
  suitable sprites/data. No generated Pokemon redesigns or blanket later-gen roster.
- **30 PC boxes / 900 slots**, familiar PC interaction, ordinary persistent saves.
  This is an approved target; implementation and save fit still require verification.
- Preserve engine flags needed for functioning systems. Replace original campaign
  triggers deliberately; never indiscriminately wipe or reuse flags/variables.
- Preserve independent optional-event state and stable IDs. No silent save resets.

## Current implementation phase

The GBA toolchain, upstream/roster builds, and baseline save tests pass; see
`docs/GBA_BASELINE.md` for commands and limits. The owner deferred the unresolved
30-box save/autosave architecture on 2026-09-10; do not treat the isolated prototype's
limits as universal GBA limits or resume that investigation without a relevant task.
See `docs/GBA_STORAGE_PROTOTYPE.md` for evidence and the deferred questions.
Automatic checkpoints and an emulator dependency are not approved. Production still
has 14 boxes; the 30-box requirement remains open, not waived or qualified.
The configuration audit is in `docs/GBA_MECHANICS_AUDIT.md`: twenty-five settings
are pinned, including the owner-approved Gen 4–5 per-move physical/special split.
The Gen 5 experience package (rules and yields), Gen 5 species base stats with
canonical Sylveon/Mega exceptions, Gen 5 ability sets with eighteen owner-chosen
exceptions, ORAS level-up learnsets and Gen 5 move data are approved, applied and
verified. The open decisions are the TM/HM list, Hidden Ability access, move flags
and breeding.
Three gaps stay open and must not be assumed away: how the player obtains a Hidden
Ability; move tutors, still Emerald's 30 and expandable only through map script
data; and breeding/inheritance rules, all still at inherited Gen 9 defaults.
The move economy is tiered by owner design: TMs are the generic toolkit and
signature moves belong to origin-locked regional tutors. Read
`docs/MOVE_ECONOMY.md` before touching TMs, tutors or move distribution. The TM list is settled at 100 single-use TMs, **rebalanced on 2026-09-13** across the eighteen types: Johto, Kanto and Hoenn carry nineteen each so that three Fairy TMs can close the list, since every offensive Fairy move is Gen 6 or later and no region could stock one. Dragon went from one attacking TM to three and Normal from ten to seven. The HM list is now **11**: the vanilla
eight plus Defog, Rock Climb and Whirlpool, which cover every field move the five
regions need as originally built. Whirlpool was built from nothing, modelled on
Waterfall. That expansion renumbered every item id from 690 up; no player save
exists, so nothing was invalidated, but item ids should now be treated as frozen.
**The tutor economy is 150 moves, every one assigned to a region** -- 89 historical TM moves, 12 vanilla Emerald tutor moves and the 49 Tier 2 signature moves; see `docs/TUTOR_ROSTERS.md`. Regions were assigned on identity (landmark, gym, species, type character), not introducing generation, which had left Kanto with 44 and Hoenn and Unova with 8 each. The split is Johto 31, Kanto 28, Hoenn 30, Sinnoh 35, Unova 26. `gTutorMoves[]` holds exactly these 150. That is the data layer only: every move is teachable, none is obtainable, because no tutor is placed, priced or scheduled. No TM or HM is placed either. No tileset assigns `MB_WHIRLPOOL`, and
the HM badge gates are vanilla placeholders against an eight-badge assumption. Egg-move data itself is reviewed and settled:
it has no generation switch and nothing egg-exclusive on this roster is unbalanced. Any change to moves, TMs or learnsets must
re-run the Fairy-coverage check; that trap has already been hit once.
Read that concise audit before changing gameplay settings; do not globally change
GEN_LATEST or treat inherited settings as approved. Independent nonvisual work may
proceed; persistent-state integration still requires a qualified save design.
The owner has explicitly authorized isolated Cherrygrove map/art production and
independent Claude/Grok interpretations. Follow docs/GBA_REMOTE_HANDOFF.md for
remote setup. Broader campaign production remains subject to its scoped requests.
Production source is `game/`, a pinned submodule plus the tracked roster and mechanics patches
in `gba/`.
**Shared map source is the `apocrypha` branch of `Davisfox5/pokeemerald-expansion`**
(current accepted Johto maps as Git history; see `docs/GBA_SHARED_SOURCE.md`). Map and
script work goes there as commits and PRs, not as new standalone patches. Porymap opens
that checkout directly. Preserve local changes and track new engine edits in patches or an
explicit source fork; never leave their only copy in a dirty submodule.
The root `make build` is still a legacy DS asset command, not a GBA ROM build.
Do not report a proposed dependency or configuration as installed or tested.

## Preserve work and report evidence

- Keep DS source trees, tools, original assets, and dirty/untracked work intact.
  They are reference/fallback material, not the production target. Use a separate
  path for GBA production; do not overwrite a donor submodule.
- A platform fallback requires a documented hard blocker, attempted GBA remedies,
  and an explicit owner decision. Never switch automatically or develop two targets.
- Record pinned revisions, configuration, relevant checks, and measured capacity.
  Distinguish estimates, source inspection, compilation, runtime tests, and approval.
- Inspect visual work yourself before owner review once that work is in scope.
  An image passing validation does not prove successful in-game integration.
- Never commit ROMs, player saves, credentials, virtual environments, or vendored
  tool binaries. Keep source assets, provenance/credits, and reproducible tooling.
