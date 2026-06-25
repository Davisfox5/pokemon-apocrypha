# Pokémon Apocrypha — Johto Item Locations

> **Scope:** Item locations for the **Johto** chapters — gift/key items, hidden items, and notable Mart stock. One of the per-region item docs. Pairs with:
> - [DESIGN.md](../DESIGN.md) — region/map design + high-level story
> - [JOHTO_BATTLES.md](JOHTO_BATTLES.md) — wild encounters + trainer battles
> - per-chapter docs (e.g. [CHAPTER1_BUILD.md](CHAPTER1_BUILD.md)) — interactions + quests
>
> **Engine:** pokeheartgold (HGSS).

---

## Chapter 1 — Cherrygrove · Route 29 · New Bark

Grounded in the real map files: `064_T21.json` (Cherrygrove), `030_R29.json` (Route 29), `057_T20.json` (New Bark). Geography: **Cherrygrove (west) → Route 29 (east) → New Bark (east)**; Route 30 (north of Cherrygrove) leads to Violet.

### Gift / key items

| Item | Where | How |
|------|-------|-----|
| Starter Poké Ball | Gold's house, Cherrygrove | Player chooses 1 of Cyndaquil / Totodile / Chikorita (Scene 2) |
| Pokédex | Elm's Lab, New Bark | Elm gives one to the player (and narratively to Kestra) (Scene 3) |
| Running Shoes + Town Map (Map Card) | Gold's house, Cherrygrove — end of starter ceremony (Scene 2) | Reassigned from the deceased Guide-Gent — Gold hands them over grumbling (repurposes vanilla tour msgs 6–7, 10–12). Given in Scene 2 so the player can run on Route 29. |
| Poké Ball ×5 | Cherrygrove, post-catching-tutorial (Scene 4) | Gold, after the catching demo |

### Field & hidden items (already placed on the maps)

| Item | Location (x,z) | Source object / script |
|------|----------------|------------------------|
| Potion (visible ball) | Route 29 (654,386) | `obj_R29_monstarball` → `std_itemball_r29_potion` |
| Nugget (hidden) | Route 29 / Cherrygrove border (572,390) | `std_hiddenitem_r29_r30_t21_nugget` |
| Potion (hidden) | Cherrygrove, west (522,388) | `std_hiddenitem_t21_nugget` → **downgraded to Potion** (was a Nugget; see note) |
| Potion (hidden) | New Bark (682,391) | `std_hiddenitem_t20_potion` |
| Apricorn — Red (param0=5) | Route 29 tree (596,392) | `obj_R29_bonguri` → `std_apricorn_tree` |

> The confirmed "reward curiosity on Route 29" goal is **already satisfied** by the existing visible Potion ball + hidden Nugget — no new item needed. **Decision (applied, reversible):** keep the Route 29/border Nugget but **downgrade the Cherrygrove (522,388) Nugget to a Potion**, so the player stays money-poor through the opening (revisit once the broader economy is designed). The cut Cherrygrove beach hidden-item beat stays cut. The Apricorn tree is harmless flavor (Kurt's ball-craft pays off in Ch.3, Azalea).

### Marts

**Cherrygrove Mart** — early/basic stock: Poké Balls, Potions, Antidote, Paralyze Heal, escape items. The player has little money this chapter; the Mart is mostly for Poké Balls and a Potion or two before heading out.

---

## Chapter 2 — *(to be designed)*

Mr. Pokémon's gift (held-item introduction), Route 30/31 items, Sprout Tower rewards, Ruins of Alph items, Union Cave items, Old Rod (Route 32). To be filled when Chapter 2 is designed.
