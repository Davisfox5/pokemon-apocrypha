# Celadon City ten years on (Kanto, GBA)

Status: second round built and installed. Engine branch `claude/celadon-city` (on
`claude/saffron-city`), hub branch `claude/celadon-city`. Owner visual review pending.

The owner turned the first round (FireRed's map with the changes painted on) down: "start
with HGSS and work backward". The second round is HGSS's Celadon (pokeheartgold header 55,
area bank 15, zone T07, `source/hgss/`), cell for cell in HGSS's own coordinates (a 60x50
cut of its 64x64 block), drawn in Gen 3: FireRed Celadon's own metatiles for the ground and
FireRed's buildings on HGSS's lots, with the story's changes (DESIGN.md Chapter 6, the
approved plan in `evidence/plan.png`). `evidence/compare.png` puts HGSS beside the build.

## HGSS's plan, element by element

| HGSS | Gen 3 |
|---|---|
| North row on a paved terrace: houses, Dept Store, Condominiums, houses, Center | FireRed's paving (rows 8-17); FireRed's house (10-13), Dept Store as the market's services (14-22, doors (16, 13), (20, 13)), house (23-26), Mansion with balconies as the Pokemon Hotel on the Condominiums lot (28-34, door (31, 13)), houses (36-43), Center (45-49, door (47, 13)) |
| Main road east to Route 7 | rows 14-17 to the east edge |
| West avenue and the road west to Route 16 | cols 10-12; rows 33-35 to the west edge |
| Fountain plaza | lawn (13-22, 19-30) with FireRed's fountain and lawn edges, the market's four Slateport tents on it, produce on the paving east of it |
| Teal house by the plaza | the café: FireRed's house door and the Bike Shop's awning (26-29, door (27, 25)) |
| Game Corner and prize corner | FireRed's (31-41, doors (34, 25), (39, 24)) on HGSS's lawn, the railing below |
| East houses | FireRed's houses (44-51) |
| Canal, footbridge | FireRed's pond rims and water (25-30, rows 29-43), surfable; the Bond Bridge's planks on the road (rows 33-35) |
| South-east loop of houses and the restaurant | the paved loop (31-53, rows 29-41), FireRed's houses on its lawn, the restaurant's lot a residence (door (40, 37)) |
| Gym on its forecourt, houses either side, ledges | the Botanical Gardens: the gym under Cerulean's Bike Shop glass (14-21, door (17, 41)), the flanking houses' lots beds and trees, the forecourt, Cerulean's hedges for the ledges |
| Woods round the town | FireRed's trees, each forest's tops, edges and trunks chosen from its shape |
| Main road, west avenue, west road | the bike lane painted down their middle in Celadon's teal |

Signs: the city sign by the fountain ("The City of Rainbow Dreams. Rebuilt by its people."),
the services, the hotel, the Game Corner, the prize exchange, trainer tips, the gardens, the
café.

## Interiors

The Center and its upstairs are cloned from Cherrygrove's (Emerald-native), the door playing
FireRed's sliding door. Eight rooms are FireRed's own, repurposed (Chapter 6: "Repurpose
interiors, don't rebuild"), each on gTileset_Building with a secondary of its own
(`tools/gba/maps/celadon/interiors.py`):

| Map | FireRed room | City door |
|---|---|---|
| KantoCeladonMarketServices | Dept Store 1F | (16, 13), (20, 13) |
| KantoCeladonHotelLobby, KantoCeladonHotelUpstairs | Condominiums 1F, 2F (stairs between them) | (31, 13) |
| KantoCeladonGameCorner, KantoCeladonPrizeRoom | Game Corner, prize room | (34, 25), (39, 24) |
| KantoCeladonCafe | Restaurant | (27, 25) |
| KantoCeladonGardens | Celadon Gym | (17, 41) |
| KantoCeladonResidence | Pokemon Hotel room | (40, 37) |

## Pipeline

```
python3 tools/gba/maps/celadon/hgss_source.py PATH/TO/pokeheartgold   # HGSS reference (source/hgss/)
python3 tools/gba/maps/celadon/parts.py ENGINE       # FireRed's buildings and the new pieces, source/sprites/
python3 tools/gba/maps/celadon/compose.py ENGINE     # HGSS's plan in FireRed's metatiles, parts placed, lane painted
python3 tools/gba/maps/celadon/pack.py ENGINE        # one exact 13-bank pack
python3 tools/gba/maps/celadon/interiors.py ENGINE   # the eight rooms
python3 tools/gba/maps/celadon/install.py ENGINE     # first authoring only (revert the previous install first)
make -j$(nproc)
python3 tools/gba/maps/celadon/check.py ENGINE       # native audit
python3 tools/gba/maps/celadon/runtime.py ENGINE gba/art/celadon-kanto/evidence/gameplay
python3 tools/gba/maps/celadon/porymap.py ENGINE PORYMAP   # after committing the engine
python3 tools/gba/maps/celadon/review.py ENGINE
```

## Evidence

- Pack: 581 tiles (69 of 496 secondary), 325 metatiles, 194 of 195 colours, every pixel exact;
  324 building cells are FireRed's own metatiles, 340 cells packed from pixels
- Audit (`evidence/native-audit.json`): installed map = compose = packer decode; ledger;
  every door, sign, the plaza, the gardens, both ends of the footbridge, both route edges
  reachable, no open cell unreachable; canal water surfable, the deck walkable under the
  player; doors and rooms both ways; scope
- Headless run (`evidence/gameplay/`): 44 frames, no background mismatch; behind the
  glasshouse's, the hotel's and the services' roofs; across the footbridge both ways; every
  room in and out, the hotel up and down its stairs; the Center's door frames 0-2; save, cold
  reload, Continue
- Porymap 6.3.1 round trip: 0 of 768,000 city pixels differ; save rewrites no Celadon file
- Determinism: parts, compose and pack rebuild identically
- `evidence/compare.png` (HGSS beside the build), `evidence/review/*.png` (each area, HGSS beside the build)
