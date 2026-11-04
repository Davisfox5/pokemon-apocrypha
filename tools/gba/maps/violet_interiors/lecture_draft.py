import room as RM, numpy as np
def court(r, L, top=11, bottom=22, stone=(25, 26, 27)):
    dst, src = [], []
    for y in range(top, bottom + 1):
        for x in range(12, 19):
            dst.append(L(x, y)); src.append(L(x, stone[(y - top) % len(stone)]))
    RM.paint(r, dst, src)
    low = r.lower
    X0, Y0, X1, Y1 = L(12, 0)[0] * 16 + 4, top * 16 + 4, L(19, 0)[0] * 16 - 6, (bottom + 1) * 16 - 6
    W, Sd = (248, 248, 240), (150, 160, 176)
    def hline(y, x0, x1): low[y:y + 2, x0:x1] = W; low[y + 2, x0 + 1:x1] = Sd
    def vline(x, y0, y1): low[y0:y1, x:x + 2] = W; low[y0 + 1:y1, x + 2] = Sd
    hline(Y0, X0, X1 + 2); hline(Y1, X0, X1 + 2); vline(X0, Y0, Y1 + 2); vline(X1, Y0, Y1 + 2)
    cy, cx = (Y0 + Y1) // 2, (X0 + X1) // 2
    hline(cy, X0, X1)
    yy, xx = np.mgrid[0:low.shape[0], 0:low.shape[1]]
    d = np.sqrt((xx - cx - 0.5) ** 2 + (yy - cy - 0.5) ** 2)
    low[(d >= 14) & (d < 16)] = W
    low[(d >= 16) & (d < 17) & (yy > cy + 2)] = Sd
