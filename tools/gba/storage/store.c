#include "store.h"
#include <string.h>

#define HEADER 32u
#define ROOT_BYTES (HEADER + APS_PAGES * 8u)
#define COMMIT_OFFSET (APS_SECTOR_SIZE - 1u)
static const uint8_t magic[8] = {'A','P','O','C','P','A','G','E'};
static uint32_t get32(const uint8_t *p) { return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24; }
static void put32(uint8_t *p, uint32_t v) { for (unsigned i=0;i<4;++i) p[i]=(uint8_t)(v>>(i*8)); }
uint32_t ApsCrc32(const void *data, size_t length)
{
    static const uint32_t table[16]={
        0x00000000u,0x1db71064u,0x3b6e20c8u,0x26d930acu,
        0x76dc4190u,0x6b6b51f4u,0x4db26158u,0x5005713cu,
        0xedb88320u,0xf00f9344u,0xd6d6a3e8u,0xcb61b38cu,
        0x9b64c2b0u,0x86d3d2d4u,0xa00ae278u,0xbdbdf21cu};
    const uint8_t *p=data; uint32_t crc=~0u;
    while (length--) {
        crc ^= *p++;
        crc=(crc>>4)^table[crc&15u];
        crc=(crc>>4)^table[crc&15u];
    }
    return ~crc;
}
static bool readSector(struct ApsStore *s, uint8_t n) { s->cacheValid=false; return s->flash.read(s->flash.context,n*APS_SECTOR_SIZE,s->buffer,APS_SECTOR_SIZE); }
static bool erased(const uint8_t *p, size_t n) { while(n--) if(*p++!=255) return false; return true; }
static bool validOps(struct ApsFlash f) { return f.read && f.erase && f.program; }

