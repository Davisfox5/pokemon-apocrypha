# Pokémon Apocrypha — Art / Asset Pass Spec (Chapter 1)

**Purpose.** Everything in Chapter 1 that is **not code** — palettes, map tiles, interior 3D
room models, and new overworld sprites. These cannot be produced from this repo's build
(`make` only assembles existing binaries; there is **no tile/model/sprite source pipeline**),
so each item below is an external-GUI-tool task. Field scripts, messages, events, item/flag
logic, and the new-game flow are **already built and compiling** (see
[CHAPTER1_BUILD.md](CHAPTER1_BUILD.md)); this doc is the remaining art layer only.

**Hard finding (verified this pass):** the engine has **917 overworld sprites** and **none**
are usable as moving-boxes, furniture, boats, benches, piers, or decorative cherry trees
(only the generic HM `SPRITE_TREE` (86) and follower-mon sprites exist). So **no "just moved
in" props, waterfront objects, or blossom trees can be placed by code** — every one needs a
new sprite/tile/model first. That is why this pass produced specs, not object placements.

---

## 0. Toolchain (what to install)

| Tool | Used for | Targets |
|---|---|---|
| **DS Pokémon ROM Editor (DSPRE)** | map tiles, map→model wiring, headers, events sanity | the built `.nds` and/or the NARCs below |
| **Tinke** / **Nitro Explorer** | unpack/repack NARCs, swap `.bin` members | `bm_room.narc`, tileset NARCs |
| **G3DCWL / "DS Map Studio"** or **3DS Max + Nitro plugins** | author/convert NSBMD room models | `bm_room_*.bin` |
| **NitroPaint** | palettes (NCLR), tile graphics (NCGR), tilemaps (NSCR), OW sprite frames | tileset + sprite NARCs |
| (optional) **kiwi.ds / apicula** | inspect existing NSBMD to match format | reference only |

**Workflow shape:** edit asset in GUI tool → export in Nitro format → repack into the
NARC member → drop the NARC back under `files/…` → re-run `_omni_native_build.sh` (the build
just packs `files/` into the ROM, so replaced assets ship as-is).

---

## 1. Game-wide cinematic colour grade (PILOT: Cherrygrove)

From DESIGN.md *Visual Identity & Art Direction*. Author this **first, on Cherrygrove**, then
reuse it as the template for every other Johto tileset.

- **Grade:** shadows → cool teal; highlights → warm amber; midtones rich-but-desaturated
  (kill the flat GSC primaries). This is a palette (NCLR) re-author, not new tiles.
- **Local accent — Cherrygrove:** cherry-blossom **pink**.
- **Day/night variants:** author both so the grade deepens at night rather than fighting it.
  HGSS swaps palettes by time-of-day automatically; just supply the graded variants.
- **Files:** the Cherrygrove outdoor tileset palette(s). Find via DSPRE → MAP_CHERRYGROVE →
  its area/tileset; the time-of-day light tables are the `data/area**light.txt` /
  `data/arealight.narc` set already shipped in `files/data/`.
- **Acceptance:** boot to Cherrygrove; it must read as a *different game* from vanilla HG at a
  glance, same geography. Compare day vs. night.

---

## 2. Cherrygrove "10 years on" — map tiles & props (064_T21)

All [asset]. Coordinates are the real global-world coords from `064_T21.json`.

1. **Matured cherry grove + blossom park.** Reskin tree tiles → flowering cherry; densest
   framing **Gold's house (558,401)** and central lanes (x≈554–562, z≈399–403). Add a small
   **park pocket** NW of the Mart/Center (≈548–553, 393–398): petal-strewn ground tile + bench.
   *Needs:* cherry-blossom tree tile, fallen-petal ground tile, bench prop.
2. **Weathered fishing waterfront.** South strip is already sea. Add a **sand strip**
   (z≈406–409), a **worn wooden pier** ≈(560–564, 407–410), **2–3 idle/beached boat objects**,
   **drying-net props**. Non-boardable (no warp). Ties to the re-voiced `gswoman1` line
   ("These boats don't go far anymore…"). *Needs:* pier + net tiles; boat objects/sprites.
3. **Modest growth — 1–2 new homes** west of the player's house (≈540–545, 401–405). Facades
   by default; optionally make **one enterable** with a "moved here for the quiet, like Gold"
   resident (new room model + a flavor NPC line).
4. **Coastal lookout** SE near the Southeast house (≈566–569, 406–409): railing tile + bench
   ("this is where Gold sits"). *Needs:* railing/overlook tile, bench prop.
5. **Understated Gold reverence (no statue).** A **worn battle-ring tile** in Gold's yard
   (≈556–558, 404). The reverence **sign is already written** (`scr_seq_T21_005` / msg row 24).
