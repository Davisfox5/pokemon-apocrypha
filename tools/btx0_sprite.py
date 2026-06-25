#!/usr/bin/env python3
"""btx0_sprite.py - extract / inject HGSS overworld sprite textures in BTX0 mmodel .bin files.

HGSS OW characters are BTX0 (Nitro 3D texture) containers. nitrogfx can't touch them.
This tool reads the single TEX0 block, decodes the fmt3 (4bpp / 16-color) 32x32 texture
frames to an editable indexed PNG (vertical strip), and re-injects an edited indexed PNG
back into the container WITHOUT changing any size/offset byte (it overwrites only the texel
and palette byte windows). That guarantees a byte-identical round-trip when nothing changed.

  btx0_sprite.py extract <in.bin> <out.png>            # also writes <out.png>.json sidecar
  btx0_sprite.py inject  <orig.bin> <edited.png> <out.bin>
  btx0_sprite.py verify  <in.bin>                      # extract->inject-unchanged, assert sha256 match

Edited PNG must stay mode 'P', exactly 32 wide x (32*Nframes) tall, <=16 palette colors,
and keep palette slot 0 as the transparent/background color.
"""
import sys, struct, json, hashlib
from PIL import Image

def u8(b, o):  return b[o]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def u32(b, o): return struct.unpack_from('<I', b, o)[0]

def parse(b):
    assert b[0:4] == b'BTX0', "not a BTX0 file"
    assert u16(b, 4) == 0xFEFF, "bad byte-order mark"
    TB = u32(b, 0x10)                       # TEX0 block base (offset[0])
    assert b[TB:TB+4] == b'TEX0', "no TEX0 block at offset[0]"
    texDataSize = u16(b, TB+0x0C) << 3
    texDictAbs  = TB + u16(b, TB+0x0E)
    texDataAbs  = TB + u32(b, TB+0x14)
    palDataSize = u32(b, TB+0x30) << 3
    palDictAbs  = TB + u32(b, TB+0x34)
    palDataAbs  = TB + u32(b, TB+0x38)

    def dictinfo(dictBase):
        numEntries = u8(b, dictBase+1)
        constBlk   = dictBase + u16(b, dictBase+6)
        elemSize   = u16(b, constBlk+0)
        nameOff    = u16(b, constBlk+2)
        dataElems  = constBlk + 4
        namesAbs   = constBlk + nameOff
        return numEntries, elemSize, dataElems, namesAbs

    texN, _, texData, texNames = dictinfo(texDictAbs)
    palN, _, palData, _        = dictinfo(palDictAbs)
    palBase = palDataAbs + ((u16(b, palData)) << 3)   # palOff (==0 for OW sprites)

    frames = []
    for i in range(texN):
        p = u32(b, texData + i*8)
        frames.append(dict(
            i=i, fmt=(p >> 26) & 7,
            W=8 << ((p >> 20) & 7), H=8 << ((p >> 23) & 7),
            texelOff=(p & 0xFFFF) << 3, color0=(p >> 29) & 1,
            name=b[texNames+i*16:texNames+i*16+16].split(b'\0')[0].decode('ascii', 'replace')))
    uniq = sorted({f['texelOff'] for f in frames})
    # sanity: OW sprites are fmt3, 32x32
    for f in frames:
        assert f['fmt'] == 3 and f['W'] == 32 and f['H'] == 32, \
            f"unexpected frame fmt/size {f}"  # branch here if a non-OW model is ever passed
    return dict(TB=TB, texDataAbs=texDataAbs, texDataSize=texDataSize,
                palDataAbs=palDataAbs, palDataSize=palDataSize, palBase=palBase,
                frames=frames, uniqOffs=uniq)

def _expand5(v):  return (v << 3) | (v >> 2)          # 5bit -> 8bit (replicates low bits)
def _quant5(v):   return int(round(v * 31 / 255))     # 8bit -> 5bit (round-trips with _expand5)

def read_palette(b, info):
    pal = []
    for k in range(16):
        c = u16(b, info['palBase'] + k*2)
        pal.append((_expand5(c & 0x1F), _expand5((c >> 5) & 0x1F), _expand5((c >> 10) & 0x1F)))
    return pal