struct Root { uint32_t generation, crc[APS_PAGES]; uint8_t map[APS_PAGES]; };
static enum ApsResult loadRoot(struct ApsStore *s, uint8_t sector, struct Root *root)
{
    if (!readSector(s,sector)) return APS_IO;
    uint8_t *b=s->buffer;
    if (erased(b,APS_SECTOR_SIZE)) return APS_EMPTY;
    if (memcmp(b,magic,8)) return APS_CORRUPT;
    if (b[COMMIT_OFFSET]!=0) return APS_CORRUPT;
    uint32_t crc=get32(b+24); put32(b+24,0);
    if (ApsCrc32(b,ROOT_BYTES)!=crc) return APS_CORRUPT;
    if (get32(b+8)!=APS_SCHEMA || get32(b+12)!=APS_LAYOUT || get32(b+20)!=APS_BYTES || get32(b+28)!=APS_PAGES) return APS_FOREIGN;
    root->generation=get32(b+16);
    uint32_t used=3;
    for (unsigned i=0;i<APS_PAGES;++i) {
        uint32_t n=get32(b+HEADER+i*8);
        if (n<2 || n>=APS_SECTORS || (used & (1u<<n))) return APS_CORRUPT;
        used|=1u<<n; root->map[i]=(uint8_t)n; root->crc[i]=get32(b+HEADER+i*8+4);
    }
    for (unsigned i=0;i<APS_PAGES;++i) {
        if (!readSector(s,root->map[i])) return APS_IO;
        if (ApsCrc32(s->buffer,APS_SECTOR_SIZE)!=root->crc[i]) return APS_CORRUPT;
    }
    return APS_OK;
}
static void accept(struct ApsStore *s, const struct Root *r, uint8_t root)
{
    s->generation=r->generation; memcpy(s->crc,r->crc,sizeof(s->crc));
    memcpy(s->map,r->map,sizeof(s->map)); s->root=root; s->mounted=true;
}
enum ApsResult ApsMount(struct ApsStore *s, struct ApsFlash flash)
{
    if (!s || !validOps(flash)) return APS_ARGUMENT;
    memset(s,0,sizeof(*s)); s->flash=flash;
    struct Root a,b;
    enum ApsResult ra=loadRoot(s,0,&a), rb=loadRoot(s,1,&b);
    // Never replace an unknown schema or a failed device read with an older view.
    if (ra==APS_IO || rb==APS_IO) return APS_IO;
    if (ra==APS_FOREIGN || rb==APS_FOREIGN) return APS_FOREIGN;
    if (ra==APS_OK && (rb!=APS_OK || (int32_t)(a.generation-b.generation)>0)) { accept(s,&a,0); return APS_OK; }
    if (rb==APS_OK) { accept(s,&b,1); return APS_OK; }
    return ra==APS_EMPTY && rb==APS_EMPTY ? APS_EMPTY : APS_CORRUPT;
}
static bool writePage(struct ApsStore *s, uint8_t physical, uint32_t crc)
{
    if (!s->flash.erase(s->flash.context,physical)) return false;
    if (!s->flash.program(s->flash.context,physical*APS_SECTOR_SIZE,s->buffer,APS_SECTOR_SIZE)) return false;
    return readSector(s,physical) && ApsCrc32(s->buffer,APS_SECTOR_SIZE)==crc;
}
static bool writeRoot(struct ApsStore *s, uint8_t sector, const struct Root *r)
{
    memset(s->buffer,255,APS_SECTOR_SIZE);
    uint8_t *b=s->buffer; memcpy(b,magic,8); put32(b+8,APS_SCHEMA); put32(b+12,APS_LAYOUT);
    put32(b+16,r->generation); put32(b+20,APS_BYTES); put32(b+24,0); put32(b+28,APS_PAGES);
    for(unsigned i=0;i<APS_PAGES;++i) { put32(b+HEADER+i*8,r->map[i]); put32(b+HEADER+i*8+4,r->crc[i]); }
    uint32_t crc=ApsCrc32(b,ROOT_BYTES); put32(b+24,crc);
    if (!s->flash.program(s->flash.context,sector*APS_SECTOR_SIZE,b,ROOT_BYTES)) return false;
    if (!readSector(s,sector)) return false;
    if (get32(s->buffer+24)!=crc) return false;
    put32(s->buffer+24,0);
    if (ApsCrc32(s->buffer,ROOT_BYTES)!=crc) return false;
    uint8_t committed=0;
    if (!s->flash.program(s->flash.context,sector*APS_SECTOR_SIZE+COMMIT_OFFSET,&committed,1)) return false;
    uint8_t verify=255;
    return s->flash.read(s->flash.context,sector*APS_SECTOR_SIZE+COMMIT_OFFSET,&verify,1) && verify==0;
}
enum ApsResult ApsFormat(struct ApsStore *s, struct ApsFlash flash, ApsFillPage fill, void *context)
{
    if (!s || !validOps(flash) || !fill) return APS_ARGUMENT;
    memset(s,0,sizeof(*s)); s->flash=flash;
    // Formatting is only permitted on a blank medium; never erase a foreign save.
    for (unsigned i=0;i<APS_SECTORS;++i) {
        if (!readSector(s,i)) return APS_IO;
        if (!erased(s->buffer,APS_SECTOR_SIZE)) return APS_FOREIGN;
    }
    struct Root r; r.generation=1;
    for (unsigned i=0;i<APS_PAGES;++i) {
        r.map[i]=(uint8_t)(i+2);
        if (!fill(context,i,s->buffer)) return APS_IO;
        r.crc[i]=ApsCrc32(s->buffer,APS_SECTOR_SIZE);
        if (!writePage(s,r.map[i],r.crc[i])) return APS_IO;
    }
    if (!writeRoot(s,0,&r)) return APS_IO;
    accept(s,&r,0); return APS_OK;
}
enum ApsResult ApsRead(struct ApsStore *s, uint32_t offset, void *out, uint32_t length)
{
    if (!s || !s->mounted || (!out && length) || offset>APS_BYTES || length>APS_BYTES-offset) return APS_ARGUMENT;
    uint8_t *dst=out;
    while(length) {
        uint32_t page=offset/APS_SECTOR_SIZE, in=offset%APS_SECTOR_SIZE, n=APS_SECTOR_SIZE-in;
        if(n>length) n=length;
        if(!s->cacheValid || s->cachedPage!=page) {
            if(!readSector(s,s->map[page])) return APS_IO;
            if(ApsCrc32(s->buffer,APS_SECTOR_SIZE)!=s->crc[page]) return APS_CORRUPT;
            s->cachedPage=(uint8_t)page; s->cacheValid=true;
        }
        memcpy(dst,s->buffer+in,n); dst+=n; offset+=n; length-=n;
    }
    return APS_OK;
}
enum ApsResult ApsCommit(struct ApsStore *s, const uint8_t *pages, uint8_t count, ApsFillPage fill, void *context)
{
    if(!s || !s->mounted || !fill || (count && !pages)) return APS_ARGUMENT;
    if(count>APS_MAX_CHANGED) return APS_TOO_MANY_CHANGES;
    uint32_t seen=0, used=3;
    for(unsigned i=0;i<count;++i) {
        if(pages[i]>=APS_PAGES || (seen & (1u<<pages[i]))) return APS_ARGUMENT;
        seen|=1u<<pages[i];
    }
    if(!count) return APS_OK;
    // Read-only validation precedes invalidating the inactive root or erasing data.
    for(unsigned i=0;i<APS_PAGES;++i) {
        used|=1u<<s->map[i];
        if(!readSector(s,s->map[i])) return APS_IO;
        if(ApsCrc32(s->buffer,APS_SECTOR_SIZE)!=s->crc[i]) return APS_CORRUPT;
    }
    struct Root r; r.generation=s->generation+1;
    memcpy(r.map,s->map,sizeof(r.map)); memcpy(r.crc,s->crc,sizeof(r.crc));
    uint8_t target=s->root^1u;
    // From this point an I/O failure requires remounting: commit may have landed.
    s->mounted=false;
    if(!s->flash.erase(s->flash.context,target)) return APS_IO;
    for(unsigned i=0;i<count;++i) {
        unsigned physical=2; while(physical<APS_SECTORS && (used & (1u<<physical))) ++physical;
        if(physical==APS_SECTORS) return APS_ARGUMENT;
        used|=1u<<physical;
        uint8_t page=pages[i]; r.map[page]=(uint8_t)physical;
        if(!fill(context,page,s->buffer)) return APS_IO;
        r.crc[page]=ApsCrc32(s->buffer,APS_SECTOR_SIZE);
        if(!writePage(s,(uint8_t)physical,r.crc[page])) return APS_IO;
    }
    if(!writeRoot(s,target,&r)) return APS_IO;
    accept(s,&r,target); return APS_OK;
}
