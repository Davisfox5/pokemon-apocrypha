// Headless mGBA checks for the Hidden Grotto mechanic, driven by tools/gba/grottoes/runtime.py.
//
//   grotto_runtime ROM SYMBOLS OUT write|read
//
// write: new game; the test woods (three big-tree entrances, one per interior); the first visit rolls content;
//        a forced Pokémon slot shows its overworld sprite, starts a wild battle with the Hidden
//        Ability, empties after fleeing; a forced item slot shows an item ball and is picked up;
//        the refill rate over 4000 simulated 256-step wraps; walking advances the step counter;
//        the exit returns to the entrance; the blossom and winding interiors open from their own
//        entrances and lead back to them; ordinary save.
// read:  cold reload of that save; the grotto state and step counter survive.
#define main unused_map_runtime_main
#include "RUNTIME_C"
#undef main

static const char *out;
static unsigned SB3_GROTTOES, SB3_STEPS, MON_SIZE, MD_ABILITY_NUM, MD_SPECIES, MD_LEVEL, MD_IS_SHINY;
static unsigned GROTTO_GROUP, GROTTO_NUM, PROOF_GROUP, PROOF_NUM, PROOF_INDEX, ITEM_PEARL, BLOSSOM_NUM, WINDING_NUM;
// Test woods: each entrance is the two trunk-row cells where two trees meet, at x = 5/6, 15/16, 25/26
// on row 11; the field starts at row 12. Interiors: arrival (15,18), exit below it; the round
// hollow's content stands at (15,12).
#define ENT_Y 11
#define FIELD_Y 13
#define ARRIVE_X 15
#define ARRIVE_Y 18
#define CONTENT_STEPS 5
enum { A = 1, B = 2, RIGHT = 16, LEFT = 32, UP = 64, DOWN = 128 };

static unsigned callN(const char *name, unsigned a0, unsigned a1, unsigned a2)
{
    unsigned r1 = rd("r1"), r2 = rd("r2");
    wr("r1", a1); wr("r2", a2);
    unsigned v = call(name, a0);
    wr("r1", r1); wr("r2", r2);
    return v;
}
static void shot(const char *t) { screenshot(out, t); printf("{\"shot\":\"%s\"}\n", t); fflush(stdout); }
static void need(int ok, const char *tag) { if (!ok) { fprintf(stderr, "FAILED %s (group %u map %u at %u,%u)\n", tag, state[1], state[2], state[3], state[4]); shot(tag); exit(40); } }
static int locked(void) { return call("ArePlayerFieldControlsLocked", 0); }
static int overworld(void) { unsigned cb = c->busRead32(c, sym("gMain") + 4); return (cb & ~1u) == (sym("CB2_Overworld") & ~1u); }
static void peek(void) { call("MapProof_ReadState", 0); unsigned a = sym("gMapProofState"); for (int i = 0; i < 10; i++) state[i] = c->busRead32(c, a + 4 * i); }
static int moves;
static void step(unsigned key) { peek(); unsigned x = state[3], y = state[4], m = state[2]; for (int t = 0; t < 32; t++) { frames(2, key); peek(); if (state[3] != x || state[4] != y || state[2] != m) { moves++; break; } } frames(40, 0); }
static void tap(unsigned key) { frames(2, key); frames(12, 0); }
static void wait_field(int max) { for (int i = 0; i < max && !(overworld() && !locked()); i++) frames(10, 0); }
static unsigned sb3(void) { return c->busRead32(c, sym("gSaveBlock3Ptr")); }
static unsigned grotto_state(void) { return call("GetHiddenGrottoState", 0); }
static void set_state(unsigned v) { c->busWrite8(c, sb3() + SB3_GROTTOES, v); need(grotto_state() == v, "set-state"); }
static unsigned enemy(void) { return sym("gParties") + 1 * 6 * MON_SIZE; }
static unsigned slot_rom(unsigned n) { return c->busRead32(c, sym("gHiddenGrottoes") + 8) + 8 * n; }
static unsigned slot_count(void) { return c->busRead8(c, sym("gHiddenGrottoes") + 4); }
static unsigned state_of(unsigned id) { return c->busRead8(c, sb3() + SB3_GROTTOES + id); }
static void at(unsigned g, unsigned m, unsigned x, unsigned y, const char *tag) { observe(tag); need(state[1] == g && state[2] == m && state[3] == x && state[4] == y, tag); }

