"""Painter draw order replica (Q.EXE 0x4736c + 0x4668c + 0x464d0). bsporder.py camx camy camz [CITY] -> list of (ord, dx, dy, cellx, celly, blk, kind, idx)."""
import sys, os, json
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'port', 'data')
T = [-3,-3,3,-3,3,3,-3,3,-2,-3,2,-3,3,-2,3,2,2,3,-2,3,-3,2,-3,-2,-1,-3,1,-3,3,-1,3,1,1,3,-1,3,-3,1,-3,-1,0,-3,3,0,0,3,-3,0,-2,-2,2,-2,2,2,-2,2,-1,-2,1,-2,2,-1,2,1,1,2,-1,2,-2,1,-2,-1,0,-2,2,0,0,2,-2,0,-1,-1,1,-1,1,1,-1,1,0,-1,1,0,0,1,-1,0,0,0]
def wsort(L):
    """Leaf sort as DOS does it: 0x464d0 -> Watcom qsort 0x5490d, n < 16 path = gap 3 pass over indices 3, 6, 9.. then gap 1 insertion, far first; ties keep what the passes leave (checked on live lists e20 e21 e30)."""
    assert len(L) < 16, 'n >= 16 = quicksort path of 0x5490d, not ported'
    for gap in (3, 1):
        for p in range(gap, len(L), gap):
            q = p
            while q > 0 and L[q][0] > L[q - gap][0]: L[q], L[q - gap] = L[q - gap], L[q]; q -= gap
    return L
def order(camx, camy, camz, city='KCITY'):
    d = json.load(open(os.path.join(D, city + '.json'))); bsp = json.load(open(os.path.join(D, city + '_bsp.json')))
    W, H = d['w'], d['h']; out = []
    for e in range(49):
        dx, dy = T[e * 2], T[e * 2 + 1]; cx, cy = (camx >> 9) + dx, (camy >> 9) + dy
        if not (0 <= cx < W and 0 <= cy < H): continue
        bi = (d['cells'][cy * W + cx] & 0x7f) - 1
        if bi < 0: continue
        nodes = bsp[bi]['nodes']; ob = d['blocks'][bi]['o']; lx = (camx & 0x1ff) - dx * 512; ly = (camy & 0x1ff) - dy * 512
        def walk(i):
            if i < 0: return
            n = nodes[i]
            if n[0] == 1:
                for dist, oi in wsort([((lx - ob[o][0]) ** 2 + (ly - ob[o][1]) ** 2 + (camz - ob[o][2] + 1) ** 2, o) for o in n[1]]): out.append((len(out), dx, dy, cx, cy, bi, 'o', oi))
                return
            af = ((ly - n[6]) * n[4] + n[3] * (lx - n[5]) < 0) if n[0] == 0 else n[6] < camz
            walk(n[7] if af else n[8]); out.append((len(out), dx, dy, cx, cy, bi, 'w' if n[0] == 0 else 'q', n[1])); walk(n[8] if af else n[7])
        if nodes: walk(0)
    return out
if __name__ == '__main__':
    a = sys.argv[1:]
    for r in order(int(a[0]), int(a[1]), int(a[2]), a[3] if len(a) > 3 else 'KCITY'): print(*r)
