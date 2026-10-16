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
- Preserve the original wall/cap texture and shading treatment. Repair joins
  locally and inspect the cap, front/side faces and corners as one continuous
  surface. Retain texture detail during palette reduction.
- Put stair/door warps on their actual visible entrances. Remove superseded
  marker squares and restore their ground; inspect the first/last steps and
  the whole stair-to-wall join.
- Clean isolated pixel noise within the same material and shading plane. Keep
  deliberate creases and crisp silhouettes. Maintain consistent palette ramps
  across neighboring banks; inspect light/dark bands and seams after native
  palette reduction. Keep foreground art, ground beneath it and collision separate.
- Confirm sprite/item-removal donors are unobscured across their full bounds.
  Inspect repaired corners for leftover clothing, skin, outlines and corrupted
  palette pixels; reconstruct the missing local terrain from clean context.
- Fit reused art to the receiving location: width, height, baseline, wall depth,
  shoulders, approach and adjacent corners. Rebuild the complete join when needed.
  An approved entrance or building still needs local seam/footprint inspection.
- Use original-game textures and accepted shared art. Preserve tree footprints
  and complete canopies, coherent grass borders, cliff tops/faces, stair axis,
  shore lips and dock grain. Reuse the approved Violet Center and shared Pokémart.
- Validate actual decoded native tiles/palettes/layers and Porymap output, plus
  relevant headless movement, gates, connections, water, doors/stairs and ordinary
  saves. Review all affected floors/maps and both sides of transitions. Record
  exact source/ROM identities, before/after evidence and concrete remaining limits.
- Keep owner-approved topology and traversal unless a change is authorized.
  Edit current native sources; preserve owner work, IDs, prior drafts and saves.
  Adapt the technique to each map's own tilesets and hardware budget. Cave-specific
  art, palettes and generators stay local to Union Cave. Visual acceptance remains
  with the owner.

## Ownership and autonomy

- Owner: story, creative direction, visual review, playtesting, approval/revisions.
- Agents: map/asset design and production, coding, gameplay within approved canon,
  tooling, integration, testing, visual inspection, and all revision labor.
- Do not hand routine drawing, pixel cleanup, palette editing, frame assembly,
  collision painting, map placement, import/export, or editor operation to the owner.
  Automate or perform it. Make routine reversible technical choices independently.
- Use existing tools, source formats, scripts, and narrow adapters first. Build a
  new editor only when a demonstrated recurring problem justifies it.
- Every reusable object placed over land must have a transparent background at
  all times in its source artwork and foreground tiles. This applies to buildings,
  all trees (large, small, cuttable and apricorn), props and other terrain-spanning
  objects. Never include donor grass, dirt, sand, pavement or rock-face patches in
  the object. Author terrain beneath it independently and match adjacent materials
  and transitions. Preserve the object's complete silhouette, trunk and details;
  keep terrain-colored ground shadows separate from the reusable object. Native
  foreground transparency must reveal the actual destination terrain. A constrained
  animation composite must use that same terrain while its source remains transparent.
- Johto large trees must use the approved Cherrygrove design: shared master T01,
  with T02 pink foliage exclusive to Cherrygrove. The native Emerald T05 is the
  sole Cut-tree choice. See `gba/art/johto-common/trees/catalog.json`. Superseded
  tree cutouts have been deleted; never restore or substitute them from old
  snapshots, Git history, generated artifacts or donor crops. Run the tree asset
  check before adding or replacing tree assets.
- Reuse owner-approved regional building artwork across cities. Use the shared
  master assets and approved modules; do not redraw, recrop, recolor, or invent
  a replacement for each map. Keep local terrain and foreground/background trees
  separate: reusable buildings use transparent foreground pixels over independent
  terrain tiles. Never bake donor grass, dirt or road fragments into a building.
  Terrain beneath each placement must match the neighboring material, texture phase
  and edge transitions; never cut a road at a rectangular building/import boundary.
  If a constrained animation frame must be composited, sample that destination's
  terrain exactly. Adapt door anchors, collision and roof overlap to the destination.
  Johto uses Center C06 and the approved shared Violet Mart M01. See
  `gba/art/johto-common/approved-buildings.json`. Local houses and landmarks retain
  their approved city identity; other regions receive their own approved sets.
  Architectural changes to a locked shared asset require owner direction.
- Cliff and stair orientation must follow the actual raised side, not screen-side
  placement. A right-hand wall is not automatically a mirror of the left wall.
  Install the reviewed stair master, align both landings and movement to its rise,
  and keep complete trees on ground planes with no canopy painted over vertical
  rock faces. Realign complete neighboring rows and check exclusive 2x2 trunk
  footprints; never shift an isolated tree into its neighbor or crop a crown.
  Review the full forest boundary and route access after moving a row.
- Transition cleanup must preserve authored irregular terrain contours. Select edges,
  caps, corners and backing from immediate neighboring materials, orientation and
  height. Do not globally straighten, round or flatten dirt paths when correcting
  abrupt seams. Inspect each transition in its assembled neighborhood.
- Pink/blossom trees are exclusive to Cherrygrove City throughout the game.
  Other cities and routes use their appropriate non-pink vegetation.
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
