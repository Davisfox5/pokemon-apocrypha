#ifndef APOCRYPHA_PAGE_STORE_H
#define APOCRYPHA_PAGE_STORE_H
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define APS_SECTOR_SIZE 4096u
#define APS_SECTORS 32u
#define APS_PAGES 23u
#define APS_BYTES (APS_PAGES * APS_SECTOR_SIZE)
#define APS_MAX_CHANGED (APS_SECTORS - 2u - APS_PAGES)
#define APS_SCHEMA 1u
// This is a prototype schema, not a released game save format.
#define APS_LAYOUT 0x41503031u

enum ApsResult { APS_OK, APS_EMPTY, APS_CORRUPT, APS_FOREIGN, APS_IO, APS_TOO_MANY_CHANGES, APS_ARGUMENT };
struct ApsFlash {
    void *context;
    bool (*read)(void *, uint32_t offset, void *, uint32_t length);
    bool (*erase)(void *, uint8_t sector);
    bool (*program)(void *, uint32_t offset, const void *, uint32_t length);
};
struct ApsStore {
    struct ApsFlash flash;
    uint32_t generation;
    uint32_t crc[APS_PAGES];
    uint8_t map[APS_PAGES];
    uint8_t root;
    bool mounted;
    bool cacheValid;
    uint8_t cachedPage;
    uint8_t buffer[APS_SECTOR_SIZE];
};
typedef bool (*ApsFillPage)(void *, uint8_t logicalPage, uint8_t *page);
uint32_t ApsCrc32(const void *, size_t);
enum ApsResult ApsMount(struct ApsStore *, struct ApsFlash);
enum ApsResult ApsFormat(struct ApsStore *, struct ApsFlash, ApsFillPage, void *);
enum ApsResult ApsRead(struct ApsStore *, uint32_t offset, void *, uint32_t length);
enum ApsResult ApsCommit(struct ApsStore *, const uint8_t *changedPages, uint8_t count, ApsFillPage, void *);
#endif
