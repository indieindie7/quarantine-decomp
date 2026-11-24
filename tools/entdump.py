"""entdump.py [out.json]: live DOS dynamic entities (24 B records from live ptr 0x245f10, draw 0x33fb8; NOTES 'DYNAMIC ENTITIES FOUND') -> JSON [{x,y,z,size,shade,mirror,parts:[[FILE,idx,dx,dy]]}]."""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dosrd import Reader, DELTA
G = {0x83180: 'EXPLO', 0x83188: 'CITYOBJ', 0x8318c: 'CITYGUN', 0x7f38c: 'SHAD8DK', 0x83100: 'FIRE', 0x8312c: 'ETRACERS', 0x7f2d0: 'PUMTFR1', 0x7f2dc: 'CYCTSPR', 0x7f2e4: 'CYCTWIN', 0x7f2fc: 'CAB1SPR', 0x7f300: 'COMPSPR', 0x8315c: 'PEDH1', 0x83160: 'PEDH2', 0x83164: 'PEDH3', 0x83168: 'PEDH4'}
R = Reader(); B = {R.u32(g): n for g, n in G.items()}; out = []; unk = 0
GD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dos', 'Quarantine'); HDR = {}
for fn in os.listdir(GD):
    if fn.upper().endswith('.SPR'):
        h = open(os.path.join(GD, fn), 'rb').read(513); HDR.setdefault(h[:1 + h[0] * 2], fn[:-4].upper())
def bank(ptr):
    """Bank name of a live sprite-bank pointer: known global, else header match (count + w,h list) against dos/Quarantine/*.SPR."""
    if ptr in B: return B[ptr]
    if not 0x200000 < ptr < 0x600000: return None
    n = R.p(ptr, 1)[0]; m = R.p(ptr + 1, n * 4); B[ptr] = HDR.get(bytes([n]) + b''.join(bytes([m[i * 4 + 1], m[i * 4]]) for i in range(n))) if n else None  # memory rec = (h, w, u16 off), loader 0x39368
    return B[ptr]
raw = R.p(0x245f10, 24 * 40); nc = struct.unpack('<H', R.rd(0x91418, 2))[0]; LL = struct.unpack('<h', R.rd(0x913ac + 2 * (nc - 1), 2))[0] if 0 < nc <= 49 else 0; dl = R.rd(0x8e440, 20 * max(LL, 0))  # exact drawn set: draw list, see entsync.py drawn() / NOTES 'STALE ENTITY SLOTS'
SL = sorted({(struct.unpack('<I', dl[j*20:j*20+4])[0] - 0x245f10) // 24 for j in range(max(LL, 0)) if struct.unpack('<i', dl[j*20+4:j*20+8])[0] == 1 and 0 <= struct.unpack('<I', dl[j*20:j*20+4])[0] - 0x245f10 < 960}); cnt = len(SL)
open(os.path.join(os.environ.get('TEMP', '.'), 'entunk.txt'), 'a').write('drawlist L %d: %s
' % (LL, ' '.join('%x:%d' % struct.unpack('<Ii', dl[j*20:j*20+8]) for j in range(max(LL, 0)))))
for i in SL:
    a, x, y, z, sz, sp, fl, sh, b2, b3 = struct.unpack('<IiihhIBbBB', raw[i*24:i*24+24])
    if not (0x200000 < a < 0x600000 and 0x200000 < sp < 0x600000 and 0 < x < 1 << 20 and 0 < y < 1 << 20): open(os.path.join(os.environ.get('TEMP', '.'), 'entunk.txt'), 'a').write('invalid slot %d rec %s
' % (i, raw[i*24:i*24+24].hex())); continue
    parts = []
    if fl & 0x80:
        for k in range(fl & 0x1f):
            pp, idx, dx, dy, pad = struct.unpack('<IbbbB', R.p(sp + k * 8, 8)); f = G.get(pp - DELTA) or bank(R.u32(pp - DELTA))
            if f is None: unk += 1; open(os.path.join(os.environ.get('TEMP', '.'), 'entunk.txt'), 'a').write('gvar %x ptr %x idx %d hdr %s
' % (pp - DELTA, R.u32(pp - DELTA), idx, R.p(R.u32(pp - DELTA), 24).hex() if 0x200000 < R.u32(pp - DELTA) < 0x600000 else '-')); continue
            parts.append([f, idx, dx, dy])
    elif bank(sp): parts.append([B[sp], fl & 0x3f, 0, 0])
    else: unk += 1; open(os.path.join(os.environ.get('TEMP', '.'), 'entunk.txt'), 'a').write('single sp %x fl %x hdr %s
' % (sp, fl, R.p(sp, 24).hex()))
    if parts: out.append({'x': x, 'y': y, 'z': z, 'size': sz, 'shade': sh, 'mirror': 1 if fl & 0x40 else 0, 'parts': parts})
if len(sys.argv) > 1: json.dump(out, open(sys.argv[1], 'w'))
print('ents', len(out), 'unknown', unk, 'count', cnt)
