#!/usr/bin/env python3
"""donorlib.py - donor-texture extraction from Gen-4 NSBTX texture sets.

Reads BTX0 texture-set files (HGSS area texsets from NARC a/0/4/4, Platinum
field texture_sets/*.nsbtx), decodes textures to RGBA, and renders labeled
contact sheets for donor-art browsing.

API:
  read_btx(data)        -> (textures, palettes)
                           textures: {name: {name,w,h,fmt,c0t,texels,w1}}
                           palettes: {name: bytes (BGR555)}
  hgss_texset(idx)      -> (textures, palettes)   NARC a/0/4/4 member idx
  plat_texset(idx)      -> (textures, palettes)   map_texture_set_%03d.nsbtx
  find_palette(name, palettes, source=None) -> palette name or None
  decode_rgba(tex, palettes, source=None)   -> (PIL.Image RGBA, pal_name)
  contact_sheet(texset_label, textures, palettes, out_png, source=None)

BTX0 layout (verified against nsbmd.build_btx_named and vanilla files):
  u32@0x10 of container = TEX0 offset. Within TEX0:
    u16@0x0E = texdict ofs, u32@0x14 = texdata ofs,
    u32@0x34 = paldict ofs, u32@0x38 = paldata ofs (all TEX0-relative).
  NNS dict: u8 count @+1, u16 size @+2, u16 ofsEntry @+6; at dict+ofsEntry:
    u16 unit, u16 ofs_name; entry k data at dict+ofsEntry+4+k*unit;
    16-byte names at dict+ofsEntry+ofs_name+k*16.
  Texture entry (unit 8) = w0,w1 u32s: w0 bits 0-15 texel ofs in 8-byte
    units, width 8<<((w0>>20)&7), height 8<<((w0>>23)&7), fmt (w0>>26)&7,
    color-0-transparent bit 29. Palette entry (unit 4) = u16 ofs in 8-byte
    units into paldata + u16 flag.
  A palette's byte length is not stored; it runs to the next distinct
  palette offset (last one to end of paldata).

Palette association: the authoritative texture->palette binding lives in map
model materials (NSBMD MAT0 texToMatList/palToMatList), not in the texture
set. Empirically (scanned every material of every Platinum map_data_*.bin
model and every HGSS a/0/6/5 land-data model) the binding is:
  1. palette named exactly like the texture, else
  2. texture name + "_pl" (truncated to 16 chars), else
  3. an irregular name (e.g. grass01gs->grass01, sea_on->sea_f02_pl,
     ngrass->grass, nbridge->dun_bridge) -- these are baked into
     PAL_OVERRIDES below from the map-model ground truth.
"""
import os
import struct
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from narc import narc_read  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(_HERE))
HGSS_TEXSET_NARC = os.path.join(_REPO, "disasm/pokeheartgold/files/a/0/4/4")
PLAT_TEXSET_DIR = os.path.join(
    _REPO, "disasm/pokeplatinum/res/field/maps/texture_sets")

FMT_NAMES = {1: "a3i5", 2: "pltt4", 3: "pltt16", 4: "pltt256",
             5: "comp4x4", 6: "a5i3", 7: "direct"}

# texel bytes for a w*h texture, by fmt (fmt5's extra index block excluded)
_FMT_SIZE = {1: lambda w, h: w * h,
             2: lambda w, h: w * h // 4,
             3: lambda w, h: w * h // 2,
             4: lambda w, h: w * h,
             5: lambda w, h: w * h // 4,
             6: lambda w, h: w * h,
             7: lambda w, h: w * h * 2}

