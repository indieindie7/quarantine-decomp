"""q2inst.py <disc root> <outdir> [--check] : Quarantine II DOS installer archive (11-25). INSTALL.EXE (Borland C++, PKWARE DCL
1990-92) reads IMAGE.DAT = text lines: file count, then per file 4 lines (path, first byte + 1 (0 for file 0), last byte in ROADWAR.1, unpacked
size). Each span of ROADWAR.1 is one PKWARE DCL "implode" stream (byte 0 = 0 binary / 1 ascii literals, byte 1 = dict bits 4..6).
BLD_INFO.CFG / LANGRC.RES are the installer's own text, every byte +1. Decoder = port of Mark Adler's blast.c. Writes the tree;
--check compares each file with the same path on the disc when present."""
import sys, os

def _build(rep):
    lens = []
    for b in rep:
        lens += [b & 15] * ((b >> 4) + 1)
    cnt = [0] * 14; sym = []
    for l in lens: cnt[l] += 1
    offs = [0] * 15
    for i in range(1, 14): offs[i + 1] = offs[i] + cnt[i]
    sym = [0] * len(lens)
    for s, l in enumerate(lens): sym[offs[l]] = s; offs[l] += 1
    return cnt, sym

LIT = _build(bytes([11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8, 9, 7, 6, 7, 8, 7, 6, 55, 8, 23, 24, 12,
                    11, 7, 9, 11, 12, 6, 7, 22, 5, 7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9, 12, 8, 12, 5,
                    38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27, 44, 253, 253, 253, 252, 252, 252, 13, 12, 45, 12,
                    45, 12, 61, 12, 45, 44, 173]))
LEN = _build(bytes([2, 35, 36, 53, 38, 23]))
DIST = _build(bytes([2, 20, 53, 230, 247, 151, 248]))
BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]

def blast(src):
    st = {'p': 0, 'b': 0, 'n': 0}
    def bits(need):
        v, n = st['b'], st['n']
        while n < need:
            v |= src[st['p']] << n; st['p'] += 1; n += 8
        st['b'] = v >> need; st['n'] = n - need
        return v & ((1 << need) - 1)
    def decode(h):
        cnt, sym = h; code = first = index = 0
        for ln in range(1, 14):
            code |= bits(1) ^ 1
            c = cnt[ln]
            if code < first + c: return sym[index + (code - first)]
            index += c; first = (first + c) << 1; code <<= 1
        raise ValueError('bad code')
    lit, dic = bits(8), bits(8)
    assert lit in (0, 1) and 4 <= dic <= 6, (lit, dic)
    out = bytearray()
    while True:
        if bits(1):
            s = decode(LEN); ln = BASE[s] + bits(EXTRA[s])
            if ln == 519: break
            sh = 2 if ln == 2 else dic
            d = (decode(DIST) << sh) + bits(sh) + 1
            for _ in range(ln): out.append(out[-d])
        else:
            out.append(decode(LIT) if lit else bits(8))
    return bytes(out)

def main(a):
    root, out = a[0], a[1]; chk = '--check' in a
    lines = open(os.path.join(root, 'IMAGE.DAT'), 'rb').read().decode('latin1').split('\r\n')
    n = int(lines[0]); arc = open(os.path.join(root, 'ROADWAR.1'), 'rb').read()
    ok = same = diff = 0
    for i in range(n):
        path, s, e, size = lines[1 + 4 * i:5 + 4 * i]; s, e, size = int(s), int(e), int(size)
        d = blast(arc[max(s - 1, 0):e + 1])  # listed first byte is one past the real start (except file 0)
        if len(d) != size: print('SIZE', path, len(d), size); continue
        ok += 1; p = os.path.join(out, *path.split('\\')); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(d)
        q = os.path.join(root, *path.split('\\'))
        if chk and os.path.isfile(q):
            if open(q, 'rb').read() == d: same += 1
            else: diff += 1; print('DIFF', path)
    print('files', n, 'size ok', ok, 'same as disc', same, 'differ', diff, 'archive end', e + 1, len(arc))

if __name__ == '__main__': main(sys.argv[1:])
