# Pokemon Apocrypha

A five-region Pokemon story set roughly a decade later, built for **GBA with
Gen 3 2D graphics on pokeemerald-expansion**. AI agents perform production;
the owner directs story and creative identity and reviews the results.

Remote Claude/Grok sessions: use branch **codex/gba-source-handoff** and the
[GBA remote setup guide](docs/GBA_REMOTE_HANDOFF.md). The Mac folder name
`the-omni-hack` and GitHub repository `pokemon-apocrypha` refer to the same project.

## Find what you need

- Agents: [shared rules](AGENTS.md), then [task-specific context index](docs/CONTEXT_INDEX.md).
- Approved scope: [foundation decisions](docs/FOUNDATION_DECISIONS.md).
- Build commands, measurements, and actual status: [GBA baseline qualification](docs/GBA_BASELINE.md).
- Production and testing: [agent workflow](docs/AGENT_WORKFLOW.md).
- Story: relevant sections of [DESIGN.md](DESIGN.md); do not load the whole document by default.
- Historical DS implementation and fallback: [archive index](archive/gen4/README.md).
  Read only when a task explicitly needs historical evidence.

Resume work using the [agent handoff](docs/AGENT_HANDOFF.md): completed decisions,
verified builds, pending implementation and exact next steps.

## Implementation status

The pinned expansion is installed at `game/`. Upstream and roster benchmark builds,
emulator boot, and baseline save tests pass. Use `python3 tools/gba/build.py` after
the documented setup. The [mechanics audit](docs/GBA_MECHANICS_AUDIT.md) records eighteen applied scope
corrections and the remaining rules choices. The owner deferred save/autosave
architecture; the [isolated storage prototype](docs/GBA_STORAGE_PROTOTYPE.md) records
results and open questions, not universal GBA limitations. Production 30 boxes and
the full five-region game are not yet implemented. The four `disasm/`
submodules remain source references, separate from the active expansion.
Existing scripts and root `make build` still implement the deprecated DS asset
pipeline. Do not run those commands as GBA setup. Follow the baseline document.

Track source, editable art, and reproducible tools. Do not commit ROMs, saves,
credentials, environments, or third-party tool binaries.
