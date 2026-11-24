"""Dump the live DOS draw list (0x8e440, 20 B entries, count 0x91410) as (i, kind, blk, type, idx, camx, camy). drawlist.py [CITY]"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dosrd import Reader
R = Reader(); n = int(sys.argv[1]) if len(sys.argv) > 1 else R.u32(0x91410) & 0xffff
raw = R.rd(0x8e440, n * 20); tab = [struct.unpack('<10I', R.rd(0x97020 + b * 40, 40)) for b in range(128)]
def find(rec):
    for b, t in enumerate(tab):
        if t[4] <= rec < t[4] + t[3] * 18: return b, 'q', (rec - t[4]) // 18
        if t[1] <= rec < t[1] + t[0] * 20: return b, 'w', (rec - t[1]) // 20
        if t[6] <= rec < t[6] + t[5] * 12: return b, 'o', (rec - t[6]) // 12
    return -1, '?', rec
print('count', n)
for i in range(n):
    rec, kind, w8, a, b, c, d = struct.unpack('<IIH4hxx', raw[i * 20:i * 20 + 20])[:7] if False else struct.unpack('<II6h', raw[i * 20:i * 20 + 20])[:7]
    print(i, kind if kind < 0x32 else 'W', *find(rec), a, b, c, d)