# Irregular texture->palette bindings harvested from map-model materials
# (majority binding across all Platinum map_data models and HGSS a/0/6/5
# land-data models). Only consulted when rules 1-2 miss.
PAL_OVERRIDES = {
    "hgss": {
        "allpeak": "apeak",
        "allpeak_pgs": "apeak",
        "allpeakgs": "apeak",
        "cliff01gs": "cliff01",
        "conttree_b": "conttree",
        "conttree_t": "conttree",
        "criffp": "criff",
        "criffp2": "criff2",
        "criffp3": "criff3",
        "criffp4": "criff4",
        "criffp5": "criff5",
        "dsea_on": "sea_f02_pl",
        "dsea_un": "sea_un",
        "enccliff": "enccriff",
        "grass01gs": "grass01",
        "nbridge": "dun_bridge",
        "nectgr": "nectgrass",
        "ngrass": "grass",
        "nsand": "sandset",
        "sea_on": "sea_f02_pl",
        "tree01gs": "tree01",
        "tree04_2": "tree01",
        "wcliff": "criff",
    },
    "plat": {
        "allpeak": "apeak",
        "conttree_b": "conttree",
        "conttree_t": "conttree",
        "criffp": "criff",
        "criffp2": "criff2",
        "criffp3": "criff3",
        "criffp4": "criff4",
        "criffp5": "criff5",
        "dun_allpeak": "apeak",
        "dun_hashi": "bridge",
        "dun_shadow": "shadowchip",
        "dun_srock": "searock",
        "dun_sside": "seaside3",
        "enccliff": "enccriff",
        "nbridge": "dun_bridge",
        "nectgr": "nectgrass",
        "ngrass": "grass",
        "ngrass02": "grass02",
        "nsand": "sandset",
        "tree04_2": "tree01",
        "wcliff": "criff",
    },
}


def _read_dict(b, off, unit):
    """NNS G3D resdict -> (names, raw entry bytes)."""
    count = b[off + 1]
    ofs_entry = struct.unpack_from("<H", b, off + 6)[0]
    eh = off + ofs_entry
    eunit, ofs_name = struct.unpack_from("<HH", b, eh)
    assert eunit == unit, f"dict unit {eunit} != {unit}"
    names, entries = [], []
    for k in range(count):
        d = eh + 4 + k * eunit
        entries.append(b[d:d + eunit])
        raw = b[eh + ofs_name + k * 16:eh + ofs_name + k * 16 + 16]
        names.append(raw.rstrip(b"\0").decode("ascii", "replace"))
    return names, entries


def read_btx(data):
    """Parse a BTX0 file -> (textures, palettes).

    textures: {name: {"name", "w", "h", "fmt", "c0t", "texels", "w1"}}
      (fmt5 comp4x4 textures get their main 4x4-block data only)
    palettes: {name: bytes}  raw BGR555 palette data
    """
    assert data[:4] == b"BTX0", f"not a BTX0 ({data[:4]!r})"
    tex0 = struct.unpack_from("<I", data, 0x10)[0]
    assert data[tex0:tex0 + 4] == b"TEX0", "TEX0 block not found"
    tex0_size = struct.unpack_from("<I", data, tex0 + 4)[0]
    texdict = tex0 + struct.unpack_from("<H", data, tex0 + 0x0E)[0]
    texdata = tex0 + struct.unpack_from("<I", data, tex0 + 0x14)[0]
    paldict = tex0 + struct.unpack_from("<I", data, tex0 + 0x34)[0]
    paldata = tex0 + struct.unpack_from("<I", data, tex0 + 0x38)[0]
    paldata_end = tex0 + tex0_size

    textures = {}
    tnames, tentries = _read_dict(data, texdict, 8)
    for nm, e in zip(tnames, tentries):
        w0, w1 = struct.unpack("<2I", e)
        w = 8 << ((w0 >> 20) & 7)
        h = 8 << ((w0 >> 23) & 7)
        fmt = (w0 >> 26) & 7
        ofs = (w0 & 0xFFFF) * 8
        size = _FMT_SIZE[fmt](w, h) if fmt in _FMT_SIZE else 0
        textures[nm] = {
            "name": nm, "w": w, "h": h, "fmt": fmt,
            "c0t": (w0 >> 29) & 1,
            "texels": bytes(data[texdata + ofs:texdata + ofs + size]),
            "w1": w1,
        }

    pnames, pentries = _read_dict(data, paldict, 4)
    offsets = [struct.unpack("<HH", e)[0] * 8 for e in pentries]
    # a palette runs to the next DISTINCT offset (offsets can be shared),
    # the last one to the end of paldata
    distinct = sorted(set(offsets))
    pal_len = len(data) - paldata if paldata_end > len(data) else paldata_end - paldata
    palettes = {}
    for nm, o in zip(pnames, offsets):
        i = distinct.index(o)
        nxt = distinct[i + 1] if i + 1 < len(distinct) else pal_len
        palettes[nm] = bytes(data[paldata + o:paldata + nxt])
    return textures, palettes


