"""wallref.py: Python reference model of the DOS wall set-up (Q.EXE 0x482fc for raw ti >= 0, 0x487b8 for ti < 0): table view transform
(0x372c0 + 0x37368 + 0x373e0), near clip at depth 12, projection (leaf 0x371f8), back-face rule, drawn point range (r0..g), shade divisor.
Same maths as port/shaders/wall.gdshader `doswall` branch; change the model first, prove it with --live, then match the shader to it.
  wallref.py x y z head [cellx celly]   every wall of the 7x7 cells (or one cell): cnt, sx, range, dx
  wallref.py --live                     DOSBox paused in game: the last wall DOS set up (table 0x984a8 = x, ytop shorts per point) must equal one model wall
"""
import sys, os, json, math, struct
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
D = os.path.join(T, '..', 'port', 'data')
tab = struct.unpack('<1441h', open(os.path.join(D, 'sintab.bin'), 'rb').read()[:2882])
def dsin(h):
    h %= 5760; q, r = divmod(h, 1440)
    return [tab[r], tab[1440 - r], -tab[r], -tab[1440 - r]][q]
def tdiv(a, b):  # C integer division (toward zero)
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q
def shade_div(wl, head):
    """Shade divisor 110 - (angle between wall and view) / 2."""
    n = wl[0]; wqx = wl[1] * n; wqy = -wl[2] * n
    a = int(math.floor(math.degrees(math.atan2(min(abs(wqx), abs(wqy)), max(abs(wqx), abs(wqy), 0.0001))) + 0.001))
    if abs(wqy) > abs(wqx): a = 90 - a
    if wqx < 0: a = 180 - a
    if wqy < 0: a = 360 - a
    wd = abs(a % 360 - (head >> 4))
    if wd > 180: wd = 360 - wd
    if wd > 120: wd = 180 - wd
    return max(110 - (wd >> 1), 1)
def view_points(cx, cy, wl, camx, camy, head):
    """Table view transform of the wall points, k = 0..n running END -> START (0x487b8 stores them so). -> vx[], vd[]"""
    f0, f1 = -dsin(head), dsin(head + 1440); n = wl[0]
    gx = ((camx >> 9) << 9) - camx; gy = ((camy >> 9) << 9) - camy
    ox = -((gx * f1 + gy * f0) >> 11); oy = (gy * f1 - gx * f0) >> 11
    cdx = cx - (camx >> 9); cdy = cy - (camy >> 9)
    a16 = (-f1 * 16) >> 6; b16 = (-f0 * 16) >> 6; c16 = (16 * f1) >> 6
    bcx = -(cdy * b16 + cdx * a16 + ox); bcy = -(c16 * cdy + b16 * cdx + oy)
    T = [((wl[4] + wl[1] * (n - k)) >> 5, (wl[5] + wl[2] * (n - k)) >> 5) for k in range(n + 1)]
    return [((-f1 * ti) >> 6) + ((-f0 * tj) >> 6) - bcx for ti, tj in T], [((-f0 * ti) >> 6) + ((tj * f1) >> 6) - bcy for ti, tj in T]
def slide(vx, vd, i, j):
    """Point i (depth < 12) slides along the wall towards point j until depth 12."""
    dd = vd[j] - vd[i]
    if dd: vx[i] = tdiv((vx[j] - vx[i]) * (12 - vd[i]), dd) + vx[i]
    vd[i] = 12
def near_clip(vx, vd):
    """-> point count left, or 0 when the whole wall is nearer than depth 12."""
    cnt = len(vd); s = 0
    while s < cnt and vd[s] < 12: s += 1
    if s == cnt: return 0
    if s > 0: slide(vx, vd, s - 1, s); return cnt
    e = cnt - 1
    while vd[e] < 12: e -= 1
    if e != cnt - 1: slide(vx, vd, e + 1, e); cnt = e + 2
    return cnt
def draw_range(sx, cnt, rev, nt):
    """-> (r0, g) first and last point index (in draw direction) of the part DOS draws, or None when no point is on screen."""
    at = lambda i: sx[cnt - 1 - i if rev else i]
    f = 0
    while f < cnt and not 0 <= at(f) <= 320: f += 1
    if f >= cnt: return None
    g = l1 = max(f, 1)
    while g < cnt:
        X = ((at(g) + 32768) & 65535) - 32768  # DOS compares the low 16 bits
        if X < 0 or (X > 320 and not nt): break  # 0x482fc stops at the first point right of the view; 0x487b8 only at x < 0
        g += 1
    return l1 - 1, min(g, cnt - 1)
