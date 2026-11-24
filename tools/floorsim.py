"""Emulate the DOS floor span filler (Q.EXE 0x4a6e4 + 0x3c664) for one screen row and brute-force tile/rot/shift/shade/lag against a DOS shot. Usage: floorsim.py <par_png> <row> [x0 x1]"""
import sys, os, struct, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dosrd import Reader
def s32(r, a): return struct.unpack('<i', r.rd(a, 4))[0]
def live():
    r = Reader()
    return {'S': s32(r, 0x7eabc), 'C': s32(r, 0x7eab8), 'cx': s32(r, 0x83224), 'cy': s32(r, 0x83228), 'cam': [s32(r, 0x83230 + i * 4) for i in range(3)], 'o66': r.s16(0x83566), 'o68': r.s16(0x83568), 'tab': list(struct.unpack('<202i', r.rd(0x98598, 808)))}
def row(L, y, xs, dh, rot, p6, qy=None):
    """u,v texel coords for screen row y (qy = row whose q feeds the bases, for the lag test)"""
    def qv(yy): return int((dh << 8) / L['tab'][yy]) if L['tab'][yy] else 0
    q = qv(y if qy is None else qy); a = L['S'] * q; b = q * L['C']; sh = p6 + 9; ls = 10 - p6
    if rot == 0: du = (-b) >> sh; dv = (-a) >> sh; ub = (-((a >> 11) - L['cx'])) << ls; vb = ((b >> 11) + L['cy']) << ls
    elif rot == 1: dv = b >> sh; du = (-a) >> sh; vb = ((a >> 11) - L['cx']) << ls; ub = ((b >> 11) + L['cy']) << ls
    elif rot == 2: du = b >> sh; dv = a >> sh; ub = ((a >> 11) - L['cx']) << ls; vb = (-((b >> 11) + L['cy'])) << ls
    else: dv = (-b) >> sh; du = a >> sh; vb = (-((a >> 11) - L['cx'])) << ls; ub = (-((b >> 11) + L['cy'])) << ls
    du &= 0xffff; dv &= 0xffff
    u = (ub + du * (xs - 160) + L['o68']) & 0xffff; v = (vb + dv * (xs - 160) + L['o66']) & 0xffff
    return (v >> 10), (u >> 10)
if __name__ == '__main__':
    LAG = int(os.environ.get('LAG', '1')); L = live(); print({k: v for k, v in L.items() if k != 'tab'}, L['tab'][100:112], L['tab'][190:200])
    json.dump(L, open(os.path.join(os.environ['TEMP'], 'floorlive.json'), 'w'))
    im = np.asarray(Image.open(sys.argv[1]).convert('RGB'), dtype=float)[::2, ::2][:, 320:640]
    y = int(sys.argv[2]); x0, x1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (100, 220)
    D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'port', 'data')
    idx = np.asarray(Image.open(D + '/KCITY_walls_idx.png'))[960:1024]; pal = np.asarray(Image.open(D + '/KCITY_pal.png').convert('RGB'), dtype=float)[0]; lut = np.asarray(Image.open(D + '/KCITY_shade.png'))
    xs = np.arange(x0, x1); tgt = im[y, x0:x1]; res = []
    for dh in range(-60, 61, 1):
        if dh == 0: continue
        for rot in range(4):
            for p6 in (0, 1, 2):
                try: v, u = row(L, y, xs, dh, rot, p6, y - LAG)
                except Exception: continue
                for t in range(15):
                    ti = idx[v, t * 64 + u]
                    for lv in range(0, 64, 3):
                        e = np.abs(pal[lut[lv][ti]] - tgt).mean(); res.append((e, dh, rot, p6, t, lv))
    res.sort(); print(res[:6])
