"""Integer reference of the DOS floor path (Q.EXE ground quad 0x47d10 + filler 0x4a6e4 + span 0x3c664), NOTES 'FLOOR FILLER'.
floorref.py <dos_grab.png> <camx> <camy> <camz> <head> [rowlag=1] [pixlag=1] [carry=1] [out=png] [city=KCITY]
Renders floor quads at 320x200 (palette index), prints share of pixels equal to the DOS grab (RGB565) per row band."""
import sys, os, json, struct
from PIL import Image
T = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(T, '..', 'port', 'data')
def tdiv(a, b):
    q = abs(a) // abs(b); return q if (a < 0) == (b < 0) else -q
def s16(v): v &= 0xffff; return v - 0x10000 if v & 0x8000 else v
def s32(v): v &= 0xffffffff; return v - (1 << 32) if v & 0x80000000 else v
SIN = struct.unpack('<1441h', open(os.path.join(D, 'sintab.bin'), 'rb').read())
def dsin(h):
    h %= 5760; q, r = divmod(h, 1440)
    return (SIN[r], SIN[1440 - r], -SIN[r], -SIN[1440 - r])[q]
TAB = [0] * 202
for y in range(101, 200): TAB[y] = 0x1400 // (0x1400 // (y - 100)); TAB[201 - y] = -TAB[y]
CLIP_T, CLIP_B, CLIP_L, CLIP_R = 37, 149, 0, 320
DBG = None
def rot(x, y, r):
    for _ in range(r & 3): x, y = 512 - y, x
    return x, y
def render(city, camx, camy, camz, head, rowlag=1, pixlag=1, carry=1, rad=7, yoff=0):
    d = json.load(open(os.path.join(D, city + '.json'))); W, H = d['w'], d['h']; cells = d['cells']; blocks = d['blocks']
    tiles = open(os.path.join(D, 'live_kfloor.bin'), 'rb').read(); lut = open(os.path.join(D, 'live_kshade.bin'), 'rb').read()
    C = dsin(head + 1440); S = -dsin(head)
    buf = [[-1] * 320 for _ in range(200)]
    gx = ((camx >> 9) << 9) - camx; gy = ((camy >> 9) << 9) - camy
    ox = -((gx * C + gy * S) >> 11); oy = (gy * C - gx * S) >> 11
    a16 = (-C * 16) >> 6; b16 = (-S * 16) >> 6; c16 = (16 * C) >> 6
    ccx, ccy = camx >> 9, camy >> 9
    order = sorted(((cx, cy) for cy in range(ccy - rad, ccy + rad + 1) for cx in range(ccx - rad, ccx + rad + 1) if 0 <= cx < W and 0 <= cy < H), key=lambda c: -((c[0] - ccx) ** 2 + (c[1] - ccy) ** 2))
    for cx, cy in order:
        c = cells[cy * W + cx]
        if (c & 0x7f) == 0: continue
        b = blocks[(c & 0x7f) - 1]; r = (c >> 8) & 3
        cdx, cdy = cx - ccx, cy - ccy
        bcx = -(cdy * b16 + cdx * a16 + ox); bcy = -(c16 * cdy + b16 * cdx + oy)
        for q in b['q']:
            z = q[3]
            if not ((camz < z and q[6] < q[10]) or (z < camz and q[10] < q[6])): continue
            P = []
            for v in range(4):
                lx, ly = rot(q[5 + v * 2], q[6 + v * 2], r); i, j = lx >> 5, ly >> 5
                P.append([((-C * i) >> 6) + ((-S * j) >> 6) - bcx, ((-S * i) >> 6) + ((j * C) >> 6) - bcy])
            n = len(P); out = []
            if all(p[1] < 15 for p in P): continue
            for k in range(n):  # near clip at depth 15 (0x47d10)
                a = P[k]; pv = P[k - 1]; nx = P[(k + 1) % n]
                if a[1] >= 15: out.append(a); continue
                if pv[1] >= 15: out.append([s16(tdiv((15 - a[1]) * (pv[0] - a[0]), pv[1] - a[1])) + a[0], 15])
                if nx[1] >= 15: out.append([s16(tdiv((15 - a[1]) * (nx[0] - a[0]), nx[1] - a[1])) + a[0], 15])
            P = out; n = len(P)
            if n < 3: continue
            V = [(tdiv(p[0] << 8, max(p[1], 12)) + 160, tdiv((z - camz) * 256, max(p[1], 12)) + 100 + yoff) for p in P]
            fill(buf, V, [p[1] for p in P], n, (z - camz) << 8, q[2] & 3, q[4], tiles[(q[1][r] & 15) * 4096:][:4096], lut, C, S, camx, camy, rowlag, pixlag, carry, yoff)
    return buf