_texset_cache = {}


def hgss_texset(idx):
    """HGSS area texture set: member idx of NARC a/0/4/4 (do not mutate)."""
    key = ("hgss", idx)
    if key not in _texset_cache:
        members = narc_read(HGSS_TEXSET_NARC)
        _texset_cache[key] = read_btx(members[idx])
    return _texset_cache[key]


def plat_texset(idx):
    """Platinum field texture set map_texture_set_%03d.nsbtx (do not mutate)."""
    key = ("plat", idx)
    if key not in _texset_cache:
        path = os.path.join(PLAT_TEXSET_DIR, f"map_texture_set_{idx:03d}.nsbtx")
        with open(path, "rb") as f:
            _texset_cache[key] = read_btx(f.read())
    return _texset_cache[key]


def find_palette(name, palettes, source=None):
    """Resolve a texture name to its palette name, or None.

    Rule (empirical, from map-model material bindings): exact name, then
    name+"_pl" truncated to 16 chars, then PAL_OVERRIDES[source], then a
    last-ditch strip of a trailing 'gs' variant suffix. source is "hgss",
    "plat", or None (tries both override tables)."""
    if name in palettes:
        return name
    pl = (name + "_pl")[:16]
    if pl in palettes:
        return pl
    tables = ([PAL_OVERRIDES[source]] if source in PAL_OVERRIDES
              else list(PAL_OVERRIDES.values()))
    for table in tables:
        ov = table.get(name)
        if ov and ov in palettes:
            return ov
    if name.endswith("gs"):
        return find_palette(name[:-2].rstrip("_"), palettes, source)
    return None


def _pal_rgb(pal):
    """BGR555 bytes -> list of (r, g, b) 888 tuples."""
    out = []
    for i in range(0, len(pal) - 1, 2):
        v = pal[i] | (pal[i + 1] << 8)
        r = (v & 31) << 3
        g = ((v >> 5) & 31) << 3
        b = ((v >> 10) & 31) << 3
        out.append((r | (r >> 5), g | (g >> 5), b | (b >> 5)))
    return out