// From the field, walk north into the entrance between two trees.
static void enter_at(unsigned ex, unsigned num, const char *tag, const char *belowshot)
{
    call("MapProof_Enter", PROOF_INDEX | (ex << 8) | ((unsigned)FIELD_Y << 16)); frames(300, 0); wait_field(60);
    at(PROOF_GROUP, PROOF_NUM, ex, FIELD_Y, "entrance-square");
    step(UP);
    at(PROOF_GROUP, PROOF_NUM, ex, ENT_Y + 1, "below-entrance");
    if (belowshot) shot(belowshot);
    step(UP); frames(200, 0); wait_field(60);
    at(GROTTO_GROUP, num, ARRIVE_X, ARRIVE_Y, tag);
}
static void enter(const char *tag) { enter_at(5, GROTTO_NUM, tag, NULL); }
// Walk up to stand below the content, facing it.
static void approach(void) { for (int i = 0; i < CONTENT_STEPS; i++) step(UP); at(GROTTO_GROUP, GROTTO_NUM, ARRIVE_X, ARRIVE_Y - CONTENT_STEPS, "below-content"); }
static void leave_to(unsigned ex, const char *tag)
{
    step(DOWN); frames(260, 0); wait_field(60);
    observe(tag); need(state[1] == PROOF_GROUP && state[2] == PROOF_NUM && state[3] == ex && state[4] == ENT_Y + 1, tag);   // the door exit steps the player back out onto the field
}
static void leave(const char *tag) { leave_to(5, tag); }

