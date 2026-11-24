import sys, os, struct
sys.path.insert(0, r'C:\Games\Quarantine\tools')
from dosrd import Reader
R = Reader(); base = 2383632 - 24 * 20; raw = R.p(base, 24 * 60)
for i in range(60):
    r = raw[i*24:i*24+24]; a, x, y, z, sz, sp, fl, sh, b2, b3 = struct.unpack('<IiihhIBBBB', r)
    print(hex(base + i*24), hex(a), x, y, x >> 9 if 0 < x < 1 << 20 else '', y >> 9 if 0 < y < 1 << 20 else '', z, sz, hex(sp), hex(fl), sh, b2, b3)
