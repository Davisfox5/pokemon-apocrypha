"""Canalave's two native layers and per-cell traversal, from the reference (reference.py).

Bottom layer: Platinum's terrain with its contact shadows; every sea pixel is Emerald's animated water.
Top layer: Platinum's buildings and props (the renderer's foreground), and the canal wall's pixels in cells
that are part water, so the water under them stays animated.

Traversal is Platinum's own permission grid (collision bit and terrain type per cell); the margin is blocked.
"""
from __future__ import annotations
import numpy as np
import cn_reference as Rf
from cn_reference import W, H, MARGIN, PX

# Platinum terrain types seen in Canalave
T_WATER, T_BRIDGE, T_DOOR, T_EAST_WARP = 0x15, 0x71, 0x69, 0x6C
# Emerald
MB_NORMAL, MB_OCEAN_WATER, MB_NON_ANIMATED_DOOR, MB_ANIMATED_DOOR = 0x00, 0x15, 0x60, 0x69
LAYER_NORMAL, LAYER_COVERED, LAYER_SPLIT = 0, 1, 2
WATER = (41, 115, 231)                    # stand-in colour for an animated-water pixel in previews
GROUND = 'terrain'                        # 'ground' keeps Platinum's soft cast shadows; 'terrain' leaves them out

class Town:
    def __init__(self, cache):
        self.d = Rf.render(cache)
        c = Rf.crop(self.d)
        self.c = c
        self.full = c['full'][..., :3].copy()
        self.low = c[GROUND][..., :3].copy()            # bottom layer, RGB
        self.sea = c['sea'].copy()                      # animated water pixels of the bottom layer
        self.up = c['fg'].copy()                        # top layer, RGBA
        self.up_ground = np.zeros(self.sea.shape, bool) # top pixels that are terrain (lifted off water)
        self.mat = c['mat']
        self.coll = c['collision'].copy()
        self.types = c['types'].copy()
        self.behaviour = np.zeros((H, W), np.uint8)
        self.elev = np.full((H, W), 3, np.uint8)
        self.layer = np.zeros((H, W), np.uint8)
        self.notes = []

    # ------------------------------------------------------------------ helpers
    def cell(self, x, r):
        return slice(r * PX, r * PX + PX), slice(x * PX, x * PX + PX)

    def traversal(self):
        """Platinum water is Emerald ocean water at elevation 1; everything else walks at 3."""
        t = self.types
        water = (t == T_WATER) & ~self.coll
        self.behaviour[water] = MB_OCEAN_WATER
        self.elev[water] = 1
        self.elev[self.coll] = 0
        self.behaviour[t == T_DOOR] = MB_NON_ANIMATED_DOOR

    def lift_canal_walls(self):
        """8x8 quadrants that are part sea: the terrain pixels go to the top layer over animated water when
        the top layer is free there; otherwise the water in that quadrant is drawn still (frame 0)."""
        self.still = np.zeros(self.sea.shape, bool)
        for y in range(0, H * PX, 8):
            for x in range(0, W * PX, 8):
                s = self.sea[y:y + 8, x:x + 8]
                if s.all() or not s.any():
                    continue
                if (self.up[y:y + 8, x:x + 8, 3] > 0).any():
                    self.still[y:y + 8, x:x + 8] = s
                    self.sea[y:y + 8, x:x + 8] = False
                else:
                    g = ~s
                    self.up[y:y + 8, x:x + 8, :3][g] = self.low[y:y + 8, x:x + 8][g]
                    self.up[y:y + 8, x:x + 8, 3][g] = 255
                    self.up_ground[y:y + 8, x:x + 8] = g
                    self.sea[y:y + 8, x:x + 8] = True

    def layers(self):
        """Layer type per cell: a top layer over a cell the player walks is drawn over the player, except
        decks (Platinum's bridge type) and terrain lifted off the water, which the player stands on."""
        for r in range(H):
            for x in range(W):
                sl = self.cell(x, r)
                a = self.up[sl][..., 3] > 0
                if not a.any():
                    self.layer[r, x] = LAYER_NORMAL
                elif self.coll[r, x] or self.types[r, x] == T_BRIDGE or (a & ~self.up_ground[sl]).sum() == 0:
                    self.layer[r, x] = LAYER_COVERED
                else:
                    self.layer[r, x] = LAYER_NORMAL

    def image(self, water=WATER):
        """The composed town as it should decode (animated water as one flat stand-in colour)."""
        out = self.low.copy()
        out[self.sea] = water
        a = self.up[..., 3] > 0
        out[a] = self.up[..., :3][a]
        return out

def build(cache, engine):
    import cn_cleanup as cleanup
    t = Town(cache)
    cleanup.apply(t, engine)
    t.traversal()
    t.lift_canal_walls()
    t.layers()
    return t
