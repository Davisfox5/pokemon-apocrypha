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
in `gba/`. Preserve local changes and track new engine edits in patches or an
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
