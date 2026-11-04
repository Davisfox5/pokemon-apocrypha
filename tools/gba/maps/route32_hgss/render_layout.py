"""Render a pokeemerald-expansion layout straight from a git ref.

usage: render_map.py REPO REF LAYOUT_NAME OUT.png
"""
import io
import json
import re
import subprocess
import sys

from PIL import Image

NUM_PRI_TILES = 512
NUM_PRI_METATILES = 512
NUM_PRI_PALS = 6


def show(repo, ref, path, binary=True):
    out = subprocess.run(["git", "-C", repo, "show", f"{ref}:{path}"],
                         capture_output=True, check=True).stdout
    return out if binary else out.decode()


def read_pal(text):
    lines = text.splitlines()
    return [tuple(int(v) for v in l.split()[:3]) for l in lines[3:3 + 16]]


class Tilesets:
    def __init__(self, repo, ref):
        self.repo, self.ref = repo, ref
        self.headers = show(repo, ref, "src/data/tilesets/headers.h", False)
        self.graphics = show(repo, ref, "src/data/tilesets/graphics.h", False)
        self.metatiles = show(repo, ref, "src/data/tilesets/metatiles.h", False)

    def _block(self, name):
        m = re.search(r"const struct Tileset " + re.escape(name) + r"\s*=\s*\{(.*?)\};",
                      self.headers, re.S)
        return m.group(1)

    def load(self, name):
        blk = self._block(name)
        tiles_sym = re.search(r"\.tiles\s*=\s*(\w+)", blk).group(1)
        pal_sym = re.search(r"\.palettes\s*=\s*(\w+)", blk).group(1)
        mt_sym = re.search(r"\.metatiles\s*=\s*(\w+)", blk).group(1)
        tiles_path = re.search(re.escape(tiles_sym) + r"\[\]\s*=\s*INC\w+\(\"([^\"]+)\"",
                               self.graphics).group(1)
        tiles_path = re.sub(r"\.4bpp(\.lz|\.smol|\.fastSmol)?$", ".png", tiles_path)
        pal_section = re.search(re.escape(pal_sym) + r"\[\]\[16\]\s*=\s*\{(.*?)\};",
                                self.graphics, re.S).group(1)
        pal_paths = [re.sub(r"\.gbapal$", ".pal", p)
                     for p in re.findall(r"\"([^\"]+\.(?:gbapal|pal))\"", pal_section)]
        mt_path = re.search(re.escape(mt_sym) + r"\[\]\s*=\s*INC\w+\(\"([^\"]+)\"",
                            self.metatiles).group(1)
        img = Image.open(io.BytesIO(show(self.repo, self.ref, tiles_path)))
        if img.mode != "P":
            img = img.convert("P")
        w = img.width // 8
        data = img.tobytes()
        tiles = []
        for t in range((img.width // 8) * (img.height // 8)):
            tx, ty = (t % w) * 8, (t // w) * 8
            tiles.append([[data[(ty + y) * img.width + tx + x] & 15 for x in range(8)]
                          for y in range(8)])
        pals = []
        for p in pal_paths:
            try:
                pals.append(read_pal(show(self.repo, self.ref, p, False)))
            except subprocess.CalledProcessError:
                pals.append([(255, 0, 255)] * 16)
        mt = show(self.repo, self.ref, mt_path)
        metas = [[int.from_bytes(mt[i + j * 2:i + j * 2 + 2], "little") for j in range(8)]
                 for i in range(0, len(mt), 16)]
        return tiles, pals, metas


def render(repo, ref, layout_name, out):
    layouts = json.loads(show(repo, ref, "data/layouts/layouts.json", False))["layouts"]
    lay = next(l for l in layouts if l.get("name") == layout_name or l.get("id") == layout_name)
    ts = Tilesets(repo, ref)
    p_tiles, p_pals, p_metas = ts.load(lay["primary_tileset"])
    s_tiles, s_pals, s_metas = ts.load(lay["secondary_tileset"])
    pals = (p_pals[:NUM_PRI_PALS] + s_pals[NUM_PRI_PALS:] + [[(0, 0, 0)] * 16] * 16)[:16]
    w, h = lay["width"], lay["height"]
    blocks = show(repo, ref, lay["blockdata_filepath"])
    img = Image.new("RGB", (w * 16, h * 16))
    px = img.load()
    cache = {}

    def tile(tid):
        if tid < NUM_PRI_TILES:
            return p_tiles[tid] if tid < len(p_tiles) else None
        i = tid - NUM_PRI_TILES
        return s_tiles[i] if i < len(s_tiles) else None

    def meta(mid):
        if mid < NUM_PRI_METATILES:
            return p_metas[mid] if mid < len(p_metas) else None
        i = mid - NUM_PRI_METATILES
        return s_metas[i] if i < len(s_metas) else None

    def draw_meta(mid):
        if mid in cache:
            return cache[mid]
        m = meta(mid)
        cell = [[pals[0][0]] * 16 for _ in range(16)]
        if m:
            for layer in (0, 1):
                for q in range(4):
                    e = m[layer * 4 + q]
                    t = tile(e & 0x3FF)
                    if t is None:
                        continue
                    hf, vf, pal = e & 0x400, e & 0x800, pals[(e >> 12) & 15]
                    ox, oy = (q % 2) * 8, (q // 2) * 8
                    for y in range(8):
                        for x in range(8):
                            c = t[7 - y if vf else y][7 - x if hf else x]
                            if c == 0 and layer:
                                continue
                            cell[oy + y][ox + x] = pal[c]
        cache[mid] = cell
        return cell

    for i in range(w * h):
        v = int.from_bytes(blocks[i * 2:i * 2 + 2], "little") & 0x3FF
        cell = draw_meta(v)
        bx, by = (i % w) * 16, (i // w) * 16
        for y in range(16):
            row = cell[y]
            for x in range(16):
                px[bx + x, by + y] = row[x]
    img.save(out)
    print(out, img.size, lay["primary_tileset"], lay["secondary_tileset"])


if __name__ == "__main__":
    render(*sys.argv[1:5])
