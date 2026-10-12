#include "store.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if(!(x)) { fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x); exit(1); } } while(0)
static uint8_t flashBytes[APS_SECTORS*APS_SECTOR_SIZE], original[sizeof(flashBytes)];
static uint8_t expected[APS_BYTES], previous[APS_BYTES];
static struct ApsStore store;
static int cut=-1, action=0;
static bool corruptProgram=false, loseCommitAck=false;
static unsigned programStride=64, eraseStride=1024;
static bool readFlash(void *ctx,uint32_t offset,void *dst,uint32_t n)
{ (void)ctx; if(offset>sizeof(flashBytes)||n>sizeof(flashBytes)-offset) return false; memcpy(dst,flashBytes+offset,n);return true; }
static bool advance(void) { return cut<0 || action++!=cut; }
static bool eraseFlash(void *ctx,uint8_t sector)
{
    (void)ctx; if(sector>=APS_SECTORS)return false;
    for(unsigned i=0;i<APS_SECTOR_SIZE;i+=eraseStride) {
        if(!advance())return false;
        unsigned n=APS_SECTOR_SIZE-i;if(n>eraseStride)n=eraseStride;
        memset(flashBytes+sector*APS_SECTOR_SIZE+i,255,n);
    }return true;
}
static bool programFlash(void *ctx,uint32_t offset,const void *src,uint32_t n)
{
    (void)ctx; const uint8_t *p=src;
    if(offset>sizeof(flashBytes)||n>sizeof(flashBytes)-offset)return false;
    unsigned stride=n==32+APS_PAGES*8 ? 1 : programStride;
    if(n==1 && p[0]==0) {
        for(unsigned bit=0;bit<8;++bit) { if(!advance())return false; flashBytes[offset]&=(uint8_t)~(1u<<bit); }
        return !loseCommitAck;
    }
    for(unsigned i=0;i<n;i+=stride) {
        if(!advance())return false;
        unsigned end=i+stride;if(end>n)end=n;
        for(unsigned j=i;j<end;++j) { CHECK((flashBytes[offset+j]&p[j])==p[j]);flashBytes[offset+j]&=p[j]; }
    }
    if(corruptProgram && n>1) flashBytes[offset]^=1;
    return true;
}
static struct ApsFlash flash={NULL,readFlash,eraseFlash,programFlash};
static bool fill(void *ctx,uint8_t page,uint8_t *dst) { memcpy(dst,(uint8_t*)ctx+page*APS_SECTOR_SIZE,APS_SECTOR_SIZE);return true; }
static void data(uint8_t *p,size_t n,uint32_t seed)
{ for(size_t i=0;i<n;++i){ seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;p[i]=(uint8_t)seed; } }
static void verify(const uint8_t *want)
{
    uint8_t page[APS_SECTOR_SIZE];
    for(unsigned i=0;i<APS_PAGES;++i) { CHECK(ApsRead(&store,i*APS_SECTOR_SIZE,page,sizeof(page))==APS_OK);CHECK(!memcmp(page,want+i*APS_SECTOR_SIZE,sizeof(page))); }
    // All 900 opaque 80-byte records, including those crossing sector boundaries.
    uint8_t mon[80];
    for(unsigned slot=0;slot<900;++slot){ CHECK(ApsRead(&store,slot*80,mon,80)==APS_OK);CHECK(!memcmp(mon,want+slot*80,80)); }
}
static bool allEqual(const uint8_t *want)
{
    uint8_t page[APS_SECTOR_SIZE];
    for(unsigned i=0;i<APS_PAGES;++i)if(ApsRead(&store,i*APS_SECTOR_SIZE,page,sizeof(page))!=APS_OK||memcmp(page,want+i*APS_SECTOR_SIZE,sizeof(page)))return false;
    return true;
}
static void saveFile(const char *path)
{ FILE *f=fopen(path,"wb");CHECK(f);CHECK(fwrite(flashBytes,1,sizeof(flashBytes),f)==sizeof(flashBytes));CHECK(!fclose(f)); }
static void loadFile(const char *path)
{ FILE *f=fopen(path,"rb");CHECK(f);CHECK(fread(flashBytes,1,sizeof(flashBytes),f)==sizeof(flashBytes));CHECK(fgetc(f)==EOF);fclose(f); }
int main(int argc,char **argv)
{
    data(expected,sizeof(expected),0x12345678);
    if(argc==3 && !strcmp(argv[1],"write")) {
        memset(flashBytes,255,sizeof(flashBytes));CHECK(ApsFormat(&store,flash,fill,expected)==APS_OK);saveFile(argv[2]);return 0;
    }
    if(argc==3 && !strcmp(argv[1],"read")) { loadFile(argv[2]);CHECK(ApsMount(&store,flash)==APS_OK);verify(expected);return 0; }
    if(argc==3 && (!strcmp(argv[1],"update") || !strcmp(argv[1],"read-updated"))) {
        loadFile(argv[2]);CHECK(ApsMount(&store,flash)==APS_OK);
        const uint8_t changed[]={0,17,22};
        for(unsigned i=0;i<3;++i)data(expected+changed[i]*APS_SECTOR_SIZE,APS_SECTOR_SIZE,0x998800+i);
        if(!strcmp(argv[1],"update")) { CHECK(ApsCommit(&store,changed,3,fill,expected)==APS_OK);saveFile(argv[2]); }
        verify(expected);return 0;
    }
    CHECK(ApsCrc32("123456789",9)==0xcbf43926u);
    memset(flashBytes,255,sizeof(flashBytes));CHECK(ApsMount(&store,flash)==APS_EMPTY);
    CHECK(ApsFormat(&store,flash,fill,expected)==APS_OK);verify(expected);
    CHECK(ApsFormat(&store,flash,fill,expected)==APS_FOREIGN);CHECK(ApsMount(&store,flash)==APS_OK);
    memcpy(original,flashBytes,sizeof(original));memcpy(previous,expected,sizeof(previous));
    uint8_t pages[7]={0,2,4,8,12,18,22};
    for(unsigned i=0;i<7;++i)data(expected+pages[i]*APS_SECTOR_SIZE,APS_SECTOR_SIZE,0xabc000+i);
    // Oversized saves must fail BEFORE any erase/program operation.
    uint8_t eight[8]={0,1,2,3,4,5,6,7};
    CHECK(ApsCommit(&store,eight,8,fill,expected)==APS_TOO_MANY_CHANGES);CHECK(!memcmp(original,flashBytes,sizeof(original)));
    uint8_t dup[2]={1,1};CHECK(ApsCommit(&store,dup,2,fill,expected)==APS_ARGUMENT);
    CHECK(ApsRead(&store,APS_BYTES,NULL,1)==APS_ARGUMENT);
    CHECK(ApsRead(&store,0,NULL,0)==APS_OK);
    cut=1000000;action=0;CHECK(ApsCommit(&store,pages,7,fill,expected)==APS_OK);int actions=action;cut=-1;
    CHECK(ApsMount(&store,flash)==APS_OK);verify(expected);
    memcpy(flashBytes,original,sizeof(original));CHECK(ApsMount(&store,flash)==APS_OK);
    loseCommitAck=true;CHECK(ApsCommit(&store,pages,7,fill,expected)==APS_IO);loseCommitAck=false;
    CHECK(!store.mounted);CHECK(ApsMount(&store,flash)==APS_OK);verify(expected);
    // Corrupt newest root: recover complete older generation, not mixed pages.
    flashBytes[store.root*APS_SECTOR_SIZE]^=1;CHECK(ApsMount(&store,flash)==APS_OK);verify(previous);
    unsigned recovered=0;
    for(int fault=0;fault<=actions;++fault) {
        memcpy(flashBytes,original,sizeof(original));cut=-1;CHECK(ApsMount(&store,flash)==APS_OK);
        cut=fault;action=0;enum ApsResult result=ApsCommit(&store,pages,7,fill,expected);CHECK(result==APS_OK||result==APS_IO);
        cut=-1;CHECK(ApsMount(&store,flash)==APS_OK);CHECK(allEqual(previous)||allEqual(expected));++recovered;
    }
    // A failed readback must leave the active generation intact.
    memcpy(flashBytes,original,sizeof(original));CHECK(ApsMount(&store,flash)==APS_OK);
    corruptProgram=true;CHECK(ApsCommit(&store,pages,7,fill,expected)==APS_IO);corruptProgram=false;
    CHECK(ApsMount(&store,flash)==APS_OK);verify(previous);
    // After a later commit, old root invalidation/reclamation also has to be safe.
    CHECK(ApsCommit(&store,pages,7,fill,expected)==APS_OK);verify(expected);
    memcpy(original,flashBytes,sizeof(original));memcpy(previous,expected,sizeof(previous));
    for(unsigned i=0;i<7;++i)data(expected+pages[i]*APS_SECTOR_SIZE,APS_SECTOR_SIZE,0xdef000+i);
    for(int fault=0;fault<=actions;++fault) {
        memcpy(flashBytes,original,sizeof(original));cut=-1;CHECK(ApsMount(&store,flash)==APS_OK);
        cut=fault;action=0;enum ApsResult result=ApsCommit(&store,pages,7,fill,expected);CHECK(result==APS_OK||result==APS_IO);
        cut=-1;CHECK(ApsMount(&store,flash)==APS_OK);CHECK(allEqual(previous)||allEqual(expected));++recovered;
    }
    CHECK(ApsMount(&store,flash)==APS_OK);verify(expected);
    // Damage shared payload: neither root may be reported as a valid complete save.
    flashBytes[store.map[1]*APS_SECTOR_SIZE]^=1;CHECK(ApsMount(&store,flash)==APS_CORRUPT);
    // Valid but unknown version: detect it without altering the medium.
    memcpy(flashBytes,original,sizeof(original));CHECK(ApsMount(&store,flash)==APS_OK);
    uint8_t *root=flashBytes+store.root*APS_SECTOR_SIZE;root[8]=2;memset(root+24,0,4);
    uint32_t crc=ApsCrc32(root,32+APS_PAGES*8);for(unsigned i=0;i<4;++i)root[24+i]=(uint8_t)(crc>>(i*8));
    memcpy(original,flashBytes,sizeof(original));CHECK(ApsMount(&store,flash)==APS_FOREIGN);CHECK(!memcmp(original,flashBytes,sizeof(original)));
    printf("{\"slots\":900,\"record_bytes\":80,\"snapshot_capacity\":%u,\"flash_bytes\":%zu,\"host_workspace_bytes\":%zu,\"max_atomic_changed_pages\":%u,\"fault_cases\":%u,\"program_fault_stride\":%u,\"erase_fault_stride\":%u,\"status\":\"passed_bounded_transactions_only\"}\n",APS_BYTES,sizeof(flashBytes),sizeof(store),APS_MAX_CHANGED,recovered,programStride,eraseStride);
    return 0;
}
