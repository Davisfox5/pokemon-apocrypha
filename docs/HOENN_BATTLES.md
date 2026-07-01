# Pokémon Apocrypha — Hoenn Battles & Encounters

The Hoenn companion to [JOHTO_BATTLES.md](JOHTO_BATTLES.md) / [KANTO_BATTLES.md](KANTO_BATTLES.md):
wild encounter tables, trainer/gym battles, and the level band for the Hoenn chapters. Hoenn
begins at **Slateport City (Chapter 8)**, when the player arrives by sea from Vermilion, and
continues north (Mauville, Lavaridge…).

> Detail split (see [[apocrypha-doc-taxonomy]]):
> - this file — Hoenn encounters + trainers + battles
> - [HOENN_ITEMS.md](HOENN_ITEMS.md) — Hoenn items + marts
> - per-chapter docs (`CHAPTER<N>_BUILD.md` / `CHAPTER<N>_SCENES_SPEC.md`) — staging + dialogue

> **⚑ Cross-region source (READ THIS).** Hoenn does not exist in the HGSS build engine. Every
> map, trainer slot, and encounter table in this doc is **referenced from the pokeemerald
> decomp** (`disasm/pokeemerald/`: `data/maps/…`, `src/data/wild_encounters.json`,
> `src/data/trainers.h` + `trainer_parties.h`) and is **rebuilt as native HGSS data** — new
> `MAP_*`/trainer/encounter entries. pokeemerald is the **roster/layout source of truth**;
> Apocrypha re-lines, re-teams, and **re-tunes levels to the whole-game curve.** Sister
> decomps: pokeemerald = Hoenn, pokeplatinum = Sinnoh, pokefirered = Kanto extras. See
> [[apocrypha-cross-region-maps]].

**Level curve:** Hoenn continues the single **whole-game** curve defined at the top of
[JOHTO_BATTLES.md](JOHTO_BATTLES.md) (Full Epic Scale, **+3 lift**) — *not* a separate Hoenn
re-scale. The player arrives in Hoenn at **~lv 25-26, 2 badges (Hive + Requiem)**, sitting
just past the **badge-2 line (~lv22)** and climbing toward the **badge-3 line (~lv27)**.

> **Re-tune direction = lift UP, hard.** Vanilla Hoenn is *early-game* in Emerald, so its
> Slateport-area routes sit ~**lv12-14** — far *below* the Apocrypha player. Apocrypha lifts
> them ~**+13** to meet the band (the mirror image of Kanto, where vanilla endgame routes were
> pulled *down*). Keep species **Hoenn-native**; just seat the levels at the player's actual
> progression and prefer readable first-stage commons. Per the Inter-Regional Exchange, Hoenn
> is now the **native-base** region and imports are the sparse migrants — note the neat echo:
> **Plusle/Minun/Electrike**, which were *rare migrants* in Kanto's broadcast corridor (Ch6),
> are **natives here.**

---

## Chapter 8 — Slateport City · Route 110 (south) · Route 109 (beach)

**Player level by end of chapter:** ~27-28. **Badges:** 2 (Hive + Requiem), **no new badge**
— Brawly's Slateport gym is **closed** (he commutes from Dewford and isn't in). Chapter 8 is
a **new-region exploration chapter**: the filmed Gabby & Ty battle, the Route 110 vendor
rescue, optional beach battles, and the museum/quest — no gym spike, and no Hoenn badge yet. The
Hoenn circuit leads with **Wes's Shadow gym at Rustboro** (DESIGN gym list); **Brawly's Fighting
badge** — at **Dewford**, via the Petalburg→Dewford ferry — is a *later* Hoenn badge, not the first.
**Mauville** (the next city north, Chapter 9) **has no gym** (Surge only consults on its power
grid). Staging: [CHAPTER8_BUILD.md](CHAPTER8_BUILD.md); dialogue:
[CHAPTER8_SCENES_SPEC.md](CHAPTER8_SCENES_SPEC.md).

### Level anchors

