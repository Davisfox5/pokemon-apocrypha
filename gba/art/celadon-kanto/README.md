# Celadon City ten years on (Kanto, GBA)

Status: built and installed. Engine branch `claude/celadon-city` (on `claude/saffron-city`),
hub branch `claude/celadon-city`. Owner visual review pending.

Method: [AGENTS.md](../../../AGENTS.md), "Kanto towns" and "Planning a new town". FireRed's
Celadon (`CeladonCity_Frlg`, 60x40, General_Frlg + CeladonCity) is the base. HGSS's Celadon
(pokeheartgold header 55, area bank 15, zone T07) is the plan reference. The owner approved the
plan in `evidence/plan.png`.

## What HGSS changed against FireRed

- A. The fenced pond became a north-south canal with a footbridge on the street.
- B. The fountain plaza opened into a larger lawn.
- C, D. The Dept Store and Condominiums stand side by side on the north row.
- E. Game Corner and prize corner stay at the centre.
- F. The gym stands on a paved forecourt.
- G. The restaurant has its own awning front.
- No hotel.

## What was built

| # | Change | Gen 3 source | Cells |
|---|---|---|---|
| 1 | Market: five tents round the fountain lawn (purple, gold, red, teal, blue), produce on the east walk; the lawn a row taller (B) | Slateport Market's tents, baskets and crates (Emerald), canvases laid onto Celadon's own colour ramps | tents (6-9, 17-22), (17-20, 17-22), (5-8, 12-14) |
| 2 | Market services: the Dept Store as FireRed draws it, its sign | FireRed | doors (11, 14), (15, 14) |
| 3 | Botanical Gardens on the gym's site: the gym's walls under a glass roof with the planting showing through, its crest a leaf, a forecourt (F), hedges for the ledges, a north gate from the market | Cerulean's Bike Shop glass and hedge (FireRed), Celadon's own tree crowns under the glass in Celadon's teal | glasshouse (8-15, 26-30), door (11, 30), gate (5-6, 25) |
| 4 | Pokemon Hotel: the south row's last two houses made one, a storey taller, balconies, one door in the middle | FireRed's Celadon houses | (44-51, 24-29), door (48, 29) |
| 5 | Café: FireRed's house door and a striped awning on the house between the market and the gardens (G) | Bike Shop awning (FireRed) | (16-19, 25-29), door (17, 29) |
| 6 | Game Corner and prize room kept | FireRed | (34, 21), (39, 20) |
| 7 | Bike lane, Route 7 to Route 16, painted in Celadon's teal with white edge lines and a bicycle mark | Celadon's paving recoloured | rows 13 and 16, cols 5 and 18, row 23 |
| 8 | Canal: FireRed's pond carried south to the treeline (A), the street crossing it on a plank footbridge | FireRed's pond pieces; Three Island's Bond Bridge (FireRed) | (24-29, 21-33), bridge (24-29, 24-25) |

Also: the city sign ("The City of Rainbow Dreams. Rebuilt by its people."), signs for the
services, gardens, hotel and café; no NPCs yet (the Rocket grunts are gone with FireRed's
objects).

## Interiors

The Center and its upstairs are cloned from Cherrygrove's (Emerald-native), the door playing
FireRed's sliding door. Eight rooms are FireRed's own, repurposed (Chapter 6: "Repurpose
interiors, don't rebuild"), each on gTileset_Building with a secondary of its own
(`tools/gba/maps/celadon/interiors.py`):

| Map | FireRed room | City door |
|---|---|---|
| KantoCeladonMarketServices | Dept Store 1F | (11, 14), (15, 14) |
| KantoCeladonCondominiums | Pokemon Hotel room | (30, 11) |
| KantoCeladonGameCorner, KantoCeladonPrizeRoom | Game Corner, prize room | (34, 21), (39, 20) |
| KantoCeladonGardens | Celadon Gym | (11, 30) |
| KantoCeladonCafe | Restaurant | (17, 29) |
| KantoCeladonHotelLobby, KantoCeladonHotelUpstairs | Condominiums 1F, 2F (stairs between them) | (48, 29) |

Solid until built: FireRed's restaurant door (37, 29), the house door (41, 29), the
condominiums' back doors, the store's upper floors and elevator, the condominiums' 3F, the
Game Corner's stairs down.

## Pipeline

```
python3 tools/gba/maps/celadon/hgss_source.py PATH/TO/pokeheartgold   # HGSS reference (source/hgss/)
python3 tools/gba/maps/celadon/parts.py ENGINE       # source/sprites/*.png from Gen 3 maps
python3 tools/gba/maps/celadon/compose.py ENGINE     # FireRed's grid edited, parts placed, lane painted
python3 tools/gba/maps/celadon/pack.py ENGINE        # one exact 13-bank pack
python3 tools/gba/maps/celadon/interiors.py ENGINE   # the eight rooms
python3 tools/gba/maps/celadon/install.py ENGINE     # first authoring only
make -j$(nproc)
python3 tools/gba/maps/celadon/check.py ENGINE       # native audit
python3 tools/gba/maps/celadon/runtime.py ENGINE gba/art/celadon-kanto/evidence/gameplay
python3 tools/gba/maps/celadon/porymap.py ENGINE PORYMAP   # after committing the engine
python3 tools/gba/maps/celadon/review.py ENGINE
```

## Evidence

- Pack: 663 tiles (151 of 496 secondary), 410 metatiles, 194 of 195 colours, every pixel exact
- Audit (`evidence/native-audit.json`): installed map = compose = packer decode; ledger;
  every door, sign, the gate, the forecourt and both ends of the footbridge reachable; canal
  water surfable, the deck walkable under the player; doors and rooms both ways; scope
- Headless run (`evidence/gameplay/`): 47 frames, no background mismatch; behind the hotel's
  and the glasshouse's roofs; across the footbridge both ways; every room in and out, the
  hotel up and down its stairs; Center door frames 0-2; save, cold reload, Continue
- Porymap 6.3.1 round trip: 0 of 614,400 city pixels differ; save rewrites no Celadon file
- Determinism: parts, compose and pack rebuild identically
- `evidence/compare.png` (FireRed beside the build), `evidence/review/*.png`
