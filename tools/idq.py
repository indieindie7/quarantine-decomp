"""idq.py <par_idv.png> <par_ref.png> [y0 y1]: per mismatching pixel of ref (port vs DOS), which item the idv snap shows there. Prints counts per (cell idx, dx, dy, item, kind)."""
import sys, collections
from PIL import Image
def lin(v):
    v /= 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
iv = Image.open(sys.argv[1]).convert('RGB'); rf = Image.open(sys.argv[2]).convert('RGB'); w = rf.width // 3
y0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0; y1 = int(sys.argv[4]) if len(sys.argv) > 4 else 200
ip = iv.load(); rp = rf.load(); C = collections.Counter(); X = {}
for y in range(y0, y1):
    for x in range(320):
        a = rp[x * 2, y * 2]; b = rp[x * 2 + w, y * 2]
        if a == b: continue
        r, g, bl = ip[x * 2, y * 2]
        oid = round(lin(r) * 63) - 8; ci = round(lin(g) * 63) - 8; k = 'S' if bl > 240 else ('F' if bl > 100 else 'W')
        key = (ci % 7 - 3, ci // 7 - 3, oid, k, 'blank' if (r, g, bl) == (0, 0, 0) else '')
        C[key] += 1; e = X.setdefault(key, [x, x, y, y]); e[0] = min(e[0], x); e[1] = max(e[1], x); e[2] = min(e[2], y); e[3] = max(e[3], y)
for k, n in C.most_common(40): print(n, 'dx,dy', k[0], k[1], 'item', k[2], k[3], k[4], 'x', X[k][0], X[k][1], 'y', X[k][2], X[k][3])
