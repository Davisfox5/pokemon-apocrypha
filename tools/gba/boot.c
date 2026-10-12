// Headless execution of an ordinary ROM. This does not create a new map or art.
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <stdio.h>
#include <stdlib.h>

static void logMessage(struct mLogger *logger, int category, enum mLogLevel level, const char *format, va_list args)
{
    (void)logger; (void)category;
    if (level & (mLOG_FATAL | mLOG_ERROR)) { vfprintf(stderr, format, args); fputc('\n', stderr); }
}

int main(int argc, char **argv)
{
    if (argc != 2) { fprintf(stderr, "usage: boot ROM\n"); return 2; }
    struct mLogger logger = {.log = logMessage, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) return 3;
    mCoreConfigInit(&core->config, "apocrypha-baseline");
    color_t *pixels = calloc(240 * 160, sizeof(color_t));
    if (!pixels) return 4;
    core->setVideoBuffer(core, pixels, 240);
    if (!mCoreLoadFile(core, argv[1])) return 5;
    core->reset(core);
    for (int i = 0; i < 600; ++i) core->runFrame(core);
    uint32_t pc = 0;
    core->readRegister(core, "pc", &pc);
    unsigned different = 0;
    for (int i = 1; i < 240 * 160; ++i) different += pixels[i] != pixels[0];
    printf("{\"frames\":600,\"pc\":%u,\"nonuniform_pixels\":%u,\"save_test\":false}\n", pc, different);
    core->deinit(core);
    free(pixels);
    // At a frame boundary the CPU can be waiting in BIOS VBlankIntrWait.
    return different && (pc < 0x4000 || (pc >= 0x08000000 && pc < 0x0A000000)) ? 0 : 6;
}