def fill(buf, V, SH, n, p4, rt, s, tex, lut, C, S, camx, camy, rowlag, pixlag, carry, yoff=0):
    top = min(range(n), key=lambda i: V[i][1]); bot = max(range(n), key=lambda i: V[i][1])
    li = (top - 1) % n; lc = top; ri = (top + 1) % n; rc = top
    ytop = V[top][1]; ybot = V[bot][1]
    if not (ytop < ybot and CLIP_T < ybot and ytop <= CLIP_B): return
    sh = [max(0, min(0xfff, tdiv(x << 8, 110))) for x in SH]
    l6c = sh[top]; shstep = tdiv(sh[bot] - l6c, ybot - ytop)
    l40 = V[top][0] << 10; l3c = l40; esi = edi = 0
    dy = V[li][1] - V[lc][1]
    if dy: esi = tdiv((V[li][0] - V[lc][0]) * 0x400, dy)
    dy = V[ri][1] - V[rc][1]
    if dy: edi = tdiv((V[ri][0] - V[rc][0]) * 0x400, dy)
    l48 = min(ybot, CLIP_B); l54 = V[li][1]; l50 = V[ri][1]
    du = 0; dv = 0; l34 = S; l2c = C
    y = ytop
    def step(y):
        q = tdiv(p4, TAB[y - yoff]); A = s32(S * q); B = s32(q * C); shf = s + 9; sl = 10 - s
        if rt == 0: return s16(-B >> shf), s16(-A >> shf), s32(-((A >> 11) - camx) << sl), s32(((B >> 11) + camy) << sl)
        if rt == 1: return s16(-A >> shf), s16(B >> shf), s32(((B >> 11) + camy) << sl), s32(((A >> 11) - camx) << sl)
        if rt == 2: return s16(B >> shf), s16(A >> shf), s32(((A >> 11) - camx) << sl), s32(-((B >> 11) + camy) << sl)
        return s16(A >> shf), s16(-B >> shf), s32(-((B >> 11) + camy) << sl), s32(-((A >> 11) - camx) << sl)
    while y <= l48:
        if y == l54:
            while y == l54: lc = li; li = (li - 1) % n; l54 = V[li][1]
            esi = tdiv((V[li][0] - V[lc][0]) * 0x400, V[li][1] - V[lc][1]); l40 = V[lc][0] << 10
        if y == l50:
            while y == l50: rc = ri; ri = (ri + 1) % n; l50 = V[ri][1]
            edi = tdiv((V[ri][0] - V[rc][0]) * 0x400, V[ri][1] - V[rc][1]); l3c = V[rc][0] << 10
        xl = s16(l40 >> 10); xr = s16(((l3c >> 10) & 0xffff) + 1)
        if not (y < CLIP_T or xr <= CLIP_L or xl >= CLIP_R) and TAB[y - yoff] != 0:
            if not rowlag: du, dv, l34, l2c = step(y)
            k = xl - 0xa0
            u0 = (l34 + (du & 0xffff) * k) & 0xffff; v0 = (l2c + ((k * dv) & 0xffff)) & 0xffff
            if xr > CLIP_R: xr = CLIP_R
            if xl < CLIP_L: u0 = (u0 + (du & 0xffff) * (CLIP_L - xl)) & 0xffff; v0 = (v0 + (CLIP_L - xl) * dv) & 0xffff; xl = CLIP_L
            if xr > xl:
                if rowlag: du, dv, l34, l2c = step(y)
                L = lut[(l6c >> 6) * 256:][:256]; row = buf[y]
                if DBG and DBG[1] == y and xl <= DBG[0] < xr: print('DBG', dict(V=V, SH=SH, top=top, bot=bot, lc=lc, li=li, xl=xl, xr=xr, u0=u0, v0=v0, du=du, dv=dv, l6c=l6c, rt=rt, s=s, p4=p4))
                ecx = (u0 << 16) | v0; edx = ((du & 0xffff) << 16) | (dv & 0xffff)
                for x in range(xl, xr):
                    kk = max(0, x - xl - (1 if pixlag else 0))
                    if carry: e = (ecx + kk * edx) & 0xffffffff; u = e >> 16; v = e & 0xffff
                    else: u = (u0 + kk * du) & 0xffff; v = (v0 + kk * dv) & 0xffff
                    row[x] = L[tex[((v >> 10) & 63) << 6 | ((u >> 10) & 63)]]
        l6c += shstep; l40 += esi; l3c += edi; y += 1
if __name__ == '__main__':
    a = sys.argv[1:]; kw = dict(x.split('=') for x in a[5:]); city = kw.get('city', 'KCITY')
    cam = [int(v) for v in a[1:5]]
    buf = render(city, *cam, rowlag=int(kw.get('rowlag', 1)), pixlag=int(kw.get('pixlag', 1)), carry=int(kw.get('carry', 1)), yoff=int(kw.get('yoff', 0)))
    pal = open(os.path.join(D, 'live_kpal.bin'), 'rb').read()
    q5 = lambda v: ((v >> 3) << 3) | (v >> 5); q6 = lambda v: ((v >> 2) << 2) | (v >> 6)
    m = 4 if max(pal) < 64 else 1
    P = [(q5(pal[i * 3] * m), q6(pal[i * 3 + 1] * m), q5(pal[i * 3 + 2] * m)) for i in range(256)]
    dos = Image.open(a[0]).convert('RGB'); sx = dos.width // 320; sy = dos.height // 200; dp = dos.load()
    tot = eq = 0; rows = {}
    for y in range(200):
        for x in range(320):
            i = buf[y][x]
            if i < 0: continue
            e = P[i] == dp[x * sx, y * sy]; tot += 1; eq += e; r = rows.setdefault(y // 8 * 8, [0, 0]); r[0] += 1; r[1] += e
    print(json.dumps({'drawn': tot, 'equal': round(eq / max(tot, 1), 4), 'rows': {k: round(v[1] / v[0], 3) for k, v in sorted(rows.items())}}))
    if 'out' in kw:
        im = Image.new('RGB', (320, 200)); px = im.load()
        for y in range(200):
            for x in range(320):
                if buf[y][x] >= 0: px[x, y] = P[buf[y][x]]
        im.save(kw['out'])
