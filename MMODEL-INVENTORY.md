# Overworld Model Inventory — pokeheartgold `a/0/8/1` (`mmodel.narc`)

> Source-grounded inventory for *Pokemon Apocrypha*. Companion to `ASSET-SOURCES.md`,
> `CUSTOM-ASSETS.md`, and `ENGINEERING.md`.
> Read directly from `disasm/pokeheartgold` @ `b843c93` on 2026-07-05 (submodule
> initialized this session). Every identity below is confirmed against the decomp:
> the constant tables in `include/constants/mmodel.h` and `include/constants/sprites.h`,
> and actual map placements in `files/fielddata/eventdata/zone_event/*.json`.

## What this is

Every overworld sprite in HGSS — player, NPCs, trainers, story characters, and
interactable objects — is a BTX model in the **`a/0/8/1` NARC (`mmodel.narc`)**.
There are **863 model files, indices 0–862**. This document decodes them and maps
the useful ones to the Apocrypha cast.

### Two namespaces (important)

| Layer | Header | What it is |
|---|---|---|
| **Model index** | `constants/mmodel.h` (`MMODEL_*`) | The **actual file index in `a/0/8/1`** (0–862). This is the "BTX index." |
| **Sprite ID** | `constants/sprites.h` (`SPRITE_*`) | The **event-facing ID** that map JSON uses (`"spriteId": "SPRITE_GSRIVEL"`). An indirection layer resolved to a model index at runtime. Numbers differ from the model index. |

Maps reference `SPRITE_*`; the file in `a/0/8/1` is the `MMODEL_*` index. Both are
given below. **185 distinct human/object sprites are actually placed** in vanilla
maps (the rest are player states, unused, or follower-mon).

### Layout of the 863 models