def wall(d, cx, cy, wl, camx, camy, camz, head):
    """One wall (wl[8] = its texture list) of the block at cell (cx, cy). Returns dict; 'kill' = why DOS draws nothing, else None."""
    n = wl[0]; nt = len(wl) > 9 and wl[9] < 0; R = dict(n=n, div=shade_div(wl, head), nt=nt, cnt=n + 1, kill=None)
    vx, vd = view_points(cx, cy, wl, camx, camy, head)
    if vd[0] <= 9 and vd[n] <= 9: R['kill'] = 'both ends near'; return R
    cnt = near_clip(vx, vd)
    if cnt == 0: R['kill'] = 'all near'; return R
    P = lambda z: [tdiv((z - camz) * 256, max(vd[k], 12)) + 100 for k in range(cnt)]
    sx = [tdiv(vx[k] * 256, max(vd[k], 12)) + 160 for k in range(cnt)]; tx = wl[8]
    two = bool(tx) and 'wf' in d and tx[0][0] < 15 and tx[0][1] < 12 and (d['wf'][tx[0][0]][tx[0][1]] & 2) != 0
    rev = sx[cnt - 1] < sx[0]; R.update(cnt=cnt, sx=sx, yt=P(wl[6] - wl[3]), yb=P(wl[6]), vd=vd[:cnt], rev=rev, two=two)
    if rev and not two: R['kill'] = 'back face'; return R
    rg = draw_range(sx, cnt, rev, nt)
    if rg is None: R['kill'] = 'no point on screen'; return R
    r0, g = rg; i0 = cnt - 1 - r0 if rev else r0; iN = cnt - 1 - g if rev else g; R.update(r0=r0, g=g, i0=i0, iN=iN, dx=sx[iN] - sx[i0])
    if R['dx'] <= 0: R['kill'] = 'dx <= 0'
    return R
def cell_walls(d, camx, camy):
    """Every wall of the 7x7 cells around the camera, with the cell's texture set picked. -> cx, cy, block, wall idx, wall record"""
    W, H = d['w'], d['h']
    for cy in range(max((camy >> 9) - 3, 0), min((camy >> 9) + 4, H)):
        for cx in range(max((camx >> 9) - 3, 0), min((camx >> 9) + 4, W)):
            c = d['cells'][cy * W + cx]
            for wi, wl in enumerate(d['blocks'][(c & 0x7f) - 1]['w'] if c & 0x7f else []):
                yield cx, cy, (c & 0x7f) - 1, wi, wl[:8] + [wl[8][(c >> 8) & 3] if wl[8] else []] + wl[9:]
def walls(camx, camy, camz, head, city='KCITY', only=None):
    d = json.load(open(os.path.join(D, city + '.json')))
    for cx, cy, bi, wi, wl in cell_walls(d, camx, camy):
        if only is None or (cx, cy) == only: yield cx, cy, bi, wi, wall(d, cx, cy, wl, camx, camy, camz, head)
if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--live':
        from dosrd import Reader
        import subprocess
        cam = json.loads(subprocess.run([sys.executable, '-I', os.path.join(T, 'dosmem.py'), 'cam'], capture_output=True, text=True).stdout)
        raw = struct.unpack('<68h', Reader().rd(0x984a8, 136)); hit = 0; tot = 0
        print('cam', cam, 'dos 0x984a8', raw[:16])
        for cx, cy, bi, wi, R in walls(cam['x'], cam['y'], cam['z'], cam['head']):
            if 'sx' not in R: continue
            tot += 1; m = [v for k in range(R['cnt']) for v in (R['sx'][k], R['yt'][k])]
            if tuple(((v + 32768) & 65535) - 32768 for v in m) == raw[:len(m)]:
                hit += 1; print('MATCH cell', cx, cy, 'blk', bi, 'wall', wi, {k: R[k] for k in ('cnt', 'sx', 'yt', 'rev', 'kill', 'nt') if k in R}, {k: R[k] for k in ('r0', 'g', 'dx') if k in R})
        print('model walls', tot, 'matching the DOS table', hit, 'PASS' if hit else 'FAIL (or the table was last written by a non-wall polygon: try another pose)')
        sys.exit(0 if hit else 1)
    x, y, z, h = [int(v) for v in a[:4]]; only = (int(a[4]), int(a[5])) if len(a) > 5 else None
    for cx, cy, bi, wi, R in walls(x, y, z, h, only=only):
        print(cx, cy, 'blk', bi, 'w', wi, 'n', R['n'], 'div', R['div'], 'nt', int(R['nt']), 'KILL ' + R['kill'] if R['kill'] else '', 'cnt', R['cnt'], 'sx', R.get('sx'), 'range', R.get('r0'), R.get('g'), 'dx', R.get('dx'))
