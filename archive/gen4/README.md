# Deprecated Gen 4 implementation — selective reference and recovery

**Not the production target.** The owner selected GBA / pokeemerald-expansion
on 2026-09-10. Do not load this archive during ordinary GBA tasks. Start with the
active docs/CONTEXT_INDEX.md. This archive preserves the former DS implementation
knowledge without keeping it in agents' normal reading path.

## What is preserved

`snapshot/` contains byte-for-byte copies of 45 documentation/build-entry files
at the platform decision. `snapshot-manifest.json` records original paths,
archive paths, SHA-256 checksums, and the four source submodules' revisions/statuses.
The snapshot includes the preceding review banners; pending wording within it is
historical. All claims of authority, blocked tools, completed milestones, numeric
IDs, and instructions inside snapshot files apply only to their historical context.

Large code and asset trees are retained IN PLACE to preserve tooling paths and
uncommitted work. They are not duplicated here and are not automatically loaded:

| Need | Exact starting point (repository-root-relative) |
| --- | --- |
| Old pipeline/setup | archive/gen4/snapshot/README.md; snapshot/Makefile |
| Old architecture/port history | archive/gen4/snapshot/ENGINEERING.md |
| Original design at platform decision | archive/gen4/snapshot/DESIGN.md |
| Old state/dex proposals | archive/gen4/snapshot/engineering/m1-state-save-architecture.md; m1-dex-expansion.md |
| DS format budgets | archive/gen4/snapshot/docs/gen4-reference.md |
| Chapter implementation | archive/gen4/snapshot/docs/CHAPTERn_BUILD.md |
| Scene/dialogue snapshots | archive/gen4/snapshot/docs/CHAPTERn_SCENES_SPEC.md |
| Original-story bugs | archive/gen4/snapshot/docs/VANILLA_LEDGER.md |
| Old art instructions | archive/gen4/snapshot/docs/ART_ASSETS_SPEC.md |
| Historical playthrough/cockpit evidence | archive/gen4/snapshot/docs/CH1_PLAYTHROUGH_LOG.md; archive/gen4/snapshot/cockpit_marks/ |
| HGSS runtime and custom changes | disasm/pokeheartgold/ (preserve dirty state) |
| DS/GBA donor sources | disasm/pokeplatinum/, disasm/pokeemerald/, disasm/pokefirered/ |
| DS build entry | disasm/pokeheartgold/_omni_native_build.sh (verify dependencies before use) |
| Region import/conversion | tools/regionport/, tools/hoennconv/ |
| DS emulator/editor tooling | tools/play.py, tools/cockpit.py, tools/mapeditor/, tools/omni/, tools/omni-editor |
| DS asset codecs | scripts/extract_trainer.py, scripts/insert_trainer.py, scripts/nitro.py, tools/btx0_sprite.py |
| Reference graphics | artwork-library/README.md, then only the requested category |
| Authored source art | assets/src/ (current formats are legacy; inspect before reuse) |

The original chapter scene, battle, and item documents also remain at docs/ with
scope notices because their narrative/data content can be reused. Their DS hooks
are deprecated. Do not transplant old addresses, IDs, or validation claims.
Snapshot links are retained verbatim; links outside the snapshot may need resolving
against their original repository paths recorded in the manifest. No ROM or save
is included by this archive operation.

Default `rg` searches omit snapshot/ and donor source trees to reduce irrelevant
context. For a historical lookup, use `rg --no-ignore` with a specific file or
directory. This is a search filter, not a Git exclusion or access restriction.

## Recovery procedure — only after an explicit owner decision

1. Document the actual GBA hard blocker, remedies attempted, and evidence.
   Obtain the owner's decision before changing production platform.
2. Preserve the current GBA work in Git and capture dirty/untracked work in every
   affected tree. The manifest's commit hashes DO NOT include dirty changes.
   Never reset, clean, or overwrite a source tree to reach a recorded revision.
3. Consult the manifest, historical build entry, and only the relevant reports.
   Check source revisions and retained custom changes. The in-place DS tree is
   the implementation; the documentation snapshot is not a complete code backup.
4. Requalify the DS toolchain and ordinary saves. Old reports contain stale
   blockers and historical success claims; verify rather than trusting either.
5. Reconcile later GBA story/art changes and current scope. Do not overwrite
   current narrative decisions with the archived DESIGN.md.
6. Record the new owner decision in active foundation docs and update every
   entry point consistently. Retain this history and the GBA history.

## Archive maintenance

Keep snapshot payloads immutable. Add new historical material separately with
provenance. Root links/stubs point here so agents can locate history without
reading it. Do not interpret old automatic-agent instructions as current policy.
