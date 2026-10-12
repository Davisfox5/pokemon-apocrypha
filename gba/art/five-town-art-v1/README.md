# Five-town artwork study

Created September 29, 2026 with the built-in image-generation tool. Artwork only: no engine source, map binaries, tilesets, collision, saves or emulator changes.

## Deliverables

- cherrygrove.png: Johto harbor town, existing five houses, island dock, boats, northeast pond and route approaches.
- sandgem.png: owner-reference Sinnoh layout, turquoise lab, orange Center, blue Mart and houses; dry southeast sand.
- floccesy.png: Unova layout with lodge/court, paired sheds, clock garden, park, Center and paired houses; uses current polish layout as reference.
- pallet.png: Kanto proposal, two homes, Oak's lab, flower garden and southern water route.
- littleroot.png: Hoenn proposal, two homes, Birch's lab and northern forest exit.

Exact prompts, reference paths and original generated paths: prompts.json. All five images were visually inspected. These are composed RGB concept images, not indexed native art or automatically importable tiles. Regional building identities are retained; vegetation uses a coordinated common style. Fine texture, differing illustration scales and occasional terrain-edge variations still need normalization during conversion. Littleroot's worn trail has a grassy break near its northern entrance; this is artwork, not a collision barrier. Existing playable map coordinates remain authoritative for the established towns.

## Conversion direction

Use 16x16 map cells assembled from 8x8 graphics. Normalize all doors to the same native width before scaling objects; do not shrink every whole image to a common width. Prefer 5-6-cell house widths and approximately 2x3-cell trees, checking each building against existing doors and character scale. Reuse one cleaned crown per region, repeated roof/wall/window courses and a small library of straight/corner terrain transitions. Keep props, foreground canopy and ground separate when extracting production assets; these previews are flattened. Reserve palette index zero for transparency and plan coherent 15-opaque-color material banks. Assign palette banks under the actual engine constraints before importing. Design toward roughly 800 static tile patterns per area as a planning target, leaving room below the current 1008 allocation for animation and revisions; this is not a measured count for these artworks. Simplify fine grass/water texture first. No pixel-exact grid alignment, palette fit or tile budget has been claimed or tested.

## References and provenance

Architecture/location designs belong to Nintendo, Game Freak and Creatures. Shared art direction: ../floccesy-v2/floccesy-art-preview.png. Local geography references are listed in prompts.json. Kanto visual reference: https://www.benolab.com/soluces/kanto (saved references/pallet.png). Hoenn original-layout reference: https://www.y9freegames.com/es/blog/pokemon-emerald-walkthrough-guide/ (saved references/littleroot.jpg). External reference images are geography guides, not production tiles. Pallet and Littleroot are visual proposals, not new narrative canon or connected playable maps.