| Subject | Level | Notes |
|---------|-------|-------|
| Route 109 beach trainers | 25-26 | Optional; the swimmers/tubers/sailors + Seashore House |
| Route 110 south trainers | 26-27 | The northbound rescue segment (north half + Trick House = Ch9) |
| **Gabby & Ty** (filmed, tier 1) | 26 | Double battle; tier 1 of their 6-tier Hoenn rematch ladder |
| Vendor-rescue pack (scripted wild) | 26-27 | 2-3 territorial Poochyena/Mightyena; not trainers |
| Wilds — Route 110 land | 25-27 | Hoenn-native, lifted up ~+13 from vanilla |
| Wilds — Route 109 / Slateport water | 25-30 | Surf/fishing; Wailmer the rare high mark |
| **Brawly** (reference — **NOT fought**) | — | Gym closed; roster below is for the later reopening |

The player should reach the north exit ~lv 27-28 via the rescue + optional beach battles, with
no grinding — climbing toward (but not yet reaching) the first Hoenn gym (**Wes, Shadow, at
Rustboro**, per the gym list). The north path itself leads to Mauville (no gym) and Lavaridge.

### Wild encounters

Species faithful to vanilla Hoenn; **levels lifted up** to the band, second-stage commons
softened where a low level would read oddly. **Hoenn is native-base** now; the one sparse
migrant is a coastal Kanto mon in the harbor water ("rode in on a hull"), kept rare.

**Route 110 (`Route110`) — land, lv 25-27** (southern segment):

| Slot | Species (levels) |
|------|------------------|
| Common | Poochyena → occasional Mightyena (lv 25-27) |
| Common | Wingull (lv 25-26) |
| Uncommon | Electrike (lv 25-27) — Electric; the Mauville power corridor bleeding south |
| Uncommon | Gulpin (lv 25-26) |
| Uncommon | Oddish (lv 25-26) |
| Rare (pair) | **Plusle / Minun** (lv 26-27) — Hoenn **natives** here (migrants back in Kanto) |

**Route 109 (`Route109`) + Slateport (`SlateportCity`) — water:**

| Method | Species (levels) |
|--------|------------------|
| Surf | Tentacool (lv 25-28), Wingull → Pelipper (lv 26-30) |
| Surf (rare) | Wailmer (lv 28-30) — the rare high mark |
| Old / Good Rod | Magikarp (lv 25), Tentacool (lv 25-27) |
| Super Rod | Wailmer (lv 28-30), Carvanha (lv 27) |
| **Rare (migrant)** | **Krabby** (Kanto) in the harbor (lv 25-27) — "rode in on a hull"; keep rare |

> **Re-tune note.** Vanilla Route 110 land is ~lv12-13 and Route 109/Slateport water is a wide
> lv5-40 fishing spread. Apocrypha seats land at lv25-27 and water at lv25-30 (Wailmer/Carvanha
> the high marks). Keep the *families* Hoenn-faithful; just lift the floor to the player's tier.
> Beach/harbor Wingull ties to the "port gulls" motif that started in Vermilion (Ch7).

### Trainer battles (pokeemerald source → rebuilt HGSS trainers, re-tuned up)

Teams are **Hoenn-native**; the imports elsewhere in the world become the *base* here. Movepools
stay route-tier. **1:1 to the pokeemerald source slots** (which become the new HGSS trainers).

**Gabby & Ty — the filmed battle (`TRAINER_GABBY_AND_TY_1`, double).** The RSE media duo; tier
1 of a **6-tier rematch ladder** (`_1..6`) that recurs across the Hoenn arc. Lifted up from
vanilla tier 1 (Magnemite@17 + Whismur@17):

| Side | Pokémon | Level | Notes |
|------|---------|-------|-------|
| Gabby | Magneton | 26 | Sonic Boom / Thunder Wave / Metal Sound — she narrates every move |
| Ty | Loudred | 26 | Astonish / Stomp / Howl — Ty says nothing; Loudred says everything |

> **Gabby & Ty rematch ladder** (for later Hoenn chapters, on the curve): tier 2 ~lv30, tier 3
> ~lv34, tier 4 ~lv38, tier 5 ~lv42, tier 6 ~lv46 (vanilla caps at Magneton/Exploud@39 with
> custom moves — lift each tier to the region-appropriate band as they reappear). Place one
> tier per later Hoenn route; they film the player's climb.