- **0–279** — human/NPC/trainer/story-character/object models (**the cast — the focus of this doc**).
- **280–296** — gap / internal (unused name slots).
- **297–862** — **follower-Pokémon overworlds** (full Gen 1–4 dex #1–493 + forms). See §Follower block.

---

## The named story cast (verified)

Decoded from Japanese dev names and **confirmed by where each is placed in vanilla
maps**. "Apocrypha role" ties each to `DESIGN.md`; "Asset action" flags reuse vs.
the aged/custom work the *10-years-later* premise demands (see `CUSTOM-ASSETS.md`).

| Model idx | `SPRITE_` | Vanilla identity | Verified placement | Apocrypha role | Asset action |
|---:|---|---|---|---|---|
| 58 | GSRIVEL | **Silver** (teen rival) | 15 zones (Blackthorn/Dragon's Den, routes) | Silver — now **Champion**, everywhere | ⚠️ **Aged redesign** — vanilla is a teenager; Apocrypha Silver is an adult Champion. New BTX. |
| 158 | WATARU | **Lance** | 7 zones (Mahogany Rocket HQ, Indigo, Dragon's Den) | Lance — retired to Blackthorn villa | ♻️ Reuse; optionally age slightly |
| 160 | OOKIDO | **Prof. Oak** | Pallet, Rte 30 | Oak — still an authority (Blue's mentor) | ♻️ Reuse |
| 225 | SAKAKI | **Giovanni** | Rte 22, Rocket HQ, Viridian | Backstory / Rocket lineage (Silver's father) | ♻️ Reuse for flashback/lore |
| 59 | DAIGO | **Steven Stone** | Johto towns (T03/T06/T11) | Steven — Hoenn, suspicious of Silph | ♻️ Reuse |
| 181 | MASAKI | **Bill** | Ecruteak/Goldenrod PCs | Bill — comms/PC network | ♻️ Reuse |
| 187 | MINAKI | **Eusine** | 7 zones near Suicune sites | Eusine — legendary-research thread | ♻️ Reuse |
| 223 | GANTETSU | **Kurt** | **Slowpoke Well + Azalea** | Kurt — agitated re: Slowpoke Well (DESIGN §Azalea) | ♻️ Reuse (already elderly) |
| 191 | NANAMI | **Daisy Oak** | Pallet | Blue/Leaf's generation in Kanto | ♻️ Reuse |
| 170 | RED | **Red** | Mt. Silver | Red — postgame, Mt. Silver | ♻️ Reuse |
| 192 | REDMAMA | Red's mother | Pallet | Pallet Town NPC | ♻️ Reuse |
| 159 | GSMAMA | Player's mother | New Bark | Player's mother | ♻️ Reuse |
| 184 | MANIA | **Mania** (Shuckle giver) | 10 zones (Rtes 42/44, Cianwood) | Cianwood NPC | ♻️ Reuse |
| 182 | CAPTAIN | S.S. captain | S.S. Aqua | S.S. network captain (transport thread) | ♻️ Reuse |
| 227 | CHOUROU | **Elder / Sage** | Sprout Tower / Dragon's Den | Sprout Tower sages, Ecruteak elders | ♻️ Reuse |
| 172 | BOZU | Monk boy | Sprout Tower, Ruins | Sprout Tower monks (DESIGN §Violet) | ♻️ Reuse |
| 83, 84 | ITAKO / ITAKO_ | Spirit medium | **Ecruteak & Violet gyms** | Ecruteak spiritual core (Morty) | ♻️ Reuse |
| 180 | DANCER | Kimono dancer | 7 zones (Ecruteak theater) | Ecruteak Kimono Girls | ♻️ Reuse |
| 190 | KURUMI | Named NPC (uncertain) | — | Spare named NPC | verify in-game |
| 226 | SUIT | Suited man | Rocket/exec scenes | Silph/Rocket suits, executives | ♻️ Reuse |
| 33 | MYSTERY | Hooded/mystery figure | events | **Shadowy Silph/Rocket figure** | ♻️ Reuse — good for concealed antagonists |
| 57 | SUNGLASSES | Man in sunglasses | events | Agent/handler NPC | ♻️ Reuse |

*(A handful of dev-name models remain ambiguous — `MONO_PIP` 242, `AJI_PERU` 111,
`JUPETTA` 224 — verify their role in-game before assigning.)*

## Team Rocket set

| Model idx | `SPRITE_` | Identity | Apocrypha use |
|---:|---|---|---|
| 173 / 174 | ROCKETW / ROCKETM | Rocket grunt ♀/♂ (♂ placed in 17 zones) | Rocket grunts — reuse heavily |
| 175 / 176 | RKANBUW / RKANBUM | Rocket **executive** ♀/♂ (Kanbu) | Rocket execs (Archer/Ariana/Petrel/Proton lineage) |
| 244 / 245 | RKANBUM2 / RKANBUM3 | Additional exec ♂ variants | Distinct named execs |
| 36 | BADMAN | Thug / bad man | Low-level Rocket muscle |
| 171 | THIEF | Thief | Event thief NPC |

Rocket is well covered for reuse. Apocrypha reframes Rocket as a political/scientific
enterprise (DESIGN §Antagonists) — the **grunt/exec art reuses fine**; the leadership
(Silver, and any new named execs) is where custom work goes.

## Gym leaders & Elite Four

| Model idx | `SPRITE_` | Vanilla | Count |
|---:|---|---|---|
| 146–153 | GSLEADER1–8 | Johto gym leaders | 8 |
| 162–169 | GSLEADER9–16 | Kanto gym leaders | 8 |
| 154–157 | GSBIGFOUR1–4 | Johto Elite Four (Will/Koga/Bruno/Karen) | 4 |
| 215–222 | LEADER1–8 | Secondary/generic leader set (DP-inherited) | 8 |
| 103–106 | BRAINS1–4 | Frontier Brains | 4 |

**16 leader + 4 E4 overworlds ship natively** — enough bodies for Johto+Kanto's
gym rosters. But Apocrypha's leaders are frequently *reassigned or aged* (Brock as a
breeder, Gardenia relocated to Fuchsia, Saturn as a gym leader, etc.), and **Sinnoh,
Unova, and Hoenn leaders have no overworld here** → custom/ported art (see Gaps).

## Player character & states

`HERO`/`HEROINE` (69/70) plus ~40 animation-state variants — cycling, surfing,
fishing, ladder, saving, celebrating (`BANZAI`), running (`R*`), Pokéathlon (`PKTH*`),
`STATUE*`, `SHAKE*`, alt outfits (`HERO_2`/`HEROINE_2`), and the DPPt cameo protags
`PL_BOY01C`/`PL_GIRL01C` (247/248). Any new player-character design must supply **all
of these states** as BTX, not just the base walk cycle — a significant per-protagonist
asset set.

## Objects & interactables (reusable as-is)

- **Traversal**: `ROCK` (91), `BREAKROCK` (92, rock smash), `TREE` (93, cut), `MONSTARBALL` (94, item ball).
- **Apricorns (Kurt)**: `BONGURI` trees + `BONMI` fruit in 7–8 colours (251–265). Directly relevant to Azalea/Kurt.
- **Legendaries/statics**: `HOU_OBJ01` (Ho-Oh), `LUG_OBJ01` (Lugia), `RGYARADOSU` (Red Gyarados, Lake of Rage), `KABIGON` (Snorlax), `YADON` (Slowpoke, Slowpoke Well), `RAPURASU` (Lapras), `ROTOM` forms.
- **Doors/signage**: `LEAG_DOOR2`, `GINGA_DOOR` (Galactic HQ door, from Platinum), `GATE_*`, `SIGN*` (5), `POKEWALL`, `SCROLL`, `MEDAL`, `STOP`, trophies (`GTOROPHY`/`STOROPHY`/`BTOROPHY`), `STATUEHERO/HEROINE`.

## Generic NPC population (reusable townsfolk & trainer classes)

Two full sets of generic bodies to populate the world:

- **Base set (0–57)**: BABYBOY/GIRL, BOY1–3, GIRL1–3, MAN1–5, WOMAN1–5, MIDDLEMAN/WOMAN, OLDMAN/WOMAN, plus trainer/vocation classes — REPORTER, CAMERAMAN, POLICEMAN, GENTLEMAN, LADY, WORKMAN, FARMER, COWGIRL, CLOWN, ARTIST, SPORTSMAN, FIGHTER, CAMPBOY, PICNICGIRL, FISHING (fisher), SEAMAN (sailor), DOCTOR, MAID, WAITER/WAITRESS, SHOP clerks, ASSISTANT, GORGEOUS ♂/♀, SKIER, IDOL, DELIVERY.
- **"GS" set (113–145, prefix `GS*`)**: HGSS-specific reskins of the same classes (GSBOY, GSGIRL, GSMAN, GSWOMAN, GSOLDMAN, GSBIGMAN, GSGENTLEMAN, GSSWIMMER ♂/♀, GSFIGHTER, PCWOMAN, etc.).

These cover ordinary crowds region-wide with **zero new art** — the modernized cities
(DESIGN's "10 years later") mainly need new *tiles/buildings* (`CUSTOM-ASSETS.md` §1),
not new pedestrians.

## Follower-Pokémon block (297–862)

**566 follower/overworld Pokémon models** — the complete Gen 1–4 National Dex (#1–493)
plus forms (Unown A–?, Rotom appliances, Deoxys, Arceus types, Shellos/Gastrodon east/west,
gendered Meganium/Pikachu/etc.), and a `STATIC_*` follower subset (`sprites.h`
994–1049). This is a large, free asset base for the follow-me system (`follow_mon.c`).
Note it stops at **#493 (Arceus)** — consistent with `ENGINEERING.md`'s dex-cap finding;
any Gen-5 follower overworlds (Unova) do not exist here and must be built.

---

## Gaps for Apocrypha (what the base does NOT provide)

The native `a/0/8/1` covers **Johto + Kanto** vanilla-era characters and Gen 1–4
follower mon. It does **not** contain:

1. **Aged versions of the returning cast.** Vanilla Silver is a teenager; Apocrypha
   Silver is an adult Champion. Blue-as-professor, Jasmine-as-civic-icon,
   Brock-as-breeder, Clair, Wally, etc. need **aged/redesigned overworlds** — the
   single largest character-art task. → `CUSTOM-ASSETS.md` §2 (OW Gen 4 Trainer
   Sprite Creator's *aged* templates).
2. **Sinnoh cast**: Cynthia, Volkner, Gardenia, Saturn, Barry, Darach, Palmer — no
   overworlds here. Source from `pokeplatinum`/`pokediamond` `mmodel.narc`
   (`ASSET-SOURCES.md`).
3. **Unova cast**: Iris, N, Ghetsis, Cheren, Elesa, Clay, Brycen, Marlon, Colress,
   Alder — **no source anywhere**; extract B2W2 overworlds and convert to BTX
   (`ASSET-SOURCES.md` §Unova, `CUSTOM-ASSETS.md`).
4. **Hoenn cast**: Brawly, Wally (Steven = `DAIGO` exists). Port from `pokeemerald`
   overworlds (Gen-3 → BTX conversion).
5. **New Apocrypha cast**: **Mel** (the journalist) and any original NPCs — author
   original BTX to the 32×32 / 16-frame / ≤16-colour spec.

## Recommended next actions

1. **Extract & thumbnail the 863 BTX files** from `a/0/8/1` (Tinke) so the team can
   *see* each index — this doc names them; a visual sheet makes them usable.
2. **Lock a reuse-vs-rebuild list** per character from the tables above (♻️ reuse vs.
   ⚠️ aged redesign vs. ✳️ port/new).
3. **Prototype the aged Silver overworld** first — he's the most-placed character
   (15+ zones) and the tone-setter for the redesign.
4. **Reserve model indices** for new cast (Mel, aged variants, imported region
   leaders) beyond 862 when planning the expanded `mmodel.narc`.