def decode_rgba(tex, palettes, source=None):
    """Decode one texture (fmt 1/2/3/4/6) -> (PIL RGBA image, pal_name).

    Raises KeyError if no palette associates, NotImplementedError for
    fmt 5 (comp4x4) / fmt 7 (direct) textures."""
    from PIL import Image
    w, h, fmt = tex["w"], tex["h"], tex["fmt"]
    if fmt not in (1, 2, 3, 4, 6):
        raise NotImplementedError(
            f"{tex['name']}: fmt {fmt} ({FMT_NAMES.get(fmt)}) not supported")
    pal_name = find_palette(tex["name"], palettes, source)
    if pal_name is None:
        raise KeyError(f"{tex['name']}: no palette found")
    rgb = _pal_rgb(palettes[pal_name])

    def color(idx):
        return rgb[idx] if idx < len(rgb) else (0, 0, 0)

    t = tex["texels"]
    px = bytearray(w * h * 4)
    n = w * h
    c0t = tex["c0t"]
    if fmt == 2:      # pltt4: 2bpp, LSB-first
        for i in range(n):
            v = (t[i >> 2] >> ((i & 3) * 2)) & 3
            r, g, b = color(v)
            a = 0 if (c0t and v == 0) else 255
            px[i * 4:i * 4 + 4] = bytes((r, g, b, a))
    elif fmt == 3:    # pltt16: 4bpp, low nibble first
        for i in range(n):
            v = (t[i >> 1] >> ((i & 1) * 4)) & 15
            r, g, b = color(v)
            a = 0 if (c0t and v == 0) else 255
            px[i * 4:i * 4 + 4] = bytes((r, g, b, a))
    elif fmt == 4:    # pltt256: 8bpp
        for i in range(n):
            v = t[i]
            r, g, b = color(v)
            a = 0 if (c0t and v == 0) else 255
            px[i * 4:i * 4 + 4] = bytes((r, g, b, a))
    elif fmt == 1:    # a3i5: low 5 bits index, high 3 alpha
        for i in range(n):
            v = t[i]
            r, g, b = color(v & 31)
            px[i * 4:i * 4 + 4] = bytes((r, g, b, (v >> 5) * 255 // 7))
    elif fmt == 6:    # a5i3: low 3 bits index, high 5 alpha
        for i in range(n):
            v = t[i]
            r, g, b = color(v & 7)
            px[i * 4:i * 4 + 4] = bytes((r, g, b, (v >> 3) * 255 // 31))
    img = Image.frombytes("RGBA", (w, h), bytes(px))
    return img, pal_name


def contact_sheet(texset_label, textures, palettes, out_png, source=None):
    """Render every texture in the set (sorted by name, 2x zoom, on a
    checkerboard) with a name / WxH / fmt / palette label. Returns a list of
    (texname, error string) for textures that failed to decode."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.load_default()
    ZOOM, PAD, SHEET_W = 2, 8, 1100
    LINE_H, HDR_H = 11, 26
    failures = []
    items = []  # (name, img or None, label lines)
    for nm in sorted(textures):
        tex = textures[nm]
        lab2 = f"{tex['w']}x{tex['h']} {FMT_NAMES.get(tex['fmt'], tex['fmt'])}"
        if tex["fmt"] in (2, 3, 4) and tex["c0t"]:
            lab2 += " c0t"
        try:
            img, pal_name = decode_rgba(tex, palettes, source)
            img = img.resize((tex["w"] * ZOOM, tex["h"] * ZOOM), Image.NEAREST)
            lab3 = f"pal {pal_name}"
        except Exception as e:
            failures.append((nm, str(e)))
            img, lab3 = None, "DECODE FAILED"
        items.append((nm, img, [nm, lab2, lab3], tex))

    def cell_w(it):
        nm, img, labels, tex = it
        iw = img.width if img else tex["w"] * ZOOM
        tw = max(int(font.getlength(s)) for s in labels)
        return max(iw, tw) + PAD

    def cell_h(it):
        nm, img, labels, tex = it
        ih = img.height if img else tex["h"] * ZOOM
        return ih + len(labels) * LINE_H + PAD

    # flow layout
    rows, row, x = [], [], PAD
    for it in items:
        w = cell_w(it)
        if row and x + w > SHEET_W - PAD:
            rows.append(row)
            row, x = [], PAD
        row.append(it)
        x += w
    if row:
        rows.append(row)
    sheet_h = HDR_H + sum(max(cell_h(i) for i in r) for r in rows) + PAD
    sheet = Image.new("RGB", (SHEET_W, sheet_h), (28, 28, 32))
    draw = ImageDraw.Draw(sheet)
    draw.text((PAD, 7), f"{texset_label}  ({len(items)} textures)",
              fill=(255, 220, 120), font=font)
    y = HDR_H
    for r in rows:
        rh = max(cell_h(i) for i in r)
        x = PAD
        for it in r:
            nm, img, labels, tex = it
            if img is not None:
                # checkerboard under the texture only
                for cy in range(0, img.height, 8):
                    for cx in range(0, img.width, 8):
                        c = (120, 120, 120) if ((cx ^ cy) >> 3) & 1 else (168, 168, 168)
                        draw.rectangle([x + cx, y + cy,
                                        x + min(cx + 8, img.width) - 1,
                                        y + min(cy + 8, img.height) - 1], fill=c)
                sheet.paste(img, (x, y), img)
                ty = y + img.height + 1
            else:
                draw.rectangle([x, y, x + tex["w"] * ZOOM - 1,
                                y + tex["h"] * ZOOM - 1], outline=(200, 60, 60))
                ty = y + tex["h"] * ZOOM + 1
            for li, s in enumerate(labels):
                col = (235, 235, 235) if li == 0 else (150, 170, 200)
                if s == "DECODE FAILED":
                    col = (255, 80, 80)
                draw.text((x, ty + li * LINE_H), s, fill=col, font=font)
            x += cell_w(it)
        y += rh
    sheet.save(out_png)
    return failures


# ---------------------------------------------------------------------------
def _verify_roundtrip():
    """Extraction-fidelity checks on HGSS texset 2, plus a writer round-trip
    of its fmt3 textures through nsbmd.build_btx_named."""
    import nsbmd
    textures, palettes = hgss_texset(2)
    bad = []
    for nm, tex in textures.items():
        expect = _FMT_SIZE[tex["fmt"]](tex["w"], tex["h"])
        if len(tex["texels"]) != expect:
            bad.append(f"{nm}: texel len {len(tex['texels'])} != {expect}")
            continue
        try:
            decode_rgba(tex, palettes, "hgss")
        except Exception as e:
            bad.append(f"{nm}: {e}")
    print(f"hgss texset 2: {len(textures)} textures, {len(palettes)} palettes")
    if bad:
        print("FAILURES:")
        for b in bad:
            print("  " + b)
    else:
        print("all textures: texel sizes OK, palette found, decode OK")

    # writer round-trip: fmt3 subset through build_btx_named -> read_btx
    subset = [(nm, t["w"], t["h"], t["texels"], 3, not t["c0t"])
              for nm, t in sorted(textures.items()) if t["fmt"] == 3]
    pals, seen = [], set()
    for nm, t in sorted(textures.items()):
        if t["fmt"] != 3:
            continue
        pn = find_palette(nm, palettes, "hgss")
        if pn not in seen:
            seen.add(pn)
            pals.append((pn, palettes[pn][:32].ljust(32, b"\0")))
    blob = nsbmd.build_btx_named(subset, pals)
    rt_tex, rt_pal = read_btx(blob)
    mism = []
    for nm, w, h, texels, fmt, opaque0 in subset:
        r = rt_tex[nm]
        if (r["w"], r["h"], r["fmt"], r["texels"]) != (w, h, fmt, texels):
            mism.append(nm)
        if r["c0t"] == opaque0:  # c0t must be inverse of opaque0
            mism.append(nm + " (c0t)")
    for pn, pdata in pals:
        if rt_pal[pn][:32] != pdata:
            mism.append(pn + " (pal)")
    if mism:
        print("round-trip MISMATCHES:", mism)
    else:
        print(f"build_btx_named round-trip OK "
              f"({len(subset)} fmt3 textures, {len(pals)} palettes)")
    return not bad and not mism


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "donor_sheets"
    os.makedirs(outdir, exist_ok=True)
    ok = _verify_roundtrip()
    sheets = ([("hgss", i) for i in (2, 5, 6, 7, 8, 9, 11, 18)]
              + [("plat", i) for i in (6, 13, 18, 19)])
    any_fail = False
    for src, i in sheets:
        textures, palettes = (hgss_texset if src == "hgss" else plat_texset)(i)
        out = os.path.join(outdir, f"{src}_{i:02d}.png")
        fails = contact_sheet(f"{src} texset {i}", textures, palettes, out, src)
        print(f"{out}: {len(textures)} textures"
              + (f", FAILED: {fails}" if fails else ""))
        any_fail |= bool(fails)
    sys.exit(0 if ok and not any_fail else 1)


if __name__ == "__main__":
    main()
