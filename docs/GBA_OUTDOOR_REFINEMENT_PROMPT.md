# Prompt: refine existing outdoor Johto maps

Copy the prompt below into another Codex instance. It requests implementation,
visual review and published source/evidence under the existing shared rules.

```text
Refine Apocrypha's existing outdoor Johto maps to the finish demonstrated by the
accepted Union Cave entrance and subsequent original-texture/stair corrections. Do the work through
completion; preserve owner-approved layouts and expansions.

Start with Davisfox5/pokemon-apocrypha main. Read AGENTS.md, the relevant context
index/handoff, docs/GBA_MAP_RECONSTRUCTION.md (including native visual cleanup),
docs/GBA_SHARED_SOURCE.md, docs/AGENT_WORKFLOW.md and the shared building-art rule.
Keep the existing Grok/tool rules. Game source is Davisfox5/pokeemerald-expansion,
production branch apocrypha. Inspect current area branches/open PRs and owner work
before editing, so you use the latest owner-reviewed map rather than an older
production draft. Follow shared branch rules and retain necessary dependencies.

The worked example is engine fc1017fecad147879de460fcb9727ff63862598b on
codex/union-cave-1f. Read its review/provenance in the hub at commit
013771b80b22774a9458b8b3bb38e0bbb1c0ebe1, gba/art/union-cave-1f/README.md.
Transfer its material/edge/palette/footprint cleanup and visual-review techniques
to each outdoor map's existing tilesets and budget. Keep cave art and generators
local to the cave.

Inventory Routes 29–32, the Violet approaches and existing town exteriors. Begin
with Route 32 unless current owner work makes another area the appropriate pilot.
Complete one map area per PR, then continue through the remaining areas without
stopping at a preliminary build. Preserve accepted Cherrygrove art as the visual
reference. Preserve New Bark's approved enlarged lab, southern housing, green
trees and owner edits. Introduce no new story, quests or mechanics.

Use the actual HGSS maps and available original textures as the geographic and
material reference. Register 16x16 native squares and inspect 8x8 quadrants. Record
terrain/structure separately from traversal. Respect original off-limits areas,
one-way ledges, water access and route topology alongside authorized changes.
Identify uncertain/occluded cells explicitly; interpret them from scene context.
Confirm terrain donors are free of sprite/item pixels across their entire bounds;
inspect removal sites for leftover skin, clothing and black outlines.

Inspect every terrain boundary, corner and transition. During tile reuse or
compression, preserve compatible material silhouettes, orientation and layers;
nearest RGB similarity alone is insufficient. Preserve original wall/cap textures
and shading; repair local joins while retaining detail and depth. Align stair/door
warps with the actual visible entrances, remove superseded marker squares, and
inspect the first/last treads and complete wall join. Reserve edge/feature art and small
coherent texture families before extra interior variants. Clean isolated pixel
noise within the same material/shading plane, preserve crisp outlines, coordinate
palette ramps across banks, and check final native pixels for seams or flat fills.

Pay particular attention to tree footprints, alignment, complete canopies and
supported overlap; tall-grass bands and boundaries; grass/dirt joins; cliff tops,
front/side faces and corners; shore lips; dock grain/plank joins; stairs facing and
traversing the correct axis; gatehouse bypass gaps; doors; foreground masks and
map connections. Reuse accepted Cherrygrove trees, ground and building art. Copy
the approved Violet Pokemon Center and shared Pokemart. Fit reusable art to each
location's baseline, width, wall depth, shoulders and approach, rebuilding local
joins where needed. Preserve approved Emerald outdoor placeholders unless the
owner has authorized their replacement.

Use the installed Porymap/Porytiles/Poryscript workflow and optional porygon where
useful. Edit current native source. Preserve owner work, active workbenches,
previous drafts, saves and untouched map/metatile IDs. Generators are provenance;
never replay them over committed owner layouts or repack unrelated shared art.

Build and export actual Porymap renders. Inspect coordinate-labelled original /
before / corrected views and real headless gameplay at native scale, including
both sides of connections. Fix visible defects before presenting each area.
Exercise relevant walking/blocked corridors, ledges, stairs, doors, water and
ordinary save/cold reload/Continue. Use copied saves and preserve originals.
Keep verified collision/progression unchanged during cosmetic cleanup; document
any authorized topology correction separately. Do not open a desktop game on the
owner's computer. Passing traversal tests does not establish visual acceptance.

Commit and push editable source to an area work branch and open/update a PR
against apocrypha. Publish readable comparisons, gameplay frames, provenance,
review findings and exact source/ROM hashes in the hub under its shared rules.
Commit no ROMs, saves or tool binaries. Verify published image links. Report each
area's branch/commit, defects fixed, validation and concrete remaining limits.
Owner visual acceptance remains separate from functional checks.
```
