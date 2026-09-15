// Qualification via the ordinary ROM's engine entry points, not menu automation.
// Each invocation is a fresh emulator process; only a normal flash file is shared.
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void quietLog(struct mLogger *l, int c, enum mLogLevel level, const char *fmt, va_list args)
{
    (void)l; (void)c;
    if (level & (mLOG_FATAL | mLOG_ERROR)) { vfprintf(stderr, fmt, args); fputc('\n', stderr); }
}
static void reg(struct mCore *c, const char *name, uint32_t value)
{
    if (!c->writeRegister(c, name, &value)) { fprintf(stderr, "register %s failed\n", name); exit(10); }
}
static uint32_t call(struct mCore *c, uint32_t address, uint32_t arg)
{
    reg(c, "cpsr", 0x3f); // System mode, Thumb; engine installed interrupt handlers remain available.
    reg(c, "sp", 0x03007d00);
    reg(c, "r0", arg);
    reg(c, "lr", 0x09ffff01);
    reg(c, "pc", address & ~1u);
    for (unsigned i = 0; i < 200000000; ++i)
    {
        uint32_t pc;
        c->readRegister(c, "pc", &pc);
        if (pc >= 0x09ffff00 && pc <= 0x09ffff08)
        {
            uint32_t result;
            c->readRegister(c, "r0", &result);
            return result;
        }
        c->step(c);
    }
    uint32_t stuck; c->readRegister(c, "pc", &stuck);
    fprintf(stderr, "engine call timed out at %08x, PC %08x\n", address, stuck);
    exit(11);
}
int main(int argc, char **argv)
{
    if (argc != 9) { fprintf(stderr, "usage: persistence ROM FLASH write|read NEWGAME SAVE LOAD SB1PTR VAR_OFFSET\n"); return 2; }
    struct mLogger logger = {.log = quietLog};
    mLogSetDefaultLogger(&logger);
    struct mCore *c = mCoreFind(argv[1]);
    if (!c || !c->init(c)) return 3;
    mCoreConfigInit(&c->config, "apocrypha-persistence");
    color_t *pixels = calloc(240 * 160, sizeof(color_t));
    c->setVideoBuffer(c, pixels, 240);
    if (!mCoreLoadFile(c, argv[1])) return 4;
    if (!strcmp(argv[3], "read"))
    {
        FILE *f = fopen(argv[2], "rb");
        if (!f) return 5;
        unsigned char bytes[131072];
        size_t n = fread(bytes, 1, sizeof(bytes), f);
        fclose(f);
        if (n != sizeof(bytes) || !c->savedataRestore(c, bytes, n, false)) return 6;
    }
    c->reset(c);
    for (int i = 0; i < 600; ++i) c->runFrame(c);
    uint32_t newgame = strtoul(argv[4], NULL, 0), save = strtoul(argv[5], NULL, 0);
    uint32_t load = strtoul(argv[6], NULL, 0), ptr = strtoul(argv[7], NULL, 0);
    uint32_t offset = strtoul(argv[8], NULL, 0);
    uint32_t status;
    if (!strcmp(argv[3], "write"))
    {
        call(c, newgame, 0);
        c->busWrite16(c, c->busRead32(c, ptr) + offset, 4321);
        status = call(c, save, 0); // SAVE_NORMAL
        void *bytes = NULL;
        size_t n = c->savedataClone(c, &bytes);
        FILE *f = fopen(argv[2], "wb");
        if (!f || n != 131072 || fwrite(bytes, 1, n, f) != n) return 7;
        fclose(f); free(bytes);
    }
    else
        status = call(c, load, 0);
    uint32_t value = c->busRead16(c, c->busRead32(c, ptr) + offset);
    printf("{\"phase\":\"%s\",\"save_status\":%u,\"story_value\":%u}\n", argv[3], status, value);
    c->deinit(c); free(pixels);
    return status == 1 && value == 4321 ? 0 : 8;
}
