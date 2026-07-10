#!/usr/bin/env python3
"""pathfind.py <matrix:SINNOH|EVERYWHERE> <sx> <sz> <tx> <tz> - BFS a walkable
path over HGSS land-data permission planes; prints play.py button tokens."""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from narc import narc_read
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'mapeditor'))
from mapdata import MapMatrix
from collections import deque

HG = os.path.join(ROOT, 'disasm', 'pokeheartgold')
land = narc_read(os.path.join(HG, 'files/a/0/6/5'))

def load_matrix(name):
    d = os.path.join(HG, 'files/fielddata/mapmatrix/map_matrix')
    for f in os.listdir(d):
        if name in f:
            return MapMatrix.load(os.path.join(d, f))
    raise SystemExit('no matrix ' + name)

def perms(mem):
    magic, n = struct.unpack_from('<HH', mem, 16)
    return mem[20+n:20+n+0x800]

def walkable(mm, cache, x, z):
    cx, cz = x // 32, z // 32
    if not (0 <= cx < mm.width and 0 <= cz < mm.height):
        return False
    mid = mm.cell(cx, cz)
    if mid == 0xFFFF:
        return False
    if mid not in cache:
        cache[mid] = perms(land[mid])
    p = cache[mid]
    i = ((z % 32) * 32 + (x % 32)) * 2
    return not (p[i+1] & 0x80) and p[i] not in {0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x19, 0x2A, 0x50, 0x51, 0x52, 0x53, 0x73, 0x78, 0x7C}

def main():
    name, sx, sz, tx, tz = sys.argv[1], *map(int, sys.argv[2:6])
    mm = load_matrix(name)
    cache = {}
    prev = {(sx, sz): None}
    q = deque([(sx, sz)])
    DIRS = [(0,-1,'UP'), (0,1,'DOWN'), (-1,0,'LEFT'), (1,0,'RIGHT')]
    goal = None
    while q:
        x, z = q.popleft()
        if (x, z) == (tx, tz):
            goal = (x, z); break
        for dx, dz, b in DIRS:
            n = (x+dx, z+dz)
            if n not in prev and walkable(mm, cache, *n):
                prev[n] = (x, z, b); q.append(n)
    if not goal:
        sys.exit('no path')
    steps = []
    cur = goal
    while prev[cur] is not None:
        px, pz, b = prev[cur]
        steps.append(b); cur = (px, pz)
    steps.reverse()
    # compress into play.py tokens
    out, i = [], 0
    while i < len(steps):
        j = i
        while j < len(steps) and steps[j] == steps[i]:
            j += 1
        out.append(f"{steps[i]}*{j-i}" if j-i > 1 else steps[i])
        i = j
    print(f"# {len(steps)} steps")
    print(' '.join(out))

if __name__ == '__main__':
    main()
