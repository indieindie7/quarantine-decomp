"""entsync.py <out.json> [tries]: DOSBox grab (ctrl+F5) taken while the live entity list is stable (same list 120 ms before, right before and 60 ms after the grab key). Prints the grab path. 'rate' as first arg: print how often the list changes."""
import sys, os, time, json, glob, ctypes
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import struct
from dosrd import Reader, DELTA
G = {0x83180: 'EXPLO', 0x83188: 'CITYOBJ', 0x8318c: 'CITYGUN', 0x7f38c: 'SHAD8DK', 0x83100: 'FIRE', 0x8312c: 'ETRACERS', 0x7f2d0: 'PUMTFR1', 0x7f2dc: 'CYCTSPR', 0x7f2e4: 'CYCTWIN', 0x7f2fc: 'CAB1SPR', 0x7f300: 'COMPSPR', 0x8315c: 'PEDH1', 0x83160: 'PEDH2', 0x83164: 'PEDH3', 0x83168: 'PEDH4'}
R = Reader(); B = {R.u32(g): n for g, n in G.items()}
GD = os.path.join(T, '..', 'dos', 'Quarantine'); HDR = {}; UNK = os.path.join(os.environ.get('TEMP', '.'), 'entunk.txt')
for fn in os.listdir(GD):
    if fn.upper().endswith('.SPR'):
        h = open(os.path.join(GD, fn), 'rb').read(513); HDR.setdefault(h[:1 + h[0] * 2], fn[:-4].upper())
def bank(ptr, gv=0):
    """Bank name of a live sprite-bank pointer not in G: header match (count + w,h list) against dos/Quarantine/*.SPR (same as entdump.py); misses go to %TEMP%/entunk.txt."""
    if ptr in B: return B[ptr]
    if not 0x200000 < ptr < 0x600000: return None
    n = R.p(ptr, 1)[0]; m = R.p(ptr + 1, n * 4); B[ptr] = HDR.get(bytes([n]) + b''.join(bytes([m[i * 4 + 1], m[i * 4]]) for i in range(n))) if n else None
    open(UNK, 'a').write('gvar %x ptr %x -> %s hdr %s' % (gv, ptr, B[ptr], R.p(ptr, 16).hex()) + chr(10))
    return B[ptr]
def drawn():
    """Entity slots DOS drew in the last frame: sorted draw list 0x8e440 (20 B: ptr, type; type 1 = entity record, draw 0x46ec4), its length = last
    of the per-cell running totals 0x913ac[u16 0x91418 - 1] (render, decomp_q.c 40035). Exact when paused; count [0x9141a] is 0 then and slots above it are stale."""
    nc = struct.unpack('<H', R.rd(0x91418, 2))[0]
    if not 0 < nc <= 49: return []
    L = struct.unpack('<h', R.rd(0x913ac + 2 * (nc - 1), 2))[0]
    if not 0 < L <= 400: return []
    raw = R.rd(0x8e440, 20 * L); S = set()
    for i in range(L):
        p, t = struct.unpack('<Ii', raw[i*20:i*20+8]); q, r = divmod(p - 0x245f10, 24)
        if t == 1 and r == 0 and 0 <= q < 40: S.add(q)
    return sorted(S)
def ents():  # same rules as entdump.py, one open process handle
    out = []; raw = R.p(0x245f10, 24 * 40)
    for i in drawn():
        a, x, y, z, sz, sp, fl, sh, b2, b3 = struct.unpack('<IiihhIBbBB', raw[i*24:i*24+24])
        if not (0x200000 < a < 0x600000 and 0x200000 < sp < 0x600000 and 0 < x < 1 << 20 and 0 < y < 1 << 20): continue
        parts = []
        if fl & 0x80:
            for k in range(fl & 0x1f):
                pp, idx, dx, dy, pad = struct.unpack('<IbbbB', R.p(sp + k * 8, 8)); f = G.get(pp - DELTA) or bank(R.u32(pp - DELTA), pp - DELTA)
                if f is not None: parts.append([f, idx, dx, dy])
        elif bank(sp): parts.append([B[sp], fl & 0x3f, 0, 0])
        if parts: out.append({'x': x, 'y': y, 'z': z, 'size': sz, 'shade': sh, 'mirror': 1 if fl & 0x40 else 0, 'parts': parts})
    return out
if sys.argv[1] == 'paused':  # 1 when the list stands still for 0.4 s
    e0 = ents(); t0 = time.time(); ok = 1
    while time.time() - t0 < 0.4:
        if ents() != e0: ok = 0; break
    print(ok); sys.exit()
if sys.argv[1] == 'rate':
    t0 = time.time(); last = None; n = 0; ch = []
    while time.time() - t0 < 3.0:
        e = json.dumps(ents()); n += 1
        if e != last: ch.append(round(time.time() - t0, 2)); last = e
    print('reads', n, 'changes', len(ch), 'first', ch[:6], 'ents', len(json.loads(last))); sys.exit()
sys.argv, av = ['dbox.py', 'none'], sys.argv
import importlib.util
sp = importlib.util.spec_from_file_location('dbox_m', os.path.join(T, 'dbox.py')); D = importlib.util.module_from_spec(sp)
try: sp.loader.exec_module(D)
except SystemExit: pass
sys.argv = av; h = D.hwnd(); tries = int(av[2]) if len(av) > 2 else 40
for t in range(tries):
    a0 = ents(); time.sleep(0.12); a = ents()
    if a != a0: continue
    before = set(glob.glob(D.PLAY + r'\capture\*.png'))
    D.post(h, 'f11', True); time.sleep(0.06); b = ents(); D.post(h, 'f11', False); time.sleep(0.8)
    new = sorted(set(glob.glob(D.PLAY + r'\capture\*.png')) - before, key=os.path.getmtime)
    if a == b and new:
        json.dump(a, open(av[1], 'w')); print('tries', t + 1); print(new[-1]); sys.exit()
    for f in new: os.remove(f)
sys.exit('no stable grab')
