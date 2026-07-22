#!/usr/bin/env python3
"""Batch-extract HGSS overworld BTX0 mmodel sprites to RGBA PNG strips."""
import re, struct
from pathlib import Path
from PIL import Image

ROOT = Path("/Users/davisfox/Documents/GitHub/the-omni-hack")
MM = ROOT / "disasm/pokeheartgold/files/data/mmodel/mmodel"
HDR = ROOT / "disasm/pokeheartgold/include/constants/mmodel.h"
OUT = ROOT / "artwork-library/heartgold-johto/overworld-sprites"
OUT.mkdir(parents=True, exist_ok=True)

names = {}
for m in re.finditer(r"#define MMODEL_(\w+)\s+(\d+)", HDR.read_text()):
    n = int(m.group(2))
    if n not in names:
        names[n] = m.group(1).lower()

def u8(b, o):  return b[o]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def exp5(v):   return (v << 3) | (v >> 2)

def extract(b):
    if b[0:4] == b'BTX0' and u16(b, 4) == 0xFEFF:
        TB = u32(b, 0x10)
    elif b[0:4] == b'BMD0' and u16(b, 4) == 0xFEFF:
        TB = None
        for i in range(u16(b, 0x0E)):
            off = u32(b, 0x10 + i*4)
            if b[off:off+4] == b'TEX0':
                TB = off
                break
        if TB is None:
            raise ValueError("BMD0 without TEX0")
    else:
        raise ValueError("not BTX0/BMD0")
    if b[TB:TB+4] != b'TEX0':
        raise ValueError("no TEX0")
    texDictAbs = TB + u16(b, TB+0x0E)
    texDataAbs = TB + u32(b, TB+0x14)
    palDictAbs = TB + u32(b, TB+0x34)
    palDataAbs = TB + u32(b, TB+0x38)

    def dictinfo(dictBase):
        numEntries = u8(b, dictBase+1)
        constBlk = dictBase + u16(b, dictBase+6)
        nameOff = u16(b, constBlk+2)
        return numEntries, constBlk + 4, constBlk + nameOff

    texN, texData, _ = dictinfo(texDictAbs)
    palN, palData, _ = dictinfo(palDictAbs)
    palBase = palDataAbs + (u16(b, palData) << 3)

    frames = []
    for i in range(texN):
        p = u32(b, texData + i*8)
        frames.append(dict(fmt=(p >> 26) & 7,
                           W=8 << ((p >> 20) & 7), H=8 << ((p >> 23) & 7),
                           off=(p & 0xFFFF) << 3, c0=(p >> 29) & 1))
    # dedupe by texel offset, keep order
    seen, uniq = set(), []
    for f in frames:
        if f['off'] not in seen:
            seen.add(f['off'])
            uniq.append(f)

    pal = []
    for k in range(256):
        try:
            c = u16(b, palBase + k*2)
        except struct.error:
            break
        pal.append((exp5(c & 0x1F), exp5((c >> 5) & 0x1F), exp5((c >> 10) & 0x1F)))

    W = max(f['W'] for f in uniq)
    H = sum(f['H'] for f in uniq)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = img.load()
    y0 = 0
    for f in uniq:
        base = texDataAbs + f['off']
        if f['fmt'] == 3:      # 4bpp 16-color
            for y in range(f['H']):
                for xb in range(f['W'] // 2):
                    byte = b[base + y*(f['W']//2) + xb]
                    for k, ci in ((0, byte & 0xF), (1, byte >> 4)):
                        if ci or not True:
                            pass
                        a = 0 if ci == 0 else 255
                        r, g, bl = pal[ci] if ci < len(pal) else (255, 0, 255)
                        px[xb*2 + k, y0 + y] = (r, g, bl, a)
        elif f['fmt'] == 4:    # 8bpp 256-color
            for y in range(f['H']):
                for x in range(f['W']):
                    ci = b[base + y*f['W'] + x]
                    a = 0 if ci == 0 else 255
                    r, g, bl = pal[ci] if ci < len(pal) else (255, 0, 255)
                    px[x, y0 + y] = (r, g, bl, a)
        else:
            raise ValueError(f"unsupported fmt {f['fmt']}")
        y0 += f['H']
    return img, len(uniq)

ok = fail = 0
fails = []
for f in sorted(MM.glob("mmodel_*.bin")):
    n = int(f.stem.split('_')[1])
    label = f"{n:04d}_{names.get(n, 'unnamed')}"
    try:
        img, nframes = extract(f.read_bytes())
        img.save(OUT / f"{label}.png")
        ok += 1
    except Exception as e:
        fail += 1
        fails.append(f"{label}: {e}")

print(f"ok={ok} fail={fail}")
for line in fails[:30]:
    print("  FAIL", line)