**Route 110 — southern segment (subset; the rest is Ch9).** Rebuilt from the vanilla Route 110
placements, re-lined as Hoenn-corridor locals:

| pokeemerald slot | Trainer (recast) | Team (Hoenn-native) | Level | Notes |
|------------------|------------------|---------------------|-------|-------|
| `TRAINER_TIMMY` | Youngster Timmy | Poochyena, Zigzagoon | 25, 26 | The going-up-while-everyone-flees kid |
| `TRAINER_ANTHONY` | Triathlete (cyclist) | Magnemite, Electrike | 26, 26 | Electric; trains beside the bike-gated Cycling Road |
| `TRAINER_EDWARD` | Psychic Edward | Ralts, Meditite | 26, 26 | Hoenn psychics; "territory is fear with a border" |
| `TRAINER_DALE` | Fisherman Dale | Magikarp, Carvanha | 25, 27 | Magikarp near-gag lead; Carvanha the bite |
| `TRAINER_ISABEL_1` | Pokéfan Isabel | Plusle, Minun | 26, 26 | The cutesy cheer-pair, native here |

**The vendor-rescue pack (scripted wild, not trainers).** 2-3 territorial wild battles clearing
the cornered Mauville merchants — "the pack that claimed the path":

| Encounter | Species | Level | Notes |
|-----------|---------|-------|-------|
| Pack member ×2 | Poochyena | 26 | Scripted wild; can be scared off, not caught-required |
| Pack alpha | Mightyena | 27 | The last one standing; clears the path on defeat/flee |

**Route 109 beach + Seashore House (optional).** Rebuilt from the vanilla beach placements;
**rename any vanilla "Mel"** (collision with Apocrypha's journalist). Hoenn-native water/beach:

| pokeemerald slot | Trainer (recast) | Team (Hoenn-native) | Level | Notes |
|------------------|------------------|---------------------|-------|-------|
| `TRAINER_LOLA_1` | Tuber Lola | Marill | 25 | "everybody near the water is fair game" |
| `TRAINER_AUSTINA` | Tuber Austina | Azurill, Marill | 25, 26 | The baby-mon-and-evolution pair |
| (recast swimmer) | Swimmer | Tentacool, Wingull | 26, 26 | Guards the drop-off |
| (recast sailor) | Sailor | Machop, Wingull | 26, 26 | Beach tough-guy |
| Seashore House `_Dwayne` | Sailor Dwayne | Wingull, Machop | 25, 26 | "battle for the stool" |
| Seashore House `_Simon` | Tuber Simon | Marill | 25 | |
| Seashore House `_Johanna` | Beauty Johanna | Wingull, Goldeen | 26, 26 | |

All beach battles are **optional** (~lv 25-26), Hoenn-native, water/beach movepools. A soft,
fun training pocket — no progression gate.

**Brawly — the closed gym (reference; NOT battled in Ch8).** Slateport's Fighting gym is closed
(Brawly commutes from Dewford). His vanilla roster (`TRAINER_BRAWLY_1`: Machop@16 / Meditite@16
/ Makuhita@19, Sitrus Berry) is recorded here for the **later reopening**, where it re-tunes to
the region-appropriate band (a badge-3-tier Fighting gym, ~**lv28-30**, Makuhita→**Hariyama**
ace; add Bulk Up pressure per his vanilla kit). **No `trainer_battle` this chapter** — the gym
is a closed façade + aide (see [CHAPTER8_BUILD.md](CHAPTER8_BUILD.md) §8.6).

### No badge, no boss (this chapter)

Chapter 8 has **no gym battle** — the climb is pure route/rescue XP toward the first Hoenn gym
(**Wes, Shadow, at Rustboro**, per DESIGN's gym list; **Brawly's Fighting badge** at Dewford, via
the Petalburg→Dewford ferry, is a *later* Hoenn badge; **Mauville has no gym**, Surge only consults
there). The Gabby & Ty filmed battle is the chapter's one "signature" fight; everything else is
optional beach/route training and the scripted rescue. The first Hoenn badge is a **later
chapter.**
