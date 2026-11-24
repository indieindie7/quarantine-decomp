"""idp.py <case>: which port item owns each pixel that differs from DOS. Renders the case with --idv (320x200 id view) and groups the
differing pixels by (cell dx, dy from the camera cell, kind, item column = quad idx | nq + wall idx), with the x / row box of each group.
Works on the 320x200 idv shot (tools/idq.py wants 640). Next: tools/wallref.py x y z head cellx celly."""
import sys, os, json
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import paritylib as L
from PIL import Image, ImageChops
n = sys.argv[1]; c = json.load(open(os.path.join(L.CASES, n, 'case.json')))
out = 'shots/idv_%s.png' % n; L.port_shot(c, out, 'res://tests/cases/%s/ents.json' % n, '--idv')
p, d = L.load_pair(os.path.join(L.PORT, 'shots', 'par_%s_port.png' % n), os.path.join(L.CASES, n, 'dos.png'))
p = p.convert('RGB').resize((320, 200), 0); d = d.convert('RGB').resize((320, 200), 0)
m = ImageChops.difference(p, d).convert('L').load(); iv = Image.open(os.path.join(L.PORT, out)).convert('RGB').resize((320, 200), 0).load()
lin = lambda v: (v / 255 / 12.92) if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4
G = {}
for y in range(200):
    for x in range(320):
        if not m[x, y]: continue
        r, g, b = iv[x, y]; oid = round(lin(r) * 63) - 8; ci = round(lin(g) * 63) - 8
        k = (ci % 7 - 3, ci // 7 - 3, 'spr' if b > 240 else 'floor' if b > 100 else 'wall', oid)
        e = G.setdefault(k, [0, 320, 0, 200, 0]); e[0] += 1; e[1] = min(e[1], x); e[2] = max(e[2], x); e[3] = min(e[3], y); e[4] = max(e[4], y)
cx, cy = c['cam']['x'] >> 9, c['cam']['y'] >> 9
print(n, 'cam', c['cam']['x'], c['cam']['y'], c['cam']['z'], c['cam']['head'], 'cell', cx, cy)
for k, e in sorted(G.items(), key=lambda v: -v[1][0])[:12]: print('%4d px  cell %d,%d (d %d,%d) %-5s item %d  x %d-%d rows %d-%d' % (e[0], cx + k[0], cy + k[1], k[0], k[1], k[2], k[3], e[1], e[2], e[3], e[4]))