6. **Weathering pass.** Age Center/Mart/house textures within the grade — a decade of sea air.

**Cherrygrove asset checklist:** graded palette set (+day/night) · cherry-blossom tree tile ·
fallen-petal ground tile · pier tile · drying-net prop · 1–2 house models (or facades) ·
railing/overlook tile · bench prop · worn-battle-ring tile · boat objects.

---

## 3. Interiors — player's house "just moved in" (060_T20R0201)

The opening cold-open already runs in this map (built). What's missing is the **look**.

- **Swap to a roomier existing room model.** The map currently uses the vanilla New Bark
  protagonist-house interior. Point 1F (and 2F) at a nicer **existing** `bm_room_*.bin`
  member so it doesn't read as the default home. The map→room-model index lives in the
  **area-build / `areaDataBank`** wiring — `MAP_NEW_BARK_PLAYER_HOUSE_1F` uses
  `areaDataBank = 25` (`src/data/map_headers.h:1906`); 2F is `MAP_NEW_BARK_PLAYER_HOUSE_2F`
  (`:1936`). Re-point in DSPRE, or swap the `bm_room.narc` member bytes.
- **"Just moved in" dressing.** Place **moving-box objects**, scattered furniture, the PC.
  *Blocked:* no box/furniture OW sprite exists (see top finding) — this needs new OW sprites
  **or** baking the boxes into a custom room model (preferred: it's static dressing).
- **Bespoke room (optional, highest effort):** author a custom NSBMD in DS Map Studio / 3DS
  Max and fold it into `bm_room.narc`. This is the "entirely custom interior" ask; everything
  else above is reuse + dressing.
- **Already done in code (no art needed):** Mom placement/dialogue, the 2F PC granting a
  Potion, the upstairs-and-back flow, Mom's menu+Pokégear hand-off.

---

## 4. New overworld sprites — Gold & Kestra (distinct identities)

Currently **Gold = SPRITE_GSMIDDLEMAN1** and **Kestra = SPRITE_GSGIRL2** (best in-engine
fits; both ship fine). For true identity:

- **Adult Gold OW sprite.** A distinct grown-Gold (the GSC hero, aged ~10 years). New OW
  sprite sheet (walk/face frames + palette) inserted as a new `SPRITE_*`; then change
  `obj_T21_gold` (and the ceremony Gold) `spriteId` in `064_T21.json`.
  *Do NOT use `SPRITE_HERO_2` — it is player-only and crashes as an NPC.*
- **Kestra OW sprite (optional).** GSGIRL2 is a clean fit; only replace if a bespoke
  child-rival look is wanted. Keep her **female and fixed** across all five regions.

Sprite NARC + the `SPRITE_` table (`include/constants/sprites.h`) are the insertion points;
follow an existing OW sprite's frame/palette layout exactly.

---

## 5. Route 29 & New Bark grade (after Cherrygrove template lands)

- **Route 29 (030_R29):** apply the warm-amber/teal grade to the outdoor tileset; let the
  **westmost 2–3 tree tiles** spill cherry-blossom (continuity from the grove) fading to
  ordinary graded woodland east. Optional sea-view ridge ≈(640–650, 404–408): railing+bench.
- **New Bark (057_T20):** same regional grade, **cooler/cleaner local accent** (lab teal /
  off-white) — institute, not village. Campus redress: microscopes, equipment crates, paved
  paths, tidy signage around Elm's Lab exterior (≈684–700, 384–400); optional non-enterable
  research-annex facade. (New Bark's *script/NPC* redress is tracked in CHAPTER1_BUILD.md §8.3,
  separate from this art doc.)

---

## 6. Priority order (ship value vs. effort)

1. **Cherrygrove colour grade (§1).** Highest impact, lowest effort (palette only). Proves the
   "different game" promise the moment you boot.
2. **Cherrygrove cherry-blossom tree + petal tiles (§2.1).** The signature look.
3. **Player-house model swap + dressing (§3).** The opening is the first thing players see.
4. **Waterfront + lookout tiles/objects (§2.2, §2.4).**
5. **Adult-Gold OW sprite (§4).**
6. **Route 29 / New Bark grade (§5).**

---

## 7. What is already done in code (do not re-spec)

Opening flow (start in Cherrygrove house, cold open, Mom, 2F PC+Potion, Pokégear, gender-only
intro with naming deferred), Scene 1 (Silver battle + Kestra first-meeting + **naming** +
crowd), Scene 2 (grass rescue + Gold catch + outdoor starter ceremony + **Running Shoes &
Map Card**), Cherrygrove NPC/sign re-voicing, dead-flow retirement. All compiling
(`MAKE EXIT=0`). See [CHAPTER1_BUILD.md](CHAPTER1_BUILD.md) for the script-level detail.
