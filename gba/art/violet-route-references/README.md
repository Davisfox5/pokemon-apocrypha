# Violet-adjacent route references

Original HGSS Route 36 (west of Violet) and Route 32 (south toward Union Cave) map images. These are layout references, not finished native maps. Provenance, source URLs, dimensions and SHA-256 hashes are in `provenance.json`.

Route 36: preserve the east-west approach, southern Ruins of Alph gate, western Route 35 gate, northern Route 37 branch, fenced western grass, stepped cliff/ledge boundary and original narrow road obstruction. Route 32: preserve the northern approach, Ruins of Alph branch, rocky terraces, grass blocks, water/wooden docks, elevated railway, southern Pokemon Center and Union Cave approach. The railway is an overhead HGSS structure, not a new traversal mechanic.

The production source currently has only `VioletCityEntrance`, the existing eastern approach and its east gate, not complete Route 36 or Route 32 maps. New route source must preserve stable IDs and the established art/whole-tree strategy. The city's west and south connection points need to be coordinated with the actual Violet layout; do not invent a second complete city by replaying the small eastern-entrance prototype.

Independent 16px image sampling has begun: Route 36 has 80x29 complete sampled cells and Route 32 has 30x125. The per-cell ledgers and grid images are provisional reference surveys. They do not supply native collision or completed layouts; source registration and structures must be reviewed before native composition. `tools/gba/maps/violet_routes/survey.py` reproduces them.
