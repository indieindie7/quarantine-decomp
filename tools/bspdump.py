"""Dump live per-block BSP trees from DOSBox (NOTES 'DRAW ORDER = PER-BLOCK BSP'). bspdump.py [CITY] -> port/data/<CITY>_bsp.json
node = [kind, a, b, nx, ny, px, py, A, B]; kind 0 wall (a = wall idx), 1 leaf (a, b raw), 2 floor (a = quad idx, py = z); A/B = node idx or -1."""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dosrd import Reader, DELTA
city = sys.argv[1] if len(sys.argv) > 1 else 'KCITY'
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'port', 'data')
nb = len(json.load(open(os.path.join(D, city + '.json')))['blocks'])
R = Reader(); out = []; bad = {}
for blk in range(nb):
    nW, pW, pT, nQ, pQ, nO, pO, root, n20, tex = struct.unpack('<10I', R.rd(0x97020 + blk * 40, 40))
    nodes = []; idx = {}
    def walk(p):
        if p == 0: return -1
        if p in idx: return idx[p]
        i = len(nodes); idx[p] = i; nodes.append(None)
        raw = R.p(p, 0x24); kind = raw[0]; a, b, nx, ny, px, py, A, B = struct.unpack('<2I4i2I', raw[4:])
        if kind == 0:
            if (a - pW) % 20 or not 0 <= (a - pW) // 20 < nW: bad[blk] = ('wall', hex(a), hex(pW), nW)
            nodes[i] = [0, (a - pW) // 20, b, nx, ny, px, py, walk(A), walk(B)]
        elif kind == 2:
            if (a - pQ) % 18 or not 0 <= (a - pQ) // 18 < nQ: bad[blk] = ('quad', hex(a), hex(pQ), nQ)
            nodes[i] = [2, (a - pQ) // 18, b - tex if b else 0, nx, ny, px, py, walk(A), walk(B)]
        else:
            ol = []
            while a:
                rec, x, y, z, pad, nxt = struct.unpack('<I3hHI', R.p(a, 16)); ol.append((rec - pO) // 12); a = nxt
                if (rec - pO) % 12 or not 0 <= ol[-1] < nO: bad[blk] = ('obj', hex(rec))
            nodes[i] = [kind, ol, 0, nx, ny, px, py, -1, -1]
            if kind != 1: bad[blk] = ('kind', kind)
        return i
    walk(root); out.append({'nW': nW, 'nQ': nQ, 'nO': nO, 'pO': pO, 'nodes': nodes})
json.dump(out, open(os.path.join(D, city + '_bsp.json'), 'w'), separators=(',', ':'))
ks = [0, 0, 0]
for b in out:
    for n in b['nodes']:
        if n[0] < 3: ks[n[0]] += 1
print('blocks', nb, 'nodes wall/leaf/floor', ks, 'walls', sum(b['nW'] for b in out), 'quads', sum(b['nQ'] for b in out), 'bad', len(bad), list(bad.items())[:5])
J = json.load(open(os.path.join(D, city + '.json')))['blocks']
print('json mismatch', [(i, len(J[i]['w']), b['nW'], len(J[i]['q']), b['nQ'], len(J[i]['o']), b['nO']) for i, b in enumerate(out) if (len(J[i]['w']), len(J[i]['q']), len(J[i]['o'])) != (b['nW'], b['nQ'], b['nO'])][:6], 'max items', max(b['nW'] + b['nQ'] + b['nO'] for b in out), 'objs in leaves', sum(len(n[1]) for b in out for n in b['nodes'] if n[0] == 1), 'of', sum(b['nO'] for b in out))
b = out[88]; print('blk88', b['nW'], b['nQ'], b['nO'], hex(b['pO'])); [print(i, n) for i, n in enumerate(b['nodes'][:40])]