int main(int argc, char **argv)
{
    if (argc != 5) { fprintf(stderr, "grotto_runtime ROM SYMBOLS OUT write|read\n"); return 2; }
    out = argv[3];
    FILE *f = fopen(argv[2], "r"); if (!f) return 3;
    while (ns < 128 && fscanf(f, "%79s %x", names[ns], &addrs[ns]) == 2) ns++;
    fclose(f);
    // Layout constants measured from the engine build by runtime.py.
    SB3_GROTTOES = sym("K_SB3_GROTTOES"); SB3_STEPS = sym("K_SB3_STEPS"); MON_SIZE = sym("K_MON_SIZE");
    MD_ABILITY_NUM = sym("K_MD_ABILITY_NUM"); MD_SPECIES = sym("K_MD_SPECIES"); MD_LEVEL = sym("K_MD_LEVEL"); MD_IS_SHINY = sym("K_MD_IS_SHINY");
    GROTTO_GROUP = sym("K_GROTTO_GROUP"); GROTTO_NUM = sym("K_GROTTO_NUM"); PROOF_GROUP = sym("K_PROOF_GROUP"); PROOF_NUM = sym("K_PROOF_NUM");
    PROOF_INDEX = sym("K_PROOF_INDEX"); ITEM_PEARL = sym("K_ITEM_PEARL"); BLOSSOM_NUM = sym("K_BLOSSOM_NUM"); WINDING_NUM = sym("K_WINDING_NUM");

    struct mLogger log = {.log = quiet}; mLogSetDefaultLogger(&log);
    c = mCoreFind(argv[1]); if (!c || !c->init(c)) return 4;
    mCoreConfigInit(&c->config, "hidden-grotto"); c->setVideoBuffer(c, pixels, 240);
    if (!mCoreLoadFile(c, argv[1])) return 5;
    char flash[2048]; snprintf(flash, sizeof(flash), "%s/grotto.sav", out);
    if (!strcmp(argv[4], "read"))
    {
        unsigned char data[131072]; f = fopen(flash, "rb");
        if (!f || fread(data, 1, sizeof(data), f) != sizeof(data)) return 6;
        fclose(f); if (!c->savedataRestore(c, data, sizeof(data), false)) return 7;
    }
    c->reset(c); frames(600, 0);

    if (!strcmp(argv[4], "read"))
    {
        need(call("LoadGameSave", 0) == 1, "load-status");
        call("MapProof_Resume", 0); frames(300, 0); wait_field(60);
        unsigned s = grotto_state(), steps = c->busRead8(c, sb3() + SB3_STEPS);
        printf("{\"reload_state\":%u,\"reload_steps\":%u}\n", s, steps);
        need(s == 2 && steps == 77, "state-survives-reload");
        observe("reloaded"); shot("cold-reload");
        enter("reloaded-entered"); frames(30, 0); shot("reloaded-grotto");
        c->deinit(c); return 0;
    }

    call("MapProof_Boot", 0); frames(240, 0); wait_field(60);
    // MapProof_Boot skips the naming screen: give the player a terminated name for item messages.
    { static const unsigned char nm[] = {0xCA, 0xC6, 0xBB, 0xD3, 0xBF, 0xCC, 0xFF, 0xFF}; unsigned sb2 = c->busRead32(c, sym("gSaveBlock2Ptr")); for (int i = 0; i < 8; i++) c->busWrite8(c, sb2 + i, nm[i]); }
    unsigned lead = c->busRead16(c, slot_rom(0));
    need(callN("ScriptGiveMon", lead, 50, 0) != 2, "give-lead");
    printf("{\"slots\":%u,\"lead_species\":%u}\n", slot_count(), lead);

    // A new save: the grotto is unvisited (counts as full) until the first entry rolls it.
    need(grotto_state() == 0, "unvisited-at-start");
    call("MapProof_Enter", PROOF_INDEX | (15u << 8) | (14u << 16)); frames(300, 0); wait_field(60); shot("entrance-outside");
    enter_at(5, GROTTO_NUM, "first-entry", "entrance-below");
    unsigned first = grotto_state(); printf("{\"first_roll\":%u}\n", first);
    need(first >= 1 && first <= slot_count(), "first-visit-rolls");
    frames(30, 0); shot("first-visit");
    leave("exit-to-entrance"); frames(30, 0); shot("exit-outside");

    // Every Pokémon slot: forced, sprite shown, battle with the Hidden Ability, empty after fleeing.
    for (unsigned n = 0; n < slot_count(); n++)
    {
        unsigned rom = slot_rom(n), species = c->busRead16(c, rom), item = c->busRead16(c, rom + 2);
        unsigned lo = c->busRead8(c, rom + 4), hi = c->busRead8(c, rom + 5), gender = c->busRead8(c, rom + 6);
        char t[64];
        set_state(n + 1);
        enter("forced-entry"); frames(30, 0);
        approach(); frames(20, 0);
        sprintf(t, "slot%u-content", n); shot(t);
        if (species)
        {
            frames(1, A); frames(400, 0);
            sprintf(t, "slot%u-battle", n); shot(t);
            need(!overworld(), "battle-started");
            unsigned mon = enemy();
            unsigned sp = callN("GetMonData2", mon, MD_SPECIES, 0), lv = callN("GetMonData2", mon, MD_LEVEL, 0);
            unsigned an = callN("GetMonData2", mon, MD_ABILITY_NUM, 0), shiny = callN("GetMonData2", mon, MD_IS_SHINY, 0);
            unsigned ab = call("GetMonAbility", mon), ha = callN("GetAbilityBySpecies", species, 2, 0), g = call("GetMonGender", mon);
            printf("{\"slot\":%u,\"species\":%u,\"level\":%u,\"ability_num\":%u,\"ability\":%u,\"hidden_ability\":%u,\"shiny\":%u,\"gender\":%u,\"slot_gender\":%u}\n", n, sp, lv, an, ab, ha, shiny, g, gender);
            need(sp == species && lv >= lo && lv <= hi && an == 2 && ab == ha && ab != 0 && shiny == 0, "hidden-ability-mon");
            if (gender == 2) need(g == 0xFE, "female-slot");
            need(grotto_state() == 0xFF, "empty-once-encountered");
            // Run: Fight/Bag/Pokémon/Run, Run is bottom right.
            for (int i = 0; i < 30 && !overworld(); i++) { tap(RIGHT); tap(DOWN); frames(1, A); frames(90, 0); frames(1, B); frames(30, 0); }
            frames(240, 0); wait_field(80);
            at(GROTTO_GROUP, GROTTO_NUM, ARRIVE_X, ARRIVE_Y - CONTENT_STEPS, "back-after-battle");
            sprintf(t, "slot%u-after-battle", n); shot(t);
        }
        else
        {
            unsigned before = callN("CheckBagHasItem", item, 1, 0);
            frames(1, A); frames(200, 0);
            sprintf(t, "slot%u-pickup", n); shot(t);
            for (int i = 0; i < 20 && !(overworld() && !locked() && !call("ScriptContext_IsEnabled", 0)); i++) { frames(1, A); frames(40, 0); }
            wait_field(60);
            unsigned after = callN("CheckBagHasItem", item, 1, 0);
            printf("{\"slot\":%u,\"item\":%u,\"had_before\":%u,\"has_after\":%u,\"state\":%u}\n", n, item, before, after, grotto_state());
            need(after == 1 && grotto_state() == 0xFF, "item-picked-and-empty");
            sprintf(t, "slot%u-after-pickup", n); shot(t);
        }
        // Empty grotto on the next visit: nothing to talk to.
        for (int i = 0; i < CONTENT_STEPS; i++) step(DOWN);
        leave("exit-after-take");
        enter("empty-entry"); frames(30, 0);
        sprintf(t, "slot%u-empty-revisit", n); shot(t);
        approach(); frames(1, A); frames(60, 0); need(overworld() && !locked(), "empty-nothing-to-talk-to");
        for (int i = 0; i < CONTENT_STEPS; i++) step(DOWN);
        leave("exit-empty");
    }

    // The other two interiors: each entrance leads to its own interior, rolls its own grotto, and
    // the exit returns to that entrance. The blossom one is entered by its right-hand cell.
    need(state_of(1) == 0 && state_of(2) == 0, "others-unvisited");
    enter_at(16, BLOSSOM_NUM, "blossom-entry", NULL); frames(30, 0); shot("blossom-interior");
    need(state_of(1) == 1 && state_of(0) != 0, "blossom-rolled-its-own-grotto");
    leave_to(16, "blossom-exit");
    enter_at(25, WINDING_NUM, "winding-entry", NULL); frames(30, 0); shot("winding-interior");
    need(state_of(2) == 1, "winding-rolled-its-own-grotto");
    for (int i = 0; i < 3; i++) step(UP);
    frames(20, 0); shot("winding-path");
    for (int i = 0; i < 3; i++) step(DOWN);
    leave_to(25, "winding-exit");
    printf("{\"blossom_state\":%u,\"winding_state\":%u}\n", state_of(1), state_of(2));

    // Refill rate: 4000 wraps of the 256-step counter with the grotto empty.
    unsigned fills = 0, counts[16] = {0};
    for (int i = 0; i < 4000; i++)
    {
        set_state(0xFF); c->busWrite8(c, sb3() + SB3_STEPS, 255);
        call("UpdateHiddenGrottoStepCounter", 0);
        unsigned s = grotto_state();
        if (s != 0xFF) { fills++; if (s < 16) counts[s]++; }
    }
    printf("{\"refill_trials\":4000,\"refills\":%u,\"by_slot\":[", fills);
    for (unsigned n = 1; n <= slot_count(); n++) printf("%s%u", n > 1 ? "," : "", counts[n]);
    printf("]}\n");
    need(fills > 120 && fills < 290, "refill-near-5-percent");
    // No refill mid-count.
    set_state(0xFF); c->busWrite8(c, sb3() + SB3_STEPS, 10);
    for (int i = 0; i < 200; i++) call("UpdateHiddenGrottoStepCounter", 0);
    need(grotto_state() == 0xFF, "no-refill-before-256");

    // Walking advances the counter.
    call("MapProof_Enter", PROOF_INDEX | (8u << 8) | (14u << 16)); frames(300, 0); wait_field(60);
    c->busWrite8(c, sb3() + SB3_STEPS, 0); moves = 0;
    for (int i = 0; i < 6; i++) step(RIGHT);
    for (int i = 0; i < 6; i++) step(LEFT);
    frames(60, 0);
    unsigned walked = c->busRead8(c, sb3() + SB3_STEPS);
    printf("{\"squares_walked\":%d,\"steps_counted\":%u}\n", moves, walked);
    need(moves >= 8 && walked == (unsigned)moves, "steps-counted");

    // Save with a known state for the reload phase.
    set_state(2); c->busWrite8(c, sb3() + SB3_STEPS, 77);
    unsigned status = call("TrySavingData", 0);
    void *data = NULL; size_t size = c->savedataClone(c, &data);
    f = fopen(flash, "wb");
    if (status != 1 || size != 131072 || !f || fwrite(data, 1, size, f) != size) return 11;
    fclose(f); free(data);
    printf("{\"save_status\":%u}\n", status);
    c->deinit(c); return 0;
}