def cmd_extract(binpath, pngpath):
    b = bytearray(open(binpath, 'rb').read())
    info = parse(b)
    pal = read_palette(b, info)
    uniq = info['uniqOffs']; N = len(uniq)
    img = Image.new('P', (32, 32*N))
    flat = []
    for rgb in pal: flat += list(rgb)
    img.putpalette(flat)
    px = img.load()
    for f, off in enumerate(uniq):
        base = info['texDataAbs'] + off
        for y in range(32):
            for xb in range(16):
                byte = b[base + y*16 + xb]
                px[xb*2,     f*32 + y] = byte & 0x0F
                px[xb*2 + 1, f*32 + y] = (byte >> 4) & 0x0F
    img.info['transparency'] = 0
    img.save(pngpath)
    json.dump(dict(src=binpath, nframes=N, texelOffs=uniq,
                   palu16=[u16(b, info['palBase']+k*2) for k in range(16)]),
              open(pngpath + '.json', 'w'), indent=1)
    print(f"extracted {N} frames -> {pngpath}  (32x{32*N}, 16-color indexed)")
    return N

def cmd_inject(origpath, pngpath, outpath):
    b = bytearray(open(origpath, 'rb').read())
    info = parse(b)
    uniq = info['uniqOffs']; N = len(uniq)
    img = Image.open(pngpath)
    assert img.mode == 'P', "edited PNG must be indexed (mode P)"
    assert img.size == (32, 32*N), f"PNG must be 32x{32*N}, got {img.size[0]}x{img.size[1]}"
    px = img.load()
    pal = img.getpalette() or []
    pal += [0] * (48 - len(pal))                       # pad to 16 RGB triples
    # palette -> RGB555 (16 slots), in place, same 32 bytes
    for slot in range(16):
        r, g, bl = pal[slot*3], pal[slot*3+1], pal[slot*3+2]
        c = (_quant5(r) & 0x1F) | ((_quant5(g) & 0x1F) << 5) | ((_quant5(bl) & 0x1F) << 10)
        struct.pack_into('<H', b, info['palBase'] + slot*2, c)
    # texels -> 4bpp, in place, same 512 bytes per frame
    for f, off in enumerate(uniq):
        base = info['texDataAbs'] + off
        for y in range(32):
            for xb in range(16):
                lo = px[xb*2,     f*32 + y] & 0x0F
                hi = px[xb*2 + 1, f*32 + y] & 0x0F
                b[base + y*16 + xb] = lo | (hi << 4)
    out = bytes(b)
    orig = open(origpath, 'rb').read()
    assert len(out) == len(orig), "size changed (must not)"
    # everything outside the texel + palette windows must be byte-identical
    tlo, thi = info['texDataAbs'], info['texDataAbs'] + info['texDataSize']
    plo, phi = info['palDataAbs'], info['palDataAbs'] + info['palDataSize']
    for i in range(len(out)):
        if (tlo <= i < thi) or (plo <= i < phi):  continue
        assert out[i] == orig[i], f"byte changed outside texel/palette window at 0x{i:X}"
    open(outpath, 'wb').write(out)
    print(f"injected {N} frames -> {outpath}")

def cmd_verify(binpath):
    import tempfile, os
    d = tempfile.mkdtemp()
    png = os.path.join(d, 'rt.png'); out = os.path.join(d, 'rt.bin')
    cmd_extract(binpath, png)
    cmd_inject(binpath, png, out)
    a = hashlib.sha256(open(binpath, 'rb').read()).hexdigest()
    c = hashlib.sha256(open(out, 'rb').read()).hexdigest()
    ok = (a == c)
    print(f"  orig sha256: {a}")
    print(f"  round  sha256: {c}")
    print("ROUND-TRIP", "OK (byte-identical)" if ok else "MISMATCH")
    return ok

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'extract':  cmd_extract(sys.argv[2], sys.argv[3])
    elif cmd == 'inject': cmd_inject(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'verify': sys.exit(0 if cmd_verify(sys.argv[2]) else 1)
    else: print(__doc__); sys.exit(2)
