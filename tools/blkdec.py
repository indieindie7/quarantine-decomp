"""Quarantine DOS .MAP/.BLK/.SPR reader (from Q.EXE 0x32670, 0x4987c). Provisional."""
import struct, sys, json, os
def rd_map(p):
    d = open(p, 'rb').read()
    w, h = struct.unpack_from('<HH', d, 0)
    cells = struct.unpack_from('<%dH' % (w * h), d, 4)
    return w, h, cells, len(d) - 4 - w * h * 2
def rd_blk(p):
    d = open(p, 'rb').read()
    ver, n = struct.unpack_from('<HH', d, 0)
    hdr = [struct.unpack_from('<4H', d, 4 + i * 8) for i in range(n)]
    o = 4 + n * 8
    blocks = []
    for a, b, c, e in hdr:
        quads = [d[o + i * 18:o + i * 18 + 18] for i in range(a)]; o += a * 18
        walls = [d[o + i * 18:o + i * 18 + 18] for i in range(b)]; o += b * 18
        k = c // 4
        tex = [(d[o + i * 2], d[o + i * 2 + 1]) for i in range(k)]; o += k * 2
        ex1 = d[o:o + k * 2]; o += k * 2
        ex2 = d[o:o + k * 2]; o += k * 2
        ex3 = d[o:o + k * 2]; o += k * 2
        recs = [d[o + i * 12:o + i * 12 + 12] for i in range(e)]; o += e * 12
        blocks.append(dict(quads=quads, walls=walls, tex=tex, ex1=ex1, ex2=ex2, ex3=ex3, recs=recs, hdr=(a, b, c, e)))
    return ver, blocks, len(d) - o
def rd_spr(p):
    d = open(p, 'rb').read()
    n = d[0]
    wh = [(d[1 + i * 2], d[2 + i * 2]) for i in range(n)]
    o = 1 + n * 2; out = []
    for w, h in wh:
        out.append((w, h, d[o:o + w * h])); o += w * h
    return out, len(d) - o
if __name__ == '__main__':
    g = sys.argv[1]
    for c in ['CITY', 'JCITY', 'KCITY', 'PCITY', 'SCITY', 'WCITY']:
        w, h, cells, left = rd_map(f'{g}/{c}.MAP')
        ver, bl, bleft = rd_blk(f'{g}/{c}.BLK')
        print(c, 'map', w, h, 'left', left, 'cell max', max(cells), 'hi bits', sorted({x >> 8 for x in cells})[:12], '| blk ver', ver, 'n', len(bl), 'left', bleft)
    for s in ['WALL1', 'OBJECTS', 'KWALL3', 'PWALL2']:
        sp, left = rd_spr(f'{g}/{s}.SPR'); print(s, len(sp), sorted({(w, h) for w, h, _ in sp})[:8], 'left', left)
    import collections
    ver, bl, _ = rd_blk(f'{g}/CITY.BLK')
    cnt=[collections.Counter() for _ in range(6)]; zs=collections.Counter(); nv=collections.Counter()
    for b in bl:
        for q in b['quads']:
            for i in range(6): cnt[i][q[i]]+=1
            for v in range(4): zs[q[8+v*3]]+=1
    for i in range(6): print('hdr byte',i,sorted(cnt[i].items())[:20])
    print('z',sorted(zs.items()))
    w, h, cells, _ = rd_map(f'{g}/CITY.MAP')
    use=collections.Counter(c&0xff for c in cells); print('blocks used',len(use),'max',max(use)); print('flags',collections.Counter(c>>10 for c in cells))
    for i in (0, 0x22, 0x27, 0x35, 0x41):
        b = bl[i]; print('blk', hex(i), b['hdr'])
        for q in b['quads'][:40]: print('  q', q[:6].hex(' '),'|',' '.join('%d,%d,%d'%(q[6+v*3],q[7+v*3],q[8+v*3]) for v in range(4)))
        for q in b['walls'][:6]: print('  w', q[0], q[1], struct.unpack('<8h', q[2:18]))
        n=len(b['tex'])//1
        print('  tex', b['tex'][:len(b['quads'])]); print('  ex1', b['ex1'][:40].hex(' ')); print('  ex2', b['ex2'][:40].hex(' ')); print('  ex3', b['ex3'][:40].hex(' '))
        for r in b['recs'][:5]: print('  r', struct.unpack('<6h',r))
